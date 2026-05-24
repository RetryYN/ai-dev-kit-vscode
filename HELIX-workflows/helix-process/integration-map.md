---
doc_id: integration-map
title: スキル・コマンドの穴と統合状況
status: accepted
accepted_date: 2026-05-24
revised: 2026-05-25
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
integration_target:
  docs_path: docs/architecture
  category: ADR・research 関連
---

# スキル・コマンドの穴と統合状況

## スキルの穴

スキル総数111（workflow 33 / agent-skills 23 / common 12 / advanced 9 / project 8 / automation 8 / design-tools 6 / writing 5 / tools 4 / integration 3）。

| スキル | 状態 |
|---|---|
| recovery / incident / reverse / refactor / research / context | あり |
| retrofit | なし（穴） |
| detection-routing / learning-engine / cross-detection / layer-context-injection | ワークフロー文書あり、workflow スキル追加済（2026-05-25 完遂） |

## コマンドの穴

| コマンド | 状態 |
|---|---|
| learn / context / matrix / doctor / drift-check / readiness / debt / interrupt | あり |
| helix-recover（Recovery 起動） | あり（2026-05-25 完遂） |
| helix-route（検出 → モードルーティング起動） | あり（2026-05-25 完遂） |
| helix-scrum-agile / helix-incident / helix-add-feature（HELIX-workflows V2 mode CLI 完備） | あり（2026-05-25 完遂、commits 3ac35fc / 54a563b / e38088e）= Forward + Reverse + Discovery + Refactor + Retrofit + Recovery + Scrum + Incident + Add-feature の 9 mode CLI 完備達成 |
| route_engine SIGNAL_TO_MODE 4 mode 接続（scrum_agile / incident / add_feature / recovery） | あり（2026-05-25 完遂、commit e815745）= route 自動推奨 9 mode 完備 |

学習・注入・オーケストレーション・横断集約のコマンドは揃っており、`helix-recover / helix-route` は 2026-05-25 の対応で補完された。

## テンプレートの穴

| テンプレート | 状態 |
|---|---|
| PLAN kind 11種（design / impl / poc / reverse / troubleshoot / refactor / retrofit / research / add-design / add-impl / recovery） | 全てあり |
| generates 成果物: retrofit-matrix / research-memo / ADR / recovery-log | retrofit-matrix / research-memo / ADR / recovery-log は全てあり（2026-05-25 完遂） |
| 工程(L): L1 / L2 / L3 / L4（sprint-guide 5種）/ L5 | あり |
| 工程(L): L0 / L6 / L7 / L8 / L9 / L10 / L11 / L12 / L13 / L14 | あり（英語版 `cli/templates/plan/v2/L00-L14-*-template.md` として既存、2026-05-25 確認） |
| drive=agent（2段設計の Stage 2 昇華） | なし（穴, two-stage-agent-design） |
| 自動走行ループ（指定時間→budget time window、heartbeat wake→PLAN 再開、compaction API 統合） | なし（穴, continuous-run-context-management） |

PLAN の kind 雛形は揃っている。generates 成果物は `helix retrofit init` による retrofit-matrix と `helix recover dump` による recovery-log、加えて research-memo / ADR の雛形も 2026-05-25 完了対応で揃っている。工程テンプレートは L00–L14 (英語版) として `cli/templates/plan/v2/` に既存、L1–L14 完備済み。

## 未統合

| 項目 | 状態 |
|---|---|
| vmodel-semantics 注入セット（mandatory_skills / recommended_commands / orchestration_mode） | 定義済み（2026-05-25 完遂、commit 2942d81、cli/config/vmodel-semantics.yaml に injection block 反映 + helix vmodel show --injection-only CLI 接続 commit 79b8220）= layer-context-injection の核心が実体反映 |
| ワークフロー文書 ↔ skills/ | 未統合（helix-process/ は独立 md） |
| ワークフロー文書 ↔ .md プロトコル層（AGENTS.md / CLAUDE.md） | 未統合 |

## 統合済み

- スキル: recovery / incident / reverse / refactor / research / context
- コマンド: learn / context / matrix / doctor / drift-check / readiness / debt / interrupt
- 基盤: detector 14 / gate / test 212 / doctor / drift-check（infra-readiness.md 参照）

## 結論と優先順位

埋めるべき穴は次の通り。

1. vmodel-semantics の注入セット定義（最優先）。これを定義しないと layer-context-injection で設計した L 単位注入が実際に効かない。設計済みの内容を yaml に落とすだけで、新規判断は不要。  
   - 2026-05-25 完遂: commit 2942d81（**integration-map 注記追加対象**）
2. コマンド2件: helix-recover（Recovery 起動）、helix-route（検出 → モードルーティング起動）。
3. スキル: retrofit ワークフロースキル、および detection-routing / learning-engine / cross-detection / layer-context-injection の workflow スキル化。
4. テンプレート: generates 成果物（retrofit-matrix / research-memo / ADR / recovery-log）と、工程 L0 / L6〜L14 のドキュメントテンプレート。
5. 文書統合: helix-process/ のワークフローを skills/ と .md プロトコル層へ接続。

いずれも設計・仕様は確定済みで、残るはリポジトリ上の定義・実装作業。新たな設計判断を要する空白はない。
