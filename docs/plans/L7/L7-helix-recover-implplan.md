---
plan_id: L7-helix-recover-implplan
title: "L7-helix-recover-implplan: helix-recover CLI 実装 — Recovery mode (AI 暴走・独断専行ガード+収束) 起動コマンド (v3 接続契約確定版)"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/recovery-workflow.md
pairs_test_design:
  - HELIX-workflows/helix-process/deviation-plan-map.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・スコープ確認・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計判断 adversarial check (CLI 設計・状態 dump 方式・rollback 責務限定・recovery-log 既存契約整合)"
  - role: se
    slot_label: "SE — cli/helix-recover + cli/lib/recovery_engine.py 実装 + test 拡張"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・4 artifact 双方向 trace review"
generates:
  - artifact_path: cli/helix-recover
    artifact_type: cli_extension
  - artifact_path: cli/lib/recovery_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_recovery_engine.py
    artifact_type: test
  - artifact_path: cli/tests/helix-recover.bats
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/recovery-workflow.md
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/deviation-plan-map.md
  - cli/helix
  - cli/lib/helix_db.py
  - cli/lib/recovery_plan_check.py
  - cli/templates/plan/recovery/template.md
  - docs/plans/L7/L7-vmodel-semantics-injection-setplan.md
  - docs/plans/L7/L7-helix-route-implplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/recovery-workflow.md](../../../HELIX-workflows/helix-process/recovery-workflow.md)
> **本 PLAN の対象**: `cli/helix-recover` コマンドの新規実装。AI エージェント（Claude Code / Codex）が独断専行・暴走した際に、**ガード（事前警告）と収束（事後リカバリー）** の 2 段構えで対応するための CLI エントリーポイントを実体化する。
> **位置づけ**: integration-map.md §結論と優先順位 **#2 コマンド 2 件のうち 1 件**。recovery-workflow.md で設計完了済みの Recovery mode を CLI として実体化する。**recovery-log は既存 cli/lib/recovery_plan_check.py の 7 必須セクション契約に完全準拠** し、新規 7 セクションを増やさない (PLAN-098 で確立済の正本)。

### parent_design (draft status) を採用する理由

`recovery-workflow.md` の frontmatter status は `draft` のまま。これは HELIX-workflows が 2026-05-24 commit 群で正本化直後であり、各 doc の status frontmatter 更新が後続作業として残っているため。本 PLAN は HELIX-workflows 正本群を **design-frozen 扱い** とし、L7 implementation を許可する。**SE 実装時は親設計 (recovery-workflow.md) を変更しない**。draft → accepted 更新は別 PLAN で batch 処理する。

### tl-advisor 第 1 ラウンド指摘の反映 (本 v2 で全 P1×6 解消)

| # | tl-advisor P1 指摘 | 本 v2 での反映 |
|---|---|---|
| P1-1 | rollback 責務が危険 (実 git reset と誤解の余地) | §2.A: `rollback` を **dry-run / 手順提示のみ** に明示限定、実 git reset / DB rollback は別 PLAN |
| P1-2 | C1 入力源 brittle (task_runs schema では取れない) | §2.A: `git diff --numstat HEAD~N..HEAD` を入力源として凍結 (helix.db 依存なし、最も普遍的) |
| P1-3 | C4 budget consumption 単一値未定義 | §2.A: `helix budget status --json` の `claude.weekly_used_pct` / `codex.weekly_used_pct` two-key 判定で凍結 |
| P1-4 | recovery-log 既存 7 必須セクションとずれ | §2.B: `cli/lib/recovery_plan_check.py REQUIRED_TEMPLATE_SECTIONS` (事故記録/timeline/訂正履歴/中間結論/context 再構築/再開ポイント/再発防止) に完全準拠 |
| P1-5 | テスト 7+4 不足 | §2.D: 境界値・入力源欠落・C4 3 指標別・rollback 不変・recovery_plan_check 互換性を追加 |
| P1-6 | helix-route との境界曖昧 | §2.E: 「route=全モード入口判断、recover=Recovery 確定後の実行・状態保存・再開支援」を明文化 |

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 参考調査 (recovery-workflow.md / integration-map.md / recovery_plan_check.py / 既存 template / cli/helix router 登録方式 確認) | PM | ✅ done |
| 2 | CLI インターフェース設計 (subcommand 構成 / 入口判定 4 条件 / 入力源凍結 / rollback dry-run 限定) | PM | ✅ done (§2.A) |
| 3 | recovery_engine.py 設計 (状態 dump / recovery-log 7 セクション準拠生成 / RecoveryCondition 拡張) | PM | ✅ done (§2.B) |
| 4 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | ✅ done (needs_revision、本 v2 で P1×6 解消) |
| 5 | tl-advisor adversarial check 第 2 ラウンド | PM → TL | □ pending |
| 6 | TL 第 2 ラウンド指摘反映 (もしあれば) | PM | □ pending |
| 7 | SE 委譲: cli/helix-recover + cli/lib/recovery_engine.py 実装 | PM → SE | □ pending |
| 8 | bash -n / shellcheck / python3 -m py_compile 確認 | SE | □ pending |
| 9 | pytest test_recovery_engine.py + bats helix-recover.bats 全 PASS | SE | □ pending |
| 10 | cli/helix router 登録 + `helix help` + `helix commands check` 確認 | SE | □ pending |
| 11 | pmo-sonnet で 4 artifact 双方向 trace 確認 | PM → PMO | □ pending |
| 12 | commit + push | PM | □ pending |

