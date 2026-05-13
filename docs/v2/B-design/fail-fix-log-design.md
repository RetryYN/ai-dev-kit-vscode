# fail-fix-log 設計書 (FR-GR11: 穴を埋める原則の構造化)

*Status*: draft (implementation-ready)
*Owner*: Docs role
*Scope*: HELIX v2 Phase 3〜F
*Source of truth references*: `docs/v2/L1-REQUIREMENTS.md`, `docs/v2/B-design/l2-master-sketch.md`, `skills/workflow/incident/SKILL.md`, `.helix/audit/deferred-findings.yaml`
*Created*: 2026-05-14

## 0. 背景と原則

### 0.1 目的

この設計は、V2 の「失敗したら終了しない」実行原則を実装レベルへ落とし込むための永続化スキームを定義する。

- 失敗の検知 (`detector` / hook / lint / gate / manual) を DB に構造化して記録する。
- 検知情報に対する対策 (`memory` / `documentation` / `structural_fix` 等) を設計上紐付ける。
- `occurrence_count` を使って再発を可視化し、再発時に自動対策に繋ぐ。
- `deferred-findings.yaml` の carry を `status='open'` として引き継ぎ、閉域化まで追跡可能にする。

### 0.2 原則

1. **記録だけでなく対策を強制**: `fail_fix_log` は「起点」ではなく「再発防止サイクル」の起点とする。
2. **再発観測**: 同根因は `occurrence_count` を上げて再発兆候を検知する。
3. **CLI 第一級の入口**: すべての起票・更新を `helix incident` へ集中。
4. **フック経路の自動化**: PostToolUse / pre-commit / gate / scan tool を失敗検知と接続。
5. **memory との共進化**: `memory_feedback` から発生した事象は `fail_fix_log` に反映し、しきい値超で再起票を推奨。

### 0.3 設計範囲

適用対象:

- `docs/v2/L1-REQUIREMENTS.md` の FR-GR11。
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_helix_fill_holes_principle.md`
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_codex_completion_vs_actual_output.md`
- `.helix/audit/deferred-findings.yaml`
- `skills/workflow/incident/` 配下の incident 機能セット

適用対象外:

- 本番 DB など他アプリケーションの独立監査基盤。
- 外部監視 SaaS への直接連携 (次フェーズで API リレーを追加可能)。

## 1. 既存資産と課題整理

### 1.1 既存の記録点

- `helix` 側には既存で `deferred-findings.yaml` が存在し、carry 対応の決済待ち事項を保持。
- hook・hooker の自動収集は存在するが、**失敗分類の一元的 schema** が不足。
- `feedback_*` は人間理解向け記憶として存在するが、再現処理・再発防止を実装で使い回す構造が弱い。
- incident ワークフローは存在するが、表層的な実行ログに集中しやすく、`event_kind` 別ライフサイクル・再発監視が不足。

### 1.2 問題と解決

| 問題 | 現在状態 | 解決方針 |
|---|---|---|
| 事象と対策が分散 | memory, deferred-findings, コード実装の hook で分裂 | `fail_fix_log` を hub 化し全てを同一 schema に集約 |
| 再発の定量化不足 | `resolved` で終端されることが多い | `occurrence_count` / `mitigated_at` / `resolved_at` を保持 |
| KPI 可視化不足 | dashboard は主に gate 監査中心 | `helix detect dashboard` / `report dev-state` に fail_fix 指標を追加 |
| 構造化不整合 | 命名の揺れ / 運用ルールの穴 | `event_kind` / `severity` / `mitigation_kind` に CHECK 制約 |
| file write 失敗の監視欠落 | `completion` 成功でも実ファイル不在の事例 | FR-GR11 の `doc_artifact_missing` と起点を直接 log 化 |

### 1.3 参照先一覧（内部リンク）

- [docs/v2/L1-REQUIREMENTS.md](docs/v2/L1-REQUIREMENTS.md)
- [feedback_helix_fill_holes_principle.md](~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_helix_fill_holes_principle.md)
- [feedback_codex_completion_vs_actual_output.md](~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_codex_completion_vs_actual_output.md)
- [skills/workflow/incident/SKILL.md](skills/workflow/incident/SKILL.md)
- [.helix/audit/deferred-findings.yaml](.helix/audit/deferred-findings.yaml)

