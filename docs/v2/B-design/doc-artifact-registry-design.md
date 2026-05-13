# doc_artifact_registry PoC 詳細設計（FR-GR08 / FR-GR10）

Version: 1.0  
Status: 設計中（実装向け）  
Owner: Docs（TL）  
Date: 2026-05-14  
Related FR:
- FR-GR08 `helix doc register` / doc 実体検知 / Codex completion ≠ 実体出力の構造的対策
- FR-GR09 `lint ecosystem` への接続
- FR-GR10 `expected_artifacts.yaml` の期待値一元化
- FR-GR11 `fail_fix_log` 連動（`doc_artifact_missing`）

## 1. この設計の目的

FR-GR08 と FR-GR10 は、`docs` 追加時の実体欠損を「検知不能な事象”として埋め合わせる”」問題に対して、
`helix.db` を真実源とする **期待 Artifact レジストリ** として解決する。

本設計の最終到達点は以下。

- `helix doc register` が `write` 系操作を DB に反映し、ハッシュ・行数・サイズの更新を自動管理できる。
- `helix doc verify` が `expected` と `actual` の差分を判定し、未作成を fail-close 可能にする。
- `helix doc sync-expectations` が `PLAN × Sprint × Artifact` 期待値を一括同期する。
- `helix doc verify`/`gate` が失敗したときに `fail_fix_log` へ構造化再発防止イベントを投下する。

> 背景参照: `docs/v2/L1-RE_REQUIREMENTS.md` の FR-GR08 / FR-GR10 と  
> `docs/v2/B-design/fail-fix-log-design.md` の fail_fix_log 設計。  

## 2. 設計範囲と非機能要件

### 2.1 対象

本設計は以下の CLI / DB / Hook 変更を対象にする。

- `docs/` 配下文書の作成・更新時の実体検知
- 期待 artifact の宣言管理（PLAN × Sprint）
- gate / dashboard / CI での可視化
- `fail_fix_log` 自動連携

### 2.2 非対象

- `docs/` 以外のアセット（`src/` の検査）は対象外。
- 既存 `detector` ロジック自体のアルゴリズム刷新は対象外（新規 doc 専用コマンドとして実装する）。
- 既存 hook 案件で PostToolUse 以外（PreToolUse / pre-commit）を強制停止対象に再定義しない。

### 2.3 非機能要件

- **100% 自動登録**: `Write` / `Edit` 終了時に対象 path があれば 1 回の register を発行。
- **整合性**: `expected`, `exists`, `missing`, `stale`, `superseded` を DB の 1 つの状態遷移で表現。
- **再発防止**: 欠損検知はイベントログ化して再発率を管理。
- **Argparse 互換**: すべての CLI は `argparse` スタイル（`--help`, `--version`, 引数エラー 2 終了）を満たす。
- **セーフティ**: 参照先 path が `docs/` 以外のときは auto-register を行わない（警告）。

## 3. 用語（用語統一）

| 用語 | 定義 |
|---|---|
| 期待 Artifact | FR-GR10 の `expected_artifacts.yaml` に定義された `path/kind/min_lines/related_fr` |
| 実体 Artifact | 実ファイルとして存在し内容を持つ `docs/...` ファイル |
| doc_artifacts レコード | 期待と実体を突き合わせる DB 行 |
| missing | 期待されるが実体が存在しない状態 |
| stale | 実体が更新されているか、期待メタ情報と食い違う疑いのある状態 |
| superseded | plan/sprint 入れ替えで期待値が更新され、旧行が更新対象から外れた状態 |

## 4. エンティティ設計

### 4.1 テーブル定義（必須）

