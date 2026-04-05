# L4 Fullstack スプリントガイド

> --drive fullstack の場合に参照する Fullstack 実装スプリント手順
> Phase A（BE Sprint // FE Sprint 並行）→ Phase B（L4.5 結合）の2段構成

## Phase A: BE Sprint // FE Sprint（並行実行）

Phase A では BE Track と FE Track を**並行実行**する。
API 契約（D-API / D-CONTRACT）が凍結済みであることが前提。

---

### BE Track（L4-be-sprint-guide 準拠）

#### BE .1a コード調査
- 既存 API エンドポイント棚卸し
- DB スキーマ確認
- `helix-codex --role tl --task "BE 側 API 構造の棚卸し"` で TL 確認

#### BE .1b 変更計画
- D-API / D-CONTRACT との整合確認
- ER 図更新・マイグレーション手順策定
- `helix-codex --role tl --task "BE 変更計画レビュー"` で TL 承認

#### BE .2 最小実装
- DB マイグレーション → リポジトリ層 → サービス層 → API エンドポイント
- `helix-codex --role dba --task "マイグレーション DDL 作成"` で DBA 委譲
- `helix-codex --role se --task "サービス層実装"` / `helix-codex --role pg --task "CRUD + API 実装"` で実装委譲

#### BE .3 安全性
- `helix-codex --role security --task "BE OWASP チェック"` でセキュリティ監査
- 入力バリデーション・認証認可・SQL インジェクション対策

#### BE .4 テスト
- Unit → Integration → API テスト
- `helix-codex --role qa --task "BE テスト作成"` で QA 委譲

---

### FE Track（L4-fe-sprint-guide 準拠）

#### FE .1a コード調査
- 既存コンポーネント棚卸し
- デザインシステム互換性確認
- 依存ライブラリ確認

#### FE .1b 変更計画
- コンポーネントツリー設計（Atomic Design レベル割当）
- Props 設計（型定義・デフォルト値・バリアント）
- D-UI / D-STATE との整合確認

#### FE .2 最小実装
- Atom → Molecule → Organism の順で実装
- **MSW（Mock Service Worker）で API モックを使用**（BE 完成前でも開発可能）
- `helix-codex --role pg --task "コンポーネント実装"` で PG 委譲
- Storybook story 同時作成

#### FE .3 安全性
- アクセシビリティ監査（WCAG AA 準拠）
- レスポンシブ確認（mobile / tablet / desktop）
- XSS 対策（ユーザー入力のサニタイズ）

#### FE .4 テスト
- コンポーネントテスト（Testing Library）
- Storybook ビジュアルリグレッション
- `helix-codex --role qa --task "FE テスト作成"` で QA 委譲

---

### Contract CI（Phase A 期間中に定期実行）

- API 契約テスト（D-CONTRACT / D-API に基づくスキーマバリデーション）
- BE が公開した API と FE が期待する API の整合性を自動検証
- `helix-codex --role qa --task "API 契約テスト実行"` で QA 委譲
- 不整合検出時は **即座に BE/FE 両チームに通知** → D-CONTRACT 更新を協議

---

## Phase B: L4.5 結合

Phase A の BE .4 / FE .4 が完了した後に実施。

### B.1 FE → BE API 繋ぎ込み
- MSW モック → 実 API への切替
- API レスポンス形式の差異チェック（型・null 許容・ページネーション）
- エラーレスポンスのハンドリング確認（4xx / 5xx）
- `helix-codex --role pg --task "MSW → 実 API 切替"` で PG 委譲

### B.2 E2E テスト
- ユーザーシナリオベースの E2E テスト（Playwright）
  - `helix-codex --role qa --task "E2E テスト作成"` で QA 委譲
- 認証フロー → CRUD 操作 → エラーケースの一気通貫テスト
- パフォーマンス確認（API レスポンスタイム + FE レンダリング）

### B.3 結合レビュー
- `codex review --uncommitted` でコードレビュー
- BE/FE 間のデータフロー総点検
- `helix-codex --role tl --task "Fullstack 結合レビュー"` で TL 承認
- D-API / D-CONTRACT / D-UI / D-STATE との最終整合チェック
- G4 ゲート準備（実装凍結チェックリスト）

## Codex ロール委譲マップ

| フェーズ | ステップ | 委譲先ロール | helix-codex コマンド | 出力 |
|---------|---------|------------|---------------------|------|
| A-BE | .1a/.1b | tl | `helix-codex --role tl --task "BE 設計レビュー"` | 承認 / 差戻し |
| A-BE | .2 | dba | `helix-codex --role dba --task "マイグレーション DDL"` | DDL + ロールバック |
| A-BE | .2 | se/pg | `helix-codex --role se --task "サービス層実装"` | ビジネスロジック |
| A-BE | .3 | security | `helix-codex --role security --task "BE OWASP チェック"` | 脆弱性レポート |
| A-BE | .4 | qa | `helix-codex --role qa --task "BE テスト作成"` | テストスイート |
| A-FE | .2 | pg | `helix-codex --role pg --task "コンポーネント実装"` | .tsx + スタイル |
| A-FE | .4 | qa | `helix-codex --role qa --task "FE テスト作成"` | テストスイート |
| A-CI | 常時 | qa | `helix-codex --role qa --task "API 契約テスト"` | 整合性レポート |
| B | .1 | pg | `helix-codex --role pg --task "MSW → 実 API 切替"` | 繋ぎ込みコード |
| B | .2 | qa | `helix-codex --role qa --task "E2E テスト"` | E2E テストスイート |
| B | .3 | tl | `helix-codex --role tl --task "結合レビュー + G4 判定"` | Pass / Fail |

## Fullstack 駆動の注意点

- Phase A の BE / FE は**並行実行**が前提。直列にしない
- API 契約（D-API / D-CONTRACT）は G3 で凍結済みであること
- FE は MSW を使って BE 完成を待たずに開発を進める
- Contract CI で不整合が見つかったら Phase A 中に即修正
- Phase B は BE .4 / FE .4 の両方が完了してから開始
- L5 は常に必要（結合後の Visual Refinement が Fullstack 駆動の仕上げ）
