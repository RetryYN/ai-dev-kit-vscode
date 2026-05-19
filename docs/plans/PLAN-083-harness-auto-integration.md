---
plan_id: PLAN-083
title: "PLAN-083: Harness 自動統合 (PreToolUse 自動 fire + Stop 自動 release + session_id 連携)"
status: completed
size: M
drive: be
created: 2026-05-17
owner: PM
phases: L1, L2, L3, L4
gates: G1, G2, G3, G4
related_plans:
  - PLAN-078 (agent_slots v28、fire/release 基盤)
  - PLAN-080 (Harness Monitoring v30、harness_check_events + 2 hooks)
  - PLAN-081 (Stop-hook Phase 1、handover_auto_dump + helix-stop-hook)
  - PLAN-082 (PLAN-076/077 機械化、agent_mandatory.audit_phase + sprint_lint)
related_memories:
  - project_2026_05_17_5plan_parallel_session
---

# PLAN-083: Harness 自動統合

## 1. 背景

PLAN-078/080/081/082 で agent_slots / harness_check_events / handover_auto_dump / agent_mandatory が個別実装されたが、Opus / Codex / Claude Code subagent の起動時の **自動 fire/release** が未統合。現状:

- 手動: `cli/helix-agent fire` を Bash で呼ぶ
- 半自動: `cli/helix-codex` wrap で Codex 起動時のみ fire/release 自動 (PLAN-078)
- **未実装**: Claude Code Agent tool 経由の subagent (pmo-sonnet / pdm-* 等) 起動時の fire

結果: `agent_mandatory.audit_phase()` で subagent 呼び出しが捕捉されず、PLAN-082 の subagent_audit advisory が常に "missing" を返す。

### 1.1 ユーザー指摘 (PLAN-080 trigger 再掲)

> 「スロット状況を動的にチェックする管理する方法は？ヘリックス自体の動きとかも忘れて進められがちだし、そこがハーネスとして重要な気がするんだけど？」

PLAN-080 で 3 軸 (Pull/Push/Audit) を確立、PLAN-083 で **自動化** (Opus / Codex / Agent tool の起動を hook で機械的に捕捉) を完成させる。

## 2. 目的

Claude Code Agent tool / Bash (Codex 経由) を **自動的に agent_slots に fire/release 記録** する。これにより:
- `agent_mandatory.audit_phase()` が実 session の subagent 呼び出しを正確 audit
- PLAN-082 の subagent_audit advisory が実用化される
- harness_monitor.get_active_status() が real-time の slot 数を返す

## 3. スコープ

### 3.1 in-scope (M サイズ想定)

#### Phase 2: PreToolUse hook で Agent tool 自動 fire
- `.claude/hooks/pretooluse-agent-fire.sh` 新規
- Agent tool 呼び出しを stdin JSON から検出 → subagent_type 抽出 → agent_slots に fire
- session_id は HELIX_SESSION_ID env から取得 (なければ UUID 生成)

#### Phase 3: Stop hook 拡張で running slot 自動 release
- `cli/helix-stop-hook` に「session 終了時に session_id の running slot を全 cancelled で release」追加
- handover_auto_dump と統合 (release 件数を CURRENT.json に記録)

#### Phase 4: session_id 自動検出
- `cli/lib/session_helper.py` 新規 (`detect_session_id()` 関数)
- HELIX_SESSION_ID env → Claude Code SESSION_ID env → /tmp/claude-* path → UUID fallback の優先順
- helix-codex / helix-agent / hook 全体で再利用

#### Phase 5: テスト + 過去機構との互換性 + commit
- test_session_helper.py / test_pretooluse_agent_fire.bats
- 既存 PLAN-078/080/081 機能の破壊なし
- session_id 不在時の degradation 動作

### 3.2 out-of-scope

- PostToolUse hook (= 別 PLAN、後段で考察)
- session_id 共有 storage (= 別 PLAN、複数プロセス同時実行対応)
- Web/UI 表示 (= 別 PLAN)

## 4. Phase 構成 (5 Phase 想定)

| Phase | スコープ | size | 担当 |
|---|---|---|---|
| Phase 1 | 設計 (L1-L2、本 doc + 統合点 仕様) | S | Opus |
| Phase 2 | PreToolUse hook 自動 fire | M | Codex se |
| Phase 3 | Stop hook 拡張 release | M | Codex se |
| Phase 4 | session_helper.py | S | Codex se |
| Phase 5 | test + commit + push | M | Codex pg + Opus |

## 4.5 V-model 4 artifact (PLAN-075 準拠)

| Artifact | 担当層 | 想定パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | docs/v2/L3-detailed-design/D-CONCEPT.md (補完: 本 PLAN doc §3 + PLAN-080 §3) |
| ② 実装コード | L4 実装 | cli/lib/session_helper.py + .claude/hooks/pretooluse-agent-fire.sh + cli/helix-stop-hook (拡張) |
| ③ テスト設計 | L4 設計 | docs/v2/L4-test-design/PLAN-083-unit-test-design.md (Phase 5 で起票) |
| ④ テストコード | L4 実装 | cli/lib/tests/test_session_helper.py + tests/pretooluse-agent-fire.bats + tests/stop-hook-release.bats |

## 5. 受入条件

