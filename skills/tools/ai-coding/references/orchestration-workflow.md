# オーケストレーション・ディスパッチワークフロー

> 出典: docs/archive/v-model-reference-cycle-v2.md §工程表のオーケストレーション記載、§サブエージェント間の引継ぎフロー

## ディスパッチフロー

```
Opus (Orchestrator)
  │
  ├─ 1. 工程表の現在行を読み取る
  │     - 工程ID、タスク、難易度、担当モデル、スキル、ツール制限
  │     - 前提工程、参照ドキュメント、検証レイヤー、目標Lv
  │
  ├─ 2. 前提条件を確認
  │     - 前提工程が全て completed か
  │     - 参照ドキュメントが存在するか
  │     ⚠️ 参照先が未指定の工程は実行不可（スキップ）
  │
  ├─ 3. サブエージェントを選定
  │     - subagent-config.md のタスク種別→モデル対応表を参照
  │     - スキル付与、ツール制限、思考トークンを設定
  │
  ├─ 4. 入力を整形して配送（Task tool）
  │     - 下記「サブエージェント I/O 仕様」に従う
  │
  ├─ 5. 出力を検証
  │     - status: completed → 次タスクへ
  │     - status: failed → リトライ（最大3回）→ 人間にエスカレ
  │     - status: blocked → ブロッカーを記録、代替タスクに着手
  │
  └─ 6. 次タスクの入力に変換
        - 前タスクの artifacts を次タスクの context に注入
        - 引継ぎ情報（decisions, changes）をマージ
```

## サブエージェント I/O 仕様

### 入力（Opus → サブエージェント）

```yaml
task_id: "T-001"
task_description: "認証モジュール実装"
context:
  skills: ["security", "api"]       # 読み込むスキル
  tools_allowed: ["Read", "Edit", "Bash"]
  tools_denied: []
  reference_docs:
    - "design/auth.md"
    - "api-contract/auth.yaml"
  prior_outputs: []                 # 前タスクの成果物
expected_output:
  format: "実装コード + テスト"
  quality_target: "Lv4"
  files: ["src/auth/**"]
```

### 出力（サブエージェント → Opus）

```yaml
task_id: "T-001"
status: "completed"                 # completed | failed | blocked | partial
quality_achieved: "Lv4.5"
artifacts:
  - "src/auth/login.ts"
  - "src/auth/login.test.ts"
changes_summary: "JWT認証 + リフレッシュトークンを実装"
decisions:
  - "bcrypt cost factor = 12（パフォーマンスとセキュリティのバランス）"
issues: []                          # 問題がある場合
```

### ブロッカー報告（status: blocked の場合）

```yaml
task_id: "T-003"
status: "blocked"
blocker:
  type: "dependency"                # dependency | unclear_spec | tool_limitation
  description: "外部API仕様が未確定"
  blocked_by: "T-005"              # 依存先タスクID（あれば）
  suggested_action: "T-005完了後に再開"
```

## Opus の自作業禁止ルール

| 作業 | 閾値 | 委譲先 |
|------|------|--------|
| コード実装 | 15行超 | Sonnet (Task tool) / Codex (codex exec) |
| テスト作成 | 常時 | Sonnet (Task tool) |
| ドキュメント作成 | 常時 | Sonnet (Task tool) |
| ファイル一括編集 | 3ファイル超 | Sonnet (Task tool) |
| 調査・検索 | 3クエリ超 | Haiku (Task tool) |
| コードレビュー | 常時 | Codex 5.3 (codex review) |

Opus が自分で行うこと:

- ユーザー意図の言語化・構造化
- タスク分解と工程表の作成・更新
- 外注指示（プロンプト）の作成
- サブエージェント出力のレビュー・統合
- エスカレーション判断（verification §13 参照）
- 最終的な品質判定

## 引継ぎプロトコル（タスク間）

```
Task A (Sonnet) の出力
   ↓
Opus (Orchestrator):
  1. Task A の出力ステータスを確認
  2. artifacts を次タスクの context.prior_outputs に設定
  3. decisions を累積リストに追加
  4. issues があれば対処判断（リトライ/スキップ/エスカレ）
   ↓
Task B へ配送
```

