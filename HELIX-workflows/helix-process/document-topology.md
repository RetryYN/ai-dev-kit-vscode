# HELIX システム改修対象フォルダ構成と参照関係

本書は、現行 HELIX システムを改修するために、workflow / skill / runtime / harness / DB / detector / injection の構成と参照関係を回収するための台帳である。

対象は HELIX を動かす仕組みそのものに限る。`docs/plans/` は project management control plane の一部として構造だけ扱い、個別 PLAN 本文や個別プロジェクト成果物は列挙しない。

## 1. 対象範囲

| 領域 | パス | 現存状態 | 役割 | 回収対象 |
|---|---|---|---|---|
| Core / Runtime | `helix/` | 現存 | HELIX の概念、共通実行規律、Claude / Codex adapter | Yes |
| Workflow docs | `HELIX-workflows/` | 現存 | Forward / workflow / DB / detection / injection の仕様 | Yes |
| Skills | `skills/` | 現存 | workflow・実装・設計・検証の実行知識 | Yes |
| CLI / Harness | `cli/` | 現存 | HELIX command、engine、DB、detector、routing、templates | Yes |
| Claude runtime | `.claude/` | 現存 | Claude Code hooks、agents、commands、runtime context | Yes |
| Codex project marker | `.codex` | 現存（ファイル、0 byte） | project-local Codex marker / state placeholder | 構造のみ Yes |
| Codex user runtime | `~/.codex/` | 現存（ユーザー領域） | Codex CLI user config、rules、skills、sessions、logs | 構造のみ Yes |
| HELIX runtime state | `.helix/` | 現存 | handover、cache、audit、runtime state、locks | 構造のみ Yes |
| Project management control plane | `cli/helix-plan`, `cli/helix-task`, `cli/helix-handover`, `cli/helix-sprint`, `cli/helix-gate`, `.helix/*`, `docs/plans/` | 現存 | PLAN / task / handover / sprint / gate / phase / registry で工程を制御する | Yes |
| Project plan files | `docs/plans/` | 現存 | 個別 PLAN 本文 / 進捗 | 個別列挙は No |
| Project design docs | `docs/v2/**` | 現存 | HELIX-workflows の V モデル成果物 | 必要時のみ参照 |

現存状態の定義:

- **現存**: このリポジトリ内に存在する。
- **現存（ユーザー領域）**: リポジトリ外の `~/.codex` に存在する。HELIX repo から直接管理しない。
- **未整備**: 対応文書や実装が未作成、または代替 skill / command で運用中。
- **対象外**: HELIX システム改修の構成回収には含めない。

## 2. 現行フォルダ構成

抽出対象の主要ディレクトリは次の通り。

```text
helix/
├── HELIX_CORE.md
├── HELIX_RUNTIME_RULES.md
├── CLAUDE_RUNTIME_ADAPTER.md
├── CODEX_RUNTIME_ADAPTER.md
├── AGENTS.md.example
├── validate.sh
└── sync-codex-skills.sh

HELIX-workflows/
├── HELIX-process-L0-L14.md
└── helix-process/
    ├── README.md
    ├── L0-concept.md ... L14-operation-verification.md
    ├── *-workflow.md
    ├── db-*.md
    ├── *routing.md / *detection.md / *gate*.md
    ├── layer-context-injection.md
    ├── integration-map.md
    └── document-topology.md

skills/
├── SKILL_MAP.md
├── workflow/
├── common/
├── project/
├── tools/
├── integration/
├── agent-skills/
├── advanced/
├── automation/
├── design-tools/
└── writing/

cli/
├── helix-*
├── config/
├── lib/
├── templates/
├── roles/
├── schemas/
├── prompts/
├── scripts/
├── setup/
└── tests/

.claude/
├── CLAUDE.md
├── agents/
├── commands/
├── hooks/
├── agent-memory/
└── memory/

.codex
└── project-local Codex marker / state placeholder

~/.codex/
├── AGENTS.md
├── config.toml
├── rules/
├── skills/
├── sessions/
├── logs / sqlite state
└── plugins/

.helix/
├── handover/
├── audit/
├── cache/
├── runtime/
├── scrum/
├── reverse/
├── sprint/
├── tasks/
├── rules/
└── state/

project management control plane
├── cli/helix-plan
├── cli/helix-task
├── cli/helix-handover
├── cli/helix-sprint
├── cli/helix-gate
├── cli/lib/plan_*.py
├── cli/lib/task_*.py
├── cli/lib/handover.py
├── cli/lib/sprint_*.py
├── cli/lib/deliverable_gate.py
├── cli/lib/plan_registry.py
├── .helix/phase.yaml
├── .helix/task-plan.yaml
├── .helix/handover/
└── docs/plans/             # 個別 PLAN 本文。構成把握のみ、個別列挙しない。
```

