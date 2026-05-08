---
plan_id: PLAN-034
title: helix-codex output tee + 委譲プロンプト共通フッタ（PLAN-033 retro 3 件 carry 集約）
status: completed
created: 2026-05-09
finalized: 2026-05-09
completed: 2026-05-09
author: Opus (PM) / Codex Docs
size: M
phases: L2→L3→L4
gates: G1, G2, G3
acceptance:
  - W-12-A: `cli/helix-codex` で codex stdout を audit log へ tee で保存し、`PIPESTATUS` 取得済み exit code で判定可能化する。
  - W-12-B: 委譲プロンプトへ共通フッタ（summary/decision/ファイル/検証フォーマット）を自動付加し、`HELIX_CODEX_NO_FOOTER=1` 時のみ無効化できること。
  - W-3: `docs/architecture/codex-review-sandbox-limitation.md` を作成し、read-only sandbox での `helix review --uncommitted` 回避と PLAN-035 への引き継ぎを明記する。
  - W-4: 2 Docs Sprint での受入条件とリンク整合が閉じている。
related: [PLAN-031, PLAN-032, PLAN-033, ADR-014, ADR-015]
---

## §1 目的

PLAN-033 の RETRO carry 3 件を本 PLAN へ集約し、PLAN-034 としてドキュメント起票する。

本 PLAN の主目的は以下の 2 つを 1 カンバンで扱うこと。

1. `cli/helix-codex` の実行監査性と結果判定可能性を上げる施策の起票（W-12）
2. `helix review --uncommitted` の read-only 依存制約を踏まえた運用ガードを明文化し、PLAN-035 へ production fix を明示的に carry すること（W-3）

## §2 前提・背景

### §2.1 carry 再集約の理由

PLAN-033 に残存した 3 件を、同一リソース改修を中心に再統合する。

- carry 3 件: `PLAN-033` retro W-0 / W-1 / W-2 / W-3
- W-12: `cli/helix-codex` の出力 tee + 委譲プロンプト共通フッタ
- W-3: `helix review --uncommitted` read-only sandbox 制約の docs-only carry

### §2.2 直近運用上の問題

1. Codex 出力の末尾表示カットで root-cause が失われる
    - `cli/helix-codex` の `run_codex_once` が子プロセス stdout をそのまま透過
    - output 尾部が切られると、`final summary` と `decision` の断片が見えず判断不能
2. 委譲プロンプト記載漏れ
    - 指示フットバックが毎回手動で入り、記載漏れや文言バラつきが発生
    - 一部タスクでは P0/P1 が見落とされる
3. `helix review --uncommitted` と read-only sandbox の衝突
    - 現状、`helix review --uncommitted` が read-only 環境で session init を失敗する実害
    - 本 PLAN では調査結果を文書化し、production fix を PLAN-035 に委譲

## §3 スコープ

### §3.1 対象

#### W-12-A: helix-codex output tee アーカイブ
- `cli/helix-codex`
- 対象関数: `run_codex_once`（`codex` の stdout 管理）
- 監査ログ出力先:
  - `.helix/audit/codex-runs/<ts>-<role>-<task-id>.log`
  - `mkdir -p .helix/audit/codex-runs` を起動時に実施
- 機能要件:
  - `> >(tee -a ...)` による標準出力複製
  - `PIPESTATUS` による子プロセス終了コード取得
  - 既存 Layer 2 / Layer 3 判定の整合維持

#### W-12-B: 委譲プロンプト共通フッタ
- `cli/helix-codex` の prompt 構築ロジック
- 共通フッタ内容（上書き禁止）:
  - `## 出力フォーマット (helix-codex 自動付加、上書き禁止)`
  - `最終 summary は 5 行以内で末尾に置く`
  - `decision (passed/failed/blocked/changes_required) は最終 summary の冒頭 1 行目に明示`
  - `変更ファイル一覧と検証結果を末尾 30 行に固定し、tail -30 で取得可能にする`
