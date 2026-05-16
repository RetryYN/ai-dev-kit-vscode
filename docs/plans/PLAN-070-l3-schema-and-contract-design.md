---
plan_id: PLAN-070
title: "PLAN-070: L3 詳細設計 (D-API / D-DB / D-CONTRACT) Phase C 着手"
status: frozen
size: L
drive: fullstack
created: 2026-05-16
frozen_at: 2026-05-16
gate_status: G3_approved
owner: PM
phases: L3
gates: G3
acceptance:
  - L3 D-API draft が capability 別に role 別 endpoint contract / request-response schema / error model を網羅
  - L3 D-DB draft が helix-db v22+ migration (drive 切替記録列 / baseline_policy_family score 計算式 / artifact_links + design_sprint_entries column) を YAML / SQL 草案で示す
  - L3 D-CONTRACT draft が mock_to_implementation promotion hook + functional_freeze enforce point の CLI 契約を明文化
  - L3 D-API 拡張 draft (Sprint .5) が push/pr trigger endpoint / hook callback / audit endpoint / Stop hook telemetry を扱う
  - L3 D-DB 拡張 draft (Sprint .6) が push_runs / pr_runs / hook_log / audit_log / session_telemetry の v25+ migration 草案を示す
  - cross-doc 整合性チェック: spine.yaml / fe-draft / fullstack-draft / L2 MASTER §3-§10 と矛盾しないこと
  - G3 entry blocker (M-01〜M-08 + CI-001〜CI-008) の resolved 状態を引き継ぎ、本 PLAN 成果物が新規矛盾を導入しないこと
related:
  - PLAN-068-vmodel-strengthening-improvements
  - PLAN-069-g3-entry-blocker-resolution (完遂)
  - PLAN-065-qa-strictness
  - PLAN-066-security-scan-systematic
  - PLAN-067-helix-automation-layer
  - docs/v2/L2-MASTER.md (G2 凍結正本)
  - docs/v2/B-design/vmodel-semantics-spine.yaml
  - docs/v2/B-design/helix-db-v21-spec.md (v22+ への接続)
---

# PLAN-070: L3 詳細設計 (D-API / D-DB / D-CONTRACT) Phase C 着手

## §1 背景・目的

L2 G2 凍結（commit `e28ca8d`, 2026-05-16）を前提に、Phase C の L3 詳細設計を起動するための起点 PLAN として PLAN-070 を起票する。  
本 PLAN では、`docs/PLAN-069` で整えた spine/cross-drive ブロッカー解消後の状態を起点に、`design` と `DB` と `contract` の実装設計を L3 粒度で確定する。

本 PLAN の対象は「次の L4 実装で実装可能な契約の形」を固定することにある。  
具体的には以下を確定し、次工程で draft ↔ 実装の drift を抑える。

1. capability 単位での D-API endpoint とエラー契約の固定  
2. helix-db v22+ を前提とした migration 草案（YAML/SQL）の確定  
3. mock_to_implementation と functional_freeze の CLI 契約を L3 で整える  
4. 全部門（be / fe / db / fullstack）で spine 参照整合を維持し、新規矛盾を増やさない

## §2 スコープ
primary scope: contract / DB / API across be+fe+db+fullstack drives (frontmatter `drive: fullstack` は実装起点を示し、本 PLAN は cross-drive 契約とする)

### D-API（backend / fullstack API）
- 能力別 endpoint contract（method/path/headers）
- request schema / response schema（正常系・準正常系）
- error model（ステータスコード、error code、message、error context）
- role 別の受領責務（tl / se / pg / fe / docs など）での参照観点分離

### D-DB（helix-db v22+）
- `contract_entries` の drive 切替記録列定義（`drive`, `origin_mode`, `evidence_status`）
- `design_sprint_entries` / `design_sprint_artifact_links` の v22 拡張草案
- `baseline_policy_family` と `score formula` の DB 集約への写像
- `view_vmodel_integrity` 更新を前提とした SQL 定義方針

### D-CONTRACT（CLI 契約）
- `mock_to_implementation` の promotion hook schema（from_artifact_kind, to_artifact_kind, link_kind, append_only）
- `functional_freeze` の enforce point（drive/layer/filter 条件と判定結果）の CLI オペレーション契約
- cross doc 参照（spine / fullstack-draft / fe-draft / v2-gate-overlay）への契約整合条件

