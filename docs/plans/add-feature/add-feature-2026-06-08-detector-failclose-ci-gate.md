---
plan_id: add-feature-2026-06-08-detector-failclose-ci-gate
title: "Action(add-feature): V2 Phase3-① 自動化 — detector fail-close gate化 + CI連動"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # L6 正本(TL裁定): GatePolicy / DetectorReport 契約
drive: be
status: finalized  # 設計 finalized(TL round1→round2 approve)。実行は PARKED(banner 参照)= 検証ゲート閉合後に automation-gate-map gate hardening として再開。
current_task_scope: parked_feature_ticket_only
approval_required_before_l7_work: true
approval_required_before_ci_or_fail_close: true
ticket_is_completion_evidence: false
tl_review: approve  # round1 changes_required(P1×2/P2×3/P3×1)→反映→round2 changes_required(残P2=roadmap同期漏れ1件のみ)→verbatim同期適用で解消。TL round2 確認: doctor rc=0/昇格6件全✓・strict rc=1でpair除外妥当・parent_design妥当・テスト十分・plan lint PASS
created: 2026-06-08
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): detector の advisory→fail-close 化 = 検出機構を gate として実走させる"
  - "automation-gate-map: 昇格 detector を fail-close gate として V-model 層へ接続"
design_change_class: contract_extension  # 振る舞い追加(advisory→fail-close + CI gate + 新 exit code)。pure_impl ではない。再凍結 scope(TL裁定): registry-detector-機能設計(GatePolicy/DetectorReport) + functional-registry/coding-rule/ddd-registry/whole-source-coverage の各設計 + 対応 L7 test design + automation-gate-map
agent_slots:
  - role: se
    slot_label: "SE — doctor gate モード + CI 配線 + テスト実装（Codex）"
  - role: tl-advisor
    slot_label: "TL — 昇格 allowlist の安全性 / 公開API・exit code 契約 / 再凍結 scope の adversarial check"
generates:
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: .github/workflows/ci.yml
    artifact_type: config
  - artifact_path: HELIX-workflows/helix-process/automation-gate-map.md
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires: []
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  - docs/plans/discovery/poc-2026-06-03-trace-symmetry-detector.md
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - .github/workflows/ci.yml
---

# Phase3 Action ①: detector fail-close gate化 + CI連動

> ⚠️ **PARKED（2026-06-08）**: 本 Action は Phase3 の「自動化」サブ項目だが**本体ではない**。Phase3 の本体 = **L7 検証実走（単体テスト実施）の完遂**（roadmap §3 主眼）。ユーザー指摘で「Phase3=検証」「Phase2 は設計+テスト設計の凍結で検証は未実施」と確認、L7 検証が 31/88 UT trace = 片肺と実測判明。よって検証本体を優先し、本 detector-gate は**検証が閉じた後の自動化サブ項目として park**。PLAN/TL approve は資産として保持（再開時に流用）。
> **親 再帰属（2026-06-08）**: frontmatter の `parent_process` は deprecated roadmap を指すが、再開時は **Forward 検証ゲート（[automation-gate-map](../../../HELIX-workflows/helix-process/automation-gate-map.md) §5 enforcement 段階の detector allowlist fail-close 昇格）**に帰属させる。deprecated Process を live parent にしない（退化防止）。

> 親 Process: [V2 実装計画 roadmap](../process/process-2026-06-03-v2-implementation-roadmap.md) §3.2 が宣言する Phase3 子 Action 三分割の **①自動化（検出/ゲート）**。
> PoC [trace-symmetry-detector](../discovery/poc-2026-06-03-trace-symmetry-detector.md) が「fail-close は Phase3」と defer した advisory detector 群を、**今 green な分だけ** hard gate へ引き上げ、CI に接続する。

## 1. 目的 / 解く問題

直近 session で whole-source design coverage の detector 群（registry_design_coverage / functional_registry / DDD / coding-rule / trace symmetry）を新設したが、いずれも **advisory（exit 0、warn 出力のみ）**。CI（[ci.yml](../../../.github/workflows/ci.yml)）は pytest / bats / verify-all / drift-check のみで **detector を未連動**。

→ detector はデグレを「報告」するが「ブロック」しない。デグレ第一歩（SSoT 乖離・trace 切れ）が CI をすり抜ける。Phase3 自動化 = **green な detector を fail-close gate 化し CI Required check に接続**して、デグレを構造的に止める。

## 2. スコープ

### In（この Action でやる）
- `helix doctor` に **gate モード**（`--gate`、`--strict-vmodel-pair-freeze` の一般化）を追加。**昇格 allowlist の check が fail/findings を出したら exit 1**。
- 昇格 allowlist = **現状 green（0 findings）の detector のみ**（§4 安全性）。
- `ci.yml` に `helix doctor --gate` を走らせる step/job を追加（CI Required check 化）。
- [automation-gate-map.md](../../../HELIX-workflows/helix-process/automation-gate-map.md) に昇格 detector を fail-close gate として登録（V-model 層へ接続）。
- gate モード / default モードの exit code・出力をテスト固定（bats + pytest）。

