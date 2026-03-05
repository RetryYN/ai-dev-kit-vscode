---
name: deploy
description: デプロイ・リリース・ロールバックのBlue/Green戦略と実行チェックリストを提供
metadata:
  helix_layer: L5
  triggers:
    - デプロイ実行時
    - リリース準備時
    - ロールバック時
  verification:
    - "デプロイ: exit code 0 + ヘルスチェック HTTP 200"
    - "スモークテスト: 主要エンドポイント HTTP 200"
    - "ロールバック手順: 文書化済み + テスト通過"
compatibility:
  claude: true
  codex: true
---

# デプロイ・リリーススキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- リリース準備時
- デプロイ実施時
- ロールバック時

## HELIX フェーズ位置づけ

- **HELIX フェーズ**: L5 デプロイ
- **ゲート定義**: `ai-coding/references/layer-interface.md §L5 内部ゲート` を参照（L5.1 準備 / L5.2 実行 / L5.3 安定性）
- **I/O 仕様**: `ai-coding/references/orchestration-workflow.md §L5: デプロイ` を参照
- **SLO/パフォーマンス基準**: `observability-sre/SKILL.md §7 劣化レベル表`（唯一の閾値権威源。本スキル内で重複定義しない）
- **前提**: 検証フェーズ完了（V-L5 テスト検証 pass + V-L6 運用検証 pass）

---

## 1. デプロイ戦略

### 戦略比較

| 戦略 | 概要 | リスク | 用途 |
|------|------|--------|------|
| **Recreate** | 旧停止→新起動 | 高（ダウンタイム） | 開発環境 |
| **Rolling** | 段階的に入れ替え | 中 | 一般的 |
| **Blue/Green** | 新環境に切り替え | 低 | 本番推奨 |
| **Canary** | 一部ユーザーから | 最低 | 大規模サービス |

### Blue/Green デプロイ

```
┌─────────────────────────────────────────┐
│  Load Balancer                          │
│       ↓（切り替え）                      │
├───────────────┬─────────────────────────┤
│  Blue（現行）  │   Green（新版）         │
│  v1.0.0       │   v1.1.0               │
│  稼働中 ✅    │   待機中 ⏸️             │
└───────────────┴─────────────────────────┘

手順:
1. Green環境に新版デプロイ
2. Green環境で動作確認
3. LBをGreenに切り替え
4. 問題あればBlueに切り戻し
5. 安定したらBlue環境を更新
```

### Canaryデプロイ

```
Phase 1: 5%のトラフィックを新版へ
Phase 2: 問題なければ25%へ
Phase 3: 問題なければ50%へ
Phase 4: 問題なければ100%へ

各フェーズで監視:
- エラー率
- レスポンスタイム
- ビジネスメトリクス
```

---

## 2. リリースフロー

### 標準フロー

```
1. リリースブランチ作成
   └─ release/v1.1.0

2. ステージング環境デプロイ
   └─ 動作確認、QAテスト

3. リリース承認
   └─ チェックリスト確認、承認者サイン

4. 本番デプロイ
   └─ 計画時間に実施

5. 動作確認
   └─ ヘルスチェック、主要機能確認

6. リリース完了宣言
   └─ Slackで通知

7. タグ付け
   └─ git tag v1.1.0
```

### リリーススケジュール

```
定期リリース:
- 毎週火曜日 14:00（日本時間）
- 金曜・祝前日は避ける

緊急リリース:
- 承認者2名の承認必須
- ホットフィックスブランチから
- 最小限の変更のみ
```

---

## 3. リリースチェックリスト

### リリース前

```markdown
## リリース前チェックリスト

### コード
- [ ] 全テスト通過
- [ ] コードレビュー完了
- [ ] セキュリティスキャン通過（L5.1 ゲート基準）
  - [ ] `npm audit` / `pip-audit`: critical 0件（例外なし）
  - [ ] high: 新規追加 0件（既知受容リストは `docs/security/accepted-vulnerabilities.md` で管理）
  - [ ] 依存パッケージの既知 CVE: critical/high 0件（新規追加分）
  - [ ] 機密情報が .gitignore に登録済み（security/SKILL.md §2 参照）
- [ ] 静的解析（lint）通過

### 環境
- [ ] ステージングで動作確認済み
- [ ] マイグレーション確認済み
- [ ] 環境変数設定済み
- [ ] 外部サービス接続確認済み

### ドキュメント
- [ ] リリースノート作成
- [ ] API変更があれば仕様書更新
- [ ] 運用手順書更新（必要な場合）

### 体制
- [ ] リリース担当者確定
- [ ] ロールバック担当者確定
- [ ] 緊急連絡先確認

### 承認
- [ ] リリース承認者: @xxx
- [ ] 承認日時: YYYY-MM-DD HH:MM
```

### リリース中

```markdown
## リリース実施チェックリスト

- [ ] メンテナンスモード有効化（必要な場合）
- [ ] DBバックアップ取得
- [ ] デプロイ実行
- [ ] マイグレーション実行（必要な場合）
- [ ] ヘルスチェック確認
- [ ] 主要機能の動作確認
- [ ] メンテナンスモード解除
- [ ] 監視ダッシュボード確認
```

### リリース後

```markdown
## リリース後チェックリスト

- [ ] エラー率正常（observability-sre §7: none レベル維持）
- [ ] レスポンスタイム正常
- [ ] ログに異常なし
- [ ] ユーザーからの報告なし
- [ ] Extended Watch 完了（L5.3 pass 後 **60分間**、low 閾値で P2 Warning 監視）
- [ ] リリース完了通知送信
- [ ] Gitタグ作成
- [ ] リリースブランチマージ（main, develop）
```

