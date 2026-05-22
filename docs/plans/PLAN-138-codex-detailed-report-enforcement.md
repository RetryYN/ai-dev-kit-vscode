---
plan_id: PLAN-138
title: "PLAN-138: helix-codex detailed report 強制出力 (SUMMARY_START 前 patch / test / file list 必須化)"
kind: refactor
layer: L4
drive: be
status: draft
size: S
created: "2026-05-23"
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — helix-codex prompt template に detailed report section 追加 + WARN 検出 module 実装"
  - role: pmo-sonnet
    slot_label: "PMO — prompt template 整合レビュー・CODEX_TL_MODE.md フォーマット規約との整合確認"
generates:
  - artifact_path: cli/templates/prompts/codex-base.md
    artifact_type: template
  - artifact_path: cli/lib/codex_output_validator.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_codex_output_validator.py
    artifact_type: test
dependencies:
  parent: PLAN-MM-001
  requires: []
  blocks: []
related_adr: []
related_plans:
  - PLAN-137
related_docs:
  - CLAUDE.md §コミット規約
  - helix/CODEX_TL_MODE.md §最終報告の最小フォーマット
---

# PLAN-138: helix-codex detailed report 強制出力

> **kind**: refactor | **layer**: L4 | **drive**: be | **size**: S

---

## §0. 背景・位置付け

`[[feedback_codex_report_section_loss]]` に対応する。
PLAN-106 / 109 / 117 の実装委譲で Codex が `SUMMARY_START〜SUMMARY_END` のみを返し、
詳細 patch 内容・test 結果・完遂 file list が欠落した。

問題点:
1. patch 内容が届かず PM が変更内容を検証できない
2. 完遂 file list 不在で commit 対象ファイルの確認が困難
3. test 結果 (PASS/FAIL 数) が summary に含まれない

本 PLAN は `helix-codex` の prompt template に `## 出力形式` section を `SUMMARY_START` の前に
強制注入し、output の section 欠落を WARN で検出する。

**WebSearch skip**: 既存 template 拡張 + WARN module 追加のみ。新技術採用なし。

---

## §1. 設計方針

### 期待する Codex output 構造

```
## Patch
<変更ファイル名 + 変更内容の要点 (diff or 箇条書き)>

## Tests
<実行テストコマンド + PASS 数 / FAIL 数 / skip 数>

## File List
<作成・変更した全ファイルの絶対パス一覧>

SUMMARY_START
<1-5 行要約>
SUMMARY_END
```

### prompt template 追加 section (`cli/templates/prompts/codex-base.md`)

```markdown
## 出力形式 (必須)

SUMMARY_START の前に以下の 3 section を必ず出力してください。省略不可。

### Patch
変更したファイル名と変更内容の要点。新規作成はファイルパスと追加行数を記載。

### Tests
実行したテストコマンド + 結果 (PASS 数 / FAIL 数 / skip 数)。
未実行の場合は「テスト未実行: 理由」を明記。

### File List
本タスクで作成・変更した全ファイルの絶対パス一覧。
```

### `codex_output_validator.py` インタフェース

```python
REQUIRED_SECTIONS = ["## Patch", "## Tests", "## File List", "SUMMARY_START"]

def validate_codex_output(output: str) -> list[str]:
    """欠落 section の list を返す (空リスト = 全 PASS)"""

def warn_missing_sections(output: str, task_id: str | None = None) -> bool:
    """欠落時に stderr へ WARN 出力。欠落あり = True"""
```

### helix-codex への統合

```bash
# WARN のみ。fail-close しない (後方互換維持)
python3 "$HELIX_HOME/cli/lib/codex_output_validator.py" \
  --output "$CODEX_OUTPUT" --task-id "$TASK_ID" || true
```

---

## §2. 実装計画

### Sprint .1: template 追加 + validator 実装 (se、size S)

**Entry 条件**: `cli/templates/prompts/` 配下を ls して template file 名を確認

1. `cli/templates/prompts/codex-base.md` に `## 出力形式` section を追加
2. `cli/lib/codex_output_validator.py` 新規作成
3. `helix-codex` output 受け取り箇所に validator 呼び出し追加
4. `python3 -m py_compile cli/lib/codex_output_validator.py` PASS (mandatory in sprint)
5. `bash -n cli/helix-codex` PASS (mandatory in sprint)

受入条件:
- `validate_codex_output("## Patch\n...\nSUMMARY_START\n...")` → 空リスト
- `validate_codex_output("SUMMARY_START\n...")` → `["## Patch", "## Tests", "## File List"]`
- `warn_missing_sections` が欠落時に stderr へ WARN 出力

### Sprint .2: unit test (qa、size S)

1. `cli/lib/tests/test_codex_output_validator.py` 新規作成 (5 scenario)
   - all_present / missing_patch / missing_tests / missing_file_list / summary_only
2. `pytest cli/lib/tests/test_codex_output_validator.py -v` 全 PASS

---

## §3. DoD

1. `validate_codex_output` が 5 scenario で正しい欠落リストを返す
2. `warn_missing_sections` が欠落時に stderr へ WARN 出力する
3. `cli/templates/prompts/codex-base.md` に `## 出力形式` section が存在する
4. `helix-codex` が Codex output 受け取り後に validator を呼び出す
5. `pytest test_codex_output_validator.py -q` 全 PASS (5 scenario)
6. `bash -n cli/helix-codex` + `py_compile codex_output_validator.py` PASS
7. `python3 cli/lib/plan_validator.py docs/plans/PLAN-138-*.md` PASS

---

## §4. デグレ禁止

- `SUMMARY_START〜SUMMARY_END` の既存マーカーの動作は変更しない
- validator の WARN は stderr のみ。exit code を非ゼロにしない (fail-close しない)
- 既存 helix-codex の `--role` / `--task` / `--approved` 等は変更しない
- prompt template は `## 出力形式` section の追加のみ。既存 section の削除・変更は行わない

---

## §5. V-model trace

- ① 設計: `docs/plans/PLAN-138-codex-detailed-report-enforcement.md` (本 file)
- ② 実装: `cli/lib/codex_output_validator.py` / `cli/helix-codex` / `cli/templates/prompts/codex-base.md` → docstring に「設計: PLAN-138」
- ③ テスト設計: Sprint .2 entry で §2 Sprint .2 を正本とする
- ④ テストコード: `cli/lib/tests/test_codex_output_validator.py` → docstring に「DoD 検証: PLAN-138 §3」

---

## §6. リスク

| リスク | 緩和策 |
|---|---|
| template 追加で Codex output が冗長化 | `## Patch` は diff 全体でなく変更 file 名 + 行数サマリに制限 (§1 で明示) |
| validator が誤 WARN を出し続ける | WARN のみで fail-close しない。閾値調整は issue 化 |
| PLAN-137 と cli/helix-codex が衝突 | PLAN-137 Sprint .2 と本 PLAN Sprint .1 を直列化推奨 (同一 file 変更) |
| `codex-base.md` の path 違い | Sprint .1 entry で `cli/templates/prompts/` を ls して確認 (§2 で明示) |
