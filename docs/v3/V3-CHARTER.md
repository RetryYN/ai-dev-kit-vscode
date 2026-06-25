# HELIX V3 Charter — clean harness base からの再構築（Python 化 + HELIX 優位の後乗せ）

> **status: corpus 再構築中**（最新 clean harness の網羅 capture を base に docs/v3 を作り直し → TL 契約反映後 freeze）。**物理削除・DB 破棄・注入トリムは cutover まで一切しない**。
> base SSoT: [新 base 網羅 capture](audit/2026-06-26-new-base-comprehensive-capture.md)（最新 `UT-TDD_AGENT-HARNESS-main.zip` を 8 領域並列 capture + 二巡目本文補完。本書はこれに従属し、衝突時は capture が上書き）。
> 決定経緯: 2026-06-25 V3 clean 立ち上げ方針 → 2026-06-26 **harness が refactoring で clean 化 + FE/design 駆動/refactor-candidate を net-new 追加**したため「最新 harness を丸ごと忠実に capture（今）→ HELIX 独自強化は capture 後（後）」へ（ユーザー指示）。
> 関連: [設計差分 対照表](../research/2026-06-25-fork-detector-adoption-comparison.md) / [engine 抽出](../research/2026-06-25-fork-engine-design-extract.md)（**旧版基準・行番号陳腐化注意**、旧 zip = `-2026-06-25.zip` で検証可）。

## 0. なぜ V3（in-place retrofit を捨て、clean harness を base にする）

- 現 `docs/v2` は **V1→V2 系譜で汚れている**（I-legacy-import / L2-MASTER / CONCEPT の V1 比較・deprecated banner = Strangler Fig 遺物）。V1 は V2 に織り込まれ**ファイル境界で切れない**。**107 pytest + 49 bats + config が docs パスを pin** → 外科的 excise は build を即赤にする。
- フォーク（UT-TDD Agent Harness = HELIX の TypeScript/Bun フォーク）は **閉じたパズルとして実運用で証明済み**。さらに 2026-06-26 時点で **refactoring により構造が clean 化**（schema/lint/workflow を policy/types 分離・schema を catalog+per-domain module へ分解）し、**FE 設計ガバナンス・design-bottomup 駆動・refactor-candidate detector を net-new で追加**。旧 V3 corpus（旧 fork 抽出）より完成度が上。
- 結論: in-place 差し替えでなく **最新 clean harness を忠実に V3 base として capture → Python 化 → HELIX 独自強化を後乗せ → V2 以下を cutover で wholesale 廃止**。

## 1. V3 設計の背骨（clean harness 由来 keystone）

V3 は「**ルール化 doc/workflow 契約 → 単一 registry SSoT(schema) → projection-writer(rebuild ⊥ append_event) → detector(pure-function 3 層・ok=AND) → lint-wiring メタゲート → baseline ratchet**」の閉ループを正本にする（harness で実証済）。

| keystone | 中身（capture §で実証） | HELIX 現状との差 |
|---|---|---|
| **C1 schema 単一 registry SSoT** | DDL を単一 registry から生成（**SCHEMA_VERSION=18 / 実 56 table**、catalog + tables-{core,evaluation,graph} + indexes）。識別子 fail-close（import 時 `assertSqlIdentifier`）。**table を projection ⊥ append_event に分類**（TL C-1） | plan_lint/validator 二重管理 drift・schema 分散 → 根絶 |
| **C2 単一 projection-writer** | `rebuild_projection`= projection table のみ TRUNCATE+再投影（原子・冪等 upsert・stableId 決定的 PK）。`append_event`= append table へ冪等追記（rebuild で消えない）。secret/PII/raw transcript 非保存（TL C-5） | file scan・DB 24件 vs disk 354件の乖離 → DB を正本化 |
| **C3 detector** | **pure-function 3 層**（`analyze`/`load`/`messages`）+ 各 detector に `source_kind: db_projection\|file_snapshot\|hybrid` 明示（TL C-3）。「あるべき − 実在 = もれ」を ok=AND・absence-blindness 防止（scope-0 silent OK 禁止）で検出 | HELIX detector は毎回 glob scan・無音 fallback → 契約化 |
| **C4 lint-wiring メタゲート** | 配線されない死蔵 detector を BFS 到達性で禁止（harness: DEFERRED 理由付き 1 件 + stale 申告も violation） | HELIX に相当なし（死蔵 detector 放置）→ 新設 |
| **C5 baseline ratchet** | shrink-only baseline（`oracle-test-trace-baseline` = 件数増加禁止 ReadonlySet + CI monotone-decrease assert） | 人手 closure ledger → 機械化 |
| **C6 ルール化 doc/workflow 契約** | frontmatter(layer/status/pair_artifact)/ID/必須セクション/forward_routing を機械パース可能に。**auto-enroll rule engine（11 型）**= 新 doc が現れたら全 rule 自動適用（lint 手書き不要） | workflow は散文・未登録 → 契約化 |

