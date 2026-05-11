# thumb template (HELIX asset CLI)

## 出力仕様
- サイズ: 1200x630
- 形式: PNG
- 保存先: {{out_path}}

## 共通変数
- style: {{style}}  (default: editorial)
- palette: {{palette}}  (default: charcoal, white, and electric cyan)
- motif: {{motif}}  (user free text)
- text: {{text}}  (overlay text)

## 生成プロンプト

Generate a 1200x630 thumbnail image with:
- Style: {{style}}, tech-forward, professional
- Color palette: {{palette}}
- Motif: {{motif}}
- Text overlay: "{{text}}" (in a clean modern font)
- Background: dark gradient unless {{palette}} specifies otherwise
- Composition: OG card layout with a prominent title area and clear social-share framing

Design the thumbnail like a strong editorial social preview.
The title region should be visually dominant, with enough contrast and structure to support article or blog promotion.
Use a layout that can accommodate large headline copy and a supporting motif without losing balance.

Prefer a magazine-like hierarchy, crisp spacing, and a composed visual rhythm.
The image should feel click-worthy but not sensationalist.
Keep the design professional, current, and legible when scaled down in feed previews.

Use restrained motion cues, subtle depth, and a focused focal point.
Avoid crowded UI, tiny details, and low-contrast decorative effects.

Save the result to {{out_path}}.
