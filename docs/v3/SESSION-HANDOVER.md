# HELIX V3 — セッション引き継ぎメモ

> 更新: 2026-06-27 / 対象: **engine parity 到達 + 3 検出軸の段階 cutover 実行**（staged retirement stage①②③ + vg_overview→V3 委譲）
> 正本: [V3-CHARTER §6](V3-CHARTER.md) / **base SSoT = [新 base 網羅 capture](audit/2026-06-26-new-base-comprehensive-capture.md)** / cutover = [staged-retirement-plan](cutover/staged-retirement-plan.md) / memory `project_2026_06_26_v3_rebuild_from_clean_harness`

## 0. 最新の現在地（2026-06-27 — cutover staged-retirement 実行後）

> **cutover は wholesale でなく「V3 detector がカバー済の検出 subset のみ段階退役」**。V2 CLI は残置（V3 = 検出 ENGINE であって V2-full-CLI 置換ではない＝wholesale は category error、[readiness-assessment](cutover/readiness-assessment.md)）。

- **AI 主導・安全自走の原則を確立・配線**: HELIX_CORE §6（commit `6095c21`）に設置 → CLAUDE.md / AGENTS.md 入口に surface（`ebdcffa`）。機械的ガードレールの内側で AI が人間の逐次承認を待たず自走、停止は gate 赤/detector/V モデル逸脱/§10 破壊境界のみ。UT-TDD harness（チーム駆動）と対比。
- **archive 完了**: git tag `v2-archive-pre-cutover-20260627`（at `021e927`、annotated）+ origin/dogfood push。V2 完全保持の recovery point。
- **3 検出軸を段階 cutover（requirement_drift→FN-DET-04 / import_cycle→FN-DET-17 / plan_dependency→FN-DET-18）**:
  - stage① shadow（`eefeeee`、additive `helix v3-doctor` 並走・非破壊）
  - stage② 委譲（`90db9a8`、`HELIX_V3_DELEGATED_CHECKS` guard で V2 doctor を no-op 化・**env 復元で可逆**）
  - stage③ block 物理削除（`fcc9e4f`、V2 standalone dispatch 123 行除去・委譲永続化）
  - **vg_overview→V3 委譲 refactor**（`794afaa`、3 軸を delegated stub 化 + 3 helper を tombstone 退役 = V2 検出 1355 行除去。helper test は retire-marker 化）
  - **honest test closure**（`a32382f`、requirement_drift CLI contract test を委譲 contract へ更新）
- **regression 切り分け確定**: broad 回帰 4 fail = ①私の stage②委譲が invalidate した 1 件（修正済）+ ②cutover **前** archive tag `021e927` でも fail する **pre-existing repo 実負債 3 件**（`overall_clean=False`、L7+ deferred-gate 負債の正当な surface）。**cutover による新規 breakage はゼロ**。assertion を緩めて隠さない（guardrail 悪用回避）。
- **未実行（次セッションの user-gated）**: helper の**完全 file 物理削除** = registry retirement sweep（`functional-registry.yaml` path 登録 + `import-cycle-baseline.json` / `plan-dependency-baseline.json` + helix-doctor 残 dispatch + bats 整合）。§10 破壊境界・別ユニット・明示 GO 必須。**helper(.py)は今は tombstone 残置**（vg_overview 等が path pin → rm すると registry-drift）。

## 1. base 現在地（2026-06-26 — corpus freeze、不変）

- **最新 clean harness（`UT-TDD_AGENT-HARNESS-main.zip`、984 entries）を差し替え**（旧版 = `-2026-06-25.zip` に退避）。harness が refactoring で clean 化 + FE/design-bottomup/refactor-candidate を net-new 追加していた。
- **8 領域並列 capture + 二巡目本文補完**（FR-L1 registry 51 / concept v3.1 / gate-design / ADR-001〜007 / L3-L6 設計本文 / enum 全列挙 / 56-table inventory / oracle family）→ [capture doc](audit/2026-06-26-new-base-comprehensive-capture.md) が **V3 base SSoT**。
- **TL adversarial review（tl-advisor 2026-06-26）= changes_required → 契約(C-1〜C-5)反映後 go**。capture §9.5 に反映済。
- **Phase A 完遂: docs/v3 corpus 全 18 doc を新 base から再構築**（charter / engine C1-C6 / L0-L6 / fe / harness / distribution / helix-w）。**commit 426a09c（rebuild）+ freeze-fix commit（TL 3 round 収束 + harness-bug 4 契約）**。**TL re-review #3 = go → L1-L6+engine+harness corpus freeze 達成**。

## 2. 確定事項（再 litigate しない・charter §9 で旧前提を訂正済）

