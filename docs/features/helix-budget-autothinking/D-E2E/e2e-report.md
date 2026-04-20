# D-E2E: E2E 検証レポート — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**Date**: 2026-04-21
**実行環境**: WSL2 Ubuntu 22.04 / Python 3.11 / SQLite 3.37

---

## 1. シナリオ

### S-01: budget status コールドスタート
`helix budget status --no-cache` を実行し Claude/Codex 両側の消費と推奨が表示される。

### S-02: budget classify 軽微タスク
`helix budget classify --task 'typo 修正' --size S --files 1` が effort=low or medium を返す。

### S-03: budget classify 設計タスク
`helix budget classify --task '新規 API 設計 + DB migration 横断' --role tl --size L --files 8` が effort=high or xhigh を返す。

### S-04: budget simulate 統合判定
`helix budget simulate --task 'API ハンドラ 3 本実装' --role se --size M` が推奨モデル + thinking を出力。

### S-05: キャッシュ
同 status を連続 2 回実行して 2 回目にキャッシュヒットする。

### S-06: DB マイグレーション
新規 `.helix/helix.db` を init し v7 (最新) に到達。skill_usage 新カラム 6 件 + budget_events テーブルが存在。

### S-07: 降格判定 (Spark 枯渇 + M タスク)
mock 残量 95% で `suggest_model("gpt-5.3-codex-spark", ...)` が fallback_applied=True を返す。

### S-08: 降格判定 (5.4 保持)
mock 残量 98% で `suggest_model("gpt-5.4", ...)` が fallback_applied=False を返す。

---

## 2. 期待結果 vs 実測結果

| シナリオ | 期待 | 実測 | 判定 |
|---------|------|------|------|
| S-01 | exit 0 + Claude/Codex 表示 | `Claude (max): 100% used ...  Codex (max): 0% (5h) / 0% (weekly)  source: jsonl-fallback/unavailable` | ✅ PASS |
| S-02 | effort in {low, medium} | `effort: medium (score=4)` | ✅ PASS |
| S-03 | effort in {high, xhigh} | `effort: high (score=10)` | ✅ PASS |
| S-04 | 推奨モデル + thinking 表示 | `推奨モデル: gpt-5.3-codex (thinking=medium)` | ✅ PASS |
| S-05 | 2 回目 cached=true | helix test に含まれる動作 | ✅ PASS (bats) |
| S-06 | version=7 + 6 カラム + budget_events | `v7 migration skill_usage new columns` / `v7 migration budget_events table` 両 PASS | ✅ PASS |
| S-07 | fallback_applied=True | `model_fallback spark exhaustion` PASS | ✅ PASS |
| S-08 | fallback_applied=False | `model_fallback 5.4 hold` PASS | ✅ PASS |

**合格率**: 8/8 (100%)

---

## 3. クリティカルパス観測性

### 主要ログ出力

| シナリオ | 観測ポイント | 出力内容 |
|---------|------------|---------|
| status 正常 | stdout | 消費%  + source |
| status ccusage 未インストール | recommendations | `[info] ccusage 未インストール...` |
| status state.db 未存在 | recommendations | `[info] ~/.codex/state.db 未存在` |
| classify 軽微 | stdout | effort + score + breakdown |
| classify 重い | stderr | `[warn] 分割推奨 (xhigh + S)` (該当時) |
| simulate fallback | stdout | `[fallback] <from> -> <to>` |
| migration v7 | stdout (init_db) | `DB initialized: <path>` |

### 失敗時観測性

- budget 取得失敗 → `warning` フィールドに `type(e).__name__` (例: `ValueError`) を出すがスタックトレースは出さない
- classifier LLM 呼び出し失敗 (将来拡張) → ルールベース fallback 発火、warning 記録
- migration 失敗 → transaction rollback + exception raise (呼び出し側でハンドル)

---

## 4. 既存機能との回帰

- `helix test`: 467/467 PASS (既存 453 + 新規 14)
- `helix-codex --role pg --task 'x' --dry-run`: 既存挙動維持
- `helix gate G2/G3/G4`: 全 PASS (本 feature 対応後)

---

## 5. 未検証項目 (L8 以降)

- 実運用 1 週間での枠切れ事故ゼロ検証 (AC-U2)
- observed-limits.json の実測学習精度 (2-3 週で収束想定)
- gpt-5.4-mini LLM 呼び出しの実精度 (実装は次期スプリント)

---

## 6. 結論

**E2E 合格**。Minimum Viable 範囲のクリティカルパス 8 シナリオすべて PASS。
次期スプリントで LLM 呼び出し + hook 統合 + report サブコマンドを追加予定。
