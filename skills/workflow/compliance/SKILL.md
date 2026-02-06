---
name: compliance
description: コンプライアンス・規制対応。ライセンス検証、データ保護、監査対応時に使用
metadata:
  helix_layer: L1
  triggers:
    - ライセンス確認時
    - データ保護対応時
    - 監査準備時
    - 規制要件確認時
  verification:
    - ライセンス互換性確認
    - データ保護要件充足
    - 監査証跡の完全性
compatibility:
  claude: true
  codex: true
---

# コンプライアンススキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- OSSライセンス確認・選定時
- 個人情報保護対応時（GDPR、個人情報保護法）
- セキュリティ監査準備時
- 規制要件の実装時

---

## 1. OSSライセンス管理

### ライセンス互換性マトリクス

| ライセンス | 商用利用 | 改変 | 配布 | 特許 | コピーレフト |
|-----------|---------|------|------|------|------------|
| MIT | ✅ | ✅ | ✅ | ❌ | なし |
| Apache 2.0 | ✅ | ✅ | ✅ | ✅ | なし |
| BSD 2/3 | ✅ | ✅ | ✅ | ❌ | なし |
| ISC | ✅ | ✅ | ✅ | ❌ | なし |
| MPL 2.0 | ✅ | ✅ | ✅ | ✅ | ファイル単位 |
| LGPL 2.1/3.0 | ✅ | ✅ | ✅ | ❌ | ライブラリ単位 |
| GPL 2.0/3.0 | ✅ | ✅ | ✅ | ❌ | 全体 |
| AGPL 3.0 | ✅ | ✅ | ✅ | ❌ | 全体+ネットワーク |

### リスクレベル

```
🟢 Low Risk（制約なし）
   MIT, Apache 2.0, BSD, ISC

🟡 Medium Risk（条件付き利用可）
   MPL 2.0, LGPL

🔴 High Risk（慎重な判断が必要）
   GPL, AGPL → プロジェクト全体に感染する可能性

⛔ 禁止
   SSPL, BSL → 商用利用制限あり
```

### 自動ライセンスチェック

```bash
# Node.js プロジェクト
npx license-checker --summary
npx license-checker --failOn "GPL-3.0;AGPL-3.0"

# Python プロジェクト
pip-licenses --format=table
pip-licenses --fail-on="GPL-3.0"

# CI/CD 統合
# .github/workflows/license-check.yml
```

```yaml
# GitHub Actions
name: License Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check licenses
        run: |
          npx license-checker --failOn "GPL-3.0;AGPL-3.0;SSPL-1.0"
```

---

## 2. データ保護

### GDPR / 個人情報保護法 対応

| 要件 | 実装 |
|------|------|
| データ最小化 | 必要最小限のデータのみ収集 |
| 同意管理 | 明示的な同意取得・記録 |
| アクセス権 | ユーザーデータのエクスポート機能 |
| 削除権 | ユーザーデータの完全削除機能 |
| データポータビリティ | JSON/CSVエクスポート |
| 漏洩通知 | 72時間以内の通知体制 |

### 個人情報の分類

```
■ 直接識別情報（PII）
  - 氏名、メールアドレス、電話番号
  - 住所、マイナンバー、パスポート番号
  → 暗号化必須、アクセスログ必須

■ 間接識別情報
  - IPアドレス、Cookie ID、デバイスID
  - 位置情報、行動履歴
  → 匿名化/仮名化を検討

■ 機微情報（センシティブ）
  - 健康情報、宗教、政治信条、性的指向
  → 明示的同意＋厳格なアクセス制御
```

### 実装パターン

