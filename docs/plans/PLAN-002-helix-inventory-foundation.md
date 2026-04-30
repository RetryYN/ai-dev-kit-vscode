# PLAN-002: HELIX 棚卸し基盤 (Phase 0 + A0/A1 + helix.db v8 audit_decisions) (v2)

## 1. 目的
- PLAN-002 v34 の棚卸し関連のみを独立させ、TL ループ要因である範囲肥大化を解消する。
- Phase 0 preflight、A0（Discovery）、A1（Classification）を一貫して成立させ、`decisions.yaml` と `audit_decisions` の正本・監査の基盤を確立する。
- `audit_decisions` 以外の auto-restart 関連（HMAC、HOME DB、残量警告、CURRENT v2、B/C/D PoC）は PLAN-003 へ分離する。

## 2. スコープ

### 2.1 含める範囲
- Phase 0 preflight
  - gitleaks (license/version/install) の前提承認証跡
  - `.gitignore` allowlist パッチ
  - redaction 2 ファイル（`.helix/audit/redaction-denylist.example.yaml`（tracked）、`.helix/audit/redaction-denylist.local.yaml`（gitignore））
- HMAC 署名/鍵管理は PLAN-003 側で扱う
- A0 Discovery
  - 棚卸しは手動スクリプト運用（`inventory-once.sh`）
  - destructive 操作なし
- A1 Classification
  - `decisions.yaml` の分類確定 (`keep/remove/merge/deprecate`)
  - `audit_decisions` テーブル同期運用
  - `idempotency key`: `(candidate_id, schema_version, scope_hash)`
  - G3 までに `docs/design/A1-source-of-truth.md` を作成・凍結（本 PLAN の L2/L3 必須成果物）
- L1 設計
  - `D-DB` / `D-AUDIT`（棚卸し限定）
  - ゲート前提、フェイルセーフ、再ベースライン再実行、非機能観点
- L2 設計 / L3 詳細
  - `schema_version`
  - `audit_decisions` DDL とインデックス
  - migration v7→v8（`audit_decisions` + `import_runs` 追加）
  - migration テスト計画（empty/current/old、backup/restore）
- L4 実装
  - `A0/A1` 向けの最小実装（CLI は A1 分類 CLI までを含む）
- L6 検証
  - preflight / A0 / A1 / DB migration / dry-run import / fixture 実行の結果で妥当性検証
- L7 デプロイ
  - 既存配布物への前提条件追加のみ
- L8 受入
  - G1〜G7 の満了、A0/A1 完了条件、`decisions.yaml` と `audit_decisions` 同期証跡確認

### 2.2 含めない範囲（PLAN-003 へ分離）
- HMAC 署名、`worktree_snapshot_hash`、`handover_manifest_hash`、`phase_yaml_hash`
- HOME DB（`~/.helix/auto-restart/log.db`）
- hook registration、settings merge、private runtime copy
- CURRENT schema v2（legacy input / normalized output）
- 30%/15%/5% 閾値、tiktoken、keyring、5% D-owned 自動 dump 契約
- B/C/D outcome matrix と再ベースラインの分岐運用
- `context_warnings` と `dep_review_log` テーブル

### 2.3 想定する除外
- 本 PLAN は「棚卸し成果を安全に確定させる」ことに限定し、運用自動化系の継続能力は扱わない。
- auto-restart 系の受け渡しは、PLAN-003 で受ける。

## 3. 関連 PLAN
- auto-restart 系はこの PLAN で扱わず、[PLAN-003-auto-restart-foundation.md](PLAN-003-auto-restart-foundation.md) に完全移管する。
- [PLAN-003-auto-restart-foundation.md](PLAN-003-auto-restart-foundation.md) は本 PLAN（Phase 0 + A0 + A1 + audit_decisions の移行）完了を前提とし、同一対象を前提データとして参照する。
- 本 PLAN の受入時点で以下が成立していることを前提とする。
  - `A0` / `A1` が Phase 0 で定義した再現性条件を満たす
  - `decisions.yaml` と `audit_decisions` の同期ルールが定義・実装済み
  - `scope_hash` の扱いに対する再ベースライン方針が固定
  - `migration` は v7→v8 で `audit_decisions` と `import_runs` の追加を前提

