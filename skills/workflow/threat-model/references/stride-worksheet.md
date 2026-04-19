> 目的: G2 で STRIDE 脅威分析を漏れなく実施し、DREAD で優先順位を定量化する。

# STRIDE Worksheet

## 1. 使い方
1. 資産・境界・データフローを整理
2. STRIDE 6カテゴリで脅威を列挙
3. DREAD でスコア化
4. High を L4 タスクに紐付け

## 2. STRIDE ワークシート（表）
| Threat ID | STRIDE | 対象コンポーネント | 脅威内容 | 既存対策 | 追加対策 | 残留リスク |
|---|---|---|---|---|---|---|
| TH-001 | S | Auth API | JWT なりすまし | 署名検証 | aud/iss 検証強化 | 低 |
| TH-002 | T | Order API | パラメータ改ざん | 入力検証 | サーバ側再計算 | 低 |
| TH-003 | R | Admin UI | 操作否認 | 監査ログ | 改ざん検知 | 中 |
| TH-004 | I | User API | PII 漏えい | マスキング | 応答最小化 | 中 |
| TH-005 | D | Gateway | DoS | rate limit | WAF ルール追加 | 中 |
| TH-006 | E | RBAC | 権限昇格 | 役割判定 | policy test | 高 |

空欄テンプレート:
| Threat ID | STRIDE | 対象コンポーネント | 脅威内容 | 既存対策 | 追加対策 | 残留リスク |
|---|---|---|---|---|---|---|
| TH-xxx | S/T/R/I/D/E |  |  |  |  |  |

## 3. DREAD スコア式
式:
`DREAD = (Damage + Reproducibility + Exploitability + AffectedUsers + Discoverability) / 5`

評価目安:
- High: 7.0 以上（G2で対策必須）
- Medium: 4.0-6.9（L4で対策計画必須）
- Low: 3.9 以下（受容可能、根拠記録）

評価テンプレート:
| Threat ID | D | R | E | A | D | 総合 | 優先度 |
|---|---:|---:|---:|---:|---:|---:|---|
| TH-001 | 8 | 7 | 7 | 8 | 6 | 7.2 | High |
| TH-002 | 6 | 5 | 6 | 6 | 5 | 5.6 | Medium |

## 4. OWASP 対応マップ
| STRIDE | 主なOWASPカテゴリ | 代表コントロール |
|---|---|---|
| S | A07 Identification and Authentication Failures | MFA, strong session management |
| T | A03 Injection, A08 Software and Data Integrity Failures | validation, signed artifacts |
| R | A09 Security Logging and Monitoring Failures | tamper-evident audit logs |
| I | A01 Broken Access Control, A02 Cryptographic Failures | least privilege, encryption |
| D | A10 SSRF, abuse patterns | rate limit, queue isolation |
| E | A01 Broken Access Control | RBAC/ABAC checks, policy tests |

## 5. G2 判定チェック
- [ ] STRIDE 6カテゴリをすべて記入
- [ ] Threat ごとに対策・残留リスク記載
- [ ] DREAD を全件採点
- [ ] High の owner / due を設定
- [ ] `docs/security/threat-model.md` に保存

## 6. 詳細記入ガイド
### 6.1 Threat 記述ルール
- [ ] 攻撃者視点で記述する
- [ ] 攻撃経路を記述する
- [ ] 影響資産を記述する
- [ ] 成功条件を記述する
- [ ] 検出方法を記述する

### 6.2 対策の深さ
- [ ] 予防策
- [ ] 検知策
- [ ] 是正策
- [ ] 運用策
- [ ] 残留リスク受容

### 6.3 DREAD 採点の一貫性
- [ ] 採点基準をチームで共有
- [ ] 2名以上でレビュー
- [ ] High の採点根拠を記録
- [ ] Medium の見直し期限を設定
- [ ] Low の受容根拠を記録


## 7. レビュー質問 (厳選)

脅威モデリングレビューで使う具体質問:
- [ ] STRIDE 6 区分すべてについて、該当なし理由または脅威候補が記録されているか
- [ ] 資産・攻撃面・信頼境界の対応関係が図と表で一致しているか
- [ ] DREAD の各点数に根拠があり、主観的な一言評価で終わっていないか
- [ ] 高リスク項目に対して、予防策・検知策・対応策の三層が定義されているか
- [ ] 想定攻撃者の能力・前提条件が過小評価されていないか
- [ ] 残留リスクを受容する場合、受容理由と期限が明記されているか
