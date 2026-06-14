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
forward_return: "L6 registry-detector GatePolicy 再凍結 (contract_extension) -> approved L7 detector fail-close 昇格 + CI gate 実装 -> 単体実行 evidence -> automation-gate-map enforcement closure (L6↔L7 G6/G7 pending gate evidence に帰属)."
drive: be
status: completed
status_note: "2026-06-14 UNPARK(ユーザー goal「ゲートの fail-close/CI 昇格を先に固める」)→ 完遂。残差(CI 配線 + 境界契約 unpark)を C-fix で実装。完遂境界 = CI job 配線まで(branch protection 登録は DF-FCCI-BRANCHPROT の人間 handover、右腕 G8-G14 は別 Action)。§9 再活性化セクション正本。"
current_task_scope: ci_enforcement_and_boundary_unpark  # 旧 parked_feature_ticket_only から昇格
approval_required_before_l7_work: true
approval_required_before_ci_or_fail_close: true
ticket_is_completion_evidence: false
tl_review: approve  # [設計2026-06-08] round1/2 approve。[再活性化2026-06-14] scope諮問→C-fix諮問(P0=fresh checkout永続red検出→check_vg_overview --gate採用)→impl review=changes_required(P2×1=PLAN内旧コマンド残骸)→TL指示通りverbatim修正(§9.3/§9.4 を check_vg_overview --gate へ)。TL impl review確認: CI job適切(fetch-depth0/requirements/strict不混入/contents:read)・unpark過剰なし・F4 honest debt化・完遂境界維持・doctor gate exit0/strict exit1・bats 17/17+57/57 PASS。実装本体approve相当+唯一のP2 doc fix適用済
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

> ✅ **UNPARKED（2026-06-14）**: ユーザー goal「ゲートの fail-close/CI 昇格を先に固める」で本 Action を再活性化。**残差スコープは §9 を正本**とする（doctor --gate と push G-vg-overview は本 ticket 起票後の Phase1/2 で既に landed したため、残差 = CI 配線 + 境界契約 unpark に縮小）。TL 再諮問（gpt-5.5 high, 2026-06-14）= 条件付き推奨で技術選択を再裁定（§9）。
>
> ~~⚠️ **PARKED（2026-06-08）**~~（履歴・解除済）: 本 Action は Phase3 の「自動化」サブ項目だが**本体ではない**。Phase3 の本体 = **L7 検証実走（単体テスト実施）の完遂**（roadmap §3 主眼）。ユーザー指摘で「Phase3=検証」「Phase2 は設計+テスト設計の凍結で検証は未実施」と確認、L7 検証が 31/88 UT trace = 片肺と実測判明。よって検証本体を優先し、本 detector-gate は**検証が閉じた後の自動化サブ項目として park**。PLAN/TL approve は資産として保持（再開時に流用）。
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
| 2026-06-14 | **PARKED → 後続 session で L7 検証実走（pre-L7 gate-hardening Phase1/2）が landed**。その過程で `helix doctor --gate`（GATE_MODE + check_vg_overview_gate）と `helix push --gate` の **G-vg-overview**（vg_overview.overall_clean blocking）が**既に実装・landed**。本 ticket の §3.1/§3.2/§3.3 のうち **doctor gate モード本体 + push 側 fail-close は充足済**。残差は **CI 配線**のみ。 | PM (Opus) |
| 2026-06-14 | **UNPARK（ユーザー goal）+ TL 再諮問（gpt-5.5 high）= 条件付き推奨**。§9 に残差スコープ・TL 裁定・完遂境界を確定。実装を Codex se（TDD）へ委譲予定。 | PM (Opus) |
| 2026-06-14 | **Codex se 実装（exit143 timeout だが 13 ファイル整合着地）→ PM 独立検証 全 green（contract 88/push_gate 43/bats 12+57/doctor --gate exit0/全体 pytest 2598 passed）→ 敵対的検証 Workflow（4レンズ）で P0 検出**。**P0 = `helix doctor --gate` は fresh CI checkout（.helix/ 無し）で .helix/phase/matrix の `check` fail により exit 1 = detector-gate Required check が永続 red**（empirical 確証: git archive fresh checkout で exit 1=3 fail）。全テストが見逃し ci-safety レンズのみ捕捉。併せて P1×2（pyyaml 未install / weakness-map YAML parse error=修正済）/ P2×2（pass値 drift / unavailable→clean）/ P3。 | PM (Opus) + verify Workflow |
| 2026-06-14 | **P0 修正方針を TL 再諮問（gpt-5.5 high）= C-fix 採用**（A=全 doctor 結合の設計負債で却下 / C-parse=CLI 契約迂回で暫定のみ）。**`check_vg_overview --gate` を overall_clean のみ fail-close 化**（help:141 の documented 契約の doc-impl mismatch 修正、新規公開契約でない）。CI は `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json`（project-state 非依存 = fresh checkout OK、empirical 確認済）。pyyaml を requirements-dev.txt 追加 + detector-gate で install。**scope 拡張（TL 裁定根拠）: allowed files に `cli/helix-doctor` + `requirements-dev.txt` を追加**（§5）。 | PM (Opus) |
| 2026-06-14 | **C-fix 実装 + Workflow finding 全是正**。helix-doctor の `check_vg_overview --gate` を fail-close 化（GATE_MODE 時 overall_clean=false / parse 失敗 → exit 1）。ci.yml: command を `check_vg_overview --gate --json` へ + `requirements-dev.txt` install step + `fetch-depth: 0`（F4 PR ratchet 修正）。requirements-dev.txt に PyYAML。test/audit/bats 同期: contract test command/pass 33/warn 104/reason/interpretation/ci_detector_gate/fetch-depth/requirements assertion、bats ミラー sync、helix-doctor-json.bats に **新規 5 exit テスト**（--gate clean=exit0 / no-gate=exit0 / --gate+strict-full-flow=exit1 fail-close 実証 / **fresh checkout project-state 非依存=exit0 P0 回帰ガード**）。ci-gate-surface-audit に ci_detector_gate surface。F4 push-event ratchet は DF-FCCI-CI-RATCHET-PUSH で既知 debt 化（TL 裁定、push_gate が authoritative）。F2/P3=cosmetic 非アクション。**PM 再検証 = contract 88 / helix-doctor-json bats 17（新規5含む）/ l0-l14 bats 57 / fresh checkout exit0 全 green**。 | PM (Opus) + verify Workflow（16 agent / 7 confirmed） |

