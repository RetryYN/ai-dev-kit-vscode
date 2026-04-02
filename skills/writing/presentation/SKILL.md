---
name: presentation
description: Marp CLIによるMarkdownからPPTX/PDFスライド自動生成で、レトロ・レビュー・報告のスライド作成を効率化
metadata:
  helix_layer: L8
  triggers:
    - ミニレトロ(G2/G4)時
    - L8受入報告時
    - 設計レビュー発表時
  verification:
    - "marp --pptx 生成成功"
    - "スライド数が内容に対して適切"
compatibility:
  claude: true
  codex: true
---

# スライド自動生成スキル（Marp CLI）

## 適用タイミング

このスキルは以下の場合に読み込む：
- ミニレトロ（G2/G4）時
- L8受入報告時
- 設計レビュー発表時

---

## 1. Marp CLI セットアップ手順

```bash
npm install -D @marp-team/marp-cli
```

初期確認：

```bash
npx marp --version
mkdir -p docs/slides/src docs/slides/dist
```

最小生成：

```bash
npx marp docs/slides/src/sample.md --pptx --pdf --html --output docs/slides/dist
```

---

## 2. スライドテンプレート

### 2.1 レトロ用（G2/G4）

```markdown
---
marp: true
theme: default
paginate: true
---

# ミニレトロ
- 対象: G2/G4
- 期間: YYYY-MM-DD

---

## うまくいったこと
- 事実ベースで3件

---

## 課題
- 事実 + 影響

---

## 次アクション
- 誰が / いつまでに / 何を
```

### 2.2 報告用（L8受入）

```markdown
# L8 受入報告

## 要件との突合
- 要件IDごとの達成状況

## 検証結果
- テスト結果
- 残課題

## 判定
- 受入可否
- 次ステップ
```

### 2.3 レビュー用（設計レビュー）

```markdown
# 設計レビュー

## 背景
## 提案内容
## 代替案比較
## リスクと対策
## 意思決定事項
```

---

## 3. Marp Markdown 記法ガイド

### ページ区切り

- `---` で改ページする
- 1スライド1メッセージに限定する

### レイアウト

```markdown
<!-- _class: lead -->
# 表紙

<!-- _footer: "Project X" -->
## フッター付きスライド
```

### テーマ指定

```markdown
---
marp: true
theme: default
paginate: true
size: 16:9
---
```

運用ルール：
- 見出しは名詞止めで短くする
- 箇条書きは最大5項目まで
- 表は詳細値より結論優先で置く

---

## 4. HELIX ゲート/レトロとの連携

### G2/G4 通過後

1. ゲート結果を `docs/slides/src/retro-g2.md` または `retro-g4.md` に反映
2. `npx marp ... --pptx --pdf` で配布物を生成
3. 生成ファイルをゲート証跡に添付

例：

```bash
npx marp docs/slides/src/retro-g4.md --pptx -o docs/slides/dist/retro-g4.pptx
npx marp docs/slides/src/retro-g4.md --pdf  -o docs/slides/dist/retro-g4.pdf
```

### L8 受入報告時

- `acceptance-report.md` から報告用スライドを自動生成
- 要件ID・検証結果・残課題を最終ページに集約する

---

## 5. 出力形式の使い分け（PPTX/PDF/HTML）

| 形式 | 用途 | 長所 | 注意点 |
|------|------|------|--------|
| PPTX | 社内会議、編集前提配布 | 後編集しやすい | フォント差分で崩れる場合がある |
| PDF | 正式記録、レビュー固定版 | 表示が安定 | アニメーション不可 |
| HTML | Web共有、即時確認 | ブラウザで閲覧可能 | 配布先環境の依存に注意 |

推奨運用：
- レビュー前: HTML
- 会議当日: PPTX
- 証跡保管: PDF

---

## 6. 自動生成ジョブ例

```bash
# 例: package.json scripts
marp:retro:g4="marp docs/slides/src/retro-g4.md --pptx --pdf --output docs/slides/dist"
marp:l8="marp docs/slides/src/l8-report.md --pptx --pdf --output docs/slides/dist"
```

CIでの最小チェック：
- Markdownの存在
- `--pptx` 生成成功
- 出力ファイルサイズが0でない

---

## 7. 完了判定

- `marp --pptx` で生成成功
- スライド数が内容に対して過不足ない（目安: 1トピック1-2枚）
- G2/G4/L8の証跡と出力物が対応している
