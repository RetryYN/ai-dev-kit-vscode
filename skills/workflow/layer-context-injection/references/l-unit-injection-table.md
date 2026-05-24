> 目的: L0-L14 の工程概念を 20 セルの injection-set 実体へ対応付ける一覧を示す

# L Unit Injection Table

## L0-L14 と layer 対応

| 工程 | 主な概念 layer | 代表 owner_role | 注入の焦点 |
|---|---|---|---|
| L0 | planning | pm | 企画と整理 |
| L1 | planning | pm | 要求と前提条件 |
| L2 | requirement | pm / fe | UI 設計と判断材料 |
| L3 | requirement | pm / tl | 要件凍結と受入条件 |
| L4 | architecture | tl | 基本設計とゲート判断 |
| L5 | detailed | tl / dba | 詳細設計と契約 |
| L6 | functional | se | 単体設計と実装前準備 |
| L7 | functional | se | 実装と単体テスト |
| L8 | functional | qa / tl | 結合検証 |
| L9 | architecture | tl | 総合検証 |
| L10 | requirement | fe / tl | UX 磨き上げ |
| L11 | requirement | pm / tl | 最終レビュー |
| L12 | planning | devops / pm | デプロイと受入 |
| L13 | planning | devops | 実環境安定化 |
| L14 | planning | pm | 運用学習と次サイクル接続 |

## mode 別の読み替え

| mode | 注入時の強調点 |
|---|---|
| forward | 現在工程に必要な skill と command を狭く提示する |
| reverse | explorer と verification を厚めに出す |
| scrum | 検証用 skill と hypothesis 系 command を厚めに出す |
| discovery | 不確実性が高いので recommended_agents を増やす |

## 実務上の見方

- L0-L14 は人間が理解しやすい工程番号
- 20 セルは機械が使いやすい実体キー
- 同じ工程でも drive によって recommended_skills と recommended_commands は変わる