## 3. 件数

| 領域 | 件数 |
|---|---:|
| `HELIX-workflows/helix-process/*.md` | 48 |
| `skills/**/SKILL.md` | 130 |
| `skills/workflow/*/SKILL.md` | 40 |
| `skills/common/*/SKILL.md` | 12 |
| `skills/project/*/SKILL.md` | 8 |
| `skills/tools/*/SKILL.md` | 4 |
| `skills/integration/*/SKILL.md` | 3 |
| `skills/agent-skills/*/SKILL.md` | 24 |
| `skills/advanced/*/SKILL.md` | 9 |
| `skills/automation/*/SKILL.md` | 8 |
| `skills/design-tools/*/SKILL.md` | 6 |
| `skills/writing/*/SKILL.md` | 5 |
| `cli/helix-*` command | 80+ |
| `cli/lib/*.py` | 139 |
| `.claude/agents/*.md` | 19 |
| `.claude/hooks/*` | 17 |
| `.codex` | project-local Codex marker / state placeholder |
| `~/.codex/` | user-level Codex config / skills / sessions |
| project management command | `helix plan` / `helix task` / `helix handover` / `helix sprint` / `helix gate` |

## 4. 参照の正本順

HELIX システム改修時の参照順は次の通り。

```text
helix/HELIX_CORE.md
  -> helix/HELIX_RUNTIME_RULES.md
  -> helix/{CLAUDE,CODEX}_RUNTIME_ADAPTER.md
  -> HELIX-workflows/HELIX-process-L0-L14.md
  -> HELIX-workflows/helix-process/{workflow,DB,detection,injection}.md
  -> skills/SKILL_MAP.md
  -> skills/**/SKILL.md
  -> cli/config/*.yaml
  -> cli/helix-* / cli/lib/*.py
  -> .claude/{agents,hooks,commands}
  -> .codex / ~/.codex runtime state
  -> .helix runtime state
```

原則:

- `HELIX_CORE.md` は概念を定義する。
- `HELIX_RUNTIME_RULES.md` は実行規律を定義する。
- adapter は Claude / Codex 差分だけを定義する。
- `HELIX-workflows` は workflow / DB / detection / injection の仕様正本である。
- `skills` は実行知識であり、workflow の代替正本ではない。
- `cli` は実装であり、仕様とずれた場合は drift として回収する。
- `.claude` は Claude Code runtime 実装であり、HELIX 概念を再定義しない。
- `.codex` / `~/.codex` は Codex runtime state / user config であり、HELIX 概念を再定義しない。
- project management control plane は HELIX 本体の一部である。個別 PLAN 本文は列挙しないが、PLAN / task / handover / sprint / gate / registry の仕組みは本書の回収対象に含める。

> 常時注入 core セットの**単一権威 (SSoT) は `helix/core-manifest.tsv`**。上の参照順は人間可読な説明であり、実際に注入する import の正本は manifest。setup.sh / global loader は manifest を参照し、core セットを二重定義しない（drift 防止）。

## 4.2 bounded context と配置（helix/ ↔ HELIX-workflows/）

HELIX 本体は 2 つの bounded context に分かれる（HELIX_CORE §5 DDD に準拠）。これは「ねじれ」ではなく意図された境界である。

| BC | ディレクトリ | 責務 |
|---|---|---|
| governance / runtime | `helix/` | 概念正本・絶対原則・実行規律・runtime adapter・core manifest |
| process model | `HELIX-workflows/` | V モデル工程定義（L0-L14 正本 + `helix-process/*` 詳細） |

- 常時注入 core セットは BC を**越境して**選択される（manifest が governance BC から process BC の `HELIX-process-L0-L14.md` を 1 本選ぶ）。これは正常な参照であり、物理統合は不要。
- **公開 API**: `@~/.helix/core/<path>` import は配布契約。消費側プロジェクトの loader が直接読むため、**path 変更 = 公開 API 破壊**（既存消費側が setup.sh 再実行まで参照切れ）。core ファイルの物理移動は原則行わない（配置非依存 mount `~/.helix/core` でパスを安定させる設計）。

