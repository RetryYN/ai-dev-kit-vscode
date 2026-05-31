# PLAN モデル: Process ⊃ Action（行程と実行の親子）

> **配置（G 正本）**: 本書が PLAN モデルの**規範正本（定義本文）**。process model BC（`HELIX-workflows/`）に属し、消費側へ配布される運用概念。
> **用語ミラー（P）**: `docs/v2/L0-helix-workflows/concept.md §12 Glossary` に `Process Plan` / `Action Plan` / `plan_scope` を SSoT 用語として載せる（term / schema field / grep pattern / implementation_status のみ。**定義本文は二重化しない**）。`helix/` governance は本書を参照するだけで再定義しない。
> **出自**: 2026-06-01 ユーザー確定モデル + tl-advisor 条件付き推奨。第一インスタンス = [process-2026-06-01-plan-rule-closure.md](../../docs/plans/process/process-2026-06-01-plan-rule-closure.md)。

## 1. 区別の軸（Process と Action）

PLAN は「Forward 用 / 駆動用」の横並び 2 種**ではない**。**Process ⊃ Action の親子（縦の入れ子）**で扱う。

- **Process Plan（親 = 行程）**: 駆動モデル・工程の**連鎖**を記録する。「今回どう進めるか」。例: 内部監査 → web検索 → Discovery → Reverse。**駆動モデルが連続するとき、その繋がりが Process**。
- **Action Plan（子 = 実行）**: **単一ワークフロー内部の収束ループ**を記録する。例: Discovery 内部 `仮説 → 実装 → 検証 → 改善 →（収束 = decide）`。**駆動モデルの収束地点を決めるのが Action**。

## 2. 親子規律（守るべき不変条件）

1. **親子のみ（`process ⊃ action[]`、1 段）**。`process が process を内包する`多段ネストは禁止（追跡が崩れる）。初期 contract は 1 段。
2. **Process は Forward の代替正本にならない**。Process Plan は `forward_return` を**必須**とし、Forward へ戻す接続先を持たずに完了扱いにできない（HELIX Core 絶対原則 = 駆動は枝で必ず Forward へ戻す）。
3. **L単位は Process を兼ねる**。L PLAN（`L<NN>-…plan`）は既存 V-model 正本のまま扱い、`plan_scope` を**強制しない**。L の中に派生ワークフローが出たときだけ、その Action Plan を `parent_process` でぶら下げる。
4. **単独立ち上げは Process 先行**。親 Process がない駆動立ち上げは、Process Plan（行程）から設計し、その下に個別 Action Plan を設計する。

## 3. 2 つの結合ケース

- **内包型**: 親 Process = L単位（既存）。L PLAN の中に派生した駆動モデルの **Action Plan だけ**を `parent_process: docs/plans/L<NN>/…` で繋ぐ（L PLAN 自体は Process を兼ねるので新規 Process Plan は作らない）。
- **単独型**: 親 Process = 新規 **Process Plan**。`docs/plans/process/` に置き、`contains_action_plans` で子 Action を列挙、`forward_return` で戻し先を宣言。

## 4. step type と workflow 名（混同禁止）

Process の連鎖を構成する step には 2 種がある:
- **workflow step**: HELIX 駆動モデル名（discovery / reverse / recovery / incident / add-feature / refactor / retrofit / research / scrum）。**Action Plan を持てる**。
- **非 workflow step**: 監査・web検索 等の準備行為。Action Plan を持たない（必要なら research workflow に正規化）。`内部監査` / `web検索` はこれ。

→ `workflow_chain` には両方が並ぶが、**Action Plan を持てるのは workflow step のみ**。step type と workflow 名を混同しない。

## 5. PLAN frontmatter contract（最小、tl-advisor 推奨）

### Process Plan
| field | 値 | 必須 |
|---|---|---|
| path | `docs/plans/process/process-YYYY-MM-DD-<topic>plan.md` | ✓ |
| `plan_id` | `process-YYYY-MM-DD-<topic>` | ✓ |
| `plan_scope` | `process` | ✓ |
| `workflow_chain` | string（将来 `workflow_steps[]` へ移行） | ✓ |
| `contains_action_plans` | list[path] | ✓ |
| `forward_return` | string（Forward 戻し先。Core 必須） | ✓ |
| 共通 | `title` / `kind` / `layer` / `drive` / `status` / `agent_slots` / `generates` / `dependencies` | 共通 |

