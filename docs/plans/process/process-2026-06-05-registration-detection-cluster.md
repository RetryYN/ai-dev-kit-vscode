---
plan_id: process-2026-06-05-registration-detection-cluster
title: "Process Plan: 登録・検出機械化クラスタ整備 — 機能一覧/DDD/コーディングルールの doc完備・機械ゼロ (L4 carry) を一掃"
plan_scope: process
workflow_chain: "Action1(共通基盤 RegistryLoader/Detector framework + functional-registry 縦slice: L4 schema凍結→L6 detector契約→L7 warn-only doctor接続) → Action2(coding-rule SSoT path check: L4→L6→L7) → Action3(DDD glossary/BC 構造coverage: L4→L6→L7) → [defer Phase4-5: DDD anti-corruption semantic + helix.db table化]"
kind: planning
layer: L4
drive: be
status: draft
created: 2026-06-05
owner: PM
contains_action_plans:
  - docs/plans/add-feature/add-feature-2026-06-05-registry-detector-base.md
  - docs/plans/add-feature/add-feature-2026-06-05-coding-rule-ssot.md
  - docs/plans/add-feature/add-feature-2026-06-05-ddd-registry-coverage.md
forward_return: "各 Action は L4 基本設計追補(契約/schema凍結)→L6 detector契約(関数粒度+単体テスト設計)→L7 実装/テスト で Forward に戻す。Process は全 Action の L7 完了後、G6/G7 相当の統合検証(helix doctor に check_* 群が warn→ratchet→fail-close で接続され、~10 L4-carry doctor check が実体化した状態)へ収束。V2 roadmap Phase3(detector fail-close gate化+CI連動)/Phase4(DB拡張) に内包。"
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 共通基盤の抽象境界 / phasing / baseline昇格基準 / 責務重複(trace_symmetry) の adversarial check（完了 2026-06-05 bg5o6lxwb=条件付き推奨）"
  - role: se
    slot_label: "SE — registry_checks.py 共通基盤 + 各 detector + helix doctor 接続の実装（Codex、TDD）"
generates:
  - artifact_path: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
    artifact_type: markdown_doc
dependencies:
  parent: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  requires: []
  blocks: []
related_docs:
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
  - docs/v2/L0-helix-workflows/concept.md
  - cli/lib/trace_symmetry.py
  - cli/lib/vmodel_pair_freeze.py
  - cli/helix-doctor
  - HELIX-workflows/helix-process/plan-model.md
  - HELIX-workflows/helix-process/add-feature-workflow.md
---

# 登録・検出機械化クラスタ整備 — Process（親）

> HELIX の「登録 + 検出 (drift/coverage)」が一群で **doc 完備・機械担保ゼロ (L4 carry 未実装)** という将来負債を一掃する Process。2026-06-05、user が goal「現在・将来負債をなくす」に明示追加。
> 駆動モデル = **Add-feature**（doctor check 群は L0/L3 doc に carry として設計済み・未実装 = 既存正本に機械能力を追加。要求は確定済みで Discovery 不要 = TL b48bm3o8v 確定）。Process（親）⊃ Action（子）で `forward_return` を Forward へ収束させる（plan-model.md）。

## 1. 解く問題（実体確認済み）

3 ドメインが「doc 設計は完備だが登録・検出の機械化が未実装」:

| ドメイン | doc | 機械 | 未実装 doctor check |
|---|---|---|---|
| 機能一覧 (functional-registry 548件) | ✅ (FR番号 trace列はあるが code_path 列なし) | ❌ ゼロ | check_functional_registry / check_fr_sot_alignment / check_deprecated_registry |
| DDD ドメイン (Glossary 19 + BC 10) | ✅ (5列+implementation_status) | ❌ ゼロ | check_glossary_coverage / check_ubiquitous_language / check_bc_anti_corruption / check_bc_mode_coverage |
| コーディングルール (CLAUDE.md prose 5項) | ✅ prose | ⚠️ commitlint + custom hook のみ (ruff/shellcheck/markdownlint 未設定) | check_coding_rule_sot |

`trace_symmetry.py` は `functional_registry` を `EXCLUDED_ARTIFACT_TYPES` で除外、`cli/config` に registry yaml なし、`helix_db` に glossary/bc/term table なし。~10 doctor check が「定義済み・未実装」のまま = **デグレ第一歩封鎖が機械で効いていない**。

## 2. 設計方針（TL bg5o6lxwb = 条件付き推奨）

**最小共通基盤 + functional-registry 縦 slice 先行**（最初から汎用ルールエンジン化は過剰設計 = 差戻し）。

