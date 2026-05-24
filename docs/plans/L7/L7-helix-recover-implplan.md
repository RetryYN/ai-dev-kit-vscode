---
plan_id: L7-helix-recover-implplan
title: "L7-helix-recover-implplan: helix-recover CLI 実装 — Recovery mode (AI 暴走・独断専行ガード+収束) 起動コマンド"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
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
    slot_label: "TL — 設計判断 adversarial check (CLI 設計・状態 dump 方式・ロールバック判定)"
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
  - docs/plans/L7/L7-vmodel-semantics-injection-setplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/recovery-workflow.md](../../../HELIX-workflows/helix-process/recovery-workflow.md)
> **本 PLAN の対象**: `cli/helix-recover` コマンドの新規実装。AI エージェント（Claude Code / Codex）が独断専行・暴走した際に、**ガード（事前警告）と収束（事後リカバリー）** の 2 段構えで対応するための CLI エントリーポイントを実体化する。
> **位置づけ**: integration-map.md §結論と優先順位 **#2 コマンド 2 件のうち 1 件**。recovery-workflow.md で設計完了済みの Recovery mode を CLI として実体化する。新規設計判断は不要で、設計をコードに落とすことが本 PLAN の本体。

### parent_design (draft status) を採用する理由

`recovery-workflow.md` の frontmatter status は `draft` のまま。これは HELIX-workflows が 2026-05-24 commit 群で正本化直後であり、各 doc の status frontmatter 更新が後続作業として残っているため。本 PLAN は HELIX-workflows 正本群を **design-frozen 扱い** とし、L7 implementation を許可する。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 参考調査 (recovery-workflow.md / integration-map.md / deviation-plan-map.md / cli/helix router 登録方式 確認) | PM | ✅ done (本 PLAN 起草前に Read 完了) |
| 2 | CLI インターフェース設計 (subcommand 構成 / 入口判定 4 条件 / 対話 mode 設計) | PM | ✅ done (§2.A で詳細化) |
| 3 | recovery_engine.py 設計 (状態 dump / recovery-log 生成 / ロールバック判定支援) | PM | ✅ done (§2.B で詳細化) |
| 4 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | □ pending |
| 5 | TL 指摘反映 | PM | □ pending |
| 6 | SE 委譲: cli/helix-recover + cli/lib/recovery_engine.py 実装 | PM → SE | □ pending |
| 7 | bash -n / shellcheck / python3 -m py_compile 確認 | SE | □ pending |
| 8 | pytest test_recovery_engine.py + bats helix-recover.bats 全 PASS | SE | □ pending |
| 9 | cli/helix router 登録 + `helix help` 出力に recover が現れることを確認 | SE | □ pending |
| 10 | pmo-sonnet で 4 artifact 双方向 trace 確認 | PM → PMO | □ pending |
| 11 | commit + push | PM | □ pending |

## §2 実装計画

### §2.A cli/helix-recover CLI 設計

#### サブコマンド構成

```
helix recover [subcommand] [options]

subcommand:
  check        現在の実行状態を診断し、Recovery 必要度を判定して表示
  dump         helix.db + phase.yaml から状態 dump を取り recovery-log.md を生成
  plan         recovery kind PLAN の draft を対話的に起票
  rollback     再開ポイントを指定して git / helix.db の状態を戻す支援
  status       最新の recovery-log.md と helix.db 上の recovery PLAN を一覧
```

#### 入口判定 4 条件 (recovery-workflow.md §入口判定 準拠)

`helix recover check` は以下の 4 条件を helix.db + phase.yaml から診断し、検出した条件を表示する:

| 条件 ID | 状況 | 検出ロジック |
|---|---|---|
| C1 | AI が想定外の大規模変更をした | helix.db の recent task log で変更ファイル数が閾値超過 (default: 30 files / 1500 lines) |
| C2 | 独断専行で工程・設計から逸脱した | agent_mandatory audit が未発火フェーズを検出、または helix doctor に WARN/FAIL が蓄積 |
| C3 | 認識のズレが蓄積し収拾がつかない | recovery kind PLAN が既存で status=draft のままキャリー、またはハンドオーバー escalated 状態が継続 |
| C4 | 予算・操作が過剰に消費されている | helix budget status で consumption が threshold (default: 80%) 超過 |

`helix recover check` の出力形式:

```
[HELIX Recovery Check]
C1 大規模変更: WARN (最新タスク: 42 files 変更)
C2 工程逸脱:  CLEAR
C3 認識ズレ:  WARN (handover status=escalated)
C4 予算過剰:  CLEAR

2 条件該当。`helix recover dump` で状態 dump を取ることを推奨します。
```

