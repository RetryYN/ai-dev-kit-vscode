---
plan_id: L7-test-failures-triageplan
title: "L7-test-failures-triageplan: cli/tests sweep 11 failures triage"
kind: troubleshoot
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: QA
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: cli/tests/
pairs_test_design: cli/tests/
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM advisor - scope and priority review for failure triage split"
  - role: tl-advisor
    slot_label: "TL advisor - root cause and non-regression review"
  - role: se
    slot_label: "SE - follow-up implementation owner for split fix PLANs"
  - role: qa
    slot_label: "QA - sweep reproduction, classification, quality gate judgment"
generates:
  - artifact_path: docs/plans/L7/L7-test-failures-triageplan.md
    artifact_type: design_doc
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-9mode-cli-e2e-verificationplan.md
    - docs/plans/L7/L7-route-engine-4mode-extplan.md
    - docs/plans/L7/L7-scrum-to-discovery-renameplan.md
  blocks:
    - docs/plans/L7/L7-route-list-signals-regression-fixplan.md
    - docs/plans/L7/L7-size-discovery-alias-test-fixplan.md
    - docs/plans/L7/L7-skill-chain-evidence-fixplan.md
    - docs/plans/L7/L7-codex-allowed-files-regression-fixplan.md
related_docs:
  - cli/tests/helix-route.bats
  - cli/tests/helix-size-drive-auto.bats
  - cli/tests/test-helix-skill.bats
  - cli/tests/test_helix_codex_allowed_files.bats
  - cli/lib/route_engine.py
  - cli/helix-size
  - cli/lib/skill_catalog.py
  - cli/helix-codex
  - cli/lib/codex_post_validation.py
---

# L7-test-failures-triageplan: cli/tests sweep 11 failures triage

## §1 背景

W8-A (9 mode CLI E2E verification) の `cli/tests/` full sweep で、9 mode CLI / route_engine 4 mode 接続とは別系統の既存 fail が 11 件再現した。本 PLAN は fail の再現、分類、root cause 推定、修正 PLAN 分割までを扱う。実際の修正は scope 外とし、`cli/tests/` と `cli/lib/` は read-only で調査した。

実行証跡:

| Command | Result |
|---|---|
| `bats cli/tests/` | `not ok - missing file: cli/tests/`。この環境の bats は directory argument を受け付けない |
| `bats cli/tests/*.bats` | `1..584`, failed 11 tests |
| `helix doctor` | `25 pass, 0 fail, 94 warn` |
| `helix code find "bats cli tests route size skill codex allowed-files"` | internal Codex read-only session creation failed, local fallback returned code catalog matches |

直近履歴:

| Range | Observed commits |
|---|---|
| 本 session | `53c8c28` common skill V2 rename, `61de6be` route C8 integration test, `e815745` route_engine 4 mode extension, `9496a34` 9 mode CLI E2E bats, `e0f0bfc` HELIX-workflows V2 ecosystem doc |
| 前 session 含む | `9fadf81` discovery migration, `ebbce41` 9 mode CLI整備, `42f0488` commands index drift fix |

## §2 fail 一覧

`bats cli/tests/*.bats` raw output の failed list と、個別再現で採取できた actual output を集約する。現行 bats runner は assertion diagnostic を出さない fail があり、その場合は `not ok` 行を error message として記録する。

