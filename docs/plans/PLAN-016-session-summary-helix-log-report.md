# PLAN-016: session-summary の md 廃止 — Stop hook を helix log report session 化

## §1. 目的 / position

PLAN-014/015 で整理された session-summary の持続的ノイズ対策を次段に進め、`Stop` hook 出力を `.helix/session-summaries/*.md` の更新に依存しない運用へ収束する。

本 PLAN は、`Stop` hook での停止を維持しつつ、セッション集計を `helix log report session` 起点へ統合する実装方針を、PLAN-014/15 と整合する粒度で確定する。

PM 決定を反映した前提:
- `helix log report session --date` は既定 `today`。
- Stop hook 配線は維持しつつ、`cli/helix-session-summary` は DB INSERT のみのシム化。
- 既存 `.helix/session-summaries/*.md` は残置し、新規生成のみ停止する（案 B）。

本 PLAN は設計+実装の一本化で記述し、実行は `PLAN-016` finalize 後に PG に委譲する。

## §2. スコープ

### §2.1 in-scope

- 実装前調査結果（現行仕様）に基づく現状整理（停止条件・DB 集計・hook 配線・参照箇所）
- `cli/helix-log` での `report session` 追加仕様の確定
- `cli/lib/helix_db.py` の session 集計拡張仕様の確定
- `cli/helix-session-summary` を DB INSERT only シムへ変更する方針確定（stdout/stderr 無出力）
- migration 方式の確定（案 B 採用、A/C は将来候補）
- 実装 Sprint と DoD、回帰観点を含む `helix-plan draft --file` 扱いの PLAN 本文整備
- `CLI` 関連資料（README/ADRs/skill/plan）への参照更新と、`retro` 起草対象の明示

### §2.2 out-of-scope

- 本 PLAN 文書（draft 段階）の起草作業時点では実コード改修・テスト実行・`helix-plan draft` 登録を伴わない（PLAN finalize 後に Sprint .2/.3/.4 で PG/Opus が実施）
- 本番環境 Hook 自動反映手順の運用整備（環境別 rollout）
- `PLAN-014/015` 以外の機能（予算報告、別コマンド再設計など）の再設計

## §3. 要件 / 設計

### §3.1 現状調査結果（実 read ベース）

#### A. `cli/helix-session-summary`

- 現在、`HELIX_DB_PATH` を使って `cost_log` へ INSERT。
- 続けて Python で当日分 (`hook_events` / `gate_runs` / `cost_log`) を集計し、`$HELIX_SESSION_SUMMARY_DIR/<TODAY>-session.md` を生成。
- `flock` + atomic rewrite で同日セクションを上書きし、既存ファイルとの同時互換を担保。
- 現行実装は Stop hook 側出力（`Generating session summary...`）は設定上存在。

#### B. `cli/helix-log`

- 現在 `summary|tasks|actions|feedback|quality|selections` のみ。
- `session` が未実装。

#### C. `cli/lib/helix_db.py`

- `cost_log` / `hook_events` / `gate_runs` は参照済みテーブル。
- `report(db_path, report_type)` は固定分岐。
- `CURRENT_SCHEMA_VERSION = 15`。

#### D. Stop hook 配線

- `.claude/settings.json` の Stop hook は `~/ai-dev-kit-vscode/cli/helix-session-summary`。
- `.claude/settings.local.json` は権限/制約設定のみ。
- `cli/lib/merge_settings.py` の `HELIX_HOOKS` も Stop→`helix-session-summary`。

#### E. `.helix/session-summaries/` 運用実態

- 既存 md は日付ベースで履歴保持。
- 直近の更新履歴は参照文脈上で利用されるが、実行時再生成必須の前提は未限定。

### §3.2 目標アーキテクチャ（DoD 前提）

方針:
- Stop hook 実行時は、DB への記録のみ実施し、md ファイルへの新規追記・再生成を止める。
- セッション確認は `helix log report session` で都度集計表示。
- 集計は `hook_events` / `gate_runs` / `cost_log` の同一日付条件で実施。

必須要件:
1. `Stop hook` 後に当日新規 `.helix/session-summaries/<DATE>-session.md` が生成されない。
2. `helix log report session --date <DATE>` が任意日付で再集計表示可能。
3. 集計出力は既存レポートと同一フォーマット系トーン（テーブル中心）で、対象日付の `終了 N 回` を解釈。

