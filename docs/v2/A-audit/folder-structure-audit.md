# FR-INV10 Folder Structure Audit

最終更新: 2026-05-14

## 概要

- 対象: `/home/tenni/ai-dev-kit-vscode` 配下の `.git/` を除く全ディレクトリ・全ファイル
- 主結論: 現状の肥大化の主因は `段2 HELIX本体` よりも **runtime (`.helix/`) の恒久化** と **生成物/キャッシュの repo 滞留** です。
- 定量結果: 総 **5,315 files / 3,017,486 lines** のうち `.helix/` が **3,859 files / 2,808,626 lines / 72.6% of files / 93.1% of lines** を占有します。
- 次点の構造課題: `cli/` の flat command 63 本、`docs/` の 30+ subdirs、`skills/` の 106+ skill 群、`hooks/tests/agents/references` の分散配置です。
- 不確実性: line 数はバイナリを除外した text 判定ベース、`段1 product` はこの repo が HELIX 本体であるため `src/public/tests` を **product-like** として便宜分類しています。

## 選択肢

| 選択肢 | メリット | デメリット | 推奨度 |
| --- | --- | --- | --- |
| A. runtime を repo に残したまま局所整理 | 今すぐ変更しやすい | 根本原因である `.helix/` 膨張を止められない | 低 |
| B. runtime / cache / generated を段階的に repo 外しし、source-of-truth を再編 | 肥大化の主因を直接削れる | hook・CI・参照パスの移行が必要 | 高 |
| C. V2 で repo 分割 (`core` / `runtime` / `skills-vendor`) まで進める | 長期的には最も整理される | Phase 1-2 だけでは完了せず PM 判断が重い | 中 |

## 推奨

推奨は **B. runtime / cache / generated を repo から段階的に外し、`hooks/tests/agents/docs/skills` の正本を一本化する** です。先に `runtime clean-up` をやらない限り、`cli/skills/docs` の整理だけでは「HELIX の方がプロジェクト本体より重い」状態は解消しません。

## ソース

- `find . -path ./\.git -prune -o -type d -print | sort`
- `find . -maxdepth 1 -mindepth 1 | sort`
- `find . -type d -name hooks|commands|agents|tests|references`
- `wc -l (text files only, Python walker with binary skip)`
- `git status --short docs/v2/A-audit`
- `rg -n "FR-INV10|folder-structure-audit|A-audit" .helix docs helix skills cli`

## Part 1: ディレクトリツリー (depth 3)

注記: 冒頭ツリーは `tree -L 3` 相当の可読化版です。全ディレクトリの完全 inventory は Part 2 の表に収録します。

