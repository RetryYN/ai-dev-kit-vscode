---
name: migration
description: migration関連タスク時に使用
---

# 移行スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- システム移行時
- データ移行時
- 技術スタック変更時

---

## 1. 移行の種類

| 種類 | 説明 | 例 |
|------|------|-----|
| データ移行 | DBデータの移動・変換 | MySQL→PostgreSQL |
| システム移行 | アプリケーション刷新 | モノリス→マイクロサービス |
| インフラ移行 | 環境の移動 | オンプレ→クラウド |
| 技術移行 | フレームワーク変更 | Vue→React |

---

## 2. 移行戦略

### ビッグバン移行

```
旧システム ─────停止─────→ 新システム
              ↓
           一括切り替え

メリット:
- シンプル
- 並行運用不要

デメリット:
- リスク高
- ロールバック困難
- ダウンタイム必要

適用:
- 小規模システム
- リスク許容可能
```

### 段階的移行（Strangler Fig）

```
旧システム ──┬─────→ 機能A（新）
            ├─────→ 機能B（旧→新）
            └─────→ 機能C（旧）

メリット:
- リスク低
- 段階的に検証
- ロールバック容易

デメリット:
- 期間が長い
- 並行運用コスト
- 複雑性

適用:
- 大規模システム
- ミッションクリティカル
```

### 並行運用移行

```
旧システム ─────稼働─────→ 停止
新システム ─────稼働─────→ 継続

メリット:
- 比較検証可能
- 即座に切り戻し

デメリット:
- 2倍のコスト
- データ同期必要

適用:
- 高可用性要件
- 検証重要
```

---

## 3. データ移行

### 移行フロー

```
1. 現状分析
   └─ スキーマ、データ量、依存関係

2. 移行設計
   └─ マッピング、変換ルール、検証方法

3. ツール準備
   └─ ETLスクリプト、検証スクリプト

4. テスト移行
   └─ 本番データのコピーで検証

5. 本番移行
   └─ 計画実行、検証

6. 検証・切り替え
   └─ データ整合性確認、アプリ切り替え
```

### ETLスクリプト例

```python
import psycopg2
from datetime import datetime

class DataMigrator:
    def __init__(self, source_conn, target_conn):
        self.source = source_conn
        self.target = target_conn
        self.batch_size = 1000
    
    def migrate_users(self):
        """usersテーブルの移行"""
        offset = 0
        total = 0
        
        while True:
            # 抽出
            source_cursor = self.source.cursor()
            source_cursor.execute(f"""
                SELECT id, name, email, created_at
                FROM users
                ORDER BY id
                LIMIT {self.batch_size} OFFSET {offset}
            """)
            rows = source_cursor.fetchall()
            
            if not rows:
                break
            
            # 変換 & ロード
            target_cursor = self.target.cursor()
            for row in rows:
                transformed = self._transform_user(row)
                target_cursor.execute("""
                    INSERT INTO users (id, name, email, created_at, migrated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email
                """, transformed)
            
            self.target.commit()
            total += len(rows)
            offset += self.batch_size
            
            print(f"Migrated {total} users")
        
        return total
    
    def _transform_user(self, row):
        """データ変換ロジック"""
        id, name, email, created_at = row
        return (
            id,
            name.strip(),  # 前後空白除去
            email.lower(),  # 小文字化
            created_at,
            datetime.now()  # 移行日時
        )
```

### データ検証

```python
class DataValidator:
    def __init__(self, source_conn, target_conn):
        self.source = source_conn
        self.target = target_conn
    
    def validate_counts(self, table: str) -> bool:
        """件数検証"""
        source_count = self._count(self.source, table)
        target_count = self._count(self.target, table)
        
        if source_count != target_count:
            print(f"❌ {table}: source={source_count}, target={target_count}")
            return False
        
        print(f"✅ {table}: {source_count} records")
        return True
    
    def validate_checksums(self, table: str, columns: list) -> bool:
        """チェックサム検証"""
        source_checksum = self._checksum(self.source, table, columns)
        target_checksum = self._checksum(self.target, table, columns)
        
        if source_checksum != target_checksum:
            print(f"❌ {table}: checksum mismatch")
            return False
        
        print(f"✅ {table}: checksum match")
        return True
    
    def validate_samples(self, table: str, sample_ids: list) -> bool:
        """サンプルデータ検証"""
        for id in sample_ids:
            source_row = self._get_row(self.source, table, id)
            target_row = self._get_row(self.target, table, id)
            
            if source_row != target_row:
                print(f"❌ {table} id={id}: data mismatch")
                return False
        
        print(f"✅ {table}: sample validation passed")
        return True
```

---

## 4. 無停止移行（Zero Downtime）

### 双方向同期

