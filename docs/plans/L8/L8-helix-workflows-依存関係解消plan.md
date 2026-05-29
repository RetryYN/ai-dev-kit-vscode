---
plan_id: L8-helix-workflows-依存関係解消plan
title: "L8-helix-workflows-依存関係解消plan: HELIX-workflows V2 依存関係不整合の検出 + 解消"
kind: design
layer: L8
drive: be
status: finalized
freeze_note: "L5↔L8 pair freeze (2026-05-29): pair doc dependency-resolution-design.md frozen, T-DEP-* 10ケース凍結。テスト実行/fixture実体は L7-L8 carry"
created: 2026-05-27
owner: PM
process_layer: L8
parent_process: HELIX-workflows/helix-process/L8-integration-test.md
pairs_design:
  - docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G8 evidence)"
generates:
  - artifact_path: docs/v2/L8-test-design/helix-workflows-dependency-resolution-design.md
    artifact_type: design_doc
dependencies:
  parent: L8-helix-workflows-結合テストplan
  requires:
    - L5-helix-workflows-モジュール分割設計plan
    - L5-helix-workflows-内部処理設計plan
    - L8-helix-workflows-結合テストplan
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/L8-integration-test.md
  - docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md
  - docs/v2/L8-test-design/helix-workflows-integration-test-design.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
---

## §0 PLAN concept

本 PLAN は L5 モジュール分割設計の dependency graph を機械検証可能な状態で凍結する。循環依存 / 一方向 rule 違反 / unused module / missing dependency を検出 + 解消する仕組みを設計する。

L8 = V-model 右腕 検証フェーズの一部。L5 モジュール分割 doc §12 dependency direction rules の運用 enforcement を担う。

### §0.1 担当 scope

| 観点 | 本 PLAN scope |
|---|---|
| dependency graph 解析 | ◎ |
| 循環依存検出 (cycle detection) | ◎ |
| 一方向 rule 違反検出 (cli/ → cli/lib/ 一方向) | ◎ |
| unused module 検出 | ◎ |
| missing dependency 検出 | ◎ |
| helix doctor check_dependency_direction 新設 | ◎ |

### §0.2 解消対象 dependency 不整合

1. **循環依存**: cli/lib/<A>.py imports <B>.py かつ <B>.py imports <A>.py
2. **逆方向**: cli/lib/<A>.py が cli/helix-<X> を call (cli/lib → cli/ は禁止)
3. **stale module**: import 元 0 件の module (削除 candidate)
4. **missing**: PLAN.generates で宣言された artifact が実 file 不在
5. **subagent ↔ Agent tool 不整合**: .claude/agents/<X>.md frontmatter `model` field と guard hook 許可リスト不一致

## §1 工程表

| Step | 作業 | 担当 | 状態 |
|---|---|---|---|
| 1 | 既存 helix doctor check_dependency_* の有無調査 (`grep -n "check_dep" cli/lib/doctor_*.py`) | PM | pending |
| 2 | dependency graph 解析 algorithm 起草 (Python AST + import graph) | PM | pending |
| 3 | 循環依存検出 algorithm (DFS / Tarjan SCC) | PM | pending |
| 4 | 一方向 rule 違反検出 algorithm (cli/ → cli/lib/ 階層チェック) | PM | pending |
| 5 | stale / missing 検出 algorithm | PM | pending |
| 6 | helix doctor check_dependency_direction の output 仕様 (pass / warn / fail) | PM | pending |
| 7 | 既存 dependency 不整合の inventory 抽出 (本 PLAN 起票時点) | pmo-sonnet | pending |
| 8 | 不整合解消 ロードマップ起票 (P0 / P1 / P2 別) | PM | pending |
| 9 | 二重 audit R1 (tl-advisor + pmo-sonnet) | TL + PMO | pending |
| 10 | R1 反映 + R2 audit | PM + TL + PMO | pending |
| 11 | commit + push | PM | pending |

## §2 実装計画

### §2.1 doc 構造 candidate

`docs/v2/L8-test-design/helix-workflows-dependency-resolution-design.md`:

```
§0 PLAN reference + scope 宣言
§1 dependency graph 全体方針
  §1.1 解析対象 (cli/ + cli/lib/ + .claude/hooks/ + .claude/agents/ + skills/)
  §1.2 graph 表現 (Python AST + import / bash source / yaml ref)
  §1.3 出力 format (mermaid + json + textual report)
§2 循環依存検出
  §2.1 algorithm (DFS / Tarjan SCC)
  §2.2 既知 cycle inventory (本 PLAN 起票時点)
  §2.3 解消戦略 (依存反転 / 共通 module 抽出)
§3 一方向 rule 違反検出
  §3.1 階層定義 (cli/ < cli/lib/ < cli/config/、cli/ → cli/lib/ → cli/config/ のみ許可)
  §3.2 .claude/hooks/ → cli/lib/ via helix CLI call (直接 import 禁止)
  §3.3 違反 inventory
§4 stale module 検出
  §4.1 import 元 0 件の module
  §4.2 削除 candidate vs 廃止候補 (DEPRECATED marker)
  §4.3 ⚠️ subagent 禁止 7 種の扱い (L5 モジュール分割 doc §7.3 と整合)
§5 missing dependency 検出
  §5.1 PLAN.generates で宣言された artifact が実 file 不在
  §5.2 helix doctor check_plan_drift との整合
§6 subagent ↔ Agent tool guard hook 整合
  §6.1 .claude/agents/<X>.md frontmatter `model` vs pretooluse-agent-guard.sh 許可リスト
  §6.2 違反検出 (Sonnet/Opus override block)
§7 helix doctor check_dependency_direction
  §7.1 sub-check 構成 (check_circular / check_one_way / check_stale / check_missing / check_subagent_guard)
  §7.2 exit code (0 pass / 1 warn / 2 fail-close)
  §7.3 fail-close vs advisory 判定基準
§8 不整合解消 ロードマップ
  §8.1 P0 (即修正): 循環依存 / 一方向 rule 違反
  §8.2 P1 (carry): stale module の削除
  §8.3 P2 (任意): subagent 禁止 7 種の整理
§9 4 artifact 双方向 trace
§10 implementation_status 表 (planned/partial/implemented)
```

## §3 DoD

- AC-DEP-01: dependency graph 解析 algorithm 凍結
- AC-DEP-02: 循環依存検出 algorithm + 既知 cycle inventory
- AC-DEP-03: 一方向 rule 違反検出 algorithm + 違反 inventory
- AC-DEP-04: stale module 検出 + 削除 candidate / DEPRECATED 分類
- AC-DEP-05: missing dependency 検出 + helix doctor check_plan_drift 整合
- AC-DEP-06: subagent ↔ guard hook 整合チェック
- AC-DEP-07: helix doctor check_dependency_direction 新設仕様
- AC-DEP-08: 不整合解消 ロードマップ (P0 / P1 / P2)
- AC-DEP-09: 二重 audit R1 + R2 PASS
- AC-DEP-10: implementation_status 表に planned/partial/implemented 全件記載

## §4 関連

- pair: L5-helix-workflows-モジュール分割設計plan (主)、L5-helix-workflows-内部処理設計plan (補)
- parent: L8-helix-workflows-結合テストplan
- ADR snapshot 候補: 不要 (本 PLAN 内で大局判断は発生しない見込み)
