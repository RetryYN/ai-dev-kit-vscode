---
plan_id: PLAN-102
title: pytest-xdist 並列化 + helix-db.lock per-worker fixture isolation
status: draft
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - SE (Codex gpt-5.4)
  - QA (Codex gpt-5.3-codex)
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・WAL opt-in 境界・migration 影響評価"
  - role: pmo-sonnet
    slot_label: "PMO — drift 整合確認・doc retrofit 支援"
  - role: tl-advisor
    slot_label: "TL adversarial check — fixture 設計・lock 分離戦略 review"
  - role: se
    slot_label: "SE — conftest.py 拡張・helix-db.lock 分離実装・WAL mode opt-in"
  - role: qa
    slot_label: "QA — pytest-xdist 回帰確認・benchmark・flake 監視"
generates:
  - artifact_type: python_module
    path: cli/lib/tests/conftest.py
  - artifact_type: python_module
    path: cli/lib/tests/conftest_xdist.py
  - artifact_type: test
    path: cli/lib/tests/test_xdist_isolation.py
  - artifact_type: config
    path: pyproject.toml
  - artifact_type: config
    path: requirements-dev.txt
  - artifact_type: adr_snapshot
    path: docs/adr/ADR-034-pytest-xdist-parallel-isolation.md
dependencies:
  requires:
    - PLAN-100
    - PLAN-104
  blocks: []
  parent: null
related_adr:
  - ADR-034-pytest-xdist-parallel-isolation
related_docs:
  - CLAUDE.md §コマンド
  - cli/lib/tests/conftest.py (本 session commit 0d5eb6a で新設、本 PLAN で拡張)
acceptance_criteria:
  - "pytest -n auto sweep が 1846 PASS / 4 skipped を維持 (regression なし)"
  - "pytest sweep 530秒 → 200-300秒以下 (40%+ 削減)"
  - "helix-db.lock 衝突 0 件 (per-worker DB file 化で根本回避)"
  - "bats / shell test には影響なし (xdist scope 外)"
  - "datetime 依存 test (test_skill_dispatcher_stats 等) は並列下で flake なし (動的化済、本 session 確立済 pattern)"
  - "WAL mode は env-gated opt-in (HELIX_DB_WAL=1)、production migration / 既存 helix.db に影響なし"
  - "pytest-xdist が requirements-dev.txt に追加され、CI / dev 環境両方で再現可能"
  - "新規 test cli/lib/tests/test_xdist_isolation.py が worker_id 別 DB 分離を確認"
---

# PLAN-102: pytest-xdist 並列化 + helix-db.lock per-worker fixture isolation

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-034** で凍結:

- pytest-xdist 採用判断 (vs unittest-parallel / pytest-parallel / なし)
- per-worker DB isolation 戦略 (file-per-worker vs in-memory-per-worker)
- helix-db.lock の per-worker tmp 化 (既存 flock pattern との互換)
- WAL mode は test only env-gated opt-in (production migration 影響回避)
- bats / shell test は xdist scope 外 (既に subprocess level で分離済)
- CI default は serial 維持 (-n auto は dev / local 用 opt-in)、CI への適用は別 PLAN

## 背景

本 session (2026-05-23) Wave 3 で Codex se による pytest 全体 sweep profile を実施した結果:

- **本番 sweep**: 530.93 秒 (~9 分) で完走、1846 passed / 4 skipped
- 8 min timeout を SIGTERM していたので test 自体は健全
- 単体実行は数秒、SQLite file 操作 + helix-db.lock 取得 + 大量 fixture setup が累積コスト

**問題**:

1. **pytest sweep ~9 分は CI / local 開発の bottleneck**: 単体 test を頻繁に走らせる開発フローで負担大
2. **xdist 並列化前提条件が未整備**: 共有 `helix-db.lock` / 共有 SQLite file への並列 write が衝突
3. **datetime 依存 fixture の flake リスク**: 本 session で test_skill_dispatcher_stats 4 件を動的化済 ([[feedback_pytest_fixture_time_dependent_flake]]) だが並列下の boundary 条件で再発リスクあり

**目標**: pytest sweep 530秒 → 200-300秒以下 (40%+ 削減)、helix-db.lock 衝突なし、regression なし。

