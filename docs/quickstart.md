# HELIX クイックスタート（5 分）

## 1. インストール（1 分）

```bash
bash ~/ai-dev-kit-vscode/setup.sh
```

## 2. プロジェクト初期化（1 分）

```bash
cd your-project
helix init
helix matrix init && helix matrix compile
```

## 3. サイジング（30 秒）

```bash
helix size --files 5 --lines 200 --type new-feature
```

## 4. 最初の設計（2 分）

```bash
helix plan draft --title "機能名"
# → .helix/plans/PLAN-001.yaml が生成される
```

## 5. 状態確認（30 秒）

```bash
helix status
# → 次にすべきことが表示される
```
