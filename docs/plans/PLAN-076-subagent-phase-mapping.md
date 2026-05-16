---
plan_id: PLAN-076
title: "PLAN-076: subagent 工程マッピング framework (mandatory / on-demand 2 分類)"
status: draft
size: L
drive: be
created: 2026-05-17
owner: PM
phases: L1, L2, L3, L4
gates: G0.5, G2, G3, G4
related_plans:
  - PLAN-075 (V-model 設計⇔テスト対応、同時並行)
  - PLAN-077 (Sprint Plan 標準化、同時並行)
trigger: |
  ユーザー指摘 2026-05-17:
  (1)「サブエージェントのイノベーションとか、テックフォークとかも起動ポイントを
       工程に組み込んだほうがよくない？」
  (2)「工程明示的サブエージェントと実行選択サブエージェントって考え方はどうだろうか？」

  現状 14 種の PdM/PMO subagent の起動タイミングが HELIX 工程に紐付いていない
  (CLAUDE.md に「~に使う」記述があるだけ)。設計⇔テスト対応 (PLAN-075) と
  同じ trace 欠落問題。subagent を性格別に 2 分類し、framework 化する。
acceptance:
  - HELIX_CORE.md / SKILL_MAP.md / CLAUDE.md に subagent 2 分類 + 工程マップを明文化
  - mandatory subagent 10 種が HELIX 工程に紐付き、機械的に引ける
  - on-demand subagent 4 種は判断主導、強制化しない
  - cli/helix-agent コマンド (list / suggest / fire-mandatory / audit) 実装
  - helix.db に subagent_invocations table 追加
  - helix doctor / G2-G4 ゲートに「mandatory subagent 呼び出し audit」自動 lint
---

# PLAN-076: subagent 工程マッピング framework (mandatory / on-demand 2 分類)

## §1 背景

### 現状の問題

14 種の subagent (`.claude/agents/*.md` に定義) が HELIX 工程と紐付いていない。CLAUDE.md に「~に使う」記述があるだけで、いつ呼ぶか・必ず呼ぶか・呼ばれなかったらどうするかが framework 化されていない。

PLAN-074 で `pdm-tech-innovation` / `pmo-tech-fork` 等が G0.5 / L2 で呼ばれず素通りした (本来は新規プロダクト企画なら G0.5 で必須)。これは framework の trace 欠落問題。

### subagent 14 種の現状

| Subagent | 性格 | 呼ばれるべき工程 |
|---|---|---|
| pdm-tech-innovation | mandatory | G0.5 |
| pdm-marketing-innovation | mandatory | G0.5 |
| pdm-innovation-manager | mandatory | G0.5 / L1 接続 |
| pmo-tech-fork | mandatory | L2 entry (OSS 採用判断時) |
| pmo-tech-docs | mandatory | L2 entry (設計手法精読時) |
| pmo-helix-explorer | mandatory | L2-L4 entry |
| pmo-project-explorer | mandatory | L3-L4 entry |
| pmo-project-scout | mandatory | L4 entry (CLAUDE.md §4.5 既存) |
| pmo-helix-scout | mandatory | L2-L4 entry |
| pmo-sonnet | mandatory | G2/G4/L8 review |
| pmo-haiku | on-demand | 軽 Web 検索時 |
| pmo-tech-news | on-demand | 週次定期 sweep |
| pm-advisor | on-demand | PM 級難判断時 |
| tl-advisor | on-demand | TL 級難判断時 |

## §2 2 分類設計

### ① 工程明示的サブエージェント (mandatory by phase) — 10 種

HELIX 工程で **必須** 組み込み。

- 工程入場時に呼び出し履歴を helix.db で監査
- helix doctor / G2-G4 ゲートで「呼ばれていない → warn / fail」自動 lint 対象
- skip 理由は carry note / handover に必ず記録

### ② 実行選択サブエージェント (on-demand by judgment) — 4 種

工程に縛られず、**判断に応じて** 任意起動。

- free will、lint 対象外
- `helix agent suggest` で候補提示のみ、強制せず

### 設計上の意味

| 観点 | mandatory (10 種) | on-demand (4 種) |
|---|---|---|
| trace 対象 | 必須 (helix.db audit) | 任意 |
| 強制化 | lint / ゲート fail-close | なし |
| CLI | `helix agent fire-mandatory --phase L2` | `helix agent suggest --task "..."` |
| 記録 | 呼ばれない → carry note 必須 | 呼んだ場合のみ会話記録 |
| 失敗時 | retry / escalation | 任意判断 |

## §3 5 Phase 構成

### Phase 1 — HELIX core に subagent マップ明文化 (size: M)

- helix/HELIX_CORE.md §工程別 subagent 起動マップ (mandatory / on-demand 分離) 新規
- skills/SKILL_MAP.md 各 L レイヤ説明に「mandatory subagent」明示
- CLAUDE.md (project + global) 2 分類運用ルール

### Phase 2 — cli/helix-agent 実装 (size: M)

- `helix agent list [--type mandatory|on-demand]`
- `helix agent suggest --task "..."` (gpt-5.4-mini 推挙、on-demand 候補)
- `helix agent fire-mandatory --phase L2 [--auto]` (mandatory 一括並列投入)
- `helix agent audit --plan-id PLAN-XXX` (呼び出し履歴 audit)
- `helix agent show <name>` (subagent 詳細)

### Phase 3 — helix.db `subagent_invocations` table (size: S)

```sql
CREATE TABLE subagent_invocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subagent_name TEXT NOT NULL,
    subagent_type TEXT NOT NULL CHECK(subagent_type IN ('mandatory', 'on-demand')),
    phase TEXT NOT NULL,
    plan_id TEXT,
    invoked_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'skipped')),
    skip_reason TEXT
);
```

### Phase 4 — 既存 PLAN audit + retrofit (size: M)

- PLAN-067〜075 の subagent 呼び出し履歴を audit
- 必須工程で呼ばれていない subagent を carry note 化
- 必要に応じて remedial 呼び出し or 設計判断見直し

### Phase 5 — helix doctor / G2-G4 自動 lint (size: M)

- helix doctor に「mandatory subagent 呼び出し check」追加
- G2 / G3 / G4 ゲートで「該当工程の mandatory subagent 呼び出し履歴」を helix.db から audit、fail-close

## §4 受入条件

- helix/HELIX_CORE.md に §工程別 subagent 起動マップ が明文化 (Phase 1)
- cli/helix-agent コマンド 5 種が動作 (Phase 2)
- helix.db `subagent_invocations` table が稼働 (Phase 3)
- 既存 PLAN の subagent 呼び出し audit 完了 (Phase 4)
- helix doctor / G2-G4 で mandatory subagent lint が fail-close で動作 (Phase 5)

## §5 依存関係

- PLAN-075 (V-model) と独立進行可能 (相互依存なし)
- PLAN-077 (Sprint Plan 標準) と相互補完 (Sprint 内の subagent 呼び出しを mandatory 化)

## §6 Next Action

1. **今セッション**: Phase 1 (HELIX core 文書化) 完遂
2. **次セッション以降**: Phase 2-5 を段階的
