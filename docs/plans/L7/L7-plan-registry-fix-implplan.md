---
plan_id: L7-plan-registry-fix-implplan
title: "plan_registry bulk import regression fix: PLAN-163 frontmatter parse failure"
kind: troubleshoot
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/HELIX-process-L0-L14.md
parent_design: docs/plans/PLAN-091-v5-framework-core.md
pairs_test_design:
  - cli/lib/tests/test_plan_registry.py
is_reference: false
size: S
created_at: 2026-05-24
authors:
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — PLAN-163 frontmatter 修正 + plan_parser robust 化実装"
  - role: pmo-sonnet
    slot_label: "PMO — 修正方針整合確認 + DoD review"
  - role: tl-advisor
    slot_label: "TL-advisor — 修正方針 adversarial check (Step 4)"
  - role: pm-advisor
    slot_label: "PM-advisor — scope escalation 判断 (on-demand)"
generates:
  - artifact_type: doc_update
    artifact_path: docs/plans/PLAN-163-helix-workspace-cli-subcommands.md
  - artifact_type: python_module
    artifact_path: cli/lib/plan_parser.py
  - artifact_type: test
    artifact_path: cli/lib/tests/test_plan_registry.py
dependencies:
  requires: []
  parent: docs/plans/PLAN-091-v5-framework-core.md
  blocks: []
related_docs:
  - cli/lib/tests/test_plan_registry.py
  - docs/plans/PLAN-163-helix-workspace-cli-subcommands.md
  - cli/lib/plan_registry.py
  - cli/lib/plan_parser.py
acceptance_criteria:
  - "python3 -m pytest cli/lib/tests/test_plan_registry.py PASS (test_bulk_import_all_docs 含む)"
  - "pytest 全回帰 failed == 0"
  - "helix plan lint docs/plans/PLAN-163-helix-workspace-cli-subcommands.md PASS"
  - "PLAN-163 の意味的内容を変更しない (frontmatter syntax 修正のみ)"
---

# L7-plan-registry-fix-implplan: plan_registry bulk import regression fix

## §0 PLAN concept

### 背景・検出経緯

本 session (2026-05-24 第 6 部) で 3 件の Codex SE (workflow-skills / docs-integration /
status-batch) が repo-wide pytest 実行時に同一 1 件の失敗を検出し、いずれも
「unrelated regression」として SUMMARY remaining に記録した:

```
FAILED cli/lib/tests/test_plan_registry.py::test_bulk_import_all_docs
```

失敗内容: `result["failed"] == 0` アサーション違反。
`bulk_import(docs_dir=DEFAULT_DOCS_DIR, ...)` 実行時に 1 件以上の PLAN が parse error
として計上される。

### 失敗原因 (最有力仮説)

`docs/plans/PLAN-163-helix-workspace-cli-subcommands.md` の frontmatter に
**unquoted コロン + スペース含む YAML スカラー**が存在する:

```yaml
status_history:
  - 2026-05-23: draft (前 session 連続起票で作成、PLAN-156 子 PLAN として定義)
  - 2026-05-24: superseded (PLAN-156 Sprint .2-.4 で本 PLAN scope 全実装済...)
```

YAML において `key: value` 形式のリストアイテムは **mapping** として解析される。
`yaml.safe_load` がこれを `{2026-05-23: "draft (...)", 2026-05-24: "superseded (...)"}` の
dict リストとして読み込む場合、後続の upsert 処理でキー型が date 型になり
`_json_safe()` 経由で変換されても、plan_parser が期待しない型として
`parse_error` を返す可能性がある。

副次的な観察: PLAN-163 の `generates` エントリが `path` キー (PLAN-163) を使用しており
`artifact_path` (plan_parser 期待) と食い違っているが、これは `_iter_generates` で
skip されるのみで failure には至らない。

### 修正スコープ

- 主: `docs/plans/PLAN-163-helix-workspace-cli-subcommands.md` frontmatter の
  `status_history` 値を quoted string に修正
- 副 (方針次第): `cli/lib/plan_parser.py` の parse logic を robust 化し、
  `status_history` のような任意フィールドで parse error 全体が起きないよう防護

### DoD ブロッカー

本 regression は `pytest 全回帰 failed == 0` という exit 条件を満たせない状態にある。
修正で全回帰 PASS に復帰させることが本 PLAN の唯一の目標。

---

## §1 工程表 (8 step)

| Step | 作業 | 担当 | 受入条件 |
|------|------|------|----------|
| 1 | PLAN-163 frontmatter 全件 Read + `status_history` parse 動作確認 | PMO / SE | 失敗フィールド特定完了 |
| 2 | `cli/lib/plan_parser.py` parse logic Read + `upsert_plan` の failure path 確認 | SE | 失敗箇所の行特定完了 |
| 3 | 修正方針決定: 案 A / B / C の比較 (§2.B 参照) | SE + PMO | 方針 1 案に絞り込み |
| 4 | tl-advisor adversarial check: 修正方針 + 影響範囲 | tl-advisor | passed / 条件付き passed |
| 5 | 修正実装: PLAN-163 frontmatter (案 A or C) + plan_parser (案 B or C) | SE | py_compile / syntax check PASS |
| 6 | test 追加: `test_plan_registry_handles_status_history_mapping` (§2.D) | SE | pytest 該当 test PASS |
| 7 | pytest 全回帰確認: `test_bulk_import_all_docs` PASS + 全回帰 failed == 0 | SE | 全回帰 PASS |
| 8 | commit + push + PLAN status 更新 | SE | commit hash 記録 |

---

## §2 実装計画

### §2.A 原因特定手順

