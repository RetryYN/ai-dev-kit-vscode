---
name: review-stage-routing
description: コードレビューを6段階 (Format/Lint/Style/Logic/Design/Architecture) に分け、各段階を「どのロール (PM/TL/SE/PE/QA/security) が見るか」に振り分ける分業境界スキル。観点 (何を見るか) は common/code-review の5軸 + Google eng-practices に委譲し、本スキルは段階×ロール割当と「AIが指摘しなかった箇所こそ上位ロールが見る」逆説ルールのみを担う。helix review / code-reviewer エージェント / adversarial-review の起動順と責任分界を決める時に使用する。
metadata:
  helix_layer: L7
  triggers:
    - "自動: helix review (Sprint .2/.5) 実行時のレビュー段階ルーティング決定"
    - "自動: G7 実装 closure ゲートでの段階別レビュー責任分界の確定時"
    - "任意: PR レビューで AI/人間/各ロールの分担を決める時"
    - "任意: AI レビューがゼロ指摘の diff を上位ロールに回す判断時 (逆説ルール)"
  verification:
    - "6 段階すべてに担当ロール (または自動ゲート) が割当済み"
    - "Stage 4 Logic: AI 指摘ゼロ領域を列挙し上位ロール確認に回した記録あり"
    - "Stage 6 Architecture 該当変更は PR レビュー前に ADR 起票済み (docs/adr/)"
    - "観点判定は common/code-review に委譲し本スキルで重複定義していない"
    - "判定ラベルは common/code-review と同一 (LGTM / LGTM with nits / Changes requested)"
compatibility:
  claude: true
  codex: true
---

# レビュー段階ルーティング スキル

コードレビューの「観点 (何を見るか)」ではなく「分業 (誰が見るか)」を決めるスキル。
6 段階それぞれの問題の性質に応じて、自動ゲート・PE・SE・TL・QA・security・PM のどこに振り分けるかを確定する。

## 責務境界

> - **本スキル (review-stage-routing)**: 6 段階の分業境界 = どの段階を誰が見るか、逆説ルール、ADR 降下
> - **common/code-review**: レビュー観点 (5軸 + Google eng-practices) と判定ラベル = 何を見てどう判定するか
> - **code-reviewer (agent)**: Correctness/Readability/Architecture/Security/Performance の 5 軸実評価
> - **workflow/adversarial-review (G2)**: 高リスク設計判断の対立検証
> - **workflow/security / threat-model / compliance**: 脆弱性・脅威・法令の専門評価
> - **workflow/verification / quality-lv5**: 検証レイヤとテスト品質

本スキルは観点や判定基準を再定義しない。それらは common/code-review が正本。
本スキルが足すのは「段階 → ロール」のルーティングと、AI と人間 (上位ロール) の境界線だけ。

## 適用タイミング

### 自動発火

| 条件 | タイミング | 根拠 |
|------|-----------|------|
| helix review 実行 | Sprint .2/.5 完了時 | codex review に渡す段階観点と、後続の人間レビュー範囲を決める |
| G7 実装 closure ゲート | L7 実装完了時 | Stage 4 Logic の責任分界を確定し fail-close 判定に乗せる |

### 任意発火 (PM/TL 判断)

| 条件 | 判断基準 |
|------|---------|
| PR レビューの分担決定 | 複数ロールが関与する PR |
| AI ゼロ指摘 diff の扱い | helix review / code-reviewer が指摘を返さなかった領域 |

### スキップ条件

- サイジング S (小規模) で単一ロールが全段階を見られる場合
- Format/Lint のみの機械的変更 (Stage 1-2 の自動ゲートで完結)
- 同一 PR で既にルーティング確定済み

## 6 段階と既存観点の対応

6 段階は「問題の性質 = 正解の一意性」で切る。観点は common/code-review の語彙に対応づける (再定義しない)。

| 段階 | 問題の性質 | 対応する既存観点 (common/code-review) | ゲート性質 |
|------|-----------|--------------------------------------|-----------|
| 1 Format | 正解が一意 | スタイル (自動) | ブロッキング (lint) |
| 2 Lint | 正解が一意 | 一貫性・複雑性の機械検出 | ブロッキング (lint) |
| 3 Style | ほぼ一意 | 命名・コメント・可読性 (Readability) | 非ブロッキング (Nit) |
| 4 Logic | 文脈依存 | Correctness・Security・Performance | 条件付き (Critical=Blocking) |
| 5 Design | 正解が複数 | 設計・Architecture | レビュー会話 (G2) |
| 6 Architecture | 正解が未来予想 | (PR 外: ADR で決定) | 事前 ADR |

