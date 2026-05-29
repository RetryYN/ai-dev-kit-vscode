---
doc_id: l5-helix-workflows-cross-cutting-design
title: "HELIX-workflows V2 横断的関心事設計 (cross-cutting concerns, IEEE1016 Patterns use / arc42 §8)"
status: frozen
process_layer: L5
doc_type: cross_cutting_design
parent_plan: L5-helix-workflows-外部IF詳細設計plan
pairs_design: docs/v2/L4-architecture/helix-workflows-functional-design.md
pairs_test_design: docs/v2/L8-test-design/helix-workflows-integration-test-design.md  # IT-IF IF結合 (V-model L5↔L8 正対)
industry_standards:
  - "IEEE Std 1016-2009 (Software Design Descriptions): Patterns use viewpoint"
  - "arc42 §8 Cross-cutting Concepts"
---

> (recovery-2026-05-30 独立化: interface-detailed-design §14 から正本移設)

# L5 横断的関心事設計 (cross-cutting concerns)

- 文書名: `docs/v2/L5-internal-design/helix-workflows-cross-cutting-design.md`
- 対象版: HELIX-workflows V2
- 作成日: 2026-05-30 (recovery-2026-05-30 独立化)
- 出典元: `helix-workflows-interface-detailed-design.md §14` から正本移設
- 目的: IEEE Std 1016-2009 Patterns use viewpoint / arc42 §8 に対応する横断的関心事の集約設計。ロギング / エラー伝播 / トランザクション境界 / セキュリティ横断 の 4 関心事が「どのモジュール群に横断的に効くか」を定義する

---

## §0 概要 (IEEE1016 Patterns use viewpoint + arc42§8 準拠)

IEEE Std 1016-2009 の **Patterns use viewpoint** は、設計パターンを識別し、設計実体との対応を記述する責務を持つ。arc42 §8 **Cross-cutting Concepts** は、アーキテクチャを横断して一貫して適用すべき方針・規約を一箇所に集約する章である。

本設計書はこの 2 規格の交差点に位置する。HELIX-workflows V2 の全モジュールに共通適用される横断的関心事を「どのモジュール群」「どのルール」「どの参照先」という 3 軸で記述する。

### 位置付け

- **上位設計 (L4)**: `helix-workflows-functional-design.md` が機能分解と機能間インタフェース方針を定義
- **本文書 (L5 横断)**: 全機能に共通適用される横断方針を集約 (本文書が正本)
- **IF詳細設計 (L5)**: `helix-workflows-interface-detailed-design.md` が CLI/hook の個別契約を定義。§14 は本文書へのポインタ節
- **結合テスト設計 (L8)**: `helix-workflows-integration-test-design.md` が本文書の横断方針を検証する

### 独立化の背景

`interface-detailed-design.md §14` として追補されていたが、IEEE1016 Patterns use viewpoint と arc42 §8 はそれぞれ独立した設計ビューを要求する。横断的関心事はインタフェース詳細設計とは異なる関心軸であるため、SSoT を分離文書として独立させた (L5-06 欠落対応、recovery-2026-05-30)。

---

## §1 横断的関心事サマリ表

