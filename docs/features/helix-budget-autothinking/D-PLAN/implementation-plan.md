# D-PLAN: 実装工程表 — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**Size**: L (8 files, 600 lines, API)
**L4 駆動**: be (ロジック → API → テスト)
**期間見積**: 2 日 (実装 1.5 日 + 検証 0.5 日)

---

## 0. 環境

### 前提環境
- OS: Linux (WSL2 Ubuntu 22.04)
- Python: 3.11+
- SQLite: 3.35+ (DROP COLUMN サポート)
- Codex CLI: 最新
- `~/.claude/projects/` / `~/.codex/` 読み取り可能

### 必要ツール
- bats-core (既存)
- pytest (新規追加、requirements-dev.txt)
- `ccusage` (optional、npm install -g ccusage)

### 作業ブランチ
- `improvements/helix-overhaul` (現ブランチ) で作業継続
- G6 pass 後に `main` merge PR

---

## 1. タスク一覧 (マイクロスプリント単位)

### Sprint 1a: bootstrap (着手準備)

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 1a-01 | `cli/config/model-fallback.yaml` 作成 (デフォルトルール) | Codex PG | — | 15 分 |
| 1a-02 | `cli/config/plan-limits.yaml` 作成 | Codex PG | — | 15 分 |
| 1a-03 | `cli/roles/effort-classifier.conf` 作成 | Codex docs | — | 10 分 |
| 1a-04 | `cli/templates/effort-classify-prompt.md` 作成 | Codex docs | — | 20 分 |
| 1a-05 | `.gitignore` に `.helix/budget/` 追加 | PM | — | 5 分 |

### Sprint 1b: DB マイグレーション

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 1b-01 | `cli/lib/db_migrate.py` に v5→v6 マイグレ追加 | Codex SE | 1a-* | 30 分 |
| 1b-02 | `cli/helix-migrate` dispatcher (未存在なら作成) | Codex PG | 1b-01 | 20 分 |
| 1b-03 | マイグレーション bats テスト (T-NH-15~18, T-ER-15~17) | Codex QA | 1b-01 | 30 分 |

### Sprint 2: 消費取得モジュール (budget.py)

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 2-01 | `cli/lib/budget.py` - ClaudeBudget クラス (ccusage + JSONL fallback) | Codex SE | 1b-* | 45 分 |
| 2-02 | `cli/lib/budget.py` - CodexBudget クラス (state.db 直接クエリ) | Codex SE | 1b-* | 45 分 |
| 2-03 | `cli/lib/budget.py` - ForecastEngine (線形外挿) | Codex SE | 2-01, 2-02 | 30 分 |
| 2-04 | `cli/lib/budget.py` - BudgetCache (1h TTL) | Codex PG | 2-01 | 20 分 |
| 2-05 | pytest (test_budget.py 12 件) | Codex QA | 2-01~04 | 40 分 |

### Sprint 3: effort classifier

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 3-01 | `cli/lib/effort_classifier.py` - score_task (5 軸) | Codex SE | 1a-03, 1a-04 | 30 分 |
| 3-02 | `cli/lib/effort_classifier.py` - call_classifier (gpt-5.4-mini) | Codex SE | 3-01 | 40 分 |
| 3-03 | `cli/lib/effort_classifier.py` - キャッシュ (SHA256 task_hash) | Codex PG | 3-02 | 20 分 |
| 3-04 | pytest (test_effort_classifier.py 10 件) | Codex QA | 3-01~03 | 35 分 |

### Sprint 4: model fallback

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 4-01 | `cli/lib/model_fallback.py` - load_rules (YAML 検証) | Codex PG | 1a-01 | 20 分 |
| 4-02 | `cli/lib/model_fallback.py` - suggest_model + apply_rule | Codex SE | 4-01, 2-* | 30 分 |
| 4-03 | pytest (test_model_fallback.py 8 件) | Codex QA | 4-01~02 | 25 分 |

