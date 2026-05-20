---
plan_id: PLAN-092
doc_id: PLAN-092-unit-test-design
title: "PLAN-092 単体テスト設計 (PostToolUse 自動登録 + helix.db v35 schema)"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-21
revised: 2026-05-21 (§3 業界 standard 参照 + WebSearch 3 query 追補、PLAN-087 ガードレール準拠リカバリー)
owner: QA
related_docs:
  - docs/plans/PLAN-092-posttooluse-plan-auto-register.md
  - docs/plans/PLAN-091-v5-framework-core.md
  - docs/plans/PLAN-MM-001-v5-framework-master-plan.md
phases: L4
gates: G3,G4
---

# PLAN-092 単体テスト設計 (PostToolUse 自動登録 + helix.db v35 schema)

## §0 概要

本書は PLAN-092 の ③ テスト設計 artifact であり、① 設計・② 実装コード・④ テストコードとは統合しない独立 file として管理する。

- 対象 PLAN: PLAN-092 (PostToolUse 自動登録 + helix.db v35 schema)
- 対応 ① 設計 doc: `docs/plans/PLAN-092-posttooluse-plan-auto-register.md` §5 / §7
- ③ 本 file: `docs/v2/L4-test-design/PLAN-092-unit-test-design.md`
- 対応 ④ テストコード: `cli/lib/tests/test_plan_parser.py` (Sprint .1b 実装後)
- V-model 根拠: PLAN-091 §10 (V-model TDD pair freeze) / `helix/HELIX_CORE.md §設計⇔テスト対応`

本書は PLAN-092 §5 の v35 schema 10 table と §7 の `plan_parser.py` 4 API を unit test case に落とし込む。テストコード実装時は docstring 冒頭に `DoD 検証: PLAN-092-unit-test-design.md U-092-001〜010` を記載する。

## §1 テスト対象と境界

対象 module は `cli/lib/plan_parser.py`。public API は PLAN-092 §7.2 の `parse_frontmatter` / `upsert_plan` / `detect_cycle` / `main` とする。

| API | unit test 境界 |
|---|---|
| `parse_frontmatter(filepath)` | markdown frontmatter 抽出、YAML parse、必須 field warning |
| `upsert_plan(conn, frontmatter, doc_path)` | `plan_registry` と関連 4 table 展開、fail-open 記録 |
| `detect_cycle(conn, plan_id)` | `plan_dependencies` requires / parent edge の循環検出 |
| `main(filepath, mode="upsert")` | exit code / stderr / cycle warning の CLI entrypoint 表現 |

unit test では `:memory:` SQLite と手動 v35 schema 適用を使う。実 `helix.db`、migration runner 全体、PostToolUse hook shell、settings.json 登録、PLAN-093/094/099 連携は対象外で、integration test 範囲とする。

## §2 単体テスト 10 case 詳細設計

### U-092-001 正常 frontmatter parse で PlanFrontmatter 全フィールドを populated する

**case ID**: U-092-001
**title**: 正常 PLAN markdown の frontmatter parse
**対象関数 / API**: `parse_frontmatter(filepath)`
**関連設計 ref**: PLAN-092 §7.1 / §7.2、PLAN-091 §5

**入力 (fixture / mock 状態)**:
- `tmp_path` に `---` で囲まれた PLAN markdown を作る
- `plan_id`, `title`, `kind`, `layer`, `drive`, `status`, `size`, `owner` を含める
- `dependencies.requires=[PLAN-091]`, `dependencies.parent=[PLAN-MM-001]` を含める
- `agent_slots` は `role: se` と `role: qa` の 2 件にする
- `related_docs` と `generates` は複数件、secret / PII は含めない

**実行手順**:
1. markdown fixture を作成する
2. `parse_frontmatter(str(path))` を呼ぶ
3. top-level field と nested field を読む
4. `capsys` で stderr を読む

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- `None` ではない frontmatter object / dict を返す
- 必須 field と optional field が fixture 値で populated される
- dependencies / agent_slots / related_docs / generates が保持される
- stderr warning は出ない
- DB 更新は発生しない

**検証 assertion 一覧**:
- `assert result is not None`
- `assert result["plan_id"] == "PLAN-092"`
- `assert result["kind"] == "impl"` / `assert result["layer"] == "L4"`
- `assert len(result["agent_slots"]) == 2`
- `assert captured.err == ""`

