---
plan_id: PLAN-110
title: helix doctor warn 漸減 framework (80→30-40 目標)
status: draft
kind: refactor
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — Sprint .1 warn 分類・check 別集計・対応方針ドラフト"
  - role: tl-advisor
    slot_label: "TL adversarial check — Sprint .2 対応方針 A/B/C 妥当性確認"
  - role: se
    slot_label: "SE — Sprint .3 修正実装 (lint 緩和 / 設計修正) + test 追加"
  - role: qa
    slot_label: "QA — Sprint .4 regression 確認・warn 件数達成検証"
generates:
  - artifact_type: python_module
    path: cli/lib/helix_doctor.py
  - artifact_type: config
    path: .helix/doctor-suppress.yaml
  - artifact_type: design_doc
    path: docs/adr/ADR-038-helix-doctor-warn-policy.md
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr:
  - ADR-038-helix-doctor-warn-policy
related_docs:
  - cli/lib/helix_doctor.py
  - cli/helix-doctor
  - docs/plans/PLAN-077-sprint-plan-standardization.md
  - docs/plans/PLAN-076-subagent-phase-mapping.md
acceptance_criteria:
  - "helix doctor 実行後 warn 件数が 30-40 以下 (現行 80 warn から 50%+ 削減)"
  - "helix doctor pass 件数が現行以上 (regression なし)"
  - "helix doctor fail 0 件維持"
  - "warn 分類表が ADR-038 に文書化されており A/B/C 対応方針が凍結済"
  - "acceptable warn を白名リスト化する .helix/doctor-suppress.yaml が機能する"
  - "月次 sweep PLAN (PLAN-110-followup) として carry 記録済"
---

# PLAN-110: helix doctor warn 漸減 framework (80→30-40 目標)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-038** で凍結 (Sprint .2 で採用方針確定後に起票):

- warn check 別の対応方針分類 (A: 修正必要 / B: lint 緩和 / C: 白名)
- `.helix/doctor-suppress.yaml` 白名リストの設計方針
- lint 緩和対象 check の閾値変更ポリシー
- 月次 sweep 継続化の運用ルール

## 背景

本 session (2026-05-23) 現在の `helix doctor` 出力:

```
passed: 24
failed: 0
warnings: 80 (本 session 末時点 / 82 件から微減)
```

warn 件数は累積的に増加しており、以下の運用上の問題を生じている:

1. **visibility 低下**: 80 warn があると新規 warn の発生に気づきにくい
2. **lint の形骸化**: 件数が多すぎて「warn = 見逃してよい」という暗黙認識が定着するリスク
3. **sprint 単位の品質確認**: Sprint .6 mandatory in sprint で `helix doctor` を実行しても
   80 warn の中から新規 warn を目視で探す必要があり、効率が低い

**目標**: warn を **30-40 件** まで漸減し、warn が「対処すべき指摘」として機能する状態を回復する。

一括修正ではなく、warn の性質を分類した上で:

- 修正が正当な warn は修正する (案 A)
- lint 閾値が過剰な warn は緩和する (案 B)
- 設計上 acceptable な warn は白名リスト化する (案 C)

の 3 経路で対処し、ADR-038 で方針を凍結する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **内部 lint ツールの整理** であり、外部ライブラリ / 業界 standard への
新規依存なし。WebSearch **skip**。

skip 理由: helix doctor は HELIX 独自 lint ツールであり、check の改善は
既存 PLAN (PLAN-076 / PLAN-077 等) の設計意図に基づく内部判断のみで完結する。

## warn 分類 framework

### 3 つの対応方針

| 方針 | 概要 | 適用条件 | 期待削減 |
|---|---|---|---|
| **A: 修正必要** | warn が示す実態 (drift / stale / 欠落) を修正する | warn 内容が実際の問題を指しており、修正コストが低い | 高 (修正後 warn 消滅) |
| **B: lint 緩和** | check 閾値 / 条件が過剰であり、現実に合わせて緩和 | 設計当時の想定と運用実態が乖離しており、fix より緩和が正当 | 中 (check の許容範囲拡大) |
| **C: 白名 (acceptable)** | warn は正確だが、設計上 acceptable な状態として恒常的に許容する | 修正不能 / 修正不要 / 故意の状態 | 低 (suppress yaml で非表示化) |

### 白名リスト設計

`.helix/doctor-suppress.yaml` で warn を抑制する:

```yaml
# .helix/doctor-suppress.yaml
# 設計上 acceptable な warn を白名リスト化する
# 各 entry は check_id + optional reason で構成

suppressed:
  - check_id: check_subagent_phase
    pattern: "pmo-haiku"
    reason: "on-demand subagent は工程必須ではない (PLAN-076 §on-demand 分類)"
  - check_id: check_sprint_completion
    pattern: "PLAN-100"
    reason: "PLAN-100 は completed 状態で carrier 管理不要"
```

