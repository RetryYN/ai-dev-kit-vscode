---
name: dependency-map
description: 依存関係マップの作成と脆弱性・ライセンス・循環依存の検証観点を提供
metadata:
  helix_layer: L4
  triggers:
    - パッケージ追加・更新時
    - 外部サービス連携時
    - セキュリティ監査時
    - アップグレード計画時
  verification:
    - "npm audit / pip-audit 0 critical/high"
    - "npx license-checker --failOn 'GPL;AGPL' 通過"
    - "npx madge --circular 0件"
    - "依存関係マップ作成済み（内部/外部/サービス依存）"
    - "外部サービス障害: 影響評価シナリオ 未評価 0件"
compatibility:
  claude: true
  codex: true
---

# 依存関係マップスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- パッケージの追加・更新時
- 外部サービスとの連携時
- セキュリティ監査・脆弱性対応時
- メジャーアップグレード計画時
- L4検証（依存関係）実行時

---

## 1. 依存関係の分類

### 内部依存

```
src/
├── services/
│   ├── user-service.ts     ← auth-service に依存
│   └── auth-service.ts     ← db-client に依存
├── utils/
│   └── db-client.ts
└── components/
    └── LoginForm.tsx       ← auth-service に依存
```

### 外部依存（パッケージ）

```yaml
dependencies:
  runtime:           # 本番環境で必要
    - next: "14.0.0"
    - react: "18.2.0"
  dev:               # 開発時のみ
    - typescript: "5.0.0"
    - jest: "29.0.0"
  peer:              # 利用者が提供
    - react: ">=18"
```

### 外部サービス依存

```yaml
external_services:
  - name: "Stripe API"
    type: "payment"
    criticality: "high"
    fallback: "none"

  - name: "SendGrid"
    type: "email"
    criticality: "medium"
    fallback: "queue_and_retry"
```

---

## 2. 依存関係マップ作成

### 可視化

```
┌─────────────────────────────────────────┐
│                Frontend                  │
│  ┌──────────┐  ┌──────────┐            │
│  │LoginForm │──│ AuthHook │            │
│  └──────────┘  └────┬─────┘            │
└────────────────────│────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────┐
│                Backend                   │
│  ┌───────────┐  ┌───────────┐          │
│  │AuthService│──│UserService│          │
│  └─────┬─────┘  └─────┬─────┘          │
│        │              │                 │
│        ↓              ↓                 │
│  ┌───────────────────────┐             │
│  │      Database         │             │
│  └───────────────────────┘             │
└─────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────┐
│           External Services              │
│  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │ Stripe │  │SendGrid│  │  Auth0 │   │
│  └────────┘  └────────┘  └────────┘   │
└─────────────────────────────────────────┘
```

### 依存関係マトリクス

| モジュール | 依存先 | 依存の種類 | 結合度 |
|-----------|--------|-----------|--------|
| LoginForm | AuthHook | 直接 | 高 |
| AuthService | UserService | 直接 | 中 |
| AuthService | Database | 直接 | 高 |
| PaymentService | Stripe | 外部 | 高 |

---

## 3. 脆弱性検証

### 自動スキャン

```bash
# npm
npm audit
npm audit --production  # 本番依存のみ

# yarn
yarn audit

# pnpm
pnpm audit

# Python
pip-audit
safety check

# 汎用
snyk test
trivy fs .
```

### 脆弱性対応優先度

| 重大度 | 対応期限 | アクション |
|--------|---------|-----------|
| Critical | 24時間以内 | 即座にパッチ適用 or 削除 |
| High | 1週間以内 | 優先対応 |
| Medium | 1ヶ月以内 | 計画的対応 |
| Low | 次回更新時 | 併せて対応 |

### 脆弱性レポート

```yaml
vulnerability_report:
  scan_date: "2025-01-01"
  scanner: "npm audit"

  summary:
    critical: 0
    high: 1
    medium: 3
    low: 5

  findings:
    - package: "lodash"
      version: "4.17.20"
      vulnerability: "CVE-2021-23337"
      severity: "high"
      fixed_in: "4.17.21"
      action: "upgrade"
```

---

## 4. ライセンス検証

→ 互換性マトリクス・リスクレベルの詳細は `skills/workflow/compliance/SKILL.md` セクション1を参照

### クイックリファレンス

```
✅ 安全: MIT, Apache-2.0, BSD, ISC
⚠️ 注意: LGPL, MPL-2.0
❌ 禁止: GPL, AGPL, SSPL
```

### ライセンスチェックコマンド

```bash
# npm
npx license-checker --summary
npx license-checker --failOn "GPL;AGPL"

# Python
pip-licenses --format=table
pip-licenses --fail-on="GPL-3.0"

# 詳細レポート
npx license-checker --json > licenses.json
```

---

## 5. 循環依存の検出

### 検出ツール

```bash
# JavaScript/TypeScript
npx madge --circular src/
npx dpdm --circular src/

# Python
pydeps --show-cycles src/
```

### 循環依存の解消

```
Before (循環):
A → B → C → A

After (解消):
A → B → C
    ↓
    Interface (抽象化層)
    ↑
    A
```

### 解消パターン

1. **インターフェース抽出**: 共通インターフェースを定義
2. **依存性注入**: DIコンテナで解決
3. **イベント駆動**: イベントバスで疎結合化
4. **モジュール統合**: 密結合モジュールを統合

---

## 6. アップグレード戦略

### 依存関係の更新計画

```yaml
upgrade_plan:
  package: "next"
  current: "13.5.0"
  target: "14.0.0"
  type: "major"

  breaking_changes:
    - "App Router がデフォルトに"
    - "一部APIの廃止"

  migration_steps:
    - "依存パッケージの互換性確認"
    - "非推奨APIの置換"
    - "テスト実行"
    - "段階的ロールアウト"

  rollback_plan:
    - "package.json を戻す"
    - "npm install"
    - "キャッシュクリア"
```

### 更新優先度

```
1. セキュリティパッチ   → 即座
2. バグフィックス       → 週次
3. マイナーアップデート → 月次
4. メジャーアップデート → 計画的
```

---

## 7. 外部サービス依存管理

### サービス依存マップ

```yaml
external_dependencies:
  - service: "Stripe"
    purpose: "決済処理"
    criticality: "critical"
    sla: "99.9%"
    fallback:
      strategy: "queue_and_retry"
      max_retry: 3
      timeout: 30s

  - service: "SendGrid"
    purpose: "メール送信"
    criticality: "high"
    sla: "99.5%"
    fallback:
      strategy: "alternative_provider"
      alternative: "AWS SES"
```

### 障害時の影響評価

| サービス | 影響範囲 | 業務影響 | 復旧優先度 |
|---------|---------|---------|-----------|
| Stripe | 決済機能 | 売上停止 | P0 |
| SendGrid | 通知機能 | 遅延許容 | P2 |
| Auth0 | 認証機能 | ログイン不可 | P0 |

---

## チェックリスト

### パッケージ追加時

```
□ ライセンス確認
□ 脆弱性スキャン
□ バンドルサイズ確認
□ メンテナンス状況確認
□ 代替パッケージの検討
```

### 定期監査

```
□ npm audit 実行（週次）
□ ライセンスチェック（月次）
□ 依存関係の更新確認（月次）
□ 循環依存チェック（月次）
```

### アップグレード時

```
□ 破壊的変更の確認
□ 依存パッケージの互換性
□ テスト実行
□ ロールバック計画
□ 段階的デプロイ
```