**失敗時の意味**:
- PLAN-091 frontmatter 語彙を parser が受け取れていない
- `upsert_plan` に必要な構造化 field が欠落する
- PLAN 自動登録の entrypoint 契約が破られている

### U-092-002 frontmatter 欠損または YAML parse 失敗で None 返却 + stderr warning を出す

**case ID**: U-092-002
**title**: 不正 markdown の fail-open parse
**対象関数 / API**: `parse_frontmatter(filepath)`
**関連設計 ref**: PLAN-092 §6.4 / §7.2 / §10.1

**入力 (fixture / mock 状態)**:
- fixture A は `---` 区切りを持たない markdown
- fixture B は `---` 区切りあり、YAML 構文が壊れた markdown
- file path は存在する通常ファイルにする
- DB connection は使わない
- stderr は `capsys` で捕捉する

**実行手順**:
1. fixture A/B を `tmp_path` に作る
2. fixture A に `parse_frontmatter` を実行する
3. stderr warning を確認する
4. fixture B でも同じ確認を行う

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- fixture A は `None` を返す
- fixture B も `None` を返す
- どちらも stderr warning を出す
- 例外は caller へ伝播しない
- DB 更新は発生しない

**検証 assertion 一覧**:
- `assert result_no_frontmatter is None`
- `assert result_invalid_yaml is None`
- `assert "WARNING" in captured.err`
- `assert "frontmatter" in captured.err.lower() or "parse" in captured.err.lower()`
- `pytest` が例外未送出を確認する

**失敗時の意味**:
- PLAN-092 §6.4 の fail-open 設計に反する
- parse error が warning として可視化されない
- hook が不正 PLAN 保存で停止する可能性がある

### U-092-003 必須フィールド不在では警告フラグを立てつつ parse 自体は成功する

**case ID**: U-092-003
**title**: 必須 field 欠損の soft warning
**対象関数 / API**: `parse_frontmatter(filepath)`
**関連設計 ref**: PLAN-092 §7.1 / §7.2、PLAN-091 §5

**入力 (fixture / mock 状態)**:
- `---` 区切りと YAML 構文は正しい markdown を使う
- `plan_id`, `kind`, `layer` を欠落させる
- 任意 field として `title`, `status`, `related_docs` は含める
- warning list / flag がある実装なら戻り値で観測する
- stderr warning 実装なら `capsys` で観測する

**実行手順**:
1. 必須 field 欠損 fixture を作る
2. `parse_frontmatter(str(path))` を呼ぶ
3. 戻り値が `None` でないことを確認する
4. warning 表現を確認する

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- YAML parse 自体は成功する
- 戻り値は `None` ではない
- `plan_id` / `kind` / `layer` 欠損が warning として表現される
- 欠損 field を勝手に補完しない
- DB 更新は発生しない

**検証 assertion 一覧**:
- `assert result is not None`
- `assert "title" in result`
- `assert "plan_id" not in result or not result["plan_id"]`
- `assert warning contains "plan_id"`
- `assert warning contains "kind" and "layer"`

**失敗時の意味**:
- syntax error と semantic warning を区別できていない
- `upsert_plan` の fail-open 記録へ渡す情報が欠落する
- PLAN-091 frontmatter validation との責務境界が崩れる

### U-092-004 新規 PLAN INSERT で registry と関連 4 table に展開挿入する

**case ID**: U-092-004
**title**: 新規 PLAN の v35 table 展開 INSERT
**対象関数 / API**: `upsert_plan(conn, frontmatter, doc_path)`
**関連設計 ref**: PLAN-092 §5.1〜§5.5 / §7.1 / §7.2

**入力 (fixture / mock 状態)**:
- `sqlite3.connect(":memory:")` に v35 schema を手動適用する
- 正常 PLAN-092 風 frontmatter dict を使う
- `dependencies` は `requires`, `parent`, `blocks` を含める
- `agent_slots`, `related_docs`, `test_design_ref`, `generates` を含める
- `failure_log` は初期 0 件にする

**実行手順**:
1. v35 schema fixture を適用する
2. `upsert_plan(conn, frontmatter, doc_path)` を呼ぶ
3. 戻り値の `plan_id`, `status`, `counts` を確認する
4. 5 table と `failure_log` を SELECT する

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- `plan_registry` に 1 行 INSERT される
- `frontmatter_json` は JSON 文字列として保存される
- `plan_dependencies` / `plan_agent_slots` / `plan_references` / `plan_generates` に展開される
- `failure_log` は増えない
- stderr warning は出ない

