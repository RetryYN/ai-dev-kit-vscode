# helix builder コマンドガイド

## 8 ビルダー

```bash
helix builder list
```

利用可能タイプ:

- `json-converter`
- `verify-script`
- `agent-loop`
- `task`
- `workflow`
- `agent-pipeline`
- `agent-skill`
- `sub-agent`

## 基本フロー

```bash
# 1) 入力スキーマ確認
helix builder task schema

# 2) 入力 JSON を渡して生成
helix builder task generate --input '{"name":"auth-task","steps":["analyze","implement"]}'

# 3) 生成物の検証
helix builder task validate --artifact '[{"path":"builders/tasks/auth-task.yaml"}]'

# 4) 実行履歴の確認
helix builder task history --limit 5
```

## 入力 JSON の書き方

- `helix builder <type> schema` で必須フィールドを確認
- `--input` は JSON 文字列か JSON ファイルパス

ファイル入力例:

```bash
cat > /tmp/builder-input.json <<'JSON'
{
  "name": "auth-pipeline",
  "description": "認証系の標準パイプライン"
}
JSON

helix builder workflow generate --input /tmp/builder-input.json
```

## from_history の活用

履歴から seed を指定して再生成できる。

```bash
helix builder workflow history --limit 5
helix builder workflow generate --seed <execution-id> --input '{"name":"auth-pipeline-v2"}'
```

## 組み合わせパターン

- `verify-script` + `task`: 検証付きタスク雛形を生成
- `agent-skill` + `sub-agent`: 役割分離したエージェントセットを作成
- `workflow` + `agent-pipeline`: 複数 builder を直列化