- opt-out:
  - `HELIX_CODEX_NO_FOOTER=1` で無効化（テスト用）

#### W-3: docs/architecture/codex-review-sandbox-limitation.md（実装 carry）
- `docs/architecture/codex-review-sandbox-limitation.md` 新規作成
- 内容:
  - read-only sandbox と `helix review --uncommitted` の不整合整理
  - 調査手順と短期運用ルール
  - PLAN-035 carry（production fix）引き継ぎ

### §3.2 非対象

- `cli/helix-review` の production fix (read-only sandbox 制約の根本解消) → PLAN-035 へ carry
- 本番インフラ / API / 認証 / 決済 / PII / secret/env 変更
- `state-events.md` の接続点修正
- 既存 audit log の retention/rotation 機構 (audit log は逐次追記のみ、cleanup は本 PLAN 範囲外)

## §4 方針

### §4.1 W-12 全体方針

PLAN-033 carry 2 件のうち W-12 は同一ファイル群 (`cli/helix-codex`) を編集するため 1 Sprint に集約し、衝突回避を優先する。

#### W-12-A 実装方針 (output tee アーカイブ)

- `run_codex_once` の `timeout "$TIMEOUT" "$CODEX_BIN" exec ... < /dev/null` を **process substitution** で tee する:
  ```bash
  timeout "$TIMEOUT" "$CODEX_BIN" exec ... < /dev/null > >(tee -a "$AUDIT_FILE")
  rc=$?  # process substitution は pipe ではなく、$? は codex の真の exit code を取得
  ```
- pipeline (`| tee`) ではなく process substitution を採用する理由: 既存の `${PIPESTATUS[0]}` 取得を導入せずに済み、既存の Layer 2/3 fallback 判定 (codex_exit) と整合する
- `AUDIT_FILE` は `.helix/audit/codex-runs/<ts>-<role>[-<plan-id>][-<task-id>].log` 形式
- `mkdir -p "$(dirname "$AUDIT_FILE")"` を `run_codex_once` の最初に実施
- 失敗時 (mkdir/tee エラー) は audit を諦めて従来通り stdout 透過 (silent fallback)、production への影響を排除

#### W-12-B 実装方針 (委譲プロンプト共通フッタ自動付加)

- `printf -v PROMPT '...---TASK_INPUT_END---\n'` (cli/helix-codex:967 付近) の **TASK_INPUT_END マーカーの後** に共通フッタを付加
- フッタ内容 (上書き禁止):
  ```
  ## 出力フォーマット (helix-codex 自動付加、上書き禁止)
  
  - 最終 summary は 5 行以内で末尾に置く
  - decision (passed/failed/blocked/changes_required) は最終 summary の冒頭 1 行目に必ず明示
  - 変更ファイル一覧と検証結果を末尾 30 行に固定し、tail -30 で取得可能にする
  ```
- opt-out: `HELIX_CODEX_NO_FOOTER=1` 環境変数で disable (test/dev 用)
- 既存 CODEX_DISCIPLINE_PROMPT との同居: フッタは TASK_INPUT_END の後に独立した節として置く (Codex に対する後段指示として優先度を上げる)

#### output フォーマット統一

- 監査 log は run 完了順で保存 (timestamp 命名により sort 可)
- summary は **末尾**、decision は **summary 冒頭 1 行目**
- 変更一覧と検証結果は最後の 30 行で収束 (`tail -30 "$AUDIT_FILE"` で取れる)

### §4.2 W-3 全体方針

`helix review --uncommitted` は本番 fix の範囲外（PLAN-035 carry）とし、PLAN-034 では「問題点 + 運用ルール + carry 先の明示」のみ実施する。

運用ルール:

- 原則: `helix review --uncommitted` は read-only sandbox では実行しない
- 例外: `helix review --uncommitted` を実行する場合は `sandbox=workspace-write` を利用
- 代替: `helix codex` 実行後は Opus 側（PM）経路で review を実施
- 監査観点: 調査ログ（実行コマンドと失敗コード）を後続PLANで参照できる場所へ残す

## §5 Sprint 表（PLAN-034）

### Sprint 構成（PLAN-031/032/033 形式）

- W-0: draft 起票 + TL 2 ラウンドレビュー + finalize
- W-12: helix-codex output tee + 委譲プロンプト共通フッタ（`cli/helix-codex` 集中改修）
- W-3: helix review read-only 制約調査 + docs（W-12 と編集衝突なし）
- W-4: 統合検証 + retrospective + status completed

| Sprint | 役割 / 規模 | 担当 | 主要作業 | 成功条件 | 受入テスト / 検証 |
|---|---|---|---|---|---|
| W-0 | Docs/Plan（S） | Docs（本体） | PLAN-034 起票・carry 3 件統合・WBS整備案の明文化 | PLAN 文体の統一、受入条件の整合 | plan レビュー |
| W-12 | Code / WBS axis-1（M） | SE（実装担当：別Sprint）| `cli/helix-codex` を W-12 として一体改修 | audit log + footer 付加 + exitcode 取扱いの整合 | 自動テスト/セルフテスト更新 |
| W-3 | Docs / WBS axis-2（S） | Docs（本体） | `docs/architecture/codex-review-sandbox-limitation.md` 作成 | 回避策を明文化し、PLAN-035 へ carry する | docs lint/リンク点検 |
| W-4 | Docs/Validation（S） | Docs（本体） | 受入条件、Retro、PLAN 追記 | W-12/W-3 carry が追跡可能 | W-12/W-3 条件一覧に基づく完了確認 |

### W-12（統合）

- 目的: `cli/helix-codex` 出力可観測性を上げ、委譲評価の再現性を担保する
- 主要タスク:
  - `run_codex_once` の timeout 出力を tee へ変更
  - audit log 名を `ts-role-task-id` 形式に統一
  - `PIPESTATUS` を優先して codex 真の exit code を保持
  - prompt builder に共通フッタを追記
  - `HELIX_CODEX_NO_FOOTER` の判定を追加
- 想定成果:
  - Cut された output でも末尾・head から要点取得可能
  - plan/実装レビュー時の判断材料が安定化

### W-3（調査ドキュメント）

- 目的: read-only 対応漏れを運用レベルで抑止し、PLAN-035 へ設計負債を橋渡し
- 主要タスク:
  - `cli/helix-review` 調査ログを踏まえた制約記述
  - 実害再発条件（read-only session init）を明示
  - 実行ガイドライン（workspace-write または Opus 委譲）を明記
- 想定成果:
  - 調査中止要否が定義化され、短期回避策が共有される

### W-4（統合）

- 目的: W-12 の実装 carry と W-3 docs を接続
- 主要タスク:
  - W-12 ドキュメントの受入条件再点検
  - W-3 調査結果への PLAN-035 carry 明確化
  - retro の Problem/Try 更新

## §6 受入条件（ドキュメント起票版）

### §6.1 carry 解消条件（W-12）

- W-12-A:
  - codex stdout tee の保存先が `.helix/audit/codex-runs/` 下になる
  - `codex` の実 exit code が `PIPESTATUS` ベースで追跡される
  - 長文 output の audit 証跡が残る
- W-12-B:
  - 委譲プロンプト末尾に共通フッタが標準付与される
  - 先頭行 decision、summary 5 行以内、末尾30 行固定の観測可能性が担保される
  - `HELIX_CODEX_NO_FOOTER=1` でフッタを回避可能

### §6.2 carry 解消条件（W-3）

- PLAN-033 retro W-3:
  - read-only 制約での失敗条件を明文化
  - 代替実行フローを追加
  - PLAN-035 を本 PLAN 内に参照付き carry として明記

