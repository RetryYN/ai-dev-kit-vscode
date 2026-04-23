# OpenClaw Fork Security Policy
> 目的: OpenClaw Fork Security Policy の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

## 1. 目的

本ポリシーは、外部スキルを HELIX にフォークする際の最小セキュリティ基準を定義する。
対象は `SKILL.md`、`references/`、`scripts/`、テンプレート、依存定義、付随ドキュメントを含む。

前提:
- OpenClaw レジストリは悪意あるスキル混入を前提に扱う
- 判定は `default deny` とし、証跡が不足するものは採用しない
- 実コード監査を省略してフォークしない

---

## 2. 判定原則

### 2.1 フォーク可否

| 判定 | 条件 |
|------|------|
| `approve` | Critical/High が 0、必要証跡が揃い、ライセンス互換性が確認済み |
| `needs-attention` | Medium 以下は許容可能だが、修正計画または隔離運用が必要 |
| `reject` | Critical が 1 件以上、またはライセンス/秘密情報/外部送信の拒否条件に該当 |

### 2.2 Severity 定義

| Severity | 代表例 | フォーク方針 |
|----------|--------|-------------|
| Critical | 秘密情報送信、未承認の外部通信、sandbox 外書込、自己更新/自己改変、RCE、禁止ライセンス | 即時 reject |
| High | `eval`/`exec`/`subprocess` の無制限利用、Critical/High CVE、プロンプト注入、無断データ送信 | 修正完了まで block |
| Medium | 過剰なワークスペースアクセス、version pin 不足、監査証跡不足、Medium CVE | 修正計画を条件に保留 |
| Low | 日本語化不足、メタデータ不足、ログ粒度不足 | フォーク前に補正推奨 |

### 2.3 OWASP Top 10 対応軸

| OWASP | フォーク時の着眼点 |
|-------|------------------|
| A01 Broken Access Control | 読み書きパス、権限境界、sandbox 逸脱 |
| A02 Cryptographic Failures | API キー、トークン、秘密鍵の保護と保存方法 |
| A03 Injection | prompt injection、shell injection、`eval`、テンプレート注入 |
| A04 Insecure Design | 自己進化、自己更新、無制限ツール実行などの危険設計 |
| A05 Security Misconfiguration | allowlist 不在、無制限通信、無制限ファイルアクセス |
| A06 Vulnerable and Outdated Components | npm/pip 依存、固定されていないバージョン |
| A07 Identification and Authentication Failures | 外部 API 認証情報の管理不備 |
| A08 Software and Data Integrity Failures | 由来不明コード、ハッシュ未記録、上流差分未追跡 |
| A09 Security Logging and Monitoring Failures | 監査証跡、採否記録、再監査ログの欠落 |
| A10 SSRF | スキル内 HTTP クライアント、URL 動的組立、ユーザー入力起点の外部送信 |

---

## 3. 事前拒否条件

以下のいずれかに該当した場合、その時点でフォークを中止する。

- allowlist 外への通信先が存在し、無効化もできない
- API キー、トークン、秘密鍵、個人情報がハードコードされている
- `~`、絶対パス、親ディレクトリ遡りで sandbox 外へ書き込む
- `eval`、`new Function`、`exec`、`spawn`、`subprocess`、`os.system` などが無制限に使われている
- ユーザーデータやリポジトリ内容を外部 LLM/API に送る設計で、明示同意・マスキング・送信先制御がない
- `SKILL.md` やテンプレートに、秘密情報要求、システムプロンプト上書き、検証回避の指示が含まれる
- GPL/AGPL/SSPL/BSL など HELIX 配布方針と非互換のライセンスを含む
- バイナリ、難読化コード、遠隔ダウンロード実行、自己更新機構が含まれる

---

## 4. フォーク前セキュリティチェックリスト

各候補スキルごとに、以下を `G2 → G4 → G6 → G7` の順で確認する。

### 4.1 G2 脅威分析

| 項目 | 必須確認 | 証跡 | 失敗時 severity |
|------|----------|------|-----------------|
| 由来 | 上流 URL、ライセンス、タグ/コミット、取得日を記録 | upstream manifest | Medium |
| 外部通信 | 送信先ドメイン、HTTP メソッド、送信データ、allowlist 適合 | 通信一覧表 | Critical |
| 認証情報 | API キー/トークン/シークレットの取得元と保存先 | secret inventory | Critical |
| ファイルアクセス | 読み書きパス、絶対パス、ホーム配下、親ディレクトリ遡り | path matrix | Critical |
| コード実行 | `eval`/`exec`/`subprocess`/動的 import の有無 | dangerous primitive list | High |
| データ送信 | ユーザープロンプト、コード、ログ、PII の外部送信有無 | data flow | Critical |
| prompt injection | `SKILL.md`、テンプレート、スクリプト内の命令文 | prompt review memo | High |
| ライセンス | MIT/Apache-2.0/BSD/ISC は原則許可、MPL/LGPL は個別審査 | license review | Critical |