### 将来移動 policy（公開 API 破壊を避ける）

core ファイルの path をやむを得ず変更する場合:

1. **メジャーバージョン境界**でのみ行う。
2. 旧 path の **shim / alias を最低 2 minor バージョン維持**する。
3. `setup.sh` に **migration detector**（旧 path import を検出して警告 + 新 path へ誘導）を入れる。
4. `helix/core-manifest.tsv` を更新し、drift test で setup.sh / loader との一致を保証する。

## 4.1 現存性レビュー

この文書の主要項目は実ファイルと突合済み。現時点の注意点は次の通り。

| 項目 | 状態 | 扱い |
|---|---|---|
| `.codex` | 現存。ただし directory ではなく 0 byte file | repo-local marker / placeholder として扱う |
| `~/.codex/` | 現存。user-level config / sessions / skills | 構造のみ把握し、repo 文書では管理しない |
| `skills/workflow/recovery` | 未整備 | `recovery-workflow.md` + `cli/helix-recover` + `context-memory` / `error-fix` / `incident` で代替運用 |
| `HELIX-workflows/helix-process/infra-readiness.md` | 現存 | 管理・自動化文書に含める |
| `HELIX-workflows/helix-process/v2-9mode-ecosystem.md` | 現存 | 旧 9 mode / ecosystem 文脈の legacy reference として回収対象 |
| `docs/plans/` | 現存 | project management control plane の保存先として構造のみ扱う。個別 PLAN 本文は列挙しない |
| `skills/SKILL_MAP.md` の Refactor / Retrofit / Recovery CLI 記述 | 現存。ただし現 CLI と矛盾の疑い | `cli/helix-refactor`, `cli/helix-retrofit`, `cli/helix-recovery` が存在するため、未整備警告は再確認対象 |

## 5. Workflow 文書構成

### 5.1 Forward

| 種別 | ファイル | 役割 |
|---|---|---|
| Forward index | `HELIX-process-L0-L14.md` | L0-L14 の常時注入正本 |
| Workflow index | `helix-process/README.md` | workflow 文書の索引 |
| L detail | `L0-concept.md` ... `L14-operation-verification.md` | 各 L 工程の詳細 |

### 5.2 入口 workflow

| workflow | 文書 | 主な skill | CLI / engine |
|---|---|---|---|
| Scrum | `scrum-workflow.md` | `skills/agent-skills/helix-scrum` | `cli/helix-scrum-agile`, `cli/lib/scrum_agile_engine.py` |
| Discovery | `discovery-workflow.md` | `skills/agent-skills/helix-discovery`, `skills/workflow/poc` | `cli/helix-discovery`, `cli/lib/discovery_compat.py` |
| Reverse | `reverse-workflow.md` | `skills/workflow/reverse-analysis`, `reverse-r0` ... `reverse-rgc` | `cli/helix-reverse`, `cli/lib/reverse_local.py` |
| Incident | `incident-workflow.md` | `skills/workflow/incident`, `runbook`, `postmortem` | `cli/helix-incident`, `cli/lib/incident_engine.py` |
| Add-feature | `add-feature-workflow.md` | `skills/workflow/design-doc`, `api-contract` | `cli/helix-add-feature`, `cli/lib/add_feature_engine.py` |
| Refactor | `refactor-workflow.md` | `skills/common/refactoring`, `skills/common/testing` | `cli/helix-refactor`, `cli/lib/refactor_engine.py` |
| Retrofit | `retrofit-workflow.md` | `skills/workflow/retrofit`, `skills/advanced/migration` | `cli/helix-retrofit`, `cli/lib/retrofit_engine.py` |
| Research | `research-workflow.md` | `skills/workflow/research`, `skills/advanced/tech-selection` | `cli/helix-research`, `cli/lib/research_guard.py` |
| Recovery | `recovery-workflow.md` | 専用 `skills/workflow/recovery` は未整備。`skills/common/error-fix`, `skills/workflow/context-memory`, `skills/workflow/incident` で代替 | `cli/helix-recover`, `cli/helix-recovery`, `cli/lib/recovery_engine.py` |

### 5.3 工程専門 workflow

