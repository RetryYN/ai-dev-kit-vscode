---
adr_id: ADR-036
title: zizmor (GitHub Actions security audit) 採用 + 3 段統合 (CI enforcement + local advisory + knowledge reference)
status: Accepted with conditions
date: 2026-05-23
deciders:
  - PM (Opus)
  - PMO-tech-fork (Sonnet、agent ae182efe で評価レポート受領)
  - TL-advisor (gpt-5.5 high、本 ADR adversarial check 実施、changes_required 判定)
related_plans:
  - parent: null
  - L2_snapshot_of: PLAN-222
supersedes: []
superseded_by: []
---

# ADR-036: zizmor (GitHub Actions security audit) 採用 + 3 段統合

## Status

**Accepted with conditions** — 2026-05-23

tl-advisor adversarial check (2026-05-23) で P1 指摘 4 件・P2 指摘 3 件・P3 指摘 1 件を受領。条件解消後に **Accepted** へ格上げする。条件は本文末「Acceptance Conditions」section 参照。

## Context

HELIX (ai-dev-kit-vscode) は AI エージェント (Claude Code + Codex CLI) ベースの開発フレームワークで、GitHub Actions ベースの CI/CD を運用している。既存 6 workflow (`ci.yml` / `commitlint.yml` / `feature.yml` / `hotfix.yml` / `poc.yml` / `refactor.yml`) には以下の技術的負債が存在する:

1. **actions が SHA 未固定**: 全 workflow で `actions/checkout@v4` / `actions/setup-python@v5` がタグ参照 (v4 / v5)。タグはミュータブルなため、悪意ある作者または compromised maintainer が同名タグを新 commit に差し替えると HELIX CI が即時に汚染される (supply chain 攻撃)
2. **permissions 宣言不在**: workflow / job レベルで `permissions:` が宣言されておらず GITHUB_TOKEN のデフォルト権限 (write 含む) が広範に付与される (Principle of Least Privilege 違反)
3. **GitHub Actions 固有のセキュリティ観点が HELIX skill に欠落**: `skills/common/security/` は OWASP / 認証認可 / 機密情報スキャンを扱うが CI pipeline security 専用 reference は不在

これらに対応するため、GitHub Actions に特化した静的セキュリティ解析ツールを評価した。

### 評価対象 OSS

| ツール | 対象 | カバー範囲 | license |
|---|---|---|---|
| **zizmor** | GitHub Actions workflows | 30+ ルール (template-injection / dangerous-triggers / unpinned-uses / excessive-permissions / artipacked / cache-poisoning 等) | MIT |
| CodeQL | アプリケーション code | 多言語、Workflow も部分対応だが limited | GitHub 専用 |
| Trivy | container / IaC / 依存関係 | container image / IaC / SBOM。Workflow は対象外 | Apache 2.0 |
| Snyk | container / 依存関係 | 商用 freemium、Workflow は対象外 | Proprietary |
| actionlint | Workflow lint | yaml syntax / shell lint / matrix。security ルールは限定的 | MIT |

CI pipeline security (Workflow yaml レベルの脆弱性検出) を主目的とするツールは **zizmor が唯一の有力選択肢**。他は対象レイヤーが異なる (アプリ / container / 依存) もしくは security より lint 寄り (actionlint)。

### zizmor 基本評価 (pmo-tech-fork agent ae182efe、2026-05-23 実施)

| 軸 | 値 | 評価 |
|---|---|---|
| license | MIT | 商用転用・再配布・改変ともに制限なし |
| stars | 5,300+ (2026-05 時点) | GitHub Actions security 分野で最有力 |
| 最終 commit | 2026-05-16 (v1.25.2) | 本評価の 1 週間前。非常に活発 |
| 言語 | Rust 98.2% | pip / brew / cargo / Docker / バイナリ 全方式対応 |
| 保守者 | William Woodruff (Trail of Bits 出身) / zizmorcore org / Grafana Labs スポンサー | 組織化・資金化済みで持続リスク低 |
| 既知の HELIX 既存資産との重複 | なし (security skill は OWASP / アプリ層、zizmor は CI pipeline 層) | 完全補完 |

### WebSearch 履歴 (PLAN-087 ガード遵守、5 query)

- https://github.com/zizmorcore/zizmor (公式 repository、MIT)
- https://docs.zizmor.sh/ (公式 docs、ルール体系)
- https://docs.zizmor.sh/integrations/ (zizmor-action / pre-commit / Docker 等の統合パターン)
- https://grafana.com/blog/how-to-detect-vulnerable-github-actions-at-scale-with-zizmor/ (Grafana Labs での大規模実運用事例)
- https://nedbatchelder.com/blog/202410/github_action_security_zizmor (独立評価)
- https://opensourcesecurity.io/2025/2025-05-securing-github-actions-william-woodruff/ (保守者 interview、継続性確認)

