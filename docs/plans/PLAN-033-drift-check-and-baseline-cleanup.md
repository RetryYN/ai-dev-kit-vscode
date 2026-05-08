---
plan_id: PLAN-033
title: HELIX v2/32 carry 解消 (drift-check jq 解消 + baseline PID-aware cleanup + tests 役割明示)
status: completed
created: 2026-05-09
finalized: 2026-05-09
completed: 2026-05-09
author: Opus (PM)
size: M
phases: L1→L2→L3→L4→L6
gates: G1, G2, G3, G4
acceptance:
  - W-1: `cli/helix-drift-check` の汎用 deliverable 検出における `jq` 依存を排除し、`jq` 未導入時でも frozen guard が PASS 可能。
  - W-2: 既に `codex-baseline-$$-<timestamp>.txt` 命名 (cli/helix-codex:1034) となっている baseline に対し、`cli/lib/codex_post_validation.py` で **PID 生存確認** (`kill -0` 相当) と **stale cleanup** (PID dead かつ window 外) を追加し、orphan baseline 永続残存を排除する。
  - W-3: `docs/architecture/test-layout.md` に `tests/` と `cli/lib/tests/` の役割分担（E2E と unit）を明文化。
  - W-4: テスト群の回帰: 既存 `pytest cli/lib/tests/` と `bats cli/tests` を維持しつつ、W-1/W-2/W-3 導入に伴う新規シナリオを追加 PASS。
related: [PLAN-031, PLAN-032, ADR-014, ADR-015]
---

## §1 Goal

PLAN-032 の未完了 carry 3 件（W-1/W-2/W-3）を PLAN-033 として再集約し、以下の 3 目標を達成する。

- `cli/helix-drift-check` の jq 依存を排して、汎用 D-XXX deliverable 検知時の silent fail を防ぐ。
- baseline 管理を PID-aware にし (生存確認 + stale cleanup)、並列実行・残骸除去・監査性を改善する (命名自体は既に PID 入り)。
- `tests/` 系と `cli/lib/tests/` 系の役割境界を docs で明確化し、意図しない重複解消を抑止する。

本 PLAN は「ドキュメントとして draft を起票」し、実装は W-1/W-2/W-3 の担当に委譲する。

## §2 スコープ

### §2.1 対象

- PLAN-032 carry W-1（`cli/helix-drift-check` の jq 依存排除）
  - 既存 `cli/helix-drift-check` 内の汎用 D-XXX deliverable 判定ロジック（`cli/helix-drift-check:213-216` 付近）
  - `jq` 分岐の除去、Python helper (`json.load`/`json.loads`) への置換
  - `cli/lib/tests` に index lookup 単体検証追加
  - drift-check 自体は shell 実行で、検知ロジック整合確認を強化
- PLAN-032 carry W-2（baseline PID-aware cleanup）
  - 前提確認: `cli/helix-codex:1034` で既に `codex-baseline-$$-<timestamp>.txt` 命名済み (PID 入り)
  - `cli/lib/codex_post_validation.py::load_newer_baselines` を PID-aware 化:
    - ファイル名から PID 抽出 (regex `codex-baseline-(\d+)-\d+\.txt`)
    - `kill -0 <pid>` 相当 (`os.kill(pid, 0)`) で PID 生存確認
    - PID dead かつ window 外 baseline は concurrent から除外し、可能なら削除 (stale cleanup)
    - PID 生存中は window 外でも concurrent に含める (long-running concurrent 対応)
  - `own_baseline` 判定は既存 path 比較を維持 (caller 引数で渡される own path で識別)
  - `cli/lib/tests/test_codex_post_validation.py` に PID 生存確認 / stale cleanup / 命名 regex の追加ケース
- PLAN-032 carry W-3（tests 役割明示）
  - `docs/architecture/test-layout.md` を「重複ではなく役割分担（E2E 対 unit）」へ更新
  - `tests/test_code_catalog.py` 冒頭注記（E2E 入口）
  - `cli/lib/tests/test_code_catalog.py` 冒頭注記（unit 入口）

