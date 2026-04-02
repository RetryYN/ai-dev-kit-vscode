---
name: pptx
description: python-pptxによるテンプレートベースPPTX自動生成で定型報告書・提案書・進捗報告のスライドをデータ駆動で作成
metadata:
  helix_layer: L8
  triggers:
    - UAT報告書作成時
    - 社内報告・提案書作成時
    - 定期進捗報告時
  verification:
    - "python-pptx によるPPTX生成成功"
    - "テンプレートの全プレースホルダが置換済み"
compatibility:
  claude: true
  codex: true
---

# PPTXテンプレート生成スキル（python-pptx）

## 適用タイミング

このスキルは以下の場合に読み込む：
- UAT報告書作成時
- 社内報告・提案書作成時
- 定期進捗報告時

---

## 1. python-pptx セットアップ手順

```bash
python -m venv .venv
source .venv/bin/activate
pip install python-pptx pyyaml
```

最小確認：

```bash
python - <<'PY'
from pptx import Presentation
Presentation()
print('python-pptx ok')
PY
```

---

## 2. テンプレートPPTXの作り方

テンプレート作成ルール：
1. PowerPointでレイアウト（表紙、本文、表、チャート）を先に作る
2. 置換対象を `{{title}}` のようなプレースホルダで記述する
3. 1スライド1責務にし、再利用しやすい形で保存する

推奨ファイル配置：
- `docs/slides/template/report-template.pptx`
- `docs/slides/data/report.yaml`
- `scripts/generate_pptx.py`

---

## 3. データ駆動スライド生成パターン（JSON/YAML → PPTX）

### YAML例

```yaml
title: 週次進捗報告
subtitle: 2026-04-02
summary:
  - 完了: API認可改修
  - 進行中: E2Eテスト拡充
risks:
  - 本番データ移行の検証待ち
```

### 置換スクリプト例

```python
from pathlib import Path
import yaml
from pptx import Presentation

TEMPLATE = Path("docs/slides/template/report-template.pptx")
DATA = Path("docs/slides/data/report.yaml")
OUTPUT = Path("docs/slides/dist/report.pptx")

def replace_text(shape, values):
    if not shape.has_text_frame:
        return
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            for key, value in values.items():
                run.text = run.text.replace(f"{{{{{key}}}}}", str(value))

def main():
    prs = Presentation(TEMPLATE)
    values = yaml.safe_load(DATA.read_text(encoding="utf-8"))

    for slide in prs.slides:
        for shape in slide.shapes:
            replace_text(shape, values)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUTPUT)

if __name__ == "__main__":
    main()
```

---

## 4. チャート・表の自動挿入

### チャート挿入例

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

chart_data = CategoryChartData()
chart_data.categories = ["Plan", "Actual"]
chart_data.add_series("進捗", (70, 55))

slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(1), Inches(1.5), Inches(8), Inches(4),
    chart_data,
)
```

### 表挿入例

```python
rows, cols = 3, 3
table = slide.shapes.add_table(rows, cols, Inches(1), Inches(1), Inches(8), Inches(2)).table
table.cell(0, 0).text = "項目"
table.cell(0, 1).text = "計画"
table.cell(0, 2).text = "実績"
```

運用ルール：
- 数値はスクリプト側で整形（桁区切り・単位）してから埋め込む
- 表の列構成をテンプレートで固定し、行データのみ差し替える

---

## 5. プレースホルダ置換検証

生成後に次を確認する。

```bash
# 置換漏れチェック（文字列検索）
unzip -p docs/slides/dist/report.pptx ppt/slides/slide*.xml | rg "\{\{.*\}\}"
```

判定基準：
- `{{...}}` が0件
- 文字化けなし
- 必須スライド（表紙/要約/リスク）が存在

---

## 6. HELIX L8 報告との連携

1. L8受入前にUAT結果を YAML/JSON へ整形
2. `python scripts/generate_pptx.py` で報告書を生成
3. 生成PPTXを受入資料として添付
4. 要件ID・判定・残課題を最終スライドに明示

最小実行：

```bash
python scripts/generate_pptx.py
```

---

## 7. 完了判定

- python-pptx によるPPTX生成成功
- テンプレートの全プレースホルダが置換済み
- L8報告に必要な項目（要件達成状況/検証結果/残課題）が反映されている
