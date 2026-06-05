---
plan_id: add-feature-2026-06-05-ddd-registry-coverage
title: "Action 3: DDD glossary/BC 構造 coverage — ddd-registry.yaml + check_glossary/ubiquitous/anti_corruption/bc_mode を warn-only で doctor 接続"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
workflow: add-feature
kind: add-impl
layer: L4
drive: be
status: completed
tl_review: approve  # PLAN review bnt57fdf7=changes_required(P1: check責務/trace/Bats) → 反映 → impl review boze5wqis=approve(P0/P1なし、P2-1 loader契約 doc文言を実装に精密化済、P2-2/P2-3 は carry §5)
created: 2026-06-06
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — ddd-registry schema(単一 vs 分割) / 4 check の責務境界 / concept.md §12/§14 ↔ yaml alignment 粒度 / trace_symmetry 除外 の adversarial check"
  - role: se
    slot_label: "SE — ddd_registry_checks.py + ddd-registry.yaml + 4 check + doctor 接続 + test の実装（Codex、TDD）"
generates:
  - artifact_path: cli/config/ddd-registry.yaml
    artifact_type: yaml_config
  - artifact_path: cli/lib/ddd_registry_checks.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_ddd_registry_checks.py
    artifact_type: test
  - artifact_path: cli/config/ddd-registry-baseline.json
    artifact_type: json_config
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/ddd-registry-detector-単体テスト設計.md
    artifact_type: design_doc
  # 注: L4 schema は独立 doc を作らず L6 ddd-registry-detector §3 に内包 (Action1 topology 判断を踏襲)
dependencies:
  parent: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-05-registry-detector-base.md
  blocks: []
forward_return: "L4 基本設計追補(ddd-registry YAML schema を L6 §3 に内包・凍結) → L6 detector 契約(check_glossary_coverage / check_ubiquitous_language / check_bc_anti_corruption / check_bc_mode_coverage の関数粒度仕様 FN-DDD-* + 単体テスト設計) → L7 実装(registry_checks.py 基盤を再利用した ddd_registry_checks.py + yaml + detector warn-only + doctor 接続 + TDD)。親 Process の G6/G7 統合検証へ収束。"
related_docs:
  - docs/plans/process/process-2026-06-05-registration-detection-cluster.md
  - docs/plans/add-feature/add-feature-2026-06-05-registry-detector-base.md
  - cli/lib/registry_checks.py
  - cli/lib/functional_registry_checks.py
  - cli/lib/trace_symmetry.py
  - docs/v2/L0-helix-workflows/concept.md
---

# Action 3: DDD glossary/BC 構造 coverage

> 親 Process: [登録・検出機械化クラスタ整備](../process/process-2026-06-05-registration-detection-cluster.md)。Action1 で凍結した共通基盤 (`registry_checks.py`) を**再利用**し、DDD ドメイン（ユビキタス言語 Glossary + Bounded Context）へ縦 slice する 3 本目の Action。Process を **L7 完了**へ収束させる最終 Action。

## 0. 解く問題（実体確認済み 2026-06-06）

DDD のユビキタス言語と Bounded Context は `docs/v2/L0-helix-workflows/concept.md` に**完備（doc）だが機械担保ゼロ**:

| ドメイン | 正本 | 既存機械 | 本 Action で実体化する doctor check |
|---|---|---|---|
| Glossary（ユビキタス言語 SSoT） | concept.md §12.1（**19 語**、5 列分割 + implementation_status） | ❌ ゼロ | `check_glossary_coverage`（列充足）|
| Bounded Context | concept.md §14.1（**10 行** = Forward 本体 1 + 派生 9）+ §14.2 越境例 | ❌ ゼロ | `check_bc_anti_corruption` / `check_bc_mode_coverage` |