白名エントリは ADR-038 に記録し、定期 sweep (月次) で見直す。

## 実装計画

### Sprint .1: warn 全件分類 (PMO Sonnet 委譲、size S)

**目的**: `helix doctor --json` で全 warn を構造化取得し、check 別に集計・分類する。

実施内容:

1. `helix doctor --json` または `helix doctor 2>&1` で全出力を取得
2. check_id (warn メッセージの prefix または分類) 別に件数集計
3. 上位 10 check を特定 (件数 top)
4. 各 check について:
   - 発火条件を `cli/lib/helix_doctor.py` で確認
   - 発火根拠となる PLAN / ADR を特定
   - 対応方針 A/B/C の初期分類を付与
5. 分類結果を本 PLAN §warn 分類表 (Sprint .1 更新) に追記

Sprint .1 完了条件:

- warn 80 件の分類表が完成 (check_id / 件数 / 初期方針 A/B/C / 根拠 PLAN)
- 案 A (修正) / 案 B (緩和) / 案 C (白名) の候補件数が判明

### Sprint .2: 対応方針確定 + ADR-038 凍結 (Opus + tl-advisor)

**目的**: Sprint .1 の分類を踏まえて各 check の対応方針を確定し、ADR-038 で凍結する。

実施内容:

1. Sprint .1 の分類表を Opus がレビューし、推奨方針を確定
2. tl-advisor 召喚:
   ```
   helix codex --role tl-advisor --task "helix doctor warn 分類方針 A/B/C の adversarial check。
   各 check の閾値緩和 (案 B) が PLAN-076/077 の設計意図に反しないかを確認してほしい。
   分類表 [添付] の方針に懸念があれば指摘すること。"
   ```
3. tl-advisor 助言を踏まえて最終方針確定
4. ADR-038 起票 (方針凍結 + 各 check の処理方針を記録)

Sprint .2 完了条件:

- ADR-038 が accepted 状態で存在
- 各 check の対応方針が 1 つに確定している
- 目標 30-40 warn 達成が見込める修正計画が立案済

### Sprint .3: 修正実装 3 wave 並列 (Codex se 委譲、size M)

**目的**: ADR-038 で凍結した方針に基づき、3 経路で並列修正を実施する。

#### Wave A: 案 A (修正) — Codex se

対象: 実際の drift / stale / 欠落が原因の warn を修正する。

実施内容例 (Sprint .1 結果で確定):

- stale sprint entry の cleanup
- 欠落 ADR index entry の補完
- check が期待する frontmatter field の追加 (PLAN doc retrofit)

mandatory: 修正後に `helix doctor` で対象 warn が消えることを確認。

#### Wave B: 案 B (lint 緩和) — Codex se

対象: check 閾値が過剰な warn を緩和する。

実施内容例:

- `check_subagent_phase` の mandatory subagent リストを PLAN-076 現行仕様と
  照合し、on-demand 4 種が誤って mandatory と判定されている場合は除外リスト更新
- `check_sprint_completion` の completed PLAN を warn 対象外にする条件追加
- warning threshold の数値調整 (例: warn を出す warn 件数下限を引き上げ)

mandatory: 緩和後に意図した warn のみが残ることを確認。

#### Wave C: 案 C (白名) — Codex se

対象: 設計上 acceptable な warn を suppress する。

実施内容:

1. `.helix/doctor-suppress.yaml` 新規作成 (schema 設計含む)
2. `cli/lib/helix_doctor.py` (または `cli/helix-doctor`) に suppress yaml 読み込みロジック追加:
   - suppress.yaml に一致する warn は出力から除外
   - 除外数をサマリに表示 (`suppressed: N`)
3. suppressed warn の一覧を `helix doctor --show-suppressed` オプションで確認可能にする

mandatory: `python3 -m py_compile cli/lib/helix_doctor.py` PASS

Sprint .3 完了条件 (3 wave 共通):

- 各 wave の対象 warn が消滅または suppress 済
- `helix doctor` pass 件数が Sprint .2 時点以上
- `helix doctor` fail 0 件維持

### Sprint .4: 検証 + 月次 sweep 記録 (Codex qa 委譲、size S)

**目的**: 3 wave の修正結果を検証し、目標 warn 件数達成を確認する。

実施内容:

1. `helix doctor` 全件実行 → warn 件数確認 (目標 30-40)
2. regression 確認:
   - pass 件数が Sprint .1 時点以上であること
   - fail 0 件維持
3. 新規 warn が発火するケースを smoke test で確認 (修正 Wave A/B で誤って check が
   無効化されていないことを確認)