## 2. SQL スキーマ設計 (§1)

### 2.1 fail_fix_log DDL

```sql
CREATE TABLE IF NOT EXISTS fail_fix_log (
  id INTEGER PRIMARY KEY,
  event_kind TEXT NOT NULL CHECK (event_kind IN (
    'codex_completion_no_output',
    'doc_artifact_missing',
    'detector_false_positive',
    'gate_fail_close',
    'codex_role_misdispatch',
    'lint_failure',
    'security_scan_finding',
    'dependency_vulnerability',
    'test_flaky',
    'hook_failure',
    'memory_drift',
    'manual_incident',
    'other'
  )),
  severity TEXT NOT NULL CHECK (severity IN ('P0','P1','P2','P3')),
  title TEXT NOT NULL,
  context_json TEXT,
  root_cause TEXT,
  mitigation_kind TEXT CHECK (mitigation_kind IN (
    'scan_tool',
    'external_tool',
    'structural_fix',
    'hook',
    'detector',
    'memory_feedback',
    'documentation',
    'workaround',
    'not_planned'
  )),
  mitigation_ref TEXT,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','investigating','mitigated','resolved','wontfix')),
  source TEXT,
  related_axis TEXT,
  related_fr TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  mitigated_at TEXT,
  resolved_at TEXT,
  occurrence_count INTEGER NOT NULL DEFAULT 1,
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fail_fix_kind_status ON fail_fix_log(event_kind, status);
CREATE INDEX IF NOT EXISTS idx_fail_fix_severity_status ON fail_fix_log(severity, status);
CREATE INDEX IF NOT EXISTS idx_fail_fix_created ON fail_fix_log(created_at);
CREATE INDEX IF NOT EXISTS idx_fail_fix_related_axis ON fail_fix_log(related_axis);
CREATE INDEX IF NOT EXISTS idx_fail_fix_occurrence ON fail_fix_log(occurrence_count);
```

### 2.2 データ型・表現設計

- `id`: DB 内部の識別子。追加時のみ採番。
- `event_kind`: 失敗種別の列挙。
- `severity`: 4 段階 (P0 が最重)。
- `title`: 1 行でわかる短文。
- `context_json`: 発生 task、対象ファイル、error msg、エグゼキュータ情報など。
- `root_cause`: 根本原因 (free text)。
- `mitigation_kind`: 施策分類。未確定なら NULL。
- `mitigation_ref`: 施策参照 (`FR-` / `PR-` / memory file / commit SHA)。
- `status`: オープン状態。
- `source`: どの経路で起票されたか (`auto-log`, `manual`, `hook`, `detector`)。
- `related_axis`: detector axis などの関連キー (`axis-11` など)。
- `related_fr`: 関連 FR-XX。
- `created_at` / `mitigated_at` / `resolved_at`: 時系列。
- `occurrence_count`: `related_root_cause` が再発した回数を蓄積。
- `last_seen_at`: 最終再発時刻。`created_at` とは独立運用する。

### 2.3 非正規化/拡張方針

- v2 導入フェーズでは `context_json` のみ JSON 字句を文字列保存。
- 将来は `context_kind`, `actor`, `run_id`, `axis_category`, `sla_deadline_at` を独立列に拡張。
- `source` は `hook` / `detector` / `cli` / `manual` を想定。将来 `agent` / `ci` 追加可能。

### 2.4 インデックス戦略

- 稼働監視: `idx_fail_fix_created`, `idx_fail_fix_occurrence`
- 運用監査: `idx_fail_fix_kind_status`, `idx_fail_fix_related_axis`
- 分析: severity と status の複合参照、related_fr での絞込を高頻度使用。

## 3. CLI 仕様設計 (§2)

### 3.1 コマンド仕様

