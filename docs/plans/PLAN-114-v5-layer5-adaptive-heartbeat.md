---
plan_id: PLAN-114
title: "ScheduleWakeup adaptive heartbeat 実装 (V5 Layer 5、15/30/5 min)"
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - SE (Codex gpt-5.4)
agent_slots:
  - role: pm-advisor
    slot_label: "PM — adaptive interval 閾値承認・plan guard P0 境界確認・時間枠指示ポリシー確定"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメント整合確認・drift チェック・Sprint review"
  - role: tl-advisor
    slot_label: "TL adversarial check — adaptive scheduler 設計 review・budget 判定 logic・heartbeat 無限ループ防止確認"
  - role: se
    slot_label: "SE — helix runtime status CLI 実装・helix runtime heartbeat CLI 実装"
  - role: qa
    slot_label: "QA — fake budget / fake carry / fake bg task fixture test 全ケース検証"
generates:
  - artifact_type: cli_extension
    artifact_path: cli/helix-runtime
  - artifact_type: python_module
    artifact_path: cli/lib/runtime_status.py
  - artifact_type: test
    artifact_path: cli/lib/tests/test_runtime_heartbeat.py
  - artifact_type: design_doc
    artifact_path: docs/plans/PLAN-114-v5-layer5-adaptive-heartbeat.md
  - artifact_type: adr_snapshot
    artifact_path: docs/adr/ADR-041-v5-layer5-adaptive-heartbeat-decision.md
dependencies:
  parent: PLAN-099
  requires:
    - PLAN-099
  blocks: []
related_adr:
  - ADR-032
  - ADR-041
acceptance_criteria:
  - "python3 -m py_compile cli/lib/runtime_status.py PASS"
  - "bash -n cli/helix-runtime PASS"
  - "pytest test 全 7 ケース PASS (T5-001〜T5-007、PLAN-099 §11.2 準拠)"
  - "budget ≤ 30% 時に 30min interval を選択する (T5-002)"
  - "HELIX_PHASE=critical 時に 5min interval を選択する (T5-003)"
  - "bg task active 時に heartbeat を無効化する (T5-004、no-op 確認)"
  - "carry == 0 時に heartbeat を停止する (T5-005)"
  - "heartbeat wake 時は候補提示のみ、自動実行しない (T5-007、P0 guard 確認)"
  - "ADR-041 起票 (L2 大局判断 snapshot)"
  - "helix doctor pass/fail/warn カウント維持 (regression なし)"
---

# PLAN-114: ScheduleWakeup adaptive heartbeat 実装 (V5 Layer 5)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-041** で凍結 (起票予定):

- ScheduleWakeup adaptive heartbeat 採用判断 (HELIX carry 追跡の外部 state polling として扱う設計選択)
- adaptive interval 4 段階 (通常 15min / 低予算 30min / critical 5min / active task 中無効) の設計値確定
- 発火条件 AND 3 要素 (carry > 0 AND bg task なし AND budget healthy) の採用
- `helix runtime status --json` + `helix runtime heartbeat` の 2 CLI 分割設計
- P0 承認 guard: heartbeat wake は候補提示のみ、承認なし task pop 絶対禁止

## 背景

**PLAN-099 (V5 自動走行 framework 5-layer)** の Layer 5 担当 PLAN。

PLAN-099 §9 で設計を確定済み:
- Layer 5 = `ScheduleWakeup adaptive heartbeat で carry check + 自動 task pop (候補提示のみ)`
- 実装スコープは PLAN-099 の P2a (Layer 4+5 PoC 先行) に分類、Layer A/B 確定前に着手可能
- 本 PLAN はその実装 PLAN として独立起票

**課題 (PLAN-099 §1 より)**:
- 14h idle 事故: 09:57 に carry 残存で turn 終了 → 23:49 まで harness が再起動せず 14h アイドル化
  (memory: `feedback_dont_stop_with_carry_remaining.md` 参照)
- carry 放置: 完了報告後に次 wave を投入しない = 時間枠利用効率の低下
- 解決: adaptive heartbeat が carry を定期検出し、候補を systemMessage で提示して PM の next action を促す

**CLAUDE.md §ScheduleWakeup 運用ルールとの整合**:
```
ScheduleWakeup は harness 追跡外の外部状態 polling 専用。
carry heartbeat = session 間隔の管理 (HELIX harness が知らない外部状態) として適用。
条件: carry > 0 AND bg task なし AND budget healthy
```

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は新 framework 採用判断 (adaptive ScheduleWakeup 設計) を含むため、PLAN-087 ガード対象。PLAN-099 §3 で実施済の WebSearch 3 query を parent として継承し、以下の key evidence を引用する。

