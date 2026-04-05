# L2 設計書: Learning Engine

> フェーズ: L2 全体設計
> ステータス: Accepted
> 作成日: 2026-04-05
> 対象: `cli/lib/learning_engine.py`, `cli/lib/recipe_store.py`, `cli/lib/global_store.py`

---

## 1. 目的

Learning Engine は HELIX CLI の実行履歴から成功/失敗パターンを分析し、再利用可能な recipe を生成するシステムである。プロジェクトローカルで蓄積した recipe をグローバル DB に昇格することで、プロジェクト横断の知識共有を実現する。

### 1.1 解決する課題

| 課題 | Learning Engine による解決 |
|------|---------------------------|
| 同じ失敗を繰り返す | 失敗パターンを recipe 化し、類似タスク実行前に警告を表示 |
| 成功パターンが属人化する | 成功 recipe を構造化して蓄積。パターンマッチングで推薦 |
| 品質評価が定性的 | action 通過率 45% + observation 通過率 55% の定量スコア |
| プロジェクト間で知識が共有されない | global_store による recipe 昇格とプロジェクト横断検索 |

---

## 2. アーキテクチャ

### 2.1 3 層構造

```
Layer 1: Learning Engine (learning_engine.py)
    分析・recipe 生成・検証情報収集

Layer 2: Recipe Store (recipe_store.py)
    プロジェクトローカルの recipe 保存・検索・推薦

Layer 3: Global Store (global_store.py)
    グローバル DB への同期・昇格・プロジェクト横断検索
```

### 2.2 データフロー

```
SQLite helix.db (task_runs + action_logs + observations)
    |
    v
learning_engine.analyze_success()  /  analyze_failure()
    |
    v
recipe dict (構造化パターン)
    |
    +---> .helix/recipes/*.json (プロジェクトローカル)
    |
    v
recipe_store.from_history(query)  -- ローカル検索・失敗警告
    |
    v
global_store.sync_from_local()
    |
    +---> ~/.helix/global.db (recipe_index テーブル)
    +---> ~/.helix/recipes/*.json (グローバル recipe ファイル)
    |
    v
global_store.search_global(query)  -- プロジェクト横断検索
    |
    v
global_store.get_promotion_candidates()  -- 昇格候補の抽出
    |
    v
global_store.record_promotion()  -- 昇格記録
```

---

## 3. Recipe 生成フロー

### 3.1 成功パターン分析 (`analyze_success`)

```
入力: task_run_id, db_path
    |
    v
1. task_runs テーブルから完了済みタスクを取得
   - status = 'completed' であることを検証
    |
    v
2. action_logs テーブルからアクション一覧を取得
   - action_index ASC でソート
   - 各アクションの action_type, action_desc, status, evidence を抽出
    |
    v
3. observations テーブルから通過率を集計
   - total, passed を COUNT/SUM
    |
    v
4. 品質スコア算出
   - action_pass_rate = passed_actions / total_actions
   - observation_pass_rate = passed_observations / total_observations
   - quality_score = (action_pass_rate * 0.45 + observation_pass_rate * 0.55) * 100
    |
    v
5. パターンキー生成
   - _build_pattern_key(task_type, action_types)
   - 形式: "{task_type_slug}::{action_types_head}::{sha1_digest}"
    |
    v
6. 分類・タグ付け
   - builder_type 推定 (_guess_builder_type)
   - tags: ["task:xxx", "role:xxx", "action:xxx", ...]
    |
    v
7. 知見の自動推論
   - _infer_why_it_worked(): なぜ成功したかの推論
   - _infer_applicability(): どこで再利用できるかの推論
    |
    v
8. 検証情報収集
   - _collect_verification(): テスト結果、契約検証、品質チェック
    |
    v
9. 秘密情報 redaction
   - 全フィールドを _redact() で処理
    |
    v
出力: recipe dict
```

### 3.2 失敗パターン分析 (`analyze_failure`)

成功パターンと同様の流れだが、以下が異なる:

| 項目 | 成功 | 失敗 |
|------|------|------|
| ステータス検証 | `status = 'completed'` | `status != 'completed'` |
| スコア算出 | `(action_pass * 0.45 + obs_pass * 0.55) * 100` | `100 - ((action_fail * 0.45 + obs_fail * 0.55) * 100)` |
| 追加分析 | why_it_worked, applicability | failure_type 分類, failure_reason 抽出, 再発防止テンプレート |
| pattern_key | `{task_type}::...` | `{task_type}-failure::...` |
| recipe_id | `recipe-{run_id}-{hash}` | `recipe-failure-{run_id}-{hash}` |

### 3.3 Builder 実行の分析

Builder System の実行結果も Learning Engine で分析可能。`builder_executions` テーブルの行 ID を負数エンコード（`-1 * row_id`）することで、通常の `task_runs` の正の ID と区別する。

```python
def _encode_builder_execution_run_id(builder_row_id: int) -> int:
    return -1 * int(builder_row_id)
```

---

## 4. 品質スコア算出

### 4.1 成功時スコア