## §2 実装計画

### §2.A cli/helix-recover CLI 設計

#### サブコマンド構成 (rollback dry-run 限定版)

```
helix recover [subcommand] [options]

subcommand:
  check        現在の実行状態を診断し、Recovery 必要度を判定して表示
  dump         helix.db + phase.yaml から状態 dump を取り recovery-log.md (7 必須セクション準拠) を生成
  plan         recovery kind PLAN の draft を対話的に起票 (cli/templates/plan/recovery/template.md ベース)
  rollback     再開ポイント候補を **表示のみ (dry-run)**、実 git reset / DB rollback は手動ガード (本 PLAN scope 外、別 PLAN で実装)
  status       最新の recovery-log.md と helix.db 上の recovery PLAN を一覧
```

**重要**: `rollback` サブコマンドは v1 で `--dry-run` を **強制実装**。`--apply` フラグは本 PLAN では実装せず、`exit 2 with error "use 'helix recover rollback --dry-run' first, then run git/db commands manually"` を返す。実変更は別 PLAN (`L7-helix-recover-rollback-applyplan` 候補) で `cutover_orchestrator` 連携付きで実装する。

#### 入口判定 4 条件 (入力源凍結版)

`helix recover check` は以下の 4 条件を **凍結済入力源** から診断し、検出した条件を表示する:

| 条件 ID | 状況 | 入力源 (凍結) | 閾値 (凍結) | severity |
|---|---|---|---|---|
| **C1** | AI が想定外の大規模変更をした | `git diff --numstat HEAD~N..HEAD` (N は `--since-commits` 引数、default=1)、または `git diff --numstat HEAD` (uncommitted) | 30 files 超過 OR 1500 lines 超過で WARN、50/3000 超で FAIL | CLEAR / WARN / FAIL |
| **C2** | 独断専行で工程・設計から逸脱した | `cli/lib/agent_mandatory.py audit_phase()` の未発火検出 OR `helix doctor --json` の FAIL/WARN 件数 | 必須 audit 未発火 1 件以上で WARN、3 件以上で FAIL | CLEAR / WARN / FAIL |
| **C3** | 認識のズレが蓄積し収拾がつかない | `.helix/handover/CURRENT.json` の `task.status == 'escalated'` OR recovery kind PLAN status=draft 7 日以上停滞 | escalated 中 OR 停滞 7 日超で WARN | CLEAR / WARN |
| **C4** | 予算・操作が過剰に消費されている | `helix budget status --json` の `claude.weekly_used_pct` / `codex.weekly_used_pct` の two-key | **どちらか** 80% 超で WARN、**両方** 80% 超で FAIL | CLEAR / WARN / FAIL |

**入力源欠落時の挙動**: `git diff` 失敗 / `helix budget status` JSON 取得失敗 / `agent_mandatory.audit_phase()` DB 接続失敗 のいずれも severity=**UNKNOWN** (CLEAR と区別) を返す。

`helix recover check` の出力形式 (--json でも CLI でも同等構造):

