---
plan_id: PLAN-096
title: "PLAN-096: GitHub Actions + ブランチタイプ別パイプライン (V5 framework 要素 #15 + #16 実装)"
layer: cross
kind: impl
status: draft
size: M
drive: be
created: 2026-05-20
revised: "2026-05-20 (Round 3 反映: revised quote + agent_slots opus→pm-advisor + artifact_type 16 種正規化)"
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・CODEOWNERS 承認境界設計・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメントチェック・template 整合確認・draft 起票支援"
  - role: se
    slot_label: "SE — GitHub Actions workflow yml / commitlint.config.js 実装"
  - role: docs
    slot_label: "Docs — PR template / ISSUE_TEMPLATE / CODEOWNERS 起草"
  - role: tl-advisor
    slot_label: "TL adversarial check — CODEOWNERS 人間承認境界判断・G2/G3 凍結判定"
generates:
  - artifact_path: .github/workflows/feature.yml
    artifact_type: workflow_config
  - artifact_path: .github/workflows/poc.yml
    artifact_type: workflow_config
  - artifact_path: .github/workflows/refactor.yml
    artifact_type: workflow_config
  - artifact_path: .github/workflows/hotfix.yml
    artifact_type: workflow_config
  - artifact_path: .github/pull_request_template.md
    artifact_type: github_config
  - artifact_path: .github/ISSUE_TEMPLATE/bug_report.md
    artifact_type: github_config
  - artifact_path: .github/ISSUE_TEMPLATE/feature_request.md
    artifact_type: github_config
  - artifact_path: .github/ISSUE_TEMPLATE/failure_pattern.md
    artifact_type: github_config
  - artifact_path: .github/ISSUE_TEMPLATE/design_proposal.md
    artifact_type: github_config
  - artifact_path: .github/CODEOWNERS
    artifact_type: github_config
  - artifact_path: commitlint.config.js
    artifact_type: workflow_config
  - artifact_path: docs/adr/ADR-029-github-actions-branch-pipeline-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
    - PLAN-MM-001
  blocks: []
related_adr:
  - ADR-029-github-actions-branch-pipeline-decision
related_docs:
  - docs/plans/PLAN-MM-001-v5-framework-master-plan.md
  - docs/plans/PLAN-091-v5-framework-core.md
  - helix_github_workflow_rules.md
  - helix_improvement_plan_draft.md §Phase 1-3
  - CLAUDE.md §V5 framework 18 要素 #15 #16
---

# PLAN-096: GitHub Actions + ブランチタイプ別パイプライン

> **kind**: impl (Layer A 工程ルール + Layer C 連携自動化の接続部)
> **layer**: cross (L4-L7 実装・検証・デプロイ全域に影響)
> **drive**: be (CLI / hook / YAML 実装中心、UI なし)
> **前提**: PLAN-091 (V5 framework 本体語彙正本) 完遂後に着手する。
> **担当 V5 要素**: #15 GitHub 運用ルール統合、#16 helix_improvement_plan_draft.md Phase 1-3 統合

---

## §0. 本 PLAN の位置付け

V5 framework 18 要素のうち、**#15 GitHub 運用ルール統合** と **#16 helix_improvement Phase 1-3 統合** を担う。

`helix_github_workflow_rules.md` (root level draft、536 行) の Phase 1 詳細仕様を HELIX 工程体系 (ブランチ ↔ PLAN kind / HELIX フェーズ) に接続し、GitHub Actions 4 workflow として機械的に検証・記録・学習 DB 連携を自動化する設計を確定する。

本 PLAN は **Layer A (工程ルール整備) + Layer C (連携自動化) の境界に位置する**。PLAN-091 が定義した frontmatter 語彙 (kind / layer / drive) をブランチ命名規則へ射影し、PR / CI で機械的に確認する接続層を担う。

---

## §1. 目的

1. ブランチ命名規則 (6 タイプ) を HELIX kind マッピングと双方向対応させ、CI で機械検証可能にする
2. GitHub Actions 4 workflow (feature / poc / refactor / hotfix) をブランチタイプ別に実装し、HELIX Sprint 標準 8 ステップと対応させる
3. PR template + ISSUE_TEMPLATE 4 種を整備し、失敗文脈 (target_cluster_id / related_failures) の入力をワークフローに組み込む
4. Conventional Commits 強制 (commitlint) で commit log から PLAN-id / kind / impact を機械抽出可能にする
5. CODEOWNERS で人間承認境界を明示し、cli/ / docs/v2/ / helix/ / skills/ ごとのレビュー責任を確定する
6. Protected Branch (main) 設定でデプロイゲート (L7) に自動 Status Check を組み込む
7. 段階導入 P1→P2→P3 で既存 CI (ci.yml) とのデグレなく統合する

