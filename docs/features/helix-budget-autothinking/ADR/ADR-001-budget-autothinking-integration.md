# ADR-001〜005: helix-budget + auto-thinking 設計判断

**Feature**: helix-budget-autothinking
**Date**: 2026-04-21
**Status**: Accepted (PM 判断, G2 で TL adversarial-review 予定)

---

## ADR-001: Claude 消費取得は `ccusage` subprocess 呼び出しで採用

### Context

Claude の消費トラッキングは `~/.claude/projects/*.jsonl` 解析で可能。OSS の `ccusage` が成熟している (FR-A1 参考)。

### Options

| 案 | Pros | Cons |
|----|------|------|
| A. `ccusage` subprocess | メンテ不要、CLI 出力を parse | npm 依存、未インストール時のフォールバック必要 |
| B. 自前 JSONL parser | 依存削減、環境非依存 | 実装・保守コスト、機能重複 |
| C. `ccusage` 内部関数ラップ (import) | 型安全・高速 | Node.js 依存 + HELIX の Python 路線と不整合 |

### Decision

**A 採用 + JSONL フォールバック**。

- 通常: `ccusage` subprocess (JSON 出力) を parse
- 未インストール環境: JSONL を直接 parse する最小実装をフォールバックに持つ
- 将来 `ccusage` 仕様変更時は fallback に切替可

### Consequences

- 既存 OSS と重複せず、先行調査 (helix-budget-prior-art.md A 結論) に整合
- `ccusage` の品質に依存 → L6 統合検証時に version 固定推奨
- フォールバック実装 (~50 行) は最小機能のみ (weekly / daily 集計のみ)

---

## ADR-002: Codex 消費取得は `~/.codex/state.db` 直接クエリ

### Context

Codex 消費は state.db (SQLite) に記録される。`codex-ratelimit` OSS もあるが依存追加コストあり。`codex-usage-research.md` ADR-002 参考。

### Options

| 案 | Pros | Cons |
|----|------|------|
| A. state.db 直接クエリ | 軽量 (sqlite3 標準ライブラリ)、依存ゼロ | state.db スキーマ変更リスクあり (非公式) |
| B. `codex-ratelimit` fork/import | テスト済みコード流用 | 他人のリポジトリ依存、メンテ放棄リスク |
| C. 非公式 API (`chatgpt.com/backend-api/wham/usage`) | 公式に近い値 | 認証 token 漏洩リスク + 規約グレー |

### Decision

**A 採用**。C はデフォルト無効 (opt-in flag `--use-wham-api` のみ、NFR-S2)。

- state.db 未存在環境はエラーにせず「取得不可」を返す (initial install 直後など)
- スキーマ変更検知時は警告出力 + fallback に切替
- `codex-ratelimit` は参考のみ、クエリパターン確認に使用

### Consequences

- Codex state.db バージョン依存 (将来の Codex 更新で壊れる可能性)
- 検証: L6 で Codex バージョン別に動作確認 (最新 + 1 つ前)
- 代替手段として `codex` CLI の `/status` (TUI) パースも検討したが自動化困難で棄却

---

## ADR-003: effort classifier は gpt-5.4-mini を採用

### Context

タスク難度 → effort (low/medium/high/xhigh) の自動判定が必要 (FR-D2)。既存 HELIX には recommender / classifier が gpt-5.4-mini で動作する実績あり (`cli/roles/recommender.conf`)。

### Options

| 案 | Pros | Cons |
|----|------|------|
| A. gpt-5.4-mini (既存路線) | 実績あり、コスト < $0.001/call、応答 < 3秒 | 精度は mini 相当 |
| B. gpt-5.3-codex | 精度高 | コスト 5-10x、応答遅 |
| C. ルールベースのみ (LLM なし) | コスト 0 | ヒューリスティック限界、新タスク種別で精度低下 |
| D. ローカル ML (scikit-learn 等) | コスト 0 | 学習データ少、開発コスト |

### Decision

**A 採用 + C ハイブリッド**。

