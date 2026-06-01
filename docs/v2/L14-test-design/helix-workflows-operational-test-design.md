---
doc_id: L14-helix-workflows-operational-test-design
title: "HELIX-workflows V2 運用テスト設計 (Operational Test Design, L1↔L14 pair)"
status: frozen
freeze_evidence: "2026-06-02 L0-L3 review + L4 completion session; TL adversarial check; pair docs L14 L12 created; L4-L9 pair; plan_validator 0 ERROR"
created: 2026-06-02
owner: PM
process_layer: L14
pairs_with: L1
pairs_design: docs/v2/L1-requirements/helix-workflows-business-requirements.md
parent_plan: L1-helix-workflows-業務要求plan
related_requirements:
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L1-requirements/helix-workflows-nfr.md
---

# 運用テスト設計 (L1↔L14 pair)

## §1 目的と境界

本書は、L1 業務要求 `BR-01`〜`BR-12` と、運用で継続観測する対象 NFR (`NFR-OP-01`〜`05`, `NFR-AV-01`〜`03`) を、L14 で実行可能な運用テストシナリオへ固定するための設計書である。目的は、HELIX-workflows V2 dogfooding の運用品質を「観測可能な閾値」「fail-close 条件」「定点監視」に落とし込み、L1↔L14 pair freeze の片肺を解消することにある。

L14 は運用検証と運用学習の層であり、本書は実装コードや監視定義そのものを置く場所ではない。実テストコード、計測ジョブ、CLI 実装、DB query、監視 rule の実体化は L7 以降と運用フェーズへ送る。本書では、運用テストの scaffold、受入基準、trace、carry を固定し、後続工程が同じ観測点を再利用できる状態を作る。

## §2 運用テストシナリオ

| OT-ID | 対応要件ID | シナリオ概要 | 前提条件 | 受入基準(合否判定可能な閾値・観測点) | 検証方式 |
|---|---|---|---|---|---|
| OT-01 | BR-01 | HELIX 自身の dogfooding 開発が 13 工程主線で継続運転されていることを月次確認する | 当月分の PLAN / gate / handover / run 証跡が参照可能 | 月次 `completed` 扱いの V-model 整合 PLAN 数が `>= 50`、かつ L0/L1/L3-L9/L11-L14 の欠落工程 0 件 | 監視 |
| OT-02 | BR-02 | 4 artifact retrofit の進捗を `helix doctor` warn 推移で監視する | retrofit 対象 PLAN 群と doctor 出力履歴がある | 月末 warn 件数が `<= 20`、または前月比で warn 純増 `<= 0` を維持 | 自動+監視 |
| OT-03 | BR-03 | workflow / CLI / skill / DB schema drift の新規発生を週次検知する | drift detector の週次実行ログがある | 週次の新規 drift 件数 `= 0`、未解消 drift の翌週持ち越し P0 件数 `= 0` | 自動+監視 |
| OT-04 | BR-04 | 9 mode 入口判定から Forward 復帰までの event 登録を追跡する | mode 実行履歴と closure event がある | mode 入口判定された実行の `forward_return` 記録率 `= 100%`、mode_transition event 欠落 0 件 | 自動 |
| OT-05 | BR-05 | V-model ペア凍結監査の量閉じ性を週次計測する | 6 pair の frontmatter / trace 情報が参照可能 | 監査対象 5 pair 以上で `balance_ratio >= 1.0`、pair freeze coverage `>= 80%`、fail-close 漏れ 0 件 | 自動+監視 |
| OT-06 | BR-06 | 影響範囲分析 query の応答性能と再現性を確認する | 代表的な改修シナリオと trace データがある | 代表 query の p95 応答時間 `<= 5 秒`、結果の空返却誤判定 0 件 | 自動 |
| OT-07 | BR-07 | vmodel-semantics による skill / command / agent 注入の適用率を監視する | 注入対象 session の summary / context evidence がある | mandatory injection の適用率 `= 100%`、mandatory skill / command 欠落 0 件 | 自動 |
| OT-08 | BR-08 | 採用 project で HELIX V2 標準導線が再現できることを確認する | 配布対象 project で導入手順と月次 run が記録されている | 対象 project ごとに `status -> plan -> gate -> review` の標準導線完走率 `= 100%`、blocking drift 0 件 | 手動+監視 |
| OT-09 | BR-09 | inventory と実資産の乖離率を月次で監視する | inventory 一覧と実ファイル / 実装検索結果がある | inventory drift 率 `<= 5%`、`implementation_status` 欠落行 0 件 | 自動+監視 |
| OT-10 | BR-10 | V1→V2 段階移行の残量と kill criteria を確認する | migration dashboard と対象一覧がある | Phase α 対象の V1 PLAN `is_reference: true` 化率 `= 100%`、migration pending P0 件数 `= 0` | 自動+監視 |
| OT-11 | BR-11 | 大規模 doc 改定時の doc-reviewer 召喚運用を監査する | doc change log と review evidence がある | 対象 commit の doc-reviewer 召喚率 `>= 95%`、review evidence 欠落 0 件 | 自動 |
| OT-12 | BR-12 | 上流変更に対する下流追随の ratchet guard を運用監査する | commit diff と trace check 結果がある | upstream/downstream alignment 違反 `= 0`、balance_ratio regression `= 0`、ID reference 切れ `= 0` | 自動 |
| OT-13 | NFR-OP-01 | auto-deprecation 機構が不要資産を archive 判定できることを確認する | 月次 archive 判定ジョブと候補一覧がある | 判定対象の decision log 記録率 `= 100%`、P0 老廃物の月末残存 `= 0` | 自動+監視 |
| OT-14 | NFR-OP-02 | 累積資産 audit が毎月完走し、P0 老廃物が残留しないことを確認する | 対象月の audit report がある | 月次 audit report 生成率 `= 100%`、P0 老廃物未処理件数 `= 0` | 手動+監視 |
| OT-15 | NFR-OP-03 | warn 累積上限の alert / 完了条件を継続監視する | doctor warn の定点観測ログがある | warn 件数が `> 50` の場合は alert 発火率 `= 100%`、Phase α 完了判定時は warn 件数 `<= 20` | 監視 |
| OT-16 | NFR-OP-04 | skill / command / agent の進化系統 trace の欠落を検知する | lineage trace と変更履歴がある | 変更対象の lineage trace 充足率 `= 100%`、孤立変更 0 件 | 自動 |
| OT-17 | NFR-OP-05 | verify-before-act が session 跨ぎ memory carry で強制されることを確認する | memory carry を含む session と検証ログがある | verify-before-act 違反 `= 0`、検証証跡欠落 0 件 | 自動 |
| OT-18 | NFR-AV-01 | `helix` CLI の起動成功率を月次で測定する | 対象期間の CLI 起動ログがある | 月次起動成功率 `>= 99%`、原因未分類の起動失敗 0 件 | 監視 |
| OT-19 | NFR-AV-02 | `helix.db` の整合性と破損 0 件を確認する | DB health check と integrity check のログがある | integrity check 成功率 `= 100%`、corruption 検出件数 `= 0` | 自動+監視 |
| OT-20 | NFR-AV-03 | session 中断時の handover dump 自動生成と再開可能性を確認する | 中断 session の handover 証跡がある | 中断 session の handover dump 自動生成率 `= 100%`、再開不能 session 0 件 | 自動 |

