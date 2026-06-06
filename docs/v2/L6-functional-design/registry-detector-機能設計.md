---
doc_id: L6-functional-design-registry-detector
title: 登録・検出 共通基盤 機能設計（関数仕様 / DbC）
status: frozen
freeze_evidence: "2026-06-05 V-model pair-freeze (L6↔L7 base): FN-RDB-01〜07 を DbC で定義し L7 UT-RDB-01〜07 と 1:1。trace_symmetry detector で L6 design entries 21 (既存14+RDB7)・balance1.0/coverage100%/orphan0/missing-pair0、exit0。Codex se TDD 実装 (cli/lib/registry_checks.py) を PM 独立検証: py_compile PASS / pytest 7/7 PASS / 10 invariant 直接 probe PASS (advisory=exit0[P0でも] / fail_close=P0,P1で非0 / ratchet=baseline比新規のみ / promote 段階skip拒否+evidence不足は非昇格[fail-close既定] / load malformed→RegistryLoadError 部分黙殺なし)。doctor 25-0-104 を A/B isolation で neutral 確認。base 契約のみ凍結 (個別 detector 契約は Action1b L6 追補)"
owner: SE
process_layer: L6
pairs_test_design: docs/v2/L7-test-design/registry-detector-単体テスト設計.md
upstream_design:
  - docs/v2/L4-basic-design/方式設計.md
related_requirements:
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
related_decision: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
verification_layers:
  - id: FN-RDB-01
    layer: L7
  - id: FN-RDB-02
    layer: L7
  - id: FN-RDB-03
    layer: L7
  - id: FN-RDB-04
    layer: L7
  - id: FN-RDB-05
    layer: L7
  - id: FN-RDB-06
    layer: L7
  - id: FN-RDB-07
    layer: L7
---

# 登録・検出 共通基盤 機能設計（関数仕様 / Design by Contract）

> Action1（`add-feature-2026-06-05-registry-detector-base`）の L6 成果物。registration-detection cluster の **共通基盤**（RegistryLoader / RegistryEntry / DetectorReport / Finding / GatePolicy）を関数粒度（DbC）で固定し、L7 単体テスト（`registry-detector-単体テスト設計.md`）と 1:1 で対にする。functional-registry.yaml の 548 件 data fill と doctor 接続は **Action1b 以降**（本 doc は基盤クラスの契約のみ）。

## 1. 目的と範囲

- 範囲: `cli/lib/registry_checks.py` が提供する 5 つの基盤型と、その公開メソッドの契約。
- 非範囲: 個別 detector の判定ロジック（check_functional_registry 等）、YAML data の中身、doctor への配線、ratchet/fail-close の実運用昇格（= 後続 Action）。本 doc は **GatePolicy の状態機械の契約**は定義するが、advisory（warn-only）以外の実走は Action1 では行わない。
- 検証層: 全 FN-RDB-* は **L7 単体テスト**で検証する（component/system 粒度の L9 ではない）。frontmatter `verification_layers` で L7 を宣言し、L4↔L9 trace の対象外とする。

## 2. DbC 表記

- **requires**: 呼び出し側が満たすべき事前条件。
- **ensures**: 正常終了時に関数が保証する事後条件。
- **invariant**: 異常系を含め常に保たれる不変条件（fail-close 方針はここに書く）。
- severity 階梯: `P0`（即時破綻）/ `P1`（要修正）/ `P2`（劣化）/ `P3`（情報）。

## 3. 機能設計（FN-RDB-* 定義）

