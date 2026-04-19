> 目的: L3 工程表をマイクロスプリント、feature flag、rollback と一体で作成する。

# WBS Template

## 1. WBS 作成原則
- 1タスクは0.5〜1.5日で分割
- 依存関係はIDで明示
- 各タスクに L4 Sprint を割り当て
- feature flag と rollback を必ず記載（不要なら N/A）

## 2. WBS テンプレート
```markdown
# L3 Schedule WBS

## 前提
- API Freeze:
- Schema Freeze:
- Release:

## WBS
| ID | タスク | 担当 | 依存 | 期間 | 環境 | L4 Sprint | feature flag | rollback |
|---|---|---|---|---|---|---|---|---|
| WBS-01 | 影響調査 | @se | - | 0.5d | dev | .1a | N/A | N/A |
| WBS-02 | 実装計画 | @se | WBS-01 | 0.5d | dev | .1b | N/A | N/A |
| WBS-03 | 骨格実装 | @se | WBS-02 | 1.0d | dev | .2 | ff_xxx | flag off |
| WBS-04 | 強化実装 | @se | WBS-03 | 1.0d | dev | .3 | ff_xxx | route rollback |
| WBS-05 | 検証固定 | @qa | WBS-04 | 0.5d | stg | .4 | N/A | baseline restore |
| WBS-06 | 仕上げ | @tl | WBS-05 | 0.5d | stg | .5 | N/A | doc restore |
```

## 3. マイクロスプリント連動表
| Sprint | 目的 | 完了条件 | 代表成果物 |
|---|---|---|---|
| .1a | 既存調査 | 影響範囲確定 | 調査メモ |
| .1b | 計画固定 | タスク順序・受入条件確定 | WBS |
| .2 | 骨格実装 | 最小動作確認 | PR/差分 |
| .3 | 強化実装 | 回帰・セキュリティ対策 | テスト追加 |
| .4 | 検証固定 | テスト pass | 検証ログ |
| .5 | 仕上げ | レビュー反映・文書同期 | 完了報告 |

## 4. feature flag テンプレート
```yaml
feature_flag:
  name: "ff_<domain>_<feature>_v2"
  default: false
  rollout:
    - internal
    - beta
    - all
  metrics:
    - error_rate
    - latency_p95
  cleanup_deadline: "YYYY-MM-DD"
```

チェック:
- [ ] 命名規則に準拠
- [ ] default=false
- [ ] 監視指標2つ以上
- [ ] cleanup 期限あり

## 5. rollback 手順テンプレート
```markdown
## Rollback
1. feature flag を OFF
2. 新経路を旧経路へ戻す
3. 必要なら migration down
4. smoke test 実行
5. 監視値正常化確認
```

発火条件例:
- 5xx > 2%
- p95 が旧版比 30% 超悪化
- Sev1/2 発生

## 6. 運用詳細チェック
### 6.1 タスク粒度
- [ ] 1タスクは1日以内
- [ ] 依存先が明確
- [ ] 受入条件が記載
- [ ] 完了定義が記載
- [ ] 担当が単一責任

### 6.2 リスク管理
- [ ] 高リスクに緩和策あり
- [ ] 代替手順あり
- [ ] 障害時連絡先あり
- [ ] rollback 所要時間見積あり
- [ ] rollback 実施条件あり

### 6.3 進捗レビュー
- [ ] .1a 完了時レビュー
- [ ] .2 完了時レビュー
- [ ] .3 完了時レビュー
- [ ] .4 完了時レビュー
- [ ] .5 完了時レビュー


## 7. レビュー質問 (厳選)

WBS レビューで使う具体質問:
- [ ] クリティカルパス上のタスクにバッファ日数と根拠が設定されているか
- [ ] 各タスクの完了条件が成果物ベースで定義され、作業ベースで終わっていないか
- [ ] 依存関係が双方向に検証され、循環依存や隠れ依存がないか
- [ ] リスク高タスクに fallback 手段または feature flag 方針が紐付いているか
- [ ] レビュー・テスト・リリース準備タスクが末尾にまとめ漏れなく配置されているか
- [ ] オーナーの稼働上限を超える週が存在しないか
