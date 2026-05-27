# L5 外部IF詳細設計

- 文書名: `docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md`
- 対象版: HELIX-workflows V2
- 作成日: 2026-05-27
- 担当: docs (L5設計)
- 目的: `CLI 36件 (本文 §2-§9 で完全定義、付録 A は実装状況追跡表) / hook 11件` の入出力契約凍結（argparse / output format / exit code / payload schema / error handling / timeout / retry / blocking）

---

## §0 PLAN reference + scope 宣言

このドキュメントは下記を前提に作成し、対象外範囲を明示する。

- 参照 PLAN: `docs/plans/L5/L5-helix-workflows-外部IF詳細設計plan.md`
- 参照 F設計: `docs/v2/L4-architecture/helix-workflows-functional-design.md`
- 参照 ADR: `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`
- 参照 ADR: `docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md`
- 参照 L9 設計: `docs/v2/L9-test-design/helix-workflows-functional-test-design.md`

スコープは **L5 外部IF（command-line / hook / event schema）に限定**し、
実装ロジック変更・DB migration・新規依存追加は含まない。

本書は以下を**凍結**する。

1. CLI 入力（位置引数、オプション、サブコマンド）仕様
2. 出力形式（text / `--json`）
3. 終了コード規約（0/1/2/domain）
4. 失敗時フェイルポリシー（fail-close / fail-open）
5. hook payload schema
6. audit 連携（role_audit / event_log）
7. timeout / retry / blocking 方針
8. U-01〜U-07c の最終決定（計 9 決定、U-07 は §10.9-10.11 で mutation/migration/coexist event hook に分割）

未スコープ: GUI/API server API 変更、外部 SaaS API 契約、認証基盤変更、PII 処理。

## §1 CLI API 共通ルール

### §1.1 argparse pattern（positional / --flag / --json）

- 共通パターン:
  - `helix <command> [<subcommand>] [args...] [--json] [--verbose] [--timeout N]`
  - `-h/--help` は全コマンドで存在し、対象コンテキストの usage と exit code `0` を返す。
- positional は最小化し、重要スイッチは `--flag` 化。
- 同名フラグは長形式優先、短縮形式は `-h/-v/-n` 等必須時のみ提供。
- Boolean フラグは `--no-xxx` 形式を併設（既定有効時のみ）。
- output 切替フラグ:
  - `--json`: machine-friendly 構造化出力
  - `--pretty`: text フォーマットの整形（既定）
  - `--silent`: 成功時テキスト圧縮、json 利用時は非対応（非互換排除）

### §1.2 出力 format（text default, --json）

- text は 1行 or 多行要約＋人間向けアラートを基本とする。
- `--json` は UTF-8 JSON かつキー順固定:
  - `ok`, `command`, `timestamp`, `payload`, `issues`