## 3.1 readiness retro 反映 (PLAN-004 v5 連動)

### 3.1.1 適用範囲
- 本 PLAN は PLAN-004 v5 確定前に finalize 済みのため、readiness 概念を retro 反映する。
- 実装スコープは変更せず、retro 方針の追記のみ実施する。
- L-level readiness は本 PLAN の既存 L1/L2/L3/L4/L6/L7/L8 対応セクションへ対応付けて評価する。

### 3.1.2 readiness exit 条件マッピング
| L-level | 本 PLAN の対応セクション | readiness exit 条件 | 適合状況 |
|---|---|---|---|
| L1 | §4.4 / §4.4.1 / §4.4.2 | A0/A1 の受入条件に対する要件明確化と、triaged 残存時の fail 条件定義があること | 適合 |
| L2 | §4.5 / §4.5.1 | D-DB / D-AUDIT 成果物を成果要件として確定し、設計 freeze 前提が明示されていること | 適合 |
| L3 | §4.6 / §4.6.1 / §4.6.2 / §4.6.3 | DDL と migration/rollback 条件を固定し、検証ケースを L4 前提で拘束すること | 適合 |
| L4 | §4.7 | Sprint 単位で deterministic 実装を定義し、棚卸し対象外を PLAN-003 へ移管していること | 適合 |
| L6 | §6 | G1-L3 / migration rehearsal / dry-run import の検証を満たすこと | 部分 |
| L7 | §7 | 既存配布物への前提追加のみとし、deploy 受入前提を明示すること | 適合 |
| L8 | §8 | G1〜G7 と A1 完了条件を同時に確認する受入を定義していること | 適合 |

### 3.1.3 deferred-finding カウント方針
- 本 PLAN の既存 review finding は本文上の明示的な P1/P2 記述が少なく、deferred-finding の明示候補は現時点で「未明示」と扱う。
- `docs/plans/PLAN-002-helix-inventory-foundation.md` の改訂履歴中の P1/P2 記載（v3/v4/v5）を、deferred 候補候補リストとして抽出対象へ取り込む。
- `.helix/audit/deferred-findings.yaml` への記録は PLAN-004 v5 の G4（実装後）で行う運用を採用する。

### 3.1.4 accuracy_score 適用
- 本 PLAN 完了（G7）時の 5 軸評価を、`PLAN-004 v5 §4.1` の精度枠組みで retro 再評価する。
- `deferred-finding` 件数（P1/P2 を含む）を反映して accuracy_score を計算する方針を明文化する。
- 反映結果は次 PLAN の基準値として参照する（レビュー運用上の carry 指標）。

## 4. Phase 構成

### Phase 0（Preflight）

#### 4.1.1 前提確認
- `gitleaks` 導入確認（未導入時は fail-closed）
  - version >= `8.18` を確認
  - インストール元と license（MIT）を確認
  - PM 署名付き承認証跡を残す
- preflight 成果物を以下に固定
  - `docs/plans/PLAN-002-phase0-preflight.md`
  - `docs/research/preflight-gitignore-verification.log`

#### 4.1.2 redaction とログ保護
- 以下の redaction 規約を前提にする
  - ファイル名/本文とも `redaction` 適用前提
  - 機密値は HMAC 化しない（本 PLAN では非署名ハッシュ検知のみ）
  - 未 redacted 値は正規表現で検知し、ログは `***` 置換して保存
- redaction 構成ファイル
  - `.helix/audit/redaction-denylist.example.yaml`（配布用・tracked）
  - `.helix/audit/redaction-denylist.local.yaml`（実運用値、`.gitignore`管理）
- `.gitignore` 追加
  - `.helix/audit/redaction-denylist.local.yaml`
  - `inventory-run-*.log`（`A0 raw log` の tracked 化を禁止）
