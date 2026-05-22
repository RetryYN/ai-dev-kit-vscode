---
plan_id: PLAN-183
title: "PLAN-183: helix GitHub Actions CI/CD pipeline"
kind: impl
layer: L4
drive: be
status: draft
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl-advisor
    slot_label: "TL — CI/CD pipeline 設計方針 adversarial check (workflow 分割 / job 依存 / secrets 管理)"
  - role: se
    slot_label: "SE — .github/workflows/helix-ci.yml 実装・matrix job 設計・cache 設定"
  - role: devops
    slot_label: "DevOps — GitHub Actions runner 設定・secret 管理・badge 統合"
  - role: qa
    slot_label: "QA — pytest core5 / bats smoke の CI 実行確認・flaky test 検出戦略"
  - role: pmo-sonnet
    slot_label: "PMO — plan_validator / helix doctor 統合整合・G4 ゲートとの連携確認"
generates:
  - artifact_path: .github/workflows/helix-ci.yml
    artifact_type: config
  - artifact_path: .github/workflows/helix-pr.yml
    artifact_type: config
  - artifact_path: docs/commands/ci-cd.md
    artifact_type: doc_update
dependencies:
  parent: PLAN-MM-001
  requires: []
  blocks: []
related_plans:
  - PLAN-096
  - PLAN-077
related_adr:
  - ADR-029 (GitHub Actions + ブランチタイプ別パイプライン、L2 snapshot)
related_docs:
  - docs/plans/PLAN-096-github-workflow-integration.md
  - docs/plans/PLAN-077-sprint-plan-standard-structure.md
  - cli/lib/plan_validator.py
  - cli/helix-doctor
acceptance_criteria:
  - "push trigger で plan_validator 全 PLAN PASS・helix doctor 0 fail・pytest core5 全 PASS・bats smoke 全 PASS が自動実行される"
  - "PR trigger で上記 + docs/plans/ diff がある場合に plan_validator の差分 PLAN のみ追加検証される"
  - "CI 結果が PR に status check として反映され、fail 時は merge block される"
  - ".github/workflows/helix-ci.yml の yaml lint が actionlint で PASS する"
  - "helix doctor の warn 件数が前回 run より増加した場合 CI が WARN コメントを PR に投稿する"
  - "bats smoke は cli/lib/tests/ + verify/ の全 bats ファイルを対象にする"
  - "pytest は cli/lib/tests/ を対象に --tb=short -q で実行し、結果をサマリーとして PR コメントに投稿する"
---

# PLAN-183: helix GitHub Actions CI/CD pipeline

## L2 凍結 (ADR snapshot)

本 PLAN tree は GitHub Actions の新規統合を含む。CI/CD pipeline の設計方針 (job 分割 / trigger / cache / secrets 管理) は既存 ADR-029 (GitHub Actions + ブランチタイプ別パイプライン) で L2 大局判断が凍結済み。新規の大局判断を含まないため、追加 ADR snapshot は不要。

| ADR | 凍結対象 | Status |
|---|---|---|
| ADR-029 | GitHub Actions ブランチタイプ別パイプライン設計 | Draft |

双方向 trace:
- 本 PLAN → ADR-029: frontmatter `related_adr` + 本 section
- ADR-029 → 本 PLAN: `related_plans` に PLAN-183 を記載

---

## 0. 背景

本 session (2026-05-23) の push 6 commit で pre-push hook による機械チェックが機能していたが、push 後の自動検証 (plan_validator / helix doctor / pytest / bats) は手動実行に依存している。開発サイクルが加速する中、PR マージ前の品質ゲートが自動化されていないリスクがある。

PLAN-096 (GitHub Actions 統合) が ADR-029 で L2 凍結済みのため、本 PLAN はその L4 実装フェーズとして着手する。

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| GitHub Actions workflow syntax | docs.github.com/actions/using-workflows/workflow-syntax | yaml 構造・trigger・job 定義の根拠 |
| actionlint | github.com/rhysd/actionlint | workflow yaml の静的 lint ツール |
| pytest-github-actions-annotate-failures | pypi.org/project/pytest-github-actions-annotate-failures | pytest fail を PR annotation に変換 |
| actions/cache | github.com/actions/cache | Python venv / pip キャッシュ戦略 |

## 2. 設計方針

### 2.1 pipeline 構成

```
helix-ci.yml (push trigger)
  job: validate-plans        plan_validator 全 PLAN
  job: helix-doctor          helix doctor 0 fail チェック
  job: pytest-core5          pytest cli/lib/tests/ -q
  job: bats-smoke            bats verify/ cli/lib/tests/
  ※ 各 job は独立実行 (並列)、前段依存なし

helix-pr.yml (PR trigger)
  job: validate-diff-plans   変更 PLAN のみ plan_validator
  job: pytest-core5          同上
  job: bats-smoke            同上
  job: doctor-delta          helix doctor warn 件数比較 + PR コメント
```

