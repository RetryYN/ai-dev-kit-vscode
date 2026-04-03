---
name: refactoring
description: コード構造改善で責務分離パターン・共通化判断基準・デグレ対策手順を提供
metadata:
  helix_layer: L2
  triggers:
    - コード改善時
    - 技術的負債の解消時
    - パフォーマンス最適化時
    - 可読性向上時
  verification:
    - "既存テスト全通過（npm test / pytest exit code 0）"
    - "lint 0 errors（eslint / ruff）"
    - "カバレッジ: リファクタ前後で低下なし"
compatibility:
  claude: true
  codex: true
---

# リファクタリングスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- コード改善時
- 技術的負債の解消時
- パフォーマンス最適化時
- 可読性向上時

---

## 1. リファクタリング原則

### いつやるか

```
✅ やる
- 機能追加の前（準備リファクタ）
- バグ修正時（理解のためのリファクタ）
- コードレビュー後
- テストが十分にある時

❌ やらない
- 締め切り直前
- テストがない時
- 理解していないコード
- 機能追加と同時（分離する）
```

### リファクタリングの範囲

```
小: 変数名変更、メソッド抽出
中: クラス分割、責務移動
大: アーキテクチャ変更、設計変更

⚠️ 大きなリファクタは分割して段階的に
```

---

## 2. 共通化ルール

### DRY原則（Don't Repeat Yourself）

```
同じコードが3回出たら共通化を検討

⚠️ ただし過度な共通化は避ける
⚠️ 「たまたま同じ」と「本質的に同じ」を区別
```

### 共通化の判断基準

| 状況 | 判断 |
|------|------|
| 同じロジックが3箇所以上 | 共通化 ✅ |
| 2箇所だが今後増える見込み | 共通化 ✅ |
| 2箇所で変更頻度が違う | 分離のまま ❌ |
| 似てるが微妙に違う | 分離のまま ❌ |

### 共通化パターン

```typescript
// ❌ 重複コード
function getUserName(user: User) {
  return `${user.lastName} ${user.firstName}`
}
function getAdminName(admin: Admin) {
  return `${admin.lastName} ${admin.firstName}`
}

// ✅ 共通化
interface HasName {
  lastName: string
  firstName: string
}
function getFullName(person: HasName) {
  return `${person.lastName} ${person.firstName}`
}
```

### 共通化レイヤー

```
utils/        → 純粋関数、汎用ユーティリティ
helpers/      → ドメイン固有のヘルパー
services/     → ビジネスロジック
components/   → UIコンポーネント
hooks/        → React Hooks
```

---

## 3. 分割ルール

### 単一責任原則（SRP）

```
1クラス/1関数 = 1責務

変更理由が複数ある → 分割すべき
```

### 関数分割の基準

| 指標 | 閾値 | 対応 |
|------|------|------|
| 行数 | 20行超 | 分割検討 |
| 引数 | 3個超 | オブジェクト化 or 分割 |
| ネスト | 3段超 | 早期リターン or 分割 |
| 分岐 | 5個超 | ポリモーフィズム検討 |

### 分割パターン

```typescript
// ❌ 巨大関数
function processOrder(order: Order) {
  // バリデーション（20行）
  // 在庫確認（15行）
  // 決済処理（30行）
  // 通知送信（10行）
  // ログ記録（5行）
}

// ✅ 責務で分割
function processOrder(order: Order) {
  validateOrder(order)
  checkInventory(order)
  processPayment(order)
  sendNotification(order)
  logTransaction(order)
}
```

### ファイル分割の基準

| 指標 | 閾値 | 対応 |
|------|------|------|
| 行数 | 300行超 | 分割検討 |
| クラス数 | 2個超 | 1ファイル1クラス |
| export数 | 5個超 | 関連性で分割 |

### モジュール分割

```
機能凝集:     1つの機能を完結させる（推奨）
論理凝集:     似た処理をまとめる（まあまあ）
時間凝集:     同時に実行される処理（避ける）
偶発的凝集:   たまたま一緒（避ける）
```

---

## 4. デグレ対策

### テストファースト

```
1. 既存の動作を確認するテストを書く
2. テストが通ることを確認
3. リファクタリング実施
4. テストが通ることを確認
5. 追加テストがあれば書く
```

### テストカバレッジ

```
リファクタリング前に確認:
[ ] 正常系テストあり
[ ] 異常系テストあり
[ ] 境界値テストあり
[ ] 変更箇所のカバレッジ十分
```

### 段階的変更

```
大きな変更 → 小さなステップに分割

1. インターフェースを先に作る
2. 新実装を並行して作る
3. 呼び出し元を段階的に切り替え
4. 旧実装を削除
```

### Strangler Figパターン

```
┌─────────────────────────────────────────┐
│  旧システム                              │
│  ┌─────────────────────────────────┐    │
│  │  新システム（徐々に拡大）        │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘

1. 新機能は新システムに実装
2. 旧機能を段階的に移行
3. 最終的に旧システムを廃止
```

### 後方互換性

```typescript
// ❌ 破壊的変更
function getUser(id: string): User  // 旧
function getUser(id: number): User  // 新（既存コード壊れる）

// ✅ 後方互換を保つ
function getUser(id: string | number): User
// または
function getUserById(id: number): User  // 新APIを追加
```

### デグレ検出

```bash
# 変更前後の比較
npm run test:snapshot  # スナップショットテスト
npm run test:e2e       # E2Eテスト
npm run test:visual    # ビジュアルリグレッション

# カナリアリリース
1. 5%のユーザーに新コード
2. エラー率監視
3. 問題なければ段階的に拡大
```

---

## 5. コードスメル検出

### よくあるスメル