- HMAC 署名運用（キー生成・.hmac denylist）は PLAN-003 へ移管し、PLAN-002 では含めない

#### 4.1.3 実行手順（最短）
- `inventory-run-*.log` の tracked 化を `git check-ignore -q -- .helix/audit/inventory-run-example.log` の exit code で判定する（`--non-matching` は使用しない）
  - pass 条件: exit code `0`（`inventory-run-example.log` が ignored）
  - fail-closed 条件: exit code 非 0（tracked or 未 ignore）
- 例:
```bash
if ! git check-ignore -q -- .helix/audit/inventory-run-example.log; then
  echo "FAIL: inventory-run-*.log is not ignored";
  exit 1;
fi
```
- `.helix/audit/redaction-denylist.local.yaml` が tracked でないことを fail-closed チェック
- `inventory-once.sh` 実行ログに対し `gitleaks detect` を事後実行
  - **Step 1**: 検出要約を生成（`rule_id, file, line_redacted, raw_log_sha256, detected_at, head_sha, script_hash`）
  - **Step 2**: `raw` 検出結果は redaction 適用後、`.helix/audit/preflight-gitleaks-summary.log`（tracked）へ追記
  - **Step 3**: `inventory-once.sh` raw log は `~/.helix/quarantine/inventory-run-<head_sha>-<timestamp>.log`（mode 0600、90日保管）へ退避、または `AUDIT_QUARANTINE=disabled` で即時破棄
  - **Step 4**: Phase 0 preflight は PM 確認まで **fail-closed**（停止）
- `inventory-once.sh` の完了時、再現可能性（head_sha + script hash + DB snapshot）を保持

### Phase A0: Discovery（棚卸し）

#### 4.2.1 実行範囲
- manual scripts のみで candidate を抽出
- destructive 操作を含まない
- A0 で新規 CLI は作らない

#### 4.2.2 収集成果
- `.helix/audit` 配下候補生成物（redacted 追跡前提）を収集
  - `.helix/audit/{orphans,refactor-candidates,integrity-breaks}.md`
  - `.helix/audit/decisions.yaml`
  - `inventory-once.sh`
  - `.helix/audit/inventory-summary-<head_sha>-<timestamp>.log`（検出 summary + 統計 + redaction 適用済み）
- raw 生ログ（repo 外、never tracked）を分離保管
  - `~/.helix/quarantine/inventory-run-<head_sha>-<timestamp>.log`（mode 0600、Tier A）

#### 4.2.3 fail-safe と初期 triage
- 候補は初期状態を `triaged` とし、A1 分類前提で保持
- `decisions.yaml` の初期化は再現可能な形で実施
- `gitleaks` 検出が残る場合は分類対象を凍結、再実行条件を明記

### Phase A1: Classification

#### 4.3.1 分類ルール
- `decisions.yaml` に `candidate` / `metadata` / `classification` / `evidence` を保持
- 分類状態：`triaged` → `classified`
- `classified` 結果は `keep/remove/merge/deprecate` のいずれか
- 不明確は `triaged` を維持し、G-3 完了条件に影響

#### 4.3.2 正本同一性
- G3 までに `docs/design/A1-source-of-truth.md` を作成・凍結する（本 PLAN の L2/L3 必須成果物）
  - 正本: `decisions.yaml`（source of truth）
  - import 方向: `decisions.yaml` → `audit_decisions`（一方向、逆書き戻し禁止）
  - 衝突時挙動: `4.3.3` の衝突マトリクス採用（Case A/B/C）
  - verify-sync: G4 で `helix audit verify-sync` を実行し、`import 0 件` を保証
  - DB 制約対応表: A1 validator の reject 条件 ↔ DB CHECK 条件の 1:1 対応
- `decisions.yaml` import は dry-run 先行を前提

#### 4.3.3 scope_hash / idempotency key
- A1 import の主キーは次式
  - `idempotency_key = (candidate_id, schema_version, scope_hash)`