## 2. clean harness → V3 取り込みマップ

> **転用（ファイル移植）でなく「忠実に capture して Python で新規構築」**。harness ファイルを V3 へ引きずらない＝系譜の汚れを構造的に断つ。HELIX 独自強化は capture 後の別フェーズ（§6 後段）。

| 次元 | clean harness 実態 | V3 での扱い |
|---|---|---|
| **D1 DB/projection・D3 schema** | 56-table clean registry / projection⊥append_event | **Python で忠実に再構築**（C1/C2、TL C-1/C-2 凍結） |
| **D2 detector・lint アーキ** | pure-function 3 層・source_kind 混在・lint-wiring・baseline ratchet | **Python 再構築**（C3/C4/C5、TL C-3） |
| **D4 workflow 契約・駆動モデル** | **13-14 mode**（+screen-design/frontend-design/**design-bottomup**）・routing・auto-enroll | **Python 再構築**（C6） |
| **D5 V-model L0-L14 + 粒度ペアリング** | document-system-map §1 master / V-pair 6 組 / L6=単体粒度 DbC / FR-L1 registry 51 | **新規再構築**（L0-L6 corpus） |
| **D6 FE/UI** | **FE ガバナンス機械契約済**（§1c per-layer / frontend-design-coverage / screen-impl-pair-freeze / tokens.yaml / screens table / design-bottomup） | **harness から盗む**（旧 charter「HELIX 独自優位」は誤り＝§9-4）。**実 UI 描画(src/web)だけ greenfield** |
| **D7 agent/role harness** | agent-guard(14 allowlist)・tier-router(T0-T2)・work-guard・review-guard・attempt-escalation・worker≠reviewer | **Python 再構築**（D8 harness）+ HELIX 既存 hook 規律を後乗せ |
| **D8 配布** | GitHub-pull(ADR-005) / 中央 Web UI / 4-provider 住所モデル | **Python 再構築 + 公開 API `@~/.helix/core/<path>` 据え置き** |
| **D9 スタック** | TS/Bun（ADR-001） | **Python/SQLite へ反転**（公開 API・テスト資産を守る、zod→pydantic / bun:sqlite→stdlib sqlite3 / vitest→pytest / biome→ruff） |
| **D10 HELIX W** | harness 自身は単一 V（外殻=既存）。W は AI エージェントシステム製造時 | **新規再構築**（製品が harness ＝ agent system のため自己適用） |

**HELIX/V3 が持たず harness から新規に盗む**: `promotion_strategy`(reuse-as-is/with-hardening/redesign/discard) / 全 PLAN §6 用語 delta・§7 FR delta(anti-drift) / auto-enroll rule engine(11 型) / tier-router(T0-T2) / attempt-escalation(3-strikes) / refactor-candidate detector / review-guard / vmodel.json(4 artifact+8 edge) / 4-provider 住所モデル。

## 3. TL 確定契約（freeze-blocking、tl-advisor 2026-06-26）

freeze 前に固定する。engine 実装前の最小不変条件（詳細 = capture §9.5）:

- **C-1 table 分類**: projection（rebuild 全消し）⊥ append_event（冪等追記・truncate 対象外）。clean harness は projection-only だが **V3 は append_event を独自差分で追加**（red-first/green-digest/review-guard/hook-bypass の時系列監査）。`test_results`(current) ≠ `test_result_events`(red→green 履歴)。
- **C-2 row identity**: 各 table に logical_key / stale_key / delete_scope。rebuild 2 回 bit-identical、append_event は rebuild 後残存。
- **C-3 detector**: pure analyzer + loader 隔離 + `source_kind` 明示 + absence は ok=false + runDoctor.ok=AND + lint-wiring 維持。
- **C-4 cutover gate**: pin inventory / dangling detector / rollback condition が green まで cutover 禁止。
- **C-5 secret 境界**: secret/PII/raw transcript 非保存（ID・理由・score・redacted summary のみ）。

## 4. 破棄計画（V2 以下 wholesale 廃止）

- **cutover 時に一括退役**: legacy 一式（`docs/v2` + 散在 V1 + 旧 docs）＋ それを pin する **107 pytest + 49 bats + config を同 commit で同時退役**（dangling/orphan-red ゼロ）。
- **DB（`.helix/helix.db`）は再構築**（gitignored・rebuildable projection・捨てて困らない）。
- **物理削除は cutover まで一切しない**（V2 並行 build＝big-bang 破壊なし）。即時の context 緩和は legacy を**注入(@import/loader)から外す**（rm でなく注入トリム＝安全・可逆）。
- **cutover gate を freeze 前に作る**（TL C-4）: ① pin inventory ② dangling detector ③ rollback 条件。

## 5. V3 構造（`docs/v3/`）

```
docs/v3/
  V3-CHARTER.md          ← 本書（設計アンカー、capture §に従属）
  audit/
    2026-06-26-new-base-comprehensive-capture.md  ← base SSoT（全 keystone・56 table・enum・FR registry）
    2026-06-25-foundation-tl-review-disposition.md
  engine/                ← keystone 設計（clean harness 由来・Python build）
    schema-registry.md       C1: 56-table 単一 registry / projection⊥append_event / enum SSoT / 識別子 fail-close
    projection-writer.md     C2: rebuild_projection ⊥ append_event / 冪等 upsert / stableId / secret guard
    detector-wiring.md       C3/C4: pure-function 3 層 + source_kind + ok=AND + lint-wiring
    baseline-ratchet.md      C5: shrink-only baseline
    doc-workflow-rules.md    C6: frontmatter/ID/forward_routing 契約 + 13 mode + auto-enroll rule engine
  L0-L14/                ← V-model 設計（harness 由来・新規再構築）
    L0-concept.md            concept v3.1 骨子（4 問題 / 13 mode ecosystem / W-model）
    L1-requirements.md       FR-L1 registry 51 / BR / NFR(IPA×ISO 25010)
    L3-requirements-spec.md  L3 FR/AC-FR / screen-functional
    L4-basic-design.md       architecture(依存方向 ADR-002)/data(5 集約)/function(C1-C12)/external-if
    L5-detailed-design.md    module 分解 / physical-data(56 table)/ if-detail(D-CONTRACT)/ DbC freeze
    L6-functional-design.md  関数単位 DbC + U-* oracle / descent-obligation / gate-confirm
  fe/fe-ui-design.md     ← FE 設計（harness governance を盗む。§1c per-layer / tokens SSoT / screen-impl-pair / design-bottomup / 描画 greenfield）
  distribution/distribution-design.md ← 配布（ADR-005 GitHub-pull / 中央 UI / 公開 API 据え置き / 4-provider 住所）
  harness/harness-design.md           ← AI 規律（agent-guard/tier-router/work-guard/review-guard/attempt-escalation・DB 化）
  helix-w-design.md      ← HELIX W（2 段 V 合流。製品が agent system のため自己適用）
```
実装は Python clean engine（配置は build 段階で確定）。gate ID `G0.5-G14` / VALID_SUB_DOCS slug / rule 型 id / 公開 API path = **消費側依存の公開 API（破壊禁止）**。

## 6. 段取り（B→A→engine→cutover、tl-advisor 2026-06-26 妥当判定）

**Phase B（未読補完）→ A（corpus 再構築/Python 化）→ engine 先行（C1→C2）→ cutover → HELIX 独自強化 の一本道。**

1. **(完了) Phase B 二巡目 capture**: SSoT governance(FR registry/concept/gate-design/ADR) + L3-L6 設計本文 + schema-enum-test-design を補完（要約のみで engine 凍結する最大リスクを緩和）。
2. **(進行) Phase A corpus 再構築**: 本 capture を base に `docs/v3` の charter / engine C1-C6 / L0-L6 / fe / harness / distribution / helix-w を **§9 訂正 + TL 契約 + Python 化**で作り直す。製造元 repo の正業＝PM/architect(Opus) 直接起草。
3. **cutover gate 構築**（pin inventory / dangling detector / rollback、Python = Codex 委譲）。
4. **Phase 6 engine 実装先行**（test-first・L7 PLAN 起票・Codex 委譲）: **C1 schema-registry → C2 projection-writer**（engine が rebuild 可能になるまで cutover 不可）。
5. **Phase 5 cutover**（破壊的・escalation）: 旧 DB 破棄 + legacy docs/test 同時退役。cutover detector green 後。
6. **Phase 7-8**: DB 構築 + idempotent/deletion/stale 検証 → detector + lint-wiring + baseline 強化。
7. **HELIX 独自強化フェーズ**（capture 後）: FE 実 UI 描画 / 配布 setup / HELIX W / 既存 HELIX AI 規律 hook の上乗せ。

Phase 2/A は Opus 直接、実装コード（Python, Phase 6-8）は Codex 委譲。freeze 前に TL review。V2 は cutover まで現役。

## 7. status

**corpus 再構築中（Phase A）**。

- 旧「design corpus freeze-ready（3 TL ラウンド収束）」は **2026-06-26 の新 base capture で supersede**（旧 corpus は旧 fork 抽出 = 規模・実態が古い。§9 で 6 件の凍結事項を訂正）。
- Phase B 二巡目 capture 完了 → base SSoT = [capture doc](audit/2026-06-26-new-base-comprehensive-capture.md)。
- TL adversarial review（tl-advisor 2026-06-26）= **changes_required → 契約(C-1〜C-5)反映後 go**。capture §9.5 に反映済。
- 次 = Phase A の corpus 作り直し（engine C1-C6 → L0-L6 → fe/harness/distribution/helix-w）→ TL 再 review → cutover gate → engine 実装。**物理削除・注入トリム・DB 破棄は未実行**。
