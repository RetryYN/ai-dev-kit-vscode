---
adr_id: ADR-035
title: 外部素材 skill 4 件の HELIX 体系統合 (doc-system-architect / requirements-deriver / god-writing / gpt-image)
status: Accepted
date: 2026-05-23
deciders:
  - PM (Opus)
  - PMO (Sonnet)
related_plans:
  - parent: null
  - L2_snapshot_of: 本 PR (外部 skill 4 件統合、PLAN なし軽量 PR)
supersedes: []
superseded_by: []
---

# ADR-035: 外部素材 skill 4 件の HELIX 体系統合

## Status

**Accepted** — 2026-05-23

## Context

ユーザーが 2026-05-23 session 内で、外部素材として 4 つの skill を投入した:

| 素材 | 元 path | 規模 |
|---|---|---|
| doc-system-architect | `./files (4)/SKILL.md` | 138 行、SKILL.md 単独 |
| requirements-deriver | `./files (4)/mnt/user-data/outputs/requirements-deriver/SKILL.md` | 元素材 1 file |
| gpt-image | `./gpt-image/` | 72K、5 file (SKILL.md + knowledge/ + skill/) |
| god-writing | `./god-writing/` | 928K、97 file、11 カテゴリ |

ユーザー指示:
- 「ヘリックススキルにまとめ上げてほしい」(4 件すべて)
- 「必要があれば Web 検索で補強」(gpt-image / god-writing)
- 「Codex に搭載されているのが GPT Image 2.0 になっている」(gpt-image は GPT Image 2 ベースで起票必須)
- 「統合後にクリーンアップを」(元 dir 削除指示)

## Decision

### D1: skill カテゴリ配置

| skill | HELIX カテゴリ | helix_layer | 配置理由 |
|---|---|---|---|
| doc-system-architect | `workflow/` | L1 (メタ層) | ドキュメント体系の設計判断 = workflow phase |
| requirements-deriver | `workflow/` | L1 | 機能要件 → 非機能要件導出 = L1 要件定義の核心 |
| gpt-image | `design-tools/` | L5 | アイキャッチ / 図解生成 = L5 Visual Refinement |
| god-writing | `writing/` | L5 | LP / FE / コピー = L5 (writing カテゴリ新規大型 skill) |

### D2: HELIX format 変換戦略

全 4 件とも以下に統一:

