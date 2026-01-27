## 4. ADR（Architecture Decision Record）

### テンプレート

```markdown
# ADR-001: 認証方式の選定

## ステータス

承認済み（2025-01-15）

## コンテキスト

ユーザー認証の方式を決定する必要がある。
要件:
- SPAとモバイルアプリの両方に対応
- セッション管理の負荷を下げたい
- セキュリティを確保

## 検討した選択肢

### 1. セッションベース認証

メリット:
- 実装がシンプル
- 即時無効化が容易

デメリット:
- サーバー側でセッション管理が必要
- スケールアウト時にセッション共有が必要

### 2. JWT認証

メリット:
- ステートレス
- スケールしやすい

デメリット:
- トークン無効化が難しい
- トークンサイズが大きい

### 3. JWT + リフレッシュトークン

メリット:
- ステートレス（短期トークン）
- 長期セッション維持可能
- リフレッシュトークンで無効化可能

デメリット:
- 実装が複雑

## 決定

**JWT + リフレッシュトークン** を採用する

理由:
- SPAとモバイルの両方に対応できる
- 短いアクセストークン（15分）でセキュリティ確保
- リフレッシュトークンで長期セッション対応

## 影響

- アクセストークン: 15分、ステートレス
- リフレッシュトークン: 7日、DBで管理
- ログアウト時はリフレッシュトークンを無効化
```

### ADR管理

```
docs/
└── adr/
    ├── 000-template.md
    ├── 001-auth-method.md
    ├── 002-database-selection.md
    └── 003-api-versioning.md
```

---

## 5. 運用手順書

### テンプレート

```markdown
# デプロイ手順書

## 概要

本番環境へのデプロイ手順

## 前提条件

- [ ] 本番環境へのSSHアクセス権
- [ ] デプロイ承認済み
- [ ] ステージングでの動作確認済み

## 手順

### 1. 事前準備（10分前）

1. Slackでデプロイ開始を通知
   ```
   @channel 本番デプロイを開始します（v1.2.3）
   ```

2. 監視ダッシュボードを開く
   - Grafana: https://grafana.example.com
   - エラー監視: https://sentry.example.com

### 2. バックアップ（5分）

```bash
ssh production
pg_dump -Fc mydb > backup_$(date +%Y%m%d_%H%M%S).dump
```

### 3. デプロイ実行（5分）

```bash
# GitHub Actionsから実行
# または手動:
ssh production
cd /app
git fetch origin
git checkout v1.2.3
docker-compose pull
docker-compose up -d
```

### 4. 動作確認（5分）

```bash
# ヘルスチェック
curl https://api.example.com/health

# 主要機能確認
- [ ] ログイン
- [ ] ダッシュボード表示
- [ ] データ登録
```

### 5. 完了通知

```
@channel デプロイ完了しました（v1.2.3）
```

## ロールバック手順

問題発生時:

```bash
ssh production
cd /app
git checkout v1.2.2  # 前バージョン
docker-compose pull
docker-compose up -d
```

## 緊急連絡先

| 担当 | 連絡先 |
|------|--------|
| インフラ | @xxx |
| バックエンド | @yyy |
```

---

