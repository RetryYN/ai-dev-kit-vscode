# FR-INV09 PLAN 外実装の棚卸し

## 概要

- 対象: `cli/` / `skills/` / `helix/` / `.claude/` / `docs/archive/` に残る capability / command / hook / skill / config / script
- 目的: `docs/plans/PLAN-001`〜`PLAN-068` のいずれにも明示紐付けが見えない実装を洗い出し、V2 で `PLAN 化 / 既存 PLAN へ統合 / 廃止 / 継続` を判断できる状態にする
- 判定基準:
  - `off-plan`: `docs/plans/` に明示言及が見当たらない、または capability の起源 commit が `PLAN-NNN` を持たず、根拠が memory / archive /運用文書側に偏っている
  - `merge`: 実装起源は off-plan だが、後続の PLAN/requirements に吸収済み
  - `new-plan`: 現行運用上は生きているが、正式 PLAN が不足
  - `deprecate`: 実体はあるが V2 コア運用へ残す必要が薄い
  - `keep`: ユーザー局所運用として残すが、V2 コア PLAN には昇格しない

## 不確実性

- `git log --all --no-merges --pretty=format:'%h %s'` と `rg` による静的監査であり、会話本文そのものは参照していない
- 一部 capability は後続 docs (`docs/v2/L1-REQUIREMENTS.md`, `docs/v2/CONCEPT.md`) には記載があるが、`docs/plans/` 側の一次計画が不足している
- `.claude/settings.json` のような複合設定は複数 commit / 複数 PLAN の結果であり、完全な単一起源は断定できない

## 発見項目

| 項目名 | 種別 | 発見手段 | commit | 言及元 | 推測される起源 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|
| `cli/helix-budget` | command | git log / memory のみ | `13b9ba5`, `c6a995c` | `memory/project_helix_budget.md`, `docs/features/helix-budget-autothinking/D-API/api-contract.yaml` | 運用上の必要から先行実装した MVP | `new-plan` | 実機能は大きいが `docs/plans/` に専用 PLAN が見当たらない |
| `skills/integration/agent-cost-design/SKILL.md` | skill | git log / 言及なし | `0337b34` | なし | 試験的な user skill 追加 | `keep` | コア能力よりローカル知識に近く、V2 コア PLAN 化の優先度は低い |
| `cli/roles/pm-advisor.conf`, `cli/roles/tl-advisor.conf`, `cli/roles/impl-sonnet.conf` | config | git log / doc grep で PLAN なし | `dfaae0d`, `88dac12` | `docs/v2/L1-REQUIREMENTS.md`, `docs/v2/A-audit/capability-inventory.md` | orchestration v2 を先回りして role 拡張 | `merge` | 要件・監査 docs には載っているため、PLAN-028 系へ統合するのが自然 |
| `.claude/settings.json` の hook 配線 (`SessionStart` / `PreToolUse` / `PostToolUse` / `Stop`) | hook | config/yaml 棚卸し | `3f703b7`, `4c3f2c1`, `a7c9c08` | `ADR-009`, `.claude/settings.json` | 複数 hook 強化を運用優先で逐次追加 | `merge` | 機能自体は PLAN-018 / 043 / 063 に散っているが、最終配線の正本 PLAN がない |
| `helix/sync-codex-skills.sh` | script | git log / 言及なし | `8ee876b` | なし | Codex 連携の暫定セットアップ補助 | `deprecate` | `migrate` / installer 系に寄せられず、単独 script のまま残す必要性が弱い |
| `cli/helix-builder` | command | git log / memory のみ | `7ab8165`, `51004a3`, `46f6016` | `memory/project_builder_system.md`, `memory/project_2026_05_04_roadmap_consolidation.md` | Builder System を先行実装 | `new-plan` | 実装規模が大きく `cli/lib/builders/` 群まで持つのに、正式 PLAN が見当たらない |
| `cli/helix-discover` | command | git log / memory のみ | `f5db7bc`, `61af3cc`, `f90f0ec` | `memory/project_2026_04_23_codex_timeout_fix.md`, `memory/feedback_agent_judgment_verification.md` | Recipe / Learning Engine の実験経路 | `new-plan` | 削除候補から除外される程度に生きているが、PLAN 紐付けがない |
| `cli/helix-matrix` | command | git log / memory のみ | `7ab8165`, `f90f0ec` | `memory/project_2026_04_22_agent_skills_integration.md` | matrix 駆動の前倒し実装 | `new-plan` | V2 deliverable 管理に関係する中核 CLI なのに `docs/plans/` の所有 PLAN がない |
| `cli/helix-team` | command | git log / memory のみ | `d093966`, `7ab8165` | `memory/project_2026_04_23_codex_timeout_fix.md`, `memory/feedback_agent_judgment_verification.md` | mixed-agent/team 実験の本実装 | `new-plan` | 生存 CLI として扱われており、V2 orchestration へ正式接続が必要 |
| `helix plan reset` (`cli/helix-plan`, `cli/helix-plan-cmds/reset.sh`) | command | archive 残存 / memory | `689ebc6` | `docs/archive/proposals/helix-plan-reset-command-2026-05-01.md`, `docs/archive/proposals/helix-v3-followup-design-2026-05-01.md`, `PLAN-017` test mention | finalized plan 再編集の運用ギャップを即応実装 | `new-plan` | 実コマンドは運用されているが、専用 PLAN ではなく archive proposal に退避している |

