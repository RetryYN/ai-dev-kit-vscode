---
plan_id: L5-helix-workflows-モジュール分割設計plan
title: "L5-helix-workflows-モジュール分割設計plan: HELIX-workflows V2 モジュール構成 / 責務分担 / 依存 graph"
kind: design
layer: L5
drive: be
status: finalized
created: 2026-05-27
owner: PM
process_layer: L5
parent_process: HELIX-workflows/helix-process/L5-detailed-design.md
pairs_test_design:
  - docs/v2/L8-test-design/helix-workflows-integration-test-design.md
  - docs/v2/L8-test-design/helix-workflows-dependency-resolution-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G5 evidence)"
  - role: doc-reviewer
    slot_label: "doc-reviewer — ドキュメント品質レビュー"
generates:
  - artifact_path: docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md
    artifact_type: design_doc
dependencies:
  parent: L4-helix-workflows-機能設計plan
  requires:
    - L4-helix-workflows-方式設計plan
    - L4-helix-workflows-機能設計plan
    - L4-helix-workflows-データ設計plan
    - L4-helix-workflows-外部IF設計plan
    - L5-helix-workflows-内部処理設計plan
  blocks:
    - L5-helix-workflows-データ詳細設計plan
    - L5-helix-workflows-外部IF詳細設計plan
related_docs:
  - HELIX-workflows/helix-process/L5-detailed-design.md
  - HELIX-workflows/helix-process/L8-integration-test.md
  - docs/v2/L4-architecture/helix-workflows-functional-design.md
  - docs/v2/L4-architecture/helix-workflows-system-architecture.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md
---

## §0 PLAN concept

本 PLAN は HELIX-workflows V2 の **モジュール構成 / 責務分担 / 依存 graph** を凍結する。L4 機能設計（F1-F10）の機能カタログを物理 module（python file / bash script / hook file / config）にどう配置するかを確定する。

### §0.1 担当 scope（L5 4 分割における本 PLAN の責務）

| 観点 | 本 PLAN scope | 隣接 PLAN scope |
|---|---|---|
| モジュール構成・責務分担・依存 graph | ◎ 本 PLAN | — |
| 内部処理フロー / 状態機械 / 算定式 | × | L5-helix-workflows-内部処理設計plan |
| helix.db 物理 schema | × | L5-helix-workflows-データ詳細設計plan |
| CLI API spec / hook payload schema | × | L5-helix-workflows-外部IF詳細設計plan |

### §0.2 module 分類

