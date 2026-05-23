---
plan_id: PLAN-160
title: "PLAN-160: HELIX framework documentation site (mkdocs-material ベース)"
layer: cross
kind: impl
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: L
drive: be
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — 既存 docs 資産棚卸し + mkdocs 構成案作成・整合確認"
  - role: pmo-tech-fork
    slot_label: "Tech Fork — mkdocs-material / Diátaxis integration OSS 探索・採用判断"
  - role: tl
    slot_label: "TL — mkdocs.yml アーキテクチャ設計・helix docs CLI 設計・ADR-056 起票判断"
  - role: docs
    slot_label: "Docs — mkdocs.yml 初期構成 + navigation 組織化 + index ページ起草"
  - role: se
    slot_label: "SE — helix docs serve / helix docs build CLI 実装 + CI integration"
  - role: qa
    slot_label: "QA — mkdocs build 検証 + broken link check + 表示確認手順"
generates:
  - artifact_path: docs/site/mkdocs.yml
    artifact_type: yaml_config
  - artifact_path: docs/site/docs/index.md
    artifact_type: markdown_doc
  - artifact_path: cli/helix-docs
    artifact_type: cli_extension
  - artifact_path: docs/adr/ADR-056-helix-mkdocs-site-snapshot.md
    artifact_type: adr_snapshot
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr:
  - ADR-056
related_plans:
  - PLAN-100-existing-retrofit-v2-revision
  - PLAN-127-v2-l2-master-plan-adr-trace
related_docs:
  - docs/commands/index.md
  - docs/architecture/cli-layout.md
  - helix/HELIX_CORE.md
  - skills/SKILL_MAP.md
---

# PLAN-160: HELIX framework documentation site (mkdocs-material ベース)

> **kind**: impl (mkdocs-material サイト構築 + helix docs CLI 実装)
> **layer**: cross (docs 全域 + CLI 拡張にまたがる)
> **drive**: be (CLI 拡張が中心、frontend は mkdocs-material に委ねる)
> **本 PLAN の役割**: HELIX framework は CLAUDE.md / SKILL_MAP.md / HELIX_CORE.md / 100+ PLAN / 50+ ADR で構成されるが、新規メンバーや外部利用者が全体像を把握できる navigation が存在しない。mkdocs-material を使った documentation site を `docs/site/` 配下に構築し、`helix docs serve` / `helix docs build` CLI で日常的な参照フローに組み込む。

---

## §0. L2 大局判断 (ADR-056)

本 PLAN は以下の L2 大局判断を含む。詳細は ADR-056 に凍結する。

| 判断項目 | 採用案 | 根拠 |
|---|---|---|
| ドキュメントツール選択 | mkdocs-material | Python エコシステム統一・Material Design 対応・HELIX Bash/Python 混在環境と親和 |
| 情報アーキテクチャ | Diátaxis 4 象限 (tutorial / how-to / reference / explanation) | 新規メンバー向け tutorial と既存利用者向け reference を分離 |
| navigation 組織化 | PLAN / ADR / Skills / Commands / Architecture の 5 セクション | 既存 docs 構造を尊重しつつ閲覧経路を整理 |
| CI 統合 | mkdocs build --strict を helix test に追加 | broken link / missing nav を回帰防止 |

**WebSearch 必須 3 query (Sprint .1 実施前に実行)**:
1. `mkdocs-material 2026 Diátaxis integration best practices`
2. `mkdocs navigation PLAN ADR large documentation site 2025 2026`
3. `mkdocs strict mode broken link check CI integration GitHub Actions`

---

## §1. 目的

1. `docs/site/` 配下に mkdocs-material ベースの documentation site を構築し、PLAN / ADR / Skills / Commands を navigation で組織化する (Sprint .1〜.3)
2. `helix docs serve` (ローカル開発サーバー) と `helix docs build` (静的サイト生成) を CLI として実装する (Sprint .4)
3. `helix test` に `mkdocs build --strict` を組み込み、broken link を CI で回帰防止する (Sprint .5)

---

## §2. 背景

### 2.1 現状の問題

| 問題 | 影響 |
|---|---|
| 読み手が全体像を把握できる entry point がない | 新規メンバーが CLAUDE.md → SKILL_MAP.md → HELIX_CORE.md の読み順を知らない |
| 100+ PLAN が `docs/plans/` に平置き | 関連 PLAN 群のグループ化・検索ができない |
| 50+ ADR が `docs/adr/` に平置き | 特定トピック (V5 framework / security / db) の ADR を探せない |
| CLI コマンド一覧が `docs/commands/index.md` のみ | 実例・オプション・使用 context が分散している |