| # | Test name | file | error message / observed actual |
|---|---|---|---|
| 1 | FAIL helix route list-signals shows 7 signals and 1 alias | `cli/tests/helix-route.bats` | `not ok 102 - helix route list-signals shows 7 signals and 1 alias`; actual `helix route list-signals` line_count=`19`, test expected `11` |
| 2 | FAIL --uncertain -> scrum (検証駆動 案内) | `cli/tests/helix-size-drive-auto.bats` | `not ok 115 - --uncertain -> scrum (検証駆動 案内)`; actual JSON `{"size": "M", "drive": "discovery", "mode": "discovery", "phases": []}`, test expected `"drive": "scrum"` and `"mode": "scrum"` |
| 3 | FAIL --uncertain --ui -> scrum (uncertain が最優先) | `cli/tests/helix-size-drive-auto.bats` | `not ok 116 - --uncertain --ui -> scrum (uncertain が最優先)`; actual JSON `drive=discovery`, test expected `drive=scrum` |
| 4 | FAIL --drive scrum 明示 -> scrum | `cli/tests/helix-size-drive-auto.bats` | `not ok 117 - --drive scrum 明示 -> scrum`; actual JSON `{"size": "M", "drive": "discovery", "mode": "discovery", "phases": []}`, stderr includes `[DEPRECATED] --drive scrum は legacy alias です。内部では discovery として扱います。` |
| 5 | FAIL PLAN-024 W-2d: helix skill chain records evidence entry | `cli/tests/test-helix-skill.bats` | `not ok 506 - PLAN-024 W-2d: helix skill chain records evidence entry`; failing assertion is `assert_evidence_entries` after `helix skill chain "test"` |
| 6 | FAIL different plan baseline candidate is ignored without auto-detect hint | `cli/tests/test_helix_codex_allowed_files.bats` | `not ok 560 - different plan baseline candidate is ignored without auto-detect hint`; manual reproduction status=`1`, output includes `エラー: --allowed-files 外の変更を検出しました ... tracked-b.txt` |
| 7 | FAIL no plan-id skips auto-detect hint | `cli/tests/test_helix_codex_allowed_files.bats` | `not ok 561 - no plan-id skips auto-detect hint`; bats assertion diagnostic unavailable |
| 8 | FAIL stale pid baseline candidate does not trigger auto-detect hint | `cli/tests/test_helix_codex_allowed_files.bats` | `not ok 562 - stale pid baseline candidate does not trigger auto-detect hint`; bats assertion diagnostic unavailable |
| 9 | FAIL forged baseline candidate outside trust boundary does not trigger auto-detect hint | `cli/tests/test_helix_codex_allowed_files.bats` | `not ok 563 - forged baseline candidate outside trust boundary does not trigger auto-detect hint`; bats assertion diagnostic unavailable |
| 10 | FAIL symlink baseline candidate does not trigger auto-detect hint | `cli/tests/test_helix_codex_allowed_files.bats` | `not ok 564 - symlink baseline candidate does not trigger auto-detect hint`; bats assertion diagnostic unavailable |
| 11 | FAIL codex allowed-files new file case completes without auto-detect hint | `cli/tests/test_helix_codex_allowed_files.bats` | `not ok 565 - codex allowed-files new file case completes without auto-detect hint`; manual reproduction status=`1`, output includes `エラー: --allowed-files 外の変更を検出しました ... rogue.txt` |

## §3 fail 分類

| Category | Tests | Root cause axis | Non-regression note |
|---|---:|---|---|
| A: route 系 | 1 | `route_engine.SIGNAL_TO_MODE` 追加後、legacy test の expected signal count が古い | `test-route-engine-4mode-integration.bats` と `test-route-engine-c8-integration.bats` は PASS。4 mode 接続自体は non-regression |
| B: size 系 | 3 | `scrum` legacy alias が runtime output では `discovery` に正規化されたが、tests が旧 `scrum` 期待のまま | `helix-size` は stderr で deprecated alias を明示しており、Discovery rename 方針とは整合 |
| C: skill 系 | 1 | `helix skill chain` の evidence entry 記録が空、または fake recommender 経路と evidence insert 条件が drift | `helix skill use common/testing` の skill_usage entry は PASS |
| D: codex allowed-files | 6 | `helix-codex` post-validation が `--allowed-files` 外の new/modified file を fail-close するようになり、旧 test の「警告なしで status 0」期待と衝突 | `baseline existing untracked file touch is ignored` は PASS。既存 untracked touch と新規/変更検出の境界が焦点 |

## §4 triage 結果 + 別 PLAN 候補

### A: route 系 triage

