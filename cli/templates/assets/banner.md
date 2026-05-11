# banner template (HELIX asset CLI)

## 出力仕様
- サイズ: 1200x400
- 形式: PNG
- 保存先: {{out_path}}

## 共通変数
- style: {{style}}  (default: minimal tech)
- palette: {{palette}}  (default: deep slate, cyan, and electric blue)
- motif: {{motif}}  (user free text)
- text: {{text}}  (overlay text)

## 生成プロンプト

Generate a 1200x400 banner image with:
- Style: {{style}}, tech-forward, professional
- Color palette: {{palette}}
- Motif: {{motif}}
- Text overlay: "{{text}}" (in a clean modern font)
- Background: dark gradient unless {{palette}} suggests a brighter scheme
- Composition: wide horizontal layout, text and logo area on the left, motif graphic on the right, strong negative space for readability

Create a polished hero-style banner suitable for GitHub README, OG preview, or a hero card.
Use layered depth, crisp contrast, and restrained detail so the overlay text remains legible.
Prefer a balanced editorial-tech look with subtle lighting, soft glow accents, and clean geometry.
Avoid clutter, busy patterns, and any handwritten or decorative type.

The left side should feel like a brand anchor.
The right side should contain a visually interesting but non-distracting motif that reinforces the theme.
Keep the overall image premium, minimal, and easy to crop for repository headers.

Generate a composition that feels intentional at thumbnail size and still reads well at full width.
Use sharp edges, soft shadows, and modern interface-inspired visual cues.
Do not place important details too close to the edges.

Save the result to {{out_path}}.
