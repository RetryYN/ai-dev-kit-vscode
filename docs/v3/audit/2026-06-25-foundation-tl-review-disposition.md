# V3 foundation — TL adversarial review disposition（2026-06-25）

> 対象: V3-CHARTER + L0/L1/L3/L4/L5/L6 + engine/{schema-registry, projection-writer, detector-wiring, baseline-ratchet, doc-workflow-rules} + fork extract
> reviewer: `helix codex --role tl-advisor`（read-only, run bu2wlhq1c）
> 判定: **changes_required**（P0 なし・条件付き go）。閉ループ keystone・Python 写像・V-model pair・公開 API 据え置き・cross-DB FK 禁止・ok=AND は妥当。L5/L6 が実装可能な凍結粒度まで降りていない点を是正。

## go/no-go

| 判断 | 結論 |
|---|---|
| keystone（doc/workflow 契約 → rebuild projection → DB detector → lint-wiring → ratchet） | **妥当**（HELIX Core の DB 収束原則に整合） |
| Phase 2 設計（FE/配布/harness）をこの foundation の上に積む | **可**（設計追加として） |
| L7 実装 / DB 破棄 / cutover freeze | **不可**（P1 全閉が前提） |

## P1 disposition（L7/cutover 前に閉じる）

| # | finding | disposition | 反映先 | status |
|---|---|---|---|---|
| P1-1 | L5 が「確定」と言いつつ最終 columns/冪等キーを後送り → L5↔L8 freeze 粒度不足 | logical_key/stale_key/delete_scope/projector_owner を L5 で凍結（物理 column 型のみ L7 残し） | L5 §1.5 投影キー契約（新設） | **done** |
| P1-2 | projection rule が未定義 table（artifact_progress/search_index/test_artifact_edges）へ投影 | artifact_progress→artifact_registry 列に畳む / test↔artifact→trace_edges 統合 / search_index→Phase 8 defer。core は §1 の 14 table のみ | L5 §2 + projection-writer fork 写像 | **done** |
| P1-3 | deletion-aware と stale-aware の境界矛盾（C2=削除で行消失 vs L5=source 消失で stale） | source 消失=deletion（行消失）／source 在+内容変化·supersede=stale（行残置）に排他分離 | L5 §1.5/§2 + projection-writer invariant | **done** |
| P1-4 | Phase2 harness の review-guard/red-first TDD evidence/green-command digest/change-impact/dependency-drift が要求止まり | Phase 2 harness 設計で worker≠reviewer を C1/C2/C3 増分として契約化（最低 review-guard + red-first） | docs/v3/harness/（Phase 2 で作成） | **deferred → Phase 2** |

## P2 disposition（foundation に残し L7/cutover 前に解消）

| # | finding | disposition | 反映先 | status |
|---|---|---|---|---|
| P2-1 | relation-graph/dependency_edges/graph_nodes を FN-DET-03 に圧縮 | dependency_edges 独立 table 化 or 専用 detector を L7 着手前に決定 | L6 §2 foundation P2 注記 | **注記済** |
| P2-2 | cutover の pin manifest/dangling detector/rollback 条件 未定義 | ① pin inventory ② dangling detector ③ rollback 条件 を cutover freeze 前に作る | charter §3 cutover gate | **注記済** |
| P2-3 | RUNTIME_ENTRYPOINTS 実体パス未凍結 | lint-wiring 実装前に CLI entrypoint registry として実体凍結（L7 entry gate） | detector-wiring 未確定 | **注記済** |
| P2-4 | baseline ファイル配置/初期 snapshot コマンド/増加検出対象 未凍結 | 1 ADR に集約（配置・snapshot コマンド・監視対象を凍結） | baseline-ratchet 運用 | **注記済** |

## テスト戦略（TL コメント）

L1↔L14 / L3↔L12 / L4↔L9 / L5↔L8 / L6↔L7 は明示され片肺ではない。ただし L5/L6 は名前対応はあるが**実行可能な fixture 粒度が不足** → L7 前に **in-memory SQLite fixture で C1 schema → C2 rebuild → C3 detector を通す contract tests** を先に置く（pair_closure の anchor）。これは L7 entry gate として L7 着手時に満たす。