### Out（この Action でやらない = 別 Action / 後段）
- **pair trace symmetry (`--strict-vmodel-pair-freeze`) の昇格**（TL P1-1）: strict が現状 rc=1（critical:3）= 今 fail。CI 即 red を避けるため初期昇格対象外。Phase2 片肺の strict 残（critical pair docs）を解消した後、別 Action で昇格。
- △（findings 残）detector の昇格（glossary_coverage findings:7 / coding_rule_sot findings:11 / stale lock）→ gap 解消後に別途昇格。**今回は warn 据え置き**。
- whole-coverage audit recipe（verification-strategy §11）の full CI 連動 → 範囲が広いので Action 分割（本 Action は doctor gate の CI 連動に絞る）。
- Phase3 ②Python化 / ③L7実装回帰（別 Action）。
- push gate（helix push --gate）側の変更（既に G-tests 等で別途 gate 済み）。

## 3. 設計（WHAT）

### 3.1 doctor gate モード
- `helix doctor --gate`（名称 TL 確認）: 全 check は通常どおり走らせ出力する（既存 advisory 出力は不変）。**allowlist に載る check が fail/findings>0 なら最後に exit 1**。それ以外（warn 据え置き check の findings）は exit に影響しない。
- **default `helix doctor`（フラグ無し）は完全に従来どおり**（exit code・出力不変 = 公開API・外部CLI出力互換）。
- 既存 `--strict-vmodel-pair-freeze`（critical missing pair docs で exit 1）は `--gate` のサブ集合として包含 or 共存（TL 判断）。

### 3.2 昇格 allowlist（初期セット = 今 green な 0-finding detector のみ = **6 件限定**）
> **TL P1-1 反映**: `pair trace symmetry (--strict-vmodel-pair-freeze)` は **昇格しない**。TL read-only 実走で strict は `critical:3` で rc=1（現状 fail）→ 昇格すると CI 即 red。Phase2 片肺の strict 残を解消後、別 Action で昇格（§2 Out へ）。初期昇格は以下 6 件のみ。

| check | 現 severity | 昇格 |
|---|---|---|
| check_functional_registry | ✓ pass | → fail-close |
| check_fr_sot_alignment | ✓ pass | → fail-close |
| check_bc_anti_corruption | ✓ pass | → fail-close |
| check_bc_mode_coverage | ✓ pass | → fail-close |
| check_coding_rule_alignment | ✓ pass | → fail-close |
| check_registry_design_coverage | ✓ pass | → fail-close |
| pair trace symmetry (--strict-vmodel-pair-freeze) | strict rc=1 (critical:3) | **昇格しない**（別 Action へ defer） |
| check_glossary_coverage | △ findings:7 | 据え置き（warn） |
| check_coding_rule_sot | △ findings:11 | 据え置き（warn） |
| stale lock | △ | 据え置き（warn） |

allowlist は cli 側に **明示データ**（配列/設定）で持ち、昇格対象の増減を 1 箇所で管理（将来 △ / pair strict が green 化したら追記）。**実装時に `helix doctor` を実走し、昇格 6 件が全 ✓ であることを確認してから allowlist 確定**（環境差で findings が出る check は昇格しない）。

### 3.3 CI連動
- **TL P2 反映**: `ci.yml` に **専用 job `detector-gate`** を追加（既存 `test` job に混ぜない = 失敗原因の切り分けを明確に、job 名を安定させ Required check 化）。`helix doctor --gate` を実行、失敗で CI red。
- CLAUDE.md「CI↔V-model gate 紐づけ」の宣言（doctor=検出 gate）を実体化。`concurrency: cancel-in-progress` は既存方針に合わせる。permissions は最小（contents: read）。

## 4. 受入条件（roadmap §3.2 + 安全性）

1. **外部 CLI 出力互換**: default `helix doctor` の stdout/json が不変（既存 doctor テスト全 PASS + default 出力 snapshot 一致）。
2. **exit code 互換**: default の exit code 不変。`--gate` のみ exit セマンティクス変更（昇格 6 件 green→0 / 昇格 check 退行→1）。`--json` も非破壊。
3. **frontmatter enum 非破壊 / `@~/.helix/core/<path>`・公開 API 非破壊**。
4. **安全性（CI を即壊さない）= 主条件（TL P3 反映、環境差吸収）**: 固定数値（30/0/107 等）ではなく、**「昇格 6 件が全 ✓ / 除外対象（pair strict・glossary・coding_rule_sot・stale lock）は昇格 set に未混入で △ のまま」**を主判定とする。これにより **`helix doctor --gate` は今日 exit 0**（CI merge 時に即 red にならない）。実装時に実走で 0 を証明。
5. **回帰検証**: 昇格 check の 1 つを擬似的に fail させた fixture で `--gate` が exit 1。default モードは同 fixture でも exit 不変。
6. **昇格は exit 判定のみ変え、check 内容（findings 算出ロジック）は不変**。