- `schema_version` と `scope_hash` を必須化
- 同一キー衝突挙動（G3 凍結）:
  - Case A: 同一 `(candidate_id, schema_version, scope_hash)` + 同一 `decision_hash` → no-op
  - Case B: 同一 `(candidate_id, schema_version, scope_hash)` + 異なる `decision_hash` → active 降格 + 再 insert
  - Case C: 異なる `scope_hash` → active 降格 + 新規 active insert
- `docs/design/A1-validator-db-constraints-map.md` は、Case A/B/C の挙動を以下 2 層制約に分解して反映する
  - active uniqueness（`idx_audit_decisions_active_unique`）
  - event uniqueness（`idx_audit_decisions_event_unique`）

#### 4.3.4 A1 の成果物
- `docs/design/A1-decisions-schema.yaml`
- `docs/design/A1-validator-spec.md`
- `docs/design/A1-state-transition-tests.md`
- `docs/design/A1-validator-db-constraints-map.md`（A1 validator ↔ DB 制約の 1:1 対応）
- `docs/design/A1-dry-run-procedure.md`
- `docs/design/A1-source-of-truth.md`
- `decisions.yaml`（source）と `decisions-yaml-dry-run-import.log`

### L1 設計

#### 4.4.1 要件
- `docs/requirements/L1-requirements.md`
- A0/A1 の受入条件とゲート接続
- Scope が変わる場合の再ベースライン方式を前提仕様化

#### 4.4.2 受入
- A1 classified は `scope` 内 100% 到達を前提
- triaged 残存は G-3 fail とする（再ベースライン可能かを再検討）
- PO deferred 型は G-3 pass としない

### L2 設計（D-DB / D-AUDIT）

#### 4.5.1 L2 設計内容
- `D-DB`：`audit_decisions` 監査テーブルの v8 構成
- `D-AUDIT`：`decisions.yaml` と監査 DB の同期要件を固定
- 外部依存
  - gitleaks / redaction を必須前提
  - L4 以降で keyring/tiktoken は触らない（PLAN-003 側へ委譲）
- ハッシュ正規化規則（追加）
  - `hash_algorithm: SHA-256`
  - `canonical_format`: `yaml.safe_load` 後、`json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` を UTF-8 bytes 化してハッシュ
  - `source_hash`: `decisions.yaml` ファイル全体（redaction 適用後）
  - `decision_hash`: 1件 decision エントリを redaction 適用後で以下フィールドでハッシュ化
    - `{candidate_id, schema_version, scope_hash, decision, evidence, rationale, fail_safe_action}`
    - `status/import_run_id/created_at/updated_at/imported_at/source_hash` は除外
  - hash 計算順序: 入力 YAML → redaction 適用 → canonical 化 → SHA-256
  - `redaction` は DB 保存とログにも redaction 適用後値を格納
  - pre-redaction 完全性検証は PLAN-002 では未実施（必要なら PLAN-003 で HMAC を追加検討）
  - `hash_version: 1` を固定（将来変更時は `decision_hash_version` 追加で破壊的変更を検知）

### L3 詳細