```sql
CREATE TABLE doc_artifacts (
  id INTEGER PRIMARY KEY,
  artifact_path TEXT NOT NULL UNIQUE,
  artifact_kind TEXT NOT NULL CHECK (artifact_kind IN (
    'design_doc',
    'plan_doc',
    'audit_doc',
    'requirement_doc',
    'review_doc',
    'test_doc',
    'config',
    'migration',
    'memory',
    'other'
  )),
  expected_section TEXT,
  expected_min_lines INTEGER,
  actual_lines INTEGER,
  actual_bytes INTEGER,
  status TEXT NOT NULL DEFAULT 'expected'
    CHECK (status IN ('expected','exists','missing','stale','superseded')),
  source_task TEXT,
  source_role TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  verified_at TEXT,
  last_modified TEXT,
  plan_id TEXT,
  sprint_id TEXT,
  related_fr TEXT,
  hash_sha256 TEXT
);

CREATE INDEX idx_doc_artifacts_status ON doc_artifacts(status);
CREATE INDEX idx_doc_artifacts_plan ON doc_artifacts(plan_id, status);
CREATE INDEX idx_doc_artifacts_path ON doc_artifacts(artifact_path);
CREATE INDEX idx_doc_artifacts_kind ON doc_artifacts(artifact_kind, related_fr);
```

### 4.2 列仕様

#### `artifact_kind`
- `CHECK` により enum 管理。
- 将来追加時は migration で拡張（新種別追加は v22 構造変更として追加 PR）。

#### `expected_min_lines`
- FR-GR10 の `min_lines` を格納。
- `NULL` は「閾値未指定」として扱い、`missing` 判定対象から外す。

#### `status`
- 遷移:
  - `expected` → `exists`（実体ありで計測成功）
  - `expected` → `missing`（実体不存在）
  - `exists` → `stale`（実体更新でハッシュ差分 / 期待値差分）
  - `exists|stale` → `superseded`（同期された期待セットから外れたとき）

#### `verified_at`
- `helix doc verify` 実行時刻を更新。
- 未検証なら `NULL` のまま。

#### `hash_sha256`
- `sha256sum` の16進文字列（小文字）を格納。
- `actual_lines` / `actual_bytes` の再計算に利用。

### 4.3 補助ビュー（想定）

```sql
CREATE VIEW doc_artifact_metrics_v1 AS
SELECT
  COUNT(*) AS expected_count,
  SUM(CASE WHEN status='exists' THEN 1 ELSE 0 END) AS exists_count,
  SUM(CASE WHEN status='missing' THEN 1 ELSE 0 END) AS missing_count,
  SUM(CASE WHEN status='stale' THEN 1 ELSE 0 END) AS stale_count,
  ROUND(100.0 * SUM(CASE WHEN status='exists' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS exists_rate
FROM doc_artifacts;
```

## 5. expected_artifacts.yaml スキーマ

### 5.1 Schema (v1)

```yaml
schema_version: 1
expectations:
  - plan_id: V2-PHASE-A
    artifacts:
      - path: docs/v2/A-audit/capability-inventory.md
        kind: audit_doc
        min_lines: 50
        related_fr: FR-INV01
      - path: docs/v2/A-audit/audit-summary.md
        kind: audit_doc
        min_lines: 600
        related_fr: FR-INV05
  - plan_id: V2-PHASE-B
    sprint_id: S-001
    artifacts:
      - path: docs/v2/B-design/vmodel-semantics-spine.yaml
        kind: design_doc
        min_lines: 100
        related_fr: FR-VD01
```

### 5.2 バリデーションルール

- `schema_version` は正の整数。
- `expectations[]` は空配列不可。
- `plan_id` 必須。
- `artifacts[].path` は `docs/` プレフィックス必須。
- `artifacts[].kind` は `artifact_kind` と同一文字列制約。
- `min_lines` は 0 以上の整数。
- 同一 `plan_id` に同一 `path` の重複定義禁止（`UNIQUE(path, plan_id)`）を CLI 側で防御。

### 5.3 同期アルゴリズム

1. YAML parse 成功
2. `plan_id` グループごとに既存 `doc_artifacts` 行を退避
3. 各 artifact エントリを upsert:
   - なければ insert（`status='expected'`, `expected_min_lines` 入力）
   - あれば期待値差分を更新（`status='expected'`/`stale`）
