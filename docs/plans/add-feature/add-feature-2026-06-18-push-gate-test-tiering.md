---
plan_id: add-feature-2026-06-18-push-gate-test-tiering
title: "Action(add-feature): push-gate の G-tests をティア化 (auto: 軽量/フル自動判定) + dogfood CI full backstop + D-CONTRACT gate enum drift 修正"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: push_gate (G-tests) の G7 実装凍結証跡経路。本 Action は G-tests の test 実行を毎回 full から auto(軽量/full 自動判定)へ拡張し、dogfood の CI full backstop を明文化、D-CONTRACT gate enum の既存ドリフト(G-vg-overview 欠落)を同期。
forward_return: "push_gate.py G-tests に test tier (auto/full) を導入 (auto=changed-files-scoped 軽量、full トリガ該当時は従来 full) -> changed_files selector を保守 bucket+full fallback で実装 -> ci.yml に dogfood/feature/* を full backstop 追加 -> D-CONTRACT §4.5 gate enum に G-vg-overview 追加 + test_tier semantics 記載 -> docs/commands/push.md + github-operations §3.5 (push policy SSoT) 同期 -> L7 境界契約に本 Action を current_scope_authorized 追加 + count 22->23 同期 -> G7/push gate pending gate evidence に帰属."
drive: be
status: completed
status_note: "2026-06-18 完遂。ユーザー指示『毎回フルはいらない。フル/軽量を分けろ』→ AskUserQuestion で『CI backstop 追加 + auto 軽量化』選択。G-tests auto tier 化(fail-close) + dogfood/feature CI backstop + D-CONTRACT/D-API/push.md/github-ops 契約同期(G-vg-overview ドリフト解消含む) + count 22→23。tl-advisor: 設計諮問=passed / impl review=changes_required(P1×3)→round2解消 / re-review=changes_required(P2 allow_main return_key/P3 feature**)→PM doc-sync で closure。検証=pytest 175→165(doc編集後) all pass / fail-close 各ケース full / ライブ tier 現変更(push_gate含む)→full・局所→auto / --full parse PASS。landing は self-push=full tier(push_gate.py が FULL_TRIGGER)。"
current_task_scope: push_gate_test_tiering
approval_required_before_l7_work: false  # ユーザー AskUserQuestion (2026-06-18) で本 scope を明示承認
tl_review: approve  # 設計諮問 passed / impl review changes_required(P1×3)→round2 / re-review changes_required(P2/P3 doc-sync)→PM 修正+contract test 検証で closure。substance approve。
ticket_is_completion_evidence: false
created: 2026-06-18
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): push_gate.py G-tests に test tier 判定 (auto/full) + changed_files selector (保守 bucket+full fallback)"
  - "CI: ci.yml に dogfood/feature/* push を full backstop として追加"
  - "契約: D-CONTRACT §4.5 gate enum に G-vg-overview 追加 + test_tier semantics、push.md / github-operations §3.5 同期"
design_change_class: design_or_contract_changed  # push gate G-tests の test 実行範囲を毎回 full から auto へ拡張 (gate 公開契約 evolution) + D-CONTRACT gate enum 同期 + CI trigger 追加。G-tests ID / 既存 flag 意味は不変 (非破壊)。再凍結 scope: L6-L7 (push gate 機能設計)。
agent_slots:
  - role: se
    slot_label: "SE — push_gate test tier 判定 + changed_files selector + ci.yml + 契約 doc 同期 + pytest/bats（Codex）"
  - role: tl-advisor
    slot_label: "TL — tier 判定の安全性 / full トリガ網羅 / 契約非破壊 / dogfood backstop / fail-close 既定 の adversarial check"
generates:
  - artifact_path: cli/lib/push_gate.py
    artifact_type: code
  - artifact_path: cli/lib/changed_files.py
    artifact_type: code
  - artifact_path: .github/workflows/ci.yml
    artifact_type: ci_config
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-18-fruses-reverse-derived-promotion.md
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/github-operations.md
  - docs/commands/push.md
  - docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-draft.md
  - cli/lib/push_gate.py
  - cli/lib/changed_files.py
---

# Action: push-gate G-tests ティア化 (auto: 軽量/フル自動判定) + dogfood CI backstop + 契約同期

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。ユーザー指示「毎回フルはいらない。フルが必要なタイミングと軽量でいいタイミングを分けろ」。AskUserQuestion (2026-06-18) で「CI backstop 追加 + auto 軽量化」を選択。残り L7 Action 群を高速化する investment（push_gate.py = shared core を触るため本 Action 自身は full push で landing）。

## 1. 目的 / 解く問題
`helix push --gate` の G-tests は毎回 **full `pytest cli/lib/tests/`(~2611) + 全 bats(~796)** を実行し ~14分かかる。小さな局所変更でも全件回るため push が遅い。一方 ci.yml は **`main` のみ**対象で dogfood push を full backstop しない（= ローカル gate が dogfood の唯一の full）。

