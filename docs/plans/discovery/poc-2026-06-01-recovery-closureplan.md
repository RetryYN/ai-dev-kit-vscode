---
plan_id: poc-2026-06-01-recovery-closure
title: "poc-2026-06-01-recovery-closure: Recovery closure event 冪等記録 + Forward 再開候補復元 (柱2 closure 閉ループ検証)"
kind: poc
layer: L1
drive: discovery
status: draft
created: 2026-06-01
owner: PM
plan_scope: action
parent_process: docs/plans/process/process-2026-06-01-plan-rule-closure.md
workflow: discovery
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 収束方針・Forward 昇格判断"
  - role: tl-advisor
    slot_label: "TL — closure event contract / module boundary 設計"
  - role: se
    slot_label: "SE — Recovery closure adapter 薄実装（PoC、承認後）"
  - role: dba
    slot_label: "DBA — mode_transition 物理 schema / idempotency（schema escalation 承認後）"
  - role: qa
    slot_label: "QA — PoC verify script(Bats/Pytest) 実装・冪等/復元 AC"
generates:
  - artifact_path: docs/plans/discovery/poc-2026-06-01-recovery-closureplan.md
    artifact_type: markdown_doc
  - artifact_path: verify/h-closure-01-recovery-closure-event---forwa.sh
    artifact_type: script
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/discovery-workflow.md
  - HELIX-workflows/helix-process/recovery-workflow.md
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
---

# Discovery PoC: Recovery closure event 冪等記録 + Forward 再開候補復元

> mode: Discovery（kind=poc、検証駆動）/ Sprint #1 / hypothesis **H-CLOSURE-01**
> 正本: [discovery-workflow.md](../../../HELIX-workflows/helix-process/discovery-workflow.md)
> 位置づけ: **柱2（駆動 workflow 配線）の closure 閉ループが未実装**という穴を、Recovery 1 本の closure を end-to-end で検証して潰し、confirmed 後に Forward（L4 closure 設計）へ昇格する前段。**本 PLAN は doc/整理/設計提案/検証計画まで**（PoC 実装・schema は escalation 承認待ち、§8）。

## §1 背景・問題設定（なぜ Discovery か）

2026-06-01 実態調査 + tl-advisor pivot 判定:

- **柱2 配線は recommendation 止まり**: `cli/lib/route_engine.py`（701 行）の Action 型は `suggest_only` / `immediate_plan_draft` / `discovery_first` / `emergency_routing`。`helix route` は `eval`/`suggest`/`list-signals` のみ = detection signal → 推奨コマンド/plan hint を出すだけ。**workflow 完了 → closure event → V-model DB 収束 → Forward 再接続の閉ループは未実装**（中央 closure engine 不在）。
- **契約はあるが実体がない**: `FR-EVT-01` / `helix mode close --target-layer <Lx>` / `idempotency_key` は L1 技術要求 / L3 機能要件に定義済み。だが L4/L5 データ設計に `mode_transition` テーブルが無く、`helix mode close` の実装も無い。= **L4-L6/L7 実体と中央配線の欠落**。
- **TL pivot 判定（2026-06-01, changes_required→pivot 支持）**: gate（柱1）は V-model 収束を守る検問。検問対象の遷移・closure・Forward 復帰が動かない状態で gate を先に強めると未完成の配線を正本化する。**closure 閉ループを先に検証・配線せよ**。
- 不確実なのは「closure event モデルが Recovery で実際に閉じるか（冪等記録 + Forward 復元）」。これは Discovery（検証駆動）の対象。

## §2 仮説（H-CLOSURE-01）

> **Recovery 完了時に closure event（`source_workflow` / `target_forward_layer` / `closure_reason` / `idempotency_key`）を `mode_transition` へ冪等記録し、そこから Forward 再開候補を機械復元できる。**

なぜ Recovery を第一実例にするか（TL）: ①`helix route` / `helix recover` / recovery-workflow の既存実装があり最小改修で end-to-end を組める ②AI 暴走収束という HELIX 自身の失敗モードに直結 ③Forward 復帰先（再開ポイント）を検証しやすい。