4. YAML 内に存在しない旧レコードは `superseded` へ遷移

## 6. CLI 設計

全コマンドは `cli/helix-*` の `doc` サブコマンド群で統一する想定。

### 6.1 `helix doc register`

#### ユースケース

- PostToolUse hook から呼び出し
- 人手による `--auto` 既定登録

#### 仕様

- `--path <path>`: 必須（docs 配下 path）
- `--kind <kind>`: 任意。指定なければ `other`
- `--section <expected_section>`: 任意
- `--min-lines N` / `--plan-id <id>` / `--sprint-id <id>` / `--role <role>` / `--task <task>`
- `--auto`:
  - 実行モードを auto-register に切り替え
  - `expected_section` は未指定時は `auto_detected`
  - `artifact_kind` は拡張子/パス規則で補完

#### 実装挙動

- `artifact_path` の `stat` / `read` が可能なら `actual_lines`, `actual_bytes`, `hash_sha256`, `last_modified` を更新。
- 既存レコードの場合:
  - `status` は現状次第で `exists` へ昇格
  - 期待値がなくても `other` 系として登録
- 未更新対象の場合:
  - `status='exists'` / `expected_min_lines` 未設定

### 6.2 `helix doc verify`

#### ユースケース

- plan-sprint 検証
- gate 実行連携
- PR/CI 事前チェック

#### 引数

- `--plan-id <id>`: 省略時は全 plan 予定分
- `--sprint-id <id>`: 同時指定可
- `--status [missing|exists|stale|expected|superseded]`:
  - フィルタ条件
- `--gate <G2|G3|G4>`:
  - G2/G3/G4 の fail-close 判定を有効化
- `--fail-close`:
  - 指定があり、重大差分ありなら `exit 2`
- `--json`, `--dry-run`

#### 判定ロジック

1. 期待 rows を列挙
2. 実体ファイル存在・行数・ハッシュを再取得
3. `status` を更新
4. `--gate` がある場合:
   - FR-GR10 の対象カテゴリに対し fail-close
   - missing が 1 件以上なら `exit 2`
   - stale は警告のみ

### 6.3 `helix doc list`

#### 引数

- `--status`, `--kind`, `--plan-id`, `--sprint-id`, `--section`, `--fr`, `--sort`, `--limit`, `--offset`, `--json`

#### 出力

- table mode:
  - id, plan_id, sprint_id, artifact_path, kind, status, lines, bytes, last_modified
- json mode:
  - 署名されたキーで構造化

### 6.4 `helix doc sync-expectations`

#### 引数

- `--file <expected_artifacts.yaml>` 既定: `docs/v2/expected_artifacts.yaml`
- `--plan-id <id>`:
  - YAML には複数 plan でも、対象を限定して部分同期可能
- `--strict`:
  - JSON Schema mismatch を即 fail-close
- `--dry-run`

#### 戻り値

- 追加・更新・削除件数
- 遷移統計（expected→exists など）

### 6.5 `helix doc verify-hash`

#### 引数

- `--path <path>`: 必須
- `--refresh`:
- 不在なら `missing`
- 差分あれば `changed`
- 一致なら `unchanged`

## 7. ログ設計（観測/監査）

| event | source | フォーマット |
|---|---|---|
| register 実行 | CLI | `artifact_path`, `kind`, `status_before`, `status_after`, `bytes`, `lines` |
| verify 実行 | CLI | `plan_id`, `gate`, `missing_count`, `stale_count`, `exists_count`, `elapsed_ms` |
| missing 自動記録 | verify fail-close | `event_kind='doc_artifact_missing'` を `fail_fix_log` へ |

### 7.1 fail_fix_log 連携仕様

`helix doc verify` で `missing` 検出時、以下を 1 件送る。

