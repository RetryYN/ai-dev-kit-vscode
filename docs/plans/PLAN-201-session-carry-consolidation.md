---
plan_id: PLAN-201
title: "PLAN-201: 2026-05-23 session carry consolidation (リカバリープラン)"
kind: recovery
layer: cross
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: S
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — carry 内容精査・実装 PLAN マッピング・priority 確認"
  - role: pm-advisor
    slot_label: "PM adversarial check — carry scope 過不足・次 session 着手順序"
generates:
  - artifact_path: docs/v2/retrospectives/carry-list-2026-05-23.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-100
  blocks: []
---

# PLAN-201: 2026-05-23 session carry consolidation (リカバリープラン)

## 概要

本 PLAN は **V5 framework 17 番要素「リカバリープラン kind (recovery)」** の適用事例として、2026-05-23 session で発生した carry items を集約し、次 session の実装着手順序を明確化するリカバリープランである。

本 session では PLAN-102〜201 (100 PLAN bundle) を起票したが、全 PLAN が `status: draft` であり実装は未着手。本 PLAN は draft carry を整理し、**実装着手可能な状態への橋渡し**を担う。

## 背景 (事象記録)

### 本 session の実施内容

- **Wave 1**: PLAN-102〜110 (9 PLAN) 起票 — test infra / catalog / hook 系
- **Wave 2**: PLAN-111〜130 (20 PLAN) 起票 — Codex harness / GitHub Actions / 観測系
- **Wave 3**: PLAN-131〜150 (20 PLAN) 起票 — DB / lock / retry / migration 系
- **Wave 4**: PLAN-151〜170 (20 PLAN) 起票 — skill / agent / UX 系
- **Wave 5**: PLAN-171〜201 (31 PLAN) 起票 — 高度化 / version / retrospective / carry 系

### 残 carry の性質

100 PLAN の全起票が `status: draft` であることは**設計上の意図**であり、本 session の目的は「起票による knowledge 永続化」にある。ただし以下の carry は**前 session から持ち越された未解決 item**であり、次 session での優先対応が必要。

## carry 集約表

| carry ID | 内容 | 優先度 | 想定 PLAN | 依存 |
|---|---|---|---|---|
| C-01 | pytest-xdist 並列化 + helix-db.lock test fixture isolation | P0 | PLAN-102 相当 | なし |
| C-02 | gate test flake 1 件 root cause 調査 (test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references) | P0 | PLAN-104 相当 | なし |
| C-03 | PLAN-101 session_id fallback の実環境 dogfooding 確認 | P1 | PLAN-101 | なし |
| C-04 | cli/lib/agent_mandatory.py datetime.utcnow() deprecation sweep (Python 3.13+ removal) | P1 | 独立修正 | なし |
| C-05 | Codex SUMMARY 集約問題: 委譲 Codex の改善案セクション消失 | P2 | PLAN-187 相当 | なし |
| C-06 | PLAN-199 Sprint .1 着手 (helix/VERSION 初期化) | P2 | PLAN-199 | ADR-059 起票後 |

### 前 session (2026-05-22) からの持ち越し carry

| carry ID | 内容 | 現状 | 対応 PLAN |
|---|---|---|---|
| C-07 | merge_settings.py _is_helix_hook() 判定 bug | 修正済 (e3c658d) | PLAN-101 完遂で close |
| C-08 | ADR frontmatter 追加 + auto-regenerate hook 修正 | 修正済 (e3c658d) | close |
| C-09 | L1-REQUIREMENTS FR-V5-10〜18 placeholder 確定 | FR-V5-10〜18 audit 完遂 → carry 不要 close | close |

## 認識訂正履歴 (本 session の重要訂正)

本 session では PLAN 起票 bulk 作業が主体であったため、設計上の認識訂正は最小限。ただし以下を記録:

1. **PLAN-200 の role**: 「100 PLAN 達成記念」は祝祭的側面を持つが、PLAN 体系上は `kind=retrofit` + retrospective doc 生成として位置づける (pure celebration PLAN は anti-pattern)
2. **PLAN-201 の位置づけ**: 本 session では新規 carry 発生はほぼなく、前 session からの持ち越し carry の整理が主目的。V5 17 番要素の適用実証として意義を持つ

## 次 session 着手手順

### 最短経路 (短縮版 A 案)

```
1. C-02: gate test flake root cause 調査 (30min)
   → helix test bats のみ再現確認 → fail 条件特定 → fix PR
2. C-01: pytest-xdist 並列化 PLAN 起票 + Sprint .1 着手
   → conftest.py fixture isolation design → Codex se 委譲
3. C-03: PLAN-101 dogfooding 確認 (10min)
   → 新規設計 doc Write で session_id fallback が機能することを確認
4. PLAN-199 Sprint .1: helix/VERSION 作成 + helix-version show (別 session)
```

### V5 継続進行 (B 案)

```
1. PLAN-091 Sprint .3 (未完遂分) 確認
2. PLAN-092 結合テスト設計の双方向 trace 整合
3. PLAN-093 drift 検出 CLI 実装
```

### 着手方針決定基準

- ユーザー時間枠が短い (1-2h): A 案 C-01/C-02 の P0 のみ
- ユーザー時間枠が長い (4h+): A 案完了後に B 案へ
- carry 指定がある場合: 指定 carry を最優先

## 再発防止 (session 終了前チェックリスト)

本 PLAN は V5 17 番要素「リカバリープラン kind」の適用である。次 session 終了前に以下を確認:

1. carry == 0 (または時間枠満了)
2. リカバリープラン (kind=recovery) 起票済 (本 PLAN がその役割を担う)
3. handover updated
4. memory feedback 永続化済

→ 4 項目満たさず turn 終了は禁止 ([[feedback_dont_stop_with_carry_remaining]])

## 受入条件

- 本 PLAN が `docs/plans/PLAN-201-session-carry-consolidation.md` に存在する
- carry 集約表が存在し C-01〜C-06 の P0/P1/P2 分類が明確である
- 次 session 着手手順 A/B 案が記載されている
- plan_validator PASS

## context 再構築方法 (次 session 向け)

次 session 開始時、最短の context 再構築手順:

```bash
# 1. 本 session carry 確認
cat docs/plans/PLAN-201-session-carry-consolidation.md

# 2. memory 確認
cat ~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/MEMORY.md | head -50

# 3. 最新 git log 確認
git log --oneline -10

# 4. P0 carry から着手
python3 cli/lib/plan_validator.py docs/plans/PLAN-201-session-carry-consolidation.md
```