## Decision

### D1: zizmor を採用する (主検査) + 補完ツール併用

GitHub Actions workflow security audit の **主検査** ツールとして zizmor を採用する。代替案 (CodeQL / Trivy / Snyk / actionlint) は対象レイヤーが異なるか機能が限定的であり、zizmor の代替にはならない。

ただし「唯一の有力選択肢」と断定せず、**補完ツールとの併用** で深層防御を構築する:

| 役割 | ツール | 採用 |
|---|---|---|
| Workflow security (主検査) | **zizmor** | 本 ADR で採用 |
| Workflow syntax / shell lint | actionlint | 任意 (将来別 ADR で評価) |
| OSS health / supply chain 姿勢 | OpenSSF Scorecard | 任意 (将来別 ADR で評価) |
| Runtime セキュリティ (network egress 制限等) | StepSecurity Harden-Runner | 任意 (本番運用時に再評価) |
| pre-commit integration | pre-commit + zizmor | Sprint .4 と統合検討 |
| 依存更新 (Renovate vs Dependabot) | Renovate (代替候補) | D3 で比較 |

### D2: 3 段統合方式

3 つの統合ポイントに同時導入する。1 つに絞らない理由は、各統合ポイントが異なるフィードバック loop と用途を持つため:

1. **CI ジョブ** (`.github/workflows/security.yml`、PR ごとに走り SARIF 出力 + GitHub Security tab upload): 統合層、本番ブロック gate
2. **pre-push hook** (`scripts/git-hooks/pre-push`、workflow 変更時にローカル実行): 開発者の手元フィードバック loop、CI 待ちなし
3. **skill reference** (`skills/common/security/references/gha-security.md`、HELIX skill 体系内ドキュメント): エージェント (Claude Code / Codex) と人間の参照資料

CI ジョブ単独では開発者フィードバックが遅い (PR push 後)。pre-push hook 単独ではバイパス可 (`--no-verify`)。skill reference 単独では機械強制力なし。**3 段で深層防御 (defense in depth) を構築する**。

### D3: SHA 固定維持戦略 = Dependabot actions ecosystem (Renovate と比較した上で採用)

actions を SHA 固定すると、security patch 反映の更新追跡コストが発生する。Dependabot の `actions` ecosystem を `.github/dependabot.yml` で有効化し、週次で SHA 更新 PR を自動生成する運用とする。手動更新は drift 発生のリスクが高いため不採用。

`# v4` のような version コメントを SHA の隣に付け、zizmor の `ref-version-mismatch` ルールにも対応する。

#### Renovate との比較 (tl-advisor 指摘 P1)

| 観点 | Dependabot | Renovate |
|---|---|---|
| GitHub native 統合 | 標準搭載、設定 yaml のみ | GitHub App インストール必要 |
| Pin-digest support | actions ecosystem で対応 | 同等以上 |
| Grouping / batching | 限定的 (recent では類似 PR グループ化が一部対応) | 強力 (group rules で複数 actions を 1 PR に束ねる) |
| Automerge | 限定的 (auto-approve だけ可、auto-merge は別 workflow 必要) | ネイティブで条件 automerge |
| 設定の learning curve | 低 | 中-高 (renovate.json + presets) |
| HELIX 規模での運用負担 | 6 workflow × 3 actions = 18 行 / 週次 PR 最大 5 で十分 | overkill 気味 |

**判断**: HELIX 規模では Dependabot で十分。Renovate の grouping / automerge の優位性は HELIX が actions 数百規模になったときに再評価する (現状 HELIX の actions は 6 workflow × 3 actions = ~18 個)。

**Acceptance condition**: Dependabot 初回 PR (zizmor 採用直後の week 1) が期待通り SHA pin + version コメント付きで生成されることを実 workflow fixture で確認 (PLAN-222 Sprint .2 完了条件)。

### D4: false positive 管理方針 + 機械検査強制

意図的な permissions 省略・特殊な workflow パターンに対する zizmor 警告は以下の優先順位で抑制する:

1. **行単位**: 該当行に `# zizmor:ignore[rule-name]` コメントを追加 (理由は必ずコメントで明記)
2. **ファイル単位**: `.github/workflows/<file>.yml` 内で局所的に ignore したい場合は `# zizmor:ignore[rule-name]` を該当 block に
3. **プロジェクト単位**: `zizmor.yml` 設定ファイルで全 workflow に対する ignore (**最小限**、運用上 1-2 件以内に抑える)

