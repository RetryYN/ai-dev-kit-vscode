---
plan_id: PLAN-139
title: "PLAN-139: runtime carry monitoring — carry > 0 かつ bg task なし時の ScheduleWakeup 判定 framework"
status: draft
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (pmo-sonnet)
agent_slots:
  - role: pm-advisor
    slot_label: "PM — carry 判定境界・ScheduleWakeup 使用可否の大局承認"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・Sprint review・docs drift チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — helix runtime CLI 設計 review・carry 集計ロジック"
  - role: se
    slot_label: "SE — cli/helix-runtime 実装・carry-status JSON 出力・can-end exit 判定"
  - role: qa
    slot_label: "QA — bats / pytest fixture test 全ケース検証"
generates:
  - artifact_type: cli_extension
    artifact_path: cli/helix-runtime
  - artifact_type: python_module
    artifact_path: cli/lib/carry_monitor.py
  - artifact_type: test
    artifact_path: cli/lib/tests/test_carry_monitor.py
  - artifact_type: test
    artifact_path: cli/tests/test_helix_runtime.bats
  - artifact_type: design_doc
    artifact_path: docs/plans/PLAN-139-runtime-carry-monitoring.md
  - artifact_type: adr_snapshot
    artifact_path: docs/adr/ADR-041-runtime-carry-monitoring-decision.md
dependencies:
  parent: PLAN-099
  requires:
    - PLAN-099
    - PLAN-091
  blocks: []
related_adr:
  - ADR-032
  - ADR-041
---

# PLAN-139: runtime carry monitoring — carry > 0 かつ bg task なし時の ScheduleWakeup 判定 framework

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-041** で凍結 (起票予定):

- `helix runtime carry-status --json` を新設し、TodoWrite / handover / memory carry を単一 JSON に集計する設計選択
- `helix runtime can-end` の exit 0 / exit 1 による機械判定採用
- ScheduleWakeup の「外部状態 polling 専用」制限の範囲内で carry heartbeat を適法化する解釈
- SessionStart hook での carry 残り検出 + 案内追加の採用判断

---

## 1. 目的

[[feedback_dont_stop_with_carry_remaining]] で「carry 残り時に turn 終了禁止」が確立したが、運用は手動確認ベースのままである。

本 PLAN は carry 残件数の機械判定 CLI と、ScheduleWakeup の適切な使い分けを **framework として自動化** する:

1. `helix runtime carry-status --json` — TodoWrite / handover / memory carry を集計して JSON 出力
2. `helix runtime can-end` — exit 0 (終了可) / exit 1 (carry 残り) を機械判定
3. SessionStart hook で carry 残り検出 → 案内メッセージに自動追加

---

## 2. 背景

### 2.1 起点課題

CLAUDE.md §ScheduleWakeup 運用ルール (2026-05-19 確立) では以下を定める:

> carry が残っている / ユーザー時間枠 (例「24 時まで連続作業」) が満たされていない場合は turn を終えず、次の wave を投入し続ける

しかし現状:
- carry 残件数を取得する CLI がない (handover status + TodoWrite 手動目視が必要)
- `can-end` の判定は PM 頼みで機械化されていない
- SessionStart 時に carry 残りを通知する hook がない

### 2.2 PLAN-099 との関係

PLAN-099 (V5 自動走行 framework 5-layer) の **Layer 5 改良** に位置付ける。PLAN-099 §9 では adaptive heartbeat CLI (`helix-heartbeat-scheduler`) の設計を確定しているが、その前提となる「carry > 0 判定」ロジックを本 PLAN で実装する。

Layer 5 heartbeat は `helix runtime carry-status --json` の出力を入力として参照する依存関係となる (ただし本 PLAN 完遂後に PLAN-099 P2a で接続)。

### 2.3 ScheduleWakeup 適法化根拠

CLAUDE.md §ScheduleWakeup 運用ルールでは「harness 追跡外の外部状態 polling 専用」と定義される。carry heartbeat は session 間の HELIX harness 未追跡状態を poll するものであり、この定義に準ずる。ただし **carry > 0 AND bg task なし AND budget healthy** の条件を必ず満たしてから発火させる。

---

## 3. 業界 standard 参照

