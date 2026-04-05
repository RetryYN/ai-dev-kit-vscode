# L4 FE スプリントガイド

> --drive fe / fullstack の場合に参照する FE 実装スプリント手順

## スプリント手順（FE 駆動）

### .1a コード調査
- 既存コンポーネント棚卸し（src/components/ のツリー構造）
- デザインシステム互換性確認（トークン/テーマ設定）
- 依存ライブラリ確認（React/Vue/Svelte + CSS フレームワーク）
- 既存テスト確認（テストカバレッジ・Storybook 有無）

### .1b 変更計画
- コンポーネントツリー設計（Atomic Design レベル割当）
- 新規/既存コンポーネントの判定
- @fe-design にデザイン方針確認を委譲
- Props 設計（型定義・デフォルト値・バリアント）

### .2 最小実装
- Atom → Molecule → Organism の順で実装
- デザイントークン適用（CSS変数 / Tailwind config）
- @fe-component に実装委譲
- @fe-style にスタイリング委譲
- Storybook story 同時作成

### .3 安全性
- @fe-a11y にアクセシビリティ監査委譲
- WCAG AA 準拠確認（コントラスト/フォーカス/キーボード）
- @fe-style にレスポンシブ確認（mobile/tablet/desktop）
- パフォーマンス確認（バンドルサイズ/レンダリング）

### .4 テスト
- @fe-test にテスト作成委譲
- コンポーネントテスト（Testing Library）
- Storybook ビジュアルリグレッション
- E2E テスト（Playwright）
- a11y 自動テスト（axe-core）

### .5 仕上げ
- @fe-design に L5 Visual Refinement 委譲
- デザインカンプとの差異チェック（ピクセル単位）
- デザイントークンのハードコード残存チェック
- G5 ゲート準備（スクリーンショット3枚: desktop/tablet/mobile）

## サブエージェント委譲マップ

| ステップ | 委譲先 | 作業内容 | 出力 |
|---------|--------|---------|------|
| .1b | @fe-design | デザイン方針確認 | トークン定義 YAML |
| .2 | @fe-component | コンポーネント実装 | .tsx + Props 型 |
| .2 | @fe-style | スタイリング | CSS/Tailwind |
| .3 | @fe-a11y | アクセシビリティ監査 | 指摘リスト |
| .3 | @fe-style | レスポンシブ確認 | 修正パッチ |
| .4 | @fe-test | テスト作成 | .test.tsx + .stories.tsx |
| .5 | @fe-design | Visual Refinement | レビュー結果 |

## fullstack 駆動の場合

Phase A で BE Sprint と FE Sprint を並行実行:
- FE Sprint: 上記 .1a〜.4 を実行
- BE Sprint: API 実装を並行
- Contract CI: API 契約テストを定期実行

Phase B (L4.5 結合):
- FE → BE の API 繋ぎ込み
- MSW モック → 実 API への切替
- E2E テストで結合確認