- **frontmatter** (HELIX 標準): `name` / `description` / `metadata.helix_layer` / `metadata.triggers` / `metadata.verification` / `compatibility.claude/codex`
- **本文構成**: 「## 適用タイミング」を冒頭、「## HELIX 体系内の責務境界」section を必須
- **WebSearch 証拠**: 起草時に 2-3 query 以上、本文に inline 反映 + 出典 URL 明記 (PLAN-087 ガード遵守)
- **references/** 構造: 元素材が複数 file の場合 (gpt-image / god-writing) は references/ 配下に full copy、INDEX.md で navigation

### D3: gpt-image は GPT Image 2 (Codex CLI default) ベース

元素材は GPT Image 1.5 ベースだったが、ユーザー指摘により **GPT Image 2 (2026/04/21 リリース、Codex CLI default、$imagegen built-in skill)** ベースに全面更新:

- model 名: `gpt-image-2`、date-pin: `gpt-image-2-2026-04-21`
- 解像度: 1K / 2K / 4K native (4096×4096 最大、API は 2K まで stable、4K は beta)
- 参照画像: 最大 16 reference images で style anchor
- 多言語: 日本語 / 中国語 / 韓国語 / ヒンディー語 / ベンガル語 native、~99% typography accuracy
- Reasoning: Thinking mode (生成前 layout 計画 / Web 検索 / self-check)
- Pricing: token-based ($5/$8/$10/$30 per M tokens)、$0.006-0.21/image、Batch API 50% off
- Codex CLI 統合: `$imagegen` built-in skill 経由
- **DALL-E 3 retired** の後継

### D4: god-writing は既存 writing/* と重複許容

god-writing は 11 カテゴリ / 97 file の巨大統合 skill で、既存 writing/japanese / writing/explain / writing/social / writing/story と重複領域あり。

決定: **既存 writing/* は基礎用途で残置、god-writing は LP / FE 応用用途**として棲み分け。重複領域は責務境界 section で明示。将来統合候補は別 PLAN で検討。

### D5: requirements-deriver は doc-system-architect の子スキル

元素材で「requirements-deriver はこの体系の子スキル」と明記されており、doc-system-architect → requirements-deriver の親子関係を SKILL_MAP §責務境界で保持。

### D6: クリーンアップ方針

統合完了後、元の 3 ディレクトリを削除:

- `./files (4)/` (doc-system-architect + requirements-deriver 素材)
- `./gpt-image/` (gpt-image 素材)
- `./god-writing/` (god-writing 素材)

これによりリポジトリは整理された skill ファイルのみを保持する。

## Consequences

### Positive

- HELIX skill catalog が 107 → 111 skill に拡張
- L1 要件定義 phase に doc-system-architect (体系設計) + requirements-deriver (非機能要件導出) が追加され、AI のシングルテナント固定化問題が関所で防がれる
- L5 Visual Refinement phase に god-writing (LP/FE 統合) + gpt-image (Codex CLI で画像生成) が追加され、FE 駆動 workflow が大幅強化
- references 数が 121 → 221+ に増加 (god-writing の 97 + gpt-image の 4 など)
- WebSearch 証拠を inline 反映する HELIX format が「ユーザー素材 → HELIX 化」の標準パターンとして確立

### Negative

- writing/ カテゴリ内で既存 skill と god-writing の重複が許容され、将来統合の負債が積み上がる
- gpt-image の Pricing は token-based のため、Codex 委譲時のコスト見積もりが non-trivial (本 skill 内に「事前見積もり推奨」を明記)
- god-writing は 964K の巨大 skill で、helix skill catalog rebuild の indexing コストが増加
- 元素材の interview/ カテゴリは当初指示の「9 カテゴリ」に含まれていなかったが実在 file として正規収録 (10 カテゴリに拡張)

### Neutral

- SKILL_MAP.md に新規セクション 2 件追加 (ドキュメント体系系 / LP・FE・画像生成系 の責務境界クリア化)
- helix skill catalog rebuild が必要 (次 wave で実施)

## Alternatives Considered

### A1: 既存 skill との重複を解消してから統合

god-writing と既存 writing/japanese / explain / social / story の重複領域を整理してから god-writing を投入する案を検討。**却下**: 統合作業が肥大化し、ユーザー指示 (素材を skill 化) を満たすまでの時間が大幅増加。重複許容 + 棲み分けで先行投入、将来統合は別 PLAN で扱う方が PR スコープ管理上正解。

### A2: gpt-image を GPT Image 1.5 ベースで投入してから GPT Image 2 に更新

ユーザー指摘の前に GPT Image 1.5 ベースで一旦投入し、後から更新する案。**却下**: ユーザー指示「Codex 搭載が 2.0」を満たさない時間ができ、skill の整合性が崩れる。同 session 内で 2.0 ベースに全面更新する選択を採った。

### A3: 元素材ディレクトリを skills/ に直接 move

`./files (4)/` をそのまま `skills/external/` に move する案。**却下**: HELIX format 統一 (frontmatter / triggers / verification / 責務境界) を満たさず、helix skill catalog の LLM マッチングに乗らない。HELIX format 変換 + references/ 構造化が必須。

## Implementation

### 完了済 (本 PR、commit 予定)

- [x] skills/workflow/doc-system-architect/SKILL.md (201 行) 起草
- [x] skills/workflow/requirements-deriver/SKILL.md (271 行) 起草
- [x] skills/design-tools/gpt-image/SKILL.md (GPT Image 2 ベース) + references/ 4 file 起草
- [x] skills/writing/god-writing/SKILL.md (313 行) + references/ INDEX.md + 97 file full copy
- [x] SKILL_MAP.md に 4 skill 追加 (workflow/ + writing/ + design-tools/ row)
- [x] SKILL_MAP.md に責務境界 section 2 件追加 (ドキュメント体系系 / LP-FE-画像系)
- [x] SKILL_MAP.md スキル数 107 → 111 / references 121 → 221+ に更新
- [x] ADR-035 (本 file) 起草

### 残作業 (本 session 内継続)

- [ ] 元の 3 ディレクトリ削除 (`./files (4)/` / `./gpt-image/` / `./god-writing/`)
- [ ] helix skill catalog rebuild (`helix skill catalog rebuild`)
- [ ] helix skill search 動作確認 (各 skill の LLM マッチング検証)
- [ ] commit + push

## References

### WebSearch evidence (本 ADR 根拠、PLAN-087 ガード遵守)

#### doc-system-architect 起草時 (3 query 実施済)
- ISO IEC IEEE 42010:2022: iso.org/standard/74393, ieee.org standards/42010
- IPA 非機能要求グレード 2018: ipa.go.jp/archive/digital/iot-en-ci/jyouryuu/hikinou/
- Diátaxis 2026 update: diataxis.fr/start-here/, idratherbewriting.com

#### gpt-image 起草・更新時 (3 query 実施済)
- GPT Image 2 official: openai.com/index/introducing-chatgpt-images-2-0/, developers.openai.com/api/docs/models/gpt-image-2
- Codex CLI integration: codex.danielvaughan.com/2026/04/27/codex-cli-image-generation-gpt-image-2-visual-development-workflows/, developers.openai.com/codex/cli
- Pricing & resolution: imagine.art/blogs/gpt-image-2-pricing, mindwiredai.com/2026/04/22/what-is-gpt-image-2-the-complete-breakdown-features-pricing-and-who-gets-access/

#### god-writing 起草時 (2 query 実施済)
- LP copywriting frameworks: universaldigitalservices.com/copywriting-formulas-aida-pas-convert/, landy-ai.com/blog/landing-page-copywriting-frameworks, thrivethemes.com/copywriting-formulas/
- UX writing microcopy: ericwongcontentstrategist.com 2026 guide, useronboarding.academy/post/onboarding-ux-writing, technicalwriterhq.com/writing/ux-writing/

### 関連 ADR / PLAN

- PLAN-087 (Web 検索ガードレール framework、起草時遵守)
- PLAN-101 (PreToolUse hook session_id fallback、本 ADR Write 動作前提)
- ADR-033 (design-doc-guard-session-id-fallback、PLAN-101 の L2 snapshot)

## Validation

helix doctor 24 pass / 0 fail / 79-80 warn を維持すること。helix skill catalog rebuild で 4 skill が認識されること (helix skill list で確認)。
