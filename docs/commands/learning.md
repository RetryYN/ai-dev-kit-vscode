# helix learn / promote / discover ガイド

## 目的

- 成功実行から recipe を抽出
- しきい値を超えた recipe を Builder 生成物へ昇格
- local/global から再利用パターンを検索

## 1. learn

```bash
helix learn --task-id T001
helix learn --all
```

動作:

- 成功タスクを解析
- `.helix/recipes/` に recipe 保存
- `~/.helix/global.db` へ同期

## 2. promote

```bash
# 候補表示（自動判定）
helix promote --auto

# 明示昇格
helix promote <recipe-id> --type skill
helix promote <recipe-id> --type script
helix promote <recipe-id> --type task
helix promote <recipe-id> --type sub-agent
```

しきい値変更:

```bash
helix promote --auto --threshold 5
```

## 3. discover

```bash
helix discover --query "auth" --limit 10
```

検索対象:

- project local recipes
- user global recipes / index

## recipe の構造

主要キー:

- `recipe_id`
- `pattern_key`
- `steps`
- `metrics`
- `classification`
- `security`
- `verification`

## global.db の仕組み

- パス: `~/.helix/global.db`
- role: recipe index / promotion records の正本
- 同期時は redaction を実施して機密を除去

## 昇格の閾値と手順

デフォルトは「同一 pattern が 3 回成功」。

手順:

1. `helix learn --all` で蓄積
2. `helix promote --auto` で候補確認
3. `helix promote <recipe-id> --type ...` で昇格
4. 必要なら `helix builder ... history` で生成結果確認
