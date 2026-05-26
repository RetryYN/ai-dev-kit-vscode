---
doc_id: L1-helix-workflows-nfr
title: "HELIX-workflows V2 非機能要求 (Non-Functional Requirements)"
status: draft
created: 2026-05-26
owner: PM
process_layer: L1
pairs_with: L14
next_pair_freeze: L4
canonical_source: HELIX-workflows/helix-process/L1-requirements.md
parent_plan: L1-helix-workflows-非機能要求plan
related_l0: docs/v2/L0-helix-workflows/concept.md
related_br: docs/v2/L1-requirements/helix-workflows-business-requirements.md
---

# HELIX-workflows V2 非機能要求 (Non-Functional Requirements)

> **位置づけ**: 本 doc は HELIX-workflows V2 dogfooding の L1 非機能要求正本。L0 concept の `L1-IN-12` / `L1-IN-15`、および業務要求 doc の BR-02 / BR-03 / BR-06 / BR-07 / BR-08 を、IPA 非機能要求グレード 2018 と ISO/IEC 25010 の二軸で製本する。
>
> **導出シグナル**: `requirements-deriver` の観点では、R6 (24時間・停止許容なし)、R8 (高同時実行・並列 Codex)、R9 (外部ツール連携)、R11 (多 OS / 多 runtime)、R12 (既存 V1→V2 移行)、R13 (監査・追跡)、R14 (外部リソース / token / runtime 制約) が主要シグナルとして立ち上がる。
>
> **件数 (2026-05-26 tl-advisor G1 audit P0 #2 確定)**: NFR は **6 領域 (AV / PF / OP / MG / SC / SE) × 計 23 件** (AV=3, PF=4, OP=5, MG=3, SC=5, SE=3)。L4 基本設計 (G4 凍結) で詳細化 + IPA グレード値確定。

> **SSoT 参照** (2026-05-26 doc-system-architect retrofit): ユビキタス言語 = [L0 §12 Glossary](../L0-helix-workflows/concept.md) / 業界標準整合 = §13 / Bounded Context = §14。本 doc は L0 §12-§14 を parent_doc reference とし、用語独自定義は行わない (anti-corruption layer)。

## §1 可用性 (Availability)

| NFR-ID | 要件 | 根拠シグナル | IPA 大項目 | ISO 25010 | 検証観点 |
|---|---|---|---|---|---|
| NFR-AV-01 | `helix` CLI 起動成功率を **99% 以上**に維持する | R6 / BR-01 | 可用性 | 信頼性 | 月次起動監査で成功率集計 |
| NFR-AV-02 | `helix.db` の整合性を **100%** とし、corruption を 0 件に保つ | R6 / R13 / BR-03 | 可用性 | 信頼性 | DB health check と破損 0 件 |
| NFR-AV-03 | session 中断時に handover dump を自動生成し、復旧の起点を失わない | R6 / R13 / BR-01 | 可用性 | 信頼性 | handover dump 自動生成率 |

## §2 性能・拡張性 (Performance / Scalability)

| NFR-ID | 要件 | 根拠シグナル | IPA 大項目 | ISO 25010 | 検証観点 |
|---|---|---|---|---|---|
| NFR-PF-01 | `helix doctor` の実行時間を **30 秒以内**に抑える (PLAN 324 件規模) | R8 / BR-02 | 性能・拡張性 | 性能効率性 | 定常データ量での wall-clock 計測 |
| NFR-PF-02 | 影響範囲 query を **5 秒以内**で返す | R8 / BR-06 | 性能・拡張性 | 性能効率性 | L0 §5.3 Cascade KPI |
| NFR-PF-03 | **8 並列 Codex** 投入時も workspace isolation で衝突なく動作する | R8 / BR-07 | 性能・拡張性 | 性能効率性 | 並列実行競合 0 件 |
| NFR-PF-04 | skeleton レベルの PLAN 起票を **1 分以内**で完了させる | R14 / BR-01 | 性能・拡張性 | 性能効率性 | 起票開始から初稿生成までの時間 |

## §3 運用・保守性 (Operability / Maintainability)

`L1-IN-12` は本章の核心であり、HELIX の累積資産を老廃物として滞留させないための **排泄系 (excretion)** 契約として扱う。`L1-IN-15` のうち進化 / 老化 / 共生 / 代謝は、本章と §4 / §5 へ段階 carry する。

| NFR-ID | 要件 | 根拠シグナル | IPA 大項目 | ISO 25010 | 検証観点 |
|---|---|---|---|---|---|
| NFR-OP-01 | **auto-deprecation 機構** (`L1-IN-12`): 使用頻度 / 最終更新時刻 / drift 検出回数で老化判定し、不要 PLAN / skill / hook を自動 archive する | R13 / BR-02 / BR-03 | 運用・保守性 | 保守性 | archive 判定ルールと月次実行ログ |
| NFR-OP-02 | 累積資産 (PLAN 324 / skill 118 / hook 30+) を月次 audit し、P0 老廃物は即時排出する | R13 / BR-02 | 運用・保守性 | 保守性 | 月次 audit レポート |
| NFR-OP-03 | `helix doctor` の warn 累積上限を **50 で alert / 20 で Phase α 完了条件**とする | R13 / BR-02 / BR-03 | 運用・保守性 | 保守性 | warn 推移の定点観測 |
| NFR-OP-04 | 工程別 skill / command / agent の **進化系統 trace** を保持し、framework 世代継承を追跡可能にする | R12 / R13 / `L1-IN-15` | 運用・保守性 | 保守性 | lineage trace の欠損 0 |
| NFR-OP-05 | session 跨ぎ memory carry では **verify-before-act** (`feedback_memory_verify_before_act`) を機械強制する | R13 / BR-07 | 運用・保守性 | 保守性 | verify-before-act 違反 0 件 |

## §4 移行性 (Portability / Migration)

| NFR-ID | 要件 | 根拠シグナル | IPA 大項目 | ISO 25010 | 検証観点 |
|---|---|---|---|---|---|
| NFR-MG-01 | V1 PLAN (`is_reference=true`) から V2 PLAN への retrofit pipeline を段階移行可能にする | R12 / BR-02 | 移行性 | 移植性 | retrofit 失敗率 / 再実行性 |
| NFR-MG-02 | `helix.db` schema migration は `schema_migration_log` を用いて **idempotent** に適用できる | R12 / BR-03 | 移行性 | 移植性 | migration 再実行で副作用 0 |
| NFR-MG-03 | 採用 project が HELIX-workflows V2 を持ち込めるよう、CLI / template / hook を portable package として配布できる | R11 / R12 / BR-08 | 移行性 | 移植性 | package 導入手順の再現性 |

## §5 セキュリティ (Security)

| NFR-ID | 要件 | 根拠シグナル | IPA 大項目 | ISO 25010 | 検証観点 |
|---|---|---|---|---|---|
| NFR-SC-01 | secret / API key を `CLAUDE.md` / `AGENTS.md` / skill / docs に書かない | R13 / BR-03 | セキュリティ | セキュリティ | secret scan 0 件 |
| NFR-SC-02 | `settings.json` auto regen の反復を検知し、commit 前 diff 確認を強制する | R13 / BR-03 | セキュリティ | セキュリティ | repeated regen 検知ログ |
| NFR-SC-03 | Agent tool guard hook で PMO + PdM の許可工具以外を block し、想定外 Opus 発火を防ぐ | R9 / R13 / BR-07 | セキュリティ | セキュリティ | guard 違反 block 率 |
| NFR-SC-04 | Codex は commit / push を行わず、成果物検証後に人間 PM が統合 commit する | R13 / BR-03 | セキュリティ | セキュリティ | commit guard 違反 0 件 |
| NFR-SC-05 | 本番影響 / 認証 / 認可 / 決済 / 個人情報 / ライセンス / destructive data operation は人間確認必須とする | R4 / R5 / R13 | セキュリティ | セキュリティ | 境界案件の自己判断 0 件 |

## §6 システム環境 (System Environment)

| NFR-ID | 要件 | 根拠シグナル | IPA 大項目 | ISO 25010 | 検証観点 |
|---|---|---|---|---|---|
| NFR-SE-01 | Linux (WSL2 含む) と macOS の両方で動作する | R11 / BR-08 | システム環境 | 互換性 | 主要コマンドの二環境確認 |
| NFR-SE-02 | Claude Code (CLI + native VS Code extension) と Codex CLI の両方をサポートする | R9 / R11 / BR-08 | システム環境 | 互換性 | CLI / extension 両導線の継続性 |
| NFR-SE-03 | 実行基盤を Python 3.11+ / Bash 5.0+ / SQLite 3.40+ / git 2.40+ に揃える | R11 / BR-08 | システム環境 | 互換性 | runtime version 下限チェック |

## §7 IPA × ISO 25010 二軸タグ表

| NFR-ID | 要約 | IPA | ISO 25010 |
|---|---|---|---|
| NFR-AV-01 | CLI 起動成功率 99% 以上 | 可用性 | 信頼性 |
| NFR-AV-02 | helix.db 整合性 100% | 可用性 | 信頼性 |
| NFR-AV-03 | handover 自動 dump | 可用性 | 信頼性 |
| NFR-PF-01 | `helix doctor` 30 秒以内 | 性能・拡張性 | 性能効率性 |
| NFR-PF-02 | 影響範囲 query 5 秒以内 | 性能・拡張性 | 性能効率性 |
| NFR-PF-03 | 8 並列 Codex の衝突回避 | 性能・拡張性 | 性能効率性 |
| NFR-PF-04 | PLAN 起票 1 分以内 | 性能・拡張性 | 性能効率性 |
| NFR-OP-01 | `L1-IN-12` auto-deprecation | 運用・保守性 | 保守性 |
| NFR-OP-02 | 月次資産 audit | 運用・保守性 | 保守性 |
| NFR-OP-03 | warn 50 alert / 20 完了条件 | 運用・保守性 | 保守性 |
| NFR-OP-04 | 進化系統 trace | 運用・保守性 | 保守性 |
| NFR-OP-05 | verify-before-act 強制 | 運用・保守性 | 保守性 |
| NFR-MG-01 | V1→V2 retrofit pipeline | 移行性 | 移植性 |
| NFR-MG-02 | schema migration idempotency | 移行性 | 移植性 |
| NFR-MG-03 | portable package 化 | 移行性 | 移植性 |
| NFR-SC-01 | secret を docs 等に書かない | セキュリティ | セキュリティ |
| NFR-SC-02 | settings regen 検知 | セキュリティ | セキュリティ |
| NFR-SC-03 | tool guard hook | セキュリティ | セキュリティ |
| NFR-SC-04 | Codex commit/push 禁止 | セキュリティ | セキュリティ |
| NFR-SC-05 | 高リスク変更の人間確認 | セキュリティ | セキュリティ |
| NFR-SE-01 | Linux / macOS 両対応 | システム環境 | 互換性 |
| NFR-SE-02 | Claude / Codex 両対応 | システム環境 | 互換性 |
| NFR-SE-03 | runtime version 下限固定 | システム環境 | 互換性 |

**ISO/IEC 25010 網羅メモ**

- 現れた特性: 性能効率性 / 互換性 / 信頼性 / セキュリティ / 保守性 / 移植性
- 現時点で主対象外の特性: 機能適合性 / 使用性
- 理由: 機能適合性は L3 機能要求と L4-L6 設計で凍結し、使用性は HELIX-workflows が UI を持たないため L2/L10 skip 前提。ただし docs site / visual workflow / interactive UI を追加する場合は L2/L10 unskip 条件として再導出する

## §8 関連 doc

- **上流**: [docs/v2/L0-helix-workflows/concept.md](../L0-helix-workflows/concept.md)
- **並走業務要求**: [helix-workflows-business-requirements.md](./helix-workflows-business-requirements.md)
- **PLAN**: [docs/plans/L1/L1-helix-workflows-非機能要求plan.md](../../plans/L1/L1-helix-workflows-%E9%9D%9E%E6%A9%9F%E8%83%BD%E8%A6%81%E6%B1%82plan.md)
- **HELIX-workflows 正本**: [HELIX-workflows/helix-process/L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
- **L1 工程 doc**: [docs/v2/process/L01-requirements-and-operational-test-design.md](../process/L01-requirements-and-operational-test-design.md)
- **L4/L9/L13/L14 接続方針**: NFR 自体の pair freeze は L4 基本設計 ↔ L9 総合テストで固定し、L13 安定性と L14 運用検証で運用値を継続観測する
- **carry**: `pairs_test_design: []` は L1 では許容し、L4 基本設計起票時に L9/L13/L14 の検証設計 artifact を追加する
- **`L1-IN-15` carry**: 逆引き audit 11 穴は §3 運用・保守性、§4 移行性、§5 セキュリティで段階的に吸収し、未実装分は L3/L4 設計で明示的に差分化する
- **L3 接続規約 (2026-05-26 tl-advisor G1 P1 #2/#3 反映、4 L1 doc 共通)**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) は L1 4 PLAN 全件 (業務 / 機能 / 技術 / 非機能) を `dependencies.requires` に列挙し、`docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を pair artifact として同時起票して L3 非機能要件 (IPA グレード値) と L12 受入テスト設計の NFR 系 AC-* を pair freeze する (詳細は業務要求 doc §7 参照、L4↔L9 + L13 + L14 は更に下流の多層検証)
