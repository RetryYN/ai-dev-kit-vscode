---
plan_id: PLAN-104
title: gate test flake root cause 特定 + 修正 (test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references)
status: draft
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
  - QA (Codex gpt-5.3-codex)
agent_slots:
  - role: qa
    slot_label: "QA — 100 回ループ再現実験・root cause 分析"
  - role: se
    slot_label: "SE — fixture isolation 修正実装"
  - role: tl-advisor
    slot_label: "TL adversarial check — flake 仮説 + 修正方針 review (on-demand)"
generates:
  - artifact_type: test
    path: cli/lib/tests/test_gate_design_doc_fail_close.py
  - artifact_type: python_module
    path: cli/lib/tests/conftest.py
dependencies:
  requires:
    - PLAN-100
  blocks:
    - PLAN-102
  parent: null
related_docs:
  - cli/lib/tests/test_gate_design_doc_fail_close.py
  - .claude/hooks/pretooluse-design-doc-web-search-guard.sh
acceptance_criteria:
  - "対象 test を 100 回ループで実行し 0 fail (再現なし → close / 再現あり → root cause 特定 + 修正)"
  - "root cause が特定された場合: 修正実装 + 100 回ループ 0 fail で確認"
  - "PLAN-102 (pytest-xdist 並列化) の Sprint .4 flake check で 0 fail 確認の前提条件を満たす"
  - "helix doctor 24 pass / 0 fail / warn 維持"
  - "既存 gate test 全件 PASS 維持 (regression なし)"
---

# PLAN-104: gate test flake root cause 特定 + 修正

## L2 凍結 (ADR snapshot)

本 PLAN tree 内に L2 大局判断なし (既存 test の信頼性改善のみ)。ADR snapshot 不要。

## 背景

本 session (2026-05-23) Wave 3 で Codex se による pytest 全体 sweep (`-x` オプション) を実施した際、以下の test が **1 回 fail し、再実行で再現しない** flake が観測された。

- 対象 test: `cli/lib/tests/test_gate_design_doc_fail_close.py::test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references`
- 観測 session: Wave 3 (Codex se、pytest -x 全体 sweep)
- 再現実験: Opus が直接 5 回実行で全 PASS、flake は再現せず

**flake が残留した状態で PLAN-102 (pytest-xdist 並列化) に進むと、並列実行下での fail 頻度が上昇するリスクがある** (並列化で race condition が増幅される)。PLAN-102 Sprint .4 の前提条件として root cause を確定させる必要がある。

**対象 test の役割**: PLAN-087 の gate fail-close framework (設計 doc 作成時 Web 検索 3 query 必須ガード) が、既存 WebSearch evidence + OSS reference があれば pass できることを確認する end-to-end test。PreToolUse hook の設定ファイルおよび helix-db 状態に依存する。

## WebSearch 履歴

内部 test 改善のため WebSearch なし (PLAN-087 ガード: 内部 test / refactor は除外対象)。

## 仮説リスト

| # | 仮説 | 確認方法 |
|---|---|---|
| H1 | helix-db state 残留 (前 test の commit がクリーンアップされず残る) | HELIX_DB_PATH fixture の scope / teardown 確認 |
| H2 | SQLite WAL / journal file の flush タイミング (write 直後 read が stale data を返す) | PRAGMA journal_mode 確認 + sleep 挿入再現実験 |
| H3 | hook 設定ファイル (pretooluse-design-doc-web-search-guard.sh) の transcript scan でファイル mtime 競合 | CLAUDE_TRANSCRIPT_PATH の有無 + mtime window 確認 |
| H4 | pytest fixture setup 順序 (xdist 並列化なし serial 下でも稀に fixture order が変わる) | pytest -p no:randomly で再実行 |
| H5 | test 内の前提条件 (WebSearch evidence / OSS reference の tmp file) が稀に未生成 | fixture 内 assert で事前確認 |

## 実装計画 (Sprint .1 - .3)

### Sprint .1: 再現条件特定 (Codex qa 委譲)

**目的**: 100 回ループで fail 頻度を計測し、H1-H5 仮説を絞り込む。

実行手順:

```bash
# 100 回ループ実行
for i in $(seq 1 100); do
  python3 -m pytest cli/lib/tests/test_gate_design_doc_fail_close.py \
    -k "test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references" \
    -q 2>&1 | tail -3
done

# 並列 (xdist なし) で同時実行 (H2 / H3 検証)
python3 -m pytest cli/lib/tests/test_gate_design_doc_fail_close.py \
  -k "test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references" \
  --count=20 -q  # pytest-repeat 使用 (なければ loop)
```

