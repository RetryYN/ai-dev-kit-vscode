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

## タスク受領

1. サイジング S/M/L（SKILL_MAP.md §タスクサイジング）
2. フェーズスキップ決定（SKILL_MAP.md §フェーズスキップ決定木）
3. ゲート判定（`skills/tools/ai-coding/references/gate-policy.md §ゲート一覧`）
4. 該当スキルを Read（SKILL_MAP.md オーケストレーションフローの `→` 右のスキル名を参照）
5. 実行開始
6. ミニレトロ: G2/G4/L8 通過時（`skills/tools/ai-coding/references/gate-policy.md §ミニレトロ`）

> **Reverse モード**: 既存コードからの設計復元は SKILL_MAP.md §Phase R / `workflow/reverse-analysis/SKILL.md` を参照。Forward とは別のサイジング・ゲート体系（R0→R4→Forward→RGC）を使用。
> ※ RGC（Reverse Gap Closure）は `helix reverse rgc` で実装済み。R4 Gap Register から集計を表示する。

## 設計提案

- ユーザーへの技術提案前に `helix plan draft → review → finalize` を実施
- TL approve なしで finalize 不可
- 詳細は `workflow-core.md §設計提案レビュー` 参照

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