```
[HELIX Recovery Check] (2026-05-24T14:30:00+09:00)
C1 大規模変更:  WARN  (42 files / 1837 lines changed in HEAD~1..HEAD)  [git_diff_numstat]
C2 工程逸脱:    CLEAR  (mandatory audit all fired)                      [agent_mandatory_audit]
C3 認識ズレ:    WARN  (handover status=escalated since 2026-05-23)     [handover_current_json]
C4 予算過剰:    UNKNOWN (helix budget status --json failed: exit 1)    [budget_status_json]

2 条件 WARN (C1, C3) / 1 条件 UNKNOWN (C4)
推奨: helix recover dump で状態 dump を取得、helix recover plan で PLAN 起票
```

#### 対話 mode (helix recover plan)

引数なし or `--interactive` で対話フローを起動:

1. `helix recover check` 結果を表示
2. 発火した条件 (C1-C4 のうち WARN / FAIL) を確認し、ユーザーへ確認プロンプトを出力
3. 再開ポイント (git commit SHA または PLAN ID) を入力してもらう (`--reopen-point` 引数で非対話)
4. `helix recover dump` を自動実行して recovery-log.md を生成 (7 セクション準拠)
5. recovery kind PLAN の draft テキストを `cli/templates/plan/recovery/template.md` ベースで生成、標準出力 / ファイル保存

引数 mode (`--condition C1 --reopen-point <SHA> --auto-routed-from helix-route`) で非対話実行可能。`--auto-routed-from` は helix-route から呼ばれた場合のトレーサビリティ用。

**v3 追加**: route 連携用に `--signal-id <signal>` を **追加引数** として受け付ける (recover/route 接続契約 R2-P1-7 解消):

```
helix recover plan --signal-id runaway --reopen-point HEAD --auto-routed-from helix-route
```

内部で `signal_to_condition(signal_id)` を呼び、signal vocabulary (drift/runaway/regression_*/debt_degradation/incident/unknown_design) を C1-C4 condition_id にマップする:

| signal_id | condition_id | 理由 |
|---|---|---|
| runaway | C2 (工程逸脱) | AI 暴走は工程逸脱の表面化 |
| regression_dev | C3 (認識ズレ) | 開発中デグレは認識ズレの蓄積結果 |
| regression_prod | (recover 対象外、Incident 委譲) | helix-recover が処理せず、Incident/troubleshoot へ |
| incident (env=prod) | C3 (認識ズレ) + 緊急 | 本番障害発生時は認識ズレ + 暴走複合の可能性 |
| drift / debt_degradation / unknown_design | (recover 対象外、plan draft 委譲) | これらは route → plan draft (Reverse/Refactor) で処理 |

`--signal-id` と `--condition` の両受け: `--signal-id` 優先 (route 経由を示す)、不在時は `--condition` を直接使用 (手動起動)。両不在で対話 mode へ fallback。

route 経由 (`--auto-routed-from helix-route` あり) のとき、recovery-log §再発防止 に以下を自動記録:
- `route_signal: runaway`
- `routed_from: helix-route`
- `signal_to_condition_mapping: runaway → C2`

### §2.B cli/lib/recovery_engine.py 設計

Python モジュール。`cli/helix-recover` のバックエンドロジックを担う。**`cli/lib/recovery_plan_check.py` の既存契約と完全互換**。

#### 主要クラス / 関数 (Literal 型化版)

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

ConditionId = Literal["C1", "C2", "C3", "C4"]
Severity = Literal["CLEAR", "WARN", "FAIL", "UNKNOWN"]
SourceKey = Literal[
    "git_diff_numstat",
    "agent_mandatory_audit",
    "handover_current_json",
    "budget_status_json",
]