## §3 trace matrix

対象要件数は `20` 件 (`BR-01`〜`BR-12` の 12 件 + `NFR-OP-01`〜`05` と `NFR-AV-01`〜`03` の 8 件)、運用テストシナリオ数は `20` 件である。したがって `balance_ratio = OT数 / 要件数 = 20 / 20 = 1.00` であり、要件ごとに最低 1 OT を持つ。

| 要件ID | 対応 OT-ID | coverage |
|---|---|---|
| BR-01 | OT-01 | 1:1 |
| BR-02 | OT-02 | 1:1 |
| BR-03 | OT-03 | 1:1 |
| BR-04 | OT-04 | 1:1 |
| BR-05 | OT-05 | 1:1 |
| BR-06 | OT-06 | 1:1 |
| BR-07 | OT-07 | 1:1 |
| BR-08 | OT-08 | 1:1 |
| BR-09 | OT-09 | 1:1 |
| BR-10 | OT-10 | 1:1 |
| BR-11 | OT-11 | 1:1 |
| BR-12 | OT-12 | 1:1 |
| NFR-OP-01 | OT-13 | 1:1 |
| NFR-OP-02 | OT-14 | 1:1 |
| NFR-OP-03 | OT-15 | 1:1 |
| NFR-OP-04 | OT-16 | 1:1 |
| NFR-OP-05 | OT-17 | 1:1 |
| NFR-AV-01 | OT-18 | 1:1 |
| NFR-AV-02 | OT-19 | 1:1 |
| NFR-AV-03 | OT-20 | 1:1 |

## §4 carry

- 実テストコード、監視 rule、DB query、scheduler job、dashboard は本書では未実装とし、L7 以降と運用フェーズで実体化する。
- `OT-08` の採用 project 対象数、`OT-10` の Phase β/γ 閾値、`OT-11` の大規模 doc 判定条件の細部は L3/L4 で補助設計に落とす。
- `OT-13`〜`OT-17` の判定に使う inventory / lineage / verify-before-act の実収集経路は L4 基本設計と L7 実装で具体化する。
- `OT-18`〜`OT-20` の可用性計測窓、集計粒度、通知先、再実行手順は L13 運用安定化の runbook と結合して確定する。
