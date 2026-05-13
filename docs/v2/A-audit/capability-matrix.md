# FR-INV03 Capability Matrix

## Scope

- 対象: HELIX V1 現状 capability の整理
- 観点: 5 層 `PM / Orchestration / Command / Skill / Verify` × 3 問題 `バグ / スパゲッティ化 / 契約漏れ`
- 注意: 要件文に「9 セル」とあるが、指定軸は `5 × 3` のため、本書では **15 セル** として整理する
- 判定基準:
  - `機能している`: 実装と検証が接続され、運用上も fail-close しやすい
  - `部分機能`: 実装はあるが、適用範囲・自動性・強制度が不足
  - `仕組み倒れ`: 枠組みはあるが、実利用や接続が弱い
  - `不在`: 該当層に明示 capability が見当たらない

## Matrix

| 層 | 問題 | 既存 capability | 状態 | 不足箇所 | Phase 紐付け |
|---|---|---|---|---|---|
| PM | バグ防止 | PM/TL ゲート運用 (`helix/HELIX_CORE.md`, `skills/SKILL_MAP.md`) と PM advisor / PMO 経路 (`docs/plans/PLAN-028-helix-v2-orchestration.md`, [`cli/helix-claude`](/home/tenni/ai-dev-kit-vscode/cli/helix-claude:1))。handover で blocker / ready_for_review を明示可能 ([`cli/lib/handover.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/handover.py:1)) | 部分機能 | PM 層は工程・承認の統制が中心で、実装バグの早期検知を直接 fail-close する能力は弱い。bug density や flaky 傾向を PM 視点で集約表示する dashboard が不足 | Phase H, Phase I |
| PM | スパゲッティ防止 | PLAN / WBS / role 分担の強制 (`helix/CODEX_TL_MODE.md`, `cli/ROLE_MAP.md`, PLAN-028)。PM が実装禁止になり責務分離は前進 | 部分機能 | 重複コード・関数肥大・暗黙依存を PM が追える集約指標がない。構造 debt を「PM が意思決定できる粒度」に翻訳する capability が不足 | Phase H, Phase J |
| PM | 契約漏れ防止 | D-API / D-DB / D-CONTRACT 変更時の人間確認ルール (`AGENTS.md`, `helix/HELIX_CORE.md`) と handover escalation ([`cli/lib/handover.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/handover.py:1)) | 部分機能 | ルール依存が強く、docs drift・API drift・handover 漏れを PM 向けに一元可視化する層がない。PM 向け契約差分レポートが必要 | Phase H, Phase I |
| Orchestration | バグ防止 | `helix codex` の consent / approved / allowed-files / summary audit (`docs/plans/PLAN-018-llm-guard-retroactive-hardening.md`, [`cli/helix-codex`](/home/tenni/ai-dev-kit-vscode/cli/helix-codex:1))、`helix claude` の実行モード制約 (`PLAN-028`, [`cli/helix-claude`](/home/tenni/ai-dev-kit-vscode/cli/helix-claude:1))、axis-14 orchestration detector ([`cli/lib/detectors/registry.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/detectors/registry.py:1)) | 部分機能 | 委譲誤りやコンテキスト不足は抑止しているが、実装品質そのものは間接制御に留まる。役割別の失敗パターン学習と routing 最適化が必要 | Phase G, Phase H |
| Orchestration | スパゲッティ防止 | role 分担・task injection・allowed-files 注入で変更範囲を狭める設計 (PLAN-028, PLAN-018, [`cli/helix-codex`](/home/tenni/ai-dev-kit-vscode/cli/helix-codex:1)) | 部分機能 | 「どの役割に投げると構造劣化しやすいか」の feedback loop が弱い。構造 debt と delegation quality の接続が未成熟 | Phase H, Phase J |
| Orchestration | 契約漏れ防止 | plan_id / wbs_id / acceptance / reference-doc 注入で工程表準拠を強制 ([`cli/helix-codex`](/home/tenni/ai-dev-kit-vscode/cli/helix-codex:1))。research / docs / PMO を分離して無秩序な実装を抑止 (PLAN-028, PLAN-018) | 部分機能 | 契約変更の影響解析結果を orchestration routing に戻す仕組みが薄い。contract break を見て自動で `tl-advisor` / review 経路へ昇格させる制御が欲しい | Phase G, Phase H |
| Command | バグ防止 | `helix gate`, `helix test`, shims, post-validation, hook 群 (`PLAN-018`, [`cli/helix-gate`](/home/tenni/ai-dev-kit-vscode/cli/helix-gate:1), [`cli/lib/codex_post_hook.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/codex_post_hook.py:1), `verify/*.sh`) | 機能している | 入口ごとの検証は揃っているが、SessionStart / PostToolUse / pre-commit の自動同期は未統合。command 層の自動化統合は別 PLAN-067 が未完 | Phase I |
| Command | スパゲッティ防止 | `helix gate`、review、code/test entrypoint、shim による逸脱抑止。将来の `helix sync` / pre-commit detector 設計は PLAN-067 に存在 | 部分機能 | 重複・dead code・肥大化の実行タイミングが command ごとに散在。編集直後・commit 前・gate 前を一貫接続する command layer が不足 | Phase I, Phase J |
| Command | 契約漏れ防止 | `helix gate --pair-check` と contract guard 方針 (`PLAN-063`, [`cli/helix-gate`](/home/tenni/ai-dev-kit-vscode/cli/helix-gate:1))、raw CLI 遮断 (`PLAN-018`) | 部分機能 | API/YAML 契約中心で、FE state-events、handover、docs 実装 drift を一つの command UX に束ね切れていない。`helix sync`/`helix detect` との導線統合が必要 | Phase G, Phase I |
| Skill | バグ防止 | verification / testing / error-fix / ai-coding / research 系 skill が判断ガイドを提供 (`skills/SKILL_MAP.md`, `skills/common/testing/SKILL.md` など) | 部分機能 | skill は知識注入として有効だが fail-close ではない。採用漏れ・誤用を runtime で補足する強制力が不足 | Phase G, Phase J |
| Skill | スパゲッティ防止 | coding / refactoring / legacy / dependency-map skill に構造改善知識がある。recommender で task に応じた推挙も可能 ([`cli/lib/skill_recommender.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/skill_recommender.py:1)) | 部分機能 | skill 推挙と実際の構造欠陥検知が閉じていない。たとえば dup / dead / relation graph finding から refactoring skill を自動昇格する loop が弱い | Phase H, Phase J |
| Skill | 契約漏れ防止 | api / api-contract / db / reverse-analysis / verification skill が契約と drift の見方を持つ (`skills/project/api/SKILL.md`, `skills/workflow/api-contract/SKILL.md`) | 部分機能 | FE 契約、handover 契約、運用契約まで横断した「contract skill chain」が不足。契約種別ごとの推奨 skill が細かく出し分けられていない | Phase G, Phase H |
| Verify | バグ防止 | 14 detector + telemetry / gate integration (`PLAN-063`, [`cli/lib/detectors/registry.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/detectors/registry.py:1))、verification agent (`PLAN-010`, `verify/*.sh`)、pytest/Bats 群 | 機能している | 実装コード向けは強いが、プロダクト機能レベルの仕様逸脱や FE 動作 drift はまだ薄い。dynamic / scenario-level verify を厚くする余地あり | Phase G, Phase I |
| Verify | スパゲッティ防止 | axis-01 dead, axis-03 dup, axis-09 refactor, axis-10 relation graph, axis-14 orchestration により構造劣化を可視化 ([`cli/lib/detectors/registry.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/detectors/registry.py:1), `docs/plans/PLAN-063-helix-db-detector-system.md`) | 機能している | detector verdict を修正行動へ自動接続する layer が弱い。graph 可視化から具体 remediation plan へ繋ぐ補助が必要 | Phase H, Phase J |
| Verify | 契約漏れ防止 | contract registry (`PLAN-063`, [`cli/lib/contract_registry.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/contract_registry.py:1))、axis-07 doc drift、axis-08 plan integrity、axis-12 connection、`helix gate --pair-check`、Reverse / Fullback 系設計 (`PLAN-008`, PLAN-010) | 部分機能 | API/YAML 契約は前進しているが、FE 契約・handover 契約・運用契約までの coverage は不足。不整合を phase 横断で 1 つの score に落とす capability が必要 | Phase G, Phase H, Phase I |

