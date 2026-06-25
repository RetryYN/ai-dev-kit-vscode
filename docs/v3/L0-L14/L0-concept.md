# HELIX V3 — L0 企画書（clean harness base 再構築）

> **status: 再構築中**（[新 base capture](../audit/2026-06-26-new-base-comprehensive-capture.md) を base に作り直し / 物理削除は cutover まで一切しない）
> 起点: [V3-CHARTER.md](../V3-CHARTER.md)（メタ・アンカー）/ base SSoT = capture doc / harness concept v3.1（capture §5）。
> 本書は HELIX **V3 harness** という *プロダクト* の企画書（L0）。「どう作るか」= charter、「何を作るか」= 本書。

## 0. 位置づけ

V3 は HELIX harness の **clean 再立ち上げ**。最新 clean UT-TDD Agent Harness（HELIX の TS/Bun フォーク、閉ループを実運用実証 + refactoring で構造 clean 化 + FE/design-bottomup/refactor-candidate を net-new 追加）を **忠実に capture し Python/SQLite で再構築**する。harness のコードは取り込まず設計意図を盗む。HELIX 独自強化（FE 実描画 / 配布 / 既存 AI 規律）は capture 後の別フェーズ。

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

**out（やらない）**: TypeScript/Bun 化（Python 維持）/ 公開 API パス破壊 / harness ファイルの転用（設計を盗み新規構築）。

## 4. 駆動モデル ecosystem（concept v3.1 §2.5 — 13 mode）

Forward(spine) を背骨に、13 駆動 mode（`DRIVE_TDD_FITS` = design 含む 10 駆動 + 工程専門 screen-design/frontend-design + design-bottomup。capture §1）。出口は必ず Forward L0-L14 合流。signal→mode auto-routing（4 象限 priority: Incident>Recovery>Reverse>Refactor）、mode→command 機械契約、layer-context 注入 + orchestration_mode 5 値、横断検出 5 機構。実行モード 4 種（claude-only/codex-only/hybrid/standalone）。2 MUST 原則 = ①ルール同一性（Claude/Codex 同一判定・同一 exit code）②hybrid 機能分散（frontier-reviewer ≠ worker runtime）。

- **unitized L5-L7 descent**（大規模実装の分解規律、Forward 内・駆動 workflow ではない）: L4 まで一貫 Forward → large unit のみ L5→L6→L7 を unit 単位で刻む。Scrum（要件反復）と別概念。詳細・guardrail = [C6 §4.5](../engine/doc-workflow-rules.md)。

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

## 7. 制約 / リスク

- **Python/SQLite 維持** / **公開 API 据え置き** / **物理 FK は同一 DB 内のみ**（cross-DB FK 破綻の教訓）/ **cutover まで V2 現役**。
- 主要リスク: cross-DB FK 再発（→ logical ref + detector）/ count-pin ripple（→ baseline ratchet）/ projection 非冪等（→ rebuild⊥append_event 契約を最初に固定）/ cutover dangling（→ pin inventory + dangling detector）/ TS→Python 等価ズレ（→ 契約テストで独自固定）/ **要約のみで engine 凍結**（→ Phase B 二巡目 capture で緩和済）。

## 8. 次工程

→ **L1 要求定義**（harness FR-L1 registry 51 を採用し BR/NFR + 運用テスト設計へ）。engine keystone は L4/L5/L6 で capture を反映して確定。
