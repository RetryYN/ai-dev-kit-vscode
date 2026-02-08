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
