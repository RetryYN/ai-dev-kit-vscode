---
plan_id: add-feature-2026-06-05-coding-rule-ssot
title: "Action 2: コーディングルール SSoT path check — coding-rule-registry.yaml + check_coding_rule_sot を warn-only で doctor 接続"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
workflow: add-feature
kind: add-impl
layer: L4
drive: be
status: completed
tl_review: approve  # PLAN review bnt57fdf7=changes_required(P1: 14entry/check責務/trace/Bats) → 反映 → impl review b5dc2tltq=approve(P0/P1なし、P2 id重複check/P3 parser脆弱性は carry §5)
created: 2026-06-06
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — coding-rule registry schema / enforcement_path 契約 / SSoT alignment 粒度 / linter 導入 defer 妥当性 の adversarial check"
  - role: se
    slot_label: "SE — coding_rule_checks.py + coding-rule-registry.yaml + check 群 + doctor 接続 + test の実装（Codex、TDD）"
generates:
  - artifact_path: cli/config/coding-rule-registry.yaml
    artifact_type: yaml_config
  - artifact_path: cli/lib/coding_rule_checks.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_coding_rule_checks.py
    artifact_type: test
  - artifact_path: cli/config/coding-rule-registry-baseline.json
    artifact_type: json_config
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: docs/v2/L6-functional-design/coding-rule-detector-機能設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/coding-rule-detector-単体テスト設計.md
    artifact_type: design_doc
  # 注: L4 schema は独立 doc を作らず L6 coding-rule-detector §3 に内包 (Action1 topology 判断を踏襲)
dependencies:
  parent: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-05-registry-detector-base.md
  blocks: []
forward_return: "L4 基本設計追補(coding-rule registry YAML schema を L6 §3 に内包・凍結) → L6 detector 契約(check_coding_rule_sot / check_coding_rule_alignment の関数粒度仕様 FN-CRREG-* + 単体テスト設計) → L7 実装(registry_checks.py 基盤を再利用した coding_rule_checks.py + yaml + detector warn-only + doctor 接続 + TDD)。親 Process の G6/G7 統合検証へ収束。"
related_docs:
  - docs/plans/process/process-2026-06-05-registration-detection-cluster.md
  - docs/plans/add-feature/add-feature-2026-06-05-registry-detector-base.md
  - cli/lib/registry_checks.py
  - cli/lib/functional_registry_checks.py
  - CLAUDE.md
  - .commitlintrc.json
---

# Action 2: コーディングルール SSoT path check

> 親 Process: [登録・検出機械化クラスタ整備](../process/process-2026-06-05-registration-detection-cluster.md)。Action1 で凍結した共通基盤 (`registry_checks.py`: RegistryLoader / RegistryEntry / Finding / GatePolicy / DetectorReport) を**再利用**し、coding-rule ドメインへ縦 slice する 2 本目の Action。

## 0. 解く問題（実体確認済み 2026-06-06）

コーディングルールは `CLAUDE.md` の **prose** で SSoT 化されているが、各ルールの**機械強制が散在 or 不在**で「宣言されているが効いていない」状態を機械で検出できない:

| SSoT 節 (CLAUDE.md) | ルール数 | 既存機械強制 | gap |
|---|---|---|---|
| `## コーディング規約` | 5 | Python: py_compile / Bash: bash -n は CI 手動運用。**ruff / shellcheck / markdownlint 未設定**（`pyproject.toml` は pytest 設定のみ、`.shellcheckrc` / `.markdownlint.*` / `ruff.toml` 不在） | lint 強制が prose 依存 |
| `## コミット規約` | 5 | `.commitlintrc.json` (prefix / scope enum) + commit-msg hook | prefix/scope のみ、責務分割・大型分割・自動生成物除外は prose 依存 |
| `## 禁止事項` | 4 | push gate G-secret (secret scan) + pretooluse guard 群 | secret は機械、認可/license/外部SDK fallback/runtime state 追跡禁止 は prose 依存 |

→ **`check_coding_rule_sot` が未実装** = 「ルール SSoT ↔ 強制機構」の対応が機械担保ゼロ。ルールを CLAUDE.md から消しても・強制機構の設定ファイルを消しても誰も検出しない = デグレ第一歩。

## 1. スコープ

**coding-rule registry** (`cli/config/coding-rule-registry.yaml`):
- CLAUDE.md の 3 節（コーディング規約 / コミット規約 / 禁止事項）の各ルールを 1 entry として登録。各 entry に:
  - `id`（`CR-CODE-01` 等）/ `rule`（要約）/ `sot_section`（CLAUDE.md の節見出し）
  - `enforcement`: `kind`（lint_config / hook / commitlint / ci_gate / manual）/ `paths`（強制機構の実体ファイル path、複数可）/ `status`（enforced / partial / manual / not-implemented）

