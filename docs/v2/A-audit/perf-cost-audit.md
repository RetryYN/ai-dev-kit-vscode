# FR-INV15 性能 / コスト 現状監査

最終更新: 2026-05-14

## 概要

本メモは、HELIX V2 の性能 NFR (`NFR-10`〜`NFR-14`) とコスト NFR (`NFR-20`〜`NFR-22`) の根拠を作るため、現行実装の性能特性、token/cost 観測、既存 benchmark、cost guard の運用実態を棚卸しした監査結果です。

結論:

- 軽量 CLI (`helix status`, `helix dashboard`, `SessionStart`) の wall time は **28.6ms〜118.9ms** で、`1s` 目標に対して十分余裕があります。
- 一方で `helix detect dashboard` は **2.35s** で時間目標内ですが、`axis-03` の `IndentationError` により **完走失敗** します。現状の主要ギャップは純粋な速度より **安定性** です。
- detector 個別実行は大半が **1ms〜361.7ms** ですが、`axis-01` は **2.25s** と突出しています。
- コスト面では `helix budget status --json --no-cache` が **11.74s** と重く、かつ `Claude weekly_used_pct=100`, `weekly_cost_usd=434.64`, `weekly_budget_usd=200.0` で、**NFR-21/22 は未達** です。
- cost telemetry は不完全です。`budget_events=0`, `bench_snapshots=0`, `cost_log.tokens_est=0`, `cost_log.cost_est=0.0`, `Codex source=unavailable` なので、**role 別コストと guard 発火履歴の観測基盤が不足** しています。
- DB query の生 SQL は現データ量では **0.01ms〜0.75ms** と高速ですが、`contract_entries / test_design_entries / test_baseline` がほぼ空で、**4 layer chain の実運用負荷はまだ測れていません**。
- `./cli/helix detect` は dispatcher 未配線で、受入条件の例にある `helix detect dashboard` は現状 `./cli/helix-detect dashboard` が実体です。routing のズレも V2 前提の監査論点です。

不確実性:

- 本監査は 2026-05-14 に実施した 1 回の採取値です。CLI 性能は環境依存なので、継続 benchmark としては未成熟です。
- detector 計測は現行 `.helix/helix.db` を複製した一時 workspace で行い、元 DB を汚さないようにしています。
- token/cost は `budget status` の集計、`invocation_log`, `cost_log` を併用していますが、保存粒度が揃っていません。特に role 別 unit cost は **未観測** が多いです。
- `4 layer chain` は schema 上の土台はありますが、record が空に近いため、現 query time は **実運用の将来値ではありません**。

## 測定方法

1. 軽量 CLI:
   - `./cli/helix status`
   - `./cli/helix-dashboard --json`
   - `./cli/libexec/helix-session-start`
2. detector:
   - `./cli/helix-detect run axis-XX --json`
   - `./cli/helix-detect dashboard --json`
3. cost/budget:
   - `./cli/helix-budget status --json --no-cache`
   - `.helix/helix.db` の `invocation_log`, `cost_log`, `budget_events`, `detector_runs`, `sessions`
4. DB query:
   - `docs/plans/PLAN-065-qa-strictness.md` の 4 layer chain SQL
   - `cli/lib/helix_db.py` の telemetry 集計 query

## 既存 benchmark / observability 現状

| 観測対象 | 現状 | コメント |
|---|---|---|
| `bench_snapshots` | 0 rows | benchmark 永続記録なし |
| `detector_runs` | 28 rows | detector 実行履歴はあるが継続 benchmark には不足 |
| `budget_events` | 0 rows | cost guard 発火履歴が残っていない |
| `invocation_log` | 121 rows | role / model / duration の基礎ログはある |
| `cost_log` | 126 rows | rows はあるが `tokens_est=0`, `cost_est=0.0` |
| `sessions` | 20 rows | SessionStart telemetry は稼働 |

## メトリクス一覧

