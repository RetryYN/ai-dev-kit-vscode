# Phase H Agent Transformation 整理計画

最終更新: 2026-05-14  
作成: Research (Codex)  
対象: L1 `FR-AT01`〜`FR-AT05`  
位置づけ: Phase H の実装前に、agent/orchestration/cost/tool-contract の散在を実行可能レベルで整理する計画

---

## 概要

Phase H の主題は、新機能追加そのものではなく、既に存在する `helix-codex` / `helix-claude` / `skill_dispatcher` / budget / contract registry / detector 周辺の散在責務を、段 2 基盤として再編することにある。

現状の観測:

- agent 実行正本は `cli/roles/*.conf` と `cli/config/models.yaml` に寄っている一方、実行経路は `cli/helix-codex`, `cli/helix-claude`, `cli/lib/skill_dispatcher.py`, `cli/lib/agent_policy_guard.py` に分散している。
- cost guard は `cli/lib/budget.py`, `cli/lib/budget_cli.py`, `cli/lib/model_fallback.py`, `cli/helix-codex` の fallback 分岐に分散している。
- `routing_decisions` は detector 側が参照前提だが、本体 schema には未収載で、agent routing の正本が曖昧。
- contract registry は YAML import 中心で、`OpenAPI fragment` を一級 command として出力する経路がない。
- `agent_registry` は L1 要件上は必要だが、現 schema / runtime とも未実装。

結論:

- **Option A: wrapper 継ぎ足し** は短期改修としては容易だが、責務の再散在を招くため非推奨。
- **Option B: BaseAgent / LLM Router / Cost Guard / Contract Export / Tool Registry を段階導入** が最も整合的で、L1 要件・監査結果・互換性制約を同時に満たしやすい。
- **推奨度: 高**。ただし scope は広く、Phase 2/3/4 の先行整理完了後に着手するのが妥当。

---

## 選択肢

| 選択肢 | 内容 | メリット | デメリット | 推奨度 |
|---|---|---|---|---|
| A | `cli/helix-codex` / `cli/helix-claude` に都度分岐を足し続ける | 最小差分で局所対応できる | routing, fallback, cost, tool 制約がさらに分散する | 低 |
| B | BaseAgent / LLM Router / Cost Guard を基盤化し、wrapper は shim 化する | 責務境界が明確になる。監査・テスト・将来拡張がしやすい | 初期設計コストが高い。移行順序を誤ると互換性を壊す | 高 |
| C | 先に DB schema (`agent_registry`, `routing_decisions`) だけ入れて runtime は後追い | v21/v22 migration の見通しは立つ | runtime が追従しないと空運用を再生産する | 中 |
| D | `helix skill chain` を agent 正本に寄せ、wrapper は薄くする | skill/recommendation と routing の接続を強化しやすい | Codex/Claude 実行差分や cost 制御を skill 層へ持ち込みすぎる | 中 |

推奨は **B を主軸にし、C を同一フェーズ内の下支えとして併走** させる構成である。

---

## ソース

- 要件:
  - `docs/v2/L1-REQUIREMENTS.md` FR-AT01〜05
- 監査:
  - `docs/v2/A-audit/hooks-commands-subagents.md`
  - `docs/v2/A-audit/perf-cost-audit.md`
  - `docs/v2/A-audit/db-schema-current.md`
  - `docs/v2/A-audit/audit-summary.md`
  - `docs/v2/A-audit/capability-inventory.md`
  - `docs/v2/A-audit/capability-matrix.md`
- 実装:
  - `cli/helix-codex`
  - `cli/helix-claude`
  - `cli/config/models.yaml`
  - `cli/lib/model_registry.py`
  - `cli/lib/budget.py`
  - `cli/lib/budget_cli.py`
  - `cli/lib/model_fallback.py`
  - `cli/lib/contract_registry.py`
  - `cli/lib/agent_policy_guard.py`
  - `cli/lib/helix_db.py`
  - `cli/lib/detectors/axis_14_orchestration.py`
  - `cli/lib/detectors/registry.py`

