# L5 Visual Design 仕様書

## 1. デザイン方針
### 1.1 デザインコンセプト
<!-- プロダクトの視覚的方向性を記述する -->
<!-- 記入例:
「信頼感と親しみやすさの両立」
- 業務ツールとしての堅牢さをベースに、操作の軽快さを演出
- 余白を十分に取り、情報密度を抑えたクリーンなレイアウト
- ユーザーの習熟度に応じて段階的に機能を開示するプログレッシブ・ディスクロージャー
-->

### 1.2 デザイントークン
| カテゴリ | トークン名 | 値 | 用途 |
|---------|-----------|-----|------|
| Color/Primary | --color-primary | #xxxx | CTA・ブランド |
| Color/Secondary | --color-secondary | #xxxx | 補助・サブアクション |
| Color/BG | --color-bg | #xxxx | ページ背景 |
| Color/Surface | --color-surface | #xxxx | カード・モーダル背景 |
| Color/Text | --color-text | #xxxx | 本文テキスト |
| Color/Text-Muted | --color-text-muted | #xxxx | 補助テキスト |
| Color/Error | --color-error | #xxxx | エラー状態 |
| Color/Warning | --color-warning | #xxxx | 警告状態 |
| Color/Success | --color-success | #xxxx | 成功状態 |
| Color/Info | --color-info | #xxxx | 情報通知 |
| Color/Border | --color-border | #xxxx | 区切り線・枠線 |
| Spacing/xs | --space-xs | 4px | アイコンとラベルの間隔 |
| Spacing/sm | --space-sm | 8px | 密接な要素間 |
| Spacing/md | --space-md | 16px | 標準要素間 |
| Spacing/lg | --space-lg | 24px | セクション内の区切り |
| Spacing/xl | --space-xl | 32px | セクション間の区切り |
| Spacing/2xl | --space-2xl | 48px | 大きなブロック間 |
| Font/Body | --font-body | | 本文テキスト |
| Font/Heading | --font-heading | | 見出し・タイトル |
| Font/Mono | --font-mono | | コード・数値 |
| Font/Size/xs | --font-size-xs | 12px | キャプション・注釈 |
| Font/Size/sm | --font-size-sm | 14px | 補助テキスト・ラベル |
| Font/Size/md | --font-size-md | 16px | 本文 |
| Font/Size/lg | --font-size-lg | 20px | 小見出し |
| Font/Size/xl | --font-size-xl | 24px | セクション見出し |
| Font/Size/2xl | --font-size-2xl | 32px | ページタイトル |
| Font/Weight/normal | --font-weight-normal | 400 | 本文 |
| Font/Weight/medium | --font-weight-medium | 500 | ラベル・強調 |
| Font/Weight/bold | --font-weight-bold | 700 | 見出し |
| Line-Height/tight | --line-height-tight | 1.25 | 見出し |
| Line-Height/normal | --line-height-normal | 1.5 | 本文 |
| Line-Height/relaxed | --line-height-relaxed | 1.75 | 長文 |
| Radius/sm | --radius-sm | 4px | 入力フィールド |
| Radius/md | --radius-md | 8px | カード・ボタン |
| Radius/lg | --radius-lg | 12px | モーダル・ダイアログ |
| Radius/full | --radius-full | 9999px | アバター・バッジ |
| Shadow/sm | --shadow-sm | 0 1px 2px rgba(0,0,0,0.05) | ボタン・入力フィールド |
| Shadow/md | --shadow-md | 0 4px 6px rgba(0,0,0,0.1) | カード・ドロップダウン |
| Shadow/lg | --shadow-lg | 0 10px 15px rgba(0,0,0,0.1) | モーダル・ダイアログ |
| Transition/fast | --transition-fast | 150ms ease | ホバー・フォーカス |
| Transition/normal | --transition-normal | 250ms ease | 開閉・展開 |
| Transition/slow | --transition-slow | 400ms ease | ページ遷移 |
| Z-Index/dropdown | --z-dropdown | 100 | ドロップダウンメニュー |
| Z-Index/sticky | --z-sticky | 200 | 固定ヘッダー |
| Z-Index/modal | --z-modal | 300 | モーダル・オーバーレイ |
| Z-Index/toast | --z-toast | 400 | トースト通知 |

<!-- 記入例:
| Color/Primary | --color-primary | #2563EB | CTA・ブランド |
| Color/Secondary | --color-secondary | #64748B | 補助・サブアクション |
| Color/BG | --color-bg | #FFFFFF | ページ背景 |
| Font/Body | --font-body | 'Inter', 'Noto Sans JP', sans-serif | 本文テキスト |
-->

### 1.3 配色比率
- メイン (70%): --color-bg + --color-surface
- サブ (25%): --color-secondary + --color-text-muted
- アクセント (5%): --color-primary

## 2. レイアウト設計
### 2.1 ブレークポイント
| 名前 | 幅 | レイアウト | コンテナ幅 |
|------|-----|----------|-----------|
| mobile | < 640px | 1カラム | 100% |
| tablet | 640-1024px | 1-2カラム | 100% |
| desktop | 1024-1280px | 2-3カラム | 1024px |
| wide | > 1280px | 3カラム | 1280px |

