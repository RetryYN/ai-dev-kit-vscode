> 目的: OWASP Top 10 と Agentic Top 10 の診断観点を使うときに参照する

## OWASP Top 10 自動スキャン

OWASP Top 10 を `rg` で一次検出し、ヒット箇所をレビュー対象にする。
このスキャンは「脆弱性の可能性」を見つけるための補助であり、確定診断ではない。

| OWASP | 検出観点 | `rg` パターン例 |
|------|----------|------------------|
| A01: Broken Access Control | 管理権限の直書き・認可チェック漏れ | `rg -n "isAdmin\\s*=\\s*true|role\\s*==\\s*['\\\"]admin['\\\"]|/admin" --type py --type js --type ts` |
| A02: Cryptographic Failures | 弱いハッシュ・平文保存 | `rg -n "md5\\(|sha1\\(|AES-ECB|password.*plain|base64.*password" --type py --type js --type ts` |
| A03: Injection（SQLi） | 文字列連結SQL・危険なフォーマット | `rg -n "f['\\\"].*SELECT|execute\\(.*\\+|format\\(.*SELECT" --type py` |
| A03: Injection（XSS） | 危険な HTML 挿入 | `rg -n "innerHTML|dangerouslySetInnerHTML|v-html" --type js --type ts` |
| A04: Insecure Design | 開発用バックドア・デバッグ分岐残存 | `rg -n "bypass|backdoor|debug.*auth|skip.*auth" --type py --type js --type ts` |
| A05: Security Misconfiguration | デバッグ有効・危険な設定値 | `rg -n "DEBUG\\s*=\\s*True|CORS_ORIGINS:\\s*\\[\"\\*\"\\]|allow_origins=\\[\"\\*\"\\]" --type py --type js --type ts --type yaml` |
| A06: Vulnerable and Outdated Components | 古い依存・保守停止依存の放置 | `rg -n "(deprecated|unmaintained|end-of-life|known-vulnerable)" package.json package-lock.json requirements*.txt go.mod` |
| A07: Identification and Authentication Failures | 証明書検証無効・認証情報の直書き | `rg -n "verify=False|VERIFY_SSL.*False|password.*=.*['\\\"]" --type py` |
| A08: Software and Data Integrity Failures | 署名検証スキップ・unsafe deserialize | `rg -n "verify_signature\\s*=\\s*False|yaml\\.load\\(|pickle\\.loads\\(" --type py --type js --type ts` |
| A09: Security Logging and Monitoring Failures | 例外握り潰し・監査ログ不足 | `rg -n "except\\s+Exception:\\s+pass|logger\\.debug\\(.*token|print\\(.*password" --type py --type js --type ts` |
| A10: SSRF | 外部URLをそのまま取得 | `rg -n "requests\\.(get|post)\\(.*(url|uri)|axios\\.(get|post)\\(.*(url|uri)|fetch\\(.*(req\\.query|req\\.body)" --type py --type js --type ts` |

### 運用手順

```bash
# 例: まず OWASP A03（Injection）を重点スキャン
rg -n "f['\\\"].*SELECT|execute\\(.*\\+|format\\(.*SELECT" --type py
rg -n "innerHTML|dangerouslySetInnerHTML|v-html" --type js --type ts
```

```
1. ヒット箇所を分類（真陽性 / 偽陽性）
2. 真陽性は修正PRにリンクし、再スキャンしてクローズ
3. 偽陽性は理由を記録（次回の除外パターン改善）
```

---

## OWASP Agentic Top 10 対策

エージェント実行時のリスクを OWASP Agentic Top 10 観点で管理する。

### AG01 プロンプトインジェクション

- 入力バリデーション: ユーザー入力をシステムプロンプトと分離し、命令文をそのまま昇格しない
- 出力フィルタリング: 生成物に悪意あるコードや危険コマンドが含まれないかを検査する
- HELIX: `helix-codex` に渡す task テキストを sanitize し、危険トークンを除去してから実行する

### AG02 不適切な権限管理

- 最小権限原則: `sandbox: workspace-write` をデフォルトにし、`danger-full-access` は明示承認時のみ許可する
- ツール制限: `allowed-tools` で必要最小限のツールのみを許可する
- HELIX: role ごとの許可ツールリストを定義し、実行前に照合する

### AG03 過度な自律性

- 承認ゲート: 重要操作（破壊的変更・本番影響）前に人間承認を必須にする
- HELIX: Phase Guard + `helix plan review` を承認境界として運用する

### AG04 安全でないツール使用

- ツール呼び出し前にパラメータ検証（パス、正規表現、危険コマンド）を行う
- HELIX: `helix-hook` の advisory と `gate-checks` で事前検知する

### AG05 情報漏洩

- コンテキストに秘密情報を含めない（キー、トークン、PII を除外）
- 出力時に redaction を実行し、漏えい文字列を伏せる
- HELIX: `store.py` / `global_store.py` の redaction ルールを適用する

### AG06-AG10（概要）

- AG06: エージェント記憶・コンテキスト汚染のリスク  
  HELIX対策: 参照元の provenance を記録し、未検証メモリを実行判断に直結させない
- AG07: ツール連携・依存チェーンの脆弱性リスク  
  HELIX対策: allowlist、依存監査、危険プリミティブ検出をゲート化する
- AG08: 監視不足・異常検知遅延のリスク  
  HELIX対策: hook ログ、freeze-break 検知、異常イベントの即時アラートを有効化する
- AG09: 意図逸脱・目標ハイジャックのリスク  
  HELIX対策: 計画固定（plan review）と逸脱時の `blocked`/`interrupted` 判定を徹底する
- AG10: 監査不能・責任追跡不可のリスク  
  HELIX対策: SQLite 実行ログ、ミニレトロ、Learning Engine で証跡を保持する

---

