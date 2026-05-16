---
doc_id: D-CONTRACT-draft-v0.1
plan_id: PLAN-070
sprint: SprintC / .3
status: draft
created: 2026-05-16
primary_drive: fullstack
secondary_drives:
  - fe
  - db
  - be
---

# PLAN-070 SprintC: L3 D-CONTRACT draft v0.1

## §1 目的とスコープ

### 1.1 目的

本稿は PLAN-070 SprintC における D-CONTRACT の draft を起票し、`mock_to_implementation` promotion hook と `functional_freeze` enforce point の CLI 契約を 1 ファイルで固定する。

本稿の役割は、L2-MASTER / D-API / D-DB / spine / fe-draft / fullstack-draft の参照点を contract primitive に収束させ、Sprint A/B で生じた primitive の重複定義と enum 揺れを防ぐことにある。

### 1.2 スコープ

- `mock_to_implementation` promotion hook schema
- `functional_freeze` enforce point CLI contract
- `fe-draft` / `fullstack-draft` promotion contract alignment
- drive 切替時の decision recording contract
- cross-doc 整合性チェックの判定規約

### 1.3 Non-goals

- hook 実行本体の実装
- promotion enforcement の内部実装
- `functional_freeze` CLI の内部ロジック
- D-API / D-DB / spine の本体改修
- state-events / UI 実装 / SQL migration 本文

### 1.4 設計前提

- L2 G2 凍結を破壊しない
- SQLite 制約と実装乖離を新設 contract で隠蔽しない
- canonical enum を優先し、短縮表記は使わない
- promotion は append-only である
- `g2_evidence_preserved` は推奨でなく必須条件である

## §2.0 共通 D-CONTRACT primitive

本節は D-CONTRACT における共通 primitive を定義する。個別 contract の本体は §3 以降で、ここで定義した shape を `"$ref"` 参照する。

### 2.0.1 PromotionHook

```yaml
PromotionHook:
  type: object
  additionalProperties: false
  required:
    - kind
    - from_artifact_kind
    - to_artifact_kind
    - from_layer
    - to_layer
    - link_kind
    - append_only
    - g2_evidence_preserved
  properties:
    kind:
      type: string
      enum:
        - mock_to_implementation
        - baseline_promotion
        - spec_promotion
    from_artifact_kind:
      type: string
    to_artifact_kind:
      type: string
    from_layer:
      type: string
      enum:
        - planning
        - requirement
        - architecture
        - detailed
        - functional
    to_layer:
      type: string
      enum:
        - planning
        - requirement
        - architecture
        - detailed
        - functional
    link_kind:
      type: string
      enum:
        - covers
        - derives_from
        - reviews
        - implements
    append_only:
      type: boolean
    g2_evidence_preserved:
      type: boolean
```

### 2.0.2 FunctionalFreezeCheck

```yaml
FunctionalFreezeCheck:
  type: object
  additionalProperties: false
  required:
    - plan_id
    - drive
    - size
    - sprint_type
    - layer
    - pair_status
    - judgment
    - approved_by
  properties:
    plan_id:
      type: string
    drive:
      type: string
      enum:
        - fe
        - fullstack
        - db
        - be
    size:
      type: string
      enum:
        - S
        - M
        - L
    sprint_type:
      type: string
      enum:
        - planning
        - requirement
        - architecture
        - detailed
        - functional
        - impl
    layer:
      type: string
      enum:
        - planning
        - requirement
        - architecture
        - detailed
        - functional
    pair_status:
      type: string
      enum:
        - pending
        - design_only
        - test_only
        - paired
        - waived
        - failed
    judgment:
      type: string
      enum:
        - pass
        - fail
        - waived
    waived_reason:
      type: string
    approved_by:
      type: string
```

### 2.0.3 PairStatusTransition

