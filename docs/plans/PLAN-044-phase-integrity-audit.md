---
plan_id: PLAN-044
title: 'PLAN-044（HELIX 全フェーズ整合性監査 - drift 8 件 + 1 件 carry 集約解消）'
status: completed
completed: 2026-05-10
created: 2026-05-10
author: Docs (Codex)
priority: medium
size: M
phases_affected: L7, R0-R4, RGC, gate schema (cross-phase)
parent_plan: PLAN-043
gates: G1, G2, G3, G4
acceptance:
  - drift_p1_count: 0
  - drift_p2_count: 0
  - drift_p3_count: 0
  - grade_recover: A
  - tests_all_pass: true
  - branch_minimal_footprint: true
verification_commands:
  drift_p1_count:
    command: "本 PLAN 完了時 codex research による再監査で確認"
    expected: "0"
  drift_p2_count:
    command: "本 PLAN 完了時 codex research による再監査で確認"
    expected: "0"
  drift_p3_count:
    command: "本 PLAN 完了時 codex research による再監査で確認"
    expected: "0 (D-009 は scope 外 carry のため除外)"
  grade_recover:
    command: "PLAN-044 retro §動作健全性 grade で再評価"
    expected: "A"
  tests_all_pass:
    command: "cli/helix test && python3 -m pytest cli/lib/tests/ tests/ -q"
    expected: "helix-test 614+, pytest cli/lib/tests/ 1007+, pytest tests/ 23 全 PASS"
  branch_minimal_footprint:
    command: "git branch --list 'improvements/plan-044*' | wc -l"
    expected: "0 (W-final で削除)"
related: [PLAN-043, PLAN-042, PLAN-041, PLAN-038, ADR-014, ADR-016]
---

## §1 目的

PLAN-043 完遂後に実施した HELIX 全フェーズ監査で検出した drift 8 件を本 PLAN で解消し、D-009 は scope 外 carry として PLAN-045 へ固定する。

本 PLAN の狙いは、単なる文言修正ではなく、次の 3 点を同時に満たすことにある。

1. Forward / Reverse / readiness の各正本にある記述差を解消し、phase 定義を repo 全体で一貫させる。
2. helper 実装、CLI help、state machine、template の整合を取ることで、文書上の定義と実動の分岐を一致させる。
3. 監査結果を PLAN として固定し、grade B+ 判定を A に戻すための根拠を明文化する。

対象 drift は以下の 8 件である。

- P1: D-001, D-002, D-003
- P2: D-004, D-005, D-006, D-007, D-008
- P3: D-009

## §2 全体方針

### §2.1 設計原則

- W-0 は draft 起草専任とし、実装ファイルの変更は行わない。
- W-1 は spec 正本の文書整備であり、gate helper 実装の変更を伴わない。
- W-2 は Reverse 正本の文書整備であり、W-1 で gate 正本を固定した後に着手する。
- W-4 は L8 と RG4 の表現整備であり、W-2 で Reverse の正本が揃った後に着手する。
- W-3 と W-5 と W-6 は helper / CLI / test の実装であり、文書正本の整備が完了してから着手する。
- W-final は統合検証、retro、push を担う。
- scope 外の変更は行わず、必要になった場合は interrupted / blocked 扱いで戻す。
- D-009 は writable `.helix/` が必須の環境前提として扱い、scope 外 carry として PLAN-045 候補に明記する。

### §2.2 スコープ境界

#### W-0: draft + TL review + finalize

- 本ファイル `docs/plans/PLAN-044-phase-integrity-audit.md` のみを新規作成する。
- 監査結果、Sprint 構成、acceptance、risk を整理し、後続 task の正本を固定する。

#### W-1: Spec 正本補完

- 対象: `skills/SKILL_MAP.md`
- 対象: `skills/tools/ai-coding/references/gate-policy.md`
- 追加内容: G6.5 / G6.7 / G6.9 の forward gate 参照、Pre-Release セクション、evidence schema、fail-close 条件

#### W-2: Reverse 5 type 整合

- 対象: `skills/SKILL_MAP.md`
- 対象: `skills/workflow/reverse-analysis/SKILL.md`
- 追加内容: code / design / upgrade / normalization / fullback の 5 type matrix、R0-R4 mapping、skip 条件、RGC の動作差分

#### W-3: Gate schema 整合

- 対象: `cli/lib/meta_phase.py`
- 対象: `cli/lib/deliverable_gate.py`
- 対象: `cli/templates/state-machine.yaml`
- 対象: `.helix/state-machine.yaml`
- 追加内容: G6.5 / G6.7 / G6.9 の VALID_GATES、layer mapping、prereq 同期