| メトリクス名 | 現状値 | 目標値 (V2 NFR) | gap | 改善策候補 | V2 Phase 紐付け |
|---|---|---|---|---|---|
| `startup_status_cold_ms` | 44.7ms | `NFR-12` 関連 1000ms 以内 | -955.3ms | 現状維持、継続採取のみ追加 | Phase F |
| `startup_status_warm_p50_ms` | 41.6ms | `NFR-12` 関連 1000ms 以内 | -958.4ms | benchmark 自動保存を追加 | Phase F |
| `dashboard_json_ms` | 28.6ms | `NFR-12` 1000ms 以内 | -971.4ms | 既存実装維持、継続 benchmark 化 | Phase F |
| `session_start_hook_ms` | 118.9ms | `NFR-12` 1000ms 以内 | -881.1ms | SessionStart の benchmark を `bench_snapshots` へ保存 | Phase E |
| `detect_dashboard_ms` | 2350.4ms (`rc=1`) | `NFR-10` 30000ms 以内 | 時間は -27649.6ms だが機能未達 | `axis-03` 例外を先に解消 | Phase E |
| `detect_axis_00_ms` | 50.8ms (`blocked`) | `NFR-10` 30000ms 以内 | 時間は -29949.2ms だが baseline blocked | baseline detector の意味と成功条件を固定 | Phase E |
| `detect_axis_01_ms` | 2245.2ms (`passed`) | `NFR-10` 30000ms 以内 | -27754.8ms | dead code scan の対象範囲を差分化 | Phase E |
| `detect_axis_02_ms` | 48.6ms (`blocked`) | `NFR-10` 30000ms 以内 | 時間は -29951.4ms だが blocked | coverage baseline writer を接続 | Phase D |
| `detect_axis_03_ms` | 133.6ms (`rc=1`, `IndentationError`) | `NFR-10` 30000ms 以内 | 時間は -29866.4ms だが機能未達 | tokenize 対象の parse error 耐性を追加 | Phase E |
| `detect_axis_04_ms` | 53.3ms (`failed`) | `NFR-10` 30000ms 以内 | -29946.7ms | skill decay しきい値と seed data を明確化 | Phase F |
| `detect_axis_05_ms` | 58.3ms (`blocked`) | `NFR-10` 30000ms 以内 | 時間は -29941.7ms だが blocked | plan debt input source を増やす | Phase E |
| `detect_axis_06_ms` | 280.0ms (`failed`) | `NFR-10` 30000ms 以内 | -29720.0ms | naming confusion の rule tuning と false positive 抑制 | Phase F |
| `detect_axis_07_ms` | 50.8ms (`blocked`) | `NFR-10` 30000ms 以内 | 時間は -29949.2ms だが blocked | doc drift の source mapping を補強 | Phase E |
| `detect_axis_08_ms` | 110.9ms (`failed`) | `NFR-10` 30000ms 以内 | -29889.1ms | plan-retro link の writer を追加 | Phase E |
| `detect_axis_09_ms` | 361.7ms (`failed`) | `NFR-10` 30000ms 以内 | -29638.3ms | refactor detector の scoring と suppress 導線を追加 | Phase F |
| `detect_axis_10_ms` | 73.7ms (`rc=1`, path resolve error) | `NFR-10` 30000ms 以内 | 時間は -29926.3ms だが機能未達 | symlink / temp root 対応で path 解決を安定化 | Phase F |
| `detect_axis_11_ms` | 54.2ms (`failed`) | `NFR-10` 30000ms 以内 | -29945.8ms | regression baseline writer を接続 | Phase D |
| `detect_axis_12_ms` | 48.8ms (`blocked`) | `NFR-10` 30000ms 以内 | 時間は -29951.2ms だが blocked | connection deficiency の入力 data を増やす | Phase E |
| `detect_axis_13_ms` | 62.9ms (`failed`) | `NFR-10` 30000ms 以内 | -29937.1ms | model/skill telemetry の欠損補完 | Phase F |
| `detect_axis_14_ms` | 54.0ms (`passed`) | `NFR-10` 30000ms 以内 | -29946.0ms | orchestration 監査を routing table と統合 | Phase E |
| `db_query_vmodel_contract_to_test_gap_ms` | 0.747ms | `NFR-10` 関連 30000ms 以内 | -29999.253ms | query より writer 実装を優先 | Phase D |
| `db_query_vmodel_code_to_baseline_gap_ms` | 0.057ms | `NFR-10` 関連 30000ms 以内 | -29999.943ms | `coverage_eligible` への baseline 接続を追加 | Phase D |
| `db_query_vmodel_test_to_baseline_gap_ms` | 0.010ms | `NFR-10` 関連 30000ms 以内 | -29999.990ms | test baseline 自動投入を追加 | Phase D |
| `db_query_vmodel_full_chain_ms` | 0.023ms | `NFR-10` 関連 30000ms 以内 | -29999.977ms | 4 layer chain 実データ投入後に再測定 | Phase D |
| `db_query_invocation_summary_ms` | 0.074ms | `NFR-10` 関連 30000ms 以内 | -29999.926ms | materialized summary ではなくまず record 完整性を優先 | Phase F |
| `db_query_detector_summary_ms` | 0.028ms | `NFR-10` 関連 30000ms 以内 | -29999.972ms | benchmark 保存後に p95 管理へ移行 | Phase F |
| `coverage_eligible_without_baseline_count` | 51 rows | `NFR-13` 補助指標 0 rows が望ましい | +51 rows | PostToolUse / test baseline writer を接続 | Phase D |
| `full_chain_rows` | 0 rows | `CONCEPT` 目標 4 layer chain 稼働、`L1` では整合度 80% | 実測不能 | schema ではなく writer と link writer を先行 | Phase D |
| `budget_status_json_ms` | 11741.3ms | `NFR-22` 関連 guard 実行は対話的に返ること | 体感上重い | `ccusage` 依存を cache / async refresh 化 | Phase E |
| `claude_weekly_used_pct` | 100% | `NFR-22` warning 80%, stop 100% | warning 比 +20pt, stop 到達 | 80% 超時の `budget_events` 永続化を必須化 | Phase E |
| `claude_weekly_remaining_pct` | 0% | `NFR-22` 20%以上が望ましい | -20pt 以上 | 予算逼迫時の role/model fallback を強制 | Phase E |
| `claude_weekly_cost_usd` | $434.64 / budget $200.00 | `NFR-21` 既存予算内 | +$234.64 | 週次予算と実 cost の差分警告を追加 | Phase E |
| `claude_weekly_tokens` | 680,038,900 tokens | `NFR-20` PM token -50% | 比較 baseline 欠如 | PM/PMO 分離で baseline 計測を追加 | Phase B |
| `claude_block_projected_cost_usd` | $62.13 | `NFR-21` 既存 budget 内運用 | 残 budget 文脈不足 | block cost の週次換算を表示 | Phase E |
| `budget_events_rows` | 0 rows | `NFR-22` 発火履歴が残ること | 観測欠落 | warning/fallback/limit を全件 insert | Phase E |
| `cost_log_rows` | 126 rows | `NFR-20/21` の根拠化に十分な telemetry | rows はあるが中身不足 | `tokens_est` と `cost_est` 実値投入を復旧 | Phase E |
| `cost_log_total_tokens` | 0 tokens | `NFR-20` 比較基盤が必要 | 観測欠落 | token 見積ではなく provider 実績を保存 | Phase E |
| `cost_log_total_cost_usd` | $0.00 | `NFR-21` 実支出追跡が必要 | 観測欠落 | `cost_log` の writer を有効化 | Phase E |
| `role_cost_tl` | unit USD 未観測 / 16 invocations | `NFR-20` role 別最適化可能な粒度 | 観測欠落 | `invocation_log.cost_cents` を全 role で記録 | Phase E |
| `role_cost_se` | 約 $0.0043 / invocation, 7 invocations (`0.03/7`) | `NFR-20` role 別最適化可能な粒度 | sample 少 / 不完全 | sample 増と provider 原価の整合確認 | Phase E |
| `role_cost_pe_pg` | unit USD 未観測 / 22 invocations | `NFR-20` role 別最適化可能な粒度 | 観測欠落 | `pg` 実行にも cost_cents を保存 | Phase E |
| `role_cost_pmo` | unit USD 未観測 / 1 invocation | `NFR-20` PMO 経路の token 削減証明 | 観測欠落 | `pmo` role の invocation 集計を固定化 | Phase B |
| `role_cost_research` | unit USD 未観測 / 13 invocations | `NFR-20` role 別最適化可能な粒度 | 観測欠落 | research role の単価ログと task size 併記 | Phase B |
| `codex_budget_source` | `unavailable` (`~/.codex/state.db` absent) | `NFR-21/22` Codex 側も予算監視 | 観測欠落 | Codex state source fallback を実装 | Phase E |
| `bench_snapshots_rows` | 0 rows | benchmark 継続比較があること | 観測欠落 | `helix bench` / CI で自動蓄積 | Phase F |

