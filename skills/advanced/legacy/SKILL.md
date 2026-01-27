---
name: legacy
description: legacy関連タスク時に使用
---

# レガシーコード対応スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- レガシーシステム改修時
- 技術的負債解消時
- 段階的モダナイズ時

---

## 1. レガシーコードの定義

### レガシーコードとは

```
Michael Feathers の定義:
「テストのないコード」

一般的な特徴:
- テストがない
- ドキュメントがない
- 元の開発者がいない
- 古い技術スタック
- 複雑で理解困難
- 変更が怖い
```

### レガシー度の判定

| レベル | 特徴 | 対応方針 |
|--------|------|---------|
| 軽度 | テスト不足、ドキュメント不足 | テスト追加、ドキュメント整備 |
| 中度 | 設計問題、技術的負債 | 段階的リファクタリング |
| 重度 | スパゲッティ、理解不能 | Strangler Fig、書き換え検討 |

---

## 2. 改修の原則

### ボーイスカウトルール

```
「来た時よりも綺麗にして帰る」

- 触った箇所を少しだけ改善
- 大きな変更は避ける
- 積み重ねで改善
```

### 変更の安全性確保

```
1. 理解する前に変更しない
2. テストを書いてから変更
3. 小さく変更、頻繁にコミット
4. 動作確認を怠らない
```

### 優先順位

```
高優先:
□ セキュリティ脆弱性
□ 本番障害リスク
□ ビジネスクリティカルな機能

中優先:
□ パフォーマンス問題
□ 保守性の低いコード
□ 頻繁に変更する箇所

低優先:
□ めったに触らない箇所
□ 動いているコード
□ 見た目の問題
```

---

## 3. テスト追加戦略

### 特性テスト（Characterization Test）

```python
"""
現在の動作を記録するテスト
「正しい動作」ではなく「現在の動作」を保証
"""

def test_calculate_price_characterization():
    """現在の calculate_price の動作を記録"""
    # 既存の動作を観察して記録
    assert calculate_price(100, 0.1) == 90.0
    assert calculate_price(100, 0) == 100.0
    assert calculate_price(0, 0.1) == 0.0
    
    # 発見したエッジケース
    # 負の値を渡すと正の結果になる（バグ？仕様？）
    assert calculate_price(-100, 0.1) == 90.0  # 要確認
```

### ゴールデンマスターテスト

```python
"""
入出力の組み合わせを保存して比較するテスト
複雑なロジックの動作保証に有効
"""

import json
import hashlib

def test_report_generation_golden_master():
    # 現在の出力を生成
    result = generate_report(sample_data)
    
    # ゴールデンマスターと比較
    with open("golden_master/report.json") as f:
        expected = json.load(f)
    
    assert result == expected

# ゴールデンマスター更新（意図的な変更時のみ）
def update_golden_master():
    result = generate_report(sample_data)
    with open("golden_master/report.json", "w") as f:
        json.dump(result, f, indent=2)
```

### テスト追加の優先順位

```
1. バグ修正時 → 再発防止テスト
2. 機能追加時 → 新機能テスト + 既存機能の回帰テスト
3. リファクタリング前 → 特性テスト
4. 重要な機能 → 優先的にテスト追加
```

---

## 4. リファクタリング手法

### Sprout Method（新芽メソッド）

```python
# 既存の複雑なメソッドに新機能を追加したい場合

# Before: 既存のメソッド（触りたくない）
def process_order(order):
    # 100行の複雑なロジック
    ...

# After: 新機能は新しいメソッドとして追加
def process_order(order):
    # 100行の複雑なロジック
    ...
    # 新機能を呼び出し
    send_notification(order)  # 新しく追加

def send_notification(order):
    """新機能（テスト可能）"""
    # 新しいロジック
    ...
```

### Wrap Method（ラップメソッド）

```python
# 既存メソッドの前後に処理を追加したい場合

# Before
def pay(amount):
    # 支払い処理
    ...

# After
def pay(amount):
    log_payment_start(amount)  # 前処理
    _pay_original(amount)       # 元の処理
    log_payment_complete(amount)  # 後処理

def _pay_original(amount):
    # 元の支払い処理
    ...
```

### Extract Class（クラス抽出）

```python
# 巨大なクラスを分割

# Before: 神クラス
class Order:
    def calculate_total(self): ...
    def apply_discount(self): ...
    def validate_address(self): ...
    def send_email(self): ...
    def generate_pdf(self): ...

# After: 責務を分離
class Order:
    def __init__(self):
        self.calculator = OrderCalculator()
        self.validator = AddressValidator()
    
    def calculate_total(self):
        return self.calculator.calculate(self)

class OrderCalculator:
    def calculate(self, order): ...
    def apply_discount(self, order, discount): ...

class AddressValidator:
    def validate(self, address): ...
```

---