### §6.3 総合受入条件（W-4）

- W-12 実装 + W-3 docs を統合検証し、リンク切れがないこと
- retro で Try / Problem / Keep を最新 carry 対応版に更新
- W-4 で status を `finalized` → `completed` に遷移
- pytest cli/lib/tests/ 969 passed (regression なし)、bats 339+α passed、cli/helix-test 611 passed (regression なし) を維持

## §7 リスク登録

### R-1: W-12 の並列改修で既存出力ロジックの副作用
- 内容: tee 化時にタイムアウト exit 判定が崩れ、再試行制御や監査が壊れる可能性
- 対策:
  - `PIPESTATUS` の明示取得を前提にテストケース追加
  - 既存 Layer2/Layer3 の契約ログと整合確認
  - 失敗時 fallback を維持

### R-2: フッタ運用の誤理解
- 内容: `decision` 未記載や `summary` 長文化で逆に可読性が下がる
- 対策:
  - テキスト要件（5行以内、先頭1行）を固定
  - テスト項目（ヘッダ検証）を Plan で明示

### R-3: W-3 docs-only な不整合
- 内容: 根本 fix を実装側が先送りすると再発が続く
- 対策:
  - PLAN-035 の carry 条件を文書内固定
  - retro `Try` に明示する

### R-4: `helix review` の read-only 失敗再現時の運用ルール欠落
- 内容: PM/委譲者間で実施順がブレる
- 対策:
  - docs に環境条件（sandbox/workspace-write）を明文化
  - 代替ルート（Opus 実行経路）を明示

## §8 Test Plan

PLAN-034 は W-12 (cli/helix-codex 実装) + W-3 (docs-only) を扱うため、code/docs の両方を検証する。

### §8.1 W-12 (cli/helix-codex 実装) 検証

- **静的検証**:
  - `bash -n cli/helix-codex` で構文チェック (現状 PASS、改修後も PASS 維持)
  - cli/helix-codex で動的構築する PROMPT が `helix codex --dry-run --task "..." --role pg` で出力可能なこと
- **動作検証 (Bats 追加)**:
  - W-12-A: tee で `.helix/audit/codex-runs/` に audit log が作成される (mock codex でも可)
  - W-12-A: process substitution + `$?` で codex の真の exit code が取得される (mock codex で exit 1 を返し、helix-codex の retry が発火することを確認)
  - W-12-B: dry-run で PROMPT 末尾に共通フッタが含まれる (`grep "出力フォーマット (helix-codex 自動付加" <(helix codex --dry-run ...)`)
  - W-12-B: `HELIX_CODEX_NO_FOOTER=1 helix codex --dry-run ...` でフッタが含まれない