`PairStatusTransition` は Sprint A §2.0 PairStatusTransition（`docs/v2/L3-detailed-design/D-API/D-API-draft.md` §2.0）を正本参照し、D-CONTRACT 側では shape を再定義せず同一構造を採用する。pair_status の遷移は L1 FR-VS06 通り `pending -> design_only / test_only -> paired`、`pending -> failed`、`pending -> waived` を許容する。ただし `PairStatusTransition` DTO は終端状態 (`pending` / `paired` / `waived` / `failed`) のみを扱い、中間状態 (`design_only` / `test_only`) は D-DB `design_sprint_entries.pair_status` 列で記録する。

### 2.0.4 DriveSwitchPolicy

```yaml
DriveSwitchPolicy:
  type: object
  additionalProperties: false
  required:
    - from_drive
    - to_drive
    - allowed
    - decision_required
    - target_table
  properties:
    from_drive:
      type: string
      enum:
        - be
        - fe
        - db
        - fullstack
    to_drive:
      type: string
      enum:
        - be
        - fe
        - db
        - fullstack
    allowed:
      type: boolean
    decision_required:
      type: boolean
    target_table:
      type: string
      enum:
        - design_sprint_drive_decisions
```

### 2.0.5 共通判定規約

- `kind='mock_to_implementation'` は promotion hook の canonical enum とする
- `link_kind='derives_from'` を mock 由来の基本リンクとする
- `append_only=true` は必須であり、例外は存在しない
- `g2_evidence_preserved=true` は必須であり、省略不可
- `decision_required=true` の drive switch は D-DB `design_sprint_drive_decisions` に記録する

### 2.0.6 YAML 互換ルール

```yaml
contract_rules:
  enum_policy:
    canonical_only: true
    shorthand_forbidden: true
  reference_policy:
    cross_doc_ref: true
    local_duplication_forbidden: true
  validation_policy:
    append_only_required: true
    g2_evidence_required: true
    sqlite_constraint_aware: true
```

## §3 mock_to_implementation promotion hook 契約

### 3.1 契約概要

`mock_to_implementation` hook は、mock artifact を implementation artifact へ昇格させるための promotion contract である。対象は `fe-draft` / `fullstack-draft` の mock 由来 track を含む。

この hook は「何を昇格させるか」を宣言するだけではなく、「昇格後も evidence を失わないこと」を contract に含める。

### 3.2 schema

```yaml
PromotionHook:
  description: SprintC で正式化する mock_to_implementation hook の共通 primitive

mock_to_implementation_hook:
  type: object
  additionalProperties: false
  required:
    - kind
    - from_artifact_kind
    - to_artifact_kind
    - from_layer
    - to_layer
    - link_kind
    - append_only
    - g2_evidence_preserved
    - source_docs
    - promotion_trigger
  properties:
    kind:
      const: mock_to_implementation
    from_artifact_kind:
      const: mock
    to_artifact_kind:
      const: component_impl
    from_layer:
      enum:
        - architecture
        - detailed
    to_layer:
      enum:
        - functional
        - detailed
    link_kind:
      const: derives_from
    append_only:
      const: true
    g2_evidence_preserved:
      const: true
    source_docs:
      type: array
      items:
        type: string
    extension_artifact_kinds:
      type: array
      items:
        type: string
        enum:
          - function_impl
          - integration_impl
    promotion_trigger:
      type: object
      required:
        - sprint_entry
        - cli_hook
        - db_record
      properties:
        sprint_entry:
          type: string
        cli_hook:
          type: string
        db_record:
          type: string
```

### 3.3 正本転写ルール

- `kind`, `from_artifact_kind`, `to_artifact_kind`, `link_kind` は `docs/v2/B-design/vmodel-semantics-spine.yaml` の `promotion_kinds.mock_to_implementation` から正本転写する
- `to_artifact_kind` は `component_impl` 単一値に固定し、`function_impl` / `integration_impl` の拡張は optional field `extension_artifact_kinds` に分離する
- `append_only` は `true` を固定する
- `g2_evidence_preserved` は `true` を固定する
- `source_docs` は fe-draft / fullstack-draft / spine / L2-MASTER の参照を含む

### 3.4 trigger 条件

hook trigger は次の順で発火する。

