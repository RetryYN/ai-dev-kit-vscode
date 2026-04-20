# D-ARCH: アーキテクチャ設計 — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**Layer**: L2 設計

---

## 0. 概要

helix-budget + auto-thinking Phase B は HELIX CLI に「消費トラッキング + タスク難度自動判定 + モデル降格」を追加するモジュール群。新規 CLI (`helix budget`) + 既存 CLI (helix-codex/helix-skill) への非破壊拡張で構成される。

## 0.1 コンテキスト

前提条件:
- HELIX CLI v5 (37コマンド、helix.db v5、453 テスト)
- Phase A (サブエージェント `effort` frontmatter) 既完了
- Claude Max + ChatGPT Max プラン運用前提
- `~/.claude/projects/*.jsonl` / `~/.codex/state.db` 読み取り権限あり

関連資料:
- L1 要件: `../D-REQ-F/requirements.md` / `../D-REQ-NF/nfr.md` / `../D-ACC/acceptance.md`
- ADR: `../D-ADR/adr.md` (ADR-001〜006)
- 先行調査: `.helix/research/helix-budget-prior-art.md` / `codex-usage-research.md`

## 0.2 責務境界

| モジュール | 責務 | 責務外 |
|----------|------|-------|
| `cli/helix-budget` | CLI dispatcher | ロジックは持たない (lib に委譲) |
| `cli/lib/budget.py` | 消費取得 + forecast | 難度判定 / 降格 |
| `cli/lib/effort_classifier.py` | 難度判定 (5軸 + LLM) | 残量判定 |
| `cli/lib/model_fallback.py` | 降格ルール適用 | 残量取得 / 難度判定 |
| `cli/lib/budget_cli.py` | サブコマンドエントリ | core ロジック |
| `helix-codex/helix-skill` | `--auto-thinking` フラグ受付 | 判定自体 |

## 0.3 運用方針

- **非破壊**: 既存 CLI は `--auto-thinking` を付けなければ従来通り動作
- **キャッシュ優先**: 1h TTL でトークン/API コスト最小化
- **フェイルセーフ**: 残量取得失敗時は既定挙動で続行 (警告のみ)
- **プライバシー**: 認証情報は絶対ログ・LLM 送信に含めない (NFR-S1/S4)
- **学習**: `observed-limits.json` で実測ベース上限を自動更新 (2-3 週で精度向上)

---

## 1. モジュール分割図

```
cli/
├── helix-budget                  (Bash dispatcher, ~120 lines)
│   ├── status / forecast / classify / simulate / cache
│   └── python3 cli/lib/budget_cli.py $subcmd
├── helix-budget-hook             (SessionStart hook entry, ~40 lines)
├── helix-codex                   (既存 + --auto-thinking 分岐追加)
├── helix-skill                   (既存 + --auto-thinking 分岐追加)
│
├── lib/
│   ├── budget.py                 (~200 lines) — 消費取得メイン
│   │   ├── ClaudeBudget         (ccusage / JSONL fallback)
│   │   ├── CodexBudget          (state.db 直接クエリ)
│   │   ├── BudgetCache          (.helix/budget/cache/*.json)
│   │   └── ForecastEngine       (線形外挿 + cc-statistics 発想)
│   │
│   ├── effort_classifier.py     (~150 lines) — 難度判定
│   │   ├── score_task()         5 軸スコアリング
│   │   ├── call_classifier()    gpt-5.4-mini subprocess
│   │   ├── map_to_effort()      スコア → level 変換
│   │   └── cache (SHA256 task_hash キー, 1h TTL)
│   │
│   ├── model_fallback.py        (~100 lines) — 降格エンジン
│   │   ├── load_rules()         model-fallback.yaml 読込
│   │   ├── suggest_model()      残量 + effort → 推奨モデル
│   │   └── apply_rule()         降格適用
│   │
│   ├── budget_cli.py            (~150 lines) — CLI エントリ
│   │   └── status / forecast / classify / simulate サブコマンド
│   │
│   └── (既存) skill_dispatcher.py — budget check 追加 hook point
│
├── config/
│   ├── model-fallback.yaml      (新規)
│   └── plan-limits.yaml         (新規)
│
├── roles/
│   └── effort-classifier.conf   (新規 — gpt-5.4-mini ロール定義)
│
└── templates/
    └── effort-classify-prompt.md (新規 — LLM プロンプト)
```

---

## 2. データフロー

### 2.1 session-start フロー

```
[Claude Code 起動]
    ↓
SessionStart hook (settings.json)
    ↓
helix-budget-hook session-start
    ↓
python3 budget_cli.py status --brief
    ↓
  キャッシュ hit? → JSON 読み込み
       ↓ NO
  ClaudeBudget.get() + CodexBudget.get() 並列
       ↓
  ForecastEngine.predict()
       ↓
  キャッシュ保存 (1h TTL)
    ↓
stdout に 1 行サマリ: "[HELIX] Budget: Claude 58%, Codex 72% (warn: Spark<20%)"
```

### 2.2 auto-thinking フロー