## 9. 再活性化（2026-06-14）= 残差スコープ・TL 裁定・完遂境界

### 9.1 起点 / 何が既に landed したか
ユーザー goal「ゲートの fail-close/CI 昇格を先に固める」（L7 product 実装の前にゲートを固める）で本 ticket を再活性化。本 ticket 起票（2026-06-08）後に **pre-L7 gate-hardening Phase1/2** が landed し、以下は**充足済**:
- `helix doctor --gate`（`GATE_MODE` で `check_vg_overview_gate` を走らせ `overall_clean=false` なら exit 1）= [cli/helix-doctor:2613](../../../cli/helix-doctor)。
- `helix push --gate` の **8th gate = G-vg-overview**（`vg_overview.overall_clean` を blocking 判定）= [cli/lib/push_gate.py:713](../../../cli/lib/push_gate.py)。
- `vg_overview.required_clean` = 11 detector（full fail-close 7 + changed-files ratchet 4）= [cli/lib/vg_overview.py:266](../../../cli/lib/vg_overview.py)。

→ **fail-close gate は local（push + doctor）では既に効いている**。**真の残ギャップ = CI が `helix doctor --gate` を一度も実行していない**（[.github/workflows/ci.yml](../../../.github/workflows/ci.yml) は pytest/bats/helix-test/helix-verify-all/drift-check のみ）= 局所 push だけ fail-close で CI 素通りの構造ギャップ（W4 / TL P1）。