**check 責務は concept.md §12.2 を SSoT とする**（TL bnt57fdf7 P1 で責務取り違えを是正）:
- `check_glossary_coverage` = 「各用語の対応 CLI / file path / schema field 列が空でないか」（列充足）。本 Action で実体化。
- `check_ubiquitous_language` = 「L1-L14 doc 内の表記ゆれ / 未定義用語を warn」（**全 doc 横断の semantic scan、FP 高い・重い**）→ **Phase 4-5 defer**（§5 carry）。本 Action は構造 coverage に限定するため scope 外と明記。
- `check_bc_anti_corruption` / `check_bc_mode_coverage` = BC 構造 coverage。本 Action で実体化。

→ 本 Action は **3 check**（glossary_coverage / bc_anti_corruption / bc_mode_coverage）を実体化し、`check_ubiquitous_language`（cross-doc semantic）は defer。

L3 要件は機械判定基準を既に定義済み（AC-12: Glossary row ≥ 14 + 3 列充足 / AC-14: BC row = 10 = Forward 1 + 派生 9 + §14.2 越境 ≥ 3 / AC-15: `helix doctor check_*` carry ≥ 6 を L4 凍結）。本 Action はこの AC を**機械で実体化**する。

## 1. スコープ

**ddd-registry**（`cli/config/ddd-registry.yaml`、単一 yaml に 2 section = TL bnt57fdf7 単一推奨）:
- `glossary:` — concept.md §12.1 の 19 語を各 entry 化。`term` / `definition` / `cli` / `file_path` / `schema_field` / `grep_pattern` / `implementation_status`（installed / partial / L4-carry / not-implemented）。
- `bounded_contexts:` — concept.md §14.1 の 10 行を各 entry 化。`name`（Forward / Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery）/ `kind`（forward / derived）/ `unique_terms` / `anti_corruption_via`（越境写像先）。
- 注（TL P2）: `registry_checks.RegistryLoader` は top-level `entries` 前提のため、**DDD 専用 loader**（2 section を読む）を L6 §3 に明記して設計する（Action1 が functional-registry 専用 loader を持つのと同型）。

**検出契約**（Action1 `registry_checks.py` の `Finding` / `GatePolicy` / `DetectorReport` を再利用、**3 check** を warn-only で `helix doctor` 接続。md↔yaml alignment は各 check に内包 = 独立 alignment check 不要 = TL P2）:
- `check_glossary_coverage`: §12.1 ↔ yaml の Glossary 件数整合（row ≥ 19、md⇔yaml drift を warn）+ 重複 term + 各 entry の `cli` / `file_path` / `schema_field` 3 列充足（§12.2 SSoT 定義）+ `grep_pattern` 存在 + `implementation_status` valid enum。
- `check_bc_anti_corruption`: 各 BC entry に `unique_terms` + `anti_corruption_via` が充足 + §14.2 越境例 ≥ 3。
- `check_bc_mode_coverage`: BC entries が Forward 1 + 派生 9 workflow（Scrum/Discovery/Reverse/Incident/Add-feature/Refactor/Retrofit/Research/Recovery）を**全件 cover**（mode 漏れ検出。checker は Forward を別枠で数える = AC-14）。

## 2. 非スコープ（Action1 と同じ warn-only 哲学を継承）

- **helix.db への glossary/bc/term table 化 / migration**（**Phase 4-5 defer**、TL b48bm3o8v）。本 Action は yaml + md の構造 coverage に留める。
- **DDD anti-corruption の semantic 照合**（用語の意味写像が正しいか）= **Phase 4-5 defer**。本 Action は `anti_corruption_via` 欄の**充足有無**（構造）のみ。
- `check_ubiquitous_language`（L1-L14 全 doc 横断の表記ゆれ / 未定義用語 semantic scan、§12.2 SSoT 定義）= **Phase 4-5 defer**（FP 高・全 doc 走査で重い）。本 Action の `check_glossary_coverage` は §12.1 表内の列充足に限定（混同しない = TL P1）。
- `trace_symmetry.py` の `EXCLUDED_ARTIFACT_TYPES` 追加は **ddd-registry の data/mirror artifact にのみ適用**。L6/L7 detector 設計 doc は `artifact_type: design_doc` を維持し **pair freeze 対象に残す**（functional_registry も L3 catalog doc のみ除外し detector 設計 doc は除外していないのと同型 = TL P1）。本体ロジック統合はしない。
- fail-close 化（本 Action は **warn-only**。fail-close 昇格は baseline clean 後 = 別段階）。
- concept.md 本文の自然言語パース（定義文の意味照合）。表 row 単位の構造件数・列充足に留める（FP 回避）。

