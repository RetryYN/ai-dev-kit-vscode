# hero template (HELIX asset CLI)

## 出力仕様
- サイズ: 1920x1080
- 形式: PNG
- 保存先: {{out_path}}

## 共通変数
- style: {{style}}  (default: tech cinematic)
- palette: {{palette}}  (default: midnight blue, violet, and cyan)
- motif: {{motif}}  (user free text)
- text: {{text}}  (overlay text)

## 生成プロンプト

Generate a 1920x1080 hero image with:
- Style: {{style}}, tech-forward, professional
- Color palette: {{palette}}
- Motif: {{motif}}
- Text overlay: "{{text}}" (in a clean modern font)
- Background: dark gradient unless {{palette}} specifies otherwise
- Composition: cinematic horizontal scene, full-bleed background with a foreground subject and strong depth separation

Create a large-format landing page hero with a premium, cinematic technology mood.
The foreground subject should be bold and readable, while the background should provide atmosphere without overpowering the focal point.
Use dramatic lighting, layered haze, and subtle motion cues to suggest scale and momentum.

Keep the composition suitable for LP hero sections where headline content may be placed later.
Leave a clear visual lane for future UI overlays while preserving impact.
The image should feel modern, ambitious, and launch-ready.

Lean into premium product storytelling: clean surfaces, engineered geometry, and controlled highlights.
Avoid fantasy elements, cluttered UI fragments, and overly literal stock-photo aesthetics.
The final image should work as a banner across wide screens and still hold up after crop adjustments.

Save the result to {{out_path}}.
