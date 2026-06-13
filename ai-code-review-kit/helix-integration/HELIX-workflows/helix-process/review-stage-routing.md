---
doc_id: review-stage-routing
title: レビュー段階ルーティング（6段階×ロール分業）
status: accepted
accepted_date: 2026-05-24
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
integration_target:
  docs_path: docs/architecture
  category: 管理・自動化基盤
---

# レビュー段階ルーティング（6段階×ロール分業）

## 概要

コードレビューを6段階（Format / Lint / Style / Logic / Design / Architecture）に分け、各段階を「どのロールが見るか」に振り分ける。これは観点（何を見るか）を定義する `skills/common/code-review` とは別の軸で、**分業境界（誰が見るか）**だけを補強する。モード追加ではなく、既存の helix review / G2 / G4 ゲートと code-reviewer エージェントへの被せレイヤ。

Vモデルの設計レベルに対応するレビュー責任を段階化することで、`test-perspective-gate`（W字補強）がテスト観点を上流参加させるのと対をなし、レビュー観点の分担抜け漏れを防ぐ。

## 既存レビュー資産との関係（重複させない）

| 既存資産 | 役割 | 本ワークフローとの関係 |
|---|---|---|
| `skills/common/code-review` (L4/G4) | 観点5軸 + Google eng-practices、判定ラベル | 観点と判定の正本。本WFは参照のみ |
| `.claude/agents/code-reviewer` | Correctness/Readability/Architecture/Security/Performance | Stage 3-5 の一次評価器として起動 |
| `helix review` (codex review ラッパー) | Sprint .2/.5 の自動一次レビュー | Stage 1-4 の自動一次レビューを担う |
| `skills/workflow/adversarial-review` (G2) | 高リスク設計の対立検証 | Stage 5/6 の高リスク時にエスカレーション |
| `skills/workflow/security`/`threat-model` | 脆弱性・脅威の専門評価 | Stage 4 の security ゲート条件時に分岐 |
| `skills/workflow/verification`/`quality-lv5` | 検証レイヤ・テスト品質 | Stage 4 の照合証跡を記録 |

本ワークフローが足すのは「段階→ロール」のルーティングと逆説ルールのみ。

## 段階 × ロール × ゲート対応

正本は `cli/config/models.yaml` と `cli/ROLE_MAP.md`。

| 段階 | 問題の性質 | 一次担当 | エスカレーション | 対応ゲート |
|---|---|---|---|---|
| 1 Format | 正解が一意 | 自動 (lint) | PE (gpt-5.3-codex) | CI lint |
| 2 Lint | 正解が一意 | 自動 (静的解析) | PE | CI lint |
| 3 Style | ほぼ一意 | PE / pmo-haiku | — | — (Nit) |
| 4 Logic | 文脈依存 | SE (gpt-5.4) / PE | QA / security (gpt-5.4) | G7 実装 closure |
| 5 Design | 正解が複数 | TL (gpt-5.5) | adversarial-review | G2 設計凍結 |
| 6 Architecture | 未来予想 | PM (Opus) | tl-advisor | L2 以前 / ADR |

## 運用導線

### 1. helix review の出力を段階分離する

```
helix review --uncommitted
```

codex review の出力を Stage 1-4 の一次レビューとして受け取り、「指摘あり領域」と「指摘ゼロ領域」に分離する。

### 2. 段階ごとに担当へ振り分ける

- Stage 1-2: CI lint ゲートで完結（人間は見ない）
- Stage 3: PE が Nit として処理
- Stage 4: SE が一次、security ゲート条件該当は security ロールへ
- Stage 5: TL がレビュー、高リスクは adversarial-review（G2）へ
- Stage 6: PR 外。ADR 起票を促す

### 3. 逆説ルール（Stage 4 の核心）

helix review が指摘を返さなかった領域を列挙し、対応する PLAN-NNN（`docs/plans/`）を開いて SE/QA が仕様照合する。AI 指摘ゼロを「安全」と判断しない。照合記録は verification の証跡として残す（fail-close）。

### 4. G7 / G2 ゲート判定

- G7 実装 closure: Stage 4 で Critical 0 件、PLAN 照合済みを確認
- G2 設計凍結: Stage 5 で TL レビュー済み、高リスクは adversarial-review 実施済みを確認
- 判定ラベルは common/code-review と同一（LGTM / LGTM with nits / Changes requested）

## ADR 降下

Stage 6 該当変更（システム境界・認証範囲・データフロー・デプロイ単位）は ADR（`docs/adr/`）で事前決定する。ADR 化すると「ADR と整合しているか」の機械チェックに変わり、Stage 6 の一部が Stage 5/4 に降りる（AI/一次ロールの扱える範囲が広がる）。adversarial-review は ADR ドラフト完了後に自動発火する。

## 検証基準（fail-close）

- 6 段階すべてに担当ロールまたは自動ゲートが割当済み
- Stage 4: AI 指摘ゼロ領域の PLAN 照合記録あり
- Stage 6 該当変更は ADR 起票済み
- 観点・判定は common/code-review に委譲（本WFで重複定義なし）

## 非該当（やらないこと）

- 新ゲート・新 CLI コマンドの追加
- 観点や判定基準の再定義
- AI 比率の数値を定量ゲート化すること