| Query | 出典 | 抽出した業界 standard |
|---|---|---|
| "Claude Code ScheduleWakeup cron heartbeat session management 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.143 / 2.1.144) | `/loop` (`/proactive`) alias で heartbeat 運用が community で試用されていることを確認。CHANGELOG 2.1.144 で `/resume` background session 対応。ScheduleWakeup は external state polling 専用 (HELIX CLAUDE.md §ScheduleWakeup 運用ルール) |
| "adaptive scheduler budget aware interval selection agent 2026" | claw0 github / agent farm scheduler patterns 2026 | budget-aware adaptive interval が agent farm 系 framework の標準実装パターン。claw0 は 15min default + budget low 時 30min を実装。HELIX は critical/hotfix 5min を追加して 4 段階に拡張 |
| "carry check task queue polling stop condition agent idle prevention 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.143) | background session worktree isolation 対応。bg task active 中は polling を無効にする設計がエコシステム内で推奨される (不要な wake によるコスト増加防止) |

## 業界 standard 参照

- Claude Code CHANGELOG 2.1.143: https://github.com/anthropics/claude-code/releases (background session worktree isolation)
- Claude Code CHANGELOG 2.1.144: https://github.com/anthropics/claude-code/releases (/resume background session 対応)
- claw0 OSS: adaptive heartbeat の 4 段階 interval 設計の先行事例として参照
- HELIX PLAN-099 §9: parent PLAN の Layer 5 設計根拠 (本 PLAN は §9 仕様を実装する)
- HELIX CLAUDE.md §ScheduleWakeup 運用ルール: 発火条件の HELIX 原則正本
- memory: [[feedback_dont_stop_with_carry_remaining]] (14h idle 事故の根本原因と対策)

## 設計方針 (TL v5 round 5 修正条件 遵守)

CLAUDE.md §TL v5 round 5 修正条件 を厳密遵守する。特に補助 **#8 (adaptive heartbeat)** と **P0 guard** が本 PLAN の核心:

> (補助 #8) 「15min heartbeat: adaptive (通常 15min / 低予算 30min / critical/hotfix 5min / active task 中無効)。固定値禁止、ScheduleWakeup は `carry>0 AND bg task なし AND budget healthy` の時だけ」

> (P0) 「承認なし task pop は Plan Consent / WBS / handover Next Action を超える設計 → HELIX discipline 破壊。queue worker は必ず plan guard を通すこと」

### adaptive interval 4 段階定義 (PLAN-099 §9.1 準拠)

| 状況 | interval | 判定条件 |
|---|---|---|
| 通常 | 15 min | budget > 30% AND carry > 0 AND bg task なし AND phase が critical/hotfix 以外 |
| 低予算 | 30 min | budget ≤ 30% AND carry > 0 AND bg task なし |
| critical / hotfix | 5 min | HELIX_PHASE=critical OR hotfix AND carry > 0 AND bg task なし |
| active task 中 | 無効 (no-op) | bg task active (run_in_background 実行中) |
| carry 0 または時間枠満了 | 停止 | carry == 0 OR ユーザー時間枠満了 OR budget 枯渇 |

**優先順位**: active task 中 (無効) > carry 0 (停止) > budget 枯渇 (停止) > critical (5min) > 低予算 (30min) > 通常 (15min)

### 発火条件 AND 3 要素 (CLAUDE.md §ScheduleWakeup 運用ルール準拠)

```
carry > 0
AND bg task なし (run_in_background active がない)
AND budget healthy (Opus 残量 > 20%)
```

AND 条件の外れたケース:
- carry 0 → ScheduleWakeup をセットしない
- bg task active → ScheduleWakeup をセットしない (no-op)
- budget ≤ 20% → ScheduleWakeup をセットしない

### P0 承認 guard (CRITICAL)

heartbeat wake 時の動作:
```
heartbeat wake → helix handover status --json で carry 確認
      ↓
  carry > 0 → systemMessage「継続作業: [Next Action top-1]」を表示
      ↓
  decision: continue (候補提示のみ、自動実行禁止)
      ↓
  PM (Opus) が承認 → helix job / handover Next Action 経由で実行
```

**自律 pop は候補提示まで**。承認フロー前に worker が自律実行することは禁止 (TL v5 P0)。

### 2 CLI 分割設計

`helix runtime` を新規 CLI として作成し、2 subcommand に分割:

```
helix runtime status [--json]    # budget / carry / bg task 状態を取得
helix runtime heartbeat          # adaptive interval を計算し ScheduleWakeup をセット
```

2 CLI 分割の理由:
- status は heartbeat 以外の用途 (statusLine / PreCompact hook) でも再利用可能
- heartbeat は ScheduleWakeup セット処理のみに責務を絞る
- `runtime_status.py` を Python module として切り出し、各 Layer hook から import 可能にする

### runtime_status.py 仕様

```python
# cli/lib/runtime_status.py
# 取得する状態:
#   carry: int  (helix handover status --json の carry フィールド)
#   budget_pct: float  (helix budget status --json の opus_remaining_pct フィールド)
#   bg_task_active: bool  (run_in_background プロセスが存在するか)
#   phase: str  (HELIX_PHASE 環境変数 または .helix/phase.yaml の current_phase)
#
# 返り値: RuntimeStatus dataclass
# 利用先: helix-runtime heartbeat + helix-statusline (Layer 2) + precompact hook (Layer 3)
```

## 実装計画

### Sprint .1: runtime_status.py + helix runtime status 実装 (Codex se 委譲)

**対象ファイル**: `cli/lib/runtime_status.py` (新規), `cli/helix-runtime` (新規)

実装内容:
- `RuntimeStatus` dataclass: carry / budget_pct / bg_task_active / phase / time_window_active
- `get_runtime_status()`: helix handover / helix budget を subprocess で呼び出して状態取得
- `detect_bg_task_active()`: 実行中の run_in_background プロセス確認 (ps aux + grep pattern)
- `helix runtime status [--json]` subcommand: RuntimeStatus を JSON / テキストで表示

mandatory in sprint:
- `python3 -m py_compile cli/lib/runtime_status.py` PASS
- `bash -n cli/helix-runtime` PASS

### Sprint .2: adaptive interval 計算 + ScheduleWakeup セット実装 (Codex se 委譲)

**対象ファイル**: `cli/helix-runtime` (Sprint .1 の拡張)

実装内容:
- `calculate_interval()` 関数: RuntimeStatus から adaptive interval を計算 (4 段階 + 停止条件)
- `set_schedule_wakeup()` 関数: 計算した interval で ScheduleWakeup をセット
  - interval == 0 (no-op / 停止) → ScheduleWakeup をセットしない
  - interval > 0 → `helix runtime heartbeat --in ${interval}m` 形式で次回 heartbeat をスケジュール
- `build_carry_message()` 関数: carry > 0 時の systemMessage を構築
  (「継続作業: [Next Action top-1]」表示、plan guard = 候補提示のみ)
- `helix runtime heartbeat` subcommand: 上記を統合

mandatory in sprint:
- `bash -n cli/helix-runtime` PASS (Sprint .1 からの回帰なし)

### Sprint .3: pytest fixture test 実装 + DoD 確認 (Codex qa 委譲)

**対象ファイル**: `cli/lib/tests/test_runtime_heartbeat.py` (新規)

テストケース (PLAN-099 §11.2 T5-001〜T5-007 完全準拠):

| ケース | 内容 |
|---|---|
| T5-001 | carry > 0 + budget 正常 (> 30%) + HELIX_PHASE=normal → interval=15min、ScheduleWakeup セット |
| T5-002 | carry > 0 + budget ≤ 30% + bg task なし → interval=30min |
| T5-003 | carry > 0 + HELIX_PHASE=critical + budget 正常 → interval=5min |
| T5-004 | carry > 0 + bg task active → interval=0 (no-op、ScheduleWakeup セットなし) |
| T5-005 | carry == 0 → interval=0 (停止、ScheduleWakeup セットなし) |
| T5-006 | 時間枠満了 (HELIX_TIME_WINDOW_ACTIVE=0) → interval=0 (停止) |
| T5-007 | heartbeat wake → systemMessage に候補提示、自動実行コマンドが呼ばれないことを確認 (plan guard P0) |

fake fixture 方針:
- `RuntimeStatus` dataclass を直接 mock で制御 (subprocess 呼び出しを bypass)
- `HELIX_PHASE` 環境変数を直接制御
- `HELIX_TIME_WINDOW_ACTIVE` 環境変数で時間枠満了を模擬
- `HELIX_BUDGET_PCT` 環境変数で budget % を注入 (Priority 1 経由)
- ScheduleWakeup の実際のセットは mock で検証 (実際のスリープは不要)

mandatory in sprint:
- `python3 -m py_compile cli/lib/tests/test_runtime_heartbeat.py` PASS
- `python3 -m pytest cli/lib/tests/test_runtime_heartbeat.py -v` 全 7 ケース PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (Sprint Exit 時、本 PLAN が G4 相当)

## DoD (Definition of Done)

- [ ] `python3 -m py_compile cli/lib/runtime_status.py` PASS
- [ ] `bash -n cli/helix-runtime` PASS
- [ ] pytest test 全 7 ケース PASS (T5-001〜T5-007)
- [ ] budget ≤ 30% 時に 30min interval を選択 (T5-002 PASS)
- [ ] HELIX_PHASE=critical 時に 5min interval を選択 (T5-003 PASS)
- [ ] bg task active 時に heartbeat を無効化 (T5-004 PASS、no-op 確認)
- [ ] carry == 0 時に heartbeat を停止 (T5-005 PASS)
- [ ] 時間枠満了時に heartbeat を停止 (T5-006 PASS)
- [ ] heartbeat wake 時は候補提示のみ、自動実行しない (T5-007 PASS、P0 guard)
- [ ] ADR-041 起票 (本 PLAN tree の L2 snapshot)
- [ ] helix doctor pass/fail/warn カウント regression なし

## V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §設計方針 / §実装計画 |
| ③ テスト設計 | 本 PLAN §実装計画 Sprint .3 ケース一覧 (T5-001〜T5-007) |
| ② 実装コード | cli/lib/runtime_status.py + cli/helix-runtime (Sprint .1-.2 で実装) |
| ④ テストコード | cli/lib/tests/test_runtime_heartbeat.py (Sprint .3 で実装) |

双方向 trace:
- 本 PLAN → テスト: Sprint .3 ケース一覧に T5 番号明記
- テストコード → 設計: pytest test に `# PLAN-114 T5-001` コメントで対応付け (Sprint .3 実装時)
- テスト設計 → テストコード: test 関数名で T5-NNN 対応 (Sprint .3 実装時)

## carry / 学び (起票時記録)

- **PLAN-099 §9.2 発火条件の AND 解釈**: `carry > 0 AND bg task なし AND budget healthy` の AND 論理。いずれか 1 つでも false なら heartbeat をセットしない。条件の優先順位は active task 中が最優先
- **ScheduleWakeup の HELIX 位置付け**: CLAUDE.md 正本では「harness 追跡外の外部状態 polling 専用」。carry heartbeat は「HELIX harness が session 間隔を知らない」ことを外部状態と見なしての適用。この解釈は ADR-041 で明文化する
- **budget_pct の取得精度**: `helix budget status --json` の opus_remaining_pct フィールドを使用。Codex と Claude 両側の残量を確認し、どちらかが閾値以下なら低予算扱いとする
- **bg_task_active の検出精度**: ps aux + grep は false positive リスクがある。Sprint .1 で `helix job status --active --json` が使える場合はこちらを優先する。確認ロジックを Sprint .1 で詳細設計する
- **time_window_active の管理**: ユーザーが「24 時まで」「N 時間連続」と指定した場合、PM (Opus) が `HELIX_TIME_WINDOW_ACTIVE=1` と `HELIX_TIME_WINDOW_END` をセットする運用。自動検出は現状スコープ外
- **Layer 2 (statusLine) との connection**: 赤 (≤ 20% context) 到達時は heartbeat interval を 5min に強制する設計を検討したが、Layer 間の疎結合を維持するため、現時点では別系統で運用し PLAN-114 後続 iteration で接続する
- **固定値禁止の実施**: 全 interval / threshold は env variable で外部化 (`HELIX_HEARTBEAT_INTERVAL_NORMAL_MIN=15` 等)。Sprint .1 で env 一覧を確定する

## 関連 reference

- PLAN-099 §9 (Layer 5 設計、本 PLAN の実装根拠)
- PLAN-099 §11.2 (テストケース T5-001〜T5-007)
- PLAN-112 (Layer 2 statusLine、≤ 20% 時の将来連携候補)
- PLAN-111 (Layer 3 PreCompact hook、runtime_status.py を共有する予定)
- ADR-032 (PLAN-099 の L2 snapshot)
- ADR-041 (本 PLAN の L2 snapshot、起票予定)
- [[feedback_dont_stop_with_carry_remaining]] (14h idle 事故の根本原因、本 PLAN の存在理由)
- [[feedback_task_notification_trust]] (task-notification と ScheduleWakeup の使い分け)
- CLAUDE.md §ScheduleWakeup 運用ルール (発火条件の HELIX 原則正本)
- CLAUDE.md §TL v5 round 5 修正条件 (設計方針の根拠、補助 #8 / P0)
