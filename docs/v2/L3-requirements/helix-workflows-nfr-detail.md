---
doc_id: L3-helix-workflows-nfr-detail
title: "HELIX-workflows V2 非機能要件 (確定版、L3 IPA グレード値)"
status: draft
created: 2026-05-26
owner: PM
process_layer: L3
pairs_with: L12
next_pair_freeze: L4
parent_plan: L3-helix-workflows-非機能要件plan
related_l1: docs/v2/L1-requirements/helix-workflows-nfr.md
pair_artifact: docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
---

# HELIX-workflows V2 非機能要件 (確定版、L3 IPA グレード値)

> **本 doc の位置づけ**: L1 [`helix-workflows-nfr.md`](../L1-requirements/helix-workflows-nfr.md) の NFR-AV/PF/OP/MG/SC/SE 計 23 件を、L3 で **IPA 非機能要求グレード値 (レベル 0-5)** と数値 target まで固定した正本。L12 受入テスト設計の NFR 系 AC-NFR-* と V-model **L3↔L12 pair freeze** を成立させる。
>
> **確定ルール**: 本 doc の「レベル」は HELIX-workflows 用に採用する L3 の確定値であり、L4 ではその達成方法 (監視・実装方式・集計経路) を凍結する。L12 は初期受入、L13 は安定性、L14 は運用検証を担当する。

> **SSoT 参照** (2026-05-26 doc-system-architect retrofit): ユビキタス言語 = [L0 §12 Glossary](../L0-helix-workflows/concept.md) / 業界標準整合 = §13 / Bounded Context = §14。本 doc は L0 §12-§14 を parent_doc reference とし、用語独自定義は行わない (anti-corruption layer)。

## §1 可用性 (NFR-AV-* IPA グレード値)

| NFR-ID | L3 確定値 | target / 判定条件 | ISO 25010 | 検証境界 |
|---|---|---|---|---|
| NFR-AV-01 | **可用性レベル 3** | `helix` CLI 起動成功率を **月次 99.9% 以上**に固定する | 信頼性 | L12: 起動監査 / L13-L14: 月次継続観測 |
| NFR-AV-02 | **可用性レベル 4** | `helix.db` 整合性 **100%**、corruption **0 件**、復旧後の metadata 欠落 **0 件** | 信頼性 | L12: health check / L13-L14: 破損監査 |
| NFR-AV-03 | **可用性レベル 3** | session 中断時の handover dump 自動生成率 **95% 以上**、復旧開始まで **15 分以内** | 信頼性 | L12: dump 発火確認 / L13-L14: 中断復旧監査 |

## §2 性能・拡張性 (NFR-PF-* IPA グレード値)

| NFR-ID | L3 確定値 | target / 判定条件 | ISO 25010 | 検証境界 |
|---|---|---|---|---|
| NFR-PF-01 | **性能レベル 2** | `helix doctor` 実行時間を **30 秒以内**、PLAN 324 件規模で **ピーク 5 倍**まで劣化許容内に収める | 性能効率性 | L12: 単発性能 / L13: 定常実行 |
| NFR-PF-02 | **性能レベル 2** | 影響範囲 query の中央値 **5 秒以内**、p95 **10 秒以内** | 性能効率性 | L12: query ベンチ / L13: 継続計測 |
| NFR-PF-03 | **性能レベル 3** | **8 並列 Codex** 投入時の workspace 衝突 **0 件**、排他待ちで全 run が完走 | 性能効率性 | L12: 並列受入 / L13: soak |
| NFR-PF-04 | **性能レベル 2** | skeleton レベルの PLAN 起票を **1 分以内**に完了し、初稿生成失敗率を **5% 未満**に抑える | 性能効率性 | L12: 起票受入 / L13: 運用時間計測 |

## §3 運用・保守性 (NFR-OP-*、`L1-IN-12` 排泄系含む)

`L1-IN-12` は本章の中核であり、HELIX の累積資産を老廃物として滞留させないための **排泄系 (excretion)** 契約を L3 で確定する。`L1-IN-15` P1 のうち進化 / 老化は本章、繁殖は §4、共生は §6、代謝は §2 と連携する。

