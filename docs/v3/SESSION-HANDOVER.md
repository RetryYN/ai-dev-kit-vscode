# HELIX V3 — セッション引き継ぎメモ

> 更新: 2026-06-26 / 対象: V3 design corpus を **最新 clean harness の網羅 capture から再構築**（Phase B→A 完遂）
> 正本: [V3-CHARTER §6](V3-CHARTER.md) / **base SSoT = [新 base 網羅 capture](audit/2026-06-26-new-base-comprehensive-capture.md)** / memory `project_2026_06_26_v3_rebuild_from_clean_harness`

## 1. いま どこ（現在地）

- **最新 clean harness（`UT-TDD_AGENT-HARNESS-main.zip`、984 entries）を差し替え**（旧版 = `-2026-06-25.zip` に退避）。harness が refactoring で clean 化 + FE/design-bottomup/refactor-candidate を net-new 追加していた。
- **8 領域並列 capture + 二巡目本文補完**（FR-L1 registry 51 / concept v3.1 / gate-design / ADR-001〜007 / L3-L6 設計本文 / enum 全列挙 / 56-table inventory / oracle family）→ [capture doc](audit/2026-06-26-new-base-comprehensive-capture.md) が **V3 base SSoT**。
- **TL adversarial review（tl-advisor 2026-06-26）= changes_required → 契約(C-1〜C-5)反映後 go**。capture §9.5 に反映済。
- **Phase A 完遂: docs/v3 corpus 全 18 doc を新 base から再構築**（charter / engine C1-C6 / L0-L6 / fe / harness / distribution / helix-w）。**すべて未コミット**（untracked, P-tier）。**物理削除・DB 破棄・注入トリムは未実行**。

## 2. 確定事項（再 litigate しない・charter §9 で旧前提を訂正済）

1. **DB = 56-table clean registry**（旧「core 14 + Phase2」を訂正。projection ⊥ append_event 分類、TL C-1）。`test_results`(current) ≠ `test_result_events`(red→green 履歴、**V3 新設の append_event**)。
2. **detector = pure-function 3 層 + `source_kind`(db_projection/file_snapshot/hybrid)**（旧「DB-only・file scan 禁止」を訂正、TL C-3）。普遍 = ok=AND + lint-wiring + absence-blindness 防止。
3. **FE = harness の設計ガバナンスを盗む**（旧「HELIX 最大の優位・src/web 空」を訂正）。§1c per-layer / frontend-design-coverage / screen-impl-pair-freeze / tokens.yaml SSoT / design-bottomup。**実 UI 描画(src/web)だけ greenfield**。
4. **駆動 = 13-14 mode**（+screen-design/frontend-design/design-bottomup）。
5. **言語 = Python 反転**（harness=TS/Bun、ADR-001）。zod→pydantic / bun:sqlite→stdlib sqlite3 / vitest→pytest / biome→ruff。公開 API `@~/.helix/core/<path>` 据え置き。
6. **review-guard は git 計算（source_kind=file_snapshot）→ guardrail_decisions**（`working_tree_snapshots` table は作らない＝harness 実態）。
7. **HELIX 独自強化（FE 実描画 / 中央 UI ADR-005 / 既存 hook）は capture 後の別フェーズ**（ユーザー指示）。
8. **盗む net-new**: promotion_strategy / 全 PLAN §6・§7 delta / auto-enroll rule engine(11 型) / tier-router / attempt-escalation / refactor-candidate / review-guard / vmodel.json。

## 3. TL 確定契約（freeze 前に固定、capture §9.5 / charter §3）

C-1 table 分類(projection⊥append_event) / C-2 row identity(logical_key/stale_key/delete_scope) / C-3 detector(pure+loader+source_kind+ok=AND+absence fail) / C-4 cutover gate(pin inventory/dangling/rollback) / C-5 secret・PII・raw transcript 非保存。

## 4. 次にやること（resume point、この順）

1. **(任意・推奨) corpus を 1 commit で固定** — `docs(v3): rebuild corpus from clean harness capture (TL contracts applied)`。dogfood。**zip は add しない**。
2. **TL 再 review**（再構築済 corpus を tl-advisor で。C-1〜C-5 反映の確認 + 残 P1 有無）→ freeze。
3. **cutover gate 構築**（pin inventory / dangling detector / rollback、Python = Codex 委譲）。
4. **Phase 6 engine 実装先行**（test-first・L7 PLAN 起票・Codex 委譲）: **C1 schema-registry → C2 projection-writer**（engine が rebuild 可能になるまで cutover 不可 = フロー 5→6 逆転）。
5. **Phase 5 cutover**（破壊的・escalation）→ Phase 7-8 → HELIX 独自強化。

## 5. 落とし穴・運用メモ

- **explorer/PMO は「最終メッセージで構造化サマリを返す」モードで収束**（file 書くと非収束）。3/8 が途中経過で止まった → SendMessage で最終サマリ回収できる（context warm）。返答は grep で spot-verify。
- **tl-advisor 出力は SUMMARY tail のみ** → 完全版は rollout JSONL（`~/.codex/sessions/<date>/rollout-*.jsonl`）の最新 assistant text を python で抽出（[[feedback_rollout_jsonl_bypass_pattern]]）。
- **製造元 repo**: 設計 doc は Opus 直接編集可、Python 実装は Codex 委譲。委譲 Codex は commit/push しない。push は `helix push --gate`（8 gate）。
- §11 未読（capture）: concept §3.5 アンカー本文 / requirements_v1.2 §5-§10 / L7-unit-test §349 以降 / skill 本文多数。engine 実装で必要になったら都度補完。