## 監査軸別所見

### 1. CLI 起動時間

- 代表値として `helix status` は cold **44.7ms**, warm p50 **41.6ms**。
- 現時点で CLI 起動そのものはボトルネックではありません。
- ただし `helix detect` は dispatcher 経路が未配線で、速度以前に command routing が一貫していません。

### 2. detector 実行時間

- 最遅は `axis-01` **2245.2ms**。
- 多くの axis は `50ms` 前後で返りますが、`passed/failed/blocked` より前に **例外終了** するものがあり、`NFR-10` の本質的な阻害要因は速度より安定性です。
- `axis-03` は `IndentationError`、`axis-10` は temp root での path 解決例外です。

### 3. dashboard 表示時間 / SessionStart

- `helix-dashboard --json` は **28.6ms**、`helix-session-start` は **118.9ms**。
- 現状の SessionStart 単体は `NFR-12` に十分余裕があります。
- ただし V2 で `detect dashboard --quick` や auto-sync を積み増すと、将来の headroom は減ります。今のうちに `bench_snapshots` 保存が必要です。

### 4. DB クエリ性能

- 素の SQLite query は全て **1ms 未満**。
- ただしこれは record が薄いから速いだけで、4 layer chain の真の運用性能ではありません。
- `coverage_eligible` symbol 59 件中、baseline 未接続が **51 件** あるため、V-model query の現状は高速でも有効性が低いです。

