## テスト品質メトリクス

### 測定項目

```yaml
test_metrics:
  coverage:
    statement: 85%
    branch: 78%
    function: 90%

  pyramid:
    unit: 70%
    integration: 20%
    e2e: 10%

  reliability:
    flaky_rate: 2%  # 不安定テストの割合
    pass_rate: 98%  # 平均パス率

  performance:
    unit_avg: 50ms
    integration_avg: 500ms
    e2e_avg: 5s

  maintenance:
    test_to_code_ratio: 1.2  # テストコード/本番コード
    age_avg: 30days  # テストの平均年齢
```

### 品質ダッシュボード

```
┌─────────────────────────────────────────────┐
│              テスト品質ダッシュボード         │
├─────────────────────────────────────────────┤
│ カバレッジ                                   │
│ ████████████████░░░░ 85%                    │
│                                             │
│ ピラミッド比率                               │
│ Unit:        ███████░░░ 70%                 │
│ Integration: ██░░░░░░░░ 20%                 │
│ E2E:         █░░░░░░░░░ 10%                 │
│                                             │
│ 信頼性                                       │
│ Flaky:       2%  ✅                          │
│ Pass Rate:   98% ✅                          │
└─────────────────────────────────────────────┘
```

---

## Flaky Test対策

### 検出

```bash
# 同じテストを複数回実行
> 目的: 同じテストを複数回実行 の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

npm run test -- --repeat=10

# Flaky検出ツール
npx jest --detectOpenHandles
```

### 原因と対策

| 原因 | 対策 |
|------|------|
| 時間依存 | 時間をモック |
| 順序依存 | テストを独立化 |
| 非同期待機不足 | 適切なawait/waitFor |
| 外部サービス依存 | モック化 |
| リソース競合 | 並列実行制限 |

### Flakyテスト管理

```typescript
// 一時的にスキップ（期限付き）
describe.skip('Flaky test - TODO: fix by 2025-01-15', () => {
  // ...
});

// Flakyマーク（CI設定で除外可能に）
describe('Feature', () => {
  it.flaky('sometimes fails due to timing', () => {
    // ...
  });
});
```

---

## テスト実行最適化

### 並列実行

```bash
# Jest
jest --maxWorkers=4

# Playwright
npx playwright test --workers=4
```

### テスト分割

```yaml
# CI/CD でのテスト分割
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - run: npm test -- --shard=${{ matrix.shard }}/4
```

### 差分テスト

```bash
# 変更ファイルに関連するテストのみ
jest --changedSince=main

# 影響範囲テスト
jest --findRelatedTests src/services/auth.ts
```
