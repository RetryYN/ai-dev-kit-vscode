---
name: quality-lv5
description: テスト品質をLv1-5で評価し、テストピラミッド比率とカバレッジ目標の検証手順を提供
metadata:
  helix_layer: L5
  triggers:
    - テスト作成完了時
    - 品質ゲート通過時
    - リリース前検証時
  verification:
    - "カバレッジ ≥70% (statement), ≥60% (branch)"
    - "テストピラミッド比率: Unit ≥60%, Integration 15-30%, E2E ≤15%"
    - "クリティカルパスカバレッジ 100% (優先度1必須)"
    - "Flaky率 <5%, テストパス率 >95%"
compatibility:
  claude: true
  codex: true
---

# テスト品質検証スキル（L5）

## 適用タイミング

このスキルは以下の場合に読み込む：
- テスト作成完了時の品質確認
- 品質ゲート通過判定時
- リリース前の最終検証時
- L5検証（テスト検証）実行時

---

## 1. 品質レベル定義

> **命名規約**: 本スキルのテスト品質レベル (T1-T5) は、企画書の開発成熟度 (M1-M5) とは別の軸。
> T = テスト品質の深さ、M = 実装全体の成熟度。

### T1: 最低限

```
□ 主要機能の正常系テスト
□ クリティカルバグの検出可能
目標: Unit 50%+
```

### T2: 基本

```
□ 正常系 + 主要異常系
□ バリデーションテスト
□ 境界値テスト
目標: Unit 60%+, Integration 主要フロー
```

### T3: 標準

```
□ 正常系 + 全異常系
□ エッジケース
□ 回帰テスト
目標: Unit 70%+, Integration 60%+
```

### T4: 高品質

```
□ T3 + パフォーマンステスト
□ セキュリティテスト
□ 負荷テスト
目標: Unit 80%+, Integration 70%+, E2E クリティカルパス
```

### T5: 最高品質

```
□ T4 + カオステスト
□ 耐障害性テスト
□ 継続的テスト
目標: Unit 90%+, Integration 80%+, E2E 全フロー
```

---

## 2. テストピラミッド検証

### 理想比率

```
        /\
       /  \      E2E: 10%
      /----\
     /      \    Integration: 20%
    /--------\
   /          \  Unit: 70%
  /------------\
```

### 比率計算

```typescript
// テスト数ベース
const ratio = {
  unit: unitTests.length / totalTests * 100,
  integration: integrationTests.length / totalTests * 100,
  e2e: e2eTests.length / totalTests * 100
};

// 判定
const isHealthy =
  ratio.unit >= 60 &&
  ratio.integration >= 15 &&
  ratio.integration <= 30 &&
  ratio.e2e <= 15;
```

### アンチパターン

```
❌ アイスクリームコーン（E2E過多）
   /████████\
   \████████/
    \██████/
     \████/
      \██/

❌ ホールグラス（中間層不足）
    /\
   /  \
  /    \
  |    |
  \    /
   \  /
    \/
```

---

## 3. カバレッジ検証

### 測定対象

```
□ ステートメントカバレッジ（行）
□ ブランチカバレッジ（分岐）
□ 関数カバレッジ（関数）
□ 条件カバレッジ（条件式）
```

### 目標設定

| レイヤー | 最低限 | 推奨 | 理想 |
|---------|-------|------|------|
| Unit | 60% | 80% | 90% |
| Integration | 40% | 60% | 70% |
| E2E | クリティカル | 主要フロー | 全フロー |

### 除外対象

```javascript
// カバレッジ除外の正当な理由
/* istanbul ignore next */
if (process.env.NODE_ENV === 'development') {
  // 開発時のみのコード
}

// 除外すべきでないもの
// - ビジネスロジック
// - エラーハンドリング
// - バリデーション
```

---

## 4. クリティカルパス検証

### クリティカルパスの定義

```
優先度1（必須）:
□ ユーザー認証フロー
□ 決済フロー
□ 主要CRUD操作

優先度2（重要）:
□ パスワードリセット
□ 通知送信
□ データエクスポート

優先度3（通常）:
□ 設定変更
□ 検索・フィルタ
□ 表示オプション
```

### クリティカルパステスト

```typescript
describe('Critical Path: User Authentication', () => {
  test('CP-001: User can register with valid data', async () => {
    // 正常系
  });

  test('CP-002: User can login with correct credentials', async () => {
    // 正常系
  });

  test('CP-003: User cannot login with wrong password', async () => {
    // 異常系
  });

  test('CP-004: User can reset password', async () => {
    // リカバリーパス
  });
});
```

---

## 5. テスト品質メトリクス・Flaky対策・実行最適化

→ 詳細は `references/advanced.md` を参照

### 主要メトリクス

| 指標 | 推奨値 |
|------|--------|
| Flaky率 | < 5% |
| パス率 | > 95% |
| テスト/コード比 | > 1.0 |
| Unit平均実行時間 | < 100ms |

---

## 6. 品質ゲート

### 通過条件

```yaml
quality_gate:
  coverage:
    min_statement: 70%
    min_branch: 60%

  tests:
    must_pass: true
    max_flaky: 5%

  new_code:
    min_coverage: 80%
    no_new_bugs: true

  security:
    no_critical: true
    no_high: true
```

### CI/CD統合

```yaml
# GitHub Actions
test:
  steps:
    - run: npm test -- --coverage
    - name: Quality Gate
      run: |
        coverage=$(cat coverage/coverage-summary.json | jq '.total.statements.pct')
        if (( $(echo "$coverage < 70" | bc -l) )); then
          echo "Coverage below threshold: $coverage%"
          exit 1
        fi
```

---

## チェックリスト

### テスト作成時

```
□ 正常系テスト
□ 異常系テスト
□ 境界値テスト
□ エッジケーステスト
```

### 品質検証時

```
□ カバレッジ目標達成
□ ピラミッド比率確認
□ クリティカルパス網羅
□ Flakyテストなし
```

### リリース前

```
□ 全テスト通過
□ 品質ゲート通過
□ パフォーマンステスト
□ セキュリティテスト
```
