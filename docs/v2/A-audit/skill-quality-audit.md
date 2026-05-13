# FR-INV18 skill catalog 品質監査

## 概要

- 対象実体は `skills/*/*/SKILL.md` で **104 skill**。`skills/SKILL_MAP.md` の「106スキル」とは不一致。
- カテゴリは実体上 **10カテゴリ**。`SKILL_MAP.md` の「11カテゴリ」指定とは不一致で、`writing/story` 記載残りと `project/fe-*` 5件未反映が主因。
- `skill_usage` テーブルは **0 行**。したがって usage hit 数は全件 `0` だが、厳密には「死蔵」ではなく「未計測」が混在する。
- `helix skill search/chain` はこの sandbox で内部 `helix-codex` セッション初期化に失敗し、**推挙ヒット率の実測は未完**。代替として frontmatter / triggers / catalog 露出を監査した。

## 選択肢

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| A. 現状維持 + metadata 補修のみ | 低コスト、破壊的でない | 重複と入口分散が残る | 低 |
| B. V2 で入口統合 + 大型 skill 分割 | 推挙精度と探索性が同時に上がる | 移行期の alias 管理が必要 | **高** |
| C. agent-skills を大幅廃止 | catalog を細くできる | upstream mirror の知識を失い、再利用性も下がる | 中 |

**推奨**: **B. V2 で入口統合 + 大型 skill 分割**。まず `project/ui` / `workflow/research` / `workflow/incident` 周辺を統合し、その後 `common/visual-design` / `tools/ai-coding` / `workflow/verification` を分割する。

## 主要所見

- frontmatter 品質: 良 81 / 部分 23 / 不在 0。部分 23 件は実質すべて `agent-skills/`。
- references 総数は 123。本文未リンクの references を持つ skill は 13 件。特に `project/fe-*` 5件、`workflow/research`、`design-tools/web-system` は入口導線が弱い。
- 10+ references の過大 skill は `common/visual-design` (44)、`tools/ai-coding` (16)、`integration/agent-design` (11)。
- `agent-skills/` は 23 件で、SKILL_MAP の「上流19 + HELIX独自4」と件数整合するが、frontmatter 形式が HELIX 標準に寄っておらず推挙品質を落とす。
- `writing/story` は SKILL_MAP に記載があるが実体ファイルがない。一方で `project/fe-design` / `fe-component` / `fe-style` / `fe-a11y` / `fe-test` は実体があるが SKILL_MAP 表に未反映。

## skill 個票

