# ブランド DESIGN.md リファレンス — 日本版 (24件)

> 日本サービスのデザイン仕様書（DESIGN.md 9セクション形式）カタログ。L2 Visual 設計・L5 Visual Refinement 時に「類似ブランド」を参照して配色・タイポグラフィ・レイアウト方針を検討するための資料。

## ライセンス

- **Source**: [kzhrknt/awesome-design-md-jp](https://github.com/kzhrknt/awesome-design-md-jp)
- **License**: MIT License
- **Copyright**: (c) 2026 awesome-design-md-jp contributors
- **最終同期日**: 2026-04-15
- **同期コミット**: 要追従（年次棚卸し時に更新）
- ライセンス原文: [../LICENSE-NOTICE.md](../LICENSE-NOTICE.md)

## なぜ日本版が必要か

日本語 UI は欧文圏とは根本的に異なるタイポグラフィ仕様が必要:

- **CJK フォントフォールバック**（和文 → 欧文 → generic）
- **高めの line-height**（1.5–2.0 vs 欧文 1.4–1.5）
- **日本語の字間**（本文で 0.04–0.1em）
- **禁則処理**（CJK 句読点の改行ルール）
- **OpenType 機能**（`palt`, `kern` によるプロポーショナル和文組版）
- **混植ルール**（和欧文混在時のフォント切替）

これらを仕様書化していないと AI エージェントは壊れたタイポグラフィで日本語 UI を生成してしまう。このカタログはその解決策。

## 24 ブランド一覧（カテゴリ別）

### フィンテック・業務 SaaS
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [freee](freee.md) | 会計 SaaS | 信頼感重視・和文厳密指定・クリーンビジネス UI |
| [MoneyForward](moneyforward.md) | フィンテック | 金融 UI の情報密度と安心感の両立 |
| [SmartHR](smarthr.md) | HR SaaS | Stone palette × #0077c7・Yu Gothic・業務ミニマル |
| [Cybozu](cybozu.md) | グループウェア | 業務効率重視・情報密度・操作性 |
| [Sansan](sansan.md) | 名刺 SaaS | B2B の信頼感・落ち着いた配色 |

### EC・マーケットプレイス
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [Mercari](mercari.md) | C2C | メルカリレッド #ff333f・Panda CSS・モバイルファースト |
| [Rakuten](rakuten.md) | 総合 EC | 情報密度高レイアウト・楽天カラー・ファネル導線 |
| [MUJI](muji.md) | 小売・ライフスタイル | 無印良品のミニマル・余白美学・和のタイポ |
| [Cookpad](cookpad.md) | レシピ UGC | 料理写真中心のビジュアル・UGC 読みやすさ |
| [Tabelog](tabelog.md) | グルメ | レビュー UX・評価スコア表示・エリア絞り込み |

### メディア・コミュニティ
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [note](note.md) | メディアプラットフォーム | 読み物の可読性・余白・書き手体験 |
| [pixiv](pixiv.md) | クリエイタープラットフォーム | 濃密コンテンツレイアウト・クリエイター UX |
| [Zenn](zenn.md) | 技術記事 | 開発者向けタイポグラフィ・コードブロック・読みやすさ |
| [Qiita](qiita.md) | 開発者コミュニティ | エンジニア向け UI・タグ運用・コードハイライト |
| [WIRED.jp](wired.md) | テックメディア | 雑誌的レイアウト・見出しヒエラルキー・濃淡表現 |
| [ABEMA](abema.md) | 動画配信 | ダークテーマ・番組表 UI・ライブ感 |

### メッセージ・プラットフォーム
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [LINE](line.md) | メッセンジャー | LINE グリーン・モバイルチャット UI・スタンプ UX |
| [Notion](notion.md) | 生産性 | Notion 日本語適用版・ミニマル・ドキュメント UI |
| [connpass](connpass.md) | 技術イベント | イベント一覧 UI・日付表示・参加導線 |

### コンシューマー・ブランド
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [Apple](apple.md) | 家電 | プレミアム感・プロダクト写真・高級タイポ |
| [Toyota](toyota.md) | 自動車 | ヘビーウェイト見出し・ブランド威厳・車種表現 |

### エージェンシー・クリエイティブ
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [Droga5](droga5.md) | クリエイティブエージェンシー | ブランドインパクト・大胆な表現・モダンタイポ |
| [STUDIO](studio.md) | ノーコードデザインツール | デザインツール UI・クリエイター体験 |
| [Novasell](novasell.md) | AI エージェンシー | AI サービスの表現・モダンな構成 |

## 使い方

### L2 Visual 方針策定時
1. 類似ブランドを 2-3 件選ぶ（カテゴリ or テイストで）
2. `DESIGN.md` の Color Palette・Typography Rules・Component Stylings を参照
3. 自プロジェクト用に「参考箇所」「独自化箇所」を切り分け
4. D-VIS-ARCH（Visual 設計書）に反映

### L5 Visual Refinement 時
1. 実装結果が参照ブランドから乖離していないか対比
2. 特に日本語タイポ（font-family フォールバック・line-height・letter-spacing・禁則）を重点確認
3. 違和感があれば DESIGN.md のルールに合わせて調整

### 日本語タイポグラフィのクイック参考
- **line-height 1.6-1.8** が多数派（欧文より高め）
- **font-family** は `"Hiragino Kaku Gothic ProN", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif` 系が主流
- **letter-spacing** 0.04-0.08em（本文）
- **OpenType** `palt` はほぼ全ブランドで有効化（プロポーショナル和文）

## 関連資料

- [../design-md-format.md](../design-md-format.md) — DESIGN.md 9セクションフォーマット詳細
- [../brands-en/INDEX.md](../brands-en/INDEX.md) — 英語版ブランド（10件）
- [../accessibility-design.md](../accessibility-design.md) — 日本語 a11y 設計論
- [../../SKILL.md](../../SKILL.md) — visual-design スキル本体