正解が一意でなくなるほど AI 比率は下がり、上位ロールの責任が上がる。
AI が降りていくのではなく、段ごとに問題の性質が変わると捉える。

## 段階 → ロール ルーティング (正本: cli/config/models.yaml, cli/ROLE_MAP.md)

| 段階 | 一次担当 | 二次/エスカレーション | 対応ゲート |
|------|---------|----------------------|-----------|
| 1 Format | 自動 (pre-commit / lint) | PE (gpt-5.3-codex) | CI lint |
| 2 Lint | 自動 (静的解析) | PE | CI lint |
| 3 Style | PE / pmo-haiku | — | — (Nit 扱い) |
| 4 Logic | SE (gpt-5.4, スコア4+) / PE (1-3) | QA (gpt-5.4) / security (gpt-5.4) | G7 実装 closure |
| 5 Design | TL (gpt-5.5) | adversarial-review (高リスク時) | G2 設計凍結 |
| 6 Architecture | PM (Opus) | TL-advisor | L2 以前 / ADR |

helix review (codex review ラッパー) は Stage 1-4 の自動一次レビューを担う。
その出力を受けて、本スキルが「どの段階を人間/上位ロールに回すか」を確定する。

## Stage 4 Logic: 逆説ルール (本スキルの中核)

helix review / code-reviewer が指摘を返した箇所は AI/一次ロールに任せる。
**指摘を返さなかった箇所こそ、SE/QA が仕様書 (docs/plans/, PLAN-NNN) と照合して念入りに見る。**

理由: AI のバグ検出 recall は現状でも 5 割強が上限。コードベース内では整合していても、
仕様由来のエッジケース (空配列スキップ・リトライ条件・境界の 1 件ずれ・テナント境界等) を取りこぼす。
AI コメントがゼロの PR を「安全」と判断しない。Stage 4 は AI カバー率が中途半端 (約 6 割) で油断が生じやすいため、ここに上位ロールの集中力を最も投下する。

手順:
1. helix review の出力から「指摘あり領域」と「指摘ゼロ領域」を分離する。
2. 指摘ゼロ領域を列挙し、対応する PLAN-NNN を開いて SE/QA が仕様照合する。
3. security ゲート条件 (認証・決済・PII・外部API・インフラ変更) 該当は security ロールへ。
4. 照合記録を verification の証跡として残す (fail-close)。

## Stage 6 と ADR 降下

Stage 6 (システム境界・認証範囲・データフロー・デプロイ単位) は PR レビューで扱わない。
PR がこれらに触れている場合は「ADR (docs/adr/) で事前決定すべき」と警告し、レビューを止める。

ADR を書くと、その判断は「ADR と整合しているか」の機械チェックに変わり、
Stage 6 の一部が Stage 5/4 に降りてくる (AI/一次ロールが扱える範囲が広がる)。
暗黙のチーム合意を ADR 化する投資が、そのまま AI 委譲範囲を拡大する。
adversarial-review (G2) は ADR ドラフト完了後に自動発火するため、本スキルはその起動条件の確認に留める。

## 判定 (common/code-review と同一ラベル)

本スキルは独自の判定基準を作らない。判定は common/code-review に従う。

- Blocking 1 件以上 → Changes requested
- Blocking 0 + Nit あり → LGTM with nits
- 全なし → LGTM

段階別の Approve チェック:

```
[ ] Stage 1-2  自動ゲート (CI lint) 通過
[ ] Stage 3    Style: Nit に対応 or 却下理由を記録
[ ] Stage 4    Logic: PLAN 照合済み (AI 指摘ゼロ領域を含む) / Critical 0 件
[ ] Stage 5    Design: TL レビュー済み / 高リスクは adversarial-review 実施
[ ] Stage 6    Architecture: 該当変更は ADR と整合
→ common/code-review 判定: LGTM / LGTM with nits / Changes requested
```

## 禁止事項

- 観点や判定基準を本スキルで再定義しない (common/code-review が正本)。
- 新しいゲートや CLI コマンドを追加しない。既存の helix review / G2 / G4 に乗せる。
- AI 比率の数値を fail-close の定量基準にしない (段階の性質を示す目安)。
- AI ゼロ指摘を Approve の根拠にしない。