→ G-tests を **auto tier**（changed-files が局所かつ full トリガ非該当なら軽量、それ以外は full）に拡張し、**dogfood/feature を CI full backstop に追加**して軽量化を安全にする。併せて D-CONTRACT gate enum の既存ドリフト（G-vg-overview 欠落）を同期する。

## 2. スコープ
### In（この Action でやる）
- **push_gate.py G-tests の tier 判定** `decide_test_tier(changed_files, branch, flags)`:
  - `full` を返す条件（= TL full 必須トリガ、保守的）: `--full`/`--test-tier full` 明示 / branch∈{main, release/*} or `--allow-main` / changed-files source が unavailable / 変更に下記 FULL_TRIGGER パターン該当 / selector が空だが code 変更あり。
  - **FULL_TRIGGER パターン**: `pyproject.toml`, `requirements*.txt`, `.github/workflows/*`, `cli/lib/tests/conftest.py`, `cli/helix-test`, bats helper / test runner, shared core(`push_gate.py`/`changed_files.py`/`vg_overview.py`/`helix_db.py`/`plan_validator.py`), `docs/v2/L3-detailed-design/D-CONTRACT/*`, `HELIX-workflows/helix-process/github-operations.md`, `docs/commands/push.md`, `cli/config/functional-registry.yaml`, `HELIX-workflows/helix-process/automation-gate-map.md`, 契約 test mirror(`cli/lib/tests/test_helix_l0_l14_flow_contract.py` / `cli/tests/test-helix-l0-l14-flow-contract.bats`), test 削除/rename。
  - 既定 mode = `auto`。`full` 時は従来どおり full pytest+bats（**完全再現**）。
- **changed_files selector**（保守 bucket + full fallback、import-graph はやらない）: 変更 `cli/lib/<mod>.py` → `cli/lib/tests/test_<mod>*.py`、変更 `cli/lib/tests/test_*.py` → 自身、変更 `cli/tests/*.bats` → 自身、変更 `cli/helix-*` / `cli/<script>` → 対応 bats(best-effort)。**マップ不能な code 変更が1つでもあれば full fallback**。`cli/lib/changed_files.py` の既存機構を流用。
- **ci.yml**: `on: push: branches:` に `dogfood`、`feature/**` を追加（PR は main のまま）。dogfood push が full CI backstop されるようにする。
- **D-CONTRACT §4.5**: gate enum に `G-vg-overview` 追加（既存ドリフト修正）+ `test_tier`(auto/full) semantics と full トリガ記載。
- **契約 doc 同期**: `docs/commands/push.md`（`--full`/auto 既定/tier 挙動）、`HELIX-workflows/helix-process/github-operations.md §3.5`（push policy SSoT に tier 追記）。
- **detail 表示に mode**: gate 結果に `G-tests (tier=auto|full, pytest N + bats M)` を出力（監査可能化、TL P3）。
- pytest（TDD）: tier 判定の各トリガ→full / 局所変更→light / selector 空→full / unavailable→full / `--full`→full。selector マップの正当性。
- **L7 境界契約 evolution**: 本 Action を current_scope_authorized に追加、forbidden_now 不変、count 22→23 を全 pin 同期（C-3b 同様 audit yaml×6 + contract py + bats mirror、`aeb7013` diff をテンプレに +1）。

### Out（やらない）
- import-graph ベースの厳密 test selector（過剰、別 PLAN）。
- `pytest --lf/--ff` を push gate の安全根拠にする（cache 依存、不可）。
- 定期 full の CI cron（別途運用判断）。
- pytest 並列化（`-n auto`）（flaky リスク既知、別判断）。
- G-tests ID 変更 / 既存 flag(`--gate`/`--execute`/`--plan-id`/`--allow-main`)の意味変更。

## 3. 受入条件
1. **auto 既定 + full 完全再現**: 既定 `auto`。`--full` で従来の full pytest+bats を完全再現。`G-tests` ID 不変、既存 flag 意味不変。
2. **full トリガ網羅**: §2 の全トリガで full に倒れる。特に shared core / 契約 / conftest / workflows / changed-files unavailable / selector 空 → full（**fail-close**、skip しない）。
3. **light の正当性**: 局所変更（例: 単一 detector .py + その test）で light が選ばれ、変更関連 test のみ実行。マップ不能 code 変更混在で full fallback。
4. **CI backstop**: ci.yml が dogfood/feature push で full を回す（dogfood 軽量化の backstop 成立）。
5. **契約同期**: D-CONTRACT §4.5 に G-vg-overview + test_tier、push.md + github-ops §3.5 が一致（gate enum ドリフト解消）。
6. **境界契約整合**: 本 Action が current_scope_authorized、forbidden_now 不変、count 22→23 リップルが audit yaml + contract py + bats mirror で一貫（count-drift テスト green）。
7. **全テスト緑**: 全 pytest + 全 bats（本 Action は push_gate=shared core を触るので self-push は full）+ `helix push --gate --full` で従来同等に green。

## 4. テスト計画
- push_gate tier 判定 pytest（TDD、§2/§3 の各トリガ）。
- changed_files selector pytest（マップ正当性 + full fallback）。
- 契約 doc 整合（D-CONTRACT enum に G-vg-overview）。
- `helix push --gate --full` が従来 full と同等（self-push 検証）。

## 5. forward_return / 収束
- forward_return: frontmatter の通り。push gate 機能設計（G-tests tier）+ CI backstop + 契約同期 → G7/push gate pending gate evidence に帰属。
- design_change_class = design_or_contract_changed。再凍結 scope = L6-L7（push gate 機能設計）。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用。

## 6. escalation / リスク
- **最大リスク**: push gate (shared core) の挙動変更で全 push を壊す → ① 既定 auto は full トリガを保守的に網羅し迷えば full（fail-close）② `--full` で完全な従来挙動を温存（escape hatch）③ tier 判定を pytest で網羅拘束。
- dogfood に CI backstop が無いまま軽量化すると回帰見逃し → ci.yml に dogfood/feature 追加で同 Action 内に閉じる。
- 契約変更（D-CONTRACT/push.md/github-ops）は同時更新（drift 防止）。
- auth/payment/PII/secret/schema 変更なし。CI trigger 追加は infra 変更だが branch protection(main) は不変。

## 6.1 TL review 反映条件（tl-advisor 2026-06-18 = passed 条件付き推奨）
- P1: dogfood CI full backstop を明文化（ci.yml に dogfood/feature 追加）。← §2 In。
- P1: D-CONTRACT gate enum と実装/docs のドリフト（G-vg-overview 欠落）を同期。← §2 In。
- P2: import-graph 厳密 selector は初手で作らない → 保守 bucket + full fallback。← §2 In/Out。
- P2: changed-files unavailable は full fallback（skip 禁止）。← §3 受入2。
- P3: detail に tier mode を表示（軽量/full の監査可能化）。← §2 In。
- 公開契約不破壊: G-tests ID 維持 / 既存 flag 意味不変 / default auto を policy+docs に明記 / --full で full 再現 / selector 不能→full or fail-close。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-18 | Action 起票。ユーザー指示「毎回フルはいらない、フル/軽量を分けろ」→ AskUserQuestion で「CI backstop 追加 + auto 軽量化」選択。tl-advisor 設計諮問=passed(条件付き推奨)。事実確認: ci.yml は main のみ(dogfood backstop 無)、D-CONTRACT §4.5 enum に G-vg-overview 欠落(既存ドリフト)。次=Codex se TDD 実装。 | PM (Opus) |
| 2026-06-18 | 実装 round1（Codex se TDD）: decide_test_tier(fail-close: full/allow_main/main/release/unavailable/deleted-renamed/FULL_TRIGGER/unmapped→full) + FULL_TRIGGER_GLOBS(shared core+conftest+workflows+契約+registry+gate-map+contract mirror) + changed_files selector(保守bucket+full fallback) + ci.yml dogfood/feature backstop + D-CONTRACT G-vg-overview + push.md/github-ops 同期 + detail tier 表示 + count 22→23。pytest 154。 | Codex se |
| 2026-06-18 | TL impl review = **changes_required**（高リスク gate ゆえ厳格）: P1#1 cli/helix-push に --full/--test-tier 未配線(docs/push_gate のみ) / P1#2 source_status 未知値が full に倒れない(docs-only/malformed で 0 test pass 穴) / P1#3 test_helix_push.py 旧 detail pin / P2 D-API run_all_gates 旧6gate / P3 feature/* vs **。PM が3 P1 を独立再現確認。 | PM (Opus) + tl-advisor |
| 2026-06-18 | 実装 round2（Codex se）: P1#1 cli/helix-push 配線(usage+parser+HELIX_AUTOMATION_TEST_TIER 透過) / P1#2 source_status allowlist fail-close(known-good 以外→full) / P1#3 test_helix_push detail=tier=full,... 更新 / P2 D-API 8gate+test_tier 同期 / P3 feature/** 統一。PM 独立再検証: pytest 175/175、fail-close 各ケース full、ライブ tier 現変更(push_gate含む)→full・局所→auto、--full parse PASS。次=TL re-review。 | PM (Opus) + Codex se |
| 2026-06-18 | TL re-review: P1#1/#2/#3 **closure 確認**、設計妥当。残 P2[Blocking] D-CONTRACT return_keys に allow_main 欠落 / P3[nit] push.md feature/*。**PM doc-sync 直接修正**(G-tier 契約 doc): D-CONTRACT return_keys に allow_main + plan_id 追加(実装と一致)、push.md feature/**。contract test 含む pytest 165 pass で closure 検証。tl_review=approve(substance)、status=completed。次=commit + gate-driven push(--full)。 | PM (Opus) + tl-advisor |