- 文字化け防止のため、全 JSON は ASCII 外文字をエスケープしない。
- JSON payload schema は全コマンド共通で下記を参照し、必要に応じ payload schema を拡張。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["ok", "command", "timestamp", "payload", "issues"],
  "properties": {
    "ok": {"type": "boolean"},
    "command": {"type": "string", "pattern": "^helix "},
    "timestamp": {"type": "string", "format": "date-time"},
    "payload": {"type": "object"},
    "issues": {
      "type": "array",
      "items": {"$ref": "#/definitions/issue"}
    }
  },
  "definitions": {
    "issue": {
      "type": "object",
      "required": ["code", "severity", "message"],
      "properties": {
        "code": {"type": "string"},
        "severity": {"type": "string", "enum": ["info", "warning", "error"]},
        "message": {"type": "string"},
        "details": {"type": "object"}
      }
    }
  }
}
```

### §1.3 exit code ルール（0 success / 1 user error / 2 fail-close / N domain error）

- `0`：成功。payload `ok=true`。
- `1`：コマンド入力不正、引数不足、権限制約違反（ユーザー起因）。
- `2`：外部依存不能/内部破損などフェイルクローズ（再試行で回復困難な状態）。
- Domain code: コマンドごとに固定 10xx/11xx/12xx を付与。
- Domain code が必要な場合、`exit code` は `100 + code` を返す。例: `1010`。
- コード表（抜粋）:
  - `1001` command not found / routing not found（検証エラー）
  - `1010` contract drift（plan mismatch）
  - `1020` artifact stale（age > policy）
  - `1030` transition illegal
  - `1040` resource busy (blocking)
  - `1050` hook timeout
  - `1060` hook fail-open allowed

### §1.4 timeout / retry / blocking

- `--timeout` は全コマンドで受け付け（デフォルト 30s）。
- `--timeout` は user error で上限チェック。
- retry は以下 2 段階で実施:
  - stage1: 瞬時エラーなら `--retries`（1→3）
  - stage2: ネットワーク/外部ジョブは指数バックオフ（1s,2s,4s）
- blocking 処理（mutation / db 更新 / scheduler）は 30 秒以上で fail-close。
- long-running 処理は実行中ログ（role_audit）を必須出力。

---

## §2 helix doctor check_*（F1/F2/F4/F5/F6/BR-12）

この節は plan の A-05 系 doctor 系を補完し、14 件の詳細契約を定義する。

### U-03 決定
- `helix doctor --check-mode-transition` を採用。`--check-mode-routing` は alias として将来削除予定（deprecate）。

以下の 14 件は共通的に以下の前提で定義。

- usage: `helix doctor <check-command> [--json] [--timeout N] [--verbose]`
- input: 既定では `.helix`/実行環境状態
- output: text / --json の2種
- exit code: 成功時 0、入力不正 1、フェイルクローズ 2、ドメイン差分 1001/1010/1020
- side effect: read-only（ただし `doctor check-safety` のみ `--fix` 指定時のみ書込）
- error message template: `ERROR(DOC-XXXX): <message>`

#### A-01 helix doctor check-mode-transition

- usage: `helix doctor check-mode-transition [--plan-id <id>] [--json]`
- payload schema (JSON Schema):

```json
{
  "command": "helix doctor check-mode-transition",
  "type": "object",
  "properties": {
    "ok": {"type":"boolean"},
    "command": {"type":"string"},
    "timestamp": {"type":"string","format":"date-time"},
    "payload": {
      "type": "object",
      "properties": {
        "current_mode": {"type":"string"},
        "mode_transition_table": {
          "type":"array",
          "items": {"type":"object","properties": {
            "from": {"type":"string"},
            "to": {"type":"string"},
            "allowed": {"type":"boolean"},
            "reason": {"type":"string"}
          }}
        }
      }
    }
  },
  "required": ["ok","command","timestamp","payload"]
}
```
- exit code: 0 / 1 / 2 / 1030（違反）
- side effect: none
- error message template: `ERROR(DOC-1030): mode transition table は不整合です: {transition}`

#### A-02 helix doctor check-planned-cli-age
- usage: `helix doctor check-planned-cli-age [--days <N>] [--json]`
- U-05 決定: `status=planned` かつ `created > 90d` の CLI を warn。
  - `--days <N>` で上書き可（例: `--days 30`）。
- payload schema (JSON Schema):

```json
{
  "type": "object",
  "properties": {
    "payload": {
      "type": "object",
      "properties": {
        "status": {"type":"string","enum":["fresh","planned","stale"]},
        "items": {
          "type":"array",
          "items": {
            "type":"object",
            "properties": {
              "command": {"type":"string"},
              "created": {"type":"string","format":"date-time"},
              "days_since_created": {"type":"integer"},
              "warning": {"type":"boolean"}
            }
          }
        }
      }
    }
  }
}
```
- exit code: 0（warning の場合も 0） / 1 / 2 / 1020（aging違反）
- side effect: none
- error message template: `WARN(DOC-1020): planned 期限超過: {command}`

#### A-03 helix doctor check-gate-readiness

- usage: `helix doctor check-gate-readiness [--plan-id <id>] [--stage <all|L3|L4>] [--json]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"plan_id":{"type":"string"},"readiness":{"type":"number","minimum":0,"maximum":1},"blocking": {"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1（未達） / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): ゲート整合性が満たされていません: {items}`

#### A-04 helix doctor check-artifacts-integrity

- usage: `helix doctor check-artifacts-integrity [--json] [--include-optional]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"artifacts":{"type":"array","items":{"type":"string"}},"corrupted":{"type":"array","items":{"type":"string"}},"mode":{"type":"string"}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): artifact integrity check failed` 

#### A-05 helix doctor check-plan-links

- usage: `helix doctor check-plan-links [--json] [--strict]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"broken_links":{"type":"array","items":{"type":"string"}},"dangling_refs":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): plan link integrity error`

#### A-06 helix doctor check-role-consistency

- usage: `helix doctor check-role-consistency [--role-map <path>] [--json]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"roles_seen":{"type":"array","items":{"type":"string"}},"unknown_roles":{"type":"array","items":{"type":"string"}},"violations":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): role map 与えられた制約に違反: {violations}`

#### A-07 helix doctor check-mode-transition-table

- usage: `helix doctor check-mode-transition-table [--json] [--mode-transition-path <path>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"mode_transition": {"type":"array","items":{"type":"object","properties":{"from":{"type":"string"},"to":{"type":"string"},"policy":{"type":"string"}}}}}}}
```
- exit code: 0 / 1 / 2 / 1030
- side effect: none
- error message template: `ERROR(DOC-1030): mode transition table syntax invalid`

#### A-08 helix doctor check-legacy-compat

- usage: `helix doctor check-legacy-compat [--compat-level <strict|compat|legacy>] [--json]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"legacy_items":{"type":"array","items":{"type":"string"}},"compatibility_score":{"type":"number"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `WARN(DOC-1010): legacy compatibility risk` 

#### A-09 helix doctor check-hook-coverage

- usage: `helix doctor check-hook-coverage [--json] [--event <type>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"configured_hooks":{"type":"array","items":{"type":"string"}},"implemented_hooks":{"type":"array","items":{"type":"string"}},"coverage": {"type":"number"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): hook coverage below policy`

#### A-10 helix doctor check-audit-continuity

- usage: `helix doctor check-audit-continuity [--json] [--from <ts>] [--to <ts>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"missing_windows":{"type":"array","items":{"type":"string"}},"max_lag_ms":{"type":"integer"}}}}}
```
- exit code: 0 / 1 / 2 / 2
- side effect: none
- error message template: `ERROR(DOC-2XXX): audit continuity interruption`

#### A-11 helix doctor check-taskgraph

- usage: `helix doctor check-taskgraph [--plan-id <id>] [--json] [--strict]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"graph_ok":{"type":"boolean"},"node_count":{"type":"integer"},"cycle_count":{"type":"integer"},"errors":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): task graph cycle detected`

#### A-12 helix doctor check-state-machine

- usage: `helix doctor check-state-machine [--json] [--state-file <path>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"state_file":{"type":"string"},"valid":{"type":"boolean"},"invalid_states":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1030
- side effect: none
- error message template: `ERROR(DOC-1030): state machine invalid transition detected`

#### A-13 helix doctor check-config-sanity

- usage: `helix doctor check-config-sanity [--json] [--scope <global|workspace|plan>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"scope":{"type":"string"},"invalid_keys":{"type":"array","items":{"type":"string"}},"value_summary":{"type":"object"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): config schema violation`

#### A-14 helix doctor check-bridge-policy

- usage: `helix doctor check-bridge-policy [--json] [--bridge <git|scheduler|hook>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"bridge":{"type":"string"},"policy_ok":{"type":"boolean"},"gaps":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): bridge policy breach`

## §3 helix budget（F6 homeostasis）— U-01 確定

### 決定

- U-01: `helix budget status --homeostasis` を subverb に統一。
- `helix budget --homeostasis` は今期は非推奨エイリアス。

#### A-15 helix budget status

- usage: `helix budget status [--json] [--detailed]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"scope":{"type":"string"},"items":{"type":"array","items":{"type":"object","properties":{"resource":{"type":"string"},"used":{"type":"number"},"limit":{"type":"number"},"headroom":{"type":"number"}}}},"status":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1020
- side effect: none
- error message template: `ERROR(DOC-1020): budget status read failure`

#### A-16 helix budget status --homeostasis

- usage: `helix budget status --homeostasis [--json] [--days <N>] [--project <name>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"saturated": {"type":"boolean"},"pressure_index":{"type":"number"},"signals":{"type":"array","items":{"type":"object","properties":{"signal":{"type":"string"},"weight":{"type":"number"},"advice":{"type":"string"}}}}}}}
```
- exit code: 0 / 1 / 2 / 1020
- side effect: none
- error message template: `WARN(DOC-1020): budget homeostasis pressure high`

#### A-17 helix budget predict

- usage: `helix budget predict [--json] [--horizon-days <7|14|30>] [--scenario <baseline|growth|aggressive>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"horizon_days":{"type":"integer"},"prediction":{"type":"array","items":{"type":"object","properties":{"date":{"type":"string"},"expected_usage":{"type":"number"},"recommended_action":{"type":"string"}}}},"version":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: no write
- error message template: `ERROR(DOC-2XXX): budget forecast unavailable`

## §4 helix plan（F2 / F7 / F9）— plan fork / plan apoptosis

この節は PLAN ライフサイクルの CLI 契約。

#### A-18 helix plan

- usage: `helix plan <create|view|fork|status|apoptosis|validate> [--json] [--plan-id <id>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"action":{"type":"string"},"plan_id":{"type":"string"},"result":{"type":"object","properties":{"forked":{"type":"boolean"},"apoptosed":{"type":"boolean"},"updated_fields":{"type":"array","items":{"type":"string"}}}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: plan ファイル更新（fork/apoptosis）
- error message template: `ERROR(DOC-1010): plan lifecycle action failed`

#### A-19 helix plan fork

- usage: `helix plan fork --from <plan-id> --to <plan-id> [--json] [--copy-artifacts]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"from":{"type":"string"},"to":{"type":"string"},"copied":{"type":"boolean"},"artifact_refs":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: 新規 plan 作成、索引更新
- error message template: `ERROR(DOC-2XXX): plan fork failed`

#### A-20 helix plan apoptosis

- usage: `helix plan apoptosis --plan-id <id> --mode <archive|close|retire> [--json] [--force]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"plan_id":{"type":"string"},"mode":{"type":"string"},"archived":{"type":"boolean"},"reason":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: plan metadata write + audit
- error message template: `ERROR(DOC-2XXX): plan apoptosis failed`

#### A-21 helix matrix

- usage: `helix matrix --plan-id <id> [--json] [--diff <other-id>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"plan_id":{"type":"string"},"rows":{"type":"array","items":{"type":"object","properties":{"item":{"type":"string"},"coverage":{"type":"number"}}}},"diff_with":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: optional read/write（差分レポート生成）
- error message template: `ERROR(DOC-1010): matrix diff generation failed`

#### A-22 helix plan validate

- usage: `helix plan validate --plan-id <id> [--json] [--strict]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"valid":{"type":"boolean"},"violations":{"type":"array","items":{"type":"string"}},"summary":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error message template: `ERROR(DOC-1010): plan validation failure`

## §5 helix evolution（F7）— score / promote / deprecate

### U-06, U-07 系を併記

- U-06: hook matcher は `Task` を採用（本節では CLI 側に payload に `tool_name/agent_name/duration_ms` 要求を加える）

#### A-23 helix recipe score

- usage: `helix recipe score <discover|promote|list> [--json] [--window <days>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"items":{"type":"array","items":{"type":"object","properties":{"artifact_id":{"type":"string"},"score":{"type":"number"},"trend":{"type":"string"}}}},"window_days":{"type":"integer"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: none / cache 更新（cache）
- error message template: `ERROR(DOC-2XXX): recipe scoring failed`

#### A-24 helix recipe promote

- usage: `helix recipe promote <artifact-id> [--json] [--channel <stable|legacy>] [--finalize]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"artifact_id":{"type":"string"},"new_status":{"type":"string"},"channel":{"type":"string"},"applied_at":{"type":"string","format":"date-time"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: artifact state write
- error message template: `ERROR(DOC-2XXX): recipe promote blocked by policy`

#### A-25 helix recipe deprecate

- usage: `helix recipe deprecate <artifact-id> [--json] [--reason <text>] [--force]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"artifact_id":{"type":"string"},"deprecated":{"type":"boolean"},"reason":{"type":"string"},"notify_targets":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: registry update / notification
- error message template: `ERROR(DOC-2XXX): recipe deprecate failed`

## §6 helix version / migrate / portable（F8 / F10）— U-02 確定

### 決定

- U-02: `helix portable adopt` と `helix coexist adopt` は分離 CLI を維持。
- F8/F10 の共通 `--compatibility-adr` 引数を導入する。

#### A-26 helix version

- usage: `helix version [--json] [--json-schema] [--check]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"version":{"type":"string"},"revision":{"type":"string"},"compatibility":{"type":"string"},"checks":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: read-only
- error message template: `ERROR(DOC-2XXX): version metadata mismatch`

#### A-27 helix migrate

- usage: `helix migrate [--from <v> ] [--to <v>] [--dry-run] [--yes] [--json] [--compatibility-adr <path>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"from":{"type":"string"},"to":{"type":"string"},"mode":{"type":"string","enum":["dry-run","apply"]},"operations":{"type":"array","items":{"type":"string"}},"changed_files":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 2
- side effect: file write / backup 作成
- error message template: `ERROR(DOC-2XXX): migrate aborted for safety`

#### A-28 helix portable adopt

- usage: `helix portable adopt [--compatibility-adr <path>] [--source <dir>] [--json]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"compatibility_adr":{"type":"string"},"adopted":{"type":"boolean"},"portable_id":{"type":"string"},"created_at":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: 設定更新 + portability manifest 作成
- error message template: `ERROR(DOC-1010): portable adoption blocked`

#### A-29 helix portable validate

- usage: `helix portable validate [--compatibility-adr <path>] [--json] [--strict]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"compatible":{"type":"boolean"},"checks":{"type":"array","items":{"type":"string"}},"deviation":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: none
- error message template: `ERROR(DOC-1010): portable compatibility failed`

## §7 helix db autophagy（F9）

#### A-30 helix db autophagy

- usage: `helix db autophagy [--json] [--days <N>] [--dry-run] [--force]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"deleted_records":{"type":"integer"},"retained_records":{"type":"integer"},"candidates":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string"},"age_days":{"type":"integer"}}}},"dry_run":{"type":"boolean"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: DB cleanup（`--dry-run` 含めファイル更新なし）
- error message template: `ERROR(DOC-2XXX): db autophagy failed`

#### A-31 helix db cleanup-legacy

- usage: `helix db cleanup-legacy [--json] [--scope <global|task|artifact>] [--yes]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"scope":{"type":"string"},"removed_items":{"type":"array","items":{"type":"string"}},"failed_items":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: DB delete + snapshot
- error message template: `ERROR(DOC-2XXX): db cleanup failed`

## §8 helix coexist（F10）— framework / status / adopt

### U-02 決定反映

- `helix coexist adopt` は独立コマンドで提供し、`helix portable adopt` と同名語彙を避ける。

#### A-32 helix coexist status

- usage: `helix coexist status [--json] [--target <id>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"target":{"type":"string"},"compatibility_mode":{"type":"string"},"active":{"type":"boolean"},"conflicts":{"type":"array","items":{"type":"string"}},"summary":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: none / optional cache write
- error message template: `ERROR(DOC-1010): coexist status not found`

#### A-33 helix coexist adopt

- usage: `helix coexist adopt [--compatibility-adr <path>] [--source <path>] [--json] [--yes]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"target":{"type":"string"},"compatibility_adr":{"type":"string"},"adopted":{"type":"boolean"},"rollback_plan":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: config + coexist manifest write
- error message template: `ERROR(DOC-1010): coexist adopt failed`

#### A-34 helix coexist validate

- usage: `helix coexist validate [--compatibility-adr <path>] [--json] [--strict]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"compatible":{"type":"boolean"},"check_items":{"type":"array","items":{"type":"string"}},"incompatibilities":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2
- side effect: none
- error message template: `ERROR(DOC-1010): coexist validate failed`

## §9 helix recovery（Recovery mode）— U-04 確定

### 決定

- U-04: `helix recovery --finalize-to-adr` を採用。
- `helix recover` は別名エイリアスではなく、別セッション運用コマンドとして維持。

#### A-35 helix recovery

- usage: `helix recovery [--start|--finalize-to-adr|--status] [--json] [--plan-id <id>]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"mode":{"type":"string","enum":["start","status","finalize-to-adr"]},"incident_id":{"type":"string"},"state":{"type":"string"},"next_steps":{"type":"array","items":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 1010
- side effect: recovery record write
- error message template: `ERROR(DOC-1010): recovery finalize failed`

#### A-36 helix recover

- usage: `helix recover [--json] [--diagnose-only] [--create-plan]`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"payload":{"type":"object","properties":{"diagnostics":{"type":"array","items":{"type":"string"}},"plan_id":{"type":"string"},"risk_level":{"type":"string"}}}}}
```
- exit code: 0 / 1 / 2 / 2
- side effect: diagnostics output / optional plan draft write
- error message template: `ERROR(DOC-2XXX): recover command failed`

## §10 hook payload schema — 11 hook 詳細

以下の payload schema は Claude Code hook 仕様を採用し、`stdout` は必須（少なくとも 1 行）。

### §10.1 statusLine（implemented）

- event type: `StatusLine`
- matcher: `StatusLine`
- expected exit code interpretation: `0=pass`, `2=fail-close + stdout`
- payload schema (JSON Schema):

```json
{
  "type": "object",
  "required": ["status", "session_id", "timestamp"],
  "properties": {
    "status": {"type": "string"},
    "session_id": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"},
    "extra": {"type": "object"}
  }
}
```
- timeout: 2s
- fail-close / fail-open: fail-open（UI 表示のみ影響）
- retry: 1 回のみ
- audit log: role_audit + event_log

### §10.2 PreCompact（implemented）

- event type: `PreCompact`
- matcher: `PreCompact`
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"session_id":{"type":"string"},"precompact_reason":{"type":"string"},"message_count":{"type":"integer"},"window_ms":{"type":"integer"}}}
```
- timeout: 5s
- fail-close / fail-open: fail-close（前提保全）
- retry: no retry（単一フェーズ）
- audit log: role_audit + event_log

### §10.3 pretooluse-agent-guard（implemented）

- event type: `PreToolUse`
- matcher: `agent-guard`
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"tool_name":{"type":"string"},"agent_name":{"type":"string"},"risk_level":{"type":"string"},"policy_id":{"type":"string"},"metadata":{"type":"object"}}}
```
- timeout: 3s
- fail-close / fail-open: fail-close
- retry: 1
- audit log: role_audit + event_log

### §10.4 SessionStart cleared/compacted（implemented）

- event type: `SessionStart`
- matcher: `SessionStart`
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"session_id":{"type":"string"},"cwd":{"type":"string"},"user_context":{"type":"object"},"compact_state":{"type":"string"}}}
```
- timeout: 5s
- fail-close / fail-open: fail-close（監査必要）
- retry: 1
- audit log: role_audit + event_log

### §10.5 UserPromptSubmit（implemented）

- event type: `UserPromptSubmit`
- matcher: `UserPromptSubmit`
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"session_id":{"type":"string"},"prompt_length":{"type":"integer"},"intent_hint":{"type":"string"},"timestamp":{"type":"string"}}}
```
- timeout: 3s
- fail-close / fail-open: fail-open（最終制御は次段）
- retry: 1
- audit log: role_audit + event_log

### §10.6 pre-commit doc lint / plan validate

- event type: `PreCommit`
- matcher: `*.md,*.yaml,plan.md`
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"files":{"type":"array","items":{"type":"string"}},"checkers":{"type":"array","items":{"type":"string"}},"result":{"type":"string"}}}
```
- timeout: 10s
- fail-close / fail-open: fail-close
- retry: 1
- audit log: role_audit + event_log