```text
ai-dev-kit-vscode/
├── .claude/ (9 entries)
│   ├── agent-memory/ (1 entries)
│   │   └── code-reviewer/
│   ├── agents/ (7 entries)
│   │   ├── be-api.md
│   │   ├── be-logic.md
│   │   ├── code-reviewer.md
│   │   ├── db-schema.md
│   │   ├── devops-deploy.md
│   │   ├── qa-test.md
│   │   └── security-audit.md
│   ├── commands/ (7 entries)
│   │   ├── build.md
│   │   ├── code-simplify.md
│   │   ├── sdd-plan.md
│   │   ├── sdd-review.md
│   │   ├── ship.md
│   │   ├── spec.md
│   │   └── test.md
│   ├── hooks/ (3 entries)
│   │   ├── post-tool-use.sh
│   │   ├── pretooluse-opus-repo-block.sh
│   │   └── stop.sh
│   ├── memory/ (4 entries)
│   │   ├── constraints.md
│   │   ├── decisions.md
│   │   ├── MEMORY.md
│   │   └── rejected-approaches.md
│   ├── CLAUDE.md
│   ├── settings.json
│   ├── settings.local.json
│   └── settings.local.json.bak
├── .claude-plugin/ (2 entries)
│   ├── marketplace.json
│   └── plugin.json
├── .github/ (1 entries)
│   └── workflows/ (1 entries)
│       └── ci.yml
├── .helix/ (37 entries)
│   ├── adversarial-review/ (1 entries)
│   │   └── baseline-G2.md
│   ├── audit/ (4 entries)
│   │   ├── codex-runs/
│   │   ├── deferred-findings.yaml
│   │   ├── plan-037-w4-inventory.txt
│   │   └── plan-038-w4-duplication-report.md
│   ├── budget/ (1 entries)
│   │   └── cache/
│   ├── cache/ (11 entries)
│   │   ├── locks/
│   │   ├── plan028-w6/
│   │   ├── plan029-w12/
│   │   ├── pmo/
│   │   ├── recommendations/
│   │   ├── skill_classifier/
│   │   ├── code-catalog-rejected.log
│   │   ├── code-catalog.jsonl
│   │   ├── code-catalog.jsonl.prev
│   │   ├── skill-catalog.json
│   │   └── skill-catalog.jsonl
│   ├── cross-sprint-reviews/ (2 entries)
│   │   ├── 2026-05-08T04-41-14-826516.json
│   │   └── 2026-05-08T05-22-15-396914.json
│   ├── design-proposals/ (1 entries)
│   │   └── fe-drive-and-drift-check-expansion.md
│   ├── handover/ (1 entries)
│   │   └── archive/
│   ├── locks/ (21 entries)
│   │   ├── handover-current.lock
│   │   ├── helix-db.lock
│   │   ├── yaml-models.lock
│   │   ├── yaml-phase.lock
│   │   ├── yaml-PLAN-048.lock
│   │   ├── yaml-PLAN-049.lock
│   │   ├── yaml-PLAN-053.lock
│   │   ├── yaml-PLAN-054.lock
│   │   ├── yaml-PLAN-055.lock
│   │   ├── yaml-PLAN-056.lock
│   │   ├── yaml-PLAN-057.lock
│   │   ├── yaml-PLAN-058.lock
│   │   ├── yaml-PLAN-059.lock
│   │   ├── yaml-PLAN-060.lock
│   │   ├── yaml-PLAN-061.lock
│   │   ├── yaml-PLAN-062.lock
│   │   ├── yaml-PLAN-063.lock
│   │   ├── yaml-PLAN-064.lock
│   │   ├── yaml-PLAN-065.lock
│   │   ├── yaml-PLAN-066.lock
│   │   └── yaml-PLAN-067.lock
│   ├── mini-plans/ (1 entries)
│   │   └── MPLAN-001.yaml
│   ├── patterns/ (3 entries)
│   │   ├── pattern.yaml
│   │   ├── README.md
│   │   └── verify-tools.yaml
│   ├── plan/ (1 entries)
│   │   └── design-md-integration/
│   ├── plans/ (82 entries)
│   │   ├── PLAN-001.yaml
│   │   ├── PLAN-002.yaml
│   │   ├── PLAN-003.yaml
│   │   ├── PLAN-004.yaml
│   │   ├── PLAN-005.yaml
│   │   ├── PLAN-006.yaml
│   │   ├── PLAN-007.yaml
│   │   ├── PLAN-008.yaml
│   │   ├── PLAN-009.yaml
│   │   ├── PLAN-010.yaml
│   │   ├── PLAN-011.yaml
│   │   ├── PLAN-012.yaml
│   │   ├── PLAN-013.yaml
│   │   ├── PLAN-014.yaml
│   │   ├── PLAN-015.yaml
│   │   ├── PLAN-016.yaml
│   │   ├── PLAN-017.yaml
│   │   ├── PLAN-018.yaml
│   │   ├── PLAN-019.yaml
│   │   ├── PLAN-020.yaml
│   │   ├── PLAN-021.yaml
│   │   ├── PLAN-024.yaml
│   │   ├── PLAN-027.yaml
│   │   ├── PLAN-028.yaml
│   │   ├── PLAN-029.yaml
│   │   ├── PLAN-030.yaml
│   │   ├── PLAN-031.yaml
│   │   ├── PLAN-032.yaml
│   │   ├── PLAN-033.yaml
│   │   ├── PLAN-034.yaml
│   │   ├── PLAN-035.yaml
│   │   ├── PLAN-036.yaml
│   │   ├── PLAN-037.yaml
│   │   ├── PLAN-038.yaml
│   │   ├── PLAN-039.yaml
│   │   ├── PLAN-040.yaml
│   │   ├── PLAN-041.yaml
│   │   ├── PLAN-042.yaml
│   │   ├── PLAN-043.yaml
│   │   ├── PLAN-044.yaml
│   │   ├── PLAN-045.yaml
│   │   ├── PLAN-046.yaml
│   │   ├── PLAN-047.yaml
│   │   ├── PLAN-048.yaml
│   │   ├── PLAN-048.yaml.lock
│   │   ├── PLAN-049.yaml
│   │   ├── PLAN-049.yaml.lock
│   │   ├── PLAN-050.yaml
│   │   ├── PLAN-051.yaml
│   │   ├── PLAN-051.yaml.lock
│   │   ├── PLAN-052.yaml
│   │   ├── PLAN-052.yaml.lock
│   │   ├── PLAN-053.yaml
│   │   ├── PLAN-053.yaml.lock
│   │   ├── PLAN-054.yaml
│   │   ├── PLAN-054.yaml.lock
│   │   ├── PLAN-055.yaml
│   │   ├── PLAN-055.yaml.lock
│   │   ├── PLAN-056.yaml
│   │   ├── PLAN-056.yaml.lock
│   │   ├── PLAN-057.yaml
│   │   ├── PLAN-057.yaml.lock
│   │   ├── PLAN-058.yaml
│   │   ├── PLAN-058.yaml.lock
│   │   ├── PLAN-059.yaml
│   │   ├── PLAN-059.yaml.lock
│   │   ├── PLAN-060.yaml
│   │   ├── PLAN-060.yaml.lock
│   │   ├── PLAN-061.yaml
│   │   ├── PLAN-061.yaml.lock
│   │   ├── PLAN-062.yaml
│   │   ├── PLAN-062.yaml.lock
│   │   ├── PLAN-063.yaml
│   │   ├── PLAN-063.yaml.lock
│   │   ├── PLAN-064.yaml
│   │   ├── PLAN-064.yaml.lock
│   │   ├── PLAN-065.yaml
│   │   ├── PLAN-065.yaml.lock
│   │   ├── PLAN-066.yaml
│   │   ├── PLAN-066.yaml.lock
│   │   ├── PLAN-067.yaml
│   │   └── PLAN-067.yaml.lock
│   ├── proposals/ (3 entries)
│   │   ├── PLAN-011-sprint7.md
│   │   ├── PLAN-012-sprint1a-contracts.md
│   │   └── PLAN-013-contract-migration-debt.md
│   ├── research/ (3 entries)
│   │   ├── codex-usage-research.md
│   │   ├── fe-driven-research.md
│   │   └── helix-budget-prior-art.md
│   ├── retros/ (54 entries)
│   │   ├── 2026-04-21-G2.md
│   │   ├── 2026-04-21-G4.md
│   │   ├── 2026-04-21-helix-maturity-review-v2.md
│   │   ├── 2026-04-21-helix-maturity-review.md
│   │   ├── 2026-04-21-L8-helix-budget-autothinking.md
│   │   ├── 2026-05-03-G4-PLAN-013.md
│   │   ├── 2026-05-03-G4-PLAN-014.md
│   │   ├── 2026-05-03-G4-PLAN-015.md
│   │   ├── 2026-05-04-G4-PLAN-002.md
│   │   ├── 2026-05-04-G4-PLAN-003.md
│   │   ├── 2026-05-04-G4-PLAN-004.md
│   │   ├── 2026-05-04-G4-PLAN-005.md
│   │   ├── 2026-05-04-G4-PLAN-006.md
│   │   ├── 2026-05-04-G4-PLAN-007.md
│   │   ├── 2026-05-04-G4-PLAN-008.md
│   │   ├── 2026-05-04-G4-PLAN-009.md
│   │   ├── 2026-05-04-G4-PLAN-010.md
│   │   ├── 2026-05-04-G4-PLAN-016.md
│   │   ├── 2026-05-04-G4.md
│   │   ├── PLAN-028.md
│   │   ├── PLAN-029.md
│   │   ├── PLAN-030.md
│   │   ├── PLAN-031.md
│   │   ├── PLAN-032.md
│   │   ├── PLAN-033.md
│   │   ├── PLAN-034.md
│   │   ├── PLAN-035.md
│   │   ├── PLAN-036.md
│   │   ├── PLAN-037.md
│   │   ├── PLAN-038.md
│   │   ├── PLAN-039.md
│   │   ├── PLAN-040.md
│   │   ├── PLAN-041.md
│   │   ├── PLAN-042.md
│   │   ├── PLAN-043.md
│   │   ├── PLAN-044.md
│   │   ├── PLAN-045.md
│   │   ├── PLAN-046.md
│   │   ├── PLAN-047.md
│   │   ├── PLAN-048.md
│   │   ├── PLAN-049.md
│   │   ├── PLAN-050.md
│   │   ├── PLAN-051.md
│   │   ├── PLAN-052.md
│   │   ├── PLAN-053.md
│   │   ├── PLAN-054.md
│   │   ├── PLAN-055.md
│   │   ├── PLAN-056.md
│   │   ├── PLAN-057.md
│   │   ├── PLAN-058.md
│   │   ├── PLAN-059.md
│   │   ├── PLAN-060.md
│   │   ├── PLAN-061.md
│   │   └── PLAN-062.md
│   ├── reverse/ (2 entries)
│   │   ├── fullback/
│   │   └── upgrade/
│   ├── reviews/ (1 entries)
│   │   └── plans/
│   ├── rules/ (4 entries)
│   │   ├── common-defs.yaml
│   │   ├── deliverables.yaml
│   │   ├── naming.yaml
│   │   └── structure.yaml
│   ├── runtime/ (1 entries)
│   │   └── index.json
│   ├── scrum/ (1 entries)
│   │   └── research/
│   ├── session-summaries/ (19 entries)
│   │   ├── 2026-04-14-session.md
│   │   ├── 2026-04-15-session.md
│   │   ├── 2026-04-16-session.md
│   │   ├── 2026-04-17-session.md
│   │   ├── 2026-04-18-session.md
│   │   ├── 2026-04-19-session.md
│   │   ├── 2026-04-20-session.md
│   │   ├── 2026-04-21-session.md
│   │   ├── 2026-04-22-session.md
│   │   ├── 2026-04-23-session.md
│   │   ├── 2026-04-24-session.md
│   │   ├── 2026-04-25-session.md
│   │   ├── 2026-04-28-session.md
│   │   ├── 2026-04-29-session.md
│   │   ├── 2026-04-30-session.md
│   │   ├── 2026-05-01-session.md
│   │   ├── 2026-05-02-session.md
│   │   ├── 2026-05-03-session.md
│   │   └── 2026-05-04-session.md
│   ├── sprint/ (1 entries)
│   │   └── PLAN-013-completion.yaml
│   ├── state/ (2 entries)
│   │   ├── deliverables.json
│   │   └── deliverables.json.prev
│   ├── tmp/ (217 entries)
│   │   ├── cli-review-task.md
│   │   ├── codex-after-15908.8RnXvj
│   │   ├── codex-after-22294.ahLruw
│   │   ├── codex-after-28493.xiAmQ0
│   │   ├── codex-after-28975.xQzLzg
│   │   ├── codex-after-32168.5rqZ58
│   │   ├── codex-after-32267.r3Ujp3
│   │   ├── codex-after-32347.eXgK0b
│   │   ├── codex-after-33158.cWnlZC
│   │   ├── codex-after-36616.bZr0uc
│   │   ├── codex-after-43562.SVXDH9
│   │   ├── codex-after-44806.9CFHZ4
│   │   ├── codex-after-45073.rb203L
│   │   ├── codex-after-47396.i1KRSL
│   │   ├── codex-after-49861.VFRjTS
│   │   ├── codex-after-65685.r5zOUg
│   │   ├── codex-after-66575.HasS6k
│   │   ├── codex-after-67043.IwXfEX
│   │   ├── codex-after-73187.8CavdW
│   │   ├── codex-after-74015.GJMqzi
│   │   ├── codex-after-86595.ZIyhPH
│   │   ├── codex-after-92175.NlpuPa
│   │   ├── codex-after-93124.fKQVfb
│   │   ├── codex-after-93577.EYqRki
│   │   ├── codex-after-94242.CLvO6w
│   │   ├── codex-after-94293.elF3iE
│   │   ├── codex-after-94537.hW8mdF
│   │   ├── codex-after-94831.0h5zGn
│   │   ├── codex-after-94832.JJvNSO
│   │   ├── codex-after-94833.zD3Go5
│   │   ├── codex-after-97753.xNwgaJ
│   │   ├── codex-after-98257.2ao5Od
│   │   ├── codex-after-98885.SbIuBi
│   │   ├── codex-baseline-15908-1778355234284799805.txt
│   │   ├── codex-baseline-22294-1778513934739305206.txt
│   │   ├── codex-baseline-28493-1778413109713552173.txt
│   │   ├── codex-baseline-28975-1778514144478919908.txt
│   │   ├── codex-baseline-32267-1778514214111075783.txt
│   │   ├── codex-baseline-32347-1778418734697977602.txt
│   │   ├── codex-baseline-44806-1778418951225323341.txt
│   │   ├── codex-baseline-49861-1778512497654663432.txt
│   │   ├── codex-baseline-65685-1778362088785751025.txt
│   │   ├── codex-baseline-66575-1778362106832709197.txt
│   │   ├── codex-baseline-67043-1778362108997918258.txt
│   │   ├── codex-baseline-73187-1778358467133900481.txt
│   │   ├── codex-baseline-74015-1778358473665168803.txt
│   │   ├── codex-baseline-86595-1778375158726666744.txt
│   │   ├── codex-baseline-94831-1778353435916995680.txt
│   │   ├── codex-baseline-94832-1778353435916904021.txt
│   │   ├── codex-baseline-94833-1778353435859479443.txt
│   │   ├── codex-baseline-97753-1778353491094536423.txt
│   │   ├── codex-baseline-98257-1778353493117831745.txt
│   │   ├── codex-untracked-after-15908.AOWJW3
│   │   ├── codex-untracked-after-22294.SLHLxi
│   │   ├── codex-untracked-after-28493.AOnkpw
│   │   ├── codex-untracked-after-28975.tOjVjE
│   │   ├── codex-untracked-after-32168.h2Z1JI
│   │   ├── codex-untracked-after-32267.zBgwQB
│   │   ├── codex-untracked-after-32347.c0b8sZ
│   │   ├── codex-untracked-after-33158.YIuNLg
│   │   ├── codex-untracked-after-36616.lS3atC
│   │   ├── codex-untracked-after-43562.veZ2Qy
│   │   ├── codex-untracked-after-44806.aWMK8D
│   │   ├── codex-untracked-after-45073.aTUO7G
│   │   ├── codex-untracked-after-47396.t5Be3w
│   │   ├── codex-untracked-after-49861.L0c35X
│   │   ├── codex-untracked-after-65685.CGccXq
│   │   ├── codex-untracked-after-66575.m5oS8W
│   │   ├── codex-untracked-after-67043.iiFPVp
│   │   ├── codex-untracked-after-73187.dm9LQJ
│   │   ├── codex-untracked-after-74015.w3Etvr
│   │   ├── codex-untracked-after-86595.cdJe0B
│   │   ├── codex-untracked-after-92175.7z3VSN
│   │   ├── codex-untracked-after-93124.jOXrfb
│   │   ├── codex-untracked-after-93577.Q3zri7
│   │   ├── codex-untracked-after-94242.Uj4iHD
│   │   ├── codex-untracked-after-94293.sK8ojb
│   │   ├── codex-untracked-after-94537.L3qbmS
│   │   ├── codex-untracked-after-94831.2y7V2f
│   │   ├── codex-untracked-after-94832.HWbece
│   │   ├── codex-untracked-after-94833.6FGrAB
│   │   ├── codex-untracked-after-97753.ebnkZS
│   │   ├── codex-untracked-after-98257.tR2HUZ
│   │   ├── codex-untracked-after-98885.QHRYge
│   │   ├── docs-update-task.md
│   │   ├── enh-1-init-start-phase.md
│   │   ├── enh-2-session-start-inject.md
│   │   ├── phase-1a-task.md
│   │   ├── phase-1b-task.md
│   │   ├── phase-1c-task.md
│   │   ├── phase-2-task.md
│   │   ├── plan-024-sprint2.md
│   │   ├── plan-024-sprint3.md
│   │   ├── plan-027-sprint3.md
│   │   ├── plan-028-prompt-draft.md
│   │   ├── plan-028-w1-prompt-v2.md
│   │   ├── plan-030-draft-prompt.md
│   │   ├── plan-030-tl-3rdreview.md
│   │   ├── plan-030-tl-final.md
│   │   ├── plan-030-tl-rereview.md
│   │   ├── plan-030-tl-review-prompt.md
│   │   ├── plan-030-w1-prompt.md
│   │   ├── plan-030-w2-prompt.md
│   │   ├── plan-030-w3-prompt.md
│   │   ├── plan-030-w4-prompt.md
│   │   ├── plan-038-draft-prompt.txt
│   │   ├── plan-038-review-r1-prompt.txt
│   │   ├── plan-038-review-r2-prompt.txt
│   │   ├── plan-038-w1-prompt.txt
│   │   ├── plan-038-w23-prompt.txt
│   │   ├── plan-038-w4-prompt.txt
│   │   ├── plan-039-draft-prompt.txt
│   │   ├── plan-039-review-r1-prompt.txt
│   │   ├── plan-039-review-r2-prompt.txt
│   │   ├── plan-039-w1-prompt.txt
│   │   ├── plan-039-w23-prompt.txt
│   │   ├── plan-039-w4-prompt.txt
│   │   ├── plan-040-draft-prompt.txt
│   │   ├── plan-040-review-r1-prompt.txt
│   │   ├── plan-040-review-r2-prompt.txt
│   │   ├── plan-040-w1-prompt.txt
│   │   ├── plan-040-w23-prompt.txt
│   │   ├── plan-040-w4-prompt.txt
│   │   ├── plan-041-draft-prompt.txt
│   │   ├── plan-041-review-r1-prompt.txt
│   │   ├── plan-041-review-r2-prompt.txt
│   │   ├── plan-041-w1-prompt.txt
│   │   ├── plan-041-w23-prompt.txt
│   │   ├── plan-041-w4-prompt.txt
│   │   ├── plan024-w3a-output.log
│   │   ├── plan024-w3a-prompt.md
│   │   ├── plan024-w3b-output.log
│   │   ├── plan024-w3b-prompt.md
│   │   ├── plan024-w3c-output.log
│   │   ├── plan024-w3c-prompt.md
│   │   ├── plan024-w3d-output.log
│   │   ├── plan024-w3d-prompt.md
│   │   ├── plan028-tl-final.log
│   │   ├── plan028-tl-rereview.log
│   │   ├── plan028-tl-review.log
│   │   ├── plan028-w1-adr015-prompt.md
│   │   ├── plan028-w1-output-v2.log
│   │   ├── plan028-w1-output.log
│   │   ├── plan028-w2-config-prompt.md
│   │   ├── plan028-w2-output.log
│   │   ├── plan028-w3-cli-prompt.md
│   │   ├── plan028-w3-output.log
│   │   ├── plan028-w4-docs-prompt.md
│   │   ├── plan028-w4-output.log
│   │   ├── plan028-w5a-output-v2.log
│   │   ├── plan028-w5a-output.log
│   │   ├── plan028-w5a-prompt-v2.md
│   │   ├── plan028-w5a-prompt.md
│   │   ├── plan028-w5b-output.log
│   │   ├── plan028-w5b-prompt.md
│   │   ├── plan028-w6-output-v2.log
│   │   ├── plan028-w6-output.log
│   │   ├── plan028-w6-prompt-v2.md
│   │   ├── plan028-w6-prompt.md
│   │   ├── plan029-outline-output.log
│   │   ├── plan029-outline-prompt.md
│   │   ├── plan029-r2-output.log
│   │   ├── plan029-research-integrate-prompt.md
│   │   ├── plan029-research-output.log
│   │   ├── plan029-research-prompt.md
│   │   ├── plan029-tl-fix-output.log
│   │   ├── plan029-tl-fix-prompt.md
│   │   ├── plan029-tl-rereview.log
│   │   ├── plan029-tl-review.log
│   │   ├── plan029-w1-output.log
│   │   ├── plan029-w1-prompt.md
│   │   ├── plan029-w10-output-v2.log
│   │   ├── plan029-w10-output.log
│   │   ├── plan029-w10-prompt.md
│   │   ├── plan029-w11-output.log
│   │   ├── plan029-w11-prompt.md
│   │   ├── plan029-w12-output.log
│   │   ├── plan029-w12-prompt.md
│   │   ├── plan029-w2-output.log
│   │   ├── plan029-w2-prompt.md
│   │   ├── plan029-w3-output.log
│   │   ├── plan029-w3-prompt.md
│   │   ├── plan029-w4-output-v2.log
│   │   ├── plan029-w4-output.log
│   │   ├── plan029-w4-prompt.md
│   │   ├── plan029-w5-output.log
│   │   ├── plan029-w5-prompt.md
│   │   ├── plan029-w6-output.log
│   │   ├── plan029-w6-prompt.md
│   │   ├── plan029-w7-output.log
│   │   ├── plan029-w7-prompt.md
│   │   ├── plan029-w8-output.log
│   │   ├── plan029-w8-prompt.md
│   │   ├── plan029-w9-output-v2.log
│   │   ├── plan029-w9-output.log
│   │   ├── plan029-w9-prompt-v2.md
│   │   ├── plan029-w9-prompt.md
│   │   ├── sprint2-w2a-prompt.md
│   │   ├── sprint2-w2b-prompt.md
│   │   ├── sprint2-w2c-prompt.md
│   │   ├── sprint2-w2d-prompt.md
│   │   ├── w2a-output.log
│   │   ├── w2b-output.log
│   │   ├── w2c-output.log
│   │   ├── w2d-output.log
│   │   ├── w3a-output.log
│   │   ├── w3a-prompt.md
│   │   ├── w3b-output.log
│   │   ├── w3b-prompt.md
│   │   ├── w3c-output.log
│   │   ├── w3c-prompt.md
│   │   ├── w3d-output.log
│   │   ├── w3d-prompt.md
│   │   ├── w3e-output.log
│   │   ├── w3e-prompt.md
│   │   ├── w3f-output.log
│   │   └── w3f-prompt.md
│   ├── config.yaml
│   ├── debt-register.yaml
│   ├── doc-map.yaml
│   ├── framework.yaml
│   ├── gate-checks.yaml
│   ├── helix.db
│   ├── matrix.yaml
│   ├── matrix.yaml.lock
│   ├── phase.yaml
│   ├── phase.yaml.lock
│   ├── state-machine.yaml
│   ├── task-plan.yaml
│   └── test_v20.db
├── .pytest_cache/ (4 entries)
│   ├── v/ (1 entries)
│   │   └── cache/
│   ├── .gitignore
│   ├── CACHEDIR.TAG
│   └── README.md
├── cli/ (74 entries)
│   ├── config/ (4 entries)
│   │   ├── defaults.yaml
│   │   ├── model-fallback.yaml
│   │   ├── models.yaml
│   │   └── plan-limits.yaml
│   ├── helix-plan-cmds/ (10 entries)
│   │   ├── _shared.sh
│   │   ├── draft.sh
│   │   ├── finalize.sh
│   │   ├── import.sh
│   │   ├── lint.sh
│   │   ├── list.sh
│   │   ├── mini.sh
│   │   ├── reset.sh
│   │   ├── review.sh
│   │   └── status.sh
│   ├── lib/ (84 entries)
│   │   ├── .helix/
│   │   ├── .pytest_cache/
│   │   ├── __pycache__/
│   │   ├── builders/
│   │   ├── detectors/
│   │   ├── extractors/
│   │   ├── learning/
│   │   ├── tests/
│   │   ├── agent_policy_guard.py
│   │   ├── allowed_files_estimator.py
│   │   ├── audit_a1.py
│   │   ├── audit_hash.py
│   │   ├── audit_inventory.py
│   │   ├── audit_validator.py
│   │   ├── budget.py
│   │   ├── budget_cli.py
│   │   ├── code_catalog.py
│   │   ├── code_edges.py
│   │   ├── code_recommender.py
│   │   ├── codex_post_hook.py
│   │   ├── codex_post_validation.py
│   │   ├── codex_thinking.py
│   │   ├── command_catalog.py
│   │   ├── command_mapper.py
│   │   ├── concurrent_lock.py
│   │   ├── context_guard.py
│   │   ├── contract_registry.py
│   │   ├── defaults_loader.py
│   │   ├── deferred_findings.py
│   │   ├── deliverable_gate.py
│   │   ├── hard_guard.py
│   │   ├── handover.py
│   │   ├── helix_db.py
│   │   ├── log_report.py
│   │   ├── meta_phase.py
│   │   ├── research_tool_guard.py
│   │   ├── roles.py
│   │   ├── run_context.py
│   │   ├── skill_dispatcher.py
│   │   ├── skill_recommender.py
│   │   ├── task_os.py
│   │   └── yaml_loader.py
│   ├── libexec/ (9 entries)
│   │   ├── helix-post-tool-use
│   │   ├── helix-pre-tool-use
│   │   ├── helix-session-start
│   │   ├── helix-stop
│   │   ├── json_filter.py
│   │   ├── merge_settings.py
│   │   ├── path_guard.py
│   │   ├── phase_guard.py
│   │   └── tool_filter.py
│   ├── prompts/ (2 entries)
│   │   ├── review-findings.md
│   │   └── review-summary.md
│   ├── roles/ (20 entries)
│   │   ├── classifier.conf
│   │   ├── dba.conf
│   │   ├── devops.conf
│   │   ├── docs.conf
│   │   ├── effort-classifier.conf
│   │   ├── fe.conf
│   │   ├── impl-sonnet.conf
│   │   ├── legacy.conf
│   │   ├── perf.conf
│   │   ├── pmo-haiku.conf
│   │   ├── pmo-sonnet.conf
│   │   ├── qa.conf
│   │   ├── recommender.conf
│   │   ├── research.conf
│   │   ├── se.conf
│   │   ├── security.conf
│   │   ├── tl-advisor.conf
│   │   ├── tl.conf
│   │   ├── pg.conf
│   │   └── pm-advisor.conf
│   ├── schemas/ (5 entries)
│   │   ├── allowed-files.schema.json
│   │   ├── deliverable-matrix.schema.json
│   │   ├── gate-evidence.schema.json
│   │   ├── matrix.schema.json
│   │   └── vmodel-semantics.schema.json
│   ├── scripts/ (10 entries)
│   │   ├── batch-fix-verify-comments.sh
│   │   ├── build-code-catalog.sh
│   │   ├── build-skill-catalog.sh
│   │   ├── check-upstream-state.sh
│   │   ├── migrate-plan-docs.sh
│   │   ├── run-bats-lite.sh
│   │   ├── run-codex-review.sh
│   │   ├── seed-catalog.sh
│   │   ├── sync-skill-catalog.sh
│   │   └── test-bats-lite.sh
│   ├── setup/ (4 entries)
│   │   ├── gitignore-helix.sh
│   │   ├── gitleaks.sh
│   │   ├── inventory-discovery.sh
│   │   └── redaction-denylist.sh
│   ├── templates/ (30 entries)
│   │   ├── agents/
│   │   ├── assets/
│   │   ├── docs/
│   │   ├── hooks/
│   │   ├── patterns/
│   │   ├── plan/
│   │   ├── prompts/
│   │   ├── rules/
│   │   ├── state/
│   │   ├── teams/
│   │   ├── action-types.yaml
│   │   ├── AGENTS.md.template
│   │   ├── CLAUDE.md.template
│   │   ├── config.yaml
│   │   ├── D-AGENT-EXEC.md
│   │   ├── D-AGENT-INFRA.md
│   │   ├── D-TECH-STACK.md
│   │   ├── doc-map.yaml
│   │   ├── framework.yaml
│   │   ├── gate-checks.yaml
│   │   ├── handover-current.json.template
│   │   ├── handover-current.md.template
│   │   ├── matrix.yaml
│   │   ├── phase.yaml
│   │   ├── retro.md.template
│   │   ├── scrum-backlog.yaml
│   │   ├── scrum-handoff.md.template
│   │   ├── scrum-sprint.yaml
│   │   ├── state-machine.yaml
│   │   └── task-catalog.yaml
│   ├── tests/ (72 entries)
│   │   ├── .helix/
│   │   ├── _helix-bats-helper.bash
│   │   ├── helix-budget-migration.bats
│   │   ├── helix-budget-status.bats
│   │   ├── helix-gate-detector.bats
│   │   ├── helix-gate-pair-check.bats
│   │   ├── helix-size-drive-auto.bats
│   │   ├── README.md
│   │   ├── test-bats-lite-runner.bats
│   │   ├── test-codex-review-prompt.bats
│   │   ├── test-drift-check-dbschema.bats
│   │   ├── test-drift-check-manual.sh
│   │   ├── test-drift-check.bats
│   │   ├── test-gate-auto-enqueue-manual.sh
│   │   ├── test-handover.bats
│   │   ├── test-helix-asset.bats
│   │   ├── test-helix-audit-a0.bats
│   │   ├── test-helix-audit-preflight.bats
│   │   ├── test-helix-audit.bats
│   │   ├── test-helix-bats-cleanup.bats
│   │   ├── test-helix-claude-pmo.bats
│   │   ├── test-helix-code.bats
│   │   ├── test-helix-codex-auto-fallback.bats
│   │   ├── test-helix-codex-write-audit.bats
│   │   ├── test-helix-codex.bats
│   │   ├── test-helix-dashboard.bats
│   │   ├── test-helix-doctor-pmo.bats
│   │   ├── test-helix-entry.bats
│   │   ├── test-helix-flexibility.bats
│   │   ├── test-helix-gate-cross-sprint.bats
│   │   ├── test-helix-gate-g10-outcome.bats
│   │   ├── test-helix-gate-g9-g11.bats
│   │   ├── test-helix-gate-pre-release.bats
│   │   ├── test-helix-gate-readiness.bats
│   │   ├── test-helix-interrupt-history.bats
│   │   ├── test-helix-job.bats
│   │   ├── test-helix-lock.bats
│   │   ├── test-helix-meta-phase.bats
│   │   ├── test-helix-observe.bats
│   │   ├── test-helix-phase-deploy-3stages.bats
│   │   ├── test-helix-phase-l5b.bats
│   │   ├── test-helix-plan-finalize-frontmatter.bats
│   │   ├── test-helix-plan-lint.bats
│   │   ├── test-helix-plan-mini.bats
│   │   ├── test-helix-plan-reset.bats
│   │   ├── test-helix-plan.bats
│   │   ├── test-helix-readiness-e2e.bats
│   │   ├── test-helix-readiness.bats
│   │   ├── test-helix-research.bats
│   │   ├── test-helix-reverse-design.bats
│   │   ├── test-helix-reverse-multitype.bats
│   │   ├── test-helix-reverse-review.bats
│   │   ├── test-helix-review-internal-skip.bats
│   │   ├── test-helix-routing.bats
│   │   ├── test-helix-scheduler.bats
│   │   ├── test-helix-scrum-extended.bats
│   │   ├── test-helix-scrum-trigger.bats
│   │   ├── test-helix-scrum.bats
│   │   ├── test-helix-session-summary.bats
│   │   ├── test-helix-setup.bats
│   │   ├── test-helix-size-agent.bats
│   │   ├── test-helix-skill.bats
│   │   ├── test-helix-sprint-strict.bats
│   │   ├── test-helix-verify-agent.bats
│   │   ├── test-pretooluse-opus-repo-block.bats
│   │   ├── test-retro-auto-enqueue.bats
│   │   ├── test_codex_role_intent.bats
│   │   ├── test_drift_check_generic.bats
│   │   ├── test_helix_codex_allowed_files.bats
│   │   ├── test_helix_codex_audit.bats
│   │   ├── test_helix_codex_footer.bats
│   │   └── test_helix_gate_g5_design_md.bats
│   ├── claude
│   ├── codex
│   ├── helix
│   ├── helix-asset
│   ├── helix-audit
│   ├── helix-bats-cleanup
│   ├── helix-bench
│   ├── helix-budget
│   ├── helix-builder
│   ├── helix-check-claudemd
│   ├── helix-claude
│   ├── helix-code
│   ├── helix-codex
│   ├── helix-commands
│   ├── helix-context
│   ├── helix-dashboard
│   ├── helix-debt
│   ├── helix-debug
│   ├── helix-detect
│   ├── helix-discover
│   ├── helix-doctor
│   ├── helix-drift-check
│   ├── helix-entry
│   ├── helix-gate
│   ├── helix-gate-api-check
│   ├── helix-handover
│   ├── helix-hook
│   ├── helix-init
│   ├── helix-interrupt
│   ├── helix-job
│   ├── helix-learn
│   ├── helix-lock
│   ├── helix-log
│   ├── helix-matrix
│   ├── helix-meta-phase
│   ├── helix-migrate
│   ├── helix-mode
│   ├── helix-observe
│   ├── helix-plan
│   ├── helix-pr
│   ├── helix-promote
│   ├── helix-readiness
│   ├── helix-recipe
│   ├── helix-research
│   ├── helix-retro
│   ├── helix-reverse
│   ├── helix-review
│   ├── helix-scheduler
│   ├── helix-scrum
│   ├── helix-session-start
│   ├── helix-session-summary
│   ├── helix-setup
│   ├── helix-size
│   ├── helix-skill
│   ├── helix-sprint
│   ├── helix-status
│   ├── helix-task
│   ├── helix-team
│   ├── helix-test
│   ├── helix-test-debug
│   ├── helix-verify-agent
│   ├── helix-verify-all
│   └── ROLE_MAP.md
├── docs/ (34 entries)
│   ├── adr/ (18 entries)
│   │   ├── ADR-001-deliverable-matrix-as-source-of-truth.md
│   │   ├── ADR-002-builder-system-foundations.md
│   │   ├── ADR-003-learning-engine.md
│   │   ├── ADR-004-bash-python-hybrid.md
│   │   ├── ADR-005-yaml-sqlite-dual-state.md
│   │   ├── ADR-006-template-copy-architecture.md
│   │   ├── ADR-007-three-mode-integration.md
│   │   ├── ADR-008-builder-abstraction.md
│   │   ├── ADR-009-hook-strategy.md
│   │   ├── ADR-010-task-os.md
│   │   ├── ADR-011-test-duplication.md
│   │   ├── ADR-012-g1-gate-design.md
│   │   ├── ADR-013-r4-gate-design.md
│   │   ├── ADR-014-roles-config-format.md
│   │   ├── ADR-015-helix-v2-orchestration.md
│   │   ├── ADR-016-concurrent-lock-primitive.md
│   │   ├── ADR-template.md
│   │   └── index.md
│   ├── agent-skills/ (4 entries)
│   │   ├── getting-started.md
│   │   ├── LICENSE-upstream
│   │   ├── README.md
│   │   └── skill-anatomy.md
│   ├── architecture/ (5 entries)
│   │   ├── cli-layout.md
│   │   ├── codex-review-sandbox-limitation.md
│   │   ├── helix-flexibility-constraint.md
│   │   ├── plan-template.md
│   │   └── test-layout.md
│   ├── archive/ (2 entries)
│   │   ├── plans/
│   │   └── proposals/
│   ├── assets/ (1 entries)
│   │   └── helix-banner.png
│   ├── audit/ (4 entries)
│   │   ├── ai-knowledge-overlap-2026-05.md
│   │   ├── dead-code-candidates-2026-05.md
│   │   ├── dead-code-final-2026-05.md
│   │   └── skill-resolution-2026-05.md
│   ├── backlog/ (2 entries)
│   │   ├── feature-doc-alignment-audit.md
│   │   └── intentional-deferred.md
│   ├── commands/ (12 entries)
│   │   ├── ai-harness.md
│   │   ├── asset.md
│   │   ├── builder.md
│   │   ├── dashboard.md
│   │   ├── index.md
│   │   ├── interrupt.md
│   │   ├── learning.md
│   │   ├── matrix.md
│   │   ├── plan.md
│   │   ├── reverse.md
│   │   ├── scrum.md
│   │   └── twin.md
│   ├── design/ (17 entries)
│   │   ├── D-BUILDER-INTEGRATION.md
│   │   ├── D-DB-MIGRATION.md
│   │   ├── D-HOOK-SPEC.md
│   │   ├── D-INTERRUPT-SPEC.md
│   │   ├── D-LEARNING-REFACTOR.md
│   │   ├── D-QUALITY-SPEC.md
│   │   ├── D-RECIPE-SPEC.md
│   │   ├── D-RESILIENCE.md
│   │   ├── D-STATE-SPEC.md
│   │   ├── L2-builder-system.md
│   │   ├── L2-cli-architecture.md
│   │   ├── L2-design.md
│   │   ├── L2-learning-engine.md
│   │   ├── L3-detailed-design.md
│   │   ├── L3-schedule-wbs.md
│   │   ├── L5-visual-design.md
│   │   └── skill-catalog-jsonl.md
│   ├── features/ (23 entries)
│   │   ├── helix-budget-autothinking/
│   │   ├── helix-effort-agent-adr/
│   │   ├── PLAN-021/
│   │   ├── PLAN-048/
│   │   ├── PLAN-049/
│   │   ├── PLAN-050/
│   │   ├── PLAN-051/
│   │   ├── PLAN-052/
│   │   ├── PLAN-053/
│   │   ├── PLAN-054/
│   │   ├── PLAN-055/
│   │   ├── PLAN-056/
│   │   ├── PLAN-057/
│   │   ├── PLAN-058/
│   │   ├── PLAN-059/
│   │   ├── PLAN-060/
│   │   ├── PLAN-061/
│   │   ├── PLAN-062/
│   │   ├── PLAN-063/
│   │   ├── PLAN-064/
│   │   ├── PLAN-065/
│   │   ├── PLAN-066/
│   │   └── PLAN-067/
│   ├── log-verification/ (1 entries)
│   │   └── PLAN-013-log-verification.md
│   ├── memory/ (1 entries)
│   │   └── 2026-05-04-helix-completion-memory.md
│   ├── metrics/ (1 entries)
│   │   └── PLAN-013-metrics-dashboard.md
│   ├── plans/ (69 entries)
│   │   ├── PLAN-001-poc-skill.md
│   │   ├── PLAN-002-helix-fullauto-foundation.md
│   │   ├── PLAN-002B-helix-inventory-foundation.md
│   │   ├── PLAN-003-auto-restart-foundation.md
│   │   ├── PLAN-004-pm-reward-design.md
│   │   ├── PLAN-005-ops-automation-skills.md
│   │   ├── PLAN-006-upstream-meta-phase.md
│   │   ├── PLAN-007-scrum-multitype-trigger.md
│   │   ├── PLAN-008-reverse-multitype.md
│   │   ├── PLAN-009-run-phase-l9-l11.md
│   │   ├── PLAN-010-verification-agent.md
│   │   ├── PLAN-011-code-index-system.md
│   │   ├── PLAN-012-code-index-coverage.md
│   │   ├── PLAN-013-code-index-eligibility-taxonomy.md
│   │   ├── PLAN-014-stop-hook-idempotency.md
│   │   ├── PLAN-015-stop-hook-test-guard-hack.md
│   │   ├── PLAN-016-session-summary-helix-log-report.md
│   │   ├── PLAN-017-bats-coverage-core-cli.md
│   │   ├── PLAN-018-llm-guard-retroactive-hardening.md
│   │   ├── PLAN-019-helix-migrate-target-expansion.md
│   │   ├── PLAN-028-helix-v2-orchestration.md
│   │   ├── PLAN-029-helix-rigor-expansion.md
│   │   ├── PLAN-030-carry-consolidation.md
│   │   ├── PLAN-031-carry-resolution.md
│   │   ├── PLAN-032-helix-test-and-concurrent-resolution.md
│   │   ├── PLAN-033-drift-check-and-baseline-cleanup.md
│   │   ├── PLAN-034-codex-output-and-prompt-template.md
│   │   ├── PLAN-035-helix-review-and-bats-cleanup.md
│   │   ├── PLAN-036-codex-post-validation-and-bats-cleanup.md
│   │   ├── PLAN-037-codex-fallback-and-lint-expansion.md
│   │   ├── PLAN-038-codex-prompt-and-plan-workflow-tightening.md
│   │   ├── PLAN-039-undeployed-feature-activation.md
│   │   ├── PLAN-040-helix-plan-split-and-codex-summary-isolation.md
│   │   ├── PLAN-041-summary-marker-and-legacy-progressive.md
│   │   ├── PLAN-042-filter-design-and-legacy-and-lock-poc.md
│   │   ├── PLAN-043-consolidated-carry-resolution.md
│   │   ├── PLAN-044-phase-integrity-audit.md
│   │   ├── PLAN-045-runtime-debt-resolution.md
│   │   ├── PLAN-046-runtime-quality.md
│   │   ├── PLAN-047-ds120-integration.md
│   │   ├── PLAN-048-codex-write-default.md
│   │   ├── PLAN-049-reverse-docs-enhancement.md
│   │   ├── PLAN-050-codex-review-findings.md
│   │   ├── PLAN-051-bats-lite-and-hidden-failures.md
│   │   ├── PLAN-051-bats-lite-and-hidden-failures.md.lock
│   │   ├── PLAN-052-schema-migration-tests-fix.md
│   │   ├── PLAN-052-schema-migration-tests-fix.md.lock
│   │   ├── PLAN-053-helix-code-tests-fix.md
│   │   ├── PLAN-053-helix-code-tests-fix.md.lock
│   │   ├── PLAN-054-phase-template-l65-69-fix.md
│   │   ├── PLAN-054-phase-template-l65-69-fix.md.lock
│   │   ├── PLAN-055-plan-lint-and-misc-and-env-fix.md
│   │   ├── PLAN-055-plan-lint-and-misc-and-env-fix.md.lock
│   │   ├── PLAN-056-codex-misc-tests-fix.md
│   │   ├── PLAN-056-codex-misc-tests-fix.md.lock
│   │   ├── PLAN-057-non-codex-misc-tests-fix.md
│   │   ├── PLAN-057-non-codex-misc-tests-fix.md.lock
│   │   ├── PLAN-058-refactor-dead-code-and-impl-fix.md
│   │   ├── PLAN-058-refactor-dead-code-and-impl-fix.md.lock
│   │   ├── PLAN-059-skill-resolution-audit.md
│   │   ├── PLAN-059-skill-resolution-audit.md.lock
│   │   ├── PLAN-060-skill-ai-knowledge-overlap.md
│   │   ├── PLAN-061-dead-code-actual-removal.md
│   │   ├── PLAN-062-helix-code-db-findings.md
│   │   ├── PLAN-063-helix-db-detector-system.md
│   │   ├── PLAN-064-helix-asset-cli.md
│   │   ├── PLAN-065-qa-strictness.md
│   │   ├── PLAN-066-security-scan-systematic.md
│   │   └── PLAN-067-helix-automation-layer.md
│   ├── postmortem/ (1 entries)
│   │   └── PLAN-013-completion-postmortem.md
│   ├── proposals/ (1 entries)
│   │   └── PLAN-013-next-cycle-proposal.md
│   ├── qa/ (1 entries)
│   │   └── criteria-2026.md
│   ├── reference/ (1 entries)
│   │   └── ds120-mapping.md
│   ├── release-notes/ (1 entries)
│   │   └── PLAN-013-release-note.md
│   ├── requirements/ (1 entries)
│   │   └── L1-requirements.md
│   ├── research/ (1 entries)
│   │   └── PLAN-029-research-findings.md
│   ├── roadmap/ (1 entries)
│   │   └── 2026-05-04-completion-roadmap.md
│   ├── rollback/ (1 entries)
│   │   └── PLAN-013-rollback.md
│   ├── runbook/ (10 entries)
│   │   ├── .gitkeep
│   │   ├── bats-cleanup-routine.md
│   │   ├── codex-test-bootstrap.md
│   │   ├── helix-codex.md
│   │   ├── helix-handover.md
│   │   ├── helix-migrate.md
│   │   ├── helix-plan.md
│   │   ├── PLAN-013-runbook.md
│   │   ├── README.md
│   │   └── spark-disable-rollback.md
│   ├── security-review/ (1 entries)
│   │   └── PLAN-013-security-review.md
│   ├── slo/ (1 entries)
│   │   └── PLAN-013-slo-sli.md
│   ├── smoke/ (1 entries)
│   │   └── PLAN-013-smoke-test.md
│   ├── specs/ (1 entries)
│   │   └── D-API-helix-log-report-session.md
│   ├── sprint/ (2 entries)
│   │   ├── L4-agent-sprint-guide.md
│   │   └── L4-be-sprint-guide.md
│   ├── v2/ (3 entries)
│   │   ├── A-audit/
│   │   ├── CONCEPT.md
│   │   └── L1-REQUIREMENTS.md
│   ├── generated-assets.yaml
│   ├── quickstart.md
│   ├── security-guidelines.md
│   └── setup-guide.md
├── helix/ (5 entries)
│   ├── AGENTS.md.example
│   ├── CODEX_TL_MODE.md
│   ├── HELIX_CORE.md
│   ├── sync-codex-skills.sh
│   └── validate.sh
├── public/ (1 entries)
│   └── generated/ (1 entries)
│       └── codex/
├── scripts/ (3 entries)
│   ├── git-hooks/ (2 entries)
│   │   ├── pre-commit
│   │   └── pre-push
│   ├── install-git-hooks.sh
│   └── review-upstream-sync.sh
├── skills/ (11 entries)
│   ├── advanced/ (6 entries)
│   │   ├── ai-integration/
│   │   ├── external-api/
│   │   ├── i18n/
│   │   ├── legacy/
│   │   ├── migration/
│   │   └── tech-selection/
│   ├── agent-skills/ (25 entries)
│   │   ├── api-and-interface-design/
│   │   ├── browser-testing-with-devtools/
│   │   ├── ci-cd-and-automation/
│   │   ├── code-review-and-quality/
│   │   ├── context-engineering/
│   │   ├── debugging-and-error-recovery/
│   │   ├── deprecation-and-migration/
│   │   ├── documentation-and-adrs/
│   │   ├── frontend-ui-engineering/
│   │   ├── helix-scrum/
│   │   ├── hooks/
│   │   ├── idea-refine/
│   │   ├── incremental-implementation/
│   │   ├── mock-driven-development/
│   │   ├── performance-optimization/
│   │   ├── planning-and-task-breakdown/
│   │   ├── references/
│   │   ├── security-and-hardening/
│   │   ├── shipping-and-launch/
│   │   ├── source-driven-development/
│   │   ├── spec-driven-development/
│   │   ├── system-design-sizing/
│   │   ├── technical-writing/
│   │   ├── test-driven-development/
│   │   └── using-agent-skills/
│   ├── automation/ (8 entries)
│   │   ├── browser-script/
│   │   ├── flow-optimize/
│   │   ├── init-setup/
│   │   ├── job-queue/
│   │   ├── lock/
│   │   ├── observability/
│   │   ├── scheduler/
│   │   └── site-mapping/
│   ├── common/ (12 entries)
│   │   ├── code-review/
│   │   ├── coding/
│   │   ├── design/
│   │   ├── documentation/
│   │   ├── error-fix/
│   │   ├── git/
│   │   ├── infrastructure/
│   │   ├── performance/
│   │   ├── refactoring/
│   │   ├── security/
│   │   ├── testing/
│   │   └── visual-design/
│   ├── design-tools/ (5 entries)
│   │   ├── character/
│   │   ├── diagram/
│   │   ├── graphic/
│   │   ├── pptx/
│   │   └── web-system/
│   ├── integration/ (3 entries)
│   │   ├── agent-cost-design/
│   │   ├── agent-design/
│   │   └── agent-teams/
│   ├── project/ (8 entries)
│   │   ├── api/
│   │   ├── db/
│   │   ├── fe-a11y/
│   │   ├── fe-component/
│   │   ├── fe-design/
│   │   ├── fe-style/
│   │   ├── fe-test/
│   │   └── ui/
│   ├── tools/ (4 entries)
│   │   ├── ai-coding/
│   │   ├── ai-search/
│   │   ├── ide-tools/
│   │   └── web-search/
│   ├── workflow/ (31 entries)
│   │   ├── adversarial-review/
│   │   ├── api-contract/
│   │   ├── compliance/
│   │   ├── context-memory/
│   │   ├── debt-register/
│   │   ├── dependency-map/
│   │   ├── deploy/
│   │   ├── design-doc/
│   │   ├── dev-policy/
│   │   ├── dev-setup/
│   │   ├── estimation/
│   │   ├── gate-planning/
│   │   ├── incident/
│   │   ├── observability-sre/
│   │   ├── poc/
│   │   ├── postmortem/
│   │   ├── project-management/
│   │   ├── quality-lv5/
│   │   ├── requirements-handover/
│   │   ├── research/
│   │   ├── reverse-analysis/
│   │   ├── reverse-r0/
│   │   ├── reverse-r1/
│   │   ├── reverse-r2/
│   │   ├── reverse-r3/
│   │   ├── reverse-r4/
│   │   ├── reverse-rgc/
│   │   ├── runbook/
│   │   ├── schedule-wbs/
│   │   ├── threat-model/
│   │   └── verification/
│   ├── writing/ (4 entries)
│   │   ├── explain/
│   │   ├── japanese/
│   │   ├── presentation/
│   │   └── social/
│   └── SKILL_MAP.md
├── src/ (1 entries)
│   └── features/ (1 entries)
│       └── helix-budget-autothinking/
├── tests/ (3 entries)
│   ├── __pycache__/ (1 entries)
│   │   └── test_code_catalog.cpython-312-pytest-9.0.3.pyc
│   ├── integration/ (2 entries)
│   │   ├── test_plan023.sh
│   │   └── test_skill_autofire.sh
│   └── test_code_catalog.py
├── verify/ (32 entries)
│   ├── 001-helix-init.sh
│   ├── 002-helix-size.sh
│   ├── 003-helix-sprint.sh
│   ├── 004-helix-gate.sh
│   ├── 005-freeze-break.sh
│   ├── 006-api-contract.sh
│   ├── 007-adr-index.sh
│   ├── 008-yaml-parser.sh
│   ├── 009-helix-scrum.sh
│   ├── 010-helix-reverse.sh
│   ├── h101-forward-full-flow.sh
│   ├── h102-freeze-break-recovery.sh
│   ├── h103-scrum-to-forward-handoff.sh
│   ├── h104-multi-sprint-accumulation.sh
│   ├── h105-unified-status-display.sh
│   ├── h201-codex-role-dispatch.sh
│   ├── h202-pr-generation.sh
│   ├── h203-claudemd-enforcement.sh
│   ├── h204-session-context-injection.sh
│   ├── h205-gate-cascade-integrity.sh
│   ├── h206-concurrent-mode-safety.sh
│   ├── h301-codex-skill-file-validation.sh
│   ├── h302-gate-static-all-patterns.sh
│   ├── h303-sprint-edge-cases.sh
│   ├── h304-hook-all-triggers.sh
│   ├── h305-init-framework-variants.sh
│   ├── h306-size-all-type-patterns.sh
│   ├── h307-reverse-full-prereq-chain.sh
│   ├── h308-scrum-rejected-and-pivot.sh
│   ├── h309-graceful-yaml-failure.sh
│   ├── h310-no-helix-dir-noop.sh
│   └── h401-full-flow-integration.sh
├── .codex
├── .gitignore
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── requirements-dev.txt
└── setup.sh
```

