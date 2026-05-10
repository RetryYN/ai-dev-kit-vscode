# HELIX ↔ DS-120 政府ガイドライン Mapping

## 概要
DS-120（デジタル・ガバメント推進標準ガイドライン実践ガイドブック、現「デジタル社会推進標準ガイドライン群」）と HELIX 各工程の対応 mapping 公式版。

DS-120 は Informative 参考文書として扱い、HELIX を強制ルール化しない。各 Sprint の参照基準として活用する。

## 公式情報
- URL: https://www.digital.go.jp/resources/standard_guidelines#ds120
- 本文: 2025-06-19 更新
- テンプレート: 2025-10-06 更新

## Mapping 一覧

| HELIX | DS-120 章 | 該当 SKILL | 取り込み内容 | 優先度 | Sprint |
|---|---|---|---|---|---|
| L1 要件定義 | 第5章 要件定義書テンプレート | `workflow/requirements-handover` | 業務 / 機能 / 非機能 / 制約 / ステークホルダー / リスク | P0 | W-1 |
| L2 全体設計 | アーキテクチャ章 + リスク管理 | `workflow/design-doc` | リスク識別 / 評価 / 対応 / モニタリング / 責任分担 | P0 | W-3 |
| L3 詳細設計 | 第6章 調達仕様書テンプレート | `workflow/api-contract` + `workflow/schedule-wbs` | 調達範囲 / 技術要件 / I/F / 工程 / 品質 / 変更管理 | P0 | W-2 |
| L6 統合検証 | 品質確保章 | `workflow/quality-lv5` | 品質目標 / 測定 / 改善 | P0 | W-4 |
| L8 受入 | 受入承認章 | `workflow/verification` | 受入基準 / 手順 / 運用引継 | P0 | W-4 |
| L9 デプロイ検証 | 第8章 サービス・業務運営 | `workflow/observability-sre` | 運用設計 | P1 | W-5 |
| L10 観測 | 第9章 運用・保守 | `workflow/observability-sre` | SLO / SLI / 監視 | P1 | W-5 |
| L11 運用学習 | 第9章 + 第10章 監査 | `workflow/incident` + `workflow/postmortem` | 障害対応 / 変更管理 / 監査 / 継続改善 | P1 | W-5 |

## 公式名称注記
ガイドライン群名は「デジタル社会推進標準ガイドライン群」へ変更済みである。旧称「デジタル・ガバメント推進標準ガイドライン群」は政府内部手続文書で併用されることがある。

## AI-native fitness
- 政府テンプレは保守的で手動前提のため、HELIX では強制ルール化せず Informative reference として扱う
- 各 Sprint 内で「政府準拠 fields」を集約し、HELIX 自動化（Codex 委譲 / hook）と分離する
- 適合判断は各 Sprint ごとに個別に行う

## 各 SKILL からの参照
本文書は以下 SKILL から参照される。

- `skills/workflow/requirements-handover/SKILL.md` (W-1)
- `skills/workflow/api-contract/SKILL.md` (W-2)
- `skills/workflow/schedule-wbs/SKILL.md` (W-2)
- `skills/workflow/design-doc/SKILL.md` (W-3)
- `skills/workflow/quality-lv5/SKILL.md` (W-4)
- `skills/workflow/verification/SKILL.md` (W-4)
- `skills/workflow/observability-sre/SKILL.md` (W-5)
- `skills/workflow/incident/SKILL.md` (W-5)
- `skills/workflow/postmortem/SKILL.md` (W-5)

## 関連 PLAN
- PLAN-047 (本 mapping を含む実装 PLAN)

## 使い方
- 章番号と HELIX レイヤーの対応を固定する
- P0 / P1 / P2 の分類根拠を確認する
- 代表的な参照先を横断レビューの起点にする
- 迷いやすい境界は本文の注記を優先する

## 境界注記
- L1 は要件の収集・整理に限定し、設計詳細へ踏み込みすぎない
- L2 は方針とリスクに重点を置き、契約凍結は行わない
- L3 は調達仕様・契約・工程を固定し、実装を先取りしない
- L6 と L8 は品質と受入の観点を分けて扱う
- L9 から L11 は運用・観測・学習の循環として扱う

## TODO / FIXME 確認
- 本文書内の `TODO` なし
- 本文書内の `FIXME` なし
- 参照先リンクは相対パスとスキル名の整合を維持

## 参照整合メモ
- `workflow/api-contract` は L3 の契約整理に対応
- `workflow/schedule-wbs` は L3 の工程固定に対応
- `workflow/design-doc` は L2 の設計方針整理に対応
- `workflow/quality-lv5` と `workflow/verification` は L6 / L8 を分担
- `workflow/observability-sre`、`workflow/incident`、`workflow/postmortem` は L9-L11 の運用循環を分担
