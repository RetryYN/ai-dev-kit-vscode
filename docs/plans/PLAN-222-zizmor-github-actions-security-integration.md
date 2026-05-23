---
plan_id: PLAN-222
title: "PLAN-222: zizmor (GitHub Actions security audit) 統合 — CI ジョブ + workflow SHA 固定 + permissions 宣言 + skill reference"
layer: L4
kind: impl
status: draft
size: S
drive: be
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-tech-fork
    slot_label: "PMO — OSS 評価レポート (実施済、本 PLAN trigger)"
  - role: pg
    slot_label: "PG — 案 B: .github/workflows/ zizmor CI ジョブ追加 + 既存 workflow SHA 固定 + permissions 宣言"
  - role: pg
    slot_label: "PG — 案 C: scripts/git-hooks/pre-push に zizmor ローカル統合"
  - role: docs
    slot_label: "Docs — 案 A: skills/common/security/references/gha-security.md 新規起草"
generates:
  - artifact_path: .github/workflows/security.yml
    artifact_type: yaml_config
  - artifact_path: skills/common/security/references/gha-security.md
    artifact_type: markdown_doc
  - artifact_path: scripts/git-hooks/pre-push
    artifact_type: script
  - artifact_path: docs/adr/ADR-036-zizmor-adoption-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr:
  - ADR-036-zizmor-adoption-decision
related_docs:
  - skills/common/security/SKILL.md
  - .github/workflows/ci.yml
  - scripts/git-hooks/pre-push
acceptance_criteria:
  - ".github/workflows/security.yml で zizmor scan が PR ごとに走り SARIF 出力する"
  - "既存 6 workflow (ci/commitlint/feature/hotfix/poc/refactor) の actions/checkout + actions/setup-python が SHA 固定済"
  - "全 workflow に permissions 宣言が追加され zizmor の excessive-permissions / undocumented-permissions 警告 0 件"
  - "scripts/git-hooks/pre-push が .github/workflows/ 変更時に zizmor ローカル実行を行う"
  - "skills/common/security/references/gha-security.md が存在し zizmor 30+ ルールの主要 5 (template-injection / dangerous-triggers / unpinned-uses / excessive-permissions / artipacked) を HELIX 文脈で解説する"
  - "ADR-036-zizmor-adoption-decision.md が accepted 状態で存在する"
  - "shellcheck + yaml lint + bash -n 全 PASS"
---

# PLAN-222: zizmor (GitHub Actions security audit) 統合

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-036** で凍結 (Sprint .1 実施後に accepted 化):

- zizmor 採用根拠 (CodeQL / Trivy / Renovate 等の代替との比較)
- 統合方式 (CI ジョブ + pre-push hook + skill reference の 3 段構え)
- SHA 固定維持戦略 (Dependabot actions ecosystem 併用)
- false positive 管理方針 (zizmor.yml 設定 + `# zizmor:ignore` コメント運用)

## 背景

HELIX は AI エージェント (Claude Code + Codex CLI) ベースの開発フレームワークで、GitHub Actions ベースの CI/CD を運用している。既存 6 workflow (ci.yml / commitlint.yml / feature.yml / hotfix.yml / poc.yml / refactor.yml) には以下の技術的負債が存在:

1. **actions が SHA 未固定** (`actions/checkout@v4`, `actions/setup-python@v5` 等): タグはミュータブルなため、悪意ある作者が同名タグを新 commit に差し替えると HELIX CI が即時に汚染される
2. **permissions 宣言不在**: workflow / job レベルで `permissions:` が宣言されておらず GITHUB_TOKEN のデフォルト権限が広範に付与されている
3. **GitHub Actions 固有のセキュリティ観点が HELIX skill に欠落**: skills/common/security/ は OWASP / 認証認可 / 機密情報スキャンを扱うがCI pipeline security は未収録

