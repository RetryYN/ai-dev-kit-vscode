# HELIX V3 — cutover 設計（V2→V3 engine 切替 + cutover-gate）

> **status: draft**（TL refine #1 反映済、2026-06-26）/ keystone TL C-4 + [FR-V3-CUT-01](../L0-L14/L1-requirements.md) の実体化。base = [capture §9.5 C-4 / §10 実行順](../audit/2026-06-26-new-base-comprehensive-capture.md)。
> 接続: [C1 schema](../engine/schema-registry.md) / [C2 projection](../engine/projection-writer.md) / [distribution 公開 API](../distribution/distribution-design.md)。
> **最重要制約**: cutover EXECUTION は破壊的・不可逆 = escalation（人間確認必須）。**cutover-gate（§2、4 hard checks）が green になるまで cutover 禁止**。

## 0. cutover とは / staged / detector 縮退 policy

V3 engine（`cli/lib/v3/`）は V2 と**並行**構築済（V2 不変＝rollback 保全）。cutover = **V3 を active engine に切替える不可逆点**で、**[FR-V3-CUT-01] V2 + pin する 107 pytest + 49 bats + config を同一 commit で退役**する。

clean harness 実行順（capture §10）= Phase 6 engine（C1→C2 = **完了済**）→ Phase 5 cutover → Phase 7 DB → Phase 8 detector。cutover 時点で V3 は **rebuild 可能（C1+C2）だが detector はまだ**（Phase 8）。→ **staged cutover**（big-bang でなく DB/schema/projection 層だけ先に V3 確定）。

- **detector 縮退 policy（TL P1）**: detector 不在期間を黙認しない。cutover-gate は detector deferred を **`accepted_gap` finding** として扱い、**(a) Phase 8 到達期限 (b) owner (c) bridge 採否（V2 detector を一時併走させるか）** の 3 つが揃って初めて gap を受容。**いずれか欠落なら fail-close**（cutover block）。縮退期間中は V3 corpus/code に **no-change freeze**（gap を広げる変更を禁止）。

## 1. cutover 手順（preflight → execute → verify → rollback 窓）

**時系列を分離**（TL P1: archive はまだ無い preflight と、archive 後の verify を混同しない）:

1. **preflight（pre-check、破壊なし・read-only）**: cutover-gate（§2、4 hard checks）が green。archive はまだ作らない — **archive 先の書込権限・容量・checksum 計画・restore dry-run 可否**を確認するだけ。
2. **execute（破壊的・escalation、§4 の個別承認）**: ①promote（helix を V3 engine 配線へ切替）②V2 DB を `.helix/archive/<ts>/` へ退避（削除でなく move）+ **archive checksum 記録** ③V2 + 107 pytest + 49 bats + config を退役（同一 commit）。
3. **verify（archive 後）**: archive checksum 一致 / V3 DB が rebuild 済で projection 健全 / 公開 API 解決 / helix 主要 command 動作。fail → 即 rollback（§3）。
4. **rollback 窓**: verify 期間中は archive 保持し可逆を維持。**window expiry（期限）到達 + verify 全 green** で初めて最終 V2 物理削除が可能（**別 escalation**、本 cutover に含めない）。

## 2. cutover-gate（C-4、4 hard checks・detector・read-only）

`cli/lib/v3/cutover/gate.py`。**pure-function 3 層 + source_kind 宣言**（[C3 契約](../engine/detector-wiring.md)）。`ok = AND(pin_inventory, dangling, rollback_preflight, rebuild_dry_run)`。absence=ok=false（fail-close）。

| # | check | 内容 | source_kind | ok 条件 |
|---|---|---|---|---|
| 1 | **pin_inventory** | (a) 存続 surface（公開 API core-manifest 全 path / helix CLI 主要 entrypoint / V3 schema+projection 能力）が V3 に存在 (b) **退役 surface（107 pytest + 49 bats + config）が明示 inventory と一致**し、cutover commit がそれ**だけ**を退役（過不足 = consumer impact、fail） | hybrid | 存続=全在 ∧ 退役=inventory と完全一致 |
| 2 | **dangling** | V3 corpus(docs/v3) + code(cli/lib/v3) の壊れ参照 0（md link / Python import / PLAN generates·requires が実在へ解決。§B dangling 同型） | file_snapshot | dangling = 0 |
| 3 | **rollback_preflight** | archive 先 writable + 容量十分 + checksum 計画あり + **restore dry-run 成功** + **V2 path inventory（明示リスト）が未改変**（`cli/lib/v3` は許容、V2 surface は inventory 突合＝blanket git status でない）+ **promote reverse 手順が定義済** + **rollback window expiry 定義済** | hybrid | 全条件 true |
| 4 | **rebuild_dry_run** | V3 engine が sources から throwaway DB へ **C1 migrate + C2 rebuild_projection を実行成功**（cutover 前に V3 の rebuild 能力を実証） | hybrid（DB throwaway + file sources） | 例外なく rebuild 完了 |

