# サブエージェント構成設定
> 目的: サブエージェント構成設定 の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

> 出典: docs/archive/v-model-reference-cycle-v2.md §サブエージェント構成設定

## スキル付与テーブル

タスク種別に応じて、サブエージェントに事前読み込みするスキルを指定。

| タスク種別 | 推奨スキル | 説明 |
|-----------|-----------|------|
| 認証・セキュリティ | security, api | セキュリティベストプラクティス |
| API実装 | api, error-fix | RESTful設計、エラーハンドリング |
| UI実装 | ui, design | UI設計パターン |
| ビジュアルデザイン適用 | visual-design, ui, design | 配色・余白・タイポグラフィ・構図の適用（L5） |
| DB操作 | db, performance | スキーマ設計、クエリ最適化 |
| テスト | testing, quality-lv5 | テスト設計 |
| 検証 | verification, code-review | 検証ロジック、レビュー観点 |
| 事前調査 | ai-coding §7 | 設計・実装前の先行事例調査（Haiku 4.5 固定） |

## ツール制限テーブル

| タスク種別 | 許可ツール | 禁止ツール |
|-----------|-----------|-----------|
| 読み取り専用 | Read, Grep, Glob | Edit, Write, Bash |
| 検証 | Read, Grep, Glob, Bash | Edit, Write |
| 実装 | 全ツール | なし |
| UI実装 | Read, Edit, Write, Grep, Glob, Bash | なし（Bash はテスト実行・dev server 起動に必要） |

原則: **最小権限** — 必要最小限のツールのみ許可。

## 思考トークン設定（Claude サブエージェント用）

Task tool 経由の Claude サブエージェント（Sonnet / Haiku）に適用する。

| 難易度スコア | 設定 | 対象タスク |
|-------------|------|-----------|
| 0-3点 | なし(-) | 軽量タスク |
| 4-7点 | low | 標準タスク |
| 8-10点 | medium | 複雑タスク |
| 11-14点 | high | 最高難度タスク |

> **Codex 系モデルとの関係**: Codex 系（5.4/5.3/5.3 Spark/5.2）は `codex exec` 経由で実行し、`model_reasoning_effort = "xhigh"` 固定（CLAUDE.md 参照）。上記の難易度別設定は適用しない。
> モデル割当の正本は `workflow-core.md §モデル割当テーブル`。

## スキル自動推論ルール

タスク記述から必要スキルを推論するキーワードマッピング:

| キーワード | 推論スキル |
|-----------|-----------|
| 認証, auth, login, JWT, OAuth | security |
| API, endpoint, REST, GraphQL | api |
| UI, コンポーネント, component | ui, design |
| デザイン, 配色, 余白, フォント, 構図, SNS画像 | visual-design |
| DB, データベース, SQL, クエリ | db |
| テスト, test, spec | testing |
| 検証, verify, validation | verification |
| エラー, error, 例外 | error-fix |
| 調査, research, 事前調査, 先行事例 | ai-coding §7 |

推論精度が低い場合(キーワード一致のみ)、設計書の該当セクションから追加推論を行う。

### 事前調査タスクの自動付与条件

G1R / G3 / 実装.1 ゲート時に、`ai-coding/SKILL.md §7` の強制条件（単一ソース）に基づき「事前調査」タスクを自動付与する。
MUST 条件該当 → Haiku 4.5 に自動付与。SHOULD → PM 判断。不要 → 付与しない。

---

## タスク種別の判定

タスクを受領したら、以下の種別に分類する。SKILL_MAP.md のサイジング(S/M/L)と組み合わせて、読み込むスキルを決定する。

| 種別 | 判定条件 | 例 |
|------|---------|-----|
| feature | 新機能追加 | ユーザー登録、ダッシュボード |
| bugfix | 既存機能の修正 | ログインエラー修正 |
| refactor | 構造改善(動作変更なし) | モジュール分割、命名変更 |
| infra | インフラ・環境変更 | CI/CD、環境変数 |
| docs | ドキュメント変更 | README更新、API仕様書 |
| security | セキュリティ関連 | 認証変更、脆弱性対応 |
| research | 事前調査（ai-coding §7 の強制条件該当時に自動付与） | 外部API調査、ライブラリ選定調査 |

## 種別×フェーズのスキルマトリクス

各フェーズで読み込むスキルを種別ごとに定義。`-` はそのフェーズをスキップ。

| 種別 | L1 | L2 | L3(API) | 実装 | L5 | L6 |
|------|----|----|---------|------|----|----|
| feature | requirements-handover, estimation | design-doc, api, db, visual-design（方針） | api-contract | coding + ドメインスキル | visual-design（UI変更時） | verification, testing |
| bugfix | - | error-fix | - | error-fix, coding | -（UI変更時のみ） | testing |
| refactor | - | refactoring, design-doc | - | refactoring, coding | - | testing, code-review |
| infra | - | infrastructure | - | infrastructure, dev-setup | - | deploy |
| docs | - | documentation | - | documentation | - | - |
| security | requirements-handover | security, api | api-contract | security, coding | - | verification, testing |
| research | - | - | - | - | - | - |

## ドメインスキル解決

feature 種別の「ドメインスキル」を、タスク記述のキーワードから特定する。
上記 §スキル自動推論ルール のキーワードに加え、以下を適用。

| キーワード | 追加スキル |
|-----------|-----------|
| 画面, UI, フォーム, コンポーネント | ui, design |
| 外部連携, webhook, OAuth, SSO | external-api |
| 多言語, i18n, ローカライズ | i18n |
| 移行, migration, データ移行 | migration |
| レガシー, 古いコード, 技術的負債 | legacy |
| AI, LLM, プロンプト, 生成AI | ai-integration |
| 監視, メトリクス, ログ, アラート | observability-sre |
| デプロイ, CI/CD, リリース | deploy |
| パフォーマンス, 高速化, N+1 | performance |
