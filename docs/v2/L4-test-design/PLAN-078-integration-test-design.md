---
plan_id: PLAN-078
doc_id: PLAN-078-integration-test-design
title: "PLAN-078 結合テスト設計 (helix-agent CLI + helix-codex wrap)"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (PLAN-078 Sprint .2b)
owner: PM
related_docs:
  - docs/plans/PLAN-078-agent-slot-management.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (§10 対象 ① 設計)
  - docs/v2/L4-test-design/PLAN-078-unit-test-design.md (姉妹 ③)
phases: L4
gates: G4
---

> **V-model 4 artifact 位置付け** (PLAN-075):
> 本書は ③ テスト設計 artifact。① 設計 (D-DB EXT §10 + PLAN-078 §4-§5) と
> ④ テストコード (`cli/lib/tests/test_agent_slots_integration.py` + `tests/helix-agent.bats`)
> を双方向 trace で繋ぐ独立文書である。

# PLAN-078 結合テスト設計 (③ D-TEST-DESIGN-INT)

## §1 概要

### 1.1 目的

PLAN-078 (helix.db v28 `agent_slots` + 並列実行可視化) の **結合テスト** を設計する。

本書の対象は、`helix-agent` の Bash wrapper、`helix-codex` の wrap 統合、
`automation_runs` との FK 連携、`fire → release` の lifecycle、CLI 出力フォーマットである。
結合層として「CLI 1 本の起動経路が、SQLite 永続化と状態遷移を正しく引き回すか」を検証する。

### 1.2 スコープ

対象は以下の 5 領域である。

1. `cli/helix-agent` CLI
2. `cli/helix-codex` への wrap 統合
3. `agent_slots` ↔ `automation_runs` FK 連携
4. `fire → release` lifecycle
5. CLI 出力フォーマット (`table` / `json`)

対象外は以下である。

- `agent_slots` の pure unit helper の単体整合
- D-DB migration の個別 SQL 文の詳細検証
- 実際の Codex ネットワーク実行
- 既存 PLAN 群の業務ロジック検証

### 1.3 V-model 4 artifact 双方向 trace

