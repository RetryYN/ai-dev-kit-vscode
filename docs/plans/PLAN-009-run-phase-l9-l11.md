# PLAN-009: Run 工程（L9-L11）(v3.3)

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

#### 3.1.1 L7 / G7 / L8 / L9 の責務境界 (P2 解消)

Run 工程追加に伴い、deploy 前後の責務を以下のように固定する。L9 は既存 G7 の再実行ではなく **L8 受入後の longer-run verification** として設計する。

| フェーズ/ゲート | 担当範囲 | 時間軸 | 主要判定 |
|---|---|---|---|
| `L7` | デプロイ準備・本番投入実行・即時スモーク | デプロイ前〜直後 (~30分) | デプロイ手順の安全実行、初動異常の検出 |
| `G7` | **release go/no-go**（即時スモーク + rollback 判断） | デプロイ直後 (~30分以内) | 即時 SLO 維持・blocking 障害なし |
| `L8` | PO 受入 / 受入条件 ↔ 成果物突合 | L7 通過後〜数時間 | PO 受領、受入条件の充足 |
| `L9` | **post-acceptance run verification**（longer-run、本番運用直後 1-4h） | L8 通過後 1-4h | 主要 API / CRUD の継続健全性、リリースノート整合、監視開始確認 |

`G7` の即時スモーク（リクエスト数件規模）と `L9` の longer-run verification（時間軸を持つ運用観測） は重複しない。`G7` で blocking 障害を捕捉できず L9 で発見した場合は、L7/G7 へ差戻し + scrum (post-deploy) を起票する。

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

### 3.3a Run 成果物の redaction / retention / 閲覧権限 (P2 解消)

L10 (`observation report` / `anomaly log`) と L11 (`run-learning report` / `next-cycle improvement proposal`) はユーザー指標・incident ログ・サポート問い合わせ傾向を扱うため、PII / secret / runtime log raw が混入するリスクがある。`workflow/observability-sre` (PLAN-005) の redaction 方針を継承し、以下を必須化する。

#### 保存禁止情報

`auth credentials` / `PII` (個人識別情報・問い合わせ本文の氏名/連絡先など) / `runtime log raw` / `env vars` / `内部エンドポイント url の secret 部分` を保存しない。

#### redaction 必須項目

PLAN-007 §3.5.2 / PLAN-008 §3.6 と同等の redaction 手順を適用する。

| 成果物 | redaction 対象フィールド |
|---|---|
| `observation report` | metric source path / dashboard query 内の token / customer identifier |
| `anomaly log` | trace 詳細の secret / user PII / 内部 IP+port の機密部分 |
| `run-learning report` | incident summary 内の顧客名 / サポート問い合わせ本文 / 流出 secret |
| `next-cycle improvement proposal` | 提案根拠 evidence の PII / secret 引用 |

#### retention

- `observation report`: 365 日（年次レビュー対応）
- `anomaly log`: 730 日（incident timeline 追跡用）
- `run-learning report`: 永続保存（archive 可、redaction 済み）
- `next-cycle improvement proposal`: 次サイクル完了まで（最低 90 日）

retention 経過後は `archived` 化 → `cli/helix-scheduler` の月次ジョブ `audit-retention: run-phase` で削除。

#### 閲覧権限

PLAN-008 §3.6 と同等に、**HELIX 内部には raw を保持しない**。各ロールの閲覧範囲は以下:

- PM: 全 redaction 済みデータ閲覧 + 外部 source への `raw proxy 参照` 許可（72h TTL audit token、`audit.evidence_view` 監査ログ記録必須）
- TL: redaction 済み + `archived` 以外を閲覧可。raw proxy 参照は `incident 対応中` のみ許可（PM 承認必須）
- SE / PG: redaction 済みのみ閲覧可。raw proxy 参照不可
- 外部利害関係者 (PO 等): redaction 済み `run-learning report` のみ参照可

#### raw 取り扱いの確定 (P2 解消)

「raw 参照」とは **HELIX 外部 source (本番ログ基盤 / Sentry / Datadog 等) への監査付き一時参照** を意味し、HELIX 内部 (helix.db / `.helix/audit/` / `observation report` / `anomaly log` など) には raw を保存しない。