`# zizmor:ignore` には必ず以下を併記する (理由なき ignore は禁止):

- **理由** (1-2 行、人間が読んで判断可能な内容)
- **owner** (責任者または issue/ADR/PLAN reference)
- **期限** または **再評価条件** (例: `expires=2026-12-31` または `re-evaluate-when=migrate-to-oidc`)

#### 機械検査 (tl-advisor 指摘 P2 対応)

人間規律だけでは劣化するため、`rg 'zizmor:ignore'` ベースの機械検査を CI に追加する (Acceptance Condition で必須):

```bash
# 全 zizmor:ignore コメントが理由 + owner/期限を持つか検査
rg -A2 'zizmor:ignore' .github/workflows/ | \
  python3 cli/lib/zizmor_ignore_lint.py --strict
```

`cli/lib/zizmor_ignore_lint.py` は別 PLAN で実装 (PLAN-222 carry または別 PLAN 起票)。

### D5: pre-push hook 動作 = zizmor 未インストール時は warning + push 通過

開発者全員が `pip install zizmor` を実施しているとは限らないため、pre-push hook は zizmor 未インストール時 warning のみで push を block しない (fail-open)。CI ジョブ (案 B) で fail-close を担保する。

```bash
if command -v zizmor >/dev/null 2>&1; then
    zizmor .github/workflows/ || exit 1
else
    echo "[pre-push] zizmor not installed, skipping local scan (CI will catch)"
fi
```

### D6: zizmor-action 自体も SHA 固定

`uses: zizmorcore/zizmor-action@<SHA>` で SHA 固定。Dependabot で更新追跡。

## Consequences

### Positive

- HELIX 自身の workflow が SHA 固定 + permissions 明示で supply chain 攻撃耐性向上
- 開発者の手元 + CI の二段でフィードバック loop 確立
- skill reference により AI エージェントが workflow 生成時にセキュリティ観点を内蔵化
- HELIX 既存 skill (`skills/common/security/`) との重複ゼロで完全補完

### Negative

- Dependabot による週次 PR 増加 (1-3 PR/week 想定)
- 開発者環境への zizmor インストール推奨 (`pip install zizmor`)、未インストール時は CI で初検出になる
- false positive 管理運用 (`# zizmor:ignore` コメント運用) の規律維持コスト

### Risks

| risk | 影響 | 緩和策 |
|---|---|---|
| Dependabot PR の merge 漏れで SHA drift | 既知脆弱性 fix の遅延 | 週次 PR 自動 review (Codex pg 委譲も検討) |
| zizmor false positive で CI 阻害 | PR merge 遅延 | D4 の `# zizmor:ignore` + 理由コメント運用 |
| GitHub 以外の CI 移行時の無価値化 | 投資 sunk cost | HELIX は GitHub 運用前提のため当面は問題なし、移行検討時に再評価 |
| zizmor 開発停止 | 保守不能 | Grafana スポンサー + Trail of Bits 出身者 + 5300+ stars で持続リスク低、最悪 fork 可能 (MIT) |
| Rust バイナリ依存 | Windows native での導入難 | WSL2 (ubuntu 環境) で pip install 対応、CI は ubuntu-latest で問題なし |

## Alternatives Considered

### A1: CodeQL のみ (採用見送り)

CodeQL は GitHub 提供で導入容易だが、Workflow yaml の security check は limited (template-injection 等を部分カバー)。zizmor の 30+ ルールには遥かに及ばない。**CodeQL はアプリケーション code 用、zizmor は Workflow 用** として併用可能 (補完関係)。

### A2: actionlint のみ (採用見送り)

actionlint は Workflow の lint ツールで yaml syntax + matrix + shell lint 等を check するが、**security ルールは限定的** (overly-permissive scope 程度)。zizmor の supply chain / injection / cache poisoning 等は対象外。**actionlint は CI lint 用、zizmor は security 用** として併用可能。

### A3: ツール導入なし、手動 review のみ (採用見送り)

HELIX は AI エージェント中心のため、Workflow 変更は Codex 委譲または Opus 直接で頻繁に発生する。人間 review でセキュリティ観点を全て catch するのは現実的でなく、機械 lint で網羅性を担保する必要がある。

### A4: 商用 SAST ツール (Snyk 等) 採用 (採用見送り)

商用は freemium 後の費用発生、license 管理コスト、ベンダーロックインで HELIX 思想 (OSS 中心) と整合しない。