| skill id | 行数 | frontmatter 品質 | 使用履歴 | 重複候補 | V2 変更計画 | 理由 |
|---|---:|---|---:|---|---|---|
| `advanced/ai-integration` | 868 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `advanced/external-api` | 610 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `advanced/i18n` | 527 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `advanced/legacy` | 495 | 良 | 0 | advanced/migration | modify | レガシー改修と移行は近接するが実施局面が異なるため、境界明記で足りる |
| `advanced/migration` | 483 | 良 | 0 | advanced/legacy | modify | レガシー改修と移行は近接するが実施局面が異なるため、境界明記で足りる |
| `advanced/tech-selection` | 806 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `agent-skills/api-and-interface-design` | 299 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/browser-testing-with-devtools` | 320 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/ci-cd-and-automation` | 395 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/code-review-and-quality` | 354 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/context-engineering` | 303 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/debugging-and-error-recovery` | 304 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/deprecation-and-migration` | 210 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/documentation-and-adrs` | 282 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/frontend-ui-engineering` | 332 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/helix-scrum` | 449 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/idea-refine` | 182 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/incremental-implementation` | 245 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/mock-driven-development` | 301 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/performance-optimization` | 355 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/planning-and-task-breakdown` | 228 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/security-and-hardening` | 354 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/shipping-and-launch` | 314 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/source-driven-development` | 208 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/spec-driven-development` | 205 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/system-design-sizing` | 303 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/technical-writing` | 413 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/test-driven-development` | 384 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `agent-skills/using-agent-skills` | 178 | 部分 | 0 | - | modify | upstream mirror 系で metadata.triggers が空、HELIX 形式へ正規化が必要 |
| `automation/browser-script` | 247 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `automation/flow-optimize` | 153 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `automation/init-setup` | 40 | 良 | 0 | automation/observability | merge | 初期化と監視が小粒 skill のまま分裂し、単体では価値密度が低い |
| `automation/job-queue` | 47 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `automation/lock` | 39 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `automation/observability` | 39 | 良 | 0 | automation/init-setup | merge | 初期化と監視が小粒 skill のまま分裂し、単体では価値密度が低い |
| `automation/scheduler` | 45 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `automation/site-mapping` | 201 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/code-review` | 464 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/coding` | 114 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/design` | 307 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/documentation` | 720 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/error-fix` | 324 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/git` | 220 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/infrastructure` | 643 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/performance` | 921 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/refactoring` | 447 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/security` | 854 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/testing` | 470 | 良 | 0 | workflow/quality-lv5 | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `common/visual-design` | 11855 | 良 | 0 | project/fe-design, project/fe-style, design-tools/web-system | split | 44 references / 11,855 行で過大、ブランド事例と本体指針を分割すべき |
| `design-tools/character` | 215 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `design-tools/diagram` | 212 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `design-tools/graphic` | 198 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `design-tools/pptx` | 185 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `design-tools/web-system` | 1020 | 良 | 0 | common/visual-design | modify | references 3 件が本文から未参照で、入口導線の補強が必要 |
| `integration/agent-cost-design` | 679 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `integration/agent-design` | 1486 | 良 | 0 | agent-skills/spec-driven-development, integration/agent-teams | split | references が多く探索負荷が高い。索引 skill 化またはテーマ分割が必要 |
| `integration/agent-teams` | 645 | 良 | 0 | integration/agent-design | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `project/api` | 260 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `project/db` | 384 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `project/fe-a11y` | 634 | 良 | 0 | project/ui | merge | UI 派生 5 分割が project/ui と二重化し、利用者の入口が分散している |
| `project/fe-component` | 632 | 良 | 0 | project/ui | merge | UI 派生 5 分割が project/ui と二重化し、利用者の入口が分散している |
| `project/fe-design` | 642 | 良 | 0 | project/ui | merge | UI 派生 5 分割が project/ui と二重化し、利用者の入口が分散している |
| `project/fe-style` | 554 | 良 | 0 | project/ui | merge | UI 派生 5 分割が project/ui と二重化し、利用者の入口が分散している |
| `project/fe-test` | 668 | 良 | 0 | project/ui | merge | UI 派生 5 分割が project/ui と二重化し、利用者の入口が分散している |
| `project/ui` | 77 | 良 | 0 | project/fe-design, project/fe-component, project/fe-style, project/fe-a11y, project/fe-test | merge | UI 派生 5 分割が project/ui と二重化し、利用者の入口が分散している |
| `tools/ai-coding` | 4165 | 良 | 0 | - | split | 中核だが 4,165 行規模、governance と prompt recipe の分離余地が大きい |
| `tools/ai-search` | 149 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `tools/ide-tools` | 957 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `tools/web-search` | 163 | 良 | 0 | workflow/research | merge | 調査実務と検索手段が分離され過ぎ、G1R 導線で一体化した方が使いやすい |
| `workflow/adversarial-review` | 259 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/api-contract` | 372 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/compliance` | 262 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/context-memory` | 739 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/debt-register` | 294 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/dependency-map` | 349 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/deploy` | 467 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/design-doc` | 482 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/dev-policy` | 378 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/dev-setup` | 328 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/estimation` | 478 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/gate-planning` | 363 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/incident` | 447 | 良 | 0 | workflow/postmortem | merge | 障害対応と学習の境界はあるが現状は近接しすぎ、同一パック化が妥当 |
| `workflow/observability-sre` | 657 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/poc` | 351 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/postmortem` | 321 | 良 | 0 | workflow/incident | merge | 障害対応と学習の境界はあるが現状は近接しすぎ、同一パック化が妥当 |
| `workflow/project-management` | 354 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/quality-lv5` | 470 | 良 | 0 | common/testing, workflow/verification | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/requirements-handover` | 397 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/research` | 361 | 良 | 0 | tools/web-search | merge | 調査実務と検索手段が分離され過ぎ、G1R 導線で一体化した方が使いやすい |
| `workflow/reverse-analysis` | 91 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/reverse-r0` | 255 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/reverse-r1` | 274 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/reverse-r2` | 210 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/reverse-r3` | 194 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/reverse-r4` | 262 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/reverse-rgc` | 214 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/runbook` | 303 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/schedule-wbs` | 349 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/threat-model` | 287 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `workflow/verification` | 1079 | 良 | 0 | workflow/quality-lv5 | split | L1-L11 + Reverse を 1 skill に集約し過ぎ、V-model と Reverse を分離した方が明快 |
| `writing/explain` | 206 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `writing/japanese` | 217 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `writing/presentation` | 203 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |
| `writing/social` | 270 | 良 | 0 | - | as-is | 責務は明確で、現状は大きな再編より metadata 補修を優先すべき |