```
# 手動 log
helix incident log --kind <kind> --severity P1 --title "..." \
  --context '{...}' --root-cause "..." --mitigation-kind structural_fix \
  --mitigation-ref FR-GR11 --source manual --related-axis axis-11 --related-fr FR-GR11

# 一覧
helix incident list [--status open] [--severity P1] [--kind ...] [--days 30]

# 詳細
helix incident show <id>

# 状態遷移
helix incident mitigate <id> --ref <PR/commit/memory>
helix incident resolve <id> --ref <PR/commit/memory>

# 集計
helix incident stats [--by kind|severity|month]

# 同一事象の occurrence count 増加
helix incident bump <id>
```

### 3.2 argparse 互換インターフェース定義 (設計目標)

**主コマンド**: `helix incident`

- `log`: `--kind`, `--severity`, `--title`, `--context`, `--root-cause`, `--mitigation-kind`, `--mitigation-ref`, `--source`, `--related-axis`, `--related-fr`, `--dry-run`
- `list`: `--status`, `--severity`, `--kind`, `--days`, `--axis`, `--fr`, `--limit`, `--offset`, `--json`
- `show`: `id`
- `bump`: `id`
- `mitigate`: `id`, `--ref`
- `resolve`: `id`, `--ref`
- `stats`: `--by`, `--days`, `--json`, `--csv`

### 3.3 返却仕様

#### list

```
[entries]
- id
- title
- event_kind
- severity
- status
- source
- occurrence_count
- created_at
```

#### show

- 全カラムと `context_json` を整形して表示。
- `context_json` が大きい場合は先頭 4KB + `--full` で全件。

#### stats

- `--by kind`:
  - `kind`, `open_count`, `mitigated_count`, `resolved_count`, `open_occurrences`
- `--by severity`:
  - `severity`, `avg_occurrence_count`, `open_rate`
- `--by month`:
  - 月次起票数、未解決率、解決率。

### 3.4 エラー処理

- 不明な `kind` / `severity` / `mitigation_kind` は **exit 2**。
- `id` が存在しない場合は **exit 3**。
- `mitigate/resolve` が既に完了済みなら **idempotent に no-op + warning**。

### 3.5 CLI と既存 skill の整合

- `skills/workflow/incident/SKILL.md` の運用をベースにし、`status` ライフサイクルを `open -> investigating -> mitigated -> resolved` または `wontfix` に収束。
- CLI は `incident` で `--json` をサポートして `helix` の自動テストで検証可能にする。

## 4. auto-log 経路設計 (§3)

### 4.1 概要

`fail_fix_log` は各種発火源から構造化ログを受ける。

- PostToolUse
- pre-commit
- helix gate
- security scan
- dependency audit
- bats/hook 失敗

### 4.2 受信イベント種別マッピング

| 受信元 | 検知条件 | event_kind |
|---|---|---|
| PostToolUse | `files: []` かつ `codex` completion で作業 file が実体なし | `codex_completion_no_output` |
| pre-commit | lint fail | `lint_failure` |
| helix gate | axis fail |
| hook | detector confirmed false positive として再分類 | `detector_false_positive` |
| helix gate | gate fail-close 対象
| helix gate | 直接 fail close (軸要件不整合) | `gate_fail_close` |
| gitleaks/semgrep | security findings | `security_scan_finding` |
| pip-audit/npm-audit | dependency vulnerability | `dependency_vulnerability` |
| pytest/bats | unstable fail pattern | `test_flaky` |
| hook failure | hook 実行エラー
| hook failure |
| 予期しない入力差分 | memory drift | `memory_drift` |
| 手動 | 運用レビューでの追記 | `manual_incident` |

### 4.3 イベントルーター疑似コード

```python
# pseudo

def route_auto_log(event):
    if event.source == 'post_tool_use' and event.kind_hint == 'no_output':
        kind = 'codex_completion_no_output'
    elif event.source == 'pre_commit' and event.subkind == 'lint_failed':
        kind = 'lint_failure'
    elif event.source == 'gate' and event.hard_close:
        kind = 'gate_fail_close'
    elif event.source == 'detector' and event.confirmed_false_positive:
        kind = 'detector_false_positive'
    elif event.source == 'detector' and event.critical:
        kind = 'gate_fail_close'
    elif event.source == 'security_scan':
        kind = 'security_scan_finding'
    elif event.source == 'dependency_audit':
        kind = 'dependency_vulnerability'
    elif event.source == 'test' and event.flaky:
        kind = 'test_flaky'
    elif event.source == 'hook' and event.hook_failed:
        kind = 'hook_failure'
    elif event.source == 'memory':
        kind = 'memory_drift'
    else:
        kind = 'manual_incident'

    emit_fail_fix_log(kind, event)
```