1. **DB = harness 56-table → V3 58**（旧「core 14 + Phase2」を訂正。harness 56 + V3 追加 2 = `test_result_events`(append) + `functional_registry`(projection)。分類 SSoT = C1 §5 = **projection 49 / append_event 3 / config 6**、TL C-1）。append_event 3 = `test_result_events` / `guardrail_decisions` / `hook_events`（capture §103 = red-first/review-guard/hook-bypass のみ）。`baseline_registry` は table でなく C5 frozenset、`state_events` は table でなく `screen_trace`。
2. **detector = pure-function 3 層 + `source_kind`(db_projection/file_snapshot/hybrid)**（旧「DB-only・file scan 禁止」を訂正、TL C-3）。普遍 = ok=AND + lint-wiring + absence-blindness 防止。
3. **FE = harness の設計ガバナンスを盗む**（旧「HELIX 最大の優位・src/web 空」を訂正）。§1c per-layer / frontend-design-coverage / screen-impl-pair-freeze / tokens.yaml SSoT / design-bottomup。**実 UI 描画(src/web)だけ greenfield**。
4. **駆動 = 13 mode**（`DRIVE_TDD_FITS` = design 含む 10 駆動 + screen-design/frontend-design/design-bottomup。Forward backbone は数えない）。
5. **言語 = Python 反転**（harness=TS/Bun、ADR-001）。zod→pydantic / bun:sqlite→stdlib sqlite3 / vitest→pytest / biome→ruff。公開 API `@~/.helix/core/<path>` 据え置き。
6. **review-guard は git 計算（source_kind=file_snapshot）→ guardrail_decisions**（`working_tree_snapshots` table は作らない＝harness 実態）。
7. **HELIX 独自強化（FE 実描画 / 中央 UI ADR-005 / 既存 hook）は capture 後の別フェーズ**（ユーザー指示）。
8. **盗む net-new**: promotion_strategy / 全 PLAN §6・§7 delta / auto-enroll rule engine(11 型) / tier-router / attempt-escalation / refactor-candidate / review-guard / vmodel.json。

## 3. TL 確定契約（freeze 前に固定、capture §9.5 / charter §3）

C-1 table 分類(projection⊥append_event) / C-2 row identity(logical_key/stale_key/delete_scope) / C-3 detector(pure+loader+source_kind+ok=AND+absence fail) / C-4 cutover gate(pin inventory/dangling/rollback) / C-5 secret・PII・raw transcript 非保存。

## 4. 次にやること（resume point、この順）

1. ~~corpus を 1 commit で固定~~ **DONE = `426a09c`**（`docs(v3): rebuild corpus from clean harness capture`、19 files、zip 除外、local only）。
2. **TL 再 review #1→#2 = 収束途上（未コミット修正分）**:
   - #1 changes_required（P1×4 + P2×3）→ 全反映: ①count→harness 56 / V3 58 ②**C1 §5 = 唯一の分類 SSoT**（append_event 3 のみ、findings/gate_runs/drive_runs/model_runs=projection）③functional_registry→C1 登録 / baseline_registry=C5 frozenset / state_events=screen_trace ④L4 DB-only→source_kind / §B dangling→実在節 repoint / PlanKind(11)⊥ArtifactType / 13 mode。
   - #2 = P1×4+P2×3 全解消を確認、ただし**新 P1（config を rebuild 対象に含めた自己矛盾）+ P2（L4 "Kind 12"）→ 反映済**: C1=「config は rebuild 非対象（seed/migrate、truncate されず残存）」、L5 §2 を **3 経路分離**（①rebuild TRUNCATE=projection 49 のみ ②config 6=seed ③append_event 3=append path）。
   - **harness-bug 予防 4 件を corpus に追加**（ユーザー: UT fork review 2026-06-26）→ [[project_2026_06_26_v3_harness_bug_prevention]]: #1 dry-run hermeticity / #2 execute⊥json honesty（harness §1.5 + FN-HRN-07/08）/ #3 detector source-completeness git→fs fallback fail-close（detector-wiring §3 + projection-writer §4 + AT-V3-09）/ #4 work-guard marker one-shot lifecycle（harness §1.6 + FN-HRN-06 hard）。
   - **TL 再 review #3 = `passed`（go / freeze 可。P1 なし）**: config 3 経路 + PlanKind/ArtifactType + harness-bug 契約 4 件すべて健全と確認。残 P2 2 件（FN-HRN-08 observable fixture / fallback root catalog 明示）は **L7 精緻化として corpus 記録済**（harness §7 / detector-wiring §検証）。
   - → 全修正を 1 commit（config fix + L4 enum + harness-bug 4 契約 + L7 P2 注記）→ **L1-L6 + engine + harness corpus freeze 達成**。
3. **cutover gate 構築**（pin inventory / dangling detector / rollback、Python = Codex 委譲）。
4. **Phase 6 engine 実装先行**（test-first・L7 PLAN 起票・Codex 委譲）: **C1 schema-registry → C2 projection-writer**（engine が rebuild 可能になるまで cutover 不可 = フロー 5→6 逆転）。
5. **Phase 5 cutover**（破壊的・escalation）→ Phase 7-8 → HELIX 独自強化。