## リトライ・エスカレーション

```
サブエージェント失敗時:
  1回目失敗 → プロンプトを調整してリトライ
  2回目失敗 → エラー内容を追加してリトライ
  3回目失敗 → 人間にエスカレーション

進捗停滞時:
  同一タスク 5リトライ以上 → 人間に状況報告と支援要請
  1タスク 2時間以上 → ブロッカー報告
```

---

## フェーズ I/O 詳細仕様

Opus はフェーズ完了時にこの仕様で出力を検証し、次フェーズの入力に整形する。
サマリーは `SKILL_MAP.md §フェーズ別 I/O サマリー` を参照。

### L1: 要件定義

```yaml
入力:
  user_request: "ユーザーの要求文（自然言語）"
  project_context: "CLAUDE.md / 既存設計書"

出力:
  requirements:
    - id: "REQ-001"
      description: "要件の説明"
      priority: must | should | could
      acceptance_criteria: "受入基準"
  assumptions:
    - id: "A-001"
      content: "仮定の内容"
      status: verified | unverified
  scope:
    in: ["スコープ内"]
    out: ["スコープ外"]
  sizing:
    size: S | M | L
    skip_phases: ["スキップするフェーズ"]

完了条件: 全 REQ に priority + acceptance_criteria 付与済み
```

### L2: 設計

```yaml
入力:
  requirements: "L1 出力"
  scope: "L1 出力"

出力:
  design:
    frontend: "設計書パス or インライン"
    backend: "設計書パス or インライン"
    database: "スキーマ定義パス or インライン"
  decisions:
    - choice: "選択内容"
      reason: "理由"
      rejected: "却下した選択肢"
  risks:
    - description: "リスク内容"
      mitigation: "対策"

完了条件: 全 REQ が設計に反映されている
```

### L2.5: API契約

```yaml
入力:
  design: "L2 出力"

出力:
  api_contract:
    openapi_spec: "パス"
    type_definitions:
      frontend: "パス"
      backend: "パス"
    db_schema: "パス"
  consistency:
    fe_be_match: "100%"
    be_db_match: "100%"

完了条件: FE↔BE↔DB の型一致率 100%
```

### L3: 依存関係

```yaml
入力:
  design: "L2 出力"
  api_contract: "L2.5 出力"

出力:
  dependency_map:
    modules:
      - name: "モジュール名"
        depends_on: ["依存先"]
    execution_order: ["実装順序"]
    parallel_groups:
      - group: 1
        tasks: ["並列可能なタスク"]

完了条件: 循環依存なし + 実装順序決定済み
```

### L4: 工程表

```yaml
入力:
  dependency_map: "L3 出力"
  difficulty_scores: "estimation §9 で算出"

出力:
  schedule:
    - task_id: "T-001"
      task: "タスク内容"
      difficulty: 0-14
      model: "Haiku | Sonnet | Codex 5.3"
      skills: ["読み込むスキル"]
      tools_allowed: ["許可ツール"]
      prerequisites: ["前提タスクID"]
      reference_docs: ["参照ドキュメント"]
      verification_layer: "L2 | L2.5 | L3 | L5"

完了条件: 全タスクに difficulty + model + skills + reference_docs 付与済み
```

### 実装フェーズ

```
入力: L4 出力（schedule）+ 設計書群
出力: 上記「サブエージェント I/O 仕様」に従う（既存）
完了条件: 全タスクの status が completed
```

### 検証フェーズ

```
入力: 実装コード + 設計書群
出力: verification SKILL.md §10 の検証レポートテンプレートに従う
完了条件: 全検証レイヤーで合格（不合格 → レイヤー内5ループ → エスカレ）
```

### 受入フェーズ

```
入力: L1 要件リスト + 最終成果物
出力:
  acceptance:
    - req_id: "REQ-001"
      status: pass | fail
      evidence: "根拠"
完了条件: 全 REQ が pass
```