1. Sprint A endpoint で promotion が宣言される
2. CLI hook が実行される
3. D-DB に append-only record が登録される
4. D-API の pair/status 参照が更新される
5. cross-doc 整合性チェックが pass する

### 3.5 例外条件

- `waived`: PM 承認が記録されている場合のみ通過可
- `failed`: 自動 rollback を要求する
- `blocked`: `g2_evidence_preserved=false` または source_docs 欠落
- `invalid`: canonical enum 以外を使用した場合

### 3.6 hook 実行の判定表

| 条件 | 判定 | 補足 |
|---|---|---|
| `append_only=true` | pass 必須 | false は fail-close |
| `g2_evidence_preserved=true` | pass 必須 | false は fail-close |
| source_docs 完備 | pass 必須 | 参照欠落は blocked |
| canonical enum | pass 必須 | 短縮表記禁止 |
| PM waiver あり | waived 通過 | 承認文脈を記録 |

### 3.7 fe-draft / fullstack-draft 整合チェックリスト

- `promotion_for_fe` / `promotion_for_fullstack` はともに `mock_to_implementation`
- `requires_functional_freeze_for_fe` / `requires_functional_freeze_for_fullstack` はともに `true`
- `pair_status` は `pending -> design_only / test_only -> paired` と `waived / failed` を崩さない
- `review_unit` と `pair_status` の接続点を変更しない
- `track_specific` で定義された contract artifact は削除しない

### 3.8 SQLite 制約との注意点

- DB 側の append-only 追加と contract 側の append_only は同値ではない
- DB 制約が存在しないからといって contract を緩めない
- 実装乖離の吸収は contract でなく補助的 migration note で扱う

### 3.9 参照先

- `docs/v2/B-design/vmodel-semantics-spine.yaml`
- `docs/v2/B-design/vmodel-semantics-fe-draft.yaml`
- `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml`
- `docs/v2/L2-MASTER.md`
- `docs/v2/L1-REQUIREMENTS.md`

## §4 functional_freeze enforce point CLI 契約

### 4.1 CLI 目的

`functional_freeze` は、L1 master の `AC-16` と L2-MASTER の drive 切替・guard policy を受けて、G3 サブゲートの enforce point を CLI で固定する。

本契約は `helix gate G3 --subgate functional_freeze --plan-id <id> --drive <drive>` を正本操作として扱う。

### 4.2 CLI grammar

```text
helix gate G3 --subgate functional_freeze --plan-id <plan_id> --drive <drive>
```

### 4.3 判定式

判定式は次の通りである。

```text
size = L AND drive IN (fe, fullstack, db)
```

### 4.4 判定対象

- `fe`: 対象
- `fullstack`: 対象
- `db`: 対象
- `be`: 対象外

### 4.5 pair_status check

`functional_freeze` は対象 drive に対して pair_status の一致を確認する。具体的には、`paired` を要求する。`waived` は PM 承認 (`approved_by` 必須) を伴う例外として通過可とする。

`design_only` / `test_only` は `paired` への中間状態であり、functional_freeze 通過対象外である。

### 4.6 exit code

| code | meaning | 条件 |
|---|---|---|
| 0 | pass | 判定式不成立、または成立 + pair_status='paired'、または成立 + waived 通過（judgment='waived'、approved_by 確認済み） |
| 1 | fail | 判定式成立 + pair_status='failed' |
| 2 | internal error | 内部エラー（DB 不整合等） |

### 4.7 output format

出力は JSON と human-readable の双方を提供する。human-readable は operator 用、JSON は gate runner / audit 用である。

#### JSON

```json
{
  "result": {
    "plan_id": "PLAN-070",
    "drive": "fullstack",
    "gate": "G3.functional_freeze",
    "size": "L",
    "judgment": "pass",
    "pair_status": "paired",
    "approved_by": "pm",
    "exit_code": 0
  }
}
```

#### human-readable

```text
G3.functional_freeze: pass
plan_id=PLAN-070 drive=fullstack size=L pair_status=paired approved_by=pm
```

### 4.8 gate runner integration