- HELIX 内に保存可: `evidence_id` / `source_path` (外部 source URI) / `source_query` (sanitized) / `content_hash` / `redacted_summary` / `secret_patterns_hit_count`
- HELIX 内に保存禁止: 候補本文の raw text / auth credentials raw / PII 平文 / runtime log raw / env vars 平文
- raw proxy 参照時は `audit.evidence_view` を発行し、72h TTL audit token を発行。TTL 経過後は token 無効化 (`audit.evidence_token_revoked`)。
- export は redacted 済みデータ限定。raw export は禁止。外部送信は PM 承認 + 暗号化必須。

### 3.4 ゲート設計（G9/G10/G11）

- **G9 判定要件**
  - スモークテストの pass 条件達成
  - リリースノートと実装差分の整合性確認完了
  - Rollback 準備チェック項目（最終確認）完了
  - 観測開始確認
- **G10 判定要件**
  - 観測計画どおりの指標記録率 90% 以上
  - 異常検知ログ欠測が 0 件
  - SLO 逸脱が §3.4.1 G10 outcome mapping に収束し、**`pass` の場合のみ G10 完了**として L11 遷移可
  - `watch-continue` は **L10 観測延長として再 G10 必須**（G10 完了扱いではない、§3.4.1 参照）
  - `blocked` / `failed` は次工程（L11）に進めず、是正/差戻しに接続
- **G11 判定要件**
  - incident の主要原因分類 + 再発防止提案が完了
  - 次サイクルへ持ち越す改善提案（最小 1 件）提出
  - 運用学習報告と受入記録の連携更新

#### 3.4.1 G10 outcome mapping (P2 解消)

`要是正` を pass/blocked/failed のどれと扱うか曖昧だったため、以下の outcome に分離する。fail-close 方針として **未解決の是正事項を pass させない**。

| outcome | gate_status | L11 遷移 | 説明 / 次工程 | 是正 owner・ETA |
|---|---|---|---|---|
| `pass` | `pass` (G10 完了) | **可** | SLO 逸脱なし or 是正完了 + 指標記録率 ≥ 90% + 異常欠測 0 件。L11 へ進行 | — |
| `watch-continue` | `non-passing continuation` (G10 **未完了**) | **不可** | 軽微な逸脱 (P3 相当) + SLO 範囲内、観測延長で継続可。L10 観測延長 (最大 +30 日) → 再 G10 必須 | TL (観測継続)、ETA 30 日以内 |
| `blocked` | `blocked` (G10 未完了) | **不可** | 中度の逸脱 (P2 相当) + 是正計画あり、本番運用は継続。L10 中断 → 是正 → 再 G10 | PM 指名、ETA 14 日以内 |
| `failed` | `failed` (G10 fail-close) | **不可** | 重大な SLO 違反 (P1 相当) or incident 継続中。**L6/L7 差戻し** + post-deploy scrum 起票 (PLAN-007 §3.1.5) + incident 起票 (`workflow/incident`) | PM、ETA は incident 解消ベース |

`要是正` は単独 outcome ではなく、`blocked` または `failed` のサブカテゴリとして扱い、必ず是正 owner と ETA を付与する。`watch-continue` で 30 日延長後も収束しない場合は `blocked` に格上げする。

**L11 遷移は `pass` のみ可** (P2 解消)。`watch-continue` を G10 pass として L11 へ進める実装は禁止し、phase transition rules で fail-close する。`watch-continue` は **non-passing continuation** であり、観測延長中は G10 状態が継続するが完了扱いにはならない。

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

- L10 は標準 7 日 + 追加 23 日の 2 段階進行とし、暫定の `watch-continue` 判定 (§3.4.1) で観測延長を明示化。
- L11 は `postmortem` + `run-learning report` の 2 成果物提出を必須化し、提出期限付きで運用。
- `G9/G10/G11` は本文の定義を `review` で固定し、判定責任者を PM 1 名に限定。

## 6. Sprint 計画概要（Run Sprint 1〜4）

> v3 改訂で `Sprint L1〜L4` を `Run Sprint 1〜4` に改名。HELIX 本体の L1〜L4 フェーズ名と衝突しないようにラベル分離 (P3 解消)。

### Run Sprint 1: L9 設計固定

