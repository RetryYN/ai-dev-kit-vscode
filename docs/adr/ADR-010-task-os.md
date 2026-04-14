# ADR-010: Task OS（2層構造: タスク→アクション）

> Status: Accepted
> Date: 2026-04-14
> Deciders: PM, TL

---

## Context

HELIX CLI は開発タスクを AI エージェント（Codex / Claude Sonnet）に委譲する際、以下の課題があった:

- **タスク分類の欠如**: 「BE実装」「テスト追加」「ドキュメント作成」等の分類が暗黙的
- **実行手順の不明瞭さ**: 同種タスクで毎回プロンプトを組み立て直す非効率
- **品質検証の不統一**: タスク完了判定の基準が曖昧（AI が「完了しました」と言っても実際は未完成のケース）
- **学習の困難さ**: 過去のタスク実行から何が成功し何が失敗したかを体系的に追跡できない

初期実装では `helix-codex --role <role> --task "<自由記述>"` でタスクを文字列として委譲していたが、再現性・品質保証・学習データ蓄積の面で限界があった。

---

## Decision

**Task OS として2層構造のタスク管理システムを導入する**:

### 2層構造

```
┌─────────────────────────────────────┐
│  Layer 1: タスク (63種類・12カテゴリ) │  ← PM が選択する計画単位
│  - 目的・完了条件・見積             │
│  - ロール指定（tl/se/pg/qa 等）     │
│  - 必須スキル（参照すべき SKILL.md） │
│  - 実行アクションリスト             │
└──────────────┬──────────────────────┘
               ↓ 展開
┌─────────────────────────────────────┐
│  Layer 2: アクション (27種類・295個) │  ← エージェントが実行する操作単位
│  - 具体的な操作（Grep, Write, Test） │
│  - 観測条件（expect_keywords）      │
│  - 証跡収集（evidence）             │
└─────────────────────────────────────┘
```

### タスクカタログ（`cli/templates/task-catalog.yaml`）

63タスクを12カテゴリに分類:

- be（BE実装）: 12タスク
- fe（FE実装）: 10タスク
- db（DB設計）: 8タスク
- qa（テスト・検証）: 8タスク
- docs（ドキュメント）: 7タスク
- security（セキュリティ）: 5タスク
- devops（インフラ）: 4タスク
- research（調査）: 4タスク
- refactor（リファクタリング）: 3タスク
- review（レビュー）: 2タスク

各タスクには以下を定義:

```yaml
- task_id: BE-001
  category: be
  name: "API エンドポイント実装"
  role: pg
  estimate: M
  skill: common/coding
  actions:
    - { type: grep, target: existing endpoints }
    - { type: read, target: API 設計書 }
    - { type: write, target: 実装コード }
    - { type: test, target: unit + integration }
    - { type: verify, target: linter + type check }
```

### アクションタイプ（`cli/templates/action-types.yaml`）

27種類のアクションを定義。各アクションには:

- `name`: アクション識別子
- `desc`: 説明
- `tool`: 使用ツール（Grep, Read, Write, Bash 等）
- `observe`: 観測条件（期待キーワード、証跡）

例:
```yaml
grep_search:
  name: "内部検索"
  desc: "コードベース・設計書・既存ドキュメント内の検索"
  tool: "Grep, Glob, Read"
  observe:
    expect_keywords: ["grep", "found", "検索", "結果", "件"]
    evidence: "検索クエリと結果件数"
```

### 実行フロー（`helix-task`）

```
helix task catalog           # カタログ一覧表示
helix task plan <task_id>    # タスク実行計画（アクション展開）
helix task run <run_id>      # 実行（Codex / Claude に委譲）
helix task observe <run_id>  # アクション品質検証（keyword 照合）
helix task status            # 実行履歴
```

### SQLite 永続化（`helix.db`）

- `task_runs` テーブル: タスク実行履歴
- `action_runs` テーブル: アクション単位の実行ログ
- `task_observations` テーブル: 観測結果（expect_keywords ヒット率等）

---

## Alternatives

### A1: タスクを自由記述文字列のまま維持

- 利点: 柔軟、新規タスクの表現が容易
- 欠点: 再現性なし、品質検証不能、学習データ化困難（既に顕在化していた問題）

### A2: 単層構造（タスク = アクション）

- 利点: シンプル
- 欠点: 1タスクに複数のアクションが含まれる現実を表現できない、アクションレベルの観測ができない

### A3: 3層構造（プロジェクト → タスク → アクション）

- 利点: 大規模プロジェクトの階層管理が可能
- 欠点: オーバーエンジニアリング、HELIX の既存フェーズ（L1-L8）と責務が重複

---

## Consequences

### 正の影響

- **再現性**: タスク ID で同種タスクを再現可能（同じプロンプト・同じチェック）
- **品質検証**: アクション単位で observe（keyword 照合）による品質チェック
- **学習データ**: タスク成功・失敗パターンを SQLite で蓄積 → `learning_engine.py` が recipe 生成
- **PM の認知負荷軽減**: `helix task catalog` で選ぶだけで適切なアクション展開

### 負の影響

- **カタログメンテナンス**: 63タスク × 27アクションの定義を最新に保つ必要
- **新規タスクの追加コスト**: 自由記述より定義が重い
- **表現の限界**: 想定外タスクはカタログにない → 自由記述モード（`helix codex --role --task "..."`）も併存

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| カタログ陳腐化 | `helix task observe` で keyword ヒット率を計測 → 低下タスクを警告 |
| アクション粒度のブレ | action-types.yaml を正本として全タスクが参照、粒度は review で統一 |
| 自由記述との二重管理 | PM のみ自由記述を許可、SE 以下は カタログのみ（運用ルール） |
| SQLite スキーマ変更時の互換性 | `helix_db.py` のマイグレーション機構（v1→v4 実績あり） |

---

## References

- `cli/helix-task` (Task OS CLI)
- `cli/templates/task-catalog.yaml` (63タスク定義)
- `cli/templates/action-types.yaml` (27アクション定義)
- `cli/lib/helix_db.py` (task_runs, action_runs, task_observations テーブル)
- `cli/lib/learning_engine.py` (タスク実行パターンの学習)
- ADR-003: Learning Engine Foundations（学習エンジン連携）
- ADR-005: YAML-SQLite Dual State（状態管理方針）