```bash
# Step 1: yaml parse 動作を直接確認
python3 -c "
import yaml
from pathlib import Path
text = Path('docs/plans/PLAN-163-helix-workspace-cli-subcommands.md').read_text()
lines = text.splitlines()
# frontmatter 抽出
end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == '---')
block = '\n'.join(lines[1:end])
result = yaml.safe_load(block)
print(type(result.get('status_history')))
print(result.get('status_history'))
"
```

期待: `status_history` が list[dict] (mapping として誤解析) で返ってくることを確認。
もし list[str] なら別の原因を追う。

```bash
# Step 2: plan_registry.bulk_import で PLAN-163 のみを対象にした単体確認
python3 -c "
import sys; sys.path.insert(0, 'cli/lib')
import plan_parser
result = plan_parser.parse_frontmatter('docs/plans/PLAN-163-helix-workspace-cli-subcommands.md')
print(result)
"
```

### §2.B 修正方針 (tl-advisor R1 で確定)

**案 A: PLAN-163 frontmatter のみ修正 (最小範囲)**

`status_history` の各値を quoted string に修正する:

```yaml
# 修正前
status_history:
  - 2026-05-23: draft (前 session ...)
  - 2026-05-24: superseded (...)

# 修正後
status_history:
  - "2026-05-23: draft (前 session ...)"
  - "2026-05-24: superseded (...)"
```

- メリット: 変更範囲最小、影響ゼロ
- デメリット: 同類 frontmatter が他 PLAN にあれば再発する

**案 B: plan_parser の parse logic robust 化のみ**

`upsert_plan` が `parse_error` を返す条件を限定する。
`status_history` のような任意フィールドの型不正は warning に留め、
必須フィールド (`plan_id` / `kind` / `layer`) が揃っていれば成功とする。

- メリット: 将来の同類 frontmatter バグを吸収できる
- デメリット: scope が広い、意図しない寛容化のリスク

**案 C: 両方実施 (frontmatter 修正 + parse logic 強化)**

案 A で即時修正 + 案 B で防護を追加する。S サイズ内で収まる場合に採用。

### §2.C 修正実装 (案 A / B / C 確定後)

- 案 A: PLAN-163 Edit (frontmatter `status_history` の各値を quoted に変更)
- 案 B: `plan_parser.py` の `parse_frontmatter` で `yaml.YAMLError` の
  catch を粒度を上げて対応するか、`_json_safe` の dict-key 型正規化を強化
- 案 C: A + B を順番に実施

### §2.D テスト追加

`status_history` にコロン含むインライン値を持つ frontmatter fixture を作成し、
`test_bulk_import_all_docs` 相当の回帰を固定する:

```python
def test_bulk_import_handles_status_history_mapping(tmp_path: Path) -> None:
    """status_history に 'date: note' 形式の値を含む PLAN が parse error にならない回帰確認"""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    db_path = tmp_path / "helix.db"
    plan_doc = docs_dir / "PLAN-999-status-history.md"
    plan_doc.write_text(
        "---\n"
        "plan_id: PLAN-999\n"
        "title: status history colon test\n"
        "kind: troubleshoot\n"
        "layer: L7\n"
        "drive: be\n"
        "status: draft\n"
        "status_history:\n"
        '  - "2026-05-24: draft (initial)"\n'
        '  - "2026-05-25: in_progress (sprint .1)"\n'
        "---\n\n"
        "# Body\n",
        encoding="utf-8",
    )
    result = plan_registry.bulk_import(docs_dir=docs_dir, db_path=db_path)
    assert result == {"total": 1, "success": 1, "failed": 0, "errors": []}
```

---

## §3 成果物

| artifact | path | 担当 |
|----------|------|------|
| frontmatter 修正 (案 A or C) | docs/plans/PLAN-163-helix-workspace-cli-subcommands.md | SE |
| parse logic 修正 (案 B or C) | cli/lib/plan_parser.py | SE |
| regression test 追加 | cli/lib/tests/test_plan_registry.py | SE |

---

## §4 受入条件 / DoD

```
[ ] python3 -m pytest cli/lib/tests/test_plan_registry.py -v PASS
    - test_bulk_import_all_docs PASS
    - test_bulk_import_handles_status_history_mapping PASS (新規追加)
    - 既存 4 test PASS 維持

[ ] pytest 全回帰 failed == 0
    (現状: 1969 passed / 1 failed → 1970 passed / 0 failed に復帰)

[ ] helix plan lint docs/plans/PLAN-163-helix-workspace-cli-subcommands.md PASS
    (warnings 0 が目標)

[ ] PLAN-163 の意味的内容・scope を変更しない
    (frontmatter syntax 修正のみ、本文・acceptance_criteria 変更なし)

[ ] python3 -m py_compile cli/lib/plan_parser.py PASS (案 B/C 採用時)
```

---

## §5 関連 PLAN / docs

- PLAN-091: V5 framework 本体 (plan_registry 設計責任元)
- PLAN-092: PostToolUse 自動登録 + helix.db v35 schema
- PLAN-163: 本 PLAN の修正対象 frontmatter
- cli/lib/plan_parser.py: parse logic
- cli/lib/plan_registry.py: bulk_import entry point
- cli/lib/tests/test_plan_registry.py: regression test

---

## §6 後続 PLAN 候補

- plan_registry error reporting 改善: `parse_error` 時に frontmatter の具体的な
  field / line を出力する (現状は "parse_error" のみ)
- helix plan lint 拡張: `status_history` のような任意フィールドで
  unquoted コロン含む値を起票時に検出し早期警告する

---

## §7 進捗

| Sprint | 日時 | 内容 | commit |
|--------|------|------|--------|
| Step 1-4 | — | 原因特定 + tl-advisor check | — |
| Step 5-6 | — | 修正実装 + test 追加 | — |
| Step 7-8 | — | 全回帰 PASS + commit | — |