| 関心事 | 集約方針 | 適用モジュール群 | 参照 §/節 |
|---|---|---|---|
| ロギング | helix.db event_log への構造化記録を全 hook・CLI コマンドが共通して行う | cli/lib/*.py 全体 / cli/helix-* 全体 | §2 |
| エラー伝播 | exit code 体系 (0/1/2/1001〜1060) の層をまたぐ伝播ルール | cli/helix-* シェル → cli/lib/plan_*.py → helix.db | §3 |
| トランザクション境界 | SQLite write の atomic 単位を compatibility_adapter.write_connection に統一 | cli/lib/compatibility_adapter.py / plan_registry.py / discovery_migrate.py | §4 |
| セキュリティ横断 | hook guard (fail-close) と model family 検証の適用方針。L4-09 脅威分析 (双方向 trace: system-architecture.md §14 追補予定) と対応 | .claude/hooks/pretooluse-agent-guard.sh / cli/helix-codex / cli/helix-claude | §5 |

---

## §2 ロギング方針 (helix.db event_log 構造化記録)

- **方針**: 全 hook および副作用を持つ CLI コマンドは `helix.db` の `event_log` テーブルへ構造化レコードを記録する。
- **必須フィールド**: `session_id`, `event_type`, `timestamp`, `actor` (CLI コマンド名 or hook 名), `result` (`pass`/`fail`/`skip`), `exit_code`
- **任意フィールド**: `payload` (JSON)、`error_code`、`duration_ms`
- **適用モジュール**: `cli/lib/plan_registry.py` / `cli/lib/compatibility_adapter.py` / `cli/lib/learning_engine.py` / `.claude/hooks/*.sh`
- **除外**: `--dry-run` フラグが付いた場合、event_log への書き込みは行わない (dry run は副作用ゼロ原則)
- **監査連携**: `interface-detailed-design.md §10` の各 hook の `audit log: role_audit + event_log` 記述はこの方針の個別適用である。`role_audit` は role の使用記録、`event_log` はイベント全般のタイムラインを担う。

---

## §3 エラー伝播ルール (exit code の層をまたぐ伝播)

exit code 体系は `edge-case-design.md §0.2` で定義された値を L5 IF 層で伝播する。

| exit code | 意味 | 伝播ルール |
|---|---|---|
| 0 | 正常終了 | 上位シェルに透過伝播 |
| 1 | 一般エラー (user error, 入力不正) | hook が 1 を返した場合、CLI は `WARN` に降格して続行可 (fail-open hook に限る) |
| 2 | 重大エラー / fail-close 強制 | hook が 2 を返した場合、CLI は即座に中断。上位シェルは 2 を透過伝播する |
| 1001 | plan registry エラー | CLI レイヤーで `ERROR(DOC-1001)` を stdout に出力してから exit 2 に変換 |
| 1010 | state 整合エラー | 同上。recovery 系コマンドが受け取った場合は recovery plan への自動遷移を検討 |
| 1020 | budget/homeostasis 警告 | fail-open。`issues[severity=warning]` を付与して続行 |
| 1030 | mode 遷移不正 | fail-close。CLI は現在 mode を維持して exit 2 |
| 1040 〜 1059 | 各 F 機能固有エラー | `ERROR(DOC-1040〜1059)` を stdout + exit 2 |
| 1060 | incident 緊急エラー | fail-close。incident log を書いてから exit 2 |

- **シェル → Python 呼び出し境界**: `cli/helix-*` bash スクリプトは Python helper の exit code をそのまま `exit $?` で透過する。変換は行わない。
- **Python 内部例外**: `cli/lib/*.py` では `SystemExit(code)` を用い、`raise Exception` をスタックトレースとして stdout/stderr に出力しない (ユーザー向けには `ERROR(...)` メッセージのみ)。
- **既存 interface-detailed §11 との関係**: §11 は `fail-close/fail-open の選択基準` と `timeout/retry 共通規約` を定義する。本節 §3 はその「層間伝播の具体ルール」として補完する (置換ではない)。

---

## §4 トランザクション境界 (SQLite write の atomic 単位)

- **統一接続口**: `cli/lib/compatibility_adapter.py` の `write_connection()` コンテキストマネージャが SQLite の **1 トランザクション = 1 write_connection ブロック** を定義する。
- **commit 単位**:
  - 1 CLI コマンドの副作用全体 → 1 トランザクション (例: `helix plan update` は plan_registry + event_log を 1 commit)
  - hook の event_log 書き込み → 独立トランザクション (hook は短命、メイン処理と分離)
  - migration スクリプト → 1 migration step = 1 トランザクション (途中失敗でロールバック)
- **並行書き込み**: `helix workspace` による並列ワークツリー環境では、各ワーカーが独立 DB ファイルを持つ (isolation 方針は ADR-040 §DB-Isolation を参照)。メイン DB への write は `helix workspace sync` 時に serialize する。
- **read-only 操作**: `--json`, `--dry-run`, `helix doctor`, `helix status` 等の read-only コマンドは `write_connection` を使用しない。誤用検出は `compatibility_adapter` の write guard で fail-close。
- **適用モジュール**: `cli/lib/compatibility_adapter.py` / `cli/lib/plan_registry.py` / `cli/lib/discovery_migrate.py` / `cli/lib/helix_db.py`

---

## §5 セキュリティ横断方針 (hook guard / fail-close の適用)

本節は hook guard と model family 検証の横断方針をまとめる。L4-09 脅威分析節 (system-architecture.md §14 追補予定、双方向 trace: L4-09) との対応を示す。

| セキュリティ機能 | 適用場所 | 方針 | fail-close / fail-open |
|---|---|---|---|
| hook guard (pretooluse-agent-guard) | `.claude/hooks/pretooluse-agent-guard.sh` | subagent_type が許可 12 種 (PMO 9 + PdM 3) 外は exit 2 でブロック | **fail-close** |
| model family 検証 | 同上 | frontmatter と model family 不一致の場合 exit 2 でブロック (想定外 Opus 発火防止) | **fail-close** |
| plan lint / commit lint | `.claude/hooks/pre-commit` (interface-detailed §10.6) | .md/.yaml の構造不整合は exit 2。carry note は pass | **fail-close** |
| PreCompact 前状態保全 | `sessionstart-harness-summary.sh` (interface-detailed §10.2/§10.4) | 未保存 L2/L3/ADR 判断がある場合のみ decision:block。常用禁止 | **条件付き fail-close** |
| DB write guard | `cli/lib/compatibility_adapter.py` | read-only コマンドからの write_connection 呼び出しを検出して fail-close | **fail-close** |

- **fail-close の基準統一**: セキュリティ関連 (認証・モデル family・artifact 破損・重要状態遷移) は `interface-detailed §11` の方針に従い fail-close とする。
- **fail-open の範囲**: 監査系 hook (event_log 書き込み遅延、metrics_log 欠損) は fail-open とし `issues[severity=warning]` を付与する。
- **双方向 trace**: 本節の hook guard 方針は L4-09 脅威分析節 (system-architecture.md、recovery-2026-05-30 で追補予定) と対応する。L4-09 が STRIDE 観点の脅威一覧を持ち、本節 §5 がその L5 IF レベルの対策方針を記述する関係。