---

## §2. 背景と採用根拠

### 2.1 現状の問題

| 問題 | 具体的影響 |
|---|---|
| ブランチ命名規則が暗黙 | ブランチからの kind 判定不可、CI ルール分岐不能 |
| PR template 不在 | 失敗文脈 (target_cluster_id / related_failures) が PR に記録されない |
| CODEOWNERS 不在 | 人間承認境界が不明確、cli/ と docs/v2/ のレビュー責任が曖昧 |
| commitlint 不在 | PLAN-id / kind / scope が commit log から抽出不能 |
| ブランチタイプ別 CI 不在 | feature / poc / refactor / hotfix で評価基準が同一、適切な検証が走らない |
| 失敗ログ DB 連携不在 | CI 失敗が helix.db に記録されず、学習ループが閉じない |

### 2.2 helix_improvement_plan_draft.md との接続

`helix_improvement_plan_draft.md` の Phase 1 (基盤層) / Phase 2 (データ層) / Phase 3 (パイプライン層) を本 PLAN で実装起点として設計する。

| helix_improvement Phase | 本 PLAN 担当範囲 | 後段 PLAN |
|---|---|---|
| Phase 1 基盤層 | ブランチ規則 / PR template / CODEOWNERS / commitlint / workflow 骨格 | 本 PLAN §5-§11 |
| Phase 2 データ層 (DB) | workflow から helix.db 記録のフック設計 | PLAN-092/093 で DB schema |
| Phase 3 パイプライン層 | 4 workflow の評価ロジック + 失敗自動記録 | 本 PLAN §8 が骨格定義 |
| Phase 4 抽象化層 | エスカレーション機構 | PLAN-097 |

---

## §3. 業界 standard 参照 (Web 検索 3 query ベース、PLAN-087 ガードレール準拠)

| 参照 | Source URL | 本 PLAN での引用箇所 |
|---|---|---|
| Conventional Commits v1.0.0 specification | https://www.conventionalcommits.org/en/v1.0.0/ | §9 commitlint 設計の根拠。type/scope/subject/body/footer の構造規約 |
| commitlint official docs — @commitlint/config-conventional | https://commitlint.js.org/guides/getting-started.html | §9 commitlint.config.js の extends パターン + husky 統合方法 |
| GitHub branch protection rules — required status checks | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches | §10 Protected Branch 設定根拠。Required reviews / Require status checks to pass before merging |
| GitHub Actions — workflow syntax (on / jobs / steps) | https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions | §8 workflow yml 設計の正本。`on.pull_request.branches` / `on.push.branches` による trigger 設計 |
| CODEOWNERS syntax and examples | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners | §11 CODEOWNERS 設計の正本。パスパターン / チーム / 個人 ID 記法 |
| GitHub Actions — reusable workflows | https://docs.github.com/en/actions/sharing-automations/reusing-workflows | §8 共通 steps を reusable workflow に切り出す設計根拠 |
| semantic-release — conventional commit based versioning | https://github.com/semantic-release/semantic-release | §リリース戦略の補足。Conventional Commits から SemVer を自動判定する業界 standard |
| Atlassian — Branch per feature workflow | https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow | §5 feature ブランチ戦略の業界整合。短命ブランチ + main 保護の基本パターン |

---

## §4. V5 framework 担当要素

### 4.1 要素 #15: GitHub 運用ルール統合

`helix_github_workflow_rules.md` §1〜§12 を HELIX 工程 (L4 Sprint → L7 デプロイ) に接続する。

```
ブランチ命名規則 (#1)  →  HELIX kind マッピング (§6)
PR template (#2)       →  失敗文脈フィールド + PLAN-id 記録 (§7)
ラベル運用 (#3)        →  CI 自動付与 + helix.db learning 記録 (§8)
Conventional Commits (#4) → commitlint 強制 (§9)
マージ条件 (#5)        →  ブランチタイプ別 Status Check (§10)
CODEOWNERS (#6)        →  人間承認境界明示 (§11)
Status Check (#7)      →  workflow 必須 job 定義 (§8)
```