## 3. forward_return

L4 基本設計追補（ddd-registry YAML schema を L6 §3 に内包・凍結）→ L6 detector 契約（4 check の関数粒度仕様 FN-DDD-* + 単体テスト設計 UT-DDD-*）→ L7 実装（TDD: 先に test、`ddd_registry_checks.py`（registry_checks 基盤再利用）+ yaml + 4 detector + doctor 接続）。親 Process の G6/G7 統合検証（~10 L4-carry doctor check 実体化）へ収束 = **Process 完了 trigger**。

## 4. acceptance

- `ddd-registry.yaml` が concept.md §12.1 の 19 語 + §14.1 の 10 BC（Forward 1 + 派生 9）を機械可読に保持。
- **3 check** が **warn-only** で動作: Glossary 件数 drift / 3 列未充足 / BC anti-corruption 欄欠落 / mode 漏れを低 FP 報告。各 check は concept.md §12/§14 の表 row を parse し yaml と突合（md⇔yaml alignment を内包）。`check_ubiquitous_language`（cross-doc semantic）は defer（§2）。
- **machine baseline snapshot**（`cli/config/ddd-registry-baseline.json`、fingerprint 付き）を明示し ratchet 昇格の入力契約とする（Action1 と同型）。Action3 で追加した自資産（ddd_registry_checks.py / ddd-registry.yaml）は **functional-registry.yaml にも登録**し自己未登録を残さない。
- `helix doctor` で 3 check が warn-only 動作、既存 doctor を **0 fail 維持**（warn 増のみ）、doctor 実行 30 秒以内。**doctor 配線の Bats 最小テスト**を追加（section 名 / WARN 増 / 既存 FAIL 不増。`bash -n` だけでは不足 = TL bnt57fdf7）。
- L6↔L7 設計対（FN-DDD-* ↔ UT-DDD-*）が trace_symmetry で balance ~1.0 / coverage 100% / orphan 0 / wrong_layer_pair 0（`verification_layers=L7`、既存 frozen pair 退行なし）。L6/L7 detector 設計 doc は `artifact_type: design_doc` を維持（pair freeze 対象）。`EXCLUDED_ARTIFACT_TYPES` への `ddd_registry` 追加は registry data/mirror artifact にのみ適用し detector 設計 doc には付けない（TL P1）。
- plan_validator / lint PASS。gate-driven push で landing。**Process PLAN を全 Action L7 完了で収束更新**（status / forward_return 到達記録）。

## 5. carry

- helix.db table 化（glossary / bc / term）と DDD anti-corruption semantic 照合（Phase 4-5）。
- `check_ubiquitous_language`（§12.2 SSoT = L1-L14 全 doc 横断の表記ゆれ / 未定義用語 semantic scan）の実体化（Phase 4-5。本 Action は構造 coverage の 3 check に限定）。
- **（TL impl review boze5wqis P2-2）** `check_glossary_coverage` は term/件数 alignment 中心で `implementation_status` の SSoT 値そのものは concept.md と比較しない。enum 内で concept 側 status が変わっても drift 検出できない → status 値 alignment 強化（fail-close 昇格時、parser 改修を伴う）。
- **（TL impl review boze5wqis P2-3）** markdown table parser は `|` split ベースで escaped pipe を含む列値比較に弱い。status/value alignment を追加する際に小さく分離・堅牢化する。
- 4 check の fail-close 昇格（gap=0 達成後）。
- L1-L14 の各 doc が §12 Glossary を parent_doc reference で参照しているかの trace（anti-corruption layer 遵守の検出）は後続（本 Action は §12/§14 の構造 coverage に限定）。