### Sprint 5: CLI 本体

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 5-01 | `cli/lib/budget_cli.py` - サブコマンド dispatch | Codex SE | 2-*, 3-*, 4-* | 45 分 |
| 5-02 | `cli/helix-budget` bash dispatcher | Codex PG | 5-01 | 20 分 |
| 5-03 | `cli/helix-budget-hook` (SessionStart) | Codex PG | 5-01 | 20 分 |
| 5-04 | bats (helix-budget-*.bats 全 20 件) | Codex QA | 5-01~03 | 90 分 |

### Sprint 6: 既存 CLI 拡張

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 6-01 | `helix-codex` に `--auto-thinking` フラグ追加 | Codex SE | 3-*, 4-* | 40 分 |
| 6-02 | `helix-skill use` に `--auto-thinking` フラグ追加 | Codex SE | 6-01 | 30 分 |
| 6-03 | `cli/lib/skill_dispatcher.py` 拡張 (budget check hook point) | Codex SE | 6-01 | 25 分 |
| 6-04 | `cli/helix-log` に `report budget` 追加 | Codex PG | 2-*, DB v6 | 40 分 |
| 6-05 | bats (拡張系 10 件) | Codex QA | 6-01~04 | 60 分 |

### Sprint 7: hook 統合 + init

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 7-01 | `cli/helix-init` に hook 登録 + migration 誘導追加 | Codex PG | 5-03, 1b-* | 30 分 |
| 7-02 | `cli/lib/merge_settings.py` に helix-budget hook 対応 | Codex PG | 7-01 | 20 分 |
| 7-03 | security-audit agent セキュリティテスト (T-ER-11~14) | security-audit | 5-*, 6-*, 7-* | 30 分 |

### Sprint 8: 統合 + 回帰

| ID | タスク | 担当 | 依存 | 想定時間 |
|----|-------|------|------|---------|
| 8-01 | `helix test` 全 PASS 確認 (既存 453 + 新規 55) | Codex QA | 全 Sprint | 20 分 |
| 8-02 | 手動 smoke テスト (status/forecast/classify/simulate) | PM | 8-01 | 20 分 |
| 8-03 | `helix gate G4` pass | PM | 8-01, 8-02 | 5 分 |
| 8-04 | ドキュメント更新 (CLAUDE.md / SKILL_MAP.md) | Codex docs | 8-03 | 30 分 |

---

## 2. 依存関係グラフ

```
Sprint 1a (設定ファイル)
       ↓
Sprint 1b (DB マイグレ)
       ↓
Sprint 2 (budget.py) ─┐
                      ├─→ Sprint 5 (CLI)
Sprint 3 (classifier)─┤        ↓
                      │   Sprint 6 (既存 CLI 拡張)
Sprint 4 (fallback) ──┘        ↓
                          Sprint 7 (hook/init)
                               ↓
                          Sprint 8 (統合/回帰)
                               ↓
                             G4 Gate
```

並列実行可能:
- Sprint 2 ∥ Sprint 3 ∥ Sprint 4 (独立)
- Sprint 6-01〜04 は 5 完了後並列可

---

## 3. 担当 (ロール別)

| ロール | 担当スプリント | 推定合計時間 |
|-------|-------------|-----------|
| Codex SE (上級実装) | 2-01~04, 3-01~02, 4-02, 5-01, 6-01~03 | ~6 時間 |
| Codex PG (通常実装) | 1a-01~04, 1b-02, 2-04, 3-03, 4-01, 5-02~03, 6-04, 7-01~02 | ~3.5 時間 |
| Codex QA (テスト) | 1b-03, 2-05, 3-04, 4-03, 5-04, 6-05, 8-01 | ~5 時間 |
| Codex docs | 1a-03~04, 8-04 | ~1 時間 |
| security-audit agent | 7-03 | ~30 分 |
| PM (Opus) | 1a-05, 8-02~03 | ~30 分 |