### 4.2 要素 #16: helix_improvement_plan_draft.md Phase 1-3 統合

本 PLAN は helix_improvement_plan_draft.md Phase 1 の実装起点。Phase 2 (DB) は PLAN-092/093 が担当し、Phase 3 (パイプライン評価ロジック詳細) は後段 sprint で追補する。

---

## §5. ブランチ命名規則 (helix_github_workflow_rules.md §1 準拠)

### 5.1 タイプ一覧と HELIX kind マッピング

| ブランチタイプ | 形式 | 例 | HELIX kind |
|---|---|---|---|
| `feature/` | `feature/<short-desc>` or `feature/<issue>-<short-desc>` | `feature/skill-curator` | impl / design / add-impl / add-design |
| `poc/` | `poc/<hypothesis-id>` | `poc/local-llm-evaluation` | poc |
| `refactor/` | `refactor/<scope>` | `refactor/12-failure-log-schema` | refactor / retrofit |
| `hotfix/` | `hotfix/<incident-id>` | `hotfix/db-connection-leak` | recovery |
| `docs/` | `docs/<scope>` | `docs/setup-guide-update` | add-design (docs 特化) |
| `chore/` | `chore/<scope>` | `chore/upgrade-sqlite` | impl (chore 分類) |

### 5.2 命名規約

- 小文字 + ハイフン区切り
- `<short-desc>` は 30 文字以内
- main / develop への直接 push は Protected Branch で禁止

### 5.3 ブランチタイプ ↔ HELIX フェーズ対応

| ブランチタイプ | 主な HELIX フェーズ | 典型 Sprint |
|---|---|---|
| feature | L3.5 機能設計 → L4 実装 → L4.5 結合 | Sprint .1〜.5 |
| poc | S0-S4 (Scrum) | PoC Sprint |
| refactor | L4 (機能変更なし) | Sprint .1〜.3 |
| hotfix | L4 (緊急) + L9 デプロイ検証 | 緊急 Sprint |
| docs | L2/L3 (設計 doc) | Doc Sprint |
| chore | L4 (依存更新 等) | Chore Sprint |

---

## §6. ブランチタイプ ↔ HELIX kind マッピング詳細

PLAN-091 §5.1 の kind 11 種とブランチタイプの対応。

```
feature/*
  └── impl          : 機能実装 (L4 Sprint)
  └── design        : 設計 doc 起票 (L1-L2)
  └── add-impl      : 既存実装への追加機能
  └── add-design    : 既存設計への追補

poc/*
  └── poc           : 仮説検証 (S0-S4)

refactor/*
  └── refactor      : 機能変更なし内部改善
  └── retrofit      : 既存規約への合わせ込み

hotfix/*
  └── recovery      : session 断絶・インシデント対応 (PLAN-098 連動)
  └── troubleshoot  : バグ解析・障害対応

docs/*
  └── add-design    : 設計 doc 追補 (docs ブランチの主要 kind)
  └── research      : 技術調査 doc

chore/*
  └── impl          : 依存更新・設定変更
```

**CI での kind 判定**: ブランチ名 prefix から `BRANCH_KIND` 環境変数を算出し、workflow 分岐に使用する。

---

## §7. PR template (.github/pull_request_template.md)

### 7.1 共通テンプレート構造

```markdown
## 種別
<!-- feature / poc / refactor / hotfix / docs / chore -->

## 関連 Issue
<!-- #番号、または「なし」 -->

## 変更内容
<!-- 何をどう変えたか。簡潔に。 -->

## PLAN 参照
<!-- 関連 PLAN-id (例: PLAN-096) -->
<!-- kind (例: impl) -->
<!-- ADR ref (例: ADR-029、なければ「なし」) -->

## 失敗・問題の文脈（該当する場合）
- target_cluster_id:
- related_failures:
- resolution_summary:

## 検証
- [ ] テスト実行済み (`helix test` または pytest / bats)
- [ ] ベンチマーク確認済み（refactor の場合）
- [ ] 既存挙動の保持確認（refactor の場合）
- [ ] ポストモーテム作成済み（hotfix の場合）
- [ ] helix doctor 全通過

## レビュー観点
<!-- レビュアーに特に見てほしい点があれば記載 -->
```

### 7.2 ブランチタイプ別追加フィールド

**feature の場合**

```markdown
## 設計成果物
<!-- D-API / D-DB / PLAN doc リンク -->

## テスト設計
<!-- 単体テスト設計 + 結合テスト設計 pair freeze 確認 -->
<!-- docs/v2/L4-test-design/ の対応 file -->
```