不確実性:

- `routing_decisions` は detector/tests では前提化されているが、本体 schema に未収載のため、Phase H で新設するか既存 telemetry へ吸収するかは最終設計判断が必要。
- `BaseAgent` 導入後に Claude 側実行を Python class にどこまで寄せるかは、bash wrapper の責務境界次第で変わる。

---

## 推奨

Phase H では、以下の原則で整理することを推奨する。

1. `cli/helix-codex` / `cli/helix-claude` は **UI/CLI shim として維持** し、agent 判断・model 解決・fallback・cost guard の本体は Python ライブラリへ降ろす。
2. `BaseAgent` は「抽象 OO フレームワーク」ではなく、**role 実行契約の最小共通層** として導入する。
3. `LLM Router` は routing の単一正本とし、`model_registry`, `model_fallback`, `agent_policy_guard`, `routing_decisions` の交点になるよう設計する。
4. `Cost Guard` は予算取得・閾値判定・fallback 提案・event 記録を 1 箇所へ集約し、80%/100% の動作を明示する。
5. `OpenAPI fragment export` は FE/BE 契約連携の入口として扱い、単なる YAML dump ではなく `contract_entries` 再利用を前提に設計する。
6. `Tool Registry` は security hardening と orchestration audit の両方を支えるため、`allowed_tools` を schema だけで終わらせず runtime enforcement まで含める。

---

## §1 FR-AT01: BaseAgent 統一 IF

### 1.1 目的

- wrapper と role 実行契約を分離し、Codex / Claude / verify / skill などの agent 実行単位を共通の抽象で扱えるようにする。
- `agent_kind`, `step`, `step_ids` をクラス定義時に強制し、曖昧な agent 種別を減らす。

### 1.2 現状

- `helix-codex` と `helix-claude` は bash entrypoint に強く寄っている。
- `agent_policy_guard.py` は role/engine/task の整合性だけを見ており、agent 実体との対応表を持たない。
- `hooks-commands-subagents.md` 監査では role/agent/subagent の多重化が Phase H 論点として挙がっている。

### 1.3 選択肢

| 案 | 内容 | メリット | デメリット | 推奨度 |
|---|---|---|---|---|
| A | bash wrapper のまま metadata だけ別管理 | 移行が軽い | 強制力が弱く drift しやすい | 低 |
| B | `BaseAgent` 抽象 class を導入し、wrapper はその adapter とする | 契約の強制とテストがしやすい | 初期の接着コードが必要 | 高 |
| C | role conf に agent metadata を全部押し込む | source-of-truth を 1 箇所に寄せやすい | 実行ロジック側の型保証が弱い | 中 |

### 1.4 推奨構造

- 新設: `cli/lib/base_agent.py`
- 役割:
  - `agent_kind`
  - `step`
  - `step_ids`
  - `provider`
  - `role`
  - `permission_mode`
  - `allowed_paths`
  - `allowed_tools`
- `__init_subclass__` で以下を fail-close:
  - `agent_kind` 未指定
  - `step` 未指定
  - `step_ids` 空
  - `agent_kind` 重複
- 生成責務:
  - CLI 解析後の normalized task context を受ける
  - 実行前 validation を行う
  - router に dispatch request を渡す

### 1.5 migration 対象

- 第1群:
  - Codex 実行 wrapper
  - Claude 実行 wrapper
- 第2群:
  - verify agent
  - skill dispatch 経由 agent
  - advisor role
- 第3群:
  - 旧 `.claude/agents/*` 互換 metadata

---

## §2 FR-AT02: LLM Router 集約

### 2.1 目的

- model 解決、provider 選択、fallback、role 固有制約、routing telemetry を単一入口へ統合する。

### 2.2 現状

- `cli/helix-codex` が model 解決、consent、fallback を大量に内包している。
- `cli/helix-claude` は permission/disallowed tools を独自に解釈している。
- `model_registry.py`, `model_fallback.py`, `agent_policy_guard.py` が別々に存在する。
- `routing_decisions` は detector 側で前提化されるが runtime 正本がない。

