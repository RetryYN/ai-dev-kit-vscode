# D-API: CLI API 設計 — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**Layer**: L2 設計

---

## 1. 新規 CLI: `helix budget`

サブコマンド 4 種 + 1 ヘルパー。

### 1.1 `helix budget status`

**用途**: Claude / Codex 両側の消費 % + 枯渇予測を表示。

```
$ helix budget status
Claude (Max):   42% used / 58% remaining  (weekly reset: 2026-04-28 00:00)
Codex (Max):    35% (5h) / 28% (weekly)   (5h reset: 14:30, weekly: 04-28)
枯渇予測:
  Claude: 残 3.2 日 (現ペース継続時)
  Codex:  残 5.5 日 (5.3 優先、Spark 2 日)

推奨: Spark 残 < 20% — 軽量タスクは 5.4-mini に切り替え推奨
```

**フラグ**:
- `--json`: JSON 形式出力 (自動化向け)
- `--breakdown`: モデル別消費内訳 (5.3/5.4/Spark/5.4-mini)
- `--no-cache`: キャッシュ無効化 (強制再取得)

**JSON スキーマ**:
```json
{
  "claude": {
    "plan": "max",
    "weekly_used_pct": 42,
    "weekly_remaining_pct": 58,
    "weekly_reset_at": "2026-04-28T00:00:00Z",
    "forecast_exhaustion_days": 3.2,
    "source": "ccusage"
  },
  "codex": {
    "plan": "max",
    "five_hour_used_pct": 35,
    "weekly_used_pct": 28,
    "five_hour_reset_at": "2026-04-21T14:30:00Z",
    "weekly_reset_at": "2026-04-28T00:00:00Z",
    "forecast_exhaustion_days": 5.5,
    "by_model": {
      "gpt-5.3-codex": {"used_pct": 18, "weight": 1.0},
      "gpt-5.3-codex-spark": {"used_pct": 62, "weight": 0.67},
      "gpt-5.4": {"used_pct": 3, "weight": 1.3}
    },
    "source": "state.db + codex-ratelimit"
  },
  "recommendations": [
    {"severity": "warning", "message": "Spark 残 < 20% — 軽量タスクは 5.4-mini 推奨"}
  ],
  "cached": true,
  "cache_age_sec": 342
}
```

### 1.2 `helix budget forecast`

**用途**: N 日後の消費予測 + 枯渇シミュレーション。

```
$ helix budget forecast --days 7
過去 7 日平均: Claude 12%/日, Codex 14%/日
7 日後予測:   Claude 84% 消費, Codex 98% 消費 (枯渇リスク: HIGH)
```

**フラグ**:
- `--days N` (default 7): 予測日数
- `--json`: JSON 出力

### 1.3 `helix budget classify`

**用途**: タスク難度から effort (low/medium/high/xhigh) を推定 (dry-run)。

```
$ helix budget classify --task "cli/helix-debt に --id オプション追加" --role se --size S --files 1
effort: low
score: 3/20 (files=1, 横断=1, 仕様理解=1, 副作用=0, テスト=0)
根拠: 単一ファイル・既存パターン追加・副作用なし
推奨 thinking: medium (ロール既定 high を自動降格、timeout リスク回避)
```

**フラグ**:
- `--task "text"` (必須)
- `--role tl|se|pg|fe|qa|security|dba|devops|docs|research|legacy|perf`
- `--size S|M|L`
- `--files N` / `--lines N` (省略可、task から推定)
- `--json`

### 1.4 `helix budget simulate`

**用途**: classify + 残量を組み合わせて最終推奨モデル + thinking を提示。

```
$ helix budget simulate --task "API ハンドラ実装 (3 エンドポイント)" --role se
分類: effort=medium, size=M, files=3
残量: 5.3=70%, 5.4=85%, Spark=25% (警告)
推奨: gpt-5.3-codex --thinking medium
理由: 実装系 M タスクは 5.3 が最適 / Spark は残少・品質リスクで回避 / 5.4 は必要ない
```

### 1.5 `helix budget cache [clear|status]`

キャッシュ管理ヘルパー。

---

## 2. 既存 CLI 拡張

### 2.1 `helix-codex --auto-thinking`

```
$ helix-codex --role se --task "..." --auto-thinking
[auto-thinking] classifier: effort=medium (score=6/20)
[auto-thinking] budget check: 5.3=70% OK → 降格不要
[helix-codex] invoking codex exec with --thinking medium
...
```

`--thinking <level>` と併用時は手動優先、`--auto-thinking` は suggest 表示のみ。

### 2.2 `helix-skill use --auto-thinking`

Codex ロール選択時のみ有効 (Claude サブエージェントは frontmatter 固定)。

---

## 3. Hook 統合

### 3.1 SessionStart hook

**登録**: `~/.claude/settings.json` の `hooks.SessionStart` に追加
**コマンド**: `~/ai-dev-kit-vscode/cli/helix-budget-hook session-start`
**出力**:
```
[HELIX] Budget: Claude 58% left, Codex 72% left (warnings: Spark < 20%)
```

### 3.2 非ブロッキング

- exit 0 固定 (hook 失敗でセッション起動を妨げない)
- stderr エラーは `.helix/budget/hook.log` に記録

---

## 4. データファイル

| パス | 用途 | 備考 |
|------|------|------|
| `.helix/budget/cache/status.json` | 取得結果 1h キャッシュ | TTL 切れで再取得 |
| `.helix/budget/observed-limits.json` | 実測上限 (枯渇時点の累積値) | 学習データ |
| `.helix/budget/hook.log` | hook 実行ログ | ローテーション 1MB |
| `cli/config/model-fallback.yaml` | 降格ルール | 外出し・ユーザー編集可 |
| `cli/config/plan-limits.yaml` | プラン別想定上限 | Free/Pro/Max/Team |

**gitignore 追加**: `.helix/budget/` 全体 (NFR-S3)

---

## 5. Exit codes

| code | 意味 |
|------|------|
| 0 | 正常 |
| 1 | 一般エラー |
| 2 | CLI 引数エラー |
| 3 | 残量取得失敗 (両側) |
| 4 | classifier 呼び出し失敗 |
| 10 | 枯渇警告 (non-fatal, stderr に警告) |

---

## 6. エラーメッセージ方針

- 日本語 (ユーザー向け) / JSON mode は英語 key
- サジェスト付き (例: "ccusage 未検出 → `npm install -g ccusage` または JSONL フォールバック使用")
- 認証情報・path は一切出力しない (NFR-S1)
