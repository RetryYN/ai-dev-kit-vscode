---
plan_id: PLAN-098
title: "PLAN-098: リカバリープラン kind 正規化 (recovery template 7 セクション + session 終了前チェックリスト 4 項目 fail-close + helix doctor check_recovery_plan_freshness)"
layer: cross
kind: design+impl
status: draft
size: M
drive: troubleshoot
created: 2026-05-20
revised: 2026-05-20
owner: PM
phases: L0, L1, L2, L3, L4
gates: G1, G2, G3, G4
agent_slots:
  - role: pm-advisor
    slot_label: "PM 親設計判断・finalize"
  - role: pmo-sonnet
    slot_label: "template 起草・整合確認"
  - role: se
    slot_label: "recovery_plan_check.py + helix doctor check 実装"
  - role: qa
    slot_label: "fail-close 境界テスト + 7 セクション欠落シナリオ"
generates:
  - artifact_path: cli/templates/plan/recovery/template.md
    artifact_type: design_doc
  - artifact_path: cli/lib/recovery_plan_check.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_recovery_plan_check.py
    artifact_type: test
  - artifact_path: cli/lib/helix_doctor.py (拡張 = check_recovery_plan_freshness 追加)
    artifact_type: cli_extension
  - artifact_path: docs/runbook/recovery-plan-usage.md
    artifact_type: runbook
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
    - PLAN-093-plan-drift-detection-curator (helix doctor 拡張統合の前提)
    - PLAN-MM-001-v5-framework-master-plan
  blocks: []
related_adr: [ADR-031]
related_plans:
  - "PLAN-091 (kind: recovery を 11 番目として定義)"
  - PLAN-093 (helix doctor check 統合)
  - PLAN-099 (Layer 4 SessionStart 連動)
related_docs:
  - docs/plans/PLAN-MM-001-v5-framework-master-plan.md
  - docs/plans/PLAN-091-v5-framework-core.md
  - cli/ROLE_MAP.md
related_memories:
  - feedback_recovery_plan_kind_missing (直接 source、本 PLAN の出発点)
  - feedback_dont_stop_with_carry_remaining (session 終了前チェック source、14h idle 事故)
  - project_2026_05_20_v5_framework_evolution_recovery (V5 確立過程の recovery 事例)
acceptance:
  - cli/templates/plan/recovery/template.md が 7 必須セクションを含み、helix plan draft --kind recovery で生成可能
  - cli/lib/recovery_plan_check.py が 7 セクション存在確認 + freshness 検出を実装
  - helix doctor check_recovery_plan_freshness が status=active recovery PLAN の N 日超過を検出 (default 7 日 warn / 14 日 fail)
  - session 終了前チェックリスト 4 項目 fail-close が hook で機械強制可能 (P3 段階)
  - V-model 4 artifact 双方向 trace 確立 (本 PLAN ↔ test design ↔ test code)
---

# PLAN-098: リカバリープラン kind 正規化

> **kind**: design+impl (新 kind 追加 + check 実装)
> **layer**: cross (全層に影響、recovery は session 断絶からの再開を扱う)
> **drive**: troubleshoot (障害復旧 driven)
> **本 PLAN の役割**: V5 framework 18 要素の #17 リカバリープラン kind を正規化、本 session で確立した `feedback_recovery_plan_kind_missing` の直接実装。

## §0. 本 PLAN の位置付け

本 PLAN は V5 framework 18 要素の **#17 リカバリープラン kind (recovery)** を正規化する子 PLAN。本 session (2026-05-20) で発覚した「中間結論消失 / carry 残件不明確 / 14h idle 事故 / 認識訂正履歴の揮発」という session 断絶問題からの直接実装。

PLAN-091 §5.1 kind 11 種で **11 番目に `recovery`** を定義しているが、本 PLAN で template / check / fail-close enforcement を具体化することで「recovery kind の運用」を確立する。

## §1. 目的

1. recovery kind の **template 7 必須セクション** を確立し、session 断絶からの再開を標準化する
2. **session 終了前チェックリスト 4 項目** を fail-close 化し、「気づいたら次 session で何も分からない」状態を防ぐ
3. **helix doctor check_recovery_plan_freshness** で stale recovery PLAN を検出
4. PLAN-099 Layer 4 (SessionStart cleared/compacted + UserPromptSubmit 履歴注入) と連動して、recovery PLAN を session 再開時の context 再構築 source として活用する

## §2. 背景

### 2.1 本 session で発覚した問題 (feedback_recovery_plan_kind_missing source)