**検出契約** (Action1 `registry_checks.py` を再利用、warn-only で `helix doctor` 接続):
- `check_coding_rule_sot`: 各 entry の `enforcement.paths` が**実在するか**（不在=機械強制が宣言だけ）/ `status` と paths の整合（status=enforced なのに paths 不在 = FP risk finding）/ 自己資産（coding_rule_checks.py / yaml）の未登録逆方向漏れ。
- `check_coding_rule_alignment`: CLAUDE.md の 3 節に書かれた prose ルール数 ↔ yaml entry 数の整合（md⇔yaml drift を warn-only baseline で surface。Action1 `check_fr_sot_alignment` と同型）。

## 2. 非スコープ（Action1 と同じ warn-only 哲学を継承）

- **linter の新規導入・設定**（ruff / shellcheck / markdownlint の config 追加と全コードへの適用）= **defer**。本 Action は「強制機構が宣言と一致するか」の検出のみ。linter 導入は全コードに findings を生む別判断（影響大）で、別 Action / 段階。registry は不在を `status: not-implemented` として**正直に記録**し warn する。
- helix.db table 化 / migration（**Phase 4 defer**）。
- `trace_symmetry.py` への統合（責務重複、別 detector に分離）。
- fail-close 化（本 Action は **warn-only**。fail-close 昇格は baseline clean + changed-files ratchet 後 = 別段階）。
- CLAUDE.md prose の自然言語パース（ルール文の意味照合）。entry は prose を要約した手動 registry で、節見出し単位の件数整合に留める（FP 回避）。

## 3. forward_return

L4 基本設計追補（coding-rule registry YAML schema を L6 §3 に内包・凍結）→ L6 detector 契約（`check_coding_rule_sot` / `check_coding_rule_alignment` の関数粒度仕様 FN-CRREG-* + 単体テスト設計 UT-CRREG-*）→ L7 実装（TDD: 先に test、`coding_rule_checks.py`（registry_checks 基盤再利用）+ yaml + detector + doctor 接続）。親 Process の G6/G7 統合検証へ収束。

## 4. acceptance

- `coding-rule-registry.yaml` が CLAUDE.md の 3 節の全ルール（コーディング規約 5 + コミット規約 5 + 禁止事項 4 = **14 entry**、TL bnt57fdf7 P1 で実体確認）を `enforcement.{kind,paths,status}` 付きで機械可読に保持。entry 粒度は**個別ルール単位**（節見出し単位は粗すぎ = TL P1）。
- `check_coding_rule_sot` が **warn-only** で動作: enforcement.paths 不在 / status⇔paths 不整合 / 自己資産未登録を低 FP 報告。`status: not-implemented` の entry は warn として可視化（PASS でなく既知 gap の surface が正）。
- `check_coding_rule_alignment` が CLAUDE.md 3 節の prose ルール件数 ↔ yaml entry 件数差を warn-only baseline で surface。
- **machine baseline snapshot**（`cli/config/coding-rule-registry-baseline.json`、fingerprint 付き）を明示し ratchet 昇格の入力契約とする（Action1 と同型）。Action2 で追加した自資産（coding_rule_checks.py / coding-rule-registry.yaml）は **functional-registry.yaml にも登録**し自己未登録を残さない（Action1 P1 自資産 registration を踏襲）。
- `helix doctor` で 2 check が warn-only 動作、既存 doctor を **0 fail 維持**（warn 増のみ）、doctor 実行 30 秒以内。**doctor 配線の Bats 最小テスト**を追加（section 名表示 / WARN 増 / 既存 FAIL 不増を検証。`bash -n cli/helix-doctor` だけでは守れない = TL bnt57fdf7 テスト戦略）。
- L6↔L7 設計対（FN-CRREG-* ↔ UT-CRREG-*）が trace_symmetry で balance ~1.0 / coverage 100% / orphan 0 / wrong_layer_pair 0（`verification_layers=L7`、Action1 と同じ pair freeze 方式で既存 frozen pair を退行させない）。
- plan_validator / lint PASS。gate-driven push で landing。

## 5. carry

- linter（ruff / shellcheck / markdownlint）の正式導入と既存コードへの適用（findings 解消含む）は別 Action。本 Action はその gap を registry に `not-implemented` で記録し warn するに留める。
- `check_coding_rule_sot` の fail-close 昇格（gap=0 達成後）。
- pretooluse guard 群（hook）と registry entry の網羅対応精緻化（hook 実体 path の自動追従）。
- **（TL impl review b5dc2tltq P2）** `duplicate_id` / id pattern（`CR-{SECTION}-NN`）finding の追加。現物は一意だが count alignment だけでは将来の重複・形式崩れを検出しにくい。ratchet（fail-close）昇格前に追加する。
- **（TL impl review b5dc2tltq P3）** CLAUDE.md parser は `## <固定見出し>` + 直下 `- ` bullet 前提で見出し改名・説明 bullet 追加に弱い。warn-only 方針とは整合するが fail-close 昇格時に堅牢化する。
