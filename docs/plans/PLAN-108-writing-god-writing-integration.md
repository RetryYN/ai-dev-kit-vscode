---
plan_id: PLAN-108
title: writing/* と god-writing 統合 (重複領域整理・棲み分け確定)
status: draft
kind: retrofit
drive: be
layer: cross
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — Sprint .1 重複分析・責務境界確認"
  - role: tl-advisor
    slot_label: "TL adversarial check — 統合方針 A/B/C 判定 (Sprint .2)"
  - role: se
    slot_label: "SE — Sprint .3 skill 構造変更・helix doctor lint 追加 (採用案が C の場合)"
generates:
  - artifact_type: markdown_doc
    path: skills/writing/god-writing/SKILL.md
  - artifact_type: design_doc
    path: docs/adr/ADR-037-writing-god-writing-integration.md
  - artifact_type: markdown_doc
    path: skills/SKILL_MAP.md
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr:
  - ADR-037-writing-god-writing-integration
related_docs:
  - skills/writing/god-writing/SKILL.md
  - skills/writing/japanese/SKILL.md
  - skills/writing/explain/SKILL.md
  - skills/writing/social/SKILL.md
  - skills/writing/story/SKILL.md
  - skills/SKILL_MAP.md
acceptance_criteria:
  - "重複領域マップが文書化されている (Sprint .1 完了)"
  - "統合方針 A/B/C のうち 1 案が tl-advisor adversarial check を通過し ADR-037 で凍結"
  - "採用方針に応じて skills/ 構造が整理されており helix skill catalog rebuild が PASS"
  - "SKILL_MAP.md §責務境界クリア化 (LP/FE/画像生成系) が採用方針と整合"
  - "helix doctor pass 数が現行以上 (regression なし)"
  - "将来同様の重複に対する lint (helix doctor check_skill_overlap) が動作"
---

# PLAN-108: writing/* と god-writing 統合 (重複領域整理・棲み分け確定)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-037** で凍結 (Sprint .2 で採用方針確定後に起票):

- 統合方針の選択: 案 A (god-writing に full merge) / 案 B (現状維持) / 案 C (共通 references 新設)
- `skills/writing/_common/` 新設の要否
- 既存 `writing/japanese` 等の廃止 / 残置 / 縮退方針
- SKILL_MAP.md §責務境界クリア化 の更新範囲
- helix doctor check_skill_overlap lint の設計

## 背景

本 session (2026-05-23) で `skills/writing/god-writing/` を統合した
(313 行 SKILL.md + 97 references)。

god-writing は **9 カテゴリ統合の応用 LP 用途** として設計されており、
既存 `writing/*` との責務境界は SKILL_MAP.md §380-406 に明示済:

- `writing/japanese`: 基礎日本語 (god-writing references/japanese/basic/ と重複)
- `writing/explain`: 技術文書 4 部構成 + EEAT (god-writing references/technical/ と一部重複)
- `writing/social`: SNS 投稿テンプレート + GEO (god-writing references/copywriting/social-copy.md と一部重複)
- `writing/story`: ストーリーテリング (god-writing references/copywriting/storytelling.md と一部重複)
- `writing/presentation`: スライド資料 (god-writing 範囲外)

現在は「基礎用途 = 既存 writing/*、応用 LP 用途 = god-writing」の棲み分けで
運用中。中長期的に重複を整理し、将来統合 / 廃止の判断を確定させるため本 PLAN を起票する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は内部 skill 整理 (外部ライブラリ・業界 standard への依存なし) のため
WebSearch **skip**。SKILL_MAP §正本宣言・責務境界の内部資料のみを根拠とする。

skip 理由: 内部 skill 構造の整合 task であり、外部 API / フレームワーク /
業界 standard の採用判断を含まない。

## 重複領域マップ (現状)

| writing/* skill | god-writing 対応 references | 重複性 | 現状棲み分け |
|---|---|---|---|
| writing/japanese | references/japanese/basic/ (14 files) | 高 | japanese = 基礎 lint、god-writing = 応用修辞 |
| writing/explain | references/technical/ + references/seo/ (一部) | 中 | explain = 技術ブログ 4 部構成、god-writing = LP/SEO 記事 |
| writing/social | references/copywriting/social-copy.md | 中 | social = SNS 単発投稿、god-writing = セールスコピー統合 |
| writing/story | references/copywriting/storytelling.md | 低-中 | story = ストーリー単体、god-writing = コピー統合の一部 |
| writing/presentation | (対応なし) | なし | god-writing 範囲外 |

## 統合方針 3 案

| 案 | 概要 | メリット | デメリット | 採用条件 |
|---|---|---|---|---|
| **A: full merge** | writing/* を god-writing に吸収、presentation のみ残置 | skill 数削減 (5→2)、search 曖昧さ消滅 | 既存動線断絶、廃止 migration 必要 | writing/* 使用頻度が god-writing の 10% 以下 |
| **B: 現状維持** | SKILL_MAP §380-406 責務境界を ADR-037 で正式凍結 | 変更コストゼロ、二層構造が明確 | 重複増加で search 精度低下リスク | writing/* 利用実績あり廃止影響大 |
| **C: 共通 references 新設** | 重複 content を `skills/writing/_common/` に移動、両者が参照 | DRY 化、既存動線維持 | `_common/` 抽象層追加で複雑化 | 重複 content 量が無視できないレベル |

案 B が現状 SKILL_MAP §406 の「重複を許容して導入」方針と整合しており最有力。
Sprint .1 の使用頻度確認と Sprint .2 の tl-advisor 判定で最終決定。

## 実装計画

### Sprint .1: 重複領域詳細分析 (PMO Sonnet 委譲、size S)

**目的**: 上記重複領域マップを file レベルに深掘りし、統合方針の意思決定材料を揃える。

実施内容:

1. `writing/japanese / explain / social / story` の SKILL.md を Read
2. god-writing の対応 references (上記マップ参照) を Read
3. 各 file の uniqueness 分類:
   - `unique_to_existing`: 既存 writing/* にしか存在しないコンテンツ
   - `unique_to_god_writing`: god-writing にしか存在しないコンテンツ
   - `overlap`: 実質的に同じ content が両方にある
4. `helix skill stats --days 90` で writing/* の使用頻度確認
5. 分類結果を本 PLAN §重複領域マップ に追記 (Opus Edit)

Sprint .1 完了条件:

- 重複領域マップが file レベルに更新済
- uniqueness 分類が完了
- 使用頻度データが取得済

### Sprint .2: 統合方針確定 + ADR-037 凍結 (Opus + tl-advisor)

**目的**: Sprint .1 の分析結果を元に A/B/C いずれかを確定し ADR-037 で凍結。

実施内容:

1. Sprint .1 の分析結果を踏まえて推奨案を Opus が選定
2. tl-advisor 召喚: `helix codex --role tl-advisor --task "writing/* と god-writing 統合方針 A/B/C の adversarial check ..."`
3. tl-advisor の助言を踏まえて最終案確定
4. ADR-037 起票 (方針採用根拠 + 棄却案の理由 + 将来見直し条件)
5. SKILL_MAP §§380-406 を採用方針と整合する記述に更新

Sprint .2 完了条件:

- ADR-037 が accepted 状態で存在
- SKILL_MAP §責務境界 が採用方針と整合済

### Sprint .3: 採用方針の実装 (Codex se 委譲 or Opus 直接、案によって変化)

**目的**: ADR-037 で凍結した方針を skills/ 構造に反映する。

案 A の場合:
- writing/japanese / explain / social / story の SKILL.md を god-writing への redirect doc に変更
- SKILL_MAP の各 skill 説明を更新
- `helix skill catalog rebuild` + 動作確認

案 B の場合:
- Sprint .2 の SKILL_MAP 更新のみ (構造変更なし)
- 本 Sprint は実質 DoD 確認のみ

案 C の場合:
- `skills/writing/_common/` ディレクトリ新設
- 重複 references を _common/ に移動
- 各 SKILL.md の references path 更新
- `helix skill catalog rebuild` + 動作確認

全案共通:
- `helix skill catalog rebuild` で catalog 再生成 PASS
- `helix skill search "日本語文章を改善したい"` が期待 skill を返すこと確認

### Sprint .4: drift 検出 lint 追加 (Codex se 委譲、size S)

**目的**: 将来同様の重複が発生したら自動 WARN する機構を追加。

実装方針:

- `cli/lib/helix_doctor.py` (または相当 module) に `check_skill_overlap` 追加
- SKILL.md の `references:` セクションを parse して同一 path が複数 SKILL から参照される場合 WARN
- `helix doctor` の warn 数に加算 (fail-close ではなく advisory)
- 許容済重複 (B 案採用時は正当) は `_common/` 等の明示タグで WARN 抑制可能にする

Sprint .4 完了条件:

- `helix doctor check_skill_overlap` が動作
- 新たな重複追加時に WARN が発火することを test で確認

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `helix skill catalog rebuild` PASS (Sprint .3/.4 後)
- [ ] `helix doctor` pass 数が現行以上 (regression なし)
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] ADR-037 accepted 状態で exists (Sprint .2 完了時)
- [ ] commit message に `PLAN-108 sprint .X` 明示

## DoD (Definition of Done)

- [ ] 重複領域マップが file レベルに確定 (Sprint .1 完了)
- [ ] 統合方針 (A/B/C) が tl-advisor adversarial check を通過
- [ ] ADR-037 snapshot 起票済 (accepted)
- [ ] SKILL_MAP §責務境界 (§380-406) が採用方針と整合
- [ ] 採用方針に応じた skills/ 構造変更が完了
- [ ] `helix skill catalog rebuild` PASS
- [ ] `helix doctor check_skill_overlap` が動作し現行 warn に加算
- [ ] helix doctor pass 数が現行以上

## carry / 学び (起票時記録)

- **案 B (現状維持) が最有力**: SKILL_MAP §406 に「重複を許容して導入」と
  明示されており、基礎 / 応用の二層は意図的設計。Sprint .1 の使用頻度確認で
  writing/* の実績がゼロに近い場合のみ案 A を検討する
- **writing/presentation は god-writing 範囲外**: present skill は slide 用途専用で
  god-writing の LP / コピー領域と重複なし。いずれの案でも残置確定
- **catalog rebuild への影響**: 案 C は references path を変更するため
  catalog の既存 entry が stale になる可能性。rebuild 後の search 精度を
  Sprint .3 で必ず確認する
- **ADR-037 起票タイミング**: Sprint .2 で採用方針が確定してから起票。
  Sprint .1 の分析中は draft にしない (判断根拠が揃っていない状態で凍結しない)

## 関連 reference

- ADR-037 (本 PLAN tree の L2 snapshot、Sprint .2 で起票)
- ADR-035 (外部スキル統合 framework、god-writing 統合の前提)
- [[feedback_codex_docs_enum_inline_prompt]] (Codex 委譲時の enum 違反対策)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_adr_before_plan_violation]] (PLAN ⊃ ADR レイヤー併存、ADR-037 併設)
- SKILL_MAP.md §380-406 (現行責務境界クリア化 LP/FE/画像生成系)
- skills/writing/god-writing/SKILL.md (本 session 統合済、本 PLAN の整理対象)
- PLAN-087 (Web 検索ガード framework)