**refactor の場合**

```markdown
## ベンチマーク比較
| 項目 | 変更前 | 変更後 | 差分 |
|---|---|---|---|
| 実行時間 |  |  |  |
| メモリ使用量 |  |  |  |
| 複雑度 |  |  |  |

## 既存挙動の保持確認
<!-- 既存テスト全パス + degrade なしの確認 -->
```

**hotfix の場合**

```markdown
## インシデント概要
- 検知時刻：
- 影響範囲：
- 重要度：(critical / high / medium)

## 暫定対応 / 恒久対応
<!-- どちらか明示 -->

## ポストモーテム
<!-- 別途作成する場合は予定日 -->
<!-- recovery kind PLAN-id を記録 (PLAN-098 連動) -->
```

**poc の場合**

```markdown
## 検証仮説
<!-- Scrum backlog の hypothesis_id -->

## 検証方法
<!-- verify/*.sh スクリプト -->

## 期待される知見
<!-- confirmed / rejected / pivot のいずれかが出ること -->

## マージ予定
<!-- poc は原則マージしない。知見転写先 feature ブランチを記録 -->
```

---

## §8. GitHub Actions 4 workflow 設計

### 8.1 設計方針

- 既存 `.github/workflows/ci.yml` を**触らない** (デグレ禁止)
- 4 workflow は新規 file として追加のみ
- 共通 steps は reusable workflow (.github/workflows/reusable-helix-check.yml) に切り出す
- HELIX Sprint 標準 8 ステップ (PLAN-091 §8.2 impl template) と CI steps を対応させる

### 8.2 trigger 設計

```yaml
# 全 4 workflow 共通 trigger 設計
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
  push:
    branches:
      - 'feature/**'   # feature.yml
      - 'poc/**'        # poc.yml
      - 'refactor/**'  # refactor.yml
      - 'hotfix/**'    # hotfix.yml
```

各 workflow は `if: startsWith(github.head_ref, '<prefix>/')` でブランチタイプを自動判定する。

### 8.3 feature.yml (impl / design / add-impl / add-design kind)

**対応 HELIX フェーズ**: L4 Sprint lint + test + helix doctor + V-model 4 artifact 確認

```yaml
# .github/workflows/feature.yml (設計仕様)
name: Feature Branch Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: ['feature/**']

jobs:
  # Step 4 対応: 機械チェック (mandatory in sprint)
  lint:
    name: ci/lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Branch type check
        run: |
          echo "BRANCH_KIND=impl" >> $GITHUB_ENV
          # feature/* → impl/design/add-impl/add-design
      - name: Python syntax check
        run: find cli/lib -name "*.py" -exec python3 -m py_compile {} \;
      - name: Bash syntax check
        run: find cli -maxdepth 1 -name "helix*" -exec bash -n {} \;
      - name: Markdown lint
        run: |
          if command -v markdownlint &>/dev/null; then
            markdownlint docs/ skills/ --ignore docs/adr/index.md
          fi
      - name: YAML lint
        run: |
          if command -v yamllint &>/dev/null; then
            yamllint .github/workflows/ cli/
          fi

  # Step 5 対応: テスト起動 (mandatory in sprint)
  test:
    name: ci/test
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r cli/requirements.txt 2>/dev/null || true
      - name: Run pytest
        run: python3 -m pytest cli/lib/tests/ -q --tb=short
      - name: Run bats
        run: |
          if command -v bats &>/dev/null; then
            bats cli/tests/ --timing
          fi

  # V-model 4 artifact 確認 (feature 固有)
  vmodel-check:
    name: ci/vmodel-4artifact
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - name: helix doctor vmodel lint
        run: |
          if [ -f cli/helix ]; then
            cli/helix doctor --check vmodel_lint 2>/dev/null || echo "WARN: vmodel_lint not yet implemented"
          fi

  # helix doctor (mandatory)
  helix-doctor:
    name: ci/helix-doctor
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: helix doctor
        run: |
          if [ -f cli/helix ]; then
            cli/helix doctor 2>/dev/null || echo "WARN: helix doctor warnings present"
          fi

  # PLAN-091 V5 lint (feature は impl kind が主)
  plan-lint:
    name: ci/plan-lint-v5
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - name: helix plan lint --v5 (warn-only P1 mode)
        run: |
          if [ -f cli/helix ] && cli/helix plan lint --help 2>/dev/null | grep -q "\-\-v5"; then
            cli/helix plan lint --v5 --warn-only docs/plans/ 2>/dev/null || true
          fi
```

