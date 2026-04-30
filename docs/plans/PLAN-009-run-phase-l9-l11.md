# PLAN-009: Run 工程（L9-L11）(v3)

## 1. 目的 / Why

`L8` は「受入完了（PO 受領）」で工程の最終点として扱われるが、実際の本番投入後の安定性担保、継続監視、運用学習までの接続が不足している。

`PLAN-009` は、`L8` の後段として `Run` 工程を `L9`〜`L11` に分解し、
- デプロイ検証を必須化し、
- 観測期間の運用責務を明文化し、
- 事後学習を次イテレーションに接続する

ことで、受入〜改善までを同一フレームに収めることを目的とする。

## 2. スコープ

### 2.1 含む

- `L9`: デプロイ検証 Phase の方針、入力/出力、ゲート（G9）
- `L10`: 観測 Phase の運用期間設計、観測 KPI、インシデント未然監視、ゲート（G10）
- `L11`: 運用学習 Phase の事後検証・改善提案フロー、ゲート（G11）
- `PLAN-004 / PLAN-005 / PLAN-007 / PLAN-008` への接続方針
- `SKILL_MAP.md` / `HELIX_CORE.md` への反映方針（この PLAN の作成時点では更新対象外）

### 2.2 含まない

- デプロイ自動化実装（PLAN-005 や L6/L7 実装領域の扱い）
- 監視基盤の具体的スクリプト/ダッシュボード実装
- インシデント対応手順の詳細運用（`workflow/postmortem` 側の実装計画）
- ロールバック実行仕様の実装化

## 3. 採用方針

### 3.1 L9 デプロイ検証

- **入力**: L8 受入完了成果物、デプロイ手順
- **実施内容**:
  - 本番投入直後 1〜4 時間以内のスモーク確認（主要 API / CRUD 主要フロー）
  - リリースノート / 予定変更点の実装一致チェック
  - Rollback 準備状態の最終確認（戻し手順・承認経路・実行可能性）
  - 監視開始確認（観測対象 metric の計測可否）
- **成果物**: `deployment-verification report`
- **ゲート**: `G9`（デプロイ安定性ゲート、Auto + PM）
- **参照**: `PLAN-005`（`workflow/deploy`）、`workflow/observability-sre`

### 3.2 L10 観測

- **入力**: L9 デプロイ検証完了、観測対象 metric 定義
- **実施内容**:
  - `1〜30日` を標準観測期間とし、日次で SLO/SLI、エラーレート、レイテンシ、ユーザー指標を確認
  - 異常シグナルの発生時は一時停止判定（必要なら L11 へ進ませず追加検証）
  - 観測結果を `observation report` と `異常検知ログ` に記録
- **成果物**: `observation report`, `anomaly log`
- **ゲート**: `G10`（観測完了ゲート、PM）
- **参照**: `workflow/observability-sre`, `PLAN-007` のデプロイ後 scrum 連携

### 3.3 L11 運用学習

- **入力**: L10 観測完了、incident ログ、retro ノート
- **実施内容**:
  - SLO 違反 / incident / サポート問い合わせ傾向の要約
  - `postmortem` と照合した再発防止提案の抽出
  - 次サイクルの `Sprint` 改善提案へ落とし込み（優先度付き）
  - `PLAN-004` の readiness / accuracy_score を更新可能にする記録整備
- **成果物**: `run-learning report`, `next-cycle improvement proposal`
- **ゲート**: `G11`（運用学習完了ゲート、PM）
- **参照**: `workflow/postmortem`, `PLAN-004`

### 3.4 ゲート設計（G9/G10/G11）

- **G9 判定要件**
  - スモークテストの pass 条件達成
  - リリースノートと実装差分の整合性確認完了
  - Rollback 準備チェック項目（最終確認）完了
  - 観測開始確認
- **G10 判定要件**
  - 観測計画どおりの指標記録率 90% 以上
  - 異常検知ログ欠測が 0 件
  - SLO 逸脱が `観測継続` / `保留` / `要是正` の定義内に収束
- **G11 判定要件**
  - incident の主要原因分類 + 再発防止提案が完了
  - 次サイクルへ持ち越す改善提案（最小 1 件）提出
  - 運用学習報告と受入記録の連携更新

### 3.5 既存 `SKILL_MAP.md` / `HELIX_CORE.md` への追加方針

本 PLAN は現在 2 層で反映を想定する。

- `SKILL_MAP.md`:
  - `Phase 3`（受入 `L8`）の末尾ではなく、`Phase 4` **Run** として `L9 → L10 → L11` の流れを新規追加する方針
  - ゲート一覧は **G9/G10/G11** を `L8` の後段に追加する方針
  - `フェーズスキップ決定木` に `S 案件` の `L4 のみ` 例外条件と `Run 工程の適用可否` を明記
- `HELIX_CORE.md`:
  - `3 フェーズ思想` の記述を `4 フェーズ思想` に拡張し、`Phase 4 Run` を明示する方針
  - `L8` の直後に `Run（L9-L11）` への移行を明示する運用注記を追加する方針
  - Run 工程として `L9 → L10 → L11` を明示し、`フェーズスキップ決定木` では Run 工程の適用可否判定のみを維持

