---
plan_id: PLAN-191
title: "PLAN-191: helix-docs API reference auto-gen (CLI / Python module docstring 抽出)"
layer: L4
kind: impl
status: draft
size: M
drive: be
created: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — cli/lib/api_gen.py 実装 + helix docs api-gen subcommand 実装"
  - role: docs
    slot_label: "Docs — 生成 markdown テンプレート設計 + mkdocs nav 統合"
  - role: qa
    slot_label: "QA — api-gen テスト設計・実装 (全 module scan / markdown 出力検証)"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・PLAN-160 依存整合・G4 review"
generates:
  - artifact_path: cli/lib/api_gen.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_api_gen.py
    artifact_type: test
  - artifact_path: cli/helix-docs
    artifact_type: cli_extension
  - artifact_path: docs/v2/L4-test-design/PLAN-191-test-design.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-160
  requires:
    - PLAN-160
  blocks: []
related_plans:
  - PLAN-160-helix-mkdocs-site
  - PLAN-131-adr-decision-graph
related_adr: []
related_docs:
  - docs/commands/index.md
  - docs/architecture/cli-layout.md
---

# PLAN-191: helix-docs API reference auto-gen

> **kind**: impl | **layer**: L4 | **drive**: be | **parent**: PLAN-160

---

## §0. 位置付け

HELIX CLI 80+ command + Python module 100+ の API reference は手動管理で乖離が生じやすい。
本 PLAN は docstring / argparse help を自動抽出して markdown を生成する `helix docs api-gen`
を実装し、PLAN-160 の mkdocs-material site に統合する。

**L2 大局判断**: 軽量実装 (L4 直接着手) のため ADR snapshot 不要。
ツール選択 (pdoc3 vs ast.parse) は Sprint .1 WebSearch で確定する。

---

## §1. 目的

1. `helix docs api-gen` で `cli/` Bash / `cli/lib/` Python を scan し markdown を生成する
2. 生成 markdown を `docs/site/docs/reference/` に配置して mkdocs nav に統合する
3. `helix docs build` 実行時に api-gen が自動先行実行されるパイプラインを構築する

---

## §2. 背景

### 2.1 現状の問題

| 問題 | 影響 |
|---|---|
| `docs/commands/index.md` が手動管理 | コマンド追加時に更新漏れが発生 |
| Python module の public API が未文書化 | 利用者が実装を直接読む必要がある |

### 2.2 WebSearch 3 query (Sprint .1 で実施、PLAN-087 ガードレール準拠)

| # | Query |
|---|---|
| Q1 | `pdoc3 mkdocs integration 2025 2026 best practices` |
| Q2 | `argparse CLI documentation auto-gen markdown python 2026` |
| Q3 | `sphinx autodoc alternatives lightweight python docstring extractor 2026` |

---

## §3. 設計方針

### 3.1 scan 対象

```
cli/helix-*           Bash コマンド: helix <cmd> --help を subprocess 取得
cli/lib/*.py          Python: ast.parse で docstring 抽出
cli/lib/**/*.py       再帰 (__init__.py 含む)
除外: cli/lib/tests/ / cli/lib/migrations/
```

### 3.2 生成 markdown フォーマット

```markdown
# helix <subcommand>
> **path**: cli/helix-<subcommand>

## 概要
<argparse description または先頭 docstring>

## オプション
| オプション | 説明 | デフォルト |
```

### 3.3 パイプライン統合

`helix docs build` の冒頭で `helix docs api-gen` を自動呼び出す。

---

## §4. 実装計画

| Sprint | 内容 | 担当 | 受入条件 |
|---|---|---|---|
| **.1** | WebSearch 3 query + api_gen.py API 設計確定 | pmo-sonnet + docs | WebSearch 証拠記録済、public API シグネチャ確定 |
| **.2** | `cli/lib/api_gen.py` Python scanner 実装 | SE | `scan_python_modules` が 100+ module 処理 PASS |
| **.3** | Bash scanner + `helix docs api-gen` CLI 実装 | SE | `helix docs api-gen` が reference/ に markdown 生成 |
| **.4** | `test_api_gen.py` 実装 + QA | QA | T1〜T5 全件 PASS / `helix test` 回帰 PASS |

### Sprint .2 — Python scanner 実装

```python
# cli/lib/api_gen.py public API
def scan_python_modules(root: Path) -> list[ModuleDoc]: ...
def scan_bash_commands(cli_dir: Path) -> list[CommandDoc]: ...
def render_markdown(doc: ModuleDoc | CommandDoc) -> str: ...
```

### Sprint .4 — テスト 5 scenario

- T1: Python module scan (fixture module → docstring 抽出)
- T2: markdown render (ModuleDoc → 期待 markdown 照合)
- T3: Bash command scan (mock subprocess → help text 抽出)
- T4: empty module (docstring なし → 空 section として処理)
- T5: scan_python_modules 再帰 (サブディレクトリ含む)

---

## §5. DoD

- [ ] `python3 -m py_compile cli/lib/api_gen.py` PASS
- [ ] `pytest cli/lib/tests/test_api_gen.py -v` 全件 PASS (5 test 以上)
- [ ] `helix docs api-gen` が `docs/site/docs/reference/` に markdown を生成する
- [ ] `helix docs build` が api-gen 先行実行後に成功する
- [ ] WebSearch 3 query 証拠が §2.2 に記録されている
- [ ] `python3 cli/lib/plan_validator.py docs/plans/PLAN-191-*.md` PASS
- [ ] `helix test` 全体回帰 PASS

---

## §6. V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 | docs/plans/PLAN-191-*.md |
| ② 実装コード | cli/lib/api_gen.py / cli/helix-docs |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-191-test-design.md (Sprint .1 で起票) |
| ④ テストコード | cli/lib/tests/test_api_gen.py |

双方向 reference: cli/lib/api_gen.py 先頭 comment に `# PLAN-191` 明記。
テスト設計 frontmatter に `related_plans: [PLAN-191]` 明記。

---

## §7. リスク

| リスク | 緩和策 |
|---|---|
| pdoc3 が mkdocs-material と不整合 | Sprint .1 WebSearch で先行確認、代替として ast.parse 実装を用意 |
| Bash `--help` 出力形式が統一されていない | stdout を raw text として保存、整形はベストエフォート |
| docs/site/ が PLAN-160 Sprint .3 完了前 | `--out-dir` の directory を自動作成 |

---

## §8. 完了記録

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