### 4.4 検出しきい値

- `event_kind` ごとに severity 初期値を設定。
- `root_cause` 参照一致 (`hash(context_json)` + `title` 正規化) で既存レコードを検知。
- 同一 key がある場合は `occurrence_count += 1` + `last_seen_at = now` + `status` を維持/更新。

### 4.5 受理後の状態遷移

- 新規: `open`
- 調査中: `investigating`
- 対策投入済: `mitigated` (`mitigated_at` 記録)
- 解決: `resolved` (`resolved_at` 記録)
- 対応せず: `wontfix` (要理由)

## 5. memory 連携設計 (§4)

### 5.1 双方向連携

- memory フィードバック検知時:
  1. `event_kind='manual_incident'` もしくは事象別 kind に起票
  2. `mitigation_kind='memory_feedback'`
  3. `mitigation_ref=<memory file path>`

- `occurrence_count >= 3` の場合:
  - 自動で記録に対する再提起フラグを設定
  - `helix report dev-state --include incidents` で alert
  - 開発者導線に「memory feedback 推奨」表示

### 5.2 memory_feedback ファイルマッピング

- `feedback_helix_fill_holes_principle.md`: FR-GR11 の原則と対応。
- `feedback_codex_completion_vs_actual_output.md`: `codex_completion_no_output` / `doc_artifact_missing` 対策。

### 5.3 運用手順

1. 重要再発 (P1以上 or occurrence>=3) の場合、memory に 1 件以上の永続記録を追加。
2. memory 追加後、`helix incident log` で `mitigation_kind=memory_feedback` を設定。
3. 次回同種事象で `bump` が自動/半自動で働く。

## 6. deferred-findings との統合 (§5)

### 6.1 統合方針

- `.helix/audit/deferred-findings.yaml` の unresolved finding を起票時に `status='open'` の `fail_fix_log` へ反映。
- `findings[*].id` を `mitigation_ref`/`root_cause` に記録。
- 逆方向として、`resolve` 時は audit 側を `status: resolved` に変換可能。

### 6.2 同期処理定義

1. 起動時: `deferred-findings.yaml` を読み取り、未解決 item を `fail_fix_log` へ差分マージ。
2. 差分条件:
   - `source = carry`
   - `plan_id`, `phase`, `title` が一致しないかをキー判定。
3. 競合条件:
   - 既存同一 root-cause の場合は `occurrence_count` を加算。
   - 既存レコードが解決済みなら再発防止の意図により open へ戻さない。
4. 監査追跡:
   - `source='manual'` で起票したもので carry 由来かどうかは `mitigation_ref` に保持。

### 6.3 同期例

- DF-PLAN-007 の P1 carry: `status=open` として `fail_fix_log` に追加。
- `gate_fail_close` 再発時: 同種 context は `occurrence_count` をインクリメント。

## 7. 既存 capability との統合 (§5)

### 7.1 skills/workflow/incident/

本 skill を SoT とし、`fail_fix_log` を `incident` の主保存テーブル化。

- `incident log` CLI が `fail_fix_log` へ保存。
- `incident list/show/stats` を DB ビューから生成。
- incident の既存運用観点(対応履歴、連絡テンプレ)との整合を保つ。

### 7.2 14 detector 連動

- 軸別検知の失敗時に `source='auto-log'` で起票。
- `related_axis` を `axis-XX` で保存。
- false positive 承認後は `mitigation_kind='detector'` もしくは `documentation`。

### 7.3 hook / pre-commit / gate 連携

- pre-commit: lint/cv / hook 失敗時を `helix incident log` 経由で保存。
- gate: 失敗種別に応じて `event_kind` を差し替え。
- PostToolUse: 実ファイル確認で no-output を検知した場合、`codex_completion_no_output` を auto-log。

## 8. dashboard / report 連携 (§6)

