---
plan_id: PLAN-214
title: "PLAN-214: helix-docs 多言語化 (i18n、英語 / 中国語 / 韓国語)"
kind: impl
layer: cross
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-160-helix-mkdocs-site.md   # from dependencies.parent
size: L
created: "2026-05-23"
owner: PM
agent_slots:
  - role: pmo-tech-docs
    slot_label: "Tech Docs — mkdocs-material i18n plugin / gettext best practices 外部精読"
  - role: tl
    slot_label: "TL — i18n アーキテクチャ設計 (SKILL.md lang section vs 別 file 分岐) + ADR-057 起票判断"
  - role: docs
    slot_label: "Docs — 英語 / 中国語 / 韓国語 翻訳テンプレート起草 + SKILL.md section 骨格追加"
  - role: se
    slot_label: "SE — gettext ベース CLI message 翻訳 + helix-docs i18n plugin 設定実装"
  - role: qa
    slot_label: "QA — i18n build 検証 + 言語切替動作確認 + broken link check (各言語)"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-160 mkdocs 設計との整合確認 + i18n scope 逸脱チェック"
generates:
  - artifact_path: docs/site/mkdocs.yml
    artifact_type: yaml_config
  - artifact_path: docs/site/docs/en/index.md
    artifact_type: markdown_doc
  - artifact_path: docs/site/docs/zh/index.md
    artifact_type: markdown_doc
  - artifact_path: docs/site/docs/ko/index.md
    artifact_type: markdown_doc
  - artifact_path: cli/locale/en/LC_MESSAGES/helix.po
    artifact_type: other
  - artifact_path: docs/adr/ADR-057-helix-docs-i18n-snapshot.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-160
  requires:
    - PLAN-160
  blocks: []
related_adr:
  - ADR-057
related_plans:
  - PLAN-160
related_docs:
  - docs/site/mkdocs.yml
  - helix/HELIX_CORE.md
  - skills/SKILL_MAP.md
---

# PLAN-214: helix-docs 多言語化 (i18n、英語 / 中国語 / 韓国語)

> **kind**: impl (多言語 docs site + CLI message gettext 化)
> **layer**: cross (docs/site、SKILL.md、CLI message の全域にまたがる)
> **drive**: be (CLI message gettext 化が中心、docs site は mkdocs-material i18n plugin に委ねる)
> **本 PLAN の役割**: HELIX は日本語ベースで設計・運用されているが、グローバル展開に向け
> 英語 / 中国語 / 韓国語の i18n 対応を追加する。docs site は mkdocs-material i18n plugin、
> CLI message は gettext (.po/.mo) ベースで翻訳管理し、SKILL.md / PLAN.md には
> `lang_en / lang_zh / lang_ko` section を追加して多言語 summary を保持する。

---

## §0. L2 大局判断 (ADR-057)

本 PLAN は以下の L2 大局判断を含む。詳細は ADR-057 に凍結する。

| 判断項目 | 採用案 | 根拠 |
|---|---|---|
| docs site i18n 方式 | mkdocs-material `i18n` plugin (per-language docs/) | 言語別ディレクトリで nav 独立化・material テーマ標準対応 |
| CLI message 翻訳基盤 | gettext (.po/.mo) + Python `gettext` 標準ライブラリ | 追加依存不要・翻訳ツール (Poedit 等) エコシステム利用可能 |
| SKILL.md 多言語 section | frontmatter 内 `lang:` mapping (lang_en / lang_zh / lang_ko) | 既存 SKILL.md 構造を最小変更・skill catalog rebuild と連携可能 |
| 翻訳優先順位 | 英語 full → 中国語 / 韓国語 core section のみ (Sprint .3-4 で段階化) | 英語 full 完成で対外利用可能、CJK は段階追加でリスク分散 |

**WebSearch 必須 3 query (Sprint .1 実施前に実行)**:
1. `mkdocs-material i18n plugin 2025 2026 per-language navigation setup`
2. `gettext Python CLI tool translation best practices 2025`
3. `SKILL.md multilingual frontmatter section HELIX i18n design pattern`

---

## §1. 目的

1. `docs/site/` に英語 / 中国語 / 韓国語の言語別ディレクトリを追加し、
   mkdocs-material i18n plugin でサイト多言語化する (Sprint .1〜.3)
2. CLI message (`helix` コマンドの stdout / stderr テキスト) を gettext ベースで
   翻訳管理し、`HELIX_LANG=en/zh/ko` で切り替え可能にする (Sprint .4)
3. SKILL.md / PLAN.md に `lang_en / lang_zh / lang_ko` section を追加する
   テンプレートとガイドラインを整備する (Sprint .3)

---

## §2. 背景

HELIX docs は日本語のみで、非日本語話者が参照できない。CLI message も日本語ハードコード、
SKILL.md も日本語のみで英語タスク記述との推挙精度に課題がある。

本 PLAN は PLAN-160 (mkdocs-material site 構築) 完了後に実施する。
mkdocs-material i18n plugin を採用し、CLI message は Python 標準 `gettext` を使う。

---

## §3. 実装方針

