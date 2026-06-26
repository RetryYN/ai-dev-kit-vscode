# D-SCRUM-UNITIZED-FORWARD — Scrum 駆動 unitized Forward + internal-MCP 風 agent query 契約

> 2026-06-27 / status: draft（設計 seed・可逆） / 提案者: user / 起草: PM(Opus) 自走
> Forward 接続先: ① = `HELIX-workflows/helix-process/scrum-workflow.md` の精緻化 /
> ② = `HELIX-workflows/helix-process/two-stage-agent-design.md` の精緻化（HELIX W）。
> 本書は設計記録（P-tier）。confirm 後に各 G-tier workflow doc へ昇格する。

## 動機

大規模サース / 複雑設計で、L0-L14 を一枚岩の Forward で通すと unit が大きすぎて凍結・検証が粗くなる。
**基本設計（L4）までは統一して Forward で降ろし、実装が大きいときは unit 単位に分割して
詳細設計（L5）⇒機能設計（L6）⇒実装（L7）の micro-Forward を細かく刻む**ことで、大規模・複雑性に対応する。

## ① Scrum 駆動 unitized Forward

### 構造

```
L0 ─ L1 ─ L3 ─ L4（基本設計：統一・単一）        ← ここまで一枚岩で凍結
                 │
                 ├─ unit A: L5 ⇒ L6 ⇒ L7（micro-Forward・検証閉合）─┐
                 ├─ unit B: L5 ⇒ L6 ⇒ L7 ─────────────────────────┤→ 単一 V-model DB へ rejoin
                 └─ unit C: L5 ⇒ L6 ⇒ L7 ─────────────────────────┘   （L8/L9 で統合検証）
```

- **L4 統一**: システム境界・コンポーネント分割・契約は L4 で単一に凍結（unit はこの分割から導出）。
- **per-unit micro-Forward**: 各 unit = 縦スライス1本（1 FR/機能群）。自分の L5⇒L6⇒L7 と
  対の検証（L8 結合 / L7 単体）を持ち、pair_closure で閉じる。
- **収束（絶対原則）**: 各 unit の L7 closure は統一 L4 設計へ rejoin し、単一 V-model DB に収束する。
  unit-Forward は枝であって代替でない（HELIX_CORE §0）。

### 規律（この session で実証済み）

本 session の V3 detector 追加（FN-DET-04/15/17/18）は、まさにこの unitized micro-Forward だった:
- 各 detector = 1 unit（自分の L6 設計＝検出契約 → L7 実装 → 単体テスト → 検証 → commit）。
- **共有状態の直列化**: 共有ファイル（core.py の CORE_DETECTORS）を touch する unit は直列、
  独立 unit は並列（既存「並列8・衝突判定」規律と地続き）。
- **unit ごとに独立検証 → commit**（pytest green を unit 境界で確認）。

### 開ける設計問題（confirm 要）

- unit 境界の正式定義（縦スライス粒度 = L4 のどの分割単位に対応させるか）。
- unit 間依存（後段 unit が前段 unit の出力を入力にする場合）の Forward 表現と直列化判定。
- 既存 `helix scrum` mode（discovery 駆動）との関係: unitized-Forward は「L4 後の実装分割」、
  scrum は「要件未確定の反復」。別ステージとして両立させるか統合するか。

## ② internal-MCP-server 風 agent query 契約（②は①の上の agent 設計レイヤ）

### 着想

エージェントシステムを設計するとき（HELIX W / two-stage-agent-design）、各機能の問い合わせを
ad-hoc 呼び出しでなく**宣言された query 契約（内部 MCP server の tool schema 風 = typed request/response）**
として設計する。

### なぜ HELIX カラーが出るか

- **DbC と直結**: query 契約 = requires/ensures = L6 機能設計（関数粒度の契約）そのもの。
  設計とテストが契約で機械的に閉じる（粒度ペアリング原則 L6↔L7）。
- **検証単位 = 契約**: query 契約が各 agent 機能の単体テスト面になる（FN↔UT ペアリングと一致）。
- **既に芽がある**: V3 detector は全てこの形（`Input → analyze(pure) → messages/Result` = query 契約）。
  V3 の INTQ（internal-query）detector 3 本がこの seed。②は detector で実証した pure-function
  query 契約を **agent 機能一般へ一般化**する話で、地に足がついている。

### 開ける設計問題（confirm 要）

- query 契約の schema 表現（JSON Schema 風 / dataclass / DbC アノテーション のどれを正本にするか）。
- 「内部 MCP server」を比喩に留めるか、実際に MCP プロトコルで実装するか（後者は重い）。
- two-stage-agent-design（Phase1 一般システム V / Phase2 エージェント昇華 V）の
  どの L にこの契約設計を載せるか（L6 機能設計が自然）。

## 進め方

1. ①を先に formalize（即実行可能・本 session で実証済み）→ `scrum-workflow.md` へ unit 分割ステージを追補。
2. ②を②レイヤとして①の上に載せる → `two-stage-agent-design.md` の L6 に query 契約設計を追補。
3. 各々 L4 基本設計 PLAN として起票し、HELIX DB へ収束（phase 4 HELIX 独自強化）。

> 本書は draft（可逆）。confirm された範囲だけ G-tier workflow doc へ昇格する。未 confirm の設計問題は
> 上記「開ける設計問題」に残し、勝手に確定しない（設計 intent は user/設計判断に属する）。