| スメル | 症状 | 対策 |
|--------|------|------|
| Long Method | 20行超の関数 | Extract Method |
| Large Class | 300行超のクラス | Extract Class |
| Long Parameter List | 3引数超 | Parameter Object |
| Duplicated Code | 同じコード3箇所 | Extract Method/Class |
| Feature Envy | 他クラスのデータばかり使う | Move Method |
| Data Clumps | 同じデータの組が複数箇所 | Extract Class |
| Primitive Obsession | プリミティブ型の多用 | Value Object |
| Switch Statements | 長いswitch文 | ポリモーフィズム |
| Parallel Inheritance | 継承が並行して増える | Composition |
| Comments | コメントで説明が必要 | Rename/Extract |

### 自動検出ツール

```bash
# ESLint（複雑度）
eslint --rule 'complexity: ["error", 10]'

# SonarQube
sonar-scanner

# Code Climate
codeclimate analyze
```

---

## 自動リファクタリング提案

### コンセプト

コードの「臭い」を自動検出し、優先度付きでリファクタリング候補を提案する。

### 検出パターン（rg ベース）

```bash
# 重複コード: 同一パターンの3回以上出現
rg -c "パターン" --type py | awk -F: '$2>=3'

# 長すぎる関数: 行数 > 50
rg -l --type py | xargs -I{} awk '/^def /{n=NR}/^[^ ]/{if(NR-n>50)print FILENAME":"n}' {}

# 深すぎるネスト: インデント4段以上（目安）
rg -n "^( {16,}|\\t{4,})" --type py

# パラメータ過多: 引数5個以上（目安）
rg -n "^def [a-zA-Z0-9_]+\\([^\\)]{40,}\\):" --type py

# Godクラス: メソッド20個以上（目安）
rg -n "^\\s*def " --type py | awk -F: '{print $1}' | sort | uniq -c | awk '$1>=20'
```

### リファクタリング候補の優先順位

1. 変更頻度が高い箇所（`git log --follow`）
2. テストカバレッジが低い箇所
3. 依存が多い箇所（import 数）

### HELIX 統合

- G4 ゲートで `debt_register` に自動登録する
- `helix learn` に「リファクタリング成功パターン」を蓄積する
- `gate-policy` のリファクタリング運用ルールと連携する

---

## 6. リファクタリングカタログ

### Extract Method

```typescript
// Before
function printOwing() {
  console.log("*****")
  console.log("Banner")
  console.log("*****")
  // 詳細計算...
}

// After
function printOwing() {
  printBanner()
  printDetails()
}
```

### Replace Conditional with Polymorphism

```typescript
// Before
function getSpeed(vehicle: Vehicle) {
  switch (vehicle.type) {
    case 'car': return vehicle.baseSpeed * 1.0
    case 'bike': return vehicle.baseSpeed * 0.8
    case 'truck': return vehicle.baseSpeed * 0.6
  }
}

// After
interface Vehicle {
  getSpeed(): number
}
class Car implements Vehicle {
  getSpeed() { return this.baseSpeed * 1.0 }
}
```

### Introduce Parameter Object

```typescript
// Before
function amountInvoiced(start: Date, end: Date, customer: Customer)
function amountReceived(start: Date, end: Date, customer: Customer)

// After
interface DateRange { start: Date; end: Date }
function amountInvoiced(range: DateRange, customer: Customer)
function amountReceived(range: DateRange, customer: Customer)
```

---

## 技術負債の体系的管理

### 負債の分類

| 種類 | 例 | 緊急度 | 対処 |
|------|-----|--------|------|
| 意図的負債 | 「今は動くが将来問題」 | 低 | 台帳化 + 計画的返済 |
| 無意識的負債 | 設計ミス、知識不足 | 中 | 検出 → 台帳化 → 次スプリントで返済 |
| 環境的負債 | ライブラリ EOL、脆弱性 | 高 | 即時対応 or 期限付き計画 |
| テスト負債 | カバレッジ不足、flaky テスト | 中 | 20% 改善枠で返済 |

### 判断フロー（迷ったらこれ）

1. まず「本番事故に直結するか」を判定（脆弱性/EOL/認証不備は高優先）
2. 直近スプリントで触る領域の負債を優先返済（変更時に同時解消）
3. 触らない領域は台帳化して返済期限を設定
4. 返済不可なら ADR/台帳に「受容理由」「見直し日」を残す

### HELIX `helix debt` との統合

- `helix debt add` で負債を台帳化する
- G4 で `debt_register` 存在チェックを実施する
- イテレーション 20% を改善枠として固定する
- `helix bench` で負債数の推移を追跡する

### 自動検出パターン（rg ベース）

```bash
# TODO / FIXME / HACK / WORKAROUND の一覧化
rg -n "TODO|FIXME|HACK|WORKAROUND" .

# 依存ライブラリの EOL/更新遅延を確認
npm outdated
pip list --outdated

# 循環依存の検出（Node.js 例）
npx madge --circular src

# 重複コードの検出（トークンベース）
npx jscpd .
```

### 運用ルール（gate-policy 連携）

- G4 通過条件として「未解決 debt の台帳化」を必須とする
- L8 後に返済タスクを次イテレーションへ移送する
- リファクタ実装は freeze-break を避け、原則 L4 着手前または次イテレーションで行う

---

## チェックリスト

### リファクタリング前

```
[ ] テストが十分にある
[ ] 変更範囲が明確
[ ] 機能追加と分離している
[ ] チームに共有済み
```

### リファクタリング後

```
[ ] テストが全て通る
[ ] パフォーマンス劣化なし
[ ] 可読性が向上した
[ ] コードレビュー済み
```