1. **cli/** — bash dispatcher (helix-*)
2. **cli/lib/** — Python helper module (algorithm / DB access / validator)
3. **cli/config/** — YAML / JSON config (roles.yaml, models.yaml, helix-workflows.yaml)
4. **.claude/hooks/** — Claude Code hook (statusLine / PreCompact / SessionStart / UserPromptSubmit / PreToolUse / PostToolUse / Stop)
5. **.claude/agents/** — subagent frontmatter + system prompt
6. **scripts/** — git hook (pre-commit / pre-push)
7. **skills/** — HELIX skill (SKILL.md + references)
8. **HELIX-workflows/** — process / mode workflow doc (正本)
9. **docs/v2/** — L0-L14 設計 / テスト設計 doc (正本 mirror)
10. **docs/plans/** — PLAN (L0-L14 工程別)
11. **docs/adr/** — ADR snapshot

### §0.3 不確定事項からの引き継ぎ（pmo-sonnet inventory より）

本 PLAN で確定すべき不確定事項:

- (U-01〜U-11 のうち module 配置に直接関わるものは無、ただし U-07 hook 種別確定 ↔ .claude/hooks/ 配置 整合性確認は本 PLAN scope)

## §1 工程表

| Step | 作業 | 担当 | 状態 |
|---|---|---|---|
| 1 | 現状の cli/ / cli/lib/ / .claude/hooks/ / scripts/ の module 一覧抽出 | PM + pmo-sonnet | done |
| 2 | F1-F10 各機能が touch する module を機能 × module matrix で抽出 | PM | done |
| 3 | 責務分担 ルール起草 (1 module = 1 機能 or 1 横断 concern) | PM | done |
| 4 | 依存 graph (mermaid) 起草 - 循環依存検出 | PM | done |
| 5 | F6-F10 新規 module の追加配置決定 (homeostasis.py / evolution.py / migration.py / apoptosis.py / coexist.py 等) | PM + tl-advisor | done |
| 6 | hook 11 件の .claude/hooks/ 配置確定 + matcher 確定 | PM | done |
| 7 | 二重 audit R1 (tl-advisor + pmo-sonnet) | TL + PMO | done |
| 8 | R1 反映 + R2 audit | PM + TL + PMO | done |
| 9 | L8 結合テスト設計 pair freeze | PM | done |
| 10 | commit + push | PM | pending |

## §2 実装計画

### §2.1 doc 構造 candidate

`docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md`:

```
§0 PLAN reference + scope 宣言
§1 module 分類体系 (11 大分類)
§2 機能 × module matrix (F1-F10 × 各 module)
§3 cli/ dispatcher
  §3.1 helix-* bash entry 一覧 (~30 entry)
  §3.2 役割 dispatch table (cli/ROLE_MAP.md 連動)
§4 cli/lib/ Python helper
  §4.1 既存 module 一覧 + 責務
  §4.2 新規追加 module (F6-F10): homeostasis.py / evolution.py / migration.py / apoptosis.py / coexist.py
  §4.3 共通 module: db.py / plan_validator.py / skill_recommender.py / verify_codex.py
  §4.4 依存 graph (mermaid)
§5 cli/config/ YAML / JSON
  §5.1 既存 config 一覧
  §5.2 新規追加 config: helix-workflows.yaml (versioning) / coexist.yaml / homeostasis-threshold.yaml
§6 .claude/hooks/ Claude Code hook
  §6.1 hook 11 件一覧 + 種別 + matcher + 入出力契約
  §6.2 hook 間依存関係 (例: SessionStart cleared → UserPromptSubmit 注入)
§7 .claude/agents/ subagent
  §7.1 PMO 9 + PdM 3 = 12 subagent 一覧 + frontmatter + 許可 model family
§8 scripts/ git hook
  §8.1 pre-commit (plan_lint / doc_link_check)
  §8.2 pre-push (email_pattern / secret_scan)
§9 skills/ HELIX skill
  §9.1 SKILL.md 配置原則 (skills/<category>/<skill>/SKILL.md)
  §9.2 references/ 配置原則
§10 doc / PLAN / ADR 配置原則
  §10.1 HELIX-workflows/ (正本)
  §10.2 docs/v2/ (mirror)
  §10.3 docs/plans/L<NN>/ (工程別)
  §10.4 docs/adr/ (snapshot)
§11 module 命名規約
  §11.1 cli/lib/*.py (snake_case)
  §11.2 .claude/hooks/*.sh (kebab-case)
  §11.3 skills/<category>/<skill>/SKILL.md
§12 dependency direction rules
  §12.1 cli/ → cli/lib/ 一方向
  §12.2 .claude/hooks/ → cli/lib/ via helix CLI call
  §12.3 循環依存禁止
§13 4 artifact 双方向 trace
§14 implementation_status 表 (planned/partial/implemented)
```

### §2.2 module 粒度

- 1 file = 1 責務（SRP）が default
- 例外: dispatcher (cli/helix) は薄い router、複数機能を呼び出すが logic は持たない
- 例外: .claude/hooks/sessionstart-history-injection.sh (複数 source からの bundle 統合) は本来 1 module = 1 責務違反、L5 で分割推奨候補とする

## §3 DoD

- AC-MOD-01: 機能 × module matrix が F1-F10 全 5 機能領域 + Reverse 経路 + governance hook で完備
- AC-MOD-02: 新規追加 module (F6-F10 関連) のファイル名 / path 確定
- AC-MOD-03: hook 11 件の .claude/hooks/ 配置 + matcher 確定
- AC-MOD-04: 依存 graph (mermaid) で循環依存ゼロ確認
- AC-MOD-05: subagent 12 件 + 許可 model family の整合性確認
- AC-MOD-06: module 命名規約凍結
- AC-MOD-07: 二重 audit R1 + R2 PASS
- AC-MOD-08: L8 pair PLAN への blocks 設定
- AC-MOD-09: implementation_status 表に planned/partial/implemented 全件記載
- AC-MOD-10: dependency direction rule 違反検出 lint candidate 起票 (helix doctor check_dependency_direction)

## §4 関連

- pair: docs/v2/L8-test-design/helix-workflows-integration-test-design.md
- parent: L4-helix-workflows-機能設計plan
- siblings: L5-helix-workflows-内部処理設計plan / L5-helix-workflows-データ詳細設計plan / L5-helix-workflows-外部IF詳細設計plan
- ADR snapshot 候補: ADR-046 (CLI canonical + hook contract + module dependency rule の大局判断時)

## L5 完遂 evidence (2026-05-29)

- 設計 doc: docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md — 本体化完遂 (§2.1 機能×module matrix 100% coverage)、frontmatter status: frozen
- pair freeze: L5↔L8 双方向 trace (IT-MOD 結合テスト設計 + dependency-resolution-design)
- 監査: pmo-sonnet 機械検証 (placeholder 0 / matrix 100% coverage) + tl-advisor adversarial check
- DoD: AC-MOD-01〜AC-MOD-09 達成。AC-MOD-10 (helix doctor check_dependency_direction lint 候補) は L7 carry
- carry (L7 実装): 新規 module (F6-F10: homeostasis.py / evolution.py 等) の implemented 遷移 + dependency direction lint 実装
