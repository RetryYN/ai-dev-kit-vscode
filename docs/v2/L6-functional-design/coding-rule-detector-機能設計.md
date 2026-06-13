---
doc_id: L6-functional-design-coding-rule-detector
title: coding-rule 検出器 機能設計（YAML schema + 検出契約 / DbC）
status: frozen
freeze_evidence: "2026-06-06 V-model pair-freeze (L6↔L7): FN-CRREG-01〜04 を DbC + YAML schema(§3, L4追補) で定義し L7 UT-CRREG-01〜04 と 1:1。trace_symmetry で balance1.0/coverage100%/orphan0 を確認し、pytest / py_compile / doctor / bats / baseline 生成を通す。warn-only doctor 接続のため fail は増やさず gap を surface する。"
owner: SE
process_layer: L6
pairs_test_design: docs/v2/L7-test-design/coding-rule-detector-単体テスト設計.md
upstream_design:
  - docs/plans/add-feature/add-feature-2026-06-05-coding-rule-ssot.md
related_requirements:
  - CLAUDE.md
verification_layers:
  - id: FN-CRREG-01
    layer: L7
  - id: FN-CRREG-02
    layer: L7
  - id: FN-CRREG-03
    layer: L7
  - id: FN-CRREG-04
    layer: L7
artifact_type: design_doc
---

# coding-rule 検出器 機能設計（YAML schema + 検出契約 / Design by Contract）

> Action2 の L6 成果物。`registry_checks.py` の `Finding / GatePolicy / DetectorReport` を再利用し、`CLAUDE.md` の 14 ルールを `cli/config/coding-rule-registry.yaml` に固定しつつ、mechanical enforcement の有無を warn-only で検出する。

## 1. 目的

- `CLAUDE.md` の prose ルールを 14 entry の YAML SSoT に固定する。
- enforcement path の実在、status と path の整合、self asset の functional-registry 登録漏れを検出する。
- `CLAUDE.md` 3 節の bullet 件数と registry entry 件数の drift を検出する。
- baseline を deterministic に生成し、doctor warn-only 昇格の入力にする。

## 2. 設計判断

- **Action1 の複製**: loader / report / baseline / doctor の骨格は `functional_registry_checks.py` をミラーし、domain 固有差分だけを `coding_rule_checks.py` に閉じ込める。
- **warn-only 一貫**: `manual / partial / not-implemented` は既知 gap として P3 warning に落とし、fail-close へ昇格させない。
- **self asset 逆方向漏れ**: `coding_rule_checks.py` と `coding-rule-registry.yaml` は `functional-registry.yaml` への登録を必須にし、reverse leak を detector 自身が検出する。
- **自然言語解析の限定**: `CLAUDE.md` は 3 見出し配下の bullet 数だけを見る。文意一致や sentence diff までは扱わない。

## 3. YAML schema（L4 追補・凍結）

`cli/config/coding-rule-registry.yaml`: top-level `entries: list`、各 entry:

| field | 型 | 必須 | 意味 |
|---|---|---|---|
| `id` | str | ✓ | `CR-CODE-01` 形式の固定 ID |
| `rule` | str | ✓ | CLAUDE.md rule の要約 |
| `sot_section` | str | ✓ | `コーディング規約` / `コミット規約` / `禁止事項` |
| `enforcement.kind` | str | ✓ | `lint_config / hook / commitlint / ci_gate / manual` |
| `enforcement.paths` | list[str] | ✓（空可） | 実在 enforcement file path |
| `enforcement.status` | str | ✓ | `enforced / partial / manual / not-implemented` |

不変条件:
- `sot_section` は 3 見出し enum のみ。
- `enforcement.kind` / `enforcement.status` は enum 外を許さない。
- `status=enforced` で `paths=[]` は schema error ではなく detector finding として surface する。

## 4. 機能設計（FN-CRREG-*）

| FN ID | 関数 / 公開契約 | requires | ensures | invariant |
|---|---|---|---|---|
| FN-CRREG-01 | `load_coding_rule_registry(yaml_path)` | yaml path 存在 | 正規化済 `list[CodingRuleEntry]` を返す | 必須欠落・enum 外は `RegistryLoadError` で fail-close、部分黙殺しない |
| FN-CRREG-02 | `check_coding_rule_sot(registry_path, repo_root)` | registry yaml と repo root が与えられる | enforcement gap、missing path、status/path mismatch、self asset 未登録を `DetectorReport(mode=advisory)` で返す | read-only、exit 0、functional-registry 登録漏れも warn-only |
| FN-CRREG-03 | `check_coding_rule_alignment(claude_md_path, registry_path)` | CLAUDE.md と registry path が存在 | total count と per-section count drift を `DetectorReport(mode=advisory)` で返す | read-only、3 見出し配下 bullet のみ数える |
| FN-CRREG-04 | `build_coding_rule_baseline_payload(...)` / `write_coding_rule_baseline(...)` / `main(argv)` | registry / CLAUDE.md path が存在 | fingerprint 付き baseline JSON を deterministic に生成し、CLI は output path を stdout へ返す | 同一入力なら byte-stable、`--emit-baseline` 以外では書き込みを行わない |

### 4.1 Finding vocabulary

governance hardening map へ渡す finding type は以下に固定する。現在フェーズでは warn-only / advisory の設計語彙であり、fail-close 実装や L7 closure ではない。

- `missing_rule`
- `duplicate_rule`
- `stale_rule_status`
- `rule_source_missing`

## 5. 合格基準

- 14 entry registry が `CLAUDE.md` の 5+5+4 rule と一致する。
- FN-CRREG-01〜04 が L7 UT-CRREG-01〜04 と 1:1。
- doctor 接続後も fail は増えず、warn-only で gap が可視化される。
- baseline JSON に `intentional_baseline / reports / fingerprint` が揃い、生成は deterministic。

## 6. L7 引き継ぎ

- 対の単体テスト設計: [coding-rule-detector-単体テスト設計.md](../L7-test-design/coding-rule-detector-単体テスト設計.md)
- 実装: `cli/lib/coding_rule_checks.py` / `cli/lib/tests/test_coding_rule_checks.py`
- doctor 接続: `cli/helix-doctor`