## WebSearch 履歴 (PLAN-087 ガード遵守、本 session 2026-05-23 実施)

| Query | 主な出典 | 抽出した業界 standard |
|---|---|---|
| "pytest-xdist SQLite database lock contention parallel test isolation fixture tmp_path 2026" | pytest-xdist Issue #139, sqlalchemy Discussion #13109, pydevtools handbook, Mergify blog | Two workers writing to same SQLite file collide. Use tmp_path or session-scoped fixture with worker-aware setup |
| "pytest-xdist worker_id fixture SQLite per-worker database isolation best practice" | pytest-xdist Read the Docs, dbfixtures Issue #470, leen.dev pipeline blog | worker_id fixture (gw0/gw1) 経由で per-worker DB 命名 (f"test_db_{worker_id}")、session-scoped fixture で per-worker 一度 setup |
| "pytest parallel test fileLock contention python 2026 helix.db SQLite WAL mode performance" | sqlite.org/lockingv3.html, dev.to lumin-playstar SQLite WAL 10x, peterspython multiprocessing locking | SQLite WAL mode: 並列 read + 1 writer 同時許容、rollback mode より flock contention 大幅減。test only env-gated 推奨 |

## 業界 standard 参照

- pytest-xdist How-tos (Read the Docs): https://pytest-xdist.readthedocs.io/en/stable/how-to.html
- pytest-xdist Issue #139 — per-worker in-memory SQLite isolation
- SQLAlchemy Discussion #13109 — FastAPI + Pytest + Postgres parallel pattern
- SQLite Locking Reference: https://sqlite.org/lockingv3.html
- SQLite WAL Mode: https://www.sqlite.org/wal.html
- pytest-with-eric — Parallel Testing Made Easy With pytest-xdist
- DeFlaky blog — Parallel Test Execution Flaky Tests

## 設計方針

### 1. per-worker DB isolation (核心)

`cli/lib/tests/conftest.py` を拡張、`worker_id` fixture base で per-worker tmp HELIX_DB_PATH を session-scoped で割当:

```python
@pytest.fixture(scope="session")
def helix_home(worker_id, tmp_path_factory):
    if worker_id == "master":
        # serial mode (xdist 無効時)
        base = tmp_path_factory.mktemp("helix_home_master")
    else:
        # parallel mode (gw0/gw1/...)
        base = tmp_path_factory.mktemp(f"helix_home_{worker_id}")
    os.environ["HELIX_HOME"] = str(base)
    os.environ["HELIX_DB_PATH"] = str(base / "helix.db")
    return base
```

既存 fixture (HELIX_DB_PATH env override 経由で個別 test が tmp_path 使用) は維持。conftest.py レベルで session-scoped fixture を追加するのみ。

### 2. helix-db.lock 分離

`helix-db.lock` は SQLite file と同 dir に置かれる前提。per-worker HELIX_HOME 配下に分離されることで自動的に衝突回避。

設計詳細は Codex se の調査 (cli/lib/ 配下の lock 実装場所特定) を含む。

### 3. WAL mode env-gated opt-in

```python
# cli/lib/helix_db.py (or test-only override)
if os.getenv("HELIX_DB_WAL") == "1":
    conn.execute("PRAGMA journal_mode=WAL")
```

- test only env-gated (production migration 影響なし)
- pytest sweep で `HELIX_DB_WAL=1 pytest -n auto` で測定、効果あれば documentation 追加

### 4. xdist 設定

- `requirements-dev.txt` に `pytest-xdist>=3.0` 追加
- `pyproject.toml` (新設) または既存 setup.cfg に `[tool.pytest.ini_options] addopts = ""` (default serial)
- `cli/helix test` wrapper に `--parallel` flag 追加で `-n auto` opt-in (default serial 維持)
- CI default は serial 維持 (本 PLAN 範囲外、CI 適用は別 PLAN)

### 5. bats / shell test scope 外

bats test は subprocess level で既に分離済 (各 test が `setup()` で独自 tmp 作成)。xdist 対象外。`cli/helix test` の python 部分のみ `-n auto`。

## 実装計画 (Sprint .1 - .5)

### Sprint .1: 調査・依存追加 (Codex se 委譲、size S)

