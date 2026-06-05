---
doc_id: L6-functional-design-ddd-registry-detector
title: DDD registry 検出器 機能設計（Glossary / BC coverage + baseline）
status: frozen
freeze_evidence: "2026-06-06 V-model pair-freeze (L6↔L7): FN-DDD-01〜05 を DbC + YAML schema(§3, L4追補) で定義し L7 UT-DDD-01〜05 と 1:1 に固定。trace_symmetry で balance1.0/coverage100%/orphan0 を確認し、pytest / py_compile / doctor / bats / baseline 生成を通す。warn-only doctor 接続のため fail は増やさず DDD gap を surface する。"
owner: SE
process_layer: L6
pairs_test_design: docs/v2/L7-test-design/ddd-registry-detector-単体テスト設計.md
upstream_design:
  - docs/plans/add-feature/add-feature-2026-06-05-ddd-registry-coverage.md
related_requirements:
  - docs/v2/L0-helix-workflows/concept.md
verification_layers:
  - id: FN-DDD-01
    layer: L7
  - id: FN-DDD-02
    layer: L7
  - id: FN-DDD-03
    layer: L7
  - id: FN-DDD-04
    layer: L7
  - id: FN-DDD-05
    layer: L7
artifact_type: design_doc
---

# DDD registry 検出器 機能設計（Glossary / BC coverage + baseline）

> Action3 の L6 成果物。`registry_checks.py` の `Finding / GatePolicy / DetectorReport` を再利用し、`concept.md` §12 / §14 の DDD 正本を `cli/config/ddd-registry.yaml` に固定しつつ、構造 drift と coverage gap を warn-only で検出する。

## 1. 目的

- `concept.md` §12.1 の 19 用語を `glossary:` section に固定する。
- `concept.md` §14.1 の 10 BC と §14.2 の越境例を `bounded_contexts:` section と detector contract に固定する。
- `check_ubiquitous_language` は実装せず、`check_glossary_coverage` / `check_bc_anti_corruption` / `check_bc_mode_coverage` の 3 check に責務を限定する。
- baseline を deterministic に生成し、doctor warn-only 昇格の入力にする。

## 2. 設計判断

- **Action2 の複製**: loader / report / baseline / doctor helper の骨格は `coding_rule_checks.py` をミラーし、DDD 固有差分だけを `ddd_registry_checks.py` に閉じ込める。
- **専用 loader**: `registry_checks.RegistryLoader` は top-level `entries` 前提のため、`glossary:` / `bounded_contexts:` 2 section を読む `load_ddd_registry()` を専用実装する。
- **warn-only 一貫**: row drift、列欠落、BC 欄欠落、mode 漏れ、implementation gap は advisory finding に落とし、doctor fail は増やさない。
- **semantic scan defer**: `check_ubiquitous_language` は cross-doc scan で FP が高いため Phase4-5 defer とし、本 Action では扱わない。

## 3. YAML schema（L4 追補・凍結）

`cli/config/ddd-registry.yaml`: top-level 2 section。

### 3.1 `glossary`

| field | 型 | 必須 | 意味 |
|---|---|---|---|
| `term` | str | ✓ | `concept.md` §12.1 の用語名 |
| `definition` | str | ✓ | 用語の定義 |
| `cli` | str | ✓ | 対応 CLI |
| `file_path` | str | ✓ | 対応 file path |
| `schema_field` | str | ✓ | 対応 schema field |
| `grep_pattern` | str | ✓ | 検出 grep pattern |
| `implementation_status` | str | ✓ | `installed / partial / L4-carry / not-implemented`。現行 SSoT 互換として `installed / migration target` も許容する |

### 3.2 `bounded_contexts`

| field | 型 | 必須 | 意味 |
|---|---|---|---|
| `name` | str | ✓ | `Forward / Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery` |
| `kind` | str | ✓ | `forward / derived` |
| `unique_terms` | list[str] | ✓ | workflow 固有用語 |
| `anti_corruption_via` | str | ✓ | §12 Glossary 経由の写像先 |

不変条件:
- `glossary` は 19 row 以上、`bounded_contexts` は 10 row。
- `implementation_status` は 4 値 enum を基本とし、現行 SSoT の `installed / migration target` を互換値として許容する。
- `kind` は `forward / derived` 以外を許さない。
- `check_glossary_coverage` が `cli / file_path / schema_field / grep_pattern` の空欄を surface する。

## 4. 機能設計（FN-DDD-*）

| FN ID | 関数 / 公開契約 | requires | ensures | invariant |
|---|---|---|---|---|
| FN-DDD-01 | `load_ddd_registry(yaml_path)` | yaml path 存在、top-level に `glossary` と `bounded_contexts` がある | 正規化済 `DDDRegistry` を返す | section 欠落・必須 key 欠落・型違い・**BC `kind` enum 外**は `RegistryLoadError` で fail-close、部分黙殺しない。**`implementation_status` の enum 値違反は loader で fail-close せず `check_glossary_coverage` が `invalid_implementation_status` advisory finding で surface**（warn-only 方針、TL impl review P2 反映） |
| FN-DDD-02 | `check_glossary_coverage(registry_path, repo_root, concept_md_path)` | registry yaml と concept SSoT が与えられる | Glossary row drift、term drift、重複 term、列欠落、grep pattern 欠落、invalid enum、implementation gap を `DetectorReport(mode=advisory)` で返す | read-only、exit 0、`check_ubiquitous_language` は実装しない |
| FN-DDD-03 | `check_bc_anti_corruption(registry_path, repo_root, concept_md_path)` | BC section と concept §14.2 が読める | `unique_terms` / `anti_corruption_via` 欄欠落と越境例不足を `DetectorReport(mode=advisory)` で返す | read-only、越境例は §14.2 bullet を数える |
| FN-DDD-04 | `check_bc_mode_coverage(registry_path, repo_root, concept_md_path)` | BC section と concept §14.1 が読める | Forward 1 + derived 9 の coverage 不足 / 余剰を `DetectorReport(mode=advisory)` で返す | read-only、Forward は別枠で数える |
| FN-DDD-05 | `build_ddd_registry_baseline_payload(...)` / `write_ddd_registry_baseline(...)` / `main(argv)` | registry / concept path が存在 | fingerprint 付き baseline JSON を deterministic に生成し、CLI は output path を stdout へ返す | 同一入力なら byte-stable、`--emit-baseline` 以外では書き込みを行わない |

## 5. 合格基準

- 19 用語 + 10 BC が `concept.md` と `ddd-registry.yaml` の間で機械比較できる。
- FN-DDD-01〜05 が L7 UT-DDD-01〜05 と 1:1。
- doctor 接続後も fail は増えず、warn-only で DDD 構造 gap が可視化される。
- baseline JSON に `intentional_baseline / reports / fingerprint` が揃い、生成は deterministic。

## 6. L7 引き継ぎ

- 対の単体テスト設計: [ddd-registry-detector-単体テスト設計.md](../L7-test-design/ddd-registry-detector-単体テスト設計.md)
- 実装: `cli/lib/ddd_registry_checks.py` / `cli/lib/tests/test_ddd_registry_checks.py`
- doctor 接続: `cli/helix-doctor`
