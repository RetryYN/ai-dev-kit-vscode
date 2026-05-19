# ADR-029: GitHub Actions + ブランチタイプ別パイプライン採用判断

## Status

Proposed (2026-05-20)

> proposed (2026-05-20) — PLAN-096 と同時起票。Deciders による承認後 Accepted に遷移。

## Deciders

- PM (Opus)
- PO (yoshiyuki0907yn@gmail.com)
- TL review: tl-advisor (gpt-5.5 high) — CODEOWNERS 人間承認境界 指摘反映済み

## Related

- PLAN-096-github-actions-branch-pipeline (本 ADR の実装 PLAN)
- PLAN-MM-001-v5-framework-master-plan (親設計)
- PLAN-091-v5-framework-core (frontmatter 語彙正本)
- PLAN-097-abstraction-layer-escalation (抽象化層 Curator 連携、後段)
- PLAN-098-recovery-plan-kind-normalization (hotfix → recovery kind 連動)
- ADR-025-v5-framework-core-decision (V5 framework 本体 ADR)

---

## 業界 standard 参照 (Web 検索 3 query ベース、PLAN-087 ガードレール準拠)

| 参照 | Source URL | 採用判断との関連 |
|---|---|---|
| Conventional Commits v1.0.0 specification | https://www.conventionalcommits.org/en/v1.0.0/ | commit log から PLAN kind / scope を機械抽出可能にするための規約選定根拠 |
| GitHub branch protection rules | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches | Protected Branch による Status Check 強制の公式仕様根拠 |
| GitHub Actions workflow syntax | https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions | 4 workflow の trigger / jobs / steps 設計の公式仕様根拠 |
| CODEOWNERS syntax | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners | 人間承認境界設計の公式仕様根拠 |
| Atlassian Feature Branch Workflow | https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow | ブランチタイプ別評価基準分離の業界 standard 根拠 |

---

## Context

HELIX V2 運用において、以下の問題が累積していた:

1. **ブランチ命名規則が暗黙**: feature / poc / refactor / hotfix の区別が CI に反映されず、ブランチタイプ別の評価基準が適用できない
2. **PR template 不在**: 失敗文脈 (target_cluster_id / related_failures) が PR に記録されない。helix.db の失敗学習ループが閉じない
3. **CODEOWNERS 不在**: cli/ / docs/v2/ / helix/ / skills/ の人間承認境界が不明確
4. **commitlint 不在**: PLAN-id / kind / scope が commit log から抽出不能
5. **ブランチタイプ別 CI 不在**: feature / poc / refactor / hotfix で同一 CI が走り、適切な検証が行われない
6. **失敗ログ DB 連携不在**: CI 失敗が helix.db に記録されず、PLAN-093 Curator への学習データが蓄積されない

これらの問題は `helix_github_workflow_rules.md` (root level draft) と `helix_improvement_plan_draft.md` Phase 1-3 で課題として認識されていたが、HELIX 工程 (kind / layer / HELIX フェーズ) との接続が設計されていなかった。

本 ADR は、**ブランチタイプ ↔ HELIX kind マッピング + GitHub Actions 4 workflow + commitlint + CODEOWNERS + Protected Branch** の組み合わせを採用する大局判断を凍結する。

---

## Decision

以下の設計を採用する:

### 1. ブランチ命名規則 + HELIX kind マッピング (V5 要素 #15)

6 ブランチタイプと PLAN-091 §5.1 の kind 11 種を双方向対応させる。CI でブランチ prefix から `BRANCH_KIND` を算出し、ブランチタイプ別 workflow を分岐する。

```
feature/* → impl / design / add-impl / add-design
poc/*     → poc
refactor/* → refactor / retrofit
hotfix/*  → recovery / troubleshoot
docs/*    → add-design / research
chore/*   → impl
```

### 2. GitHub Actions 4 workflow 採用

既存 `.github/workflows/ci.yml` に加えて、以下 4 workflow を新規追加する (既存 ci.yml は触らない):