### Action Plan
| field | 値 | 必須 |
|---|---|---|
| path | `docs/plans/<workflow>/<workflow>-YYYY-MM-DD-<topic>plan.md` | ✓ |
| `plan_id` | `<workflow>-YYYY-MM-DD-<topic>` | ✓ |
| `plan_scope` | `action` | ✓ |
| `parent_process` | `docs/plans/process/…md`（内包型は L PLAN path） | ✓ |
| `workflow` | discovery / reverse / recovery / … | ✓ |
| `action_loop` or `acceptance` | 収束条件 | ✓ |
| `forward_return` or `decide_target` | optional（**closure schema 名は使わない**） | - |

> **closure 契約の分離（tl-advisor 必須条件）**: `mode_transition` / `closure_reason` / `target_forward_layer` / closure event schema を PLAN validator の必須 contract に**焼かない**。これらは closure PoC（H-CLOSURE-01）confirmed 後に別 PLAN で L4/L5 凍結する。本モデルは PLAN の構造（行程 / 実行の親子）だけを規定する。

### 命名の整理（命名分裂を防ぐ）
| path | 種別 | plan_scope |
|---|---|---|
| `docs/plans/L<NN>/L<NN>-…plan` | Forward 工程 PLAN（L単位 = 暗黙 Process） | （強制しない） |
| `docs/plans/process/process-…plan` | 単独 Process Plan（親） | `process` |
| `docs/plans/<workflow>/<workflow>-…plan` | Action Plan（子、駆動モデル別） | `action` |
| `docs/plans/PLAN-NNN…` | V1 legacy（`is_reference: true`、V2 strict 対象外、書き直し前提） | - |

## 6. validator / hook / lint への落とし込み（実装は Codex 委譲、本書は contract）

1. `_classify_plan_format`: `process` / `action` / V1-legacy / V2 / `invalid` を分類（`unknown` 解消）
2. 親子リンク検証: action の `parent_process` 存在、process の `contains_action_plans` path 存在（**warning から開始**）
3. `plan_lint` ↔ `plan_validator`: `VALID_PLAN_SCOPES` + workflow enum を同期、**drift test を追加**
4. `helix plan lint --strict-frontmatter`: required fields 欠落を fail-close
5. design-doc hook matcher: 現行命名（L / process / workflow）を意図的に include / exclude

## 7. 業界標準との対応（anti-corruption mapping、2026-06-01 web検索 精読）

業界の「制御層 ⊃ 実行層」二層分離（Temporal Workflow/Activity・Airflow DAG/Task・Argo Orchestration/Work template・GitHub Actions・ISO 9001・OODA・Saga）と Process⊃Action は整合する。HELIX 用語を業界語へ写す:

| HELIX | 業界の対応語 | 性質 |
|---|---|---|
| **Process（親=行程）** | Orchestration template (Argo) / Workflow (Temporal) / DAG (Airflow) / Procedure (ISO 9001 how-sequence) | 制御グラフ・連鎖を定義し計算しない層 |
| **Action（子=実行）** | Activity (Temporal) / Task (Airflow) / Work template (Argo) / Work Instruction (ISO 9001) / Retryable transaction (Saga) | 単一の反復・冪等実行 |
| **forward_return / 収束** | **Pivot transaction (Saga)** | 本線への不可逆コミット境界（= Core「Vモデルへ戻さねば完了でない」の設計根拠） |
| **収束条件** | join condition / `none_failed_min_one_success` (Airflow) | 分岐合流の成功判定 |

設計上の注意（web検索 由来）:
- **命名の精度**: ISO 9001 の「Process」は最上位（why/what）。HELIX の Process は「連鎖（how-sequence）」寄りで ISO の Procedure に近い。外部混同を避けるため Glossary で「行程の連鎖」と精密定義する（TL P3 整合）。
- **収束条件の明示**: 複数 workflow が本線へ合流する場合、素朴な `all_success` 合流は skip→fail 伝播の罠（Airflow 公式）。Action の収束条件と Process の合流条件を明示する。
- **2 段固定の妥当性**: GitHub Actions(10 段)/Jira の実態でも深い入れ子は追跡困難。Process⊃Action の 1 段固定（§2-1）は追跡性で正しい。

## 8. 関連

- 第一インスタンス: [process-2026-06-01-plan-rule-closure.md](../../docs/plans/process/process-2026-06-01-plan-rule-closure.md)
- 用語ミラー: [concept.md §12 Glossary](../../docs/v2/L0-helix-workflows/concept.md)
- 起票コマンド: [docs/commands/plan.md](../../docs/commands/plan.md)
- workflow 別 entry: `HELIX-workflows/helix-process/*-workflow.md`
- HELIX Core 絶対原則（駆動は枝で Forward へ戻す）: [helix/HELIX_CORE.md](../../helix/HELIX_CORE.md) §0/§3