### 8.4 poc.yml (poc kind、Scrum S0-S4)

**対応 HELIX フェーズ**: Scrum verify スクリプト実行 + poc_validation_log 自動記録

```yaml
# .github/workflows/poc.yml (設計仕様)
name: PoC Branch Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: ['poc/**']

jobs:
  # Scrum verify スクリプト実行
  poc-verify:
    name: ci/poc-verify
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Scrum verify scripts
        run: |
          if ls verify/*.sh 2>/dev/null | head -1; then
            for script in verify/*.sh; do
              echo "=== Running: $script ==="
              bash "$script" || echo "WARN: $script failed"
            done
          else
            echo "No verify/*.sh scripts found — PoC 未実装 or スクリプトなし"
          fi

  # poc_validation_log 記録 (helix.db、PLAN-092 Phase 完成後に本格稼働)
  poc-log:
    name: ci/poc-log
    runs-on: ubuntu-latest
    needs: poc-verify
    steps:
      - uses: actions/checkout@v4
      - name: Record poc_validation_log
        run: |
          echo "PoC branch: $GITHUB_HEAD_REF"
          echo "PR: ${{ github.event.pull_request.number }}"
          # TODO: helix db insert poc_validation_log (PLAN-092 schema 完成後)
          echo "poc_validation_log insert is pending PLAN-092 schema"

  # poc はマージしない前提の確認
  poc-no-merge-check:
    name: ci/poc-no-merge-guard
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: PoC merge guard (warn-only)
        run: |
          echo "WARN: poc/* branch is designed to NOT merge into main."
          echo "Knowledge transfer should be done via a separate feature/* branch."
          # 実際にはマージを block しない (warn のみ)
          # P3 段階で fail-close 検討
```

### 8.5 refactor.yml (refactor / retrofit kind)

**対応 HELIX フェーズ**: refactor_degrade_pattern detector + ベンチマーク比較

```yaml
# .github/workflows/refactor.yml (設計仕様)
name: Refactor Branch Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: ['refactor/**']

jobs:
  # 全テスト (degrade 確認が必須)
  test-full:
    name: ci/test-full
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r cli/requirements.txt 2>/dev/null || true
      - name: Run full regression
        run: |
          python3 -m pytest cli/lib/tests/ -q --tb=short
          if command -v bats &>/dev/null; then
            bats cli/tests/ --timing
          fi

  # degrade pattern 検出
  degrade-check:
    name: ci/refactor-degrade-check
    runs-on: ubuntu-latest
    needs: test-full
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check for regression
        run: |
          # refactor_degrade_pattern: 変更前後のテスト数比較
          BEFORE=$(git stash && python3 -m pytest cli/lib/tests/ --co -q 2>/dev/null | grep "test session starts" -A999 | tail -1 || echo "0")
          git stash pop || true
          echo "Degrade check: test count comparison — see test-full job"

  # ベンチマーク比較 (refactor 固有)
  benchmark:
    name: ci/benchmark
    runs-on: ubuntu-latest
    needs: test-full
    steps:
      - uses: actions/checkout@v4
      - name: Run benchmark
        run: |
          echo "Benchmark: refactor branch $GITHUB_HEAD_REF"
          # TODO: helix benchmark run (PLAN-097 抽象化層完成後に本格化)
          echo "Benchmark step is pending PLAN-097 implementation"

  # refactor_degrade_pattern 自動記録
  refactor-log:
    name: ci/refactor-log
    runs-on: ubuntu-latest
    needs: [test-full, degrade-check]
    steps:
      - name: Record refactor result
        run: |
          echo "refactor_degrade_pattern insert is pending PLAN-092 schema"
```

### 8.6 hotfix.yml (recovery / troubleshoot kind)

**対応 HELIX フェーズ**: hotfix_incident_log 自動生成 + postmortem template 強制