合計実装時間: ~16 時間 (2 日ペース、並列実行で短縮可)

---

## 4. 環境準備

### 4.1 開発環境セットアップ

```bash
# pytest 追加 (未インストールなら)
pip install --user pytest pytest-cov

# ccusage オプション確認
which ccusage || echo "WARN: ccusage 未インストール、JSONL fallback テスト追加必要"

# 現行 helix.db バックアップ
cp .helix/helix.db .helix/helix.db.backup-v5-$(date +%Y%m%d-%H%M%S)

# 現行テスト PASS 確認
~/ai-dev-kit-vscode/cli/helix test
# 期待: 453 PASS
```

### 4.2 実装開始前チェック

- [ ] phase.yaml が L4 (G3 pass 後) に遷移済み
- [ ] ブランチ `improvements/helix-overhaul` で clean
- [ ] バックアップ取得済み
- [ ] 既存 453 テスト PASS

---

## 5. ロールバック準備

### 5.1 commit 戦略

- Sprint 単位で atomic commit (部分完了ではなく Sprint 完了時)
- 各 Sprint 完了時に `helix test` で regression 確認
- Sprint 末で `helix review --uncommitted` を回す

### 5.2 ロールバック単位

| 粒度 | 方法 | 影響 |
|-----|------|------|
| Sprint 単位 | `git revert <sprint-commit>` | 個別 Sprint 取り消し |
| Feature 全体 | `git reset --hard <pre-feature>` | 本 feature 完全撤回 (確認必須) |
| DB のみ | `cp .helix/helix.db.backup-v5-* .helix/helix.db` | DB v5 に戻す |
| hook のみ | `python3 cli/lib/merge_settings.py ~/.claude/settings.json --remove` | hook 除去 |

### 5.3 ロールバック発動条件

- G4 gate fail 連続 2 回 → PM 判断で Sprint 単位 revert
- 既存 453 テスト 1 件でも break → 即 Sprint revert + 原因調査
- security-audit Critical 指摘 → 該当 Sprint 修正まで後続ブロック
- 本番用語: これは開発ブランチ機能追加なので「本番影響」の概念は L7 デプロイまで発生しない

### 5.4 ロールバック後の引き継ぎ

- `.helix/helix.db` バックアップ復元手順を runbook に記載
- 工程表 (本ファイル) に "ロールバック実施" セクションを追記
- 次回着手時に原因分析から再開

---

## 6. リスク・留意事項

| リスク | 対策 |
|-------|-----|
| Codex 10分 timeout | Sprint 粒度を 30-45 分以内に分割、`--thinking medium` デフォルト |
| state.db スキーマ変更 (Codex 更新) | fallback 実装 + 警告表示 (D-DEP §4.2) |
| gpt-5.4-mini 応答不安定 | ルールベース fallback + キャッシュ優先 |
| L4 中の設計変更 | drift-check + debt-register で管理 |
| 実装時間超過 (想定 2 日 → 3 日+) | Sprint 6-04 (report budget) を G4 後に延期可 |

---

## 7. 検証 (G4 前)

```bash
# 全テスト
~/ai-dev-kit-vscode/cli/helix test

# 回帰チェック
~/ai-dev-kit-vscode/cli/helix gate G4

# セキュリティ
# security-audit agent を Sprint 7-03 で発火

# smoke
helix budget status
helix budget classify --task "typo 修正" --size S
helix budget simulate --task "API ハンドラ 3 本実装" --role se
```

---

## 8. 完了条件

- [ ] 全 Sprint のタスク完了
- [ ] 55 新規テスト + 453 既存テスト全 PASS
- [ ] `helix gate G4` pass
- [ ] security-audit Critical/High ゼロ
- [ ] smoke テスト 4 件 pass
- [ ] ドキュメント (CLAUDE.md / SKILL_MAP.md) 更新
- [ ] commit push 完了
