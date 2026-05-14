# PMO 9 ロール使い分けガイド (V2.2)

## 1. PMO の狙い

PMO は `Opus context` の保護、探索の分担化、複数視点の判断を担う運用ロール群。  
V2.2 では 9 ロールを明文化し、`Haiku` と `Sonnet` の役割分離を前提に、軽重を分けた委譲を標準化する。

## 2. PMO 9 ロール一覧

| ロール | model | scope | 役割 | 典型 use case |
|---|---|---|---|---|
| pmo-sonnet | Sonnet | project judgment | 構造化チェック | PLAN/review/長文 doc 解析 |
| pmo-haiku | Haiku | Web 検索 | 目星付け | "X の現状?" 即答型 Q&A |
| pmo-tech-fork | Sonnet | 外部 GitHub | OSS 評価 | ライブラリ選定前 |
| pmo-tech-docs | Sonnet | 外部 blog | 概念精読 | ベスプラ調査 |
| pmo-tech-news | Sonnet | 外部 news | 体系 sweep | 週次 watch |
| pmo-helix-explorer | Sonnet | HELIX 内 | skills/templates/cli 詳細 | 流用提案 |
| pmo-helix-scout | Haiku | HELIX 内 | 軽量目星付け | "x.md どこ?" 即答 |
| pmo-project-explorer | Sonnet | project 内 | code/docs 詳細 | 設計整合チェック |
| pmo-project-scout | Haiku | project 内 | 軽量目星付け | "auth 関連?" 即答 |

## 3. エスカレーション関係

### 3.1 基本ルール

- Haiku scout 系は軽量スキャンで起点を絞る
- Sonnet deep-dive 系に結果を引き継ぐ
- 重要判断の最終レビューは Opus で収束

### 3.2 具体フロー

```text
pmo-haiku / pmo-project-scout
  -> 目星・一次情報収集
  -> 必要なら pmo-sonnet / pmo-tech-fork / pmo-helix-explorer を追加依頼
  -> pmo-helix-scout は internal map 取得を担当
```

## 4. 呼び方（Agent 実行）

統一書式:

```text
Agent({subagent_type: "pmo-*", description: "...", prompt: "..."})
```

### 4.1 典型的な呼び出し例

- project 文脈確認:

```bash
Agent({subagent_type:"pmo-project-scout", description:"auth 関連の初期探索", prompt:"関連ドキュメントを3件ピックアップ"})
```

- 外部比較調査:

```bash
Agent({subagent_type:"pmo-tech-docs", description:"最新 OSS の設計意見", prompt:"公開情報の根拠付き要約を3本"})
```

- Helix 内横断探索:

```bash
Agent({subagent_type:"pmo-helix-explorer", description:"既存 skill 再利用", prompt:"同等フローの参照を提示"})
```

## 5. model 正式 ID 一覧（Opus fallback 防止）

実装に関する model 混在を避けるため、各 role への割当を固定化する。

- pmo-sonnet: `claude-3-5-sonnet`
- pmo-tech-fork: `claude-3-5-sonnet`
- pmo-tech-docs: `claude-3-5-sonnet`
- pmo-tech-news: `claude-3-5-sonnet`
- pmo-helix-explorer: `claude-3-5-sonnet`
- pmo-project-explorer: `claude-3-5-sonnet`
- pmo-haiku: `haiku`
- pmo-helix-scout: `haiku`
- pmo-project-scout: `haiku`

## 6. 委譲必須判定基準

以下のいずれかが成立したら Sonnet 系に切替（または併走）:

1. 200 行超の deep read が必要
2. Grep/検索が 3 回以上（異なる観点をまたぐ）
3. 長文 doc（要件・ADR・設計）解釈
4. 2 つ以上の視点が衝突（正誤・リスク判断が割れる）

### 6.1 運用例

- `pmo-haiku` が 3 行で答えた情報に追加証拠が必要なら `pmo-sonnet` へ引き継ぎ
- `pmo-helix-scout` で検索結果が散らばる場合、`pmo-helix-explorer` が一次設計を解像
- `pmo-project-explorer` 結果で影響範囲が増える場合、`pmo-project-scout` を並列投入して確認

## 7. 並列実行の原則

- 依存がない調査は必ず並列化
- まず一次情報取得を並列で行い、その後に判断責任者へ集約
- 先に `pmo-scout` で全体地図を取り、`pmo-*.explorer` で精査する

### 7.1 並列パターン

```text
依存なし:
pmo-helix-scout + pmo-project-scout + pmo-tech-news
  -> 結果集約
  -> 必要なら pmo-helix-explorer, pmo-project-explorer
```

### 7.2 依存あり:

```text
pmo-haiku (事実収集)
  -> pmo-sonnet (妥当性検証)
  -> manager が最終判断
```

