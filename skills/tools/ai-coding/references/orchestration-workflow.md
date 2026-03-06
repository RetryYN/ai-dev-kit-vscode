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
  ├─ 2.5. 事前調査ゲート（L1→L2 / L4→L4.5 遷移時）
  │     - ai-coding §8 の強制条件に該当するか PM が判定
  │     - 該当 → Haiku 4.5 に調査タスク配送
  │       └─ 調査レポートを reference_docs に追加
  │     - 非該当 → 「事前調査: スキップ（理由: ...）」を明示
  │     - 検索不可 → status: blocked（オフライン/API制限等）
  │     ⚠️ 機密情報（社内固有名・APIキー・顧客データ）を検索クエリに含めない
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
  │     - status: failed → タスクリトライ（最大3回）→ 人間にエスカレ（ゲート内リトライは別カウント）
  │     - status: blocked → ブロッカーを記録、代替タスクに着手
  │     - status: partial → artifacts を取り込み、残作業をタスク分割して工程表に追記→再配送
  │     ⚠️ フェーズ遷移時は Codex レビュー必須（使い分け）:
  │       - コード差分 → `codex review --uncommitted`
  │       - 設計書・仕様書 → `codex exec "レビュー"`
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
status: "completed"                 # completed | failed | blocked | partial | interrupted（IIP発動: 前提崩壊/範囲再定義）
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

### 途中完了報告（status: partial の場合）

```yaml
task_id: "T-002"
status: "partial"
artifacts:
  - "src/auth/login.ts"            # 完了分の成果物
remaining_tasks:
  - "リフレッシュトークン実装"
  - "ログアウトエンドポイント追加"
changes_summary: "ログイン認証を実装（リフレッシュ・ログアウトは未着手）"
decisions:
  - "JWT方式を採用"
```

**運用ルール:**
- partial は一時状態。Opus は remaining_tasks をタスク分割して工程表に追記し、元タスクを completed に更新する
- 前提条件判定: partial の artifacts は後続タスクから参照可能（completed 相当として扱う）
  - ただし参照した後続タスクには **partial-dependent** フラグを付与する
  - 参照元の remaining_tasks が全完了した時点で、partial-dependent タスクの再検証を工程表に挿入する
- 同一起点からの partial 分割は**通算3回上限**。超過時は PM が人間にエスカレーション
- 同一タスクが2回以上 partial → まずタスク粒度を見直し（分割）。分割後も partial 継続なら通算カウントで判定

## Opus の自作業禁止ルール

| 作業 | 委譲先 |
|------|--------|
| コード実装 | Codex 5.3 / Codex 5.3 Spark (codex exec) |
| レビュー・品質アップ | Codex 5.4 (codex review / codex exec) |
| 大規模コード精読 | Codex 5.2 (codex exec) |
| テスト作成 | Sonnet (Task tool) |
| ドキュメント作成 | Sonnet (Task tool) |
| 調査・検索 | Haiku 4.5 (Task tool) |
| コードレビュー | Codex 5.4 (codex review --uncommitted) |
| 設計・仕様レビュー | Codex 5.4 (codex exec "レビュー") |

**常時すべて委譲**。唯一の例外: MCP検証などツール動作確認のみ自分で実行可。

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

### リトライ階層（2層 + Progress Alert）

| 層 | 定義 | 上限 | 超過時 |
|---|---|---|---|
| **ゲート内リトライ** | 同一ゲート内の修正＋再判定（例: 実装.2 の codex review 3回） | 3回 | status: failed でゲートを出る → タスクリトライへ |
| **タスクリトライ** | status: failed のタスク再配送（Opus がプロンプト調整） | 3回 | 人間にエスカレーション |
| **Progress Alert** | 同一タスクの合計試行回数（ゲート内＋タスク通算） | 5回 | 人間に状況報告（verification §13 参照） |

```
タスクリトライ（status: failed）:
  1回目失敗 → プロンプトを調整してリトライ
  2回目失敗 → エラー内容を追加してリトライ
  3回目失敗 → 人間にエスカレーション

IIP 発動時（status: interrupted）:
  ★ リトライカウントに含めない（前提崩壊は実装ミスではない）
  → 影響度分類（P0〜P3）に従い差し戻し先を決定
  → 詳細は implementation-gate.md の IIP セクション参照

進捗停滞時:
  合計試行回数 5回以上 → 人間に状況報告と支援要請（Progress Alert）
  3回連続 failed または blocked → ブロッカー報告
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
  research_reports: []  # 事前調査レポート（該当時）

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
  research_reports: "事前調査レポート（該当時）"

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
      model: "Haiku 4.5 | Codex 5.3 | Codex 5.4 | Sonnet"
      skills: ["読み込むスキル"]
      tools_allowed: ["許可ツール"]
      prerequisites: ["前提タスクID"]
      reference_docs: ["参照ドキュメント"]
      verification_layer: "L2 | L2.5 | L3 | L4 | L5"

完了条件: 全タスクに difficulty + model + skills + reference_docs 付与済み
```

### 実装フェーズ

```
入力: L4 出力（schedule）+ 設計書群
出力: 上記「サブエージェント I/O 仕様」に従う（既存）
完了条件: 全タスクの status が completed
```

※ 実装フェーズ内部の段階ゲート（実装.1〜.5）は `implementation-gate.md` に分離して定義する。

### 検証フェーズ

```
入力: 実装コード + 設計書群
出力: verification SKILL.md §10 の検証レポートテンプレートに従う
完了条件: 全検証レイヤーで合格（不合格 → レイヤー内5ループ → エスカレ）
```

### L5: デプロイ

```yaml
入力:
  verified_code: "検証済みコード"
  verification_report: "検証レポート（V-L5 テスト検証 pass, V-L6 運用検証 pass）"
  deploy_strategy: "L2 設計書で決定した戦略（Blue/Green / Canary / Rolling）"
  rollback_plan: "deploy/SKILL.md §4 に基づくロールバック手順"

出力:
  deployment_result:
    environment: "staging | production"
    strategy: "blue-green | canary | rolling | recreate"
    version: "v1.x.x"
    status: "success | rolled-back"
    gates:
      l5_1_preparation:
        security_scan: "pass | fail"
        environment_config: "pass | fail"
        human_approval: "approved | not-required | rejected"
      l5_2_execution:
        staging_verification: "pass | fail"
        production_deploy: "pass | fail"
        health_check: "pass | fail"
      l5_3_stability:
        slo_compliance: "pass | fail | conditional-pass"
        degradation_level: "none | low | medium | high | critical"
        observation_window: "15min | 30min(canary)"
  rollback_events: []  # ロールバック発生時の記録
  performance_report:
    availability: "99.9%"
    p95_latency_ms: 150
    error_rate_percent: 0.1
    observation_period: "15min"

完了条件: L5.1〜L5.3 全ゲート pass + 劣化レベル none（low は条件付き pass）
```

※ L5 内部ゲート（L5.1〜L5.3）の詳細は `layer-interface.md §L5 内部ゲート` を参照。

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