#### 4.6.1 DDL 断片（本 PLAN に含める棚卸し範囲）
```sql
CREATE TABLE IF NOT EXISTS import_runs (
  id TEXT PRIMARY KEY,
  started_at INTEGER NOT NULL,
  source_hash TEXT NOT NULL,
  scope_hash TEXT NOT NULL,
  completed_at INTEGER,
  imported_rows INTEGER NOT NULL DEFAULT 0,
  error_summary TEXT,
  status TEXT NOT NULL CHECK(status IN ('started', 'success', 'failed'))
);

CREATE TABLE IF NOT EXISTS audit_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  scope_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'historical')),
  import_run_id TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  decision_hash TEXT NOT NULL,
  imported_at INTEGER NOT NULL,
  decision TEXT NOT NULL CHECK(decision IN ('keep', 'remove', 'merge', 'deprecate')),
  rationale TEXT NOT NULL,
  evidence TEXT NOT NULL,
  fail_safe_action TEXT NOT NULL CHECK(fail_safe_action IN ('skip', 'quarantine', 'manual_review')),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE RESTRICT,
  CHECK(created_at <= updated_at)
);

CREATE INDEX IF NOT EXISTS idx_audit_decisions_scope
  ON audit_decisions (scope_hash);
CREATE INDEX IF NOT EXISTS idx_audit_decisions_schema
  ON audit_decisions (schema_version);
CREATE INDEX IF NOT EXISTS idx_audit_decisions_updated
  ON audit_decisions (updated_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_decisions_active_unique
  ON audit_decisions(candidate_id, schema_version)
  WHERE status = 'active';
CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_decisions_event_unique
  ON audit_decisions(candidate_id, schema_version, scope_hash, decision_hash);
CREATE INDEX IF NOT EXISTS idx_audit_decisions_import_run_id
  ON audit_decisions (import_run_id);

CREATE INDEX IF NOT EXISTS idx_import_runs_id_status
  ON import_runs(status);

-- 不変条件
-- 同一 (candidate_id, schema_version) で status='active' は最新 scope_hash の 1 行のみ
-- scope_hash 変更時は旧 active 行を historical 降格し、新 active 行を INSERT
-- 同一 (candidate_id, schema_version, scope_hash, decision_hash) での重複 insert を禁止
```

#### 4.6.2 migration
`helix.db` migration は v8 へ段階的適用を採用。preflight は以下で固定する。
- **Step 1a**: `schema_version` テーブル存在確認
  - 存在時: **Step 2**
  - 欠落時: **Step 1b**
- **Step 1b**: `sqlite_master` の user table 有無を確認
  - `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';`
  - 0 行（ユーザーテーブルなし）: 新規 DB として `v8` で初期化
  - 1 行以上: fail-closed。`~/.helix/quarantine/helix.db.legacy-<timestamp>` へ backup 後、`docs/runbook/legacy-db-repair.md` 参照の手順で手動 repair へ誘導
- **Step 2**: `SELECT MAX(version) FROM schema_version` を評価
  - `current > 8` → **fail-closed**（downgrade 禁止）
  - `current == 8` → **no-op**
  - `1〜7` → v8 まで逐次 migration
- **Step 3（任意）**: version gap 検出時は warning ログ化（fail-closed しない）
- `preflight` は `CURRENT_SCHEMA_VERSION == 7` 固定文言を使用しない
- `schema_version` 重複検出は採用しない（`version` は PRIMARY KEY で重複不可）
- `decisions.yaml` の `metadata.schema_version` 重複検査は A1-validator 独立節へ移設
- `D-DB-MIGRATION.md` を更新し、対象バージョン行列と rehearsal 必須を明記する（v8 前提）
- migration block は `cli/lib/helix_db.py` に `CURRENT_SCHEMA_VERSION = 8`, `_migrate_audit_decisions_v8`, `_migrate_import_runs_v8`, `migrate()` v8 分岐として統合
- migration 時は `PRAGMA foreign_keys = ON;` を必須実行し、rehearsal では `scripts/migration/v8-rehearsal.sh`（人手起動の補助）を使用
- `context_warnings` / `dep_review_log` は追加せず、PLAN-003 の対象として扱う。
  - 対象バージョン行列（G3 凍結）:
    | 開始バージョン | 期待動作 | rehearsal 必須 |
    |---|---|---|
    | non-empty DB + schema_version 欠落 | fail-closed | ◯ |
    | 0 (空 DB) | v8 で初期化 | ◯ |
    | v1 | v1 → v8（逐次） | ◯ |
    | v4 | v4 → v8（逐次） | ◯ |
    | v6 | v6 → v8（逐次） | ◯ |
    | v7 | v7 → v8 | ◯ |
    | v8 | no-op | ◯ |
    | v9+ | fail-closed | ◯ |
- 既存 DB 破壊を避けるため、追加のみ（downgrade はなし）。