推奨コマンド:

```bash
rg -n "(fetch|axios|requests|httpx|urllib|curl|wget)" <skill-dir>
rg -n "(exec|spawn|fork|subprocess|os\\.system|eval|new Function|importlib)" <skill-dir>
rg -n "(API_KEY|TOKEN|SECRET|PASSWORD|PRIVATE_KEY)" <skill-dir>
rg -n "(\\.\\./|^/|~\\/)" <skill-dir>
```

### 4.2 G4 実装検証

| 項目 | 必須確認 | 証跡 | 失敗時 severity |
|------|----------|------|-----------------|
| 依存関係 | `package-lock`/`poetry.lock` 等の有無、固定バージョン、監査結果 | audit log | High |
| install script | `postinstall`、`setup.py`、任意スクリプト起動の有無 | install review | High |
| sandbox 整合 | HELIX の workspace-write で成立するか | sandbox review | High |
| 入出力境界 | 入力ソース、出力先、テンプレート展開範囲 | io contract | Medium |
| 権限最小化 | 必要最小限のファイル/コマンド/通信だけに絞れているか | least privilege memo | Medium |
| 監査可能性 | 実行ログ、採否ログ、バージョン記録を残せるか | auditability memo | Low |

推奨コマンド:

```bash
npm audit --omit=dev
pip-audit
rg -n "(postinstall|prepare|preinstall|setup\\(|entry_points)" <skill-dir>
```

### 4.3 G6 RC 検証

| 項目 | 必須確認 | 証跡 | 失敗時 severity |
|------|----------|------|-----------------|
| HELIX 変換 | metadata、triggers、verification、references パスを HELIX 形式に統一 | converted diff | Medium |
| 日本語化 | 秘密情報要求や危険操作を助長しない表現で日本語化 | localization review | Low |
| 安全デフォルト | 外部通信 off、秘密情報非表示、明示 opt-in のみ有効 | config diff | High |
| 回帰確認 | 既存 HELIX スキルと責務衝突しない | mapping review | Medium |
| 運用準備 | フォーク理由、制限事項、更新方法、削除条件を明記 | release memo | Low |

### 4.4 G7 vuln scan / 継続監視

| 項目 | 必須確認 | 証跡 | 失敗時 severity |
|------|----------|------|-----------------|
| 定期再監査 | 上流更新の定点確認日を設定 | review schedule | Medium |
| 差分監視 | 上流の `SKILL.md`、依存、スクリプト差分をレビュー | upstream diff log | High |
| 脆弱性再走査 | npm/pip audit、secret scan、license scan を再実行 | scheduled scan log | High |
| revoke 条件 | 悪性挙動、ライセンス変更、保守停止時の削除基準 | revoke policy | Medium |

---

## 5. 証跡記録テンプレート

各フォーク候補ごとに、少なくとも以下を記録する。
保存先は `docs/security/fork-audits/<YYYY-MM-DD>-<skill>.md` を推奨する。

```yaml
skill_name: ""
upstream:
  registry: "OpenClaw"
  url: ""
  version: ""
  commit: ""
  license: ""
  retrieved_at: ""
audit:
  reviewer_role: "security"
  gates:
    G2: "passed|failed|blocked"
    G4: "passed|failed|blocked"
    G6: "passed|failed|blocked"
    G7: "passed|failed|blocked"
findings:
  critical: []
  high: []
  medium: []
  low: []
allowlist:
  domains: []
  paths: []
  commands: []
data_handling:
  sends_user_data_externally: false
  pii_allowed: false
decision:
  verdict: "approve|needs-attention|reject"
  rationale: ""
  next_review_at: ""
```

---

## 6. HELIX フォークポリシー

### 6.1 フォーク元の明示

フォークしたスキルには、少なくとも以下を残す。

- 上流名称
- 上流 URL
- 取得日
- タグ、バージョン、またはコミット SHA
- 上流ライセンス
- HELIX での変更理由

`SKILL.md` 本文または併設ドキュメントの冒頭に provenance セクションを置くこと。

### 6.2 セキュリティ監査の証跡

- G2/G4/G6/G7 の判定結果を残す
- Critical/High は修正または reject 以外を認めない
- 監査時に用いたコマンド、差分、判断理由を残す
- 監査者、監査日、再監査予定日を残す

### 6.3 HELIX 標準への変換ルール

