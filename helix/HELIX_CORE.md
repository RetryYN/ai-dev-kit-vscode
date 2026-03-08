# HELIX Core — 共通開発フロー定義

> Claude Code / Codex CLI 共通。ツール固有設定は各ツールの設定ファイルに記載。

## 正本宣言

- **正本**: 各ツールの設定ファイル + SKILL_MAP.md + 各 SKILL.md
- **手順正本**: `ai-coding/references/workflow-core.md`（ディスパッチ・並列・ADR）+ `ai-coding/references/gate-policy.md`（ゲート・遷移）
- **矛盾時**: 実装 > アーカイブ資料（`docs/archive/`）

---

## 応答言語

- 日本語で応答する

## スキル

- `~/ai-dev-kit-vscode/skills/` に配置
- triggers 該当時は自発的に Read。全スキル一括読み込み禁止
- コンテキスト管理: `context-memory` スキル参照

## タスク受領

1. サイジング S/M/L（SKILL_MAP.md §タスクサイジング）
2. フェーズスキップ決定（§フェーズスキップ決定木）
3. ゲート判定（`ai-coding/references/gate-policy.md §ゲート一覧`）
4. 該当スキルを Read（フロー図の `→` 右のスキル名を参照）
5. 実行開始
6. ミニレトロ: G2/G4/L8 通過時（`ai-coding/references/gate-policy.md §ミニレトロ`）

## モデル割当

> 正本: `ai-coding/references/workflow-core.md §モデル割当テーブル`

| 委譲先 | 役割 | 担当 |
|--------|------|------|
| Opus（自身） | PM | 言語化・タスク分解・外注指示・出力レビュー・統合・エスカレーション判断・**フロント設計** |
| Codex 5.4 | TL | 設計（L2-L3）・技術的難易度評価（L3工程表）・レビュー・品質向上・フロントコード品質担保 |
| Codex 5.3 | SE | 設計レビュー・上級実装（スコア4+） |
| Codex 5.3 Spark | PG | 通常以下実装（スコア1-3） |
| Codex 5.2 | — | 大規模コード精読・スキャン |
| Sonnet | FE実装 | フロント実装・FEデザイン初稿・テスト・ドキュメント |
| Haiku 4.5 | リサーチ | Web検索・先行事例調査 |

- PM は自分でコード実装しない → Codex / Sonnet へ委譲
- 技術判断を独断しない → TL（Codex 5.4）と壁打ち
- 工程表作成後は自律実行
- **Codex 担当タスクを Sonnet で代替しない**

## Codex CLI

- 上級実装: `codex exec "プロンプト" -m gpt-5.3-codex`（軽量: `-m gpt-5.3-codex-spark`）
- 設計・レビュー: `codex exec "レビュー: [対象]" -m gpt-5.4` / `codex review --uncommitted`
- 精読: `codex exec "精読: [対象]" -m gpt-5.2-codex`
- 思考トークン: Codex 系は `model_reasoning_effort = "xhigh"` 固定
- `--quiet` / `-q` は存在しない。`--uncommitted` とプロンプト引数は併用不可

## 原則

- **エスカレーション**: 本番影響・認証・決済・個人情報・ライセンス → 必ず人間に確認
- **ファイル作成前**: 既存リソース確認 → 重複なら作成しない