### Non-goals
- UI 実装、state-events.md の中身変更、可視化の描画仕様  
- hook 実行ロジック内部実装（Phase E / Phase J の接続点）  
- API 実装コードや migration 実行コード本体（本 PLAN は設計起点に限定）

## §3 Sprint 構成

本 PLAN は A/B/C/D/.5/.6 を採用し、HELIX `.N` と対応させる（A=.1, B=.2, C=.3, D=.4, E=.5, F=.6）。  
Sprint 構成は既存 A/B/C/D を維持しつつ 6 スプリントへ拡張し、SprintD を必須 exit sprint として最終集約位置に置く。  
`PLAN-069` で固定した 4 スプリント構造は破壊せず、L3 詳細設計の対象を運用機能まで明示的に広げる。  
`helix gate G3 --subgate functional_freeze` は be 固定解決で pass 判定するのではなく、fe/fullstack/db を drive 別に評価する（be は起点であり、全体 pass 条件ではない）。

| Sprint | 対象軸 | 主目的 | 成果物 |
|---|---|---|---|
| M3-SprintA | .1 | D-API | capability 別 contract draft 固定 | endpoint contract / schema / error model の表 |
| M3-SprintB | .2 | D-DB | helix-db v22+ migration 草案 | migration YAML + SQL（draft） |
| M3-SprintC | .3 | D-CONTRACT | promotion + functional_freeze 契約固定 | CLI 契約表 + サンプル実行条件 |
| M3-SprintD（必須 exit sprint） | .4 | 横断 | spine/fn-draft/cross-check 集約 | 検証表 + adversarial review 纏め |
| M3-SprintE | .5 | D-API 拡張 | 運用機能 endpoint contract 固定 | push/pr/hook/audit/telemetry contract draft |
| M3-SprintF | .6 | D-DB 拡張 | 運用機能 schema migration v25+ 固定 | automation_runs / audit_log / session_telemetry draft |

### SprintA（D-API draft）

- capability を軸に、be/fullstack の responsibility を分離して一覧化する。
- endpoint 契約ごとに request / response / error を 1 ファイルに収束できる形で起票する。
- 受け入れ基準（`track` / `layer` / `pair`）が後続 gate で参照できる粒度まで短文化しない。

### SprintB（D-DB draft）

- helix-db v22+ の `contract_entries` / `design_sprint_entries` / `design_sprint_artifact_links` の列・制約を YAML 草案化する。
- `baseline_policy_family` と score 算出式を schema と SQL の双方に紐づける。
- 機密キーや既存レコード破壊を避ける additive / idempotent 方針を migration 草案で明示する。

### SprintC（D-CONTRACT draft）

- `mock_to_implementation` の schema hook を L3 で固定し、appended row の取り扱いを SQL だけで検証可能な形にする。
- `functional_freeze` の enforce point を CLI 変数（plan_id, drive, sprint_type, layer, pair_status）で明文化する。
- `fe-draft` と `fullstack-draft` の promotion 契約に齟齬がないことを D-CONTRACT 出力でチェックする。

### M3-SprintD（必須 exit sprint）／§3.D

- `spine.yaml` / `fe-draft` / `fullstack-draft` / `L2-MASTER §3-§10` を cross-document で 1 方向チェック。  
- `L1-REQUIREMENTS`（AC-15〜AC-16/17, FR-VS01〜VS06.4, P2-4/P2-5/P2-7）および `G3 エントリ前提` と突合し、G3 entry artifact（検証表）を作成する。  
- `spine / fe-draft / fullstack-draft / v2-gate-overlay / DB migration / CLI 契約` を exit sprint で再確認する。  
- 新規矛盾が見つかった場合は carry-forward を明示し、受入条件一覧へ再起票要件を記載し adversarial review 用に集約する。  

### M3-SprintE（D-API 拡張）／§3.E

- `cli/helix-push` と `cli/helix-pr` の起点となる運用 endpoint contract を明文化する。  
- `PreToolUse` / `PostToolUse` / `Stop` hook の callback 契約を endpoint レベルで固定し、hook 実行内部には踏み込まない。  
- `helix-codex audit/footer` の出力を受ける audit endpoint を定義し、role 別の traceability を保持する。  
- Stop hook telemetry は session 単位の終了情報を保持し、既存 primitive を再利用する。  
- 受入は SprintA の primitive（Envelope / ErrorModel / DetectorRef / PairStatusTransition / PromotionHookRef）に参照を固定する。  
- Non-goals は hook 実装ロジック、CLI parsing 内部、Codex CLI exec wrapper 実装とする。  