- `event_kind`: `doc_artifact_missing`
- `severity`: `P1`（plan 規模の不足なら `P2` へ調整）
- `title`: `Missing doc artifact detected`
- `root_cause`: `doc artifact missing in expected set`
- `mitigation_kind`: `documentation`
- `mitigation_ref`: 再投入 task id（`<plan_id>/<sprint_id>` または実行チケット）
- `related_fr`: 該当 FR（`FR-GR08`, `FR-GR10`, `関連 FR`）
- `occurrence_count`: 同 path + plan_id + related_fr の既存 open イベントがあれば +1

### 7.2 2 回以上 missing の扱い

- 同 artifact が 2 回連続 missing: `occurrence_count++`
- 3 回以上: `related_axis` を付加して escalation 対象候補へ転記（必要時 hook 強化）

## 8. PostToolUse hook 連携

### 8.1 スクリプト要件

- `docs/*` の write を対象にする
- hook 失敗で CLI を停止しない（ログに warning）
- register 呼び出しに `--auto` を付与

### 8.2 サンプル実装

```bash
#!/usr/bin/env bash
set -euo pipefail

TOOL_NAME="${TOOL_NAME:-}"
FILE_PATH="${FILE_PATH:-}"
FILE_EXT="${FILE_EXT:-}"

if [[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "Create" ]] \
   && [[ "$FILE_PATH" == docs/* ]]; then
  helix doc register --path "$FILE_PATH" --auto \
    --source-tool "$TOOL_NAME" \
    --source-role "${ROLE:-unknown}" || true
fi

if [[ "$FILE_PATH" == docs/* && "${FILE_EXT}" == "md" ]]; then
  : # markdown lint hook insertion point
fi
```

### 8.3 Hook 実行時のエラー処理

- `helix doc register` が 0 以外を返しても、メイン tool の完了を中断しない。
- ただし 3 回連続して失敗時は `helix hook-fail` に event として記録。

## 9. Gate 連動（G2 / G3 / G4）

### 9.1 自動実行

`helix gate` 実行時に FR-GR08 期待 artifact を紐づけて実行。

- `helix doc verify --plan-id <id> --gate G2 --fail-close`
- `helix doc verify --plan-id <id> --gate G3 --fail-close`
- `helix doc verify --plan-id <id> --gate G4 --fail-close`

### 9.2 G ルール

- G2: 設計 doc 不在で fail-close
- G3: 詳細設計 doc 不在で fail-close
- G4: 実装 doc / レビュー doc 不在で fail-close
- FR-GR08 の最小要件: 事前に `expected_artifacts.yaml` が planId へ適用済み

### 9.3 CI 連動（将来）

- commit hook / PR チェックに
  `helix doc verify --plan-id <PLAN_ID> --fail-close --gate G4`
  を追加し、未登録 docs を早期検知する。

## 10. dashboard / detect 連携

### 10.1 出力要件

`helix detect dashboard` で以下を表示する。

- `Expected`, `Exists`, `Missing`, `Stale`
- `Last week delta`（前週比 +8 exists, -2 missing など）
- `Critical missing`（`related_fr` と `kind` を含める）

### 10.2 サンプル

```
[Doc artifacts]
  Expected: 50, Exists: 34, Missing: 16, Stale: 2
  Last week: +8 exists, -2 missing
  Critical missing: docs/v2/B-design/vmodel-semantics-spine.yaml
```

### 10.3 ダッシュボード集計クエリ（概略）

```sql
SELECT
  related_fr,
  COUNT(*) AS total,
  SUM(CASE WHEN status='exists' THEN 1 ELSE 0 END) AS exists_count,
  SUM(CASE WHEN status='missing' THEN 1 ELSE 0 END) AS missing_count,
  SUM(CASE WHEN status='stale' THEN 1 ELSE 0 END) AS stale_count
FROM doc_artifacts
WHERE plan_id = :plan_id
GROUP BY related_fr;
```

## 11. PoC 実装計画

### Phase 3（helix.db v21）

1. `doc_artifacts` table 追加（上記 DDL）
2. 既存 `expected_artifacts.yaml` schema 定義採用 + parser 実装

### Phase 4（検出ガードレール）