| NFR-ID | L3 確定値 | target / 判定条件 | ISO 25010 | 検証境界 |
|---|---|---|---|---|
| NFR-OP-01 | **運用保守レベル 3** | auto-deprecation 対象の stale 資産に対し、月次 archive 実行率 **90% 以上** | 保守性 | L12: 対象判定 / L14: 月次 archive 実績 |
| NFR-OP-02 | **運用保守レベル 3** | PLAN / skill / hook の月次 audit 完遂率 **100%**、P0 老廃物の当月排出率 **100%** | 保守性 | L12: audit 手順 / L14: 継続実績 |
| NFR-OP-03 | **運用保守レベル 2** | `helix doctor` warn は **50 で alert**、Phase α exit は **20 以下**に固定 | 保守性 | L12: 閾値受入 / L14: 週次推移 |
| NFR-OP-04 | **運用保守レベル 2** | skill / command / agent の lineage trace 欠損 **0 件**、主要資産 coverage **100%** | 保守性 | L12: trace 存在確認 / L14: 世代監査 |
| NFR-OP-05 | **運用保守レベル 3** | `feedback_memory_verify_before_act` 違反 **0 件**、memory carry 実行前 verify 実施率 **100%** | 保守性 | L12: guard 受入 / L14: 違反監査 |
| NFR-OP-06 (2026-05-26 BR-09 由来) | **運用保守レベル 3** | inventory drift 率 ≤ **5%** (毎週金曜計測)、設計 doc 内 implementation_status 列充足率 **100%** (新規 doc 起票時) | 保守性 | L12: inventory drift 監査 (AC-NFR-OP-06) / L14: OT-09 週次計測 |
| NFR-OP-07 (2026-05-26 BR-11 由来) | **運用保守レベル 3** | 大規模 doc 改定 (~500 行+) の `helix codex --role doc-reviewer` 召喚 coverage **≥ 95%**、commit message / final report / 会話 history のいずれかに召喚 evidence + 判定結果残置率 **≥ 95%** | 保守性 | L12: 召喚 coverage 受入 (AC-NFR-OP-07) / L14: OT-11 週次計測 |
| NFR-OP-08 (2026-05-26 BR-12 由来) | **運用保守レベル 4** | デグレ禁止 ratchet 機構の機械強制率 **100%** (上流 ID 追加 commit で下流対応不在による fail-close が機械検出されること)、balance_ratio < 1.0 regression 検出率 **100%**、上流↔下流 trace 切れ件数 **0** | 保守性 | L12: 3 軸 check 受入 (AC-NFR-OP-08) / L14: OT-12 週次計測 / pre-commit + CI hook 統合 |

## §4 移行性 (NFR-MG-* IPA グレード値)

| NFR-ID | L3 確定値 | target / 判定条件 | ISO 25010 | 検証境界 |
|---|---|---|---|---|
| NFR-MG-01 | **移行性レベル 2** | V1→V2 retrofit pipeline の再実行成功率 **95% 以上**、rollback path を保持 | 移植性 | L12: 手順受入 / L13: 実移行試行 |
| NFR-MG-02 | **移行性レベル 3** | schema migration の idempotent 再実行で副作用 **0 件** | 移植性 | L12: rerun 検証 / L13-L14: migration 監査 |
| NFR-MG-03 | **移行性レベル 2** | 採用 project への package 導入初期化を **30 分以内**で完了できる状態にする | 移植性 | L12: bootstrap 受入 / L13: 採用 project 試行 |
| NFR-MG-04 (2026-05-26 BR-10 由来) | **移行性レベル 3** | Strangler Fig Pattern (Fowler 2004) 段階置換進捗を Phase 別残量 dashboard で管理、Phase α 終了時 V1 PLAN `is_reference: true` 化率 **100%**、Phase β 終了時 旧 enum 残存 **0**、Phase γ 終了時 Strangler 段階置換 **完了** | 移植性 | L12: migration 残量受入 (AC-NFR-MG-04) / L14: OT-10 週次計測 / L13-L14: dashboard 監視 |

## §5 セキュリティ (NFR-SC-* IPA グレード値)

| NFR-ID | L3 確定値 | target / 判定条件 | ISO 25010 | 検証境界 |
|---|---|---|---|---|
| NFR-SC-01 | **セキュリティレベル 4** | secret / API key の repository scan 検出 **0 件** | セキュリティ | L12: secret scan / L14: 継続監査 |
| NFR-SC-02 | **セキュリティレベル 3** | `settings.json` repeated regen 検知率 **100%**、commit 前 diff 確認強制 | セキュリティ | L12: guard 動作 / L14: 再発監査 |
| NFR-SC-03 | **セキュリティレベル 4** | PMO / PdM 非許可 tool 呼び出し block 率 **100%** | セキュリティ | L12: tool guard 受入 / L14: 逸脱監査 |
| NFR-SC-04 | **セキュリティレベル 3** | Codex の commit / push guard 違反 **0 件** | セキュリティ | L12: guard 存在確認 / L14: 監査ログ |
| NFR-SC-05 | **セキュリティレベル 4** | 本番影響 / 認証 / 認可 / 決済 / PII / ライセンス / destructive data の人間確認率 **100%** | セキュリティ | L12: 境界 test / L14: 逸脱 0 維持 |

## §6 システム環境 (NFR-SE-* IPA グレード値)

| NFR-ID | L3 確定値 | target / 判定条件 | ISO 25010 | 検証境界 |
|---|---|---|---|---|
| NFR-SE-01 | **環境レベル 2** | Linux (WSL2 含む) / macOS の主要コマンド matrix 成功率 **100%** | 互換性 | L12: OS matrix / L13: 継続運用 |
| NFR-SE-02 | **環境レベル 2** | Claude Code と Codex CLI の core entry flow 継続率 **100%** | 互換性 | L12: 両導線受入 / L13: 併走監査 |
| NFR-SE-03 | **環境レベル 2** | Python 3.11+ / Bash 5.0+ / SQLite 3.40+ / git 2.40+ の version 下限違反 **0 件** | 互換性 | L12: version check / L14: upgrade 監視 |

