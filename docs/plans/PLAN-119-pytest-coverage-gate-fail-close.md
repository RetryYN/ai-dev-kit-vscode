---
plan_id: PLAN-119
title: pytest coverage gate fail-close 強化 (core5 80% gate advisory→fail-close)
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — Sprint .1 現状 coverage 計測・gap 識別・carry 分類"
  - role: tl-advisor
    slot_label: "TL adversarial check — fail-close 化の段階遷移方針 review (advisory→warn→fail-close)"
  - role: se
    slot_label: "SE — Sprint .2 helix-gate G4 fail-close 実装・exit 2 化・cli/helix-gate 修正"
  - role: qa
    slot_label: "QA — Sprint .3 core10 expansion 検証・regression 確認"
generates:
  - artifact_type: cli_extension
    path: cli/helix-gate
  - artifact_type: python_module
    path: cli/lib/helix_doctor.py
  - artifact_type: adr_snapshot
    path: docs/adr/ADR-044-coverage-gate-fail-close.md
  - artifact_type: doc_update
    path: docs/plans/PLAN-119-pytest-coverage-gate-fail-close.md
dependencies:
  requires:
    - PLAN-013
  blocks: []
  parent: null
related_adr:
  - ADR-044-coverage-gate-fail-close
related_docs:
  - docs/plans/PLAN-013-helix-code-stats-coverage-gate.md
  - docs/plans/PLAN-089-gate-fail-close-advisory-transition.md
  - cli/lib/helix_doctor.py
  - cli/helix-gate
acceptance_criteria:
  - "helix gate G4 --static-only で coverage < 80% の場合 exit 2 (fail-close)"
  - "coverage >= 80% の場合 G4 pass (exit 0)"
  - "core5 scope 全 5 モジュールが coverage_eligible bucket に正しく分類されている"
  - "advisory モードから fail-close への段階遷移が ADR-044 に凍結済"
  - "helix doctor pass 件数・fail 0 件維持 (regression なし)"
  - "core10 expansion Sprint .3 で gate 対象が拡張され、80% gate が維持される"
---

# PLAN-119: pytest coverage gate fail-close 強化 (core5 80% gate advisory→fail-close)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-044** で凍結:

- coverage gate fail-close 化の採用判断 (advisory のまま継続 vs fail-close 移行)
- 段階遷移方針: advisory → warn-only → fail-close の 3 ステップ or 直接 fail-close
- core5 → core10 expansion のタイミングと scope 定義
- `helix gate G4 --static-only` への組み込み方式 (gate CLI 拡張 vs helix_doctor check 追加)

## 背景

PLAN-013 (helix code stats coverage gate) で以下が確立済:

```bash
helix code stats --uncovered --scope core5 --bucket coverage_eligible --fail-under 80
```

- G4 ゲートで coverage < 80% を検出する仕組みは存在する
- ただし現状は **advisory レベル**。G4 を通過させたまま低 coverage の実装が merge される
- PLAN-089 (gate fail-close advisory→fail-close 段階遷移) が確立したパターンを本 PLAN で coverage gate にも適用する

**問題**:

1. **advisory では機能しない**: 「coverage が 60% です」という警告は出るが G4 は通過する
2. **coverage 低下の蓄積**: advisory のまま放置すると coverage は徐々に低下し、
   80% gate の意味が失われる
3. **test 不足の可視性低下**: PR 単位での coverage drop が検出されず、テスト負債が蓄積する

**目標**: G4 ゲートで coverage < 80% が fail-close (exit 2) となり、G4 通過に coverage 80% 以上が必須となる framework を確立する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **内部 framework 強化** であり、外部ライブラリへの新規依存なし。
WebSearch **skip**。

skip 理由: `helix code stats` / `helix gate` は HELIX 独自 CLI であり、
fail-close 化は PLAN-089 確立済みパターンの適用のみ。外部業界 standard への
新規依存はない。

## 設計方針

### PLAN-089 advisory→fail-close パターンの再適用

PLAN-089 (gate fail-close advisory→fail-close 段階遷移) で確立したパターン:

```
Phase 1: check 追加 (advisory、exit 0)
Phase 2: warn-only (exit 0 だが warn メッセージ明示)
Phase 3: fail-close (exit 2)
```

本 PLAN では **Phase 3 直接移行** を採用。理由:

- core5 coverage gate は PLAN-013 で既に実装済 (Phase 1 相当)
- `helix doctor` で coverage check は warn 扱いで実装済 (Phase 2 相当)
- 現在は advisory 運用が定着しており、次ステップ = fail-close 化

tl-advisor に段階遷移方針 (直接 fail-close vs warn-only 経由) の adversarial check を
依頼し、ADR-044 で凍結する。

### helix gate G4 --static-only への組み込み

```bash
# Sprint .2 実装後の動作
helix gate G4 --static-only
# → coverage check: helix code stats --scope core5 --bucket coverage_eligible --fail-under 80
# → coverage < 80%: exit 2 (G4 fail-close)
# → coverage >= 80%: pass、次の check へ
```

`cli/helix-gate` スクリプトに coverage check を追加し、`--static-only` フラグで
pytest を実行せず coverage check のみを行う経路を確立する。

### core5 → core10 expansion (Sprint .3)

core5 (5 モジュール) が 80% gate を安定して通過できることを確認してから、
core10 (10 モジュール) に scope を拡張する。拡張対象モジュールの選定は Sprint .1
の現状 coverage 計測結果を踏まえて決定する。

## 実装計画

### Sprint .1: 現状 coverage 計測 + gap 識別 (PMO Sonnet 委譲、size S)

**目的**: 現状の core5 coverage 値を計測し、80% gate 未達モジュールと gap を識別する。