### 2.2 なぜ mkdocs-material か

- HELIX は Python / Bash 中心で、Sphinx (reStructuredText 前提) や Docusaurus (Node.js 前提) より mkdocs の方がエコシステム統一が容易
- mkdocs-material は search / navigation / dark mode / mermaid 対応が標準内蔵
- `mkdocs build --strict` で broken link 検出が CI に組み込める
- Python 3 環境のみで動作し、追加ランタイム不要

### 2.3 Diátaxis 4 象限との対応

| 象限 | HELIX での対応 |
|---|---|
| Tutorial (学習志向) | HELIX 入門 / ゼロから PLAN を起票する手順 |
| How-to (問題解決志向) | helix コマンド別利用手順 / Codex 委譲手順 |
| Reference (情報志向) | PLAN 一覧 / ADR 一覧 / CLI コマンド仕様 |
| Explanation (理解志向) | SKILL_MAP / HELIX フェーズ思想 / V5 framework 解説 |

---

## §3. 実装方針

### Sprint .1: WebSearch + OSS 探索 + ADR-056 起票

担当: pmo-tech-fork + tl

```bash
# WebSearch 3 query 実施 (§0 の query 3 本)
# mkdocs-material 最新 version 確認
# Diátaxis integration OSS (mkdocs-awesome-pages-plugin 等) 探索
```

成果物: ADR-056-helix-mkdocs-site-snapshot.md (L2 判断凍結)

### Sprint .2: docs 資産棚卸し + navigation 設計

担当: pmo-sonnet

```bash
# 既存 docs 構造確認
find docs/ -name "*.md" | wc -l
ls docs/plans/ | head -20
ls docs/adr/ | head -20
ls docs/commands/
```

navigation 設計 (mkdocs.yml の nav: セクション):

```yaml
nav:
  - Home: index.md
  - チュートリアル:
      - HELIX を始める: tutorial/getting-started.md
      - 最初の PLAN を起票する: tutorial/first-plan.md
  - How-to:
      - Codex へ委譲する: how-to/codex-delegation.md
      - PLAN を起票する: how-to/create-plan.md
      - ADR を起票する: how-to/create-adr.md
  - リファレンス:
      - CLI コマンド一覧: reference/commands.md
      - PLAN 一覧: reference/plans.md
      - ADR 一覧: reference/adrs.md
      - ロール一覧: reference/roles.md
  - 解説:
      - HELIX フェーズ思想: explanation/helix-phases.md
      - V5 framework: explanation/v5-framework.md
      - SKILL_MAP 解説: explanation/skill-map.md
```

### Sprint .3: mkdocs.yml + index ページ起草

担当: docs

配置: `docs/site/` (Git 管理対象、`docs/site/site/` は .gitignore)

```
docs/site/
  mkdocs.yml
  docs/
    index.md
    tutorial/
    how-to/
    reference/
    explanation/
```

mkdocs.yml 最小構成:

```yaml
site_name: HELIX Framework Documentation
docs_dir: docs
site_dir: site
theme:
  name: material
  language: ja
  features:
    - navigation.tabs
    - navigation.expand
    - search.highlight
plugins:
  - search:
      lang: ja
markdown_extensions:
  - pymdownx.mermaid2
  - admonition
  - tables
```

### Sprint .4: helix docs CLI 実装

担当: se

実装ファイル: `cli/helix-docs` (Bash)

```bash
# helix docs serve
mkdocs serve -f docs/site/mkdocs.yml

# helix docs build
mkdocs build -f docs/site/mkdocs.yml --strict

# helix docs open
xdg-open docs/site/site/index.html 2>/dev/null || open docs/site/site/index.html
```

cli/helix へのルーター登録 (1 行 + help 1 行):

```bash
# cli/helix 内 dispatch case 追加
docs)   exec "$HELIX_CLI_DIR/helix-docs" "$@" ;;
```

### Sprint .5: CI 統合 + 検証

担当: qa + se

```bash
# helix test に mkdocs build --strict を追加
# broken link 0 件確認
# helix commands 一覧に docs が表示されることを確認
helix commands | grep docs
```

---

