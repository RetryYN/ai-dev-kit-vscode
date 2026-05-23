---
doc_id: fe-detector-spec
title: "FE detector 判定仕様（動的検証の組み込み）"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# FE detector 判定仕様（動的検証の組み込み）

## 概要

FE/UX の品質を機械的に検証する FE detector 5種（axis-15〜19）の判定仕様。drive=fe / fullstack のとき deliverable_gate が動的に呼び出す。すべて決定論的で、AI判断を要しない（`--static-only` で実行可能）。

## 動的検証の組み込み

成果物の動的決定（size / drive）の枠に、検証ロジックを差し込む。

1. `helix-size` が drive を判定（`--drive fe` / `--drive fullstack` / `--ui`）。
2. `deliverable_gate` の `_resolve_artifact_candidates` が drive=fe のとき FE 成果物を候補化。
3. `_validate_fullstack_requirements` が drive に応じて FE detector を呼ぶ。
4. size により適用強度を調整（small は visual / a11y を warning、large は全 enforce）。

## 工程紐づけ

| detector | 工程 | layer | ゲート |
|---|---|---|---|
| state-transition-drift | L2 画面設計 | architecture | G2 |
| mock-promotion | L2 画面設計 | architecture | G2 |
| design-token-drift | L10 フロントデザイン | functional | 機能ゲート |
| a11y-regression | L10 フロントデザイン | functional | 機能ゲート |
| visual-regression | L10 フロントデザイン | functional | 機能ゲート |

## 判定仕様（各 detector）

各 detector は入力・判定・閾値・出力が決定論的に定まる。出力は既存の `DetectorResult`（pass/fail＋詳細）に揃える。

### axis-15 mock-promotion
- 入力: L2 のモック（`from_artifact_kind: mock`）と L7 の実装（`to_artifact_kind: component_impl`）
- 判定: モックの要素が実装へ append-only で引き継がれているか（削除・改変を検出）
- 閾値: モック要素の欠落 0 件で pass、1 件以上で fail
- 出力: pass/fail＋欠落要素リスト

### axis-16 design-token-drift
- 入力: デザイントークン定義（tokens.json 等の SSOT）と実装のスタイル値
- 判定: 実装にハードコードされた色・タイポ・スペース値が、トークン定義と一致するか
- 閾値: トークン外のハードコード値 0 件で pass
- 出力: pass/fail＋ドリフト箇所

### axis-17 a11y-regression
- 入力: レンダリング結果（色・フォントサイズ・代替テキスト）
- 判定: 色コントラスト比（WCAG AA 4.5:1、大文字 3:1）、フォントサイズ下限、代替テキストの有無
- 閾値: コントラスト比 < 4.5、または代替テキスト欠落で fail
- 出力: pass/fail＋違反要素

### axis-18 visual-regression
- 入力: ベースラインのスクリーンショットと現行のスクリーンショット
- 判定: ピクセル差分率
- 閾値: 差分率 > 設定値（例 0.1%）で fail（意図的変更は baseline 更新で承認）
- 出力: pass/fail＋差分率＋差分画像パス

### axis-19 state-transition-drift
- 入力: L2 の画面遷移定義（`state-events.md` / `state_events`）と実装の遷移
- 判定: 定義された遷移と実装の遷移が一致するか（未定義遷移・欠落遷移を検出）
- 閾値: 差分 0 で pass
- 出力: pass/fail＋不一致遷移

## ゲート連携

- G2（architecture）: state-transition-drift / mock-promotion
- 機能ゲート（functional）: design-token-drift / a11y-regression / visual-regression
- いずれも fail-close。すべて差分・数値比較で判定するため AI判断を要さない。

## CI 連携

これらは決定論的なので、ローカル（pre-push / `helix-pr --gate`）でフル実行し、CI は `.helix/phase.yaml` のゲート証跡を検証する軽量チェックに留める。drive=fe の PR では FE detector の pass 証跡を必須化する。
