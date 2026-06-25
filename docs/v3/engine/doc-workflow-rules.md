# C6 — ルール化 doc/workflow 契約（機械パース + 駆動 + gate + auto-enroll）

> keystone C6（最重要：契約が無ければ閉ループが始まらない）。base SSoT = [capture §3/§5/§6/§8](../audit/2026-06-26-new-base-comprehensive-capture.md) / 実体 = clean harness `src/workflow/*` / `docs/governance/{document-system-map,gate-design}.md` / `src/gate/*`。
> V3 = Python。対応: REQ-DOC-01/02/03 / AT-V3-10/11 / FR-CFG-01。

## 1. 目的

doc / workflow を**機械パース可能な契約**にし、projection-writer（C2）が DB 行へ投影できるようにする（「DB が *あるべき集合* を持つ」の供給源）。HELIX の散文 workflow は機械的にもれを検出できない、を解く。

## 2. frontmatter 契約（capture §5 — vmodel-lint が双方向 trace 検証）

```yaml
layer: L<N>                    # 機械フィルタ primary key
status: confirmed|draft|placeholder  # gate-confirm lint が status=confirmed ⟺ 対応 gate PASS を機械強制
pair_artifact: <path>|self     # vmodel-lint が双方向 trace（孤児0/ref-resolves/trace-bidir）。"self"=wireframe 特例
sub_doc: <slug>                # VALID_SUB_DOCS[layer] 登録 slug（L4 以降）
next_pair_freeze: L<N>         # 次に freeze が必要な V-pair 層
plan: docs/plans/PLAN-...      # 起票 PLAN への back-link
```

- **必須 frontmatter**: artifact kind ごとに必須 field（欠落 = violation）。`status: confirmed` は prose 宣言不可（gate PASS と機械連動、parse 失敗でも `ok=false` = fail-open 禁止 = `gate-confirm`）。
- **ID 規約**: 機械パース可能 ID（BR-/FR-L1-NN/NFR-/PM-HM-GD(画面)/U-<GROUP>-NNN/IMP-/PLAN-<PREFIX>-NN/ADR-）。違反 = violation（`id-format`/`dup-id`）。
- **必須セクション**: kind ごと（設計 doc = DbC 契約、PLAN = §0-§7。§6 用語 delta / §7 FR delta を全 PLAN 強制 = doc anti-drift）。

## 3. PLAN 契約（capture §8）

命名 `PLAN-<PREFIX>-<NN>-<slug>`（PREFIX = L1-L7/DISCOVERY/REVERSE/RECOVERY/M(master-hub)）。frontmatter: `plan_id/kind(11 enum)/layer/drive/status/agent_slots/generates(artifact_path+type)/dependencies(parent/requires/blocks)/review_evidence`。
- **review_evidence**（機械着地）: `reviewer/review_kind/reviewed_at/tests_green_at/verdict/worker_model/reviewer_model`。`tests_green_at ≤ reviewed_at` を機械強制（test-before-review）、cross_agent は `worker_model ≠ reviewer_model`（cross-review）。
- **駆動専用**: `forward_routing`(L1/L3/L4/L5/gap-only = Forward 戻し先) / `confirmed_reverse_type`(5) / `promotion_strategy`(reuse-as-is/with-hardening/redesign/discard) / `decision_outcome`(confirmed/rejected/pivot)。親子 = `dependencies.parent` 1 段 + master-hub PLAN。

## 4. 駆動モデル契約（capture §3 — 13 mode、`DRIVE_TDD_FITS` + routing）

各 mode に **red_triggers / green_requirements / forward_return / approval 要否** を機械契約として持つ。出口は必ず Forward L0-L14 合流。

| mode | 入口 signal（routing） | forward_return | approval |
|---|---|---|---|
| design(Forward) | descent_obligation_missing 等 | L3-L6 | — |
| add-feature | feature_addition/scope_extension | L3-L6 | — |
| discovery | requirement_undefined/feasibility_unknown/design_uncertain/poc | L1/L3/L4-L6 | — |
| reverse | failure/doctor/drift/gap | R4 routing → L1/L3/L4/L5/gap-only | — |
| recovery | agent_runaway/context_exhaustion/forced_stop | 再開点→Forward | **要** |
| incident | production_incident/hotfix_required | L1/L3/L4-L6/L14 | **要**(env=prod) |
| refactor | debt_degradation/code_smell | L7(behavior_unchanged) | — |
| retrofit | dependency_outdated/upgrade/config_drift | L4-L9 | config_drift で要 |
| scrum | user_feedback_iteration | Reverse fullback→Forward | — |
| research | tech_decision_required/adr_required | L1/L4 | — |
| screen-design | screen_requirement_gap/wireframe_missing | L2 | — |
| frontend-design | a11y/visual/token_drift/ux_feedback | L10 | — |
| **design-bottomup** | screen_addition_to_backend/backend_derived_screen | L3-L6（Discovery 合成経由） | — |