## 11カテゴリ件数（実地監査では 10カテゴリ）

| カテゴリ | 実体件数 | 注記 |
|---|---:|---|
| `workflow/` | 31 | - |
| `common/` | 12 | - |
| `project/` | 8 | `fe-*` 5件を含むが SKILL_MAP の一覧表には未反映 |
| `advanced/` | 6 | - |
| `tools/` | 4 | - |
| `integration/` | 3 | SKILL_MAP では 3 件、実体も 3 件で整合 |
| `writing/` | 4 | SKILL_MAP に `story` 記載が残るが実体なし |
| `design-tools/` | 5 | - |
| `automation/` | 8 | - |
| `agent-skills/` | 23 | - |
| **合計** | **104** | `SKILL_MAP.md` 記載の 106 と不一致 |

## 死蔵候補

- `skill_usage` は 0 行のため、**104/104 skill が hit 0**。ただしこれは「全件死蔵」ではなく「usage 計測が未稼働」と解釈すべき。
- V2 では `skill_usage` を実運用化するまで、死蔵判定は `hit 0` 単独ではなく `hit 0 + frontmatter 部分 + 重複高 + reference 未導線` の複合条件で行うべき。

## merge 推奨 pair top-10

- `project/ui` + `project/fe-design`
- `project/ui` + `project/fe-component`
- `project/ui` + `project/fe-style`
- `project/ui` + `project/fe-a11y`
- `project/ui` + `project/fe-test`
- `workflow/incident` + `workflow/postmortem`
- `workflow/quality-lv5` + `common/testing`
- `workflow/quality-lv5` + `workflow/verification`
- `workflow/research` + `tools/web-search`
- `automation/init-setup` + `automation/observability`

## split 推奨

- `common/visual-design`: 11855 行
- `tools/ai-coding`: 4165 行
- `integration/agent-design`: 1486 行
- `workflow/verification`: 1079 行
- `design-tools/web-system`: 1020 行
- `tools/ide-tools`: 957 行

## V2 で新規追加すべき skill

- `workflow/gate-evidence`: G0.5-G11 の証跡収集だけを扱う監査用 skill。
- `workflow/skill-governance`: catalog lint、frontmatter schema、usage 監査、alias 管理を扱う保守専用 skill。
- `workflow/transition-design`: Reverse → Forward、Scrum → Forward など工程転換時の引継ぎ基準を扱う skill。
- `common/guardrails`: prompt / tool / data boundary の横断ガードレールを一本化する skill。

## ソース

- `skills/SKILL_MAP.md`
- `skills/*/*/SKILL.md` (104 件実読/機械集計)
- `.helix/helix.db` (`skill_usage` テーブル確認)
- `docs/audit/ai-knowledge-overlap-2026-05.md`
- `docs/audit/skill-resolution-2026-05.md`