実施内容:

1. `helix code stats --uncovered --scope core5 --bucket coverage_eligible` で現状値取得
2. coverage_eligible モジュール一覧と各モジュールの現状 coverage を確認
3. 80% 未達モジュールを carry として識別 (Sprint .3 前に補完が必要なモジュール)
4. `helix code stats --scope core5 --fail-under 80` の exit code を確認
   (現在 advisory = exit 0 のはずの確認)
5. `cli/helix-gate` の現行 G4 static check 内容を Read して組み込み箇所を特定

Sprint .1 完了条件:

- core5 各モジュールの coverage 実数値が判明
- 80% 未達モジュールと差分 (uncovered line 数) が識別済
- `cli/helix-gate` の変更箇所 (行番号) が特定済

### Sprint .2: fail-close 化実装 (Codex se 委譲、size S)

**目的**: `helix gate G4 --static-only` で coverage < 80% が exit 2 となるよう実装する。

実施内容:

1. **tl-advisor adversarial check** (実装前):
   ```
   helix codex --role tl-advisor --task "coverage gate fail-close 化の設計方針 review。
   advisory→fail-close 直接移行 vs warn-only 経由の妥当性を確認してほしい。
   PLAN-089 パターンとの整合も確認すること。"
   ```
2. tl-advisor 助言を踏まえて ADR-044 起票 (方針凍結)
3. `cli/helix-gate` に coverage check 追加:
   - `--static-only` フラグで coverage check を実行
   - `helix code stats --scope core5 --bucket coverage_eligible --fail-under 80` を呼び出し
   - exit code を pass-through (80% 未達 → exit 2)
4. `cli/lib/helix_doctor.py` の coverage check を advisory から fail-close に昇格
   (warn → error 分類変更)

mandatory:
- `bash -n cli/helix-gate` PASS
- `python3 -m py_compile cli/lib/helix_doctor.py` PASS (変更時)
- `helix gate G4 --static-only` を mock coverage data で exit 2 / exit 0 両方確認

Sprint .2 完了条件:

- `helix gate G4 --static-only` が coverage < 80% で exit 2
- ADR-044 が accepted 状態で exists
- helix doctor fail 0 件維持

### Sprint .3: core10 expansion + 検証 (Codex qa 委譲、size S)

**目的**: core10 scope に拡張し、80% gate が維持されることを確認する。

実施内容:

1. core10 対象モジュール選定 (Sprint .1 の coverage 計測結果を踏まえて選定):
   - coverage_eligible bucket に分類済のモジュールから上位 10 件
   - 現状 coverage が 80% に近いモジュールを優先 (達成確率が高い順)
2. `helix code stats --scope core10` の定義を `cli/lib/` に追加
   (scope 定義が external config なら config 更新、CLI 内 hardcode なら修正)
3. `helix gate G4 --static-only` を core10 scope で実行し pass 確認
4. regression 確認:
   - `cli/helix test --no-pytest --bats-only` (bats 回帰)
   - `python3 -m pytest cli/lib/tests/ -q` (pytest 回帰)
   - helix doctor pass 件数・fail 0 件維持

Sprint .3 完了条件:

- core10 scope 定義が CLI に追加済
- `helix gate G4 --static-only --scope core10` が pass
- 全回帰 PASS

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `bash -n cli/helix-gate` PASS
- [ ] `python3 -m py_compile cli/lib/helix_doctor.py` PASS (変更時)
- [ ] `helix gate G4 --static-only` の exit 2 / exit 0 mock 確認
- [ ] 全回帰: `python3 -m pytest cli/lib/tests/ -q` PASS
- [ ] helix doctor pass 件数維持・fail 0 件維持
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (G4 時)
- [ ] commit message に `PLAN-119 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `helix gate G4 --static-only` が coverage < 80% で exit 2 (fail-close)
- [ ] `helix gate G4 --static-only` が coverage >= 80% で exit 0 (pass)
- [ ] ADR-044 起票済 (accepted、advisory→fail-close 段階遷移方針凍結)
- [ ] core5 全モジュールが coverage_eligible bucket に分類済
- [ ] core10 scope 定義追加済 (Sprint .3)
- [ ] helix doctor fail 0 件維持
- [ ] helix doctor pass 件数が起票時点 (24) 以上
- [ ] 全回帰 PASS (bats + pytest)
- [ ] tl-advisor adversarial check 通過証跡が ADR-044 または本 PLAN に記録済

## carry / 学び (起票時記録、Sprint 進行で更新)

- **core5 現状 coverage 未確認**: 本 PLAN 起票時点では `helix code stats --scope core5`
  の実数値未取得。Sprint .1 で計測前に 80% 未達の場合は test 補完 PLAN を
  PLAN-121 として別途起票し、coverage 補完→ fail-close 化 の順で進める
- **helix-gate の scope 定義場所**: `--scope core5` の scope 定義が CLI 内 hardcode か
  外部 config かは Sprint .1 で `cli/helix-gate` を Read して確認必須
- **advisory と fail-close の境界**: PLAN-089 パターンでは warn-only 中間ステップを
  経由した。本 PLAN では直接 fail-close を提案しているが、tl-advisor の判断次第で
  Sprint .2 前に warn-only フェーズを 1 sprint 挟む可能性あり

## 関連 reference

- PLAN-013 (helix code stats coverage gate 確立、本 PLAN の前提)
- PLAN-089 (gate fail-close advisory→fail-close 段階遷移パターン)
- ADR-044 (本 PLAN tree の L2 snapshot、Sprint .2 で起票)
- cli/helix-gate (G4 ゲート実装の正本)
- cli/lib/helix_doctor.py (coverage check の warn/error 分類)