## 5. 落とし穴・運用メモ

- **explorer/PMO は「最終メッセージで構造化サマリを返す」モードで収束**（file 書くと非収束）。3/8 が途中経過で止まった → SendMessage で最終サマリ回収できる（context warm）。返答は grep で spot-verify。
- **tl-advisor 出力は SUMMARY tail のみ** → 完全版は rollout JSONL（`~/.codex/sessions/<date>/rollout-*.jsonl`）の最新 assistant text を python で抽出（[[feedback_rollout_jsonl_bypass_pattern]]）。
- **製造元 repo**: 設計 doc は Opus 直接編集可、Python 実装は Codex 委譲。委譲 Codex は commit/push しない。push は `helix push --gate`（8 gate）。
- §11 未読（capture）: concept §3.5 アンカー本文 / requirements_v1.2 §5-§10 / L7-unit-test §349 以降 / skill 本文多数。engine 実装で必要になったら都度補完。

## 6. engine build phase（2026-06-26 goal、進行中）

> goal: cutover gate → engine 実装先行(C1→C2) → cutover → HELIX 独自強化。完遂。handover = `GOAL-V3-ENGINE`（GOAL-C-RIGHTARM は archive 済）。

- **方式 = unitized L5-L7 descent**（[C6 §4.5](engine/doc-workflow-rules.md)、ユーザー提案+TL refine を本 build に初適用）。engine を C1/C2/cutover-gate という unit に分解、各 unit L5/L6 frozen → L7 test-first。
- **code 住所 = `cli/lib/v3/`**（V2 と別名前空間、V2 不変 = rollback 保全。cutover で promote）。
- **proposals 取り込み済**（commit f866104）: proposal1 unitized L5-L7 descent（C6 §4.5）/ proposal2 内部 query contract pattern（helix-w §3.5、MCP table 流用禁止・既存経路投影・enhancement phase 実装）。
- **実装完了（Opus 独立検証済、全 `cli/lib/v3/`・V2 不変）**:
  - **C1 schema-registry**（`b3f35a6`）: 58 table faithful(552 col)+41 idx、sqlite materialize 成功、16 UT。API=`from v3.schema import registry, ddl`。
  - **C2 projection-writer**（`58f8a81`）: rebuild⊥append、truncate-scope/secret-guard/2x bit-identical 実証、14 UT。5 projector（残り Phase 7）。
  - **cutover-gate**（実装済・未コミット→本 commit）: 4 hard check(pin_inventory/dangling/rollback_preflight/rebuild_dry_run)、ok=AND、read-only、7 UT。**dangling が実 broken link 2 件捕捉(SESSION-HANDOVER §6 自己リンク)→修正済**、rebuild_dry_run=ok(engine 稼働確認)。
  - **cutover 設計**（`83682b6`/`6c3f602`）: staged、4 hard check、retirement inventory=270/117(FR-V3-CUT-01「107/49」訂正)、escalation 個別承認。
- **次 = Phase 7（projector ~30 完成 + 実 V2-source parse + DB 構築）→ Phase 8（~60 detector + lint-wiring + baseline）→ cutover（parity 到達 + 人間 go、破壊的）→ 独自強化（内部 query）**。
- **⚠ wholesale cutover EXECUTION は Phase 7-8 downstream**: V3 vs V2 387 test の全面 parity 前に V2 を wholesale 退役するのは巨大 regression。これは実行しない（readiness-assessment = NO-GO `3eb2a19` が正しい）。

## 7. 2026-06-27 cutover staged-retirement 実行（subset・§0 が最新）

> **wholesale NO-GO を踏まえた再フレーム**: V3 = 検出 ENGINE。wholesale V2 退役 = category error。正しい cutover = **V3 detector がカバー済の検出 subset のみ段階退役**（V2 CLI は残置）。詳細・実行記録 = [staged-retirement-plan §実行記録](cutover/staged-retirement-plan.md)。現在地サマリは **§0**。

- **engine parity（subset 範囲）到達**: 13 detector（FN-DET-01..18 の N/A 除く）+ 130 UT green、`run_v3_doctor` が C5 baseline ratchet 経由で現 repo に green（`6397561`/`ed69729`/`8b8a7a4`）。
- **3 検出軸の段階 cutover を実行**（stage①shadow→②委譲 guard→③block 削除→vg_overview 委譲→honest test closure）。commit chain = §0 参照。
- **新規 breakage ゼロ**を baseline 比較で機械確定。残る 3 fail は cutover 前から存在する pre-existing repo 実負債。
- **次の user-gated ユニット**: 完全 helper file 削除（registry retirement sweep、§10 破壊境界、明示 GO 待ち）+ 3 pre-existing repo 実負債（L7+ deferred-gate）の解消は別途。
