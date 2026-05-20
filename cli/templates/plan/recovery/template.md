---
plan_id: PLAN-NNN-recovery-slug
title: "PLAN-NNN: (リカバリータイトル placeholder)"
kind: recovery
layer: cross
drive: troubleshoot
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・再開ポイント確定"
  - role: pmo-sonnet
    slot_label: "PMO — 議論順序 timeline・認識訂正履歴の整合確認"
generates:
  - artifact_path: docs/plans/PLAN-NNN-recovery-log.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-091
  requires:
    - PLAN-NNN-prereq
  blocks: []
related_adr:
  - ADR-NNN-related
related_docs:
  - docs/plans/PLAN-NNN-parent.md
---

## §0 PLAN
議論断絶・セッション分断時の継続性を担保するため、認識再構築用テンプレートを定義する。

## §1 目的
中断後でも再開者が同じ前提で続行できるよう、時系列と判断根拠を固定化する。

## §2 背景
実装・設計連続作業中の中断で認識飛躍が発生し、再開コストが増大するリスクを解消する。

## §3 実装計画
### session 断絶記録
- 中断時刻、理由、未完了項目、ブロッカーを時系列で残す。

### 議論順序 timeline
- 決定・検討・反駁の順番をトピック順で保存。

### 認識訂正履歴
- 誤認識→訂正の履歴を短く記録し、再誤用を防ぐ。

### 中間結論 list
- 現在時点での暫定結論を 1〜3 件に要約。

### context 再構築方法
- 再開時に最初に読む文書、再実行する確認コマンド、再開順を明示。

### 再開ポイント
- 次に着手すべきタスク（PLAN/KIND/Step）を1つに絞って明記。

### 再発防止
- handover / memory / todo 更新ルールを明文化し、再断絶時の再現率を低下。

## §4 受入条件 / DoD
- timeline、認識訂正履歴、再開ポイントが明確。
- 再開手順と最短チェックが 1 ページで辿れる状態。
- `kind: recovery` に一致する Step 追記が完備。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-024
- docs: `helix/HELIX_CORE.md`, `docs/commands/ai-harness.md`, `.helix/handover/CURRENT.md`
