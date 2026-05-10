# AI Knowledge Overlap Audit (2026-05-11)

## 概要

PLAN-060 W-1: 全 105 SKILL.md を対象に、Sonnet 4.6 / Opus 4.7 (= Codex) の base knowledge で代替可能か評価。
HELIX 固有の付加価値 (helix CLI 連携 / DESIGN.md / phase / gate / hook / harness 統合等) を持つかで判定。

## 評価方法

- 各 SKILL.md の frontmatter (description / metadata) と本文を確認
- HELIX 固有キーワード (`helix `/`HELIX `/`phase.yaml`/`gate-checks`/`DESIGN.md`/`hook`/`harness`/`ADR`/`SKILL_MAP`) の出現を grep
- 統合度に応じて 4 階層に分類

## 判定基準

| Q1 (base 代替) | Q2 (HELIX 固有) | 判定 |
|---|---|---|
| Yes (high) | 空 / 抽象 | **廃止候補** |
| Yes (high) | 具体的 HELIX 統合 | 維持 + brush up |
| Yes (low) | - | 維持 |
| No | - | 維持確定 |

## カテゴリ別件数

| カテゴリ | 総数 | 維持確定 | 維持 + brush up | 廃止候補 |
|---|---|---|---|---|
| workflow/ | 29 | 29 | 0 | 0 |
| common/ | 12 | 5 | 6 | 1 (coding) |
| agent-skills/ | 25 | 19 | 4 | 2 (code-simplification, git-workflow-and-versioning) |
| writing/ | 5 | 0 | 4 | 1 (story) |
| design-tools/ | 5 | 4 | 0 | 1 (graphic) |
| automation/ | 8 | 8 | 0 | 0 |
| integration/ | 2 | 2 | 0 | 0 |
| project/ | 8 | 8 | 0 | 0 |
| tools/ | 4 | 4 | 0 | 0 |
| advanced/ | 6 | 6 | 0 | 0 |
| **合計** | **104** | **85** | **14** | **5** |

(差 1 件 = SKILL_MAP.md 自身は SKILL ではない、105 = 104 + ルーター)

## 廃止候補 (5 件)

| skill | 廃止理由 |
|---|---|
| `common/coding` | 一般コーディング tips (命名・構造・型安全性)。HELIX 統合キーワード 0 件、verification は eslint/ruff 一般要件のみ。AI base で十分 |
| `design-tools/graphic` | Vercel Satori 一般解説。HELIX 統合キーワード 0 件 |
| `agent-skills/code-simplification` | upstream: addyosmani。HELIX 統合 0、code-simplifier 一般原則 |
| `agent-skills/git-workflow-and-versioning` | upstream: addyosmani。HELIX 統合 0、Git 一般原則 |
| `writing/story` | 「なぜ→何を→どうする→結果」ナラティブ構造、ADR テンプレート言及のみ。HELIX 固有要素薄い |

## 維持 + brush up 候補 (14 件、HELIX 固有あり、追記で強化)

| skill | HELIX 固有要素 |
|---|---|
| `common/refactoring` | helix learn / debt 統合 |
| `common/git` | helix pr リリースノート連携 |
| `common/documentation` | HELIX 成果物 / hook 統合 |
| `common/code-review` | HELIX レビュー観点 |
| `common/error-fix` | 失敗パターンレジストリ |
| `common/performance` | AI セッション記録 |
| `writing/explain` | HELIX 連携 |
| `writing/presentation` | HELIX ゲート/レトロ連携 |
| `writing/social` | HELIX L8 連携、D-RELNOTE |
| `writing/japanese` | HELIX 応答言語ルール |
| `design-tools/pptx` | HELIX L8 報告連携 |
| `design-tools/character` | HELIX fe/agent L5 連携 |
| `agent-skills/code-review-and-quality` | helix_gate G4/G6 |
| `agent-skills/test-driven-development` | helix gate G4 連携 |

## 維持確定 (85 件)

### workflow/ (29 件、HELIX フロー必須)
- project-management / dev-policy / estimation / requirements-handover / compliance
- design-doc / api-contract / dependency-map / quality-lv5 / deploy / dev-setup
- incident / observability-sre / postmortem / verification / adversarial-review
- context-memory / reverse-analysis / research / poc / gate-planning
- schedule-wbs / threat-model / runbook / debt-register
- reverse-r0 / r1 / r2 / r3 / r4 / rgc

### tools/ (4 件、HELIX harness)
- ai-coding (HELIX 中核)
- ide-tools / web-search / ai-search

### integration/ (2 件、HELIX 独自体系)
- agent-design (axis 11 本)
- agent-teams

### project/ (8 件、駆動タイプ別 HELIX フロー)
- ui / api / db / fe-a11y / fe-component / fe-design / fe-style / fe-test

### automation/ (8 件、HELIX CLI 連携)
- browser-script / flow-optimize / init-setup / job-queue / lock
- observability / scheduler / site-mapping

### advanced/ (6 件、HELIX 統合)
- ai-integration / external-api / i18n / legacy / migration / tech-selection

### common/ (5 件、HELIX 必須)
- visual-design (DESIGN.md ブランド参照)
- design (HELIX D-VIS-ARCH)
- testing (HELIX テストピラミッド)
- security (HELIX セキュリティ)
- infrastructure (HELIX デプロイ)

### agent-skills/ (19 件、HELIX 統合済 or 独自体系)
- spec-driven-development (HELIX 統合)
- helix-scrum (HELIX Scrum 専用)
- mock-driven-development (FE 駆動核心)
- system-design-sizing (donnemartin 由来)
- technical-writing (Google Tech Writing)
- planning-and-task-breakdown / incremental-implementation / context-engineering
- source-driven-development / frontend-ui-engineering / api-and-interface-design
- browser-testing-with-devtools / debugging-and-error-recovery
- security-and-hardening / performance-optimization / ci-cd-and-automation
- deprecation-and-migration / documentation-and-adrs / shipping-and-launch / using-agent-skills

### design-tools/ (4 件、HELIX 統合)
- diagram (HELIX 関連図)
- web-system (shadcn/ui + HELIX D-VIS-ARCH)
- pptx (L8 連携) ← brush up
- character (fe/agent L5 連携) ← brush up

### writing/ (4 件、HELIX 連携あり)
- explain ← brush up
- presentation ← brush up
- social ← brush up
- japanese ← brush up

## メタデータ

- 監査日: 2026-05-11
- 評価者: Opus 4.7 (PM、SKILL.md head + grep ベース)
- 対象: 104 SKILL (skills/{category}/{name}/SKILL.md)
- 廃止候補: 5 件 (4.8%)
- 維持 + brush up: 14 件 (13.5%)
- 維持確定: 85 件 (81.7%)

## 推奨アクション

1. **PLAN-060 W-2**: 5 件廃止候補を Opus + ユーザー最終承認 → 削除実行
2. **PLAN-059**: 維持 + brush up 14 件の解像度向上 (description / triggers / references 追加)
3. SKILL_MAP.md 更新 (5 件削除反映)