**検証 assertion 一覧**:
- `assert result["plan_id"] == "PLAN-092"`
- `assert result["counts"]["dependencies"] == expected_dep_count`
- `assert result["counts"]["agent_slots"] == 2`
- `assert json.loads(registry_row["frontmatter_json"])["plan_id"] == "PLAN-092"`
- `assert failure_log_count == 0`

**失敗時の意味**:
- PLAN-092 §5 の中心 table 登録契約が破られている
- plan_registry が PLAN の source of truth にならない
- PLAN-093 / PLAN-099 の downstream 前提が壊れる

### U-092-005 既存 PLAN UPDATE で registry を更新し関連 4 table は全削除後に再挿入する

**case ID**: U-092-005
**title**: 同一 plan_id の idempotent upsert
**対象関数 / API**: `upsert_plan(conn, frontmatter, doc_path)`
**関連設計 ref**: PLAN-092 §5.1〜§5.5 / §7.2 / §9

**入力 (fixture / mock 状態)**:
- `:memory:` SQLite に v35 schema を適用する
- 初回 frontmatter は `status: draft` と複数関連行を持つ
- 2 回目 frontmatter は同じ `plan_id` で `status: active` にする
- 2 回目は dependencies / agent_slots / references / generates を差し替える
- timestamp は exact 比較しない

**実行手順**:
1. 初回 `upsert_plan` を実行する
2. 関連 4 table の件数と代表値を保存する
3. 同一 `plan_id` で 2 回目 `upsert_plan` を実行する
4. registry と関連 4 table を SELECT する

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- `plan_registry` は重複せず 1 行のまま UPDATE される
- `status` と `frontmatter_json` は 2 回目の値になる
- 関連 4 table は対象 `plan_id` の旧行を削除して再挿入される
- 古い edge / artifact は残らない
- UNIQUE 制約エラーは発生しない

**検証 assertion 一覧**:
- `assert registry_count_for_plan == 1`
- `assert registry_row["status"] == "active"`
- `assert json.loads(registry_row["frontmatter_json"]) == updated_frontmatter`
- `assert old_dep_plan_id not in selected_dep_plan_ids`
- `assert new_artifact_path in selected_artifact_paths`

**失敗時の意味**:
- PostToolUse 再保存で registry が stale または重複する
- dependencies / generates trace が古い PLAN 内容と混ざる
- drift detection が誤判定する

### U-092-006 parse 失敗 PLAN の upsert は failure_log に記録し plan_registry を未変更にする

**case ID**: U-092-006
**title**: parse failure の fail-open DB 記録
**対象関数 / API**: `upsert_plan(conn, frontmatter, doc_path)` / `main(filepath, mode="upsert")`
**関連設計 ref**: PLAN-092 §5.7 / §6.4 / §7.2

**入力 (fixture / mock 状態)**:
- `:memory:` SQLite に v35 schema を適用する
- `frontmatter` は `None` または parse failure sentinel にする
- baseline として別 PLAN を `plan_registry` に 1 件入れる
- `failure_log` は初期 0 件にする
- CLI 経由確認では stderr / exit code を捕捉する

**実行手順**:
1. baseline の registry 件数を取得する
2. parse failure 入力で `upsert_plan` を呼ぶ
3. registry 件数と既存 row の未変更を確認する
4. `failure_log` を SELECT する

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- `plan_registry` は INSERT / UPDATE されない
- `failure_log` に 1 行 append される
- `failure_type` は `parse_error` 相当になる
- `context` に `doc_path` とエラー概要が含まれる
- `main` 経由でも crash しない

**検証 assertion 一覧**:
- `assert registry_count_after == registry_count_before`
- `assert baseline_registry_row == unchanged_row`
- `assert failure_log_count == 1`
- `assert failure_row["failure_type"] == "parse_error"`
- `assert doc_path in failure_row["context"]`

**失敗時の意味**:
- PLAN-092 §6.4 の fail-open 設計が破られる
- parse 失敗が監査不能になる
- plan_registry が不完全 frontmatter で汚染される

### U-092-007 ROLE_MAP 30 種外の role でも plan_agent_slots 挿入は成功する

**case ID**: U-092-007
**title**: agent_slots role lint を validator 側責務として分離する
**対象関数 / API**: `upsert_plan(conn, frontmatter, doc_path)`
**関連設計 ref**: PLAN-092 §5.3 / §7.1、`cli/ROLE_MAP.md`