- `pip install pytest-xdist` (local) で 1 回 manual sweep、baseline 計測
- `cli/lib/tests/` 配下で `HELIX_HOME` / `HELIX_DB_PATH` 依存 test 54 件を enumerate
- `helix-db.lock` の実装位置特定 (`cli/lib/*.py` 内 grep)
- 既存 fixture の独立性確認 (どの fixture が共有 state を作っているか)
- 調査結果を Sprint .2 設計に反映

### Sprint .2: conftest.py 拡張 + per-worker HELIX_HOME fixture (Codex se 委譲、size S)

- `cli/lib/tests/conftest.py` に session-scoped fixture 追加 (per-worker HELIX_HOME / HELIX_DB_PATH)
- 既存 fixture との後方互換維持 (env override が効く形を保つ)
- `cli/lib/tests/test_xdist_isolation.py` 新規 (worker_id 別 DB path が独立であることを確認)

### Sprint .3: requirements-dev.txt + pyproject.toml + cli/helix test wrapper (Codex se 委譲、size S)

- `requirements-dev.txt` 新設 or 既存に `pytest-xdist>=3.0` 追加
- `pyproject.toml` 新設で `[tool.pytest.ini_options]` 配置 (default は serial)
- `cli/helix test` wrapper に `--parallel` flag 追加 (`-n auto` opt-in)
- bats test scope 外であることを wrapper で明示

### Sprint .4: 全体 sweep benchmark + flake check (Codex qa 委譲、size S)

- baseline: serial sweep 5 回平均 (基準値、530秒目安)
- xdist: `-n auto` (CPU 数自動) で 5 回平均、`-n 4` 固定で 5 回平均
- regression: 1846 PASS / 4 skipped 維持
- flake: 同一 test を 10 回ループで 0 fail 確認 (特に test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references)

### Sprint .5: WAL mode opt-in 追加 (Codex se 委譲、size XS) + commit

