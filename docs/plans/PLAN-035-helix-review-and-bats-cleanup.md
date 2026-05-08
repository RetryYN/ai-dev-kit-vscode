---
plan_id: PLAN-035
title: PLAN-035（helix review read-only fix + bats teardown 堅牢化 + Codex 完了報告信頼性強化）
status: completed
created: 2026-05-09
finalized: 2026-05-09
completed: 2026-05-09
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
note_size: W-2 は cli/tests/*.bats 52 ファイル一括置換のため SKILL_MAP の 11+ ファイル基準では L 相当だが、変更は機械的 sed 置換で行数 100 行程度に収まり、内容変更は teardown 内 1 行のみ → M で運用 (G4 を計画に含めて L4 実装凍結まで追跡)
acceptance:
  - W-1: `cli/helix-review` の read-only sandbox での `helix review --uncommitted` 実行を `HELIX_CODEX_INTERNAL` 検知時に skip へ切替し、PLAN-035 W-1 要件として実装可能になること。
  - W-2: `cli/tests/*.bats` の teardown 内 `rm -rf "$TMP_ROOT"` 系を `rm -rf "$TMP_ROOT" 2>/dev/null || true`（または `HELIX_TEST_TMPDIR` 換算）へ統一し、`Directory not empty` 起因の偶発 fail を抑止できること。
  - W-3: Codex 委譲完了報告の過信防止を docs/memory に記録し、allowed-files mock test 的な failure を Opus が full self-test (`cli/helix-test`) で検証する運用へ転換できること。
  - W-4: carry 3 件の統合検証と retrospective 連携が完了し、status transition の受入条件が明確であること。
related: [PLAN-034, PLAN-033, ADR-014, ADR-015]
---

## §1 目的

PLAN-034 carry 3 件を次スプリントとして再集約し、再発防止まで含む実行計画を定義する。

PLAN-035 は次の 3 つを対象とする。

- W-1: `helix review --uncommitted` の read-only sandbox での production fix（`HELIX_CODEX_INTERNAL` 検知時に transparent skip）
- W-2: `cli/tests/*.bats` teardown の silent fail 化（`rm -rf ...` 時の偶発失敗対策）
- W-3: Codex 完了報告に対する検証前提（`decision: passed` 等）への依存を下げる memory feedback 追加

本計画は文書起票（Plan）として開始し、実装・テスト・統合は WBS 並列 Sprint で実施する。

## §2 スコープ

### §2.1 対象範囲（PLAN-035 carry 対象）

- W-1 で `cli/helix-review` の `HELIX_CODEX_INTERNAL` 検知時の early skip を本番 fix として実装対象化する。
  - 既知方針 (PLAN-035 採用): docs/architecture/codex-review-sandbox-limitation.md §7 の 3 案 (a/b/c) のうち **(b) HELIX_CODEX_INTERNAL=1 検知時 transparent skip** を採用。短期回避策として PLAN-035 で確定し、docs §7 の根本 fix 方針 (read-only でも review 初期化成立) を **supersede** する (本 PLAN の成功条件は「review 初期化成功」ではなく **「nested review を skip して exit 0 を返す」** こと)
  - **挿入位置の固定**: `cli/helix-review` の **`--help` 解析後、`CODEX_BIN` 検査と `LOG_DIR` mkdir より前** に置く (実装者によるばらつき防止)
  - **stderr 契約**: skip 時は stderr に正確に 1 行 `[helix-review] skipped: nested review unsupported in read-only sandbox` を出力。既存テストの stderr 期待値に該当パターンがある場合は契約として許容
  - 実装コード:
    - `if [[ -n "${HELIX_CODEX_INTERNAL:-}" ]]; then`
    - `  echo '[helix-review] skipped: nested review unsupported in read-only sandbox' >&2`
    - `  exit 0`
    - `fi`
  - **参照 docs**: `docs/architecture/codex-review-sandbox-limitation.md` は PLAN-034 W-3 (commit `ffb9d2b`) で **既に作成済**。本 PLAN W-1 では **再作成しない**。実装後に docs §5 の運用ルールが運用適用される
- W-2 で `cli/tests/*.bats` teardown 52 ファイル（`"$TMP_ROOT"` / `"$HELIX_TEST_TMPDIR"` 削除）を一括統一置換。
  - `rm -rf "$TMP_ROOT" 2>/dev/null || true`、`rm -rf "$HELIX_TEST_TMPDIR" 2>/dev/null || true`
  - 既存テスト 347 件維持（regression 視点: 全 PASS）
- W-3 で `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_codex_completion_distrust.md` を新規追加し、`MEMORY.md` の index へ追加する運用を定義する。
  - `PLAN-034` W-12 の失敗（stderr に AUDIT_FILE error と helix-test fail を見落とし）を再発防止根拠として残す。

### §2.2 非対象（Out of Scope）

- `cli/helix-review` 以外の review 周辺コマンド（`cli/helix-codex`、`helix review` エンジン本体）の広範改修
- 監査ロジックの全面刷新、secret/env / 外部 API / インフラ変更
- `cli/tests` の teardown 以外のテスト構造改修（fixtures、assertion、suite 分解等）
- W-3 memory feedback の内容を超えるメモ運用規約の全面再設計
- Codex CLI 内部の session init 仕様変更 (本 PLAN は helix-review 側で transparent skip するのみ。Codex CLI 本体は変更しない)

(注: `cli/helix-review` の HELIX_CODEX_INTERNAL skip 実装と `cli/tests/*.bats` teardown 一括置換は **本 PLAN の対象** であり Out of Scope ではない。§4 Sprint 表参照)

## §3 受入条件（carry 解消定義）

- PLAN-034 carry 3 件を PLAN-035 の W-1/W-2/W-3 に再配線すること。
- 各 W-2 に対し、既存回帰テスト（347 bats）再実行を失敗なく通過しうる条件を定義すること。
- W-3 は実装外の policy 追加ではなく、memory 運用として明文化し、次回 full self-test（`cli/helix-test`）に接続することを明示すること。
- `docs/plans/PLAN-031-...`, `PLAN-032...`, `PLAN-033...`, `PLAN-034...` と同等の節構成で、追跡可能な Sprint 計画を満たすこと。
- Draft 起票後に本文・依存・reference_docs 更新が可能な状態（不整合のない状態）にあること。

## §4 Sprint 表（PLAN-035）

### 4.1 全体構成（PLAN-031/032/034 形式踏襲）

- W-0: draft 起票 + TL 2 ラウンドレビュー + finalize
- W-1: `helix-review HELIX_CODEX_INTERNAL=1 transparent skip`（production fix）
- W-2: bats teardown silent fail 化（52 ファイル一括）
- W-3: memory feedback 追加（docs/memory only）
- W-4: 統合検証 + retrospective + status completed

| Sprint | 役割 / 規模 | 担当 | 主要作業 | 成功条件 | 受入テスト / 検証 |
|---|---|---|---|---|---|
| W-0 | Docs/Plan（S） | Docs（本体） / TL | PLAN-035 draft 起票、W-1/W-2/W-3 の carry 再配線、reference_docs 反映 | 受入条件が一意に追跡可能 | plan レビュー |
| W-1 | Code / WBS axis-1（S） | SE | `cli/helix-review` の --help 解析後・CODEX_BIN 検査前に `HELIX_CODEX_INTERNAL` skip 追加 + 専用 bats 1 件追加 | nested review skip で exit 0 (review 初期化成立は不要、PLAN-035 で docs §7 を supersede) | `cli/tests/test-helix-review-internal-skip.bats` 新規 (W-2 teardown 置換と編集衝突なし、別ファイル新規作成のため) |
| W-2 | Code / WBS axis-2（M） | SE | `cli/tests/*.bats` teardown ブロックを一括 sed 置換 (52 ファイル) | teardown fail 回避（偶発 fail 消去） | `bats cli/tests` 全 suite PASS。**W-2 単体では新規テスト追加なし** (機械的置換のみ)、全 suite 数は W-1 完了後の 349 件で regression なしを確認 |
| W-3 | Docs / WBS axis-3（S） | Docs（本体） | memory feedback 新規追加 + MEMORY.md 追加 | Codex completed report の過信を制約する運用定義 | レビュー観点チェック |
| W-4 | Docs/Validation（S） | Docs + PM（運用承認） | carry 連鎖、retro placeholder 更新、状態遷移条件整理 | 3 carry の統合追跡と完了可否が明確 | 統合再現条件レビュー |

### 4.2 W-0（Plan）

- output: `PLAN-035` ドキュメント draft 起票
- 主要確認:
  - PLAN-034 carry 3 件を WBS へ再配線
  - W-1/W-2/W-3 の依存境界と受入条件を明示
  - TL レビュー 2 ラウンド前提の整理（P2 / P3 項目）で矛盾なし
- 承認条件:
  - 目的と受入条件の完全定義
  - Sprint 表の順序整合（parallel 無衝突）
  - Reference docs のリンク整合

### 4.3 W-1（Production fix）

- 目的: `cli/helix-review` を read-only sandbox nested 実行非対応として安全停止し、`helix review --uncommitted` の失敗を回避する
- 影響範囲:
  - 対象: `cli/helix-review` + `cli/tests/test-helix-review-internal-skip.bats` (新規、W-2 一括置換と衝突しない別ファイル)
  - 追加行数: 約 5 行 + bats 1 ファイル
  - 条件: `HELIX_CODEX_INTERNAL` が unset なら既存動作を維持、set なら skip
- 挿入位置の固定:
  - `cli/helix-review` の **`--help` 解析後**、`CODEX_BIN` 検査 (line 32 付近) と `LOG_DIR` mkdir (line 38 付近) より **前** に置く
  - 既存 `case "${1:-}" in --help|-h)` ブロック (line 10-19) の直後、UNCOMMITTED 変数初期化の前
- DoD:
  - `HELIX_CODEX_INTERNAL=1 cli/helix-review --uncommitted` で exit code 0
  - stderr に正確に 1 行 `[helix-review] skipped: nested review unsupported in read-only sandbox` 出力
  - `HELIX_CODEX_INTERNAL` 未設定時、通常の `helix review --uncommitted` を継続 (CODEX_BIN 検査・LOG_DIR mkdir → run_review に進む)
  - bats `cli/tests/test-helix-review-internal-skip.bats` で 2 ケース (set 時 skip / unset 時通常動作) PASS
- 参考実装方針:
  - 1 行追加の transparent skip で副作用を最小化
  - 追加時の stderr は人間判断向けに明示

### 4.4 W-2（安定化）

- 目的: `cli/tests/*.bats` teardown の偶発 fail を除去し、再現性を担保する
- 影響範囲:
  - 対象: `cli/tests/*.bats`（52 ファイル）
  - 変更対象パターン: `rm -rf "$TMP_ROOT"` / `rm -rf "$HELIX_TEST_TMPDIR"`
- DoD:
  - 全 teardown ブロックを `2>/dev/null || true` に統一
  - plan-only / full-auto のいずれでも teardown fail を起因とする不定終了が消える
- 技術方針:
  - cleanup 失敗時は fail を広く遮断（silent 化）
  - mktemp を新規作成して使い捨てる設計のため residual tmp 残存リスクは最小
- 品質補足:
  - `rm -rf` の失敗原因が「一時ディレクトリ競合」であるため、cleanup 成功可否は再試行可能設計で運用

### 4.5 W-3（運用規約）

- 目的: Codex 委譲完了報告（`decision: passed`）を鵜呑みにしないための記憶化ルールを整備する
- 影響範囲:
  - `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_codex_completion_distrust.md`（新規）
  - `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/MEMORY.md`（index 追記）
- DoD:
  - 既存 feedback「commit message verification 文を信用しない」を追記する関連 feedback として位置付け
  - "Opus が必ず `cli/helix-test` を最初に実行し 0 failed を確認する" を明示
  - Why と How-to 両輪が明確

### 4.6 W-4（統合）

- 目的: W-1/W-2/W-3 の Carry クローズ条件を同一ドキュメントで追跡し、completed 遷移判断可能状態にする
- 主要作業:
  - 各 W の受入条件を完了順に照合
  - PLAN-035 Retrospective を更新（Keep / Problem / Try）
  - status 遷移: W-0 完了で `finalized`、W-4 完了で `completed` (R-5 と整合、3 段階遷移)
- 対象成果:
  - 統合検証チェックリスト
  - carry 3 件が再発防止で閉じる理由の記録

## §5 リスク登録

- R-1: W-1 が production skip であるため、根本実装（完全対処）まで再発可能性が残るリスク
  - 対策: PLAN-035 の W-3 で回避手順と監視要件を再定義し、PLAN-036 等へ carry 可能な形で引き継ぐ
- R-2: W-2 で cleanup を silent 化すると、実際の tmp 削除失敗の早期検知が鈍る
  - 対策: mktemp 再生成戦略の前提（コネクション毎・suite 毎）を前提文書化し、bats 全体を監査対象に保持
- R-3: W-3 の feedback 追加が運用で忘却される（index 未参照・運用逸脱）
  - 対策: MEMORY.md index 追記を W-3 DoD の必須とし、Opus full self-test の最上位順序に明文化
- R-4: W-1/W-2/W-3 の実装分離を誤ると、carry 追跡とレビュー観点が交差する
  - 対策: W-1 は code, W-2 は tests, W-3 は memory のみと明示し、parallel 可能性を維持
- R-5: status 遷移の解釈ばらつき (draft → completed 直行に見える)
  - 対策: status 遷移を **draft → finalized → completed** の 3 段階で運用 (PLAN-031/032/033/034 と同形式)
    - draft: 起票時、TL レビュー前
    - finalized: W-0 完了時、TL 2 ラウンド approve 後 (実装着手準備完了)
    - completed: W-4 統合検証 + retro 完了後

## §6 Test Plan

### §6.1 W-1（production fix）

- 実行観点:
  - `HELIX_CODEX_INTERNAL=1 cli/helix-review` で exit 0 + skip message
  - `HELIX_CODEX_INTERNAL` 未設定時の通常実行
- 期待結果:
  - read-only sandbox で session init failure を回避
  - 既存フロー変更なし

### §6.2 W-2（tests）

- 実行観点:
  - `cli/tests/*.bats` 全 52 ファイルの teardown 置換が一貫 (`grep -c '2>/dev/null || true'` で機械的検証)
  - 既存 `bats cli/tests` の regression 監査
- 期待結果:
  - `Directory not empty` が原因の teardown fail 低減
  - 既存 test 347 件は PASS を維持 (W-1 で +2 → 349 想定)
- 追加 test:
  - 追加テストは基本不要（回帰観測のみ）とし、既存 suite を利用
- **長期残存境界 (silent fail の運用許容)**:
  - silent fail 化により `rm -rf` 失敗 (ディスク満杯 / 権限異常) の早期検知が落ちる
  - bats は mktemp で TMP_ROOT を毎回新規作成するため通常 run の影響なし
  - `/tmp` 配下に bats 由来の残存 dir が累積する可能性は **運用許容**、必要時は別 PLAN (PLAN-036 等) で `/tmp/bats-test-*` の定期 cleanup 監査機構を検討
  - PLAN-035 の境界: 「silent fail 化までを実施、長期監査は別 PLAN」

### §6.3 W-3（memory feedback）

- 実行観点:
  - memory feedback 内容が PLAN-034 W-12 失敗との因果を保持するか
  - MEMORY.md から参照可能か
- 期待結果:
  - Codex completed report への依存低減（full self-test 先行）運用が成立
  - 新規フィードバックとして持続運用できる記述

### §6.4 W-4（統合）

- 受入観点:
  - `PLAN-034` carry 再配線が W-1/W-2/W-3 の順序と一致
  - `status: draft` 起票内容が completed 判定に必要な evidence を欠かない
- 承認準備:
  - 既存 TEST 実行結果が実装完了後に反映される前提
  - retrospective の Keep/Problem/Try が next sprint に明示される

## §7 Out of Scope (詳細列挙、§2.2 と相補)

§2.2 でカバーした「review 周辺コマンドの広範改修 / 監査ロジック全面刷新 / teardown 以外のテスト構造改修 / memory 運用全面再設計 / Codex CLI 内部仕様変更」に加え、以下を明示的に非対象とする:

- `cli/lib` や `cli/templates` 全体の広域改修
- 外部 API / 認証 / 決済 / PII / secret/credential の変更
- state-events 接続点の変更
- PLAN-035 起票の範囲を超える運用制度の全面刷新
- bats teardown silent fail 化に伴う `/tmp/bats-test-*` 残存の長期 cleanup 監査機構 (§6.2 の境界参照、別 PLAN へ carry)

(注: `docs/architecture/codex-review-sandbox-limitation.md` は PLAN-034 W-3 commit `ffb9d2b` で **既に作成済**。本 PLAN W-1 では再作成しない、運用適用のみ実施)

## §8 実装 Notes

- 基準ドキュメント:
  - [PLAN-031-carry-resolution](PLAN-031-carry-resolution.md)
  - [PLAN-032-helix-test-and-concurrent-resolution](PLAN-032-helix-test-and-concurrent-resolution.md)
  - [PLAN-033-drift-check-and-baseline-cleanup](PLAN-033-drift-check-and-baseline-cleanup.md)
  - [PLAN-034-codex-output-and-prompt-template](PLAN-034-codex-output-and-prompt-template.md)
- carry 連鎖:
  - PLAN-034 retro carry（W-12）を PLAN-035 W-1/W-2/W-3 へ転送
  - W-4 で retro placeholder を更新し次回着手条件を明文化
- 参照仕様:
  - `docs/architecture/codex-review-sandbox-limitation.md` は PLAN-034 W-3 commit `ffb9d2b` で作成済の参照資料。本 PLAN W-1 で実装する transparent skip (方針 b) は docs §7 の根本 fix 方針 (a) を **supersede** する短期回避策として位置付ける。本 PLAN では再作成しない

## §9 Retro Placeholder

- Keep
  - carry 候補を同一 PLAN に再集約し、Sprint ごとに実装境界を分離する運用を維持する
  - PLAN-031/032/033/034 の章立てを踏襲し、追跡性を崩さない
  - W-1/W-2/W-3 が編集衝突しないよう対象軸を分離する
- Problem
  - `helix review --uncommitted` の read-only 依存制約は本 PLANに依存し、根治ではなく運用 + 実装 guard で回避している
  - teardown の silent fail 化は failure 可視性を減らす側面を持ち、運用監査が必要
- Try
  - PLAN-036 で PLAN-035 W-1 の根本解決（`helix-review` 実装体制の見直し）を検討する
  - W-2 の再発防止を観測ログ（cleanup 結果）で補強し、必要時 W-2+α へ展開する
  - W-3 の feedback 効果を PLAN-035 完了時点で Opus の self-test 順序遵守率として追跡する

## §10 更新履歴 / 承認ログ

- 2026-05-09: draft 起票（Codex Docs）
- 2026-05-09: PLAN-034 carry 3 件を W-1/W-2/W-3 として再配線し、実装順序を定義
- 2026-05-09: W-0 構造（Goal / Sprint / Risk / Test Plan / Out of Scope / Retro Placeholder）を PLAN-031/032/033/034 形式へ整合