### 9.2 残差スコープ（TL 裁定反映）
- **WI-1（主）**: `ci.yml` に専用 job `detector-gate` を追加 → `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json` を Required check 化（当初 `helix doctor --gate --json` の予定だったが、敵対的検証 Workflow が「全体 `helix doctor --gate` は `.helix/` 不在の fresh checkout で常時 red」= P0 を検出 → TL 再諮問で **C-fix 採用** = vg_overview.overall_clean のみ fail-close 評価する subcommand 形式へ変更。§9.3/§10 + 進捗ログ参照）。
  - **anchor-only**（`HELIX_DOCTOR_SKIP_EXEC_TESTS=1`）= 既存 pytest/bats job と二重実行・timeout・flake を gate 判定に混ぜない（TL 裁定2）。実測: skip-exec で `overall_clean=true anchored=98/98 exec_pass=98`。
  - **strict-full-flow / strict-vmodel-pair-freeze は含めない**（strict full-flow=G8/G9/G12/G14 deferred、strict pair=rc=1=critical:3 → CI 即 red、TL P1）。
  - **job 名 `detector-gate` を安定固定**（Required check 登録後の改名は branch protection を壊す、TL P2）。
  - **PR 差分で `HELIX_CHANGED_FILES` 相当を明示解決**し ratchet detector が `source_status=unavailable` skip に落ちないようにする（CI 接続したが ratchet 不発、を防ぐ、TL P2）。
  - permissions 最小（contents: read）、`concurrency: cancel-in-progress` は workflow level 既存に従う。
- **WI-2**: 境界契約 unpark（**3点同期**: 境界 audit yaml + Python 契約 `test_helix_l0_l14_flow_contract.py` + bats ミラー `test-helix-l0-l14-flow-contract.bats`）。`detector_failclose_ci_gate` を `parked_feature_ticket_outside_current_objective_set` → current objective へ再分類。**still-PARKED 維持**: full-required 昇格 / strict pair / L7 product / DB schema。
- **WI-3（やらない = deferred）**: ruff/shellcheck CI install は今回 WI から外す（TL 裁定4、小さく CI gate を先に通す）。**4 ratchet detector の full-required 昇格は全て deferred**（baseline 債: import-cycle 5循環 / plan-dependency 49警告 / fr_uses 3違反 / coding_rule は ruff/shellcheck 未install で linter 実質未走）= §10 deferred。
- **付随更新**: TL 資産 [ci-gate-surface-audit.yaml](../../../docs/v2/L7-test-design/ci-gate-surface-audit.yaml) の `ci_or_equivalent_connected: false → true`・status・pass 実測 drift（33→34、TL P3）。automation-gate-map に CI gate 配線を登録。

### 9.3 TL 裁定（gpt-5.5 high, 2026-06-14）= 条件付き推奨
1. CI gate = `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json` のみ（push --gate を CI に二重化しない＝gate 責務と push UX を混ぜない）。**※当初 TL 裁定は全体 `helix doctor --gate --json` だったが、実装後の敵対的検証で「全体 doctor --gate は `.helix/` 不在の fresh checkout で常時 red」= P0 を検出 → TL 再諮問で C-fix（vg_overview.overall_clean のみ fail-close する subcommand）へ変更（§10 / 進捗ログ参照）。**
2. CI の `detector-gate` は anchor-only（exec skip）。
3. ratchet 4件は全て full 昇格 deferred（債あり）、changed-files ratchet 維持。
4. ruff/shellcheck は今回外す（advisory にするなら continue-on-error + 別 job/step）。
5. 境界 unpark は CI配線 + 既存 ratchet enforcement の current objective 化のみ。残りは forbidden/PARKED 維持。
6. 再凍結 = contract_extension・軽量。対象 = ci.yml / automation-gate-map / 本 ticket forward_return / 境界 audit / 契約 test。L6/L4 全面再凍結は不要（GatePolicy/DetectorReport の公開 exit semantics は変えない＝CI が既存 gate を呼ぶだけ）。

### 9.4 完遂境界（TL `ci-gate-surface-audit.yaml` 反映 = 過剰主張の禁止）
- **local doctor gate pass ≠ goal 完遂**、**push gate doc ≠ CI 完遂**。本 Action の完遂 = `ci.yml` に `detector-gate` job が存在し CI で `helix doctor check_vg_overview --gate --json` が実走すること（+ 境界 unpark + テスト固定）。
- **GitHub branch protection への Required check 登録自体は repo 設定側の手作業**（別権限）。CI job 追加 ≠ branch protection 完了。本 Action は **CI job 配線まで**を完遂境界とし、branch protection 登録は **handover の人間向け Next Action** として残す（TL 残リスク）。
- **strict full-flow（右腕 G8/G9/G12/G14）の closure は別 Action（W2）**。本 Action は左腕 L6 focus gate の CI 配線に限定し、右腕 deferred gate を隠さない。