@dataclass(frozen=True, slots=True)
class RecoveryCondition:
    """v3: frozen + slots + __post_init__ で Literal 型値の membership check を実行時 fail-close。
    triggered は @property で severity から派生 (フィールドではない、矛盾排除)。"""

    condition_id: ConditionId
    severity: Severity        # CLEAR / WARN / FAIL / UNKNOWN
    source: SourceKey
    metric_value: float | int | str | None
    threshold: float | int | str | None
    evidence: str             # 検出根拠の短文
    detail: str               # 長文 detail (recovery-log §事故記録 に転載)

    def __post_init__(self):
        # v3 R2-P1-9: Literal 実行時 membership check
        if self.condition_id not in ("C1", "C2", "C3", "C4"):
            raise TypeError(f"invalid condition_id: {self.condition_id!r}")
        if self.severity not in ("CLEAR", "WARN", "FAIL", "UNKNOWN"):
            raise TypeError(f"invalid severity: {self.severity!r}")

    @property
    def triggered(self) -> bool:
        """v3: severity から派生 (WARN/FAIL なら True、CLEAR/UNKNOWN なら False)。"""
        return self.severity in ("WARN", "FAIL")

    @property
    def requires_attention(self) -> bool:
        """v3: triggered または UNKNOWN なら True (UNKNOWN は明示確認必要)。"""
        return self.triggered or self.severity == "UNKNOWN"


class RecoveryEngine:
    def __init__(self, helix_db_path: str, phase_yaml_path: str, project_root: str): ...

    def check_conditions(self, since_commits: int = 1) -> list[RecoveryCondition]:
        """C1-C4 の 4 条件を診断して結果リストを返す"""

    def dump_state(
        self,
        output_path: str,
        conditions: list[RecoveryCondition],
        auto_routed_from: str | None = None,    # v3: route 経由トレース
        route_signal: str | None = None,         # v3: route 経由 signal vocabulary
    ) -> str:
        """conditions + helix.db + phase.yaml + git log + handover から
        recovery-log.md を 7 必須セクション準拠で生成して path を返す。
        auto_routed_from / route_signal が指定されたとき §再発防止 に自動記録。

        v3: 出力 heading は cli.lib.recovery_plan_check.REQUIRED_TEMPLATE_SECTIONS
        を import して canonical 配列で出力 (private _SECTION_MARKERS 非依存)。
        書き込み後に check_recovery_template_sections(path) == [] を必ず assert する。"""

    def signal_to_condition(self, signal_id: str) -> "ConditionId | None":
        """v3: route signal vocabulary を recover condition vocabulary にマップ。
        Returns: C1 / C2 / C3 / C4 / None (recover 対象外)

        Mapping (PLAN §2.A 接続契約 R2-P1-7 解消):
        - runaway          → C2 (工程逸脱)
        - regression_dev   → C3 (認識ズレ)
        - incident (prod)  → C3 (認識ズレ + 緊急)
        - regression_prod  → None (Incident/troubleshoot 委譲)
        - drift / debt_degradation / unknown_design → None (plan draft 委譲)
        """

    def suggest_rollback_point(self) -> dict:
        """最終 known-good な commit SHA + PLAN ID + phase を **dry-run のみ** 返す。
        Returns: {git_commit_candidates: [SHA, ...], plan_candidates: [PLAN-ID, ...],
                  phase_snapshot: {...}, note: '実行は手動ガード、--apply 不可'}"""

    def draft_recovery_plan(
        self,
        conditions: list[RecoveryCondition],
        reopen_point: str,
        auto_routed_from: str | None = None,
    ) -> str:
        """recovery kind PLAN の frontmatter + §0-§6 テキストを生成して返す。
        cli/templates/plan/recovery/template.md をベースに、conditions / reopen_point /
        auto_routed_from を埋め込む"""
```

#### dump_state が生成する recovery-log.md の構造 (既存 7 必須セクション準拠)

**重要**: 本 v2 で `cli/lib/recovery_plan_check.REQUIRED_TEMPLATE_SECTIONS` (PLAN-098 確立) に完全準拠する。`check_recovery_template_sections()` が 7 件すべて検出することが DoD。

```markdown
---
recovery_log_id: <auto-generated>
created: 2026-05-24T14:30:00+09:00
generator: cli/helix-recover dump
helix_db_snapshot_at: <iso8601>
---

# Recovery Log — {timestamp}

## 事故記録
- 発火条件: C1 ... / C2 ... / C3 ... / C4 ...
- 各条件の severity / source / metric / threshold / evidence (RecoveryCondition から自動生成)
- 状況詳細: 各 C* の detail 集約

## timeline (タイムライン)
- helix.db の最近 N task の動作順 (codex / opus / claude_subagent)
- 各 task の status / started_at / finished_at / output_summary
- git log --oneline -N (同期間)

