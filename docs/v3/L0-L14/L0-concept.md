# HELIX V3 — L0 企画書（clean harness base 再構築）

> **status: 再構築中**（[新 base capture](../audit/2026-06-26-new-base-comprehensive-capture.md) を base に作り直し / 物理削除は cutover まで一切しない）
> 起点: [V3-CHARTER.md](../V3-CHARTER.md)（メタ・アンカー）/ base SSoT = capture doc / harness concept v3.1（capture §5）。
> 本書は HELIX **V3 harness** という *プロダクト* の企画書（L0）。「どう作るか」= charter、「何を作るか」= 本書。

## 0. 位置づけ

V3 は HELIX harness の **clean 再立ち上げ**。最新 clean UT-TDD Agent Harness（HELIX の TS/Bun フォーク、閉ループを実運用実証 + refactoring で構造 clean 化 + FE/design-bottomup/refactor-candidate を net-new 追加）を **忠実に capture し Python/SQLite で再構築**する。harness のコードは取り込まず設計意図を盗む。

ただし、V3 の最終形は UT-TDD Agent Harness の単純な移植ではない。UT-TDD harness は「人間が AI を安全に使い、漏れなく実装させる」ためのチーム駆動 harness である。HELIX 個人開発版はそこから一段進め、**AI 自身が gate / workflow / DB / detector の機械的ガードレール内で安全にシステム開発を自走する仕組み**にする。人間は常時監視者ではなく、runtime rules §10 の不可逆・破壊的境界だけを承認する。

HELIX 独自強化（AI 自走 orchestration、FE 実描画、配布、既存 AI 規律、設計書 template catalog、自動改善・自動保守）は capture 後の上乗せフェーズで行うが、L0-L6 の要求・設計には最初から **自走システムとして閉じるための機械契約**を埋め込む。

## 1. 背景・課題（concept v3.1 §1 の 4 問題 + HELIX 現状）

harness が解く 4 問題（concept v3.1）:
- **P1 設計・実装・テストの乖離**（AI が「テストも書いた」と言うが ③設計⇔テスト設計 doc 不在）
- **P2 役割境界の曖昧**（TL/QA/AI 実装の責任が PR ごとに食い違い）
- **P3 PoC の独り歩き**（知見が文書化されず再実装）
- **P4 既存実装への破壊的追加**（AI が既存設計を無断改変、既存テストを書き換え回帰検知不能）

現 HELIX の閉ループは**開いている**: detector が file glob scan（DB を読まない）/ `plan_registry` DB 24 件 vs disk 354 件乖離 / workflow が散文未登録 / 死蔵 detector 放置 / schema 分散（plan_lint/validator 二重管理 drift）。`docs/v2` は V1→V2 系譜で汚れ、107 pytest+49 bats+config が docs パスを pin → in-place retrofit はビルドを即赤にする。よって clean harness を base に V3 を立て、V2 以下を cutover で wholesale 廃止する。

## 2. 企画の核（V3 が提供する価値）

**検出を「detector の賢さ」でなく「DB が *あるべき集合* を持つこと」で成立させる。**

```
ルール化 doc/workflow  ──projection──▶  単一 registry(DB, SSoT)  ──query/snapshot──▶  pure-function detector
        ▲                                      │                                          │
        │ 機械パース可能な契約                  │ rebuild ⊥ append_event                    │ source_kind 宣言, ok=AND, fail-close
        └──────────────── lint-wiring（死蔵禁止）/ baseline ratchet（非後退）────────────────┘
```

doc と workflow を機械パース可能な契約（frontmatter/ID/必須セクション/forward_routing）にすると、単一 projection-writer が DB へ「あるべき集合」を投影する。detector はその DB（or snapshot 化した file）を読み「あるべき − 実在 = もれ」を出す。死蔵 detector は lint-wiring が禁止し、advisory→fail-close は baseline ratchet で非後退に昇格する。HELIX_CORE §2/§4 の doctrine（V-model 収束しない成果は DB コアに載らない／自動検出ループ）の**機械的実体**になる。