- D-API §3.3 の Gate runner endpoint から呼び出す
- `plan_id` は L1 master の AC-16 と一致させる
- `drive` は `fe` / `fullstack` / `db` / `be` の canonical enum を使用する
- `be` は監査用途で受理されるが、functional_freeze の対象ではない
- waived 通過は exit 0 とし、`judgment='waived'` で区別する
- `design_only` / `test_only` は `paired` への中間状態であり、functional_freeze 通過対象外である

### 4.9 drive 別 enforce

| drive | enforce 条件 | 補足 |
|---|---|---|
| fe | pair_status in ('paired', 'waived') | waived は approved_by 確認済みのみ許可 |
| fullstack | pair_status in ('paired', 'waived') | waived は approved_by 確認済みのみ許可 |
| db | pair_status in ('paired', 'waived') | waived は approved_by 確認済みのみ許可 |
| be | skip | 対象外 |

### 4.10 L1 との整合

- AC-16 を master として参照する
- FR-VS03 の判定式と矛盾しない
- FR-VS06.4 の waived 運用を破壊しない
- `design_only` / `test_only` は `paired` への中間状態であり、functional_freeze 通過対象外である

### 4.11 失敗条件

- `plan_id` 欠落
- `drive` が canonical enum 外
- `size` が L 以外
- `pair_status` が pending / design_only / test_only / failed のいずれかである（`paired` と PM 承認付き `waived` 以外）
- waiver なのに PM 承認がない

### 4.12 CLI contract table

| field | required | source |
|---|---|---|
| plan_id | yes | L1 master |
| drive | yes | L2-MASTER §8 / §9.5 |
| size | yes | SKILL_MAP / L1 AC-16 |
| sprint_type | yes | sprint plan |
| layer | yes | D-API / D-DB / D-CONTRACT |
| pair_status | yes | PairStatusTransition |
| judgment | yes | gate runner |
| approved_by | yes | waiver path |

## §4.5 push_gate_contract (P0-04 反映、2026-05-16)

### 4.5.1 `run_all_gates()` 関数契約

実測シグネチャ (`cli/lib/push_gate.py` L291-324 Read 確認済み):

```yaml
push_gate_run_all_gates:
  function: run_all_gates
  module: cli.lib.push_gate
  arguments:
    execute:
      type: boolean
      default: false
      description: "true 時かつ全 gate PASS 時のみ git push を実行"
    remote:
      type: string
      default: "origin"
    branch:
      type: string
      default: "main"
  return_type: dict
  return_keys:
    ok: { type: boolean, description: "全 gate PASS かつ push 成功 (execute=true 時)" }
    failed_count: { type: integer, minimum: 0 }
    gates:
      type: array
      items:
        type: object
        required: [id, passed, detail, fix]
        properties:
          id: { type: string, enum: [G-tests, G-catalog, G-secret, G-ff, G-attr, G-nondestructive] }
          passed: { type: boolean }
          detail: { type: string }
          fix: { type: string }
    execute_requested: { type: boolean }
    remote: { type: string }
    branch: { type: string }
    push:
      type: object
      required: [attempted, ok, detail]
      properties:
        attempted: { type: boolean }
        ok: { type: boolean }
        detail: { type: string }
  side_effects:
    helix_db_write: false
    git_push: "execute=true かつ全 gate PASS 時のみ実行"
    stdout: "main() 経由の _print_report() のみ。run_all_gates() 直接呼び出しでは stdout 出力なし"
```

### 4.5.2 既存 CLI 呼び出し pattern (caller signature)

```yaml
existing_cli_callers:
  helix_push:
    file: cli/helix-push
    pattern: "python3 push_gate.py [--execute] [--remote REMOTE] [--branch BRANCH]"
    note: "subprocess 経由。run_all_gates() を直接呼ばず CLI として起動する thin wrapper"
  helix_pr:
    file: cli/helix-pr
    pattern: "inspect.signature(run_all_gates).parameters で動的キーワード確認後に呼び出し (L147-153)"
    note: "Python import 経由で run_all_gates() を直接呼ぶ"
```

### 4.5.3 endpoint 呼び出しとの差分

