---
plan_id: PLAN-136
title: "PLAN-136: helix log report structured view (--json / --filter 拡張)"
status: draft
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: pmo-project-scout
    slot_label: "PMO — Sprint .1 helix-log-report / helix_db.py の既存 log 出力構造を軽量スキャン"
  - role: se
    slot_label: "SE — Sprint .2 --json / --filter / --since オプション実装 + Python module 拡張"
  - role: qa
    slot_label: "QA — Sprint .3 pytest unit test 追加 + bats smoke test"
generates:
  - artifact_type: cli_extension
    path: cli/helix-log-report
  - artifact_type: python_module
    path: cli/lib/log_report.py
  - artifact_type: test
    path: cli/lib/tests/test_log_report.py
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr: []
related_plans:
  - PLAN-124
related_docs:
  - docs/commands/index.md
  - cli/lib/helix_db.py
acceptance_criteria:
  - "`helix log report --json` が全 event を JSON Lines 形式で stdout 出力する"
  - "`helix log report --filter event_type=hook_fired` で hook_fired event のみが出力される"
  - "`helix log report --since 2026-05-01` で指定日以降の event のみが出力される"
  - "`helix log report --filter` と `--since` を組み合わせて AND 絞り込みができる"
  - "`helix log report --json --filter role=se` で role=se の event が JSON Lines で出力される"
  - "`python3 -m py_compile cli/lib/log_report.py` PASS"
  - "`helix doctor fail 0 件維持`"
---

# PLAN-136: helix log report structured view (--json / --filter 拡張)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内に L2 大局判断なし。既存 CLI への filter / JSON 出力オプション追加。ADR snapshot 不要。

判断根拠: 新技術採用なし。既存 `helix log report` の出力形式拡張のみ。JSON Lines (NDJSON) は既存 helix.db 出力形式と整合する既知形式。

## 背景

`helix log report` は現在 text 形式の要約出力のみ。以下の場面で machine-readable な出力が必要になっている:

1. **PMO 状況把握**: pmo-sonnet が helix.db のイベント状況を把握するとき、text を grep するより `--json | jq` の方が高速かつ正確
2. **helix doctor 連携**: `helix doctor` が log イベントを参照するとき (例: check_subagent_phase で subagent 呼び出し履歴を確認するとき)
3. **helix metrics 連携**: PLAN-124 で標準化された `--json` 出力形式と揃えることで、外部スクリプトから解析可能にする

### WebSearch skip 根拠

本 PLAN は既存 CLI への filter / JSON 出力追加。新技術採用なし。PLAN-087 ガードレール「設計 doc 新規起票・大幅 scope 変更時」に非該当。**WebSearch skip: 既存 CLI 拡張のみ、外部標準への新規依存なし**。

related_plans の PLAN-124 で `--json` 出力の標準形式が既に確立されているため、踏襲する。

## 詳細設計

### --json 出力フォーマット (JSON Lines / NDJSON)

```jsonl
{"ts": "2026-05-23T10:00:00Z", "event_type": "hook_fired", "role": "se", "plan_id": "PLAN-135", "detail": "posttooluse-helix-job-enqueue fired"}
{"ts": "2026-05-23T10:01:00Z", "event_type": "skill_used", "role": "pmo-sonnet", "plan_id": null, "detail": "skill=documentation-and-adrs"}
```

- 1 行 1 event (JSON Lines 形式、`jq` で処理可能)
- timestamp は ISO 8601 UTC
- `event_type` は helix.db の event_type カラムの値をそのまま使用
- `null` は JSON null (Python `None` を json.dumps で変換)

### --filter オプション設計

`--filter key=value` 形式で AND 絞り込み:

```bash
helix log report --filter event_type=hook_fired
helix log report --filter role=se
helix log report --filter plan_id=PLAN-135
helix log report --filter event_type=hook_fired --filter role=se  # AND 条件
```

対応 filter key: `event_type` / `role` / `plan_id` / `session_id`

未知の key を指定した場合は warning を stderr に出力し、filter を無視して全件返す。

### --since オプション設計

```bash
helix log report --since 2026-05-01          # ISO 8601 date (YYYY-MM-DD)
helix log report --since 2026-05-01T00:00:00Z  # ISO 8601 datetime
```

- helix.db の `ts` カラムと比較 (SQLite `WHERE ts >= ?`)
- 不正な日付形式の場合は stderr にエラーを出力して exit 1

### 既存出力との併用

`--json` なしの場合は既存 text 出力を維持する (後方互換)。

```bash
helix log report            # 既存 text 出力 (変更なし)
helix log report --json     # JSON Lines 出力 (追加)
```

## 実装計画

### Sprint .1: 既存実装スキャン (pmo-project-scout 委譲)

**Entry**: なし

実施内容:

1. `cli/helix-log-report` (bash) の現行実装を軽量スキャン
2. `cli/lib/helix_db.py` の log 関連 query (get_events / get_log 等) を確認
3. `cli/lib/log_report.py` の存在確認 (存在しない場合は Sprint .2 で新規作成)
4. helix.db の event テーブル schema を確認 (カラム: ts / event_type / role / plan_id / session_id / detail 等)