```yaml
# .github/workflows/hotfix.yml (設計仕様)
name: Hotfix Branch Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: ['hotfix/**']

jobs:
  # 緊急対応テスト (最小範囲、高速)
  test-hotfix:
    name: ci/test-hotfix
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r cli/requirements.txt 2>/dev/null || true
      - name: Run hotfix-scope tests
        run: python3 -m pytest cli/lib/tests/ -q --tb=short -x

  # postmortem template チェック (hotfix 固有必須)
  postmortem-check:
    name: ci/postmortem-required
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check postmortem field in PR body
        env:
          PR_BODY: ${{ github.event.pull_request.body }}
        run: |
          if echo "$PR_BODY" | grep -q "ポストモーテム"; then
            echo "OK: postmortem field found in PR"
          else
            echo "WARN: hotfix PR should include postmortem. See PR template."
            # P1: warn-only, P3 以降: fail-close
          fi

  # hotfix_incident_log 自動生成
  incident-log:
    name: ci/incident-log
    runs-on: ubuntu-latest
    needs: test-hotfix
    steps:
      - name: Generate incident log entry
        run: |
          echo "hotfix_incident_log: branch=$GITHUB_HEAD_REF"
          echo "PR number: ${{ github.event.pull_request.number }}"
          # TODO: helix db insert hotfix_incident_log (PLAN-092 schema 完成後)
          echo "hotfix_incident_log insert is pending PLAN-092 schema"

  # recovery kind PLAN 存在確認 (PLAN-098 連動)
  recovery-plan-check:
    name: ci/recovery-plan-linked
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check recovery kind PLAN existence
        env:
          PR_BODY: ${{ github.event.pull_request.body }}
        run: |
          if echo "$PR_BODY" | grep -qE "PLAN-[0-9]+"; then
            PLAN_ID=$(echo "$PR_BODY" | grep -oE "PLAN-[0-9]+" | head -1)
            echo "OK: PLAN reference found: $PLAN_ID"
          else
            echo "WARN: hotfix PR should reference a recovery kind PLAN (PLAN-098)"
          fi
```

---

## §9. Conventional Commits 強制 (commitlint)

### 9.1 commitlint.config.js 設計

```javascript
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // type: HELIX 許可リスト (helix_github_workflow_rules.md §4 準拠)
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'chore', 'docs', 'test', 'refactor', 'revert', 'perf', 'style'],
    ],
    // scope: PLAN-NNN または HELIX ドメイン名
    'scope-enum': [
      1,  // warn (P1 mode: 完全 enum 強制は P3 以降)
      'always',
      ['skill', 'workflow', 'harness', 'db', 'pipeline', 'agent', 'ci', 'hook', 'plan', 'adr', 'template'],
    ],
    // subject: 50 文字以内
    'subject-max-length': [2, 'always', 50],
    // body: 失敗文脈 / 意思決定 / 影響を記述推奨 (warn-only)
    'body-max-line-length': [1, 'always', 100],
  },
};
```

### 9.2 HELIX 固有 commit 例

```bash
# feature → impl kind
feat(plan): add PLAN-091 v5 framework core frontmatter validation

Add plan_validator.py with kind/layer/drive enum enforcement.
Refs: PLAN-091

# hotfix → recovery kind
fix(db): prevent connection leak on pipeline failure

Closes: #103
Recovery: PLAN-NNN-recovery

# refactor → refactor kind
refactor(pipeline): split feature pipeline into stages

No behavior change. Splits monolithic pipeline runner into
discrete stage handlers.
```

### 9.3 scope と PLAN kind の対応

| Conventional Commits scope | HELIX ドメイン | 対応 PLAN kind |
|---|---|---|
| `plan` | PLAN doc | design / impl / add-design |
| `adr` | ADR snapshot | design |
| `hook` | Claude Code hook | impl |
| `db` | helix.db schema | impl / refactor |
| `ci` | GitHub Actions | impl |
| `skill` | skills/ | add-design / research |
| `workflow` | workflow/ | impl / add-impl |
| `harness` | CLI harness | impl / refactor |
| `pipeline` | CI pipeline | impl |

---

## §10. Protected Branch 設定 (main)

### 10.1 Branch Protection rules

GitHub repository 設定 → Branches → Add rule → `main`:

| 設定項目 | 値 | 根拠 |
|---|---|---|
| Require pull request reviews before merging | ✅ ON | レビュー必須 |
| Required approving reviews | 1 (refactor は 2) | helix_github_workflow_rules.md §5 |
| Dismiss stale pull request approvals when new commits are pushed | ✅ ON | レビュー後 commit 再要求 |
| Require review from CODEOWNERS | ✅ ON (§11 参照) | 人間承認境界 |
| Do not allow bypassing the above settings | ✅ ON | 管理者バイパス禁止 |
| Require status checks to pass before merging | ✅ ON | CI 全通過必須 |
| Require branches to be up to date before merging | ✅ ON | merge 前 rebase 強制 |
| Do not allow force pushes | ✅ ON | 履歴改ざん禁止 |
| Do not allow deletions | ✅ ON | ブランチ削除制限 |