#### W-4: L8 明確化 + RG4 矛盾解消

- 対象: `skills/tools/ai-coding/references/workflow-core.md`
- 対象: `skills/SKILL_MAP.md`
- 対象: `skills/tools/ai-coding/references/gate-policy.md`
- 追加内容: RG4 を独立 gate としない記述へ統一、L8 の acceptance/no-gate 表現を明文化

#### W-5: Help 改善

- 対象: `cli/helix-reverse`
- 追加内容: `<type> <stage> --help` を stage 固有説明へ差し替え

#### W-6: Test 追加

- 対象: `cli/tests/`
- 対象: `cli/lib/tests/`
- 追加内容: G6.5 / G6.7 / G6.9 prereq、Reverse multitype matrix、RGC fail-close、meta_phase、deliverable_gate の回帰テスト

#### W-final: 統合検証 + retro + push

- `helix-test`、`pytest cli/lib/tests`、`pytest tests`、`bats cli/tests` の全 PASS を確認する。
- `docs/plans/PLAN-044*.md` の status を completed に更新する。
- `.helix/retros/PLAN-044.md` を作成する。
- branch 最小 footprint を維持して統合する。
- D-009 は本 PLAN scope 外として PLAN-045 候補へ carry することを確認する。

### §2.3 既知制約

- D-009 は read-only env における SQLite 接続失敗であり、CLI の実装経路ではなく実行環境の前提確認を含む。
- `helix code find` は writable `.helix/` がない read-only env では動作しない。
- 本 PLAN では D-009 を scope 外として close し、PLAN-045 候補へ carry する。
- Reverse 文書量の増加により `skills/SKILL_MAP.md` の可読性低下が起こりうるため、必要に応じて外出しを検討する。
- G8 の表現は他 phase と同等以上に明確化し、L8 の受入終端で no-gate acceptance を誤読させない。

### §2.4 参照関係

- [PLAN-043](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-043-consolidated-carry-resolution.md) を直近の carry 解消例として参照する。
- [PLAN-042](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-042-filter-design-and-legacy-and-lock-poc.md) を gate / lock / drift 文書化の前例として参照する。
- [workflow-core.md](/home/tenni/ai-dev-kit-vscode/skills/tools/ai-coding/references/workflow-core.md) と [gate-policy.md](/home/tenni/ai-dev-kit-vscode/skills/tools/ai-coding/references/gate-policy.md) を正本として扱う。

## §3 解決対象

### §3.1 W-1: Spec 正本補完

D-001 の主因は、`G6.5 / G6.7 / G6.9` が `helix gate` と templates/state-machine 側には見えている一方で、`SKILL_MAP.md` と `gate-policy.md` の正本に未定義だったことである。

この W では、仕様の正本を整えることに集中する。

- `skills/SKILL_MAP.md` の forward gate 一覧に G6.5 / G6.7 / G6.9 を追加する。
- `skills/tools/ai-coding/references/gate-policy.md` に Pre-Release セクションを新設する。
- Pre-Release には目的、exit 条件、evidence schema、fail-close 条件を含める。
- G6.5 / G6.7 / G6.9 が helper 実装や state machine で参照できるよう、名称の揺れをなくす。

受入条件は次の通り。

- `SKILL_MAP.md` の gate 一覧から G6.5 / G6.7 / G6.9 を参照できる。
- `gate-policy.md` に Pre-Release の gate 定義がある。
- 仕様の参照先が 1 本化され、templates/state-machine 側との差分が説明可能になる。

### §3.2 W-2: Reverse 5 type 整合

D-002 の主因は、Reverse CLI が code / design / upgrade / normalization / fullback の 5 type を持つ一方で、`SKILL_MAP.md` の Reverse 説明が code 型 R0-R4 のみを前提としていたことにある。

この W では、Reverse を type-aware に再記述する。

- 5 type を matrix 形式で整理し、各 type の R0-R4 振る舞いを明示する。
- code 以外の type で R1 / R3 が skip される条件を明記する。
- RGC の扱いを、type ごとの stage 差分として説明する。
- `skills/workflow/reverse-analysis/SKILL.md` の説明を、CLI 実動と一致する文言へ揃える。

受入条件は次の通り。

- 5 type それぞれに R0-R4 stage の動作差分がある。
- code 以外の type で skip 条件が明文化されている。
- RGC の説明が stage / type と矛盾しない。