- **中間結論消失**: V5 framework V1→V5 確立過程の議論順序が CLAUDE.md にしか永続化されず、recovery PLAN として独立保存されなかった
- **carry 残件不明確**: handover に Tier A/B/D を carry として書いたが、ユーザー指摘「V5 framework が本命、他は破棄」で前提誤りが発覚
- **14h idle 事故** (feedback_dont_stop_with_carry_remaining): 並行タスクなしと誤判断して turn 終了、harness 通知待ちのまま 14h アイドル
- **認識訂正履歴の揮発**: 「吸収」→「前提誤り → 置換」の認識訂正が chat のみで、永続化なし

### 2.2 既存 HELIX 資産との関係

- 既存 `handover` (`.helix/handover/CURRENT.json`): session continuity (状態 snapshot) は扱うが、議論順序 / 認識訂正履歴 / 中間結論は扱わない
- 既存 `memory feedback`: 個別 lesson learned を扱うが、session 断絶リカバリーの構造化はない
- 既存 `helix doctor`: PLAN drift 検出はあるが、recovery PLAN の freshness check はない

recovery kind は handover + memory feedback の上位概念として、**session 断絶からの再開を 1 つの PLAN doc に集約** する。

## §3. 業界 standard 参照 (Web 検索 3 query Sources、PLAN-087 ガードレール準拠)

| 参照 | source | 引用箇所 |
|---|---|---|
| Google SRE Blameless Postmortem | https://sre.google/sre-book/postmortem-culture/ | §5 recovery template 7 セクション (timeline / root cause / impact / action items) |
| Google SRE Postmortem Example | https://sre.google/sre-book/example-postmortem/ | §5 timeline + action items の構造 |
| Atlassian Incident Postmortem | https://www.atlassian.com/incident-management/postmortem/templates | §5 metadata (incident ID / severity / status / impact) |
| dastergon postmortem-templates (GitHub) | https://github.com/dastergon/postmortem-templates | §7 cli/templates/plan/recovery/template.md 参考 |
| incident.io SRE postmortem best practices | https://incident.io/blog/sre-incident-postmortem-best-practices | §5 24-72h window for objectivity + blameless 原則 |
| Indium 7 State Persistence Strategies for AI Agents | https://www.indium.tech/blog/7-state-persistence-strategies-ai-agents-2026/ | §10 段階導入 (checkpointing + state recovery + asynchronous memory) |
| Augment Code Session-End Spec Update | https://www.augmentcode.com/guides/session-end-spec-update-ai-agents | §6 session 終了前 5 分 update が context loss を防ぐ |
| XTrace AI Agent Context Handoff | https://xtrace.ai/blog/ai-agent-context-handoff | §2.1 context loss が pipeline 破綻の主因 |
| GitScrum Definition of Done Checklist Enforcement | https://gitscrum.com/en/solutions/pains/unclear-definition-of-done | §6 session 終了前 4 項目 fail-close (DoD 不在で task 閉じない) |
| BCMS Spec-Driven Development | https://thebcms.com/blog/spec-driven-development | §5 recovery template が「spec」として実装の前提を凍結 |
| 内部 reference: feedback_recovery_plan_kind_missing | MEMORY.md | 本 PLAN の出発点 (本 session 確立) |
| 内部 reference: feedback_dont_stop_with_carry_remaining | MEMORY.md | §6 4 項目の根拠 (14h idle 事故) |

## §4. V5 framework 担当要素

| # | 要素 | 本 PLAN 担当 |
|---|------|----|
| **17** | **リカバリープラン kind (recovery)** | **本 PLAN 全体** |
| 3 | kind 11 種の `recovery` 定義 | PLAN-091 §5.1 で定義、本 PLAN で詳細化 |
| 4 | matrix 外 / kind 不在 fail-close | PLAN-091 §9 で base 確定、本 PLAN は recovery freshness fail-close |
| 9 | PLAN drift 検出 (helix doctor) | PLAN-093 拡張、本 PLAN は check_recovery_plan_freshness 追加 |

## §5. recovery template 7 必須セクション

`cli/templates/plan/recovery/template.md` の必須構造:

### 5.1 事故記録 (Incident Record)

- 発生日時 (timezone 明記)
- 事故 type: `session_disruption` / `discussion_derailment` / `recognition_error` / `idle_overrun` / `context_exhaustion` / `state_loss` / `other`
- severity: critical (本番影響) / high (作業 1 session 以上のロス) / medium (作業数時間のロス) / low (作業の数 turn のロス)
- 検出方法: 自動検出 (hook / monitor) / 人間気づき / 次 session 開始時
- impact: 失った作業時間 / 失った中間結論数 / 失った carry 残件数

### 5.2 議論順序 timeline (Discussion Timeline)

- turn 番号と内容 (start → end)
- 各 turn の決定事項 / ユーザー指示 / モデル判断
- 議論の分岐点 (どこで方向転換したか)
- 認識訂正があった turn を強調表示

### 5.3 認識訂正履歴 (Recognition Correction History)