### 10.2 必須 Status Check 一覧

| Check 名 | 内容 | 必須対象 |
|---|---|---|
| `ci/lint` | Python / Bash syntax + markdownlint | 全タイプ |
| `ci/test` | pytest + bats | 全タイプ |
| `ci/helix-doctor` | helix doctor warnings | 全タイプ |
| `ci/plan-lint-v5` | helix plan lint --v5 | 全タイプ |
| `ci/vmodel-4artifact` | V-model 4 artifact 確認 | feature / refactor |
| `ci/benchmark` | ベンチマーク測定 | refactor のみ |
| `ci/poc-verify` | Scrum verify スクリプト | poc のみ |
| `ci/postmortem-required` | postmortem フィールド確認 | hotfix のみ |
| `ci/recovery-plan-linked` | recovery kind PLAN 参照確認 | hotfix のみ |

---

## §11. CODEOWNERS (.github/CODEOWNERS)

### 11.1 責任領域設計

**tl-advisor Round 1 指摘反映**: CODEOWNERS 設定は repo 運用に影響する人間承認境界の決定であるため、チーム構成が定まっていない初期は **個人 GitHub ID での代用** を採用する。

```gitignore
# .github/CODEOWNERS (設計仕様)

# CLI / ハーネス層 (最重要: 破壊変更リスク高)
/cli/              @RetryYN

# docs/v2/ V2 設計文書 (L2 大局判断を含む)
/docs/v2/          @RetryYN

# HELIX core policy (全エージェントが参照)
/helix/            @RetryYN

# skills/ (107 スキル、SKILL_MAP.md 含む)
/skills/           @RetryYN

# .claude/ (Claude Code hook / agent、fail-close hook 含む)
/.claude/          @RetryYN

# GitHub Actions workflow (CI/CD 変更は高影響)
/.github/workflows/ @RetryYN

# docs/plans/ (PLAN doc 群、V5 frontmatter 含む)
/docs/plans/       @RetryYN

# docs/adr/ (ADR snapshot 群、大局判断記録)
/docs/adr/         @RetryYN

# 全体フォールバック
*                  @RetryYN
```

### 11.2 人間承認境界の明示 (tl-advisor 指摘反映)

以下のパスへの変更は **必ず PM (Opus) が CODEOWNERS 承認** をすること:

| パス | 承認理由 | エスカレーション条件 |
|---|---|---|
| /.claude/hooks/ | fail-close hook 変更は全エージェント挙動に影響 | hook exit code 変更 |
| /helix/HELIX_CORE.md | 全フェーズ・ゲート定義の正本 | phase / gate 定義変更 |
| /docs/v2/L2-MASTER.md | V2 基本設計の正本 | ADR / PLAN 正本変更 |
| /cli/config/models.yaml | モデル割当の真実ファイル | role → model 変更 |
| /.github/CODEOWNERS | 承認境界自体の変更 | 常に PM 承認 |

---

## §12. 段階導入 3 Phase

`helix_github_workflow_rules.md` §12 の推奨順序を HELIX V5 context に合わせた段階導入計画。

### Phase 1 (P1): template + ブランチ規則 doc 化 (最初に完遂)

**実施内容**:
- ブランチ命名規則の doc 化 (本 PLAN §5)
- `.github/pull_request_template.md` 作成
- `.github/ISSUE_TEMPLATE/` 4 種作成
- `commitlint.config.js` 作成 (warn-only mode)
- Protected Branch 基本設定 (レビュー必須のみ)

**CI 挙動**: warn-only (既存 CI デグレなし)

**DoD**: 本 PLAN 起票 + 上記 file 存在 + docs/v2/ との整合確認

### Phase 2 (P2): workflow yml 実装 (P1 完遂後)

**実施内容**:
- `.github/workflows/feature.yml` 実装
- `.github/workflows/poc.yml` 実装
- `.github/workflows/refactor.yml` 実装
- `.github/workflows/hotfix.yml` 実装
- Status Check の必須化 (Branch Protection 設定)

**CI 挙動**: 各ブランチタイプで対応 workflow が発火、fail は warn-only

**DoD**: 4 workflow が対応ブランチで発火確認 + 既存 ci.yml とのデグレなし確認