```
quality_score = (action_pass_rate * 0.45 + observation_pass_rate * 0.55) * 100.0
```

| 要素 | 重み | 定義 |
|------|------|------|
| action_pass_rate | 45% | `passed_or_completed_actions / total_actions` |
| observation_pass_rate | 55% | `passed_observations / total_observations` |

**設計意図**: observation（keyword 照合による客観的検証）を action（エージェントの自己申告）より重く評価する。

### 4.2 失敗時スコア

```
quality_score = max(0, 100 - ((action_failure_rate * 0.45 + observation_failure_rate * 0.55) * 100.0))
```

失敗 recipe でもスコアを持たせることで、検索時の比較を可能にする。スコアが低いほど不安定なパターン。

### 4.3 検証ボーナス（グローバル検索時）

グローバル検索・recipe 検索時に verification 情報に基づくボーナスが加算される:

| 条件 | ボーナス |
|------|---------|
| テスト全 pass（failed = 0, total > 0） | +5.0 |
| スキーマ検証 OK（schema_valid = true） | +3.0 |
| Lint clean（lint_errors = 0） | +2.0 |
| **最大合計** | **+10.0** |

---

## 5. パターンマッチング

### 5.1 Pattern Key の構造

```
{task_type_slug}::{action_types_head(4件)}::{sha1_digest(10文字)}
```

例: `api-implementation::search_api__generate_code__verify_test__review::a1b2c3d4e5`

- `task_type_slug`: タスクタイプを slug 化（小文字、特殊文字をハイフンに変換）
- `action_types_head`: 最初の 4 アクションタイプを `__` で結合
- `sha1_digest`: 全アクションタイプから生成したハッシュ（10 文字）

### 5.2 失敗タイプ分類

`_classify_failure_type()` は出力ログ・アクションログ・observation から失敗タイプを判定する:

| 失敗タイプ | 検出パターン | 再発防止テンプレート |
|-----------|------------|-------------------|
| `syntax_error` | SyntaxError, invalid syntax, parse error, error TS | 静的検査（lint/type-check）を修正前後で実行 |
| `timeout` | timeout, timed out, deadline exceeded | 重い処理を分割し、タイムアウト閾値とリトライ条件を明示 |
| `test_failure` | test(s) failed, pytest, jest, playwright, assertion failed | 失敗テストを最小再現として固定し、1件ずつ修正 |
| `gate_failure` | gate, G1-G8, phase guard, deliverable gate, freeze | ゲート要件をチェックリスト化し、未達項目を埋めてから再判定 |
| `runtime_error` | 上記に該当しない場合のフォールバック | 入力境界・null許容・例外処理を明示し、異常系の再現テストを追加 |

**優先順位**: テスト実行系 action が failed なら `test_failure` を最優先。その後はパターン順にマッチング。

### 5.3 Builder Type 推定

`_guess_builder_type()` はアクションタイプとタスクタイプから builder_type を推定する:

| 推定結果 | 判定条件 |
|---------|---------|
| `agent-skill` | action に "skill" を含む、または task_type に "review" を含む |
| `verify-script` | action に "verify", "script" を含む |
| `sub-agent` | action に "sub-agent" を含む |
| `task` | action に "task" を含む、またはフォールバック |

---

## 6. 検証情報収集

`_collect_verification()` はプロジェクトの検証状態を 3 カテゴリで収集する。結果はキャッシュされ、同一セッション内では再収集しない。

### 6.1 テスト結果 (`_collect_test_results`)

| 収集対象 | 方法 |
|---------|------|
| helix test 結果 | ログファイル or DB から `Results: N passed, M failed` をパース |
| verify スクリプト一覧 | `verify/*.sh` のファイルリスト |
| カバレッジ | coverage-summary.json (Istanbul), .coverage (Python), coverage.out (Go) |

### 6.2 契約検証 (`_collect_contract_results`)

| 収集対象 | 方法 |
|---------|------|
| API 差分 | openapi-diff で breaking change を検出 |
| 型チェック | tsc --noEmit (TypeScript) / mypy (Python) |
| スキーマ検証 | matrix_compiler 経由で matrix.yaml の整合性を検証 |

### 6.3 品質チェック (`_collect_quality_results`)

| 収集対象 | 方法 |
|---------|------|
| Lint | ruff (Python), eslint (JS/TS), flake8 (Python) — 優先順に検出 |
| セキュリティ | npm audit (Node.js), pip-audit (Python) — high + critical をカウント |
| テキスト品質 | textlint で日本語・英語のエラー数をカウント |

---

## 7. Recipe Store（ローカル検索・推薦）

### 7.1 ストレージ

- パス: `.helix/recipes/*.json`
- 各 recipe は独立した JSON ファイルとして保存
- recipe_id をファイル名に使用

### 7.2 検索・推薦フロー (`from_history`)

