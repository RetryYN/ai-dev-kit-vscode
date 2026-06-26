# V3 cutover 準備状況アセスメント（go/no-go 判断材料）

> 2026-06-26 / 目的: **phase 3 cutover（破壊的 V2→V3 切替）の go/no-go を人間が判断するための資料**。
> cutover EXECUTION は破壊的・不可逆（HELIX rule §10）。本書は判断材料であって、実行ではない。

## 実行記録: 非破壊 promote 実施済（`eefeeee`、2026-06-26）

人間の明示 go（「OK。慎重に実施を」）を受け、cutover phase 3 を**安全・可逆な非破壊形で実施**:
`helix v3-doctor` を additive 配線（V2 `doctor` 不変、2 行削除で巻き戻し可）。V3 engine が
product として invocable。**破壊的 V2 退役は未実施**（parity 未達 = 虚偽 attestation を立てないため）。

## 判定（破壊的退役）: **NO-GO（現時点）** — 機械的準備 OK / parity 未達 / 人間 go 未取得

cutover-gate（machine verdict）と parity 実測の両面で評価する。

### 1. engine 準備（DONE）

V3 engine は **C1-C6 全 keystone を実装・統合し、operational に稼働**（34 commit、99 UT、全独立検証、V2 不変）:

| keystone | 状態 |
|---|---|
| C1 schema-registry | ✅ 58 table + 41 index materialize |
| C2 projection-writer | ✅ rebuild⊥append、9 projector、実 repo 投影（plan 366/artifact 1109/test_cases 3505/FR 584/drive_runs 109） |
| C3 detector + runner | ✅ 10 detector（FN-DET-01/02/03/10/11/12/14 + INTQ 3）、ok=AND |
| C4 lint-wiring | ✅ 死蔵防止メタゲート |
| C5 baseline-ratchet | ✅ run_doctor 統合（既知 debt grandfather・regression 赤）。doctor は現状で緑稼働 |
| C6 doc-workflow 契約 | ✅ frontmatter → projection |

### 2. cutover-gate machine verdict（parity floor 追加で gap 是正済 = `c39b2c1`）

- **非破壊 config（retire=()）→ gate ok=True**（pin/dangling/rollback_preflight/rebuild_dry_run + accepted_gap 全緑、**非 vacuous**。従来 4 key mismatch で survive surface 未検査だった bug を修正済）。
- **parity floor 実装済（条件② 解消）**: `retired_inventory` 非空（破壊）の cutover は **`parity_attested=True` を必須化**（無ければ pin_inventory 赤 → gate 赤）。これで「緑 gate ≠ 破壊安全」gap を是正 — 破壊的 cutover は parity 明示 attestation 無しには gate を通らない。
- 残: `parity_attested` は人間/process の宣言。実 coverage 自動検証（V3 が退役 V2 を実際に cover）は parity 構築（条件①）後に machine 化しうる。

### 3. parity 実測（NO-GO の主因）

cutover は「V2 + その tests/detector を退役」する。現状の差は致命的:

| | V2（破壊される） | V3（置換する） | 判定 |
|---|---|---|---|
| tests | 402（284 pytest + 118 bats） | 99 UT | ❌ 未達 |
| detectors | 41+ module | 10 | ❌ 未達 |
| projector 群 | full | 9（core のみ、残 ~20 derived/linkage 待ち） | ❌ 未達 |

→ **今 cutover すれば、動く V2 を破棄し未完成 V3 で置換 = 破滅的・不可逆**。

## go へ必要な 3 条件（AND）

1. **parity 構築**: 残 detector（FN-DET-04/05/06/07/08/09/13/15/16）+ 連結データ（test↔fn / oracle / forward_return 表現 / screens / descent）の設計+実装。multi-day。
2. ~~**gate に parity floor を追加**~~ **DONE（`c39b2c1`）**: 退役 inventory 非空時は `parity_attested=True` を必須化（緑 gate ≠ 破壊安全 gap を是正）。残: attestation の実 coverage 自動検証は条件① 後。
3. **人間の明示 go**: 上記達成後、破壊操作の最終承認（HELIX rule §10）。

## 推奨

- **現時点は NO-GO**。engine は完成・実証済みなので、安全な次段は **parity 構築の継続**（unit 単位・独立検証）。
- limited / 非破壊 cutover（V3 を additive に CLI 提供、V2 退役なし）を試す場合も、production `helix` router 編集を伴うため**人間判断が必要**。
- 破壊的 cutover は **3 条件 AND まで実行しない**。
