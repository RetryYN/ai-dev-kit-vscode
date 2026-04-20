---
name: fe-design
description: FE 情報アーキテクチャ (D-IA) 設計スキル。ページマップ・ナビゲーション階層・ラベル定義を行い、visual-design §①information の具体実装を担当する
metadata:
  helix_layer: L2
  triggers:
    - "L2 IA 設計時"
    - "L5 情報階層確認時"
    - "D-IA 生成時"
    - "コンテンツマップ設計時"
    - "モック作成時"
    - "プロトタイプ生成時"
    - "インタラクション設計時"
  outputs:
    - "docs/fe/D-IA.md"
    - ".helix/mock/<feature>/mock.html（fe 駆動時のみ必須）"
    - ".helix/mock/<feature>/state-events.md（fe 駆動時のみ必須）"
  verification:
    - "D-IA が docs/fe/ に存在する"
    - "ページ一覧と階層が可視化済み"
    - "ナビゲーションラベルが確定している"
    - "fe 駆動時: .helix/mock/<feature>/mock.html が存在し、ブラウザで開いて触れる状態である（throw-away 前提）"
    - "fe 駆動時: state-events.md に画面状態一覧・イベント一覧・状態遷移図（stateDiagram-v2）が記載されている"
    - "be 駆動時: mock.html / state-events.md は optional（未作成可）"
compatibility:
  claude: true
  codex: true
---

# FE 情報アーキテクチャ (D-IA) 設計スキル

## visual-design との関係

visual-design スキルの **①information** ステップの具体実装を担当する。
visual-design が「何を決めるか」を定義し、fe-design が「どう文書化するか」を実行する。
また、fe 駆動時は L2 で動くモックと状態・イベント定義までを出力し、L3 の API 契約導出入力を担保する。

```
visual-design §①information（方針）
  ↓
fe-design（D-IA 具体化）
  ↓ D-IA ファイル: docs/fe/D-IA.md
  ↓
fe-component（コンポーネントツリーへ）
```

---

## D-IA テンプレート

`docs/fe/D-IA.md` として作成する。

### 1. ページマップ

```markdown
## ページ一覧

| ページID | パス | 画面名 | 認証要否 | 備考 |
|---------|------|--------|---------|------|
| P-001 | / | トップ | 不要 | LP |
| P-002 | /dashboard | ダッシュボード | 必要 | ログイン後リダイレクト先 |
| P-003 | /settings | 設定 | 必要 | |
| P-004 | /settings/profile | プロフィール設定 | 必要 | P-003 の子 |
```

### 2. 階層構造

```markdown
## 情報階層

- ルート
  - トップ (P-001)
  - ダッシュボード (P-002)
  - 設定 (P-003)
    - プロフィール設定 (P-004)
    - 通知設定 (P-005)
  - (認証不要)
    - ログイン
    - パスワードリセット
```

### 3. ナビゲーション設計

```markdown
## ナビゲーション

| ナビ種別 | 表示項目 | 表示条件 |
|---------|---------|---------|
| グローバルナビ（上部） | ロゴ / ダッシュボード / 設定 / ログアウト | ログイン後 |
| グローバルナビ（上部） | ロゴ / ログイン / 新規登録 | 未ログイン |
| サイドナビ | 機能別メニュー | ダッシュボード配下 |
| パンくずリスト | 現在地階層 | 設定配下 |
```

### 4. ラベル定義

```markdown
## ラベル一覧

| ラベルキー | 日本語表示 | 英語キー | 備考 |
|-----------|---------|---------|------|
| nav.dashboard | ダッシュボード | Dashboard | |
| nav.settings | 設定 | Settings | |
| action.save | 保存する | Save | ボタン文言 |
| action.cancel | キャンセル | Cancel | |
```

---

## S 案件向け簡略版（5 行コンテンツマップ）

規模が S（ファイル数 1〜3 / 変更行数 100 以下）の場合、以下の 5 行形式で代替できる。

```markdown
## コンテンツマップ（S案件）
- トップ: / — ヒーロー + CTA + 特徴説明
- 機能一覧: /features — 機能カード一覧
- 料金: /pricing — プラン比較テーブル
- ログイン: /login — メール+パスワード
- ダッシュボード: /dashboard — 認証後メイン画面
```

---

## L5 入場時の情報階層確認

L5 Visual Refinement 入場時、以下を突合する。

```
[ ] D-IA のページ一覧と実装済みルーティングが一致しているか
[ ] ナビゲーションラベルが D-IA 定義と一致しているか
[ ] 階層変更があった場合、D-IA を更新してから L5 に入るか
```

---

## 出力形式

- ファイルパス: `docs/fe/D-IA.md`
- 形式: Markdown テーブル + 箇条書き階層
- 必須セクション: ページ一覧 / 情報階層 / ナビゲーション設計
- fe 駆動時の追加成果物（必須）:
  - `.helix/mock/<feature>/mock.html`（throw-away モック。`src/` import 禁止）
  - `.helix/mock/<feature>/state-events.md`（画面状態・イベント・状態遷移図）
- be 駆動時:
  - `mock.html` / `state-events.md` は optional（作成しない運用可）

---

## チェックリスト

```
[ ] D-IA が docs/fe/ に存在するか
[ ] ページ一覧に全画面が列挙されているか
[ ] 認証要否が全ページに記載されているか
[ ] ナビゲーション種別と表示条件が定義されているか
[ ] ラベルが日本語・英語キーで整理されているか
[ ] S案件の場合、5行コンテンツマップで代替しているか
```