## 5. テスト計画（テストファースト、TL P2 反映で拡充）
- bats（cli/tests/）: `helix doctor --gate` exit 0（昇格 6 件 green 時）／ default `helix doctor` exit・出力不変（snapshot）／ `--gate` で擬似退行→exit 1。
- pytest（cli/lib/tests/）: allowlist データ駆動の gate 判定ロジック（昇格 set ∩ findings>0 / 実行失敗 → exit 1）。
- **negative test**: 除外対象（`glossary_coverage` / `coding_rule_sot` / stale lock / pair strict）が **allowlist に含まれない**ことを明示検査（findings があっても `--gate` exit に影響しない）。
- **default 非破壊**: default モードの stdout / `--json` が昇格前後で不変（snapshot 比較）。
- 既存 doctor 回帰（output 互換）。

## 6. forward_return / 収束
- forward_return: **L7（単体テスト実施）** = detector を gate として実走させ、CI で常時検証。automation-gate-map 経由で V-model 層 gate に接続。
- design_change_class=contract_extension（§frontmatter）。pure_impl でないため対 design（automation-gate-map + exit-code 契約記述）を同時更新。**再凍結の正確な scope は TL が裁定**（[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用）。
- closure: 親 roadmap の Phase3 収束の部分項（②③ と合わせて Phase3 を判定）。

## 7. escalation / リスク
- gate/CI 強制の **振る舞い変更**（消費側が取り込むと CI 挙動が変わる）。ただし roadmap Phase3 §3.2 で**事前承認済みの計画作業**。auth/payment/PII/secret/schema 変更ではない。
- exit code 契約の追加（`--gate`）→ D-CONTRACT 視座。**TL P2 反映: 契約記述は deprecated な `docs/v2/L3-detailed-design/`（参照禁止）でなく、現行 L6（registry-detector-機能設計 の GatePolicy）/ L7 側に追補**。default `helix doctor` / `--json` / exit code は不変固定。
- リスク: allowlist に findings 残 check を誤混入すると CI 即 red → 受入 §4-4（昇格全✓・除外△維持を主条件）/§5 negative test で機械防止。

## 8. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-08 | Action 起票（Phase3 ① 自動化）。doctor gate モード + 昇格 allowlist（green のみ）+ CI 連動 + automation-gate-map 登録の設計確定。TL adversarial check へ。 | PM (Opus) |
| 2026-06-08 | **TL adversarial check round1 = changes_required**（P0 なし / P1×2 / P2×3 / P3×1）。反映: ①P1 pair trace symmetry を昇格 allowlist から除外（TL 実走 strict rc=1=critical:3、CI 即 red 回避、別 Action へ defer）→ **初期昇格 6 件限定** ②P1 parent_design を正本 `docs/v2/L6-functional-design/registry-detector-機能設計.md`（GatePolicy/DetectorReport）に + 再凍結 scope 明示 ③P2 CI は専用 job `detector-gate` ④P2 exit code 契約は現行 L6/L7（deprecated L3 不可） ⑤P2 negative test / default snapshot / `--json` 非破壊 追加 ⑥P3 受入を固定数値→「昇格全✓・除外△維持」主条件（環境差吸収）。 | PM (Opus) |
| 2026-06-08 | **PARKED**（ユーザー指摘）。Phase3 の本体は detector-gate（機能実装）でなく **L7 検証実走の完遂**（roadmap §3 主眼=L7 単体テスト実施）。実測で L7 検証が片肺（88 UT 設計に対しテスト実装 trace は 31、58 untraced）と判明。本 Action は自動化サブ項目として検証本体の後に回す。Codex se 実装は着手前に停止（git 未書き込み）。PLAN+TL approve は資産保持。 | PM (Opus) |
| 2026-06-08 | **TL re-review round2 = changes_required（残 P2 = 1 件のみ）**: 親 roadmap 進捗ログに pair trace symmetry が昇格列挙のまま残る同期漏れ（実装者誤読リスク）。→ TL 指示どおり roadmap を verbatim 同期（pair strict を「昇格対象外」に修正）で解消。TL round2 確認結果: doctor rc=0/昇格 6 件全 ✓（29 pass/0 fail/106 warn）・strict rc=1（pair 除外妥当）・parent_design 妥当（deprecated L3 参照なし）・テスト戦略十分・plan lint PASS。→ **tl_review=approve**。実装を Codex se へ委譲。 | PM (Opus) |
