---
plan_id: L7-skill-helix-layer-auditplan
title: "L7-skill-helix-layer-auditplan: skills 実 file の helix_layer audit を追加"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-25
revised: 2026-05-25
process_layer: L7
parent_design: HELIX-workflows/helix-process/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-skill-frontmatter-doctor-integrationplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — skill helix_layer audit module と pytest 3 件を実装"
  - role: qa
    slot_label: "QA — py_compile / pytest / review / plan lint / settings diff を検証"
generates:
  - artifact_path: docs/plans/L7/L7-skill-helix-layer-auditplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/skill_helix_layer_audit.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_skill_helix_layer_audit.py
    artifact_type: test
---

## §0 PLAN concept

`skills/*/SKILL.md` の frontmatter から `metadata.helix_layer` だけを read-only 監査し、欠落・不正 enum・分布を返す専用 helper `audit_skill_helix_layers()` を新規追加する。既存 `skill_frontmatter_lint.py` と `helix doctor` の振る舞いは変更せず、今回の wave は audit 用 API とテスト固定に限定する。

## §1 背景

- `L7-skill-frontmatter-doctor-integrationplan` で frontmatter lint は doctor 接続済みだが、`helix_layer` 自体の実態把握は未実装
- 実 skills には `helix_layer` 欠落や enum 不整合が混在する可能性があり、修正前に監査レポート API が必要
- `skills/` 実 file を変更せず、別 wave の doctor / autofix へ渡せる集計契約を先に固定する

## §2 scope

1. `cli/lib/skill_helix_layer_audit.py` に `audit_skill_helix_layers(skills_root: Path) -> dict` を新規追加する
2. `SKILL.md` を再帰走査し、`metadata.helix_layer` の valid / missing / invalid を集計する
3. 戻り値は `total_skills`, `with_helix_layer`, `without_helix_layer`, `invalid_helix_layer`, `distribution`, `invalid_examples` を含む
4. `distribution` には `L1..L14`, `all`, `missing` の全 key を常に含める
5. `cli/lib/tests/test_skill_helix_layer_audit.py` に pytest 3 件を追加し、count / invalid / empty directory を固定する

scope 外:

- `skills/` 配下の実 file 修正
- `cli/lib/skill_frontmatter_lint.py` / `cli/lib/tests/test_skill_frontmatter_lint.py` の契約変更
- `helix doctor` や `helix skill` への接続
- `.claude/settings.json` の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件追加 (Red) | count / invalid / empty の期待値が test で固定される | planned |
| .2 | `audit_skill_helix_layers()` 実装 | read-only 監査で distribution と invalid_examples が返る | planned |
| .3 | 検証 + review | py_compile / pytest / grep / review / plan lint / settings 0 diff が揃う | planned |

## §4 受入条件

- `audit_skill_helix_layers(skills_root)` は `skills_root` 配下の `SKILL.md` を再帰走査し、skill 件数と `helix_layer` 分布を返す
- `metadata.helix_layer` がない場合は `without_helix_layer` と `distribution["missing"]` に計上される
- `metadata.helix_layer` が `L1..L14` または `all` 以外なら `invalid_helix_layer` と `invalid_examples` に計上される
- `distribution` は `L1..L14`, `all`, `missing` の全 key を持ち、空 directory でも 0 初期化される
- 既存 `skill_frontmatter_lint.py` / `test_skill_frontmatter_lint.py` / doctor 動作を破壊しない
- `skills/` 実 file は read-only のまま変更しない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/skill_helix_layer_audit.py`
- `python3 -m pytest cli/lib/tests/test_skill_helix_layer_audit.py -q`
- `grep -c 'audit_skill_helix_layers' cli/lib/skill_helix_layer_audit.py cli/lib/tests/test_skill_helix_layer_audit.py`
- `helix review --uncommitted`
- `helix plan lint docs/plans/L7/L7-skill-helix-layer-auditplan.md`
- `git diff -- .claude/settings.json`

## §11 carry

- 実 skills への autofix や doctor 表示への接続は別 wave で扱う
- parse failure や frontmatter 欠落を `invalid_examples` へ詳細分類する拡張は必要になった時点で別 PLAN 化する