**入力 (fixture / mock 状態)**:
- `:memory:` SQLite に v35 schema を適用する
- `agent_slots` に `role: se` と `role: experimental-role` を含める
- `experimental-role` は ROLE_MAP 30 種外の slug とする
- その他の必須 field は正常値にする
- `plan_validator.py` は呼ばない

**実行手順**:
1. v35 schema fixture を準備する
2. ROLE_MAP 外 role を含む frontmatter で `upsert_plan` を呼ぶ
3. 戻り値の agent slot count を確認する
4. `plan_agent_slots` と `failure_log` を SELECT する

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- `plan_registry` INSERT は成功する
- ROLE_MAP 外 role も `plan_agent_slots` に保存される
- `role` は入力値を改変せず保持される
- role lint は parser ではなく validator 責務として残る
- `failure_log` は role lint 目的では増えない

**検証 assertion 一覧**:
- `assert result["counts"]["agent_slots"] == 2`
- `assert "se" in selected_roles`
- `assert "experimental-role" in selected_roles`
- `assert registry_count_for_plan == 1`
- `assert failure_log_count == 0`

**失敗時の意味**:
- parser / upsert が validator 責務を取り込んでいる
- 将来追加 role や plugin role の raw trace が欠落する
- ROLE_MAP 更新前の PLAN を fail-open で取り込めない

### U-092-008 循環なし graph では cycle list 空を返す

**case ID**: U-092-008
**title**: acyclic dependencies の正常判定
**対象関数 / API**: `detect_cycle(conn, plan_id)`
**関連設計 ref**: PLAN-092 §5.2 / §7.3 / §10.1

**入力 (fixture / mock 状態)**:
- `:memory:` SQLite に v35 schema を適用する
- `plan_registry` に A / B / C / D を挿入する
- `plan_dependencies` に `A requires B`, `B requires C`, `A requires D` を入れる
- `blocks` edge は入れないか、無視確認用に入れる
- 起点 `plan_id` は A とする

**実行手順**:
1. v35 schema fixture を適用する
2. registry と acyclic edge を挿入する
3. `detect_cycle(conn, "A")` を呼ぶ
4. 戻り値、実行時間、DB 未変更を確認する

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- 戻り値は空 list
- stderr は出ない
- `failure_log` は増えない
- `plan_dependencies` は変更されない
- traversal は有限時間で終了する

**検証 assertion 一覧**:
- `assert cycle == []`
- `assert isinstance(cycle, list)`
- `assert failure_log_count == 0`
- `assert dependency_count_after == dependency_count_before`
- `assert duration < small_threshold`

**失敗時の意味**:
- acyclic graph を cycle と誤判定する
- PostToolUse hook が不要に block する
- read-only 判定関数が DB 副作用を起こしている

**アルゴリズム選択注記 (§3.3 参照)**: PLAN-092 §7 凍結の BFS 実装 spec に従う。業界 standard は directed graph cycle detection に DFS + recStack だが (GeeksforGeeks / W3Schools 多数)、BFS でも Kahn's algorithm (in-degree 0 削減) で等価な判定が可能であり、spec 優先で BFS test 設計を維持する。

### U-092-009 A→B→A の 2-node 循環を [A, B, A] として検出する

**case ID**: U-092-009
**title**: 2-node cycle detection
**対象関数 / API**: `detect_cycle(conn, plan_id)` / `main(filepath, mode="upsert")`
**関連設計 ref**: PLAN-092 §5.2 / §6.2 / §6.3 / §7.3

**入力 (fixture / mock 状態)**:
- `:memory:` SQLite に v35 schema を適用する
- `plan_registry` に A / B を挿入する
- `plan_dependencies` に `A requires B` と `B requires A` を挿入する
- 起点 `plan_id` は A とする
- `dep_type` は cycle detection 対象の `requires` を使う

**実行手順**:
1. v35 schema fixture を適用する
2. A / B の registry fixture を挿入する
3. 双方向 requires edge を挿入する
4. `detect_cycle(conn, "A")` を呼ぶ

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- cycle list に `["A", "B", "A"]` が含まれる
- 完全一致 list を返す実装なら完全一致でよい
- DB row は変更されない
- pure `detect_cycle` では `failure_log` 追加を必須にしない
- `main` 経由では cycle warning / block message へ接続する

