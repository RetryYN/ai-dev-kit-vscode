# V3 cutover — 段階退役 PLAN（設計のみ・実行は §10 人間 go）

> 2026-06-27 / status: draft（設計） / 起草: PM(Opus) 自走 / **実行は §10 destructive = 人間 go 必須**。
> 前提: wholesale 破壊は category error（[readiness-assessment](readiness-assessment.md)）。本 PLAN は
> 「V2 doctor の**検出 subset のみ** V3 へ委譲して段階退役、CLI コマンドは V2 に残す」を設計する。

## 退役対象 = V3 が確実にカバーする検出のみ

[v2-detection-to-v3-mapping](v2-detection-to-v3-mapping.md) の分類に基づき、**退役してよいのは
V3 detector がカバー済の V2 check のみ**。未カバー検出（穴になる）と CLI/infra（V3 scope 外）は退役しない。

| 退役候補 V2 check | 委譲先 V3 detector | 退役可否 |
|---|---|---|
| check_requirement_drift | FN-DET-04 | ✅ 可（等価カバー） |
| check_plan_dependency_gate | FN-DET-18 | ✅ 可 |
| check_import_cycle | FN-DET-17 | ✅ 可 |
| check_plan_health（frontmatter 部分） | FN-DET-15 | △ 部分（section 名走査は V3 未実装、要確認） |
| check_l7_worklist | FN-DET-05 | △ 部分（surfacing は V2 維持が安全） |
| check_vmodel_4artifact | FN-DET-12 + 01 | △ 部分 |
| check_vg_overview（overall_clean 集約） | V3 run_doctor ok=AND | △ 集約等価だが pre-push gate 配線は別途 |
| skill_frontmatter / ddd / anchor_quality | （未カバー） | ✗ 退役不可（V2 残置） |
| template_version / role_config / mode_phase / stale_locks 等 | （CLI/infra） | ✗ 退役対象外（V3 scope 外） |

## 退役の段階（各段で rollback 可能を保つ）

1. **shadow 期（非破壊・現状）**: `helix v3-doctor` を additive 並走（実施済 `eefeeee`）。V2 doctor と V3
   を一定期間並走させ、✅ 可 の3 check（requirement_drift/plan_dependency/import_cycle）について
   **V2 と V3 の検出結果が一致するか**を観測（diff が出ないことを実証）。
2. **委譲期（§10 実行・人間 go①）**: 上記3 check を V2 doctor 側で **no-op 化（または warning 降格）**し、
   検出の正本を V3 detector に移す。V2 のコード・テストは残す（no-op フラグのみ）。rollback = フラグ復帰。
3. **削除期（§10 実行・人間 go②・最終）**: 委譲期が安定（一定期間 regression なし）を確認後、no-op 化した
   V2 check 本体とテストを物理削除。ここで初めて不可逆。archive + rollback drill（rollback.py）を先行必須。

## ガード（既存機構を再利用）

- **parity floor**: cutover-gate（gate.py）は退役 inventory 非空時に `parity_attested=True` を要求。
  委譲期/削除期の実行はこの gate を通す（実 coverage 一致を shadow 期で実証してから attestation）。
- **rollback preflight**: `build_cutover_config` の restore_dry_run（throwaway DB round-trip）を pass。
- **段階性**: 各段は前段の安定を確認してから。skip 不可。

## 未確定（confirm 要・勝手に確定しない）

- 各段の「安定」判定基準（並走期間 / regression 0 の窓）。
- vg_overview の pre-push gate 配線を V3 ok=AND にどう繋ぐか（CI 配線）。
- △ 部分カバーの check を委譲対象に含めるか（安全側＝当面 V2 維持を推奨）。

## 実行規律

- **段階 2/3 の実行は §10 destructive。本 PLAN 承認≠実行承認**。各段で人間 go を取る。
- 設計（本 PLAN）は自走で用意済み。実行は go 待ち。wholesale 破壊は行わない。
