# PMO Sonnet/Haiku 起動エラー root cause 調査

## 調査概要

- 対象: `helix claude --role pmo --model sonnet --execute` / `--model haiku --execute`
- 症状: PMO 起動直後に `Path /tmp/test-helix was not found.` で失敗し、終了時に `SessionEnd hook ... broker.json` の `ENOENT` が追随する
- 結論: 一次原因は `cli/helix-claude` ではなく project-local [`.claude/settings.local.json`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json) に残っている `/tmp/test-helix` 向けの stale 設定。`broker.json` エラーは起動失敗後の cleanup バグで、主因ではない
- 推奨: `(a) wrapper 修正` ではなく、まず project-local Claude settings から `/tmp/test-helix` 参照を除去し、その上で plugin `SessionEnd` の `clearBrokerSession()` を idempotent 化する

## 選択肢

| 選択肢 | 内容 | メリット | デメリット | 推奨度 |
|---|---|---|---|---|
| A | [`.claude/settings.local.json`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json) から `/tmp/test-helix` 関連 allow/read/additionalDirectories を削除 | 一次原因に直接効く。PMO Sonnet/Haiku 共通で効く。変更箇所が明確 | local settings の棚卸しが必要 | 高 |
| B | plugin `session-lifecycle-hook.mjs` / `broker-lifecycle.mjs` で `broker.json` 不在を許容 | 二次ノイズを除去。今後の調査性が上がる | 主因は直らない | 中 |
| C | `cli/helix-claude` 側で `/tmp/test-helix` を補正 | wrapper 起点なら効く | 今回は wrapper に根拠なし。誤修正の可能性 | 低 |
| D | workspace ID 計算修正 | `broker.json` path 不一致なら効く | 今回は hash が実 workspace と一致し、根拠が弱い | 低 |

## ソース

- project-local Claude settings の `/tmp/test-helix` 参照:
  - [`.claude/settings.local.json:141`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json:141), [150](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json:150), [163](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json:163), [429](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json:429)
- wrapper の execute 経路:
  - [`cli/helix-claude:387`](/home/tenni/ai-dev-kit-vscode/cli/helix-claude:387)
  - [`cli/helix-claude:393`](/home/tenni/ai-dev-kit-vscode/cli/helix-claude:393)
- wrapper の `PROJECT_ROOT` 解決:
  - [`cli/lib/helix-common.sh:8`](/home/tenni/ai-dev-kit-vscode/cli/lib/helix-common.sh:8)
- plugin state/workspace hash:
  - [`state.mjs:29`](/home/tenni/.claude/plugins/marketplaces/openai-codex/plugins/codex/scripts/lib/state.mjs:29)
  - [`state.mjs:40`](/home/tenni/.claude/plugins/marketplaces/openai-codex/plugins/codex/scripts/lib/state.mjs:40)
  - 実測: `sha256("/home/tenni/ai-dev-kit-vscode")[:16] == 621293cd6fa02246`
- SessionEnd cleanup:
  - [`session-lifecycle-hook.mjs:81`](/home/tenni/.claude/plugins/marketplaces/openai-codex/plugins/codex/scripts/session-lifecycle-hook.mjs:81)
  - [`broker-lifecycle.mjs:95`](/home/tenni/.claude/plugins/marketplaces/openai-codex/plugins/codex/scripts/lib/broker-lifecycle.mjs:95)
- 失敗ログ:
  - [`.helix/cache/pmo/20260514T014819-12c3e535.log`](/home/tenni/ai-dev-kit-vscode/.helix/cache/pmo/20260514T014819-12c3e535.log)
  - Claude project log: `/home/tenni/.claude/projects/-home-tenni-ai-dev-kit-vscode/43a22905-0b2a-4ba1-9c89-fcc344c8646d.jsonl`

## §1 エラーログ詳細

### 1.1 観測できた完全ログ

PMO 実行ログ [`.helix/cache/pmo/20260514T014819-12c3e535.log`](/home/tenni/ai-dev-kit-vscode/.helix/cache/pmo/20260514T014819-12c3e535.log):