| workflow | 文書 | 対応 L | 主な skill |
|---|---|---|---|
| Screen design | `screen-design-workflow.md` | L2 | `skills/project/ui`, `skills/common/design` |
| Frontend design | `frontend-design-workflow.md` | L10 | `skills/common/visual-design`, `skills/project/fe-*` |
| HELIX W | `two-stage-agent-design.md` | AI agent system | `skills/integration/agent-design`, `skills/integration/agent-teams` |

## 6. 管理・自動化文書構成

| 分類 | 文書 | 対応実装 / skill |
|---|---|---|
| DB 収束 | `db-integration.md`, `db-auto-registration.md` | `cli/lib/helix_db.py`, `cli/lib/plan_registry.py`, `cli/helix-db` |
| 検出 routing | `detection-routing.md`, `cross-detection.md` | `cli/helix-route`, `cli/lib/route_engine.py`, `skills/workflow/detection-routing` |
| Gate / test | `automation-gate-map.md`, `test-perspective-gate.md` | `cli/helix-gate`, `cli/lib/deliverable_gate.py`, `skills/workflow/gate-planning` |
| 注入 | `layer-context-injection.md` | `cli/config/vmodel-semantics.yaml`, `cli/helix-vmodel`, `skills/workflow/layer-context-injection` |
| Learning | `learning-engine.md` | `cli/helix-learn`, `cli/lib/learning_engine.py`, `skills/workflow/learning-engine` |
| Observability | `observability-metrics.md` | `cli/helix-observe`, `skills/automation/observability`, `skills/workflow/observability-sre` |
| Context | `continuous-run-context-management.md` | `cli/helix-auto-run`, `cli/lib/auto_run_engine.py`, `.helix/auto-run` |
| CI / PR | `ci-pr-workflow.md` | `cli/helix-pr`, `cli/helix-push`, `cli/tests/*.bats` |
| 資産 mapping | `asset-mapping.md`, `integration-map.md`, `folder-structure-review.md` | `cli/helix-asset`, `skills/workflow/doc-system-architect` |
| FE detector | `fe-detector-spec.md` | `skills/project/fe-*`, detector 実装 |
| 横断機構 | `cross-cutting-mechanisms.md`, `review-stage-routing.md`, `deviation-plan-map.md` | `cli/helix-interrupt`, `cli/helix-debt`, `cli/helix-review` |
| 基盤状態 | `infra-readiness.md` | `cli/helix-doctor`, `cli/helix-test`, test / detector 実装 |
| 旧 ecosystem | `v2-9mode-ecosystem.md` | legacy reference。現行 workflow / Core と用語 drift を確認する |

## 7. Skill フォルダ構成

| カテゴリ | パス | 件数 | 役割 |
|---|---|---:|---|
| workflow | `skills/workflow/` | 40 | HELIX workflow / gate / reverse / detection / project management |
| common | `skills/common/` | 12 | 汎用実装品質、レビュー、テスト、セキュリティ |
| project | `skills/project/` | 8 | API / DB / UI / FE 専門 |
| tools | `skills/tools/` | 4 | AI coding、IDE、検索 |
| integration | `skills/integration/` | 3 | agent design、agent team、cost |
| agent-skills | `skills/agent-skills/` | 24 | 上流 agent skill / legacy alias / discovery |
| advanced | `skills/advanced/` | 9 | migration、legacy、tech selection、external API |
| automation | `skills/automation/` | 8 | scheduler、job queue、lock、observability |
| design-tools | `skills/design-tools/` | 6 | diagram、image、web-system、pptx |
| writing | `skills/writing/` | 5 | writing support |

## 8. Workflow skill 一覧

`skills/workflow/` は HELIX workflow を動かす主要 skill 群である。

```text
adversarial-review/
api-contract/
compliance/
context-memory/
cross-detection/
debt-register/
dependency-map/
deploy/
design-doc/
detection-routing/
dev-policy/
dev-setup/
doc-review/
doc-system-architect/
estimation/
gate-planning/
incident/
layer-context-injection/
learning-engine/
observability-sre/
poc/
postmortem/
project-management/
quality-lv5/
requirements-deriver/
requirements-handover/
research/
retrofit/
reverse-analysis/
reverse-r0/
reverse-r1/
reverse-r2/
reverse-r3/
reverse-r4/
reverse-rgc/
review-stage-routing/
runbook/
schedule-wbs/
threat-model/
verification/
```

## 9. CLI / Harness 構成

