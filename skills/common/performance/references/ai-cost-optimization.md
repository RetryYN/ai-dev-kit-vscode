> 目的: AI 利用コスト最適化と追跡設計を定義するときに参照する

## トークンコスト最適化（90% 削減戦略）

### Prompt Caching

- system prompt（role 定義 + スキル参照）を固定し、キャッシュヒット時に大幅削減を狙う
- HELIX では `helix-codex` の role prompt はセッション内で固定し、キャッシュ対象にする
- 実装例:
  - Anthropic API の prompt caching
  - OpenAI の `cached_tokens`

### Semantic Caching

- 類似クエリの結果をローカル再利用し、同一探索の再実行を減らす
- HELIX では `helix discover` の検索結果をキャッシュ対象にする
- 実装例:
  - `input_hash` をキャッシュキーに採用
  - SQLite に結果を保存

### Model Routing（3軸マトリクス強化）

現行スコア 0-14 のみではなく、`タスク種別 × リスク × コスト` でモデルを選ぶ。

| タスク種別 | 推奨モデル | 目的 |
|-----------|-----------|------|
| 調査/検索 | Haiku | 最小コストで一次調査 |
| テンプレ生成 | Spark | 低コストで反復 |
| 実装 | SE / Codex 5.3 | 中コストで実装品質を確保 |
| レビュー/設計 | TL / Codex 5.4 | 高精度レビュー |
| フロント設計 | Opus | 表現品質重視 |

- 委譲前に推定費用を表示する（例: `推定 $X.XX`）

### Dynamic Context Pruning

- 長時間セッションで古い会話を動的に削除し、必要文脈のみ残す
- HELIX では `helix-codex --task` に渡す参照を最小化する
- 変更対象ファイル中心に限定し、全ファイル Read を避ける

### コスト追跡ダッシュボード設計

```text
helix log report cost:
  今日:    Opus $2.40 / Codex $1.80 / Sonnet $0.30 / Haiku $0.05
  今週:    $22.50（先週比 -15%）
  最適化:  キャッシュヒット率 62%、圧縮率 3.2x
```

---

## AI エージェントコスト追跡

helix-codex 委譲時のトークン使用量とコストを継続的に記録し、モデル選択を最適化する。

### トークン使用量の推定（委譲単位）

```text
input_tokens_est  = ceil(prompt文字数 / 3.2) + 添付コンテキスト補正
output_tokens_est = ceil(応答文字数 / 2.8)
total_tokens_est  = input_tokens_est + output_tokens_est
```

```text
補正例:
- 参照ファイル 1件ごとに +300
- diff 100行ごとに +180
- 長文ログ貼り付け時は実測優先
```

### モデル別コスト表（相対係数）

| モデル | 主用途 | 相対入力コスト | 相対出力コスト |
|--------|--------|----------------|----------------|
| Opus | 設計・難問解析 | 1.00 | 1.00 |
| Sonnet | テスト/文書生成 | 0.35 | 0.35 |
| Haiku | 軽量調査/一次レビュー | 0.08 | 0.08 |
| Codex 5.4 | TLレビュー・高難度実装 | 0.55 | 0.55 |
| Codex 5.3 | SE実装（スコア4+） | 0.28 | 0.28 |
| Codex 5.3 Spark | 軽微修正・高速反復 | 0.12 | 0.12 |

```
換算:
推定コスト = (input_tokens_est × 相対入力コスト) + (output_tokens_est × 相対出力コスト)
```

### プロジェクト単位の集計方法

```text
1. タスク完了ごとに usage レコードを1件保存
2. 日次: project_id + model ごとに合計
3. 週次: タスク種別（実装/レビュー/調査）で再集計
4. 月次: 予算上限と差分比較（見込み超過はモデル再配分）
```

```sql
SELECT project_id, model, SUM(input_tokens) AS in_tok, SUM(output_tokens) AS out_tok
FROM agent_cost_logs
WHERE created_at >= date('now', '-30 day')
GROUP BY project_id, model
ORDER BY project_id, model;
```

### コスト最適化ベストプラクティス

```
- 不要な委譲を減らす（同一質問の多重依頼を禁止）
- low risk は Spark/Haiku、high risk は 5.4/Opus に限定
- レビューは差分最小化して投入トークンを抑制
- 大規模ログ貼り付け前に要約してから委譲
- 失敗リトライは原因修正後に実施（無再考リトライ禁止）
```

### SQLite でのコストログ記録（`helix.db` 拡張提案）

```sql
CREATE TABLE IF NOT EXISTS agent_cost_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  model TEXT NOT NULL,
  role TEXT NOT NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  estimated_cost REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_cost_logs_project_created
  ON agent_cost_logs(project_id, created_at);
```

---

## AI セッション記録と再生

### セッションログの構造化記録

- タイムスタンプ付きアクションログを残す
- 入力/出力はハッシュ化またはマスキング（redacted）して保存する
- 使用ツール、実行時間、結果ステータスを1イベント単位で記録する

### Learning Engine 連携

- `helix learn` は成功セッションから recipe を生成する
- `helix publish` で再利用可能なセッションパターンを共有する
- 失敗セッションは failure recipe として分離し、再発防止に使う

### 記録フォーマット（JSONL）

```json
{"ts":"2026-04-04T12:00:00","action":"codex-review","input_hash":"a3f2","result":"approve","duration_ms":5200}
```

運用ルール:
- 1行=1アクション
- 機密値は保存しない（キー名・値の両方を検査）
- 再生時は `ts` 順に並べて依存順序を復元する

---