- 5 軸スコアリング (ルール) で粗分類
- 境界値 (score=4, 7, 12) で LLM 判定を呼び出す
- キャッシュ (task_hash, 1h TTL) で再呼び出し抑制

### Consequences

- 既存 classifier / recommender と統一路線で保守コスト最小
- キャッシュヒット率 70% 目標 (NFR-C3) を skill_usage 実測で検証
- 精度不足時は B (5.3) にアップグレード可 (`--classifier-model` フラグで切替)

---

## ADR-004: 降格ルールは YAML 外出し (`cli/config/model-fallback.yaml`)

### Context

モデル降格ルールは `project_helix_budget.md` に記載済みだが、ハードコードするとユーザー別の選好に対応できない (feedback: 「5.3 デフォルト、5.4 は雑プロンプト」)。

### Options

| 案 | Pros | Cons |
|----|------|------|
| A. YAML 外出し | ユーザー編集可、diff 管理可 | 読み込みロジック追加 |
| B. Python 定数 | シンプル | 編集しづらい、再インストール必要 |
| C. DB テーブル | 動的変更可能 | 過剰設計 (変更頻度低) |

### Decision

**A 採用**。

- デフォルト: HELIX ビルトイン (5.3 中心、feedback_codex_model_selection.md 反映)
- ユーザー上書き: `~/.config/helix/model-fallback.yaml` を優先読み込み
- スキーマ検証あり (YAML 壊れたら警告 + デフォルトに fallback)

### Consequences

- ユーザー別カスタマイズ可能 → 実践編運用で選好収集しやすい
- 外部ファイル読み込みで若干パフォーマンス低下 (< 10ms、キャッシュで回避)

---

## ADR-005: 非公式 API (`wham/usage`) はデフォルト無効

### Context

Codex の内部 API `chatgpt.com/backend-api/wham/usage` を使えば公式に近い残量が取れるが、以下のリスク:
- `~/.codex/auth.json` の access_token 読み取りが必要
- 規約グレー (OpenAI Terms 的に opt-in 推奨)
- token 漏洩 (logging, error trace 経由)

### Options

| 案 | Pros | Cons |
|----|------|------|
| A. デフォルト有効 | 精度最高 | セキュリティ/規約リスク |
| B. デフォルト無効 + opt-in | 安全 / 透明性高 | 初期精度は推定値ベース |
| C. 廃止 (実装しない) | 最も安全 | 将来の精度向上の芽を潰す |

### Decision

**B 採用**。

- `helix budget status --use-wham-api` で明示 opt-in
- opt-in 時も auth.json から読むのは access_token のみ、ログ出力絶対禁止
- 利用時に警告: "非公式 API / OpenAI 規約確認推奨"

### Consequences

- セキュリティ優先で Max プラン個人運用に適合
- 精度向上ニーズは observed-limits.json の学習ベースで補う (2-3 週で実測精度向上、NFR-M3)

---

## ADR-006: auto-thinking Phase B は Phase A (frontmatter) と共存

### Context

既に Phase A (サブエージェント frontmatter `effort`) が完了 (2026-04-21 0af8e8b)。Phase B (タスク難度自動判定) は Codex ロール向け。

### Decision

Phase A + B は**責務分離**。

- Phase A: Claude サブエージェント (fe-*, be-*, qa-*, security-*, db-*, devops-*) の固定 effort
- Phase B: Codex ロール (tl/se/pg/fe/qa/security/dba/devops/docs/research/legacy/perf) の動的 effort

`helix-skill use` は recommender が agent を決めた後、Codex ロールなら Phase B classifier を呼び、Claude subagent なら Phase A frontmatter を使う。

---

## 未決事項 (G2 で議論)

| 項目 | 判断理由 | 決定者 |
|------|---------|-------|
| プラン別想定上限の初期値 | Max の週次上限が非公開 | TL + PO |
| forecast 精度のしきい値 (±何%で OK) | 初期は "目安" として運用 | TL |
| 5.4-mini を codex ロールに格上げするか | spark の代替範囲 | TL + PO |
| 降格提案の UI (対話 / non-blocking / silent) | ユーザー選好 | PO |

G2 adversarial-review でこれらを潰す。