本 PLAN は PLAN-087 ガード対象 (新 CLI / hook 設計を含む)。PLAN-099 §3 を parent として継承しつつ、carry 集計設計に特化した根拠を追加する。

| Query | 出典 | 抽出した業界 standard |
|---|---|---|
| "Claude Code SessionStart hook carry detection systemMessage 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.141) | SessionStart hook で `session_type` (new / cleared / compacted) が提供される。hook は systemMessage で文脈を注入可能。carry 残り通知は systemMessage に追加するパターンが適切 |
| "agent task carry queue drain pattern autonomous workflow 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.143) + HELIX CLAUDE.md | HELIX CLAUDE.md §ScheduleWakeup 運用ルール: carry > 0 AND bg task なし AND budget healthy の 3 条件 AND でのみ ScheduleWakeup を発火。固定 interval 禁止・adaptive 必須 (PLAN-099 §9.1) |
| "JSON exit code CLI gate pattern shell 2026" | POSIX exit code convention / HELIX CLAUDE.md §Sprint Plan 標準構造 | exit 0 = 正常終了 (can-end)、exit 1 = 条件未充足 (carry 残り)、exit 2 = fail-close (block)。shell pipeline と CI gate の標準パターン。helix doctor / gate-policy と同一の exit 規約 |

---

## 4. 設計方針

### 4.1 carry 集計対象 (3 ソース)

| ソース | 取得方法 | carry と見なす条件 |
|---|---|---|
| TodoWrite | HELIX_TODO_PATH 環境変数 / デフォルト `~/.helix/todo.json` | status が `pending` または `in_progress` のエントリ |
| handover Next Action | `helix handover status --json` の `next_actions` 配列 | status が `in_progress` の CURRENT.json が存在 + next_actions 非空 |
| memory carry | `~/.claude/agent-memory/pmo-sonnet/` の carry 関連 entry | 本 PLAN では carry 件数 = 0 として扱う (memory carry は人間判断が必要なため機械集計しない) |

> memory carry を自動集計しない理由: memory は長期知識であり「残タスク」の概念と異なる。carry 判定は TodoWrite + handover の 2 ソースに限定する。

### 4.2 CLI 仕様

#### `helix runtime carry-status --json`

出力 JSON:
```json
{
  "carry_count": 3,
  "sources": {
    "todowrite": { "pending": 2, "in_progress": 1 },
    "handover": { "active": true, "next_action_count": 1 }
  },
  "can_end": false,
  "checked_at": "2026-05-23T10:00:00Z"
}
```

#### `helix runtime can-end`

```
exit 0 : carry_count == 0 (turn 終了可)
exit 1 : carry_count > 0  (carry 残り、turn 継続必須)
```

#### `helix runtime status`

`carry-status` + budget + bg task 状況を人間可読形式で表示するサブコマンド。

### 4.3 SessionStart hook 統合

既存 `sessionstart-harness-summary.sh` へ carry 残り検出を追加 (Edit)。

- `helix runtime carry-status --json` を実行
- `carry_count > 0` なら systemMessage の末尾に以下を追記:
  ```
  [carry 残り {N} 件] 前 session の未完了 action があります。
  helix runtime carry-status --json で確認してください。
  ```
- `carry_count == 0` なら追記なし (既存動作を維持)

---

## 5. 実装計画

### Sprint .1: carry_monitor.py + helix runtime CLI skeleton (Codex se 委譲)

**対象ファイル**:
- `cli/lib/carry_monitor.py` (新規)
- `cli/helix-runtime` (新規 bash)

`carry_monitor.py` 実装内容:
- `collect_todowrite(todo_path: Path) -> dict` — todo.json を読んで pending/in_progress 件数を返す
- `collect_handover(handover_path: Path) -> dict` — CURRENT.json を読んで active + next_action_count を返す
- `aggregate_carry() -> dict` — 2 ソースを集計して carry_count + can_end を含む JSON dict を返す

`cli/helix-runtime` bash 実装内容:
- `carry-status [--json]` サブコマンド: `carry_monitor.py` を呼び出して出力
- `can-end` サブコマンド: `carry_count` を確認して exit 0 / 1
- `status` サブコマンド: carry + budget 状況の人間可読表示