## 8. 禁止事項（運用上の注意）

- pmo-scout の短答結果のみで最終結論を固定しない
- 同名 role を同一問題で重複起動しない（監査性低下）
- output の evidence 未添付は再依頼
- Opus への委譲時に model 情報を曖昧にしない（`fallback` ではなく明示）

## 9. 参照

- .claude/agents 配下の pmo 定義 9 件
- `docs/commands/innovation.md`
- `skills/workflow` の運用 skill
- `cli/templates/teams` の配下チーム定義

## 10. 運用チェックリスト

1. 調査トリガは明確か
2. role が重複しないか
3. Sonnet 起票条件を満たしたか
4. 併走が必要なら dependency を明文化したか
5. 最終 answer に trace と根拠を残したか

```text
完了条件:
- 依頼元に回答経路が明確
- 追加質問なしで次工程に進める
- 失敗・不確定領域を TODO として明記
```

## 11. PMO 9 ロールの運用サマリ

- pmo-sonnet/haiku: 速報・探索・早期判断
- pmo-tech-fork/docs/news: 外部知識取得
- pmo-helix-explorer/scout: HELIX 内の設計再利用
- pmo-project-explorer/scout: プロジェクト実装の精読

運用上のポイントは「軽量は先に、重い判断は後で」。これにより、短時間で意思決定を回しつつ、最終精度を下げない設計運用を維持する。

## 12. 追加実践ガイド

### 12.1 PMO 9 の起点定義

PMO 起動前に次を固定する:

1. 解決したい問い（事実/判断/設計）
2. 期限（即日/短期/次 sprint）
3. エビデンス要求（URL / 出典 / 影響度）
4. リソース上限（1 件あたりの検索深度）

### 12.2 レポート書式（推奨）

```text
タイトル: 調査テーマ
実行ロール: pmo-*
調査結果:
  - 根拠1
  - 根拠2
判断:
  - 採択可否
  - 追加調査要否
リスク:
  - 依存
  - 証拠の古さ
次アクション:
  - PM への確認事項
```

### 12.3 Opus への要約時に必須な要素

1. 事実情報の出典
2. 不確実性
3. 逆張りケース
4. すぐ実行できる提案

### 12.4 PMO 間の重複回避

- 同一テーマに pmo-sonnet と pmo-tech-fork を同時起動しない
- pmo-haiku が見つけた方向だけで最終判断をしない
- 同種情報は 1 つに統合して短時間で再利用可能な形に圧縮

### 12.5 運用時の SLA（目安）

- scout 系: 5 分以内の初回観測
- Sonnet 系: 20 分以内の一次報告
- 深掘り継続: 60 分以内に「継続するか」の判断

### 12.6 禁止パターン

- 同じファイルを 3 回以上重複検索
- 根拠が薄いままの「可能性が高い」連呼
- `trace` や `scope` 不記載のままの提出

### 12.7 ロール運用の再確認フロー（週次）

1. role 起動比率の偏りを監視
2. pmo-scout の成功率（有用な初動率）をレビュー
3. エラー率（誤情報・誤検出率）の改善策を共有
4. 次週の運用ルールを README へ反映

## 13. pmo-roster 連携パターン

- 企画フェーズ: `pmo-helix-scout` + `pmo-project-scout` で地図化
- 設計比較フェーズ: `pmo-project-explorer` + `pmo-tech-fork`
- 意思決定前: `pmo-sonnet` + `pmo-tech-docs` で根拠合成
- 監視フェーズ: `pmo-tech-news` + `pmo-helix-explorer`

## 14. 例: PMO 連携の最短導線

```bash
# 1) まず軽く全体探索を行う
Agent({subagent_type:"pmo-helix-scout", description:"内部ドキュメント探索", prompt:"関連設計の一覧を抽出"})

# 2) 深掘りが必要なら Sonnet 系に昇格
Agent({subagent_type:"pmo-project-explorer", description:"実装依存の精読", prompt:"対象コードの影響範囲を要約"})

# 3) 結果集約
Agent({subagent_type:"pmo-sonnet", description:"最終判断整理", prompt:"両ロール結果を意思決定可能な形に整形"})
```

## 15. PMO ロールの品質ゲート

- 参照リンクの真偽を確認した結果で返却
- 変更点と提案事項を分けて提示
- 依存が分かるよう、`scope` を明示
- TODO 化した観点を残して受け渡し

## 16. まとめ

PMO 9 ロールは、作業速度と判断精度のトレードオフを分離するための分業レイヤーである。  
Haiku は高速に候補を見つけ、Sonnet は深く検証し、Opus に最終判断可能な状態で移送することが、V2.2 の安定運用の中核となる。
