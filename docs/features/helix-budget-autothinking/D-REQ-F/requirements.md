# D-REQ-F: 機能要件 — helix-budget + auto-thinking Phase B

**Feature**: helix-budget-autothinking
**Drive**: be (CLI 機能追加、UI なし)
**Size**: L (8 files, 600 lines, API)
**Origin**: project_helix_budget.md + project_auto_thinking.md (2026-04-21)

---

## 0. 目的

HELIX 自身の運用における「Claude / Codex 枠切れ事故」「thinking ミスマッチによる timeout 事故」を dogfooding で解決する。残量の自動監視 + タスク難度に応じた effort 自動判定 + 枯渇モデル自動降格で「枠切れゼロ」を実現する。

## 0.1 インスコープ

- Claude (`ccusage` or JSONL 直接 parse) と Codex (`~/.codex/state.db`) の消費取得
- `helix budget status/forecast/classify/simulate` CLI
- session-start hook (残量表示 + 20% 警告)
- gpt-5.4-mini による effort 自動判定
- 降格ルール (YAML 外出し) + ユーザー確認
- `skill_usage` + `events` テーブルへの記録・学習

## 0.2 アウトスコープ

- 公式 API (組織 Admin) 経由の残量取得 (Max では不可)
- Dashboard TUI (project_helix_dashboard_idea.md の別案件)
- Gemini / Grok など他モデル対応
- 本番環境での強制降格 (提案のみ)
- 非公式 API `chatgpt.com/backend-api/wham/usage` のデフォルト有効化 (opt-in のみ)

## 1. 背景

HELIX フレームワークを 1 週間以上運用すると Claude / Codex の枠が切れて開発が止まる事故が多発する。特に:
- Codex 5.3 Spark が週内に枯渇しやすい
- `helix-codex --role se --thinking high` を S タスクに投げて 10 分 timeout
- 残量不明のままタスク投入 → 途中で動かなくなる

**ゴール**: 残量を常時可視化し、タスク難度に応じた effort 自動判定 + 枯渇モデル自動降格で「枠切れ事故ゼロ」を実現する。

---

## 2. 機能要件 (FR)

### FR-A: 消費データ取得

| ID | 要件 | 根拠 |
|----|------|------|
| FR-A1 | Claude 消費を `ccusage` 経由で取得する (未インストール時は `~/.claude/projects/*.jsonl` を直接 parse するフォールバック) | codex-usage-research.md |
| FR-A2 | Codex 消費を `~/.codex/state.db` (SQLite) クエリで取得する | 同上 |
| FR-A3 | 5h window 残 / 週次残 / 日次消費 を取得する | 同上 |
| FR-A4 | モデル別消費重み (5.4=1.3x / 5.3=1.0x / Spark=0.67x / 5.4-mini=0.3x) で正規化する | Codex 公開値 |

### FR-B: ステータス表示

| ID | 要件 |
|----|------|
| FR-B1 | `helix budget status` で Claude/Codex 両側の消費 % + 枯渇予測日時を表示 |
| FR-B2 | 表示形式: 人間可読 (デフォルト) + `--json` (自動化向け) |
| FR-B3 | モデル別内訳を `--breakdown` フラグで表示 |

### FR-C: Hook 統合

| ID | 要件 |
|----|------|
| FR-C1 | session-start hook で残量サマリを自動表示 (ワンライナー) |
| FR-C2 | 残 < 20% でセッション開始時に警告 (非ブロッキング) |
| FR-C3 | hook 登録は `helix init` が冪等に処理 (既存 settings.json 破壊なし) |

### FR-D: Effort 自動判定 (auto-thinking Phase B)

| ID | 要件 |
|----|------|
| FR-D1 | `cli/roles/effort-classifier.conf` (gpt-5.4-mini) を定義 |
| FR-D2 | `cli/lib/effort_classifier.py` がタスク記述 + role + size を受け取り effort (low/medium/high/xhigh) を返す |
| FR-D3 | 難度スコアリング 5 軸 (ファイル数・横断度・仕様理解必要度・副作用リスク・テスト複雑度) を合計点で分類 |
| FR-D4 | `helix-codex --auto-thinking` フラグで有効化 (デフォルト off、既存挙動維持) |
| FR-D5 | 分割推奨フラグ (xhigh + S size → "分割推奨" を CLI 出力) |

### FR-E: モデル降格提案

| ID | 要件 |
|----|------|
| FR-E1 | `helix-codex` / `helix-skill use` 前処理で残量を確認 |
| FR-E2 | 枯渇モデル (残 < 10%) 検出時に降格ルールを適用した代替モデルを提案 |
| FR-E3 | 降格ルール: Spark → 5.4-mini (軽量) or 5.3 (昇格) / 5.3 → 5.4 (雑・判断) or Spark (S 純粋実装) / 5.4 → hold |
| FR-E4 | ユーザー確認待ち (非対話時は `--yes` で自動適用) |

### FR-F: 統合 + 学習

| ID | 要件 |
|----|------|
| FR-F1 | effort-classifier + budget 情報 → 最適モデル自動選択 (effort × 残量 の 2 軸) |
| FR-F2 | `skill_usage` テーブルに実効 thinking/effort + timeout 有無 + 実消費を記録 |
| FR-F3 | `helix log report budget` で週次傾向・モデル別消費・ミスマッチ率を可視化 |
| FR-F4 | 枯渇検知時の累積消費を `.helix/budget/observed-limits.json` に記録 → 実測上限として学習 |

### FR-G: CLI インターフェース

| ID | 要件 |
|----|------|
| FR-G1 | `helix budget status [--json] [--breakdown]` — ステータス表示 |
| FR-G2 | `helix budget forecast [--days N]` — N 日後の消費予測 |
| FR-G3 | `helix budget classify --task "..." --role X --size S` — effort 自動判定 (dry-run) |
| FR-G4 | `helix budget simulate --task "..." --role X` — 残量 + effort 統合で推奨モデル提示 |
| FR-G5 | `helix-codex --auto-thinking` / `helix-skill use --auto-thinking` オプション追加 |

---

## 3. 対象外 (Out of Scope)

- 公式 API (組織 Admin) 経由の残量取得 (Max プランでは使えない)
- Dashboard TUI (project_helix_dashboard_idea.md で別案件)
- 他モデル (Gemini/Grok) サポート
- 本番環境での強制降格 (あくまで提案)

---

## 4. ステークホルダー

- **PM (Opus)**: 設計判断・統合方針
- **TL (Codex 5.4)**: L2/L3 設計・レビュー
- **SE (Codex 5.3)**: L4 実装主力
- **User**: `helix budget status` を日常的に叩く想定
