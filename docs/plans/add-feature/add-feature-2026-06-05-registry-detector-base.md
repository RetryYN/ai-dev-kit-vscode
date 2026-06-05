---
plan_id: add-feature-2026-06-05-registry-detector-base
title: "Action: 登録・検出 共通基盤 + functional-registry 縦slice — registry_checks.py + functional-registry.yaml + check を warn-only で doctor 接続"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
workflow: add-feature
kind: add-impl
layer: L4
drive: be
status: draft
created: 2026-06-05
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 共通 schema/finding model / functional-registry 契約 / baseline policy の adversarial check"
  - role: se
    slot_label: "SE — registry_checks.py 基盤 + functional-registry.yaml + detector + doctor 接続 + test の実装（Codex、TDD）"
generates:
  - artifact_path: cli/lib/registry_checks.py
    artifact_type: python_module
  - artifact_path: cli/config/functional-registry.yaml
    artifact_type: config
  - artifact_path: cli/lib/tests/test_registry_checks.py
    artifact_type: test
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: docs/v2/L6-functional-design/registry-detector-機能設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/registry-detector-単体テスト設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L4-basic-design/registry-detector-基本設計.md
    artifact_type: design_doc
dependencies:
  parent: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
  requires: []
  blocks: []
forward_return: "L4 基本設計追補(共通 report/YAML schema + GatePolicy baseline 凍結) → L6 detector 契約(check_functional_registry / check_fr_sot_alignment の関数粒度仕様 + 単体テスト設計) → L7 実装(registry_checks.py + functional-registry.yaml + detector warn-only + doctor 接続 + TDD)。親 Process の G6/G7 統合検証へ収束。"
related_docs:
  - docs/plans/process/process-2026-06-05-registration-detection-cluster.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
  - cli/lib/trace_symmetry.py
  - cli/lib/vmodel_pair_freeze.py
  - cli/helix-doctor
---

# Action 1: 登録・検出 共通基盤 + functional-registry 縦slice

> 親 Process: [登録・検出機械化クラスタ整備](../process/process-2026-06-05-registration-detection-cluster.md)。TL bg5o6lxwb の「最小共通基盤 + functional-registry 縦slice 先行」を実装する driving slice。

## 0. 実行サブスライス（2026-06-05 確定）

検証可能な単位で landing するため Action1 を 2 サブスライスに分割する。

- **1a — 共通基盤型 + 設計対凍結（着手中）**: `RegistryLoader/RegistryEntry/DetectorReport/Finding/GatePolicy` を **L6↔L7 対**で先に固定（`FN-RDB-01〜07` ↔ `UT-RDB-01〜07`、trace_symmetry balance 1.0 / coverage100% / orphan0 を確認済）→ `cli/lib/registry_checks.py` + `test_registry_checks.py` を TDD 実装（Codex se）。**doctor / yaml data は触らない**。
- **1b — functional-registry 縦slice（次）**: `cli/config/functional-registry.yaml`（548件）+ `check_functional_registry` / `check_fr_sot_alignment` + `helix doctor` warn-only 接続 + **L4 基本設計追補**（component 構成 + YAML schema 凍結）。548件 code_paths の data fill 品質は PM 判断（carry §5）。

> **doc topology 判断**: 基盤型の契約は**関数粒度＝L7 単体テストで検証**されるため、当初の単一 L4 doc ではなく **L6 機能設計 ↔ L7 単体テスト設計**の対として固定した（[L6](../../v2/L6-functional-design/registry-detector-機能設計.md) / [L7](../../v2/L7-test-design/registry-detector-単体テスト設計.md)）。これにより `verification_layers=L7` で L4↔L9 trace の偽陽性を避けつつ、新規対を機械 trace 対象に載せ、既存 frozen 14↔14 pair を退行させない（baseline 24-0-105 維持）。L4 component/YAML schema は 1b で追補する。

## 1. スコープ

**共通基盤** (`cli/lib/registry_checks.py`、TL 抽象境界):
- `RegistryLoader`（YAML/MD → 正規化）/ `RegistryEntry`（id/name/domain/status/source_docs/traces/paths/patterns/metadata）/ `DetectorReport`（check_name/domain/mode/baseline/findings/metrics/exit_policy）/ `Finding`（severity P0-P3/kind/entry_id/path/message/remediation）/ `GatePolicy`（advisory→ratchet warning→fail-close）

**functional-registry 縦slice**:
- `cli/config/functional-registry.yaml`（548件、各 entry に `code_paths/doc_paths/l1_fr/l3_fr/status`。md の人間向け SSoT は draft として残し機械正本は YAML へ）
- `check_functional_registry`（path 存在 / 重複 ID / 未定義 FR / 逆方向漏れ=実装あるが未登録）+ `check_fr_sot_alignment`（md⇔yaml 件数/ID 整合）を **warn-only** で `helix doctor` 接続

## 2. 非スコープ（TL 制約）

- helix.db table 化 / migration（**Phase 4 defer**、P0）
- `trace_symmetry.py` への統合（責務重複、別 detector に分離、P1）
- 命名規約 primary 突合（FP 多、code_paths 明示 trace + AST は補助のみ）
- fail-close 化（本 Action は **warn-only**。fail-close は changed-files ratchet + baseline clean 後 = 別 Action/段階）

## 3. forward_return

L4 基本設計追補（共通 report/YAML schema + GatePolicy baseline 凍結）→ L6 detector 契約（関数粒度仕様 + 単体テスト設計）→ L7 実装（TDD: 先に test、registry_checks.py + yaml + detector + doctor 接続）。

## 4. acceptance

- `registry_checks.py` の RegistryLoader/Entry/Report/Finding/GatePolicy が単体テストで検証される。
- `functional-registry.yaml` が 548件を機械可読で保持（code_paths/doc_paths 付き）。md⇔yaml 整合 check PASS。
- `helix doctor` で check_functional_registry / check_fr_sot_alignment が **warn-only** 動作（未登録/code_path 不在/trace drift を低 FP 報告）。
- baseline snapshot 明示。doctor 実行 30秒以内、既存 24-0-105 を退行させない。
- plan_validator / lint PASS。gate-driven push で landing（baseline と将来 fail-close commit を分離）。

## 5. carry

- functional-registry.yaml の 548件 code_paths 初期埋め（既存 code catalog / @helix:index メタ / naming から、命名 primary 禁止で半自動 + 人手検証）のコスト。
- deprecated/legacy alias の扱い（check_deprecated_registry は後続）。
