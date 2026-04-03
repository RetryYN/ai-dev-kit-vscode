# HELIX セットアップガイド

初回ユーザーが「README → setup → 最初のゲート通過」まで進むための実践手順。

## 前提条件

- `bash`, `python3`, `git`, `sqlite3`, `codex` が使える
- `~/ai-dev-kit-vscode` が配置済み

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
```

## 1. インストール

```bash
bash ~/ai-dev-kit-vscode/setup.sh
```

確認:

```bash
helix --help
```

## 2. プロジェクト初期化

対象プロジェクトで実行:

```bash
cd /path/to/your-project
helix init
```

`helix init` で主に生成されるもの:

- `.helix/phase.yaml`
- `.helix/matrix.yaml`
- `.helix/rules/*.yaml`
- `.helix/doc-map.yaml`
- `.helix/gate-checks.yaml`

### モノレポの場合

リポジトリ内の特定パッケージだけを HELIX 管理対象にする。

```bash
cd /path/to/mono-repo
helix init --monorepo-package packages/api
```

`helix init` 後のコマンドは、対象パッケージを `HELIX_PROJECT_ROOT` に指定して実行する。

```bash
HELIX_PROJECT_ROOT="$(pwd)/packages/api" helix matrix compile
HELIX_PROJECT_ROOT="$(pwd)/packages/api" helix gate G2
```

## 3. matrix を有効化（必須）

```bash
helix matrix init
helix matrix compile
helix matrix status
```

- `init`: `.helix/matrix.yaml` と `.helix/rules/` を生成
- `compile`: `matrix.yaml + rules` から runtime/state を生成
- `status`: feature x deliverable の状態を確認

## 4. `.helix/rules/` の使い方

`matrix compile` の挙動は `.helix/rules/` で制御する。

- `deliverables.yaml`: 成果物カタログとゲート責務
- `structure.yaml`: docs/src の生成パス規約
- `naming.yaml`: 命名規約・正規表現

編集後は必ず再コンパイル:

```bash
helix matrix compile --force
```

## 5. thinking level の設定

`helix codex` はロールごとにデフォルト thinking level を持つ。

```bash
helix codex --role se --task "認証 API の実装"
helix codex --role tl --task "設計レビュー" --thinking xhigh
helix codex --role docs --task "README 整備" --thinking low
```

有効値: `low | medium | high | xhigh`

## 6. 初回実行ガイド（最短）

```bash
# 1) サイズ判定
helix size --files 5 --lines 200 --type new-feature --drive be

# 2) 設計提案
helix plan draft --title "ユーザー認証 API"
helix plan review --id PLAN-001
helix plan finalize --id PLAN-001

# 3) 実装
helix codex --role se --task "ユーザー認証 API を実装"

# 4) ゲート確認
helix gate G4

# 5) 状態確認
helix status
```

## 7. よく使う新コマンド

```bash
helix matrix status
helix interrupt status
helix builder list
helix learn --all
helix promote --auto
helix discover --query "auth"
```

## 8. トラブルシューティング

### `helix: command not found`

```bash
export PATH="$HOME/ai-dev-kit-vscode/cli:$PATH"
source ~/.bashrc
```

### `.helix/matrix.yaml が見つかりません`

```bash
helix init
helix matrix init
```

### `matrix validate 失敗`

```bash
helix matrix validate
# エラー箇所を修正後
helix matrix compile
```

### `fullstack で helix sprint next が失敗する`

fullstack は track 指定が必須。

```bash
helix sprint next --track be
helix sprint next --track fe
```

### `--thinking` が無効と言われる

有効値のみ指定する。

```bash
helix codex --role pg --task "修正" --thinking medium
```

### `plan finalize` できない

`review` の verdict が `approve` になっている必要がある。

```bash
helix plan status --id PLAN-001
helix plan review --id PLAN-001
```

## 9. 最初のゲート通過チェック

```bash
helix gate G2
helix gate G3
helix gate G4
```

失敗時は `helix status` の Action Guide を確認し、不足成果物と検証結果を埋める。
