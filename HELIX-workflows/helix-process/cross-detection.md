---
doc_id: cross-detection
title: "HELIX 横断検出（依存漏れ・契約漏れ・デグレ回避）"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# HELIX 横断検出（依存漏れ・契約漏れ・デグレ回避）

## 概要

helix_db を横断して、依存関係の漏れ・契約の漏れ・デグレード（回帰）を検出する。doctor が全 detector を集約し、検出結果を detection-routing.md が適切なモードへつなぐ。

## 検出対象

| 検出 | detector | 内容 |
|---|---|---|
| 依存漏れ | axis-10 relation-graph | 関係グラフの orphan / missing / cycle |
| 契約漏れ（doc） | axis-07 doc-drift | missing required doc / model drift |
| 接続欠損 | axis-12 connection-deficiency | コンポーネント間の接続の欠損 |
| デグレ（回帰） | axis-11 regression | test_baseline との比較 |

## 横断集約（doctor）

helix-doctor が全 detector を横断実行し、依存・契約・回帰の漏れを一括で洗い出す。recovery plan の鮮度チェックや stale lock の掃除も併せて行う。

## デグレ回避

- axis-11 が test_baseline と現行を比較し、回帰（デグレ）を検出する。
- baseline はコミットごとに更新し、デグレ検出時は fail-close で止める。
- これにより「直したつもりが別を壊す」を機械的に防ぐ。

## detection-routing との連携

検出した漏れ・デグレを、対応モードへルーティングする（detection-routing.md）。

| 検出 | ルーティング先 |
|---|---|
| 依存漏れ | Reverse（design type で依存を整理） |
| 契約漏れ・接続欠損 | Reverse（normalization）/ drift-check |
| デグレ（回帰） | 本番なら Incident、開発中なら Recovery |

## 横断トラブル解決の流れ

```
doctor が detector を横断実行
   → 依存漏れ / 契約漏れ / 接続欠損 / デグレ を検出
   → detection-routing でモード発動
   → 対応 kind の PLAN 起票
   → 修正 → 自動登録 → 再検出
```

単一の工程内では見えない横断的な漏れ（依存・契約・回帰）を、DB 横断の detector と doctor で機械的に拾い、モードへつなぐ。Learning Engine（learning-engine.md）が頻出パターンを学べば、これらの漏れは事前の予防ルールにも反映される。