zizmor (https://github.com/zizmorcore/zizmor、MIT、stars 5300+、最終 commit 2026-05-16) を統合することで、これらを CI 上 + ローカル pre-push で機械検出する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

pmo-tech-fork (agent ae182efe) が本 PLAN trigger の評価レポート作成時に実施:

| Query | 出典 | 抽出した業界 standard |
|---|---|---|
| zizmor github actions security audit 2026 | https://github.com/zizmorcore/zizmor | static analysis for GitHub Actions、30+ ルール、Rust 実装、MIT |
| zizmor integration ci workflow | https://docs.zizmor.sh/integrations/ | zizmor-action / pre-commit / Docker 等の統合パターン |
| zizmor vulnerable github actions detection scale | https://grafana.com/blog/how-to-detect-vulnerable-github-actions-at-scale-with-zizmor/ | Grafana Labs での実運用事例 (本ツール採用済) |
| zizmor github action security william woodruff | https://nedbatchelder.com/blog/202410/github_action_security_zizmor | Trail of Bits 出身 William Woodruff の実装、独立エンジニア視点 |
| zizmor open source security william woodruff | https://opensourcesecurity.io/2025/2025-05-securing-github-actions-william-woodruff/ | OSS security podcast 出演、保守体制継続性確認 |

## 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| zizmor 公式 | https://github.com/zizmorcore/zizmor | web evidence (本ツール公式) |
| zizmor docs | https://docs.zizmor.sh/ | web evidence (ルール体系・統合ガイド) |
| Grafana Labs 採用事例 | https://grafana.com/blog/how-to-detect-vulnerable-github-actions-at-scale-with-zizmor/ | web evidence (大規模実運用) |
| Ned Batchelder blog | https://nedbatchelder.com/blog/202410/github_action_security_zizmor | web evidence (独立評価) |
| OSS Security podcast | https://opensourcesecurity.io/2025/2025-05-securing-github-actions-william-woodruff/ | web evidence (保守者 interview) |
| GitHub - zizmorcore/zizmor | https://github.com/zizmorcore/zizmor | oss evidence (本ツール repository、MIT) |

## 採用案 (pmo-tech-fork 評価レポートより)

5 案のうち本 PLAN scope = 案 A + B + C + D (P0+P1+P2)、案 E (AI agent prompt pattern) は別 PLAN 候補:

| 案 | Priority | scope |
|---|---|---|
| 案 B (P0 必須) | CI ジョブ追加 + workflow SHA 固定 + permissions 宣言 | Sprint .1-.2 |
| 案 A (P1 推奨) | skills/common/security/references/gha-security.md 新規 | Sprint .3 |
| 案 C (P1 推奨) | scripts/git-hooks/pre-push 統合 | Sprint .4 |
| 案 D (P2 任意) | SKILL.md triggers 拡張 | Sprint .4 後段 |

## 実装計画 (Sprint .1 → .2 → (.3 ∥ .4)、tl-advisor 指摘 P1 反映で 3 step 化)

### Sprint .1: ADR-036 起票 + 採用方針確定 (Opus + tl-advisor)

実施内容:

1. ADR-036-zizmor-adoption-decision.md 起票 (採用根拠 + 統合方式 + SHA 固定維持戦略 + false positive 管理)
2. tl-advisor 召喚で zizmor 採用 + 統合方式の adversarial check
3. ADR-036 accepted 化

完了条件:

- ADR-036 が **Accepted with conditions** 状態で存在 (P1/P2/P3 解消後 Accepted 化、Acceptance Conditions AC-1〜AC-8)
- satisfy: tl-advisor adversarial check 完了 (changes_required 判定済、修正反映)

### Sprint .2: CI ジョブ + workflow SHA 固定 + permissions 宣言 (Codex pe 委譲、案 B P0)

実施内容:

1. `.github/workflows/security.yml` 新規作成: zizmor scan ジョブ (SARIF 出力 + GitHub Security tab upload)
2. 既存 6 workflow の `actions/checkout@v4` / `actions/setup-python@v5` を SHA 固定 (最新 SHA を確認してハードコード)
3. 全 workflow に `permissions:` 宣言を追加 (workflow レベル `permissions: read-all` + job レベル必要権限明示)
4. Dependabot 設定 (`.github/dependabot.yml`) で actions ecosystem を有効化 (SHA 更新を自動化)

完了条件:

- zizmor がローカル実行で全 workflow 0 警告 (unpinned-uses / undocumented-permissions / excessive-permissions)
- CI で security.yml が走り SARIF が出力される
- yaml lint + actionlint PASS

### Sprint .3: skills/common/security/references/gha-security.md 起草 (Codex docs 委譲、案 A P1)

実施内容:

1. zizmor 30+ ルールのうち主要 5 (template-injection / dangerous-triggers / unpinned-uses / excessive-permissions / artipacked) を HELIX 文脈で解説
2. 各ルールの検出コマンド例 + false positive 管理 (zizmor.yml 設定 + `# zizmor:ignore` コメント)
3. HELIX 連携 (G2/G4 ゲート時の参照、案 B の CI ジョブとの連動)
4. skills/common/security/SKILL.md の triggers に「GitHub Actions workflow 変更時」追加 (案 D)

完了条件:

- references/gha-security.md が 150-250 行で存在
- SKILL.md frontmatter description + triggers + verification の更新

### Sprint .4: scripts/git-hooks/pre-push に zizmor ローカル統合 (Codex pe 委譲、案 C P1)

実施内容:

1. pre-push hook に zizmor 実行ロジック追加:
   ```bash
   if git diff --name-only HEAD..origin/main 2>/dev/null | grep -q "^\.github/workflows/"; then
     if command -v zizmor >/dev/null 2>&1; then
       zizmor .github/workflows/ || exit 1
     fi
   fi
   ```
2. zizmor 未インストール時の挙動 (warning のみ で push 通す or fail-close、ADR-036 で確定)
3. 既存 pre-push hook の他 check (EMAIL_PATTERN 等) との順序整合

完了条件:

- pre-push hook 変更後の bash -n + shellcheck PASS
- workflow 変更を含む test commit で zizmor 起動 → 違反検出時 push block を確認
- 既存 pre-push check が回帰なし (EMAIL_PATTERN / commit message lint 等)

## DoD (Definition of Done)

- [ ] ADR-036 が accepted 状態で存在
- [ ] .github/workflows/security.yml で zizmor scan + SARIF upload が動作
- [ ] 既存 6 workflow が SHA 固定済 + permissions 宣言済
- [ ] zizmor ローカル実行で全 workflow 0 警告
- [ ] skills/common/security/references/gha-security.md が存在 (150-250 行)
- [ ] scripts/git-hooks/pre-push に zizmor 統合済 + 既存 check 回帰なし
- [ ] .github/dependabot.yml で actions ecosystem 有効化
- [ ] commit message + push まで完了 (4 並列投入後の統合 PR)

## V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 | 本 PLAN + ADR-036 | docs/plans/PLAN-222-*.md, docs/adr/ADR-036-*.md |
| ② 実装コード | Sprint .2-.4 生成物 | .github/workflows/security.yml, scripts/git-hooks/pre-push, skills/common/security/references/gha-security.md |
| ③ テスト設計 | 不要 (機械 lint で代替: zizmor scan / actionlint / shellcheck) | — |
| ④ テストコード | Sprint .4 test commit | (ad-hoc workflow 変更で zizmor 起動を確認) |

## carry / 注意点

- **SHA 固定の維持コスト**: Dependabot actions ecosystem 設定が必須 (週次 PR 自動生成)。手動更新運用は drift 発生のリスク高
- **false positive 管理**: 意図的な permissions 省略は `# zizmor:ignore` コメントで個別抑制。zizmor.yml 設定で project 全体の ignore は **最小限**
- **zizmor-action の SHA 固定**: zizmor-action 自体も SHA 固定 (`uses: zizmorcore/zizmor-action@<SHA>`) が必要
- **Windows 開発環境**: WSL2 は ubuntu 環境扱いで `pip install zizmor` 一発、native Windows は best-effort

## 関連 PLAN / ADR

- ADR-036 (本 PLAN tree の L2 snapshot)
- ADR-009 (hook-strategy、pre-push hook 統合方針)
- PLAN-100 (V2 phase4 overhaul、本 PLAN は phase4 carry 後の独立改善)

## risk

| risk | 影響 | 緩和策 |
|---|---|---|
| SHA 固定後の action 更新漏れ | 既知脆弱性 fix の遅延 | Dependabot actions ecosystem で週次 PR 自動生成 |
| zizmor false positive で CI 阻害 | PR merge 遅延 | zizmor.yml 設定 + `# zizmor:ignore` コメント運用、ADR-036 で運用ルール明文化 |
| GitHub 以外の CI 移行時の無価値化 | 投資の sunk cost | HELIX は GitHub 運用前提のため当面は問題なし、移行検討時に再評価 |

## AC-1 satisfied (2026-05-23)

`.github/workflows/security.yml` 内 3 action を SHA pin + version comment 付きに変更 (ADR-036 AC-1):

| Action | SHA | Version comment |
|---|---|---|
| `actions/checkout` | `34e114876b0b11c390a56381ad16ebd13914f8d5` | v4.3.1 |
| `actions/setup-python` | `a26af69be951a213d495a4c3e4e4022e16d87065` | v5.6.0 |
| `github/codeql-action/upload-sarif` | `8c78abb9b62512e3c45dea6559ffd924ed8549c8` | v3.28.0 |

検証: `python3 -c "yaml.safe_load(...)"` YAML OK、zizmor は CI 実行 (security.yml workflow trigger 時)。

**残 AC**:
- AC-2: zizmor-action 不使用 (`pip install zizmor` 直接実行) で **conditional satisfied**、AC-3 で Dependabot pip ecosystem に委譲
- AC-3: Dependabot 初回 PR (week 1) 待機 → 確認後 ADR-036 を `Accepted` に格上げ

scope 注: 他 workflow (ci.yml / feature.yml / hotfix.yml / poc.yml / refactor.yml / commitlint.yml) の同 action SHA pin は ADR-036 scope 外 (Dependabot で順次対応)。
