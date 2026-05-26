---
adr_id: ADR-044
title: "HELIX-workflows V2 dogfooding 方式設計 snapshot"
status: Proposed
author: PM
created: 2026-05-27
owner: PM
parent_plan: L4-helix-workflows-方式設計plan
process_layer: L4
related_design: docs/v2/L4-architecture/helix-workflows-system-architecture.md
industry_standards:
  - IEEE 42010:2022
---

# ADR-044: HELIX-workflows V2 方式設計 snapshot

## Context

HELIX-workflows V2 dogfooding の L4 基本設計では、`accepted parent design` を変更せずに `retrofit / migration / mode` の運用を進める要件が発生しています。

現時点では、L3→L4 接続と L4→L9 対応の凍結を同時に行う必要があり、方式設計の大局判断（3 層構造、4 永続化、BR-12 ratchet）を `ADR snapshot` として独立固定しないと、後追いで parent design を壊しやすくなります。BR 12 の監査条件を満たしつつ、運用設計を継続するための方針をここに記します。

## Decision

4 件の方式を採択します。

1. **三層構造**
   - 方式構造を `HELIX-workflows/`（規約） / `cli/`（実装） / `skills/`（知識）に固定する。
   - L4 計画はこの 3 層構造の前提で起票し、pairing 監査を前提化する。

2. **4 永続化**
   - `helix.db` + `.helix/audit/*.yaml` + `git history` + `.helix/handover/` の四層を、監査と復元の中心にする。
   - 変更は hook／doctor／handover の 3 経路で収束させ、失敗時の再試行先を明記する。

3. **BR-12 ratchet 機構**
   - baseline YAML（`balance-ratio-baseline.yaml` / `changeprop-violations.yaml`）を前提とし、
     `helix doctor --check-changeprop` を read-only / write update に分離する。
   - pre-commit fast と CI-only 深掘りを分け、`balance_ratio regression` を fail-close とする。

4. **二重/三重 audit pattern**
   - tl-advisor（技術）、pmo-sonnet（整合）、doc-reviewer（文書品質）を必須として配置する。
   - `Codex SUMMARY` 経路が要約消失しないよう rollout JSONL bypass を組み込み、trace を残す。

## Consequences

- **利得**: L4-L9 の pair freeze が早期に固定され、後追いの ADR 起票とレビュー遅延を抑制できる。
- **利得**: ratchet と監査分離により local 開発速度を維持しながら CI 深掘りを担保できる。
- **利得**: 三層永続化で recovery, handover, audit の再現性が高まり、監査時の説明責任が明確になる。
- **犠牲**: 新規の doc / hook 設定や audit evidence が増え、初期 skeleton の記述量が増加する。
- **犠牲**: 実験・試行の失敗ログが蓄積されるため、evidence 管理工数が上がる。
- **犠牲**: 3 重監査を厳密に運用する場合、起動コストが増加する。

## Alternatives

### 代替案 A: `helix-workflows` parent design を直接変更して L4 を進める

**却下理由**: parent design の freeze break をその場で行うと後続 L3/L4 の trace が崩れやすく、ADR snapshot の統治利点を失う。

### 代替案 B: ratchet を単一 hook に統合して導入時短縮する

**却下理由**: ローカル速度と CI 品質のトレードオフが不明確になり、fast path と深掘り path の役割分離ができなくなる。

### 代替案 C: audit を tl-advisor + pmo の 2 層に限定する

**却下理由**: doc-reviewer 証跡が欠けると大規模 doc 改定の品質保証が弱くなり、G4/G9 の証跡要件に対して十分でない。

### 代替案 D: `helix.db` のみで監査を完結させる

**却下理由**: `.helix/handover/` と `git history` を別レイヤにしないと、受け渡し時と事故再現時の検証粒度が不足する。

## Compliance

本 ADR は IEEE 42010:2022 の architecture description と整合する。

- **Architecture description の要件**: 文脈（scope）、構造（3 層・4 永続化）、決定（4 方式）を明示。
- **Traceability**: PLAN / TEST / ADR / audit 間の参照を明示し、`parent_design` と `pairs_test_design` を統合。
- **Evidence**: 監査証跡を `.helix/audit/*.yaml` と `helix.db` に持たせ、pairing と ratchet 判定に接続。
- **Decision freeze**: parent design を直接改変せず、snapshot で凍結する設計を採用。

## 補足（skeleton）

本稿は skeleton 段階であり、最終承認前の step 追加（acceptance / テスト指標閾値 / 監査コマンド）を Step 3 で carry として埋めます。
