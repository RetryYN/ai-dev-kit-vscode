# ADR-008: ビルダーシステムによる成果物生成の抽象化

> Status: Accepted
> Date: 2026-04-14
> Deciders: PM, TL

---

## Context

HELIX CLI は多様な成果物を生成する必要がある:

- AI エージェント定義（agent-loop, agent-pipeline, agent-skill, sub-agent）
- ワークフロー定義（workflow, task）
- 検証スクリプト（verify-script）
- データ変換（json-converter）

これらの成果物生成には共通する要素がある:

- 入力パラメータのスキーマ検証
- 成果物ファイルの生成（JSON/YAML/Bash）
- 成果物の品質検証
- 実行履歴の記録
- パターン検索（過去の成功例から類似ケースを検索）

当初は各コマンドが独自実装していたが、以下の問題が顕在化した:

- 実装の重複（同じロジックが複数ファイルに散在）
- 品質チェックの不統一
- 履歴記録の欠如（学習エンジンへの接続困難）
- テストの困難さ（個別コマンドごとにモック構築が必要）

---

## Decision

**Builder System として統一的な抽象化層を導入する** ことを採用する。

### アーキテクチャ

```
┌─────────────────────────────────────────┐
│         helix builder CLI               │  ← ユーザーインターフェイス
│         (cli/lib/builders/cli.py)       │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      BuilderRegistry                    │  ← ビルダー登録・検索
│      (registry.py)                      │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      BuilderBase (抽象基底)             │  ← 共通ライフサイクル
│      (base.py)                          │
│      - validate_input()                 │
│      - generate()                       │
│      - validate_output()                │
│      - build() (テンプレートメソッド)    │
└───────────────┬─────────────────────────┘
                ↓
     ┌──────────┼──────────┐
     ↓          ↓          ↓
  AgentLoop  Workflow  JsonConverter  ...  (9種類の具象ビルダー)
     │          │          │
     └──────────┼──────────┘
                ↓
┌─────────────────────────────────────────┐
│  BuilderStore (履歴・状態)              │  ← SQLite 永続化
│  BuilderHistory (実行履歴)              │
└─────────────────────────────────────────┘
```

### ビルダーの契約

各ビルダーは `BuilderBase` を継承し、以下を実装する:

- `BUILDER_TYPE`: ビルダー識別子（クラス属性）
- `INPUT_SCHEMA`: 入力パラメータの JSON Schema
- `generate(params, seed) -> list[artifacts]`: 成果物生成ロジック
- `validate_output(artifacts) -> dict`: 品質検証（valid, quality_score 等）

### 共通ライフサイクル（`build()`）

```python
def build(self, task_id, input_params):
    self.validate_input(input_params)         # JSON Schema 検証
    artifacts = self.generate(input_params)   # 成果物生成
    validation = self.validate_output(artifacts)  # 品質検証
    self.store.record_execution(              # 履歴記録
        builder_type=self.BUILDER_TYPE,
        task_id=task_id,
        artifacts=artifacts,
        validation=validation,
    )
    return artifacts, validation
```

### 現在登録されている9ビルダー

| ビルダー | 用途 | 生成物 |
|---------|------|--------|
| agent-loop | ループ型エージェント | エージェント定義 JSON |
| agent-pipeline | パイプライン型エージェント | エージェント定義 JSON |
| agent-skill | スキル定義 | SKILL.md |
| sub-agent | Claude サブエージェント | agent 定義 Markdown |
| workflow | ワークフロー定義 | ワークフロー YAML |
| task | タスク定義 | タスク YAML |
| verify-script | 検証スクリプト | Bash スクリプト |
| json-converter | JSON 変換 | 変換ロジック JSON |
| cli | Builder CLI dispatch | (N/A: cli.py 自身) |

---

## Alternatives

### A1: 各コマンドに独自実装を維持

- 利点: 初期実装コストが低い
- 欠点: 重複コード、品質不統一、履歴記録なし（既に顕在化していた問題）

### A2: プラグインアーキテクチャ（動的ロード）

- 利点: ビルダーの追加が実行時可能
- 欠点: 型チェックが弱くなる、依存関係が不透明、テストが困難

### A3: テンプレートエンジン + 設定ファイル駆動

- 利点: コードを書かずに新ビルダーを追加可能
- 欠点: 複雑なロジック（動的な生成処理）が表現できない、デバッグが困難

---

## Consequences

### 正の影響

- **実装統一**: 共通ライフサイクル（validate_input → generate → validate_output → record）により品質担保
- **テスト容易性**: `BuilderBase` の契約をテストすることで全ビルダーの基本動作を担保（test_builders_concrete.py でパラメタ化テスト可能）
- **学習エンジン接続**: `BuilderHistory` が実行履歴を SQLite に記録 → `learning_engine.py` が類似パターン検索可能
- **ビルダー追加の容易さ**: `BuilderBase` を継承し `registry.register()` で登録するだけ

### 負の影響

- **抽象化コスト**: 新規ビルダー追加時に `BuilderBase` の契約を理解する必要がある
- **継承階層の深さ**: 2段（BuilderBase → 具象ビルダー）だが、将来カテゴリ中間層を追加する可能性あり
- **Python 依存**: Builder System は Python 実装。Bash CLI からは `python3 cli/lib/builders/cli.py` 経由でアクセス（ADR-004 Bash-Python ハイブリッドに従う）

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| `BuilderBase` 変更が全ビルダーに波及 | 基底クラスの API は厳密にバージョン管理、破壊的変更は CHANGELOG 必須 |
| 具象ビルダーのテスト不足 | `test_builders_concrete.py` で全ビルダーを網羅（GAP-020で追加） |
| quality_score の算出基準がビルダー間で不統一 | 将来の D-QUALITY-SPEC.md で統一基準を定める（GAP-028） |

---

## References

- `cli/lib/builders/base.py` (BuilderBase 実装)
- `cli/lib/builders/registry.py` (BuilderRegistry)
- `cli/lib/builders/store.py` (BuilderStore, BuilderHistory)
- `cli/lib/builders/{agent_loop, agent_pipeline, ...}.py` (9具象ビルダー)
- `cli/lib/tests/test_builders.py` / `test_builders_concrete.py` (テスト)
- `docs/design/L2-builder-system.md` (設計書)
- `docs/design/D-BUILDER-INTEGRATION.md` (CLI 統合設計)
- ADR-002: Builder System Foundations（上位方針）