### 8.1 detect dashboard 統合

#### 8.1.1 出力フォーマット（概念）

```text
[Fail & Fix]
  Open: 7 (P0=0, P1=3, P2=2, P3=2)
  Mitigated last week: 4
  Top recurring: codex_completion_no_output (15x)
```

#### 8.1.2 集計定義

- Open: `status IN ('open', 'investigating')`
- `open_by_severity`: `severity` 別の件数。
- `mitigated_last_week`: 最近 7 日間で `mitigated` 遷移件数。
- `top_recurring`: `occurrence_count` 上位。

### 8.2 report dev-state 連携

- `helix report dev-state --include incidents` の追加節:
  - 月次: 起票数、未解決率、平均解決日数。
  - Top recurring: 根本原因上位。
  - mitigation rate: `resolved + mitigated / total`。
  - `P1 解消 SLA`: `median(open->resolved)`。

### 8.3 監視閾値

- P1 open が 5 件を超えたら warning。
- P0 open が存在したら fail-close。
- 一定期間で同一 `event_kind` が 5 回以上再発した場合は report 注記。

## 9. API / DB 連携インターフェース

### 9.1 `helix` からの参照 API（将来）

- `incident` コマンドのほか、`detect dashboard` と `report dev-state` から SQL 参照を追加。
- 将来拡張: `GET /v1/incidents` 系 REST（必要時）。

### 9.2 運用データとテストデータ分離

- 開発時: `.helix/helix.db`
- 本番テスト: CI では分離 DB 使用（`--db-path` オプション想定）。

### 9.3 マイグレーション

- テーブル追加は additive first。
- 既存環境の `pragma table_info(fail_fix_log)` を確認して互換。
- `occurrence_count` の整数型制約。0 以下は許容しない。

## 10. V2 Phase マッピング (§7)

### 10.1 Phase 3: helix.db 拡張

- `fail_fix_log` を schema バージョン要件へ追加。
- index + migration compatibility テストを追加。

### 10.2 Phase 4: 検出ガードレール

- detector / gate auto-log の起票を追加。
- false positive の扱いを `detector_false_positive` として明示。

### 10.3 Phase 5: 自動化

- PostToolUse hook で `files=0` 検知時の自動起票を必須化。
- `helix incident log` への変換レイヤを追加。

### 10.4 Phase F: 可視化

- dashboard と report の集計ロジックへ `fail_fix` 集計を追加。

## 11. イベント種別設計: §3 対応拡張（event_kind と mitigation_kind）

### 11.1 event_kind 選定根拠

| event_kind | 役割 |
|---|---|
| codex_completion_no_output | Codex/Write 実体不一致 |
| doc_artifact_missing | 期待 doc と実体差 |
| detector_false_positive | detector 精度関連 |
| gate_fail_close | gate fail で止まった事象 |
| codex_role_misdispatch | hook route が誤分散 |
| lint_failure | lint 実行失敗 |
| security_scan_finding | シークレット/脆弱性関連 |
| dependency_vulnerability | CVE 等 |
| test_flaky | 不安定テスト |
| hook_failure | hook 自体の失敗 |
| memory_drift | 記憶・知見 drift |
| manual_incident | 運用/レビュー起票 |
| other | 架橋困難な汎用 |

### 11.2 severity 判定ルール（初期値）

- P0: hook block / security / gate hard fail。
- P1: codex completion / doc artifact missing / role misdispatch。
- P2: lint failure / test flaky / dependency。
- P3: その他の情報整理。

### 11.3 mitigation_kind 選定

- scan_tool: 自動掃除で完結可能。
- external_tool: 外部ツール起点。
- structural_fix: 実装・schema・hook 改善。
- hook: hook 側ルール修正。
- detector: detector 側閾値修正。
- documentation: 文書運用改善。
- workaround: 一時回避。
- not_planned: 対応保留。

## 12. 再発・監視ロジック

### 12.1 bump 判定

- `bump <id>` が呼ばれた際:
  - `occurrence_count`++
  - `last_seen_at=now()`
  - `status` が `resolved/wontfix` のときは `investigating` へ戻さない（運用判断者が明示再開）

### 12.2 メトリクス