### 5. Codex / Claude API token 消費

- `budget status` は `Claude weekly_tokens=680,038,900`, `weekly_cost_usd=$434.64`, `weekly_used_pct=100` を返しています。
- 一方で DB 側の `cost_log` は `tokens_est=0`, `cost_est=0.0` なので、**provider 集計とローカル DB が二重化し、しかも一致していません**。
- `invocation_log` は role / duration / bytes を持ちますが、`cost_cents` はほぼ空です。

### 6. role 別 cost

- 頻度は `invocation_log` から取れます。
  - `pg`: 22
  - `tl`: 16
  - `research`: 13
  - `se`: 7
  - `pmo`: 1
- ただし unit USD は `se` のみ少量観測 (`$0.03/7`) で、他 role は未観測です。
- したがって、role 別 cost 最適化はまだ **議論可能な粒度まで観測できていません**。

### 7. cost guard 80% / 100%

- guard のしきい値文書は存在しますが、`budget_events` が 0 rows のため、**いつ warning / fallback / stop が起きたか証跡がない** 状態です。
- 現在の `claude.weekly_used_pct=100` は stop threshold 到達を示しますが、DB には発火履歴が残っていません。

### 8. week budget

- `weekly_budget_usd=200.0` に対し `weekly_cost_usd=434.64`。
- `NFR-21` の「既存予算内」はこの snapshot 上は明確に未達です。
- `Codex source=unavailable` なので、全体予算の半分しか見えていません。