| 観点 | 既存 CLI (helix-push / helix-pr) | 新規 endpoint (push_trigger / pr_trigger) |
|------|--------------------------------|------------------------------------------|
| 呼び出し方式 | subprocess / Python import | endpoint がサーバー内で Python import 呼び出し |
| helix.db 書き込み | なし | endpoint 側で automation_runs に INSERT |
| stdout | _print_report() で表示 | レスポンス JSON に変換して返却 |
| git push 実行 | execute フラグに従う | execute フラグに従う (同一ロジック) |

## §4.6 mock_to_implementation 全 capability 展開表（PLAN-071）

### 4.6.1 概要

本節は PLAN-070 §3 の代表 3 capability に加え、PLAN-071 で詳細化した carry 11 capability（C-01〜C-11）の mock_to_implementation hook を全 14 capability 分まとめた展開表である。

全行に共通する contract constraints:
- `append_only: true`（例外なし）
- `g2_evidence_preserved: true`（例外なし）
- `link_kind: derives_from`（canonical enum。mock 由来の基本リンク）

### 4.6.2 全 capability 展開表

| capability | from_artifact_kind | to_artifact_kind | from_layer | to_layer | link_kind | append_only | g2_evidence_preserved | 備考 |
|---|---|---|---|---|---|---|---|---|
| 契約 extractor / contract registry | mock_contract | implementation_contract | detailed | functional | derives_from | true | true | PLAN-070 SprintA 既存 |
| 14 detector system | mock_detector | implementation_detector | architecture | functional | derives_from | true | true | PLAN-070 SprintA 既存 |
| Gate runner | mock_gate | implementation_gate | architecture | functional | derives_from | true | true | PLAN-070 SprintA 既存 |
| V-model schema / QA baseline schema (C-01) | mock_baseline_policy | implementation_baseline_policy | architecture | detailed | derives_from | true | true | PLAN-071 carry |
| handover protocol (C-02) | mock_handover | implementation_handover | requirement | functional | derives_from | true | true | PLAN-071 carry |
| skill 推挙 / skill chain (C-03) | mock_skill_search | implementation_skill_chain | detailed | functional | derives_from | true | true | PLAN-071 carry |
| Reverse HELIX (C-04) | mock_reverse | implementation_reverse | architecture | functional | derives_from | true | true | PLAN-071 carry |
| Scrum HELIX (C-05) | mock_scrum | implementation_scrum | planning | functional | derives_from | true | true | PLAN-071 carry |
| Agent Transformation 散在 (C-06) | mock_dispatch | implementation_dispatch | architecture | functional | derives_from | true | true | PLAN-071 carry |
| PMO / advisor role system (C-07) | mock_advisor | implementation_advisor | requirement | functional | derives_from | true | true | PLAN-071 carry |
| Codex / Claude harness + PreToolUse guard (C-08) | mock_harness | implementation_harness | architecture | functional | derives_from | true | true | PLAN-071 carry |
| code-index (C-09) | mock_code_index | implementation_code_index | detailed | functional | derives_from | true | true | PLAN-071 carry |
| budget guard / auto-thinking support (C-10) | mock_budget | implementation_budget | detailed | functional | derives_from | true | true | PLAN-071 carry |
| code-index + contract registry 追加整合 (C-11) | mock_alignment | implementation_alignment | detailed | functional | derives_from | true | true | PLAN-071 carry |

### 4.6.3 from_artifact_kind / to_artifact_kind 命名ルール

- `from_artifact_kind` は `mock_{capability_slug}` 形式
- `to_artifact_kind` は `implementation_{capability_slug}` 形式
- capability_slug は capability 名を小文字スネークケースで圧縮したもの
- 重複がないことを本表で確保する（各行の `from_artifact_kind` はユニーク）

### 4.6.4 acceptance check

| check | expected | status |
|---|---|---|
| 全 14 capability を含む | 14 行 | pass |
| `append_only=true` が全行 | 14/14 | pass |
| `g2_evidence_preserved=true` が全行 | 14/14 | pass |
| `from_artifact_kind` が全行ユニーク | 14/14 | pass |
| `link_kind=derives_from` が全行 | 14/14 | pass |
| PLAN-070 既存 3 件との重複なし | 0 重複 | pass |

