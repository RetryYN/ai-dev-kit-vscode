# ai-dev-kit-vscode

## 概要

Claude Code / Codex CLI 用の HELIX スキルフレームワーク（40スキル）。AIエージェントの開発ワークフローを標準化するスキル集。

## 技術スタック

- 言語: Markdown（スキルファイル）, JavaScript（ツール）
- ランタイム: Node.js
- 対象ツール: Claude Code, Codex CLI

## ディレクトリ構造

```
skills/              # HELIXスキル群（40スキル）
├── SKILL_MAP.md     # スキル一覧・オーケストレーションフロー（常時ロード）
├── common/          # 共通スキル（11）
├── workflow/        # ワークフロースキル（17）
├── project/         # プロジェクト固有スキル（3）
├── advanced/        # 高度なスキル（6）
├── tools/           # ツールスキル（2）
└── integration/     # 統合スキル（1）
docs/
├── setup-guide.md   # セットアップ手順書
└── archive/         # アーカイブ済みエンタープライズ仕様
```

## コーディング規約

- SKILL.md は 500行以内。超過分は `references/` サブディレクトリに分割
- frontmatter 必須項目: name, description, metadata.helix_layer, triggers, verification, compatibility
- description: 「〇〇関連タスク時に使用」は禁止。具体的な用途と提供内容を記載
- 廃止スキル名（orchestrator, architecture, codex, vscode-plugins）は使用禁止

## コマンド

- 廃止スキル参照チェック: `rg -wn "orchestrator|architecture|codex|vscode-plugins" skills/`
- 行数チェック: `wc -l skills/**/SKILL.md`

## 禁止事項

- SKILL.md の 500行超過
- 全スキルの一括読み込み（コンテキスト爆発）
- 廃止スキル名への参照
- references/ 以外での @import 4段以上ネスト

## HELIX 処理フロー

タスク受領時は以下の順序で処理する（詳細は SKILL_MAP.md を参照）:

1. **タスクサイジング**: SKILL_MAP.md §タスクサイジング で S/M/L 判定
2. **フェーズスキップ**: SKILL_MAP.md §フェーズスキップ決定木 で実行フェーズを決定
3. **スキル読み込み**: §フェーズ別 I/O サマリー の「スキル」列から該当スキルを Read
4. **ディスパッチ**: ai-coding/references/orchestration-workflow.md のフロー
5. **サブエージェント設定**: ai-coding/references/subagent-config.md のマトリクス