Sprint .1 完了条件:

- 既存実装の構造が把握されている (bash CLI + Python helper の分担)
- event テーブルの実際のカラム名が確定している

### Sprint .2: --json / --filter / --since 実装 (se 委譲)

**Entry**: Sprint .1 完了

実施内容:

1. `cli/lib/log_report.py` 拡張 (存在しない場合は新規作成):
   - `query_events(filters: dict, since: str | None) -> list[dict]` 関数追加
   - `format_json_lines(events: list[dict]) -> str` 関数追加
   - helix.db から event を取得し、filter / since 条件で絞り込み
2. `cli/helix-log-report` bash 拡張:
   - `--json` / `--filter key=value` / `--since YYYY-MM-DD` オプション追加
   - オプション解析後 Python helper を呼び出す

mandatory:

- `python3 -m py_compile cli/lib/log_report.py` PASS
- `bash -n cli/helix-log-report` PASS

Sprint .2 完了条件:

- `helix log report --json` が JSON Lines を stdout に出力する
- `helix log report --filter event_type=hook_fired` が絞り込み出力する
- `helix log report --since 2026-05-01` が日付絞り込みをする

### Sprint .3: pytest unit test + bats smoke test (qa 委譲)

**Entry**: Sprint .2 完了

実施内容:

1. `cli/lib/tests/test_log_report.py` 新規作成:
   - test_query_events_no_filter: filter なしで全件取得
   - test_query_events_filter_event_type: event_type で絞り込み
   - test_query_events_filter_since: since で日付絞り込み
   - test_query_events_combined: filter + since の AND 条件
   - test_format_json_lines: JSON Lines 形式確認 (各行が valid JSON)
   - test_query_events_unknown_filter_key: 未知 key で stderr warning + 全件返却
2. bats smoke test (既存 `cli/helix-log-report` bats がある場合は追記、なければ `cli/tests/test_log_report.bats` 新規):
   - smoke: `helix log report --json` が exit 0 で JSON Lines を出力する
   - smoke: `helix log report --filter event_type=UNKNOWN_TYPE` が空の JSON Lines を出力する

Sprint .3 完了条件:

- `pytest cli/lib/tests/test_log_report.py -q` 全 PASS (6 件)
- bats smoke 全 PASS
- `helix doctor fail 0 件維持`

## V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-136-helix-log-report-structured.md |
| ② 実装コード | Sprint .2 で起票 | cli/helix-log-report / cli/lib/log_report.py |
| ③ テスト設計 | Sprint .3 entry で策定 | (Sprint .3 内で本 PLAN §テスト設計に追記) |
| ④ テストコード | Sprint .3 で実装 | cli/lib/tests/test_log_report.py |

**双方向 reference**:
- 本 PLAN → 実装コード: generates に `cli/helix-log-report` / `cli/lib/log_report.py` を明示
- 実装コード → 本 PLAN: `log_report.py` module docstring に「設計: PLAN-136」を追記
- 本 PLAN → テストコード: generates に `cli/lib/tests/test_log_report.py` を明示
- テストコード → 本 PLAN: test file docstring に「DoD 検証: PLAN-136 §acceptance_criteria」を追記

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/log_report.py` PASS
- [ ] `bash -n cli/helix-log-report` PASS
- [ ] `pytest cli/lib/tests/test_log_report.py -q` 全 PASS
- [ ] bats smoke PASS
- [ ] `helix doctor fail 0 件維持`
- [ ] セルフレビュー (Opus)

## DoD (Definition of Done)

- [ ] `helix log report --json` が JSON Lines 出力 (1 行 1 event)
- [ ] `helix log report --filter event_type=hook_fired` で絞り込み動作
- [ ] `helix log report --since 2026-05-01` で日付絞り込み動作
- [ ] `--json` + `--filter` + `--since` の組み合わせが動作する
- [ ] 既存 `helix log report` (text 出力) が後方互換で維持されている
- [ ] `pytest cli/lib/tests/test_log_report.py` 6 件全 PASS
- [ ] `python3 -m py_compile cli/lib/log_report.py` PASS
- [ ] `helix doctor fail 0 件維持`

## carry / リスク

| リスク | 緩和策 |
|---|---|
| helix.db event テーブルの実際スキーマが設計と異なる | Sprint .1 で実テーブル確認を必須とし、Sprint .2 前に filter key を確定する |
| `cli/lib/log_report.py` が未存在の場合の新規作成コスト | Sprint .1 で存在確認。未存在なら Sprint .2 で新規作成 (S size の変更なし) |
| `--filter` の複数指定が bash option parser で正しく動かない | Sprint .2 で `while [[ "$1" == --* ]]` ループで複数 --filter を配列に積む実装にする |
| JSON Lines の改行コード (CRLF vs LF) | Python `json.dumps() + "\n"` で LF 固定にする |

## 関連 reference

- PLAN-124 (helix doctor --json output 標準化、本 PLAN の --json フォーマット設計の根拠)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- cli/lib/helix_db.py (helix.db access layer の正本)
- docs/commands/index.md (helix log report コマンド定義の正本)
