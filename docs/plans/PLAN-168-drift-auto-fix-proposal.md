---
plan_id: PLAN-168
title: "PLAN-168: V2 doc / PLAN drift detector 自動修正提案 framework"
kind: impl
layer: L4
drive: be
status: draft
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — drift 種別分類器・patch 生成ロジック・helix doctor --auto-fix 実装"
  - role: pmo-sonnet
    slot_label: "PMO — drift 種別の自動修正可否分類レビュー・PLAN-093/117 との境界確認"
  - role: tl-advisor
    slot_label: "TL adversarial check — patch 生成の安全性・不可逆操作リスク評価 (Sprint .2 前)"
generates:
  - artifact_path: cli/lib/drift_auto_fix.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_drift_auto_fix.py
    artifact_type: test
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: docs/commands/drift-auto-fix.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-117
  requires:
    - PLAN-093-plan-drift-detection-curator
    - PLAN-117-plan-drift-detect-hook
  blocks: []
related_adr: []
related_docs:
  - docs/plans/PLAN-117-plan-drift-detect-hook.md
  - docs/plans/PLAN-093-drift-detect-progress-trace.md
  - cli/lib/plan_drift_checker.py
  - cli/helix-doctor
acceptance_criteria:
  - "drift 種別ごとに auto-fixable / human-required を分類した分類テーブルが docs に存在する"
  - "auto-fixable 種別 (D-FMT-001 / D-REC-001 / D-GEN-PATH-001) に対して patch 文字列を生成できる"
  - "helix doctor --auto-fix が dry-run モード (--dry-run) と apply モードを提供し、apply 前に diff を表示する"
  - "human-required 種別 (D-DOD-001 / D-REQ-001 / L2MASTER-001) は patch を生成せず理由メッセージを出力する"
  - "python3 -m py_compile cli/lib/drift_auto_fix.py PASS"
  - "unit test 12 case (種別分類 / patch 生成 / dry-run / apply / human-required skip / PLAN-093 結果 JSON 読み込み) 全 PASS"
  - "既存 helix doctor の warn 数を増やさない (回帰なし)"
---

# PLAN-168: V2 doc / PLAN drift detector 自動修正提案 framework

## L2 凍結 (ADR snapshot)

PLAN-117 (PostToolUse drift 検出 hook) および PLAN-093 (drift Curator) の実装拡張であり、
既存 PostToolUse hook framework (PLAN-089) + helix doctor 設計 (PLAN-093) で凍結済の判断を継承する。
新規 L2 大局判断 (新 framework 採用 / fail-close 化方針変更) は発生しないため ADR snapshot は不要。

## 背景

PLAN-117 により PLAN.md 変更時の drift が `.helix/cache/plan-drift/<plan-id>.json` に記録されるようになった。
しかし現状は「検出して WARN 表示するだけ」であり、修正は人間が手動で行う必要がある。

drift 修正の実態を観察すると:
- **自動修正可能**: frontmatter 必須 field の欠如補完、reciprocal dependency の追記、
  `generates.artifact_path` のパス表記ゆれ修正など、既知ルールで一意に解が決まるもの
- **人間判断必要**: completed なのに DoD checkbox が残る (完了判断は人間が行う)、
  requires PLAN が未完 (順序変更は PM 承認必要)、L2-MASTER との drift (設計変更を伴う)

本 PLAN は drift 種別を 2 分類し、自動修正可能なものに対して patch を生成する `helix doctor --auto-fix` を実装する。
PLAN-093 / PLAN-117 の延長線上に位置し、drift 検出 → 提案 → 適用 の一連フローを完成させる。

## WebSearch 履歴

patch 生成パターンおよび diff 表示の設計について調査した。

- Query 1: "python unified diff patch generation yaml frontmatter auto-fix pattern"
  → `difflib.unified_diff` + `pathlib.Path.write_text` が標準的実装、dry-run は diff 表示のみで write しない
- Query 2: "static analysis auto-fix pattern classification fixable vs human-required"
  → ESLint / Ruff の "fixable" 分類設計: deterministic (一意解) = auto-fix 可、semantic (意味変更) = 人間判断
- Query 3: "helix doctor CLI extension python module drift cache json format"
  → 内部設計、PLAN-117 の `.helix/cache/plan-drift/<plan-id>.json` 形式を参照

## drift 種別と自動修正可否分類

| ID | 説明 | 分類 | 修正内容 |
|---|---|---|---|
| D-FMT-001 | frontmatter 必須 field 欠如 | **auto-fixable** | template から既定値を補完 |
| D-REC-001 | reciprocal dependency 不整合 | **auto-fixable** | 対象 PLAN の requires/blocks に追記 |
| D-GEN-PATH-001 | generates.artifact_path 表記ゆれ | **auto-fixable** | 正規パス (`./ なし`) に統一 |
| D-DOD-001 | completed + DoD `- [ ]` 残 | **human-required** | DoD 完了可否は人間判断 |
| D-REQ-001 | requires PLAN が未完状態 | **human-required** | 実装順変更は PM 承認必要 |
| D-ADR-001 | related_adr の file 不在 | **human-required** | ADR 起票 or 参照削除は設計判断 |
| L2MASTER-001 | L2-MASTER / CONCEPT との drift | **human-required** | 設計変更を伴う可能性あり |