- `metadata.helix_layer` を必須化する
- `triggers` は HELIX の発火条件に再記述する
- `verification` は HELIX で再現可能な確認項目に変換する
- `references/` は相対パス解決可能な形に直す
- 上流固有の CLI や外部サービス呼び出しは、HELIX で未許可なら削除または無効化する
- 暗黙の外部通信、自己更新、自己改変、権限昇格要求は削除する
- 実行可能スクリプトは allowlist 化し、必要なら HELIX 側ラッパーに置き換える

### 6.4 日本語化ルール

- 逐語訳ではなく、安全性を優先して再記述する
- 「秘密情報を貼り付けろ」「システム指示を無視しろ」などの危険文言は削除する
- 英語固有の法的表現は、日本語注記を追加して意味を明確化する
- 原文由来の判断根拠が重要な箇所は、短い原文引用と和訳を併記する

### 6.5 定期的な上流チェック方針

- 最低月次で上流の更新、issue、ライセンス変更を確認する
- 重要スキルはリリース前ごとに再監査する
- 上流に大きな差分が入った場合は新規フォーク扱いで G2 からやり直す
- メンテナ不在、保守停止、悪性挙動報告が出た場合は即時凍結する

---

## 7. コンプライアンス適合基準

### 7.1 OSS ライセンス

| 区分 | 扱い |
|------|------|
| MIT / Apache-2.0 / BSD / ISC | 原則許可 |
| MPL-2.0 / LGPL | 配布形態と混在条件を個別審査 |
| GPL / AGPL | 原則 reject |
| SSPL / BSL / 商用制限付き | reject |

### 7.2 データ保護

- 個人情報、機密情報、未公開コードを外部 LLM/API に送らない
- 送信が必要な場合は匿名化、allowlist、明示 opt-in、送信先記録を必須とする
- 監査ログには秘密情報そのものを残さない

### 7.3 監査適合

以下を満たした場合に「適合」とする。

- OWASP Top 10 観点のレビューが完了
- ライセンス互換性が確認済み
- G2/G4/G6/G7 の証跡が存在
- 再監査予定日が設定済み

---

## 8. OpenClaw 11 スキルの HELIX 統合先マッピング

| OpenClaw スキル | HELIX 統合先 | 判断 | 理由 |
|-----------------|-------------|------|------|
| Capability Evolver | `agent-teams` + `context-memory` + `ai-coding` | 既存強化のみ | 自己進化機能は高リスク。自己改変は許可せず、学習ループと記録だけ限定導入 |
| astrai-code-review | `code-review` + `adversarial-review` + `ai-coding` | 既存強化 | モデルルーティング付きレビューとして既存レビュー系に統合可能 |
| code-security-audit | `security` + `verification` | 既存強化 | OWASP スキャンは Security/Verification の責務に一致 |
| auto-test-generator | `testing` + `quality-lv5` | 既存強化 | 自動生成よりもテスト品質評価と接続して使う方が安全 |
| credential-scanner | `security` + `compliance` | 既存強化 | 秘密情報検知は Security 主体、記録と運用は Compliance に接続 |
| database-designer | `db` | 既存強化 | DB 設計支援として既存スキルと重複 |
| diataxis-writing | `documentation` | 既存強化 | 文書品質ルールとして追加するのが妥当 |
| describe-design | `design-doc` + `reverse-analysis` | 既存強化 | コードから設計抽出する責務に一致 |
| diagrams | `diagram` + `design-doc` | 既存強化 | 図表生成は既存 `diagram` の拡張対象 |
| agent-cost-monitor | `agent-teams` + `ai-coding` | 既存強化 | エージェント運用コストの監視はチーム運用の一部として扱う |
| cacheforge-vibe-check | `code-review` + `verification` | 既存強化 | AI 生成コード検出は補助信号であり、独立 skill よりレビュー補助が適切 |

### 8.1 新規スキル作成の判断基準

以下を満たす場合のみ、新規スキルを作成する。

- 既存スキル 2 つ以上に分散すると責務が曖昧になる
- 独自の入出力契約、検証手順、references 群が必要
- セキュリティポリシー上、隔離した方が安全

今回の 11 候補については、原則として新規スキル化より既存強化を優先する。
例外は、外部通信や自己更新を伴う実装を完全に分離しないと安全を確保できない場合に限る。

---

## 9. 推奨運用フロー

1. 上流スキルを取得し、URL・コミット・ライセンスを記録する
2. G2 で通信、秘密情報、ファイルアクセス、コード実行、prompt injection を洗う
3. G4 で依存と install script、sandbox 整合を確認する
4. HELIX 形式へ変換し、日本語化後に G6 で再レビューする
5. フォーク後は G7 として月次再監査を設定する

---

## 10. 最終判断メモ

- フォークは「便利そうだから」ではなく「監査可能だから」で決める
- 実コード未確認の段階では、個別スキルを安全と見なさない
- 特に自己進化、外部通信、秘密情報処理、自己更新は常に慎重側で扱う