## Part 2: 全ディレクトリ計測

- 走査ディレクトリ数: **457**
- 走査ファイル数: **5,315**

| path | role | direct file 数 | 再帰 file 数 | 再帰 行数 | 最大 depth | 最長 path char 数 | layer |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `.` | リポジトリ全体のルート | 7 | 5,315 | 3,017,646 | 6 | 103 | 段2(HELIX本体) |
| `.claude` | Claude Code 向け設定とhook | 4 | 27 | 2,167 | 2 | 45 | 段2(HELIX本体) |
| `.claude-plugin` | .claude-plugin 配下の関連資産 | 2 | 2 | 34 | 0 | 30 | 段2(HELIX本体) |
| `.claude/agent-memory` | agent-memory 配下の関連資産 | 0 | 2 | 25 | 1 | 46 | 段2(HELIX本体) |
| `.claude/agent-memory/code-reviewer` | code-reviewer 配下の関連資産 | 2 | 2 | 25 | 0 | 46 | 段2(HELIX本体) |
| `.claude/agents` | agent定義群 | 7 | 7 | 545 | 0 | 31 | 段2(HELIX本体) |
| `.claude/commands` | コマンド文書またはslash command群 | 7 | 7 | 219 | 0 | 29 | 段2(HELIX本体) |
| `.claude/hooks` | hook群 | 3 | 3 | 205 | 0 | 42 | 段2(HELIX本体) |
| `.claude/memory` | memory 配下の関連資産 | 4 | 4 | 43 | 0 | 35 | 段2(HELIX本体) |
| `.github` | GitHub CI/テンプレート | 0 | 1 | 79 | 1 | 24 | 段2(HELIX本体) |
| `.github/workflows` | workflows 配下の関連資産 | 1 | 1 | 79 | 0 | 24 | 段2(HELIX本体) |
| `.helix` | 実行時状態・監査・handover | 13 | 3,859 | 2,807,786 | 3 | 103 | runtime(.helix) |
| `.helix/adversarial-review` | adversarial-review 配下の関連資産 | 1 | 1 | 12 | 0 | 43 | runtime(.helix) |
| `.helix/audit` | audit 配下の関連資産 | 3 | 2,999 | 2,141,563 | 1 | 97 | runtime(.helix) |
| `.helix/audit/codex-runs` | codex-runs 配下の関連資産 | 2,996 | 2,996 | 2,140,108 | 0 | 97 | runtime(.helix) |
| `.helix/budget` | budget 配下の関連資産 | 0 | 3 | 21 | 2 | 47 | runtime(.helix) |
| `.helix/budget/cache` | cache 配下の関連資産 | 0 | 3 | 21 | 1 | 47 | runtime(.helix) |
| `.helix/budget/cache/classify` | classify 配下の関連資産 | 3 | 3 | 21 | 0 | 47 | runtime(.helix) |
| `.helix/cache` | cache 配下の関連資産 | 5 | 366 | 10,797 | 2 | 103 | runtime(.helix) |
| `.helix/cache/locks` | locks 配下の関連資産 | 1 | 1 | 1 | 0 | 30 | runtime(.helix) |
| `.helix/cache/plan028-w6` | plan028-w6 配下の関連資産 | 1 | 1 | 3 | 0 | 43 | runtime(.helix) |
| `.helix/cache/plan029-w12` | plan029-w12 配下の関連資産 | 1 | 1 | 3 | 0 | 44 | runtime(.helix) |
| `.helix/cache/pmo` | pmo 配下の関連資産 | 2 | 2 | 74 | 0 | 44 | runtime(.helix) |
| `.helix/cache/recommendations` | recommendations 配下の関連資産 | 1 | 2 | 62 | 1 | 103 | runtime(.helix) |
| `.helix/cache/recommendations/code` | code 配下の関連資産 | 1 | 1 | 27 | 0 | 103 | runtime(.helix) |
| `.helix/cache/skill_classifier` | skill_classifier 配下の関連資産 | 333 | 333 | 5,661 | 0 | 99 | runtime(.helix) |
| `.helix/cross-sprint-reviews` | cross-sprint-reviews 配下の関連資産 | 2 | 2 | 9 | 0 | 54 | runtime(.helix) |
| `.helix/design-proposals` | design-proposals 配下の関連資産 | 1 | 1 | 77 | 0 | 52 | runtime(.helix) |
| `.helix/handover` | handover 配下の関連資産 | 0 | 3 | 70 | 1 | 40 | runtime(.helix) |
| `.helix/handover/archive` | archive 配下の関連資産 | 3 | 3 | 70 | 0 | 40 | runtime(.helix) |
| `.helix/locks` | locks 配下の関連資産 | 21 | 21 | 21 | 0 | 34 | runtime(.helix) |
| `.helix/mini-plans` | mini-plans 配下の関連資産 | 1 | 1 | 6 | 0 | 31 | runtime(.helix) |
| `.helix/patterns` | patterns 配下の関連資産 | 3 | 3 | 157 | 0 | 35 | runtime(.helix) |
| `.helix/plan` | plan 配下の関連資産 | 0 | 3 | 251 | 2 | 65 | runtime(.helix) |
| `.helix/plan/design-md-integration` | design-md-integration 配下の関連資産 | 1 | 3 | 251 | 1 | 65 | runtime(.helix) |
| `.helix/plan/design-md-integration/review` | review 配下の関連資産 | 2 | 2 | 214 | 0 | 65 | runtime(.helix) |
| `.helix/plans` | plans 配下の関連資産 | 82 | 82 | 633 | 0 | 31 | runtime(.helix) |
| `.helix/proposals` | proposals 配下の関連資産 | 3 | 3 | 96 | 0 | 48 | runtime(.helix) |
| `.helix/research` | research 配下の関連資産 | 3 | 3 | 782 | 0 | 40 | runtime(.helix) |
| `.helix/retros` | retros 配下の関連資産 | 54 | 54 | 6,207 | 0 | 50 | runtime(.helix) |
| `.helix/reverse` | reverse 配下の関連資産 | 0 | 2 | 38 | 1 | 34 | runtime(.helix) |
| `.helix/reverse/fullback` | fullback 配下の関連資産 | 1 | 1 | 1 | 0 | 34 | runtime(.helix) |
| `.helix/reverse/upgrade` | upgrade 配下の関連資産 | 1 | 1 | 37 | 0 | 31 | runtime(.helix) |
| `.helix/reviews` | reviews 配下の関連資産 | 0 | 2 | 104 | 2 | 34 | runtime(.helix) |
| `.helix/reviews/plans` | plans 配下の関連資産 | 0 | 2 | 104 | 1 | 34 | runtime(.helix) |
| `.helix/reviews/plans/PLAN-011` | PLAN-011 配下の関連資産 | 2 | 2 | 104 | 0 | 34 | runtime(.helix) |
| `.helix/rules` | rules 配下の関連資産 | 4 | 4 | 118 | 0 | 36 | runtime(.helix) |
| `.helix/runtime` | runtime 配下の関連資産 | 1 | 1 | 90 | 0 | 27 | runtime(.helix) |
| `.helix/scrum` | scrum 配下の関連資産 | 0 | 2 | 23 | 2 | 37 | runtime(.helix) |
| `.helix/scrum/research` | research 配下の関連資産 | 0 | 2 | 23 | 1 | 37 | runtime(.helix) |
| `.helix/scrum/research/PLAN-029` | PLAN-029 配下の関連資産 | 2 | 2 | 23 | 0 | 37 | runtime(.helix) |
| `.helix/session-summaries` | session-summaries 配下の関連資産 | 19 | 19 | 61 | 0 | 44 | runtime(.helix) |
| `.helix/sprint` | sprint 配下の関連資産 | 1 | 1 | 12 | 0 | 35 | runtime(.helix) |
| `.helix/state` | state 配下の関連資産 | 2 | 2 | 353 | 0 | 33 | runtime(.helix) |
| `.helix/tmp` | tmp 配下の関連資産 | 217 | 217 | 635,332 | 0 | 55 | runtime(.helix) |
| `.pytest_cache` | .pytest_cache 配下の関連資産 | 3 | 5 | 1,183 | 2 | 34 | 段2(HELIX本体) |
| `.pytest_cache/v` | v 配下の関連資産 | 0 | 2 | 1,126 | 1 | 34 | 段2(HELIX本体) |
| `.pytest_cache/v/cache` | cache 配下の関連資産 | 2 | 2 | 1,126 | 0 | 34 | 段2(HELIX本体) |
| `cli` | HELIX CLI本体と補助ライブラリ | 63 | 802 | 108,027 | 5 | 88 | 段2(HELIX本体) |
| `cli/config` | CLI設定 | 4 | 4 | 104 | 0 | 38 | 段2(HELIX本体) |
| `cli/helix-plan-cmds` | helix-plan-cmds 配下の関連資産 | 10 | 10 | 1,212 | 0 | 37 | 段2(HELIX本体) |
| `cli/lib` | CLIライブラリ | 76 | 533 | 65,403 | 4 | 88 | 段2(HELIX本体) |
| `cli/lib/.helix` | .helix 配下の関連資産 | 0 | 1 | 1 | 1 | 34 | 段2(HELIX本体) |
| `cli/lib/.helix/cache` | cache 配下の関連資産 | 1 | 1 | 1 | 0 | 34 | 段2(HELIX本体) |
| `cli/lib/.pytest_cache` | .pytest_cache 配下の関連資産 | 3 | 4 | 15 | 2 | 34 | 段2(HELIX本体) |
| `cli/lib/.pytest_cache/v` | v 配下の関連資産 | 0 | 1 | 2 | 1 | 34 | 段2(HELIX本体) |
| `cli/lib/.pytest_cache/v/cache` | cache 配下の関連資産 | 1 | 1 | 2 | 0 | 34 | 段2(HELIX本体) |
| `cli/lib/__pycache__` | __pycache__ 配下の関連資産 | 75 | 75 | 0 | 0 | 59 | 段2(HELIX本体) |
| `cli/lib/builders` | builders 配下の関連資産 | 14 | 28 | 2,648 | 1 | 44 | 段2(HELIX本体) |
| `cli/lib/builders/__pycache__` | __pycache__ 配下の関連資産 | 14 | 14 | 0 | 0 | 58 | 段2(HELIX本体) |
| `cli/lib/detectors` | detectors 配下の関連資産 | 17 | 34 | 4,876 | 1 | 49 | 段2(HELIX本体) |
| `cli/lib/detectors/__pycache__` | __pycache__ 配下の関連資産 | 17 | 17 | 0 | 0 | 58 | 段2(HELIX本体) |
| `cli/lib/extractors` | extractors 配下の関連資産 | 2 | 4 | 302 | 1 | 46 | 段2(HELIX本体) |
| `cli/lib/extractors/__pycache__` | __pycache__ 配下の関連資産 | 2 | 2 | 0 | 0 | 59 | 段2(HELIX本体) |
| `cli/lib/learning` | learning 配下の関連資産 | 4 | 8 | 148 | 1 | 48 | 段2(HELIX本体) |
| `cli/lib/learning/__pycache__` | __pycache__ 配下の関連資産 | 4 | 4 | 0 | 0 | 58 | 段2(HELIX本体) |
| `cli/lib/tests` | テスト | 121 | 303 | 24,837 | 3 | 88 | 段2(HELIX本体) |
| `cli/lib/tests/__pycache__` | __pycache__ 配下の関連資産 | 177 | 177 | 0 | 0 | 88 | 段2(HELIX本体) |
| `cli/lib/tests/data` | data 配下の関連資産 | 0 | 5 | 681 | 3 | 73 | 段2(HELIX本体) |
| `cli/lib/tests/data/features` | features 配下の関連資産 | 0 | 5 | 681 | 2 | 73 | 段2(HELIX本体) |
| `cli/lib/tests/data/features/plan018` | plan018 配下の関連資産 | 0 | 5 | 681 | 1 | 73 | 段2(HELIX本体) |
| `cli/lib/tests/data/features/plan018/D-API` | D-API 配下の関連資産 | 5 | 5 | 681 | 0 | 73 | 段2(HELIX本体) |
| `cli/libexec` | libexec 配下の関連資産 | 9 | 9 | 1,186 | 0 | 36 | 段2(HELIX本体) |
| `cli/prompts` | prompts 配下の関連資産 | 2 | 2 | 129 | 0 | 29 | 段2(HELIX本体) |
| `cli/roles` | ロール設定 | 20 | 20 | 259 | 0 | 31 | 段2(HELIX本体) |
| `cli/schemas` | schemas 配下の関連資産 | 5 | 5 | 372 | 0 | 46 | 段2(HELIX本体) |
| `cli/scripts` | scripts 配下の関連資産 | 10 | 10 | 569 | 0 | 38 | 段2(HELIX本体) |
| `cli/setup` | setup 配下の関連資産 | 4 | 4 | 296 | 0 | 35 | 段2(HELIX本体) |
| `cli/templates` | 配布テンプレート群 | 20 | 67 | 6,941 | 1 | 47 | 配布(install) |
| `cli/templates/agents` | agent定義群 | 4 | 4 | 118 | 0 | 34 | 配布(install) |
| `cli/templates/assets` | assets 配下の関連資産 | 0 | 2 | 0 | 1 | 42 | 配布(install) |
| `cli/templates/assets/claude` | claude 配下の関連資産 | 2 | 2 | 0 | 0 | 42 | 配布(install) |
| `cli/templates/docs` | docs 配下の関連資産 | 4 | 4 | 578 | 0 | 47 | 配布(install) |
| `cli/templates/hooks` | hook群 | 3 | 3 | 118 | 0 | 33 | 配布(install) |
| `cli/templates/patterns` | patterns 配下の関連資産 | 0 | 2 | 86 | 1 | 42 | 配布(install) |
| `cli/templates/patterns/mini-plan` | mini-plan 配下の関連資産 | 2 | 2 | 86 | 0 | 42 | 配布(install) |
| `cli/templates/plan` | plan 配下の関連資産 | 0 | 3 | 1,162 | 1 | 42 | 配布(install) |
| `cli/templates/plan/design-md-integration` | design-md-integration 配下の関連資産 | 3 | 3 | 1,162 | 0 | 42 | 配布(install) |
| `cli/templates/prompts` | prompts 配下の関連資産 | 1 | 1 | 58 | 0 | 37 | 配布(install) |
| `cli/templates/rules` | rules 配下の関連資産 | 4 | 4 | 118 | 0 | 36 | 配布(install) |
| `cli/templates/state` | state 配下の関連資産 | 0 | 2 | 94 | 1 | 39 | 配布(install) |
| `cli/templates/state/retro` | retro 配下の関連資産 | 2 | 2 | 94 | 0 | 39 | 配布(install) |
| `cli/templates/teams` | teams 配下の関連資産 | 2 | 2 | 179 | 0 | 39 | 配布(install) |
| `cli/tests` | テスト | 71 | 75 | 9,304 | 4 | 76 | 段2(HELIX本体) |
| `cli/tests/.helix` | .helix 配下の関連資産 | 0 | 4 | 79 | 3 | 76 | 段2(HELIX本体) |
| `cli/tests/.helix/budget` | budget 配下の関連資産 | 0 | 4 | 79 | 2 | 76 | 段2(HELIX本体) |
| `cli/tests/.helix/budget/cache` | cache 配下の関連資産 | 0 | 4 | 79 | 1 | 76 | 段2(HELIX本体) |
| `cli/tests/.helix/budget/cache/classify` | classify 配下の関連資産 | 4 | 4 | 79 | 0 | 76 | 段2(HELIX本体) |
| `docs` | 仕様・計画・監査ドキュメント | 4 | 316 | 35,543 | 3 | 71 | 段2(HELIX本体) |
| `docs/adr` | adr 配下の関連資産 | 18 | 18 | 1,973 | 0 | 56 | 段2(HELIX本体) |
| `docs/agent-skills` | agent-skills 配下の関連資産 | 4 | 4 | 650 | 0 | 37 | 段2(HELIX本体) |
| `docs/architecture` | architecture 配下の関連資産 | 5 | 5 | 537 | 0 | 48 | 段2(HELIX本体) |
| `docs/archive` | archive 配下の関連資産 | 0 | 4 | 1,067 | 1 | 67 | 段2(HELIX本体) |
| `docs/archive/plans` | plans 配下の関連資産 | 2 | 2 | 1,024 | 0 | 67 | 段2(HELIX本体) |
| `docs/archive/proposals` | proposals 配下の関連資産 | 2 | 2 | 43 | 0 | 63 | 段2(HELIX本体) |
| `docs/assets` | assets 配下の関連資産 | 1 | 1 | 0 | 0 | 27 | 段2(HELIX本体) |
| `docs/audit` | audit 配下の関連資産 | 4 | 4 | 477 | 0 | 44 | 段2(HELIX本体) |
| `docs/backlog` | backlog 配下の関連資産 | 2 | 2 | 190 | 0 | 48 | 段2(HELIX本体) |
| `docs/commands` | コマンド文書またはslash command群 | 12 | 12 | 1,096 | 0 | 28 | 段2(HELIX本体) |
| `docs/design` | design 配下の関連資産 | 17 | 17 | 3,969 | 0 | 43 | 段2(HELIX本体) |
| `docs/features` | features 配下の関連資産 | 0 | 138 | 4,847 | 2 | 71 | 段2(HELIX本体) |
| `docs/features/PLAN-021` | PLAN-021 配下の関連資産 | 3 | 3 | 190 | 0 | 41 | 段2(HELIX本体) |
| `docs/features/PLAN-048` | PLAN-048 配下の関連資産 | 4 | 4 | 370 | 0 | 38 | 段2(HELIX本体) |
| `docs/features/PLAN-049` | PLAN-049 配下の関連資産 | 4 | 4 | 630 | 0 | 46 | 段2(HELIX本体) |
| `docs/features/PLAN-050` | PLAN-050 配下の関連資産 | 2 | 2 | 21 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-051` | PLAN-051 配下の関連資産 | 4 | 4 | 163 | 0 | 49 | 段2(HELIX本体) |
| `docs/features/PLAN-052` | PLAN-052 配下の関連資産 | 4 | 4 | 369 | 0 | 48 | 段2(HELIX本体) |
| `docs/features/PLAN-053` | PLAN-053 配下の関連資産 | 3 | 3 | 100 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-054` | PLAN-054 配下の関連資産 | 3 | 3 | 85 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-055` | PLAN-055 配下の関連資産 | 3 | 3 | 93 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-056` | PLAN-056 配下の関連資産 | 3 | 3 | 80 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-057` | PLAN-057 配下の関連資産 | 3 | 3 | 80 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-058` | PLAN-058 配下の関連資産 | 3 | 3 | 89 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-059` | PLAN-059 配下の関連資産 | 4 | 4 | 110 | 0 | 59 | 段2(HELIX本体) |
| `docs/features/PLAN-060` | PLAN-060 配下の関連資産 | 4 | 4 | 78 | 0 | 61 | 段2(HELIX本体) |
| `docs/features/PLAN-061` | PLAN-061 配下の関連資産 | 3 | 3 | 85 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-062` | PLAN-062 配下の関連資産 | 3 | 3 | 99 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-063` | PLAN-063 配下の関連資産 | 6 | 6 | 807 | 0 | 58 | 段2(HELIX本体) |
| `docs/features/PLAN-064` | PLAN-064 配下の関連資産 | 4 | 4 | 242 | 0 | 50 | 段2(HELIX本体) |
| `docs/features/PLAN-065` | PLAN-065 配下の関連資産 | 7 | 7 | 877 | 0 | 64 | 段2(HELIX本体) |
| `docs/features/PLAN-066` | PLAN-066 配下の関連資産 | 7 | 7 | 221 | 0 | 58 | 段2(HELIX本体) |
| `docs/features/PLAN-067` | PLAN-067 配下の関連資産 | 8 | 8 | 601 | 0 | 60 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking` | helix-budget-autothinking 配下の関連資産 | 0 | 57 | 560 | 2 | 71 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-API` | D-API 配下の関連資産 | 1 | 1 | 27 | 0 | 62 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-ARCH` | D-ARCH 配下の関連資産 | 7 | 7 | 110 | 0 | 58 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-CONTRACT` | D-CONTRACT 配下の関連資産 | 4 | 4 | 56 | 0 | 70 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-DB` | D-DB 配下の関連資産 | 5 | 5 | 35 | 0 | 58 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-IMPL` | D-IMPL 配下の関連資産 | 5 | 5 | 79 | 0 | 61 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-MIG` | D-MIG 配下の関連資産 | 1 | 1 | 34 | 0 | 62 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-PLAN` | D-PLAN 配下の関連資産 | 4 | 4 | 40 | 0 | 62 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-RESEARCH` | D-RESEARCH 配下の関連資産 | 6 | 6 | 62 | 0 | 63 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-SECV` | D-SECV 配下の関連資産 | 6 | 6 | 57 | 0 | 71 | 段2(HELIX本体) |
| `docs/features/helix-budget-autothinking/D-TEST` | D-TEST 配下の関連資産 | 7 | 7 | 60 | 0 | 62 | 段2(HELIX本体) |
| `docs/features/helix-effort-agent-adr` | helix-effort-agent-adr 配下の関連資産 | 2 | 2 | 80 | 0 | 55 | 段2(HELIX本体) |
| `docs/log-verification` | log-verification 配下の関連資産 | 1 | 1 | 15 | 0 | 40 | 段2(HELIX本体) |
| `docs/memory` | memory 配下の関連資産 | 1 | 1 | 116 | 0 | 46 | 段2(HELIX本体) |
| `docs/metrics` | metrics 配下の関連資産 | 1 | 1 | 18 | 0 | 38 | 段2(HELIX本体) |
| `docs/plans` | plans 配下の関連資産 | 69 | 69 | 15,934 | 0 | 67 | 段2(HELIX本体) |
| `docs/postmortem` | postmortem 配下の関連資産 | 1 | 1 | 91 | 0 | 47 | 段2(HELIX本体) |
| `docs/proposals` | proposals 配下の関連資産 | 1 | 1 | 43 | 0 | 49 | 段2(HELIX本体) |
| `docs/qa` | qa 配下の関連資産 | 1 | 1 | 451 | 0 | 28 | 段2(HELIX本体) |
| `docs/reference` | reference 配下の関連資産 | 1 | 1 | 73 | 0 | 33 | 段2(HELIX本体) |
| `docs/release-notes` | release-notes 配下の関連資産 | 1 | 1 | 21 | 0 | 43 | 段2(HELIX本体) |
| `docs/requirements` | requirements 配下の関連資産 | 1 | 1 | 731 | 0 | 38 | 段2(HELIX本体) |
| `docs/research` | research 配下の関連資産 | 1 | 1 | 133 | 0 | 45 | 段2(HELIX本体) |
| `docs/roadmap` | roadmap 配下の関連資産 | 1 | 1 | 306 | 0 | 44 | 段2(HELIX本体) |
| `docs/rollback` | rollback 配下の関連資産 | 1 | 1 | 18 | 0 | 35 | 段2(HELIX本体) |
| `docs/runbook` | runbook 配下の関連資産 | 10 | 10 | 1,249 | 0 | 37 | 段2(HELIX本体) |
| `docs/security-review` | security-review 配下の関連資産 | 1 | 1 | 52 | 0 | 46 | 段2(HELIX本体) |
| `docs/slo` | slo 配下の関連資産 | 1 | 1 | 70 | 0 | 29 | 段2(HELIX本体) |
| `docs/smoke` | smoke 配下の関連資産 | 1 | 1 | 83 | 0 | 36 | 段2(HELIX本体) |
| `docs/specs` | specs 配下の関連資産 | 1 | 1 | 38 | 0 | 42 | 段2(HELIX本体) |
| `docs/sprint` | sprint 配下の関連資産 | 2 | 2 | 104 | 0 | 38 | 段2(HELIX本体) |
| `docs/v2` | v2 配下の関連資産 | 3 | 11 | 1,267 | 1 | 45 | 段2(HELIX本体) |
| `docs/v2/A-audit` | A-audit 配下の関連資産 | 8 | 8 | 853 | 0 | 43 | 段2(HELIX本体) |
| `helix` | コア運用方針と補助スクリプト | 5 | 5 | 795 | 0 | 31 | 段2(HELIX本体) |
| `public` | public 配下の関連資産 | 0 | 1 | 1 | 2 | 22 | 段2(HELIX本体) |
| `public/generated` | generated 配下の関連資産 | 0 | 1 | 1 | 1 | 22 | 段2(HELIX本体) |
| `public/generated/codex` | codex 配下の関連資産 | 1 | 1 | 1 | 0 | 22 | 段2(HELIX本体) |
| `scripts` | 運用補助スクリプト | 2 | 4 | 430 | 1 | 29 | 段2(HELIX本体) |
| `scripts/git-hooks` | git-hooks 配下の関連資産 | 2 | 2 | 260 | 0 | 32 | 段2(HELIX本体) |
| `skills` | HELIXスキル本体と参照資料 | 1 | 247 | 58,466 | 4 | 76 | 段2(HELIX本体) |
| `skills/advanced` | 高度スキル群 | 0 | 13 | 3,789 | 2 | 76 | 段2(HELIX本体) |
| `skills/advanced/ai-integration` | ai-integration 配下の関連資産 | 1 | 2 | 868 | 1 | 76 | 段2(HELIX本体) |
| `skills/advanced/ai-integration/references` | 参照資料群 | 1 | 1 | 567 | 0 | 76 | 段2(HELIX本体) |
| `skills/advanced/external-api` | external-api 配下の関連資産 | 1 | 2 | 610 | 1 | 67 | 段2(HELIX本体) |
| `skills/advanced/external-api/references` | 参照資料群 | 1 | 1 | 388 | 0 | 67 | 段2(HELIX本体) |
| `skills/advanced/i18n` | i18n 配下の関連資産 | 1 | 2 | 527 | 1 | 55 | 段2(HELIX本体) |
| `skills/advanced/i18n/references` | 参照資料群 | 1 | 1 | 344 | 0 | 55 | 段2(HELIX本体) |
| `skills/advanced/legacy` | legacy 配下の関連資産 | 1 | 1 | 495 | 0 | 32 | 段2(HELIX本体) |
| `skills/advanced/migration` | migration 配下の関連資産 | 1 | 1 | 483 | 0 | 35 | 段2(HELIX本体) |
| `skills/advanced/tech-selection` | tech-selection 配下の関連資産 | 1 | 5 | 806 | 1 | 74 | 段2(HELIX本体) |
| `skills/advanced/tech-selection/references` | 参照資料群 | 4 | 4 | 562 | 0 | 74 | 段2(HELIX本体) |
| `skills/agent-skills` | agent-skills 配下の関連資産 | 0 | 42 | 9,606 | 2 | 58 | 段2(HELIX本体) |
| `skills/agent-skills/api-and-interface-design` | api-and-interface-design 配下の関連資産 | 1 | 1 | 299 | 0 | 51 | 段2(HELIX本体) |
| `skills/agent-skills/browser-testing-with-devtools` | browser-testing-with-devtools 配下の関連資産 | 1 | 1 | 320 | 0 | 58 | 段2(HELIX本体) |
| `skills/agent-skills/ci-cd-and-automation` | ci-cd-and-automation 配下の関連資産 | 1 | 1 | 395 | 0 | 46 | 段2(HELIX本体) |
| `skills/agent-skills/code-review-and-quality` | code-review-and-quality 配下の関連資産 | 1 | 1 | 213 | 0 | 47 | 段2(HELIX本体) |
| `skills/agent-skills/context-engineering` | context-engineering 配下の関連資産 | 1 | 1 | 194 | 0 | 43 | 段2(HELIX本体) |
| `skills/agent-skills/debugging-and-error-recovery` | debugging-and-error-recovery 配下の関連資産 | 1 | 1 | 356 | 0 | 52 | 段2(HELIX本体) |
| `skills/agent-skills/deprecation-and-migration` | deprecation-and-migration 配下の関連資産 | 1 | 1 | 352 | 0 | 50 | 段2(HELIX本体) |
| `skills/agent-skills/documentation-and-adrs` | documentation-and-adrs 配下の関連資産 | 1 | 1 | 385 | 0 | 48 | 段2(HELIX本体) |
| `skills/agent-skills/frontend-ui-engineering` | frontend-ui-engineering 配下の関連資産 | 1 | 1 | 289 | 0 | 47 | 段2(HELIX本体) |
| `skills/agent-skills/helix-scrum` | helix-scrum 配下の関連資産 | 1 | 1 | 403 | 0 | 37 | 段2(HELIX本体) |
| `skills/agent-skills/hooks` | hook群 | 1 | 2 | 408 | 1 | 49 | 段2(HELIX本体) |
| `skills/agent-skills/hooks/references` | 参照資料群 | 1 | 1 | 129 | 0 | 49 | 段2(HELIX本体) |
| `skills/agent-skills/idea-refine` | idea-refine 配下の関連資産 | 1 | 1 | 310 | 0 | 37 | 段2(HELIX本体) |
| `skills/agent-skills/incremental-implementation` | incremental-implementation 配下の関連資産 | 1 | 1 | 194 | 0 | 54 | 段2(HELIX本体) |
| `skills/agent-skills/mock-driven-development` | mock-driven-development 配下の関連資産 | 1 | 1 | 273 | 0 | 49 | 段2(HELIX本体) |
| `skills/agent-skills/performance-optimization` | performance-optimization 配下の関連資産 | 1 | 1 | 311 | 0 | 48 | 段2(HELIX本体) |
| `skills/agent-skills/planning-and-task-breakdown` | planning-and-task-breakdown 配下の関連資産 | 1 | 1 | 288 | 0 | 49 | 段2(HELIX本体) |
| `skills/agent-skills/references` | 参照資料群 | 1 | 6 | 474 | 1 | 49 | 段2(HELIX本体) |
| `skills/agent-skills/references/checklists` | checklists 配下の関連資産 | 5 | 5 | 410 | 0 | 49 | 段2(HELIX本体) |
| `skills/agent-skills/security-and-hardening` | security-and-hardening 配下の関連資産 | 1 | 1 | 339 | 0 | 46 | 段2(HELIX本体) |
| `skills/agent-skills/shipping-and-launch` | shipping-and-launch 配下の関連資産 | 1 | 1 | 392 | 0 | 43 | 段2(HELIX本体) |
| `skills/agent-skills/source-driven-development` | source-driven-development 配下の関連資産 | 1 | 1 | 207 | 0 | 48 | 段2(HELIX本体) |
| `skills/agent-skills/spec-driven-development` | spec-driven-development 配下の関連資産 | 1 | 1 | 208 | 0 | 46 | 段2(HELIX本体) |
| `skills/agent-skills/system-design-sizing` | system-design-sizing 配下の関連資産 | 1 | 1 | 260 | 0 | 45 | 段2(HELIX本体) |
| `skills/agent-skills/technical-writing` | technical-writing 配下の関連資産 | 1 | 1 | 332 | 0 | 41 | 段2(HELIX本体) |
| `skills/agent-skills/test-driven-development` | test-driven-development 配下の関連資産 | 1 | 1 | 249 | 0 | 46 | 段2(HELIX本体) |
| `skills/agent-skills/using-agent-skills` | using-agent-skills 配下の関連資産 | 1 | 1 | 403 | 0 | 42 | 段2(HELIX本体) |
| `skills/automation` | automation 配下の関連資産 | 0 | 8 | 811 | 1 | 46 | 段2(HELIX本体) |
| `skills/automation/browser-script` | browser-script 配下の関連資産 | 1 | 1 | 64 | 0 | 42 | 段2(HELIX本体) |
| `skills/automation/flow-optimize` | flow-optimize 配下の関連資産 | 1 | 1 | 78 | 0 | 41 | 段2(HELIX本体) |
| `skills/automation/init-setup` | init-setup 配下の関連資産 | 1 | 1 | 74 | 0 | 38 | 段2(HELIX本体) |
| `skills/automation/job-queue` | job-queue 配下の関連資産 | 1 | 1 | 207 | 0 | 37 | 段2(HELIX本体) |
| `skills/automation/lock` | lock 配下の関連資産 | 1 | 1 | 48 | 0 | 33 | 段2(HELIX本体) |
| `skills/automation/observability` | observability 配下の関連資産 | 1 | 1 | 107 | 0 | 42 | 段2(HELIX本体) |
| `skills/automation/scheduler` | scheduler 配下の関連資産 | 1 | 1 | 118 | 0 | 38 | 段2(HELIX本体) |
| `skills/automation/site-mapping` | site-mapping 配下の関連資産 | 1 | 1 | 115 | 0 | 41 | 段2(HELIX本体) |
| `skills/common` | 共通スキル群 | 0 | 68 | 17,339 | 3 | 68 | 段2(HELIX本体) |
| `skills/common/code-review` | code-review 配下の関連資産 | 1 | 1 | 833 | 0 | 35 | 段2(HELIX本体) |
| `skills/common/coding` | coding 配下の関連資産 | 1 | 1 | 621 | 0 | 30 | 段2(HELIX本体) |
| `skills/common/design` | design 配下の関連資産 | 1 | 1 | 268 | 0 | 30 | 段2(HELIX本体) |
| `skills/common/documentation` | documentation 配下の関連資産 | 1 | 4 | 796 | 1 | 62 | 段2(HELIX本体) |
| `skills/common/documentation/references` | 参照資料群 | 3 | 3 | 500 | 0 | 62 | 段2(HELIX本体) |
| `skills/common/error-fix` | error-fix 配下の関連資産 | 1 | 1 | 797 | 0 | 33 | 段2(HELIX本体) |
| `skills/common/git` | git 配下の関連資産 | 1 | 1 | 237 | 0 | 27 | 段2(HELIX本体) |
| `skills/common/infrastructure` | infrastructure 配下の関連資産 | 1 | 2 | 529 | 1 | 61 | 段2(HELIX本体) |
| `skills/common/infrastructure/references` | 参照資料群 | 1 | 1 | 301 | 0 | 61 | 段2(HELIX本体) |
| `skills/common/performance` | performance 配下の関連資産 | 1 | 3 | 980 | 1 | 59 | 段2(HELIX本体) |
| `skills/common/performance/references` | 参照資料群 | 2 | 2 | 713 | 0 | 59 | 段2(HELIX本体) |
| `skills/common/refactoring` | refactoring 配下の関連資産 | 1 | 1 | 416 | 0 | 35 | 段2(HELIX本体) |
| `skills/common/security` | security 配下の関連資産 | 1 | 5 | 1,007 | 1 | 57 | 段2(HELIX本体) |
| `skills/common/security/references` | 参照資料群 | 4 | 4 | 689 | 0 | 57 | 段2(HELIX本体) |
| `skills/common/testing` | testing 配下の関連資産 | 1 | 1 | 655 | 0 | 31 | 段2(HELIX本体) |
| `skills/common/visual-design` | visual-design 配下の関連資産 | 1 | 45 | 11,855 | 2 | 68 | 段2(HELIX本体) |
| `skills/common/visual-design/references` | 参照資料群 | 8 | 44 | 11,336 | 1 | 68 | 段2(HELIX本体) |
| `skills/common/visual-design/references/brands-jp` | brands-jp 配下の関連資産 | 25 | 25 | 6,872 | 0 | 64 | 段2(HELIX本体) |
| `skills/common/visual-design/references/platforms-jp` | platforms-jp 配下の関連資産 | 11 | 11 | 2,129 | 0 | 68 | 段2(HELIX本体) |
| `skills/design-tools` | design-tools 配下の関連資産 | 0 | 8 | 1,830 | 2 | 58 | 段2(HELIX本体) |
| `skills/design-tools/character` | character 配下の関連資産 | 1 | 1 | 209 | 0 | 35 | 段2(HELIX本体) |
| `skills/design-tools/diagram` | diagram 配下の関連資産 | 1 | 1 | 170 | 0 | 33 | 段2(HELIX本体) |
| `skills/design-tools/graphic` | graphic 配下の関連資産 | 1 | 1 | 191 | 0 | 33 | 段2(HELIX本体) |
| `skills/design-tools/pptx` | pptx 配下の関連資産 | 1 | 1 | 610 | 0 | 30 | 段2(HELIX本体) |
| `skills/design-tools/web-system` | web-system 配下の関連資産 | 1 | 4 | 650 | 1 | 58 | 段2(HELIX本体) |
| `skills/design-tools/web-system/references` | 参照資料群 | 3 | 3 | 405 | 0 | 58 | 段2(HELIX本体) |
| `skills/integration` | 統合系スキル群 | 0 | 23 | 2,810 | 2 | 72 | 段2(HELIX本体) |
| `skills/integration/agent-cost-design` | agent-cost-design 配下の関連資産 | 1 | 4 | 1,105 | 1 | 72 | 段2(HELIX本体) |
| `skills/integration/agent-cost-design/references` | 参照資料群 | 3 | 3 | 824 | 0 | 72 | 段2(HELIX本体) |
| `skills/integration/agent-design` | agent-design 配下の関連資産 | 1 | 1 | 498 | 0 | 37 | 段2(HELIX本体) |
| `skills/integration/agent-teams` | agent-teams 配下の関連資産 | 1 | 3 | 1,207 | 1 | 62 | 段2(HELIX本体) |
| `skills/integration/agent-teams/references` | 参照資料群 | 2 | 2 | 868 | 0 | 62 | 段2(HELIX本体) |
| `skills/project` | プロジェクト系スキル群 | 0 | 15 | 3,851 | 2 | 44 | 段2(HELIX本体) |
| `skills/project/api` | api 配下の関連資産 | 1 | 1 | 500 | 0 | 28 | 段2(HELIX本体) |
| `skills/project/db` | db 配下の関連資産 | 1 | 1 | 724 | 0 | 27 | 段2(HELIX本体) |
| `skills/project/fe-a11y` | fe-a11y 配下の関連資産 | 1 | 4 | 543 | 1 | 42 | 段2(HELIX本体) |
| `skills/project/fe-a11y/references` | 参照資料群 | 3 | 3 | 325 | 0 | 42 | 段2(HELIX本体) |
| `skills/project/fe-component` | fe-component 配下の関連資産 | 1 | 4 | 533 | 1 | 50 | 段2(HELIX本体) |
| `skills/project/fe-component/references` | 参照資料群 | 3 | 3 | 333 | 0 | 50 | 段2(HELIX本体) |
| `skills/project/fe-design` | fe-design 配下の関連資産 | 1 | 4 | 598 | 1 | 44 | 段2(HELIX本体) |
| `skills/project/fe-design/references` | 参照資料群 | 3 | 3 | 354 | 0 | 44 | 段2(HELIX本体) |
| `skills/project/fe-style` | fe-style 配下の関連資産 | 1 | 4 | 575 | 1 | 43 | 段2(HELIX本体) |
| `skills/project/fe-style/references` | 参照資料群 | 3 | 3 | 344 | 0 | 43 | 段2(HELIX本体) |
| `skills/project/fe-test` | fe-test 配下の関連資産 | 1 | 4 | 515 | 1 | 42 | 段2(HELIX本体) |
| `skills/project/fe-test/references` | 参照資料群 | 3 | 3 | 304 | 0 | 42 | 段2(HELIX本体) |
| `skills/project/ui` | ui 配下の関連資産 | 1 | 1 | 361 | 0 | 27 | 段2(HELIX本体) |
| `skills/tools` | ツール系スキル群 | 0 | 22 | 5,434 | 2 | 66 | 段2(HELIX本体) |
| `skills/tools/ai-coding` | ai-coding 配下の関連資産 | 1 | 10 | 4,299 | 1 | 66 | 段2(HELIX本体) |
| `skills/tools/ai-coding/references` | 参照資料群 | 9 | 9 | 3,552 | 0 | 66 | 段2(HELIX本体) |
| `skills/tools/ai-search` | ai-search 配下の関連資産 | 1 | 1 | 247 | 0 | 33 | 段2(HELIX本体) |
| `skills/tools/ide-tools` | ide-tools 配下の関連資産 | 1 | 3 | 413 | 1 | 58 | 段2(HELIX本体) |
| `skills/tools/ide-tools/references` | 参照資料群 | 2 | 2 | 276 | 0 | 58 | 段2(HELIX本体) |
| `skills/tools/web-search` | web-search 配下の関連資産 | 1 | 1 | 475 | 0 | 34 | 段2(HELIX本体) |
| `skills/workflow` | ワークフロースキル群 | 0 | 43 | 11,647 | 2 | 68 | 段2(HELIX本体) |
| `skills/workflow/adversarial-review` | adversarial-review 配下の関連資産 | 1 | 1 | 906 | 0 | 46 | 段2(HELIX本体) |
| `skills/workflow/api-contract` | api-contract 配下の関連資産 | 1 | 1 | 587 | 0 | 38 | 段2(HELIX本体) |
| `skills/workflow/compliance` | compliance 配下の関連資産 | 1 | 1 | 428 | 0 | 36 | 段2(HELIX本体) |
| `skills/workflow/context-memory` | context-memory 配下の関連資産 | 1 | 3 | 1,258 | 1 | 60 | 段2(HELIX本体) |
| `skills/workflow/context-memory/references` | 参照資料群 | 2 | 2 | 785 | 0 | 60 | 段2(HELIX本体) |
| `skills/workflow/debt-register` | debt-register 配下の関連資産 | 1 | 4 | 619 | 1 | 54 | 段2(HELIX本体) |
| `skills/workflow/debt-register/references` | 参照資料群 | 3 | 3 | 372 | 0 | 54 | 段2(HELIX本体) |
| `skills/workflow/dependency-map` | dependency-map 配下の関連資産 | 1 | 1 | 486 | 0 | 40 | 段2(HELIX本体) |
| `skills/workflow/deploy` | deploy 配下の関連資産 | 1 | 1 | 653 | 0 | 31 | 段2(HELIX本体) |
| `skills/workflow/design-doc` | design-doc 配下の関連資産 | 1 | 1 | 873 | 0 | 35 | 段2(HELIX本体) |
| `skills/workflow/dev-policy` | dev-policy 配下の関連資産 | 1 | 1 | 396 | 0 | 35 | 段2(HELIX本体) |
| `skills/workflow/dev-setup` | dev-setup 配下の関連資産 | 1 | 1 | 411 | 0 | 34 | 段2(HELIX本体) |
| `skills/workflow/estimation` | estimation 配下の関連資産 | 1 | 1 | 377 | 0 | 35 | 段2(HELIX本体) |
| `skills/workflow/gate-planning` | gate-planning 配下の関連資産 | 1 | 3 | 1,409 | 1 | 68 | 段2(HELIX本体) |
| `skills/workflow/gate-planning/references` | 参照資料群 | 2 | 2 | 979 | 0 | 68 | 段2(HELIX本体) |
| `skills/workflow/incident` | incident 配下の関連資産 | 1 | 1 | 528 | 0 | 33 | 段2(HELIX本体) |
| `skills/workflow/observability-sre` | observability-sre 配下の関連資産 | 1 | 3 | 977 | 1 | 58 | 段2(HELIX本体) |
| `skills/workflow/observability-sre/references` | 参照資料群 | 2 | 2 | 710 | 0 | 58 | 段2(HELIX本体) |
| `skills/workflow/poc` | poc 配下の関連資産 | 1 | 2 | 585 | 1 | 42 | 段2(HELIX本体) |
| `skills/workflow/poc/references` | 参照資料群 | 1 | 1 | 361 | 0 | 42 | 段2(HELIX本体) |
| `skills/workflow/postmortem` | postmortem 配下の関連資産 | 1 | 1 | 446 | 0 | 35 | 段2(HELIX本体) |
| `skills/workflow/project-management` | project-management 配下の関連資産 | 1 | 1 | 385 | 0 | 43 | 段2(HELIX本体) |
| `skills/workflow/quality-lv5` | quality-lv5 配下の関連資産 | 1 | 3 | 1,166 | 1 | 54 | 段2(HELIX本体) |
| `skills/workflow/quality-lv5/references` | 参照資料群 | 2 | 2 | 849 | 0 | 54 | 段2(HELIX本体) |
| `skills/workflow/requirements-handover` | requirements-handover 配下の関連資産 | 1 | 1 | 458 | 0 | 46 | 段2(HELIX本体) |
| `skills/workflow/research` | research 配下の関連資産 | 1 | 3 | 661 | 1 | 51 | 段2(HELIX本体) |
| `skills/workflow/research/references` | 参照資料群 | 2 | 2 | 362 | 0 | 51 | 段2(HELIX本体) |
| `skills/workflow/reverse-analysis` | reverse-analysis 配下の関連資産 | 1 | 1 | 825 | 0 | 42 | 段2(HELIX本体) |
| `skills/workflow/reverse-r0` | reverse-r0 配下の関連資産 | 1 | 1 | 854 | 0 | 36 | 段2(HELIX本体) |
| `skills/workflow/reverse-r1` | reverse-r1 配下の関連資産 | 1 | 1 | 475 | 0 | 36 | 段2(HELIX本体) |
| `skills/workflow/reverse-r2` | reverse-r2 配下の関連資産 | 1 | 1 | 495 | 0 | 36 | 段2(HELIX本体) |
| `skills/workflow/reverse-r3` | reverse-r3 配下の関連資産 | 1 | 1 | 527 | 0 | 36 | 段2(HELIX本体) |
| `skills/workflow/reverse-r4` | reverse-r4 配下の関連資産 | 1 | 1 | 474 | 0 | 36 | 段2(HELIX本体) |
| `skills/workflow/reverse-rgc` | reverse-rgc 配下の関連資産 | 1 | 1 | 501 | 0 | 37 | 段2(HELIX本体) |
| `skills/workflow/runbook` | runbook 配下の関連資産 | 1 | 3 | 742 | 1 | 50 | 段2(HELIX本体) |
| `skills/workflow/runbook/references` | 参照資料群 | 2 | 2 | 442 | 0 | 50 | 段2(HELIX本体) |
| `skills/workflow/schedule-wbs` | schedule-wbs 配下の関連資産 | 1 | 4 | 739 | 1 | 57 | 段2(HELIX本体) |
| `skills/workflow/schedule-wbs/references` | 参照資料群 | 3 | 3 | 405 | 0 | 57 | 段2(HELIX本体) |
| `skills/workflow/threat-model` | threat-model 配下の関連資産 | 1 | 3 | 743 | 1 | 55 | 段2(HELIX本体) |
| `skills/workflow/threat-model/references` | 参照資料群 | 2 | 2 | 423 | 0 | 55 | 段2(HELIX本体) |
| `skills/workflow/verification` | verification 配下の関連資産 | 1 | 3 | 1,044 | 1 | 55 | 段2(HELIX本体) |
| `skills/workflow/verification/references` | 参照資料群 | 2 | 2 | 628 | 0 | 55 | 段2(HELIX本体) |
| `skills/writing` | writing 配下の関連資産 | 0 | 4 | 896 | 1 | 39 | 段2(HELIX本体) |
| `skills/writing/explain` | explain 配下の関連資産 | 1 | 1 | 336 | 0 | 33 | 段2(HELIX本体) |
| `skills/writing/japanese` | japanese 配下の関連資産 | 1 | 1 | 176 | 0 | 34 | 段2(HELIX本体) |
| `skills/writing/presentation` | presentation 配下の関連資産 | 1 | 1 | 241 | 0 | 38 | 段2(HELIX本体) |
| `skills/writing/social` | social 配下の関連資産 | 1 | 1 | 143 | 0 | 32 | 段2(HELIX本体) |
| `src` | src 配下の関連資産 | 0 | 3 | 135 | 3 | 50 | 段2(HELIX本体) |
| `src/features` | features 配下の関連資産 | 0 | 3 | 135 | 2 | 50 | 段2(HELIX本体) |
| `src/features/helix-budget-autothinking` | helix-budget-autothinking 配下の関連資産 | 0 | 3 | 135 | 1 | 50 | 段2(HELIX本体) |
| `src/features/helix-budget-autothinking/D-CONFIG` | D-CONFIG 配下の関連資産 | 1 | 1 | 65 | 0 | 50 | 段2(HELIX本体) |
| `src/features/helix-budget-autothinking/D-IMPL` | D-IMPL 配下の関連資産 | 1 | 1 | 36 | 0 | 46 | 段2(HELIX本体) |
| `src/features/helix-budget-autothinking/D-MIG` | D-MIG 配下の関連資産 | 1 | 1 | 34 | 0 | 45 | 段2(HELIX本体) |
| `tests` | ルート直下テスト | 1 | 4 | 726 | 1 | 50 | 段2(HELIX本体) |
| `tests/__pycache__` | __pycache__ 配下の関連資産 | 1 | 1 | 0 | 0 | 50 | 段2(HELIX本体) |
| `tests/integration` | integration 配下の関連資産 | 2 | 2 | 320 | 0 | 35 | 段2(HELIX本体) |
| `verify` | 検証スクリプト | 32 | 32 | 1,420 | 0 | 40 | 段2(HELIX本体) |

## Part 3: 肥大化 top

### 再帰 file 数 top-20

| path | direct | recursive | lines | depth | path_len | longest_path |
| --- | --- | --- | --- | --- | --- | --- |
| `.` | 7 | 5,315 | 3,017,646 | 6 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix` | 13 | 3,859 | 2,807,786 | 3 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix/audit` | 3 | 2,999 | 2,141,563 | 1 | 97 | `.helix/audit/codex-runs/20260512-004430-research-PLAN-063-RESEARCH-REFACTOR-THRESHOLDS-stderr.log` |
| `.helix/audit/codex-runs` | 2,996 | 2,996 | 2,140,108 | 0 | 97 | `.helix/audit/codex-runs/20260512-004430-research-PLAN-063-RESEARCH-REFACTOR-THRESHOLDS-stderr.log` |
| `cli` | 63 | 802 | 108,027 | 5 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `cli/lib` | 76 | 533 | 65,403 | 4 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `.helix/cache` | 5 | 366 | 10,797 | 2 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix/cache/skill_classifier` | 333 | 333 | 5,661 | 0 | 99 | `.helix/cache/skill_classifier/cd4108f90c868911729e1f90a952868a53f6b8ae70c60aaaead34baba6e29329.json` |
| `docs` | 4 | 316 | 35,543 | 3 | 71 | `docs/features/helix-budget-autothinking/D-SECV/security-verification.md` |
| `cli/lib/tests` | 121 | 303 | 24,837 | 3 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `skills` | 1 | 247 | 58,466 | 4 | 76 | `skills/advanced/tech-selection/references/principles-frameworks-and-stack.md` |
| `.helix/tmp` | 217 | 217 | 635,332 | 0 | 55 | `.helix/tmp/codex-baseline-67043-1778362108997918258.txt` |
| `cli/lib/tests/__pycache__` | 177 | 177 | 0 | 0 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `docs/features` | 0 | 138 | 4,847 | 2 | 71 | `docs/features/helix-budget-autothinking/D-SECV/security-verification.md` |
| `.helix/plans` | 82 | 82 | 633 | 0 | 31 | `.helix/plans/PLAN-056.yaml.lock` |
| `cli/lib/__pycache__` | 75 | 75 | 0 | 0 | 59 | `cli/lib/__pycache__/allowed_files_estimator.cpython-312.pyc` |
| `cli/tests` | 71 | 75 | 9,304 | 4 | 76 | `cli/tests/.helix/budget/cache/classify/8d8f747bff813614ad9010f5f4e7e7d7.json` |
| `docs/plans` | 69 | 69 | 15,934 | 0 | 67 | `docs/plans/PLAN-040-helix-plan-split-and-codex-summary-isolation.md` |
| `skills/common` | 0 | 68 | 17,339 | 3 | 68 | `skills/common/visual-design/references/design-md-lint-integration.md` |
| `cli/templates` | 20 | 67 | 6,941 | 1 | 47 | `cli/templates/docs/L4-fullstack-sprint-guide.md` |

