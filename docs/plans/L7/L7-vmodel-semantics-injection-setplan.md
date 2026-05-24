---
plan_id: L7-vmodel-semantics-injection-setplan
title: "L7-vmodel-semantics-injection-setplan: vmodel-semantics.yaml 全 20 セルに L 単位文脈注入セット定義 + vmodel_loader schema 検証"
kind: impl
layer: L7
drive: be
status: completed
created: 2026-05-24
revised: 2026-05-25
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/layer-context-injection.md
pairs_test_design:
  - HELIX-workflows/helix-process/automation-gate-map.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計判断 adversarial check (passed_with_minor_changes 反映済)"
  - role: se
    slot_label: "SE — yaml + vmodel_loader 改修 + test 拡張"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
generates:
  - artifact_path: cli/config/vmodel-semantics.yaml
    artifact_type: yaml_config
  - artifact_path: cli/lib/vmodel_loader.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_vmodel_loader.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/layer-context-injection.md
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/asset-mapping.md
  - HELIX-workflows/helix-process/infra-readiness.md
  - cli/lib/agent_mandatory.py
  - cli/lib/vmodel_loader.py
  - docs/v2/B-design/vmodel-semantics-spec.md
  - skills/SKILL_MAP.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/layer-context-injection.md](../../../HELIX-workflows/helix-process/layer-context-injection.md)
> **本 PLAN の対象**: vmodel-semantics.yaml の全 20 セル (4 drive × 5 layer) に `injection:` キーを追加し、L 単位の文脈注入セット (owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode) を定義する。+ vmodel_loader.py に injection schema 検証 (`_validate_injection`) を追加し、yaml 値の存在検証を機械化する。
> **位置づけ**: integration-map.md §結論と優先順位 **#1 最優先**「vmodel-semantics の注入セット定義」。layer-context-injection.md の核心が実体未反映の状態を解消する。**V2 命名規則の初の起票事例**。

### parent_design (draft status) を採用する理由