| フォルダ | 役割 |
|---|---|
| `cli/helix-*` | ユーザー・hook・harness から呼ぶ command |
| `cli/lib/` | command の実装 engine |
| `cli/lib/detectors/` | drift / debt / regression / relation などの detector |
| `cli/lib/migrations/` | HELIX DB migration |
| `cli/lib/projectors/` | event / state projection |
| `cli/config/` | model、fallback、vmodel-semantics、plan limits |
| `cli/templates/` | agent、doc、plan、rules、state、team の生成元 |
| `cli/roles/` | role 定義 |
| `cli/schemas/` | doc-map、gate、matrix、phase、review output schema |
| `cli/tests/` | Bats / integration test |
| `cli/lib/tests/` | Python unit / integration test |

## 9.1 Project management control plane

HELIX のプロジェクト管理系は、単なる `docs/plans/` の文書群ではなく、工程を制御する本体機構である。

| 機能 | 現存 | 主な実装 | 状態 / 参照 |
|---|---|---|---|
| PLAN 管理 | 現存 | `cli/helix-plan`, `cli/helix-plan-cmds/`, `cli/lib/plan_*.py` | PLAN 本文、frontmatter、依存、registry を扱う |
| Task 管理 | 現存 | `cli/helix-task`, `cli/lib/task_dispatcher.py`, `cli/lib/task_type_inference.py` | task catalog / dispatch を扱う |
| Handover | 現存 | `cli/helix-handover`, `cli/lib/handover.py`, `.helix/handover/` | セッション・担当引継ぎの正本 |
| Sprint | 現存 | `cli/helix-sprint`, `cli/lib/sprint_lint.py`, `cli/lib/sprint_auto_check.py`, `.helix/sprint/` | L7 実装進捗 / sprint step 管理 |
| Gate | 現存 | `cli/helix-gate`, `cli/lib/deliverable_gate.py`, `.helix/gate-checks.yaml` | 工程通過条件 / readiness / fail-close |
| Phase / state | 現存 | `.helix/phase.yaml`, `.helix/state-machine.yaml`, `cli/lib/phase_guard.py` | 現在工程と gate 状態 |
| Registry / DB | 現存 | `cli/lib/plan_registry.py`, `cli/lib/helix_db.py`, `cli/helix-db` | PLAN / trace / registry の保存 |
| Project management skill | 現存 | `skills/workflow/project-management/SKILL.md` | ダッシュボード・進捗・WBS の知識。HELIX 本体仕様との整合確認が必要 |

この層は Forward / workflow / runtime の下にぶら下がる補助ではなく、HELIX の工程制御そのものを実行する control plane として扱う。

## 10. Runtime 構成

### 10.1 Claude runtime

| パス | 役割 |
|---|---|
| `.claude/CLAUDE.md` | Claude Code runtime context |
| `.claude/agents/*.md` | subagent 定義 |
| `.claude/commands/*.md` | slash command |
| `.claude/hooks/*` | PreToolUse / PostToolUse / SessionStart / Stop hook |
| `.claude/agent-memory/` | agent memory |
| `.claude/memory/` | project memory |

### 10.2 Codex runtime

| パス | 役割 |
|---|---|
| `.codex` | project-local Codex marker / state placeholder。現状は directory ではなく 0 byte file |
| `~/.codex/AGENTS.md` | user-level Codex instructions |
| `~/.codex/config.toml` | Codex user config / model defaults |
| `~/.codex/rules/` | Codex rules |
| `~/.codex/skills/` | Codex installed skills。HELIX skills は `helix/sync-codex-skills.sh` で symlink |
| `~/.codex/sessions/` | Codex session history |
| `~/.codex/log/`, `~/.codex/*.sqlite` | Codex logs / runtime DB |
| `cli/codex` | raw `codex exec` を制御する project shim |
| `cli/helix-codex` | HELIX discipline を注入して Codex を呼ぶ harness |
| `helix/CODEX_RUNTIME_ADAPTER.md` | Codex 固有 runtime 差分の正本 |

### 10.3 HELIX runtime state

| パス | 役割 |
|---|---|
| `.helix/handover/` | セッション / 担当引継ぎ |
| `.helix/audit/` | audit / deferred findings |
| `.helix/cache/` | recommender / lock / classifier cache |
| `.helix/runtime/` | runtime state |
| `.helix/scrum/` | discovery / scrum runtime state |
| `.helix/reverse/` | reverse runtime state |
| `.helix/sprint/` | L7 sprint state |
| `.helix/tasks/` | task catalog / task state |
| `.helix/rules/` | local runtime rules |
| `.helix/state/` | framework state |