## Implementation Plan

PLAN-222 で 4 Sprint 実施。tl-advisor 指摘 P1 (並列判定甘い) を受け、依存順序を修正:

- **Sprint .1** (本 ADR-036): 採用方針確定 + tl-advisor adversarial check + Acceptance Conditions 設定
- **Sprint .2** (.1 完了後): CI ジョブ + workflow SHA 固定 + permissions 宣言 (Opus 直接 + Codex pg 委譲混在)
  - `security.yml` の CLI 仕様 (zizmor 実行コマンド + SARIF format + ignore 構文) を確定
  - 全 workflow の permissions 宣言の最小権限実例を確定
- **Sprint .3** (.2 完了後): `skills/common/security/references/gha-security.md` 起草 (Codex docs または Opus 直接)
  - Sprint .2 で確定した CLI 仕様 / ignore 方針 / permissions 実例を取り込む
- **Sprint .4** (.2 完了後、.3 と並列可): pre-push hook 統合 (Codex pg または Opus 直接)
  - Sprint .2 の CLI 仕様を呼び出す形に整合

**依存順序**: `.1 → .2 → (.3 ∥ .4)`。.3 / .4 は .2 の出力 (CLI 仕様 + permissions 実例 + ignore 方針) を入力に取るため .1-.2-.3/.4 の 3 step。4 並列は不可。

## Acceptance Conditions (Accepted with conditions → Accepted 化までに必要)

tl-advisor adversarial check (2026-05-23) で受領した P1/P2 指摘を解消する条件:

| # | 条件 | 対応 |
|---|---|---|
| AC-1 (P1) | `security.yml` 内の `actions/checkout` / `actions/setup-python` / `upload-sarif` が SHA pin + version comment 付きで存在 | **satisfied (2026-05-23)**: `actions/checkout@34e114876b...` # v4.3.1 / `actions/setup-python@a26af69be...` # v5.6.0 / `github/codeql-action/upload-sarif@8c78abb9b...` # v3.28.0 (PLAN-222 AC-1 wave) |
| AC-2 (P1) | `zizmor-action` 自体の SHA pin (本 ADR では `pip install zizmor` 直接実行で zizmor-action 不使用なので無条件 satisfy) | **satisfied** (zizmor-action 不使用、`pip install zizmor` 直接実行で `python3 -m pip install zizmor` の pip package SHA 検証は AC-3 で Dependabot pip ecosystem に委譲) |
| AC-3 (P1) | Dependabot 初回 PR (week 1) が期待通り SHA pinned action を更新できること | 採用後 1 週間で確認 (Dependabot ecosystem=github-actions 週次) |
| AC-4 (P1) | Sprint 並列順序を `.1 → .2 → (.3 ∥ .4)` に修正 (PLAN-222 更新) | PLAN-222 修正 |
| AC-5 (P2) | `cli/lib/zizmor_ignore_lint.py` 機械検査の実装 (理由 + owner + 期限) | PLAN-222 carry または別 PLAN |
| AC-6 (P2) | pre-push hook の workflow 変更検出が `HEAD..origin/main` ではなく stdin refs ベースであること | Sprint .4 実装で satisfy 済 (本 wave で確認) |
| AC-7 (P2) | OpenSSF Scorecard / Harden-Runner / actionlint との補完関係を D1 に追記 | 本 ADR で satisfy 済 |
| AC-8 (P3) | typo (`statisfy` → `satisfy`)、D2 表現修正 (`3 段` → `CI enforcement + local advisory + knowledge reference`) | 本 ADR で satisfy 済 |

## Related Documents

- PLAN-222 (本 ADR の trigger PLAN)
- ADR-009 (hook-strategy、pre-push hook 統合方針の base ADR)
- ADR-035 (外部 skill 統合の直前範例、HELIX format snapshot)
- skills/common/security/SKILL.md (本 ADR 後に triggers / verification 拡張)
- skills/common/security/references/gha-security.md (本 ADR 後に Sprint .3 で新規起草)

## References

- zizmor 公式: https://github.com/zizmorcore/zizmor
- zizmor docs: https://docs.zizmor.sh/
- zizmor 統合ガイド: https://docs.zizmor.sh/integrations/
- Grafana Labs blog: https://grafana.com/blog/how-to-detect-vulnerable-github-actions-at-scale-with-zizmor/
- Ned Batchelder 独立評価: https://nedbatchelder.com/blog/202410/github_action_security_zizmor
- OSS Security podcast (William Woodruff interview): https://opensourcesecurity.io/2025/2025-05-securing-github-actions-william-woodruff/