### 2.2 trigger 設計

```yaml
# helix-ci.yml
on:
  push:
    branches: [main]
  workflow_dispatch: {}

# helix-pr.yml
on:
  pull_request:
    branches: [main]
```

### 2.3 cache 戦略

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### 2.4 plan_validator 差分実行 (PR trigger)

```bash
# PR trigger 時: 変更された PLAN のみ検証
git diff --name-only origin/${{ github.base_ref }} -- 'docs/plans/PLAN-*.md' \
  | xargs -I{} python3 cli/lib/plan_validator.py {}
```

### 2.5 helix doctor delta コメント

PR trigger で `helix doctor` を実行し、warn 件数が base ブランチより増加した場合に GitHub API 経由で PR コメントを投稿する。

```bash
# doctor delta check
BASE_WARN=$(git stash && helix doctor --json | jq '.warnings | length')
HEAD_WARN=$(git stash pop && helix doctor --json | jq '.warnings | length')
if [ "$HEAD_WARN" -gt "$BASE_WARN" ]; then
  echo "WARN: helix doctor warnings increased ($BASE_WARN -> $HEAD_WARN)"
fi
```

## 3. job 詳細

### 3.1 validate-plans

```yaml
validate-plans:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.11" }
    - run: pip install pyyaml
    - name: Run plan_validator
      run: |
        fail=0
        for f in docs/plans/PLAN-*.md; do
          python3 cli/lib/plan_validator.py "$f" 2>&1 || fail=1
        done
        exit $fail
```

### 3.2 pytest-core5

```yaml
pytest-core5:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.11" }
    - uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    - run: pip install -r requirements.txt
    - name: Run pytest core5
      run: python3 -m pytest cli/lib/tests/ -q --tb=short
```

### 3.3 bats-smoke

```yaml
bats-smoke:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Install bats
      run: sudo apt-get install -y bats
    - name: Run bats smoke
      run: |
        bats verify/ --timing
        bats cli/lib/tests/*.bats --timing || true
```

## 4. L4 実装 Sprint 計画

### Sprint .1: helix-ci.yml skeleton + validate-plans job

- Entry: ADR-029 確認 + 既存 pre-push hook との重複確認
- 実装: `.github/workflows/helix-ci.yml` push trigger + validate-plans job
- チェック: actionlint PASS / yaml lint PASS
- Exit: push で plan_validator 全 PLAN が CI 上で実行される

### Sprint .2: pytest-core5 + bats-smoke job

- 実装: pytest-core5 job (cache 付き) + bats-smoke job
- 検証: pytest 全 PASS / bats 全 PASS を CI 上で確認
- Exit: helix-ci.yml の 4 job が全て green になる

### Sprint .3: helix-pr.yml + doctor-delta コメント

- 実装: `.github/workflows/helix-pr.yml` PR trigger + validate-diff-plans + doctor-delta
- GitHub API 経由の PR コメント投稿ロジック
- Exit: PR 作成時に差分 PLAN 検証 + doctor delta コメントが動作する

### Sprint .4: status check 設定 + docs 整合

- GitHub repo で required status checks 設定 (validate-plans / pytest-core5 / bats-smoke)
- `docs/commands/ci-cd.md` 新規作成 (CI 利用ガイド)
- Exit: fail 時に PR merge が block される + docs 整合確認

### Sprint .5: レビュー + ドキュメント整合

- セルフレビュー + pmo-sonnet review
- docs/commands/index.md に ci-cd.md を追加
- actionlint 最終確認

## 5. リスクと緩和策

| リスク | 影響 | 緩和 |
|---|---|---|
| pytest が CI 上で timeout (full sweep ~9分) | CI 常時タイムアウト | pytest core5 scope を cli/lib/tests/ に限定、xdist 並列化は PLAN 別途起票 |
| bats が github runner 環境で動作しない | bats-smoke 全 fail | `|| true` で non-blocking にし、WARN 扱いで CI 継続 |
| helix doctor delta が base ブランチ取得失敗 | delta check 誤動作 | fetch-depth: 0 で checkout + エラー時は skip (fail-open) |
| plan_validator が新規 PLAN 起票直後に CI block | 開発フロー阻害 | PR trigger のみ merge block、push trigger は notify-only (warn-only mode) |

## 6. DoD (Definition of Done)

- acceptance_criteria 全件 PASS
- `.github/workflows/helix-ci.yml` と `.github/workflows/helix-pr.yml` が actionlint PASS
- PR merge 前に validate-plans / pytest-core5 / bats-smoke が required status check として機能する
- `docs/commands/ci-cd.md` に CI 利用ガイドが記載済み
- helix doctor warn 増加なし