### §2.2 非対象（out of scope）

- 本 PLAN 外のコアロジック変更（新規ルール追加や D-API 変更）
- PLAN-032 W-5 で想定される broader テスト統合・物理移設の実施
- フォーマット崩れや lint 固有の大量再構成（必要最小差分のみ）
- 外部 API、インフラ、認証/認可ロジックの変更

## §3 受入条件（Draft 起票用）

### §3.1 仕様面 DoD（Carry 解消）

- W-1 で jq 依存の排除が可能で、汎用 D-XXX 検知が `jq` 有無に依存しないこと。
- W-2 で `load_newer_baselines` が PID 生存確認を行い、long-running concurrent (window 60s 超) でも生存中 PID の baseline は concurrent として扱われること。
- W-2 で stale 判定（PID dead + window 外）時に該当 baseline ファイルが cleanup (削除) され、orphan が永続残存しないこと。
- W-3 でテスト役割境界が docs で可読に整備され、将来の物理削除対象化が回避されること。

### §3.2 品質面 DoD（実装完了時）

- W-1: `pytest cli/lib/tests` の index lookup ケース PASS、drift-check 自体の shell test 無 regressions
- W-2: `pytest cli/lib/tests/test_codex_post_validation.py` 追加ケース 4 系列 PASS（PID regex 抽出 / PID 生存中の long-running concurrent / PID dead + window 外の stale cleanup / 既存 60s window 維持）
- W-3: docs 追加/更新後のリンクと説明整合性に違和感がないこと
- W-4: `bats cli/tests` と `pytest cli/lib/tests/` の既存回帰を崩さないこと

## §4 Sprint 表（PLAN-033）

### Sprint 全体構成

- W-0: draft 起票、TL レビュー 2 ラウンド、finalize
- W-1: drift-check jq 解消（parallel-safe）
- W-2: baseline PID 化（parallel-safe）
- W-3: tests 役割明示（docs-only）
- W-4: 総合検証 + retrospective + status completed への遷移

| Sprint | 役割 / 規模 | 担当 | 主要作業 | 成功条件 | 受入テスト |
|---|---|---|---|---|---|
| W-0 | Docs/Plan（S） | Docs（本体） | PLAN-033 起票、W-1/W-2/W-3 合意 | ドキュメント構造、受入条件がPLAN-031/032準拠 | 文書レビュー |
| W-1 | Code / WBS axis-1（S） | PE/SE | `cli/helix-drift-check` の jq 依存削除 | 汎用 D-XXX 検出で silent fail 排除 | pytest+bash self-test |
| W-2 | Code / WBS axis-2（S-M） | SE | baseline PID 生存確認 + stale cleanup | long-running concurrent 対応、orphan 自動除去 | pytest 追加ケース |
| W-3 | Docs / WBS axis-3（S） | Docs（本体） | test 役割境界文言化 + ファイル冒頭注記 | 物理削除禁止の意図整備 | docs lint（リンク） |
| W-4 | Docs/Validation（S） | Docs + PM | retro 登録と完了判定準備 | W-1/W-2/W-3 成果の総合接続 | 回帰テスト再確認 |

### W-0（Plan）

- output: この `PLAN-033` draft の起票
- 主要確認:
  - PLAN-032 carry 3 件の再集約
  - 役割分担と並列実行境界の明示
  - コード変更は各 Sprint へ委譲可能な記載
- 承認条件:
  - TL レビュー 2 ラウンド
  - WBS と reference-docs の照合

### W-1（axis-1）