#### 4.6.3 テスト
- **P1 fixture（必須）**
  - `scope_hash` 更新で同一 `(candidate_id, schema_version)` の複数 `active` が作成されない（partial unique index）
  - import run は started / success / failed の境界を分離し、失敗時 rollback 後の `failed` 永続化を検証
    - Step1 started commit
    - Step2 decisions insert/update commit/rollback
    - Step3/4 import_runs status 更新で `completed_at` / `imported_rows` / `error_summary` を更新
  - 並行実行時にロールバックされることを検証
- **P2 fixture（必須）**
  - 同一キー衝突の 3 ケース（Case A/B/C）を検証
    - Case A: 同一キー + 同一 `decision_hash` → no-op
    - Case B: 同一キー + 異なる `decision_hash` → active 降格 + 再 insert
    - Case C: 異なる `scope_hash` → active 降格 + 新規 active insert
  - `import_runs` との FK 連結で孤立行を作れないこと
  - `failed` 時に `failed` 行が残存し、`audit_decisions` が空であることを検証
  - 同一トランザクションで import_run と decision の INSERT を行わない仕様を検証
  - `error_summary` が redaction 適用済みの情報で記録されることを検証
- 空 DB / v7 DB / old DB（legacy v6 など）での forward migration
- L3 追加: v1/v4/v6/v7/current から v8 への migration rehearsal を追加し、version gap を warning ログとして検証
- `backup` + `restore` 手順を添付
- redaction 対象カラムの検証
- hash 正規化 fixture（必須）
  - 同一 decision エントリで `decision_hash` が同一になる
  - YAML フィールド順序差分が hash 結果を変えない
  - YAML 引用符/改行差分が hash 結果を変えない

### L4 実装

#### 4.7.1 Sprint 1（A1）
- A1 状態機械 + dry-run import の production 化
- `decisions.yaml` 同期 CLI / validator 基礎の実装
- L4 での実装対象は人間判断を伴わず deterministic に完了できるもの

#### 4.7.2 Sprint 2
- `cli/lib/helix_db.py` に v8 ブロックを追加
  - `CURRENT_SCHEMA_VERSION = 8`
  - `_migrate_audit_decisions_v8()`
  - `_migrate_import_runs_v8()`
  - `migrate()` へ v8 分岐追加
- `cli/lib/tests/test_helix_db.py` に migration テスト追加（v0, v1, v4, v6, v7, v8, v9+）
- `scripts/migration/v8-rehearsal.sh` を追加し、各開始バージョンの rehearsal をオフライン再現実行
- `docs/design` 成果物整備（D-DB-MIGRATION-PLAN / テスト観点追記）

#### 4.7.3 Sprint 3-5
- `PLAN-003` へ分離した auto-restart 項目を実装しないため、棚卸し範囲で完了可能な統合のみ

### L6 検証
- L1/L2/L3 の整合確認
- `decisions.yaml` dry-run import を 100% 判定し、G-3 前提を満たすことを確認
- migration rehearsal（empty/current/old）
- fresh checkout 系では HOME DB 検証は未対象（PLAN-003 へ移管）

### L7 デプロイ
- `.gitignore` パッチ、設計成果物、検証結果の最終整合を確認
- 既存 CI / チェックリストへ棚卸し範囲を明示追加
- 本 PLAN 実装物の移譲ポイントを PLAN-003 に明示

### L8 受入
- Phase 0 preflight と A0/A1 が完了した状態で実施
- 受入条件は以下を満たすこと
  - G-1 〜 G-7 の満了
  - `decisions.yaml` と `audit_decisions` の照合差分が許容されないこと
  - triaged 残留時は G-3 fail かつ PLAN-003 へ明示的に移譲
  - plan 内で除外した auto-restart 項目の責任範囲を明文化

## 5. ゲート

### G1
- TL レビュー条件に対する成立条件と証拠の存在確認
- phase.yaml に preflight 承認状態を記録

