# UT-TDD フォーク検出機構 → HELIX 移植 対照表 (2026-06-25)

> **目的**: HELIX の TypeScript/Bun フォーク「UT-TDD Agent Harness」の検出機構を HELIX 本体(Bash/Python+SQLite)へ逆輸入する候補を、**1 本の対照表**に統合して残す。
> **位置づけ**: 研究/対照の正本。**設計(L4/L6)はどの detector も未凍結**＝本表の後に 1 detector ずつ設計レベルで詰め、対のテスト設計と同時に**凍結**(pair_closure・同時凍結・片肺禁止)していく(ユーザー方針 2026-06-25「対照表として残す→1つずつ設計で詰める→まだ凍結してない」)。
> **前段資産との関係**: 2026-06-21 の [research-memo](ut-tdd-fork-adoption-research-memo.md) (#1〜#15 ランキング + tl-advisor 判断 + ユーザー方針) を正とし、本表は **2026-06-25 の 10-detector 実コード gap 検証**でそれを更新・拡張する。Process container = [process-2026-06-21-ut-tdd-adoption-machine-precision](../plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md)。
> **入力**: `UT-TDD_AGENT-HARNESS-main.zip` (repo root, untracked, **コミット禁止**)。`src/lint/` = 61 detector / 14,156 行。
> **方針**: TS→Python は**ファイルコピーでなく概念の再実装**。各 detector = Forward V-model への **add-feature**(L4→L6 FN-*+DbC→L7 UT anchor)、advisory→fail-close を baseline ratchet で段階昇格。人間チームゲートは不採用(単独 AI-PM 前提維持)。

## 0. gap_status の凡例 (2026-06-25 実コード敵対的検証)

| gap_status | 意味 |
|---|---|
| **full** | HELIX に相当機能が見当たらない(完全な穴) |
| **partial** | 一部重なる別角度がある(フォークの角度の差分だけが価値) |
| **advisory_only** | 同等概念はあるが advisory/push 未接続止まり(昇格で足りる) |
| **covered** | fail-close で動いている(移植不要) |

> 重要: フォーク調査側の「HELIX に全く無い」推測は実コード検証で**大半が partial へ訂正**された。下表 gap_status は cli/lib を当たった検証結果。

## 1. 対照表 (前 memo + 2026-06-25 gap 検証の統合)

### 1.1 前 memo (#1〜#15) — tl-advisor 判断済み

| # | 項目 | フォーク実装 | HELIX 現状 | gap_status | 採否 / 優先 |
|---|---|---|---|---|---|
| 7 | **review-guard** (read-only レビュー subagent の working-tree 変更を path 差分検出) | `src/runtime/review-guard.ts` | 手動 git diff(tl-advisor 副作用の実害 IMP-137) | full | **採用 P1** |
| 1 | **red-first TDD evidence** (`red_at<green_at<=reviewed_at` 時系列) | `ddd-tdd-rules.ts:317` | 無し(TDD ファースト規律の実効化機構なし) | full | **採用 P1** |
| 3 | **descent-obligation provenance** (範囲展開被覆 vs focused 引用の区別) | `descent-obligation.ts:259` | vg_overview は ID 数のみ | partial | **採用 P1**(advisory+baseline) |
| 6 | **header 宣言件数 vs 実数 突合** ("計N件" 検証) | `fr-registry-audit.ts:122` | boundary_count_drift は audit YAML pin 限定 | partial | **採用 P2**(汎化) |
| 4 | **review_evidence enforcement** (worker≠reviewer model + `tests_green_at<=reviewed_at`=定性の機械保証) | `review-evidence.ts` | G-review は approve フラグのみ、semantic_gate は doctrine のみ | partial | **採用 P1** |
| 5 | **rule-drift + doc-consistency/propagation/glossary** (表記ゆれ防止 no-leak⑤) | `rule-drift.ts` 他 | core-manifest drift のみ、cross-doc 用語整合は弱い | partial | **採用 P2** |
| 9 | **change-set 推移的回帰 + コード AST dependency-drift** (デグレ/依存漏れ no-leak③④) | `change-impact.ts` + `dependency-drift.ts` | PLAN 粒度 dependency のみ、コード import グラフ無し | partial | **採用 P1-P2** |
| 2 | test oracle strength (弱アサーション AST 検出) | `ddd-tdd-rules.ts` | **anchor_quality.py で実装済み** | covered | **不採用(重複)** |
| 10 | チーム運用モデル(人間 TL/QA/PO×gate + CODEOWNERS) | `src/team/` | 単独 AI-PM 前提 | — | **部分採用**(escalation-stale/branch-protection-emit のみ P2、人間ゲートは不採用) |
| 11 | token/cost telemetry | provider JSONL 集計 | budget.py/session_telemetry あり | partial | P3 |
| 12 | 決定論モデル選択 + tier-router | `task/tier-router.ts` | allowlist guard のみ | partial | P3 |
| 13 | forced-stop / slot self-heal | `runtime/forced-stop.ts` | agent_slots あり・手動 release | partial | P3 |
| 14 | gate 自動追加エンジン(frontmatter 形状マッチで全 doc 適用) | — | doc 毎に detector 手書き | full | P3 後段 |
| 15 | enum SSoT(コンパイル時 drift 根絶) | zod | validator enum 二重管理 drift 常習 | partial | 採用 P3 |

### 1.2 2026-06-25 追加発見 (前 memo に無い候補・全件実コード gap 検証済み)

| ID | detector | フォーク実装 | HELIX 現状/相当(実コード) | gap_status | 価値 | コスト | GOAL-C 相乗 | 推奨 |
|---|---|---|---|---|---|---|---|---|
| **N1** | **merged-plan-status** (generates 成果物が merge 済なのに PLAN draft 放置) | `merged-plan-status.ts:83` | `run_check_plan_drift`(doctor_plan_checks.py) は「artifact 無い」方向のみ。逆向き未検出 | **full** | 高 | 低 | PLAN side closure 補完 | **採用**(advisory→fail-close) |
| **N2** | **lint-wiring** (登録・実装済だが gate 未配線の死蔵 detector を検出) | `lint-wiring.ts` | source_scan は逆向き(実装→登録)のみ。**axis-04/10/13 が今まさに死蔵**(registry.py:353 登録・phase_gate=None・全 gate 不在) | **full** | 高 | 低(variant A=集合差分 ~50行) | 右腕 detector 追加時の配線漏れ安全網 | **採用・前提インフラ最先行** |
| **N3** | **relation-graph** (req→plan→design→test→source→db の typed-edge グラフ走査) | `relation-graph.ts`(657行)+`graph/loader.ts` | axis_10_relation_graph.py は**別ドメイン**(内部 code-wiring dashboard・push 未接続)。V-model 縦断グラフ/orphan-table/source→test covered-by は無 | **partial** | 高 | 中(~450行+loader, 1-2 sprint) | covered-by edge=右腕 pair の graph evidence | **採用-as-enhancement**(Wave3 大型) |
| **N4** | **drive-model-passage / scrum-reverse** (各 drive mode の Forward 復帰テーブル機械強制 / confirmed PoC↔Reverse PLAN 双方向) | `drive-model-passage.ts`+`scrum-reverse.ts` | forward_return は PLAN frontmatter(plan_validator) 手書き依存。workflow doc に Passage Certificate 不在。scrum_to_reverse_routing.py は routing のみで orphan 検出なし | **full/partial** | 高 | 中(主コスト=workflow doc 9本へのテーブル追加) | G9/G14 semantic_gate 品質前提 | **採用**(advisory→fail-close) |
| **N5** | **db-projection-coverage / ingestion** (要件 doc の DB 定義↔実 schema + ingestion 証跡ゲート) | `db-projection-coverage.ts`+`db-projection-ingestion.ts` | drift_db_diff.py(+helix-drift-check)が schema diff 実装済だが**push 未配線(advisory)**。ingestion row-count ゲートは無 | **partial** | 中 | 低 | G9/G12/G14 schema/ingestion 証跡 | **採用-as-enhancement**(Wave3 defer・DB story 成熟後) |
| **+** | **oracle-test-trace ratchet** (oracle ID の test code citation 突合 + 右腕 baseline/ratchet) | `oracle-test-trace.ts` | g7_subcheck(UT fail-close)+g8-g14_subcheck(IT/ST/AT/OT advisory)+anchor_quality。**右腕の baseline/ratchet 機構が無く昇格不可** | **partial** | 高 | 低(`known_debt_ids` 追加) | **GOAL-C 直接 unblock** | **採用-as-enhancement** |

> N2(lint-wiring) と前 memo #14(gate 自動追加エンジン) は**別物**。#14=「全 doc にルール型を自動適用」、N2=「死蔵 detector の検出」。
> "oracle-test-trace ratchet" は前 memo #1(red-first)/#3(descent)/#2(oracle strength=不採用) と隣接するが、**右腕 g8-g14 の advisory→fail-close を baseline で開く角度**は前 memo で未分離。GOAL-C の最重要 unblock として独立追跡する。

## 2. 横断設計 — 各 detector を凍結する前に確定する共通契約 (L4 基本設計 + ADR)

各 detector を個別に設計→凍結すると規約がバラける。**以下の横断契約を先に L4 基本設計 / ADR として凍結**し、各 detector 設計(L4/L6)はこれに従って凍結する(2026-06-25 ユーザー指摘「まだ凍結してない」への回答 = 横断契約も各 detector 設計もどちらも未凍結)。

| 横断契約項目 | 論点 | 暫定方針(設計で凍結) |
|---|---|---|
| **共通基盤** | path 分類 / ID_PATTERN / sha256 / frontmatter parse / git diff が各 detector に散在する | `cli/lib/detector_utils.py` を 1 本作るか、既存(trace_symmetry.ID_PATTERN / audit_hash.sha256_of / changed_files)を流用するか |
| **advisory→fail-close 昇格基準** | 昇格条件が detector ごとに自己流になる | **1 ADR に集約**(baseline=0 / TL approve / CI green N 連続 等の共通 ratchet 契約) |
| **baseline ratchet 規約** | `known_debt_ids` / `*_BASELINE` の初期スナップショット生成手順・配置・縮小のみ可制約 | スナップショット生成コマンド + yaml 配置規約を 1 つに固定 |
| **配線規律** | 移植 detector の gate 未配線=死蔵リスク | **N2(lint-wiring)を先に入れて配線忘れを機械 block**(前提インフラ) |
| **登録税(count-pin)** | add-feature PLAN 追加で boundary_count_drift + 8 audit YAML の件数 pin が ripple(前 memo §96 / memory 反復) | FN/UT 登録バッチを先打ち or 各 PLAN exit に含める。GOAL-C in-flight 編集との衝突回避 |
| **TS↔Python 等価性** | フォーク実装との出力一致をどう保証 | 主要 detector(digest 照合/oracle 判定式)は fork 実装との比較テストを置くか |
| **二層成立 + no-leak の背骨** | 定量 detector ∧ 定性 LLM レビュー ∧ (FE)ブラウザ ∧ 実行 green の AND(前 memo §0.1/§0.2、ユーザー方針) | DDD/TDD 機械強制 spine(`ddd-tdd-rules.ts` 相当)へ寄せる |

## 3. 1 detector ずつ設計→凍結する順序 (案)

> 各ステップ = add-feature PLAN 起票 + L4/L6 設計 + 対のテスト設計 + tl-advisor review + user go(規律§7 / 本 repo=PM PLAN+go) → **凍結**(pair_closure・同時凍結)。**実装(L7)はその後**。

0. **横断契約(§2)** — 昇格基準・baseline 規約・共通基盤・配線規律を L4 基本設計 / ADR として先に**凍結**(各 detector 設計の前提)。
1. **N2 lint-wiring** — 前提インフラ。axis-04/10/13 の死蔵を炙り出し、以降の移植配線忘れを block。低コスト。
2. **oracle-test-trace ratchet** — GOAL-C(右腕 full-close)の直接 unblock。低コスト。
3. **N1 merged-plan-status** — full gap・低コスト・反復痛点。quick win。
4. **#3/N4 descent-obligation + drive-model-passage** — V-model 降下/forward_return の機械強制(前 memo #3 と統合)。
5. **#1 red-first / #4 review_evidence / green-command-digest** — 定性の機械保証(F2/F3 穴)。schema 拡張あり=count-pin 注意。
6. **#9 change-set + dependency-drift-ddd-ast** — デグレ/依存漏れ(no-leak③④)。AST。
7. **#6 header-count / #5 rule-drift** — 表記ゆれ(no-leak⑤)。
8. **N3 relation-graph** — 大型 architectural。covered-by グラフで右腕 evidence。
9. **N5 db-projection / #10 escalation-stale 等 P2-P3** — defer/後段。

## 4. 既存 Process との接続

- forward_return: 採用確定分は detector ごとに add-feature PLAN(kind=impl, `parent_process=process-2026-06-21-ut-tdd-adoption-machine-precision`)。
- GOAL-C-RIGHTARM-FULLCLOSE handover とは**分離**(orientation §0.1)。ただし oracle-test-trace ratchet は GOAL-C の unblock として相互参照。
- 起票順序制約: add-feature PLAN 追加は boundary_count_drift の件数 pin を ripple させる(前 memo §96)。GOAL-C は現在 parked のため、独立トピックとして件数同期込みで起票可。

## 5. evidence / 参照

- 前段研究: [ut-tdd-fork-adoption-research-memo.md](ut-tdd-fork-adoption-research-memo.md) (#1〜#15 詳細・tl-advisor decision=passed)
- Process: [process-2026-06-21-ut-tdd-adoption-machine-precision.md](../plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md)
- 2026-06-25 gap 検証 raw(6 detector): workflow task `wszo7qd0k.output`(scratchpad)。relation-graph/merged-plan-status/lint-wiring/drive-model-passage は本 session の 4 並列 pmo-sonnet 補完。
- フォーク: `UT-TDD_AGENT-HARNESS-main.zip`(root, untracked, コミット禁止)。`src/lint/`(61)・`src/doctor/index.ts`(runDoctor 配線)・`src/graph/loader.ts`・`src/gate/`。
- HELIX 既存突合: cli/lib/{vg_overview,requirement_drift,trace_symmetry,g7_subcheck,anchor_quality,review_evidence_checks,doctor_plan_checks,plan_validator,plan_lint,dependency_cycle_checks,ddd_registry_checks,drift_db_diff,scrum_to_reverse_routing}.py、cli/lib/detectors/{registry,axis_10_relation_graph}.py。