### 再帰 行数 top-20

| path | direct | recursive | lines | depth | path_len | longest_path |
| --- | --- | --- | --- | --- | --- | --- |
| `.` | 7 | 5,315 | 3,017,646 | 6 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix` | 13 | 3,859 | 2,807,786 | 3 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix/audit` | 3 | 2,999 | 2,141,563 | 1 | 97 | `.helix/audit/codex-runs/20260512-004430-research-PLAN-063-RESEARCH-REFACTOR-THRESHOLDS-stderr.log` |
| `.helix/audit/codex-runs` | 2,996 | 2,996 | 2,140,108 | 0 | 97 | `.helix/audit/codex-runs/20260512-004430-research-PLAN-063-RESEARCH-REFACTOR-THRESHOLDS-stderr.log` |
| `.helix/tmp` | 217 | 217 | 635,332 | 0 | 55 | `.helix/tmp/codex-baseline-67043-1778362108997918258.txt` |
| `cli` | 63 | 802 | 108,027 | 5 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `cli/lib` | 76 | 533 | 65,403 | 4 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `skills` | 1 | 247 | 58,466 | 4 | 76 | `skills/advanced/tech-selection/references/principles-frameworks-and-stack.md` |
| `docs` | 4 | 316 | 35,543 | 3 | 71 | `docs/features/helix-budget-autothinking/D-SECV/security-verification.md` |
| `cli/lib/tests` | 121 | 303 | 24,837 | 3 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `skills/common` | 0 | 68 | 17,339 | 3 | 68 | `skills/common/visual-design/references/design-md-lint-integration.md` |
| `docs/plans` | 69 | 69 | 15,934 | 0 | 67 | `docs/plans/PLAN-040-helix-plan-split-and-codex-summary-isolation.md` |
| `skills/common/visual-design` | 1 | 45 | 11,855 | 2 | 68 | `skills/common/visual-design/references/design-md-lint-integration.md` |
| `skills/workflow` | 0 | 43 | 11,647 | 2 | 68 | `skills/workflow/gate-planning/references/gate-entry-exit-criteria.md` |
| `skills/common/visual-design/references` | 8 | 44 | 11,336 | 1 | 68 | `skills/common/visual-design/references/design-md-lint-integration.md` |
| `.helix/cache` | 5 | 366 | 10,797 | 2 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `skills/agent-skills` | 0 | 42 | 9,606 | 2 | 58 | `skills/agent-skills/browser-testing-with-devtools/SKILL.md` |
| `cli/tests` | 71 | 75 | 9,304 | 4 | 76 | `cli/tests/.helix/budget/cache/classify/8d8f747bff813614ad9010f5f4e7e7d7.json` |
| `cli/templates` | 20 | 67 | 6,941 | 1 | 47 | `cli/templates/docs/L4-fullstack-sprint-guide.md` |
| `skills/common/visual-design/references/brands-jp` | 25 | 25 | 6,872 | 0 | 64 | `skills/common/visual-design/references/brands-jp/moneyforward.md` |

