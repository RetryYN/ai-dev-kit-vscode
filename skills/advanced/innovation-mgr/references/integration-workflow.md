# innovation-mgr 統合ワークフロー

## 目的

Tech / Marketing の PdM 出力を L1 へ接続可能な形へ統合し、意思決定の再現性を担保する。

## 全体 6 ステップ

### 1. PdM Tech / Marketing 出力 yaml 読込

- 入力: `pdm-tech-innovation` / `pdm-marketing-innovation` の出力。
- 重要項目:
  - `strategic_options`
  - `assumptions`
  - `l1_inputs`
  - `risks`

### 2. 矛盾抽出（技術側 ↔ マーケ側）

- 目的と手段が衝突していないか確認する。
- 典型的矛盾:
  - 技術は高速展開を重視しマーケは高説明性を重視。
  - 技術は低コストを重視しマーケは高接点設計を要求。
- 成果物:
  - `counter_arguments`（各 SO ごと）
  - `矛盾ログ`（原因・影響範囲・対応方針）

### 3. 統合 strategic_options 形成

- 矛盾が解消できる候補を再構成し、再採点。
- 形成時に次を含める:
  - `adoption_conditions` を再定義
  - `estimated_effort` と `risk_level` を揃える
  - `targeting`（対象顧客 / 対象チーム）を明示

### 4. tl-advisor 1 回 adversarial check

- 1 回のみ呼び出す:
  - `helix codex --role tl-advisor --task "戦略統合 SO-xx の矛盾点と採否根拠を adversarial に検証"`
- 期待成果:
  - 欠けている反論ケース
  - 証拠不足の早期発見
  - リスクの優先度見直し
- ルール:
  - 1 企画につき 1 回に限定。再実行不可。

### 5. 採用判断（採用 / 保留 / 棄却）

- 各 `strategic_options` に対し以下を記録:
  - 根拠（数値・仮説・運用条件）
  - 保留理由（反証条件）
  - 棄却理由（撤退条件・コスト過大）
- 決定レベル:
  - `adopt`: 進行
  - `hold`: 追加検証
  - `reject`: 即中止

### 6. L1 接続（l1_inputs / g0_5_mapping finalize）

- 最低限の L1 変換:
  - `fr_candidates`: 優先実行機能
  - `nfr_candidates`: セーフガードと品質軸
  - `ac_candidates`: 検証完了条件
- `g0_5_mapping` を作成:
  - `planning_item` と L1 ID の対応
  - `coverage` を full / partial / none
- `decision_log` を保存:
  - `timestamp`, `decision_type`, `target`, `rationale`, `decided_by`

## 成果物の必須チェック

- 1 企画につき `decision_log` が 1 件以上ある。
- `adversarial check` が 1 回以上実施済み。
- `l1_inputs` が空でない。
- `g0_5_mapping` の `coverage` が全件明記。

## 非対象項目

- 競合分析の一次調査
- 技術調査の実施
- マーケ施策の実験設計

上記はそれぞれ `tech-innovation` / `marketing-innovation` が担う。
