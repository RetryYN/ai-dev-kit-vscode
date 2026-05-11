# icon template (HELIX asset CLI)

## 出力仕様
- サイズ: 256x256
- 形式: PNG
- 保存先: {{out_path}}

## 共通変数
- style: {{style}}  (default: flat minimal)
- palette: {{palette}}  (default: black, white, and cyan)
- motif: {{motif}}  (user free text)
- text: {{text}}  (overlay text)

## 生成プロンプト

Generate a 256x256 icon image with:
- Style: {{style}}, tech-forward, professional
- Color palette: {{palette}}
- Motif: {{motif}}
- Text overlay: "{{text}}" (in a clean modern font)
- Background: dark gradient unless {{palette}} specifies otherwise
- Composition: tight square layout with a simple recognizable symbol

Create a compact icon optimized for favicon and UI icon usage.
The symbol should be instantly readable at very small sizes and should avoid thin details that collapse in raster rendering.
Use flat shapes, strong silhouettes, and very limited ornament.

Keep the composition centered and optical, with generous padding around the glyph.
The visual should feel crisp, minimal, and engineered for interface surfaces.
If text is included, it must remain secondary and extremely short.

Avoid complex scenes, multiple objects, and realistic textures that reduce clarity.
The final mark should work as a durable product icon across light and dark contexts.

Save the result to {{out_path}}.