#### 対話 mode (helix recover plan)

引数なし or `--interactive` で対話フローを起動:

1. `helix recover check` 結果を表示
2. 発火した条件 (C1-C4) を確認し、ユーザーへ確認プロンプトを出力
3. 再開ポイント (git commit SHA または PLAN ID) を入力してもらう
4. `helix recover dump` を自動実行して recovery-log.md を生成
5. recovery kind PLAN の draft テキストを標準出力 / ファイル保存

引数 mode (`--condition C1 --reopen-point <SHA>`) で非対話実行可能。

### §2.B cli/lib/recovery_engine.py 設計

Python モジュール。`cli/helix-recover` のバックエンドロジックを担う。

#### 主要クラス / 関数

```python
class RecoveryEngine:
    def __init__(self, helix_db_path: str, phase_yaml_path: str): ...

    def check_conditions(self) -> list[RecoveryCondition]:
        """C1-C4 の 4 条件を診断して結果リストを返す"""

    def dump_state(self, output_path: str) -> str:
        """helix.db + phase.yaml から状態を取得し recovery-log.md を生成して path を返す"""

    def suggest_rollback_point(self) -> str:
        """helix.db の task log / phase.yaml から再開候補 commit SHA または PLAN ID を返す"""

    def draft_recovery_plan(
        self,
        conditions: list[RecoveryCondition],
        reopen_point: str,
        corrections: list[str],
    ) -> str:
        """recovery kind PLAN の frontmatter + §0-§6 テキストを生成して返す"""

@dataclass
class RecoveryCondition:
    condition_id: str   # C1 / C2 / C3 / C4
    triggered: bool
    severity: str       # WARN / CLEAR / FAIL
    detail: str
```

#### dump_state が生成する recovery-log.md の構造

```markdown
# Recovery Log — {timestamp}

## 発火条件
- C1: {triggered/clear} — {detail}
- C2: {triggered/clear} — {detail}
- C3: {triggered/clear} — {detail}
- C4: {triggered/clear} — {detail}

## 再開ポイント
- git commit: {SHA}
- PLAN: {plan_id}
- phase.yaml 状態: {phase}/{gate}

## helix.db 状態スナップショット
- 最新 task: {task_id} / {status}
- handover: {current_json_excerpt}
- agent_slots: {slot_summary}

## 認識訂正履歴
（`helix recover plan` が自動生成または手動で記入）

## 再発防止策
（Forward 接続後に L14 フィードバックとして引き渡す）
```

### §2.C cli/helix router 登録

`cli/helix` の case ブランチに `recover` を追加する（既存の `interrupt` / `learn` / `doctor` の登録パターンに倣う）:

```bash
recover)
    shift
    exec "$(dirname "$0")/helix-recover" "$@"
    ;;
```

`cli/helix help` の出力テーブルに `recover` 行を追加 (usage description: `Recovery mode の診断・dump・PLAN 起票`).

### §2.D cli/lib/tests/test_recovery_engine.py テスト設計

以下 **7 test** を実装:

- `test_check_conditions_all_clear`: C1-C4 いずれも閾値未満のとき triggered=False、severity=CLEAR
- `test_check_condition_c1_large_change`: task log に 30 files 超の変更が記録されているとき C1 が WARN
- `test_check_condition_c2_mandatory_audit_fail`: agent_mandatory audit に未発火フェーズがあるとき C2 が WARN
- `test_check_condition_c3_escalated_handover`: handover status=escalated のとき C3 が WARN
- `test_check_condition_c4_budget_over`: budget consumption が 80% 超のとき C4 が WARN
- `test_dump_state_generates_recovery_log`: dump_state() が recovery-log.md を生成し、必須 section が含まれる
- `test_draft_recovery_plan_structure`: draft_recovery_plan() が frontmatter + kind=recovery + §0-§6 section を含む文字列を返す

bats テスト (`cli/tests/helix-recover.bats`) として最低 4 ケースを追加:

- `helix recover help` が usage を出力する
- `helix recover check` が [HELIX Recovery Check] ヘッダーを出力する
- `helix recover status` が recovery-log の一覧を出力する (空の場合は "No recovery logs found")
- `helix help` の出力に `recover` が含まれる

## §3 成果物

- **製本対象 1**: `cli/helix-recover` (新規 Bash スクリプト、推定 80-120 行)
  - subcommand: check / dump / plan / rollback / status
  - cli/helix router 登録済
- **製本対象 2**: `cli/lib/recovery_engine.py` (新規 Python モジュール、推定 150-200 行)
  - RecoveryEngine クラス + RecoveryCondition dataclass
  - 4 条件診断 / 状態 dump / recovery-log 生成 / PLAN draft 生成