- **detector deferred** は §0 policy に従い `accepted_gap` finding（hard fail でなく、policy 3 要素欠落で fail-close）。
- **退役 inventory は config（数値 hardcode しない）**: gate は「cutover commit が退役した file 集合 == 凍結 inventory」を突合する（数値非依存）。**⚠ FR-V3-CUT-01 の「107 pytest + 49 bats」は harness-era 推定で本 V2 repo と不一致**（repo 実測 = **270 pytest + 117 bats**）。退役 set は「V3 が置換する V2 engine 部分の tests/config」を **cutover scope から L7 で導出・凍結**する（全 387 test の blanket 退役でなく、engine 置換に対応する subset。L1 FR-V3-CUT-01 は L7 で実数へ訂正）。

## 3. rollback（可逆性の機械保証）

cli/lib/v3 は **additive**（V2 surface を改変しない）が、それだけでは不十分（TL P1）。rollback を次で機械保証:

- **V2 path inventory**: 退役対象でない V2 surface の明示パス列挙。cutover 前後で未改変を突合。
- **archive checksum**: V2 DB / 退役 file の archive 時 checksum を記録、restore 時に照合。
- **restore drill**: preflight で restore を dry-run（archive→restore が成立するか実証）。
- **promote reverse**: promote（配線切替）の逆手順を定義し gate 入力にする（import 切替 / shim / 設定 flag のいずれか、L7 で契約化）。
- **window expiry**: rollback 窓の期限。期限内は archive 保持・即 restore 可。期限 + verify 全 green で最終削除（別 escalation）。

## 4. escalation（不可逆点・個別承認、TL: D sound）

cutover-gate（read-only 検査）は安全・自動実行可。以下は**各々独立に人間承認**:

1. **promote**（配線切替）
2. **V2 DB archive**（退避）
3. **V2 + 107pytest/49bats/config 退役**（同一 commit、破壊的）
4. **最終 V2 物理削除**（rollback 窓終了後、別 escalation）

AI は gate green まで準備し、1-4 は人間 go で実施（HELIX rule §10 destructive data operation）。

## 5. 検証（gate UT・L6↔L7）

- UT-CUT-01 pin_inventory: 存続 surface 欠落 → fail / 退役 inventory と cutover commit 不一致（過削除 or 残存）→ fail / 完全一致 → ok。
- UT-CUT-02 dangling: docs/v3 に壊れ link → 検出 / 解消 → 0。
- UT-CUT-03 rollback_preflight: archive 先 read-only / V2 path inventory 改変 / promote reverse 未定義 / window expiry 未定義 → 各 fail。restore dry-run 失敗 → fail。
- UT-CUT-04 rebuild_dry_run: throwaway DB rebuild 成功 → ok / C2 例外 → fail。
- UT-CUT-05 ok=AND: 4 check の 1 つでも fail → gate fail（cutover block）。
- UT-CUT-06 detector accepted_gap: policy 3 要素（期限/owner/bridge）揃い → accepted_gap finding で ok / いずれか欠落 → fail-close。
- UT-CUT-07 archive checksum: restore 時 checksum mismatch → verify fail。

## 6. 未確定（L7 / 後続）

- promote の具体配線方式（import 切替 / shim / 設定 flag）+ その reverse 手順 → L7 で契約化（gate 入力）。
- V3 runtime DB 物理パス（`.helix/helix.db` 再利用か別 path か）。
- 退役 inventory（107 pytest + 49 bats + config）の実体パス列挙・凍結（L7、FR-V3-CUT-01）。
- detector 縮退期間の最大許容・bridge（V2 detector 一時併走）採否の既定値。
- 既存 cutover/rollback orchestrator の confirm-token/window パターンは**参考のみ**（V3 wholesale cutover へ流用しない、TL P3）。
