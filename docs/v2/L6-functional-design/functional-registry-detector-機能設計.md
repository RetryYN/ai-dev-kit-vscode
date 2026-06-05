---
doc_id: L6-functional-design-functional-registry-detector
title: functional-registry 検出器 機能設計（YAML schema + 検出契約 / DbC）
status: frozen
freeze_evidence: "2026-06-05 V-model pair-freeze (L6↔L7): FN-FREG-01〜03 を DbC + YAML schema(§3, L4追補) で定義し L7 UT-FREG-01〜03 と 1:1。trace_symmetry L6↔L7 balance1.0/coverage100%/orphan0、exit0。Codex se TDD 実装 (cli/lib/functional_registry_checks.py, base registry_checks の Finding/GatePolicy/DetectorReport 再利用) を PM 独立検証: py_compile PASS / pytest 3/3 PASS / read-only invariant (yaml sha256 不変) PASS / advisory exit_policy=0 PASS。helix doctor [functional registry] section に warn-only 接続: 53 finding (P3×44 FR-trace不備 / P2×9 path不在+逆方向漏れ) + 1 md_name_set_mismatch を検出、結果 25-0-106 (FAIL 不増=warn-only 担保)。doctor rc=0 5s"
owner: SE
process_layer: L6
pairs_test_design: docs/v2/L7-test-design/functional-registry-detector-単体テスト設計.md
upstream_design:
  - docs/v2/L6-functional-design/registry-detector-機能設計.md
related_requirements:
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
related_decision: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
verification_layers:
  - id: FN-FREG-01
    layer: L7
  - id: FN-FREG-02
    layer: L7
  - id: FN-FREG-03
    layer: L7
---

# functional-registry 検出器 機能設計（YAML schema + 検出契約 / Design by Contract）

> Action1b の L6 成果物。`registry_checks.py`（base, FN-RDB-*）の `Finding/GatePolicy/DetectorReport` を**再利用**し、機能一覧（548件）の機械正本 `functional-registry.yaml` と、その劣化検出 `check_functional_registry` / `check_fr_sot_alignment` を **warn-only** で固定する。L4 基本設計追補（YAML schema 凍結）を本 doc §3 に内包する。

## 1. 目的と範囲

- 範囲: ①`cli/config/functional-registry.yaml` の schema（L4 追補）②`cli/lib/functional_registry_checks.py` の 2 検出器 + 1 補助関数の関数契約（FN-FREG-01〜03）。
- 非範囲: fail-close 実運用昇格（warn-only で完了。昇格は `GatePolicy.promote` の後続 Action）、命名 primary 突合、helix.db table 化（Phase4）、coding-rule / DDD（Action2/3）。
- 検証層: 全 FN-FREG-* は **L7 単体テスト**で検証（`verification_layers=L7`、L4↔L9 trace 対象外）。

## 2. 設計上の判断（PM 確定 2026-06-05）

- **schema 分離**: base（`registry_checks.RegistryEntry`）は汎用。機能一覧は `l1_fr/l3_fr` 等 trace 固有 field を持つため、専用 `FunctionalRegistryEntry` を `functional_registry_checks.py` に置く（base の `Finding/GatePolicy/DetectorReport` は再利用）。
- **code_paths 粒度**: 資産自身の primary path のみ（`helix-agent`→`cli/helix-agent`）。推移的依存は列挙しない（自動化困難・FP 源）。
- **deprecated**: YAML に `status` 付きで保持（registry は完全性を保つ）。検出器は deprecated entry の code_path 不在を warn しない（special-case）。
- **件数 drift**: YAML は実ファイル（`find`）件数を真とする。md（§2=139 / §4=140 の不整合）との差は `check_fr_sot_alignment` が surface する。

## 3. YAML schema（L4 追補・凍結対象）

`cli/config/functional-registry.yaml`: top-level `entries: list`、各 entry:

| field | 型 | 必須 | 意味 |
|---|---|---|---|
| `id` | str | ✓ | 連番 ID（例 `FR-CLI-001`、機械生成・不変） |
| `name` | str | ✓ | 資産名（CLI 名 / module / skill-id 等） |
| `domain` | str | ✓ | `cli\|lib\|hook\|agent\|skill\|workflow\|template` |
| `description` | str | ✓ | md の主機能 / 責務列 |
| `l1_fr` | list[str] | ✓（空可） | 関連 L1 FR ID |
| `l3_fr` | list[str] | ✓（空可） | 関連 L3 FR ID |
| `status` | str | ✓ | `active\|deprecated\|legacy_alias\|mandatory\|experimental` |
| `code_paths` | list[str] | ✓（空可） | 資産 primary path（repo 相対） |
| `doc_paths` | list[str] | ✓（空可） | skill/workflow/template の doc path |

不変条件: `id` 一意、`domain` は enum、`active` entry は `code_paths` か `doc_paths` の少なくとも一方が非空であることが**健全**（違反は warn）。

## 4. 機能設計（FN-FREG-* 定義）

| FN ID | 関数 / 公開契約 | requires | ensures | invariant |
|---|---|---|---|---|
| FN-FREG-01 | `check_functional_registry(registry_path, repo_root)`（劣化検出） | yaml path 存在 | 4 クラスの Finding を持つ `DetectorReport`（mode=advisory）: ①`code_paths`/`doc_paths` の path 不在（P2）②重複 `id`（P1）③`l1_fr`/`l3_fr` の ID 形式不正・空（active のみ, P3）④**逆方向漏れ**=disk 上に実在するが registry 未登録の資産（P2） | **read-only**（registry/disk を変更しない）・**warn-only**（advisory: exit 0）・deprecated entry の path 不在は finding 化しない |
| FN-FREG-02 | `check_fr_sot_alignment(md_path, yaml_path)`（SSoT 整合） | 両 path 存在 | md⇔yaml の件数差・name 集合差を Finding 化した `DetectorReport`（mode=advisory） | read-only・warn-only・件数の真は yaml（disk 実体由来）側 |
| FN-FREG-03 | `load_functional_registry(yaml_path)`（専用 loader） | yaml path 存在 | 正規化済 `list[FunctionalRegistryEntry]` | 解析不能・schema 違反（必須欠落・enum 外 domain）は `RegistryLoadError` で fail-close（部分黙殺禁止） |

## 5. 合格基準（G6 → L7）

- FN-FREG-01〜03 が L7 UT-FREG-01〜03 と 1:1（trace_symmetry L6↔L7 balance 維持）。
- 逆方向漏れ（④）と重複 id（②）の検出が UT で反証される（= 劣化検出の核）。
- 検出器は `registry_checks` の `Finding/GatePolicy/DetectorReport` を再利用し warn-only。
- 実装は TDD（UT 先行）。

## 6. L7 / doctor への引き継ぎ

- 対の単体テスト設計: [functional-registry-detector-単体テスト設計.md](../L7-test-design/functional-registry-detector-単体テスト設計.md)。
- 実装: `cli/lib/functional_registry_checks.py` / `cli/lib/tests/test_functional_registry_checks.py`。
- doctor 接続（warn-only, `[functional registry]` セクション）: `cli/helix-doctor` 末尾実行ブロック。
