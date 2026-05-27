---
plan_id: L1-helix-workflows-要求定義移行plan
title: "L1-helix-workflows-要求定義移行plan: L0 企画 → L1 要求への移行 (L1-IN 採択判断)"
kind: requirements
layer: L1
drive: be
status: draft
created: 2026-05-28
owner: PM
process_layer: L1
parent_process: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 採択判断・移行 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — L1-IN trace 整合チェック"
generates:
  - artifact_path: docs/plans/L1/L1-helix-workflows-要求定義移行plan.md
    artifact_type: doc_update
dependencies:
  parent: L0-helix-workflows-conceptplan
  requires:
    - L0-helix-workflows-conceptplan
  blocks:
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
related_docs:
  - docs/v2/L0-helix-workflows/concept.md
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
  - docs/v2/L1-requirements/helix-workflows-nfr.md
---

# L1-helix-workflows-要求定義移行plan: L0 企画 → L1 要求への移行

> **工程**: L0 → L1 移行 (工程間移行 PLAN)
> **正本**: HELIX-workflows/HELIX-process-L0-L14.md
> **本 PLAN の対象**: L0 企画書 §8 の L1 バトン (L1-IN-01〜22) を**どう詰めて採択/保留/見送り判断し、採択分を L1 4 doc に振り分けるか**の進め方 + 採択判断の軌跡。
>
> **起票理由 (2026-05-28)**: ユーザー指摘「L0 から L1 に行くのに本当はプランがいるのに、それをやっていない」。従来 L1-IN の採択判断は L0 §8 AC-07 (企画書 doc の中) に埋もれ、L0→L1 移行を進める PLAN として独立していなかった。そのため差分 (grep) だけで「L1-IN-16/17 がクリア漏れ」と早合点する事故が発生 ([[feedback_vmodel_pair_judge_by_trace_not_file]])。本 PLAN は L0 §8 の採択判断を移行 PLAN の要点書に昇華し、採択/保留/見送りを一目で trace 可能にする。

## §1 工程表 (進め方)

| Step | 作業 | 進捗 |
|---|---|---|
| 1 | L0 §8 の L1-IN-01〜22 を精読 | ☑ completed (2026-05-28) |
| 2 | 各 L1-IN を採択/保留/見送り判断 | ☑ completed (L0 §8 で確定済、本 PLAN §2 に集約) |
| 3 | 採択分を L1 4 doc (業務/機能/技術/非機能要求) に振り分け | ☑ completed (L1 4 doc §5 で実施済) |
| 4 | 保留分の確認事項を整理 (ヒアリングシート) | ☑ completed (§3) |
| 5 | L1 4 PLAN へバトン (blocks) | ☑ completed (frontmatter dependencies.blocks) |

## §2 要点書 (L1-IN-01〜22 採択判断の軌跡)

> 振り分け先 (機能要求 FR-* / 業務要求 BR-* / 技術要求 / 非機能要求 NFR-*) は L1 4 doc の対応、詳細振り分けは L1 4 doc が正本 (本 PLAN は判断軌跡の集約であり、要求内容を重複記載しない)。

### 採択 17 件 (§8.1)