### 2.2 グリッドシステム
- カラム数: 12
- ガター: --space-md (16px)
- マージン: mobile 16px / tablet 24px / desktop 32px
- 最大コンテンツ幅:

### 2.3 レイアウトパターン
<!-- 主要なレイアウトパターンを定義する -->
<!-- 記入例:
- ヘッダー固定 + サイドバー + メインコンテンツ（desktop）
- ヘッダー固定 + ボトムナビ + フルワイドコンテンツ（mobile）
-->

## 3. コンポーネント仕様
### 3.1 コンポーネント一覧
| ID | コンポーネント | 種別 | 状態数 | 対応画面 | 備考 |
|----|--------------|------|--------|---------|------|
| C-001 | Button | Atom | 5 (default/hover/active/focus/disabled) | 全画面 | Primary/Secondary/Ghost バリアント |
| C-002 | Input | Atom | 5 (default/focus/filled/error/disabled) | フォーム画面 | |
| C-003 | Card | Molecule | 2 (default/hover) | 一覧画面 | |
<!-- 記入例:
| C-001 | Button | Atom | 5 | 全画面 | size: sm/md/lg, variant: primary/secondary/ghost/danger |
| C-002 | TextInput | Atom | 5 | フォーム画面 | label/placeholder/helperText/errorMessage |
| C-003 | UserCard | Molecule | 2 | ダッシュボード | avatar + name + role badge |
| C-004 | DataTable | Organism | 3 | 一覧画面 | sort/filter/pagination 対応 |
| C-005 | Navigation | Organism | 2 | 全画面 | desktop: sidebar / mobile: bottom-nav |
-->

### 3.2 状態遷移
<!-- 各コンポーネントの状態遷移をテーブルで定義する -->
| コンポーネント | トリガー | 遷移元 | 遷移先 | アニメーション |
|-------------|---------|--------|--------|-------------|
| Button | hover | default | hover | --transition-fast |
| Button | mousedown | hover | active | --transition-fast |
| Button | focus | * | focus | --transition-fast |
| Input | focus | default | focus | --transition-fast |
| Input | blur + valid | focus | filled | --transition-fast |
| Input | blur + invalid | focus | error | --transition-fast |

### 3.3 バリアント定義
<!-- 主要コンポーネントのバリアントを定義する -->
| コンポーネント | バリアント | 用途 | トークン上書き |
|-------------|----------|------|-------------|
| Button | primary | メインアクション | bg: --color-primary |
| Button | secondary | サブアクション | bg: --color-secondary |
| Button | ghost | テキストリンク風 | bg: transparent |
| Button | danger | 破壊的操作 | bg: --color-error |

## 4. 画面詳細
### S-001: [画面名]
- **ワイヤーフレーム**:
```
+-------------------------------------------+
| Header                         [User] [+] |
+--------+----------------------------------+
| Nav    | Main Content                     |
|        |                                  |
|        | +-----+ +-----+ +-----+         |
|        | |Card | |Card | |Card |         |
|        | +-----+ +-----+ +-----+         |
|        |                                  |
+--------+----------------------------------+
```
- **レイアウト**:
  - mobile: ヘッダー + フルワイド + ボトムナビ
  - tablet: ヘッダー + 2カラムグリッド
  - desktop: ヘッダー + サイドバー + 3カラムグリッド
- **インタラクション**:
  - クリック:
  - ホバー:
  - スクロール:
- **アニメーション**:
  - transition: --transition-normal
  - duration:
  - easing:
- **エラー状態**:
  - バリデーションメッセージの配置:
  - エラー時のコンポーネント状態:
  - グローバルエラー表示位置:
- **ローディング状態**:
  - スケルトン / スピナー / プログレスバー:
  - 表示タイミング:
- **空状態**:
  - データなし時の表示:

<!-- 記入例:
### S-001: ダッシュボード
- **ワイヤーフレーム**: (上記 ASCII art 参照)
- **レイアウト**: desktop 3カラム / tablet 2カラム / mobile 1カラム + ボトムナビ
- **インタラクション**: カード hover でシャドウ拡大、クリックで詳細画面遷移
- **アニメーション**: カード表示時 fade-in 0.3s stagger 0.05s
- **エラー状態**: API エラー時はトースト通知 + リトライボタン
- **ローディング状態**: 初回読み込みはスケルトン、リフレッシュ時はスピナー
- **空状態**: イラスト + 「データがありません」 + アクションボタン
-->

## エラー状態の UI 設計

### エラーメッセージのガイドライン
| 種別 | ユーザーに見せる | 見せない |
|------|---------------|---------|
| バリデーション | 「メールアドレスの形式が正しくありません」 | 「regex /^[a-z]/ にマッチしません」 |
| 認証エラー | 「ログイン情報が正しくありません」 | 「JWT 署名検証失敗」 |
| サーバーエラー | 「エラーが発生しました。時間をおいて再度お試しください」 | スタックトレース |
| 権限エラー | 「この操作を行う権限がありません」 | 「RBAC: role=user, required=admin」 |
| Not Found | 「ページが見つかりません」 | 「Route /api/v1/internal/... not found」 |

