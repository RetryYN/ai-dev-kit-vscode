# D-RECIPE-SPEC: Recipe 自動昇格閾値と Learning Engine 仕様

> Status: Accepted
> Date: 2026-04-14
> Authors: TL

---

## 1. 目的

Learning Engine が生成する recipe の自動昇格閾値と運用仕様を明文化する。GAP-029「recipe の自動昇格閾値が文書化されていない」の解消を目的とする。

---

## 2. Recipe のライフサイクル

```
┌──────────────────────┐
│ Task 実行完了         │  Codex / Sonnet / Builder が成果物生成
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ 成功パターン収集      │  helix log で task_runs / gate_runs 記録
└──────────┬───────────┘
           ↓ helix learn
┌──────────────────────┐
│ Recipe 生成           │  learning_engine.py が成功パターンを抽象化
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Recipe Store 保存     │  .helix/recipes/ に YAML 形式で蓄積
└──────────┬───────────┘
           ↓ 同パターン N 回発生
┌──────────────────────┐
│ 自動昇格候補          │  helix promote --auto で閾値超え recipe を表示
└──────────┬───────────┘
           ↓ 人間承認
┌──────────────────────┐
│ Builder 生成物に昇格  │  helix promote <recipe-id> --type <skill|script|task|sub-agent>
└──────────────────────┘
```

---

## 3. 自動昇格閾値

### 3.1 デフォルト閾値

`helix promote --auto` のデフォルト閾値は **3 回**:

```python
# cli/helix-promote L97-101
parser.add_argument(
    "--threshold",
    type=int,
    default=3,
    help="--auto 時の候補しきい値（デフォルト: 3）",
)
```

### 3.2 閾値の根拠

3 回を採用した理由:

- **2回では偶然の可能性**: 同一パターンが偶発的に2度発生しても学習価値は低い
- **4回以上では昇格遅延**: 蓄積を待ちすぎると類似タスクで恩恵を受けられない
- **3回は再現可能性の最小値**: 「再現できるパターン」の実証として妥当

### 3.3 閾値の運用

| 用途 | 推奨閾値 |
|------|---------|
| プロジェクト初期 | 2（パターン発見を優先） |
| 運用中盤 | 3（デフォルト） |
| 成熟プロジェクト | 5（ノイズ排除を優先） |

`helix promote --auto --threshold <N>` で変更可能。

---

## 4. 昇格先種別

Recipe は以下の4種類のビルダー生成物に昇格できる:

| 昇格先 (--type) | 対象 Builder | 用途 |
|---------------|------------|------|
| `skill` | agent_skill | SKILL.md（再利用可能スキル） |
| `script` | verify_script | 検証スクリプト（verify/*.sh） |
| `task` | task_builder | タスクカタログエントリ |
| `sub-agent` | sub_agent | Claude Code サブエージェント定義 |

### 4.1 自動分類（_infer_promote_type）

`helix-promote` は recipe の内容から昇格先を推論する:

```python
# cli/helix-promote L146
def _infer_promote_type(recipe, preferred):
    # 1. preferred 指定があれば優先
    # 2. recipe tags から推論（例: "skill-tag" → skill）
    # 3. recipe structure から推論（例: actions[] あり → task）
    # 4. 推論できない場合はエラー
```

---

## 5. Recipe 生成ロジック

### 5.1 入力データ

`learning_engine.py` は以下から recipe を生成:

| ソース | テーブル | 情報 |
|--------|---------|------|
| タスク実行 | `task_runs` | タスク ID / 結果 / 成果物 |
| アクションログ | `action_logs` | アクション種別 / 成功率 |
| ゲート実行 | `gate_runs` | ゲート通過パターン |
| ビルダー実行 | `builder_executions` | ビルダー固有成功パターン |

### 5.2 パターン抽出

`analyze_success_patterns()` が以下を抽出:

- **同一タスクが N 回以上成功**
- **同一アクション列が再現**（grep → read → write → test の順序等）
- **同一ゲート通過パターン**（G3 → G4 → G5 と連続通過）

### 5.3 Recipe フォーマット

```yaml
# .helix/recipes/RCP-001.yaml
recipe_id: RCP-001
created_at: 2026-04-14
pattern_type: task_execution
occurrence_count: 5
success_rate: 1.0
tags: [be, api, crud]
summary: "BE CRUD API 実装パターン"
actions:
  - type: grep_search
    target: "既存 endpoint"
  - type: read
    target: "API 設計書"
  - type: write
    target: "実装コード"
  - type: test
    target: "unit + integration"
verification:
  - "pytest 全件通過"
  - "mypy 0 errors"
promoted: false
promoted_to: null
```

---

## 6. Recipe Store

### 6.1 保存階層（4層検索）

ADR-003 の決定に従い、recipe は以下の順で検索される:

1. **プロジェクトローカル**: `.helix/recipes/` （プロジェクト固有）
2. **ユーザーグローバル**: `~/.helix/recipes/` （全プロジェクト横断）
3. **共有インストール**: `$HELIX_HOME/recipes/` （チーム共有、将来実装）
4. **リモートハブ**: `https://hub.example.com/recipes/` （将来実装）

`find_recipe(recipe_id, project_root)` がこの順で検索。

### 6.2 重複管理

- 同一 `recipe_id` の重複は禁止
- パターンマッチングでの類似検出は `recipe_store.py` の similarity 関数で実施
- 重複検出時は後勝ち（新しい recipe が古いを上書き）

---

## 7. 昇格時の検証

`helix promote <recipe-id>` 実行時の verify:

1. **recipe 整合性**: 必須フィールド完備、形式正当性
2. **promote_type 適合性**: 対象 builder の INPUT_SCHEMA を満たすか
3. **verification チェック**: recipe の verification セクションの項目が実際に通るか

失敗時は `--force` で強制昇格可能（警告のみ）。

---

## 8. 観測指標

`helix log report quality` で以下を表示:

| 指標 | 意味 | 推奨値 |
|------|------|--------|
| Recipe 生成率 | タスク実行数 / Recipe 数 | 10-20% |
| 自動昇格候補数 | threshold 超え recipe 数 | プロジェクト規模による |
| 昇格実行率 | 候補 / 実際に昇格 | 30-50% |
| 昇格後の再利用率 | 昇格 recipe / 実際に再利用 | 60% 以上 |

---

## 9. 既知の制約・今後の課題

| 項目 | 内容 | 優先度 |
|------|------|------|
| 閾値が単一（回数のみ） | 成功率・品質スコアとの複合閾値は未実装 | P2 |
| パターン類似度の評価が単純 | tags 一致率のみで、内容的類似性は未評価 | P2 |
| 昇格後の recipe の扱い | 昇格後も同パターンが発生した場合の統計 | P3 |
| リモートハブ未実装 | 共有インストール・リモートハブ層は将来拡張 | P2 |
| learning_engine.py のモノリス | 2000行の単一ファイル、責務分割が望ましい | P2（GAP-037） |

---

## 10. References

- `cli/lib/learning_engine.py` (2000行)
- `cli/lib/recipe_store.py` (245行)
- `cli/helix-promote` (431行)
- `cli/helix-learn` (193行)
- `cli/helix-discover` (202行)
- [ADR-003: Learning Engine Foundations](../adr/ADR-003-learning-engine.md)
- [docs/design/L2-learning-engine.md](./L2-learning-engine.md)
