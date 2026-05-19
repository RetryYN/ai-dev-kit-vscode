---
plan_id: PLAN-077
title: "PLAN-077: Sprint Plan 標準化 framework (機械チェック / テスト / レビュー mandatory in sprint)"
status: draft
size: L
drive: be
created: 2026-05-17
owner: PM
phases: L4
gates: G3, G4
related_plans:
  - PLAN-075 (V-model 設計⇔テスト対応、同時並行)
  - PLAN-076 (subagent 工程マッピング、同時並行)
trigger: |
  ユーザー指摘 2026-05-17:
  「あとはテストやチェック系も工程内に組み込む。実装時にはスプリントプランを毎回組むじゃない？
   これも一定ルール化したほうがいい。レビューフローは毎回組み込みとかテストの起動も
   コードの機械チェックとかも。」

  現状 Sprint Plan が毎回フリーハンドで組まれ、機械チェック / テスト起動 / レビュー
  が暗黙になっている。PLAN-074 でも Sprint .2 ~ .5 の Codex 委譲 prompt は毎回別構造、
  py_compile / 全回帰 / レビュー手順が体系化されていない。

  subagent 2 分類 (PLAN-076) と同じ思想で、Sprint 内ステップを mandatory / on-demand
  に分けて framework 化する。
acceptance:
  - Sprint Plan 標準 8 ステップを HELIX_CORE.md / SKILL_MAP.md に明文化
  - mandatory in sprint (py_compile / 該当 test / 全回帰 / セルフレビュー) を強制化
  - on-demand in sprint (security audit / perf / coverage report) を選択化
  - cli/helix-sprint に標準ステップ自動実行 (--auto-check) を追加
  - helix doctor / G4 で「Sprint 内 mandatory ステップ完了 audit」自動 lint
---

# PLAN-077: Sprint Plan 標準化 framework

## §1 背景

### 現状の問題

L4 実装中の Sprint Plan が毎回フリーハンド。PLAN-074 では Sprint .2-.5 の Codex 委譲 prompt が毎回別構造で、以下が暗黙:

- いつ py_compile を回すか
- いつ全回帰 (helix test) を回すか
- いつレビュー (セルフ / pmo-sonnet / tl-advisor) を入れるか
- どの DoD checklist を通過させるか
- 機械チェック (lint / shellcheck / yamllint / markdownlint) のタイミング

各 Sprint が独立して進むため、品質の再現性が確保されない。Codex 委譲 prompt も毎回違うので、結果の品質ばらつきが大きい (Sprint .4 audit で review_only_drift が再発した一因)。

## §2 Sprint Plan 標準 8 ステップ

```
Sprint .X 標準構造:

Step 1: Entry 条件確認            (前 Sprint 完遂 / dependency)
Step 2: 実装着手前                (helix code find / pmo-project-scout)
Step 3: 実装                      (Codex 委譲 or Opus 直接)
Step 4: ★機械チェック (mandatory in sprint):
        - py_compile (Python) / bash -n (bash)
        - shellcheck / markdownlint / yamllint (該当 file kind 別)
        - helix code stats (coverage、該当範囲)
        - helix doctor (drift / lint / lock)
Step 5: ★テスト起動 (mandatory in sprint):
        - 単体テスト (該当範囲、即時)
        - 結合テスト (該当範囲)
        - 全回帰 (Sprint Exit 前、helix test)
Step 6: ★レビュー (mandatory in sprint):
        - セルフレビュー
        - pmo-sonnet review (G2/G4 時)
        - tl-advisor (任意 / on-demand、adversarial check)
Step 7: commit + carry note
Step 8: Exit 条件確認 (DoD)
```

Step 4-6 が **mandatory in sprint**、Sprint Exit 前に必ず通る。

### 2 分類整理 (subagent と同じ思想)

| ステップ性格 | mandatory in sprint | on-demand in sprint |
|---|---|---|
| **対象** | py_compile / 該当 test / 全回帰 / セルフレビュー / pmo-sonnet review (G2/G4) | security audit / perf test / coverage report / tl-advisor |
| **発火** | Sprint Exit 前に必ず | 必要時のみ |
| **lint** | 不在 → carry note 強制 | なし |
| **CLI** | `helix sprint complete --auto-check` で一括 | `helix sprint addon <check>` |
| **記録** | helix.db に sprint_checks table で記録 | 任意 |

## §3 5 Phase 構成

### Phase 1 — HELIX core に Sprint Plan 標準明文化 (size: M)

- helix/HELIX_CORE.md §Sprint Plan 標準構造 (8 ステップ) 新規
- skills/SKILL_MAP.md L4 説明に「Sprint Exit 前 mandatory チェック」明示
- CLAUDE.md (project + global) Sprint 運用ルール

