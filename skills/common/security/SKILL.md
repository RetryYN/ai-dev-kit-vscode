---
name: security
description: 脆弱性対策・OWASP・秘密情報管理を提供
metadata:
  helix_layer: all
  triggers:
    - 認証実装時
    - API公開時
    - セキュリティレビュー時
  verification:
    - "OWASP Top 10 チェック済み"
    - "機密情報ハードコード 0件"
    - "認証・認可テスト通過"
    - "SQL Injection/XSS 脆弱性 0件"
compatibility:
  claude: true
  codex: true
---

# セキュリティスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- 認証機能実装時
- API開発時
- セキュリティ監査時

---

## 1. 使い方（圧縮版）

1. まず脅威を列挙（資産 / 攻撃面 / 影響）
2. 認証・認可・入力検証を最初に固定
3. 通信防御と監視を同時に設計
4. OWASP 観点で欠落を洗い出す
5. secrets スキャンと運用ルールで締める

---

## 2. 最低限の設計原則

- デフォルト拒否（allow-list 優先）
- 最小権限（Least Privilege）
- 深層防御（Defense in Depth）
- 失敗時安全（Fail Safe）
- 監査可能性（Auditability）

---

## 3. 認証・認可の必須要件

### 認証

- 強固なパスワードポリシー
- トークン有効期限・失効戦略
- リフレッシュトークン管理
- セッション固定化対策

### 認可

- RBAC または ABAC を明示
- リソース単位のアクセス判定
- 管理者経路を分離
- 権限変更の監査ログ

---

## 4. 入力検証とアプリ防御

- 入力は全経路でバリデーション
- SQL は必ずプレースホルダ利用
- 出力エスケープ（文脈依存）
- CSRF token / SameSite cookie の適用
- ファイルアップロード検査（型・サイズ）

---

## 5. 通信とヘッダー

- HTTPS 強制（HSTS）
- セキュリティヘッダー設定
  - `Content-Security-Policy`
  - `X-Frame-Options`
  - `X-Content-Type-Options`
  - `Referrer-Policy`
- CORS は必要 origin のみに限定

---

## 6. レート制限と監視

- ログイン・重要API にレート制限
- 短期 burst と長期 quota を分離
- 認可失敗・異常アクセスをアラート
- 監査ログは改ざん耐性を持たせる

---

## 7. OWASP 適用方針

### OWASP Top 10

- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable and Outdated Components
- A07: Identification and Authentication Failures
- A08: Software and Data Integrity Failures
- A09: Security Logging and Monitoring Failures
- A10: Server-Side Request Forgery

### OWASP Agentic Top 10

- プロンプトインジェクション
- 過剰権限エージェント
- 危険ツール呼び出し
- 機密情報漏えい
- 自律実行の暴走

---

## 8. 秘密情報管理

- secret は環境変数/秘密管理基盤へ集約
- リポジトリに `.env` を含めない
- 鍵・証明書の混入を自動検査
- ローテーション手順を文書化

---

## 9. AI 生成コードレビュー観点

- 認可抜け（所有者チェック欠落）
- 例外時に秘密値を返す実装
- 検証不足のまま DB 反映
- 外部入力を信頼するプロンプト

---

## 10. 参照インデックス（詳細）

元内容は以下に分割保全している。

- `references/environment-and-secrets.md`
  - 環境別設定、秘密情報管理、`.gitignore`、環境変数検査
- `references/auth-and-authorization.md`
  - 認証方式、JWT、パスワードポリシー、RBAC 実装
- `references/app-transport-monitoring.md`
  - 入力検証、SQLi/XSS/CSRF、HTTPS/CORS、監視
- `references/owasp-and-agentic.md`
  - OWASP Top 10、OWASP Agentic Top 10、運用手順
- `references/scanning-and-ai-quality.md`
  - secrets スキャン、鍵混入検査、AI 生成コード品質チェック

---

## 11. セキュリティゲート運用

- G2: 設計時に脅威と対策を紐付ける
- G4: 実装時に主要脆弱性の再点検
- G6: 受入前に運用監視の実効性確認
- G7: 本番監視とインシデント対応導線を確認

---

## 12. 完了判定

以下を満たした場合に完了:

- 重大脆弱性が残っていない
- secrets 混入が検出されない
- 認証/認可テストが通過している
- 監視アラートが運用可能な状態
- 参照リンクの欠落がない


---

## 13. 実務テンプレート

### 13.1 セキュリティレビュー記録

```markdown
## Security Review
- 対象:
- 日付:
- レビュア:

### Threats
- T1:
- T2:
- T3:

### Controls
- C1:
- C2:
- C3:

### Findings
- Critical:
- High:
- Medium:
- Low:

### Actions
- 即時対応:
- 次スプリント:
```

### 13.2 インシデント初動チェック

- 影響範囲の特定
- 証拠保全（ログ/監査証跡）
- 一時遮断と恒久対策の分離
- 再発防止策の記録

### 13.3 権限レビュー周期

- 管理者権限: 週次
- サービスアカウント: 月次
- API キー: ローテーション方針に従う

---

## 14. 変更レビュー観点

- 認可チェックの抜け漏れがないか
- エラーハンドリングで情報漏えいしないか
- ログに機密情報が含まれていないか
- CORS/CSRF 設定に過不足がないか
- 依存ライブラリの脆弱性が許容範囲か

---

## 15. 追加チェックリスト

### 実装前

- [ ] 認証方式を明文化
- [ ] 認可モデルを選定
- [ ] 脅威モデルを確認

### 実装中

- [ ] 入力検証を全経路へ適用
- [ ] セッション管理を固定
- [ ] 監査ログを実装

### 実装後

- [ ] secrets スキャン実行
- [ ] OWASP 観点レビュー完了
- [ ] 運用手順に反映