### Sprint .1: WebSearch + ADR-057 起票

担当: pmo-tech-docs + tl。WebSearch 3 query 実施後、ADR-057 で L2 判断を凍結する。

### Sprint .2: 英語版 docs 骨格起草

担当: docs。`docs/site/docs/en/` に tutorial / reference / explanation 骨格を配置。
mkdocs.yml へ i18n plugin を追加し、en のみ `build: true`、zh/ko は `build: false` で保留する。

```yaml
plugins:
  - i18n:
      default_language: ja
      languages:
        en:
          name: English
          build: true
        zh:
          name: 中文
          build: false
        ko:
          name: 한국어
          build: false
```

### Sprint .3: SKILL.md lang section テンプレート整備

担当: docs + pmo-sonnet。core 5 skill (common/testing / common/security /
workflow/verification / workflow/estimation / integration/agent-design) に先行適用する。

```yaml
lang:
  en: "English 80-120 char summary"
  zh: ""
  ko: ""
```

### Sprint .4: CLI message gettext 化 + zh/ko docs 追加

担当: se。`cli/lib/i18n.py` (gettext wrapper) + `.po` ファイル 3 言語分を実装。
`HELIX_LANG=en` で CLI message を英語切替。未設定時は日本語のまま (後退互換)。

### Sprint .5: 検証 + CI 統合

担当: qa。全有効言語で `mkdocs build --strict` PASS + `helix test` に多言語 build を追加。

---

## §4. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | WebSearch 3 query + ADR-057 起票 | pmo-tech-docs + tl | ADR-057 ファイル存在 + L2 判断凍結済 |
| **Sprint .2** | 英語版 docs 骨格 + i18n plugin 設定 | docs | `mkdocs build` で en ページが 0 error 生成 |
| **Sprint .3** | SKILL.md lang section テンプレート + core 5 skill 適用 | docs + pmo-sonnet | 5 skill の `lang.en` フィールド確定 |
| **Sprint .4** | CLI message gettext 化 + zh/ko docs 追加 | se | `HELIX_LANG=en helix skill search` が英語出力 |
| **Sprint .5** | 全言語 build 検証 + CI 統合 | qa | broken link 0 件・helix test PASS (全言語) |

---

## §5. デグレ禁止項目

1. 日本語 docs (既存 `docs/site/docs/ja/` or default 言語) は変更・削除しない
2. `HELIX_LANG` 未設定時の CLI message は日本語のまま維持 (後退互換)
3. SKILL.md の既存フィールド (description / triggers 等) は変更しない
4. PLAN-160 で確立した `helix docs serve / build` の動作を壊さない

---

## §6. DoD (Definition of Done)

1. Sprint .1: `docs/adr/ADR-057-helix-docs-i18n-snapshot.md` が存在し L2 判断凍結済
2. Sprint .2: `mkdocs build --strict` で英語ページが 0 error で生成される
3. Sprint .3: core 5 skill の SKILL.md に `lang.en` フィールドが追加済
4. Sprint .4: `HELIX_LANG=en helix skill search "testing"` が英語 message を出力する
5. Sprint .5: 全有効言語で `mkdocs build --strict` PASS + broken link 0 件
6. `python3 cli/lib/plan_validator.py docs/plans/PLAN-214-*.md` PASS
7. デグレ禁止 (§5) を git diff で確認

---

## §7. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN + ADR-057) | 存在 (本 file + Sprint .1 で起票) | docs/plans/PLAN-214-*.md / docs/adr/ADR-057-*.md |
| ② 実装コード | Sprint .2〜.4 で生成 | docs/site/docs/{en,zh,ko}/ / cli/lib/i18n.py |
| ③ テスト設計 | Sprint .5 (QA) が担当 | docs/v2/L4-test-design/PLAN-214-test-design.md (Sprint .5 起票) |
| ④ テストコード | Sprint .5 実装 | cli/lib/tests/test_i18n.py |

**双方向 reference**:
- 本 PLAN (①) → 実装 (②): generates.artifact_path に列挙
- 実装 (②) → 本 PLAN (①): cli/lib/i18n.py 先頭 comment に `# PLAN-214` 明記
- 本 PLAN (①) → テスト設計 (③): Sprint .5 起票時に §7 に追記

---

## §8. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| mkdocs-material i18n plugin の page 生成数増大で build 時間が増加 | CI 時間が許容を超える | Sprint .5 で実測し、zh/ko を `build: false` に戻す段階導入 |
| SKILL.md lang section が推奨キャッシュに混入し推挙精度に影響 | skill search の精度低下 | Sprint .3 で 5 skill のみ先行適用 + PLAN-194 と連携して精度計測 |
| gettext Python 標準で CJK 文字の文字化け | CLI message が文字化けする | Sprint .4 で UTF-8 locale 設定 + bats テストで非 ASCII 出力を検証 |
| ADR-057 起票前に Sprint .2 着手した場合の i18n 方針揺れ | docs 構造を後から修正する手戻り | Sprint 順序を厳守 (Sprint .1 完了 → Sprint .2 以降着手) |
