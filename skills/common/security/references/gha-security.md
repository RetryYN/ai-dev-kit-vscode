> 目的: GitHub Actions workflow 固有のセキュリティ観点 (supply chain / template injection / permissions / cache poisoning / secrets handling) を zizmor 30+ ルールベースで HELIX 文脈に落とし込む reference。skills/common/security/SKILL.md は OWASP / 認証認可 / アプリケーション層を扱い、本 reference は CI pipeline (Workflow yaml) 層を扱う。L2 設計 / G2/G4 ゲート / pre-push hook 連携。

# GitHub Actions Security (HELIX 統合版)

GitHub Actions ベースの CI/CD で頻発するセキュリティ脆弱性を、zizmor (https://github.com/zizmorcore/zizmor、MIT) の 30+ ルールベースで体系化する。

出典:
- [zizmor 公式](https://github.com/zizmorcore/zizmor) (MIT, stars 5300+, 最終 commit 2026-05-16)
- [zizmor docs](https://docs.zizmor.sh/)
- [Grafana Labs 実運用事例](https://grafana.com/blog/how-to-detect-vulnerable-github-actions-at-scale-with-zizmor/)
- [OWASP Top 10 CI/CD Security Risks](https://owasp.org/www-project-top-10-ci-cd-security-risks/)

---

## 0. 適用範囲

| 対象 | 内容 |
|---|---|
| **対象 file** | `.github/workflows/*.yml`, `.github/workflows/*.yaml`, composite/reusable action の `action.yml` |
| **対象 layer** | CI pipeline (Workflow yaml 層)。アプリケーション code 層は `SKILL.md` の OWASP 系 reference を参照 |
| **対象 phase** | L2 (設計凍結時に CI 方針確定) / L4 (workflow 変更時) / G2/G4/G6 ゲート / pre-push hook |
| **検査タイミング** | (1) pre-push hook ローカル実行 (workflow 変更時、fail-open) / (2) CI ジョブ `security.yml` で fail-close / (3) PR review 時の人間 review |

---

## 1. 主要 5 ルール (zizmor 30+ ルールから抜粋)

### R-1: `template-injection` (危険度: critical)

#### 何を検出するか

`${{ ... }}` 内で **攻撃者制御可能なコンテキスト** (例: `github.event.pull_request.title`, `github.event.issue.body`, `github.head_ref`) を直接展開し、shell command として実行されるパターン。

#### 攻撃 example

```yaml
# ❌ 脆弱
- name: Greet
  run: echo "Hello, ${{ github.event.pull_request.title }}!"
```

PR title に `"; rm -rf /; #` を入れられると CI runner 上で任意コード実行。

#### 修正パターン

```yaml
# ✅ 安全 (env 経由で quote)
- name: Greet
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "Hello, $PR_TITLE!"
```

#### HELIX 連携

- `skills/common/security/SKILL.md` §3 XSS 対策と同根 (untrusted input の sanitize)
- L2 設計時に「外部入力を ${{ }} で展開する箇所がないか」確認、ある場合 env 経由必須

---

### R-2: `dangerous-triggers` (危険度: critical)

#### 何を検出するか

`pull_request_target` / `workflow_run` トリガーの **悪用可能パターン**。これらは PR の base branch のコードを実行するため、攻撃者 PR が `secrets.*` にアクセスできる場合がある。

#### 攻撃 example

```yaml
# ❌ 脆弱
on:
  pull_request_target:
    types: [opened]

jobs:
  build:
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}   # ← attacker fork code を checkout
      - run: ./untrusted-script.sh                          # ← secrets 込みで実行
```

#### 修正パターン

- `pull_request_target` を使わず `pull_request` を使う (secrets なし)
- secrets が必要なら、**コードを checkout せずメタデータのみ操作** する
- どうしても fork code が必要なら、明示的に承認された label を確認してから実行

#### HELIX 連携

- HELIX 現状: `pull_request_target` / `workflow_run` は使用していない (良)
- 将来 fork 受付の workflow が必要になった場合、本ルール準拠で設計
- L1/L2 設計時に「外部 fork からの PR を CI で扱うか」を明示

---

### R-3: `unpinned-uses` (危険度: high)

#### 何を検出するか

`uses: actions/checkout@v4` のような **mutable tag 参照**。タグは作者が同名で再 push 可能なため、supply chain 攻撃のリスクがある。

#### 攻撃 example

```yaml
# ❌ mutable (悪意ある作者が v4 タグを差し替えると CI 即時汚染)
- uses: actions/checkout@v4
```

#### 修正パターン

```yaml
# ✅ SHA pin (immutable) + version コメント (zizmor ref-version-mismatch 対応)
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11   # v4.1.1
```

#### HELIX 連携

- ADR-036 D3 で `.github/dependabot.yml` actions ecosystem を有効化、週次で SHA 更新 PR 自動生成
- 例外: `actions/checkout` のような GitHub 公式 actions は SHA pin **必須** (HELIX 全 workflow に適用)
- 内部の reusable workflow (`uses: ./.github/workflows/...`) は SHA pin 不要

#### 検出コマンド

```bash
# 全 workflow の unpinned uses を検出
zizmor --select unpinned-uses .github/workflows/

# 個別 workflow
zizmor --select unpinned-uses .github/workflows/ci.yml
```

---

### R-4: `excessive-permissions` / `undocumented-permissions` (危険度: high)

#### 何を検出するか

- `excessive-permissions`: workflow / job レベルで GITHUB_TOKEN に **必要以上の権限** を付与
- `undocumented-permissions`: `permissions:` 宣言が**完全不在** (default の広範な権限が付与される)

#### 攻撃 example

```yaml
# ❌ permissions 不在 (default で contents: write 等を含む広範な権限)
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<SHA>
      - run: ./untrusted-script.sh   # ← 攻撃成功時に commit / release / package 操作可能
```

#### 修正パターン

```yaml
# ✅ 最小権限原則 (workflow + job 両レベルで明示)
permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read   # job level でさらに絞る
    steps:
      - uses: actions/checkout@<SHA>
      - run: ./script.sh
```

#### HELIX 連携

- 本 ADR-036 + PLAN-222 Sprint .2 で **全 6 workflow に permissions 宣言追加済** (2026-05-23)
- `security.yml` の zizmor scan ジョブのみ `security-events: write` を job level で付与 (SARIF upload 用)
- 新規 workflow を作るときは **必ず workflow level で `permissions: contents: read`** から始める

---

### R-5: `artipacked` (危険度: medium-high)

#### 何を検出するか

artifact (`actions/upload-artifact`) 経由で **意図せず secrets / credentials が漏洩** するパターン。具体的には `~/.ssh/`, `.git/config`, `.aws/credentials` を含むディレクトリを artifact upload している。

#### 攻撃 example

```yaml
# ❌ .git/config に persisted token が含まれる場合
- uses: actions/checkout@<SHA>
  with:
    persist-credentials: true   # default
- uses: actions/upload-artifact@<SHA>
  with:
    path: .                     # ← .git/config (token 含む) が artifact に
```

#### 修正パターン

```yaml
# ✅ persist-credentials を明示 false + artifact path を絞る
- uses: actions/checkout@<SHA>
  with:
    persist-credentials: false
- uses: actions/upload-artifact@<SHA>
  with:
    path: dist/                 # ← 必要なディレクトリのみ
```

#### HELIX 連携

- HELIX 現状: artifact upload は使用していない (良)
- 将来 artifact upload が必要になった場合、本ルール準拠で設計
- secrets を環境変数経由で扱う場合は `env:` で明示し、log に出力しないよう注意

---

## 2. False positive 管理 (ADR-036 D4)

意図的に zizmor 警告を抑制する場合は `# zizmor:ignore` コメント運用。

### 行単位

```yaml
- uses: actions/checkout@<SHA>
  with:
    persist-credentials: true   # zizmor:ignore[artipacked] reason=git push back to PR branch / owner=@team-sec / re-evaluate=when migrate to PAT
```

### 必須 metadata

- **reason**: 1-2 行、人間が読んで判断可能な内容
- **owner**: 責任者 (@username) または issue/ADR/PLAN reference
- **期限** または **再評価条件**: `expires=2026-12-31` または `re-evaluate-when=migrate-to-oidc`

### 機械検査 (将来実装)

`cli/lib/zizmor_ignore_lint.py` が CI で全 `zizmor:ignore` コメントを scan し、metadata 揃いを fail-close 検査する (PLAN-222 AC-5、別 PLAN 候補)。

---

## 3. HELIX gate / hook 連携

### G2 (設計凍結ゲート)

- L2 で workflow 変更を含む PLAN の場合、zizmor ローカル実行で 0 警告を確認
- `permissions:` 宣言の有無、`pull_request_target` の使用有無を design doc に明記

### G4 (実装凍結ゲート)

- `mandatory in sprint`: workflow 変更を含む Sprint で `zizmor .github/workflows/` 0 警告
- pre-push hook + CI ジョブの両方で fail-close 確認

### G6 (RC 判定ゲート)

- 統合 PR の最終 review 時、zizmor 警告 0 を SARIF (GitHub Security tab) で確認

### pre-push hook (`scripts/git-hooks/pre-push`)

- `.github/workflows/*.yml` 変更を含む commit に対して zizmor ローカル実行
- zizmor 未インストール時は warning のみ (fail-open)、CI で fail-close 担保
- `HELIX_DRY_RUN_HOOK=1` で警告のみ通す (既存 hook 方針と整合)

### CI ジョブ (`.github/workflows/security.yml`)

- PR ごとに走り SARIF 出力 + GitHub Security tab upload
- `permissions: contents: read` + job level で `security-events: write` (SARIF upload 用)
- 警告検出時は PR を block (fail-close)

---

## 4. 補完ツール (ADR-036 D1)

zizmor は **GitHub Actions workflow security の主検査**。補完ツールとの併用で深層防御:

| 役割 | ツール | 採用状況 |
|---|---|---|
| Workflow security (主検査) | zizmor | ADR-036 で採用 |
| Workflow syntax / shell lint | actionlint | 任意 (将来別 ADR で評価) |
| OSS health / supply chain 姿勢 | OpenSSF Scorecard | 任意 (将来別 ADR で評価) |
| Runtime セキュリティ (network egress 制限等) | StepSecurity Harden-Runner | 任意 (本番運用時に再評価) |
| pre-commit integration | pre-commit + zizmor | 検討中 (Sprint .4 統合候補) |

---

## 5. 関連 skill / ADR / PLAN

### 関連 skill

- `skills/common/security/SKILL.md`: アプリケーション層セキュリティ (OWASP / 認証認可 / 機密情報、本 reference の親 skill)
- `skills/agent-skills/security-and-hardening/SKILL.md`: AI agent 視点でのセキュリティ実装 hardening
- `skills/tools/ai-coding/SKILL.md`: CI/CD エージェント統合パターン (本 reference の zizmor 統合は実例)

### 関連 ADR

- ADR-036 (本 reference の trigger ADR、zizmor 採用 + 3 段統合)
- ADR-009 (hook strategy、pre-push hook 統合方針の base)

### 関連 PLAN

- PLAN-222 (本 reference の作成 PLAN、Sprint .3 成果物)

---

## 6. 検出コマンド early reference

```bash
# 全ルール scan
zizmor .github/workflows/

# 特定ルールのみ
zizmor --select unpinned-uses,excessive-permissions .github/workflows/

# SARIF 出力 (CI 用)
zizmor --format sarif .github/workflows/ > zizmor-results.sarif

# pedantic mode (false positive 含む詳細 scan)
zizmor --pedantic .github/workflows/

# 特定 file のみ
zizmor .github/workflows/ci.yml
```

詳細: https://docs.zizmor.sh/usage/ 参照。

---

## License

Original tool: [zizmor](https://github.com/zizmorcore/zizmor) — MIT License。
本 reference は zizmor の公式 docs を引用しつつ HELIX 文脈に統合した解説で、HELIX repository license に準拠する。
