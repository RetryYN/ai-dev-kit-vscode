---
plan_id: PLAN-225
title: "PLAN-225: L1 非機能要件標準の ISO/IEC 25010:2023 移行 retrofit (8→9特性 + IPA 位置づけ是正)"
layer: cross
kind: retrofit
status: completed
size: S
drive: be
created: 2026-05-30
completed_at: 2026-05-30
completion_commits:
  - "34fb0fa (L5/L6 IEEE Std 1016-2009 viewpoint mapping + 29119-4)"
  - "dadba03 (L1 skill 3 件 ISO/IEC 25010:2023 移行 + IPA 是正)"
owner: PM
agent_slots:
  - role: pmo-tech-docs
    slot_label: "外部精読 — 25010:2023 / IPA 正本確定"
  - role: pmo-tech-news
    slot_label: "動向 sweep — 25010:2023 最新性 / SQuaRE 周辺"
  - role: docs
    slot_label: "Docs — skill 標準参照更新 (本件は PM 直接編集で実施)"
generates:
  - artifact_path: skills/workflow/requirements-deriver/SKILL.md
    artifact_type: doc_update
  - artifact_path: skills/workflow/doc-system-architect/SKILL.md
    artifact_type: doc_update
  - artifact_path: skills/SKILL_MAP.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_docs:
  - HELIX-workflows/helix-process/retrofit-workflow.md
  - docs/plans/recovery/recovery-2026-05-30-standards-fix-overreachplan.md
related_memory:
  - reference_nfr_quality_standards_2026
---

## §0 PLAN

> **遡及追認 PLAN**: 本 PLAN は 2026-05-30 に off-process で実施された標準移行 (commit 34fb0fa / dadba03) を、recovery-2026-05-30-standards-fix-overreach の収束方針 (commit 保持 + 追認) に基づき正規工程へ乗せ直すための retrofit log。実体作業は完了済で、本 PLAN は規約適合の事後整備。

L1 要件層 skill の非機能要件標準参照を、旧 ISO/IEC 25010:2011 (8 特性) から現行 ISO/IEC 25010:2023 (9 特性) へ移行し、IPA 非機能要求グレードの位置づけ (事業終了・アーカイブ・実務チェックリスト) を是正する。

## §1 目的

改訂標準 (25010:2023) への差分を可視化し、L1 要件導出 skill が現行の品質特性モデルでタグ付けできるようにする。`requirements-deriver:109` に存在した自己矛盾 (出典 2023 だが本文 8 特性) を解消する。

## §2 背景

- HELIX の requirements-deriver / doc-system-architect / SKILL_MAP が ISO/IEC 25010 を 2011 版 8 特性のまま引用していた
- IPA 非機能要求グレードを「2018 年 4 月版が最新」と現役標準であるかのように記述していた (実態は 2010 起源・2018 マイナー改訂・2019 利用ガイド・2023 頃アーカイブ移管/事業終了)
- 正本確定は pmo-tech-docs / pmo-tech-news の外部精読 (一次情報 iso.org / ipa.go.jp / digital.go.jp) で実施 → [[reference_nfr_quality_standards_2026]]

## §3 実装計画 (kind=retrofit)

### 既存 doc/code 一覧 (対象)
- `skills/workflow/requirements-deriver/SKILL.md` (核心、副軸 25010 + R1-R14 二軸タグ + §3 網羅チェック)
- `skills/workflow/doc-system-architect/SKILL.md` (IPA 業界標準解説)
- `skills/SKILL_MAP.md` (両 skill の description 索引)
- **対象外**: L4-L6 設計 doc (IEEE 42010/1016/29119 系を使用、25010/IPA 非依存)

### 規約適用範囲
- ISO/IEC 25010 を 2011 版 8 特性 → 2023 版 9 特性へ (Safety 新規 / Usability→Interaction Capability / Portability→Flexibility)
- 日本語訳は暫定明記 (JIS X 25010:2025 未発行)、英語正式名併記
- R1-R14 二軸タグ・散文の旧名 (使用性/移植性) 更新、§3 を 9 特性化 + Safety はドメイン依存 (該当薄/破壊的操作時のみ)
- IPA を「2018 最新」→「事業終了・アーカイブ・実務チェックリスト」へ、デジタル庁第1.2版 (2025-09) 注記

### 差分プレビュー (実施済 = completion_commits)
- 34fb0fa: L5/L6 IEEE 1016 + 29119-4 (設計層の標準整合、本 retrofit と同時期の品質強化)
- dadba03: L1 skill 3 件 25010:2023 移行 + IPA 是正

### 段階 rollout
- 低リスク (skill doc 文言のみ、コード/契約変更なし) のため単段適用済。機械検証: 8特性残存 0 / 新名出現 / 暫定訳注記 / IPA 注記を grep で確認済

## §4 受入条件 / DoD
- [x] requirements-deriver / doc-system-architect / SKILL_MAP の 25010 が 2023 版 9 特性
- [x] requirements-deriver:109 の自己矛盾解消
- [x] 日本語暫定訳 + 英語正式名併記
- [x] IPA 位置づけ是正 (事業終了/アーカイブ/2011 版マッピング) + デジタル庁版注記
- [x] 設計層 (L4-L6) に影響なし (L1 要件層のみ)

## §5 関連 PLAN / ADR / docs + carry
- recovery: docs/plans/recovery/recovery-2026-05-30-standards-fix-overreachplan.md (本 PLAN の起票根拠)
- memory: [[reference_nfr_quality_standards_2026]]
- docs: HELIX-workflows/helix-process/retrofit-workflow.md

### 本 PLAN scope 外の carry (ユーザー判断待ち、未着手)
- ISO/IEC 25019:2023 (利用時品質) を L1 で製品品質と二軸分離するか
- ISO/IEC 25002:2024 を用語 SSoT に採用するか
- AI 標準 (25059 / TS25058 / 42001) を AI コンポーネント案件の補助軸に採用するか
- デジタル庁第1.2版を地方公共団体案件で参照必須化するか
- 25010:2023 × IPA グレード 6 軸の bridge 変換表を HELIX 内製 (公式に存在しない)
- JIS X 25010:2025 発行後に暫定日本語訳を正式訳へ更新
