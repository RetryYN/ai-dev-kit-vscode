# D-QUALITY-SPEC: Builder quality_score 統一基準

> Status: Draft（統一基準の提案段階）
> Date: 2026-04-14
> Authors: TL

---

## 1. 目的

Builder System の各ビルダーが算出する `quality_score` の基準が不統一である問題（GAP-028）を解消するため、統一基準を策定する。本文書は現状分析と提案を含む。

---

## 2. 現状分析

### 2.1 現在の実装

9つの具象ビルダー全てが `validate_output()` で `quality_score: 100` を返している:

| ビルダー | quality_score | 算出方法 |
|---------|--------------|---------|
| agent_loop | 100 | ハードコード |
| agent_pipeline | 100 | ハードコード |
| agent_skill | 100 | ハードコード |
| sub_agent | 100 | ハードコード |
| workflow_builder | 100 | ハードコード |
| task_builder | 100 | ハードコード |
| verify_script | 100 | ハードコード |
| json_converter | 100 | ハードコード |

### 2.2 問題点

- **品質の差異が現れない**: 全ビルダーで 100 点なので、Learning Engine が成功パターンを抽出しても品質情報にバリエーションなし
- **validate_output() の形骸化**: 実装は通過/失敗のみで、品質の度合い（スコア）が活用されていない
- **history.py の score 計算**: `builder_history.py` は quality_score を 10倍して検索スコアに組み込む（L242）が、全て 100 なので一定値

### 2.3 history.py での利用

```python
# cli/lib/builders/history.py L242
quality_score = quality * 10.0
return text_score + tag_score + quality_score + summary_score + verification_bonus
```

この計算は `quality_score` が差別化されていないため、類似検索ランキングに寄与していない。

---

## 3. 統一基準の提案

### 3.1 スコア範囲

`quality_score` は **0.0〜100.0 の float** とし、以下のスケールで解釈する:

| スコア範囲 | 意味 |
|----------|------|
| 95-100 | 完璧（全検査項目パス、警告なし） |
| 80-94 | 高品質（軽微な警告あり、機能的に問題なし） |
| 60-79 | 許容レベル（複数警告、一部改善推奨） |
| 40-59 | 要改善（重大な警告、手動確認必須） |
| 0-39 | 低品質（多数の失敗、成果物再生成推奨） |

### 3.2 共通チェック項目（全ビルダー共通）

以下の項目は全ビルダーで評価する:

| 項目 | 配点 | 説明 |
|------|------|------|
| **required_fields 完備** | 20点 | INPUT_SCHEMA の必須フィールドが全て埋まっているか |
| **スキーマ検証** | 20点 | 生成物が期待スキーマに準拠するか |
| **空/極小ファイル回避** | 10点 | 生成物が 10 bytes 以上あるか（空ファイル検出） |
| **構文/形式検証** | 15点 | 生成物の形式が正しい（JSON parse / YAML parse / py_compile） |
| **セキュリティ静的チェック** | 15点 | 秘密情報・コマンドインジェクションパターンの混入なし |
| **命名規則** | 10点 | 生成物のファイル名・識別子が規約に準拠 |
| **ビルダー固有項目** | 10点 | 各ビルダー固有の品質基準（§3.3） |

合計 100 点。

### 3.3 ビルダー固有項目（10 点配分）

各ビルダーの固有チェック項目:

| ビルダー | 固有チェック |
|---------|-----------|
| agent_loop | stop_condition の妥当性、max_iterations の上限 |
| agent_pipeline | nodes の DAG 整合性、循環参照なし |
| agent_skill | YAML frontmatter 完備、triggers 最低1件 |
| sub_agent | Claude Code agent 定義の必須セクション完備 |
| workflow_builder | edges の整合性、nodes 全参照 |
| task_builder | actions 最低1件、observe セクション完備 |
| verify_script | Bash 構文チェック（bash -n）、set -euo pipefail 含む |
| json_converter | 変換ロジックの可逆性（テストデータで往復確認） |

### 3.4 スコア算出関数（提案）

```python
# cli/lib/builders/base.py に追加予定

def calculate_quality_score(self, artifacts, validations):
    """統一基準での quality_score 算出."""
    score = 0.0
    
    # 共通チェック（90点分）
    if validations.get("required_fields_ok"): score += 20
    if validations.get("schema_valid"):       score += 20
    if validations.get("no_empty_files"):     score += 10
    if validations.get("syntax_valid"):       score += 15
    if validations.get("security_ok"):        score += 15
    if validations.get("naming_ok"):          score += 10
    
    # ビルダー固有（10点分）
    specific = self._specific_quality_check(artifacts)
    score += specific.get("score", 0.0)
    
    return score
```

---

## 4. 実装計画（段階的導入）

### Phase 1: 基盤整備（1 Sprint）
- `BuilderBase` に `calculate_quality_score()` 追加
- 共通 validator 関数群を `cli/lib/builders/validators.py` に集約

### Phase 2: ビルダー個別対応（2-3 Sprint）
- 各ビルダーの `validate_output()` を段階的に更新
- 優先順位: task_builder → verify_script → agent_skill → その他
- ハードコード `100` を実際の計算結果に置換

### Phase 3: Learning Engine 連携強化（1 Sprint）
- `builder_history.py` の score 計算で quality_score 差別化が反映されることを確認
- `helix learn` の recipe 抽出で品質別にパターン分類

### Phase 4: 閾値チューニング（継続）
- quality_score 分布を `helix bench` で観測
- 実運用データから合格ライン（promote 閾値）を調整

---

## 5. 既存 API の互換性

- `validate_output()` の戻り値形式は維持（dict with `valid`, `quality_score`, `errors`）
- `quality_score` が float になる点のみ変更（現状は int 100、変更後は float 0.0-100.0）
- `builder_history.py` の score 計算は引き続き quality_score * 10.0 を使用

---

## 6. 既知の制約・今後の課題

| 項目 | 内容 | 優先度 |
|------|------|------|
| 現状はハードコード | 全ビルダーで 100 固定、提案は段階実装 | P2（GAP-028 本体） |
| ビルダー固有チェックの重み不均一 | 10点配分では細かい差別化が困難 | P3 |
| quality_score の意味のドリフト | 複数ビルダーで同じ 80 点でも意味が異なる可能性 | P3 |
| 閾値の実運用検証未実施 | 実データ蓄積後に調整必要 | P3 |

---

## 7. References

- `cli/lib/builders/base.py`（BuilderBase）
- `cli/lib/builders/{agent_loop,agent_pipeline,...}.py` (9ビルダー)
- `cli/lib/builders/store.py` L288-289（_to_quality_score）
- `cli/lib/builders/history.py` L242（score 計算）
- [ADR-002: Builder System Foundations](../adr/ADR-002-builder-system-foundations.md)
- [ADR-008: ビルダー抽象化](../adr/ADR-008-builder-abstraction.md)
- [D-BUILDER-INTEGRATION.md](./D-BUILDER-INTEGRATION.md)