**検証 assertion 一覧**:
- `assert cycle == ["A", "B", "A"]` または `assert ["A", "B", "A"] in cycles`
- `assert cycle[0] == "A"`
- `assert cycle[-1] == "A"`
- `assert len(cycle) == 3`
- `assert dependency_count_after == dependency_count_before`

**失敗時の意味**:
- 最小循環を検出できない
- PLAN-092 §6.3 の cycle detected guidance を生成できない
- dependencies graph が不整合のまま登録される

**アルゴリズム選択注記 (§3.3 参照)**: PLAN-092 §7 凍結の BFS 実装 spec に従う。業界 standard は directed graph cycle detection に DFS + recStack だが (GeeksforGeeks / W3Schools 多数)、BFS でも Kahn's algorithm (in-degree 0 削減) で等価な判定が可能であり、spec 優先で BFS test 設計を維持する。

### U-092-010 A→B→C→A の 3-node 循環を検出し BFS が無限ループしない

**case ID**: U-092-010
**title**: 3-node cycle detection と traversal 終了性
**対象関数 / API**: `detect_cycle(conn, plan_id)`
**関連設計 ref**: PLAN-092 §5.2 / §7.3 / §10.1

**入力 (fixture / mock 状態)**:
- `:memory:` SQLite に v35 schema を適用する
- `plan_registry` に A / B / C / D を挿入する
- `plan_dependencies` に `A requires B`, `B requires C`, `C requires A` を入れる
- noise edge として `A parent D` を追加してもよい
- `blocks` edge は cycle detection 対象外として扱う

**実行手順**:
1. v35 schema fixture を適用する
2. registry と 3-node cycle edge を挿入する
3. noise edge を追加する
4. `detect_cycle(conn, "A")` を呼ぶ

**期待結果 (戻り値 / DB 状態 / stderr / exit code)**:
- cycle list に `["A", "B", "C", "A"]` が含まれる
- visited / path 管理により無限ループしない
- noise edge があっても cycle path が崩れない
- `blocks` edge は cycle 判定対象外
- DB row は変更されない

**検証 assertion 一覧**:
- `assert cycle == ["A", "B", "C", "A"]` または `assert ["A", "B", "C", "A"] in cycles`
- `assert cycle[0] == cycle[-1] == "A"`
- `assert set(cycle[:-1]) == {"A", "B", "C"}`
- `assert duration < small_threshold`
- `assert dependency_count_after == dependency_count_before`

**失敗時の意味**:
- 3 段以上の dependencies cycle を見逃す
- BFS / DFS traversal の停止性を保証できない
- V5 Layer B の PLAN graph 基盤が不正確になる

**アルゴリズム選択注記 (§3.3 参照)**: PLAN-092 §7 凍結の BFS 実装 spec に従う。業界 standard は directed graph cycle detection に DFS + recStack だが (GeeksforGeeks / W3Schools 多数)、BFS でも Kahn's algorithm (in-degree 0 削減) で等価な判定が可能であり、spec 優先で BFS test 設計を維持する。実装時に DFS + recStack を選択した場合でも、同等の検証性を満たす旨を PLAN-092 §7 spec 改訂時に追記することを検討すること。

## §3 業界 standard 参照

本 section は PLAN-087 ガードレール (設計 doc 作成時 WebSearch による業界 standard 参照必須) に基づく追補である。起票時 (2026-05-21) に WebSearch を skip した不備をリカバリーし、本書の設計根拠を事後補完する。

### §3.1 Test Design Specification 標準構成 (IEEE 829 / ISO/IEC/IEEE 29119-3:2013)

本書は IEEE 829-2008 Test Design Specification の後継規格である ISO/IEC/IEEE 29119-3:2013 (Software and systems engineering — Software testing — Part 3: Test documentation) の標準構成に準拠する。

**IEEE 829 / ISO/IEC/IEEE 29119-3:2013 の Test Design Specification 3 要素**:

| 要素 | 内容 | 本書対応 section |
|---|---|---|
| features to be tested | テスト対象の機能・挙動の列挙 | §1 テスト対象と境界 |
| approaches employed | テスト手法・設計技法 | §2 case 設計 + §4 fixture 方針 |
| pass/fail criteria | 合否判定基準 | §5 fail criteria |

