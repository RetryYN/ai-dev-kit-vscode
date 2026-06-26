# V3 cutover 準備状況アセスメント（go/no-go 判断材料）

> 2026-06-26 / 目的: **phase 3 cutover（破壊的 V2→V3 切替）の go/no-go を人間が判断するための資料**。
> cutover EXECUTION は破壊的・不可逆（HELIX rule §10）。本書は判断材料であって、実行ではない。

## 実行記録: 検出 parity build 完成（2026-06-27）

repo-applicable な検出 detector を全実装し、**検出 parity を達成**:
- **13 detector 実装**（FN-DET-01/02/03/04/05/08/10/11/12/14/15/17/18）。corpus 16→18 拡張（import-cycle/plan-dependency 追加、vg_overview は ok=AND 集約で既カバー）。
- **5 deferred/N-A**: 06 oracle(@oracle 規約待ち) / 07 gate-confirm・09 review-evidence・13 fe-screen・16 rule-drift（source 空: gate_runs/review_evidence/screens/rules=0）。
- **130 UT green**、operational doctor は **green-with-baseline**（3437 既知 debt grandfather・regression 赤）。V2 不変。
- 残 cutover = C subset + 17/18 を V2 doctor から no-op 化する**段階退役 PLAN**（§10 人間 go 必須、wholesale 破壊は category error で不要）。

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
| C3 detector + runner | ✅ 11 detector（FN-DET-01/02/03/04/05/08/10/11/12/14/15）、ok=AND。repo-applicable は実質コンプリート（§3） |
| C4 lint-wiring | ✅ 死蔵防止メタゲート |
| C5 baseline-ratchet | ✅ run_doctor 統合（既知 debt grandfather・regression 赤）。doctor は現状で緑稼働 |
| C6 doc-workflow 契約 | ✅ frontmatter → projection |

### 2. cutover-gate machine verdict（parity floor 追加で gap 是正済 = `c39b2c1`）

- **非破壊 config（retire=()）→ gate ok=True**（pin/dangling/rollback_preflight/rebuild_dry_run + accepted_gap 全緑、**非 vacuous**。従来 4 key mismatch で survive surface 未検査だった bug を修正済）。
- **parity floor 実装済（条件② 解消）**: `retired_inventory` 非空（破壊）の cutover は **`parity_attested=True` を必須化**（無ければ pin_inventory 赤 → gate 赤）。これで「緑 gate ≠ 破壊安全」gap を是正 — 破壊的 cutover は parity 明示 attestation 無しには gate を通らない。
- 残: `parity_attested` は人間/process の宣言。実 coverage 自動検証（V3 が退役 V2 を実際に cover）は parity 構築（条件①）後に machine 化しうる。

### 3. parity 実測 + **scope 再定義（重要）**

**従来の「V2 の 402 tests/41 detector を全 parity」は category error**（2026-06-27 parity build で判明）。V3 は**検出 ENGINE**（projection + detection）であって、V2 の全 CLI（size/plan/gate/sprint/reverse/codex/handover…）の置換ではない。V2 の 402 tests の大半はそれら CLI コマンドのテストで、V3 が置換対象にした覚えはない。

**正しい parity 軸 = V2 の「検出 surface（doctor 検出軸）」を V3 engine が cover するか**:

| 軸 | V2 | V3 現状 | 判定 |
|---|---|---|---|
| 検出 detector（設計 16 枠） | helix-doctor ~40 check | **11 実装**（01/02/03/04/05/08/10/11/12/14/15） | ◎ repo-applicable は実質完了 |
| — not-applicable（source 空） | — | 07 gate-confirm / 09 review-evidence / 13 fe-screen / 16 rule-drift（gate_runs/review_evidence/screens/rules=0） | N/A |
| — deferred | — | 06 oracle-test-trace（@oracle 規約待ち） | deferred |
| V3 engine UT | — | **118 passed** | green |
| V2 CLI コマンド群 | full | **置換対象外**（V3 は engine、CLI は V2 が継続） | 別レイヤ |

→ **この repo で applicable な検出 detector は 11 実装で実質コンプリート**。残るのは @oracle 規約（06）と、source が生じたとき（screens/gate_runs/review_evidence/rules）の 07/09/13/16。

### cutover scope の再定義

- **wholesale 破壊的 cutover（V2 全退役）は誤った枠組み**。V3 は V2 CLI を置換しない。
- **正しい cutover = 段階的・subset 退役**: V3 engine が検出の正本になり、V2 の**検出 subset のみ**（helix-doctor の detection 部分）を段階退役。CLI コマンドは V2 のまま残す。これは wholesale 破壊より遥かに小さく安全。
- 現状の**非破壊 promote（`helix v3-doctor` additive、`eefeeee`）が当面の正しい到達点**: V3 engine を V2 と並走させ、検出軸を段階移行。

## go へ必要な条件

1. **検出 parity**: repo-applicable 検出 detector の実装 = **実質達成（11/16、残は N/A + @oracle deferred）**。
2. ~~**gate parity floor**~~ **DONE（`c39b2c1`）**。
3. **段階退役の scope 確定 + 人間 go**: 「V2 のどの検出 subset を、いつ、V3 に委譲して退役するか」を確定し、その subset 退役（§10 destructive の局所適用）に人間 go。wholesale 破壊は不要。

## 推奨

- **非破壊 promote が現到達点**。検出 detector はこの repo で実質コンプリート。
- 次は **wholesale 破壊でなく、検出 subset の段階退役 scope を L4 で設計**（どの V2 doctor check を V3 detector に委譲し退役するかの対応表）。
- **wholesale 破壊的 cutover は実行しない**（category error）。subset 退役も人間 go まで実行しない。