---

## 4. ロールバック

### ロールバック判断基準

> **閾値の正本**: observability-sre/SKILL.md §7 劣化レベル表。以下は簡易参照。

| 判断 | 劣化レベル | 代表的な閾値（§7 参照） | アクション |
|------|-----------|---------------------|----------|
| 即時ロールバック | `high` / `critical` | エラー率 >2% / p95 >800ms / availability <99% | ロールバック実行 + 人間通知 |
| 判断保留（15分監視） | `medium` | エラー率 1-2% / p95 400-800ms | 調査開始 + 軽減策適用 |
| 継続 | `none` / `low` | エラー率 <1% / p95 <400ms | 継続（low は Extended Watch） |

**即時ロールバック（劣化レベルに関わらず）:**
- 🔴 主要機能が動作しない
- 🔴 データ不整合発生

### ロールバック手順

```bash
# 1. 切り戻し判断の宣言（Slack）
"リリース v1.1.0 をロールバックします。理由: エラー率上昇"

# 2. ロールバック実行
## Blue/Greenの場合
./scripts/switch-to-blue.sh

## Kubernetesの場合
kubectl rollout undo deployment/app

## 手動デプロイの場合
git checkout v1.0.0
./scripts/deploy.sh

# 3. 動作確認
curl https://api.example.com/health

# 4. 完了宣言
"ロールバック完了。v1.0.0で稼働中"
```

### ロールバック後

```
1. 原因調査
   - ログ分析
   - エラー内容確認
   - 再現手順特定

2. 修正
   - 原因特定
   - 修正PR作成
   - テスト追加

3. 再リリース
   - 通常フローで再デプロイ
   - より慎重に監視
```

---

## 5. DB マイグレーション

### 安全なマイグレーション

```
✅ 安全な変更
- カラム追加（NULL許可 or デフォルト値あり）
- インデックス追加（CONCURRENTLY）
- テーブル追加

⚠️ 注意が必要
- カラム削除（使用されていないこと確認）
- カラム名変更（アプリ側も同時変更）
- NOT NULL追加（既存データ確認）

❌ 危険（別手順）
- 大量データ更新
- カラム型変更
- テーブル再構築
```

### 無停止マイグレーション

```
例: カラム名変更（old_name → new_name）

Phase 1: 新カラム追加
- ALTER TABLE t ADD COLUMN new_name ...
- アプリ: old_name を読み書き

Phase 2: 両方に書き込み
- アプリ: old_name と new_name 両方に書き込み
- バッチ: 既存データを new_name にコピー

Phase 3: 新カラムから読み取り
- アプリ: new_name から読み取り、両方に書き込み

Phase 4: 旧カラム削除
- アプリ: new_name のみ使用
- ALTER TABLE t DROP COLUMN old_name
```

---

## 6. モニタリング

### リリース時の監視項目

> **SLO 基準の正本**: observability-sre/SKILL.md §7 の劣化レベル表。
> 以下はデプロイ時の即時監視用の閾値であり、SLO の簡易参照。
> 詳細な劣化レベル別アクションは observability-sre を参照すること。

| 項目 | 正常値（§7 none） | アラート閾値（§7 medium） |
|------|-------------------|-------------------------|
| エラー率 | ≤ 0.5% | > 2.0% |
| レスポンスタイム（p95） | ≤ 200ms | > 800ms |
| CPU使用率 | < 70% | > 90% |
| メモリ使用率 | < 80% | > 95% |
| DBコネクション | < 80% | > 90% |

### ダッシュボード確認

```
リリース後15分間は常時監視:
1. エラーログ
2. アプリケーションメトリクス
3. インフラメトリクス
4. ビジネスメトリクス（注文数、ログイン数等）
```

---

## 7. CI/CD パイプライン

### GitHub Actions例

```yaml
name: Deploy

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: docker build -t myapp:${{ github.sha }} .
      - name: Push
        run: docker push myregistry/myapp:${{ github.sha }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: ./scripts/deploy.sh staging ${{ github.sha }}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
      - name: Deploy to production
        run: ./scripts/deploy.sh production ${{ github.sha }}
```

---

## 8. 緊急リリース（ホットフィックス）

### フロー

```
1. ホットフィックスブランチ作成
   git checkout -b hotfix/v1.0.1 main

2. 最小限の修正
   - 問題の修正のみ
   - 他の変更を含めない

3. 緊急レビュー
   - 2名以上の承認

4. 本番デプロイ
   - 通常のチェックリストを短縮版で

5. マージ
   - main, developにマージ
```

### 緊急連絡先

```
## 緊急時連絡先

| 役割 | 担当者 | 連絡先 |
|------|--------|--------|
| リリース承認 | @xxx | Slack / 電話 |
| インフラ | @yyy | Slack / 電話 |
| バックエンド | @zzz | Slack / 電話 |
```

---

## チェックリスト

### リリース準備

```
[ ] テスト完了
[ ] レビュー完了
[ ] ステージング確認
[ ] リリースノート作成
[ ] ロールバック手順確認
```

### リリース実施

```
[ ] バックアップ取得
[ ] デプロイ実行
[ ] ヘルスチェック確認
[ ] 動作確認
[ ] 監視確認
```

### リリース完了

```
[ ] 完了通知送信
[ ] タグ作成
[ ] ドキュメント更新
```