- IEEE 829-2008 は ISO/IEC/IEEE 29119-3:2013 に統合 (superseded) されており、現行標準は 29119-3
- 本書の §0 (目的・V-model 位置づけ) は Test Design Specification の "overview" に相当する
- V-model 4 artifact 分離原則 (設計 / 実装コード / テスト設計 / テストコードを別文書) は 29119-3 の artifact 独立保持方針と整合する

**参照 sources**:
- https://www.coleyconsulting.co.uk/IEEE829.htm (IEEE 829 構成の詳細解説)
- https://en.wikipedia.org/wiki/Software_test_documentation (ISO/IEC/IEEE 29119 統合経緯)
- https://ieeexplore.ieee.org/document/573169/ (IEEE 829 原文)

### §3.2 pytest fixture + SQLite `:memory:` best practices

本書 §4 fixture 方針は以下の業界 standard に基づく。

**function scope fixture (pytest default) による test isolation**:
- pytest fixture の scope default は `function` であり、test case ごとに新しい DB を提供する
- `:memory:` SQLite は `sqlite3.connect(":memory:")` で生成し、各 test で独立した state を確保する
- この方式により test 実行順序への依存を排除し、並列実行への対応を保つ

**SQLite `:memory:` の基本パターン**:

```python
import sqlite3
import pytest

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    # v35 schema を手動適用
    apply_v35_schema(conn)
    yield conn
    conn.close()
```

- `connect_args={"check_same_thread": False}` は SQLAlchemy ORM 経由の場合に必要 (本書では sqlite3 直接接続を使うため不要)
- `yield` 構造で setup / teardown を分離し、`try...finally` で session close を保証することが best practice
- `:memory:` DB は RAM resident であり高速に動作し、test 終了時に消滅するため file システム汚染がない
- 固定 timestamp を fixture に使うと `datetime.now(timezone.utc) - timedelta(days=N)` との境界条件で flake するため動的生成が必須 (本書 §4 で禁止明記済)

**参照 sources**:
- https://oneuptime.com/blog/post/2026-02-02-sqlite-testing/view (SQLite test patterns)
- https://woteq.com/how-to-test-sqlite-in-memory-databases-using-pytest (pytest + :memory: 設定)
- https://pytest-with-eric.com/database-testing/pytest-sql-database-testing/ (function scope fixture best practices)

### §3.3 Directed Graph の Cycle Detection 業界 standard

本書 U-092-008/009/010 は PLAN-092 §7 凍結の **BFS 実装** spec に従う。業界 standard との対照を以下に整理する。

**業界 standard: DFS + recStack**

Directed graph の cycle detection には DFS (Depth First Search) + `recStack` (recursion stack) を用いた方式が業界 standard として広く参照される:

- 現在の再帰スタックに含まれる node (= 探索中の path) を `recStack` として管理する
- DFS 中に `recStack` 内の node に到達した場合を cycle とみなす
- visited set で探索済み node を管理し、無限ループを防止する

**BFS による cycle detection: Kahn's algorithm (topological sort 方式)**

BFS ベースでは Kahn's algorithm が一般的:
- 全 node の in-degree (入次数) を計算する
- in-degree = 0 の node を queue に enqueue し、BFS で処理しながら隣接 node の in-degree を削減する
- 最終的に全 node を処理できなかった場合 (queue が枯渇、処理件数 < 全件数) に cycle の存在を確認する

**本書での設計方針**:

| 方式 | 業界 standard 評価 | 本書での扱い |
|---|---|---|
| DFS + recStack | directed graph cycle detection の業界 standard (GeeksforGeeks / W3Schools 多数) | PLAN-092 §7 で BFS 採用のため spec 優先 |
| BFS + Kahn's algorithm | topological sort を利用した cycle detection として業界 standard | **PLAN-092 §7 凍結 spec に従い採用** |

- U-092-008/009/010 の各 case は BFS 実装を前提とした期待値 (空 list / cycle path) を記述している
- 実装時に DFS + recStack を選択した場合も同等の検証性 (cycle あり/なし判定 + cycle path) を満たすが、その場合は PLAN-092 §7 spec の改訂を推奨する (spec との乖離を明示)
- 各 case の「アルゴリズム選択注記」はこの設計判断を test case 単位で可視化している

**参照 sources**:
- https://www.geeksforgeeks.org/dsa/detect-cycle-in-a-graph/ (DFS + recStack の詳細解説)
- https://www.w3schools.com/dsa/dsa_algo_graphs_cycledetection.php (DFS / BFS cycle detection 比較)
- https://favtutor.com/blogs/detect-cycle-in-directed-graph (BFS Kahn's algorithm の directed graph 適用)