```python
# データ削除（GDPR 削除権）
class GDPRService:
    async def delete_user_data(self, user_id: str) -> dict:
        """ユーザーデータの完全削除"""
        deleted = {
            "user_profile": await self.db.users.delete(user_id),
            "activity_logs": await self.db.logs.delete_by_user(user_id),
            "preferences": await self.db.preferences.delete(user_id),
            "sessions": await self.db.sessions.revoke_all(user_id),
        }

        # 監査ログ（匿名化して保持）
        await self.audit_log.record(
            action="user_data_deletion",
            anonymized_id=hash(user_id),
            deleted_categories=list(deleted.keys()),
            timestamp=datetime.utcnow()
        )

        return deleted

    async def export_user_data(self, user_id: str) -> dict:
        """ユーザーデータのエクスポート（ポータビリティ）"""
        return {
            "profile": await self.db.users.get(user_id),
            "activity": await self.db.logs.get_by_user(user_id),
            "preferences": await self.db.preferences.get(user_id),
            "exported_at": datetime.utcnow().isoformat()
        }
```

---

## 3. 監査証跡

### 監査ログ要件

```
必須記録項目:
  □ Who   - 操作者（ユーザーID、IPアドレス）
  □ What  - 操作内容（CRUD、権限変更）
  □ When  - タイムスタンプ（UTC）
  □ Where - 対象リソース
  □ Why   - 変更理由（必要に応じて）

保存要件:
  □ 改ざん不可（Append-only）
  □ 最低保持期間の遵守（業界による）
  □ 検索・フィルタリング可能
```

### 監査ログ実装

```python
from enum import Enum

class AuditAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_CHANGE = "permission_change"

class AuditLogger:
    def __init__(self, storage):
        self.storage = storage  # Append-only storage

    async def log(
        self,
        action: AuditAction,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        details: dict = None,
        ip_address: str = None
    ):
        entry = {
            "id": uuid4().hex,
            "timestamp": datetime.utcnow().isoformat(),
            "action": action.value,
            "actor_id": actor_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "details": details,
        }

        await self.storage.append(entry)
```

---

## 4. セキュリティコンプライアンス

### OWASP Top 10 チェック

| # | リスク | 対策 |
|---|--------|------|
| A01 | アクセス制御 | RBAC/ABAC実装、最小権限の原則 |
| A02 | 暗号化の不備 | TLS必須、AES-256、bcrypt |
| A03 | インジェクション | パラメータ化クエリ、入力検証 |
| A04 | 安全でない設計 | 脅威モデリング、セキュリティ設計 |
| A05 | セキュリティ設定ミス | ハードニング、デフォルト変更 |
| A06 | 脆弱なコンポーネント | 依存関係スキャン、自動更新 |
| A07 | 認証の不備 | MFA、セッション管理、パスワードポリシー |
| A08 | データ整合性の不備 | 署名検証、CI/CDセキュリティ |
| A09 | ログ・監視の不足 | 監査ログ、異常検知、アラート |
| A10 | SSRF | URL検証、内部ネットワーク制限 |

### 依存関係セキュリティ

```bash
# 脆弱性スキャン
npm audit
pip audit
snyk test

# CI/CD統合
# Dependabot, Renovate, Snyk
```

---

## 5. AI特有のコンプライアンス

### AI利用時の注意点

```
□ 機密データをLLMに送信しない
□ AIの出力に個人情報が含まれないか確認
□ AI生成コードのライセンスリスク確認
□ AI利用の透明性確保（AI利用の明示）
□ バイアスの検証
```

### データ分類とLLM利用可否

| データ分類 | 外部LLM | 自社LLM | 注意事項 |
|-----------|---------|---------|----------|
| 公開情報 | ✅ | ✅ | なし |
| 社内限定 | ⚠️ | ✅ | NDA確認 |
| 機密 | ❌ | ✅ | アクセス制御必須 |
| 個人情報 | ❌ | ⚠️ | 匿名化必須 |

---

## チェックリスト

### プロジェクト開始時

```
□ 使用OSSライセンスの確認
□ データ保護要件の特定
□ 監査要件の確認
□ セキュリティ要件の整理
□ AI利用ポリシーの確認
```

### リリース前

```
□ ライセンスチェック通過
□ 脆弱性スキャン通過
□ 個人情報の取り扱い確認
□ 監査ログの動作確認
□ 同意フローの確認
```