### 9. bottleneck top-10

1. `helix-budget status --json --no-cache`: **11741.3ms**
2. `helix-detect dashboard --json`: **2350.4ms** (`rc=1`)
3. `axis-01 dead code drift`: **2245.2ms**
4. `axis-09 refactor opportunity`: **361.7ms**
5. `axis-06 naming confusion`: **280.0ms**
6. `axis-03 real duplicate`: **133.6ms** (`rc=1`)
7. `helix-session-start`: **118.9ms**
8. `axis-08 plan-retro integrity`: **110.9ms**
9. `axis-10 relation graph`: **73.7ms** (`rc=1`)
10. `axis-13 model & skill analytics`: **62.9ms**

## 目標未達 / リスク整理

### 目標未達

- `NFR-10`
  - 時間自体は満たす採取値が多いが、`helix detect dashboard` と `axis-03/10` が **完走失敗**
- `NFR-20`
  - PM token 50% 削減を検証する baseline がなく、`role_cost_*` が未観測
- `NFR-21`
  - `weekly_cost_usd=$434.64` が `weekly_budget_usd=$200.0` を超過
- `NFR-22`
  - `weekly_used_pct=100`、`budget_events=0 rows`、Codex 側 budget source unavailable

### 重点改善 top-5

1. `cost_log` / `invocation_log.cost_cents` / `budget_events` を一貫させ、role 別 token/cost の観測を成立させる。
2. `axis-03` の parse error と `helix-detect dashboard` 失敗を直し、`NFR-10` を「時間」だけでなく「完走」で満たす。
3. `helix-budget status` の `11.74s` を削るため、`ccusage` 依存を cache / async refresh 化する。
4. `contract_entries -> test_design_entries -> test_baseline` の writer を実装し、4 layer chain を空運用から脱出させる。
5. `bench_snapshots` を埋めて cold/warm / detector / session-start の時系列 benchmark を残す。

## 推奨

推奨方針は次の 3 点です。

1. **Phase E を先行**して observability を直す。
   - 理由: 現在の最大ギャップは raw speed より measurement gap です。`budget_events`, `cost_log`, `invocation_log.cost_cents`, `bench_snapshots` が埋まらない限り、NFR-20〜22 は議論不能です。
2. **Phase D で 4 layer chain writer を入れる。**
   - 理由: 現 DB query は速いが空運用です。現状の「高速」は根拠として弱く、実運用 data が入った時点で再測定が必要です。
3. **Phase F で dashboard の継続 benchmark 化。**
   - 理由: `session-start` と `dashboard` は今は十分速いので、最適化より regression guard の方が優先です。

## ソース

- `docs/v2/L1-REQUIREMENTS.md`
- `docs/v2/CONCEPT.md`
- `docs/v2/A-audit/db-schema-current.md`
- `docs/plans/PLAN-065-qa-strictness.md`
- `cli/helix-status`
- `cli/helix-dashboard`
- `cli/helix-budget`
- `cli/helix-detect`
- `cli/libexec/helix-session-start`
- `cli/lib/helix_db.py`
- `.helix/helix.db`

## 集計

- 全メトリクス件数: **43**
- 「目標未達」一覧:
  - `detect_dashboard_ms`
  - `detect_axis_03_ms`
  - `detect_axis_10_ms`
  - `claude_weekly_used_pct`
  - `claude_weekly_remaining_pct`
  - `claude_weekly_cost_usd`
  - `budget_events_rows`
  - `cost_log_total_tokens`
  - `cost_log_total_cost_usd`
  - `role_cost_tl`
  - `role_cost_pe_pg`
  - `role_cost_pmo`
  - `role_cost_research`
  - `codex_budget_source`
  - `bench_snapshots_rows`
- V2 で **重点改善** top-5:
  - cost telemetry 一貫化
  - `axis-03` / `detect dashboard` 安定化
  - `helix-budget status` 高速化
  - 4 layer chain writer 実装
  - benchmark 永続化