- **regression 確認**:
  - cli/helix-test (shell-based self-test) 全 PASS
  - bats cli/tests/*.bats 全 PASS
  - pytest cli/lib/tests/ 全 PASS

### §8.2 W-3 (docs-only) 検証

- 新規 `docs/architecture/codex-review-sandbox-limitation.md` の存在確認
- Markdown 静的検証 (YAML frontmatter なし、見出し順整合)
- リンク整合 (本 PLAN と相互参照、PLAN-035 への carry 明記)

### §8.3 carry 追跡確認

- `PLAN-034` の Acceptance 4 目標の記述が W-0 → W-12 → W-3 → W-4 の順序で追跡可能
- W-12/W-3 の役割分離が `Sprint 表` と DoD で矛盾しない
- W-3 で PLAN-035 への carry 先を明記し、別 PLAN が未定義でない

### §8.4 レビュー観点

- 変更点が PLAN-033 既存 carry 2+1 件を漏れなく反映
- フォーマット（Goal/Scope/Sprint/Acceptance/Risk/Test Plan/Out of Scope/Retro Placeholder）を継承
- 記述長が 200〜350 行に収まり、読解しやすい構成である

## §9 Out of Scope

- `cli/helix-review` 本体の production fix (read-only sandbox 制約の根本解消) → PLAN-035 へ carry
- audit log の retention / rotation 機構 (本 PLAN は逐次追記のみ実装、cleanup は別 PLAN)
- 外部 API / サービス変更
- 本番システム環境変数方針変更（secret/env 追加）

(注: `cli/helix-codex` 実装本体と W-12 Bats 追加は **本 PLAN の対象** であり Out of Scope ではない。§5/§8/§10 を参照)

## §10 実装対象ファイル

### W-12 (実装)
- `cli/helix-codex`: run_codex_once の tee 化 + PROMPT 構築への共通フッタ自動付加
- `cli/tests/test_helix_codex_*.bats`: tee / footer / opt-out の Bats 追加

### W-3 (docs-only)
- `docs/architecture/codex-review-sandbox-limitation.md`: 新規作成 (read-only sandbox 制約 + 短期回避策 + PLAN-035 carry 明記)

PLAN-034 は **W-12 (実装) + W-3 (docs)** の 2 軸で完結する。W-4 (統合検証) を経て status: completed に遷移する。

## §11 関連リンク

- PLAN-031: [PLAN-031-carry-resolution.md](PLAN-031-carry-resolution.md)
- PLAN-032: [PLAN-032-helix-test-and-concurrent-resolution.md](PLAN-032-helix-test-and-concurrent-resolution.md)
- PLAN-033: [PLAN-033-drift-check-and-baseline-cleanup.md](PLAN-033-drift-check-and-baseline-cleanup.md)
- ADR-014: [docs/adr/ADR-014-roles-config-format.md](../adr/ADR-014-roles-config-format.md)
- ADR-015: [docs/adr/ADR-015-helix-v2-orchestration.md](../adr/ADR-015-helix-v2-orchestration.md)
- 運用文書: [docs/architecture/test-layout.md](../architecture/test-layout.md)
- carry 先候補: `PLAN-035`（本ドキュメント内 W-3 調査 carry）

## §12 Retro Placeholder

### Keep
- carry 統合書式を PLAN 系統で統一し、PLAN 追跡性を保ったこと
- 重要な運用制約を先にドキュメント化して実装 carry を切り出す構成
- `helix-codex` 改修と docs-only carry を parallel-safe に扱える設計

### Problem
- 長文 output の可視性欠如で TL 判定が遅延する
- レビュー前のプロンプト要求仕様が委譲ごとにバラつく
- read-only sandbox のセッション生成制約が委譲ルートで顕在化し、事前周知が不足

### Try
- W-12 実装完了時:
  - output tee で audit 取得し、`PIPESTATUS` と output 末尾固定の検証手順を PLAN-034 経由で再点検
- W-3 完了時:
  - `helix review --uncommitted` を `read-only` 禁止ルールとし、実行手順を運用に組み込む
- 受入完了時:
- PLAN-035 起票後、production fix 完了まで本 PLANに差分が残らない状態を確認

## §13 証跡（Evidence）メモ

- 受理済み情報:
  - W-3 調査により、`helix code find` 実行時に read-only session init エラーを再現
  - 運用ルールとして「read-only + review 委譲」を分岐管理する必要を確認
- 参照コマンド:
  - `helix handover status --json`（存在チェック）
  - `helix code find "PLAN-034"`（再調査）
  - `rg` で関連 PLAN 参照の存在確認

## §14 Gate 記録

- G1: 要件明確性 → PASS
- G2: 設計整合（PLAN-031/032/033 フォーマット踏襲）→ PASS
- G3: 実装順序整合（W-12 / W-3 並列、衝突なし）→ PASS
- G4: 実装凍結（W-12 完了時に passed、W-4 で確認）
- status 遷移:
  - `draft` (起票) → `finalized` (W-0 完了、TL 2 ラウンド approve 後) → `completed` (W-4 統合検証 + retro 完了後)