### §3.3 W-3: Gate schema 整合

D-005 / D-006 / D-007 は、helper 側の gate schema が spec の追加を追従できていない drift である。

この W では、helper 実装の定義を整合させる。

- `cli/lib/meta_phase.py` の `VALID_GATES` に G6.5 / G6.7 / G6.9 を追加する。
- `cli/lib/deliverable_gate.py` の layer mapping に G6.5 / G6.7 / G6.9 を追加する。
- `cli/templates/state-machine.yaml` と `.helix/state-machine.yaml` の prereq を揃える。
- state machine の正本と template の差異を最小化し、生成系で drift が再発しにくい形にする。

受入条件は次の通り。

- `pytest cli/lib/tests/test_meta_phase.py` で G6.5 / G6.7 / G6.9 が有効値として通る。
- `pytest cli/lib/tests/test_deliverable_gate.py` で layer mapping が通る。
- state-machine の不一致 test が PASS する。

### §3.4 W-4: L8 明確化 + RG4 矛盾解消

D-003 と D-004 は、phase 説明の強弱と reference 参照の不一致である。

- D-003 は `workflow-core.md` にある RG4 Gap & Routing 参照と、`gate-policy.md` の「RG4 は独立ゲートではない」という記述の衝突である。
- D-004 は L8 の受入終端について、CLI / readiness / no-gate の表現が十分に強くない問題である。

この W では、以下を実施する。

- `workflow-core.md` の RG4 参照を「R4 stage 内 routing」に修正する。
- 独立 gate と読める表現を削除する。
- `SKILL_MAP.md` と `gate-policy.md` で、L8 = acceptance, no gate を明示する。
- CLI readiness との関係を、受入終端として簡潔に表現する。

受入条件は次の通り。

- repo 全体で「RG4 独立 gate」という表現が 0 件になる。
- L8 = no-gate-acceptance が docs で少なくとも 1 箇所以上明文化される。
- CLI / readiness / acceptance の関係が同じ意味で読める。

### §3.5 W-5: Help 改善

D-008 の主因は、`helix reverse <type> <stage> --help` が共通 usage 表示のままで、stage 固有説明になっていなかったことである。

この W では、help の情報密度を CLI 実動に合わせて上げる。

- `helix reverse design R1 --help` と `helix reverse code R1 --help` の表示を分ける。
- stage ごとの意味を簡潔に表示する。
- type ごとの動作が 1 回の help で把握できるようにする。
- usage の共通部分は残しつつ、差分だけを stage-aware にする。

受入条件は次の通り。

- `helix reverse design R1 --help` と `helix reverse code R1 --help` の表示が異なる。
- type-stage 固有の説明が出る。
- 共通 usage のままではなく、文脈に応じた help になる。

### §3.6 W-6: Test 追加

D-005 / D-006 / D-007 / D-008 / D-001 / D-002 / D-003 / D-004 を回帰しないため、文書と helper の両方に対するテストを追加する。

対象は次の 2 系列である。

- `cli/tests/` の bats: G6.5 / G6.7 / G6.9 prereq、Reverse multitype matrix、RGC fail-close
- `cli/lib/tests/` の pytest: meta_phase、deliverable_gate、state-machine 整合

この W の役割は、仕様修正後の drift 再発を防ぐことにある。

受入条件は次の通り。

- bats が 5 件以上追加される。
- pytest が 5 件以上追加される。
- `helix-test` の既存通過状態を維持する。

## §4 Sprint 構成

W-0 で本 draft を起票し、TL review を 1-3 round で実施する。

推奨順序は以下とする。

1. W-1 の docs 整備を先に終える。
2. W-5 の helix-reverse 単独改善を並列で進める。
3. W-2 を W-1 完了後に投入し、Reverse 正本を確定する。
4. W-4 を W-2 完了後に投入し、L8 / RG4 表現を確定する。
5. W-3 の helper sync を W-1 完了後に実装する。
6. W-6 で test を追加する。
7. W-final で統合検証、retro、push を完了する。

この順序により、正本が先に確定し、その後の helper / CLI / test が drift なく追従できる。

## §4.1 依存表

