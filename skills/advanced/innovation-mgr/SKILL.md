---
name: innovation-mgr
description: PdM Tech/Marketing 出力統合 + 新方向性策定 + L1 接続スキル。意思決定 phase で使う。
metadata:
  helix_layer: ["L1", "L0-planning"]
  triggers:
    - 技術/マーケ方向性が複数出た時
    - G0.5 企画突合作成時
    - L1 入力化前の最終判断が必要な時
  agent: pdm-innovation-manager
---

# イノベーション統合マネージャー（PdM）スキル

## 目的

- Tech / Marketing 側の調査結果を受け、実装方針へ接続可能な形に統合する。
- 新方向性候補を比較し、採用・保留・棄却を明確化する。
- 最終的に L1 入力（FR / NFR / AC）へ接続し、意思決定を記録する。

## 統合プロセス

1. `input`  
   - `pdm-tech-innovation` と `pdm-marketing-innovation` の成果を読み込む。  
   - 主要情報は `strategic_options` と `assumptions` を軸に整形。

2. `矛盾抽出`  
   - 技術主張と市場主張の衝突点（目的・制約・運用負荷）を列挙。  
   - 解決不能な論点は `decision_log` の保留項目として残す。

3. `統合`  
- 矛盾解消案を `strategic_options` に再構成する。  
   - 共通指標（売上、コスト、品質、リードタイム）を揃える。

4. `adversarial`  
   - `helix codex --role tl-advisor --task "..."`
   - 1 回のみ呼び出しを許可（1回限界原則）。  
   - 指摘を `counter_arguments` に反映。

5. `finalize`  
   - `採用 / 保留 / 棄却` を各 `SO` 単位で決定。  
   - `decision_log` を更新し、反証条件を明示。

## tl-advisor adversarial 1 回限定原則

- 1 件の企画に対して 1 回のみ。
- 追加検証が必要な場合は理由を `decision_log` に明記し、次ステップに引き継ぐ。
- 反復的に再実行しない（再実行は実装前の `review` で吸収）。

## decision_log format

```yaml
- timestamp: 2026-05-14T12:00:00
  decision_type: adopt | hold | reject
  target: SO-01
  rationale: "根拠を 1〜2 行で簡潔に"
  decided_by: pdm-innovation-manager
  conditions:
    include:
      - "採用条件: ... "
    exclude:
      - "矛盾条件: ... "
  evidence:
    - "/path/to/tech-innovation-output.yaml"
    - "/path/to/marketing-innovation-output.yaml"
```

## 出力契約連携

- 企画側の最終成果は `cli/templates/plan/innovation-output.yaml.template` を使う。
- `l1_inputs` と `g0_5_mapping` は `innovation-mgr` 側で最終決定する。
- 本スキルは個別調査（Tech / Marketing）を実施せず、必ず成果の統合と意思決定に集中する。

## 参考

- `references/integration-workflow.md`
