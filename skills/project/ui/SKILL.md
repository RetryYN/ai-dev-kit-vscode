---
name: ui
description: FE サブエージェント 5種のインデックス。タスク内容に応じ fe-design / fe-component / fe-style / fe-a11y / fe-test へルーティング
metadata:
  helix_layer: L2
  triggers:
    - FE 駆動タイプ着手時
    - FE 領域の役割分担判断時
    - UI 設計 / コンポーネント / スタイル / a11y / テストの開始時
  verification:
    - "タスクに応じた fe-* 専用スキルが選択できていること"
compatibility:
  claude: true
  codex: true
---

# FE 5種インデックス（ルーター）

## 役割

このスキルは FE タスクの入口です。実装や検証を直接抱えず、タスク内容に応じて `fe-*` 専用スキルへ委譲します。

- 目的: FE 駆動での役割分担を明確化する
- 境界: 方針レベルの振り分けのみ行い、実装詳細は各 `fe-*` で扱う
- 出力: 選択した委譲先スキル名と理由

---

## ルーティング表

| 用途 | 委譲先 | パス |
|------|-------|------|
| 情報アーキテクチャ・画面構成 (L2) | fe-design | skills/project/fe-design/SKILL.md |
| コンポーネント実装 (L4) | fe-component | skills/project/fe-component/SKILL.md |
| スタイル・デザイントークン (L4/L5) | fe-style | skills/project/fe-style/SKILL.md |
| アクセシビリティ (L4/L5/L6) | fe-a11y | skills/project/fe-a11y/SKILL.md |
| FE テスト (L4/L6) | fe-test | skills/project/fe-test/SKILL.md |

---

## 使い方

1. Opus PM が FE タスクを受領する
2. タスクの主目的を上表に照合する
3. 該当スキルを `@fe-<name>` で呼び出す
4. 複合タスク時は主担当を1つ決め、必要に応じて副次スキルを追加する

### 呼び出し例

- 画面遷移と情報優先度の設計: `@fe-design`
- ボタン/フォームの実装: `@fe-component`
- トークン定義とテーマ調整: `@fe-style`
- キーボード操作・読み上げ配慮: `@fe-a11y`
- UI の単体/統合/E2E テスト: `@fe-test`

---

## visual-design との関係

- `common/visual-design`: L2 方針と L5 仕上げの概念、見せ方の原則、審美性の判断基準
- `project/fe-*`: 上記方針をコード・構造・検証へ具体化する実装系スキル

使い分けの基本は「概念と判断は visual-design、実装と検証は fe-*」です。

---

## 移管メモ（旧 ui スキルからの変更）

旧 `project/ui` に含まれていた以下の実装内容は各専用スキルへ移管済みです。

- Atomic Design ベースの分割指針 → `fe-design` / `fe-component`
- Props 設計と実装パターン → `fe-component`
- スタイル・デザイントークン運用 → `fe-style`
- a11y チェック（axe-core 等） → `fe-a11y`
- FE テスト設計と実装 → `fe-test`

この `ui` は後方互換のため残しつつ、FE 5種へのインデックスとして運用します。
