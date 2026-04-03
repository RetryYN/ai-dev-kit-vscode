# helix matrix コマンドガイド

## できること

- 成果物対照表 `matrix.yaml` の初期化
- `matrix.yaml + rules` から runtime/state 生成
- 構造検証
- 進捗可視化

## サブコマンド

```bash
helix matrix init
helix matrix compile
helix matrix validate
helix matrix status
```

`--force` が使えるのは `init` と `compile`。

## 最短手順

```bash
helix init
helix matrix init
helix matrix validate
helix matrix compile
helix matrix status
```

## `matrix.yaml` の書き方

最小構成:

```yaml
project:
  size: M
  default_drive: be

features:
  user-auth:
    drive: be
    scope: feature
    ui: true
    docs_root: docs/features/user-auth
    src_root: src/features/user-auth
    requires:
      L2: [D-ARCH, D-ADR, D-THREAT]
      L3: [D-API, D-DB, D-TEST, D-PLAN]
```

ポイント:

- `features.<scope-id>` は `kebab-case`
- `requires` はレイヤーごとに `D-*` を配列で定義
- status は `matrix.yaml` に書かない（state に分離）

## `rules/` の設定方法

`helix matrix init` で以下が生成される:

- `.helix/rules/deliverables.yaml`
- `.helix/rules/structure.yaml`
- `.helix/rules/naming.yaml`

編集例（命名ルール変更）:

```bash
sed -n '1,120p' .helix/rules/naming.yaml
```

編集後は再生成:

```bash
helix matrix compile --force
```

## compile が生成するもの

`helix matrix compile` 実行で主に生成/更新される:

- `.helix/doc-map.yaml`
- `.helix/gate-checks.yaml`
- `.helix/state/deliverables.json`
- `.helix/runtime/index.json`

## よくある詰まり

`matrix.yaml がない`:

```bash
helix matrix init
```

`循環参照エラー`:

- `shared_uses` の循環（A→B→A）を解消して `helix matrix validate`