```text
Path /tmp/test-helix was not found.
SessionEnd hook [node "${CLAUDE_PLUGIN_ROOT}/scripts/session-lifecycle-hook.mjs" SessionEnd] failed: ENOENT: no such file or directory, unlink '/home/tenni/.claude/plugins/data/codex-openai-codex/state/ai-dev-kit-vscode-621293cd6fa02246/broker.json'
```

同一症状の過去ログ:
- [`.helix/cache/pmo/20260511T061755-e54d8edd.log`](/home/tenni/ai-dev-kit-vscode/.helix/cache/pmo/20260511T061755-e54d8edd.log), [20260512T023025-50f7dda0.log](/home/tenni/ai-dev-kit-vscode/.helix/cache/pmo/20260512T023025-50f7dda0.log)

Claude project transcript には同じ 2 行が tool result として保存されている。追加 stack trace は確認できなかった。不確実だが、失敗は Claude CLI 側の path validation で早期終了しており、plugin まで深い例外 stack が伝播していない可能性が高い。

### 1.2 発生条件

- Claude entrypoint: `helix claude --role pmo --model sonnet --execute`
- Claude runtime version: `2.1.140`  
  根拠: Claude project jsonl の `version`
- OS: `Linux ... WSL2 x86_64 GNU/Linux`
- shell: `bash`
- Node.js: `v22.22.0`
- workspace: `/home/tenni/ai-dev-kit-vscode`

### 1.3 発生順序

1. PMO execute が Claude CLI を `--print` で起動する
2. Claude 側が `/tmp/test-helix` の path validation に失敗する
3. セッション終了処理が走る
4. codex plugin の `SessionEnd` が `broker.json` unlink を試みる
5. `broker.json` が無いため `ENOENT` が二次的に出る

## §2 root cause 仮説

### 仮説1: project-local Claude settings に stale な `/tmp/test-helix` 参照が残っている

- 状態: [`.claude/settings.local.json:141`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json:141) などに `HELIX_PROJECT_ROOT=/tmp/test-helix ...`、[`163`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json:163) に `Read(//tmp/test-helix/**)`、[`429`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json:429) に `additionalDirectories: /tmp/test-helix`
- 評価: 最有力
- 根拠:
  - `cli/helix-claude` 本体には `/tmp/test-helix` の hard-code が無い
  - 失敗文言が settings 由来 path validation と整合する
  - Sonnet/Haiku を問わず Claude runtime 共通で再現する設計になっている
- 検証手順:
  1. project-local [`.claude/settings.local.json`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json) をバックアップ
  2. `/tmp/test-helix` を含む allow rule / read rule / `additionalDirectories` を一時削除
  3. `helix claude --role pmo --model sonnet --execute --task "ping"` を再実行
  4. 同じく haiku でも再実行
  5. 失敗が消えれば一次原因確定

### 仮説2: `broker.json` unlink 失敗は startup abort 後の cleanup bug

- 状態:
  - plugin の `clearBrokerSession(cwd)` は `existsSync(stateFile)` 後に `unlinkSync(stateFile)` を直接呼ぶ
  - `broker.json` 実ファイルは現状存在しない
  - 同 state dir には `state.json` と job files は存在する
- 評価: 有力。ただし二次原因
- 根拠:
  - state dir 自体は正常に作られている
  - workspace hash も一致している
  - `broker.json` だけが無いので、startup 途中 abort または競合削除の方が自然
- 検証手順:
  1. `/tmp/test-helix` 問題を解消した状態で PMO を再実行
  2. 成功時に `broker.json` が一時生成されるか確認
  3. 失敗時でも SessionEnd が `ENOENT` を出さないよう `try/catch` を当てて再確認
  4. 必要なら `clearBrokerSession()` 前後で debug log を追加し race を観測

### 仮説3: workspace ID 計算不一致

- 状態:
  - `state.mjs` は `sha256(realpath(workspaceRoot))[:16]` で state dir を決める
  - 実測 hash は `621293cd6fa02246`
  - 実際の state dir 名も `ai-dev-kit-vscode-621293cd6fa02246`
- 評価: 低い。現時点では反証寄り
- 根拠:
  - path suffix が実測と一致
  - `state.json` / jobs がその dir に存在する