### 最大 depth top-10

| path | direct | recursive | lines | depth | path_len | longest_path |
| --- | --- | --- | --- | --- | --- | --- |
| `.` | 7 | 5,315 | 3,017,646 | 6 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `cli` | 63 | 802 | 108,027 | 5 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `cli/lib` | 76 | 533 | 65,403 | 4 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `cli/tests` | 71 | 75 | 9,304 | 4 | 76 | `cli/tests/.helix/budget/cache/classify/8d8f747bff813614ad9010f5f4e7e7d7.json` |
| `skills` | 1 | 247 | 58,466 | 4 | 76 | `skills/advanced/tech-selection/references/principles-frameworks-and-stack.md` |
| `.helix` | 13 | 3,859 | 2,807,786 | 3 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `cli/lib/tests` | 121 | 303 | 24,837 | 3 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `cli/tests/.helix` | 0 | 4 | 79 | 3 | 76 | `cli/tests/.helix/budget/cache/classify/8d8f747bff813614ad9010f5f4e7e7d7.json` |
| `docs` | 4 | 316 | 35,543 | 3 | 71 | `docs/features/helix-budget-autothinking/D-SECV/security-verification.md` |
| `skills/common` | 0 | 68 | 17,339 | 3 | 68 | `skills/common/visual-design/references/design-md-lint-integration.md` |

