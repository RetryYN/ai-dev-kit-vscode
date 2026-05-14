# PdM Innovation Team 運用ワークフロー (V2.2)

## 1. 目的

PdM Innovation は「新規企画」「既存サービス再設計」の検討時に、技術・マーケの専門的視点を短時間で収束させるための運用系 role 群。

本書は以下を目的にする。

- 技術思考とマーケ思考を分離して並列化する
- L1 入力に必要な意思決定根拠を YAML で残す
- trace 完全性（100%）を G0.5 で担保する

## 2. 利用場面

### 2.1 新規プロダクト企画 phase

企画起点で、競合比較、技術選定、提供価値、導入順を決める場面。

- 新規機能コンセプトの実現可能性確認
- ビジネス目標に対する技術/マーケの寄与分担を抽出
- 早期リスクと実装順を作成

### 2.2 既存サービス re-design 検討時

- 既存基盤に対する再設計方針検討時
- KGI/KPI 非整合の原因調査
- 差分改善（実装、導線、成長指標）を短期間で提案

## 3. 3 PdM ロールの棲み分け

```text
pdm-tech-innovation      ← 技術模倣と翻案
pdm-marketing-innovation  ← 市場/成長理論の翻案
pdm-innovation-manager   ← 統合、意思決定、L1 接続
```

### 3.1 pdm-tech-innovation

役割:

- 海外技術思想の翻案（Spotify Squad, Stripe, DORA, SPACE など）
- 実装に転換可能な示唆を YAML で提示
- 技術成熟度・依存関係・移行難度を添える

起動例:

```bash
Agent({"subagent_type":"pdm-tech-innovation","description":"新機能の技術実現性評価","prompt":"国内外の参考事例を踏まえ実装方針を案内"})
```

### 3.2 pdm-marketing-innovation

役割:

- 海外マーケ思想の翻案（PLG, JTBD, NSM, Reforge など）
- 施策導線、導入トリガ、検証指標を並列で整備
- セグメント別の訴求軸を提示

起動例:

```bash
Agent({"subagent_type":"pdm-marketing-innovation","description":"市場観点の設計支援","prompt":"海外成功事例を踏まえ GTM 仮説を作成"})
```

### 3.3 pdm-innovation-manager

役割:

- 技術・マーケ成果を統合し L1 につなげる
- G0.5 trace 充足を監督
- 意思決定のボトルネック解消と最終結論を提示

起動例:

```bash
Agent({"subagent_type":"pdm-innovation-manager","description":"技術/マーケ結果の統合作成","prompt":"tech/marketing 出力を L1 入力仕様に要約"})
```

## 4. 4-step ワークフロー

### Step 1: 企画受領 → 技術並列

```bash
/innovation-tech --task "<企画タイトル>"
Agent({subagent_type:"pdm-tech-innovation", description: "技術検討", prompt: "競合事例を含める"})
```

- tech/marketing それぞれ同時実行し、結果を競合比較できる形で保存
- 各出力に reference URL / assumption / 制約を明記

### Step 2: /innovation-marketing 並列実行

- マーケ観点から導線・価格・拡散戦略・KPI を構築
- 技術側で見えづらい市場阻害条件を補完

### Step 3: pmo 補助（一次情報整合）

- `pmo-tech-docs` で外部一次情報の精読を補完
- `pmo-helix-explorer` で HELIX 既存資産整合を確認
- 必要に応じ `pmo-project-explorer` で project 内依存を確認

### Step 4: 統合と L1 接続

```bash
/innovation-synthesize
Agent({"subagent_type":"pmo-innovation-manager","description":"最終統合","prompt":"4-step結果を統合し L1 受けを作成"})
```

- manager が最終採択案を提示
- L1 input が利用できる体裁（要件、評価軸、実装条件）に整理
- `plan` へ反映し G0.5 mapping に接続

## 5. 出力契約

`cli/templates/plan/innovation-output.yaml.template` に準拠すること。

```yaml
title: "新規企画名"
status: draft
team:
  - pdm-tech-innovation
  - pdm-marketing-innovation
  - pdm-innovation-manager
trace:
  g05_coverage: 1.0
  evidence:
    - type: "doc"
      ref: "https://..."
      reason: "competitive benchmarking"
gaps:
  - id: "G0.5-001"
    desc: "KPI 指標の測定窓口未定義"
  - id: "G0.5-002"
    desc: "非機能要件の実現条件が未確定"
```

## 6. Team YAML 参照

- `cli/templates/teams/innovation-team.yaml`
- team 利用は role ごとの責務分離を優先

## 7. G0.5 接続要件

G0.5 は `trace` の 100% カバーを強制する。重要条件は 2 点。

1. `trace_id` 必須
2. 企画項目に対する採択判断（技術/マーケ/リスク）を同一レコードに保持

失敗例:

- `trace_id` 欠落
- 参照資料が 1 つの観点のみ
- KPI と実装順の不一致

改善例:

- 追加の output ブロックで欠落観点を埋める
- 受け側 L1 が参照する evidence の key を明示

## 8. マルチモデル運用

### 8.1 モデル構成

- Opus ベースの subagent で最終品質を担保
- `helix` 経由の `tl-advisor` を 1 回 adversarial check として活用
- 競合情報は必要に応じ pmo-* の補助を追加

### 8.2 例: 実行順

1. `pdm-tech-innovation` と `pdm-marketing-innovation` を同時起動
2. 進捗が出た時点で `pmo-tech-docs` と `pmo-helix-explorer` を追加
3. `pmo-*` 結果を manager へ渡し、 `/innovation-synthesize` へ統合

## 9. 参照先

- [docs/commands/innovation.md](../commands/innovation.md)
- [skills/advanced/tech-innovation/SKILL.md](../../skills/advanced/tech-innovation/SKILL.md)
- [skills/advanced/marketing-innovation/SKILL.md](../../skills/advanced/marketing-innovation/SKILL.md)
- [skills/advanced/innovation-mgr/SKILL.md](../../skills/advanced/innovation-mgr/SKILL.md)
- [cli/templates/teams/innovation-team.yaml](../../cli/templates/teams/innovation-team.yaml)

## 10. 実 CLI 実行例

```bash
helix innovation team --task "新規 BtoB 向け通知体験強化"
```

```bash
Agent({"subagent_type":"pdm-innovation-manager","description":"synthesize","prompt":"企画名と evidence から L1 受けを作る"})
```

```bash
cat output/innovation-output.yaml
team:
  - pdm-tech-innovation
  - pdm-marketing-innovation
  - pdm-innovation-manager
trace:
  g05_coverage: 1.0
```

## 11. 成功基準（運用）

1. 4-step が 1 セッションで完了し、re-run 必須が減る
2. G0.5 trace が 100% で通過
3. L1 の受けが明確で、二度手間がない
4. PMO へ相談した evidence が再利用しやすい