### §3.3 PM 確定事項（§5.4 の更新）

#### 決定 1
- Stop hook 後の shim 出力は静音。
- `cli/helix-session-summary` 自体も標準運用上、`stdout`/`stderr` を追加出力しない。
- 例外ログは必要最小に限定。

#### 決定 2
- migration は **案 B（既存 md は保持し、新規生成のみ停止）** を採用。
- 案 A（archive 移設）・案 C（全削除）は本 PLAN では未実施。
- 将来実施時は別 PLAN で再検討。

#### 決定 3
- `helix log report session --date` の既定は `today`（省略時は当日）。
- `helix log report` の既存挙動との整合を維持。

### §3.4 `helix log report session` 実装方針

#### §3.4.1 CLI 仕様

- 追加 report type: `session`
- パターン: `helix log report session --date <YYYY-MM-DD>`
- `--date` 未指定時は `today`。
- 入出力は既存 report との一貫性を保ち、`report` サブコマンドの既存 `--date` エラーパターンに準拠。

#### §3.4.2 集計仕様

- `hook_events`: `event_type` 別件数
- `gate_runs`: `gate` / `result` 別件数
- `cost_log`: `role` / `model` 別件数
- `終了 N 回`: `cost_log` で `role='opus-pm'` かつ当日条件。

#### §3.4.3 出力仕様

- 既存 `helix log report` 系と同系統の表形式。
- 対象日付ヘッダ、テーブルヘッダ、各種集計セクションで構成。

### §3.5 マイグレーション方針（案整理）

- **採用: 案 B** — 既存 `.helix/session-summaries/*.md` をそのまま保持し、新規生成停止のみ実施（touch 0）。
- **将来選択肢: 案 A** — 既存 md を archive へ退避。
- **将来選択肢: 案 C** — `.helix/session-summaries/*.md` を全削除。

### §3.6 DoD（実装完了基準）

1. Stop hook 実行後、新規 `.helix/session-summaries/<DATE>-session.md` が生成されない。
2. `helix log report session --date <DATE>` が任意日付で実行可能。
3. 任意日付で `hook_events` / `gate_runs` / `cost_log` を同条件（日付）集計で再表示できる。
4. 既存 `helix log report` の他 report type（`quality` 等）に回帰しない。
5. `cli/helix-session-summary` は DB INSERT のみのシム動作。
6. `helix test` が shell / pytest / bats 全部 PASS（baseline: 572 / 655 / 196 以上）。
7. `helix log report session` の bats が追加され、DoD #2 を実行時点で検証できる。

### §3.7 サイジング

- size: M（ファイル想定 3-5）
- type: `refactor+enhancement`
- 想定 files:
  - `cli/helix-log`
  - `cli/lib/helix_db.py`
  - `cli/helix-session-summary`
  - `cli/tests/test-helix-log*.bats`（実装側）
  - `README.md` / 該当 `SKILL.md` / `CLAUDE.md`（必要時）
- 変更対象ドキュメント: `docs/plans/PLAN-016-session-summary-helix-log-report.md`

### §3.8 リスクと緩和

| リスク | 影響 | 緩和 |
|---|---|---|
| Stop hook 変更と実装テストの未整合 | M | 集計仕様（created_at, date 条件）を本文・DoD に固定し、retro へ残置 |
| 過去 md の参照運用との齟齬 | M | 案 B 採用で履歴保持を最優先し、将来選択肢を明確化 |
| `session` report の初期実装ミス | M | テーブル集計条件を既存コマンドと同型化し、DoD #2/#3 を bats で回帰固定 |
| 参照リンク断絶 | L | 本 PLAN の §5.1 / §5.2 で PLAN/retro/CLI の整合を明示 |

## §4. 実装計画

### §4.1 Sprint

