# HELIX V3 — cutover 設計（V2→V3 engine 切替 + cutover-gate）

> **status: draft**（TL check 前）/ keystone TL C-4 の実体化。base = [capture §9.5 C-4 / §10 実行順](../audit/2026-06-26-new-base-comprehensive-capture.md)。
> 接続: [C1 schema](../engine/schema-registry.md) / [C2 projection](../engine/projection-writer.md) / [distribution 公開 API](../distribution/distribution-design.md)。
> **最重要制約**: cutover EXECUTION は破壊的・不可逆（V2 DB 破棄・engine module 退避）= escalation（人間確認必須）。**cutover-gate（本書 §2）が green になるまで cutover 禁止**。

## 0. cutover とは / なぜ staged

V3 engine（`cli/lib/v3/`）は V2 と**並行**に構築済（V2 不変＝rollback 保全）。cutover = **V3 を active engine に切替える不可逆点**。

clean harness 実行順（capture §10）= **Phase 6 engine 実装先行（C1→C2 = 完了）→ Phase 5 cutover → Phase 7 DB 構築 → Phase 8 detector/lint-wiring/baseline**。つまり cutover 時点で V3 は **rebuild 可能（C1 schema + C2 projection）だが detector はまだ**（Phase 8）。

→ **staged cutover**: cutover は **DB/schema/projection 層を V3 へ確定**する。detector は cutover 後に Phase 8 で V3 上に構築する（この間 detection は縮退 = **明示的に受容**、silent gap にしない）。V2 は archive（削除でなく退避）し rollback 窓を残す。

## 1. cutover 手順（昇格 → DB rebuild → V2 archive → verify → rollback 窓）

1. **pre-check**: cutover-gate（§2）green を必須確認（fail なら中止）。
2. **promote**: `cli/lib/v3/` を active engine 経路へ昇格（helix CLI が V3 の schema/projection を使う配線。具体配線は L7 で確定）。公開 API `@~/.helix/core/<path>` は**不変**（cutover はこれを触らない）。
3. **DB rebuild**: V3 schema（C1 `migrate`）で runtime DB を作成 → C2 `rebuild_projection` で投影。**旧 V2 DB は archive**（`.helix/archive/` へ退避、削除しない）。
4. **verify**: rebuild した V3 DB が期待行を持つ（projection 健全）+ 公開 API 解決 + helix 主要 command 動作。
5. **rollback 窓**: verify 期間中は V2 を archive 保持し、fail なら即 restore（§3）。verify 通過後の最終 V2 物理削除は**別 escalation**（本 cutover に含めない）。

## 2. cutover-gate（C-4 検査、detector・read-only）

`cli/lib/v3/cutover/gate.py`。**pure-function 3 層 + source_kind=hybrid**（[C3 契約](../engine/detector-wiring.md)準拠）。`ok = AND(pin, dangling, rollback)`。

| 検査 | 内容 | source_kind | ok 条件 |
|---|---|---|---|
| **pin inventory** | cutover で失われてはならない V2 surface を pin し、V3 が等価を供給するか突合 | hybrid | 全 pin が V3 に存在 |
| **dangling reference** | V3 corpus(docs/v3) + code(cli/lib/v3) の壊れ参照を検出 | file_snapshot | dangling = 0 |
| **rollback condition** | V2 が archive+restore 可能・cli/lib/v3 が additive（V2 未改変）・可逆 | hybrid | rollback 可能 |

- **pin inventory（pin する V2 surface = cutover 後も必須）**:
  - 公開 API: `core-manifest.tsv` の全 import path（`@~/.helix/core/<path>` 解決）。
  - helix CLI 主要 entrypoint（消費側導線）。
  - engine 能力: V3 が schema（58 table materialize）+ projection（rebuild 成功）を供給。
  - **detector は pin しない**（Phase 8 で構築 = 明示的 deferred。gate は detector 不在を「縮退受容」として記録し、silent pass にしない）。
- **dangling**: markdown link が実ファイル/節へ解決 / Python import が実モジュールへ解決 / PLAN `generates`/`requires` が実在へ解決（§B dangling 再発防止と同型）。
- **rollback**: `git status` で `cli/lib/`（V2 engine）が未改変 + V2 DB archive 存在 + cutover 操作が逆操作可能（promote の reverse 手順が定義済）。
- absence=ok=false（pin source 読めない／scope 0 で pass しない）。fail-close。

## 3. rollback

cli/lib/v3 は **additive**（V2 を改変しない）ため rollback は単純: ①V3 昇格配線を revert ②archive した V2 DB を restore ③`cli/lib/v3` は残置（無害）。verify fail / cutover-gate 後退 で即実行。**最終 V2 物理削除までは rollback 窓を維持**。

## 4. escalation（不可逆点）

- **cutover EXECUTION（手順 2-3 = promote + V2 DB archive + 配線切替）は破壊的・不可逆** → **人間確認必須**（HELIX rule §10 destructive data operation）。AI は gate green まで準備し、**execution は人間 go で実施**。
- 最終 V2 物理削除（rollback 窓終了後）は**別 escalation**（cutover とは別承認）。
- cutover-gate 自体は read-only（検査のみ）= 安全、自動実行可。

## 5. 検証（gate UT）

- UT-CUT-01 pin inventory: V3 に schema/projection/公開 API/CLI が揃う → ok。1 つ欠落 → fail（finding）。
- UT-CUT-02 dangling: docs/v3 に壊れ link を仕込む → 検出。解消 → 0。
- UT-CUT-03 rollback: cli/lib/ 既存 file を改変した状態 → rollback 不可 fail。archive 不在 → fail。
- UT-CUT-04 ok=AND: 3 検査の 1 つでも fail → gate fail（cutover block）。
- UT-CUT-05 detector deferred: detector 不在を「縮退受容」として記録（silent pass しない、明示 finding=info）。

## 6. 未確定（L7 / TL）

- promote の具体配線（helix CLI → V3 engine の wiring 方式: import 切替 / shim / 設定 flag）。
- V3 runtime DB の物理パス（`.helix/helix.db` を V3 で再利用か別 path か）。
- staged cutover 中の detection 縮退をどこまで許容するか（Phase 8 までの期間最小化 or V2 detector ブリッジ）。