## 5. 依存関係の解消

### 依存性注入（DI）

```python
# Before: 直接依存（テスト困難）
class OrderService:
    def __init__(self):
        self.db = PostgresDatabase()  # 直接依存
        self.mailer = SMTPMailer()    # 直接依存

# After: 依存性注入（テスト可能）
class OrderService:
    def __init__(self, db: Database, mailer: Mailer):
        self.db = db
        self.mailer = mailer

# 本番
service = OrderService(PostgresDatabase(), SMTPMailer())

# テスト
service = OrderService(MockDatabase(), MockMailer())
```

### Seam（継ぎ目）の作成

```python
# グローバル関数への依存を注入可能にする

# Before
def process_payment(amount):
    current_time = datetime.now()  # テスト困難
    ...

# After: デフォルト引数で継ぎ目を作る
def process_payment(amount, get_time=datetime.now):
    current_time = get_time()
    ...

# テスト
def test_process_payment():
    fixed_time = lambda: datetime(2025, 1, 1)
    process_payment(100, get_time=fixed_time)
```

---

## 6. Strangler Fig パターン

### 段階的置き換え

```
Phase 1: Facade導入
┌─────────────┐
│   Facade    │
├─────────────┤
│ Legacy Code │
└─────────────┘

Phase 2: 一部を新実装に
┌─────────────┐
│   Facade    │
├──────┬──────┤
│ New  │Legacy│
└──────┴──────┘

Phase 3: 完全置き換え
┌─────────────┐
│   Facade    │
├─────────────┤
│  New Code   │
└─────────────┘
```

### 実装例

```python
class UserServiceFacade:
    """旧実装と新実装を切り替えるファサード"""
    
    def __init__(self, legacy_service, new_service, feature_flags):
        self.legacy = legacy_service
        self.new = new_service
        self.flags = feature_flags
    
    def get_user(self, user_id: int):
        if self.flags.is_enabled("new_user_service"):
            return self.new.get_user(user_id)
        return self.legacy.get_user(user_id)
    
    def create_user(self, data):
        # 新機能は新実装で
        return self.new.create_user(data)
    
    def update_user(self, user_id, data):
        # 移行中: 両方に書き込み
        result = self.new.update_user(user_id, data)
        self.legacy.update_user(user_id, data)  # 同期
        return result
```

---

## 7. ドキュメント整備

### 既存コードの理解

```markdown
# コード調査メモ

## 概要
- ファイル: src/legacy/order_processor.py
- 機能: 注文処理
- 作成: 2018年頃（推定）

## 主要なクラス/関数
- OrderProcessor.process(): メインの処理
- calculate_total(): 合計計算（割引ロジック複雑）

## 依存関係
- Database（直接依存）
- EmailService（直接依存）
- 外部API: PaymentGateway

## 問題点
- テストなし
- 1メソッド500行
- グローバル変数使用
- エラーハンドリング不十分

## 変更履歴（Git調査）
- 2020-03: 割引ロジック追加
- 2021-06: 税率変更対応
- 2022-01: バグ修正（#123）

## 今後の方針
1. 特性テスト追加
2. OrderCalculator抽出
3. DI導入
```

### 決定記録

```markdown
# 技術的負債返済記録

## 対象: OrderProcessor

### 決定事項
- リライトではなく段階的リファクタリング
- 理由: リライトはリスクが高い、ビジネス要件が複雑

### 実施計画
| Phase | 内容 | 期間 |
|-------|------|------|
| 1 | 特性テスト追加 | 1週間 |
| 2 | Calculator抽出 | 1週間 |
| 3 | DI導入 | 1週間 |

### 完了基準
- テストカバレッジ 80%以上
- 1メソッド50行以下
- 循環的複雑度 10以下
```

---

## 8. 避けるべきアンチパターン

### やってはいけないこと

```
❌ 理解せずに変更
   → 予期しないバグを生む

❌ 一度に大規模リファクタリング
   → リスクが高い、戻れない

❌ テストなしで変更
   → 回帰バグの温床

❌ 「後で直す」を放置
   → 負債が雪だるま式に増加

❌ 完璧を目指す
   → 終わらない、ビジネス価値がない
```

### 現実的なアプローチ

```
✅ 小さく、頻繁に改善
✅ 触る箇所だけ改善
✅ テストを先に書く
✅ 動くものを壊さない
✅ 記録を残す
```

---

## チェックリスト

### 改修前

```
[ ] コードを読んで理解
[ ] 影響範囲を把握
[ ] テストを追加
[ ] 小さな変更に分割
```

### 改修中

```
[ ] 頻繁にコミット
[ ] テストが通ることを確認
[ ] 動作確認
[ ] レビューを受ける
```

### 改修後

```
[ ] ドキュメント更新
[ ] 知見を共有
[ ] 次の改善点を記録
```
