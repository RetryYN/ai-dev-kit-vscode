# L4 DB スプリントガイド

> --drive db の場合に参照する DB 実装スプリント手順

## スプリント手順（DB 駆動）

### .1a 既存スキーマ調査
- テーブル定義一覧の取得（カラム名・型・制約）
- インデックス一覧の確認（主キー・ユニーク・複合インデックス）
- 外部キー制約の確認（FK リレーション図の作成）
- データ量の把握（行数・テーブルサイズ・成長率）
- 既存マイグレーション履歴の確認
- `helix-codex --role dba --task "既存スキーマ分析"` で DBA 調査

### .1b マイグレーション計画
- DDL 変更一覧の策定（CREATE / ALTER / DROP）
- ロールバック手順の策定（各ステップの逆操作 DDL）
- データマイグレーション計画（既存データの変換・移行）
- ダウンタイム影響の評価（オンラインスキーマ変更の可否）
- `helix-codex --role dba --task "マイグレーション計画レビュー"` で DBA 承認
- `helix-codex --role tl --task "マイグレーション計画の設計レビュー"` で TL 承認

### .2 スキーマ実装
- 実装順序: **マイグレーション実行 → リポジトリ層 → CRUD API → シードデータ**
- マイグレーション DDL 作成・適用
  - `helix-codex --role dba --task "マイグレーション DDL 実装"` で DBA 委譲
- CRUD API 実装（リポジトリパターン）
  - `helix-codex --role pg --task "CRUD リポジトリ + API 実装"` で PG 委譲
- シードデータ作成（開発用・テスト用・マスターデータ）
  - `helix-codex --role pg --task "シードデータ作成"` で PG 委譲
- ORM モデル定義の更新

### .3 安全性
- FK 制約の整合性確認（孤立レコード・カスケード設定）
- インデックス設計の最適化
  - `helix-codex --role dba --task "インデックス最適化レビュー"` で DBA 確認
- N+1 クエリ検出（ORM のクエリログ分析）
  - `helix-codex --role perf --task "N+1 クエリ検出"` で性能確認
- デッドロック リスク評価（トランザクション分離レベル確認）
- 個人情報カラムの暗号化/マスキング確認
  - `helix-codex --role security --task "DB セキュリティ監査"` でセキュリティ確認

### .4 テスト
- テスト実装順序: **マイグレーション往復 → データ整合性 → パフォーマンス**
- マイグレーション往復テスト（up → down → up が冪等に動作）
  - `helix-codex --role qa --task "マイグレーション往復テスト"` で QA 委譲
- データ整合性テスト（FK 制約・ユニーク制約・NOT NULL）
  - `helix-codex --role qa --task "データ整合性テスト"` で QA 委譲
- パフォーマンステスト（スロークエリ検出・EXPLAIN ANALYZE）
  - `helix-codex --role perf --task "クエリパフォーマンス計測"` で性能確認
- 大量データでの負荷テスト（シードデータ 10,000 件以上）
- バックアップ・リストア手順の確認

### .5 仕上げ
- `codex review --uncommitted` でコードレビュー
- ER 図の更新（最終スキーマを反映）
- マイグレーション手順書の整備（本番適用手順 + ロールバック手順）
- D-DB ドキュメントとの整合確認
- G4 ゲート準備（実装凍結チェックリスト）

## Codex ロール委譲マップ

| ステップ | 委譲先ロール | helix-codex コマンド | 出力 |
|---------|------------|---------------------|------|
| .1a | dba | `helix-codex --role dba --task "既存スキーマ分析"` | スキーマレポート |
| .1b | dba | `helix-codex --role dba --task "マイグレーション計画"` | DDL + ロールバック SQL |
| .1b | tl | `helix-codex --role tl --task "マイグレーション設計レビュー"` | 承認 / 差戻し |
| .2 | dba | `helix-codex --role dba --task "DDL 実装"` | マイグレーションファイル |
| .2 | pg | `helix-codex --role pg --task "CRUD + API 実装"` | リポジトリ + エンドポイント |
| .3 | dba | `helix-codex --role dba --task "インデックス最適化"` | インデックス推奨 |
| .3 | security | `helix-codex --role security --task "DB セキュリティ監査"` | 脆弱性レポート |
| .3 | perf | `helix-codex --role perf --task "N+1 検出"` | クエリ改善リスト |
| .4 | qa | `helix-codex --role qa --task "DB テスト作成"` | テストスイート |
| .5 | tl | `helix-codex --role tl --task "G4 ゲート判定"` | Pass / Fail |

## DB 駆動の注意点

- スキーマ変更は必ずマイグレーションファイルで管理（手動 DDL 禁止）
- ロールバック手順のないマイグレーションは .2 に進めない
- 本番データに影響する変更は人間にエスカレーション必須
- L5 は `--ui` フラグ有りのときのみ（管理画面確認は薄い）
