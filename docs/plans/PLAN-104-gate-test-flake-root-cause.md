---
plan_id: PLAN-104
title: gate test flake root cause 特定 + 修正 (test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references)
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
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

## Sprint .1 結果 (2026-05-23 実施、root cause 確定)

100 回ループ実行: **1 / 100 fail 再現** (run-58)。verbose loop 150 回追試で **3 fail 捕獲** (run 28 / 83 / 121、約 2% rate)。前 session uncommitted diff (Codex se grep wrapper + HELIX_PROJECT_ROOT init) では root cause に届かず、revert 済。

### 確定した fail pattern (3 traceback 共通)

- exit code: **141 (SIGPIPE)**
- stderr: `level=warn event=stale_lock_released lock_path=/home/tenni/ai-dev-kit-vscode/.helix/locks/helix-db.lock previous_pid=XXX current_pid=YYY`
- stdout: `=== G2: G2 ===\nSKIP: legacy PLAN (plan_not_found)\n...\n[helix-gate] vmodel_lint auto-run: G2 (PLAN-075 V-model 4 artifact)\n  WARN [vmodel_lint] incomplete=63 PLAN (V-model 4 artifact 不完全、advisory)\n[⚠] PLAN-004: ...\n[⚠] PLAN-005: ...\n[⚠] PLAN-006: ...\n[⚠] PLAN-007: ...\n[⚠] PLAN-008: ...\n` (5 PLAN で切断、incomplete=63 とミスマッチ)

### root cause 2 系統

**R-1: vmodel_lint が本番 docs/plans/ をスキャン (test isolation 破壊)**

