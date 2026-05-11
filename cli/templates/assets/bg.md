# bg template (HELIX asset CLI)

## 出力仕様
- サイズ: 1920x1080
- 形式: PNG
- 保存先: {{out_path}}

## 共通変数
- style: {{style}}  (default: subtle abstract)
- palette: {{palette}}  (default: dark graphite, mist, and cyan)
- motif: {{motif}}  (user free text)
- text: {{text}}  (overlay text)

## 生成プロンプト

Generate a 1920x1080 background image with:
- Style: {{style}}, tech-forward, professional
- Color palette: {{palette}}
- Motif: {{motif}}
- Text overlay: "{{text}}" (in a clean modern font)
- Background: dark gradient unless {{palette}} specifies otherwise
- Composition: edge-to-edge pattern with a subtle motif and tileable continuity

Create a seamless background texture suitable for presentation canvases, landing pages, and full-screen overlays.
The pattern should feel quiet, refined, and low contrast, with enough structure to suggest depth while remaining unobtrusive.
Use abstract geometry, faint noise, and repeated visual rhythm that can tile without obvious seams.

Keep the design atmospheric rather than illustrative.
The texture should support content placed above it without stealing attention.
If a motif is used, repeat it sparingly and with soft variation so the surface feels organic.

Avoid sharp focal points, typography-heavy elements, and any composition that cannot repeat cleanly.
The final result should work as a versatile branded background across large screens.

Save the result to {{out_path}}.