## 3. スコープ

**in（V3 で作る）**:
- engine keystone C1-C6（schema 単一 registry SSoT / projection-writer rebuild⊥append_event / pure-function detector + source_kind / lint-wiring / baseline ratchet / ルール化 doc/workflow 契約 + auto-enroll rule engine）。
- V-model corpus L0-L14（FR-L1 registry 51 / 粒度ペアリング / HELIX W）を Python で再構築。
- **13 駆動モデル**（`DRIVE_TDD_FITS`: design/add-feature/discovery/reverse/recovery/incident/refactor/retrofit/scrum/research + screen-design/frontend-design/**design-bottomup**。Forward backbone は駆動 mode に数えない）。
- **FE/UI 設計ガバナンス**（§1c per-layer / frontend-design-coverage / screen-impl-pair-freeze / tokens SSoT / design-bottomup）— **harness から盗む**（実 UI 描画 src/web のみ greenfield）。
- 配布（@~/.helix/core / setup / 4-provider 住所モデル）— 公開 API 据え置き。
- AI 規律 harness（agent-guard / tier-router / work-guard / review-guard / attempt-escalation / worker≠reviewer）。
- automation → DB 自動登録 → 検証 → 検出系強化。
- **設計書 template catalog**（外部・社内テンプレートを source provenance 付きで登録し、L0-L6/L8-L14 の doc coverage と gate 入力へ変換）。テンプレートは見本で終わらせず、frontmatter / required_sections / pair_test_design / trace_edges として DB へ投影する。
- **自動改善・自動保守 loop**（detector findings / review evidence / postmortem / test_result_events を learning candidate に変換し、PLAN draft / rule candidate / template gap として Forward DB に戻す）。
- **複数観点 review loop**（PM/TL/SE/QA/security/docs/perf/UX 観点を role-separated evidence として保存し、worker≠reviewer と tests_green_before_review を機械強制）。
- **prompt interpretation loop**（ユーザー指示を複数視点で解釈し、plan→execute→verify の前に scope / risk / test / doc coverage の解釈差分を検出する）。
- **upgrade-assist 補助駆動モデル**（将来の HELIX / dependency / platform upgrade を、retrofit とは別に readiness / delta capture / staged cutover / rollback evidence へ分解する）。

**out（やらない）**: TypeScript/Bun 化（Python 維持）/ 公開 API パス破壊 / harness ファイルの転用（設計を盗み新規構築）。

## 4. 駆動モデル ecosystem（concept v3.1 §2.5 — 13 mode）

Forward(spine) を背骨に、13 駆動 mode（`DRIVE_TDD_FITS` = design 含む 10 駆動 + 工程専門 screen-design/frontend-design + design-bottomup。capture §1）。出口は必ず Forward L0-L14 合流。signal→mode auto-routing（4 象限 priority: Incident>Recovery>Reverse>Refactor）、mode→command 機械契約、layer-context 注入 + orchestration_mode 5 値、横断検出 5 機構。実行モード 4 種（claude-only/codex-only/hybrid/standalone）。2 MUST 原則 = ①ルール同一性（Claude/Codex 同一判定・同一 exit code）②hybrid 機能分散（frontier-reviewer ≠ worker runtime）。

- **unitized L5-L7 descent**（大規模実装の分解規律、Forward 内・駆動 workflow ではない）: L4 まで一貫 Forward → large unit のみ L5→L6→L7 を unit 単位で刻む。Scrum（要件反復）と別概念。詳細・guardrail = [C6 §4.5](../engine/doc-workflow-rules.md)。
- **upgrade-assist**（補助駆動、C6 で契約化）: dependency / provider / model / HELIX version の将来 upgrade を、現行 Forward 成果物へ逆流させずに delta capture → impact projection → staged retirement/cutover → Forward return で閉じる。retrofit が「既存構成を現行正本へ合わせる」入口であるのに対し、upgrade-assist は「将来差分を安全に評価して取り込む」入口。

## 5. W-model（concept v3.1 §2.3.3）

製品が AI エージェントシステムを作る場合に **UT-TDD W（2 段 V）**: Phase 1（一般システム L1-L9）+ Phase 2（エージェント昇華 L1-L9）→ L10 合流。harness 自身は外殻（VSCode/Claude Code）が既存のため**単一 V** で進める。V3 は製品が harness（=agent system）のため自己適用を [helix-w-design](../helix-w-design.md) で扱う。

## 6. 成功基準（後続 L で検証条件へ）

| # | 企画ゴール | 後続検証の方向 |
|---|---|---|
| G-1 | DB が artifact の SSoT になる | plan_registry 等が DB == disk（projection 後乖離ゼロ） |
| G-2 | detector が pure-function 3 層 + source_kind 宣言 | file scan の無音 fallback ゼロ、absence=ok=false |
| G-3 | 死蔵 detector ゼロ | lint-wiring green（全 detector 到達 or DEFERRED 理由付き） |
| G-4 | doc/workflow が機械登録 | workflow/PLAN/設計が projection-writer で DB 行・auto-enroll rule 適用 |
| G-5 | FE ガバナンス維持 | §1c per-layer FE 設計 coverage が frontend-design-coverage で fail-close |
| G-6 | 公開 API 無破壊・Python 維持 | `@~/.helix/core` パス不変、スタック Python/SQLite |
| G-7 | AI 自走が機械ガードレール内で成立 | plan→execute→verify→review→learn が DB/gate で閉じ、§10 境界だけ人間承認 |
| G-8 | 設計書群が資産化される | template catalog / doc coverage / trace_edges / pair_test_design が DB projection され、抜け漏れを detector が発見 |
| G-9 | Vモデルが同一粒度で閉じる | L1↔L14, L2↔L10, L3↔L12, L4↔L9, L5↔L8, L6↔L7 の設計 doc coverage とテスト設計 coverage が同じ粒度で gate 判定 |

## 6.5 L0 workflow（今回の起点として実行する）

L0 は企画書を置くだけの工程ではない。HELIX 個人開発版では、**AI 自走開発システムとして何を作るか**を固定し、以降の L1-L6 が同じ目的へ降下しているかを機械的に検査できる状態にする。

| Step | 作業 | 出力 | 検査 |
|---|---|---|---|
| L0-0 | 入力固定 | user objective / handover / V3 charter / base capture / 外部 template evidence | 入力が artifact_registry へ登録可能 |
| L0-1 | 問題定義 | UT harness との差分（人間駆動→AI 自走） | BR-V3-08 へ trace |
| L0-2 | 価値定義 | AI 自走 / 設計資産化 / 自動改善 / review loop / prompt loop / upgrade-assist | G-7〜G-9 へ trace |
| L0-3 | 駆動モデル定義 | Forward spine + 既存 13 mode + upgrade-assist 補助駆動 | C6 drive contract へ trace |
| L0-4 | 設計資産化方針 | template catalog / doc coverage / pair_test_design / provenance | FR-TPL / REQ-TPL へ trace |
| L0-5 | 検証条件化 | L1/L3/L4/L5/L6 で要求・受入・設計・DB・detector へ降下 | trace_edges + doc_coverage gap 0 |

**初期 external template seed**:
- CREX「設計書テンプレート集」(https://crexgroup.com/ja/development/project/design-document-templates/): 要求定義 / 基本設計 / 詳細設計 / DB設計 / 画面設計 / バッチ設計 / テスト仕様書を工程別 template として扱う。品質観点は「誰が読んでも理解できる」「5W1H」「図表活用」「構造化」「一貫性」「バージョン管理」「レビュー」を template quality rule に正規化する。
- HELIX では本文を複製せず、`source_url` / `doc_kind` / `layer` / `required_sections` / `pair_test_kind` / `provenance_hash` / `freshness_status` へ正規化し、`template_catalog` と `doc_coverage` に投影する。
- seed catalog の第一バッチは [template-catalog-seeds](../engine/template-catalog-seeds.md) に置く。外部 source は HELIX canonical term へ直結せず、[domain-glossary](../engine/domain-glossary.md) の anti-corruption mapping を通す。
- review / prompt interpretation / learning-maintenance / upgrade-assist の個人開発版 workflow と全 drive model の Forward DB 収束は [personal-edition-workflows](../engine/personal-edition-workflows.md) を正本にする。

**G0.5 企画突合ゲート**（判定証跡: [G0.5-l0-to-l1-handoff](../gates/G0.5-l0-to-l1-handoff.md)）:
- L0 が `AI safe autonomous development system` を主語にしている。
- UT harness との差分が BR/FR に落ちている。
- すべての追加価値が Forward L1-L6 のどこで検証されるか決まっている。
- 外部テンプレートは本文コピーではなく normalized template catalog として扱う方針になっている。
- §10 escalation 境界（prod/auth/payment/PII/secret/license/schema/env/external API）は AI 自走から除外されている。

**今回の workflow 体感から得る改善観点**:
- L0 で目的語が曖昧なまま L1 へ進むと、UT harness の人間駆動前提が残る。差分を BR-V3-08 として明示する。
- L0 で template catalog を入れないと、L3 以降の設計書 coverage が「人間の記憶」依存になる。L0 で資産化方針を入れる。
- L0 で補助駆動を定義しないと、将来 upgrade が retrofit / recovery / cutover に散らばる。upgrade-assist を L0 で設計対象に入れる。

## 6.6 L0→L1 handoff（G0.5 出力）

`HELIX-workflows/helix-process/planning-to-requirements-transition.md` に従い、G0.5 通過時は次を L1 へ渡す。今回は L0 から開始するため、この handoff を満たさない限り L1 以降を freeze しない。

| Handoff | 内容 | L1 受理先 |
|---|---|---|
| L1-IN-VISION | HELIX 個人開発版 = AI が機械ガードレール内で安全に自走する開発システム | BR-V3-08 / FR-AUTO |
| L1-IN-SCOPE | V3 Python/SQLite engine + doc/workflow contract + template catalog + review/prompt/learning loop + upgrade-assist | L1 §2 FR 群 |
| L1-IN-NON-GOAL | TypeScript/Bun 移植、公開 API 破壊、外部 template 本文の無断複製、§10 境界の自己承認はしない | NFR / escalation |
| L1-IN-VALIDATION | L1 で運用テスト設計、L3 で受入テスト設計、L4-L6 で総合/結合/単体テスト設計へ降下する | L1 §4 / L3 §2 / L4-L6 test design |
| L1-IN-DECISIONS | 採択: AI 自走、template catalog、review loop、prompt loop、learning loop、upgrade-assist。保留: 実装 table 物理列と UI 実描画。見送り: L4 からの直行開始 | L1/L3/L4-L6 |

**禁止事項**: L0/G0.5 handoff を満たさずに L4 基本設計から開始しない。L4-L6 の記述は、L0→L1→L3 の trace がある項目だけを詳細化する。

## 7. 制約 / リスク

- **Python/SQLite 維持** / **公開 API 据え置き** / **物理 FK は同一 DB 内のみ**（cross-DB FK 破綻の教訓）/ **cutover まで V2 現役**。
- 主要リスク: cross-DB FK 再発（→ logical ref + detector）/ count-pin ripple（→ baseline ratchet）/ projection 非冪等（→ rebuild⊥append_event 契約を最初に固定）/ cutover dangling（→ pin inventory + dangling detector）/ TS→Python 等価ズレ（→ 契約テストで独自固定）/ **要約のみで engine 凍結**（→ Phase B 二巡目 capture で緩和済）。

## 8. 次工程

→ **L1 要求定義**（harness FR-L1 registry 51 を採用し BR/NFR + 運用テスト設計へ）。engine keystone は L4/L5/L6 で capture を反映して確定。