- `top_recurring`: `ORDER BY occurrence_count DESC`
- `age_days`: `julianday('now') - julianday(last_seen_at)`。
- `stale_open`: `status='open' AND age_days > 14`。

## 13. 初期 seed 設計（§8）

### 13.1 初期エントリ

| id | event_kind | severity | title | mitigation_ref |
|---|---|---|---|---|
| 1 | codex_completion_no_output | P1 | helix codex 完了通知が実 file 出力を保証しない | FR-GR08 / FR-GR11 |
| 2 | codex_role_misdispatch | P2 | --role tl は doc 作成を delegate_to docs 返却 | feedback_codex_completion_vs_actual_output.md |
| 3 | hook_failure | P2 | PMO Sonnet 起動エラー /tmp/test-helix not found | C-followup/pmo-startup-debug.md |
| 4 | doc_artifact_missing | P1 | V2 構築で 20+ doc 不在（完了通知と乖離） | FR-GR08 |

### 13.2 seed 実装アプローチ

- migration 初回時に上記を `INSERT OR IGNORE`。
- `title` の重複を防ぐため、`LOWER(title)` を正規化して比較。
- 将来、`mitigation_ref` が空の場合は `FR-GR11` をデフォルト。

## 14. 検証ステップ (§10)

### 14.1 bats: fail_fix_log CRUD test

- `fail_fix_log` の `CREATE / READ / UPDATE / STATE遷移 / stats` を bats 化。
- 想定ケース:
  - 事象追加
  - 同一 root cause で bump
  - status 遷移の制御
  - by kind の集計

### 14.2 pytest: helix incident CLI test

- `click`/argparse parser を使い、`incident list/show/log/bump/stats` を検証。
- 結果:
  - 正常系: 新規起票、一覧、表示
  - 異常系: 不正引数、存在しない id
  - json フォーマット: `--json` 返却

### 14.3 e2e: codex completion auto-log

- PostToolUse で `files=[]` を再現。
- `codex_completion_no_output` が `status='open'` として挿入されること。
- 既知タイトル同一時に `occurrence_count` が増分されること。

## 15. 非機能要件

### 15.1 パフォーマンス

- 日次で 1000 件規模まで、`incident list` 応答を 300ms 以内 (ローカル SQLite 前提)。
- stats は group by を index 参照前提で実施。

### 15.2 可用性

- コマンド起動失敗時でも hook は原子性を保つ。
- DB 書込失敗は warning のみにし、処理本体は止めない fallback（必要時 hook 停止）。

### 15.3 セキュリティ

- `context_json` には credential, token, secret を redaction 後保存。
- `secret` は `***` 置換。

## 16. リスクと対策

### 16.1 想定リスク

- 事故的な多重起票（同一事象重複）
  - 対策: hash + 根本原因ヒューリスティックで統合。
- false positive 過多
  - 対策: detector false positive ワークフローと manual override。
- 記録量増加
  - 対策: retention 策略と archive。

### 16.2 依存リスク

- incident skill の既存実装に CLI 破壊的変更が入る。
- role 分担の変更に伴う hook 変数の取り違え。
- memory 参照先が再配置される場合。

## 17. TODO 残存チェック

### 17.1 TODO / FIXME

- 本設計内の `TODO` は `0件`。
- 実装前に `rg 'TODO|FIXME' docs/v2/B-design/fail-fix-log-design.md` を実施する。

### 17.2 リンク整合確認

- 最終成果物として以下のリンクを検証:
  - `docs/v2/L1-REQUIREMENTS.md`
  - `skills/workflow/incident/SKILL.md`
  - `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_helix_fill_holes_principle.md`
  - `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_codex_completion_vs_actual_output.md`

### 17.3 受入条件へのマッピング

- FR-GR11 満たす項目:
  - table schema 追加
  - CLI 命令整備
  - auto-log 経路
  - memory feedback 連携
  - incident capability 統合
  - dashboard/report 連携
  - initial entry seed
  - 想定検証ステップ

## 18. 変更履歴

- 2026-05-14: 初版作成（docs role）。FR-GR11 の設計要求を SQL/CLI/運用まで含め、400-600 行仕様として整備。

