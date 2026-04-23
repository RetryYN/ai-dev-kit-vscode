# ブランド DESIGN.md リファレンス — 英語版 (10件)
> 目的: ブランド別の配色・書体・UI特徴を比較し、デザイン方針を決める際に参照。

> 欧米サービスのデザイン仕様書（DESIGN.md 9セクション形式）カタログ。L2 Visual 設計・L5 Visual Refinement 時に「グローバル SaaS / AI ツール / 開発者向けプロダクト」を参考にする時の参照資料。

## ライセンス

- **Source**: [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) / [getdesign.md](https://getdesign.md/)
- **License**: MIT License
- **Copyright**: (c) 2026 VoltAgent
- **取得方法**: `npx getdesign@latest add <brand>` CLI 経由（getdesign.md のオフィシャル配布）
- **最終同期日**: 2026-04-15
- ライセンス原文: [../LICENSE-NOTICE.md](../LICENSE-NOTICE.md)

## 10 ブランド一覧

### AI / LLM プラットフォーム
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [Claude](claude.md) | AI チャット | Anthropic のダーク・ウォーム系デザイン。シリアスなトーンと読書的タイポ |

### 開発者ツール
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [Linear](linear.md) | プロジェクト管理 | ダークモードファースト・Inter 510 weight・超ミニマル・紫アクセント (#5e6ad2) |
| [Vercel](vercel.md) | PaaS | 徹底モノクロ・Geist フォント・開発者向け洗練 UI |
| [Cursor](cursor.md) | AI コーディングエディタ | VS Code ベース + AI UX・ダーク専用・密度設計 |
| [Raycast](raycast.md) | 開発者向けランチャー | 矩形コマンドパレット UX・グラデーション・macOS ネイティブ感 |
| [Supabase](supabase.md) | BaaS | 緑ブランド・ドキュメント性・DB UI の参考 |

### SaaS / 生産性
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [Stripe](stripe.md) | 決済 | 信頼感の極致・#635bff 紫・美しいドキュメント・グラデーション活用 |
| [Notion](notion.md) | ドキュメント | ミニマル・モノクロベース・ブロックエディタ UX |

### デザインツール
| ブランド | カテゴリ | 学びどころ |
|---------|---------|-----------|
| [Figma](figma.md) | デザイン SaaS | ツール UI の参考・多色アクセント・プラグイン設計 |
| [Framer](framer.md) | ノーコード・プロトタイピング | モーション重視・派手系グラデ・ビジュアル訴求 |

## 使い方

### L2 Visual 方針策定時（グローバル向けプロジェクト）
1. 類似サービスを 2-3 件選ぶ（カテゴリ or 業界）
2. 各ブランドの DESIGN.md の Color Palette・Typography Rules を参照
3. 日本市場にローカライズする場合は [brands-jp/INDEX.md](../brands-jp/INDEX.md) も併読（タイポグラフィ仕様の補完）
4. D-VIS-ARCH（Visual 設計書）に反映

### よくある選定パターン
- **B2B SaaS / ダッシュボード**: Linear + Vercel + Stripe
- **AI プロダクト**: Claude + Cursor + Linear
- **開発者向けツール**: Vercel + Supabase + Raycast
- **ミニマル ドキュメント**: Notion + Linear + Vercel
- **派手・モーション重視**: Framer + Stripe + Figma

### 英語版の特徴
- ダークモード・モノクロ・絞った 1 アクセントカラーが多い（Linear 紫 / Stripe 紫 / Vercel 白黒）
- タイポは Inter / Geist / SF Pro 系のモダンサンセリフが主流
- 日本語タイポは未対応 → 日本向けプロジェクトで使う場合は [brands-jp/INDEX.md](../brands-jp/INDEX.md) の和文ルールを必ず補う

## 英語版で参照できないブランド

以下は元計画にあったが getdesign.md に未収録のため代替ブランドを取得:

| 希望 | 状態 | 代替 |
|------|------|------|
| GitHub | 未収録 | (なし・他の開発者ツールで代替) |
| OpenAI | 未収録 | Claude（Anthropic）で代替 |
| Tailwind | 未収録 | (なし・Vercel 系で代替) |
| Anthropic | **収録**（`claude` として） | ✓ 取得済み |

追加取得候補（必要時に `npx getdesign@latest add <brand>` で取得）: apple / airbnb / hashicorp / mistral.ai / cohere / elevenlabs / posthog / sentry / shopify / resend / mintlify / sanity / x.ai / webflow

## 取得方法

### 新規ブランド追加
```bash
# brands-en/ に追加したいブランドを取得
cd /tmp
npx getdesign@latest add <brand-name>
cp DESIGN.md ~/ai-dev-kit-vscode/skills/common/visual-design/references/brands-en/<brand>.md
```

### 利用可能ブランド一覧確認
```bash
# エラーメッセージから全リスト取得
npx getdesign@latest add nonexistent 2>&1 | grep "Available brands"
```

## 関連資料

- [../design-md-format.md](../design-md-format.md) — DESIGN.md 9セクションフォーマット詳細
- [../brands-jp/INDEX.md](../brands-jp/INDEX.md) — 日本版ブランド（24件）
- [../../SKILL.md](../../SKILL.md) — visual-design スキル本体
- [../../../design-tools/web-system/SKILL.md](../../../design-tools/web-system/SKILL.md) — shadcn/ui 実装への展開