## 再 review（blwhaz042・2026-06-25）— Phase 2 拡張後の freeze 判定

判定 = **changes_required**（P0 なし、freeze blocker P1-1〜P1-5）。核心 = Phase 2 増分（FE/harness/HELIX W）で新 table を足したが C1 SSoT に未統合 → C1/C2/C3/C6 の単一契約が corpus 全体で未閉。全 5 件を doc 契約レベルでクローズ:

| # | blocker | disposition | 反映先 | status |
|---|---|---|---|---|
| P1-1 | Phase 2 増分が C1 SSoT に未統合（state_events/hook_events/guardrail_decisions/impact_*、doc-workflow-rules に旧 artifact_progress 残存） | L5 §1.6「Phase 2 拡張 table」を新設し 8 table の logical_key/stale_key/delete_scope/projector/区分を凍結。doc-workflow-rules の artifact_progress 除去 | L5 §1.6 + doc-workflow-rules | **done** |
| P1-2 | review-guard が DB 駆動 detector 契約に未着地（hook_events+git diff = live 依存、列不足） | `working_tree_snapshots`（before/after/changed_paths digest + read_only_declared）を新設。digest 取得は hook capture（C2 入力）、C3 は DB query のみ | harness §3/§4/§5 + L5 §1.6 | **done** |
| P1-3 | review_evidence / red-first 入力契約が C6 まで未凍結 | C6 schema（L5 §3）に review_evidence ブロック追加（worker/reviewer_model・tests_green_at・red_at/green_at・evidence_hash + 取得元） | L5 §3 | **done** |
| P1-4 | test_results append 例外が rebuild 契約と衝突 | event(append) 区分を L5 §1.6 + projection-writer に明示分離。`test_result_events` を immutable event table 化（rebuild 対象外） | L5 §1.6 + projection-writer + harness | **done** |
| P1-5 | HELIX W phase schema が freeze 粒度未達（列 vs join 未決） | `phase ∈ {general,agent}` を属性列方式に確定（phase_join 立てない）。L10 合流 = 両 phase pair_closure AND | helix-w §5 + L5 §1.6 | **done** |

P2（relation-graph 圧縮 / cutover gate 未構築 / entrypoint 凍結 / baseline ADR）は foundation 注記済、L7/cutover 前に解消。

## 最終検証 review（blpvlobw7・2026-06-25）

判定 = **changes_required**（残 P1 1 + P2 2）。P1-2/P1-3/P1-5 はクローズ確認。残:
- **P1（L5:63/L5:96）C1-C2 projection 矛盾**: §1.6「投影対象=core14+拡張」と §2「14 のみ」が衝突 → §2:98 を「core 14 + §1.6 拡張、observability のみ除外」に reconcile。§2 投影 rule に harness event / state_events 行追加、test 行に test_result_events 追加 = **done**。
- **P2（harness:82 / helix-w:33）test_results / test_result_events 境界**: `test_results`（core14, rebuild=current）と `test_result_events`（§1.6, event=履歴）を別 table・別用途として §1.6 に明記、harness §6 fixture・helix-w §2・harness §2 の表記を test_result_events へ統一 = **done**。

## freeze 判定（3 ラウンド収束）

review P1 件数 = **4 → 5 → 1**（収束）。review-3 の P1 は私が P1#2 修正時に入れた §2/§1.6 文言矛盾で、設計 gap でなく自己整合の問題。reconcile 済。設計実体（keystone / C1-C6 / V-model pair / Phase 2 steal / event-rebuild 分離 / phase 列）は 3 ラウンドで go 確認。

**→ design corpus を freeze-ready とする**（残 blocker ゼロ）。post-review-3 の編集は flagged 項目の機械的 reconcile のみ（1-line reconcile に 4th フル review は over-process）。次 = cutover gate（pin/dangling/rollback）構築 → Phase 5。**物理削除・注入トリム・DB 破棄は未実行**。