## 認識訂正履歴
- C3 検出時に充実 (handover ESCALATION.md / 過去 recovery-log / memory feedback から自動 grep)
- 訂正前 → 訂正後 を short bullet で

## 中間結論
- C1-C4 結果からの暫定結論 1-3 件 (自動推論 + 手動補足欄)
- 例: "C1+C3 同時発火 → 大規模変更が認識ズレを生んでいる可能性高、即時 PLAN 起票推奨"

## context 再構築
- 再開時に最初に読む doc 一覧 (HELIX-workflows / 関連 PLAN / 親設計)
- 再実行する確認コマンド (helix doctor / helix recover check / git status)
- 再開順 (1. doc Read, 2. check 再実行, 3. PLAN draft 反映)

## 再開ポイント
- 次着手 PLAN/KIND/Step を **1 つ** に絞って明記 (PLAN-XXX Sprint .N Step M)
- 再開コマンド: `helix handover resume` or `helix recover plan --reopen-point <SHA>`

## 再発防止
- handover / memory / todo 更新ルールの明文化
- 例: 「次回 C1 検出時は事前に `helix size --files N` で見積もり確認」
- L14 フィードバックへの引き継ぎ note
```

**機械検証**: 生成後に `python3 -c "from cli.lib.recovery_plan_check import check_recovery_template_sections; assert check_recovery_template_sections('<path>') == []"` で 7 必須セクション網羅を確認。

### §2.C cli/helix router 登録

`cli/helix` の case ブランチに `recover` を追加する（既存の `interrupt` / `learn` / `doctor` の登録パターンに倣う）。**Bash は薄く保ち、subcommand 実装は recovery_engine.py の main(argv) に寄せる** (P2 推奨に従い、cli/helix-budget と同じ形)。

```bash
recover)
    shift
    exec "$(dirname "$0")/helix-recover" "$@"
    ;;