3. `helix doc register / verify / list` CLI 実装
4. PostToolUse hook 実装（docs 配下 auto-register）
5. fail_fix_log 連動（missing イベント）

### Phase 5（自動化）

6. `expected_artifacts.yaml` の V2 全 phase 定義へ展開
7. CI 連携（commit 時 verify）

## 12. 実装モジュール分割（実装時の責務）

- `cli/lib/doc_artifacts.py`（DB access + schema + serializer）
- `cli/lib/doc_expectations.py`（YAML parser + validator）
- `cli/lib/doc_cli.py`（argparse 定義）
- `cli/lib/doc_hash.py`（sha256 / 行数計測）
- `.claude/hooks/posttooluse-doc-register.sh`（hook）
- `cli/lib/fail_fix_bridge.py`（`fail_fix_log` 書込み）
- `cli/lib/doc_detect_adapter.py`（dashboard 検索 API）

## 13. 参照実装シナリオ

### 13.1 Write 完了後の登録

1. Agent が `docs/v2/B-design/doc-foo.md` を作成
2. PostToolUse hook で `helix doc register --path ... --auto` 呼び出し
3. `actual_lines/bytes/hash_sha256` が更新され `status='exists'`

### 13.2 verify の失敗 → auto-log

1. `helix doc verify --plan-id V2-PHASE-B --gate G3 --fail-close`
2. `docs/v2/B-design/vmodel-semantics-spine.yaml` が未作成
3. 失敗: `doc_artifact_missing` を `fail_fix_log` に記録
4. `occurrence_count++` と `mitigation_ref`（再投入タスク id）更新

### 13.3 expected 変更時

1. `docs/v2/B-design/expected_artifacts.yaml` を更新
2. `helix doc sync-expectations --file ... --plan-id V2-PHASE-B`
3. 旧期待値が `superseded` に遷移

## 14. セキュリティ・監査注意点

- ファイル read は `docs/` へ限定し、`../` を含むパスは拒否する。
- DB への埋め込みはプレースホルダ付き SQL を使い注入を防ぐ。
- hash 出力で機微情報を log しない（パス・ハッシュ・行数のみ許可）。
- hook 失敗は `exit 1` ではなく `true` フォールバックとし、agent 本体を停止させない。

## 15. 互換性 / 移行

- v1 互換: `doc_artifacts` は新規テーブルとして追加（既存資産破壊なし）。
- 既存 `doc_*` 設計は既存命名を維持し、`artifact_kind` の enum 内で統一。
- `expected_artifacts.yaml` は既存 schemaVersion 1 で開始し、`schema_version` 差分はエラーとして明示。

## 16. 品質基準 / 受入条件

### 16.1 機能受入

- 期待定義の upsert/override / prune が正しく動作
- register→verify→list→sync の一連で欠損を再現・検知・記録できる
- G2/G3/G4 fail-close が FR 対応に従う
- Hook の `--auto` 登録で既存 `docs` 書き込み漏れが減少

### 16.2 運用受入（KPI）

- expected の存在率: 90%+
- missing 検知→対応（mitigated）24 時間以内
- false positive < 5%

## 17. TODO / リスク

- `docs/v2/expected_artifacts.yaml` の全 PLAN 定義がまだ未整備（PoC 以外）
- `helix` サブコマンド `doc` の bootstrap が未存在の場合の実装順決定（cli 追加方式）
- ハッシュ差分 `stale` 判定の判定窓口（min_lines と hash 差分どちらを優先するか）
- G3/G4 の「詳細設計」「レビュー doc 不在」の path 判定（正規表現ルールの確定）
- CI の対象 plan 探索（`plan_id` 未指定時の既定挙動）

## 18. 変更追跡（参照）

- `docs/v2/L1-REQUIREMENTS.md`
- `docs/v2/B-design/fail-fix-log-design.md`
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_codex_completion_vs_actual_output.md`
- `docs/v2/B-design/l2-master-sketch.md`
- `docs/v2/C-followup/v2-dogfood-plan.md`

---
