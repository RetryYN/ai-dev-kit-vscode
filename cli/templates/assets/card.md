# card template (HELIX asset CLI)

## 出力仕様
- サイズ: 800x600
- 形式: PNG
- 保存先: {{out_path}}

## 共通変数
- style: {{style}}  (default: clean modern)
- palette: {{palette}}  (default: graphite, slate, and cyan)
- motif: {{motif}}  (user free text)
- text: {{text}}  (overlay text)

## 生成プロンプト

Generate a 800x600 card image with:
- Style: {{style}}, tech-forward, professional
- Color palette: {{palette}}
- Motif: {{motif}}
- Text overlay: "{{text}}" (in a clean modern font)
- Background: dark gradient unless {{palette}} specifies otherwise
- Composition: square-ish layout, centered subject with light texture and subtle framing elements

Create a service or feature card image that feels clean, modern, and usable in a product catalog.
The center subject should be the primary focus, supported by soft contextual texture and restrained highlights.
Keep the layout balanced so that the image can be used as a standalone card or paired with copy.

Use polished surface treatment, a measured amount of depth, and calm geometric structure.
The image should imply reliability and product quality without becoming sterile.
If a motif is used, integrate it as a subtle accent rather than a dominant object.

Avoid busy backgrounds, extreme perspective, and any composition that competes with card titles.
The result should be versatile across service cards, feature promos, and dashboard teasers.

Save the result to {{out_path}}.