```
Phase 1: 読み取りは旧、書き込みは両方
┌─────────┐    write    ┌─────────┐
│   App   │────────────→│   Old   │
│         │────────────→│   New   │
│         │←───read─────│   Old   │
└─────────┘             └─────────┘

Phase 2: 読み取りは新、書き込みは両方
┌─────────┐    write    ┌─────────┐
│   App   │────────────→│   Old   │
│         │────────────→│   New   │
│         │←───read─────│   New   │
└─────────┘             └─────────┘

Phase 3: 新のみ
┌─────────┐             ┌─────────┐
│   App   │────────────→│   New   │
│         │←────────────│         │
└─────────┘             └─────────┘
```

### Feature Flag活用

```python
from feature_flags import is_enabled

class UserRepository:
    def __init__(self, old_db, new_db):
        self.old_db = old_db
        self.new_db = new_db
    
    async def get_user(self, user_id: int):
        if is_enabled("use_new_db_read"):
            return await self.new_db.get_user(user_id)
        return await self.old_db.get_user(user_id)
    
    async def save_user(self, user: User):
        # 常に両方に書き込み
        await self.old_db.save_user(user)
        await self.new_db.save_user(user)
```

### CDC（Change Data Capture）

```yaml
# Debeziumでのリアルタイム同期
# docker-compose.yml
services:
  debezium:
    image: debezium/connect:2.4
    environment:
      BOOTSTRAP_SERVERS: kafka:9092
      CONFIG_STORAGE_TOPIC: debezium_configs
      OFFSET_STORAGE_TOPIC: debezium_offsets

# connector設定
{
  "name": "source-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "old-db",
    "database.port": "5432",
    "database.user": "replicator",
    "database.password": "secret",
    "database.dbname": "mydb",
    "table.include.list": "public.users,public.orders"
  }
}
```

---

## 5. ロールバック計画

### ロールバック判断基準

```
即時ロールバック:
🔴 データ不整合発生
🔴 重大な機能障害
🔴 パフォーマンス大幅劣化

判断保留（30分監視）:
🟡 軽微なエラー増加
🟡 一部機能の問題
```

### ロールバック手順書

```markdown
# ロールバック手順書

## 判断者
- プロジェクトマネージャー: @xxx
- テックリード: @yyy

## 手順

### 1. ロールバック宣言
Slackで宣言: "移行をロールバックします。理由: xxx"

### 2. トラフィック切り替え
```bash
# ロードバランサー切り替え
aws elbv2 modify-rule --rule-arn $RULE_ARN \
  --actions Type=forward,TargetGroupArn=$OLD_TARGET_GROUP
```

### 3. 新システム停止
```bash
kubectl scale deployment new-app --replicas=0
```

### 4. データ同期確認
- 移行中のデータ変更を旧システムに反映
- 検証スクリプト実行

### 5. 完了確認
- 旧システムの動作確認
- 監視ダッシュボード確認
- Slackで完了報告
```

---

## 6. 移行計画テンプレート

```markdown
# 移行計画書

## 概要
- 移行対象: 〇〇システム
- 移行方式: 段階的移行
- 移行期間: YYYY-MM-DD 〜 YYYY-MM-DD

## 移行スコープ
### 対象
- データベース: users, orders, products
- アプリケーション: API, 管理画面

### 対象外
- バッチ処理（次フェーズ）
- 外部連携（次フェーズ）

## スケジュール

| Phase | 期間 | 内容 |
|-------|------|------|
| 準備 | W1-W2 | 環境構築、ツール準備 |
| テスト | W3-W4 | テスト移行、検証 |
| 本番 | W5 | 本番移行 |
| 安定化 | W6-W8 | 監視、問題対応 |

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| データ不整合 | 高 | 検証スクリプト、ロールバック手順 |
| 性能劣化 | 中 | 負荷テスト、チューニング |
| 移行漏れ | 中 | チェックリスト、ダブルチェック |

## ロールバック計画
- 判断基準: 〇〇
- 手順: 〇〇
- 所要時間: 〇〇分

## 体制

| 役割 | 担当者 | 連絡先 |
|------|--------|--------|
| 移行リード | @xxx | Slack |
| DBA | @yyy | Slack |
| インフラ | @zzz | Slack |

## 承認
- [ ] プロジェクトマネージャー: @xxx
- [ ] テックリード: @yyy
- [ ] 運用チーム: @zzz
```

---

## チェックリスト

### 移行前

```
[ ] 現状分析完了
[ ] 移行計画承認
[ ] ツール準備完了
[ ] テスト移行成功
[ ] ロールバック手順確認
```

### 移行中

```
[ ] バックアップ取得
[ ] データ移行実行
[ ] 検証スクリプト実行
[ ] アプリ切り替え
[ ] 動作確認
```

### 移行後

```
[ ] 監視期間設定
[ ] 旧システム停止計画
[ ] ドキュメント更新
[ ] 振り返り実施
```