| FN ID | 関数 / 公開契約 | 所属型 | requires | ensures | invariant |
|---|---|---|---|---|---|
| FN-RDB-01 | `RegistryLoader.load(source)`（registry を正規化して読む） | RegistryLoader | `source` path 存在 + 形式既知（yaml / markdown） | 正規化済 `list[RegistryEntry]` を返す | 解析不能・必須 field 欠落は `RegistryLoadError` で fail-close（部分黙殺・silent drop 禁止） |
| FN-RDB-02 | `RegistryEntry.validate()`（1 件の検証・正規化） | RegistryEntry | raw mapping（id を含む） | `id/name/domain/status` 充足、`paths/patterns/traces` を list へ正規化 | 必須 field 欠落は `ValidationError`（silent default 生成 禁止） |
| FN-RDB-03 | `Finding(severity, kind, entry_id, path, message, remediation)` | Finding | `severity ∈ {P0,P1,P2,P3}` | 不変（frozen）record を生成 | enum 外 severity / 空 kind は生成時 error |
| FN-RDB-04 | `DetectorReport.build(check_name, domain, mode, findings, metrics, baseline)` | DetectorReport | `findings: list[Finding]` + `mode` | `exit_policy` を `GatePolicy.decide` から導出した report を返す | `mode ∈ {advisory, ratchet, fail_close}` 以外は error |
| FN-RDB-05 | `GatePolicy.decide(mode, findings, baseline)` | GatePolicy | `mode` + `findings` + `baseline` snapshot | advisory→`exit 0`（findings 有でも）/ ratchet→baseline 比 **新規**違反のみ非0 / fail_close→`P0/P1` 存在で非0 | advisory は決して build を fail させない（exit 0 固定） |
| FN-RDB-06 | `GatePolicy.promote(state, evidence)`（昇格状態機械） | GatePolicy | 現 `state` + 昇格 `evidence`（baseline_clean / full_audit_p0p1_zero / changed_files_ratchet / fp_zero_period / perf_within_nfr） | 次 state（`advisory→ratchet→fail_close`）を返す | 段階 skip 不可・evidence 5 条件を満たさない昇格は拒否（fail-close 既定） |
| FN-RDB-07 | `DetectorReport.render(fmt)`（出力直列化） | DetectorReport | `fmt ∈ {text, json}` | 人間可読 / 機械可読出力を返す | 決定的順序（findings は `severity, entry_id` で安定ソート） |

### 3.1 FN-RDC-* — registry_design_coverage detector（zero-omission B' 機械証明、Action4）

| FN ID | 関数 / 役割 | モジュール | requires | ensures | invariant |
|---|---|---|---|---|---|
| FN-RDC-01 | `check_registry_design_coverage(registry_path, repo_root)`（全 active entry の設計層被覆検査） | registry_design_coverage_checks | `registry_path` 存在・yaml load 可 | active entry ごとに coverage_layer/design_ids/excluded_reason を検査し `DetectorReport`(mode=advisory) を返す。metrics に unknown/design_id_missing/wrong_layer/l6_design_pending を含む | coverage_layer 未設定/enum外は `unknown_coverage_layer`(P1)・部分黙殺しない／L6_required の空 design_ids は `l6_design_pending`(P3) で `design_id_missing` と区別／design_id は anchor∪実IDprefix で解決・未解決は `design_id_unresolved`／coverage_layer↔design_id prefix 不整合は `wrong_layer` |

## 4. 合格基準（G6 → L7 へ）

- 7 つの FN-RDB-* が L7 の UT-RDB-* と 1:1（trace_symmetry: L6↔L7 coverage100% / orphan0 / missing-pair0 / balance1.0 を維持）。
- 各 FN の invariant（特に FN-RDB-01 fail-close / FN-RDB-05 advisory=exit0 / FN-RDB-06 段階 skip 不可）が UT で反証されること。
- 実装（`cli/lib/registry_checks.py`）は TDD（UT 先行）で起こす。

## 5. 設計 universe と粒度 caveat

- 本 doc の universe = **基盤型の公開契約のみ**。個別 detector（check_functional_registry / check_fr_sot_alignment）の関数契約は Action1b の L6 追補で定義する（本 doc に先取りしない＝過剰設計回避）。
- FN-RDB-06（promote）は **契約のみ凍結**し、実運用の昇格（ratchet/fail_close への遷移）は Action1 スコープ外（warn-only で完了）。状態機械の存在を先に固定することで、後続 Action が state を flip するだけで済む構造にする。

## 6. L7 への引き継ぎ

- 対の単体テスト設計: [registry-detector-単体テスト設計.md](../L7-test-design/registry-detector-単体テスト設計.md)。
- 実装ファイル（L7 で TDD 起こし）: `cli/lib/registry_checks.py` / `cli/lib/tests/test_registry_checks.py`。