### §10.7 PostToolUse（Task）→skill_usage（U-06 確定）

- event type: `PostToolUse`
- matcher: `Task`（U-06 決定）
- payload schema (JSON Schema) 必須キー:
  - `tool_name`, `agent_name`, `duration_ms`

```json
{
  "type": "object",
  "required": ["tool_name", "agent_name", "duration_ms", "success"],
  "properties": {
    "tool_name": {"type": "string"},
    "agent_name": {"type": "string"},
    "duration_ms": {"type": "integer", "minimum": 0},
    "success": {"type": "boolean"},
    "exit_code": {"type": "integer"},
    "stderr": {"type": "string"}
  }
}
```
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- fail-close / fail-open: fail-open（収集失敗は実行停止不可）
- timeout: 5s
- retry: 0
- audit log: role_audit + event_log

### §10.8 weekly cron / GitHub Actions

- event type: `Scheduled`
- matcher: `weekly`
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"run_id":{"type":"string"},"source":{"type":"string","enum":["cron","gha"]},"targets":{"type":"array","items":{"type":"string"}},"artifacts_ref":{"type":"string"}}}
```
- timeout: 30m
- fail-close / fail-open: fail-close（長期監視監査）
- retry: 3 / schedule jitter
- audit log: role_audit + event_log

### §10.9 mutation event hook（U-07a 確定）

- event type: `Mutation`
- matcher: `PostToolUse` + scheduler 連動
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"operation_type":{"type":"string"},"target_plan_id":{"type":"string"},"metadata":{"type":"object","properties":{"actor":{"type":"string"},"command":{"type":"string"},"timestamp":{"type":"string"}}},"dry_run":{"type":"boolean"}}}
```
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- fail-close / fail-open: fail-open（監査遅延時）
- timeout: 5s
- retry: 2（指数）
- audit log: role_audit + event_log