## §5 cross-doc 整合性

### 5.1 整合対象

以下の文書を相互整合対象とする。

- `docs/v2/B-design/vmodel-semantics-spine.yaml`
- `docs/v2/B-design/vmodel-semantics-fe-draft.yaml`
- `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml`
- `docs/v2/L2-MASTER.md`
- `docs/v2/L1-REQUIREMENTS.md`
- `docs/v2/L3-detailed-design/D-API/D-API-draft.md`
- `docs/v2/L3-detailed-design/D-DB/D-DB-draft.md`
- `docs/v2/v2-gate-overlay.md`

### 5.2 promotion_kinds / review_unit / pair_status 接続点

`promotion_kinds.mock_to_implementation` は、`review_unit` が screen / plan / detailed のいずれであっても、pair_status の遷移と promote link を明示する必要がある。

`review_unit` はレビュー単位を示すだけであり、promotion そのものを暗黙に許可しない。

### 5.3 文書別整合表

| document | must match | check |
|---|---|---|
| spine.yaml | promotion_kinds / canonical enums | `mock_to_implementation` の正本一致 |
| fe-draft | promotion_for_fe / requires_functional_freeze_for_fe | true / true 一致 |
| fullstack-draft | promotion_for_fullstack / requires_functional_freeze_for_fullstack | true / true 一致 |
| L2-MASTER | drive 切替 / guard policy / G2 凍結 | §8 / §9.5 / §10 と一致 |
| L1-REQUIREMENTS | AC-16 / FR-VS03 / FR-VS06.4 | 判定式と waiver 運用一致 |
| D-API | PairStatusTransition / Gate runner | placeholder と enforce 接続一致 |
| D-DB | design_sprint_drive_decisions | decision table 一致 |
| v2-gate-overlay | functional_freeze / pair_status / drive switch | fail-close と waiver 互換一致 |

### 5.4 矛盾検出時の対応

矛盾が見つかった場合は、Sprint .4 の必須 exit に carry し、D-CONTRACT 単独での吸収を行わない。

### 5.5 cross-doc check workflow

1. spine の canonical enum を読む
2. fe-draft / fullstack-draft の promotion 設定を読む
3. L2-MASTER §8 / §9.5 / §10 を読む
4. L1-REQUIREMENTS AC-16 / FR-VS03 / FR-VS06.4 を読む
5. D-API / D-DB の placeholder / decision table を読む
6. 一致しない場合は carry へ送る

### 5.6 チェック結果の記録フォーマット

```yaml
cross_doc_alignment:
  spine: pass
  fe_draft: pass
  fullstack_draft: pass
  l2_master: pass
  l1_requirements: pass
  d_api: pass
  d_db: pass
  carry_required: false
```

### 5.7 discrepancy handling

- enum 差分: canonical enum へ合わせる
- waived 条件差分: PM 承認の有無を優先
- drive 範囲差分: L1 master を優先
- SQL と contract の差分: contract を上位に置く

## §6 drive 切替契約

### 6.1 概要

drive 切替は、source_drive から target_drive へ移る際の contract である。ここでは `design_sprint_drive_decisions` に decision を記録することを必須条件とする。

### 6.2 source / target 遷移条件

- `be -> fe`: mock 由来の promotion link がある
- `be -> fullstack`: be / fe / contract の整合がある
- `fe -> fullstack`: mock_to_implementation の evidence が揃っている
- `db -> fullstack`: schema / migration の freeze が揃っている
- 逆方向の退避は原則 carry 対象とする

### 6.3 DriveSwitchPolicy schema

`DriveSwitchPolicy` は policy 評価 metadata であり、`from_drive`、`to_drive`、`allowed BOOLEAN`、`decision_required BOOLEAN`、`target_table TEXT CHECK ('design_sprint_drive_decisions')` を持つ。評価専用であり、DB insert は行わない。