```
[User] helix-codex --role se --task "..." --auto-thinking
    ↓
helix-codex (bash)
    ↓ [classifier 呼び出し]
python3 cli/lib/effort_classifier.py classify --task "..." --role se --size <auto>
    ↓
  score_task()  — 5 軸ルール + heuristic
    ↓
  call_classifier() — gpt-5.4-mini 呼び出し (task text + role + size)
    ↓ (response: {"effort": "medium", "reason": "..."})
  cache 保存
    ↓ [返す: effort=medium]
    ↓
helix-codex
    ↓ [budget 確認]
python3 cli/lib/budget.py check --model gpt-5.3-codex
    ↓ (残量 OK / NG)
    ↓
  NG なら: model_fallback.suggest_model()
    ↓ (suggest: gpt-5.4-mini)
    ↓
  ユーザー確認 (stdin 閉じなら --yes で続行)
    ↓
codex exec -m <final-model> --thinking <final-effort> "<task>"
    ↓
[実行]
    ↓
skill_usage テーブルに記録
  (task_hash, estimated_effort, actual_thinking, timeout, tokens_used)
```

### 2.3 学習フロー (枯渇検知)

```
budget status 取得
    ↓
 weekly_used_pct >= 95% ?
    ↓ YES
observed-limits.json に追記
  {"date": "2026-04-21", "model": "spark", "observed_week_tokens": 12M}
    ↓
次回プラン上限推定に反映 (実測ベース)
```

---

## 3. 依存関係

### 3.1 外部依存

| 依存先 | 種別 | 取得方法 | 必須/オプション |
|-------|-----|---------|---------------|
| `ccusage` npm | CLI subprocess | `npm install -g ccusage` | optional (フォールバックあり) |
| `~/.claude/projects/*.jsonl` | 読み込み | 直接 parse | 必須 |
| `~/.codex/state.db` | SQLite | `sqlite3` モジュール | 必須 (存在しない環境は警告のみ) |
| `codex-ratelimit` | 参照のみ | state.db クエリパターン移植 | 参考 |
| gpt-5.4-mini | Codex CLI | `codex exec -m gpt-5.4-mini` | auto-thinking 時必須 |

### 3.2 HELIX 内部依存

| モジュール | 用途 |
|-----------|------|
| `cli/lib/skill_dispatcher.py` | 実行前後の hook point (budget check, skill_usage 記録) |
| `helix.db` v6 | `skill_usage` 拡張 (effort_used / timeout_occurred / tokens_used) |
| `cli/helix-init` | hook 登録 + config 初期化 |
| `cli/helix-log` | `report budget` サブコマンド追加 |

---

## 4. DB スキーマ拡張 (helix.db v6)

```sql
-- 既存 skill_usage に ALTER TABLE で追加
ALTER TABLE skill_usage ADD COLUMN effort_estimated TEXT;
ALTER TABLE skill_usage ADD COLUMN effort_actual TEXT;
ALTER TABLE skill_usage ADD COLUMN timeout_occurred INTEGER DEFAULT 0;
ALTER TABLE skill_usage ADD COLUMN tokens_used INTEGER;
ALTER TABLE skill_usage ADD COLUMN model_used TEXT;
ALTER TABLE skill_usage ADD COLUMN fallback_applied INTEGER DEFAULT 0;

-- 新規 budget_events テーブル
CREATE TABLE IF NOT EXISTS budget_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  occurred_at TEXT NOT NULL,
  event_type TEXT NOT NULL,  -- 'exhaustion' / 'fallback' / 'warning' / 'forecast_miss'
  model TEXT,
  pct_used REAL,
  details_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_budget_events_at ON budget_events(occurred_at);

-- version bump
UPDATE schema_version SET version = 6 WHERE id = 1;
```

マイグレーションは `cli/lib/db_migrate.py` に追加 (既存 v5 → v6)。

---

## 5. キャッシュ戦略

| キャッシュ | TTL | Key | 用途 |
|----------|-----|-----|------|
| `budget/cache/status.json` | 1h | — | `budget status` 全体 |
| `budget/cache/classify/<sha256>.json` | 1h | task_hash | effort_classifier 結果 |
| `budget/cache/forecast.json` | 6h | — | forecast (履歴集計が重い) |

`--no-cache` で全強制再取得。キャッシュ miss 時は並列取得で応答短縮。

---

## 6. 並列性 / 非同期性

- Claude / Codex 消費取得は **並列** (asyncio or subprocess)
- effort_classifier はブロッキング (1 回あたり 2-3 秒、キャッシュで回避)
- Hook は最大 1.5 秒でタイムアウト (NFR-P3 遵守)

---

## 7. セキュリティ境界

```
┌────────────────────────────────┐
│ helix-budget (ユーザー環境)     │
│  ├── ~/.claude/projects/ (ro)  │  ← read-only parse
│  ├── ~/.codex/state.db (ro)    │  ← read-only query
│  └── ~/.codex/auth.json (NEVER) │  ← 絶対読まない
└────────────────────────────────┘
              ↓ task text のみ送信
┌────────────────────────────────┐
│ gpt-5.4-mini (Codex CLI)       │
│  (認証情報は送信しない)          │
└────────────────────────────────┘
```

認証情報が絶対に外部送信に含まれないよう `cli/lib/effort_classifier.py` の payload サニタイザでパス情報を除外する。

---

## 8. 拡張ポイント

- プラン追加: `plan-limits.yaml` に行追加のみ
- モデル追加: `model-fallback.yaml` に行追加のみ
- 新難度軸: `effort_classifier.py` の `WEIGHTS` dict に追加
- 別エージェント系統統合 (Aider, Cline 等): 新規 `lib/aider_budget.py` 等を追加し `budget_cli` の dispatch に登録