#### SprintE endpoint contract

| Method | Path | 用途 | 参照 primitive |
|---|---|---|---|
| POST | `/api/v1/automation/push/{plan_id}/trigger` | cli/helix-push 起動 | Envelope / ErrorModel / PromotionHookRef |
| POST | `/api/v1/automation/pr/{plan_id}/trigger` | cli/helix-pr 起動 | Envelope / ErrorModel / PromotionHookRef |
| POST | `/api/v1/automation/hooks/{hook_kind}/callback` | PreToolUse / PostToolUse / Stop hook | DetectorRef / PairStatusTransition |
| POST | `/api/v1/automation/audit/log` | helix-codex audit/footer 受領 | Envelope / ErrorModel |
| POST | `/api/v1/automation/session/telemetry` | Stop hook telemetry | DetectorRef / PairStatusTransition |

### M3-SprintF（D-DB 拡張）／§3.F

- `push_runs` / `pr_runs` / `hook_runs` を統合する `automation_runs` の v25 提案を示す。  
- `helix-codex audit` 出力を保持する `audit_log` の v26 提案を示す。  
- Stop hook 由来の `session_telemetry` の v27 提案を示す。  
- migration は additive / idempotent / 既存レコード非破壊を維持し、SprintB primitive（MigrationStep / ColumnSpec）に準拠する。  
- `cli/lib/helix_db.py` 内部実装の詳細変更や既存 schema の rename / drop は Non-goals とする。  

#### SprintF migration draft

| Version | Table | 主要列 |
|---|---|---|
| v25 | `automation_runs` | id, run_kind, plan_id, trigger_actor, started_at, ended_at, status, exit_code, summary |
| v26 | `audit_log` | id, run_id, audit_kind, payload, created_at |
| v27 | `session_telemetry` | id, session_id, started_at, ended_at, tokens_used, cost_usd, model, role, related_plan_id |

#### SprintF constraints

- `automation_runs` は append-only で、BEFORE UPDATE/DELETE trigger により既存行の変更を禁止する。  
- `audit_log` は `run_id` FK を持ち、audit_kind は footer / summary / diff_lines を扱う。  
- `session_telemetry` は related_plan_id を nullable FK とし、終了時集約に再利用可能な形で保持する。  
- 既存レコード破壊を避けるため、default 値と既存列互換を優先する。  

## §4 受入条件

### 4.1 D-API 受入

- capability 別に、endpoint contract（path/method/headers）と request-response schema、error model が揃っている。  
- role 別責務の表に role 列挙（tl/se/pg/fe/qa 等）を追加し、who owns を明記している。  
- `L2 MASTER` の API 設計境界を超えない。

### 4.2 D-DB 受入

- `helix-db v22+` で、`contract_entries` の drive 切替記録列を含む migration 草案を示せる。  
- `baseline_policy_family` と score formula を DB 集計条件へ反映する SQL 断片を提示できる。  
- `design_sprint_artifact_links` と `design_sprint_entries` の列定義を v22 草案として YAML で固定し、主キー/参照制約を明記する。  
- L2 MASTER §8.x の drive 切替時 append-only 記録列として以下を固定する。  
  ```yaml
  source_entry_id:
    type: uuid
    constraints:
      - not null
      - fk: design_sprint_entries.id
      - immutable: true
  target_entry_id:
    type: uuid
    constraints:
      - not null
      - fk: design_sprint_entries.id
      - immutable: true
  decision:
    type: text
    constraints:
      - not null
      - enum: [preserved, waived, failed]  # L2 §8.x master 統一
      - immutable: true
  decided_by:
    type: text
    constraints:
      - not null
      - max_len: 128
      - immutable: true
  reason:
    type: text
    constraints:
      - not null
      - max_len: 4096
      - immutable: true
  reopen_condition:
    type: jsonb
    constraints:
      - not null
      - json_schema: docs/v2/B-design/vmodel-semantics-spine.yaml#/definitions/reopen_condition
      - immutable: true
  ```
- 現行 v22 実装と同時整合として `previous_drive` / `drive_switch_reason` / `status_on_switch`（design_sprint_entries）を保持し、移行時に列欠落を起こさない。  
- migration matrix の D-DB Sprint 必須成果物を追加する。  
  - v21 semantic columns: `contract_entries` の設計価値保持列（既存）  
  - v22 drive-switch columns: `drive`, `origin_mode`, `evidence_status`, `previous_drive`, `drive_switch_reason`, `status_on_switch`  
  - v23 append-only correction columns: `source_entry_id`, `target_entry_id`, `decision`, `decided_by`, `reason`, `reopen_condition`  