## §3 ワークフロー整理: closure 共通モデル（設計の出発点）

9 駆動 workflow の「逸脱 → Forward へ戻す」を、統一 closure event モデルで整理する。closure event は次の最小フィールドで表す:

| フィールド | 意味 |
|---|---|
| `source_workflow` | どの駆動 workflow の完了か（recovery / reverse / incident / …） |
| `target_forward_layer` | Forward のどの L へ戻すか（再接続先） |
| `closure_reason` | 収束理由 / 採用結果（confirmed / resolved / converged 等） |
| `idempotency_key` | 同一 closure の二重記録を防ぐ冪等キー |
| `payload`（任意） | 戻し先で必要な最小コンテキスト（PLAN id 等） |

各駆動 workflow の戻し先（Forward 接続先、`HELIX-process-L0-L14.md` Workflow 入口表より）:

| workflow | target_forward_layer（戻し先） |
|---|---|
| Discovery | L1 / L3 / L4-L6 |
| Reverse | L1 / L3 / L4 / L7 / L8-L11 |
| Incident | L1 / L3 / L4-L6 / L14 |
| Add-feature | L4-L7 |
| Refactor | L7 |
| Retrofit | L4-L9 |
| Research | L1 / L4 |
| **Recovery（本 PoC 対象）** | 再開ポイントから L0-L14 |
| Scrum | Reverse fullback 経由 Forward |

→ closure event はこの「戻し先」を機械可読にし、`transition_history` / V-model DB へ収束させる共通機構。本 PoC は Recovery 行のみを実体化して検証する。

## §4 closure 設計提案（Discovery grade — PoC で検証、confirmed 後に L4 で正式凍結）

1. **closure event contract**: §3 の 5 フィールド。`idempotency_key` = `hash(source_workflow + plan_id + closure_reason + 単調時刻 bucket)` 等で同一 closure の二重記録を排除。
2. **`mode_transition` データ構造（概念、L4/L5 で正式化）**: 1 closure = 1 row。列 = id / source_workflow / target_forward_layer / closure_reason / idempotency_key（unique）/ created。既存 `transition_history` との関係（吸収 or 併設）は L4 で判断。
3. **配線（end-to-end）**: `route`（signal 推奨）→ `recover`（Recovery 起動）→ Recovery 完了 → **closure adapter** が closure event を `mode_transition` へ冪等記録 → そこから Forward 再開候補（target_forward_layer + payload）を復元。
4. **実装単位（TL）**: いきなり中央 `helix mode close` を作らず、**まず Recovery 専用の薄い closure adapter** を作る。共通化（全 workflow 対応の `helix mode close`）は本 PoC 採用後に判断。

### §4.5 closure 記録先 SSoT 分析（2026-06-01 実態調査、L4 で確定・schema escalation 承認後）

closure event の記録先テーブル名が分裂している（本 session 実態調査）:

| 名称 | 出現 | 位置づけ |
|---|---|---|
| `mode_transition` | コード（`cli/lib/vmodel_loader.py` / `cli/config/vmodel-semantics.yaml`）+ L1/L3 要件 doc | **de-facto canonical**（テーブル実体は未作成） |
| `transition_history` | HELIX Core / process doc | 概念語 |
| `workflow_transition` | `concept.md` 1 件 | stray（要収束） |
| `reverse_local_loops`（`target_forward_plan`/`target_forward_layer`） | `helix_db.py` 実テーブル | 既存の per-workflow 戻り先記録機構（scrum_local_loops も同型） |

**L4 判断事項（schema escalation 承認後）**: ①中央 `mode_transition` に集約 / ②`reverse_local_loops` 型 per-workflow loop を一般化 / ③`transition_history` に吸収。**lean = `mode_transition`**（コード+大半の doc で既使用。`workflow_transition` は alias 収束、`transition_history` は概念語として併存可）。idempotency は Saga の Retryable/Pivot transaction パターン（Forward 復帰 = Pivot = 不可逆コミット境界、web検索 精読）で設計。

