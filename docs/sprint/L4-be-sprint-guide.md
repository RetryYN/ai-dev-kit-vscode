# L4 BE スプリントガイド

> --drive be の場合に参照する BE 実装スプリント手順
> 一般定義: implementation-gate.md §ゲート概要 参照。本ガイドは BE 駆動固有の手順を補完する。

## スプリント手順（BE 駆動）

### .1a コード調査
- 既存 API エンドポイント棚卸し（ルーティング定義の一覧化）
- ビジネスロジック層の構造確認（Service / UseCase / Repository パターン）
- DB スキーマ確認（テーブル定義・リレーション・インデックス）
- 依存ライブラリ確認（ORM / バリデーション / 認証ミドルウェア）
- 既存テスト確認（テストカバレッジ・テストフレームワーク）
- `helix-codex --role tl --task "既存 API 構造の棚卸しレビュー"` で TL 確認

### .1b 変更計画
- L3 API 契約（D-API）との整合確認
- ER 図更新（テーブル追加/変更がある場合）
- API エンドポイント設計書の確認（パス・メソッド・リクエスト/レスポンス型）
- マイグレーション手順の策定（DDL + ロールバック SQL）
- `helix-codex --role tl --task "変更計画の設計レビュー"` で TL 承認

### .2 最小実装
- 実装順序: **DB マイグレーション → リポジトリ層 → サービス層 → API エンドポイント**
- DB マイグレーション作成・適用
  - `helix-codex --role dba --task "マイグレーション DDL 作成"` で DBA 委譲
- ビジネスロジック実装
  - `helix-codex --role se --task "サービス層実装（スコア4+）"` で上級実装
  - `helix-codex --role pg --task "CRUD 実装（スコア1-3）"` で通常実装
- API エンドポイント実装
  - `helix-codex --role pg --task "API エンドポイント実装"` で PG 委譲
- エラーハンドリング（統一エラーレスポンス形式）

### .3 安全性
- `helix-codex --role security --task "OWASP Top 10 チェック"` でセキュリティ監査
- 入力バリデーション確認（リクエストボディ・パスパラメータ・クエリパラメータ）
- 認証・認可の実装確認（JWT / セッション / RBAC）
- SQL インジェクション対策（パラメータバインディング）
- レート制限・CORS 設定の確認
- 秘密情報のハードコード検出（API キー・DB パスワード）

### .4 テスト
- テスト実装順序: **Unit → Integration → API テスト**
- Unit テスト: サービス層のビジネスロジック
  - `helix-codex --role qa --task "Unit テスト作成"` で QA 委譲
- Integration テスト: リポジトリ層 + DB 接続
  - `helix-codex --role qa --task "Integration テスト作成"` で QA 委譲
- API テスト: エンドポイントの E2E 確認
  - `helix-codex --role qa --task "API テスト作成"` で QA 委譲
- テストカバレッジ確認（目標: 80% 以上）

### .5 仕上げ
- `codex review --uncommitted` でコードレビュー
- API ドキュメント整合確認（OpenAPI / Swagger）
- D-API との差異チェック（契約 vs 実装）
- パフォーマンス確認（N+1 クエリ検出・スロークエリログ）
- G4 ゲート準備（実装凍結チェックリスト）

## Codex ロール委譲マップ

| ステップ | 委譲先ロール | helix-codex コマンド | 出力 |
|---------|------------|---------------------|------|
| .1a | tl | `helix-codex --role tl --task "API 構造棚卸し"` | 構造レポート |
| .1b | tl | `helix-codex --role tl --task "変更計画レビュー"` | 承認 / 差戻し |
| .2 | dba | `helix-codex --role dba --task "マイグレーション DDL"` | DDL + ロールバック SQL |
| .2 | se | `helix-codex --role se --task "サービス層実装"` | ビジネスロジック |
| .2 | pg | `helix-codex --role pg --task "CRUD + API 実装"` | エンドポイント + リポジトリ |
| .3 | security | `helix-codex --role security --task "OWASP チェック"` | 脆弱性レポート |
| .4 | qa | `helix-codex --role qa --task "テスト作成"` | テストスイート |
| .5 | tl | `helix-codex --role tl --task "G4 ゲート判定"` | Pass / Fail |

## BE 駆動の注意点

- FE が存在する場合でも、BE 側の API 完成を優先する
- API 契約（D-API）が凍結されていることを .2 開始前に必ず確認
- DB マイグレーションは必ずロールバック手順を用意する
- L5 は `--ui` フラグ有りのときのみ（表示確認は薄い）