### 4.3 D-CONTRACT 受入

- `mock_to_implementation` を append-only で扱う hook 契約（from_artifact_kind / to_artifact_kind / link_kind / append_only）を本文で固定する。  
- `mock_to_implementation` に `g2_evidence_preserved: true` を追加し、`FE/fullstack` と `fullstack/db` の `from_layer / to_layer` 差分を D-CONTRACT で固定する。  
- `functional_freeze enforce point` は L1 master AC-16 判定式を採用する。  
  - 判定式: `size=L AND drive in (fe/fullstack/db)`  
  - 実 CLI 契約: `helix gate G3 --subgate functional_freeze --plan-id <id> --drive <drive>` で drive 解決、size 別 enforce、drive 別 fail-close を固定。  
  - `docs/v2/B-design/vmodel-semantics.yaml` の `requires_functional_freeze` は D-CONTRACT の補助参照として扱う。  

### 4.4 代表的 cross-doc 受入

- `docs/v2/B-design/vmodel-semantics-spine.yaml` の `promotion_kinds`、`baseline_policy_family`、`score.formula` との対応を一致化する。  
- `docs/v2/B-design/vmodel-semantics-fe-draft.yaml` と `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml` の promotion 契約と矛盾しない。  
- `docs/v2/v2-gate-overlay.md` の functional_freeze 条件と CLI 変数（`--subgate functional_freeze`）の対応が明記される。  

### 4.5 G3 エントリ前提

- Plan 起票時点での L2 の M-01〜M-08、CI-001〜CI-008 の状態を破壊せず引き継ぐ。  
- Plan 起票時点の前提として、M-01〜M-08、CI-001〜CI-008 の `blocker` は `resolved` であること。  
- pair_status は対象 layer で `paired` または `waived` とし、size M で `waived` を採る場合は `waived_reason` を必須記載し、PM の明示承認を要する。  
- guard 検出器は `docs/v2/B-design/vmodel-semantics-spine.yaml` の `allowed_detectors` と一致させる。  
- 新規登録した設計項目に `unresolved` 表記を残さず、`resolved` へ遷移してから §7 判定に入る。  

### 4.6 Sprint .5 D-API 拡張受入

- 運用機能 5 endpoint（push / pr / hook / audit / telemetry）の contract が draft で固定されている。  
- 各 endpoint の path / method / request / response / error が SprintA の primitive に参照されている。  
- L1 FR-INV01 / FR-GR04 / CON-06 と整合し、hook callback と telemetry で矛盾がない。  
- FR-INV01 / FR-GR04 / CON-06 の定義は `docs/v2/L1-REQUIREMENTS.md` 参照

### 4.7 Sprint .6 D-DB 拡張受入

- v25 / v26 / v27 migration 草案が SprintB primitive（MigrationStep / ColumnSpec）を参照している。  
- `automation_runs` / `audit_log` / `session_telemetry` の 3 テーブル DDL と trigger が揃っている。  
- additive / idempotent / 非破壊であり、既存 `helix.db` schema の rename / drop を含まない。  

## §5 リスクと対策

### 5.1 schema migration リスク

- リスク: 既存 contract/設計テーブルの列追加や再作成に伴い、旧データが欠落する可能性。  
- 対策: additive / idempotent migration 前提、既定値で後方互換を担保し、`ALTER` 失敗時の安全経路を設計に入れる。

### 5.2 capability 発散リスク

- リスク: be / fullstack の endpoint contract が capability 名称単位で分岐し、レビュー窓口での評価がぶれる。  
- 対策: capability レジストリを 1 箇所（PLAN 本文の §3 を起点）で固定し、role ごとの責務欄を必須化する。

### 5.3 contract drift リスク

- リスク: spine、draft、DB migration、CLI 契約の一部だけが更新され、別層が旧形状のまま残る。  
- 対策: SprintD で cross-doc チェックを固定し、adversarial review 用の「差分一覧」を各 §4 末尾に追記可能にする。

### 5.4 追加リスク

- リスク: D-CONTRACT が hook 実装と同時に誤合体し、Phase E 接続を先取りしてしまう。  
- 対策: 本 PLAN の非対象を明確化し、D-CONTRACT は CLI 契約（宣言）に限定。  