```

`cli/helix-recover` 本体は以下の thin wrapper:

```bash
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib/helix-common.sh"
exec python3 "$SCRIPT_DIR/lib/recovery_engine.py" "$@"
```

`cli/helix help` の出力テーブルに `recover` 行を追加 (usage description: `Recovery mode の診断・dump・PLAN 起票 (rollback は dry-run のみ)`)。

`docs/commands/index.md` への記載も同時に行う (`helix commands check` 整合性のため)。

### §2.D cli/lib/tests/test_recovery_engine.py テスト設計 (拡張版)

以下 **15 unit test** を実装 (旧版 7 + P1-5 指摘で追加 8):

**基本 (旧版 7)**:
- `test_check_conditions_all_clear`: C1-C4 いずれも閾値未満で triggered=False、severity=CLEAR
- `test_check_condition_c1_large_change`: git diff 30 files 超過で C1 WARN
- `test_check_condition_c2_mandatory_audit_fail`: agent_mandatory audit 未発火 1 件以上で C2 WARN
- `test_check_condition_c3_escalated_handover`: handover status=escalated で C3 WARN
- `test_check_condition_c4_budget_over`: budget consumption 80% 超で C4 WARN
- `test_dump_state_generates_recovery_log`: dump_state() が recovery-log.md を生成
- `test_draft_recovery_plan_structure`: draft_recovery_plan() が frontmatter + kind=recovery を含む

**追加 (P1-5 で拡張、8 件)**:
- `test_check_condition_c1_boundary_30_files`: 境界 30 files ちょうどで triggered=False (< 30 が CLEAR)
- `test_check_condition_c1_boundary_31_files`: 31 files で triggered=True (WARN)
- `test_check_condition_c1_input_source_missing`: git diff コマンド失敗で severity=UNKNOWN
- `test_check_condition_c4_three_metrics`: claude.weekly / codex.weekly / codex.5h_used_pct の 3 指標別判定
- `test_check_condition_c4_both_keys_over`: claude+codex 両方 80% 超で FAIL
- `test_rollback_does_not_mutate`: rollback サブコマンドが実 git reset / helix.db 書き込みしない (subprocess mock で確認)
- `test_dump_state_passes_recovery_plan_check`: 生成 recovery-log.md が `cli.lib.recovery_plan_check.check_recovery_template_sections()` で 7 必須セクション網羅 (missing 0)
- `test_recovery_condition_dataclass_literal_types`: Literal["C1","C2","C3","C4"] / Literal["CLEAR","WARN","FAIL","UNKNOWN"] 型違反で TypeError

**bats テスト (`cli/tests/helix-recover.bats`)** 6 ケース (P2 指摘で `helix commands check` 整合追加):
- `helix recover help` が usage を出力する
- `helix recover check` が `[HELIX Recovery Check]` ヘッダーと C1-C4 行を出力する
- `helix recover status` が recovery-log 一覧を出力する (空の場合 "No recovery logs found")
- `helix recover dump --output /tmp/test-recovery-log.md` が 7 必須セクションを含む md を生成する
- `helix recover rollback` が `[dry-run]` ラベルを出力し、`--apply` フラグで exit 2 を返す
- `helix commands check` が pass する (`route` / `recover` の docs/commands/index.md drift なし)

### §2.E helix-route との責務分担明示 (P1-6 指摘で追加)

| CLI | 責務 | 入口/出口 | 担当範囲 |
|---|---|---|---|
| `helix-route` (別 PLAN) | **全モード入口判断** | 入口 | 検出シグナル (drift/degradation/runaway/incident) を 4 モード (Recovery / Incident / Reverse / Refactor) に振り分け、PLAN 起票 suggest |
| `helix-recover` (本 PLAN) | **Recovery 確定後の実行** | 出口 | route が Recovery を suggest した後、または手動で Recovery と判断した後の: 状態 dump / recovery-log 生成 / recovery PLAN draft / 再開ポイント表示 (dry-run only) |

**接続契約**:
- `helix-route` の suggest_command 出力に `--auto-routed-from helix-route` を含める (例: `helix recover plan --condition C1 --reopen-point HEAD --auto-routed-from helix-route`)
- `helix-recover plan --auto-routed-from helix-route` を受けたとき、recovery-log §再発防止 に "route 経由で自動起動" を記録する
- 双方向独立: route は recover を起動しない (suggest のみ)、recover は route を呼ばない (独立実行可能)

## §3 成果物

- **製本対象 1**: `cli/helix-recover` (新規 Bash 薄 wrapper、推定 10-20 行)
  - cli/helix router 登録済
- **製本対象 2**: `cli/lib/recovery_engine.py` (新規 Python モジュール、推定 250-350 行)
  - RecoveryEngine クラス + RecoveryCondition dataclass (Literal 型)
  - 4 条件診断 / 状態 dump (7 セクション準拠) / recovery-log 生成 / PLAN draft 生成 / rollback dry-run
- **製本対象 3**: `cli/lib/tests/test_recovery_engine.py` (新規 pytest、推定 200-280 行)
  - 15 unit test (基本 7 + 追加 8)
- **製本対象 4**: `cli/tests/helix-recover.bats` (新規 bats、推定 60-80 行)
  - 6 bats ケース
- **副次成果物**:
  - `docs/commands/index.md` に `recover` 行追加 (helix commands check 整合)
  - `cli/helix help` の Commands テーブルに `recover` 行追加
- **製本対象外** (別 PLAN 候補):
  - `helix recover rollback --apply` 実 git reset / DB rollback (cutover_orchestrator 連携)
  - recovery-log.md 単独テンプレート ファイル (本 PLAN は generator のみ、template は cli/templates/plan/recovery/template.md を流用)
  - `helix recover rotate-logs` / `helix recover gc` などの保守コマンド

## §4 受入条件 / DoD

### 機械検証 (必須)

- [ ] `bash -n cli/helix-recover` エラーなし
- [ ] `shellcheck cli/helix-recover` 警告 0 件 (SC2006 等の既存パターン除く)
- [ ] `python3 -m py_compile cli/lib/recovery_engine.py` 成功
- [ ] `python3 -m pytest cli/lib/tests/test_recovery_engine.py -v` **15 test 全 PASS**
- [ ] `bats cli/tests/helix-recover.bats` **6 ケース全 PASS**
- [ ] `helix help` の出力に `recover` が含まれる
- [ ] `helix recover help` が usage を出力する
- [ ] `helix recover check` が `[HELIX Recovery Check]` ヘッダーを出力し C1-C4 結果を返す
- [ ] `helix recover dump --output /tmp/test-recovery-log.md` が **7 必須セクション** を含む md を生成し、`python3 -c "from cli.lib.recovery_plan_check import check_recovery_template_sections; assert check_recovery_template_sections('/tmp/test-recovery-log.md') == []"` で missing 0
- [ ] `helix recover rollback` が `[dry-run]` ラベルを出力する (実行はしない)
- [ ] `helix recover rollback --apply` が exit 2 で error message を返す (本 PLAN では実装しない明示)
- [ ] `python3 cli/lib/plan_validator.py docs/plans/L7/L7-helix-recover-implplan.md` warnings 0 件
- [ ] `helix commands check` PASS (route / recover の docs/commands/index.md drift なし)
- [ ] 既存 pytest 全回帰 (1850+ test) 全 PASS (helix-recover の追加で既存が破壊されないこと)

### review 検証

- [ ] tl-advisor adversarial check 第 2 ラウンド passed
- [ ] pmo-sonnet 4 artifact 双方向 trace 確認
  - ① 正本設計 (recovery-workflow.md) ↔ ③ テスト設計 (test_recovery_engine.py docstring)
  - ② 実装コード (helix-recover + recovery_engine.py) ↔ ④ bats テストコード
  - 双方向 reference が 4 artifact 全件に明示されていること
- [ ] recovery-workflow.md §基本フロー 6 ステップが CLI サブコマンド (check → dump → plan → rollback → status) に対応していること (トレーサビリティ確認)
- [ ] `cli/lib/recovery_plan_check.py REQUIRED_TEMPLATE_SECTIONS` (PLAN-098 確立済) と recovery-log generator 出力が完全一致

## §5 関連 PLAN / ADR / docs

- **正本設計**: HELIX-workflows/helix-process/recovery-workflow.md (Recovery ワークフロー設計、design-frozen 扱い)
- **既存契約**: cli/lib/recovery_plan_check.py (PLAN-098 で確立、7 必須セクション正本)
- **既存 template**: cli/templates/plan/recovery/template.md (PLAN-098 で確立)
- **企画書 roadmap**: HELIX-workflows/helix-process/integration-map.md §結論と優先順位 #2 (コマンド 2 件のうち 1 件)
- **逸脱マップ**: HELIX-workflows/helix-process/deviation-plan-map.md (kind=recovery の起票トリガーと対応表)
- **前提 PLAN**: docs/plans/L7/L7-vmodel-semantics-injection-setplan.md (integration-map.md #1 最優先)
- **対 PLAN**: docs/plans/L7/L7-helix-route-implplan.md (route=入口、recover=出口の責務分担)
- **既存 CLI 参考**: cli/helix-interrupt / cli/helix-doctor / cli/helix-budget (thin Bash + Python main(argv) パターン)
- **既存ロジック参考**: cli/lib/helix_db.py (task log / agent_slots / phase 取得 API) / cli/lib/agent_mandatory.py (C2 検出) / cli/helix-budget (C4 検出)
- **HELIX_CORE.md**: helix/HELIX_CORE.md §Sprint Plan 標準構造

## §6 後続 PLAN 候補 (本 PLAN 完遂後)

integration-map.md §結論と優先順位 #2 の残り 1 件および以降:

- **#2 残件**: `L7-helix-route-implplan` — `helix-route` コマンド実装 (検出 → モードルーティング起動、本 PLAN と並行)
- **#3**: workflow スキル化 (detection-routing / learning-engine / cross-detection / layer-context-injection の 4 件を skills/workflow/ に追加、retrofit は完遂済)
- **#4 テンプレート**: cli/templates/generates/ 新設 (retrofit-matrix / research-memo / ADR / recovery-log)
- **別 PLAN 候補 (rollback apply 編)**: `L7-helix-recover-rollback-applyplan` — `helix recover rollback --apply` 実 git reset / helix.db rollback (本 PLAN scope 外、cutover_orchestrator 連携付き、destructive operation のため人間承認ガード必須)
- **別 PLAN 候補 (保守編)**: `L7-helix-recover-maintenanceplan` — recovery-log rotation / gc / archive
- **別 PLAN 候補 (status 更新)**: HELIX-workflows/helix-process/*.md の status: draft → accepted 一括更新 (本 PLAN 含む正本化後処理 batch)