`cli/lib/route_engine.py` は `user_feedback_iteration`, `production_incident`, `feature_addition`, `agent_runaway` などの shortcut signals を追加済み。`helix route list-signals` は 19 行を返す。fail は実装退行ではなく、legacy bats の "7 signals and 1 alias" という固定件数期待が 9 mode 拡張後の契約とズレたもの。

修正 PLAN 候補:

| PLAN candidate | Scope | Acceptance |
|---|---|---|
| `docs/plans/L7/L7-route-list-signals-regression-fixplan.md` | `helix-route.bats` の expected count / title / signal set を 9 mode + alias 契約へ更新 | route legacy + 4mode + C8 integration 全 PASS |

### B: size 系 triage

`cli/helix-size` は `--uncertain` と `--drive scrum` を受け付けた後、`scrum` を deprecated alias として `discovery` へ正規化する。tests は旧 `"drive": "scrum"` / `"mode": "scrum"` を期待している。現行 workflow 正本では Discovery が正であり、test 側更新が妥当。

修正 PLAN 候補:

| PLAN candidate | Scope | Acceptance |
|---|---|---|
| `docs/plans/L7/L7-size-discovery-alias-test-fixplan.md` | size drive auto tests を `discovery` 正規化契約へ更新し、deprecated stderr 期待を追加 | `bats cli/tests/helix-size-drive-auto.bats` PASS |

### C: skill 系 triage

`test-helix-skill.bats` は fake recommender で `helix skill chain "test"` を実行し、`.helix/helix.db` の `entries WHERE axis='evidence'` が 1 件以上になることを期待している。`helix skill use` 側の `skill_usage` insert は PASS しており、chain 経路だけ evidence insert が抜けている可能性が高い。

修正 PLAN 候補:

| PLAN candidate | Scope | Acceptance |
|---|---|---|
| `docs/plans/L7/L7-skill-chain-evidence-fixplan.md` | `helix skill chain` の evidence entry write path を調査し、fake recommender / fallback 経路でも記録される契約に統一 | `bats cli/tests/test-helix-skill.bats` PASS、evidence axis row ≥1 |

### D: codex allowed-files triage

`cli/helix-codex` は `--allowed-files` 指定時に before/after snapshot を取り、`cli/lib/codex_post_validation.py` で許可外変更を検出する。manual reproduction では `tracked-b.txt` と `rogue.txt` が fail-close される。現 test 名は「auto-detect hint が出ない」ことを主眼にしつつ、helper `run_tracked_b_change_case 0` により status 0 も期待しているため、現行 fail-close 契約と衝突している。

修正 PLAN 候補:

| PLAN candidate | Scope | Acceptance |
|---|---|---|
| `docs/plans/L7/L7-codex-allowed-files-regression-fixplan.md` | allowed-files post-validation の契約を再確認し、test を fail-close 期待へ更新するか、same-plan baseline 例外の仕様を narrow に修正 | `bats cli/tests/test_helix_codex_allowed_files.bats` PASS、unauthorized new/modified file の fail-close 維持 |

## §5 priority 評価

### route list-signals test drift (P1)

release blocker ではないが、9 mode 拡張後の CLI contract test が fail しており、次 session で更新すべき。実装本体の route_engine 4 mode / C8 tests は PASS しているため P1。

### size scrum to discovery alias test drift (P1)

Discovery rename の正本化と旧 bats 期待の drift。ユーザー導線に関わるが、runtime は deprecation message 付きで動作しているため P1。

### skill chain evidence write regression (P1)

evidence/audit 欠落は HELIX discipline の追跡性に影響する。`skill use` は PASS しているため範囲は chain 経路に限定できるが、品質ゲート証跡に関わるため P1。

### codex allowed-files post-validation contract drift (P0)

委譲 Codex の許可外変更検出は安全境界であり、test 期待と実装契約のズレを放置すると gate の信頼性が落ちる。修正方針は「fail-close 維持」を前提に早期確定が必要なため P0。

### bats directory invocation compatibility (P2)

