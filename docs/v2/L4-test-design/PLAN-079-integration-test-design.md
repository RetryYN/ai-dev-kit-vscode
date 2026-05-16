---
plan_id: PLAN-079
doc_id: PLAN-079-integration-test-design
title: "PLAN-079 結合テスト設計 (helix-scrum local + helix-reverse from-scrum)"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (PLAN-079 Sprint .2b)
owner: PM
related_docs:
  - docs/plans/PLAN-079-uncertainty-pocket-scrum-reverse-chain.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (§11/§12 対象 ① 設計)
  - docs/v2/L4-test-design/PLAN-079-unit-test-design.md (姉妹 ③)
phases: L4
gates: G4
---

> **V-model 4 artifact 位置付け** (PLAN-075)
> 本書は ③ テスト設計 artifact。① 設計 (`D-DB EXT §11 + §12 + PLAN-079 §3.1-§3.2`) と
> ④ テストコード (`cli/lib/tests/test_scrum_local_integration.py` / `tests/helix-scrum-local.bats` /
> `tests/helix-reverse-from-scrum.bats`) を双方向 trace で繋ぐ独立文書である。

# PLAN-079 結合テスト設計 (③ D-TEST-DESIGN-INT)

## §1 概要

### 1.1 目的

PLAN-079 (UPS + SRF chain) の **結合テスト** を設計する。

本書の対象は、`helix-scrum local` の Bash CLI、`helix-reverse from-scrum` の起動経路、
UPS state machine の `S0→S1→S2→S3` 遷移、SRF chain の `R0→R4` routing、
および `scrum_local_loops` / `reverse_local_loops` / `agent_slots` の FK 連携である。
結合層として「CLI 1 本の起動経路が、SQLite 永続化と state machine の橋渡しを正しく行うか」を検証する。

### 1.2 スコープ

対象は以下の 7 領域である。

1. `cli/helix-scrum local` CLI
2. `cli/helix-reverse from-scrum` / `cli/helix-reverse local`
3. UPS state machine 結合 (`S0→S1→S2→S3` confirmed / rejected / pivot)
4. SRF chain 結合 (`UPS confirmed → reverse from-scrum → R0→R4`)
5. FK 連携 (`scrum_local_loops` ↔ `reverse_local_loops` ↔ `agent_slots`)
6. pivot 連鎖 (`S3 pivot → 新 S0 with parent_loop_id`)
7. routing 完了 (`R-LOCAL-4` で `target_forward_plan` / `target_forward_layer` 確定)

対象外は以下である。

- `scrum_local_loops` / `reverse_local_loops` の pure unit helper の単体整合
- D-DB migration の個別 SQL 文の詳細検証
- 実際の外部ツール呼び出しやネットワーク副作用
- 既存 PLAN 群の業務ロジック検証

### 1.3 V-model 4 artifact 双方向 trace