### エラーページデザイン
- 404: フレンドリーなイラスト + ホームへのリンク
- 500: お詫びメッセージ + サポートへのリンク
- 403: 権限説明 + ログインへのリンク
- オフライン: 再接続待ちアニメーション

## 5. アクセシビリティ
### 5.1 WCAG 2.1 AA 準拠チェック
- [ ] コントラスト比 4.5:1 以上（通常テキスト: --font-size-md 以下）
- [ ] コントラスト比 3:1 以上（大テキスト: --font-size-lg 以上）
- [ ] コントラスト比 3:1 以上（UI コンポーネント・アイコン）
- [ ] フォーカスインジケータ visible（2px 以上の明確な視覚変化）
- [ ] キーボードナビゲーション可能（Tab / Shift+Tab / Enter / Escape）
- [ ] フォーカストラップ実装（モーダル・ダイアログ内）
- [ ] aria-label / aria-describedby 設定（アイコンボタン・入力フィールド）
- [ ] aria-live 設定（動的に変化するコンテンツ・通知）
- [ ] スクリーンリーダー対応（見出し階層・ランドマーク・読み上げ順序）
- [ ] 画像に alt テキスト（装飾画像は alt=""）
- [ ] color だけに依存しない情報伝達（エラーはアイコン + テキスト併用）
- [ ] 動きの無効化対応（prefers-reduced-motion）

### 5.2 レスポンシブチェック
- [ ] mobile (< 640px) 表示崩れなし
- [ ] tablet (640-1024px) 表示崩れなし
- [ ] desktop (1024-1280px) 表示崩れなし
- [ ] wide (> 1280px) 表示崩れなし
- [ ] タッチターゲット 44x44px 以上（mobile）
- [ ] 横スクロール発生なし（mobile）
- [ ] テキスト折り返し正常（長い文字列・日本語）
- [ ] 画像・メディアのアスペクト比維持

## 6. ダークモード（該当する場合）
| トークン | ライト | ダーク |
|---------|--------|------|
| --color-bg | | |
| --color-surface | | |
| --color-text | | |
| --color-text-muted | | |
| --color-border | | |
| --color-primary | | |
| --color-error | | |
| --color-success | | |

<!-- 記入例:
| --color-bg | #FFFFFF | #0F172A |
| --color-surface | #F8FAFC | #1E293B |
| --color-text | #0F172A | #F8FAFC |
| --color-text-muted | #64748B | #94A3B8 |
| --color-border | #E2E8F0 | #334155 |
-->

### 6.1 ダークモード切替方式
- [ ] system（OS設定に追従: prefers-color-scheme）
- [ ] manual（ユーザー手動切替）
- [ ] 両対応（デフォルト system + 手動オーバーライド）

## 7. アイコン・画像ガイドライン
### 7.1 アイコンセット
- ライブラリ:
- サイズ: 16px / 20px / 24px
- ストローク幅:
- カラールール: --color-text / --color-text-muted

### 7.2 画像仕様
| 用途 | アスペクト比 | 最大サイズ | フォーマット | fallback |
|------|------------|-----------|------------|----------|
| サムネイル | 1:1 | 200KB | WebP | JPEG |
| ヒーロー | 16:9 | 500KB | WebP | JPEG |
| アバター | 1:1 | 100KB | WebP | PNG |

## 8. モーション・アニメーション設計
### 8.1 アニメーション原則
- 目的のあるアニメーションのみ使用（装飾的アニメーション禁止）
- 300ms 以下を基本とする（ユーザーの待機感を生まない）
- prefers-reduced-motion 時はアニメーション無効化

### 8.2 アニメーション一覧
| 名前 | 対象 | 種別 | duration | easing | 用途 |
|------|------|------|----------|--------|------|
| fade-in | ページ | opacity | 250ms | ease-out | ページ遷移 |
| slide-up | モーダル | transform | 250ms | ease-out | モーダル表示 |
| collapse | アコーディオン | height | 200ms | ease-in-out | 開閉 |

## 9. 目視確認チェックリスト
| 画面 | desktop | tablet | mobile | ダーク | 判定 |
|------|---------|--------|--------|--------|------|
| S-001 | [ ] | [ ] | [ ] | [ ] | pending |

### 9.1 スクリーンショット格納先
- `.helix/visual-checks/{画面ID}-screenshots/desktop.png`
- `.helix/visual-checks/{画面ID}-screenshots/tablet.png`
- `.helix/visual-checks/{画面ID}-screenshots/mobile.png`

### 9.2 最終確認
- [ ] 全画面の目視確認完了
- [ ] デザイントークンが実装に正しく反映されている
- [ ] L2 設計書のデザイン方針と一貫性がある
- [ ] 不要なハードコードスタイル値がない
- [ ] AI っぽさのない自然なUI表現になっている
