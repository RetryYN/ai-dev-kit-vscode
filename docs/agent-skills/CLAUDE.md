# helix-agent-skills

HELIX 開発フレームワーク専用にフォークされた、AI コーディングエージェント向けのエンジニアリングスキル集。

> **Upstream**: [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)
> 本フォークでは日本語化 + HELIX 9 フェーズ統合 + Codex 12 ロール対応を追加。

## プロジェクト構造

```
skills/       → コアスキル (SKILL.md/ ディレクトリ単位)
agents/       → 再利用可能なペルソナ (code-reviewer, test-engineer, security-auditor)
hooks/        → セッションライフサイクルフック
.claude/commands/ → スラッシュコマンド (/spec, /plan, /build, /test, /review, /code-simplify, /ship)
references/   → 補助チェックリスト (testing, performance, security, accessibility)
docs/         → 各ツールのセットアップ手順
```

## HELIX フェーズ対応

| Phase (addyosmani) | HELIX Layer | 主要スキル |
|--------------------|-------------|------------|
| Define | L1 要件定義 | idea-refine, spec-driven-development |
| Plan | L2-L3 設計・詳細設計 | planning-and-task-breakdown |
| Build | L4 実装 | incremental-implementation, test-driven-development, context-engineering, source-driven-development, frontend-ui-engineering, api-and-interface-design |
| Verify | L6 統合検証 | browser-testing-with-devtools, debugging-and-error-recovery |
| Review | G2/G4/G6 ゲート | code-review-and-quality, code-simplification, security-and-hardening, performance-optimization |
| Ship | L7 デプロイ | git-workflow-and-versioning, ci-cd-and-automation, deprecation-and-migration, documentation-and-adrs, shipping-and-launch |

HELIX 独自スキル (Reverse HELIX / Scrum / adversarial-review / mock-driven-development / debt-register) は後続 Phase で追加。

## HELIX 規約 (frontmatter 拡張)

全 SKILL.md の frontmatter に以下を追加する:

```yaml
---
name: skill-name
description: 日本語でスキルの目的と発火条件を記述。「〇〇のときに使う」形式。
helix_layer: [L1, L3]            # HELIX レイヤ
helix_gate: [G0.5, G1]           # ゲート関連 (オプション)
codex_role: tl                   # 推奨 Codex ロール (tl/se/pg/fe/qa/security/dba/devops/docs/research/legacy/perf)
tier: 1                          # 優先度 (1: 即着手, 2: 次点, 3: 後回し)
upstream: addyosmani/agent-skills # フォーク元 (オプション)
---
```

## 規約

- 全 SKILL.md は日本語で記述 (上流の英語原文は git 履歴から参照可能)
- ディレクトリ名は `kebab-case`、ファイル名は `SKILL.md` (大文字固定)
- 1 SKILL.md = 1 ディレクトリ。参照資料は `references/` 配下に配置
- 100 行超の補助資料のみサブファイル化 (progressive disclosure)
- 各 SKILL.md は以下の節を備える: Overview / When to Use / Process / Rationalizations / Red Flags / Verification

## Commands

- 検証: 全 SKILL.md が有効な YAML frontmatter (`name`/`description`/`helix_layer`) を持つことを確認
- `npm test` — 該当なし (ドキュメントプロジェクト)

## 禁則

- 常に: skill-anatomy.md の形式に従う / 日本語で書く / HELIX frontmatter を付与する
- 禁止: 具体的な手順なしの抽象論 / スキル間の内容重複 (参照で代替) / 上流 MIT 表記の削除

## HELIX 本体との連携

HELIX 本体 (`~/ai-dev-kit-vscode`) の `helix skill search` / `skill use` コマンドから本スキル集を呼び出せるよう、`helix skill catalog rebuild` 対応の frontmatter を全 SKILL.md に統一する。

詳細は Phase F (本体統合) を参照。