```
query: "api implementation security"
    |
    v
1. .helix/recipes/*.json を全読み込み
    |
    v
2. 各 recipe をスコアリング
   - text_hits: pattern_key + classification + notes + source のテキスト一致
   - tag_hits: classification.tags との一致
   - quality: quality_score / 100.0
   - summary_hits: summary テキストとの一致
   score = (text_hits/N * 70) + (tag_hits/N * 20) + (quality * 10) + (summary_hits/N * 10)
    |
    v
3. 結果を分類
   - success = true の recipe -> recommendations
   - success = false / failure_type あり -> warnings + failure_recipes
    |
    v
出力: { recommendations, warnings, failure_recipes }
```

**失敗警告**: 過去に失敗したパターンが検出された場合、failure_reason を含む警告メッセージを返す。

### 7.3 Recipe 解決順序

`load_recipe(recipe_id)` はプロジェクトローカル -> ユーザーグローバルの順で解決する:

1. `.helix/recipes/{recipe_id}.json`
2. `~/.helix/recipes/{recipe_id}.json`

---

## 8. Global Store（プロジェクト横断）

### 8.1 グローバル DB スキーマ

**パス**: `~/.helix/global.db`

```sql
-- recipe_index: プロジェクト横断の recipe カタログ
CREATE TABLE recipe_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id TEXT NOT NULL,
    pattern_key TEXT NOT NULL,
    builder_type TEXT DEFAULT '',
    project_id TEXT NOT NULL,
    success_rate REAL DEFAULT 0.0,
    quality_score_mean REAL DEFAULT 0.0,
    tags_json TEXT DEFAULT '[]',
    context_json TEXT DEFAULT '{}',
    verification_json TEXT DEFAULT '{}',
    local_path TEXT DEFAULT '',
    global_path TEXT DEFAULT '',
    promotion_status TEXT DEFAULT 'none',  -- none | promoted | generated
    success_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(pattern_key, project_id)
);

-- promotion_records: 昇格履歴
CREATE TABLE promotion_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    promotion_id TEXT UNIQUE NOT NULL,
    recipe_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    builder_type TEXT NOT NULL,
    artifact_ref TEXT DEFAULT '',
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

### 8.2 同期フロー (`sync_from_local`)

```
ローカル helix.db
    |
    v
1. task_runs から status = 'completed' のレコードを取得
    |
    v
2. 各レコードに対して:
   a. .helix/recipes/ から既存 recipe を検索
   b. 見つからなければ analyze_success() で新規生成
    |
    v
3. pattern_key でグルーピング
   - success_count, quality_mean を集計
    |
    v
4. recipe ファイルを ~/.helix/recipes/ にコピー（秘密情報 sanitize 済み）
    |
    v
5. global.db の recipe_index に UPSERT
   - ON CONFLICT(pattern_key, project_id) DO UPDATE
```

### 8.3 グローバル検索スコアリング (`search_global`)

| 要素 | 重み | 算出方法 |
|------|------|---------|
| pattern_score | 55 | pattern_key 内のトークン一致率 |
| tag_score | 25 | tags とのトークン一致率 |
| success_score | 10 | min(success_count / 5, 1.0) |
| quality_score | 10 | min(quality_score_mean / 100, 1.0) |
| verification_bonus | +10 | テスト全pass(+5), schema_valid(+3), lint clean(+2) |

**クエリなしの場合**: success_count と quality_score_mean のみでランキング。

### 8.4 昇格フロー

```
1. get_promotion_candidates(threshold=3)
   - success_count >= threshold かつ promotion_status NOT IN ('promoted', 'generated')
    |
    v
2. record_promotion(recipe_id, artifact_type, builder_type, artifact_ref, status, project_id)
   - promotion_records に INSERT
   - recipe_index の promotion_status を更新
```

昇格は `helix promote` コマンドから呼び出される。

---

## 9. 秘密情報保護

Learning Engine 全体を通じて、以下の多層 redaction が適用される:

### 9.1 キーワードベース

辞書キーまたは値に以下のトークンを含む場合 `[REDACTED]` に置換:

```
password, passwd, token, secret, apikey, api_key, api-key,
access_token, refresh_token, private_key, credential,
authorization, bearer, ssh-rsa, -----begin, /home
```

### 9.2 パターンベース

正規表現で以下のパターンを検出して `[REDACTED]` に置換:

| パターン | 検出対象 |
|---------|---------|
| `Bearer [token]` | OAuth Bearer トークン |
| `sk-[...]` | OpenAI API キー |
| `ghp_[...]` | GitHub Personal Access Token |
| `xox[bap]-[...]` | Slack トークン |

### 9.3 Global Store 追加 sanitize

`sync_from_local()` 時に `_sanitize_recipe()` で recipe 全体を再度 walk して redaction を適用。グローバル共有される recipe には二重の保護がかかる。

---

## 10. 関連文書

| 文書 | パス |
|------|------|
| CLI アーキテクチャ設計 | `docs/design/L2-cli-architecture.md` |
| Builder System 設計 | `docs/design/L2-builder-system.md` |
| ADR-005 YAML-SQLite 二重状態管理 | `docs/adr/ADR-005-yaml-sqlite-dual-state.md` |
| R2 As-Is Design | `.helix/reverse/R2-as-is-design.md` |
