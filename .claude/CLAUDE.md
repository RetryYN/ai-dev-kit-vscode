# Global Settings

@~/ai-dev-kit-vscode/skills/SKILL_MAP.md
@~/ai-dev-kit-vscode/helix/HELIX_CORE.md

## Claude Code 固有設定

- **Edit 前に Read**: 未読ファイルの Edit は失敗する

### Opus = オーケストレーター + フロント設計

**常時すべて委譲**。例外は MCP検証などツール動作確認と**フロント（デザイン含む）設計**。

### セッション開始チェック（SKILL_MAP.md があるプロジェクトはスキップ）

1. `./CLAUDE.md` の存在確認
2. `.gitignore` に `CLAUDE.local.md` / `.claude/settings.local.json` 含むか
3. 問題なければ「OK: 初期化チェック完了」で終える
- CLAUDE.md 未存在 → context-memory §1.3 テンプレートで作成提案
