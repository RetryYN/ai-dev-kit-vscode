# HELIX Core — 共通開発フロー定義

> Claude Code / Codex CLI 共通。ツール固有設定は各ツールの設定ファイルに記載。
> 正本: SKILL_MAP.md §正本宣言 参照

---

## 応答言語

- 日本語で応答する

## スキル

- `~/ai-dev-kit-vscode/skills/` に配置
- triggers 該当時は自発的に Read。全スキル一括読み込み禁止
- コンテキスト管理: `context-memory` スキル参照

## モデル割当（真実は `cli/config/models.yaml`）

| ロール | モデル | thinking |
|------|--------|--------|
| PM | Opus (Claude Code) | — |
| PMO Sonnet | claude-sonnet-4-6 | medium |
| PMO Haiku | claude-haiku-4-5-20251001 | low |
| TL | gpt-5.5 | high |
| SE | gpt-5.4 | high |
| PE | gpt-5.3-codex-spark / gpt-5.3-codex | low-medium |

## タスク受領

1. サイジング S/M/L（SKILL_MAP.md §タスクサイジング）
2. フェーズスキップ決定（SKILL_MAP.md §フェーズスキップ決定木）
3. ゲート判定（`skills/tools/ai-coding/references/gate-policy.md §ゲート一覧`）
4. 該当スキルを Read（SKILL_MAP.md オーケストレーションフローの `→` 右のスキル名を参照）
4.5 実装着手前 (L4 entry): `helix code find "<keyword>"` で既存実装の流用候補を確認する
  - 公開 API / 再利用候補は `--bucket coverage_eligible`（default）で確認
  - private helper の再利用/PoC seed 探索は `--bucket private_helper` を併用する
  - 非公開 → 公開昇格候補（seed candidate）を `--seed-promotable true` で抽出する
4.6 v2 ディスパッチ: タスク性質で必須委譲先を優先決定
- BE 実装/DB/インフラ: `helix codex --role se`
- 設計・レビュー・デバッグ: `helix codex --role tl`
- 速度重視単機能実装: `helix codex --role pe`
- 状況把握 / docs チェック: `helix claude --role pmo --model sonnet --execute`
- 軽文書チェック / docs/**: `helix claude --role pmo --model haiku --execute --allow-paths "docs/**"`
4.7 スキル推奨: `helix skill chain "<タスク記述>"` を任意で実施。skip 理由がある場合は会話または final report に記録する（例: 自明な小修正、既知 skill のみ使用 等）

L4 implementation / build / G4 補足（PLAN-013）:
- L4 entry: `helix code find`、`helix code stats --uncovered --bucket coverage_eligible` を使って既存資産を確認する
- L4 implementation: 新規 public symbol は `coverage_eligible`、`_` 始まり helper は `private_helper` に分類する
- L4 build: `helix code build` で catalog を再生成し、`bucket` / `symbol_line` / metadata を自動付与する
- G4: `helix code stats --scope core5 --bucket coverage_eligible --fail-under 80` を走らせて coverage gate を判断する
5. 実行開始
6. ミニレトロ: G2/G4/L8 通過時（`skills/tools/ai-coding/references/gate-policy.md §ミニレトロ`）
7. readiness exit 条件確認 → 該当スキル Read

> **Reverse モード**: 既存コードからの設計復元は SKILL_MAP.md §Phase R / `workflow/reverse-analysis/SKILL.md` を参照。Forward とは別のサイジング・ゲート体系（R0→R4→Forward→RGC）を使用。
> ※ RGC（Reverse Gap Closure）は `helix reverse rgc` で実装済み。R4 Gap Register から集計を表示する。

## 設計提案

- ユーザーへの技術提案前に `helix plan draft → review → finalize` を実施
- TL approve なしで finalize 不可
- 詳細は `workflow-core.md §設計提案レビュー` 参照

## 工程表・承認・委譲

- 実装は L3 工程表、`.helix/task-plan.yaml`、handover Next Action の該当行を正とする。
- 工程表がある場合、`plan_id`、`task_id` または `WBS ID`、`L4 Sprint`、依存、受入条件、reference_docs を確認してから L4 に入る。
- 計画・実装順・整理案をユーザーへ提示した場合、明示承認があるまでファイル編集・依存追加・外部状態変更へ進まない。
- 工程表外の変更が必要になった場合は、先に工程表更新またはユーザー確認へ戻る。
- TL は工程表の role に応じて `helix codex`、`helix claude --dry-run`、`helix team`、`helix review` を使い、使えない場合は理由を証跡化する。

## readiness と carry rule

PLAN-004 v5 と PLAN-009 v3 の方針として、L1-L11 を進める際は以下を適用する。

- 各 L の entry/exit 条件に readiness を明示し、未充足時は前段へ差戻す。
- 各ゲート（特に G1-G11）は readiness exit 判定に接続し、未達成は carry/passed 制御に反映する。
- IIP/deferral の評価は下記で統一する。

P0: gate stop（即修正）
P1: gate stop もしくは carry（PM 承認）
P2: 次 L 開始まで carry（deferred-finding として debt に記録）
P3: 任意 carry

deferred-finding は次の品質評価に反映し、accuracy_score から減点される（数値は共通で carry レベルにより重み付け）。

## Phase 4 Run (L9-L11)

PLAN-009 v3 の 4 フェーズ拡張に合わせ、Run 工程を追加する。

### L9: デプロイ検証

- デプロイ準備、ロールバック手順、smoke test、監視初期確認、初回復旧手順を検証する。

### L10: 観測

- リリース後の SLO/SLI、アラート、エラー率、外部依存の観測を完了し、未解決重大事象を確認する。

### L11: 運用学習

- postmortem と改善施策をまとめ、次サイクルの state/events へフィードバックし、運用引継ぎ資料へ反映する。

### 連携ゲート

- G9（デプロイ安定性）
- G10（観測完了）
- G11（運用学習完了）
- 本番運用対象では Run 工程必須。PoC や検証寄りのタスクは本番影響がなければ任意 skip。

## 状態管理の二層構造

| 層 | ファイル | 役割 | 参照元 |
|----|---------|------|--------|
| 宣言的状態 | `.helix/phase.yaml` | 現在のフェーズ・ゲート通過状況・凍結フラグ | 15スクリプト |
| イベントログ | `.helix/helix.db` (SQLite) | タスク実行履歴・hook 発火・フィードバック・学習 | 18+スクリプト |

- phase.yaml は YAML で人間が読める。手動リセット可能
- helix.db はイベント蓄積のみ。`helix log report` で可視化

## 原則

- **エスカレーション**: 本番影響・認証・決済・個人情報・ライセンス → 必ず人間に確認
- **ファイル作成前**: 既存リソース確認 → 重複なら作成しない