## §4. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | WebSearch 3 query + ADR-056 起票 | pmo-tech-fork + tl | ADR-056 ファイル存在 + L2 判断凍結済 |
| **Sprint .2** | docs 資産棚卸し + navigation 設計 | pmo-sonnet | nav: セクション確定、docs/site/ ディレクトリ構造案確定 |
| **Sprint .3** | mkdocs.yml + index + How-to / Reference / Explanation 骨格 | docs | `mkdocs build` が 0 error で完了 |
| **Sprint .4** | `cli/helix-docs` 実装 + cli/helix routing 登録 | se | `helix docs serve` / `helix docs build` が動作 |
| **Sprint .5** | CI 統合 (`helix test` に mkdocs build 追加) + QA 全件確認 | qa | broken link 0 件・helix test PASS |

---

## §5. デグレ禁止項目

1. 既存 `docs/` 配下のファイルは移動・削除しない (`docs/site/docs/` は別ディレクトリに新設)
2. `docs/site/site/` (mkdocs 生成物) は .gitignore に追加し、Git 追跡しない
3. `helix test` の既存テスト (pytest / bats) を削除・スキップしない (mkdocs build を追加するのみ)
4. cli/helix の既存 dispatch (case 文) を書き換えない (追記のみ)

---

## §6. DoD (Definition of Done)

1. Sprint .1: `docs/adr/ADR-056-helix-mkdocs-site-snapshot.md` が存在し、L2 判断が凍結されている
2. Sprint .3: `mkdocs build -f docs/site/mkdocs.yml --strict` が 0 error で完了
3. Sprint .4: `helix docs serve` / `helix docs build` が正常動作
4. Sprint .4: `helix commands` に `docs` が表示される
5. Sprint .5: `helix test` に mkdocs build が組み込まれ、broken link 0 件
6. `python3 cli/lib/plan_validator.py docs/plans/PLAN-160-*.md` PASS
7. デグレ禁止 (§5) を git diff で確認

---

## §7. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN + ADR-056) | 存在 (本 file + Sprint .1 で起票) | docs/plans/PLAN-160-*.md / docs/adr/ADR-056-*.md |
| ② 実装コード | Sprint .3〜.4 で生成 | docs/site/mkdocs.yml / cli/helix-docs |
| ③ テスト設計 | Sprint .5 (QA) が担当 | docs/v2/L4-test-design/PLAN-160-test-design.md (Sprint .5 起票) |
| ④ テストコード | Sprint .5 実装 | cli/tests/test_helix_docs.bats |

**双方向 reference**:
- 本 PLAN (①) → 実装 (②): generates.artifact_path
- 実装 (②) → 本 PLAN (①): cli/helix-docs 先頭 comment に `# PLAN-160` 明記
- 本 PLAN (①) → テスト設計 (③): Sprint .5 起票時に §7 に追記
- テスト設計 (③) → 本 PLAN (①): テスト設計 frontmatter に `related_plans: [PLAN-160]` 明記

---

## §8. 関連 PLAN / ADR

### 前段 (requires)
- なし (独立実施可能)

### 関連 ADR
- ADR-056: 本 PLAN の L2 大局判断 snapshot (Sprint .1 で起票)

### 関連 docs
- docs/commands/index.md: CLI コマンド一覧 (navigation source)
- docs/architecture/cli-layout.md: CLI 構造の参照
- SKILL_MAP.md: explanation セクションの source

---

## §9. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| mkdocs-material の Python version 依存 | Python 3.8 未満環境で動作不可 | Sprint .1 で version matrix 確認 |
| 日本語検索 (MeCab 等) の追加依存 | 検索精度低下または環境差異 | mkdocs-material 標準 search plugin の日本語対応範囲で妥協、MeCab は任意 |
| docs/site/ と既存 docs/ のパス衝突 | mkdocs の docs_dir 解決エラー | Sprint .2 で docs_dir を `docs/site/docs` に明示し、既存 docs/ と分離 |
| helix test への mkdocs build 追加で CI 時間増大 | 全体テスト時間が +30 秒以上増加 | Sprint .5 で実測し、許容超なら `helix test --no-mkdocs` フラグで opt-out 提供 |
| ADR-056 起票前に Sprint .3 を先行した場合の L2 判断揺れ | navigation 設計が後から変更される | Sprint 順序を厳守 (Sprint .1 完了 → Sprint .2 以降着手) |
