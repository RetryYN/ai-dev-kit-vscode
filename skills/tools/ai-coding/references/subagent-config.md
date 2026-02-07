# サブエージェント構成設定

> 出典: v-model-reference-cycle-v2.md §サブエージェント構成設定

## スキル付与テーブル

タスク種別に応じて、サブエージェントに事前読み込みするスキルを指定。

| タスク種別 | 推奨スキル | 説明 |
|-----------|-----------|------|
| 認証・セキュリティ | security, api | セキュリティベストプラクティス |
| API実装 | api, error-fix | RESTful設計、エラーハンドリング |
| UI実装 | ui, design | UI設計パターン |
| DB操作 | db, performance | スキーマ設計、クエリ最適化 |
| テスト | testing, quality-lv5 | テスト設計 |
| 検証 | verification, code-review | 検証ロジック、レビュー観点 |

## ツール制限テーブル

| タスク種別 | 許可ツール | 禁止ツール |
|-----------|-----------|-----------|
| 読み取り専用 | Read, Grep, Glob | Edit, Write, Bash |
| 検証 | Read, Grep, Glob, Bash | Edit, Write |
| 実装 | 全ツール | なし |
| UI実装 | Read, Edit, Write, Grep, Glob | Bash |

原則: **最小権限** — 必要最小限のツールのみ許可。

## 思考トークン設定

| 難易度スコア | 設定 | 対象タスク |
|-------------|------|-----------|
| 0-3点 | なし(-) | 軽量タスク |
| 4-6点 | low | 標準タスク |
| 7-9点 | medium | 複雑タスク |
| 10点以上 | high | 最高難度タスク |

## スキル自動推論ルール

タスク記述から必要スキルを推論するキーワードマッピング:

| キーワード | 推論スキル |
|-----------|-----------|
| 認証, auth, login, JWT, OAuth | security |
| API, endpoint, REST, GraphQL | api |
| UI, コンポーネント, component | ui, design |
| DB, データベース, SQL, クエリ | db |
| テスト, test, spec | testing |
| 検証, verify, validation | verification |
| エラー, error, 例外 | error-fix |

推論精度が低い場合（キーワード一致のみ）、設計書の該当セクションから追加推論を行う。