- V1 → V2 → ... → Vn の遷移
- 各訂正の理由 (ユーザー指摘 / モデル自己発見 / 外部 review)
- 訂正前提と訂正後の差分

### 5.4 中間結論 list (Intermediate Conclusions, 3 列管理)

| Conclusion | 状態 | 確定根拠 / 訂正根拠 / 破棄根拠 |
|---|---|---|
| 結論 1 | 確定 / 未確定 / 破棄 | 根拠 |
| 結論 2 | 確定 / 未確定 / 破棄 | 根拠 |
| ... | ... | ... |

### 5.5 context 再構築チェックリスト (Context Reconstruction Checklist)

次 session 開始前に確認すべき 5 項目:
1. 関連 file Read 完了 (recovery PLAN + 関連 PLAN + memory feedback)
2. git log --oneline -15 確認 (本 session の commit 状況)
3. handover status --json 確認 (現在 state)
4. memory feedback 確認 (関連 lesson learned)
5. tl-advisor adversarial check 投入 (recovery PLAN review)

### 5.6 再開ポイント (Resume Point)

- 次 session 開始時に最初に着手する task
- 前提条件 (確定済みの context / 未解決の課題 / 未承認の決定)
- 再開時の最初の Tool call 候補 (Read / WebSearch / Agent invocation)

### 5.7 再発防止策 (Recurrence Prevention)

- 何が事故の原因か (proximate cause + root cause)
- 再発防止策 (rule / hook / template の追加 / 既存 lint の強化)
- session 終了前チェックリスト 4 項目 fail-close との連動

## §6. session 終了前チェックリスト 4 項目 (fail-close)

**P3 で hook 機械強制**:

1. **中間結論が docs に永続化されているか**: PLAN / ADR / memory に該当 commit があるか
2. **carry 残件が PLAN or handover に明記されているか**: timetable / scope 明示
3. **認識訂正があった場合 memory feedback が更新されているか**: feedback_*.md に新規 entry があるか
4. **recovery kind PLAN が必要な場合 draft 起票済みか**: kind=recovery、本 PLAN template 準拠

→ 4 項目満たさず turn 終了は禁止 (`feedback_dont_stop_with_carry_remaining` 14h idle 事故防止)。

実装段階 (PLAN-099 Layer 1+5 連動):
- Stop hook で 4 項目自動 check (advisory 段階)
- PostToolUse hook で recovery PLAN 不在検出時 systemMessage 表示 (active guidance loop pattern、PLAN-090 連動)
- 最終的に PreCompact hook + Stop hook で fail-close (P3 段階)

## §7. cli/templates/plan/recovery/template.md

```markdown
---
plan_id: PLAN-NNN
title: "PLAN-NNN: <recovery 対象 session 名>"
layer: cross
kind: recovery
status: draft
drive: troubleshoot
created: <YYYY-MM-DD>
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "Recovery PM"
  - role: tl-advisor
    slot_label: "Recovery TL adversarial check"
generates:
  - artifact_path: <next session 着手 PLAN>
    artifact_type: design_doc
dependencies:
  parent: <親 PLAN>
  requires: <前提 PLAN list>
related_memories: <関連 feedback list>
---

# PLAN-NNN: <title>

## §1. 事故記録 (Incident Record)
...

## §2. 議論順序 timeline (Discussion Timeline)
...

## §3. 認識訂正履歴 (Recognition Correction History)
...

## §4. 中間結論 list (Intermediate Conclusions)
...

## §5. context 再構築チェックリスト (Context Reconstruction Checklist)
...

## §6. 再開ポイント (Resume Point)
...

## §7. 再発防止策 (Recurrence Prevention)
...
```

## §8. cli/lib/recovery_plan_check.py

実装方針:
- `validate_recovery_plan(plan_path: Path) -> ValidationResult`:
  - frontmatter `kind: recovery` 確認
  - §1〜§7 必須セクション存在確認 (markdown heading parse)
  - §1 metadata (event_type / severity) 必須フィールド確認
  - §4 中間結論 list が 3 列形式 (Conclusion / 状態 / 根拠) であること確認
  - §5 5 項目 / §6 next session task / §7 再発防止策 が記述済みであること
- `check_freshness(plan_path: Path, max_days: int = 7) -> FreshnessResult`:
  - 最終更新日 (frontmatter `revised` または file mtime) からの経過日数
  - default 7 日超過で warn、14 日超過で fail

## §9. helix doctor check_recovery_plan_freshness

PLAN-093 拡張 (`helix doctor check_recovery_plan_freshness`):
- `docs/plans/PLAN-*.md` から `kind: recovery` AND `status: active` を抽出
- 各 PLAN に対し `check_freshness` 実行
- 結果サマリ (warn N 件 / fail M 件) 出力
- exit code: 0 (全 PASS) / 1 (warn あり、advisory 段階) / 2 (fail あり、fail-close 段階)