- Agent tool 呼び出しで agent_slots に自動 fire (subagent_type / session_id 付与)
- Stop hook で session の running slot 全 release
- `helix agent audit --phase Lx --session-id $HELIX_SESSION_ID` で実 session の audit 結果取得可能
- session_id 検出 4 fallback 経路全 PASS
- pytest + bats 全 PASS
- 既存 5 PLAN 機能破壊なし

## 6. リスク

| ID | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R-01 | PreToolUse hook の timeout (5s) で fire 失敗 | slot 記録漏れ | timeout 3s で agent_slots fire 完結、失敗時も session 阻害禁止 (exit 0) |
| R-02 | Stop hook で release 漏れ | running slot 増殖 | safety: 5min 以上 running slot を cancelled 自動遷移 (PLAN-078 list_stale_slots 活用) |
| R-03 | session_id 検出失敗 | session 跨ぎ集計が誤動作 | UUID fallback で必ず一意 ID を返す、ただし継続性は失われる |
| R-04 | 既存 .claude/hooks との衝突 | 既存 PreToolUse (Write block) との順序問題 | hook config 配置で順序確認、両立可能 |

## 7. 依存

- PLAN-078 v28 agent_slots schema (session_id 列、TEXT NULL) 既存
- PLAN-080 harness_check_events schema (session_id 列) 既存
- PLAN-081 cli/helix-stop-hook 既存 (拡張)
- PLAN-082 agent_mandatory.audit_phase (session_id 引数) 既存

## 8. Next Action

1. Phase 2 prompt 作成 → Codex se 投入
2. Phase 3 prompt 作成 → Codex se 投入
3. Phase 4 prompt 作成 → Codex se 投入
4. Phase 5 prompt 作成 → Codex pg 投入 + Opus 全回帰

## 9. 業界標準リファレンス（W5c-13）

### 9.1 CI/CD ハーネスのオーケストレーション

PLAN-083 は既存の `pretooluse` / `stop` フック統合を、既存 CI/CD での実行チェーン制御と同型で扱える状態にすることが目的。基準は次のとおり。

- GitLab CI/CD: パイプラインは YAML でジョブとステージを定義し、ステージ依存（失敗時は後続を停止）という依存グラフで実行順を管理する（Build/テスト/デプロイ段階の明示的分離）。  
  参照: `docs.gitlab.com/ci/pipelines/`, `docs.gitlab.com/ci/pipelines/pipeline_architectures/`
- GitHub Actions: ワークフローはリポジトリ配下の YAML（`on`/`jobs`/`steps`）として定義され、イベント起点でジョブ実行を起動する。  
  参照: `docs.github.com/en/actions/concepts/workflows-and-actions/workflows`, `docs.github.com/en/actions/writing-workflows/about-workflows`
- Buildkite Pipelines: 「orchestration（実行制御）をプラットフォーム側で扱い、ワークフロー定義自体を柔軟に変更可能」とする構成を前提に、段階的ステップと監視を組み合わせる。  
  参照: `buildkite.com/docs/pipelines`, `buildkite.com/platform/pipelines`

### 9.2 イベント駆動フックチェーン（Pre/Post）

Claude の hook ドキュメントでは、`PreToolUse` はツール実行前、`Stop` はタスク完了判定前に発火する標準イベントで、同一イベントに複数フックを設定したり、SDK 側でフックチェーン（複数フィルタ）を組める。  
Git クライアント連携としては Husky が client-side フック（コミット/プッシュ等）を一元化し、pre-commit などのチェーン型実行を導く。  
参考実装の観点では、イベント名の厳密一致、入力 JSON からの `tool_name` 連携、Stop 時の継続判定フロー（`ok` / `reason`）を PLAN の検証ポイントに一致させる。

- Claude Code Hooks: `PreToolUse`, `PostToolUse`, `Stop` のイベント、`hook_event_name` を含む JSON 入力、複数設定の順次評価。  
  参照: `docs.claude.com/docs/claude-code/hooks-guide`, `platform.claude.com/docs/en/agent-sdk/hooks`
- Husky: コミット系ガード（pre-commit など）を含む client-side Git hook の代表実装。  
  参照: `typicode.github.io/husky`
- pre-commit: `.pre-commit-config.yaml` で hook 種別を宣言し、`SKIP` や `stages` で実行段階を制御する運用（段階的検証）モデル。  
  参照: `pre-commit.com`

### 9.3 セッション観測（telemetry）と標準化

- OpenTelemetry はトレーシング/メトリクス/ログの収集・送信・ルーティングを標準化するデファクト系フレームワーク。  
  参照: `opentelemetry.io/docs/concepts/semantic-conventions`
- Datadog / Honeycomb は OTel を前提とした OTLP 受け入れ（直入力/Collector 経由）を想定し、サービス横断でトレース・メトリクス・ログの相関観測を前提化。  
  参照: `docs.datadoghq.com/opentelemetry/`, `docs.honeycomb.io/send-data/opentelemetry`, `docs.honeycomb.io/send-data/telemetry-pipeline/sources/opentelemetry`

PLAN-083 retrofit (W5c-13) では、session_id と hook 実行履歴を上記標準に合わせてイベントごとに観測し、`agent_slot`、`harness_check_events`、session リリースの整合を監査可能にする。

## Revision History

- 2026-05-19 (W5c-13): plan doc retrofit で「業界標準リファレンス」節を新設。CI/CD パターン、イベント駆動 hook chain、OTel セッション観測の基準を PLAN-083 の仕様に対比追加。