**共通化する範囲（ここで止める）** — `cli/lib/registry_checks.py`:
- `RegistryLoader`: YAML/Markdown 由来 registry を正規化
- `RegistryEntry`: `id/name/domain/status/source_docs/traces/paths/patterns/metadata`
- `DetectorReport`: `check_name/domain/mode/baseline/findings/metrics/exit_policy`
- `Finding`: `severity(P0-P3)/kind/entry_id/path/message/remediation`
- `GatePolicy`: `advisory → ratchet warning → fail-close` の状態管理

**共通化しない**（FP 増の元）: Markdown 表の意味解釈 / FR 番号整合 / DDD anti-corruption 意味判定 / 外部 lint 導入判断。

**接続**: `helix doctor` は Bash に複雑ロジックを足さず `registry_checks.py` を呼ぶ。`--json` は text parse なので check 名・marker 形式を固定。**`trace_symmetry` の functional_registry 除外は維持**（registry は inventory SSoT で V-model 対称性 artifact でない、混ぜると責務が濁る = P1）。

## 3. Action 分割と phasing（TL 推奨順）

| Action | 範囲 | forward_return |
|---|---|---|
| **1. 共通基盤 + functional-registry** | registry_checks.py 最小基盤 + functional-registry.yaml(code_paths/doc_paths/l1_fr/l3_fr/status) + check_functional_registry/check_fr_sot_alignment を **warn-only** で doctor 接続 | L4 共通 report/YAML schema + baseline policy 凍結 → L6 functional-registry 契約固定 → L7 detector warn-only |
| **2. コーディングルール SSoT** | coding-rule SSoT (path_exists check)。lint(ruff/shellcheck/markdownlint) 導入はライセンス/CI時間判断後、まず SSoT path check まで | L4→L6→L7 |
| **3. DDD glossary/BC 構造 coverage** | check_glossary_coverage / check_ubiquitous_language / check_bc_workflow_coverage を **構造** check として追加 | L4→L6→L7 |
| (defer) DDD anti-corruption semantic | route_engine 切替時の Glossary 経由意味写像の fail-close 検証 | **Phase 4-5 defer**（semantic FP 多） |

## 4. Baseline / Fail-Close 昇格（TL）

「同時 fail-close」ではなく **同じ昇格基準**で detector 別に段階移行（成熟度差を吸収）。昇格条件:
- baseline snapshot が明示されている
- full audit で P0/P1 = 0
- changed-files gate で新規違反を止められる（**fail-close より先に changed-files ratchet = P1**）
- false positive が一定期間ゼロ
- doctor 実行が NFR-PF-01（30秒）以内

## 5. 制約（TL P0-P3）

- **P0**: helix.db table 化 / migration は今やらない（schema 変更 = escalation 条件、**Phase 4 defer**）。Action は YAML SSoT + doctor check に限定。
- **P1**: `trace_symmetry` へ functional_registry を統合しない（責務重複）→ 別 detector として doctor に集約。
- **P1**: fail-close を baseline clean 前に入れない（既存 warn 群で開発停止）→ changed-files ratchet 先行。
- **P2**: DDD は構造 coverage から（anti-corruption semantic は初期 hard gate 化しない）。
- **P2**: ruff/shellcheck/markdownlint 導入は別判断、まず SSoT path check。
- **P3**: doctor 出力は human section と JSON consumer の両方を壊さない命名。

## 6. 最大リスク（TL）

registry schema を広げすぎ「全部載るが誰も保守しない YAML」化。**最初の成功条件は汎用性でなく、functional-registry の未登録/trace drift を低 FP で検出できること**。

## 7. forward_return

各 Action L4→L6→L7。Process は全 Action L7 後、helix doctor に check_* 群が warn→ratchet→fail-close で接続され ~10 L4-carry doctor check が実体化した状態を G6/G7 統合検証へ戻す。V2 roadmap Phase3/4 に収束。

## 8. acceptance

- registry_checks.py 共通基盤 + functional-registry detector が warn-only で `helix doctor` から動作し、548件の未登録/code_path 不在/trace drift を低 FP で報告。
- coding-rule SSoT path check + DDD 構造 coverage check が doctor 接続。
- 各 detector に baseline snapshot + 昇格基準。fail-close は changed-files ratchet 先行。
- plan_validator / lint PASS、doctor 実行 30秒以内、helix doctor の既存 24-0-105 を退行させない。
- 各 Action は gate-driven push で landing（baseline と fail-close commit を分離 = TL P2）。
