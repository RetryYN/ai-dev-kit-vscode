---
plan_id: L7-cli-helix-recovery-impl
name: L7-cli-helix-recovery-impl
description: cli/helix-recovery 新規実装 — Recovery mode workflow 進行・全体管理 CLI (recover/recovery 責務分離 + 発火条件 4 種機械化 + stop-hook 連携 + cutover_orchestrator 連携)
status: draft
process_layer: L7
kind: impl
drive: be
size: M
priority: P2
generates:
  - design: docs/v2/L7-design/L7-cli-helix-recovery-impl-design.md
  - test_design: docs/v2/L7-test-design/L7-cli-helix-recovery-impl-test-design.md
  - impl: cli/helix-recovery
  - test_code: cli/lib/tests/test_helix_recovery.py
  - test_bats: cli/lib/tests/bats/helix_recovery.bats
dependencies:
  requires:
    - L7-helix-recover-implplan
  parent: L7-helix-workflows-parent-acceptedplan
  blocks: []
parent_design: HELIX-workflows/helix-process/recovery-workflow.md
pairs_test_design: []
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 責務分離設計 adversarial check (recover/recovery 境界 / shared module 依存方向 / stop-hook 実装方式 / cutover_orchestrator 連携の適切性)"
  - role: se
    slot_label: "SE — cli/helix-recovery 実装 + recovery_workflow_engine.py + stop-hook 連携 + test 一式"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact 双方向 trace 整合チェック + recover/recovery 責務境界確認"
created: 2026-05-24
revised: 2026-05-24
owner: PM
is_reference: false
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/recovery-workflow.md](../../../HELIX-workflows/helix-process/recovery-workflow.md)
> **本 PLAN の対象**: `cli/helix-recovery` コマンドの新規実装。`cli/helix-recover` (実行層、commit 904c4f6 で実装完遂) との **責務分離** を明確化し、Recovery mode の **workflow 進行・全体管理** を担う CLI エントリーポイントを実体化する。
> **位置づけ**: CLAUDE.md / HELIX_CORE.md に「dedicated CLI 未整備、PLAN kind + recovery-log + stop-hook + cutover_orchestrator で運用」と carry 明示済の未実装 CLI を解消する。recovery-workflow.md の 6 ステップフローを CLI として完全実装する。
>
> **Recovery / Incident の kind 区別 (deviation-plan-map.md 根拠)**:
> deviation-plan-map の Incident 行 (kind: troubleshoot/recovery) と Recovery 行 (kind: recovery) は別。
> - Incident = 「本番障害 (SLO 逸脱)」で generates が module + test と recovery-log の両方
> - Recovery = 「AI 暴走・独断専行の収束」で generates は recovery-log のみ
>
> 本 PLAN (helix-recovery CLI) は Recovery mode に特化し、Incident の troubleshoot 操作は担わない。Incident mode は別 CLI (helix-incident、未起票) で対応する。本 PLAN kind=impl の根拠: Recovery mode の workflow doc (recovery-workflow.md) が設計凍結済みの状態で、そのフローを CLI として初期実装する Forward 標準案件。
>
> **automation-gate-map との接続**:
> automation-gate-map は Forward / Reverse / Scrum 各 mode の gate-checks.yaml 自動チェック仕様を定義する。Recovery mode は gate-checks.yaml の静的チェック適用範囲外であり、workflow doc 固有の DoD (§8) で代替する。

### integration-map.md §結論 carry との trace

**integration-map.md §コマンドの穴 #2「helix-recover (Recovery 起動)」は commit 904c4f6 で解消済** (実行層 CLI、C1-C4 condition 診断 + recovery-log dump)。
本 PLAN の `helix-recovery` は同 §carry #2 の後続として、recover (実行層) に対応する **workflow 管理層** を補完する。

