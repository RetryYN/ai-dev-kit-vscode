# D-REQ-NF: 非機能要件 — helix-budget + auto-thinking Phase B

**Feature**: helix-budget-autothinking

---

## 1. 性能 (パフォーマンス)

| ID | 要件 | 測定方法 |
|----|------|----------|
| NFR-P1 | `helix budget status` 応答 < 2 秒 (キャッシュヒット時 < 200ms) | bats でタイマー計測 |
| NFR-P2 | effort-classifier (gpt-5.4-mini) 応答 < 3 秒 | 既存 classifier/recommender と同基準 |
| NFR-P3 | session-start hook 追加オーバーヘッド < 500ms | hook 無効化との比較 |
| NFR-P4 | ccusage 呼び出しは 10 秒以上かかる場合は skip (キャッシュ優先) | timeout guard |

## 2. コスト

| ID | 要件 |
|----|------|
| NFR-C1 | effort-classifier 1 呼び出し < $0.001 (gpt-5.4-mini) |
| NFR-C2 | auto-thinking 有効化による追加消費は 月次 Codex 枠の 1% 以下 |
| NFR-C3 | キャッシュヒット率 70% 以上 (1 時間 TTL、task_hash キー) |

## 3. 互換性 / 非破壊

| ID | 要件 |
|----|------|
| NFR-B1 | 既存 CLI (helix-codex / helix-skill / helix-gate / helix-sprint) は新機能フラグなしで従来動作を維持 |
| NFR-B2 | `~/.claude/projects/` / `~/.codex/state.db` は read-only アクセス |
| NFR-B3 | `helix test` (既存 453 テスト) を破壊しない |
| NFR-B4 | settings.json / CLAUDE.md の既存セクションは上書きせず追記 |

## 4. 可用性 / 信頼性

| ID | 要件 |
|----|------|
| NFR-R1 | ccusage 未インストール時は JSONL 直接 parse にフォールバック |
| NFR-R2 | `~/.codex/state.db` ロック中は前回キャッシュを使用 |
| NFR-R3 | gpt-5.4-mini 応答失敗時は既存の role 既定 effort にフォールバック |
| NFR-R4 | budget ディレクトリ破損時は `helix init --repair` で再生成可能 |

## 5. セキュリティ

| ID | 要件 |
|----|------|
| NFR-S1 | `~/.codex/auth.json` の access_token を画面出力しない / ログに残さない |
| NFR-S2 | `chatgpt.com/backend-api/wham/usage` (非公式 API) は **使用しない** (デフォルト) — オプトイン |
| NFR-S3 | `.helix/budget/` 配下は `.gitignore` 必須 |
| NFR-S4 | 外部送信は gpt-5.4-mini への task 説明のみ (認証情報送信禁止) |

## 6. 運用保守性

| ID | 要件 |
|----|------|
| NFR-M1 | 新規モジュールは `cli/lib/` 配下に集約 (budget.py / effort_classifier.py / model_fallback.py) |
| NFR-M2 | SQLite スキーマ変更時はマイグレーション (helix_db v6 昇格) |
| NFR-M3 | bats テストカバレッジ 80% 以上 (既存 CI で自動検証) |
| NFR-M4 | 降格ルールは YAML で外出し (`cli/config/model-fallback.yaml`) |

## 7. 観測性

| ID | 要件 |
|----|------|
| NFR-O1 | effort 分類結果を `skill_usage` に記録 |
| NFR-O2 | 降格適用イベントを `helix.db` の `events` テーブルに記録 |
| NFR-O3 | 枯渇予測精度を `helix log report budget --accuracy` で検証可能 |

## 8. 拡張性

| ID | 要件 |
|----|------|
| NFR-E1 | モデル追加は `model-fallback.yaml` への行追加のみで対応 |
| NFR-E2 | 難度スコア軸追加は `cli/lib/effort_classifier.py` の weights dict に追加するだけで動作 |
| NFR-E3 | プラン (Free/Pro/Max/Team) 別の想定上限は `cli/config/plan-limits.yaml` で差し替え可能 |
