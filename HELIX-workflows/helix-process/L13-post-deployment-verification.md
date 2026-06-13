---
doc_id: process-l13-post-deployment-verification
title: L13 運用検証 / 運用テスト — 工程定義
status: accepted
accepted_date: 2026-05-24
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
integration_target:
  docs_path: docs/specs
  category: L0-L14 工程
---

# L13 運用検証 / 運用テスト

## 工程の位置づけ

| 項目 | 内容 |
|---|---|
| 区分 | V字 右腕（運用フェーズ） |
| 入力 | L12 受入テスト |
| 出力 | L14 への入力 |
| 対応する設計 | — |

## この工程の PLAN

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L13-運用検証plan`
- 実環境動作確認
- 初期監視

### `L13-運用テストplan`
- 運用手順の検証
- smoke / canary / 初期インシデント対応

## PLAN が内蔵するもの

- **工程表**: そのドキュメントを完成させる手順（例: 参考調査の Web 検索 → 既存資料・ヒアリング整理 → ドラフト → TL レビュー → 確定）と各手順の進捗
- **実装計画**: 記載項目をどう埋めるかの計画