### 最長 path top-10

| path | direct | recursive | lines | depth | path_len | longest_path |
| --- | --- | --- | --- | --- | --- | --- |
| `.` | 7 | 5,315 | 3,017,646 | 6 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix` | 13 | 3,859 | 2,807,786 | 3 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix/cache` | 5 | 366 | 10,797 | 2 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix/cache/recommendations` | 1 | 2 | 62 | 1 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix/cache/recommendations/code` | 1 | 1 | 27 | 0 | 103 | `.helix/cache/recommendations/code/36973f968a19e964b4b3f7b83c48e1241769a22fbdbddf07540345cede3aa397.json` |
| `.helix/cache/skill_classifier` | 333 | 333 | 5,661 | 0 | 99 | `.helix/cache/skill_classifier/cd4108f90c868911729e1f90a952868a53f6b8ae70c60aaaead34baba6e29329.json` |
| `.helix/audit` | 3 | 2,999 | 2,141,563 | 1 | 97 | `.helix/audit/codex-runs/20260512-004430-research-PLAN-063-RESEARCH-REFACTOR-THRESHOLDS-stderr.log` |
| `.helix/audit/codex-runs` | 2,996 | 2,996 | 2,140,108 | 0 | 97 | `.helix/audit/codex-runs/20260512-004430-research-PLAN-063-RESEARCH-REFACTOR-THRESHOLDS-stderr.log` |
| `cli` | 63 | 802 | 108,027 | 5 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `cli/lib` | 76 | 533 | 65,403 | 4 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |

### 単一ディレクトリ direct file 数 top-10

| path | direct | recursive | lines | depth | path_len | longest_path |
| --- | --- | --- | --- | --- | --- | --- |
| `.helix/audit/codex-runs` | 2,996 | 2,996 | 2,140,108 | 0 | 97 | `.helix/audit/codex-runs/20260512-004430-research-PLAN-063-RESEARCH-REFACTOR-THRESHOLDS-stderr.log` |
| `.helix/cache/skill_classifier` | 333 | 333 | 5,661 | 0 | 99 | `.helix/cache/skill_classifier/cd4108f90c868911729e1f90a952868a53f6b8ae70c60aaaead34baba6e29329.json` |
| `.helix/tmp` | 217 | 217 | 635,332 | 0 | 55 | `.helix/tmp/codex-baseline-67043-1778362108997918258.txt` |
| `cli/lib/tests/__pycache__` | 177 | 177 | 0 | 0 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `cli/lib/tests` | 121 | 303 | 24,837 | 3 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `.helix/plans` | 82 | 82 | 633 | 0 | 31 | `.helix/plans/PLAN-056.yaml.lock` |
| `cli/lib` | 76 | 533 | 65,403 | 4 | 88 | `cli/lib/tests/__pycache__/test_deliverable_gate_pre_release.cpython-312-pytest-9.0.3.pyc` |
| `cli/lib/__pycache__` | 75 | 75 | 0 | 0 | 59 | `cli/lib/__pycache__/allowed_files_estimator.cpython-312.pyc` |
| `cli/tests` | 71 | 75 | 9,304 | 4 | 76 | `cli/tests/.helix/budget/cache/classify/8d8f747bff813614ad9010f5f4e7e7d7.json` |
| `docs/plans` | 69 | 69 | 15,934 | 0 | 67 | `docs/plans/PLAN-040-helix-plan-split-and-codex-summary-isolation.md` |