- 検証手順:
  1. `realpath /home/tenni/ai-dev-kit-vscode` を固定
  2. 同式で hash を再計算
  3. plugin runtime から見た `cwd` と `workspaceRoot` を debug 出力
  4. 差分がなければ除外

## §3 修正計画

### 3.1 fix 候補比較

| fix | 内容 | 効果 | リスク | 推奨 |
|---|---|---|---|---|
| (a) | `cli/helix-claude` wrapper で `/tmp/test-helix` 参照削除 or 修正 | 今回は効果薄 | 誤診修正になりやすい | 低 |
| (b) | plugin-data dir / `broker.json` を pre-create | 二次エラー緩和のみ | 不要な state 汚染 | 低 |
| (c) | `SessionEnd` hook の error handling 強化 | cleanup を安定化 | 主因は残る | 中 |
| (d) | workspace ID 計算ロジック修正 | 不一致時のみ有効 | 今回は根拠不足 | 低 |
| (e) | project-local `.claude/settings.local.json` の `/tmp/test-helix` 参照削除 | 一次原因に直撃 | settings 整理が必要 | 最優先 |

### 3.2 推奨修正

推奨は `e + c`。

1. project-local [`.claude/settings.local.json`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json) から `/tmp/test-helix` を含む以下を除去
   - `Bash(HELIX_PROJECT_ROOT=/tmp/test-helix ...)`
   - `Read(//tmp/test-helix/**)`
   - `additionalDirectories` の `/tmp/test-helix`
2. codex plugin 側で `clearBrokerSession()` を idempotent 化
   - `unlinkSync` を `try/catch` で包み、`ENOENT` は無視
   - もしくは `fs.rmSync(path, { force: true })` 相当へ変更

### 3.3 理由

- `/tmp/test-helix` は wrapper ではなく settings にのみ現れる
- `mkdir -p /tmp/test-helix` が効かなかった理由としては、単に root dir の有無ではなく stale allow/read rules 全体が無効化対象になっている可能性がある。ここは未再現のため不確実
- cleanup bug は別件だが、主因解消後も観測ノイズを減らす価値が高い

### 3.4 影響範囲

- `.claude/settings.local.json` 修正:
  - この repo での Claude Code / PMO 起動に影響
  - 旧 `test-helix` 用のローカル実験レシピは使えなくなる可能性
- plugin cleanup 修正:
  - Codex plugin 全 workspace 共通
  - SessionEnd の安定性改善

## §4 検証 step

### 4.1 事前確認

1. [`.claude/settings.local.json`](/home/tenni/ai-dev-kit-vscode/.claude/settings.local.json) をバックアップ
2. `.helix/cache/pmo/` の新規ログタイムスタンプを控える
3. plugin state dir の現状を記録

### 4.2 Sonnet 検証

1. `helix claude --role pmo --model sonnet --execute --task "ping"`
2. 期待結果:
   - `Path /tmp/test-helix was not found.` が出ない
   - `SessionEnd hook ... broker.json` が出ない
   - `.helix/cache/pmo/*.log` に通常応答が出る

### 4.3 Haiku 検証

1. `helix claude --role pmo --model haiku --execute --task "ping" --allow-paths "docs/**"`
2. 期待結果:
   - Sonnet と同じく path error が出ない
   - docs 限定モードでも起動成功

### 4.4 cleanup 検証

1. 成功 run の前後で `~/.claude/plugins/data/codex-openai-codex/state/<workspace>/broker.json` の生成と削除を観測
2. 異常終了ケースでも SessionEnd が 0 終了になることを確認

## §5 暫定回避策

- 現状の暫定運用:
  - PMO Sonnet/Haiku を使わず、Codex research / docs role で代替
  - 調査系・比較系は read-only のまま Codex 側で継続可能
- 暫定期間の目安:
  - `e` の settings 修正が終わるまで
  - plugin cleanup の `c` は次のメンテで追随してよい
- 運用上の注意:
  - `/tmp/test-helix` を作るだけでは十分でない可能性が高い
  - 再発防止のため、test fixture 用 path を project-local Claude settings に残さない review を追加すべき