## §7 IPA × ISO 25010 二軸タグ表 + ISO 残り 2 特性の再導出

### §7.1 NFR 23 件の二軸タグ

| ISO 25010 特性 | 対応 NFR / L3 観点 | IPA 側の受け皿 |
|---|---|---|
| 機能適合性 | **L3 再導出**: FR-* と AC-FR-* の `balance_ratio ≥ 1.0`、契約 drift fail-close | L3 機能要件plan / L12 機能系 AC |
| 性能効率性 | NFR-PF-01〜04 | 性能・拡張性 |
| 互換性 | NFR-SE-01〜03 | システム環境 |
| 使用性 | **L3 再導出**: CLI usability (`helix help` 完備率 **90% 以上**、TTFSP **30 分以内**、自己解決可能な error 文言) | システム環境 / 運用・保守性 |
| 信頼性 | NFR-AV-01〜03 | 可用性 |
| セキュリティ | NFR-SC-01〜05 | セキュリティ |
| 保守性 | NFR-OP-01〜05 | 運用・保守性 |
| 移植性 | NFR-MG-01〜03 | 移行性 |

### §7.2 L3 再導出の扱い

- **使用性 (CLI usability)**:
  - HELIX-workflows は UI を持たないため、L3 では CLI 中心の使用性へ読み替える。
  - docs site / TUI / interactive UI を追加する場合は、L0 §8.3 の skip 条件を外し、L2/L10 を unskip して再設計する。
- **機能適合性**:
  - 機能そのものは L3 機能要件 doc が正本だが、L3 NFR でも「要件と受入の量閉じ性」を品質特性として再掲する。
  - 機能系 AC の欠落は G3 blocker として扱い、L12 の pair freeze を機械検証対象にする。

## §8 `L1-IN-15` 逆引き audit 11 穴の段階対応

| 穴 | 段階 | L3 での受け皿 | 後続で固定するもの |
|---|---|---|---|
| 進化 | L3-L4 | `NFR-OP-04` lineage trace | L4 で trace schema / audit flow |
| 繁殖 | L3-L4 | `NFR-MG-03` portable package / 親→子 project 継承 | L4 で package 契約 |
| 老化 | L3-L4 | `NFR-OP-01` auto-deprecation / `NFR-OP-02` audit | L4 で archive 実装 |
| 共生 | L3-L4 | `NFR-SE-02` Claude/Codex 両対応、`NFR-SC-03` tool guard | L4 で integration 戦略 |
| 代謝 | L3-L4 | `NFR-PF-04` 起票速度 + `NFR-OP-02` audit cadence を暫定受け皿とする | L4 で token / 生産価値 metric 設計 |
| 内分泌 | L7-L9 carry | slow/global signal は未実装、telemetry carry | L7 実装 / L9 総合検証 |
| 循環 | L7-L9 carry | cross-mode / cross-PLAN knowledge 流通は未凍結 | event / trace 実装 |
| 消化 | L7-L9 carry | 外部 OSS → 体内化 pipeline は未凍結 | intake flow / integration test |
| 性差 | L7-L9 carry | multi-model 組換え戦略は role routing carry | L7 routing / L9 compatibility |
| 多細胞化 | L13-L14 carry | team scaling は運用段階で扱う | L13 安定性 / L14 運用検証 |
| 神経変性 | L13-L14 carry | AI 役 / hook 劣化検知は運用監視で扱う | degradation detection / runbook |

## §9 関連 doc

- **上流 L1**: [helix-workflows-nfr.md](../L1-requirements/helix-workflows-nfr.md)
- **PLAN (本 doc を生成)**: [L3-helix-workflows-非機能要件plan.md](../../plans/L3/L3-helix-workflows-%E9%9D%9E%E6%A9%9F%E8%83%BD%E8%A6%81%E4%BB%B6plan.md)
- **L12 ペア相手**: [helix-workflows-acceptance-test-design.md](../L12-test-design/helix-workflows-acceptance-test-design.md) §3 非機能系受入テスト
- **L3 業務要件 sibling**: [helix-workflows-business-requirements-detail.md](./helix-workflows-business-requirements-detail.md)
- **HELIX-workflows L3 正本**: [HELIX-workflows/helix-process/L3-requirements-definition.md](../../../HELIX-workflows/helix-process/L3-requirements-definition.md)
- **L0 概念**: [docs/v2/L0-helix-workflows/concept.md](../L0-helix-workflows/concept.md)
- **下流 L4**: `L4-helix-workflows-基本設計plan` (監視方式 / guard 実装 / telemetry を凍結)