mandatory in sprint:
- `bash -n cli/helix-runtime` PASS
- `python3 -m py_compile cli/lib/carry_monitor.py` PASS

### Sprint .2: SessionStart hook 統合 + settings.json 登録確認 (Codex se 委譲)

**対象ファイル**:
- `.claude/hooks/sessionstart-harness-summary.sh` (Edit)

実装内容:
- `helix runtime carry-status --json` の呼び出し追加
- `carry_count > 0` 時の systemMessage 末尾追記ロジック
- エラー時は fail-open (hook 自体は exit 0 で通過させる)

mandatory in sprint:
- `bash -n .claude/hooks/sessionstart-harness-summary.sh` PASS
- 既存 hook の smoke test (SessionStart 正常経路が維持されること)

### Sprint .3: pytest + bats test 実装 (Codex qa 委譲)

**対象ファイル**:
- `cli/lib/tests/test_carry_monitor.py` (新規)
- `cli/tests/test_helix_runtime.bats` (新規)

テストケース:

| ケース | 内容 |
|---|---|
| T-001 | todowrite 3 件 pending → carry_count=3, can_end=false |
| T-002 | todowrite 0 件 + handover なし → carry_count=0, can_end=true |
| T-003 | todowrite 0 件 + handover active (next_actions 2 件) → carry_count=2, can_end=false |
| T-004 | todo.json 不在 → carry_count=0 (ファイルなしは 0 件扱い) |
| T-005 | `helix runtime can-end` carry_count=0 → exit 0 |
| T-006 | `helix runtime can-end` carry_count=2 → exit 1 |
| T-007 | SessionStart hook: carry 残り時に systemMessage に追記されること |
| T-008 | SessionStart hook: carry 0 時に既存動作と差分なし (fail-open) |

mandatory in sprint:
- `python3 -m pytest cli/lib/tests/test_carry_monitor.py -q` 全ケース PASS
- `bats cli/tests/test_helix_runtime.bats` 全ケース PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (G4 相当)

---

## 6. DoD (Definition of Done)

- [ ] `bash -n cli/helix-runtime` PASS
- [ ] `python3 -m py_compile cli/lib/carry_monitor.py` PASS
- [ ] pytest T-001〜T-004 全 PASS (carry_monitor.py unit)
- [ ] bats T-005〜T-006 全 PASS (can-end exit code)
- [ ] bats T-007〜T-008 全 PASS (SessionStart hook 統合)
- [ ] `helix runtime carry-status --json` が valid JSON を返す
- [ ] `helix runtime can-end` が carry 状態に応じた exit code を返す
- [ ] SessionStart hook: carry 残り時に systemMessage 追記、carry 0 時は既存動作維持
- [ ] ADR-041 起票 (L2 snapshot)
- [ ] helix doctor pass/fail/warn カウント regression なし

---

## 7. V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §4 設計方針 / §5 実装計画 |
| ③ テスト設計 | 本 PLAN §5 Sprint .3 ケース一覧 (T-001〜T-008) |
| ② 実装コード | cli/helix-runtime / cli/lib/carry_monitor.py (Sprint .1-.2) |
| ④ テストコード | cli/lib/tests/test_carry_monitor.py + cli/tests/test_helix_runtime.bats (Sprint .3) |

双方向 trace:
- 本 PLAN → テスト: Sprint .3 ケース一覧に T-NNN 番号明記
- テストコード → 設計: pytest / bats の docstring に「PLAN-139 T-NNN」明記 (Sprint .3 実装時)

---

## 8. 関連 reference

- PLAN-099 §9 (Layer 5 adaptive heartbeat、本 PLAN は前提 carry 判定を実装)
- PLAN-099 §11.2 T5-001〜T5-007 (heartbeat 側のテストケース、本 PLAN の出力を利用)
- CLAUDE.md §ScheduleWakeup 運用ルール (carry > 0 AND bg task なし AND budget healthy の発火条件)
- [[feedback_dont_stop_with_carry_remaining]] (本 PLAN の起点課題)
- ADR-032 (PLAN-099 の L2 snapshot)
- ADR-041 (本 PLAN の L2 snapshot、起票予定)
