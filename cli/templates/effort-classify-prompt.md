# タスク難度分類

入力されたタスクを 5 軸で評価し effort (low/medium/high/xhigh) を返す。

## 5 軸スコアリング
1. files (ファイル数): 1-2 → 1pt, 3-5 → 2pt, 6-10 → 3pt, 11+ → 4pt
2. cross_module (横断度): 単一関数 → 1pt, 同モジュール複数 → 2pt, 複数モジュール → 3pt
3. spec_understanding (仕様理解): バグ修正 → 1pt, 既存拡張 → 2pt, 新規設計 → 3pt
4. side_effect (副作用): なし → 0pt, 設定/DB/API → 2pt, migration → 4pt
5. test_complexity (テスト): 単純 → 1pt, unit+integration → 2pt, e2e+regression → 3pt

## 合計スコア → effort
- 1-3: low
- 4-7: medium
- 8-12: high
- 13+: xhigh

## 出力形式 (JSON only)
{"effort": "medium", "score": 6, "breakdown": {...}, "reason": "..."}