- 目的: `cli/helix-drift-check` における `jq` 呼び出しを Python helper 化
- 影響範囲:
  - `cli/helix-drift-check` 1 ブロック（汎用 D-XXX 検出、213-216 行付近）
  - **原則 inline Python helper** (`python3 -c "import json; ..."`) で済ませる。1 箇所のみの jq 使用なので新規 module 追加は過剰抽象になりやすい
  - 例外: 既存 `cli/lib/` 配下に index lookup を行う module が既にあれば拡張する。新規 `cli/lib/index_lookup.py` 追加は「将来的に再利用予定がある」と W-1 担当が判断した場合のみとし、追加した場合は別途 docs 更新の必要なし
- テスト:
  - index lookup unit テスト（`pytest cli/lib/tests`）
  - drift-check 汎用 deliverable 検出シナリオ 1 件追加（BATS または shell test）
- DoD:
  - `jq` command-not-found 時の unknown 判定にならない
  - frozen guard が `unknown` により黙る事象が消える

### W-2（axis-2）

- 目的: baseline 命名は既に PID 入り (cli/helix-codex:1034) のため、`load_newer_baselines` 側で PID 生存確認 + stale cleanup を実装
- 影響範囲:
  - `cli/lib/codex_post_validation.py` (`load_newer_baselines` 改修、PID 抽出 helper 追加)
  - `cli/lib/tests/test_codex_post_validation.py` (4 ケース追加)
  - `cli/helix-codex` 側 baseline 生成箇所は **変更なし** (既に PID/timestamp 入り)
- テスト:
  - PID regex 抽出: `codex-baseline-(\d+)-(\d+)\.txt` から pid を取り出せる
  - long-running concurrent: PID 生存中なら window 外でも concurrent に含める
  - stale cleanup: PID dead + window 外 baseline は concurrent から除外し削除
  - 既存 60 秒 window テスト維持: regex match 失敗時 (既存 fake 命名 `codex-baseline-1-older.txt` 等) は従来の window-only 判定にフォールバック (backward compat)
  - own_baseline 判定: caller が渡す own_baseline path はそのまま skip (現状維持)
- DoD:
  - PID 生存確認が `os.kill(pid, 0)` (PermissionError は生存とみなす) で動く
  - stale baseline が cleanup される (削除エラーは silent ignore)
  - orphan の継続残存が低減し、long-running concurrent も正しく検出される

### W-3（axis-3）

- 目的: tests 役割の物理削除誤認識を防ぐため docs-first の境界明文化
- 影響範囲:
  - `docs/architecture/test-layout.md`
  - `tests/test_code_catalog.py`（ヘッダ注記）
  - `cli/lib/tests/test_code_catalog.py`（ヘッダ注記）
- テスト:
  - docs lint / markdownlint の該当ルール準拠
- DoD:
  - 「重複」ではなく「E2E vs unit の責務分担」として言及
  - docs 更新後、W-1/W-2 の実装との衝突なし

### W-4（統合検証）

- output:
  - PLAN-033 retro 追記
  - 次スプリント/受入向けの完了条件提示
- テスト:
  - `pytest cli/lib/tests/`
  - `bats cli/tests`
  - `pytest tests/`（該当時）
- DoD:
  - W-1/W-2/W-3 の成果を参照し、受入条件が閉じること
  - PM による completed 判定が可能になること

## §5 Risk Registry

- R-1: drift-check Python 化時の既存 jq 前提条件差分（出力形式差異）
  - 対策: 既存ケースの出力互換をテストで担保
- R-2: `load_newer_baselines` への PID-aware 改修で既存 60s window 判定が回帰
  - 対策: 既存 window-only ケース (`codex-baseline-1-older.txt` 等の fake 命名) を維持しつつ、PID regex match 失敗時は従来の window-only 判定にフォールバックする backward compat を実装で保証
  - 追加テストで PID regex 抽出 / long-running concurrent / stale cleanup の各経路を網羅
- R-3: W-3 の文言更新が運用解釈を誤るリスク
  - 対策: 「削除対象」ではなく「役割分担」を明示する文体に固定
- R-4: PLAN draft のみ実装順ずれで W-1/W-2 が同時進行時に責務不整合
  - 対策: Sprint 表と担当分離を明記、parallel-safe を明文化