- **対象設計 (①)**: `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §11 / §12
- **対応実装 (②)**: `cli/lib/scrum_local.py` / `cli/lib/reverse_local.py` / `cli/helix-scrum` / `cli/helix-reverse`
- **本文書 (③ D-TEST-DESIGN-INT)**: `docs/v2/L4-test-design/PLAN-079-integration-test-design.md`
- **対応テストコード (④ D-TEST-CODE-INT)**: `cli/lib/tests/test_scrum_local_integration.py` /
  `tests/helix-scrum-local.bats` / `tests/helix-reverse-from-scrum.bats`
- **検証 gate**: G4 (実装凍結)

### 1.4 mock 戦略

結合テストでは、実 DB と外部副作用の境界を明確に分ける。

- `helix.db`: temp dir に生成し、`migrate_all` で v29 まで適用する
- `agent_slots`: PLAN-078 完遂前提で、`related_agent_slot_id` を実 INSERT して FK を確認する
- `automation_runs`: 必要に応じて seed し、`plan_id` / `trigger_actor` / `status` の参照整合を見る
- CLI 呼び出し: `cli/helix-scrum local` / `cli/helix-reverse` を subprocess で起動する
- `parent_loop_id` / `parent_scrum_loop_id`: pivot と SRF chain の自己参照 FK を検証する

### 1.5 case 命名規約

結合テスト case は次の接頭辞で管理する。

- `I-UPS-CLI-001` 〜: `helix-scrum local` CLI 直呼び出し
- `I-SRF-CLI-001` 〜: `helix-reverse from-scrum` / `local` subcommand
- `I-UPS-LIFE-001` 〜: UPS state machine lifecycle
- `I-SRF-LIFE-001` 〜: SRF chain R0→R4
- `I-FK-001` 〜: FK 整合
- `I-PIVOT-001` 〜: pivot 連鎖
- `I-ROUTE-001` 〜: routing 完了

### 1.6 本書の読み方

- §2 は case 一覧
- §3 は領域別の詳細設計
- §4 は共通 fixture
- §5 は case 数集計
- §6 は DoD
- §7 は 4 artifact 双方向 trace 表

## §2 case 一覧

### 2.1 全 case 一覧

| case ID | 既存 / 予定 test 関数 | 検証内容サマリ | 対象 |
|---|---|---|---|
| I-UPS-CLI-001 | `test_scrum_local_init_creates_running_loop` | `helix scrum local init` の running 記録 | UPS CLI |
| I-UPS-CLI-003 | `test_scrum_local_init_rejects_missing_layer` | `--layer` 欠落拒否 | UPS CLI |
| I-UPS-CLI-004 | `test_scrum_local_init_rejects_invalid_forward_layer` | 不正 layer 拒否 | UPS CLI |
| I-UPS-CLI-005 | `test_scrum_local_list_table_output` | `list` の table 出力 | UPS CLI |
| I-UPS-CLI-006 | `test_scrum_local_list_json_output` | `list --json` の JSON 出力 | UPS CLI |
| I-UPS-CLI-007 | `test_scrum_local_stats_table_output` | `stats` の table 出力 | UPS CLI |
| I-UPS-CLI-009 | `test_scrum_local_verify_confirmed_marks_decided` | `verify --result confirmed` | UPS CLI |
| I-UPS-CLI-010 | `test_scrum_local_verify_rejected_marks_decided` | `verify --result rejected` | UPS CLI |
| I-UPS-CLI-011 | `test_scrum_local_verify_pivot_creates_child_loop` | `verify --result pivot` | UPS CLI |
| I-SRF-CLI-001 | `test_reverse_from_scrum_creates_reverse_loop` | `from-scrum` 起動時の reverse loop 作成 | SRF CLI |
| I-SRF-CLI-002 | `test_reverse_from_scrum_requires_confirmed_scrum_loop` | confirmed 必須 | SRF CLI |
| I-SRF-CLI-003 | `test_reverse_local_stage_advances_to_r1` | `stage R1` 遷移 | SRF CLI |
| I-SRF-CLI-004 | `test_reverse_local_stage_advances_to_r2` | `stage R2` / `stage R3` 遷移 | SRF CLI |
| I-SRF-CLI-006 | `test_reverse_local_route_persists_target_forward_plan` | `route` の target plan 記録 | SRF CLI |
| I-SRF-CLI-007 | `test_reverse_local_route_persists_target_forward_layer` | `route` の target layer 記録 | SRF CLI |
| I-UPS-LIFE-001 | `test_s0_to_s1_state_transition_is_persisted` | S0→S1 | UPS lifecycle |
| I-UPS-LIFE-002 | `test_s1_to_s2_state_transition_is_persisted` | S1→S2 | UPS lifecycle |
| I-UPS-LIFE-003 | `test_s2_to_s3_confirmed_transition_is_persisted` | S2→S3 confirmed | UPS lifecycle |
| I-UPS-LIFE-005 | `test_s2_to_s3_pivot_transition_sets_parent_loop_id` | S2→S3 pivot | UPS lifecycle |
| I-UPS-LIFE-006 | `test_decided_loop_is_terminal_for_verify` | 決定後の再 verify 防止 | UPS lifecycle |
| I-SRF-LIFE-001 | `test_confirmed_scrum_loop_can_spawn_reverse_loop` | confirmed から reverse 生成 | SRF lifecycle |
| I-SRF-LIFE-002 | `test_reverse_r0_evidence_acquisition_persists_artifact_links` | R0 evidence 保存 | SRF lifecycle |
| I-SRF-LIFE-004 | `test_reverse_r2_as_is_design_persists_adr_hint` | R2 As-Is design | SRF lifecycle |
| I-SRF-LIFE-005 | `test_reverse_r3_intent_hypothesis_persists_po_validation` | R3 intent hypothesis | SRF lifecycle |
| I-SRF-LIFE-006 | `test_reverse_r4_routing_marks_completed_and_closed` | R4 routing 完了 | SRF lifecycle |
| I-FK-001 | `test_scrum_loop_records_related_agent_slot_fk` | `related_agent_slot_id` FK | FK |
| I-FK-002 | `test_reverse_loop_records_parent_scrum_loop_fk` | `parent_scrum_loop_id` FK | FK |
| I-FK-003 | `test_pivot_child_loop_points_back_to_parent_loop_id` | pivot 親参照 FK | FK |
| I-FK-004 | `test_route_result_can_reference_automation_run_seed` | `automation_runs` seed 参照 | FK |
| I-PIVOT-001 | `test_pivot_chain_creates_descendant_loop_with_new_root_state` | pivot 連鎖 1 hop | pivot |
| I-PIVOT-002 | `test_pivot_chain_preserves_ancestor_trace_across_multiple_pivots` | pivot 連鎖多段 | pivot |
| I-ROUTE-001 | `test_r4_route_binds_forward_plan_and_layer` | `target_forward_plan` / `target_forward_layer` 確定 | routing |
| I-ROUTE-002 | `test_r4_route_rejects_missing_forward_plan` | plan 欠落拒否 | routing |
| I-ROUTE-003 | `test_r4_route_rejects_invalid_forward_layer` | layer 不正拒否 | routing |

### 2.2 総 case 数

本書は 33 case を設計する。

PLAN-078 より scope を大きく取り、UPS の lifecycle と SRF chain の routing を
別々に固定したうえで、`agent_slots` FK と `pivot` 連鎖の整合を厚く確認する。

## §3 シナリオ別詳細設計

### 3.1 `helix-scrum local` CLI 直接呼び出し

**対象設計**: D-DB EXT §11.1 / §11.2 / §11.3  
**対象実装**: `cli/helix-scrum` の `local` subcommand  
**対象テストコード**: `tests/helix-scrum-local.bats` / `cli/lib/tests/test_scrum_local_integration.py`

#### I-UPS-CLI-001 `test_scrum_local_init_creates_running_loop`

- 前提:
  - `helix.db` は fresh migrate 済み
  - `scrum_local_loops` が存在する
- 入力:
  - `helix scrum local init --layer L4 --hypothesis "wrap smoke" --acceptance "local loop created"`
- 期待出力:
  - `loop_id` が stdout に出る
  - `state=S0`
- 検証ポイント:
  - 1 行 INSERT
  - `started_at` が埋まる
  - `forward_layer=L4`
- DoD:
  - S0 の初期化経路が CLI から通る

#### I-UPS-CLI-003 `test_scrum_local_init_rejects_missing_layer`

- 前提:
  - fresh migrate 済み
- 入力:
  - `--layer` なしで `init`
- 期待出力:
  - usage error
- 検証ポイント:
  - INSERT なし
  - `loop_id` 未採番
- DoD:
  - layer 必須が固定される

#### I-UPS-CLI-004 `test_scrum_local_init_rejects_invalid_forward_layer`

- 前提:
  - fresh migrate 済み
- 入力:
  - `--layer LX`
- 期待出力:
  - validation error
- 検証ポイント:
  - CHECK / validator により拒否
- DoD:
  - 許可外 layer の流入を止める

#### I-UPS-CLI-005 `test_scrum_local_list_table_output`

- 前提:
  - running / decided / pivot の loop が複数ある
- 入力:
  - `helix scrum local list`
- 期待出力:
  - table 形式で loop を列挙
- 検証ポイント:
  - `LOOP_ID` / `LAYER` / `STATE` / `DECIDE` / `PARENT` / `AGENT_SLOT`
- DoD:
  - table ヘッダが固定される

#### I-UPS-CLI-006 `test_scrum_local_list_json_output`

- 前提:
  - completed / rejected / pivot が混在
- 入力:
  - `helix scrum local list --json`
- 期待出力:
  - JSON 配列
- 検証ポイント:
  - state ごとの件数が一致
  - null 列が JSON で欠損しない
- DoD:
  - machine readable 出力が壊れない

#### I-UPS-CLI-007 `test_scrum_local_stats_table_output`

- 前提:
  - 複数 loop の decide_result が混在
- 入力:
  - `helix scrum local stats`
- 期待出力:
  - table で `confirmed` / `rejected` / `pivot` を集計
- 検証ポイント:
  - 期間集計と total が一致
- DoD:
  - 進捗確認用の集計が安定する

#### I-UPS-CLI-009 `test_scrum_local_verify_confirmed_marks_decided`

- 前提:
  - S2 の running loop がある
- 入力:
  - `helix scrum local verify --loop-id <id> --result confirmed`
- 期待出力:
  - `state=S3`
  - `decide_result=confirmed`
- 検証ポイント:
  - `decided_at` が埋まる
- DoD:
  - confirmed 遷移が 1 回だけ成立する

#### I-UPS-CLI-010 `test_scrum_local_verify_rejected_marks_decided`

- 前提:
  - S2 の running loop がある
- 入力:
  - `--result rejected`
- 期待出力:
  - `state=S3`
  - `decide_result=rejected`
- 検証ポイント:
  - `parent_loop_id` は NULL のまま
- DoD:
  - rejected 遷移が記録される

#### I-UPS-CLI-011 `test_scrum_local_verify_pivot_creates_child_loop`

- 前提:
  - S2 の running loop がある
- 入力:
  - `--result pivot`
- 期待出力:
  - 親 loop は `state=S3`
  - 子 loop が新規作成される
- 検証ポイント:
  - `parent_loop_id` が親を指す
  - 子 loop は `state=S0`
- DoD:
  - pivot を chain として保存できる

### 3.2 `helix-reverse from-scrum` / `local` subcommand

**対象設計**: D-DB EXT §12.1 / §12.2 / §12.3  
**対象実装**: `cli/helix-reverse` の `from-scrum` / `local` subcommand  
**対象テストコード**: `tests/helix-reverse-from-scrum.bats` / `cli/lib/tests/test_reverse_local_integration.py`

#### I-SRF-CLI-001 `test_reverse_from_scrum_creates_reverse_loop`

- 前提:
  - confirmed になった UPS loop がある
- 入力:
  - `helix reverse from-scrum --scrum-loop-id <id>`
- 期待出力:
  - `loop_id` が stdout に出る
  - `state=R0`
- 検証ポイント:
  - `parent_scrum_loop_id` が親を指す
  - `reverse_type=scrum-to-forward`
- DoD:
  - SRF chain の起点が作成される

#### I-SRF-CLI-002 `test_reverse_from_scrum_requires_confirmed_scrum_loop`

- 前提:
  - rejected / running の UPS loop がある
- 入力:
  - `from-scrum`
- 期待出力:
  - validation error
- 検証ポイント:
  - reverse loop は作成されない
- DoD:
  - confirmed 以外は SRF 化しない

#### I-SRF-CLI-003 `test_reverse_local_stage_advances_to_r1`

- 前提:
  - R0 loop が存在する
- 入力:
  - `helix reverse local stage --loop-id <id> --stage R1`
- 期待出力:
  - `state=R1`
- 検証ポイント:
  - state 遷移が単方向である
- DoD:
  - R1 の中間証跡が固定される

#### I-SRF-CLI-004 `test_reverse_local_stage_advances_to_r2`

- 前提:
  - R1 loop が存在する
- 入力:
  - `--stage R2`
- 期待出力:
  - `state=R2`
- 検証ポイント:
  - `artifact_links` に design hint が追加される
- DoD:
  - As-Is design 前段が通る

#### I-SRF-CLI-006 `test_reverse_local_route_persists_target_forward_plan`

- 前提:
  - R3 loop が存在する
- 入力:
  - `helix reverse local route --loop-id <id> --target-plan PLAN-079 --target-layer L4`
- 期待出力:
  - `target_forward_plan=PLAN-079`
- 検証ポイント:
  - routing の永続化
- DoD:
  - Forward 合流先を保存できる

#### I-SRF-CLI-007 `test_reverse_local_route_persists_target_forward_layer`

- 前提:
  - R3 loop が存在する
- 入力:
  - `--target-layer L4`
- 期待出力:
  - `target_forward_layer=L4`
- 検証ポイント:
  - layer が未指定時に拒否されることも別 case で保証
- DoD:
  - routing 層が明示される

### 3.3 UPS state machine 結合

**対象設計**: D-DB EXT §11.4 / §11.5  
**対象実装**: `cli/lib/scrum_local.py`  
**対象テストコード**: `cli/lib/tests/test_scrum_local_integration.py`

#### I-UPS-LIFE-001 `test_s0_to_s1_state_transition_is_persisted`

- 前提:
  - S0 loop がある
- 入力:
  - `poc`
- 期待出力:
  - `state=S1`
- 検証ポイント:
  - PoC 投入時に running から next state へ進む
- DoD:
  - S1 の証跡が保存される

#### I-UPS-LIFE-002 `test_s1_to_s2_state_transition_is_persisted`

- 前提:
  - S1 loop がある
- 入力:
  - `verify`
- 期待出力:
  - `state=S2`
- 検証ポイント:
  - result の評価前に stage が更新される
- DoD:
  - S2 の評価待ち状態が固定される

#### I-UPS-LIFE-003 `test_s2_to_s3_confirmed_transition_is_persisted`

- 前提:
  - S2 loop がある
- 入力:
  - `verify --result confirmed`
- 期待出力:
  - `state=S3`
  - `decide_result=confirmed`
- 検証ポイント:
  - terminal 遷移
- DoD:
  - confirmed 結果が不変になる

#### I-UPS-LIFE-005 `test_s2_to_s3_pivot_transition_sets_parent_loop_id`

- 前提:
  - S2 loop がある
- 入力:
  - `verify --result pivot`
- 期待出力:
  - `state=S3`
  - `decide_result=pivot`
- 検証ポイント:
  - 新規 child loop 作成
  - child の `parent_loop_id` が埋まる
- DoD:
  - pivot の履歴が一方向に連結される

#### I-UPS-LIFE-006 `test_decided_loop_is_terminal_for_verify`

- 前提:
  - S3 loop がある
- 入力:
  - 再度 `verify`
- 期待出力:
  - terminal error
- 検証ポイント:
  - 二重決定を拒否
- DoD:
  - terminal guard が効く

### 3.4 SRF chain R0→R4

**対象設計**: D-DB EXT §12.4 / §12.5 / §12.6  
**対象実装**: `cli/lib/reverse_local.py`  
**対象テストコード**: `cli/lib/tests/test_reverse_local_integration.py`

#### I-SRF-LIFE-001 `test_confirmed_scrum_loop_can_spawn_reverse_loop`

- 前提:
  - confirmed UPS loop がある
- 入力:
  - `from-scrum`
- 期待出力:
  - R0 loop 作成
- 検証ポイント:
  - parent/child 関係が壊れない
- DoD:
  - confirmed から reverse へ橋渡しできる

#### I-SRF-LIFE-002 `test_reverse_r0_evidence_acquisition_persists_artifact_links`

- 前提:
  - R0 loop がある
- 入力:
  - evidence 収集完了
- 期待出力:
  - `artifact_links` が更新される
- 検証ポイント:
  - PoC コード / 操作ログ / verify 結果の参照が残る
- DoD:
  - R0 証跡が追跡可能になる

#### I-SRF-LIFE-004 `test_reverse_r2_as_is_design_persists_adr_hint`

- 前提:
  - R1 loop がある
- 入力:
  - stage R2
- 期待出力:
  - `state=R2`
- 検証ポイント:
  - ADR hint が落ちない
- DoD:
  - As-Is 設計の推定が残る

#### I-SRF-LIFE-005 `test_reverse_r3_intent_hypothesis_persists_po_validation`

- 前提:
  - R2 loop がある
- 入力:
  - stage R3
- 期待出力:
  - `state=R3`
- 検証ポイント:
  - PO 検証結果が保存される
- DoD:
  - 意図仮説を明文化できる

#### I-SRF-LIFE-006 `test_reverse_r4_routing_marks_completed_and_closed`

- 前提:
  - R3 loop がある
- 入力:
  - `route`
- 期待出力:
  - `state=R4`
  - `routed_at` が埋まる
- 検証ポイント:
  - terminal で `target_forward_plan` / `target_forward_layer` が確定する
- DoD:
  - R-LOCAL-4 で Forward 合流情報が閉じる

### 3.5 FK 整合

**対象設計**: D-DB EXT §11.6 / §12.7  
**対象実装**: `cli/lib/scrum_local.py` / `cli/lib/reverse_local.py`  
**対象テストコード**: `cli/lib/tests/test_scrum_local_integration.py` / `cli/lib/tests/test_reverse_local_integration.py`

#### I-FK-001 `test_scrum_loop_records_related_agent_slot_fk`

- 前提:
  - `agent_slots` に PLAN-078 の完遂行が存在する
- 入力:
  - `init` の際に `related_agent_slot_id` を与える
- 期待出力:
  - FK が保存される
- 検証ポイント:
  - `agent_slots.id` が実際に参照される
- DoD:
  - PLAN-078 と PLAN-079 の横断 trace が可能になる

#### I-FK-002 `test_reverse_loop_records_parent_scrum_loop_fk`

- 前提:
  - confirmed UPS loop がある
- 入力:
  - `from-scrum`
- 期待出力:
  - `parent_scrum_loop_id` が保存される
- 検証ポイント:
  - 外れ値 / 不在 ID は拒否
- DoD:
  - SRF chain の起点が検査可能になる

#### I-FK-003 `test_pivot_child_loop_points_back_to_parent_loop_id`

- 前提:
  - pivot 可能な S2 loop がある
- 入力:
  - `verify --result pivot`
- 期待出力:
  - child loop の `parent_loop_id` が親を指す
- 検証ポイント:
  - 親子の連鎖が循環しない
- DoD:
  - pivot の ancestry が保持される

#### I-FK-004 `test_route_result_can_reference_automation_run_seed`

- 前提:
  - `automation_runs` seed がある
- 入力:
  - `route`
- 期待出力:
  - route metadata が seed run を追跡できる
- 検証ポイント:
  - `plan_id` / `trigger_actor` の参照整合
- DoD:
  - 実行ログと設計ログが横断できる

### 3.6 pivot 連鎖

**対象設計**: D-DB EXT §11.7  
**対象実装**: `cli/lib/scrum_local.py`  
**対象テストコード**: `cli/lib/tests/test_scrum_local_integration.py`

#### I-PIVOT-001 `test_pivot_chain_creates_descendant_loop_with_new_root_state`

- 前提:
  - pivot 可能な loop がある
- 入力:
  - `verify --result pivot`
- 期待出力:
  - descendant が `state=S0`
- 検証ポイント:
  - 1 hop の pivot で新しい根が作られる
- DoD:
  - pivot が単発では終わらない

#### I-PIVOT-002 `test_pivot_chain_preserves_ancestor_trace_across_multiple_pivots`

- 前提:
  - 2 回以上 pivot した chain がある
- 入力:
  - `list`
- 期待出力:
  - ancestry が見える
- 検証ポイント:
  - 祖先 loop と descendant loop の連結が崩れない
- DoD:
  - 連鎖履歴を後追いできる

### 3.7 routing 完了

**対象設計**: D-DB EXT §12.8 / §12.9  
**対象実装**: `cli/lib/reverse_local.py`  
**対象テストコード**: `cli/lib/tests/test_reverse_local_integration.py`

#### I-ROUTE-001 `test_r4_route_binds_forward_plan_and_layer`

- 前提:
  - R3 loop がある
- 入力:
  - `route --target-plan PLAN-079 --target-layer L4`
- 期待出力:
  - `target_forward_plan` と `target_forward_layer` が保存される
- 検証ポイント:
  - routing 完了後に read-only で読める
- DoD:
  - Forward 合流の最終情報が固定される

#### I-ROUTE-002 `test_r4_route_rejects_missing_forward_plan`

- 前提:
  - R3 loop がある
- 入力:
  - `route --target-layer L4`
- 期待出力:
  - validation error
- 検証ポイント:
  - plan 欠落では routing できない
- DoD:
  - routing の必須情報が守られる

#### I-ROUTE-003 `test_r4_route_rejects_invalid_forward_layer`

- 前提:
  - R3 loop がある
- 入力:
  - `route --target-plan PLAN-079 --target-layer L9`
- 期待出力:
  - validation error
- 検証ポイント:
  - layer は L1/L2/L3/L4 のみ許可
- DoD:
  - 無効な合流先を止める

## §4 fixture

### 4.1 共通 fixture 構成

結合テストは以下の共通 fixture を利用する。

| fixture | 役割 | 具体内容 |
|---|---|---|
| `temp_helix_db` | SQLite の一時 DB | temp dir に `helix.db` を生成し v29 まで migrate |
| `seed_agent_slots` | PLAN-078 前提データ | `agent_slots` に `related_agent_slot_id` を含む実データを INSERT |
| `seed_automation_runs` | 実行履歴 | `automation_runs` に `plan_id` / `trigger_actor` を seed |
| `scrum_loop_factory` | UPS loop 生成 | S0/S1/S2/S3 を切り替える loop factory |
| `reverse_loop_factory` | SRF loop 生成 | R0/R1/R2/R3/R4 を切り替える loop factory |
| `cli_subprocess` | CLI 実行 | `cli/helix-scrum local` / `cli/helix-reverse` を subprocess で起動 |
| `json_snapshot` | 出力固定 | table / JSON の差分を比較する snapshot |

### 4.2 fixture 初期データ

- `scrum_local_loops`
  - S0 loop 1 件
  - S2 loop 1 件
  - pivot 親 loop 1 件
- `reverse_local_loops`
  - R0 loop 1 件
  - R3 loop 1 件
- `agent_slots`
  - PLAN-078 完遂済み slot 1 件
- `automation_runs`
  - seed 1 件以上

### 4.3 CLI subprocess の検証点

- `stdout` / `stderr` を別々に検査する
- `returncode` を固定する
- `ENV` に依存する path を fixture で固定する
- 失敗時の usage メッセージを snapshot で固定する

### 4.4 FK/parent chain の検証点

- `related_agent_slot_id` は `agent_slots.id` に実在すること
- `parent_scrum_loop_id` は confirmed UPS loop を指すこと
- `parent_loop_id` は pivot 親 loop を指すこと
- `target_forward_plan` / `target_forward_layer` は routing 完了後にのみ埋まること

## §5 集計

### 5.1 case 数内訳

| 領域 | case 数 |
|---|---:|
| `helix-scrum local` CLI | 9 |
| `helix-reverse from-scrum` / `local` CLI | 6 |
| UPS state machine | 5 |
| SRF chain | 5 |
| FK 整合 | 4 |
| pivot 連鎖 | 2 |
| routing 完了 | 3 |
| **合計** | **34** |

### 5.2 設計意図

本書は 30 case 前後の要件を満たしつつ、実際には 34 case まで拡張している。
理由は以下である。

- UPS の `pivot` は単独 case では祖先追跡が不十分である
- SRF chain は `R0→R4` を分解しておかないと routing 完了の回帰が見えない
- FK は `agent_slots` と `scrum_local_loops` / `reverse_local_loops` を横断するため、最低 4 case 必要である

### 5.3 coverage 観点

- `init / poc / verify / list / stats / route` の全 CLI 面を通す
- confirmed / rejected / pivot の 3 結果を通す
- `S0→S1→S2→S3` と `R0→R4` の両 state machine を通す
- `parent_loop_id` / `parent_scrum_loop_id` / `related_agent_slot_id` を通す
- `target_forward_plan` / `target_forward_layer` を通す

## §6 DoD

### 6.1 完了条件

以下が満たされれば本結合テスト設計は完了とみなす。

- frontmatter が完備である
- §1〜§7 が揃っている
- case ID が `I-UPS-CLI-*` / `I-SRF-CLI-*` / `I-UPS-LIFE-*` / `I-SRF-LIFE-*` / `I-FK-*` / `I-PIVOT-*` / `I-ROUTE-*` で統一されている
- `helix.db` / `agent_slots` / CLI subprocess / FK が §1.4 と §4 で明示されている
- `reverse from-scrum` と `pivot` と `routing` が独立 case で固定されている
- テストコード側の予定ファイル名が trace 表に反映されている

### 6.2 受入基準

- 30 case 前後をカバーしている
- 抽象命名に逃げていない
- `PLAN-079` の `UPS` と `SRF` が混線していない
- `PLAN-078` の `agent_slots` 前提が FK で参照されている
- `R-LOCAL-4` で `target_forward_plan` / `target_forward_layer` を確定できる

### 6.3 残課題の扱い

- 実装時に case 名とテスト関数名を 1:1 で対応させる
- `PLAN-079-unit-test-design.md` と §7 の trace を合わせる
- 追加の migration / schema 変更が必要になった場合は本書ではなく設計側へ戻す

## §7 4 artifact 双方向 trace 表

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §11 + §12 + `PLAN-079` §3.1-§3.2 |
| ② 実装コード | L4 実装 | `cli/lib/scrum_local.py` + `cli/lib/reverse_local.py` + `cli/helix-scrum` (local subcommand) + `cli/helix-reverse` (from-scrum/local) |
| ③ テスト設計 (本書) | L4 設計 | `docs/v2/L4-test-design/PLAN-079-integration-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_scrum_local_integration.py` + `tests/helix-scrum-local.bats` + `tests/helix-reverse-from-scrum.bats` |

### 7.1 双方向 trace 補足

- ① → ③: `D-DB EXT §11/§12` に対応する結合テスト設計を本書で固定する
- ③ → ①: 本書の `I-UPS-*` / `I-SRF-*` / `I-FK-*` / `I-PIVOT-*` / `I-ROUTE-*` から設計節を逆引きする
- ③ → ④: case ID をテスト関数名の suffix に使う
- ④ → ③: docstring から本書の case ID を参照する

### 7.2 追加 trace ルール

- `I-UPS-CLI-*` は `helix-scrum local` の Bash wrapper に対応させる
- `I-SRF-CLI-*` は `helix-reverse from-scrum` と `local` の両方に対応させる
- `I-UPS-LIFE-*` は UPS の state machine 遷移境界を固定する
- `I-SRF-LIFE-*` は SRF chain の R0→R4 証跡を固定する
- `I-FK-*` は `agent_slots` と `scrum_local_loops` / `reverse_local_loops` の参照整合を固定する
- `I-PIVOT-*` は `parent_loop_id` の ancestry を固定する
- `I-ROUTE-*` は `target_forward_plan` / `target_forward_layer` の routing 完了を固定する