## Cell Assessment

| 状態 | 件数 |
|---|---:|
| 機能している | 3 |
| 部分機能 | 12 |
| 仕組み倒れ | 0 |
| 不在 | 0 |

## Weakest Top-3

1. **PM × スパゲッティ防止**
   - 構造 debt を PM が扱える粒度に変換する capability が弱い
   - detector はあるが、コスト判断・優先度判断へ昇華する PM view がない
2. **Command × スパゲッティ防止**
   - detector 実行タイミングが散在し、file edit → sync → detector → gate が一本化されていない
   - PLAN-067 の自動 sync / pre-commit detector が未完で command fail-close が弱い
3. **Verify × 契約漏れ防止**
   - API/YAML 契約は前進しているが、FE / handover / docs-to-impl drift の統合検証は未成熟
   - `contract_entries` と design/handover artifacts の横断 score 化が次の強化点

## Recommendation

- **推奨 1: Phase G で契約系を最優先**
  - 理由: 契約漏れは API だけでなく docs / handover / FE 接続点へ広がっており、後工程ほど修復コストが高い
  - 重点: `contract_entries` の対象拡張、pair-check の FE/handover 接続、contract break 時の routing 強制
- **推奨 2: Phase H-I で orchestration と command の閉ループ化**
  - 理由: 既存 detector や gate はあるが、修正行動への接続が弱い
  - 重点: `helix sync`、PostToolUse / SessionStart / pre-commit detector、自動 routing 昇格