| workflow | ブランチタイプ | 主要 job |
|---|---|---|
| `feature.yml` | feature/* | lint / test / vmodel-check / helix-doctor / plan-lint |
| `poc.yml` | poc/* | poc-verify / poc-log / poc-no-merge-check |
| `refactor.yml` | refactor/* | test-full / degrade-check / benchmark / refactor-log |
| `hotfix.yml` | hotfix/* | test-hotfix / postmortem-check / incident-log / recovery-plan-check |

### 3. Conventional Commits (commitlint) 採用

`commitlint.config.js` で `@commitlint/config-conventional` を extend し、以下を HELIX 固有拡張:
- `type-enum`: feat / fix / chore / docs / test / refactor / revert / perf / style (helix_github_workflow_rules.md §4 準拠)
- `scope-enum`: skill / workflow / harness / db / pipeline / agent / ci / hook / plan / adr / template (warn-only、P3 以降 fail-close)

### 4. CODEOWNERS 採用 (人間承認境界明示)

チーム構成が定まっていない初期は個人 GitHub ID (`@RetryYN`) での代用を採用。以下のパスで CODEOWNERS 承認必須:
- `/cli/` / `/docs/v2/` / `/helix/` / `/skills/` / `/.claude/` / `/.github/workflows/`

**tl-advisor 指摘反映**: CODEOWNERS は repo 運用に影響する人間承認境界の決定であり、チーム名を仮置きしたまま強制すると承認遅延が発生するリスクがある。初期は個人 ID で最小構成から始め、チーム構成確定後に拡張する。

### 5. Protected Branch (main) 強制

| 設定 | 値 |
|---|---|
| Require PR reviews | ✅ (refactor は 2 名) |
| Dismiss stale reviews | ✅ |
| Require CODEOWNERS review | ✅ |
| Require status checks | ✅ |
| Require branches up to date | ✅ |
| Force push 禁止 | ✅ |
| Branch deletion 禁止 | ✅ |

### 6. 段階導入 P1→P2→P3

- P1: template + ブランチ規則 doc 化 (warn-only)
- P2: workflow yml 実装 + Status Check 必須化
- P3: CODEOWNERS + fail-close + helix.db 連携

---

## Consequences

### Positive

1. **PR 規約強制**: PR template で失敗文脈 (target_cluster_id / related_failures) が記録され、helix.db 学習ループが閉じる
2. **ブランチタイプ別 CI 最適化**: feature は V-model 4 artifact チェック、poc は Scrum verify、refactor はベンチマーク比較、hotfix は postmortem 強制
3. **失敗 → 学習接続**: CI job が helix.db (PLAN-092 schema 完成後) と連携し、失敗パターンが PLAN-093 Curator に自動供給される
4. **commitlint で PLAN-id 追跡**: commit log から PLAN-NNN が機械抽出可能になり、PLAN → 実装 → commit の trace が確立される
5. **人間承認境界の明文化**: CODEOWNERS で cli/ / helix/ / .claude/ 等の高影響パスに PM 承認が必須化される

### Negative

1. **既存 PR 影響**: P2 実装後、CODEOWNERS が既存 open PR のレビュープロセスを変更する可能性がある。段階導入 P1→P2→P3 で影響を緩和する
2. **CODEOWNERS 承認遅延リスク**: 個人 ID での代用は PM 不在時にレビューがブロックされるリスクがある。緊急 hotfix 時は bypass 手順を別途定義する
3. **commitlint 学習コスト**: Conventional Commits に不慣れな場合、commit 時に lint エラーが発生する。P1 は warn-only で開始し、P3 で fail-close に移行する

---

## Alternatives

### A: 手動 PR 運用継続 (棄却)

**理由**: 失敗文脈の記録が手動依存になり、helix.db 学習ループが閉じない。PLAN-093 Curator の自動供給データがゼロになる。PR 品質のばらつきが継続する。

### B: GitLab CI (棄却)

**理由**: HELIX repo は GitHub 上に存在する。GitLab CI への移行は repo 移行コストが高く、現状の GitHub Actions / branch protection との統合メリットが失われる。

### C: 本 Decision 採用 (採択)

GitHub Actions 4 workflow + Conventional Commits + CODEOWNERS + Protected Branch の組み合わせは、GitHub 公式機能のみを使用し、外部 SaaS 依存なしで HELIX 工程と接続できる。段階導入 P1→P2→P3 で既存 CI デグレを防ぎながら品質保証機構を積み上げられる。

---

## Implementation Plan

PLAN-096 (本 ADR の実装 PLAN) の 3 Phase で実施:

- **P1** (次 session): template + ブランチ規則 + commitlint (warn-only) → file 作成のみ
- **P2** (別 session): 4 workflow 実装 + Status Check 必須化
- **P3** (PLAN-092 schema 完成後): helix.db 連携 + fail-close 強制

PLAN-097 (抽象化層 + エスカレーション) との連携: hotfix.yml の `incident-log` job が Phase 4 の抽象化エスカレーション機構と接続する設計とする。
