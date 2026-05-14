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
- TL がデザイン方針と情報階層を確認
- Props 設計（型定義・デフォルト値・バリアント）

### .2 最小実装
- Atom → Molecule → Organism の順で実装
- デザイントークン適用（CSS変数 / Tailwind config）
- Codex 実装 role がコンポーネントを実装
- 必要に応じて PMO Sonnet に read-only レビューを依頼
- Storybook story 同時作成

### .3 安全性
- QA または TL がアクセシビリティ観点を確認
- WCAG AA 準拠確認（コントラスト/フォーカス/キーボード）
- レスポンシブ確認（mobile/tablet/desktop）
- パフォーマンス確認（バンドルサイズ/レンダリング）

### .4 テスト
- QA がテスト観点を整理し実装を補助
- コンポーネントテスト（Testing Library）
- Storybook ビジュアルリグレッション
- E2E テスト（Playwright）
- a11y 自動テスト（axe-core）

### .5 仕上げ
- TL が L5 Visual Refinement の差分を確認
- デザインカンプとの差異チェック（ピクセル単位）
- デザイントークンのハードコード残存チェック
- G5 ゲート準備（スクリーンショット3枚: desktop/tablet/mobile）

## 役割マップ

| ステップ | 委譲先 | 作業内容 | 出力 |
|---------|--------|---------|------|
| .1b | TL | デザイン方針確認 | トークン定義 YAML |
| .2 | Codex 実装 role | コンポーネント実装 | .tsx + Props 型 |
| .2 | Codex 実装 role | スタイリング | CSS/Tailwind |
| .3 | QA / TL | アクセシビリティ監査 | 指摘リスト |
| .3 | Codex 実装 role | レスポンシブ確認 | 修正パッチ |
| .4 | QA | テスト作成 | .test.tsx + .stories.tsx |
| .5 | TL | Visual Refinement | レビュー結果 |

## fullstack 駆動の場合

Phase A で BE Sprint と FE Sprint を並行実行:
- FE Sprint: 上記 .1a〜.4 を実行
- BE Sprint: API 実装を並行
- Contract CI: API 契約テストを定期実行

Phase B (L4.5 結合):
- FE → BE の API 繋ぎ込み
- MSW モック → 実 API への切替
- E2E テストで結合確認

## FE mock_to_implementation lifecycle

- L2 で mock を freeze し、`state-events.md` から TL が契約導出を完了する
- L4 で本実装へ昇格は append-only を守り、`g2_evidence_preserved` を維持する
- `evidence_status='inferred'` を起点に、G4/G6 で `confirmed` を目指す

### ペア状態

- FE の開始時は `pending`
- mock 凍結時は `design_only` / `test_only`
- 本実装完了時は `paired`
- 失敗回収時は `failed`、代替ルート時は `waived`

### G4 / G6 追加条件

- G4: `MOCK-HARDCODE` と `MOCK-CODE-LEAK` が resolved
- G6: `MOCK-DERIVED-CONTRACT` が resolved

### mock 制御（2026 更新）

- data contract を先に固定（ISO 8601 / nullability / type 一致）
- error case mock を明記（timeout, 429, 401, 500）
- production code と同等の規律で mock 管理を実施
