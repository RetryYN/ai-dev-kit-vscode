---
doc_id: integration-map
title: "スキル・コマンドの穴と統合状況"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# スキル・コマンドの穴と統合状況

## スキルの穴

スキル総数111（workflow 33 / agent-skills 23 / common 12 / advanced 9 / project 8 / automation 8 / design-tools 6 / writing 5 / tools 4 / integration 3）。

| スキル | 状態 |
|---|---|
| recovery / incident / reverse / refactor / research / context | あり |
| retrofit | なし（穴） |
| detection-routing / learning-engine / cross-detection / layer-context-injection | ワークフロー文書はあり、workflow スキル未追加 |

## コマンドの穴

| コマンド | 状態 |
|---|---|
| learn / context / matrix / doctor / drift-check / readiness / debt / interrupt | あり |
| helix-recover（Recovery 起動） | なし（穴） |
| helix-route（検出 → モードルーティング起動） | なし（穴） |

学習・注入・オーケストレーション・横断集約のコマンドは揃っているが、Recovery を起動するコマンドと、検出結果をモードへ振り分ける（detection-routing）コマンドが欠けている。

## テンプレートの穴

| テンプレート | 状態 |
|---|---|
| PLAN kind 11種（design / impl / poc / reverse / troubleshoot / refactor / retrofit / research / add-design / add-impl / recovery） | 全てあり |
| generates 成果物: retrofit-matrix / research-memo / ADR / recovery-log | なし（穴） |
| 工程(L): L1 / L2 / L3 / L4（sprint-guide 5種）/ L5 | あり |
| 工程(L): L0 / L6 / L7 / L8 / L9 / L10 / L11 / L12 / L13 / L14 | なし（穴） |
| drive=agent（2段設計の Stage 2 昇華） | なし（穴, two-stage-agent-design） |
| 自動走行ループ（指定時間→budget time window、heartbeat wake→PLAN 再開、compaction API 統合） | なし（穴, continuous-run-context-management） |

PLAN の kind 雛形は揃っているが、その PLAN が生む成果物の雛形（特に新モードの retrofit-matrix / research-memo / ADR / recovery-log）が無い。工程テンプレートも L1–L5 中心で、L0 と L6–L14 が欠けている。

## 未統合

| 項目 | 状態 |
|---|---|
| vmodel-semantics 注入セット（mandatory_skills / recommended_commands / orchestration_mode） | 未定義（0件）＝ layer-context-injection の核心が実体未反映 |
| ワークフロー文書 ↔ skills/ | 未統合（helix-process/ は独立 md） |
| ワークフロー文書 ↔ .md プロトコル層（AGENTS.md / CLAUDE.md） | 未統合 |

## 統合済み

- スキル: recovery / incident / reverse / refactor / research / context
- コマンド: learn / context / matrix / doctor / drift-check / readiness / debt / interrupt
- 基盤: detector 14 / gate / test 212 / doctor / drift-check（infra-readiness.md 参照）

## 結論と優先順位

埋めるべき穴は次の通り。

1. vmodel-semantics の注入セット定義（最優先）。これを定義しないと layer-context-injection で設計した L 単位注入が実際に効かない。設計済みの内容を yaml に落とすだけで、新規判断は不要。
2. コマンド2件: helix-recover（Recovery 起動）、helix-route（検出 → モードルーティング起動）。
3. スキル: retrofit ワークフロースキル、および detection-routing / learning-engine / cross-detection / layer-context-injection の workflow スキル化。
4. テンプレート: generates 成果物（retrofit-matrix / research-memo / ADR / recovery-log）と、工程 L0 / L6〜L14 のドキュメントテンプレート。
5. 文書統合: helix-process/ のワークフローを skills/ と .md プロトコル層へ接続。

いずれも設計・仕様は確定済みで、残るはリポジトリ上の定義・実装作業。新たな設計判断を要する空白はない。
