---
doc_id: L1-helix-workflows-business-requirements
title: "HELIX-workflows V2 業務要求 (Business Requirements)"
status: draft
created: 2026-05-26
owner: PM
process_layer: L1
pairs_with: L14
next_pair_freeze: L3
canonical_source: HELIX-workflows/helix-process/L1-requirements.md
parent_plan: L1-helix-workflows-業務要求plan
pair_artifact: docs/v2/L14-test-design/helix-workflows-operational-test-design.md
related_l0: docs/v2/L0-helix-workflows/concept.md
---

# HELIX-workflows V2 業務要求 (Business Requirements)

> **本 doc の位置づけ**: HELIX-workflows V2 完全移行後の dogfooding における **業務要求 (BR-*)** 正本。L0 [見直し企画書](../L0-helix-workflows-concept.md) §8 L1 バトン 17 件のうち業務要求 scope (L1-IN-03/04/05) を Business Requirements 形式に再整理。L14 [運用テスト設計](../L14-test-design/helix-workflows-operational-test-design.md) と V-model **L1↔L14 ペア凍結**。
>
> **scope**: 業務要求 (WHY / WHAT / WHO / 業務フロー / ステークホルダー / 現状課題 → あるべき姿) まで。**機能要件 (FR)** は L3 で、**システム機能設計** は L4-L6 で、**実装** は L7 で行う (アンチパターン: L1 で FR に飛び込むな、`docs/v2/process/L01` §アンチパターン参照)。

## §1 目的・背景 (WHY / WHAT / WHO)

### §1.1 WHY (なぜ)

HELIX-workflows V2 完全移行 (2026-05-24) で「道」は確立されたが、HELIX 自身がその道を走っていない (**dogfooding 不在**)。47 doc / 60 CLI / 118 skill / 30+ helix.db table の累積資産が散在し、AI agent が独自判断で進めるたびに drift と warn が積み上がる (warn 86 件 / pair freeze warn 11 件 / 4 artifact trace warn 86 件、L0 §2 課題 10 軸)。

業務要求の核心は **「AI 暴走を機械配線で抑止しつつ、人間 PM が大局判断に集中できる開発業務」** を確立すること。具体的には:

1. **AI 独自判断の機械削減**: 配線で 70-90% の分岐を機械判定し、AI 判断は設計の良し悪し等の質的判断に限定 (L0 §6.5.4 Diagram 4)
2. **量閉じ性で資産保全**: V-model 設計⇔テストペア凍結を `balance_ratio = test_count / design_count ≥ 1.0` で構造保証 (L0 §5.3、Chargaff's rule 比喩)
3. **9 mode → Forward 回帰**: Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery の全 mode が最終的に Forward L0-L14 に収束 (L0 §6.5.2 Diagram 2)
4. **影響範囲分析**: 機能改修時に「ここだけ / 広めに」を helix.db query で 5 秒以内に機械判定 (L0 §5.3 Cascade KPI)

### §1.2 WHAT (何を)

HELIX-workflows V2 全 47 doc を **dogfooding 工程** として走らせる業務。具体的には L0 [見直し企画書](../L0-helix-workflows-concept.md) で示した 13 工程 (L0/L1/L3/L4/L5/L6/L7/L8/L9/L11/L12/L13/L14、L2/L10 skip) を HELIX 自身に適用する **自己適用業務**。

### §1.3 WHO (誰が)

- **主要利用者**: HELIX 自身を改善開発する **PM (人間 + Opus)** および **TL/SE (Codex)**
- **採用者**: HELIX-workflows V2 を採用する各 project owners (PM/TL/SE/QA)
- **間接利用者**: HELIX が生成する PLAN / doc を読む後続 team / 経営層 / 外部 reviewer

## §2 対象業務一覧

| BR-ID | 業務名 | scope | priority |
|---|---|---|---|
| BR-01 | **dogfooding 開発業務** | HELIX 自身の改善開発を HELIX-workflows V2 の 13 工程 (L0/L1/L3-L9/L11-L14) で進行 | P0 |
| BR-02 | **4 artifact retrofit 業務** | 既存 PLAN 324 件の 4 artifact 双方向 trace を段階 retrofit (warn 86 → 20 以下、Phase α 完了条件) | P0 |
| BR-03 | **drift 解消業務** | HELIX-workflows ↔ cli/helix-* ↔ skill 118 ↔ helix.db schema の drift を常時検出 + 解消 | P0 |
| BR-04 | **9 mode 入口判定 + Forward 回帰業務** | 各 mode 入口で detector 機械判定、closure 時に Forward 復帰 event を helix.db 登録 | P1 |
| BR-05 | **ペア凍結監査業務** | V-model 設計⇔テスト ペア凍結 (L1↔L14, L3↔L12, L4↔L9, L5↔L8, L6↔L7単体) の量閉じを週次計測 | P1 |
| BR-06 | **影響範囲分析業務** | 機能改修時に過去 trace を helix.db query で 5 秒以内に retrieve、変更影響を可視化 | P1 |
| BR-07 | **AI agent 配線業務** | 工程別 skill / mandatory subagent / 推奨 command を vmodel-semantics.yaml で機械注入、AI 判断の選択空間を絞る | P1 |
| BR-08 | **採用 project への展開業務** | HELIX V2 を採用する他 project が同じ道を走れるよう CLI + skill + template を維持・配布 | P2 |

## §3 業務フロー (Forward V-model 主線 + 9 mode 分岐)

### §3.1 主線 (Forward V-model、HELIX-workflows は L2/L10 skip で 13 工程)

```
L0 企画 → G0.5 → L1 要求定義 + 運用テスト設計 → G1
       → (L2 画面設計 skip)
       → L3 要件定義 + 受入テスト設計 → G3
       → L4 基本設計 + 総合テスト設計 → G4
       → L5 詳細設計 + 結合テスト設計 → G5
       → L6 機能設計 + 単体テスト設計 → G6
       → L7 実装スプリント (7 step TDD) → G7
       → L8 結合テスト → G8
       → L9 総合テスト → G9
       → (L10 UX 磨き skip)
       → L11 総合レビュー → G11
       → L12 デプロイ + 受入テスト → G12
       → L13 安定性 → G13
       → L14 運用検証 → G14
```

### §3.2 9 mode 分岐 (入口判定 + Forward 復帰)

| 入口 trigger | mode | Forward 復帰経路 |
|---|---|---|
| 要件未確定 / 仮説検証 | Discovery (D0→D4) | confirmed → L1 |
| 要件すり合わせ反復 | Scrum (sprint 反復) | 完成機能 → Reverse fullback → L1 |
| 既存コード逆引き | Reverse (R0→R4 + RGC) | R4 Gap → L1/L3/L4-L6 |
| 本番障害 hotfix | Incident | hotfix → L7 / permanent → L1/L3/L4-L6 / postmortem → L14 (3 経路並走可) |
| 既存に機能追補 | Add-feature | add-design → L4 / add-impl → L7 |
| 振る舞い不変改善 | Refactor | 完了 → L7 |
| 基盤改修 / 移行 | Retrofit | matrix + config → L4 |
| 事前調査 / 意思決定 | Research | ADR 確定 → L1 |
| AI 暴走 + 収束 | Recovery | cutover 設計差戻 (L1/L3/L4-L6) + 実装差戻 (L7) |

### §3.3 cross-cutting 横断機構

任意工程・任意 mode 実行中に発火:
- **interrupt**: design_gap / new_requirement / constraint / po_change → helix-interrupt
- **debt**: code_smell / dead_code → helix-debt
- **drift-check**: D-API / D-CONTRACT / D-DB 乖離 → Reverse normalization mode
- **readiness**: deferred finding → 後工程 PLAN へ先送り (PM 承認)

## §4 ステークホルダー

| role | model | 主担当 | 責務 |
|---|---|---|---|
| **PM** | Opus 4.7 (Claude Code) | チャットのみ | 大局判断 / 言語化 / タスク分解 / 統合 / エスカレーション判断 / 実装承認 (実装禁止) |
| **PM-advisor** | Opus 4.7 (read-only) | PM 級難判断 | スコープ / 優先度 / 大局リスク / HELIX フェーズ整合 / 委譲先選択 |
| **TL** | Codex gpt-5.5 high | 設計 / レビュー / セキュリティ | 設計判断 / 技術選択 / ゲート判定 / レビュー |
| **TL-advisor** | gpt-5.5 high (read-only) | TL 級難判断 | 設計選択 / 契約 / テスト戦略 / リファクタ判断 |
| **SE** | Codex gpt-5.4 high | 高度実装 | 契約 / 複雑実装 / リファクタリング |
| **PE** | Codex gpt-5.3-codex-spark | 単機能実装 | 速度重視実装 |
| **QA** | Codex gpt-5.3 | テスト | 機能 / 性能 / 回帰テスト |
| **Security / DBA / DevOps / Perf** | Codex gpt-5.3 | セキュリティ / DB / インフラ / 性能 | OWASP / schema / CI / 性能監視 |
| **PMO Sonnet** | claude-sonnet-4-6 | 判断伴う read-only | 構造化チェック / 整合検証 / 長文 doc 解析 |
| **PMO Haiku** | claude-haiku-4-5 | 軽作業 | Web 検索 / `docs/**` 軽修正 |
| **採用 project owners** | (外部) | HELIX V2 採用 project の PM/TL/SE | 各 project の dogfooding 適用 |

## §5 現状課題 → あるべき姿

(L0 §2 課題 10 軸を業務観点で再整理)

| BR | 現状課題 | あるべき姿 | NSM/Guardrail/Cascade KPI |
|---|---|---|---|
| BR-01 dogfooding | HELIX 自身が HELIX-workflows V2 で開発されていない、L0 PLAN dir 不在まま V2 移行宣言 | 13 工程全 PLAN 起票 + 各工程 skeleton 完備、HELIX 自身を Forward V-model で開発 | NSM: V-model 整合 PLAN 完遂数 ≥ 50 / month (L0 §5.1) |
| BR-02 4 artifact retrofit | warn 86 件、設計 ↔ 実装 ↔ テスト設計 ↔ テストコード trace が advisory | 新規 PLAN は fail-close 必須、既存 PLAN は段階 retrofit、warn 20 以下 | KGI: Phase α 完了で warn ≤ 20 (L0 §5.4) |
| BR-03 drift 解消 | HELIX-workflows ↔ cli/helix-* ↔ skill ↔ helix.db schema の drift が随時発生、accumulate 一方 | 週次 detector 検出 + Reverse normalization mode で即時解消、新規 drift 0 維持 | KPI: drift detector 新規発生件数 = 0 / week (§OT-03) |
| BR-04 9 mode 回帰 | 9 mode closure 後の Forward 昇格が個別ばらつき | 9 mode 共通 R0-R4 + RGC 基盤、closure event helix.db 登録で機械昇格 | Cascade: 9 mode → Forward 回帰率 ≥ 95% (L0 §5.3) |
| BR-05 ペア凍結監査 | V-model pair freeze warn 11 件、parent_design / pairs_test_design 未指定 PLAN | 全 PLAN frontmatter 必須化、`balance_ratio = test_count / design_count ≥ 1.0` 機械検証 | Guardrail: Pair Freeze Coverage ≥ 80% (L0 §5.2 GR-1、fail-close) |
| BR-06 影響範囲分析 | 機能改修時に過去 trace 取得が手動、影響範囲が見えない | helix.db query 5 秒以内に過去 trace retrieve、4 artifact 双方向 trace で機械判定 | Cascade: 影響範囲 query 時間 ≤ 5 秒 (L0 §5.3) |
| BR-07 AI agent 配線 | 工程別 skill / mandatory / 推奨 command の機械注入が未完、AI が独自判断 | `vmodel-semantics.yaml` L 別注入セット正本化、helix-context が L 入る時に注入、helix doctor audit | Cascade: AI 判断削減率 ≥ 70% (L0 §5.3) |
| BR-08 採用展開 | HELIX V2 採用 project は self / 数件、再現性未確認 | 採用 project が同じ 13 工程を走れる、CLI/template 互換維持 | KGI: 採用 project 数 (Phase β 完了条件) |

## §6 業務スコープ外 (本 BR では扱わない)

- **機能要件 (FR)**: L3 要件定義で扱う → L1-helix-workflows-機能要求plan に振り分け
- **画面要件**: L2 skip により対象外 (HELIX-workflows は CLI 中心、UI なし)
  - 例外: docs site / visual mock / interactive UI を作る場合は L2/L10 unskip (L0 §8 L1-IN-03)
- **技術選択 / 制約**: L1-helix-workflows-技術要求plan に振り分け
- **非機能要件 (NFR)**: L1-helix-workflows-非機能要求plan に振り分け (IPA × ISO 25010)
- **詳細設計 / 実装**: L4-L7 で扱う

## §7 L14 運用テスト pair 対応表

(各 BR-* に対応する L14 OT-* を [helix-workflows-operational-test-design.md](../L14-test-design/helix-workflows-operational-test-design.md) で定義)

| BR-* | L14 OT-* | 検証タイミング |
|---|---|---|
| BR-01 dogfooding | OT-01 V-model 整合 PLAN 完遂数 | 毎週月曜 |
| BR-02 retrofit | OT-02 helix doctor warn 数月次推移 | 毎月末 |
| BR-03 drift 解消 | OT-03 drift detector 新規発生件数 | 毎週金曜 |
| BR-04 9 mode 入口判定 + Forward 回帰 | OT-04 mode_transition event 登録率 | 毎月末 |
| BR-05 ペア凍結監査 | OT-05 V-model ペア凍結 coverage (5 pair `balance_ratio`) | 毎週金曜 |
| BR-06 影響範囲分析 | OT-06 影響範囲 query 応答時間 | 機能改修 trigger 都度 |
| BR-07 AI agent 配線 | OT-07 vmodel-semantics.yaml 注入セット利用率 | 毎週月曜 |
| BR-08 採用 project 展開 | OT-08 採用 project dogfooding 稼働率 | 毎月末 |

> **L3 接続規約 (2026-05-26 tl-advisor G1 P1 #3 反映)**: 本 doc の業務要件は L3 で詳細化 (L3-helix-workflows-業務要件plan) され、L3↔L12 ペア凍結で `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` に業務系 AC-* を pair artifact 化する。L1↔L14 (運用テスト) + L3↔L12 (受入テスト) の二重 pair が業務要件の運用品質と受入品質を両面で保証。

## §8 関連 doc

- **上流 (L0 概念)**: [docs/v2/L0-helix-workflows/concept.md](../L0-helix-workflows-concept.md)
- **PLAN (本 doc を生成)**: [docs/plans/L1/L1-helix-workflows-業務要求plan.md](../../plans/L1/L1-helix-workflows-業務要求plan.md)
- **L14 ペア相手**: [helix-workflows-operational-test-design.md](../L14-test-design/helix-workflows-operational-test-design.md)
- **HELIX-workflows L1 正本**: [HELIX-workflows/helix-process/L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
- **L1 工程 doc**: [docs/v2/process/L01-requirements-and-operational-test-design.md](../process/L01-requirements-and-operational-test-design.md)
- **並走 PLAN** (Phase B で起票): L1-helix-workflows-{機能要求 / 技術要求 / 非機能要求}plan
- **下流 PLAN**: L3-helix-workflows-requirementsplan (本 PLAN + 並走 3 PLAN 完遂後)
- **skill**: workflow/requirements-handover / workflow/requirements-deriver / workflow/doc-system-architect

## §9 carry / 既知の不足

- ~~BR-04〜BR-08 の L14 OT-* 対応~~: **解消済 (2026-05-26 tl-advisor G1 adversarial P0 #1 反映)** — L14 doc §1 に OT-04〜OT-08 追加で BR/OT が 1:1 対応 (balance_ratio = 1.0)。
- 8 BR の優先度配分 (P0/P1/P2) は L0 §3 / §5 から導出。Phase α は P0 完遂 (BR-01/02/03)、Phase β で P1 完遂、Phase γ で P2 完遂。閾値は L1-IN-13 Phase α 三段分割案 (must/should/later + kill criteria) で確定。
- §3.1 業務フローの「G ゲート」は static_subchecks + AI 判定の合成式 (L0 §6.5.4)、L1-helix-workflows-技術要求plan で `gate-policy.yaml` 化。

### §9.1 L0 §8 保留 3 件 carry 一覧化 (L1-IN-13/14/15、tl-advisor P0 #3 反映)

L0 §8.2 で「保留 (L1/L3 で確定)」とされた 3 件のうち、本 L1 工程で carry を一覧化:

| 保留 ID | 内容 | 確定タイミング | 本 L1 工程での扱い |
|---|---|---|---|
| L1-IN-13 | Phase α/β/γ 境界 KGI 確定 + must/should/later 3 層分割 + kill criteria | L3 要件定義 (G3 凍結前) | 業務要求 doc §5 BR 優先度配分 + 本 §9 で部分言及、L3 で数値閾値確定 |
| L1-IN-14 | **専門エージェント / team 構造 (memory carry §9 P1.5) の Phase 配分** (チームアルゴリズム設計 / チームセキュリティ監査 / ドメインチェック自動化 / コーディングルール自動化等の team 編成) | L4 基本設計 (G4 凍結前) | 本 §9.1 carry のみ言及、L4 で team 構造 + 各 team の使用フェーズ + ROI 評価を確定 |
| L1-IN-15 | 逆引き audit 11 穴の段階対応 (P1 進化/繁殖/老化/共生/代謝 + P2 内分泌/循環/消化/性差 + P3 多細胞化/神経変性) | 段階対応 (P1 = L3-L4 / P2 = L7-L9 / P3 = L13-L14) | NFR doc §3 NFR-OP-04 進化系統 trace + 本 §9.1 carry で全 11 穴 + 階層的 deferment |