**判定原則**: 修正結果が一意に決まる (deterministic) = auto-fixable。意味変更・PM 承認・外部 PLAN 操作を伴う = human-required。

## 設計方針

### drift_auto_fix.py 設計

```
load_drift_cache(plan_id)              -> List[DriftEntry]
classify(drift_entry)                  -> "auto-fixable" | "human-required"
generate_patch(plan_path, drift_entry) -> str   # unified diff 形式
apply_patch(plan_path, patch)          -> None   # write_text
explain_human_required(drift_entry)    -> str   # 理由メッセージ
```

- PLAN-117 の `plan_drift_checker.py` が生成した JSON を読み込んで動作する
- `generate_patch` は `difflib.unified_diff` で diff 文字列を返す
- `apply_patch` は dry-run モード時は write せず diff 文字列を stdout に出力する

### helix doctor --auto-fix 拡張

```bash
helix doctor --auto-fix [--dry-run] [--plan-id PLAN-NNN]
```

- `--dry-run`: diff を表示するだけで実際には apply しない (デフォルト)
- `--apply`: diff を確認した上で yes/no 入力後に write
- `--plan-id`: 特定 PLAN のみ対象 (省略時は全 drift cache を処理)
- human-required drift は `[SKIP: human-required]` と理由を出力して skip

### L2-MASTER / CONCEPT drift 対象化

PLAN-117 は PLAN.md 内の drift を対象とするが、本 PLAN では V2 doc (L2-MASTER / CONCEPT.md) との drift も
`helix doctor --check-v2-drift` として advisory WARN 化する。
具体的には:
- PLAN frontmatter の `drive` / `layer` が L2-MASTER §0 の matrix と整合しているか
- `related_docs` に L2-MASTER / CONCEPT.md への参照があるか (L2 大局判断含む PLAN のみ)

この drift 検出は **advisory WARN のみ** (fail-close 化は PLAN-093 Phase 4 以降)。

## 実装計画

### Sprint .1: 種別分類 + patch 生成 Python helper (Codex se、size S)

`cli/lib/drift_auto_fix.py` 新規。
`load_drift_cache` / `classify` / `generate_patch` / `explain_human_required` を実装。
unit test 8 case (各 drift 種別 × auto-fixable/human-required / generate_patch diff 形式 / explain メッセージ)。
`python3 -m py_compile` PASS + test 8 PASS が完了条件。

### Sprint .2: helix doctor --auto-fix 統合 (Codex se、size S / tl-advisor review 前)

`cli/helix-doctor` に `--auto-fix` / `--dry-run` / `--apply` / `--plan-id` フラグ追加。
`apply_patch` 実装 + dry-run / apply 分岐。
tl-advisor review (patch 安全性・不可逆操作リスク評価) を Sprint .2 着手前に実施。
unit test 4 case (dry-run diff 表示 / apply write / human-required skip / --plan-id フィルタ)。
`bash -n cli/helix-doctor` PASS + test 4 PASS が完了条件。

### Sprint .3: L2-MASTER drift 検出 + docs + pmo-sonnet review (Codex docs ∥ Codex se、size S)

`helix doctor --check-v2-drift` サブコマンド追加 (advisory WARN のみ)。
`docs/commands/drift-auto-fix.md` 起草 (使用方法 / drift 種別テーブル / dry-run フロー図)。
pmo-sonnet review + 既存 helix doctor warn 数回帰確認が完了条件。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/drift_auto_fix.py` PASS
- [ ] `bash -n cli/helix-doctor` PASS
- [ ] unit test 12 case 全 PASS
- [ ] tl-advisor review 完了 (Sprint .2 着手前)
- [ ] 既存 helix doctor warn 数回帰確認 (増加なし)
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] drift_auto_fix.py 実装: classify / generate_patch / apply_patch / explain_human_required
- [ ] helix doctor --auto-fix (--dry-run / --apply / --plan-id) 実装
- [ ] drift 種別分類テーブルが docs/commands/drift-auto-fix.md に存在
- [ ] L2-MASTER drift 検出 advisory WARN 実装
- [ ] unit test 12 case PASS
- [ ] 既存 helix doctor warn 数 回帰なし

## carry / 学び

- `apply_patch` は dry-run デフォルトとし、`--apply` は明示フラグとする。
  不可逆な上書きを防ぐため、apply 前に diff と影響 file 一覧を表示して確認を求める
- D-REC-001 (reciprocal dependency 自動補完) は対象 PLAN の plan_id を変更するため、
  対象 PLAN が `status: complete` の場合は auto-fix 禁止 (human-required に格上げ)
- L2-MASTER drift 検出は対象 PLAN の数が多い場合にパフォーマンス問題になる可能性があるため、
  `--plan-id` フィルタを常に使用することを推奨し、全件検査は opt-in とする

## 関連 reference

- PLAN-117 (PostToolUse drift 検出 hook、parent)
- PLAN-093 (drift Curator 本体)
- PLAN-089 (PostToolUse hook fail-close 設計)
- cli/lib/plan_drift_checker.py (drift JSON 形式の正本)
- cli/helix-doctor (拡張対象 CLI)
