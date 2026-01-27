---
name: error-fix
description: error-fix関連タスク時に使用
---

# エラー修正スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- エラー発生時
- バグ修正時
- デバッグ時

---

## 修正フロー

```
1. エラー特定 → 再現確認
2. 原因調査 → 根本原因特定
3. 修正実装 → 最小限の変更
4. テスト → 再現しないことを確認
5. 影響範囲確認 → 他への副作用なし
```

---

## エラー分類と対応

### TypeScript / JavaScript

| エラー | 原因 | 対応 |
|--------|------|------|
| `Type 'X' is not assignable` | 型不一致 | 型定義確認、型ガード追加 |
| `Cannot read property of undefined` | null/undefined | オプショナルチェーン、早期リターン |
| `Module not found` | import パス | パス確認、tsconfig確認 |
| `any型検出` | 型不明 | 明示的な型定義 |

### Python

| エラー | 原因 | 対応 |
|--------|------|------|
| `ImportError` | モジュール不明 | パス確認、__init__.py確認 |
| `AttributeError` | 属性不在 | hasattr確認、Optional型 |
| `TypeError` | 型不一致 | 型ヒント確認、バリデーション |

### DB / SQL

| エラー | 原因 | 対応 |
|--------|------|------|
| `relation does not exist` | テーブル未作成 | マイグレーション実行 |
| `column does not exist` | カラム未作成 | マイグレーション確認 |
| `foreign key violation` | 参照整合性 | 依存データ確認 |

---

## デバッグ手順

### 1. 再現確認

```bash
# エラーを再現できる最小コード/コマンドを特定
# 「たまに起きる」は再現条件を特定するまで調査
```

### 2. ログ確認

```bash
# バックエンド
tail -f logs/app.log | grep ERROR

# フロントエンド
# ブラウザDevTools > Console

# DB
# クエリログ確認
```

### 3. 仮説検証

```
1. 仮説を立てる（原因はXだと思う）
2. 検証方法を決める（Xを確認するにはYを見る）
3. 検証実行
4. 仮説が外れたら次の仮説へ
```

---

## 修正原則

### する

```
✅ 最小限の変更で修正
✅ 根本原因を修正（対症療法ではなく）
✅ テストを追加（再発防止）
✅ 関連箇所も確認
```

### しない

```
❌ 「とりあえず動く」修正
❌ 原因不明のまま修正
❌ 大規模リファクタを混ぜる
❌ 他の機能追加を混ぜる
```

---

## よくあるパターン

### 非同期エラー

```typescript
// ❌ awaitが抜けている
const data = fetchData() // Promise返却
console.log(data.value)  // undefined

// ✅ await追加
const data = await fetchData()
console.log(data.value)
```

### null/undefined

```typescript
// ❌ 存在確認なし
const name = user.profile.name // userがnullでエラー

// ✅ オプショナルチェーン
const name = user?.profile?.name ?? 'Unknown'
```

### 循環参照

```typescript
// ❌ A imports B, B imports A
// moduleA.ts
import { B } from './moduleB'
// moduleB.ts
import { A } from './moduleA'

// ✅ 共通モジュールに抽出
// types.ts に共通型を定義
```

---

## 報告フォーマット

```markdown
## エラー内容
- メッセージ: xxx
- 発生箇所: xxx

## 原因
- 根本原因: xxx

## 修正内容
- 変更ファイル: xxx
- 変更内容: xxx

## テスト
- [ ] 再現しないことを確認
- [ ] 関連機能に影響なし
```
