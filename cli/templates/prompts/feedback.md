HELIX gate 通過後の 5 軸 Lv1-5 フィードバック生成タスク。

対象:
- PLAN: {plan_id}
- gate: {gate_name}  (G2/G3/G4/G5/G6/G7/L8 のいずれか)
- 直近の作業: {recent_work_summary}
- 検出済み findings: {findings_summary}

評価観点 (5 軸):
1. density (情報の密度): 必要事項の網羅性、欠落の有無
2. depth (深さ): 各論点の掘り下げ度、表層的でないか
3. breadth (広さ): 関連領域への目配り、考慮漏れの有無
4. accuracy (実装の正確性): 仕様・契約・データ型の正確性
5. maintainability (保守性): 可読性、変更容易性、依存最小化

各軸を以下 5 段階で評価:
- Lv1 (poor): 観点に対して欠落・不正確
- Lv2 (insufficient): 部分的、補強必要
- Lv3 (acceptable): 標準的、可
- Lv4 (good): 充実、模範的
- Lv5 (excellent): 卓越、横展開すべき

【出力形式】
JSON のみ返す:
{
  "feedback_message": "<ユーザー向けプロンプト形式の教訓 (3-7 行、改善方向の強調、Lv4-5 を取りに行く動機付け)>",
  "scores": [
    {"dimension": "density", "level": 1-5, "comment": "<簡潔な根拠>"},
    {"dimension": "depth", "level": 1-5, "comment": "<簡潔な根拠>"},
    {"dimension": "breadth", "level": 1-5, "comment": "<簡潔な根拠>"},
    {"dimension": "accuracy", "level": 1-5, "comment": "<簡潔な根拠>"},
    {"dimension": "maintainability", "level": 1-5, "comment": "<簡潔な根拠>"}
  ]
}

【重要】feedback_message は Claude/Opus が読んでモチベーションを上げる方向で書く (萎縮しない言い回し、Lv4-5 達成の具体方向を提示)。
