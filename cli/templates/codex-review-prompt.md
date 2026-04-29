HELIX レビュー prompt template (各 role 共通)。

【役割文脈】
本レビューは role={role}、target={target_path}、phase={current_phase} を対象とする。

【5 軸 Lv1-5 評価 (HELIX philosophy: 速度 -> 正確・精度志向)】

評価軸:
1. density (情報の密度): 必要事項の網羅性、欠落の有無
2. depth (深さ): 各論点の掘り下げ度、表層的でないか
3. breadth (広さ): 関連領域への目配り、考慮漏れの有無
4. accuracy (実装の正確性): 仕様・契約・データ型の正確性
5. maintainability (保守性): 可読性、変更容易性、依存最小化

各軸 Lv1-5 で評価:
- Lv1 (poor) / Lv2 (insufficient) / Lv3 (acceptable) / Lv4 (good) / Lv5 (excellent)

レビュー finding は severity (critical/high/medium/low) とは別に、関連する 5 軸 Lv1-5 を併記:
```json
{
  "severity": "...",
  "title": "...",
  "body": "...",
  "dimension_scores": [
    {"dimension": "accuracy", "level": 2, "comment": "型不整合 1 件"}
  ]
}
```

【summary には全体評価を 5 軸 x Lv1-5 で要約】
レビュー JSON を返す場合は、`overall_scores` に 5 軸すべてを含めること。
通常の実装サマリだけを求められた場合も、この 5 軸を自己確認観点として使うこと。

```json
{
  "verdict": "approve|needs-attention",
  "summary": "...",
  "overall_scores": [
    {"dimension": "density", "level": 3, "comment": "..."},
    {"dimension": "depth", "level": 3, "comment": "..."},
    {"dimension": "breadth", "level": 3, "comment": "..."},
    {"dimension": "accuracy", "level": 3, "comment": "..."},
    {"dimension": "maintainability", "level": 3, "comment": "..."}
  ],
  "findings": [],
  "next_steps": ["..."]
}
```