- **推奨 3: Phase J で PM view と remediation 管理を整備**
  - 理由: 構造 debt / orchestration debt / contract debt を PM が優先度判断できるダッシュボードが必要
  - 重点: detector 集計の要約、top debt ranking、carry/deferred と phase planning の接続

## Sources

- 要件定義: [docs/v2/L1-REQUIREMENTS.md](/home/tenni/ai-dev-kit-vscode/docs/v2/L1-REQUIREMENTS.md:109)
- Orchestration: [docs/plans/PLAN-028-helix-v2-orchestration.md](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-028-helix-v2-orchestration.md:1), [docs/plans/PLAN-018-llm-guard-retroactive-hardening.md](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-018-llm-guard-retroactive-hardening.md:1)
- Verify / detector: [docs/plans/PLAN-063-helix-db-detector-system.md](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-063-helix-db-detector-system.md:1), [docs/plans/PLAN-010-verification-agent.md](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-010-verification-agent.md:1)
- Reverse / contract drift: [docs/plans/PLAN-008-reverse-multitype.md](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-008-reverse-multitype.md:1)
- Automation gap: [docs/plans/PLAN-067-helix-automation-layer.md](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-067-helix-automation-layer.md:1)
- 主要実装:
  - [cli/helix-codex](/home/tenni/ai-dev-kit-vscode/cli/helix-codex:1)
  - [cli/helix-claude](/home/tenni/ai-dev-kit-vscode/cli/helix-claude:1)
  - [cli/helix-gate](/home/tenni/ai-dev-kit-vscode/cli/helix-gate:1)
  - [cli/lib/handover.py](/home/tenni/ai-dev-kit-vscode/cli/lib/handover.py:1)
  - [cli/lib/skill_recommender.py](/home/tenni/ai-dev-kit-vscode/cli/lib/skill_recommender.py:1)
  - [cli/lib/contract_registry.py](/home/tenni/ai-dev-kit-vscode/cli/lib/contract_registry.py:1)
  - [cli/lib/detectors/registry.py](/home/tenni/ai-dev-kit-vscode/cli/lib/detectors/registry.py:1)