責務分離の整理:
- `helix-recover` = stateless 単発操作 (commit 904c4f6 で実装完遂 = integration-map 穴 #2 解消)
- `helix-recovery` = stateful Phase 進行管理 (本 PLAN で新設 = integration-map 穴リストに**未記載の後続 CLI**)

**tl-advisor が「integration-map で定義されていない CLI を実装する正当性」を問う場合の回答**:
integration-map §コマンドの穴は「recover 起動」を欠けとして挙げており、recover 実装で穴の問題は解消された。
recovery (workflow 管理層) は recover を前提とする次段であり、integration-map 起票時点では recover 実装後の自然な拡張として後続設計されたもの。
integration-map §コマンドの穴の記述は「穴として認識された時点の snapshot」であり、recover 解消後の後続 CLI は scope 拡張 (not 穴) として扱う。

完了後 carry (C7):
integration-map.md §コマンドの穴 に「helix-recovery (workflow 管理層、本 PLAN で解消)」を追記し、穴リストを最新化する。

---

### parent_design (draft status) を採用する理由

`recovery-workflow.md` の frontmatter status は `draft` のまま。HELIX-workflows が 2026-05-24 commit 群で正本化直後であり、各 doc の status frontmatter 更新が後続作業として残っているため。本 PLAN は HELIX-workflows 正本群を **design-frozen 扱い** とし、L7 implementation を許可する。SE 実装時は親設計 (`recovery-workflow.md`) を変更しない。draft → accepted 更新は別 PLAN で batch 処理する。

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 参考調査 (recovery-workflow.md / cli/helix-recover 全実装 / rollback-applyplan / cutover_orchestrator.py API 確認) | PM | ✅ done |
| 2 | 責務分離設計 (recover/recovery 対応表 + shared module + 境界 sample CLI 実行例) | PM | ✅ done (§2) |
| 3 | subcommand 設計 (input/output/exit-code 仕様) | PM | ✅ done (§3) |
| 4 | 発火条件 4 種機械化設計 (条件検出ロジック / threshold) | PM | ✅ done (§4) |
| 5 | cutover_orchestrator 連携設計 | PM | ✅ done (§5) |
| 6 | stop-hook 連携設計 | PM | ✅ done (§6) |
| 7 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | □ pending |
| 8 | TL 指摘反映 | PM | □ pending |
| 9 | SE 委譲: cli/helix-recovery + cli/lib/recovery_workflow_engine.py 実装 | PM → SE | □ pending |
| 10 | bash -n / shellcheck / python3 -m py_compile 確認 | SE | □ pending |
| 11 | pytest test_helix_recovery.py + bats helix_recovery.bats 全 PASS | SE | □ pending |
| 12 | cli/helix router 登録 + `helix help` + `helix commands check` 確認 | SE | □ pending |
| 13 | docs/commands/index.md 更新 | SE | □ pending |
| 14 | pmo-sonnet で 4 artifact 双方向 trace 確認 | PM → PMO | □ pending |
| 15 | commit + push | PM | □ pending |

---

## §2 cli/helix-recover vs cli/helix-recovery 責務分離 (本 PLAN の核心)

### §2.1 責務分離の根拠

`helix recover` (commit 904c4f6) は **Recovery mode の実行操作** を担う「実行層 / 単発操作」CLI として既に実装完了済みである。本 PLAN で新設する `helix recovery` は Recovery mode の **workflow 全体の進行管理** を担う「workflow 進行層 / mode 管理」CLI である。

| 観点 | `cli/helix-recover` (実行層 / 既存) | `cli/helix-recovery` (workflow 層 / 本 PLAN) |
|---|---|---|
| **責務粒度** | 単発操作 (check / dump / plan / rollback dry-run / status) | workflow 全体管理 (start / phase / log / postmortem / done) |
| **実行者** | 人間または自動スクリプトが個別操作として直接呼ぶ | PM / SE が Recovery mode 期間中に phase 進行管理として呼ぶ |
| **state 保持** | stateless (毎回 helix.db から読み取る) | stateful (recovery session を `.helix/recovery/CURRENT.json` で追跡) |
| **cutover_orchestrator** | 連携なし (dry-run 範囲内) | `done` subcommand で `cutover_preflight()` / `cutover_execute()` を呼ぶ |
| **stop-hook** | stop-hook が生成した状態 dump を読み取る (受動) | stop-hook 連携を `start` subcommand で初期化、status を更新 (能動) |
| **PLAN kind 連携** | `plan` subcommand で kind=recovery PLAN draft を生成 | `start` subcommand で既存 kind=recovery PLAN を **登録** し、phase progress を追跡 |
| **postmortem** | なし (scope 外) | `postmortem` subcommand で recovery 完了後の postmortem 生成を担う |
| **destructive operation** | rollback --apply は別 PLAN (L7-helix-recover-rollback-applyplan) | `done` subcommand で cutover_execute() 呼び出し (確認 token 必須、cutover_orchestrator 経由) |

### §2.1.1 cross-cutting-mechanisms との位置づけ

本 CLI は HELIX の横断機構 (`helix interrupt` / `helix debt` / `helix drift-check` / `helix readiness`) とは **別レイヤー** に位置する。

- 横断機構 (`helix interrupt`): 開発中の割り込み (design_gap / new_requirement / constraint / po_change) を sprint_interrupted に遷移させる **割り込み検出層**
- Recovery (`helix recovery`): 重大な暴走・工程逸脱が確認された場合に Recovery mode の **workflow を進行管理する層**

接続フロー: `helix interrupt` で割り込みが sprint_interrupted に遷移し、その内容が重大 (C1-C2 相当) と判断された場合に Recovery へエスカレーションする。
`helix recovery start` の前段確認として `helix interrupt status` で発火済 interrupt がないか確認する設計を推奨する (§4.1 参照)。

### §2.2 境界を示す CLI 実行例

#### recover (実行層) が担うシナリオ

```bash
# AI が大規模変更をしたと気づいた直後の診断
helix recover check

# 状態を dump して recovery-log.md を生成
helix recover dump --output .helix/recovery/recovery-log.md

# recovery kind PLAN draft を生成 (helix-route から自動ルーティングされた場合)
helix recover plan --signal-id runaway --reopen-point HEAD~3 --auto-routed-from helix-route

# ロールバック候補の確認 (dry-run のみ)
helix recover rollback --dry-run
```

#### recovery (workflow 層) が担うシナリオ

```bash
# Recovery mode を開始 (PLAN ID を指定して session を初期化)
helix recovery start --plan-id RECOVERY-001

# 現在の Recovery phase を確認
helix recovery status

# Phase を進める
helix recovery phase --advance --from RP-3-reopen-confirm --to RP-4-correction

# recovery-log 全体の管理 (追記 / 表示 / export)
helix recovery log --show
helix recovery log --append "認識訂正: L5 詳細設計の API 契約が L3 要件と乖離していた"

# postmortem ドラフト生成
helix recovery postmortem --output docs/postmortem/recovery-2026-05-24.md

# Recovery 完了 (cutover_orchestrator.cutover_execute() を呼ぶ)
helix recovery done --confirm-token PO-APPROVED-RECOVERY-001
```

### §2.3 shared module の依存方向

```
cli/helix-recover  ──────────────────────────────────────────────→  cli/lib/recovery_engine.py
                                                                          │ (既存、commit 904c4f6)
cli/helix-recovery ──→ cli/lib/recovery_workflow_engine.py  ──────→  cli/lib/recovery_engine.py
                             (本 PLAN で新設)                          (read-only で利用)
                        │
                        ├──→ cli/lib/cutover_orchestrator.py  (cutover_preflight / cutover_execute)
                        ├──→ cli/lib/recovery_plan_check.py   (REQUIRED_TEMPLATE_SECTIONS 参照)
                        └──→ cli/lib/helix_db.py              (recovery session state 読み書き)
```

**依存方向原則**:
- `recovery_workflow_engine.py` は `recovery_engine.py` に依存する (上位層が下位層を呼ぶ)
- `recovery_engine.py` は `recovery_workflow_engine.py` に依存しない (循環依存禁止)
- `helix-recover` は `recovery_workflow_engine.py` に依存しない (実行層と workflow 層を疎結合に保つ)

---

## §3 subcommand 設計

### §3.1 helix recovery コマンド全体

```
helix recovery <subcommand> [options]

subcommand:
  start       Recovery mode session を開始し CURRENT.json を初期化
  status      現在の Recovery session と phase の状態を表示
  phase       phase を進める / 現在 phase を確認
  log         recovery-log.md の表示 / 追記 / export
  postmortem  Recovery 完了後の postmortem ドラフトを生成
  done        Recovery mode を完了し cutover_orchestrator へ引き渡す
  help        subcommand 一覧と使い方を表示
```

### §3.2 各 subcommand の仕様

#### helix recovery start

```
Usage: helix recovery start --plan-id <PLAN_ID> [--reopen-point <SHA|PLAN_ID>] [--dry-run]

Arguments:
  --plan-id        対応する kind=recovery PLAN の ID (必須)
  --reopen-point   再開ポイント (git commit SHA or PLAN ID、省略時は後で phase で設定可)
  --dry-run        CURRENT.json を書かず設定内容を stdout のみ表示

Exit codes:
  0: session 初期化成功
  1: PLAN ID 不在 / PLAN kind != recovery
  2: 既存 Recovery session が active (--force で上書き可)

Output (stdout):
  [HELIX Recovery] session 開始: RECOVERY-001
  再開ポイント: HEAD~3 (a1b2c3d)
  .helix/recovery/CURRENT.json を初期化しました
  次のステップ: helix recovery phase --show で現在 phase を確認
```

#### helix recovery status

```
Usage: helix recovery status [--json]

Exit codes:
  0: session active
  1: session なし
  
Output (stdout、通常):
  [HELIX Recovery] RECOVERY-001 (active)
  開始: 2026-05-24T14:30:00+09:00
  現在 Phase: RP-3 再開ポイント確定
  再開ポイント: HEAD~3 (a1b2c3d)
  発火条件: C1 大規模変更 WARN, C3 認識ズレ WARN
  recovery-log: .helix/recovery/recovery-log-RECOVERY-001.md (exists)
  Forward 復帰先: L5 詳細設計 (推定)

Output (--json):
  {
    "plan_id": "RECOVERY-001",
    "status": "active",
    "started_at": "2026-05-24T14:30:00+09:00",
    "current_phase": "RP-3",
    "reopen_point": "a1b2c3d",
    "triggered_conditions": ["C1", "C3"],
    "log_path": ".helix/recovery/recovery-log-RECOVERY-001.md",
    "forward_target": "L5"
  }
```

#### helix recovery phase

```
Usage: helix recovery phase [--show | --advance --from <phase_id> --to <phase_id>]

Phase ID 一覧 (recovery-workflow.md §基本フロー に対応):
  RP-1  ガード検出 (guard_detection)
  RP-2  警告/停止 (warning_and_stop)
  RP-3  状態把握 (situation_grasp)
  RP-4  再開ポイント確定 (reopen_confirm)
  RP-5  認識訂正 (correction)
  RP-6  ロールバック/再開 (rollback_and_resume)

Exit codes:
  0: 表示 / 遷移成功
  1: 遷移元 phase が現在 phase と不一致 (--force で強制)
  2: session なし (helix recovery start が未実行)
```

#### helix recovery log

```
Usage: helix recovery log [--show | --append "<text>" | --export <path>]

  --show              recovery-log.md の現在内容を stdout に表示
  --append "<text>"   recovery-log.md の §認識訂正履歴 に 1 行追記
  --export <path>     指定パスに recovery-log.md をコピー (docs/runbook 等へ移動用)

Exit codes:
  0: 成功
  1: log ファイル不在 (helix recovery start が未実行)
```

#### helix recovery postmortem

```
Usage: helix recovery postmortem [--output <path>] [--template <template_path>]

  --output    出力先 (default: docs/postmortem/recovery-<PLAN_ID>-<date>.md)
  --template  使用テンプレート (default: cli/templates/plan/recovery/postmortem-template.md)

Exit codes:
  0: 生成成功
  1: session 不在 / recovery-log 不在
  2: 出力先パスが既存 (--force で上書き可)

生成内容:
  recovery-log.md の 7 セクション (REQUIRED_TEMPLATE_SECTIONS) から key 情報を抽出し、
  postmortem テンプレートへ自動マッピング。L14 運用検証フィードバックへの入力となる。
```

#### helix recovery done

```
Usage: helix recovery done --confirm-token <token> [--forward-target <Lx>] [--dry-run]

  --confirm-token   PO-APPROVED-<PLAN_ID> 形式の承認トークン (必須、cutover_execute と同形式)
  --forward-target  Forward HELIX の再開ポイント L 工程 (default: session の reopen_point から推定)
  --dry-run         cutover_execute() を呼ばず動作確認のみ

処理フロー:
  1. helix recovery status で session が active か確認
  2. cutover_preflight() で事前チェック実行
  3. preflight PASS なら cutover_execute(confirm_token=...) を呼ぶ
  4. CURRENT.json を status=completed に更新
  5. Forward 復帰先 (--forward-target) を stdout に表示

Exit codes:
  0: 完了成功
  1: session 不在 / preflight FAIL
  2: confirm-token 形式不正

Output (stdout):
  [HELIX Recovery] RECOVERY-001 完了
  cutover_execute 結果: {"status": "ok", "timestamp": "..."}
  Forward 復帰先: L5 詳細設計
  次のステップ: helix plan status で L5 PLAN を確認してください
```

---

## §4 発火条件 4 種の機械化

recovery-workflow.md の「入口判定」(4 状況) と `helix-recover` の C1-C4 条件は同一の概念を指す。`cli/helix-recovery` では、**既存の `helix recover check` 結果を読み取る形で再利用** する。重複実装しない。

### §4.1 recovery start における自動診断

```
helix recovery start --plan-id RECOVERY-001
```

実行時に内部で `helix recover check --json` を呼び、C1-C4 の severity を CURRENT.json に記録する:

```json
{
  "plan_id": "RECOVERY-001",
  "status": "active",
  "triggered_conditions": [
    {"condition_id": "C1", "severity": "WARN", "source": "git_diff_numstat"},
    {"condition_id": "C3", "severity": "WARN", "source": "handover_current_json"}
  ],
  ...
}
```

**設計判断**: 発火条件 4 種を `helix-recovery start` で独自判定するのではなく、`helix recover check` に委譲する。回答 = **上位コマンドが下位コマンドの出力を入力にする設計** (DRY 原則)。

### §4.2 発火条件と Phase の対応

| 発火条件 | 条件 ID | 推奨開始 Phase | 優先対応 |
|---|---|---|---|
| AI が想定外の大規模変更をした | C1 | RP-2 警告/停止 | rollback dry-run を先行 (`helix recover rollback --dry-run`) |
| 独断専行で工程・設計から逸脱した | C2 | RP-1 ガード検出 | agent_mandatory 監査 log を確認 |
| 認識のズレが蓄積し収拾がつかない | C3 | RP-3 状態把握 | handover CURRENT.json の escalated 内容を `helix recovery log --append` で記録 |
| 予算・操作が過剰に消費されている | C4 | RP-2 警告/停止 | `helix budget status` で上限確認後、作業停止 |

### §4.3 複数条件が同時発火した場合

複数の C が WARN/FAIL の場合は、**最も severity が高い条件の推奨 Phase に従う**。同 severity ならば C2 > C1 > C3 > C4 の優先順序で最初の推奨 Phase を採用する。`helix recovery status` は全発火条件を列挙する。

---

## §5 cutover_orchestrator 連携設計

### §5.1 利用する API

`cli/lib/cutover_orchestrator.py` が提供する 2 関数を `helix recovery done` が呼ぶ:

```python
from cli.lib.cutover_orchestrator import cutover_preflight, cutover_execute

# done subcommand の内部処理
preflight_result = cutover_preflight()
if preflight_result.all_clear:
    result = cutover_execute(confirm_token=args.confirm_token)
else:
    print(f"[HELIX Recovery] cutover preflight FAIL: {preflight_result}")
    sys.exit(1)
```

### §5.2 設計上の注意点

cutover_orchestrator.py は PLAN-084 Phase 4.C (DB 分離 / イベントソーシング / cutover gate 5) 向けに設計された汎用モジュールである。Recovery mode での利用は **ロールバック・切替** の文脈として適切だが、以下の制限を設ける:

- **helix recovery done は cutover_preflight() + cutover_execute() のみを呼ぶ**。内部プローブ (`_default_dual_write_health_probe` 等) の設定は Recovery 用に別途ラップせず、default probe のまま利用する (PLAN-084 の設計責任内)
- confirm token の形式は `PO-APPROVED-<PLAN_ID>` を採用し、`cutover_orchestrator.py` の `_CONFIRM_TOKEN_PREFIX = "PO-APPROVED-"` と整合させる
- ロールバック対象が DB の場合は `cutover_execute()` が正しいが、git reset 相当の操作は `cli/helix-recover rollback --apply` (L7-helix-recover-rollback-applyplan) で行う。**helix recovery done は git reset を実行しない**

### §5.3 cutover_orchestrator が適用外のケース

Recovery の対象が「設計ドキュメントの訂正」のみで、DB や git 状態を変更しない場合は cutover_orchestrator の呼び出しを skip する。`helix recovery done --skip-cutover` フラグで明示 skip 可能。

---

## §6 stop-hook 連携設計

### §6.1 stop-hook の役割

recovery-workflow.md §二段構えの機構 に「stop-hook: 停止時の状態 dump + compact 推奨」と定義されている。既存の Stop hook (`.claude/hooks/`) が発火したとき、recovery mode と連携することで状態を保全する。

### §6.2 stop-hook → recovery の接続方法

Stop hook は Claude Code が終了する際に発火する。Recovery mode が active なとき (`CURRENT.json` が存在し `status=active`)、Stop hook は以下を行う:

```bash
# .claude/hooks/stop-recovery-update.sh (本 PLAN で新設)
#!/bin/bash
# Stop hook: Recovery session が active な場合に状態 snapshot を更新する

RECOVERY_CURRENT="$HELIX_PROJECT_ROOT/.helix/recovery/CURRENT.json"

if [[ -f "$RECOVERY_CURRENT" ]]; then
  STATUS=$(python3 -c "import json,sys; d=json.load(open('$RECOVERY_CURRENT')); print(d.get('status',''))")
  if [[ "$STATUS" == "active" ]]; then
    # 停止時刻を記録し、compact 推奨メッセージを出力
    python3 -m cli.lib.recovery_workflow_engine snapshot_on_stop
    echo "[HELIX Recovery] 停止を検出。recovery session (active) の状態を snapshot しました。"
    echo "[HELIX Recovery] 推奨: /compact を実行してから次の作業を開始してください。"
  fi
fi
```

### §6.3 stop-hook 登録方法

`.claude/settings.json` の `hooks` セクションに `Stop` matcher で登録する。既存の `helix-hook` 登録フレームワーク (`cli/lib/merge_settings.py`) 経由で管理する。

### §6.4 recovery → stop-hook の初期化

`helix recovery start` が実行されたとき、stop-hook が未登録であれば警告を表示する (auto-register はしない、hooks 変更は人間の承認が必要なため):

```
[HELIX Recovery] 警告: Stop hook (stop-recovery-update.sh) が未登録です。
手動登録: helix hook add stop stop-recovery-update.sh
または .claude/settings.json の hooks.Stop に追加してください。
```

---

## §7 Sprint 分割

### Sprint .1: 責務分離確定 + CLI 設計 (本 PLAN §2-§6 = done)

- 責務分離対応表 (§2.2) の確定
- subcommand 仕様 (§3) の確定
- 発火条件連携方式 (§4.1 委譲方式) の確定
- cutover_orchestrator 連携 API (§5) の確定
- stop-hook 連携設計 (§6) の確定
- tl-advisor 第 1 ラウンド (Step 7)

**DoD**: tl-advisor 第 1 ラウンド PASS (needs_revision 含む)。P1 指摘を §2-§6 に反映完了。

### Sprint .2: cli/helix-recovery + recovery_workflow_engine.py 実装

SE 委譲 (Codex SE)。実装対象:

```
cli/helix-recovery
  start | status | phase | log | postmortem | done | help
  → exec env PYTHONPATH=... python3 -m cli.lib.recovery_workflow_engine "$@"

cli/lib/recovery_workflow_engine.py
  RecoverySession (dataclass): plan_id / status / started_at / current_phase / triggered_conditions / reopen_point / log_path / forward_target
  start_session(plan_id, reopen_point) -> RecoverySession
  get_status() -> RecoverySession | None
  advance_phase(from_phase, to_phase) -> RecoverySession
  append_log(text) -> None
  export_log(dest_path) -> None
  generate_postmortem(output_path, template_path) -> None
  complete_session(confirm_token, forward_target, skip_cutover) -> dict
  snapshot_on_stop() -> None  ← stop-hook が呼ぶ
```

**DoD**:
- `bash -n cli/helix-recovery` PASS
- `python3 -m py_compile cli/lib/recovery_workflow_engine.py` PASS
- `shellcheck cli/helix-recovery` 警告 0 件
- 単体テスト (test_helix_recovery.py): start / status / phase 遷移 / log 追記 / done の基本フロー PASS

### Sprint .3: stop-hook 連携 + cli/helix router 登録

- `.claude/hooks/stop-recovery-update.sh` 新設
- `cli/helix` router に `recovery)` ルーティング行を追加
- `helix help` / `helix commands check` で `recovery` が表示されることを確認

**DoD**:
- `cli/helix recovery help` が usage を表示
- `helix commands check` PASS
- stop-hook が bash -n / shellcheck PASS

### Sprint .4: test 一式

- `cli/lib/tests/test_helix_recovery.py` (pytest): 15 ユニット以上
  - start session 成功 / PLAN kind != recovery で exit 1 / active session 重複で exit 2
  - phase 遷移正常 / 不正遷移で exit 1
  - log append / show / export
  - postmortem 生成 / テンプレート不在で exit 1
  - done 正常 (cutover mock) / preflight FAIL で exit 1 / token 形式不正で exit 2 / skip_cutover
  - snapshot_on_stop: CURRENT.json あり / なし
  - `helix recover check --json` 呼び出し mock で triggered_conditions 連携確認
- `cli/lib/tests/bats/helix_recovery.bats` (bats): 8 ケース以上
  - start / status / phase --show / log --show / done --dry-run / help

**DoD**: pytest 15 件以上 PASS / bats 8 件以上 PASS / カバレッジ対象 symbol が `coverage_eligible` bucket に登録済

### Sprint .5: docs 登録 + smoke test + 4 artifact trace

- `docs/v2/L7-design/L7-cli-helix-recovery-impl-design.md` 起草 (subcommand 仕様を 4 artifact ① 設計として明示)
- `docs/v2/L7-test-design/L7-cli-helix-recovery-impl-test-design.md` 起草 (テストケース一覧を ③ テスト設計として明示)
- `docs/commands/index.md` に `helix recovery` 行を追加
- smoke test: `helix recovery start --plan-id TEST-001 --dry-run` → stdout 確認

**DoD**:
- 4 artifact (設計 / 実装コード / テスト設計 / テストコード) が全て存在し、双方向 reference が完備
- `helix recovery --help` が全 subcommand を列挙

---

## §8 DoD (Definition of Done)

| 項目 | 判定基準 |
|---|---|
| CLI 実行 | `helix recovery start --plan-id X --dry-run` が stdout に設定内容を表示して exit 0 |
| router 登録 | `cli/helix` に `recovery)` ルーティング行が存在 / `helix commands check` PASS |
| 責務分離 | `cli/helix-recover` と `cli/helix-recovery` が §2.3 の依存方向を遵守 (循環依存なし) |
| cutover 連携 | `helix recovery done` が `cutover_preflight()` を呼び preflight FAIL で exit 1 |
| stop-hook | `stop-recovery-update.sh` が bash -n / shellcheck PASS、CURRENT.json active 時のみ snapshot_on_stop を呼ぶ |
| pytest | test_helix_recovery.py 15 件以上 PASS |
| bats | helix_recovery.bats 8 件以上 PASS |
| 4 artifact | 設計 / 実装 / テスト設計 / テストコードの双方向 reference 完備 |
| docs | docs/commands/index.md に `helix recovery` 記載 |
| helix doctor | `helix doctor` で本 PLAN に関する新規 FAIL が増えない |

---

## §9 受入条件

1. `helix recovery start --plan-id RECOVERY-001 --dry-run` を実行したとき、PLAN ID / 再開ポイント / 発火条件の一覧が stdout に表示され、`.helix/recovery/CURRENT.json` が作成されないこと
2. `helix recovery status --json` が JSON 形式で session 情報 (plan_id / status / current_phase / triggered_conditions) を返すこと
3. `helix recovery done --confirm-token PO-APPROVED-RECOVERY-001 --dry-run` を実行したとき、cutover_execute() が呼ばれないこと (dry-run 保護)
4. `cli/helix-recover` が `recovery_workflow_engine.py` を import しないこと (`grep -r "recovery_workflow_engine" cli/helix-recover` が 0 件)
5. `cli/helix-recovery` が `recovery_engine.py` を直接 import せず、`recovery_workflow_engine.py` 経由でのみ利用すること (依存方向の保証)
6. pytest 全 PASS / bats 全 PASS が CI で確認されること

---

## §10 risk / mitigation

| risk | 影響 | mitigation |
|---|---|---|
| recover / recovery 命名衝突 | ユーザーが helix recover / helix recovery を混同する | help / README で「recover = 単発操作、recovery = workflow 管理」を明示。`helix recover help` に recovery への誘導メッセージを追記 |
| cutover_orchestrator の default probe が未設定 | `cutover_preflight()` が `healthy: false` を返し done が常に FAIL | preflight FAIL 時に `--skip-cutover` フラグを案内する。default probe を wired にする必要がある場合は別 PLAN |
| stop-hook の自動登録なし | Recovery session active 中に Claude Code が終了しても snapshot されない | `helix recovery start` の警告メッセージで手動登録を促す。自動登録は hooks 変更に人間承認が必要なため scope 外 |
| helix recover check --json の出力形式変化 | recovery start での triggered_conditions 連携が壊れる | `recovery_workflow_engine.py` の `_parse_recover_check_output()` に schema version チェックを追加し、形式変化を fail-close で検出 |
| recovery session が stale になる (start したまま放置) | status コマンドが stale な session を返し続ける | `helix recovery status` で 7 日以上 active なものに stale 警告を表示。`--force-close` で手動クローズ可能 |
| postmortem テンプレート不在 | Sprint .5 でテンプレートを新設するまで postmortem subcommand が exit 1 | Sprint .5 の一部として `cli/templates/plan/recovery/postmortem-template.md` を作成。不在時は既存 recovery template.md を fallback で利用 |

---

## §11 V3 接続契約 (route → recovery 接続)

`cli/helix-route` (L7-helix-route-implplan) が Recovery mode へ routing した場合、以下の接続を使う:

```
helix route → (signal=runaway を検出) → helix recover plan --signal-id runaway --auto-routed-from helix-route
                                       → (recovery kind PLAN draft が生成される)
                                       → ユーザーが PLAN ID を確定
                                       → helix recovery start --plan-id <PLAN_ID>  ← 本 CLI の出番
```

`helix-recover` (実行層) は route からの **PLAN draft 生成** までを担い、`helix-recovery` (workflow 層) は **PLAN ID が確定した後の session 管理** を担う。route → recover → recovery の 3 段連携が Recovery mode の完全な流れとなる。

`helix-route` が recovery-workflow を start まで自動化することは **しない** (PM 承認が必要なため)。route はあくまでも `helix recover plan` の実行で停止し、PM が PLAN ID を確定させてから `helix recovery start` を手動実行する。

### §11.1 signal=runaway の出典 (detection-routing.md)

detection-routing.md は「AI 暴走 → Recovery」ルーティングを定義する。本 PLAN §4 / §11 の signal=runaway はこの vocabulary に対応する。

- detection-routing の上位 signal は「暴走」(日本語) であり、route_engine.py が signal_id=runaway として実装する
- signal_id は detection-routing が定義する vocabulary (runaway / budget / agent_mandatory 等) に限定する
- 本 PLAN の `helix recovery start` が `helix recover check --json` で読み取る triggered_conditions (C1-C4) は、route_engine の signal_id を **発火条件 ID に変換した後段表現** である

変換対応表:
| route_engine signal_id | recovery 発火条件 | 典型 Phase |
|---|---|---|
| runaway | C1 大規模変更 / C2 独断専行 | RP-1 / RP-2 |
| budget | C4 予算過剰消費 | RP-2 |
| agent_mandatory | C2 工程逸脱 | RP-1 |
| (interrupt escalation) | C3 認識ズレ蓄積 | RP-3 |

### §11.2 interrupt → Recovery エスカレーション (cross-cutting-mechanisms.md §4 つの横断機構)

cross-cutting-mechanisms の interrupt 機構 (`helix interrupt`) は、開発中の割り込みを sprint_interrupted に遷移させる。これが重大または暴走と判断された場合、Recovery へエスカレーションする。

発火条件 C2 (独断専行・工程逸脱) は interrupt で捕捉された後に Recovery へ昇格するケースが典型。
recovery start の前段として `helix interrupt status` で発火済 interrupt を確認する運用を推奨する (interrupt が active なら escalate 経路を確認してから recovery start を実行)。

---

## §12 関連 doc / 関連 PLAN

| doc / PLAN | 関係 |
|---|---|
| HELIX-workflows/helix-process/recovery-workflow.md | 正本設計 (parent_design) |
| docs/plans/L7/L7-helix-recover-implplan.md | 前提 PLAN (recover 実行層、implements = §2.3 の下位モジュール) |
| docs/plans/L7/L7-helix-recover-rollback-applyplan.md | 後続 PLAN (rollback --apply の destructive 操作、recovery done とは独立) |
| docs/plans/L7/L7-helix-route-implplan.md | 連携 (route → recover → recovery の 3 段連携) |
| cli/lib/recovery_engine.py | 依存モジュール (commit 904c4f6 で実装済) |
| cli/lib/recovery_plan_check.py | 依存モジュール (7 必須セクション契約) |
| cli/lib/cutover_orchestrator.py | 依存モジュール (done subcommand が利用) |
| cli/lib/helix_db.py | 依存モジュール (recovery session state の永続化) |
| HELIX-workflows/helix-process/deviation-plan-map.md | 参照 (kind=recovery の逸脱マップ、Recovery / Incident 区別の根拠) |
| HELIX-workflows/helix-process/detection-routing.md | 参照 (signal=runaway 出典、signal_id → 発火条件 C1-C4 変換の上位定義) |
| HELIX-workflows/helix-process/cross-cutting-mechanisms.md | 参照 (interrupt → Recovery 前段ガード、横断機構との層分離根拠) |
| HELIX-workflows/helix-process/automation-gate-map.md | 参照 (Recovery mode が gate-checks.yaml 適用範囲外であることの確認) |
| HELIX-workflows/helix-process/integration-map.md | 参照 (§コマンドの穴 #2 trace、CRITICAL 2 対応、C7 carry で更新予定) |
| HELIX-workflows/helix-process/incident-workflow.md | 参照 (Recovery と Incident の kind 区別、helix-incident CLI との scope 分離) |
| docs/commands/index.md | 更新対象 (Sprint .5) |

---

## §13 carry / 残課題

| carry | 優先度 | 担当 |
|---|---|---|
| tl-advisor 第 1 ラウンド (Step 7) | P1 — 本 PLAN の次アクション | PM → TL |
| cutover_orchestrator の default probe が未 wired の場合、Recovery done 動作確認で別 PLAN 起票が必要 | P2 — preflight 結果次第 | PM 判断 |
| stop-hook の自動登録設計 (hooks 変更承認フローの標準化) | P3 — 別 PLAN 候補 | PM 判断 |
| postmortem-template.md の新設 (Sprint .5 の一部) | P2 — Sprint .5 内で対応 | SE |
| recovery session の stale 検出 CLI (7 日超過) | P3 — Sprint .2 内に組み込み or 別 PLAN | SE |
| `cli/helix recover help` への recovery への誘導メッセージ追記 (命名衝突 mitigation) | P2 — Sprint .3 内で対応 | SE |
| C7: integration-map.md §コマンドの穴 に「helix-recovery (workflow 管理層、L7-cli-helix-recovery-implplan で解消)」を追記 (本 PLAN 完了後) | P2 — 本 PLAN Sprint .5 完遂後に実施 | PM |
| C8: incident-workflow.md 連携の別 PLAN 起票候補 (helix-incident CLI、Incident mode の troubleshoot 操作層、本 PLAN scope 外) | P3 — 別 PLAN | PM 判断 |