### Phase 2 — cli/helix-sprint 拡張 (size: M)

- `helix sprint plan --plan-id PLAN-XXX --sprint .X` (標準テンプレート生成)
- `helix sprint check --sprint .X` (mandatory ステップ自動実行)
- `helix sprint complete --sprint .X --auto-check` (mandatory 全通過 + DoD 確認)
- `helix sprint audit --plan-id PLAN-XXX` (Sprint 全件 mandatory 通過履歴)

### Phase 3 — helix.db `sprint_checks` table (size: S)

```sql
CREATE TABLE sprint_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    sprint TEXT NOT NULL,
    check_kind TEXT NOT NULL,  -- py_compile, shellcheck, pytest, regression, review, etc.
    check_type TEXT NOT NULL CHECK(check_type IN ('mandatory', 'on-demand')),
    executed_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL CHECK(status IN ('pass', 'fail', 'skip')),
    skip_reason TEXT,
    details TEXT
);
```

### Phase 4 — Codex 委譲 prompt テンプレート標準化 (size: M)

- `cli/templates/prompts/sprint-implementation.md` (Codex 委譲標準 prompt)
- mandatory ステップ (py_compile / test / SUMMARY) を prompt に組み込み
- 委譲 prompt がフリーハンドにならず、Sprint Plan 標準と整合

### Phase 5 — helix doctor / G4 自動 lint (size: M)

- helix doctor に「Sprint mandatory check 完遂 audit」追加
- G4 ゲートで「PLAN 全 Sprint で mandatory check 通過」を helix.db から audit、fail-close

## §4 受入条件

- helix/HELIX_CORE.md に Sprint 標準 8 ステップが明文化 (Phase 1)
- cli/helix-sprint に check / complete / audit コマンド (Phase 2)
- helix.db `sprint_checks` table (Phase 3)
- Codex 委譲 prompt テンプレート (Phase 4)
- helix doctor / G4 で fail-close 動作 (Phase 5)

## §5 依存関係

- PLAN-075 (V-model) と独立進行可能
- PLAN-076 (subagent) と相互補完 (Sprint 内の subagent 呼び出しを mandatory 化)

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

- Sprint 定義済完了条件: Scrum.org は DoD をインクリメントの品質基準としてコミットメント化しており、Scrumb team/組織が文脈に合わせて標準化することを明示している（Scrum Guide と合わせて解釈）。
  - [Scrum.org: What is a Definition of Done?](https://www.scrum.org/resources/what-definition-done)
  - [Atlassian: Definition of Done in Agile](https://www.atlassian.com/agile/project-management/definition-of-done)
- CI 前提の pre-merge/commit ガード: pre-commit はコミット前後でフックを通す標準ツール群であり、pre-commit.ci は CI 経由で運用し、Husky は `.husky` 配下の `pre-commit`/`pre-push` 管理を前提とする Git hook フレームワークとして広く採用される。
  - [pre-commit](https://pre-commit.com/)
  - [pre-commit.ci](https://pre-commit.ci/)
  - [Husky: How to](https://typicode.github.io/husky/how-to.html)
  - [Lefthook configuration](https://lefthook.dev/configuration/fail_on_changes.html)
- Incremental sprint 実行の短周期運用: DORA はトランクベース開発を高頻度マージ＋fast CI 前提の実践として提示し、継続的デリバリー改善の主要標準として扱っている。
  - [DORA: Trunk-based development](https://dora.dev/capabilities/trunk-based-development/)
  - [DORA: Continuous delivery](https://dora.dev/capabilities/continuous-delivery/)

### 参照要件への反映

- PLAN-077 の Sprint step では、レビュー / テスト / 機械チェックを「Sprint Exit前必須」とする現行ルールを維持し、DoD 明確化を組み込みガードに接続する。
- pre-commit/pre-merge チェックは、段階的に「変更受入時の CI 条件」として Step 4（機械チェック）・Step 5（テスト起動）に寄与する運用で再利用する。
- マイクロスプリント運用は、PLAN-077 の「小さな反復＋高速フィードバック」原則を前提に継続的リリース性能改善の観点で定期的に再評価する。

## 変更履歴

- 2026-05-19 (W5c-11): `業界 standard 参照 (Web 検索 retrofit 2026-05-19)` を追加し、Sprint DoD / pre-commit / Husky・Lefthook / Continuous Delivery-TBD の業界標準参照を PLAN-077 に格納。

## §6 Next Action

1. **今セッション**: Phase 1 (HELIX core 文書化) 完遂
2. **次セッション以降**: Phase 2-5 を段階的