### 2.3 統合前後の比較

| 観点 | 統合前 | 統合後 |
|---|---|---|
| role → model 解決 | `helix-codex`, `helix-claude`, `model_registry.py` に分散 | `llm_router.py` の `resolve_route()` に集約 |
| provider 判定 | wrapper ごとに固定寄り | route result に `provider=codex|claude_code` を返す |
| fallback | `helix-codex` と `model_fallback.py` に分散 | router が first-class の route chain を返す |
| tool/path 制約 | role conf 読み + wrapper ロジック | agent metadata + router policy で合成 |
| telemetry | `invocation_log` はあるが routing 正本なし | `routing_decisions` へ route reason を永続化 |

### 2.4 推奨構造

- 新設: `cli/lib/llm_router.py`
- 主要 API:
  - `resolve_route(task_context, agent) -> RouteDecision`
  - `resolve_fallback_chain(route_decision) -> list[RouteDecision]`
  - `record_routing_decision(route_decision, db)`
- `RouteDecision` に含める項目:
  - `agent_kind`
  - `role`
  - `provider`
  - `primary_model`
  - `fallback_models`
  - `reason`
  - `cost_guard_state`
  - `allowed_paths`
  - `allowed_tools`
  - `plan_id / task_id / wbs_id`

### 2.5 実装順

1. route payload の型定義
2. `model_registry.py` 呼び出しの集約
3. `model_fallback.py` の router 経由化
4. `helix-codex` から role/model 解決部を剥離
5. `helix-claude` から permission/disallowed 読み取りの共通部を剥離
6. `routing_decisions` persist 追加

---

## §3 FR-AT03: Cost Guard 集約

### 3.1 目的

- Claude/Codex 予算、role fallback、warning/stop しきい値、event 記録を一本化する。

### 3.2 現状

- `budget.py` が予算取得と予測を持つ
- `budget_cli.py` が表示と simulate を持つ
- `model_fallback.py` が fallback 提案を持つ
- `helix-codex` が実行時 fallback を持つ
- `perf-cost-audit.md` では `budget_events=0`, `cost_log.tokens_est=0`, `Codex source=unavailable` がギャップとして指摘されている

### 3.3 選択肢

| 案 | 内容 | メリット | デメリット | 推奨度 |
|---|---|---|---|---|
| A | 現状モジュールを維持し、ログだけ追加 | 差分が少ない | 判断ロジックが分散したまま | 低 |
| B | `cost_guard.py` へ取得・判定・記録・fallback 理由生成を集約 | 80/100 の一貫動作を定義しやすい | 呼び出し側の差し替えが必要 | 高 |
| C | budget CLI を正本にして wrapper が subprocess 呼び出し | 実装は簡単 | 実行時オーバーヘッドが大きい | 低 |

### 3.4 推奨構造

- 新設: `cli/lib/cost_guard.py`
- 機能:
  - `collect_budget_snapshot()`
  - `evaluate_thresholds(snapshot)`
  - `suggest_route_adjustment(snapshot, role, model)`
  - `record_budget_event(snapshot, action)`
- 閾値定義:
  - 80%: warning + fallback 推奨 + event 記録
  - 100%: stop or stronger fallback + event 記録
- `weekly_used_pct` は Claude/Codex 共通の正規化フィールドに揃える

### 3.5 受入条件

- 80% 到達で warning と `budget_events` insert が発生
- 100% 到達で stop または policy fallback が発生
- `helix budget status` と runtime decision が同じ閾値解釈になる

---

## §4 FR-AT04: OpenAPI fragments 出力 CLI

### 4.1 目的

- `contract_entries` から FE/BE 契約断片を出力し、import/export の基準経路を作る。

### 4.2 現状

- `contract_registry.py` は `docs/features/**/D-API/*.yaml` の scan と DB insert が中心
- export 経路はない
- `audit-summary.md` でも FR-AT04 は「contract export を一級 command にする必要」と整理されている

### 4.3 推奨構造