### §10.10 migration event hook（U-07b 確定）

- event type: `Migration`
- matcher: `PostToolUse` + scheduler 連動
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"operation_type":{"type":"string"},"target_plan_id":{"type":"string"},"metadata":{"type":"object","properties":{"from":{"type":"string"},"to":{"type":"string"},"compatibility_adr":{"type":"string"}}},"duration_ms":{"type":"integer"}}
```
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- fail-close / fail-open: fail-close（migration integrity）
- timeout: 10s
- retry: 1
- audit log: role_audit + event_log

### §10.11 coexist event hook（U-07c 確定）

- event type: `Coexist`
- matcher: `PostToolUse` + scheduler 連動
- payload schema (JSON Schema):

```json
{"type":"object","properties":{"operation_type":{"type":"string"},"target_plan_id":{"type":"string"},"metadata":{"type":"object","properties":{"framework":{"type":"string"},"compatibility_mode":{"type":"string"}}},"status":{"type":"string"}}
```
- exit code interpretation: `0 pass`, `2 fail-close + stdout`
- fail-close / fail-open: fail-open（最終状態監査で収束）
- timeout: 5s
- retry: 2
- audit log: role_audit + event_log

## §11 error handling 共通ルール（fail-close / fail-open / timeout / retry）

- 全コマンドは共通のエラー文法を持つ。
- テキスト:
  - `INFO(...)`, `WARN(...)`, `ERROR(...)`
  - `ERROR` は `exit code` を伴う。
- JSON:
  - `issues[]` に構造化 error code を格納。
- fail-close の基準:
  - 署名不一致、artifact破損、重要状態遷移失敗。
  - `exit code` は 2 or 10xx を必須。
- fail-open の基準:
  - 監査系フックのネットワーク遅延、任意のメトリクス欠損。
  - `issues` の `severity=warning` を付与。
- timeout 時の基本挙動:
  - 既定: `ERROR CODE=1050, exit code 2`
  - hook では `retry` 後 2 回連続 timeout で fail-close。
- retry 規約:
  - 重要度が低い read-only は 2 回
  - 重要度高（db write） は 0 回（速やかに fail-close）

## §12 4 artifact 双方向 trace

本節は PLAN ⇔ ADR ⇔ テスト ⇔ Interface の追跡。

- PLAN 参照: `docs/plans/L5/L5-helix-workflows-外部IF詳細設計plan.md`
- ADR 参照: `ADR-044`, `ADR-045`
- L9 参照: `docs/v2/L9-test-design/helix-workflows-functional-test-design.md`
- IF 参照: 本文（CLI/hook）

### 双方向トレース

- A-15〜A-16（budget homeostasis）
  - PLAN: F6, plan の節
  - ADR: ADR-044 の survival 指標
  - L9: ST-F6 検証
- A-29〜A-36（recovery）
  - PLAN: Recovery mode
  - ADR: ADR-044 Fallback 方針
  - L9: ST-F9/ST-F10 依存
- A-17〜A-25（plan/evolution）
  - PLAN: F2/F7
  - ADR: ADR-045 付録 governance
  - L9: ST-F2/ST-F7/Pair tests

### 4 artifact consistency rules

1. IF 定義の変更は PLAN 対応表の行（A-xx）と同一。
2. U-0x 決定は ADR の根拠条項と一致。
3. hook payload schema は event schema を L9 で検証可能。
4. `exit code` マッピングをドキュメントと実装で一致させる（差分は例外登録）。

## §13 implementation_status 表（planned/partial/implemented）

本表は 47件（CLI 36 + hook 11）を対象に planned/partial/implemented を記載する。

| 対象 | status | 補足 |
|---|---|---|
| §1 共通ルール | implemented | 既存方針を確定化 |
| §2 doctor check_* | partial | 14件の仕様は確定、実装差分の追加反映は保留 |
| A-01〜A-14 | implemented | CLI 仕様化済み |
| A-15〜A-17 budget | partial | `helix budget status --homeostasis` 固定済 |
| A-18〜A-22 plan | partial | plan fork/apoptosis 定義のみ、hook 連携は別節 |
| A-23〜A-25 evolution | planned | promote/deprecate 補助実装確認が必要 |
| A-26〜A-29 version/migrate/portable | partial | migrate/portable の既存差分確認中 |
| A-30〜A-31 db | planned | autophagy/cleanup 実装差分確認要 |
| A-32〜A-34 coexist | partial | U-02 により分離コマンド確定 |
| A-35〜A-36 recovery | partial | `--finalize-to-adr` を準拠対象に追加 |
| §10 hooks | implemented/partial | statusLine/pre compact/sessionstart/userpromptsubmitは implemented |
| §11 error rule | implemented | fail-close/open 基準固定 |
| U-01 | implemented | `helix budget status --homeostasis` 決定 |
| U-02 | implemented | `portable/coexist` 分離決定 |
| U-03 | implemented | `--check-mode-transition` 決定 |
| U-04 | implemented | `helix recovery --finalize-to-adr` 決定 |
| U-05 | implemented | 90day + `--days` オーバーライド固定 |
| U-06 | implemented | PostToolUse(Task) 決定 |
| U-07a | implemented | mutation event 追加決定 |
| U-07b | implemented | migration event 追加決定 |
| U-07c | implemented | coexist event 追加決定 |

## 付録 A. CLI 命令一覧（実装状況追跡、本文 §2-§9 と整合する 36 件 + 検討候補 N 件）

### CLI-001
- CLI-001 `helix init`
### CLI-002
- CLI-002 `helix status`
### CLI-003
- CLI-003 `helix dashboard`
### CLI-004
- CLI-004 `helix mode`
### CLI-005
- CLI-005 `helix doctor`
### CLI-006
- CLI-006 `helix budget status`
### CLI-007
- CLI-007 `helix budget status --homeostasis`
### CLI-008
- CLI-008 `helix budget predict`
### CLI-009
- CLI-009 `helix db`
### CLI-010
- CLI-010 `helix migrate`
### CLI-011
- CLI-011 `helix commands`
### CLI-012
- CLI-012 `helix setup`
### CLI-013
- CLI-013 `helix test`
### CLI-014
- CLI-014 `helix test-debug`
### CLI-015
- CLI-015 `helix debug`
### CLI-016
- CLI-016 `helix bench`
### CLI-017
- CLI-017 `helix plan`
### CLI-018
- CLI-018 `helix plan fork`
### CLI-019
- CLI-019 `helix plan apoptosis`
### CLI-020
- CLI-020 `helix matrix`
### CLI-021
- CLI-021 `helix gate`
### CLI-022
- CLI-022 `helix gate-api-check`
### CLI-023
- CLI-023 `helix vmodel`
### CLI-024
- CLI-024 `helix push`
### CLI-025
- CLI-025 `helix readiness`
### CLI-026
- CLI-026 `helix sprint`
### CLI-027
- CLI-027 `helix task`
### CLI-028
- CLI-028 `helix interrupt`
### CLI-029
- CLI-029 `helix refactor`
### CLI-030
- CLI-030 `helix recover`
### CLI-031
- CLI-031 `helix recovery`
### CLI-032
- CLI-032 `helix incident`
### CLI-033
- CLI-033 `helix add-feature`
### CLI-034
- CLI-034 `helix retrofit`
### CLI-035
- CLI-035 `helix handover`
### CLI-036
- CLI-036 `helix recipe score`
- CLI-037 `helix recipe promote`
- CLI-038 `helix recipe deprecate`
- CLI-039 `helix version`
- CLI-040 `helix portable adopt`
- CLI-041 `helix portable validate`
- CLI-042 `helix coexist status`
- CLI-043 `helix coexist adopt`
- CLI-044 `helix coexist validate`
- CLI-045 `helix db autophagy`
- CLI-046 `helix db cleanup-legacy`

本表は本文 §2-§9 の A-XX（36件）を含み、検討候補 CLI-NNN（10件）を追加した実装状況追跡用。

## §12.5 CLI 一覧（A-01〜A-95）実装前提表（exit code / payload schema 交差チェック）

本表は A-01〜A-36 を payload schema cross-check 対象とする。A-37〜A-95 は次 PLAN 候補（L7 spike 完了後の追加 CLI）として carry 化、本 doc では schema 不在を許容する。

### A-01 `helix doctor check-mode-transition`
- usage pattern: `helix doctor check-mode-transition [--plan-id <id>] [--json]`
- input: mode state / plan snapshot
- output: text summary / payload schema JSON
- payload schema: `{ok, command, timestamp, payload.current_mode, payload.mode_transition_table, issues[]}`
- exit code: 0 / 1 / 2 / 1030
- side effect: none
- error handling: payload schema validation error は `E-IF-0101` with `ERROR(DOC-1030)`

### A-02 `helix doctor check-planned-cli-age`
- usage pattern: `helix doctor check-planned-cli-age [--days N] [--json]`
- input: CLI age metadata / created timestamp
- output: text/JSON payload schema
- payload schema: `{ok, command, timestamp, payload.status, payload.items}`
- exit code: 0 / 1 / 2 / 1020
- side effect: none
- error handling: warning でも exit code は 0

### A-03 `helix doctor check-gate-readiness`
- usage: `helix doctor check-gate-readiness [--plan-id <id>] [--json]`
- input: plan id, gate config
- output: text / payload schema json
- payload schema: `{ok, command, payload.plan_id, payload.readiness}`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: policy mismatch -> fail-close

### A-04 `helix doctor check-artifacts-integrity`
- usage: `helix doctor check-artifacts-integrity [--include-optional] [--json]`
- input: artifact paths
- output: text summary, payload schema with `payload.artifacts`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: corruption -> 1 or 2

### A-05 `helix doctor check-plan-links`
- usage: `helix doctor check-plan-links [--strict] [--json]`
- input: plan dependency graph
- output: text / payload schema with `broken_links`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: strict=1 かつ不整合で `ERROR(DOC-1010)`

### A-06 `helix doctor check-role-consistency`
- usage: `helix doctor check-role-consistency [--role-map <path>] [--json]`
- input: role map yaml
- output: text + payload schema with `violations`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: unknown role -> 1

### A-07 `helix doctor check-mode-transition-table`
- usage: `helix doctor check-mode-transition-table [--mode-transition-path <path>] [--json]`
- input: transition config
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1030
- side effect: none
- error handling: invalid transition -> `DOC-1030`

### A-08 `helix doctor check-legacy-compat`
- usage: `helix doctor check-legacy-compat [--compat-level <strict|compat|legacy>] [--json]`
- input: legacy command map
- output: text / payload schema with `compatibility_score`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: score 欠損は fail-close

### A-09 `helix doctor check-hook-coverage`
- usage: `helix doctor check-hook-coverage [--event <type>] [--json]`
- input: hook 定義ファイル
- output: text / payload schema with `coverage`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: coverage 下限未達 -> 1

### A-10 `helix doctor check-audit-continuity`
- usage: `helix doctor check-audit-continuity [--from <ts>] [--to <ts>] [--json]`
- input: time window
- output: text / payload schema with `missing_windows`
- exit code: 0 / 1 / 2
- side effect: none
- error handling: long gap -> 2

### A-11 `helix doctor check-taskgraph`
- usage: `helix doctor check-taskgraph [--plan-id <id>] [--strict] [--json]`
- input: task graph
- output: text / payload schema with `node_count`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: cycle 検出 -> 2

### A-12 `helix doctor check-state-machine`
- usage: `helix doctor check-state-machine [--state-file <path>] [--json]`
- input: 状態機 JSON
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1030
- side effect: none
- error handling: invalid states -> 1

### A-13 `helix doctor check-config-sanity`
- usage: `helix doctor check-config-sanity [--scope <global|workspace|plan>] [--json]`
- input: config file
- output: text / payload schema with `invalid_keys`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: schema violation -> 1

### A-14 `helix doctor check-bridge-policy`
- usage: `helix doctor check-bridge-policy [--bridge <git|scheduler|hook>] [--json]`
- input: bridge policy manifest
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: policy breach -> 2

### A-15 `helix budget status`
- usage: `helix budget status [--json] [--detailed]`
- input: budget source
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1020
- side effect: none
- error handling: budget read fail -> 2

### A-16 `helix budget status --homeostasis`
- usage: `helix budget status --homeostasis [--days N] [--json]`
- input: budget metrics, days
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1020
- side effect: none
- error handling: pressure high -> warning only

### A-17 `helix budget predict`
- usage: `helix budget predict [--horizon-days <N>] [--scenario <mode>] [--json]`
- input: time series + scenario
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: none
- error handling: input 欠損 -> 1

### A-18 `helix plan`
- usage: `helix plan <create|view|fork|status|apoptosis|validate> ...`
- input: action, plan id
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: create/edit plan
- error handling: validation error -> 1

### A-19 `helix plan fork`
- usage: `helix plan fork --from <id> --to <id> [--json]`
- input: source plan / target plan
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: write new plan files
- error handling: collision -> 1

### A-20 `helix plan apoptosis`
- usage: `helix plan apoptosis --plan-id <id> --mode <archive|close|retire> [--force]`
- input: plan id, mode
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: metadata update
- error handling: already closed -> 1

### A-21 `helix matrix`
- usage: `helix matrix --plan-id <id> [--diff <id>] [--json]`
- input: 2 plan snapshots
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: optional artifact generation
- error handling: matrix engine failure -> 2

### A-22 `helix plan validate`
- usage: `helix plan validate --plan-id <id> [--json]`
- input: plan doc + references
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: violations -> 1

### A-23 `helix recipe score`
- usage: `helix recipe score <discover|promote|list> [--window <N>]`
- input: score backend
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: cache update optional
- error handling: scoring backend unreachable -> 2

### A-24 `helix recipe promote`
- usage: `helix recipe promote <artifact-id> [--channel <stable|legacy>] [--json]`
- input: artifact-id
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: registry update
- error handling: status conflict -> 1

### A-25 `helix recipe deprecate`
- usage: `helix recipe deprecate <artifact-id> [--reason <text>] [--json]`
- input: artifact id, reason
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: registry update
- error handling: artifact not found -> 1

### A-26 `helix version`
- usage: `helix version [--check] [--json]`
- input: optional check flag
- output: text / payload schema with `version`
- exit code: 0 / 1 / 2
- side effect: none
- error handling: mismatch -> 1

### A-27 `helix migrate`
- usage: `helix migrate [--from <v>] [--to <v>] [--dry-run] [--yes] [--json]`
- input: migration path
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: files update
- error handling: dry-run safe failure -> 1

### A-28 `helix portable adopt`
- usage: `helix portable adopt [--source <path>] [--compatibility-adr <path>] [--json]`
- input: source path, adr
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: manifest write
- error handling: incompatibility -> 1

### A-29 `helix portable validate`
- usage: `helix portable validate [--compatibility-adr <path>] [--strict] [--json]`
- input: compatibility ADR
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: none
- error handling: missing keys -> 2

### A-30 `helix db autophagy`
- usage: `helix db autophagy [--days <N>] [--dry-run] [--json]`
- input: retention threshold
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: DB delete and snapshot
- error handling: transactional fail -> 2

### A-31 `helix db cleanup-legacy`
- usage: `helix db cleanup-legacy [--scope <global|task|artifact>] [--yes] [--json]`
- input: scope
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: DB cleanup write
- error handling: data integrity check fail -> 2

### A-32 `helix coexist status`
- usage: `helix coexist status [--json] [--target <id>]`
- input: target id
- output: text / payload schema with `active`
- exit code: 0 / 1 / 2 / 1010
- side effect: none
- error handling: target missing -> 1

### A-33 `helix coexist adopt`
- usage: `helix coexist adopt [--compatibility-adr <path>] [--yes] [--source <path>]`
- input: source + compatibility ADR
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: coexist manifest update
- error handling: rollout lock -> 2

### A-34 `helix coexist validate`
- usage: `helix coexist validate [--compatibility-adr <path>] [--strict] [--json]`
- input: policy file
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: none
- error handling: incompatibility -> 1

### A-35 `helix recovery`
- usage: `helix recovery --start|--status|--finalize-to-adr [--plan-id <id>] [--json]`
- input: recovery command mode
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: recovery state write
- error handling: finalize with missing ADR -> 2

### A-36 `helix recover`
- usage: `helix recover [--diagnose-only] [--create-plan] [--json]`
- input: diagnose flags
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: plan draft optional write
- error handling: command unavailable -> 1

### A-37 `helix init`
- usage: `helix init [--template <mono|plugin>] [--force] [--json]`
- input: テンプレ指定
- output: text / payload schema with `project_id`
- exit code: 0 / 1 / 2
- side effect: directory scaffold write
- error handling: missing template -> 1
- L7 carry: payload schema 未定

### A-38 `helix status`
- usage: `helix status [--json] [--watch]`
- input: watch フラグ
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: none
- error handling: metadata stale -> 1
- L7 carry: payload schema 未定

### A-39 `helix dashboard`
- usage: `helix dashboard [--refresh] [--json] [--scope <project|global>]`
- input: scope
- output: text / payload schema with snapshot
- exit code: 0 / 1 / 2
- side effect: cache update optional
- error handling: source missing -> 1
- L7 carry: payload schema 未定

### A-40 `helix mode`
- usage: `helix mode <forward|reverse|scrum|discovery> [--json]`
- input: mode
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1030
- side effect: session mode update
- error handling: invalid transition -> 2
- L7 carry: payload schema 未定

### A-41 `helix commands`
- usage: `helix commands [--sync] [--json] [--check-only]`
- input: flags
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: spec sync optional
- error handling: drift -> 2
- L7 carry: payload schema 未定

### A-42 `helix setup`
- usage: `helix setup [--json] [--repair] [--yes]`
- input: repair mode
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: environment init
- error handling: repair incomplete -> 2
- L7 carry: payload schema 未定

### A-43 `helix test`
- usage: `helix test [--scope <module>] [--json] [--timeout <N>]`
- input: module scope
- output: text / payload schema with `result`
- exit code: 0 / 1 / 2
- side effect: none / artifacts optional
- error handling: failing test -> 2
- L7 carry: payload schema 未定

### A-44 `helix test-debug`
- usage: `helix test-debug [--json] [--module <name>] [--trace]`
- input: target module
- output: text / payload schema verbose
- exit code: 0 / 1 / 2
- side effect: trace logs
- error handling: tracer unavailable -> 1
- L7 carry: payload schema 未定

### A-45 `helix debug`
- usage: `helix debug <subcmd> [--json] [--verbose]`
- input: debug subcommand
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: optional file dump
- error handling: unsupported subcmd -> 1
- L7 carry: payload schema 未定

### A-46 `helix bench`
- usage: `helix bench [--json] [--filter <name>] [--repeat <N>]`
- input: filter / repeat
- output: text / payload schema with metrics
- exit code: 0 / 1 / 2
- side effect: metric log write
- error handling: sample timeout -> 2
- L7 carry: payload schema 未定

### A-47 `helix gate`
- usage: `helix gate [--json] [--plan-id <id>] [--revalidate]`
- input: plan id
- output: text / payload schema with `score`
- exit code: 0 / 1 / 2 / 1010
- side effect: gate state
- error handling: unresolved issue -> 2
- L7 carry: payload schema 未定

### A-48 `helix gate-api-check`
- usage: `helix gate-api-check [--json] [--strict]`
- input: api spec path
- output: text / payload schema with endpoints
- exit code: 0 / 1 / 2
- side effect: none
- error handling: drift -> 1
- L7 carry: payload schema 未定

### A-49 `helix vmodel`
- usage: `helix vmodel [--json] [--drive <forward|reverse|hybrid>]`
- input: drive
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: model state update optional
- error handling: invalid drive -> 1
- L7 carry: payload schema 未定

### A-50 `helix push`
- usage: `helix push [--gate] [--auto-merge] [--json]`
- input: flags
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: remote push / auto-merge
- error handling: push denied -> 2
- L7 carry: payload schema 未定

### A-51 `helix readiness`
- usage: `helix readiness [--deferred-finding] [--json]`
- input: deferred mode
- output: text / payload schema with `result`
- exit code: 0 / 1 / 2
- side effect: readiness marker write
- error handling: stale marker -> 1
- L7 carry: payload schema 未定

### A-52 `helix sprint`
- usage: `helix sprint [--json] [--next] [--status]`
- input: next/status
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: sprint state update
- error handling: invalid state -> 2
- L7 carry: payload schema 未定

### A-53 `helix task`
- usage: `helix task <create|update|close|view> [--json]`
- input: task action
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: task record write
- error handling: action invalid -> 1
- L7 carry: payload schema 未定

### A-54 `helix interrupt`
- usage: `helix interrupt <start|stop|resume> [--json] [--reason <text>]`
- input: action, reason
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: state update
- error handling: invalid reason -> 1
- L7 carry: payload schema 未定

### A-55 `helix refactor`
- usage: `helix refactor [--json] [--session-id <id>] [--checkpoint]`
- input: session id
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: refactor session write
- error handling: checkpoint fail -> 2
- L7 carry: payload schema 未定

### A-56 `helix recover`
- usage: `helix recover [--diagnose-only] [--create-plan] [--json]`
- input: diagnose flags
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: optional plan draft
- error handling: diagnostic timeout -> 2
- L7 carry: payload schema 未定

### A-57 `helix recovery`
- usage: `helix recovery --start|--finalize-to-adr [--json]`
- input: recovery mode
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: recovery state
- error handling: incomplete evidence -> 2
- L7 carry: payload schema 未定

### A-58 `helix incident`
- usage: `helix incident [--json] [--severity <sev>] [--route]`
- input: severity, route
- output: text / payload schema with incident id
- exit code: 0 / 1 / 2 / 1060
- side effect: incident artifact write
- error handling: route failure -> 2
- L7 carry: payload schema 未定

### A-59 `helix add-feature`
- usage: `helix add-feature [--json] [--phase <design|impl>] [--id <id>]`
- input: phase / id
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: mode transition update
- error handling: phase mismatch -> 1
- L7 carry: payload schema 未定

### A-60 `helix retrofit`
- usage: `helix retrofit [--json] [--matrix <file>] [--plan-id <id>]`
- input: matrix file
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: retrofit plan write
- error handling: matrix parse fail -> 1
- L7 carry: payload schema 未定

### A-61 `helix handover`
- usage: `helix handover [--json] [--status | --complete | --blocker | --unblock] [--owner <name>]`
- input: command mode
- output: text / payload schema
- exit code: 0 / 1 / 2 / 2
- side effect: handover file update
- error handling: owner mismatch -> 1
- L7 carry: payload schema 未定

### A-62 `helix route`
- usage: `helix route [--signal <file>] [--json] [--dry-run]`
- input: signal source
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: routing suggestion
- error handling: signal parse error -> 1
- L7 carry: payload schema 未定

### A-63 `helix workspace`
- usage: `helix workspace [--json] [--create <name>] [--close <name>]`
- input: workspace name
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: worktree write
- error handling: worktree failure -> 2
- L7 carry: payload schema 未定

### A-64 `helix schedule`（※本節内では情報系補足）
- usage: `helix scheduler [--json] [--cron <expr>] [--once]`
- input: schedule spec
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: schedule register
- error handling: cron parse fail -> 1
- L7 carry: payload schema 未定

### A-65 `helix hook`
- usage: `helix hook [--json] [--list] [--reload]`
- input: flag
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1010
- side effect: hook config update
- error handling: hook load fail -> 2
- L7 carry: payload schema 未定

### A-66 `helix check-claudemd`
- usage: `helix check-claudemd [--json] [--strict]`
- input: claudemd ファイル
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: warnings only
- error handling: format invalid -> 1
- L7 carry: payload schema 未定

### A-67 `helix context`
- usage: `helix context [--json] [--guard <on|off>] [--snapshot]`
- input: guard mode
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: context state
- error handling: snapshot unavailable -> 2
- L7 carry: payload schema 未定

### A-68 `helix session-start`
- usage: `helix session-start [--json] [--dry-run]`
- input: mode
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: session metadata
- error handling: session lock -> 2
- L7 carry: payload schema 未定

### A-69 `helix session-summary`
- usage: `helix session-summary [--json] [--stop]`
- input: stop flag
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: session close
- error handling: missing context -> 1
- L7 carry: payload schema 未定

### A-70 `helix reverse`
- usage: `helix reverse [--json] [--stage <R0|R1|R2|R3|R4>]`
- input: stage
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1030
- side effect: reverse workflow update
- error handling: stage invalid -> 1
- L7 carry: payload schema 未定

### A-71 `helix scrum`
- usage: `helix scrum [--json] [--next] [--status]`
- input: next/status
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: scrum state write
- error handling: legacy mode -> 1
- L7 carry: payload schema 未定

### A-72 `helix scrum-agile`
- usage: `helix scrum-agile [--json] [--status] [--tick]`
- input: tick
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: cadence state
- error handling: invalid cadence -> 1
- L7 carry: payload schema 未定

### A-73 `helix discovery`
- usage: `helix discovery [--json] [--plan] [--topic <text>]`
- input: topic
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: discovery draft
- error handling: topic 空 -> 1
- L7 carry: payload schema 未定

### A-74 `helix verify-all`
- usage: `helix verify-all [--json] [--scope <all|plan|runtime>]`
- input: scope
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: verification artifacts
- error handling: first fail at module -> 2
- L7 carry: payload schema 未定

### A-75 `helix verify-agent`
- usage: `helix verify-agent [--json] [--type <harvest|design|drift>]`
- input: verify type
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: evidence write
- error handling: mismatch -> 2
- L7 carry: payload schema 未定

### A-76 `helix log`
- usage: `helix log [--json] [--filter <expr>] [--raw]`
- input: filter
- output: text / payload schema with `records`
- exit code: 0 / 1 / 2
- side effect: optional dump
- error handling: format parse fail -> 1
- L7 carry: payload schema 未定

### A-77 `helix recipe`
- usage: `helix recipe [discover|promote|list] [--json]`
- input: recipe action
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: optional cache
- error handling: action mismatch -> 1
- L7 carry: payload schema 未定

### A-78 `helix learn`
- usage: `helix learn [--json] [--source <path>] [--dry-run]`
- input: source
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: learning store
- error handling: source invalid -> 1
- L7 carry: payload schema 未定

### A-79 `helix promote`
- usage: `helix promote [--json] [--id <artifact-id>] [--target <stable|legacy>]`
- input: artifact id
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: promotion table write
- error handling: target locked -> 2
- L7 carry: payload schema 未定

### A-80 `helix discover`
- usage: `helix discover [--json] [--keyword <q>] [--top <N>]`
- input: keyword
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: search read
- error handling: query invalid -> 1
- L7 carry: payload schema 未定

### A-81 `helix builder`
- usage: `helix builder [--json] [--artifact <id>] [--dry-run]`
- input: artifact
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: builder artifact write
- error handling: artifact build error -> 2
- L7 carry: payload schema 未定

### A-82 `helix code`
- usage: `helix code [find|stat|dup] [--json] [--query <q>]`
- input: mode/query
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: index cache
- error handling: query invalid -> 1
- L7 carry: payload schema 未定

### A-83 `helix asset`
- usage: `helix asset [--json] [--preset <name>] [--out <path>]`
- input: preset/out
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: asset file write
- error handling: preset missing -> 1
- L7 carry: payload schema 未定

### A-84 `helix entry`
- usage: `helix entry [--json] [--id <entry-id>] [--mode <create|update|delete>]`
- input: mode/id
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: entry write
- error handling: id conflict -> 1
- L7 carry: payload schema 未定

### A-85 `helix audit`
- usage: `helix audit [--json] [--range <from> <to>] [--type <security|contract>]`
- input: range/type
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: evidence read
- error handling: range syntax -> 1
- L7 carry: payload schema 未定

### A-86 `helix observe`
- usage: `helix observe [--json] [--metrics] [--events]`
- input: scope flags
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: metrics cache
- error handling: observability unavailable -> 2
- L7 carry: payload schema 未定

### A-87 `helix job`
- usage: `helix job [--json] [--list|--status <id>] [--cancel <id>]`
- input: job id
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: queue operation
- error handling: queue unavailable -> 2
- L7 carry: payload schema 未定

### A-88 `helix lock`
- usage: `helix lock [--json] [--acquire <name>] [--release <name>]`
- input: lock name
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: lock table update
- error handling: deadlock risk -> 2
- L7 carry: payload schema 未定

### A-89 `helix codex`
- usage: `helix codex --role <role> --task <text> [--plan-id <id>]`
- input: role/task
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: task artifact write
- error handling: role mismatch -> 1
- L7 carry: payload schema 未定

### A-90 `helix claude`
- usage: `helix claude --role <role> --task <text> --dry-run [--plan-id <id>]`
- input: task text
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: prompt file write
- error handling: template invalid -> 1
- L7 carry: payload schema 未定

### A-91 `helix team`
- usage: `helix team run --definition <file> [--json]`
- input: definition
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: team run metadata
- error handling: definition missing -> 1
- L7 carry: payload schema 未定

### A-92 `helix review`
- usage: `helix review [--json] [--uncommitted] [--strict]`
- input: scope
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: review artifact
- error handling: parser fail -> 2
- L7 carry: payload schema 未定

### A-93 `helix skill`
- usage: `helix skill [--json] [list|search] [--q <query>]`
- input: query
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: none
- error handling: not found -> 1
- L7 carry: payload schema 未定

### A-94 `helix auto-run`
- usage: `helix auto-run [--json] [--enable|--disable] [--window <N>]`
- input: window/enable
- output: text / payload schema
- exit code: 0 / 1 / 2
- side effect: heartbeat state
- error handling: schedule conflict -> 2
- L7 carry: payload schema 未定

### A-95 `helix budget status --homeostasis`（再定義確認）
- usage: `helix budget status --homeostasis [--days <N>] [--json]`
- input: --days
- output: text / payload schema
- exit code: 0 / 1 / 2 / 1020
- side effect: none
- error handling: policy miss -> 1
- L7 carry: payload schema 未定