## §4 テスト fixture 方針

**業界 standard 準拠 (§3.2 参照)**: 本 section の全方針は §3.2 に記載した pytest + SQLite `:memory:` best practices に基づく。

- DB は `sqlite3.connect(":memory:")` を使い、file 上の `helix.db` は使わない
- beforeEach / pytest fixture で v35 migration 相当の schema を手動適用する
- `PRAGMA foreign_keys = ON` を明示し、FK / cascade / UNIQUE の期待を再現する
- markdown fixture は `tmp_path` に作り、secret / PII / credential を含めない
- 固定 timestamp は禁止し、`datetime.now(timezone.utc)` 相当の動的時刻を許容する
- timestamp assertion は exact value ではなく非空、parse 可能性、before/after range で確認する
- stderr は `capsys`、SQLite は本物の `:memory:` DB、ROLE_MAP validation は呼ばない

## §5 fail criteria (G3 / G4 ゲート)

### §5.1 G3 実装着手ゲート

- 本書が ③ 単体テスト設計 artifact として存在する
- §0-§7 が揃っている
- U-092-001〜010 が全件記述されている
- 各 case に ID / title / 対象関数 / 入力 / 期待結果 / 検証 / 失敗意味 / ref がある
- PLAN-092 §5 / §7 と本書の双方向 trace が成立する

### §5.2 G4 実装凍結ゲート

- Sprint .1b 完了条件として U-092-001〜010 が `cli/lib/tests/test_plan_parser.py` で全 PASS
- PLAN-092 §10 / §11 DoD #4 に従い、10 case 全件 PASS が必須
- `python3 -m py_compile cli/lib/plan_parser.py cli/lib/migrations/v35_plan_registry.py` が PASS
- 既存 `cli/lib/tests/` の全回帰が PASS
- test docstring に `DoD 検証: PLAN-092-unit-test-design.md U-092-001〜010` がある

### §5.3 fail 判定

- 10 case のうち 1 件でも未実装 / skipped のまま Sprint .1b を完了しようとしている
- parse failure 時に `plan_registry` が変更される
- update upsert 後に関連 4 table の stale row が残る
- 2-node / 3-node cycle を検出できない
- fixed timestamp や secret / PII fixture が残る

## §6 V-model 4 artifact 双方向 trace

| Artifact | 担当層 | ファイル / 予定 |
|---|---|---|
| ① 設計 | L3.5 機能設計 / DB schema 設計 | `docs/plans/PLAN-092-posttooluse-plan-auto-register.md` §5 / §7 |
| ② 実装コード | L4 実装 | `cli/lib/plan_parser.py` |
| ③ テスト設計 (本書) | L4 設計 | `docs/v2/L4-test-design/PLAN-092-unit-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_plan_parser.py` |

- ① → ③: PLAN-092 frontmatter `test_design_ref` と本書 §0 で `docs/v2/L4-test-design/PLAN-092-unit-test-design.md` を明示する
- ② → ①: Sprint .1a 実装時、`cli/lib/plan_parser.py` docstring 冒頭に `契約: PLAN-092 §5 / §7` を挿入予定
- ③ → ①: 本書 §0 / §2 の各 case が PLAN-092 §5 / §7 / §10 を ref として持つ
- ④ → ③: Sprint .1b 実装時、`cli/lib/tests/test_plan_parser.py` docstring 冒頭に `DoD 検証: PLAN-092-unit-test-design.md U-092-001〜010` を挿入予定

## §7 関連

- 親 PLAN: `docs/plans/PLAN-092-posttooluse-plan-auto-register.md`
- 上位 framework: `docs/plans/PLAN-091-v5-framework-core.md` §10 (V-model TDD pair freeze)
- 上位 master plan: `docs/plans/PLAN-MM-001-v5-framework-master-plan.md` §11 (V-model 4 artifact)
- 参考既存 test-design: `docs/v2/L4-test-design/PLAN-074-unit-test-design.md`
- 参考既存 test-design: `docs/v2/L4-test-design/PLAN-078-unit-test-design.md`

実装時 Next Action は Sprint .1a で `cli/lib/plan_parser.py` / `cli/lib/migrations/v35_plan_registry.py` を作成し、Sprint .1b で本書 U-092-001〜010 を `cli/lib/tests/test_plan_parser.py` に実装し、py_compile と全回帰で G4 判定すること。