- **製本対象 3**: `cli/lib/tests/test_recovery_engine.py` (新規 pytest、推定 100-140 行)
  - 7 unit test + bats 4 ケース (`cli/tests/helix-recover.bats`)
- **副次成果物**: なし
  - recovery-log.md テンプレート本体 (templates/ 配下) は integration-map.md #4 の別 PLAN 候補として分離

## §4 受入条件 / DoD

### 機械検証 (必須)

- [ ] `bash -n cli/helix-recover` エラーなし
- [ ] `shellcheck cli/helix-recover` 警告 0 件 (SC2006 等の既存パターン除く)
- [ ] `python3 -m py_compile cli/lib/recovery_engine.py` 成功
- [ ] `python3 -m pytest cli/lib/tests/test_recovery_engine.py -v` 7 test 全 PASS
- [ ] `bats cli/tests/helix-recover.bats` 4 ケース全 PASS
- [ ] `helix help` の出力に `recover` が含まれる (`helix help | grep recover` で確認)
- [ ] `helix recover help` が usage を出力する
- [ ] `helix recover check` が `[HELIX Recovery Check]` ヘッダーを出力し C1-C4 結果を返す
- [ ] `helix recover dump` が recovery-log.md を生成し、必須 6 section (発火条件/再開ポイント/helix.db スナップショット/認識訂正履歴/再発防止策 の各 heading) を含む
- [ ] `python3 cli/lib/plan_validator.py docs/plans/L7/L7-helix-recover-implplan.md` warnings 0 件
- [ ] 既存 pytest 全回帰 (1850+ test) 全 PASS (helix-recover の追加で既存が破壊されないこと)

### review 検証

- [ ] tl-advisor adversarial check 第 1 ラウンド passed (§2.A CLI 設計 / §2.B 状態 dump 方式 / §2.D テスト戦略)
- [ ] pmo-sonnet 4 artifact 双方向 trace 確認
  - ① 正本設計 (recovery-workflow.md) ↔ ③ テスト設計 (test_recovery_engine.py)
  - ② 実装コード (helix-recover + recovery_engine.py) ↔ ④ bats テストコード
  - 双方向 reference が 4 artifact 全件に明示されていること
- [ ] recovery-workflow.md §基本フロー 6 ステップが CLI サブコマンド (check → dump → plan → rollback → status) に対応していること (トレーサビリティ確認)

## §5 関連 PLAN / ADR / docs

- **正本設計**: HELIX-workflows/helix-process/recovery-workflow.md (Recovery ワークフロー設計、design-frozen 扱い)
- **企画書 roadmap**: HELIX-workflows/helix-process/integration-map.md §結論と優先順位 #2 (コマンド 2 件のうち 1 件)
- **逸脱マップ**: HELIX-workflows/helix-process/deviation-plan-map.md (kind=recovery の起票トリガーと対応表)
- **前提 PLAN**: docs/plans/L7/L7-vmodel-semantics-injection-setplan.md (integration-map.md #1 最優先、本 PLAN の前後関係)
- **既存 CLI 参考**: cli/helix-interrupt / cli/helix-doctor (router 登録・subcommand 構成の参照範例)
- **既存ロジック参考**: cli/lib/helix_db.py (task log / agent_slots / phase 取得の API)
- **budget 参考**: cli/helix-budget (C4 条件判定の budget status 参照方式)
- **HELIX_CORE.md**: helix/HELIX_CORE.md §Sprint Plan 標準構造 (本 PLAN の実施方式)

## §6 後続 PLAN 候補 (本 PLAN 完遂後、dependencies.requires に本 PLAN を入れる)

integration-map.md §結論と優先順位 #2 の残り 1 件および以降:

- **#2 残件**: `L7-helix-route-implplan` — `helix-route` コマンド実装 (検出 → モードルーティング起動、fe-detector-spec.md 準拠)
- **#3**: workflow スキル化 (detection-routing / learning-engine / cross-detection / layer-context-injection の 4 件を skills/workflow/ に追加)
- **#4 テンプレート**: recovery-log.md テンプレート (cli/templates/generates/ 配下、本 PLAN の副次成果物として分離)
- **別 PLAN 候補**: `helix recover rollback` サブコマンドの cutover_orchestrator 連携強化 (本 PLAN では再開ポイント表示のみ、実際の git reset は手動ガード)
- **別 PLAN 候補**: recovery-workflow.md の status: draft → accepted 一括更新 (HELIX-workflows 正本化後処理バッチ)