- デプロイ検証レポートの最小必須項目を定義
- G9 判定条件のレビュー承認
- `PLAN-005` / `PLAN-007` との接続点を確定

### Run Sprint 2: L10 観測計画固定

- 観測対象 KPI（SLO/SLI/latency/error/ユーザー指標）を一覧化
- 異常ログ記録フォーマットを標準化
- G10 の観測率 / 欠測ゼロ条件と outcome mapping (§3.4.1) を固定

### Run Sprint 3: L11 学習ループ化

- `run-learning report` テンプレート雛形を設定
- `postmortem` / incident を受ける再学習ルールを確定
- 次サイクルへの改善提案ルートを HELIX L1 承認条件へ接続

### Run Sprint 4: 接続整備

- `SKILL_MAP.md` / `HELIX_CORE.md` / `docs/plans` 間の参照整合を確認
- PLAN シリーズ全体のリンク整合・改訂履歴更新ルールを整理

## 7. 改訂履歴

| 日付 | バージョン | 変更内容 | 変更者 |
| --- | --- | --- | --- |
| 2026-04-30 | v1 | PLAN-009 新規ドラフト作成。Run 工程（L9-L11）を導入し、L8 後のデプロイ検証、観測、運用学習を統合。 | Docs (Codex) |
| 2026-04-30 | v2 | P1 finding 対応。`SKILL_MAP.md` は `Phase 4 Run` として `L9→L10→L11` を新規追加し、`HELIX_CORE.md` は `4 フェーズ思想` 拡張へ反映する方針へ修正。 | Docs (Codex) |
| 2026-04-30 | v3 | TL P1 finding 反映。§3.6（CLI/state/gate 反映方針）を新設し、`helix-gate G9/G10/G11` / `.helix/phase.yaml` / `gate-checks.yaml` 反映と自動検証スクリプト接続方針を明示。実装契約（CLI 引数仕様、phase schema、gate フォーマット）は本PLAN の L3 詳細設計で凍結。 | Docs (Codex) |
| 2026-05-02 | v3.1 | TL v3 review finding 解消。P2-1: §3.4.1 G10 outcome mapping (`pass/watch-continue/blocked/failed`) を新設、`要是正` を blocked/failed のサブカテゴリに固定 (是正 owner/ETA 必須)。P2-2: §3.1.1 で L7/G7/L8/L9 責務境界表を追加、`G7=即時 release go/no-go`・`L9=longer-run post-acceptance verification` に分離。P2-3: §3.3a で Run 成果物 (observation report / anomaly log / run-learning report / next-cycle improvement proposal) の保存禁止情報・redaction 必須項目・retention (365/730 日 + 永続) ・閲覧権限 (PM/TL/SE/外部) を明文化、PLAN-007 §3.5.2 / PLAN-008 §3.6 と統一。P3: §6 Sprint L1〜L4 を `Run Sprint 1〜4` に改名し HELIX 本体 L1〜L4 とのラベル衝突を解消。 | PM (Opus) |
| 2026-05-02 | v3.2 | TL v3.1 review finding 解消。P2-1: §3.4.1 outcome mapping に `gate_status` 列と「L11 遷移は `pass` のみ可」明文を追加。`watch-continue` を **non-passing continuation** として定義し L11 遷移不可を fail-close。P2-2: §3.3a に raw 取り扱いの確定章を追加、PLAN-008 §3.6 と整合 (HELIX 内部に raw 非保存、外部 source への 72h TTL audit token 経由 raw proxy 参照のみ、保存可/禁止フィールド明示)。P3: §5 緩和策の `watch done` を `watch-continue` (§3.4.1) に語彙統一。 | PM (Opus) |
| 2026-05-02 | v3.3 | TL v3.2 review finding 解消。P2: §3.4 G10 判定要件文言を `pass` のみ完了 / `watch-continue` は再 G10 必須と明記し §3.4.1 と整合させる。P3: §3.4.1 outcome mapping の 2 段表 (`gate_status / L11 遷移 / 説明` と `次工程 / 是正 owner / ETA`) を 1 つの表 (`outcome / gate_status / L11 遷移 / 説明 / 次工程 / 是正 owner・ETA`) に統合。 | PM (Opus) |