- stdout が `[⚠] PLAN-004 〜 PLAN-008` を列挙 = **HELIX_HOME (= /home/tenni/ai-dev-kit-vscode) 配下の本番 docs/plans/** を走査している (tmp_path/docs/plans/PLAN-323-test.md ではない)
- helix-gate の auto-run detector / vmodel_lint logic が PROJECT_ROOT (env) ではなく HELIX_HOME (script の `$SCRIPT_DIR/..`) を docs/plans の起点にしている疑い
- 検証: `incomplete=63 PLAN` は本番 PLAN-001〜PLAN-221 のうち 4 artifact 不完全な PLAN 数と一致するはず (要確認)

**R-2: vmodel_lint pipeline 内のどこかで SIGPIPE 発生**

- stdout が 5 PLAN で切断、incomplete=63 とミスマッチ
- subprocess.run(capture_output=True) で全 read されるはずなのに途中切断 → helix-gate **内部の pipeline** (例: `python ... | grep ... | head ...`) で head などが先に close → 上流に SIGPIPE
- 1/100 で発生 = race condition (buffer fill timing 依存)

**R-3 (関連): concurrent_lock._resolve_lock_dir の fallback**

- `cli/lib/concurrent_lock.py:26-37` の `_resolve_lock_dir()`:
  ```python
  project_root = os.environ.get("HELIX_PROJECT_ROOT", "").strip()
  if project_root and helix_home and Path.cwd().resolve() == Path(helix_home).resolve():
      return Path(project_root) / DEFAULT_LOCK_DIR
  if project_root and Path.cwd().resolve() == Path(project_root).resolve():
      return Path(project_root) / DEFAULT_LOCK_DIR
  return DEFAULT_LOCK_DIR  # ← cwd が project_root 完全一致しないと relative path に fallback
  ```
- cwd が project_root の subdirectory または symlink resolve で外れたとき、本番 `.helix/locks/` を奪う
- ただし R-1 が解消すれば test stdout に「本番 PLAN」が出ないため、まずは R-1 を直す

## Sprint .2 完遂結果 (2026-05-23 commit c007851)

### R-1/R-2/R-3 全 fix 実装済 (commit c007851)

- **R-1**: `cli/lib/vmodel_lint.py` HELIX_PROJECT_ROOT env 優先化 (HELIX_ROOT fallback 保持)
- **R-2**: `cli/helix-gate` line 1479 `grep|head -5` → `awk '/^\[⚠\]/{n++;if(n<=5)print}'` (SIGPIPE 回避)
- **R-3**: `cli/lib/concurrent_lock.py` `_resolve_lock_dir()` env 優先化 (cwd 判定除去)

### 検証結果

**単独実行 (本 wave A)**: 100/100 PASS ✓ (R-1/R-2/R-3 fix 直後の commit c007851)
**並列実行下 (本 wave B、pytest gate sweep 219 test 同時走行)**: **5/60 fail (8.3%)** ← R-4 新 root cause 存在

### R-4 root cause 確定 + fix (2026-05-23 本 wave、Sprint .3)

並列 stress test (100 ループ + pytest gate sweep 同時走行) で **traceback 詳細捕獲**:

```
TimeoutError: lock not acquired within 5.0s: helix-db
  File "cli/lib/concurrent_lock.py:59", in _flock_with_timeout
    raise TimeoutError(f"lock not acquired within {timeout:.1f}s: {name}") from exc
```

#### root cause

test の `_init_project()` 内で `helix_db.init_db()` を呼ぶと、`_write_connection` 経由で `file_lock(HELIX_DB_LOCK_NAME)` が取得される (`HELIX_DB_LOCK_NAME = "helix-db"`)。

**問題**: test 本体 (subprocess ではなく test process 自身) で `helix_db.init_db()` を呼ぶ瞬間、`HELIX_PROJECT_ROOT` env が **未設定**。R-3 fix で env 優先化したが env が無いと relative `.helix/locks` に fallback → cwd ベース resolve → **本番 `.helix/locks/helix-db.lock`** を奪取。

並列 pytest 実行で複数 test process が同じ本番 lock を取り合い、1 process だけ取得、他は 5s timeout で fail。

#### R-4 fix (commit 本 wave)

`test_helix_gate_design_doc_fail_close.py` に `_init_helix_db_for_project()` helper を追加し、`helix_db.init_db()` 呼び出し前後に `HELIX_PROJECT_ROOT` を tmp_path に scope set する:

```python
def _init_helix_db_for_project(project_root: Path) -> None:
    previous_project_root = os.environ.get("HELIX_PROJECT_ROOT")
    try:
        os.environ["HELIX_PROJECT_ROOT"] = str(project_root)
        helix_db.init_db(str(project_root / ".helix" / "helix.db"))
    finally:
        if previous_project_root is None:
            os.environ.pop("HELIX_PROJECT_ROOT", None)
        else:
            os.environ["HELIX_PROJECT_ROOT"] = previous_project_root
```

前 session Codex se が同等修正を施したが、無効な grep wrapper (R-2 違いに対処) と一緒に commit され、root cause 違いで全体 revert された。本 fix は **env scope だけ復活** させる清浄な実装。

#### 検証 (Sprint .3 完遂)

- 単独 100 ループ: **100/100 PASS** ✓
- 並列 100 ループ + pytest gate sweep 219 test 同時実行: **100/100 PASS** ✓ (R-4 fix 前は 5/60 fail)

PLAN-102 (pytest-xdist 並列化) は本 fix で **前提条件 satisfy 完了**。次 session で着手可能。

## carry / 学び

- **並列化リスク**: PLAN-102 (xdist) に進む前に R-1 / R-2 解消必須。並列下では fail rate 上昇予想
- **前 session Codex se 修正の有効性なし**: grep SIGPIPE wrapper は grep 単体の exit code 緩和、helix-gate 内部 pipeline の SIGPIPE は別問題。HELIX_PROJECT_ROOT init helper も lock path に届かない

## 関連 reference

- PLAN-102 (pytest-xdist 並列化、本 PLAN が blocks する)
- PLAN-087 (Web 検索ガード framework、対象 test の基盤)
- PLAN-089 (gate fail-close、対象 test が検証する gate)
- [[feedback_pytest_collection_stop_false_fail]] (本 session で conftest.py 追加済)
- [[feedback_codex_report_section_loss]] (Codex C が本 flake を報告した際の Codex レポート制限)