確認事項:

- fail 回数 / 100 (0 回 → close、1 回以上 → Sprint .2 へ)
- fail 時の helix-db HELIX_DB_PATH が tmp_path 化されているか
- fixture scope (function / session) の確認 (`cli/lib/tests/conftest.py` Read)
- 対象 test の setup 内容確認 (`cli/lib/tests/test_gate_design_doc_fail_close.py` Read)

Sprint Exit 条件:

- 100 回ループ結果 (fail 件数) を記録
- fail 0 → Sprint .2 は skip、Sprint .3 で close 記録のみ
- fail 1+ → H1-H5 のうち絞り込んだ仮説を記録して Sprint .2 へ

### Sprint .2: root cause 分析 (Codex qa 委譲、fail ありの場合のみ)

**前提**: Sprint .1 で fail 1+ 件確認された場合のみ実施。

確認項目:

- `cli/lib/tests/conftest.py` の HELIX_DB_PATH fixture teardown が全 case で動作するか
- `cli/lib/helix_db.py` の SQLite 接続が close されているか (connection leak)
- 対象 test 内で hook 設定を参照する箇所 (`HELIX_HOME` / WebSearch evidence path) の冪等性
- 並行実行シミュレーション (threading.Thread で 2 instance 同時起動) で fail 再現試行

分析結果:

- root cause 1 件に絞り込み、修正方針を確定する
- tl-advisor に分析結果を投げ、adversarial check を受ける (on-demand)

Sprint Exit 条件:

- root cause 1 件特定 + 修正方針合意
- tl-advisor check 完了 (または skip 理由記録)

### Sprint .3: 修正実装 + 検証 (Codex se 委譲、fail ありの場合のみ)

**前提**: Sprint .2 で root cause + 修正方針確定後に着手。

修正候補 (Sprint .2 結果で絞り込む):

- H1 対応: `cli/lib/tests/conftest.py` に teardown 強化 (DB close + tmp file 削除)
- H2 対応: test 内で write 後に `conn.execute("PRAGMA wal_checkpoint(FULL)")` 追加
- H3 対応: CLAUDE_TRANSCRIPT_PATH を test fixture 内で明示的に unset
- H4 対応: test に `@pytest.mark.order` で実行順序固定
- H5 対応: fixture 内 assert で前提条件 (evidence file 存在) を事前確認

mandatory in sprint:

- [ ] `python3 -m py_compile cli/lib/tests/test_gate_design_doc_fail_close.py`
- [ ] `python3 -m py_compile cli/lib/tests/conftest.py` (変更時)
- [ ] 対象 test 単体実行 PASS
- [ ] 100 回ループで 0 fail 確認
- [ ] 全体 gate test PASS (`python3 -m pytest cli/lib/tests/test_gate_design_doc_fail_close.py -v`)
- [ ] セルフレビュー (Opus)

Sprint Exit 条件:

- 100 回ループで 0 fail (修正なし close / 修正後 0 fail どちらも OK)
- PLAN-102 Sprint .4 の前提条件を満たす旨を carry note に記録

## DoD (Definition of Done)

- [ ] 対象 test の 100 回ループで 0 fail (再現なし close または修正後 0 fail)
- [ ] root cause が特定された場合: fix commit + 修正内容の記録
- [ ] root cause が特定されなかった場合 (100 回 0 fail): "intermittent external state" として close 記録
- [ ] PLAN-102 Sprint .4 の flake check 前提条件を carry note に明記
- [ ] helix doctor 24 pass / 0 fail / warn 維持
- [ ] regression: 既存 gate test 全件 PASS

## carry / 学び (起票時記録)

- **並列化リスク**: xdist 並列下では H1 (state 残留) / H2 (WAL flush) の影響が増幅される。本 PLAN で serial 下の flake を確定してから PLAN-102 に接続する。
- **100 回 0 fail でも close は early**: PLAN-102 Sprint .4 の並列下 flake check を最終判定とし、serial 下 0 fail は中間 milestone 扱いとする。

## 関連 reference

- PLAN-102 (pytest-xdist 並列化、本 PLAN が blocks する)
- PLAN-087 (Web 検索ガード framework、対象 test の基盤)
- PLAN-089 (gate fail-close、対象 test が検証する gate)
- [[feedback_pytest_collection_stop_false_fail]] (本 session で conftest.py 追加済)
- [[feedback_codex_report_section_loss]] (Codex C が本 flake を報告した際の Codex レポート制限)