4. 月次 sweep carry 記録:
   - PLAN-110-followup を次 session carry として memory に記録
   - 定期 sweep の目安: 月 1 回 (新 PLAN 起票ペースに合わせて)

Sprint .4 完了条件:

- `helix doctor` warn 件数が 30-40 以下
- pass 件数 24+ 維持
- fail 0 件維持

## warn 分類表 (Sprint .1 更新予定)

本 PLAN 起票時点では `helix doctor` の出力構造から推定した暫定分類:

| check_id (推定) | 推定件数 | 初期方針 | 根拠 PLAN |
|---|---|---|---|
| check_subagent_phase | 高 (~20) | B or C | PLAN-076 (mandatory 10 種 / on-demand 4 種) |
| check_sprint_completion | 中 (~15) | A or C | PLAN-077 (Sprint 標準 8 ステップ) |
| check_adr_index | 中 (~10) | A | ADR index.md との drift |
| check_plan_adr_snapshot | 中 (~10) | A | PLAN-087〜090 ADR snapshot 未追加 (次 session carry 既知) |
| check_recovery_plan_freshness | 低 (~5) | C | 設計上 acceptable (session 終了前チェック由来) |
| その他 | 低 (~20) | TBD | Sprint .1 で確定 |

注: 数値は Sprint .1 の `helix doctor --json` 取得前の推定値。Sprint .1 で実数に更新する。

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/helix_doctor.py` PASS (Sprint .3 Wave C 後)
- [ ] `helix doctor` fail 0 件維持
- [ ] `helix doctor` pass 件数が現行以上
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .4 完了時)
- [ ] ADR-038 accepted 状態で exists (Sprint .2 完了時)
- [ ] commit message に `PLAN-110 sprint .X` 明示

## DoD (Definition of Done)

- [ ] warn 分類表 (Sprint .1 結果) が ADR-038 に記録済
- [ ] 対応方針 A/B/C が tl-advisor adversarial check を通過し ADR-038 で凍結済
- [ ] Wave A: 修正対象 warn が消滅している
- [ ] Wave B: lint 緩和対象 check の閾値調整済
- [ ] Wave C: `.helix/doctor-suppress.yaml` が機能し、白名 warn が suppress されている
- [ ] `helix doctor --show-suppressed` で suppress 済 warn を確認可能
- [ ] warn 件数 30-40 以下 (現行 80 から 50%+ 削減)
- [ ] pass 件数 24 以上維持
- [ ] fail 0 件維持
- [ ] ADR-038 snapshot 起票済 (accepted)
- [ ] 月次 sweep carry (PLAN-110-followup) が memory に記録済

## carry / 学び (起票時記録)

- **Sprint .1 前の warn 実数未確定**: 本 PLAN 起票時点では warn 80 件の内訳が
  未確認。Sprint .1 で `helix doctor --json` を取得してから修正方針を確定する。
  白名 / 緩和の割合次第では目標 30-40 が Sprint .3 一回では達成できない可能性あり。
  その場合は PLAN-110-followup (次月 sweep) に残件を carry する
- **check_plan_adr_snapshot の大量 warn**: PLAN-087〜090 / PLAN-087〜098 範囲の
  ADR snapshot 未追加 warn は「次 session carry 既知」として CLAUDE.md に記録済。
  本 PLAN Sprint .3 Wave A で一括解消できる可能性が高い
- **suppress yaml の設計**: `.helix/doctor-suppress.yaml` は suppress エントリを
  永続化するため、suppress 数の増加管理が必要。suppress 件数が増えすぎると
  白名化により問題が見えなくなるリスクあり。ADR-038 で suppress 件数の上限ガイドライン
  (例: suppress ≤ warn total の 30%) を設定することを Sprint .2 で検討する
- **helix_doctor.py の suppress 読み込み追加**: Wave C は `cli/lib/helix_doctor.py` か
  `cli/helix-doctor` (bash) のどちらに suppress logic を追加するかは
  Sprint .1 でファイル構造を確認してから決定する。Python module の場合は
  py_compile + unit test が mandatory、bash の場合は bash -n + bats が mandatory

## 関連 reference

- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否判定、本 PLAN は Sprint .2 後起票)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_recovery_plan_kind_missing]] (helix doctor check_recovery_plan_freshness 由来 warn)
- ADR-038 (本 PLAN tree の L2 snapshot、Sprint .2 で起票)
- PLAN-076 (subagent 工程マッピング、check_subagent_phase の根拠)
- PLAN-077 (Sprint Plan 標準構造、check_sprint_completion の根拠)
- PLAN-087 (Web 検索ガード framework)
- cli/lib/helix_doctor.py (warn check 実装の正本)