### Phase 3 (P3): CODEOWNERS + branch protection enforce (P2 完遂後)

**実施内容**:
- `.github/CODEOWNERS` 本格設定
- Branch Protection の全 Status Check 必須化
- commitlint scope enum 強制 (warn → fail-close)
- helix.db 連携 (PLAN-092 schema 完成後)

**CI 挙動**: fail-close (Status Check 未通過 → マージ不可)

**DoD**: main への直接 push 禁止確認 + 全 Status Check 必須化確認 + CODEOWNERS レビュー動作確認

---

## §13. DoD (Definition of Done)

### 起票 DoD (本 PLAN 完遂判定)

1. **frontmatter 完備**: plan_id / title / kind / layer / drive / status / agent_slots / generates / dependencies / related_adr が全て記述されている
2. **§3 業界 standard 参照**: Web 検索 3 query 以上のベースで Sources URL が記述されている
3. **§5 ブランチ命名規則 + §6 HELIX kind マッピング**: 6 タイプ × kind 対応表が存在する
4. **§7 PR template 設計**: 共通テンプレート + 4 ブランチタイプ別追加フィールドが記述されている
5. **§8 4 workflow 設計**: feature / poc / refactor / hotfix の yaml 設計仕様が記述されている
6. **§9 commitlint 設計**: commitlint.config.js の設計と HELIX scope マッピングが記述されている
7. **§10 Protected Branch 設計**: rules + 必須 Status Check 一覧が記述されている
8. **§11 CODEOWNERS 設計**: 人間承認境界 + パス別責任者が記述されている (tl-advisor 指摘反映)
9. **§12 段階導入 P1-P3**: 3 Phase の実施内容 + CI 挙動 + DoD が記述されている
10. **ADR-029 同時起票**: docs/adr/ADR-029-github-actions-branch-pipeline-decision.md が存在し、双方向 reference が確立されている
11. **デグレなし確認**: 既存 `.github/workflows/ci.yml` を編集していない

### 実装 DoD (別 session)

- `.github/workflows/feature.yml` が feature/* ブランチの PR で発火する
- `.github/workflows/poc.yml` が poc/* ブランチの PR で発火する
- `.github/workflows/refactor.yml` が refactor/* ブランチの PR で発火する
- `.github/workflows/hotfix.yml` が hotfix/* ブランチの PR で発火する
- `commitlint.config.js` が commit message を検証する
- PR template がすべての PR に自動適用される
- CODEOWNERS が所定のパスで承認を要求する
- 既存 `ci.yml` の全 job が引き続き PASS する

---

## §14. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-096-github-actions-branch-pipeline.md |
| ② 実装コード | 未着手 (P2 別 session) | .github/workflows/*.yml / commitlint.config.js 等 |
| ③ テスト設計 | 未起票 (P2 別 session) | docs/v2/L4-test-design/PLAN-096-test-design.md (予定) |
| ④ テストコード | 未着手 (P2 別 session) | cli/lib/tests/test_github_workflow.py 等 (予定) |

**双方向 reference**:
- 本 PLAN → ADR-029: `related_adr: [ADR-029-github-actions-branch-pipeline-decision]`
- ADR-029 → 本 PLAN: `Related: PLAN-096 (本設計 tree の実装 PLAN)`
- 本 PLAN → generates: 各 artifact_path に listed

---

## §15. 関連

### 15.1 前段 PLAN (requires)
- [PLAN-091](PLAN-091-v5-framework-core.md): frontmatter 語彙正本 (kind / layer / drive / agent_slots / generates)
- [PLAN-MM-001](PLAN-MM-001-v5-framework-master-plan.md): 親設計

### 15.2 後段 PLAN (blocks: なし、本 PLAN は他 PLAN の前提ではない)
- PLAN-097 (抽象化層 + エスカレーション): helix_improvement Phase 4 を引き継ぐ
- PLAN-098 (recovery kind 正規化): hotfix → recovery kind 連動

### 15.3 関連 ADR
- [ADR-029](../adr/ADR-029-github-actions-branch-pipeline-decision.md): 本 PLAN の L2 大局判断 snapshot

### 15.4 素材 file (touch 禁止)
- `helix_github_workflow_rules.md` (root level draft、本 PLAN 起票後も触らない)
- `helix_improvement_plan_draft.md` (root level draft、同上)
- `.github/workflows/ci.yml` (既存 CI、デグレ禁止)