## 選択肢

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| V2 で off-plan 実装ごとに新規 PLAN を起票する | 監査線が明確になり、後続 drift を減らせる | 文書数が増え、小粒な capability まで計画対象になる | 高 |
| 近縁 capability を既存 PLAN へ統合する | PLAN 数を増やしすぎず、責務を寄せられる | 起源の曖昧さが残り、後から追跡しにくい | 中 |
| ローカル helper / user skill は PLAN 化せず keep/deprecate で整理する | コア計画を汚さない | 人依存 capability が残りやすい | 中 |

## 推奨

- `new-plan` 対象は 6 件: `helix-budget`, `helix-builder`, `helix-discover`, `helix-matrix`, `helix-team`, `helix plan reset`
- `merge` 対象は 2 件: advisor / impl-sonnet role 群、`.claude/settings.json` hook 配線
- `deprecate` 対象は 1 件: `helix/sync-codex-skills.sh`
- `keep` 対象は 1 件: `skills/integration/agent-cost-design/SKILL.md`

推奨理由:

- 最も影響が大きい drift は、**CLI と orchestration の中核機能が memory / archive 起源で生きているのに、PLAN 正本がない**点
- V2 では `Builder/Discover/Matrix/Team/Budget/Plan Reset` を capability 単位で明示的に起票し、`docs/v2/L1-REQUIREMENTS.md` の依存関係へ逆リンクを張るのが妥当
- hook 配線や advisor role 群のように、実体は重要だが既存 PLAN に吸収しやすいものは `merge` で十分

## 発見件数集計

### 種別別

| 種別 | 件数 |
|---|---:|
| command | 6 |
| skill | 1 |
| config | 1 |
| hook | 1 |
| script | 1 |

### V2 変更計画別

| 計画 | 件数 |
|---|---:|
| `new-plan` | 6 |
| `merge` | 2 |
| `deprecate` | 1 |
| `keep` | 1 |

## 影響の大きい drift top-5

1. `cli/helix-builder`
2. `cli/helix-matrix`
3. `cli/helix-team`
4. `cli/helix-budget`
5. `helix plan reset`

## V2 で新規 PLAN 起票が必要な capability list

- `helix-budget`
- `helix-builder`
- `helix-discover`
- `helix-matrix`
- `helix-team`
- `helix plan reset`

## ソース

- `git log --all --no-merges --pretty=format:'%h %s'`
- `git log --follow --no-merges -- <path>`
- `rg -n "<capability>" docs/plans docs/adr docs/v2 ~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory`
- [cli/helix-budget](/home/tenni/ai-dev-kit-vscode/cli/helix-budget:1)
- [skills/integration/agent-cost-design/SKILL.md](/home/tenni/ai-dev-kit-vscode/skills/integration/agent-cost-design/SKILL.md:1)
- [cli/roles/pm-advisor.conf](/home/tenni/ai-dev-kit-vscode/cli/roles/pm-advisor.conf:1)
- [cli/roles/tl-advisor.conf](/home/tenni/ai-dev-kit-vscode/cli/roles/tl-advisor.conf:1)
- [cli/roles/impl-sonnet.conf](/home/tenni/ai-dev-kit-vscode/cli/roles/impl-sonnet.conf:1)
- [.claude/settings.json](/home/tenni/ai-dev-kit-vscode/.claude/settings.json:1)
- [helix/sync-codex-skills.sh](/home/tenni/ai-dev-kit-vscode/helix/sync-codex-skills.sh:1)
- [cli/helix-builder](/home/tenni/ai-dev-kit-vscode/cli/helix-builder:1)
- [cli/helix-discover](/home/tenni/ai-dev-kit-vscode/cli/helix-discover:1)
- [cli/helix-matrix](/home/tenni/ai-dev-kit-vscode/cli/helix-matrix:1)
- [cli/helix-team](/home/tenni/ai-dev-kit-vscode/cli/helix-team:1)
- [cli/helix-plan](/home/tenni/ai-dev-kit-vscode/cli/helix-plan:1)
- [docs/archive/proposals/helix-plan-reset-command-2026-05-01.md](/home/tenni/ai-dev-kit-vscode/docs/archive/proposals/helix-plan-reset-command-2026-05-01.md:1)