### 3.6 CLI / state / gate 反映方針

- **CLI 反映**:
  - 本 Run 工程を `helix-gate` の実行対象へ拡張し、`G9 / G10 / G11` を追加する。
  - 追加ゲートは既存 `G2-G7` と同等の fail-close 設計（失敗時は前工程へ戻す/停止）で運用する。
  - ゲート実行コマンド例と判定フラグは PLAN v3 方針として提示し、実装仕様は L3 詳細設計で凍結する。

- **state 反映**:
  - `.helix/phase.yaml` の `current_phase` に `L9 / L10 / L11` を追加し、Run 工程の位相遷移を明示する。
  - Run の遷移規則として、`Run` 工程の開始・完了・例外停止時の遷移を `Run` エントリに追加する（`transition rules` 更新）。
  - これらのスキーマ詳細（`phase.yaml` の許容値、遷移条件、例外遷移）も本 PLAN では方針提示に留め、L3 詳細設計で実装契約を確定する。

- **gate 反映**:
  - `G9 / G10 / G11` の各ゲート判定条件を `gate-checks.yaml`（または同等の仕様ファイル）に登録する。
  - Run 各ゲート用の自動検証スクリプトを `scripts/` に追加し、`helix-gate` から参照可能な形で紐付ける。
  - ただし、CLI 引数仕様、`phase.yaml` スキーマ、`gate-checks.yaml` フォーマットの正確な契約は L3 詳細設計フェーズで凍結する。

- **観測/振り返り連携**:
  - `workflow/observability-sre` の観測 KPI / アラート契約との接続面を `Run` の成功条件に接続する。
  - `workflow/postmortem` の振り返り成果（再発防止提案）を L11 の `G11` 判定と `run-learning report` の提出条件に接続する。

> 本タスクは本文件の新規作成のみを実施し、他ファイルの実編集は行わない。

## 4. 関連 PLAN

- `docs/plans/PLAN-004-pm-reward-design.md`
  - readiness / accuracy_score の運用継続観点から、`L8` 以降を受入観点で受ける。
- `docs/plans/PLAN-005-ops-automation-skills.md`
  - `workflow/deploy` / observability 系の共通実装方針を L9/L10 の監査条件に接続。
- `docs/plans/PLAN-007-scrum-multitype-trigger.md`
  - デプロイ後 scrum の差し込み条件を L10/L11 の異常事例連携として接続。
- `docs/plans/PLAN-008-reverse-multitype.md`
  - フルバック Reverse の設計整合に、L11 の事後学習結果を反映するための受入境界を接続。

## 5. リスク

- 観測期間の長期化により、L10 が長引き Sprint 進行が停滞する。
- L11 が形骸化し、レトロログが定量化されず再発防止につながらない。
- ステークホルダー間で G10/G11 の完了条件が解釈違いを起こし、進行が滞る。

### 緩和策

- L10 は標準 7 日 + 追加 23 日の 2 段階進行とし、暫定の `watch done` 判定を明確化。
- L11 は `postmortem` + `run-learning report` の 2 成果物提出を必須化し、提出期限付きで運用。
- `G9/G10/G11` は本文の定義を `review` で固定し、判定責任者を PM 1 名に限定。

## 6. Sprint 計画概要（L1〜L4）

### Sprint L1: L9 設計固定

- デプロイ検証レポートの最小必須項目を定義
- G9 判定条件のレビュー承認
- `PLAN-005` / `PLAN-007` との接続点を確定

### Sprint L2: L10 観測計画固定

- 観測対象 KPI（SLO/SLI/latency/error/ユーザー指標）を一覧化
- 異常ログ記録フォーマットを標準化
- G10 の観測率 / 欠測ゼロ条件を固定

### Sprint L3: L11 学習ループ化

- `run-learning report` テンプレート雛形を設定
- `postmortem` / incident を受ける再学習ルールを確定
- 次サイクルへの改善提案ルートを L1 承認条件へ接続

### Sprint L4: 接続整備

- `SKILL_MAP.md` / `HELIX_CORE.md` / `docs/plans` 間の参照整合を確認
- PLAN シリーズ全体のリンク整合・改訂履歴更新ルールを整理

## 7. 改訂履歴

| 日付 | バージョン | 変更内容 | 変更者 |
| --- | --- | --- | --- |
| 2026-04-30 | v1 | PLAN-009 新規ドラフト作成。Run 工程（L9-L11）を導入し、L8 後のデプロイ検証、観測、運用学習を統合。 | Docs (Codex) |
| 2026-04-30 | v2 | P1 finding 対応。`SKILL_MAP.md` は `Phase 4 Run` として `L9→L10→L11` を新規追加し、`HELIX_CORE.md` は `4 フェーズ思想` 拡張へ反映する方針へ修正。 | Docs (Codex) |
| 2026-04-30 | v3 | TL P1 finding 反映。§3.6（CLI/state/gate 反映方針）を新設し、`helix-gate G9/G10/G11` / `.helix/phase.yaml` / `gate-checks.yaml` 反映と自動検証スクリプト接続方針を明示。実装契約（CLI 引数仕様、phase schema、gate フォーマット）は本PLAN の L3 詳細設計で凍結。 | Docs (Codex) |
