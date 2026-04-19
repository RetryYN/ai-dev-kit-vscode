> 目的: G1R 事前調査で一次情報の信頼性と採用判断を最短で確定する。

# Primary Sources Checklist

## 1. 一次情報ソース基準
- 優先度A: 標準仕様・公式ドキュメント・公式リポジトリの release/issue
- 優先度B: ベンダー公式ブログ・公式チュートリアル
- 優先度C: コミュニティ記事（補助利用のみ）

必須URL（実在・公式）:
- RFC 9110 HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110
- OAuth 2.0 (RFC 6749): https://www.rfc-editor.org/rfc/rfc6749
- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- PostgreSQL Documentation: https://www.postgresql.org/docs/

チェックリスト:
- [ ] 一次情報 URL が3件以上ある
- [ ] URL ごとに「何の判断に使うか」を1行で記載
- [ ] 参照日（YYYY-MM-DD）を記録
- [ ] 仕様バージョンを記録（latest の場合は明記）
- [ ] リンク切れ確認を実施

## 2. 調査プロトコル（30-60分）
1. 調査テーマを1文で固定する
2. in_scope / out_of_scope を3項目以内で定義する
3. 一次情報を3-7件収集する
4. 各情報を「制約」「推奨」「禁止」に分解する
5. 候補案A/Bを作る
6. adoption 判定を記述する
7. open_blockers の有無を確定する

テンプレート:
```yaml
research_protocol:
  topic: "<テーマ>"
  in_scope:
    - "..."
  out_of_scope:
    - "..."
  sources:
    - url: "<official-url>"
      type: "official|rfc|repo"
      used_for: "判断項目"
      noted_constraints:
        - "..."
  alternatives:
    - id: "A"
      summary: "..."
    - id: "B"
      summary: "..."
```

## 3. adoption 判定テンプレート
```yaml
adoption:
  decision: "adopt|reject|defer"
  rationale:
    - "一次情報に基づく理由1"
    - "一次情報に基づく理由2"
  impact:
    security: "low|medium|high"
    performance: "low|medium|high"
    cost: "low|medium|high"
  risks:
    - "残存リスク"
  mitigations:
    - "緩和策"
  blockers: []
```

判定基準:
- adopt: blocker なし、制約を受容可能
- reject: 重大制約あり、代替案の方が合理的
- defer: 情報不足またはPoC依存

## 4. 具体例（API レート制限方式選定）
前提:
- 要件: 1分あたり 300 req / tenant
- 非機能: burst 吸収、DoS 耐性

収集ソース:
- RFC 9110（HTTP ステータス・Retry-After）
- OWASP Top 10（可用性・濫用対策）
- Redis docs（INCR/EXPIRE 原子的利用）https://redis.io/docs/

比較:
| 案 | 方式 | 長所 | 短所 | 判定 |
|---|---|---|---|---|
| A | Fixed Window | 実装が容易 | バーストに弱い | reject |
| B | Sliding Window | 公平性が高い | 実装がやや複雑 | adopt |

adoption 記述例:
- decision: adopt
- rationale: RFC準拠ヘッダでクライアント制御可能、Redis で運用実績あり
- blockers: なし

## 5. 最終出力チェック（G1R）
- [ ] `docs/research/YYYY-MM-DD-<topic>.md` を作成
- [ ] 一次情報 URL 3件以上
- [ ] adoption（採用/不採用理由）記載
- [ ] open_blockers を明示（0件推奨）
- [ ] 次アクションを L2/L3/L4 のどれかへ接続

出力サンプル見出し:
- `# Research Report: <topic>`
- `## Sources`
- `## Findings`
- `## Adoption`
- `## Risks`
- `## Next Action`

## 6. 詳細チェック項目（運用）
### 6.1 収集品質チェック
- [ ] 公式ドメインである
- [ ] 文書の最終更新日が確認できる
- [ ] 仕様番号/版が確認できる
- [ ] 要件に直結する記述を抽出できる
- [ ] 制約事項が明示されている
- [ ] 非推奨事項が明示されている
- [ ] セキュリティ観点の記述を拾えている
- [ ] 互換性観点の記述を拾えている
- [ ] ライセンス観点の記述を拾えている
- [ ] 運用観点の記述を拾えている

### 6.2 論点別チェック
- [ ] 認証
- [ ] 認可
- [ ] 可用性
- [ ] 監査ログ
- [ ] エラーハンドリング
- [ ] レート制限
- [ ] リトライ
- [ ] タイムアウト
- [ ] バックオフ
- [ ] サーキットブレーカー
- [ ] キャッシュ整合
- [ ] データ保持期間
- [ ] PII 取り扱い
- [ ] 暗号化
- [ ] 鍵管理
- [ ] 依存更新方針
- [ ] 後方互換性
- [ ] リリースノート確認
- [ ] 既知不具合確認
- [ ] 廃止予定確認

### 6.3 判定ログ雛形
```markdown
## Decision Log
- 日付:
- テーマ:
- 判断:
- 根拠URL:
- トレードオフ:
- 残課題:
```


## 7. レビュー質問 (厳選)

G1R レビュー時に使う具体質問:
- [ ] 依拠した一次情報 URL は公式ドキュメント・標準仕様・原著論文のいずれかに分類済みか
- [ ] 各判断に対して「採用しない場合の理由」も同じ粒度で記録されているか
- [ ] 調査対象の最終更新日を確認し、陳腐化リスクをコメントしているか
- [ ] 重大な主張については一次情報を最低 2 件で相互検証したか
- [ ] 採用候補のライセンス・メンテナンス状況・サポート期限を確認したか
- [ ] 比較表の評価軸に重み付け根拠があり、結論と矛盾していないか