TASK 指定の `bats cli/tests/` はこの環境で `missing file` になるが、`bats cli/tests/*.bats` で同じ sweep を実行可能。開発体験改善として runner wrapper 側で吸収する候補だが、11 fail 本体とは別なので P2。

## §6 品質レベル判定 (QA)

| Dimension | Level | Evidence |
|---|---:|---|
| density | 4 | 584 tests sweep、対象 4 files 個別再現、doctor 実行済み |
| depth | 3 | root cause はコード read と manual actual で推定。一部 bats assertion diagnostic が runner から出ない |
| breadth | 4 | route / size / skill / codex allowed-files の 4 系統を分類 |
| accuracy | 3 | fail 名は機械収集。詳細 error は available output に限定 |
| maintainability | 4 | 修正 PLAN を 4 分割し、safety-critical allowed-files を独立化 |

総合品質レベル: T3.5 相当。triage PLAN としては G6 QA 判定 pass、修正実装ゲートは別 PLAN で再判定する。

## §7 helix doctor advisory

`helix doctor` は `25 pass, 0 fail, 94 warn`。今回 fail triage に直接関係する fail はなし。warn の主な内容は以下:

| Advisory | Summary |
|---|---|
| phase/mode consistency | `mode=discovery` だが `phase=L4`、scrum legacy value migration advisory |
| V-model 4 artifact lint | 67 incomplete PLAN advisory |
| design doc reference sections | 19 docs with empty industry standard reference section |
| PLAN ADR snapshot advisory | PLAN-175 / 176 / 202 missing ADR snapshot |
| subagent/sprint mechanization | mandatory subagent absence and sprint completion advisory |
| stale locks | stale lock check warns on test lock artifacts |

## §8 検証コマンド

| Command | Result |
|---|---|
| `bats cli/tests/*.bats` | 573 pass / 11 fail / 584 total |
| `bats cli/tests/helix-route.bats` | 10 pass / 1 fail |
| `bats cli/tests/helix-size-drive-auto.bats` | 6 pass / 3 fail |
| `bats cli/tests/test-helix-skill.bats` | 1 pass / 1 fail |
| `bats cli/tests/test_helix_codex_allowed_files.bats` | 2 pass / 6 fail |
| `helix doctor` | 25 pass / 0 fail / 94 warn |

## §9 scope 外

- `cli/tests/` の修正
- `cli/lib/` / `cli/helix-*` の修正
- 新規 sub-PLAN file の実作成
- commit / push

## §10 G4/G6 判定

| Gate | Decision | Rationale |
|---|---|---|
| G4 implementation quality | pass for triage artifact | PLAN 作成のみ。既存 fail 修正は scope 外 |
| G6 verification quality | pass with residual risk | 11 fail 全件を機械収集し、doctor 0 fail を確認。一部 runner が assertion detail を出さないリスクあり |

未検出リスク:

- Bats runner が assertion diagnostic を省略するため、D category の 4 件は exact assertion value まで未確定。
- `bats cli/tests/` directory invocation は環境依存の可能性があり、CI の bats version と差異がある。
- allowed-files は安全境界のため、test 更新前に TL/security 観点で fail-close 契約を再確認する必要がある。

## §11 carry

本 PLAN は triage のみで完了。修正は以下の PLAN に分割して起票する。

| Priority | Follow-up PLAN | Category | Action |
|---|---|---|---|
| P0 | `docs/plans/L7/L7-codex-allowed-files-regression-fixplan.md` | D | allowed-files fail-close contract と tests の整合 |
| P1 | `docs/plans/L7/L7-route-list-signals-regression-fixplan.md` | A | route list-signals expected count / signal set 更新 |
| P1 | `docs/plans/L7/L7-size-discovery-alias-test-fixplan.md` | B | scrum legacy alias tests を discovery 正規化へ更新 |
| P1 | `docs/plans/L7/L7-skill-chain-evidence-fixplan.md` | C | skill chain evidence entry write path 修正 |
| P2 | `docs/plans/L7/L7-bats-directory-sweep-compatplan.md` | runner | `bats cli/tests/` directory argument compatibility or wrapper |