### 6.4 DriveSwitchDecisionRecord schema

`DriveSwitchDecisionRecord` は D-DB §5 の `design_sprint_drive_decisions` への insert payload であり、`source_entry_id INTEGER`、`target_entry_id INTEGER NULL`、`decision TEXT CHECK ('preserved'/'waived'/'failed')`、`decided_by TEXT`、`reason TEXT`、`reopen_condition TEXT NULL` を D-DB 列と完全一致で持つ。

### 6.5 design_sprint_drive_decisions 登録

decision record には以下を必須とする。

```yaml
drive_switch_policy:
  from_drive: fe
  to_drive: fullstack
  allowed: true
  decision_required: true
  target_table: design_sprint_drive_decisions

drive_switch_decision_record:
  source_entry_id: 42
  target_entry_id: 43
  decision: preserved
  decided_by: pm
  reason: "mock_to_implementation evidence preserved and functional_freeze paired"
  reopen_condition: null
```

### 6.6 decision enum

`decision` の canonical enum は次の通りとする。

- `preserved`
- `waived`
- `failed`

### 6.7 判定規則

- `preserved`: switch が contract 上問題なく継続可能
- `waived`: PM 承認で例外継続
- `failed`: switch 不可、戻しまたは carry 必須

### 6.8 DB 連携

- D-DB §5 の `design_sprint_drive_decisions` への書き込みを要求する
- decision は append-only である
- reopen_condition は TEXT（JSON or NULL）で固定し、正式 JSON Schema は §8 carry へ送る
- `DriveSwitchPolicy` は評価専用であり、DB insert を行わない
- `DriveSwitchDecisionRecord` が D-DB §5 の insert payload である

### 6.9 L2-MASTER との接続

- `docs/v2/L2-MASTER.md` §8 の drive 切替時の扱いに一致させる
- `docs/v2/L2-MASTER.md` §9.5 の guard policy と齟齬があれば L2 を優先する
- `docs/v2/L2-MASTER.md` §10 の G2 凍結条件を破壊しない

### 6.10 drive switch table

| source | target | allowed | decision_required | target_table |
|---|---|---|---|---|
| be | fe | true | true | design_sprint_drive_decisions |
| be | fullstack | true | true | design_sprint_drive_decisions |
| fe | fullstack | true | true | design_sprint_drive_decisions |
| db | fullstack | true | true | design_sprint_drive_decisions |
| fullstack | fe | false | true | design_sprint_drive_decisions |

### 6.11 blocked cases

- source / target が canonical enum 外
- decision が未記録
- reopened condition が失われた
- waiver 承認が欠落した
- `DriveSwitchPolicy` と `DriveSwitchDecisionRecord` の混同

## §7 受入条件

### 7.1 hook contract

- `PromotionHook.kind='mock_to_implementation'` を正本採用する
- `append_only=true` を強制する
- `g2_evidence_preserved=true` を強制する
- `from_artifact_kind` / `to_artifact_kind` / `link_kind` を spine と一致させる

### 7.2 functional_freeze contract

- `helix gate G3 --subgate functional_freeze --plan-id <id> --drive <drive>` の CLI 契約が記載されている
- `size=L AND drive in (fe/fullstack/db)` の判定式が明記されている
- `be` が対象外であることが明記されている
- exit code 0/1/2 が定義されている

### 7.3 cross-doc contract

- fe-draft / fullstack-draft の promotion 契約と矛盾しない
- spine.yaml の `promotion_kinds.mock_to_implementation` と一致する
- L2-MASTER §8 / §9.5 / §10 と一致する
- L1-REQUIREMENTS AC-16 / FR-VS03 / FR-VS06.4 と一致する

### 7.4 drive switch contract

- `design_sprint_drive_decisions` を target_table として指し示す
- decision enum が `preserved / waived / failed` である
- source / target / allowed / decision_required が schema で固定される

### 7.5 no regression contract

- L2 G2 凍結の内容破壊がない
- SQLite 制約と文書 contract の矛盾を放置しない
- canonical enum の短縮表記がない

### 7.6 acceptance matrix