- **対象設計 (①)**: `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §10
- **対応実装 (②)**: `cli/lib/agent_slots.py` / `cli/helix-agent` / `cli/helix-codex`
- **本文書 (③ D-TEST-DESIGN-INT)**: `docs/v2/L4-test-design/PLAN-078-integration-test-design.md`
- **対応テストコード (④ D-TEST-CODE-INT)**: `cli/lib/tests/test_agent_slots_integration.py` / `tests/helix-agent.bats`
- **検証 gate**: G4 (実装凍結)

### 1.4 case 命名規約

結合テスト case は次の接頭辞で管理する。

- `I-CLI-001` 〜: `helix-agent` CLI 直呼び出し
- `I-WRAP-001` 〜: `helix-codex` wrap 統合
- `I-LIFE-001` 〜: `fire → release` lifecycle
- `I-FK-001` 〜: `automation_runs` FK 連携
- `I-STAT-001` 〜: `stats` 集計
- `I-STALE-001` 〜: stale 検出境界

### 1.5 mock 戦略

結合テストでは、実 DB と外部副作用の境界を明確に分ける。

- `helix.db`: temp dir に生成し、`migrate_all` で v28 まで適用する
- `codex exec`: stub で固定 exit code と stdout/stderr を返す
- `automation_runs`: 実 INSERT / FK 実接続を行い、永続化整合を確認する
- `trap`: `SIGINT` / `SIGTERM` をテスト側から再現し、`cancelled` 遷移を検証する
- `--no-record`: opt-out 経路は write なしを確認する
- Bearer token / env var: fixture で固定し、認証失敗と成功を切り替える

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
| I-CLI-001 | `test_agent_fire_creates_running_slot` | `helix agent fire` の running 記録 | CLI |
| I-CLI-002 | `test_agent_release_marks_completed_slot` | `release --status completed` | CLI |
| I-CLI-003 | `test_agent_release_marks_failed_slot` | `release --status failed` | CLI |
| I-CLI-004 | `test_agent_release_marks_cancelled_slot` | `release --status cancelled` | CLI |
| I-CLI-005 | `test_agent_fire_rejects_missing_role` | `--role` 欠落拒否 | CLI |
| I-CLI-006 | `test_agent_fire_rejects_invalid_agent_kind` | `agent_kind` 不正拒否 | CLI |
| I-CLI-007 | `test_agent_slots_active_table_output` | `slots --active` の table 出力 | CLI |
| I-CLI-008 | `test_agent_slots_all_json_output` | `slots --all --json` の JSON 出力 | CLI |
| I-CLI-009 | `test_agent_slots_stale_threshold_boundary` | 5 分 boundary の stale 判定 | CLI |
| I-CLI-010 | `test_agent_stats_by_hour_table_output` | `stats --by hour` | CLI |
| I-CLI-011 | `test_agent_stats_by_role_json_output` | `stats --by role --json` | CLI |
| I-CLI-012 | `test_agent_stats_by_plan_id_groups_rows` | `stats --by plan_id` | CLI |
| I-WRAP-001 | `test_helix_codex_wrap_fires_slot_before_exec` | 起動時 fire | wrap |
| I-WRAP-002 | `test_helix_codex_wrap_releases_completed_on_success` | 正常完了時 release | wrap |
| I-WRAP-003 | `test_helix_codex_wrap_releases_failed_on_exit_nonzero` | 非 0 exit で failed release | wrap |
| I-WRAP-004 | `test_helix_codex_wrap_cancels_on_sigint` | `trap` による cancelled | wrap |
| I-WRAP-005 | `test_helix_codex_wrap_cancels_on_sigterm` | `trap` による cancelled | wrap |
| I-WRAP-006 | `test_helix_codex_wrap_respects_no_record_opt_out` | `--no-record` opt-out | wrap |
| I-LIFE-001 | `test_fire_then_release_persists_status_transition` | running → completed | lifecycle |
| I-LIFE-002 | `test_fire_then_release_persists_exit_code` | exit_code 永続化 | lifecycle |
| I-LIFE-003 | `test_double_release_is_rejected_or_noop` | 二重 release 防止 | lifecycle |
| I-LIFE-004 | `test_release_without_fire_is_rejected` | orphan release 拒否 | lifecycle |
| I-FK-001 | `test_fire_records_automation_run_fk_when_run_exists` | FK 連携成功 | FK |
| I-FK-002 | `test_fire_without_automation_run_keeps_fk_null` | 任意列 null 許容 | FK |
| I-FK-003 | `test_fire_rejects_missing_automation_run_id_when_required` | 必須経路の欠落拒否 | FK |
| I-STAT-001 | `test_stats_groups_by_hour_and_role_consistently` | hour / role 集計一致 | stats |
| I-STAT-002 | `test_stats_groups_by_plan_id_excludes_null_plan_rows` | plan_id null 除外 | stats |
| I-STAT-003 | `test_stats_json_schema_contains_peak_parallel` | JSON schema 固定 | stats |
| I-STALE-001 | `test_stale_lists_running_slots_past_five_minutes` | stale 一覧 | stale |
| I-STALE-002 | `test_stale_excludes_recent_running_slots` | recent 除外 | stale |

### 2.2 総 case 数

本書は 28 case を設計する。
PLAN-074 より scope を絞りつつ、`fire / release` と `stats` の組み合わせを厚くして、
`helix-codex` wrap と `automation_runs` 連携を中心に確認する。

## §3 シナリオ別詳細設計

### 3.1 `helix-agent` CLI 直接呼び出し

**対象設計**: D-DB EXT §10.5 / §10.6  
**対象実装**: `cli/helix-agent`  
**対象テストコード**: `tests/helix-agent.bats` / `cli/lib/tests/test_agent_slots_integration.py`

#### I-CLI-001 `test_agent_fire_creates_running_slot`

- 前提:
  - `helix.db` は fresh migrate 済み
  - `agent_slots` と `automation_runs` が存在する
- 入力:
  - `helix agent fire --agent-kind codex --role se --plan-id PLAN-078 --wbs-id WBS-078-001 --task-summary "wrap smoke"`
- 期待出力:
  - `invocation_id` が stdout に出る
  - `status=running`
- 検証ポイント:
  - 1 行 INSERT
  - `slot_source=helix_codex`
  - `started_at` / `fired_at` が埋まる
- DoD:
  - `fire_slot()` の結合経路が CLI から通る

#### I-CLI-002 `test_agent_release_marks_completed_slot`

- 前提:
  - I-CLI-001 相当の running slot がある
- 入力:
  - `helix agent release --slot-id <id> --status completed --exit-code 0`
- 期待出力:
  - `released_at` が返る
  - `status=completed`
- 検証ポイント:
  - `released_at` が NULL でない
  - `exit_code=0`
- DoD:
  - completed 遷移が 1 回だけ成立する

#### I-CLI-003 `test_agent_release_marks_failed_slot`

- 前提:
  - running slot がある
- 入力:
  - `--status failed --exit-code 2`
- 期待出力:
  - `status=failed`
- 検証ポイント:
  - `exit_code=2`
  - `duration_ms` が算出される
- DoD:
  - 非 0 終了が failed に反映される

#### I-CLI-004 `test_agent_release_marks_cancelled_slot`

- 前提:
  - running slot がある
- 入力:
  - `--status cancelled`
- 期待出力:
  - `status=cancelled`
- 検証ポイント:
  - `completed_at` または `released_at` が記録される
- DoD:
  - 中断系の状態が table 上で識別可能

#### I-CLI-005 `test_agent_fire_rejects_missing_role`

- 前提:
  - fresh migrate 済み
- 入力:
  - `--agent-kind codex` だけで `--role` なし
- 期待出力:
  - usage error
- 検証ポイント:
  - INSERT なし
  - `invocation_id` 未採番
- DoD:
  - role 必須が固定される

#### I-CLI-006 `test_agent_fire_rejects_invalid_agent_kind`

- 前提:
  - fresh migrate 済み
- 入力:
  - `--agent-kind unknown`
- 期待出力:
  - validation error
- 検証ポイント:
  - `agent_kind` CHECK に到達する前に拒否、または DB 側で fail-fast
- DoD:
  - 許可外 kind の流入を止める

#### I-CLI-007 `test_agent_slots_active_table_output`

- 前提:
  - running slot が複数ある
- 入力:
  - `helix agent slots --active`
- 期待出力:
  - table 形式で active slot を列挙
- 検証ポイント:
  - `INVOCATION` / `AGENT` / `ROLE` / `STATUS` / `STARTED_AT` / `PLAN/WBS`
- DoD:
  - table ヘッダが固定される

#### I-CLI-008 `test_agent_slots_all_json_output`

- 前提:
  - completed / failed / running が混在
- 入力:
  - `helix agent slots --all --json`
- 期待出力:
  - JSON 配列
- 検証ポイント:
  - `status` ごとの件数が一致
  - null 列が JSON で欠損しない
- DoD:
  - machine readable 出力が壊れない

#### I-CLI-009 `test_agent_slots_stale_threshold_boundary`

- 前提:
  - 4 分 59 秒 / 5 分 00 秒 / 5 分 01 秒 の running slot を用意
- 入力:
  - `helix agent slots --stale`
- 期待出力:
  - 5 分超のみ stale
- 検証ポイント:
  - threshold boundary が 5 分で安定
- DoD:
  - stale 判定が off-by-one にならない

#### I-CLI-010 `test_agent_stats_by_hour_table_output`

- 前提:
  - 1 時間内に複数 slot がある
- 入力:
  - `helix agent stats --days 1 --by hour`
- 期待出力:
  - hour 集計の table
- 検証ポイント:
  - `PEAK_PARALLEL` / `AVG_DURATION_S` / `TOTAL_COST_USD`
- DoD:
  - hour 集計の列が安定

#### I-CLI-011 `test_agent_stats_by_role_json_output`

- 前提:
  - role が複数種類ある
- 入力:
  - `helix agent stats --days 7 --by role --json`
- 期待出力:
  - role 別 JSON
- 検証ポイント:
  - `role` 集計単位が正しい
- DoD:
  - role 別の並列度差が読める

#### I-CLI-012 `test_agent_stats_by_plan_id_groups_rows`

- 前提:
  - plan_id が複数ある
- 入力:
  - `helix agent stats --days 7 --by plan_id`
- 期待出力:
  - plan_id 別 table
- 検証ポイント:
  - `PLAN-078` が独立 row として出る
- DoD:
  - plan trace が切れない

### 3.2 `helix-codex` wrap 自動連携

**対象設計**: D-DB EXT §10.4 / §10.6 / §10.10  
**対象実装**: `cli/helix-codex`  
**対象テストコード**: `cli/lib/tests/test_agent_slots_integration.py`

#### I-WRAP-001 `test_helix_codex_wrap_fires_slot_before_exec`

- 前提:
  - `codex exec` stub が成功を返す
- 入力:
  - wrap 起動
- 期待出力:
  - `fire` が `codex exec` より先に行われる
- 検証ポイント:
  - 先に INSERT、後で exec
- DoD:
  - 起動時記録が保証される

#### I-WRAP-002 `test_helix_codex_wrap_releases_completed_on_success`

- 前提:
  - stub が exit 0
- 入力:
  - wrap 完了
- 期待出力:
  - `status=completed`
- 検証ポイント:
  - `release` が 1 回だけ呼ばれる
- DoD:
  - normal path の end-to-end が通る

#### I-WRAP-003 `test_helix_codex_wrap_releases_failed_on_exit_nonzero`

- 前提:
  - stub が exit 1
- 入力:
  - wrap 完了
- 期待出力:
  - `status=failed`
- 検証ポイント:
  - `exit_code=1`
- DoD:
  - non-zero exit の分類が正しい

#### I-WRAP-004 `test_helix_codex_wrap_cancels_on_sigint`

- 前提:
  - long-running stub
- 入力:
  - `SIGINT`
- 期待出力:
  - `status=cancelled`
- 検証ポイント:
  - `trap` が release を呼ぶ
- DoD:
  - Ctrl+C 中断が落ちない

#### I-WRAP-005 `test_helix_codex_wrap_cancels_on_sigterm`

- 前提:
  - long-running stub
- 入力:
  - `SIGTERM`
- 期待出力:
  - `status=cancelled`
- 検証ポイント:
  - `trap` 経路が SIGTERM にも反応する
- DoD:
  - シグナル種別差で漏れない

#### I-WRAP-006 `test_helix_codex_wrap_respects_no_record_opt_out`

- 前提:
  - opt-out 許可設定
- 入力:
  - `--no-record`
- 期待出力:
  - DB 変更なし
- 検証ポイント:
  - `fire` / `release` ともに skip
- DoD:
  - 既存運用への影響を抑えられる

### 3.3 lifecycle 詳細

**対象設計**: D-DB EXT §10.6  
**対象実装**: `cli/lib/agent_slots.py`

#### I-LIFE-001 `test_fire_then_release_persists_status_transition`

- 前提:
  - running slot がある
- 入力:
  - `release --status completed`
- 期待出力:
  - `running → completed`
- 検証ポイント:
  - state transition が DB に残る
- DoD:
  - lifecycle 基本経路が固定される

#### I-LIFE-002 `test_fire_then_release_persists_exit_code`

- 前提:
  - running slot がある
- 入力:
  - `release --status failed --exit-code 7`
- 期待出力:
  - `exit_code=7`
- 検証ポイント:
  - exit code が丸められない
- DoD:
  - failure 解析に使える

#### I-LIFE-003 `test_double_release_is_rejected_or_noop`

- 前提:
  - すでに completed slot がある
- 入力:
  - もう一度 `release`
- 期待出力:
  - error もしくは no-op
- 検証ポイント:
  - 二重更新が起きない
- DoD:
  - 重複 release の事故を避ける

#### I-LIFE-004 `test_release_without_fire_is_rejected`

- 前提:
  - その slot_id は存在しない
- 入力:
  - `release --slot-id <missing>`
- 期待出力:
  - not found error
- 検証ポイント:
  - orphan release が DB を壊さない
- DoD:
  - 孤立 ID の扱いが安全

### 3.4 `automation_runs` FK 連携

**対象設計**: D-DB EXT §10.7 / PLAN-078 §4.1  
**対象実装**: `cli/lib/agent_slots.py` / `cli/lib/http_api` 側の呼び出し経路  
**対象テストコード**: `cli/lib/tests/test_agent_slots_integration.py`

#### I-FK-001 `test_fire_records_automation_run_fk_when_run_exists`

- 前提:
  - `automation_runs` に run が存在する
- 入力:
  - `fire --automation-run-id <id>`
- 期待出力:
  - `automation_run_id` が保存される
- 検証ポイント:
  - FK が正しく接続される
- DoD:
  - HTTP 起動との trace が切れない

#### I-FK-002 `test_fire_without_automation_run_keeps_fk_null`

- 前提:
  - run id を渡さない
- 入力:
  - `fire` のみ
- 期待出力:
  - `automation_run_id` は NULL
- 検証ポイント:
  - 任意列として保存
- DoD:
  - CLI 単独起動が壊れない

#### I-FK-003 `test_fire_rejects_missing_automation_run_id_when_required`

- 前提:
  - HTTP 起動経路で必須扱い
- 入力:
  - 必須経路なのに run id なし
- 期待出力:
  - validation error
- 検証ポイント:
  - FK 欠落のまま業務 run を進めない
- DoD:
  - 実装契約に沿う

### 3.5 `stats` 集計

**対象設計**: D-DB EXT §10.5 / §10.7  
**対象実装**: `cli/lib/agent_slots.py`  
**対象テストコード**: `cli/lib/tests/test_agent_slots_integration.py`

#### I-STAT-001 `test_stats_groups_by_hour_and_role_consistently`

- 前提:
  - hour / role が交差するデータがある
- 入力:
  - `stats --by hour`
  - `stats --by role`
- 期待出力:
  - 集計軸ごとに整合
- 検証ポイント:
  - 総数が一致する
- DoD:
  - 集計軸の差で件数が崩れない

#### I-STAT-002 `test_stats_groups_by_plan_id_excludes_null_plan_rows`

- 前提:
  - plan_id あり / なしの slot が混在
- 入力:
  - `stats --by plan_id`
- 期待出力:
  - null plan は別扱いまたは除外
- 検証ポイント:
  - null 行の扱いが明確
- DoD:
  - 解析軸が不明瞭にならない

#### I-STAT-003 `test_stats_json_schema_contains_peak_parallel`

- 前提:
  - JSON 出力モード
- 入力:
  - `stats --by hour --json`
- 期待出力:
  - `peak_parallel` を含む JSON
- 検証ポイント:
  - schema 固定
- DoD:
  - ダッシュボード連携の前提が維持される

### 3.6 stale 検出

**対象設計**: D-DB EXT §10.5 / §10.6  
**対象実装**: `cli/helix-agent`  
**対象テストコード**: `tests/helix-agent.bats`

#### I-STALE-001 `test_stale_lists_running_slots_past_five_minutes`

- 前提:
  - 5 分超の running slot がある
- 入力:
  - `helix agent slots --stale`
- 期待出力:
  - 該当 slot が列挙される
- 検証ポイント:
  - しきい値を超えたものだけ表示
- DoD:
  - release 漏れを読める

#### I-STALE-002 `test_stale_excludes_recent_running_slots`

- 前提:
  - 直近の running slot がある
- 入力:
  - `helix agent slots --stale`
- 期待出力:
  - recent slot は表示されない
- 検証ポイント:
  - false positive がない
- DoD:
  - stale view の品質が保たれる

## §4 共通 fixture

### 4.1 temp `helix.db`

- `tmp_path` 直下に DB を作る
- `migrate_all` を呼び、v28 まで適用する
- 既存レコードは持ち込まない

### 4.2 `codex exec` stub

- 成功時は exit code 0
- 失敗時は exit code 1 以上
- stdout / stderr は固定値にして assert 可能にする
- 長時間実行 case では sleep を短く固定する

### 4.3 `automation_runs` seed

- FK 検証用に 1 行以上 seed する
- `run_kind`, `status`, `started_at` を固定し、参照可能にする
- null 経路の case では seed を使わない

### 4.4 Bearer token / env var

- `HELIX_BEARER_TOKEN` を fixture で固定する
- 認証成功 / 失敗を切り替えられるようにする
- `HELIX_SESSION_ID` は stale と stats の比較に使う

### 4.5 `trap` シミュレーション

- `SIGINT` / `SIGTERM` を別 case で発火する
- trap handler が `release` を呼んだことを assert する
- シグナル受信後に orphan slot が残らないことを確認する

## §5 集計

| 領域 | case 数 | 主な対象 |
|---|---:|---|
| CLI direct | 12 | fire / release / slots / stats |
| wrap | 6 | fire-release 自動連携 / trap / opt-out |
| lifecycle | 4 | running→terminal 遷移 |
| FK | 3 | automation_runs 連携 |
| stats | 3 | hour / role / plan_id |
| stale | 2 | 5 分境界 |
| **合計** | **30** |  |

## §6 DoD

- 全 case PASS
- Bash CLI は `bats` で検証する
- Python helper は `pytest` 経由で検証する
- `helix-codex` wrap の `fire / release / trap / --no-record` が全て PASS
- `automation_runs` FK 連携が実 DB で PASS
- `helix doctor` への影響がない
- `stats` の table / json 両出力で破綻しない

## §7 4 artifact 双方向 trace 表

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §10 + `docs/plans/PLAN-078-agent-slot-management.md` §4-§5 |
| ② 実装コード | L4 実装 | `cli/lib/agent_slots.py` + `cli/helix-agent` + `cli/helix-codex` |
| ③ テスト設計 (本書) | L4 設計 | `docs/v2/L4-test-design/PLAN-078-integration-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_agent_slots_integration.py` + `tests/helix-agent.bats` |

## §8 備考

- `PLAN-078-unit-test-design.md` は unit helper の別文書として並行管理する
- 本書は結合層の設計に限定し、helper の内部アルゴリズムは対象外とする
- 既存 PLAN-075 の V-model 4 artifact 原則に従い、本文書は実装コードと混在させない