### 100+ file ある単一ディレクトリ

| path | direct file 数 | 備考 |
| --- | --- | --- |
| `.helix/audit/codex-runs` | 2,996 | runtime/cache/generated |
| `.helix/cache/skill_classifier` | 333 | runtime/cache/generated |
| `.helix/tmp` | 217 | runtime/cache/generated |
| `cli/lib/tests/__pycache__` | 177 | source/test flat dir |
| `cli/lib/tests` | 121 | source/test flat dir |

### 1,000+ lines の単一ファイル (参考)

| path | lines | 所見 |
| --- | --- | --- |
| `.helix/audit/codex-runs/20260513-033425-pg-stderr.log` | 76,310 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260512-010849-se-PLAN-063-W-2pre-stderr.log` | 74,910 | ほぼ `.helix` log / tmp |
| `.helix/tmp/w2b-output.log` | 64,974 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260510-121931-se-PLAN-045-W-2-stderr.log` | 60,728 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260513-030436-se-stderr.log` | 58,797 | ほぼ `.helix` log / tmp |
| `.helix/tmp/w2d-output.log` | 57,572 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260510-124232-se-PLAN-045-W-3-stderr.log` | 51,763 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260510-052747-se-PLAN-040-W-1-stderr.log` | 51,272 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260511-034149-se-PLAN-056-W-1-stderr.log` | 42,578 | ほぼ `.helix` log / tmp |
| `.helix/tmp/plan028-w5b-output.log` | 41,457 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260513-025252-pg-stderr.log` | 40,949 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260513-024112-pg-stderr.log` | 39,542 | ほぼ `.helix` log / tmp |
| `.helix/tmp/plan028-w4-output.log` | 37,501 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260513-030830-se-stderr.log` | 37,422 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260513-023206-pg-stderr.log` | 36,124 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260513-030843-se-stderr.log` | 35,210 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260512-003854-se-PLAN-063-W-1a-stderr.log` | 34,998 | ほぼ `.helix` log / tmp |
| `.helix/tmp/plan028-w3-output.log` | 34,459 | ほぼ `.helix` log / tmp |
| `.helix/audit/codex-runs/20260513-022134-pg-stderr.log` | 33,387 | ほぼ `.helix` log / tmp |
| `.helix/tmp/w3e-output.log` | 32,794 | ほぼ `.helix` log / tmp |

## Part 4: 段 1 / 段 2 / 配布 / runtime 比率

合計 file 数 (`.git` 除く): **5,315**
合計 line 数 (text only): **3,018,486**

| segment | files | ratio(files) | lines | ratio(lines) | max depth | メモ |
| --- | --- | --- | --- | --- | --- | --- |
| 段1 product-like | 8 | 0.2% | 862 | 0.0% | 5 | `src/`, `public/`, `tests/` を便宜分類 |
| 段2 HELIX 本体 | 1,381 | 26.0% | 202,057 | 6.7% | 7 | `cli/`, `skills/`, `docs/`, `helix/` ほか |
| 配布 (cli/templates) | 67 | 1.3% | 6,941 | 0.2% | 4 | install で project 側へコピーされる候補 |
| runtime (.helix) | 3,859 | 72.6% | 2,808,626 | 93.0% | 5 | 最大の膨張源 |

install 後に project 側へ残る代表は `配布 + runtime` です。現状は **67 + 3,859 = 3,926 files** で、project へ持ち込まれる footprint が大きすぎます。

- 現状 配布 file 数 / 行数: **67 / 6,941**
- V2 目標案: **配布 file 数 67 → 30 以下 (-55%)、行数 6,941 → 3,000 前後 (-56%)**

## Part 5: 重複・分散・不整合の検出

### 5.1 同種ファイル/ディレクトリの分散

| 種別 | 分散箇所 | 所見 |
| --- | --- | --- |
| hooks | `.claude/hooks`, `cli/templates/hooks`, `skills/agent-skills/hooks` | source-of-truth が複数化 |
| commands | `.claude/commands`, `docs/commands` | source-of-truth が複数化 |
| agents | `.claude/agents`, `cli/templates/agents` | source-of-truth が複数化 |
| tests | `cli/tests`, `cli/lib/tests`, `tests` | source-of-truth が複数化 |
| references | `skills/*/references` が 32 箇所 | skill ごとに micro-knowledge 化されすぎ |

### 5.2 命名不一致

| 観点 | 件数 | 所見 |
| --- | --- | --- |
| snake_case を含む path | 522 | `helix_db.py`, `test_helix_*` など Python/test 由来 |
| kebab-case を含む path | 4,553 | docs/skills/PLAN/command 名の大半 |
| 数字 prefix を含む path | 3,185 | `verify/001-*`, `PLAN-xxx`, dated retro/log` が大量 |
| `helix-` を含む name | 167 | CLI command は dash 優勢 |
| `helix_` を含む name | 34 | Python module / test では underscore 優勢 |

主な不整合:

- CLI は `helix-*`、Python module は `helix_*`、docs は `PLAN-xxx-*`、verify は `001-*` と、軸ごとに命名規則が別です。
- `.helix/plans/PLAN-xxx.yaml` と `docs/plans/PLAN-xxx-*.md` のように、同じ PLAN 軸で extension と suffix 体系が分かれています。

### 5.3 廃止候補の残存

- `.pytest_cache/`, `__pycache__/`, `.helix/tmp/`, `.helix/cache/skill_classifier/` は runtime/generated artifact であり、repo 常駐の妥当性が低いです。
- `.helix/session-summaries/` は PLAN-016 系の経緯を持つが、現状の source-of-truth としては `cost_log` / `helix log report` 側へ寄せた方が整合的です。
- `helix/sync-codex-skills.sh` は既存監査でも deprecate 候補です。

### 5.4 過度な細分化

- `skills/*/references` が 32 箇所あり、skill 本体より参照資料の分散管理コストが先に立っています。
- `skills/project/fe-a11y`, `fe-component`, `fe-design`, `fe-style`, `fe-test` は 5 分割だが、利用者視点では `ui` 系の連続操作として読む方が自然です。
- `reverse-r0` から `reverse-rgc` の 6 skill はフェーズ分離としては明快でも、検索導線は深くなっています。

### 5.5 過度な集約

- `cli/` root に command entrypoint が 63 本あり、launcher 層が flat すぎます。
- `docs/` root に 30+ subdir、`docs/plans/` に 69 file、`cli/tests/` に 71 file、`cli/lib/tests/` に 121 direct file があり、flat hotspot が複数あります。
- `.helix/audit/codex-runs/` は 2,996 file の単一ディレクトリで、最悪の flat hotspot です。

## Part 6: 整理計画

| ID | 対象 path | 問題 | 整理計画 | 移動先 | 影響範囲 | V2 Phase 紐付け |
| --- | --- | --- | --- | --- | --- | --- |
| F-001 | `.helix/audit/codex-runs` | 2,996 file の実行ログが repo を支配 | extract | 別 repo / external artifact storage | 監査参照・再現手順 | Phase 1 |
| F-002 | `.helix/tmp` | 217 file / 635k lines の一時出力が常駐 | deprecate | runtime TTL cleanup | debug 手順・比較差分 | Phase 1 |
| F-003 | `.helix/cache/skill_classifier` | 333 cache file が恒久化 | deprecate | runtime TTL cleanup | 推薦キャッシュ | Phase 1 |
| F-004 | `.helix/plans/*.lock` | yaml と lock が同階層で混在 | move | `.helix/locks/plans/` | plan loader | Phase 1 |
| F-005 | `.helix/session-summaries/` | 日次 md が runtime 配下で肥大化 | archive | `docs/archive/session-summaries/` または外部保存 | 運用履歴参照 | Phase 1 |
| F-006 | `.helix/retros/` | 54 retro が runtime と docs で責務混在 | move | `docs/retros/` | retro 参照 | Phase 1 |
| F-007 | `.helix/research/` | 研究ノートが runtime 側に残留 | move | `docs/research/runtime/` | research 参照 | Phase 1 |
| F-008 | `.helix/proposals/` | proposal が runtime に残る | move | `docs/proposals/runtime/` | proposal 参照 | Phase 1 |
| F-009 | `.helix/design-proposals/` | 設計文書が runtime に残る | move | `docs/design/proposals/` | 設計リンク | Phase 1 |
| F-010 | `.helix/cross-sprint-reviews/` | review 証跡が docs でなく runtime | move | `docs/reviews/cross-sprint/` | review evidence | Phase 1 |
| F-011 | `cli/lib/__pycache__` | 75 binary file が追跡対象化 | deprecate | gitignore + clean target | pytest / import | Phase 1 |
| F-012 | `cli/lib/tests/__pycache__` | 177 binary file が flat hotspot | deprecate | gitignore + clean target | pytest | Phase 1 |
| F-013 | `tests/__pycache__` | root tests 側にも pycache が残る | deprecate | gitignore + clean target | pytest | Phase 1 |
| F-014 | `cli/tests/.helix/` | test fixture 内に runtime ミニ複製 | merge | 共通 fixture dir | Bats fixture | Phase 2 |
| F-015 | `cli/tests/` と `cli/lib/tests/` と `tests/` | test 入口が 3 箇所に分散 | merge | `tests/{bats,pytest,integration}` | CI, import path | Phase 2 |
| F-016 | `.claude/hooks` と `cli/templates/hooks` と `skills/agent-skills/hooks` | hook 定義が 3 箇所 | merge | `hooks/` source-of-truth + generated copy | Claude/Codex install | Phase 2 |
| F-017 | `.claude/commands` と `docs/commands` | slash command と説明 docs が分離し drift 余地 | merge | `docs/commands/` 正本 + generated `.claude/commands` | Claude command UX | Phase 2 |
| F-018 | `.claude/agents` と `cli/templates/agents` | agent prompt 定義が 2 系統 | merge | `agents/` source-of-truth | template install | Phase 2 |
| F-019 | `skills/*/references` 32 箇所 | reference 分割が細かく探索コスト高 | merge | skill 単位 index 再編 | skill docs | Phase 2 |
| F-020 | `skills/agent-skills/` | 25 skill と native HELIX skill 群が隣接し概念競合 | move | `vendor/agent-skills/` か plugin 化 | skill dispatch | Phase 2 |
| F-021 | `skills/project/fe-*` 5 分割 | FE skill が微粒度で散在 | merge | `skills/project/ui/` 配下へ再編 | skill docs / references | Phase 2 |
| F-022 | `skills/workflow/reverse-r0..rgc` | reverse が 6 skill に分離され深い | merge | `skills/workflow/reverse-analysis/` subdocs | reverse dispatch | Phase 2 |
| F-023 | `docs/plans/` | 69 file flat 配置で検索コスト高 | move | `docs/plans/00x-01x/...` か index 分割 | links, grep | Phase 2 |
| F-024 | `docs/features/PLAN-*` と `docs/plans/PLAN-*` | PLAN 軸 docs が二重化 | merge | feature doc を plan appendix へ | doc links | Phase 2 |
| F-025 | `docs/v2/A-audit/` | 監査 docs 増加で audit 島が形成 | merge | `docs/audit/v2/` | audit links | Phase 2 |
| F-026 | `docs/archive/plans` と `docs/plans` | 現行 / archive 切替導線が弱い | rename | archive taxonomy を明示 | plan lookup | Phase 2 |
| F-027 | `src/features/helix-budget-autothinking` と `docs/features/helix-budget-autothinking` | src/docs 二重管理の疑い | merge | 単一路線化 | feature maintainability | Phase 3 |
| F-028 | `public/generated/codex` | 生成物が repo 内に常駐 | deprecate | build artifact 化 | asset references | Phase 3 |
| F-029 | `.claude-plugin/` | plugin metadata が root 直下で孤立 | move | `plugins/claude/` | plugin loader | Phase 3 |
| F-030 | `.pytest_cache/` | 開発キャッシュが repo 常駐 | deprecate | gitignore + clean target | pytest | Phase 1 |
| F-031 | `scripts/git-hooks` と `cli/templates/hooks` | git hook と template hook が二重管理 | merge | `hooks/git/` source-of-truth | install script | Phase 3 |
| F-032 | `verify/` と `cli/tests/` | 検証 shell と Bats の責務境界が曖昧 | merge | `tests/verify` | CI matrix | Phase 3 |
| F-033 | `helix/sync-codex-skills.sh` | 単発 script が root policy から孤立 | deprecate | installer workflow へ吸収 | setup docs | Phase 3 |
| F-034 | `cli/helix-*` 63 entrypoints | CLI 入口が flat すぎる | split | `cli/commands/` + thin launcher生成 | shell completion / docs | Phase 4 |
| F-035 | `docs/` root 直下 30+ subdirs | docs taxonomy が横に広すぎる | split | `docs/{product,ops,history,v2}` | links, contributor navigation | Phase 4 |
| F-036 | `requirements-dev.txt` のみ root | packaging 情報が薄い | as-is | 現状維持だが package metadata 方針要確認 | setup | Phase 4 |

## Part 7: V2 配布物最小化方針

| 層 | files | lines | 例 | 方針 |
| --- | --- | --- | --- | --- |
| 必須最小 | 5 | 314 | `CLAUDE.md.template`, `phase.yaml`, `hooks/*` | install 初期セットだけ残す |
| drive 別 | 8 | 578 | `L4-{be,fe,db,fullstack}-sprint-guide.md`, `agents/*` | drive 指定時のみ opt-in 配布 |
| advanced | 54 | 6,049 | `matrix.yaml`, `framework.yaml`, `handover-*`, `teams/*` | 必要時追加取得 or command 生成へ |

提案:

- `cli/templates/` は **installer の source-of-truth** と割り切り、project へ常時配るのは `必須最小` のみ。
- `drive 別` は `helix init --drive <type>` 時のみ展開。
- `advanced` は `helix enable <feature>` または on-demand generation に落とし、デフォルト配布から外す。

## Part 8: V2 後の目標構造案

```text
ai-dev-kit-vscode/
├── cli/
│   ├── commands/           # thin launcher generator outputs
│   ├── lib/
│   ├── roles/
│   └── templates/
├── docs/
│   ├── core/               # adr, architecture, commands
│   ├── plans/
│   ├── audit/
│   ├── ops/                # runbook, smoke, slo, rollback
│   └── v2/
├── skills/
│   ├── core/
│   ├── project/
│   └── vendor/
├── runtime/                # gitignore or externalized
│   ├── handover/
│   ├── cache/
│   └── audit/
└── tests/
    ├── bats/
    ├── pytest/
    └── verify/
```

目標値:

- 段2 HELIX 本体 file 数: **1,381 → 700 前後 (-49%)**
- 配布物 file 数: **67 → 20-30 (-55% to -70%)**
- runtime を Git 管理する場合の上限: **3,859 → 200 以下 (-94%+)**
- max depth: **7 → 5 以内**

## 末尾集計

| 区分 | 件数 |
| --- | --- |
| 現状 file 総数 | 5,315 |
| 段1 product-like files | 8 |
| 段2 HELIX 本体 files | 1,381 |
| 配布 files | 67 |
| runtime files | 3,859 |
| 整理候補 total | 36 |
| move | 9 |
| merge | 13 |
| rename | 1 |
| deprecate | 8 |
| split | 2 |
| extract | 1 |
| archive | 1 |
| as-is | 1 |

| V2 Phase | 件数 |
| --- | --- |
| Phase 1 | 14 |
| Phase 2 | 13 |
| Phase 3 | 6 |
| Phase 4 | 3 |

### 次に実行すべき整理 top-5

- `\.helix/audit/codex-runs` を repo 外し or TTL cleanup 対象にする
- `\.helix/tmp`, `\.pytest_cache`, `__pycache__` を Git 管理対象から除外する
- `hooks` / `agents` / `commands` の source-of-truth を 1 箇所へ統一する
- `cli/tests`, `cli/lib/tests`, `tests`, `verify` の test taxonomy を再編する
- `cli/templates/` を 必須最小 / drive別 / advanced に分離し、advanced を opt-in 化する

### 実行に PM 判断が必要な top-3

- runtime (`.helix/`) を Git 管理から外すか、履歴保持をどう設計し直すか
- `skills/agent-skills` を vendor 扱いに寄せるか、HELIX core skill と同列で維持するか
- `docs/plans` / `docs/features/PLAN-*` / `.helix/plans` の PLAN 正本をどこに固定するか