| L1-IN | 判断 | 主振り分け先 | 内容 / 理由 (L0 §8) |
|---|---|---|---|
| L1-IN-01 | 採択 | 機能要求 FR-01 | NSM 計測 (6 axes V-model 整合) |
| L1-IN-02 | 採択 | 機能要求 FR-02 | Guardrail 3 軸 fail-close |
| L1-IN-03 | 採択 | 機能要求 FR-12 | PLAN dependency / generates trace |
| L1-IN-04 | 採択 | 機能要求 FR-08 | 4 artifact / pair freeze 監査 |
| L1-IN-05 | 採択 | 機能要求 FR-11 | discrepancy routing |
| L1-IN-06 | 採択 | 機能要求 FR-09 | 資産 inventory / density 可視化 |
| L1-IN-07 | 採択 | 機能要求 FR-10 | layer context injection |
| L1-IN-08 | 採択 | 機能要求 FR-07 | Forward 復帰 event (Reverse Gateway 経由必須) |
| L1-IN-09 | 採択→carry | 技術要求 §8 + L4 詳細化 | PLAN template 手順書化 (FR 化せず carry、functional-requirements §4 が正本。tl-advisor P1 反映) |
| L1-IN-10 | 採択 | 機能要求 FR-11 | discrepancy routing |
| L1-IN-11 | 採択 | 機能要求 FR-03 | TDD 順序 fail-close |
| L1-IN-12 | 採択 | L1 4 doc §5 参照 | 排泄系 (不要 PLAN/skill/hook の auto-deprecation) |
| L1-IN-18 | 採択 | 業務要求 BR-09 | 既存資産整理・マッピング (implementation_status 列必須) |
| L1-IN-19 | 採択 | 業務要求 BR-10 | 既存資産の段階移行・retrofit (Strangler Fig) |
| L1-IN-20 | 採択 | 業務要求 BR-11 | doc 品質レビュー継続化 (doc-reviewer role) |
| L1-IN-21 | 採択 | 業務要求 BR-12 | デグレ禁止ガードレール (上流→下流追随 ratchet) |
| L1-IN-22 | 採択 | 機能要求 FR-13 | PLAN 起票レビュールール (起票時 TL 自動相談、ユーザー負担最小化。2026-05-28 遡及追加) |

### 保留 3 件 (§8.2、L1/L3 で確定)

| L1-IN | 判断 | 内容 |
|---|---|---|
| L1-IN-13 | 保留 | Phase α/β/γ 境界 KGI 確定 (3 段分割 must/should/later + kill criteria) |
| L1-IN-14 | 保留 | 専門エージェント / team 構造の Phase 配分 |
| L1-IN-15 | 保留 | 逆引き audit 11 穴の段階対応 (P1/P2/P3) |

### 見送り 2 件 (§8.3)

| L1-IN | 判断 | 見送り理由 |
|---|---|---|
| L1-IN-16 | 見送り | 新 paradigm (Stream-aligned 等) 移行 — HELIX-workflows V2 をそのまま使う方針確定 |
| L1-IN-17 | 見送り | 二軸 NSM (Tech + Marketing 並列) — Primary 1 件絞り原則に反する |

## §3 ヒアリングシート (保留 3 件の確認事項)

L1/L3 で確定すべき事項を蓄積 (auto mode で都度チャットせず、ここで保留):

- [ ] **L1-IN-13** Phase 境界 KGI: must/should/later 各層の閾値 (warn 数 / drift 数) と kill criteria の具体値
- [ ] **L1-IN-14** team 構造: 専門エージェント / team scaling をどの Phase に配分するか (memory carry §9 P1.5)
- [ ] **L1-IN-15** 逆引き 11 穴: P1 (進化/繁殖/老化/共生/代謝) / P2 / P3 の優先順位と着手 Phase

## §4 DoD (移行完了条件)

- ☑ L1-IN-01〜22 全 22 件の採択判断が本 PLAN §2 に集約されている
- ☑ 採択 16 件の主振り分け先が示され、詳細は L1 4 doc §5 を正本として参照
- ☑ 保留 3 件の確認事項が §3 ヒアリングシートに整理されている
- ☑ 見送り 2 件の理由が明示されている (早合点防止)
- ☑ L1 4 PLAN へ blocks でバトンが渡されている

## §5 関連 / 再発防止

- 本 PLAN 不在による早合点事故: [[feedback_vmodel_pair_judge_by_trace_not_file]] (grep 差分だけで判定せず採択判断記録を確認)
- 工程間移行 PLAN の原則: L0→L1 だけでなく L1→L3 / L3→L4 ... 各工程移行に同様の「採択/詰め判断 PLAN」が要る (ユーザー 2026-05-28「企画書から情報をどう詰めて要求を確定させるのか = これがプラン」)
- recovery-log §5 デグレ判定 (重複追加検出) と対: 既存判断の集約を怠ると早合点・重複起票が起きる