## §10. 段階導入 (Phased Adoption)

| Phase | 内容 | 期間目安 | exit code |
|---|---|---|---|
| P1 | template + check.py 配置、helix doctor に追加 (warn-only) | 1 session | 0 |
| P2 | session 終了前 4 項目 advisory (Stop hook で表示、強制なし) | 2-3 session | 0 |
| P3 | session 終了前 4 項目 fail-close (Stop hook + PreCompact hook で turn 終了拒否) | 3-5 session | 2 |

## §11. テスト戦略

### 11.1 plan_validator unit (qa role)
- fake recovery PLAN fixture (7 セクション完備版 / 各セクション 1 個欠落版 × 7 件)
- frontmatter parse: kind=recovery + status=active + severity=high の validation
- section parse: §1〜§7 必須 heading 検出
- §4 中間結論 list 3 列形式の validation

### 11.2 freshness check unit (qa role)
- fake recovery PLAN fixture (revised 3 日前 / 7 日前 / 8 日前 / 14 日前 / 15 日前)
- 7 日 / 14 日 境界条件
- frontmatter `revised` 不在時の file mtime fallback

### 11.3 helix doctor 統合 (se role)
- fake docs/plans/ fixture (recovery 5 件 + 非 recovery 50 件)
- check_recovery_plan_freshness の対象抽出
- exit code 境界 (0 / 1 / 2)

### 11.4 Stop hook fail-close 統合 (se role、P3 段階)
- fake session state fixture (carry あり / carry なし / recovery PLAN 起票済 / 未起票)
- Stop hook decision: continue / block 判定
- session 終了前 4 項目の機械 check

## §12. DoD

1. cli/templates/plan/recovery/template.md が 7 必須セクション (§5) を含む
2. cli/lib/recovery_plan_check.py が validate_recovery_plan + check_freshness を実装
3. cli/lib/tests/test_recovery_plan_check.py が §11.1-11.2 を網羅
4. helix doctor check_recovery_plan_freshness が exit code 0/1/2 で動作
5. helix doctor list に check_recovery_plan_freshness が登録
6. docs/runbook/recovery-plan-usage.md が利用手順を記述
7. 既存 helix doctor / helix-plan / Stop hook がデグレなし (git diff 確認)

## §13. V-model 4 artifact 双方向 trace

| Artifact | 位置 | 担当 role |
|---|---|---|
| ① 設計 | docs/plans/PLAN-098-recovery-plan-kind-normalization.md (本 PLAN) | pm-advisor / pmo-sonnet |
| ② 実装コード | cli/lib/recovery_plan_check.py / helix doctor 拡張 / cli/templates/plan/recovery/template.md | se |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-098-unit-test-design.md (別 file 起票、別 session) | qa |
| ④ テストコード | cli/lib/tests/test_recovery_plan_check.py | qa |

双方向 trace:
- 本 PLAN §8 → cli/lib/recovery_plan_check.py docstring「契約: PLAN-098 §8」
- 本 PLAN §11 → docs/v2/L4-test-design/PLAN-098-unit-test-design.md の対象設計
- テスト設計 doc → cli/lib/tests/test_recovery_plan_check.py docstring「DoD 検証: PLAN-098-unit-test-design.md」

## §14. 関連 PLAN / ADR / memory

### related_plans (require)
- PLAN-091 (kind: recovery を 11 番目として定義、frontmatter 語彙の正本)
- PLAN-093 (helix doctor 拡張統合の前提)
- PLAN-MM-001 (parent hub)

### related_adrs
- ADR-031 (本 PLAN の L2 凍結 snapshot、同時起票)
- ADR-025 (V5 framework 本体、recovery kind は V5 要素 #17)
- ADR-027 (helix doctor 拡張、本 PLAN は check_recovery_plan_freshness 追加)

### related_memories
- `feedback_recovery_plan_kind_missing` (本 PLAN の出発点、本 session 確立)
- `feedback_dont_stop_with_carry_remaining` (§6 4 項目の根拠、14h idle 事故)
- `project_2026_05_20_v5_framework_evolution_recovery` (V5 確立過程の recovery 事例)

## §15. デグレ禁止確認

- 既存 cli/templates/plan/ 既存 template (design / impl / poc / reverse / refactor / retrofit / research / add-design / add-impl / troubleshoot) は **編集しない** (新規 recovery/ サブディレクトリ追加のみ)
- 既存 helix doctor (`cli/lib/helix_doctor.py` 等) は **編集しない** (新 check 追加のみ、既存 check の挙動変更禁止)
- 既存 handover CLI (`cli/helix-handover` 等) は **編集しない** (recovery PLAN は handover とは独立した上位概念)
- 既存 PLAN-001〜097 / PLAN-099 は **編集しない** (本 PLAN は新規 file のみ)