## 11. 改修時の参照関係

| 改修対象 | 仕様正本 | skill | 実装 | runtime |
|---|---|---|---|---|
| workflow routing | `detection-routing.md`, `HELIX-process-L0-L14.md` | `detection-routing`, `cross-detection` | `cli/helix-route`, `cli/lib/route_engine.py` | `.helix/cache`, `.helix/runtime` |
| skill injection | `layer-context-injection.md` | `layer-context-injection`, `SKILL_MAP.md` | `cli/config/vmodel-semantics.yaml`, `cli/helix-vmodel`, `cli/helix-skill` | recommender cache |
| DB registration | `db-integration.md`, `db-auto-registration.md` | `project-management`, `verification` | `cli/helix-db`, `cli/lib/helix_db.py` | `.helix/helix.db` |
| project management | `HELIX_RUNTIME_RULES.md`, `HELIX-process-L0-L14.md`, `db-integration.md` | `project-management`, `schedule-wbs`, `gate-planning` | `cli/helix-plan`, `cli/helix-task`, `cli/helix-handover`, `cli/helix-sprint`, `cli/helix-gate`, `cli/lib/plan_registry.py` | `.helix/phase.yaml`, `.helix/handover`, `.helix/sprint`, `docs/plans/` |
| Reverse | `reverse-workflow.md` | `reverse-analysis`, `reverse-r0` ... `reverse-rgc` | `cli/helix-reverse`, `cli/lib/reverse_local.py` | `.helix/reverse` |
| Discovery | `discovery-workflow.md` | `helix-discovery`, `poc` | `cli/helix-discovery`, `cli/lib/discovery_*` | `.helix/scrum` |
| Recovery | `recovery-workflow.md` | `context-memory`, `error-fix`, `incident` | `cli/helix-recover`, `cli/lib/recovery_*` | `.helix/handover`, `.helix/audit` |
| Gate | `automation-gate-map.md`, `test-perspective-gate.md` | `gate-planning`, `verification` | `cli/helix-gate`, `cli/lib/deliverable_gate.py` | gate state |
| Claude harness | `CLAUDE_RUNTIME_ADAPTER.md`, `.claude/CLAUDE.md` | `ai-coding`, `agent-teams` | `.claude/hooks`, `cli/helix-claude` | `.claude`, `.helix` |
| Codex harness | `CODEX_RUNTIME_ADAPTER.md`, `AGENTS.md` | `ai-coding` | `cli/helix-codex`, `cli/codex`, `cli/lib/context_guard.py`, `cli/lib/codex_*` | `.codex`, `~/.codex`, `.helix/codex-prompts`, `.helix/audit/codex-runs` |

## 12. 回収で見るべき不整合

- workflow 文書に対応する skill がない、または skill 名が旧名のまま。
- skill はあるが `SKILL_MAP.md` / `vmodel-semantics.yaml` から注入されない。
- project management control plane が Forward / workflow / DB 仕様と別物として記述されている。
- PLAN / task / handover / sprint / gate / phase / registry のどれかが仕様・skill・CLI・runtime の接続表から抜けている。
- workflow 文書に CLI がある前提で書いているが、実装 command がない。
- CLI はあるが workflow 文書・skill・runtime adapter のどこにも参照されない。
- `.claude/hooks` が HELIX Core / Runtime Rules と異なる判断をしている。
- `.codex` / `~/.codex` / `cli/codex` shim / `cli/helix-codex` の役割が文書上で分離されていない。
- `HELIX-process-L0-L14.md` が常時注入を超えて詳細を抱え込んでいる。
- `skills/SKILL_MAP.md` が索引を超えて workflow 正本を再定義している。
- `drive` / `mode` など旧 implementation field が新概念として扱われている。

## 13. この文書の使い方

1. 改修対象が workflow / skill / runtime / CLI / DB / detector / injection のどれかを決める。
2. §11 の参照関係から、仕様正本・skill・実装・runtime を同時に確認する。
3. どこか一箇所だけを直さない。仕様、skill、実装、runtime の drift を必ず確認する。
4. `docs/plans/` は project management control plane の保存先として扱うが、個別 PLAN 本文は列挙しない。