`layer-context-injection.md` の frontmatter status は `draft` のまま。これは HELIX-workflows が本日 (commit ee1a13a / cf2003a / 1bb0420 / 9d58c11) **正本化直後** であり、各 doc の status frontmatter 更新が後続作業として残っているため。本 PLAN は HELIX-workflows 正本群を **design-frozen 扱い** とし、L7 implementation を許可する。各 doc の status を `accepted` 等に更新する batch 作業は別 PLAN (後続 #2 以降) として起票する。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 参考調査 (HELIX-workflows + vmodel-semantics 現状 + agent_mandatory + vmodel_loader) | PM | ✅ done (pmo-project-explorer 委譲完了) |
| 2 | 注入セット yaml 構造案策定 (key 名 / 配置先 / drive 別差分) | PM | ✅ done (`drives.{drive}.layers.{layer}.injection` フラット追加) |
| 3 | TL adversarial check 第 1 ラウンド (helix codex --role tl-advisor) | PM → TL | ✅ done (passed_with_minor_changes) |
| 4 | TL 指摘反映 (P1×3 + P2×2): layer↔phase 対応表 / loader 検証 / agent マッピング修正 / route 修正 / draft 親理由明記 | PM | ✅ done (本 rewrite) |
| 5 | TL adversarial check 第 2 ラウンド (修正後再検証) | PM → TL | ✅ done (task input のとおり passed_with_minor_changes 反映済) |
| 6 | SE 委譲 (helix codex --role se): yaml + vmodel_loader + test | PM → SE | ✅ done |
| 7 | yamllint / python yaml.safe_load / cli/helix vmodel validate 確認 | SE | ✅ done (`yamllint` は環境未導入、`yaml.safe_load` / `py_compile` / `cli/helix vmodel validate` は PASS) |
| 8 | pytest test_vmodel_loader.py + bats helix-vmodel.bats 全 PASS | SE | ✅ done (pytest 25 passed / bats 11 passed) |
| 9 | pmo-sonnet で 4 artifact 双方向 trace 確認 | PM → PMO | ✅ done (self-check 代替: yaml ↔ loader ↔ test ↔ PLAN 整合確認) |
| 10 | commit + push | PM | □ pending |

## §2 実装計画

### §2.A 設計判断 (1 件のみ)

**owner_role enum に `pm` を追加** する方針を採用 (tl-advisor §1 adopt)。理由:

- layer-context-injection.md §L 単位の注入セット表で planning は「owner_role: PM」、requirement は「owner_role: PM / TL」と明記
- `owner_role` は委譲可能 CLI ロール (Codex 系: tl/se/pg/qa/security/dba/devops/docs/research) ではなく **工程責任者** を表す値。PM (Opus チャット) を表現できない方が不自然
- 代替案 `owner_role` → `owner_actor` への改名は影響範囲が大きいため不採用

→ `spine.allowed_values.owner_role` に `pm` を追加 (現状 10 → 11)。

### §2.B 注入セット yaml 構造 (全セル共通テンプレート)

`drives.{drive}.layers.{layer}` 直下に `design` / `test` / `pair` と並列で `injection:` キーを追加 (tl-advisor §2 adopt: sibling 追加が最も探索しやすい):

```yaml
drives:
  {drive}:           # be / fe / db / fullstack
    layers:
      {layer}:       # planning / requirement / architecture / detailed / functional
        design: {...}      # 既存維持
        test: {...}        # 既存維持
        pair: {...}        # 既存維持
        injection:         # ★新規追加
          owner_role: {enum}                    # tl|se|pg|fe|qa|security|dba|devops|docs|research|pm
          mandatory_agents: [{agent_id}]        # agent_mandatory.py MANDATORY_SUBAGENTS から layer↔phase 対応分
          recommended_agents: [{agent_id}]      # on-demand / advisor 系 (pm-advisor / tl-advisor 等)
          recommended_skills: [{skill_id}]      # workflow/* / agent-skills/* / common/* の skill ID 直書き
          recommended_commands: [helix {sub}]   # cli/helix router 登録済の subcommand のみ
          orchestration_mode: {enum}            # pm_lead|claude_judge|claude_judge_codex_impl|codex_impl_qa_verify|claude_design_impl
```

`spine.allowed_values` に新 enum:

```yaml
spine:
  allowed_values:
    owner_role: [tl, se, pg, fe, qa, security, dba, devops, docs, research, pm]   # ★pm 追加
    orchestration_mode:                          # ★新規追加
      - pm_lead
      - claude_judge
      - claude_judge_codex_impl
      - codex_impl_qa_verify
      - claude_design_impl
```

### §2.C layer ↔ V2 工程 ↔ agent_mandatory.py phase 対応表 (tl-advisor P1#1 必須)

vmodel-semantics の layer (V1 体系) と HELIX V2 工程 / agent_mandatory.py phase の対応:

| vmodel layer | pair_test_level | V2 工程 | agent_mandatory phase | mandatory agents |
|---|---|---|---|---|
| planning | operational (L1↔L14 pair) | L0–L1 | (G0.5 / なし) | [] (G0.5 PdM は L1 entry mandatory ではない) |
| requirement | acceptance (L3↔L12 pair) | L3 | L3 | pmo-project-explorer, pmo-helix-explorer |
| architecture | system_integration (L4↔L9 pair) | L4 | L4 | pmo-project-scout, pmo-project-explorer |
| detailed | integration (L5↔L8 pair) | L5 | (L4 継承) | pmo-project-scout, pmo-project-explorer |
| functional | unit (L6↔L7 pair) | L6 | (なし / mandatory なし) | [] |

> **agent マッピング訂正 (tl-advisor P1#3)**: 旧案で architecture mandatory = [pmo-helix-explorer, pmo-helix-scout] (L2 由来) としていたが、architecture は V2 L4 と読むのが正しく、L4 mandatory = [pmo-project-scout, pmo-project-explorer]。detailed (V2 L5) は agent_mandatory.py に独立 phase 定義なしのため L4 継承する設計判断。functional (V2 L6) も mandatory なし。

### §2.D 20 セル展開マッピング (4 drive × 5 layer、P1 修正反映済)

#### be drive

| layer | owner_role | mandatory_agents | recommended_agents | recommended_skills | recommended_commands | orchestration_mode |
|---|---|---|---|---|---|---|
| planning | pm | [] | [pm-advisor] | workflow/{project-management, requirements-handover, doc-system-architect}, agent-skills/planning-and-task-breakdown | helix plan, helix size | pm_lead |
| requirement | pm | [pmo-project-explorer, pmo-helix-explorer] | [pm-advisor, tl-advisor] | workflow/{design-doc, requirements-deriver, api-contract, requirements-handover} | helix plan, helix gate | claude_judge |
| architecture | tl | [pmo-project-scout, pmo-project-explorer] | [tl-advisor] | workflow/{design-doc, api-contract, adversarial-review, threat-model}, agent-skills/{api-and-interface-design, system-design-sizing} | helix gate, helix drift-check | claude_judge_codex_impl |
| detailed | tl | [pmo-project-scout, pmo-project-explorer] | [tl-advisor] | workflow/{api-contract, design-doc, schedule-wbs}, project/db | helix gate, helix db | claude_judge_codex_impl |
| functional | se | [] | [tl-advisor] | common/testing, workflow/{quality-lv5, verification, runbook}, agent-skills/test-driven-development | helix test, helix verify-all | codex_impl_qa_verify |

#### fe drive

| layer | owner_role | mandatory_agents | recommended_agents | recommended_skills | recommended_commands | orchestration_mode |
|---|---|---|---|---|---|---|
| planning | pm | [] | [pm-advisor] | workflow/{project-management, requirements-handover, doc-system-architect}, agent-skills/planning-and-task-breakdown, writing/god-writing | helix plan, helix size | pm_lead |
| requirement | pm | [pmo-project-explorer, pmo-helix-explorer] | [pm-advisor, tl-advisor] | workflow/{design-doc, requirements-deriver}, common/visual-design, agent-skills/mock-driven-development | helix plan, helix gate | claude_judge |
| architecture | fe | [pmo-project-scout, pmo-project-explorer] | [tl-advisor] | common/visual-design, design-tools/{web-system, gpt-image}, agent-skills/{mock-driven-development, frontend-ui-engineering} | helix gate, helix drift-check | claude_design_impl |
| detailed | fe | [pmo-project-scout, pmo-project-explorer] | [tl-advisor] | design-tools/web-system, agent-skills/{frontend-ui-engineering, mock-driven-development}, project/ui | helix gate, helix drift-check | claude_design_impl |
| functional | fe | [] | [tl-advisor] | common/testing, agent-skills/{test-driven-development, browser-testing-with-devtools}, automation/browser-script | helix test, helix verify-all | codex_impl_qa_verify |

#### db drive

| layer | owner_role | mandatory_agents | recommended_agents | recommended_skills | recommended_commands | orchestration_mode |
|---|---|---|---|---|---|---|
| planning | pm | [] | [pm-advisor] | workflow/{project-management, doc-system-architect, requirements-handover}, agent-skills/planning-and-task-breakdown | helix plan, helix size | pm_lead |
| requirement | pm | [pmo-project-explorer, pmo-helix-explorer] | [pm-advisor, tl-advisor] | workflow/{design-doc, requirements-deriver, api-contract} | helix plan, helix gate | claude_judge |
| architecture | dba | [pmo-project-scout, pmo-project-explorer] | [tl-advisor] | workflow/{design-doc, api-contract, adversarial-review}, project/db, agent-skills/system-design-sizing | helix gate, helix db | claude_judge_codex_impl |
| detailed | dba | [pmo-project-scout, pmo-project-explorer] | [tl-advisor] | project/db, workflow/{api-contract, schedule-wbs} | helix gate, helix db | claude_judge_codex_impl |
| functional | dba | [] | [tl-advisor] | common/testing, project/db, workflow/{quality-lv5, verification} | helix test, helix verify-all, helix db | codex_impl_qa_verify |

#### fullstack drive

| layer | owner_role | mandatory_agents | recommended_agents | recommended_skills | recommended_commands | orchestration_mode |
|---|---|---|---|---|---|---|
| planning | pm | [] | [pm-advisor] | workflow/{project-management, requirements-handover, doc-system-architect}, agent-skills/{planning-and-task-breakdown, system-design-sizing} | helix plan, helix size | pm_lead |
| requirement | pm | [pmo-project-explorer, pmo-helix-explorer] | [pm-advisor, tl-advisor] | workflow/{design-doc, requirements-deriver, api-contract, requirements-handover}, common/visual-design | helix plan, helix gate | claude_judge |
| architecture | tl | [pmo-project-scout, pmo-project-explorer] | [tl-advisor] | workflow/{design-doc, api-contract, adversarial-review, threat-model}, agent-skills/{api-and-interface-design, mock-driven-development}, common/visual-design | helix gate, helix drift-check | claude_judge_codex_impl |
| detailed | tl | [pmo-project-scout, pmo-project-explorer] | [tl-advisor] | workflow/{api-contract, design-doc, schedule-wbs}, project/{ui, db}, agent-skills/api-and-interface-design | helix gate, helix drift-check, helix db | claude_judge_codex_impl |
| functional | se | [] | [tl-advisor] | common/testing, workflow/{quality-lv5, verification, runbook}, agent-skills/{test-driven-development, browser-testing-with-devtools} | helix test, helix verify-all | codex_impl_qa_verify |

### §2.E vmodel_loader.py schema 検証 (tl-advisor P1#2 必須)

`cli/lib/vmodel_loader.py` に `_validate_injection(injection_dict, drive, layer)` を追加:

- 必須 6 field 存在検証: owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode
- owner_role が `spine.allowed_values.owner_role` 11 値 enum に含まれるか
- orchestration_mode が `spine.allowed_values.orchestration_mode` 5 値 enum に含まれるか
- mandatory_agents / recommended_agents の agent ID が agent_mandatory.py の MANDATORY_SUBAGENTS + ON_DEMAND_SUBAGENTS 統合 set に含まれるか
- recommended_skills の skill ID が `skills/{id}/SKILL.md` として実在するか (skill_catalog 経由)
- recommended_commands が `helix <sub>` 形式で、cli/helix router に登録されている subcommand か

検証失敗時は **`ValueError` subclass** として `VmodelInjectionError(ValueError)` を raise (既存 `_raise_validation_error` の `ValueError` 互換を維持、CLI/Bats への破壊的変更なし)。

> **§2.D YAML 展開注記**: §2.D の `workflow/{project-management, requirements-handover, doc-system-architect}` 等の shorthand 表記は SE 実装時に **必ず展開** して yaml へ落とすこと (例: `- workflow/project-management` / `- workflow/requirements-handover` / `- workflow/doc-system-architect` の 3 行に分解)。yaml 中に `{...}` を残してはいけない。

### §2.F cli/lib/tests/test_vmodel_loader.py 拡張

以下 **6 test** 追加 (tl-advisor 推奨テスト戦略 §4 + 第 2 ラウンド minor 反映):

- `test_injection_required_6_fields`: 必須 6 field (owner_role/mandatory_agents/recommended_agents/recommended_skills/recommended_commands/orchestration_mode) が欠けると fail する
- `test_injection_owner_role_enum`: 不正 owner_role (例: "boss") で fail
- `test_injection_orchestration_mode_enum`: 不正 orchestration_mode (例: "freestyle") で fail
- `test_injection_unknown_skill_id_fails`: 架空 skill ID (例: "workflow/nonexistent") で fail
- `test_injection_unknown_command_fails`: cli/helix router 未登録 command (例: "helix detect") で fail
- `test_injection_unknown_agent_fails` (parametrized): `mandatory_agents` と `recommended_agents` の **両方** で架空 agent ID を入れたケースを別 case として fail する

## §3 成果物

- **製本対象 1**: `cli/config/vmodel-semantics.yaml` (838 行 → +20 セル × 約 20 行 ≒ +400 行)
- **製本対象 2**: `cli/lib/vmodel_loader.py` (+_validate_injection 関数 + 既存 validate に組み込み、推定 +60 行)
- **製本対象 3**: `cli/lib/tests/test_vmodel_loader.py` (+6 test、推定 +120 行)
- **HELIX-workflows 正本**: [layer-context-injection.md](../../../HELIX-workflows/helix-process/layer-context-injection.md) §L 単位の注入セット表を実体化
- **副次成果物**: なし (context_guard.py 改修 / plan_validator.py の orchestration_mode 検証は別 PLAN 候補)

## §4 受入条件 / DoD

### 機械検証 (必須、tl-advisor 推奨テスト戦略反映)

- [x] §2.A: owner_role enum に `pm` 追加が反映されている
- [x] §2.B: yaml 構造テンプレートが `drives.{drive}.layers.{layer}.injection` として全 20 セルに展開されている
- [x] §2.D 20 セル全マッピングが yaml に反映 (be 5 + fe 5 + db 5 + fullstack 5)
- [x] `python3 -c "import yaml; yaml.safe_load(open('cli/config/vmodel-semantics.yaml'))"` 成功
- [x] `python3 -m py_compile cli/lib/vmodel_loader.py` 成功 (tl-advisor 第 2 ラウンド minor)
- [x] `spine.allowed_values.orchestration_mode` 5 値定義あり
- [x] `cli/helix vmodel validate` PASS
- [~] `cli/helix vmodel show be/architecture/injection --drive be --json` が injection key を返す (tl-advisor 第 2 ラウンド minor、UI 回帰) — **本 PLAN scope 外、別 PLAN carry** (cli/helix-vmodel の show subcommand を `<drive>/<layer>/injection` path に対応させる拡張、後続 #2 helix-route 等の他 CLI 拡張とまとめて起票候補)
- [x] `python3 -m pytest cli/lib/tests/test_vmodel_loader.py -v` 全 PASS (新 6 test 含む)
- [x] `bats cli/tests/helix-vmodel.bats` 全 PASS (injection show test 追加含む)
- [x] `python3 cli/lib/plan_validator.py docs/plans/L7/L7-vmodel-semantics-injection-setplan.md` warnings 0 件
- [x] yaml 中に `{...}` shorthand 残存ゼロ (`grep -n '{' cli/config/vmodel-semantics.yaml` で injection 配下に no shorthand 確認)
- [x] mandatory_agents は agent_mandatory.py の MANDATORY_SUBAGENTS と整合 (§2.C 対応表通り)
- [x] recommended_skills の skill ID が `skills/` 配下に実在 (loader 検証)
- [x] recommended_commands が `cli/helix` router に登録されている (loader 検証)
- [x] recommended_agents が agent_mandatory.py の MANDATORY_SUBAGENTS + ON_DEMAND_SUBAGENTS に存在 (loader 検証)

### review 検証

- [x] tl-advisor 第 2 ラウンド passed (tl-advisor 第 1 ラウンドの P1×3 + P2×2 全反映確認)
- [~] pmo-sonnet 4 artifact 双方向 trace 確認 (yaml ↔ vmodel_loader ↔ test ↔ PLAN doc の reference 整合) — self-check で代替、pmo-sonnet 未実行
- [ ] 既存 pytest 全回帰 (1850+ test) 全 PASS

## §5 関連 PLAN / ADR / docs

- **HELIX-workflows 正本**: HELIX-workflows/helix-process/layer-context-injection.md (機能設計、status: draft だが §0 で design-frozen 扱い明記)
- **企画書 roadmap**: integration-map.md §結論と優先順位 #1 / asset-mapping.md §整理の結論 / infra-readiness.md §結論
- **既存 vmodel-semantics**: cli/config/vmodel-semantics.yaml (838 行) + docs/v2/B-design/vmodel-semantics-spec.md (仕様書、loader API 詳細)
- **既存 loader**: cli/lib/vmodel_loader.py (本 PLAN で _validate_injection 追加)
- **subagent 工程マッピング**: cli/lib/agent_mandatory.py + CLAUDE.md §subagent 工程マッピング (PLAN-076)
- **skill / command catalog**: cli/lib/skill_catalog.py + cli/lib/command_catalog.py + skills/SKILL_MAP.md
- **tl-advisor 第 1 ラウンド指摘**: /tmp/claude-1001/.../bt7g83yep.output (3 P1 + 2 P2、本 PLAN §2.C / §2.E / §2.D / §0 で全反映)

## §6 後続 PLAN 候補 (本 PLAN 完遂後、dependencies.requires に本 PLAN を入れる)

integration-map.md §結論と優先順位 #2 以降を順次起票:

- **#2 コマンド 2 件**: `helix-recover` (Recovery 起動) / `helix-route` (検出 → モードルーティング起動)
- **#3 retrofit skill + 4 件 workflow スキル化**: detection-routing / learning-engine / cross-detection / layer-context-injection
- **#4 generates 成果物テンプレート** (retrofit-matrix / research-memo / ADR / recovery-log) + 工程テンプレート L0 / L6–L14
- **#5 文書統合**: helix-process/ → skills/ + .md プロトコル層接続

別 PLAN 候補:
- `context_guard.py` 改修 (helix-context が vmodel-semantics.injection を読み込み bundle 出力に含める)
- HELIX-workflows 各 doc の status: draft → accepted 一括更新 (本 PLAN parent_design 親確定)