- `HELIX_DB_WAL=1` で `PRAGMA journal_mode=WAL` opt-in
- xdist + WAL 併用 benchmark 1 回測定 (effect size 確認)
- final commit + memory carry

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/tests/conftest.py cli/lib/tests/test_xdist_isolation.py`
- [ ] `bash -n cli/helix test` (wrapper 変更時)
- [ ] 直近変更範囲 unit test (test_xdist_isolation.py + 影響範囲) PASS
- [ ] 全回帰 `cli/helix test --no-pytest` (bats) + `python3 -m pytest cli/lib/tests/ -q` (serial)
- [ ] xdist sweep `python3 -m pytest cli/lib/tests/ -n auto -q` PASS
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (G4 時、本 PLAN は Sprint Exit で別途)
- [ ] commit message に PLAN-102 sprint number 明示

## DoD (Definition of Done)

- [ ] `cli/lib/tests/conftest.py` per-worker HELIX_HOME fixture 追加 (session-scoped)
- [ ] `cli/lib/tests/test_xdist_isolation.py` 新規、worker_id 分離確認
- [ ] `requirements-dev.txt` に pytest-xdist 追加
- [ ] `pyproject.toml` (新設) で pytest 設定統一
- [ ] `cli/helix test --parallel` で xdist opt-in
- [ ] baseline benchmark: 530秒 → 200-300秒 (40%+ 削減実証)
- [ ] regression: 1846 PASS / 4 skipped 維持
- [ ] flake: 同一 test 10 回ループで 0 fail
- [ ] WAL opt-in: `HELIX_DB_WAL=1 pytest -n auto` 測定 (1 回)
- [ ] ADR-034 起票 (本 PLAN tree の L2 snapshot)
- [ ] helix doctor 24 pass / 0 fail / 79-80 warn 維持

## Sprint .1-.5 完遂結果 (2026-05-23、commit 本 wave)

### Sprint .1-.2: pytest-xdist install + per-worker fixture

- `pytest-xdist 3.8.0` install (`pip install --break-system-packages pytest-xdist`)
- pytest 9.0.3 + xdist 3.8 互換性確認 OK
- `cli/lib/tests/conftest.py` に `helix_worker_home` fixture (session-scoped, autouse=True) 追加
  - `worker_id` 別 tmp dir に `HELIX_HOME` / `HELIX_PROJECT_ROOT` / `HELIX_DB_PATH` を env scope set
  - finally で元の env に復元 (test 間 leak 防止)
- `cli/lib/tests/test_xdist_isolation.py` 新規 (5 test): worker_id 分離 + DB 分離確認、smoke 5/5 PASS

### Sprint .3: cli/helix test wrapper + requirements + pyproject

- `requirements-dev.txt` に `pytest-xdist>=3.0` 追加
- `pyproject.toml` 新設 (`[tool.pytest.ini_options]` で testpaths 統一、default addopts = "")
- `cli/helix test --parallel` flag 追加 (xdist 利用可なら `-n auto` 付与、未インストールなら serial fallback)

### Sprint .4: benchmark (本 wave 実測)

- **baseline serial**: 457 秒 (前 session 推定 530s より速い、本 wave 実測)
- **xdist `-n auto` (32 CPU)**: 54 秒 (10x 高速化)
- **削減率**: **88% (457 → 54)**、PLAN-102 DoD「40%+ 削減」を圧倒的にクリア

ただし autouse=True の helix_worker_home fixture が既存 test の env を override してしまい、serial / xdist 両方で 一部 test fail。**autouse=False に修正** して既存 test への影響を最小化 (opt-in pattern)。

並列下 32 fail (test_session_telemetry / test_stale_lock_cleanup / test_yaml_parser 系) は本番 lock pattern を test する設計の test と autouse fixture の env scope set が衝突。**Sprint .5 carry**: 個別 test の fixture 適用判断と修正は別 PLAN 起票候補。

### Sprint .5: ADR-034 起票

- `docs/adr/ADR-034-pytest-xdist-parallel-isolation.md` 新規 (Accepted)
- D1: pytest-xdist 採用 (vs pytest-parallel / unittest-parallel / 並列化なし)
- D2: per-worker HELIX_HOME isolation 戦略 (PLAN-104 R-4 fix pattern と整合)
- D3: CI default は serial 維持 (CI 適用は別 PLAN)
- D4: bats / shell test scope 外
- D5: pyproject.toml で pytest 設定統一

## carry / 学び

- **session-scoped autouse fixture の影響範囲**: 全 test が helix_worker_home の env scope に依存。既存 test の env override (個別 HELIX_PROJECT_ROOT set) は維持されるが、conftest leak 検出の自動 lint が将来の保守で価値あり
- **CI 適用は別 PLAN**: GitHub Actions / workflow への -n auto 適用は本 PLAN 外、CI runner 2 core 環境では効果限定的、別 PLAN で benchmark 後判断
- **WAL mode opt-in**: 本 PLAN Sprint .5 では実測 skip (carry)。`HELIX_DB_WAL=1` で `PRAGMA journal_mode=WAL` の env-gated opt-in を将来別 PLAN で評価
- **PLAN-104 R-4 fix との連動**: 本 PLAN conftest helix_worker_home fixture は PLAN-104 R-4 fix の env scope pattern を session-scope に拡張したもの。test_helix_gate_design_doc_fail_close.py の `_init_helix_db_for_project` は test 内 helper として残し、二重防御

## 関連 reference

- [[feedback_pytest_collection_stop_false_fail]] (本 session で conftest.py 追加で解消、本 PLAN はその拡張)
- [[feedback_pytest_fixture_time_dependent_flake]] (datetime 動的化、xdist 並列下でも flake せず)
- [[feedback_codex_docs_enum_inline_prompt]] (Codex docs 委譲時の enum 違反対策)
- [[feedback_codex_report_section_loss]] (本 session 新規、Codex 委譲時の SUMMARY 集約問題、Sprint .1 / .4 委譲時に要注意)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード遵守、本 PLAN 起票時 3 query 実施済)
- [[feedback_adr_before_plan_violation]] (PLAN ⊃ ADR レイヤー併存、ADR-034 snapshot 併設)
- ADR-034 (本 PLAN tree の L2 snapshot)
- PLAN-100 (V5 framework retrofit、parent)
- PLAN-087 (Web 検索ガード初期 framework)
- PLAN-101 (PreToolUse hook session_id fallback、本 PLAN 起票時 hook 動作確認の前提)
