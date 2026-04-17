---
name: reverse-r4
description: HELIX Reverse R4 Gap & Routing スキル。R3 Intent と As-Is の差分を Forward HELIX に振り分け
metadata:
  helix_layer: R4
  triggers:
    - R4 Gap & Routing 時
    - Forward HELIX 接続時
    - gap_register 生成時
  verification:
    - "gap_register が docs/reverse/ に存在"
    - "各 gap に routing 先が記載"
compatibility:
  claude: true
  codex: true
---

# Reverse R4 スキル

## 適用タイミング

このスキルは以下の場合に読み込む:
- R4 Gap & Routing を実施する時
- Reverse から Forward HELIX へ接続する時
- `gap_register` を新規生成または更新する時

---

## 1. R4 の目的

R4 は Reverse HELIX の終端であり、R0-R3 で観測した差分を Forward HELIX の開始点に変換する層である。

R4 で行うこと:
- 差分を `gap_register` に集約する
- 各 gap の優先度を定義する
- 各 gap を L1-L4 のどこで解消するかを決める
- Forward HELIX 入場契約を満たす形に整形する

R4 で行わないこと:
- 実装修正の実行
- 受入判定の代行
- L5-L8 への直接 routing

---

## 2. 入力と出力

### 入力
- `docs/reverse/R1-observed-contracts.*`
- `docs/reverse/R2-as-is-design.*`
- `docs/reverse/R3-intent-hypotheses.*`
- `skills/tools/ai-coding/references/gate-policy.md`

### 出力
- `docs/reverse/gap_register.md`
- 必要に応じて `docs/reverse/gap_register.yaml`

---

## 3. gap_register テンプレート

以下を最小テンプレートとして使う。

```markdown
# Gap Register

## メタ情報
- generated_at: YYYY-MM-DD
- generated_by: reverse-r4
- source_bundle:
  - R1 observed contracts
  - R2 as-is design
  - R3 intent hypotheses

## Gap 一覧
| gap_id | R3仮説 | As-Is実装 | routing先(L1-L4) | severity | owner | status |
|---|---|---|---|---|---|---|
| GAP-001 | 例: 注文は負数不可 | 負数注文が通る | L4 | critical | TL | open |
| GAP-002 | 例: 監査ログ必須 | 監査ログ仕様が未定義 | L1 | high | PM | open |

## 備考
- routing は L1/L2/L3/L4 のいずれか単一値
- status 初期値は open
```

必須カラム:
- `gap_id`
- `R3仮説`
- `As-Is実装`
- `routing先(L1-L4)`

---

## 4. 振り分けロジック

基本ルール:
- 要件ギャップ → `L1`
- 設計ギャップ → `L2`
- 詳細ギャップ → `L3`
- 実装ギャップ → `L4`

判定の具体例:
- 企画/要件文言が存在しない、または PO 判断が未確定: `L1`
- 境界設計や責務分割の再設計が必要: `L2`
- API/Schema/契約凍結の再定義が必要: `L3`
- 局所的なコード修正で閉塞可能: `L4`

昇格ルール:
- 実装ギャップでも契約変更を伴う場合は `L3` に昇格
- 詳細ギャップでも設計前提を破る場合は `L2` に昇格
- 要件再定義が必要なら常に `L1`

禁止:
- evidence 不足のまま routing を確定しない
- `TBD` や空欄 routing を許容しない

---

## 5. Forward HELIX 入場契約

R4 完了時に以下を満たすこと。

1. `gap_register` の全行に `routing先(L1-L4)` が設定済み
2. gap ごとに根拠（R1/R2/R3 参照）が1つ以上ある
3. 優先度（critical/high/medium/low）が付与済み
4. open gap の owner が決まっている

入場契約チェックリスト:

```markdown
[ ] docs/reverse/gap_register.md が存在
[ ] 全 gap の routing が L1-L4 単一値
[ ] critical/high gap の優先対応順が定義済み
[ ] Forward 着手先レイヤーを宣言済み
```

---

## 6. Forward HELIX への受け渡し

受け渡し時は、最初に着手するレイヤーを明示する。

- `L1` が1件でもある場合: L1 から再開
- `L1` がなく `L2` がある場合: L2 から再開
- `L1/L2` がなく `L3` がある場合: L3 から再開
- `L4` のみの場合: L4 実装タスクとして開始

ハンドオフ記録例:

```yaml
forward_handoff:
  entry_layer: L2
  gap_count:
    L1: 0
    L2: 3
    L3: 5
    L4: 9
  first_iteration:
    - GAP-004
    - GAP-007
```

---

## 7. RGC への接続

R4 の出力は RGC の入力である。

RGC で必要になるため、R4 時点で以下を残す:
- 全 gap の一意 ID
- closing 判定に使う evidence 種別（test/deploy/approval）
- 期待される閉塞条件

RGC 連携フィールド例:

```yaml
rgc_prep:
  gap_id: GAP-010
  expected_closure:
    - test_ref
    - deploy_ref
    - po_approval
```

---

## 8. CLI 連携メモ

`cli/helix-reverse` の `R4` は gap 出力を生成する入口として扱う。

運用上の推奨:
- `helix-reverse R4 --target <path>` で初期生成
- 生成物を `docs/reverse/gap_register.md` へ正規化
- Forward 接続時に gate-policy と整合を確認

---

## 9. 失敗パターン

- R3 仮説と As-Is 実装の対応が1対1でない
- routing 先が `L5` など仕様外値になっている
- critical gap の owner 未設定
- gap をまとめ過ぎて修正単位が粗い

対処:
- gap 粒度を「1つの修正判断単位」へ分割
- routing を再判定し、証拠を追加

---

## 10. 完了判定

R4 を `done` とする条件:
- `docs/reverse/gap_register.md` が存在
- 全 gap に `routing先(L1-L4)` が記載
- Forward HELIX の入場レイヤーが宣言済み
- RGC で使う closure 期待値が記載済み