- **routing**（`route_signal_to_mode`）: signal→mode、最長一致優先。`evaluate_route_command` が route-config 違反（legacy-db/personal-path）block、escalation 13 語（auth/payment/pii/prod/migration 等）で approval 強制、`helix` 以外の command 名を排除。
- **design-bottomup**（harness net-new）: 確立 backend（data_entity/projection/cli_command）→ FE 要件 derive（各画面×L3/L5/L6 slot）→ gap 検出（has_body=false を SLOT_SIGNAL、coverage≠substance）→ Discovery(entry=design_uncertain)へ合成 → Forward 降下。新 mode を作らず既存 routing に乗る。
- **forward_return**: 駆動 PLAN は forward_return を**機械契約**として持つ（散文依存をやめる）。欠落 = violation（`drive-model-passage` 相当）。

## 5. gate 契約（capture §6 — G0.5-G14）

- **静的 gate**（`evaluate_static_gate`、決定論・AI 不使用）: G1-G7。G7 = pair-freeze + impl-plan-trace + oracle-test-trace + coverage≥80% の AND。
- **judgment gate**（`JUDGMENT_GATES = G0.5/G2/G4/G5/G6/G7/R4`）: review tier = **cross_agent**(worker≠reviewer model)/**intra_runtime_subagent**(checklist 7=DOC/TST/COD/XR/DEP/DUP/MOD)/**human**。naive self-review 常時 block。サインオフ = G1/G3/G7/G11=PO、G4/G5/G6=TL。
- **標準 4 軸**（A1 DoD / A2 上流 trace 孤児0 / A3 V-pair 実在+双方向 / A4 sub-doc 整合）。Critical=0 → CONDITIONAL PASS。

## 6. auto-enroll rule engine（capture §6 — 11 rule 型、FR-18/FR-05 の実現機構）

新 doc が現れたら frontmatter 形状にマッチする全 rule が**自動適用**（lint 手書き不要）。各 rule 型は**純関数**（LLM/外部 API 不使用 = 決定論）。`gate-checks.yaml` が G_N の rule id 集合を宣言。

```
[1] doc registry      docs/** frontmatter 走査
[2] rule registry     関係の「型」ごとに 1 回実装した layer 非依存 rule
[3] auto-enroll       新 doc が現れたら frontmatter 形状にマッチする全 rule が自動適用 ← 核心
[4] gate 束ね         gate-checks.yaml が G_N で回す rule id 集合を宣言
[5] coverage map      どの doc/関係が検査済かを自動レポート
```

**11 rule 型**: `pair-exists` / `ref-resolves` / `trace-bidir` / `upstream-coverage`(孤児0) / `count-matches` / `id-format` / `dup-id` / `glossary-delta`(L0 §10 用語へ back-merge) / `dependency-drift`(実 import グラフ vs 期待 = ADR-002) / `asset-drift` / `backlog-format`。共通 signature `(registry: DocRegistry, params: RuleParams) -> RuleResult`（pure）。

## 7. 契約（DbC）/ config 差し替え

```
parse(path) -> Contract{kind, id, frontmatter, sections, forward_return?}
validate(Contract) -> list[Violation]
```
- **ensures**: validate を通った artifact は C2 が一意 table へ投影できる。違反は fail/warn 分離で findings へ。
- **config 差し替え**（charter Phase / FR-CFG-01）: HELIX 設定（workflow 群）を harness の workflow 契約形式へ差し替え → C6 契約を満たし C2 が DB 登録 → C3 detector が forward_return もれ検出。

## 検証

- AT-V3-10: frontmatter 契約違反 doc → detector 検出。AT-V3-11: forward_return 欠落の駆動 PLAN → 検出。
- 単体: 必須 field/ID/section 欠落の violation / 正常 artifact のパース→投影可能性 / auto-enroll rule の純関数性（同 input 同 output）/ 新 doc が gate-checks.yaml の rule 集合に自動 enroll。
