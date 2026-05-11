# logo template (HELIX asset CLI)

## 出力仕様
- サイズ: 512x512
- 形式: PNG
- 保存先: {{out_path}}

## 共通変数
- style: {{style}}  (default: bold minimal)
- palette: {{palette}}  (default: monochrome with cyan accent)
- motif: {{motif}}  (user free text)
- text: {{text}}  (overlay text)

## 生成プロンプト

Generate a 512x512 logo image with:
- Style: {{style}}, tech-forward, professional
- Color palette: {{palette}}
- Motif: {{motif}}
- Text overlay: "{{text}}" (in a clean modern font)
- Background: dark gradient unless {{palette}} specifies otherwise
- Composition: centered square layout, symbol in the middle with an optional text mark

Design a strong brand mark suitable for app icon or identity system use.
The symbol should be immediately recognizable at small sizes and should survive monochrome usage.
Keep the silhouette bold, simple, and balanced with clear geometry and minimal ornament.
If text is included, keep it compact and secondary to the symbol.

Use a centered composition with ample breathing room around the mark.
Prioritize clarity, stroke consistency, and optical balance over detail density.
The result should feel modern, authoritative, and easy to reproduce across product surfaces.

Avoid gradients that reduce icon legibility, noisy textures, and overly complex emblem shapes.
Make the logo feel engineered, not decorative.

Save the result to {{out_path}}.
