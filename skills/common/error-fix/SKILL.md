---
name: error-fix
description: エラー修正で原因特定フロー・デバッグ手順・再現テストと修正パターンを提供
metadata:
  helix_layer: L4
  triggers:
    - エラー発生時
    - バグ修正時
    - デバッグ時
  verification:
    - "対象エラー: 再現テスト実行 exit code 0（エラー未発生）"
    - "既存テスト全通過(npm test / pytest exit code 0)"
    - "修正箇所の回帰テスト追加済み"
compatibility:
  claude: true
  codex: true
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

## 体系的デバッグ手法

### パッチ連鎖防止の原則

- 症状に対する場当たり修正を避け、**根本原因を特定してから**修正する
- 「一時的に動く」より「再発しない」を優先する
- 修正のたびに再現手順と検証手順を更新する

### 5段階デバッグフロー

1. 再現条件の確定（最小再現手順）
2. 仮説の列挙（原因候補を3つ以上）
3. 仮説の検証（1つずつ潰す、複数同時に変えない）
4. 根本原因の特定（なぜなぜ分析、5回の Why）
5. 修正と回帰テスト作成

### アンチパターン

- いきなり修正する（再現確認・仮説検証なし）
- 複数箇所を同時変更する（原因切り分け不能）
- テストなしで修正完了とする（再発防止不十分）

---

## 失敗パターンレジストリ

### 記録フォーマット（構造化）

失敗を「属人メモ」ではなく、以下の4要素で記録する。

- 症状（何が起きたか）
- 原因（なぜ起きたか）
- 修正方法（どう直したか）
- 再発防止策（次回どう防ぐか）

### SQLite テーブル設計案（`failure_patterns`）

```sql
CREATE TABLE IF NOT EXISTS failure_patterns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_run_id INTEGER NOT NULL,
  task_type TEXT NOT NULL,
  failure_type TEXT NOT NULL,
  symptom TEXT NOT NULL,
  root_cause TEXT NOT NULL,
  fix_summary TEXT NOT NULL,
  prevention TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_failure_patterns_task_type
  ON failure_patterns(task_type, failure_type, created_at);
```

### `helix learn --failure` 拡張提案

- 成功レシピだけでなく、失敗レシピも学習対象として保存する
- 失敗レシピは `success: false` と `failure_type` を持つ
- 同種タスク開始時に「過去失敗パターン」を先に提示する

### よくある失敗パターン集

#### Python

- import 循環（モジュール分割境界の不備）
- 型不一致（静的型と実データの乖離）
- async 漏れ（`await` 未使用、同期/非同期混在）

#### JavaScript / TypeScript

- this バインド不備（コールバック実行文脈の喪失）
- Promise 未処理（`unhandledrejection`）
- null チェーン未考慮（`undefined` アクセス）

#### DB

- N+1 クエリ（繰り返し参照で過剰クエリ）
- デッドロック（ロック順序不整合）
- マイグレーション順序ミス（依存関係の逆転）

### HELIX Learning Engine 連携

- `from_history()` が失敗レシピを検出した場合は警告を返す
- 警告形式:
  - `このパターンは過去に失敗しています: {reason}`
- 実装前に同一パターンの再発リスクを明示できる

---

## 危険コマンドガード

以下のパターンは、誤操作時の影響が大きいためデフォルトでブロック対象とする。

- `rm -rf /` / `rm -rf ~` / `rm -rf .`
- `chmod 777` / `chmod -R 777`
- `git push --force`（`main` / `master`）
- `DROP DATABASE` / `DROP TABLE`（本番）
- `kill -9`（PID 指定なし）
- `dd if=/dev/zero`
- `> /dev/sda`

### HELIX Phase Guard 連携提案

- コマンド実行前に危険パターンを静的検知
- 検知時は実行を中断し、代替コマンドまたは明示承認を要求
- G4/G6 ではブロックイベントを監査ログへ記録する

### 例外条件

- 人間による明示承認がある場合のみ実行可
- 運用上は `HELIX_GUARD=off` 相当を一時的に付与し、理由を記録する

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
