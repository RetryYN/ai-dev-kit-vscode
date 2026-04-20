# D-DEP: 依存関係マップ — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking

---

## 1. 内部依存 (HELIX 内)

| 依存元 | 依存先 | 種別 | 備考 |
|-------|-------|------|------|
| `cli/helix-budget` | `cli/lib/budget_cli.py` | subprocess (python3) | dispatcher |
| `cli/lib/budget_cli.py` | `cli/lib/budget.py` | import | 消費取得 |
| `cli/lib/budget_cli.py` | `cli/lib/effort_classifier.py` | import | 難度判定 |
| `cli/lib/budget_cli.py` | `cli/lib/model_fallback.py` | import | 降格 |
| `cli/lib/budget.py` | `cli/lib/helix_db.py` (既存) | import | helix.db アクセス |
| `cli/lib/effort_classifier.py` | `cli/roles/effort-classifier.conf` | read | gpt-5.4-mini ロール設定 |
| `cli/lib/effort_classifier.py` | `cli/templates/effort-classify-prompt.md` | read | LLM プロンプト |
| `cli/lib/model_fallback.py` | `cli/config/model-fallback.yaml` | read | 降格ルール |
| `cli/lib/model_fallback.py` | `cli/config/plan-limits.yaml` | read | プラン別上限 |
| `cli/helix-budget-hook` | `cli/lib/budget_cli.py` | subprocess | SessionStart |
| `cli/helix-codex` | `cli/lib/effort_classifier.py` | subprocess (`--auto-thinking` 時のみ) | optional |
| `cli/helix-codex` | `cli/lib/budget.py` | subprocess (同上) | optional |
| `cli/helix-skill` | `cli/lib/skill_dispatcher.py` (既存) | import | 拡張ポイント |
| `cli/lib/skill_dispatcher.py` | `cli/lib/budget.py` (新規追加) | import | budget check hook |
| `cli/helix-init` | `cli/lib/merge_settings.py` (既存) | import | SessionStart hook 登録 |
| `cli/helix-init` | `cli/lib/db_migrate.py` (拡張) | import | v5→v6 マイグレ |
| `cli/helix-log` | `cli/lib/budget.py` | import | `report budget` サブコマンド |

### 内部依存の循環チェック

- `budget.py` → `helix_db.py` → (他に戻らない) ✅
- `effort_classifier.py` → `budget.py` への依存なし ✅
- `model_fallback.py` は上記 2 つに依存するが逆方向なし ✅
- 循環依存なし

---

## 2. 外部依存 (他 OSS / 言語ランタイム)

### 2.1 必須依存

| 依存 | 種別 | バージョン | 目的 | 代替 |
|------|------|----------|------|-----|
| Python 3.9+ | ランタイム | 3.9 以上 | HELIX CLI 共通 | なし |
| sqlite3 (標準) | Python 標準 | — | helix.db アクセス | なし |
| yaml (PyYAML) | Python ライブラリ | — | **回避**: 既存 `yaml_parser.py` 使用 | — |
| bash 4.4+ | シェル | — | CLI dispatcher | — |
| Codex CLI | 外部 CLI | 最新 | effort classifier 呼び出し | — |

### 2.2 optional 依存

| 依存 | 種別 | 目的 | フォールバック |
|------|------|------|-------------|
| `ccusage` | npm package | Claude 消費取得 | JSONL 直接 parse |
| `codex-ratelimit` | 参考実装 | state.db クエリパターン | 自前実装 |

### 2.3 非依存 (明示的に避ける)

- Node.js: ccusage 実行時のみ subprocess 経由で使う、HELIX 本体は Python 路線維持
- PyYAML: 既存 HELIX 方針で `yaml_parser.py` を使用
- HTTP ライブラリ (requests 等): 非公式 API は opt-in のみ、標準 `urllib` で十分

---

## 3. 外部サービス