- 追加 command:
  - `helix contract export --format openapi --fragment <name>`
- 実装候補:
  - `cli/lib/contract_export.py`
  - `cli/helix-contract` または既存 contract command への subcommand 追加
- fragment 単位:
  - path group
  - component schema group
  - plan / feature / drive 単位

### 4.4 import 経路

- BE:
  - `D-API/*.yaml` → `contract_entries` → export
- FE:
  - exported fragment を state-events / generated client / mock へ import

---

## §5 FR-AT05: Tool Registry schema

### 5.1 目的

- role/agent ごとの tool 使用制限を DB schema と runtime の双方で扱えるようにする。

### 5.2 現状

- `models.yaml` に `codex_disallowed_tools`, `disallowed_tools`, `allow_paths` はある
- しかし agent ごとの `allowed_tools` 正本はない
- `agent_registry` table 自体が未実装

### 5.3 推奨 schema

- `agent_registry`
  - `agent_kind`
  - `role`
  - `provider`
  - `model`
  - `thinking`
  - `allowed_paths`
  - `allowed_tools`
  - `cost_budget`
  - `status`
  - `updated_at`

### 5.4 runtime 連携

- `BaseAgent` が registry を読む
- `LLM Router` が route 決定時に `allowed_tools` を合成
- 実行後に tool 使用実績を audit log へ残す

### 5.5 audit log

- 新設または既存 table 拡張の候補:
  - `invocation_log` に `tool_policy_snapshot`
  - 別 table `tool_execution_audit`
- 最低限記録するもの:
  - `agent_kind`
  - `role`
  - `tool_name`
  - `allowed_by_policy`
  - `decision_source`
  - `timestamp`

### 5.6 受入条件

- agent ごとに許可 tool 一覧が機械可読で取得できる
- deny された tool 呼び出しが監査できる
- security / orchestration detector が参照できる

---

## §6 移行 step

### Phase H.1: BaseAgent + LLM Router 統合

1. `base_agent.py` 新設
2. Codex / Claude wrapper を adapter 化
3. `llm_router.py` 新設
4. model/fallback/path/tool 制約の route payload 化
5. `routing_decisions` の保存方式を確定

### Phase H.2: Cost Guard 集約

1. `cost_guard.py` 新設
2. `budget.py` / `model_fallback.py` の判断責務を移譲
3. 80%/100% event 記録追加
4. `helix budget status` と runtime の整合試験

### Phase H.3: OpenAPI + Tool Registry

1. `agent_registry` schema 実装
2. `allowed_tools` runtime enforcement
3. contract export 実装
4. FE/BE import 経路の接続

---

## §7 既存散在 code との互換性

- `cli/helix-codex` と `cli/helix-claude` は維持する
- 既存 option:
  - `--approved`
  - `--consent`
  - `--allowed-files`
  - `--fallback-model`
  - PMO 向け execute/dry-run
  は互換維持する
- user 視点では command 名、基本引数、summary 形式、承認規律を壊さない
- 破壊変更は内部実装に限定する

互換性ガード:

- wrapper は当面 shim + adapter として残す
- route 決定の結果は旧挙動との差分ログを一時的に残す
- 旧 `.claude/agents/*` はすぐ削除せず Phase J まで互換資産として保持する

---

## §8 依存関係

- Phase H は以下を前提とする:
  - Phase 2 の V-model 定義固定
  - Phase 3 の schema 方針固定
  - Phase 4 の detector / fail-close 方針固定
- 理由:
  - router と tool policy は gate/detector 仕様に依存する
  - cost guard event は DB schema / observability 方針に依存する
  - contract export は contract registry / FE 連携方針に依存する

したがって、**Phase H は晩段配置** が妥当である。

---

## §9 期待効果

- agent 関連 code の責務が `wrapper / agent / router / guard / registry` に分離される
- cost / token / fallback の判断が単一ロジックで説明可能になる
- `routing_decisions`, `budget_events`, `allowed_tools` により監査可能性が上がる
- OpenAPI fragment export により FE/BE 契約の再利用性が上がる