### 5.5 capability 詳細化遅延リスク

- リスク: Sprint .5 / .6 で carry capability 全量を扱えず、運用機能の数が膨らむ可能性。  
- 対策: Sprint .5 / .6 は最頻使用 5 endpoint + 3 テーブルに絞り、残りは §7 carry に再列挙して PLAN-071（任意）で詳細化する。  

## §6 関連 PLAN

- PLAN-068-vmodel-strengthening-improvements: drive / migration / pairing carry の前提として参照。  
- PLAN-069-g3-entry-blocker-resolution (完遂): M-01〜M-08、CI-001〜CI-008 の整合状態を引き継ぐ。  
- PLAN-065-qa-strictness: automation_runs.status 評価の参照先。  
- PLAN-066-security-scan-systematic: audit_log の security 観点の参照先。  
- PLAN-067-helix-automation-layer: push/pr gate / hook の起点 PLAN。 (SprintE endpoint contract の起点として参照、hook 実行内部実装は §2 Non-goals に従う)
- L2 MASTER の Phase C / gate / score / baseline_policy 系の受け口を L3 へ転写。  
- docs/v2/B-design/helix-db-v21-spec.md: v22 への移行条件を前工程で受けたため、v22+ 草案との接続点を明確化。  
- v21 → v22 移行では additive かつ idempotent を原則にし、既存テーブルの既存 PK/FK を再作成しない。  
- 既存レコード破壊を招く schema 書換えは避け、追加列と既定値で互換を維持する。  
- migration は既存データに対して段階実行し、失敗時はロールバック可能で安全経路を担保する。  

## §7 G3 entry 条件

- Spine 整合性 PASS を維持し、PLAN-069 で確認した blocker 解消状態を崩さない。  
- L2 MASTER §3（5 design × 5 test layer 成果物）と §8（Phase 別責務）を前提に、L3 出力が schema 準備責務内に収まる。  
- §4 の受入条件が全て充足され、`drive / baseline_policy_family / score / functional_freeze` が cross-doc で照合可能。  
- `cross-doc 整合性` が未検出であり、`M-01〜M-08 + CI-001〜CI-008` の継続引継ぎが記録される。  
- Sprint .5 / .6 完了後に SprintD (必須 exit) で全 6 sprint の最終集約検証を実施し、G3 entry 判定はその後に行う。

---

## §8 V-model 4 artifact mapping (PLAN-075 retrofit、2026-05-17、grandfather)

PLAN-070 は **設計系 PLAN** (L3 D-API EXT / D-DB EXT / D-CONTRACT の詳細設計起票が中核) であり、② 実装コードは他 PLAN (主に PLAN-072 / PLAN-074) で行われる。そのため PLAN-070 単独での 4 artifact 完備は構造的に不可能。

PLAN-075 Phase 4 audit (`docs/v2/audit/plan-067-074-vmodel-audit.md` §2.2) で **P1 grandfather** 判定。

| Artifact | 種類 | PLAN-070 内での扱い | 実体存在 |
|---|---|---|---|
| ① 設計 (詳細) | D-API EXT / D-DB EXT / D-CONTRACT 起票 | 本 PLAN の主成果物 | 完備 (D-API EXT 524 行 / D-DB EXT 606 行 / D-CONTRACT 817 行) |
| ② 実装コード | (本 PLAN スコープ外、PLAN-072/074 由来) | 参照のみ | 他 PLAN で完備 |
| ③ テスト設計 | (本 PLAN スコープ外、実装側 PLAN で起票) | reference のみ | PLAN-074-{system,integration,unit}-test-design.md 等を他 PLAN で起票 |
| ④ テストコード | (本 PLAN スコープ外) | reference のみ | 他 PLAN で完備 |

### Phase 5 lint への扱い

`.helix/audit/deferred-findings.yaml` で `plan_070_071_grandfather` として grandfather 例外指定。`vmodel_lint` 実行時に skip 対象。

### 双方向 trace の確保

PLAN-070 の ① 設計 artifact (D-API EXT 等) は PLAN-074 で実装され、PLAN-074-{integration,unit}-test-design.md から D-API EXT への reference が双方向で確立済 (PLAN-075 Phase 3、commit aa8a948)。PLAN-070 自体は設計成果物の中継 PLAN として grandfather 化が妥当。