| acceptance item | expected | evidence |
|---|---|---|
| hook schema fixed | yes | §3.2 |
| append_only enforced | yes | §3.6 / §7.1 |
| g2_evidence_preserved enforced | yes | §3.6 / §7.1 |
| functional_freeze CLI fixed | yes | §4.2 / §4.6 |
| fe/fullstack promotion alignment | yes | §3.7 / §5.3 |
| drive switch contract fixed | yes | §6.4 / §6.5 |

## §8 carry / open questions

### 8.1 carry items

- hook 実行内部実装は Phase E へ carry
- functional_freeze CLI 実装本体は L4 着手後へ carry
- reopen_condition JSON schema の正式化は次 sprint へ carry
- extension_artifact_kinds の最終スキーマは §8 carry で確定

### 8.2 open questions

- waiver の監査ログ粒度を CLI でどこまで固定するか
- source_docs の最小セットを厳密に固定するか
- `component_impl` と `function_impl` の分岐条件を別ファイルに分離するか

### 8.3 next sprint

次 sprint では `reopen_condition` の schema を `json_schema_version` 付きで正式化し、D-DB の decision event と整合させる。extension_artifact_kinds の扱いも carry で最終決定する。

### 8.4 implementation boundary

- contract は freeze する
- execution は freeze しない
- document alignment は freeze する

### 8.5 audit note

`mock_to_implementation` の evidence 保全は、hook 実行結果の後追い修正ではなく、昇格時点の append-only 記録で担保する。

## §9 参照一覧

### 9.1 正本

- `docs/plans/PLAN-070-l3-schema-and-contract-design.md`
- `docs/v2/L3-detailed-design/D-API/D-API-draft.md`
- `docs/v2/L3-detailed-design/D-DB/D-DB-draft.md`
- `docs/v2/L2-MASTER.md`
- `docs/v2/L1-REQUIREMENTS.md`
- `docs/v2/B-design/vmodel-semantics-spine.yaml`
- `docs/v2/B-design/vmodel-semantics-fe-draft.yaml`
- `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml`

### 9.2 参照関係の要点

- D-API は `PairStatusTransition` を正本にする
- D-DB は `design_sprint_drive_decisions` を正本にする
- spine は promotion kind の正本にする
- fe/fullstack draft は promotion の適用対象を示す
- L1 は functional_freeze の判定 master である

### 9.3 章タイトル索引

| section | title |
|---|---|
| §1 | 目的とスコープ |
| §2.0 | 共通 D-CONTRACT primitive |
| §3 | mock_to_implementation promotion hook 契約 |
| §4 | functional_freeze enforce point CLI 契約 |
| §5 | cross-doc 整合性 |
| §6 | drive 切替契約 |
| §7 | 受入条件 |
| §8 | carry / open questions |

### 9.4 用語の canonical 化

- `mock_to_implementation`
- `functional_freeze`
- `design_sprint_drive_decisions`
- `pair_status`
- `append_only`
- `g2_evidence_preserved`

### 9.5 禁止事項

- 短縮形の `mock2impl`
- `freeze` 単独表記での省略
- `waive` と `waived` の混用
- `full-stack` のハイフン表記
- `db-switch` のような非 canonical 表記

## §10 Appendix: machine-check hints

### 10.1 promotion hook check

```yaml
check:
  kind: mock_to_implementation
  append_only: true
  g2_evidence_preserved: true
  link_kind: derives_from
```

### 10.2 functional freeze check

```yaml
check:
  gate: G3.functional_freeze
  expression: "size=L AND drive in (fe, fullstack, db)"
  target_pair_status: paired
  be_exempt: true
```

### 10.3 drive switch check

```yaml
check:
  target_table: design_sprint_drive_decisions
  decision_enum:
    - preserved
    - waived
    - failed
```

### 10.4 cross-doc summary

```yaml
summary:
  promotion_kinds: aligned
  fe_draft: aligned
  fullstack_draft: aligned
  l2_master: aligned
  l1_requirements: aligned
  d_api: aligned
  d_db: aligned
```