### 9.5 実装順序（テストファースト・3点同期厳守）
1. **契約 test を先に変更（TDD red）**: `test_helix_l0_l14_flow_contract.py` に「ci.yml に `detector-gate` job が存在し exec-skip doctor --gate を実行」「strict/full-required が job に未混入」「境界 audit が detector_failclose_ci_gate を current scope 化」を assert 追加 + 既存 parked assert を current へ更新。**bats ミラーの count を同時 sync**（前 session の sync 漏れ G-tests BLOCK 再発防止）。
2. 境界 audit yaml 群の `detector_failclose_ci_gate` 再分類。
3. `ci.yml` に `detector-gate` job 追加。
4. automation-gate-map + ci-gate-surface-audit.yaml 更新。
5. PM 独立検証（pytest/bats/contract/doctor --gate exit 0 維持）→ TL impl review → 反映 → re-review approve → gate-driven push。

## 10. deferred findings（floating debt 化させない = §0 絶対原則）
本 Action でやらない残件。各々 Forward 帰属先を持つ（standing roadmap 化しない）。
- **DF-FCCI-RATCHET-FULL**: 4 ratchet detector（coding_rule_lint / dependency_cycle_checks / plan_dependency_gate / fr_uses_checks）の full-required 昇格。阻害 = baseline 債（import-cycle 5循環 / plan-dependency 49警告 / fr_uses 3違反 / coding_rule は ruff/shellcheck 未install）。帰属 = L6↔L7 G7 pending gate evidence + weakness-map W17/W18。各 detector の baseline が clean 化（債解消）してから per-detector で full 化。**現状 changed-files ratchet で新規違反は既に block 済**（無防備ではない）。
- **DF-FCCI-RUFF**: ruff/shellcheck の CI install + advisory step。帰属 = weakness-map W17。CI gate 接続が安定してから別 Action で advisory（continue-on-error）追加。
- **DF-FCCI-STRICTFLOW**: strict full-flow（右腕 G8/G9/G12/G14）の CI required 化。阻害 = 右腕実行ゲート未配線（strict full-flow overall_clean=false, deferred=4）。帰属 = weakness-map **W2**（右腕 L8/L9/L12/L14 実行ゲート）。別 Action。
- **DF-FCCI-BRANCHPROT**: GitHub branch protection への `detector-gate` Required check 登録（repo 設定・別権限の人間作業）。帰属 = handover の人間向け Next Action。CI job 配線完了後にユーザーが GitHub 設定で登録。
- **DF-FCCI-CI-RATCHET-PUSH**: CI `detector-gate` の **ratchet detector（4件）は `push:[main]` event で vacuous**（push では HELIX_CHANGED_FILES export step が無く [PR-only]、detached HEAD → `changed_files()` が `source_status=unavailable` → `_ratchet_required_clean` が clean=True に override = fail-OPEN）。**PR event は `fetch-depth: 0` で merge-base 到達性を確保し ratchet が効く**（本 Action で対処済）。push event の vacuous は**受容（TL P0 諮問で既知 debt 裁定）**: ① `helix push --gate` が ratchet の authoritative gate（changed-files を upstream→merge-base→unavailable+reason で robust 解決し HELIX_CHANGED_FILES を set）② `main` は PR-gated で PR path の ratchet が効く ③ ratchet は新規 changed-file 違反のみ対象（baseline 債は DF-FCCI-RATCHET-FULL で別管理）④ CI の非 ratchet 7 check + 構造 detector は全 event で enforce。push event ratchet の robust 化（`github.event.before..github.sha` 差分注入）は別 Action。帰属 = weakness-map W4 + L6↔L7 G7 pending evidence。検証 = 敵対的 Workflow F4（confirmed P2）。