| サービス | 用途 | ネットワーク | 必須/オプション |
|---------|------|------------|---------------|
| Codex CLI (gpt-5.4-mini) | effort classifier | HTTPS → OpenAI API | --auto-thinking 時必須 |
| Codex CLI (通常ロール) | helix-codex 実行 | HTTPS → OpenAI API | 既存機能 |
| Claude Code | セッション | HTTPS → Anthropic API | 既存機能 |
| `chatgpt.com/backend-api/wham/usage` (非公式) | Codex 残量精密取得 | HTTPS | **opt-in のみ (ADR-005)** |
| npm registry (`ccusage` 取得) | インストール時のみ | HTTPS → npmjs.com | `npm install -g ccusage` 時 |

### 3.1 ネットワーク境界

- HELIX CLI 本体はオフライン動作可能 (残量取得・分類除く)
- ccusage / Codex CLI の通信はそれら自身の責任
- HELIX 直接のネットワーク呼び出しはなし (非公式 API opt-in 時を除く)

---

## 4. 障害時影響

### 4.1 内部依存障害

| 障害 | 影響 | 緩和策 |
|-----|------|-------|
| `helix.db` 破損 | skill_usage / budget_events 記録不可 | `helix init --repair` で再生成 (履歴失う) |
| `model-fallback.yaml` 不正 | 降格エンジン動作不可 | デフォルトルールで fallback (警告表示) |
| `plan-limits.yaml` 不正 | 残量% 推定不可 | 絶対値表示のみに縮退 |

### 4.2 外部依存障害

| 障害 | 影響 | 緩和策 |
|-----|------|-------|
| `ccusage` 未インストール | Claude 消費精度低下 | JSONL 直接 parse フォールバック (NFR-R1) |
| `~/.claude/projects/` 空 | 消費データ取得不可 | エラー表示 + 0% 表示で続行 |
| `~/.codex/state.db` 未存在 | Codex 残量不明 | 警告 + "取得不可" 表示 |
| `~/.codex/state.db` ロック中 | 取得遅延 | キャッシュ使用 (NFR-R2) |
| Codex CLI 呼び出し失敗 (classifier) | auto-thinking 無効化 | ルールベース fallback (NFR-R3) |
| ネットワーク切断 | classifier 呼び出し不可 | キャッシュ hit で継続、miss 時はルールのみ |
| Codex state.db スキーマ変更 | Codex 残量取得不可 | fallback + error event 記録 + 警告 |
| OpenAI API 障害 | classifier 利用不可 | 既存の role 既定 thinking で続行 |
| Anthropic API 障害 | HELIX 動作不可 (上位レイヤー) | 対応範囲外 |

### 4.3 エスカレーション

- ccusage / state.db スキーマ変更 → issue 作成 + maintenance 対応
- 非公式 API 停止 → opt-in 利用者のみ影響、警告表示
- Codex CLI メジャー更新 → regression test (`helix test`) で検知

### 4.4 運用への影響度ランク

| 影響度 | 対象 |
|-------|------|
| Critical | helix.db 破損、Codex CLI 停止 |
| High | state.db スキーマ変更、model-fallback.yaml 不正 |
| Medium | ccusage 障害 (フォールバックあり) |
| Low | 非公式 API 障害 (opt-in のみ) |

---

## 5. 依存グラフ (ASCII)

```
                 [User]
                   ↓
        [~/.claude/settings.json hooks]
                   ↓
        [helix-budget-hook]
                   ↓
   [helix-budget] ─────────┐
                   ↓       ↓
            [budget_cli.py]
              ↓    ↓    ↓    ↓
        [budget][classify][fallback]
           ↓       ↓         ↓
     ┌─────┴──┐   [Codex CLI] [yaml]
     ↓        ↓        ↓
  [ccusage] [state.db] [gpt-5.4-mini]
     ↓        ↓
  [JSONL]  [SQLite]
```

---

## 6. 関連ドキュメント

- `D-ARCH/architecture.md` §3 — 依存関係 (architecture-level)
- `D-MIG-PLAN/migration-plan.md` — SQLite version 要件
- `D-TEST/test-design.md` — 各依存のモック化戦略
