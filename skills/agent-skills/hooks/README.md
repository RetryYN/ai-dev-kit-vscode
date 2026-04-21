# agent-skills hooks

これらは Claude Code **plugin** としてロードされた場合のみ動作する。
本体 HELIX リポジトリを直接開いている場合、.claude-plugin/ 経由の plugin ロードがない限り dead code。

## 内容
- hooks.json: SessionStart hook 定義 (${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh を呼ぶ)
- session-start.sh: セッション開始時に using-agent-skills メタスキルを注入し、HELIX 環境検出情報をメッセージとして出力する。
- sdd-cache-*.sh: WebFetch の pre/post hook として URL 単位のHTTP再検証キャッシュを管理し、304時にキャッシュ結果を返す。
- simplify-ignore*.sh: simplify-ignore ブロックのマスキング/復元と動作検証（テストスクリプト）を提供する。

## 本体 HELIX との関係
- 本体 SessionStart は別途 CLAUDE.md / settings.json で管理
- plugin として配布した場合のみ hooks.json が発火
- 競合なし (CLAUDE_PLUGIN_ROOT が未設定なら sourced されない)