## §6 Test Plan

- 既存テスト:
  - `pytest cli/lib/tests/` 回帰
  - `bats cli/tests` 回帰
  - `pytest tests/`（必要に応じて）
- 追加テスト:
  - W-1: index lookup 単体追加 (Python helper / inline) + drift-check 汎用 D-XXX 検出ケース 1 件
  - W-2: 4 系列追加
    - PID regex 抽出: `codex-baseline-(\d+)-(\d+)\.txt` から pid を取得できる
    - long-running concurrent: PID 生存中なら window 60s 外でも concurrent 含める
    - stale cleanup: PID dead + window 外 baseline は concurrent から除外し削除される
    - 既存 60s window 維持: regex match 失敗時 (既存 fake 命名) は従来挙動を維持
  - W-2 補助確認: caller が渡す own_baseline path は引き続き skip される (既存挙動の regression なし)
  - W-3: docs lint（リンク切れ含む）
- 非機能観点:
  - 追記ドキュメントの内部リンクが壊れないこと
  - 未完了項目の定点確認を PLAN 内で実施

## §7 Out of Scope

- `tests/` から `cli/lib/tests/` への物理移行・削除
- D-API / D-CONTRACT / D-DB 契約資産の再設計
- 本番影響が大きい設定変更や secret/env 変更
- `cli/lib/codex_post_validation.py` の baseline PID-aware cleanup を超えた監査基盤再設計
- baseline 命名規則そのものの変更 (既に PID 入りのため変更不要)

## §8 Implementation Notes（参考）

- [PLAN-032-helix-test-and-concurrent-resolution](PLAN-032-helix-test-and-concurrent-resolution.md)
  - parallel safe 判定の既存文脈を前提に axis を組み上げる
- [PLAN-031-carry-resolution](PLAN-031-carry-resolution.md)
  - carry 統合 → 受入追跡の書式を継承
- [docs/architecture/test-layout.md]
  - W-3 で更新対象
- [cli/lib/codex_post_validation.py]
  - W-2 の実装参照点
- [cli/helix-drift-check]
  - W-1 の対象領域

## §9 Retro Placeholder

- Keep
  - carry 構造を PLAN 単位で集約する運用自体は維持
  - PLAN-031/032 の文体と受入フローを踏襲
- Problem
  - 既存の `jq` 依存と baseline 管理 (命名は PID 入りだが 生存確認/cleanup ロジックなし) が、silent fail と orphan 残存という共通起因で残る
  - docs で役割境界を明示しない場合、再度「重複」という誤認を生む
- Try
  - 次回 W-4 統合時に、cleanup 未実行時の観測ログを 1 文追記し、再発時に追跡性を上げる
  - W-1/W-2 実装完了時に並列 3 本起動での実測数値を追記する
  - 本 PLAN 完了後、carry クローズ条件のテンプレートを次 PLAN 用に簡略化する

## §10 Approval / Update Log

- 2026-05-09: draft 起票 (Codex Docs)
- 2026-05-09: Opus による W-2 訂正 (baseline 命名は既に PID 入り → PID-aware cleanup へ表現修正)
- 2026-05-09: TL Round 1 → P2 2 件 + P3 1 件 (§6 4 系列再掲、§5 R-2 旧表現、§9 Retro 旧表現、W-1 index_lookup 過剰抽象)、Opus が反映
- 2026-05-09: TL Round 2 → P2 1 件 + P3 1 件 (line 128 backward compat 表現整合、line 219 baseline 命名→管理)、Opus が反映
- 2026-05-09: status finalized (W-1/W-2/W-3 並列実装着手準備完了)
- 2026-05-09: W-1 (commit 3ee1ecd) / W-2 (commit 5c4d281) / W-3 (commit ab9f9cf) 完了、統合検証 611/969/339/23 全 PASS
- 2026-05-09: status completed (W-4 retro + 統合検証で carry resolved 確定、retro は `.helix/retros/PLAN-033.md`)