| Sprint | 内容 | 担当 | thinking |
|---|---|---|---|
| .1 | helix log report session の仕様確定（引数・出力フォーマット・テーブル集計範囲）と現状コード調査結果の整理 | Codex docs | medium |
| .2 | helix log report session 実装（`cli/helix-log` + `cli/lib/helix_db.py` 拡張）＋ bats/pytest テスト追加 | Codex PG | low |
| .3 | `cli/helix-session-summary` を「DB INSERT only シム」に縮退 + Stop hook 切替 (`.claude/settings.json` 確認) + 回帰テスト | Codex PG | low |
| .4 | helix test 全 PASS 確認 + migration（案 B = 既存 md は触らず新規生成停止のみ確認） | Opus 直接 | — |
| .5 | doc 更新（README/該当 `SKILL.md`/`CLAUDE.md` があれば） + retro 起草 (`.helix/retros/2026-05-03-G4-PLAN-016.md`) | Codex docs | medium |

### §4.2 実装方針注記

- `.2/.3` は実装 Sprint（本 PLAN の実行対象外）。本 PLAN は実装仕様と DoD を完了させ、finalize 後の別実装タスクで PG に委譲する。
- `.4` は Opus 担当のテスト/本番前最終確認。

### §4.3 G4 ゲート判定基準（PLAN 承認）

- DoD #1〜#7 を実装完了条件として固定。
- `helix-codex review --uncommitted` で P1/P2 の未解消指摘なし。
- `accuracy_score` の遅延（deferred）新增なし。

## §5. 既存運用・リンク整合・追跡項目

### §5.1 参照更新候補（現時点）

- 運用定義
  - README: `helix session-summary`（Stop hook 目的）
  - `docs/design/D-HOOK-SPEC.md`: Stop hook / 実行時刻
  - `docs/adr/ADR-009-hook-strategy.md`: Stop → `helix-session-summary`
- 計画/retros の継続性
  - `.helix/retros/2026-05-03-G4-PLAN-014.md`
  - `.helix/retros/2026-05-03-G4-PLAN-015.md`
  - `.helix/retros/2026-05-03-G4-PLAN-016.md`（本 PLAN で起草予定）
- コード参照
  - `cli/helix-session-summary`
  - `cli/helix-log`
  - `cli/lib/helix_db.py`
  - `.claude/settings.json`
  - `cli/lib/merge_settings.py`

### §5.2 リンク整合チェック結果（本 PLAN 起草時）

- チェック対象参照の存在確認を実施。
- 破損リンク（参照先不在）: 0 件
- 例外: `.helix/retros/2026-05-03-G4-PLAN-016.md` は起草対象のため「未作成」だが、本文内はリンク未固定参照として運用。
- `helix log report session` の実体は実装 Sprint 以降で補完。

### §5.3 TODO 残存確認

- 本 PLAN 本文内の TODO/FIXME: 0 件
- 未解決の TODO は §6 に委譲し、実装前再確認で吸い上げ。

### §5.4 PM 確定事項

1. Stop hook 直後の shim 出力: 静音（DB INSERT のみ）。
2. マイグレーション: 案 B 採用（既存 md は保持、生成停止のみ）。
3. `helix log report session --date`: 既定値 today（省略時=当日）。

## §6. PM 確認事項

- 実装着手前に既存コードの現状再確認を行い、前提日付計算・hook 配線・既存 report 出力との干渉がないことを確認する。

## 参考資料

- [`docs/plans/PLAN-014-stop-hook-idempotency.md`](docs/plans/PLAN-014-stop-hook-idempotency.md)
- [`docs/plans/PLAN-015-stop-hook-test-guard-hack.md`](docs/plans/PLAN-015-stop-hook-test-guard-hack.md)
- [`.helix/retros/2026-05-03-G4-PLAN-014.md`](.helix/retros/2026-05-03-G4-PLAN-014.md)
- [`.helix/retros/2026-05-03-G4-PLAN-015.md`](.helix/retros/2026-05-03-G4-PLAN-015.md)
- [`cli/helix-session-summary`](cli/helix-session-summary)
- [`cli/helix-log`](cli/helix-log)
- [`cli/lib/helix_db.py`](cli/lib/helix_db.py)
- [`.claude/settings.json`](.claude/settings.json)
- [`cli/lib/merge_settings.py`](cli/lib/merge_settings.py)
- [`docs/design/D-HOOK-SPEC.md`](docs/design/D-HOOK-SPEC.md)
- [`docs/adr/ADR-009-hook-strategy.md`](docs/adr/ADR-009-hook-strategy.md)
- [`README.md`](README.md)
