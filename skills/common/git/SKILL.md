---
name: git
description: Git運用でブランチ命名規則・コミットメッセージフォーマット・PRテンプレートを提供
metadata:
  helix_layer: all
  triggers:
    - コミット時
    - ブランチ操作時
    - PR作成時
  verification:
    - "コミットメッセージ: Conventional Commits準拠（type: subject）"
    - "ブランチ名: feature/*/fix/*/hotfix/* パターン一致"
    - "機密情報なし（git diff --cached | grep -E 'password|secret|api_key' 0件）"
compatibility:
  claude: true
  codex: true
---

# Git運用スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- コミット時
- ブランチ操作時
- PR作成時

---

## 権限

| エージェント | コミット | プッシュ | PR作成 |
|-------------|---------|---------|--------|
| **Opus** | ✅ | ✅ | ✅ |
| **Sonnet** | ❌ | ❌ | ❌ |
| **Haiku** | ❌ | ❌ | ❌ |

```
⚠️ サブエージェントはコード変更のみ
⚠️ コミット・プッシュはOpusが統合後に実行
```

---

## コミットタイミング

### する

1. 機能単位で完結したとき
2. ユーザーが明示的に指示したとき
3. 大きな作業の区切り（途中保存）

### しない

1. 作業途中の中途半端な状態
2. テスト未通過
3. lint未通過
4. 複数機能を混ぜた状態

---

## コミットメッセージ

### フォーマット

```
<type>: <subject>

[body]

Co-Authored-By: Claude <model> <version> <noreply@anthropic.com>
```

### type一覧

| type | 用途 |
|------|------|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `refactor` | リファクタリング |
| `docs` | ドキュメント |
| `test` | テスト |
| `chore` | 雑務（依存関係等） |
| `style` | フォーマット |
| `perf` | パフォーマンス |

### 例

```
feat: Add user authentication

- Implement JWT token generation
- Add login/logout endpoints
- Include refresh token mechanism

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## ブランチ戦略

```
main (本番)
  └── develop (開発統合)
        ├── feature/xxx
        ├── fix/xxx
        └── refactor/xxx
```

### 命名規則

| ブランチ | 用途 | 例 |
|---------|------|-----|
| `feature/*` | 新機能 | `feature/user-auth` |
| `fix/*` | バグ修正 | `fix/login-error` |
| `refactor/*` | リファクタ | `refactor/api-structure` |
| `hotfix/*` | 緊急修正 | `hotfix/security-patch` |

---

## プッシュ前チェック

```bash
# 必須チェック
[ ] lint通過
[ ] テスト通過
[ ] コンフリクトなし
[ ] 機密情報なし

# コマンド例
npm run lint
npm run test
git status
git diff --cached | grep -E "(password|secret|api_key)"
```

### 禁止

```bash
# ❌ 強制プッシュ
git push --force

# ❌ main/developへ直接プッシュ
git push origin main
```

---

## PR作成

### テンプレート

```markdown
## Summary
- 変更内容を箇条書き

## Changes
- [ ] 変更ファイル1
- [ ] 変更ファイル2

## Test plan
- [ ] テスト項目1
- [ ] テスト項目2

## Related
- Issue: #xxx
- Docs: xxx.md
```

### マージ条件

1. CI通過（lint + test）
2. ユーザー承認
3. コンフリクト解消済み