> **escalation**: `mode_transition` テーブル新設 = schema migration = ユーザー承認が entry 条件（`HELIX_RUNTIME_RULES §10`）。本 §4.5 は**設計分析のみ**（実装は承認後）。

## §5 PoC 検証計画（検証条件先置き）

- verify script: `verify/h-closure-01-recovery-closure-event---forwa.sh`（`helix discovery backlog add` で stub 生成済、実装は §8 escalation 後）。
- acceptance（TL、AC-FR-07 相当）:

| AC | 検証内容 | 合格基準 |
|---|---|---|
| AC-1 冪等 | 同一 closure event を 2 回送る | `mode_transition` の row が増えない（idempotency_key で弾く） |
| AC-2 target 保存 | closure に target_forward_layer を含めて記録 | 記録後に target_forward_layer が正しく読み出せる |
| AC-3 復元 | route → recovery → closure → Forward candidate | 1 コマンド列で Forward 再開候補が復元・表示できる |

- fail-close（discovery-workflow §基本フロー）: `confirmed` は verify script 成功が必須。verify 失敗時は sprint を completed にしない。

## §6 採用 / 棄却基準

| 判定 | 条件 | 次アクション |
|---|---|---|
| **confirmed** | verify script 成功 + AC-1〜3 全充足 | §7 Forward 昇格（L4 closure 設計凍結へ） |
| **rejected** | closure モデルが Recovery で閉じない（冪等 or 復元が原理的に不可） | 学びを記録、closure event モデルを再設計 |
| **pivot** | 部分成立（例: 冪等 OK だが復元に追加情報が要る） | 仮説修正して次 sprint |

## §7 Forward 昇格先（confirmed 後）

PoC をそのまま本実装にせず、Forward へ昇格する（discovery-workflow §Forward 接続）:

- **L1/L3**: `FR-EVT-01` の closure 契約を実体に合わせて補強。
- **L4**: `docs/plans/L4/L4-helix-workflows-closure-connection-designplan.md`（closure 設計を凍結。mode_transition schema + closure adapter contract + Forward 再接続）。
- **L5/L6**: 物理データ設計（DDL）+ 機能設計（単体テスト設計、関数粒度）。
- **L7**: 実装（Codex se/dba 委譲）。
- verify script は **L6 機能設計 / 単体テストの回帰**として `verify/` に残す。
- 横展開（2 本目）: Recovery で確立した closure モデルを Incident / Reverse / Add-feature へ一般化検証（本 PoC 採用後）。

## §8 委譲・escalation 待ち（本 PLAN では着手しない）

- **PoC 実装**（Recovery closure adapter / verify script 実装）= **Codex se 委譲**（PM=Opus は実装しない）。
- **`mode_transition` テーブル追加 = schema migration = HELIX escalation 項目**（`HELIX_RUNTIME_RULES §10`）。**ユーザー明示承認後に着手**。DBA 委譲。
- 本 Discovery PLAN は **doc / 整理 / 設計提案 / 検証計画まで**。実装・schema は user 承認待ちで停止する。

## §9 スコープ規律（過剰起票回避）

- Discovery は **Recovery 1 本に限定**（TL P2: 全 workflow への拡大は過剰起票）。
- closure 共通モデル（§3）の他 workflow 行は「整理」であり、実体化は Recovery PoC 採用後の 2 本目以降。
- 本 PoC が closure 配線（柱2）の最小の動く単位。これが confirmed → L4 設計 → L7 実装 と進んで初めて、柱1 gate 自動化を載せる土台ができる。

## §10 進捗

- [x] hypothesis backlog 登録（`helix discovery backlog add H-CLOSURE-01`、verify stub 生成）
- [x] closure 共通モデル整理 + 設計提案（§3-§4）
- [x] PoC 検証計画 + 採用/棄却基準（§5-§6）
- [ ] **PoC 実装**（Codex se/dba、schema escalation 承認待ち — §8）
- [ ] `helix discovery verify` → `decide`
- [ ] confirmed 後 Forward 昇格（L4 closure 設計凍結）