| W | depends_on | reason | allowed_files |
|---|------------|--------|---------------|
| W-1 | (none) | docs first | skills/SKILL_MAP.md, skills/tools/ai-coding/references/gate-policy.md |
| W-2 | W-1 | SKILL_MAP.md 衝突回避 | skills/SKILL_MAP.md, skills/workflow/reverse-analysis/SKILL.md |
| W-4 | W-2 | SKILL_MAP.md 衝突回避 + workflow-core.md 並行編集 | skills/SKILL_MAP.md, skills/tools/ai-coding/references/workflow-core.md, skills/tools/ai-coding/references/gate-policy.md |
| W-5 | (none) | helix-reverse 単独 | cli/helix-reverse |
| W-3 | W-1 | G6.5/6.7/6.9 正本確定後 helper 同期 | cli/lib/meta_phase.py, cli/lib/deliverable_gate.py, cli/templates/state-machine.yaml, .helix/state-machine.yaml |
| W-6 | W-1, W-2, W-3, W-4, W-5 | 全実装完了後 test 追加 | cli/tests/, cli/lib/tests/ |
| W-final | W-1〜W-6 | 統合検証 + retro + push | docs/plans/PLAN-044*.md, .helix/retros/PLAN-044.md |

## §5 ゲート

- G1: drift 8 件 + 1 件 carry の分類と解消方針が明確である。
- G2: spec 正本、helper、CLI help、test の関係が phase 別に分離されている。
- G3: 各 W の対象ファイルと受入条件が特定されている。
- G4: W-final で統合検証・retro・push の完了が判定できる。

## §6 検証戦略

- W-1: `SKILL_MAP.md` と `gate-policy.md` の gate 定義の突合確認。
- W-2: Reverse 5 type matrix の記述確認と stage 差分の有無確認。
- W-3: `pytest cli/lib/tests/test_meta_phase.py` と `pytest cli/lib/tests/test_deliverable_gate.py` の PASS 確認。
- W-4: grep ベースで「RG4 独立 gate」表現の消失と L8 no-gate 記述の存在確認。
- W-5: `helix reverse design R1 --help` / `helix reverse code R1 --help` の差分確認。
- W-6: bats + pytest の新規追加分が PASS することを確認する。
- W-final: `helix-test` / `pytest cli/lib/tests` / `pytest tests` / `bats cli/tests` の全 PASS を確認する。

## §7 Risks

- `skills/SKILL_MAP.md` は現時点で 416 行あり、さらに +50〜100 行追記すると可読性と保守性が悪化するため、必要なら `skills/workflow/reverse-analysis/references/multitype-matrix.md` などへの外出しを検討する。
- G6.5 / G6.7 / G6.9 の helper 追従で、既存 test の前提が崩れる可能性があるため、W-3 と W-6 は順序を守る。
- PreToolUse hook (PLAN-043 W-6) が PLAN draft 編集を block する場合があるため、必要時は `HELIX_ALLOW_OPUS_PLAN_FIX=1` で unblock する。docs role 委譲経由なら hook 影響は受けにくいので、本 PLAN は docs 委譲経由を default とする。
- W-3 helper 変更は `VALID_GATES` への追加のみとし、既存値の remove は行わない。W-6 test 追加は新規ファイルに限定する。
- W-5 の help 改善で usage が冗長化しすぎると、かえって可読性が落ちるため、stage 固有差分のみを出す。

## §8 PLAN-043 retro carry

PLAN-043 retro carry 候補は次の 5 件であり、本 PLAN の scope には含めない。

1. legacy migration 残 7 件 → PLAN-045 carry（本 PLAN scope 外、別 progressive PLAN）
2. lock 機構 critical path 残 (helix.db / phase.yaml) → PLAN-045 carry（本 PLAN scope 外、別 PLAN）
3. stale lock cleanup automation → PLAN-045 carry（split-lock 回避設計、別 PLAN）
4. Codex 委譲時 allowed_files 自動推定 → PLAN-046+ 候補（本 PLAN scope 外）
5. D-009: `helix code find` が read-only env で SQLite 接続失敗 (env constraint, helper note 追記候補) → PLAN-045 carry

本 PLAN は framework drift 解消に scope を限定し、上記 5 件は別 PLAN で扱う。

## 関連

- [PLAN-043](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-043-consolidated-carry-resolution.md)
- [PLAN-042](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-042-filter-design-and-legacy-and-lock-poc.md)
- [SKILL_MAP.md](/home/tenni/ai-dev-kit-vscode/skills/SKILL_MAP.md)
- [gate-policy.md](/home/tenni/ai-dev-kit-vscode/skills/tools/ai-coding/references/gate-policy.md)
- [workflow-core.md](/home/tenni/ai-dev-kit-vscode/skills/tools/ai-coding/references/workflow-core.md)