### G2
- gate-policy.md §G2 必須条件を参照: 要件トレース・ADR・データフロー・threat-model・adversarial-review・ミニレトロ・security①  
  （[skills/tools/ai-coding/references/gate-policy.md §G2](../../skills/tools/ai-coding/references/gate-policy.md#G2)）
- 本 PLAN 固有条件は追加条件として分離:
  - gitleaks license/version install の承認証跡
  - Phase 0 preflight ログの存在（`docs/plans/PLAN-002-phase0-preflight.md`）
- [追加] `.gitignore` allowlist 検証ログ（tracked fail-closed）を提出

### G3
- gate-policy.md §G3 必須条件を参照: Schema Freeze、API Freeze（棚卸しは `N/A` 明記）、テスト設計、WBS、migration/rollback 準備、事前調査  
  （[skills/tools/ai-coding/references/gate-policy.md §G3](../../skills/tools/ai-coding/references/gate-policy.md#G3)）
- 本 PLAN 固有条件は追加条件として分離:
  - `A1 classified` 100% 到達
  - `scope_hash` 凍結・`scope_hash` 変更時の migration テスト
  - `audit_decisions` + `import_runs` DDL freeze（`status/import_run_id/source_hash/decision_hash/imported_at/completed_at/imported_rows/error_summary` 追加、`audit_decisions` `schema` 更新）
  - import_runs status は `started` / `success` / `failed` を受理
  - `error_summary` は redaction 適用済みで保存
  - `4.3.3` 衝突マトリクス（Case A/B/C）を G3 凍結条件に追加
  - `scope_hash` 変更時の preflight/dry-run 条件
  - `decisions.yaml` の schema freeze と import 前提条件
  - `docs/design/A1-source-of-truth.md` 作成・G3 凍結（L2/L3 必須）

### G4
- gate-policy.md §G4 必須条件を参照: CI、回帰、security②、debt 証跡、ミニレトロ  
  （[skills/tools/ai-coding/references/gate-policy.md §G4](../../skills/tools/ai-coding/references/gate-policy.md#G4)）
- 本 PLAN 固有条件は追加条件として分離:
  - `decisions.yaml`↔`audit_decisions` import-sync 証跡
  - `import` 0 件時保証（`import 0 件` の import-sync 成果を提出）
  - `imported_at` と `import_runs` 運用ルールの追跡

### G5
- UI 関連は対象外（skip）

### G6
- L4 での実装 + migration rehearsal が完了
- rollback / backup が実施可能

### G7
- PLAN-003 への移譲項目一覧が未完了でないことを確認
- 依存境界（PLAN-003 開始条件）を明文化

## 6. 成果物表

| フェーズ | 成果物 | 目的 | 保存先 |
| --- | --- | --- | --- |
| Phase 0 | `docs/plans/PLAN-002-phase0-preflight.md` | gitleaks/ .gitignore/redaction 前提 | docs/plans |
| Phase 0 | `.gitignore` 更新 | `redaction-denylist.local.yaml` の追跡防止 | .gitignore |
| Phase 0 | `.helix/audit/redaction-denylist.example.yaml` | 非秘匿 denylist 共有 |
| Phase 0 | `.helix/audit/redaction-denylist.local.yaml` | local denylist（実運用） |
| A0 | `.helix/audit/{orphans,refactor-candidates,integrity-breaks}.md` | candidate 抽出 | .helix/audit |
| A0 | `.helix/audit/decisions.yaml` | classification source-of-truth |
| A0 | `.helix/audit/inventory-once.sh` | manual script |
| A0 | `.helix/audit/inventory-summary-<head_sha>-<timestamp>.log` | 再現性サマリ（redacted） |
| A0 | `~/.helix/quarantine/inventory-run-<head_sha>-<timestamp>.log` | raw 生ログ（never tracked） |
| A1 | `docs/design/A1-decisions-schema.yaml` | schema 定義 |
| A1 | `docs/design/A1-validator-spec.md` | 検証仕様 |
| A1 | `docs/design/A1-state-transition-tests.md` | 状態遷移テスト |
| A1 | `docs/design/A1-dry-run-procedure.md` | dry-run 手順 |
| A1 | `docs/design/A1-source-of-truth.md` | 正本同一性定義（G3 までに作成・凍結） |
| A1 | `docs/design/A1-validator-db-constraints-map.md` | validator と DB 制約対応表 |
| A1/L2 | `decisions-yaml-dry-run-import.log` | import 監査 |
| L3 | `docs/design/D-DB-MIGRATION-PLAN-002-Inventory.md`（新規） | v8 migration 詳細 |
| L3 | `docs/design/D-DB-MIGRATION.md`（更新） | migration 方針 |
| L4 | `cli/lib/helix_db.py` | `CURRENT_SCHEMA_VERSION = 8` と v8 migration block |
| L4 | `cli/lib/tests/test_helix_db.py` | v0 〜 v9+ 向け migration/rehearsal テスト |
| L4 | `scripts/migration/v8-rehearsal.sh` | 逐次 migration rehearsal 補助（人力起動） |
| L6 | migration rehearsal レポート | empty/current/old DB |
| L6 | G1.5 対象除外の再確認レポート | テスト境界明示 |
| L7 | チェックリスト連携 | CI / release note |
| L8 | L8 受入シート | G1〜G7、A1 完了条件 |

## 7. 想定外作業
- 本 PLAN で収集できない要件（B/C/D 自動再開領域）は PLAN-003 を起点に起票
- `docs/design/A1-source-of-truth.md` は本 PLAN（G3）で作成・凍結する（PLAN-003 起動前提にはしない）
- `.helix/audit/decisions.yaml` の形式差異が発見された場合は、L2 設計更新の範囲内で調整

## 8. 変更リスク

### 8.1 リスク一覧
- R-1: A1 分類精度の揺れ
  - 対応: triaged 100% ではなく classified 100% のみを通過条件化
- R-2: `scope_hash` 不一致
  - 対応: 再ベースライン規則を固定、旧エントリは歴史保持
- R-3: `decisions.yaml` と `audit_decisions` 同期ズレ
  - 対応: import/sync を idempotency key 鍵付きで厳密化
- R-4: preflight 省略再開
  - 対応: gitleaks/preflight / redaction ログ検証の失敗時は fail-closed
- R-5: PLAN-003 起動時の引き継ぎ齟齬
  - 対応: 成果物表に移行対象を明示し、L8 受入で依存を検証

## 9. 改訂履歴

| 日付 | バージョン | 変更内容 |
| --- | --- | --- |
| 2026-04-30 | v6 | readiness retro 反映（PLAN-004 v5 連動） |
| 2026-04-29 | v5 | TL レビュー P1×3 + P2×2 反映（`.gitignore` 判定反転、`audit_decisions` 2層制約、import_runs rollback 方針分離、schema_version 欠落 preflight fail-closed、hash redaction 対象変更） |
| 2026-04-29 | v4 | TL P1×2 + P2×3 反映（raw log と redacted 分離、migration preflight 再定義、migration スコープ統一、same-scope 再 import 衝突ケースの明文化、A1 source-of-truth の G3 作成・凍結方針追加） |
| 2026-04-29 | v3 | TL レビュー P1×3 + P2×3 の v3 反映（partial unique index、逐次 migration、CLI `helix_db.py` への v8 ブロック接続、FK 追加、hash 正規化、gitleaks 再実行可否手順） |
| 2026-04-29 | v2 | TLレビュー P1×3 + P2×3（G2/G3/G4、migration、scope_hash、HMAC 移管、パス統一、証跡追加）を反映 |
| 2026-04-29 | v1 | PLAN-002 v34 を棚卸し基盤のみに分割。Phase 0 + A0/A1 + `audit_decisions` をPLAN-002（新）へ固定し、auto-restart 領域を PLAN-003 へ委譲 |

## 10. 付録

### 10.1 今後の連携
- PLAN-003 は `PLAN-002` の完了を前提とし、AUTO-RESTART 関係（`worktree_snapshot_hash` など）を引き継ぐ。
- `docs/plans/PLAN-002-helix-fullauto-foundation.md` は履歴アーカイブとして参照対象にとどめ、編集・削除しない。
- `docs/research/B-feasibility.md` / `docs/research/D-feasibility.md` の再検討方針は PLAN-003 側で再記録。
