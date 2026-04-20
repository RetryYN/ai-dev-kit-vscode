# D-TEST: テスト設計 — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**テストフレームワーク**: bats-core (既存 HELIX 基盤) + pytest (Python unit)

---

## 1. 対象

### 1.1 テスト対象モジュール

| モジュール | テスト種別 | 新規 bats | 新規 pytest |
|----------|----------|-----------|------------|
| `cli/helix-budget` | bats (CLI 動作) | 8 | — |
| `cli/helix-budget-hook` | bats | 3 | — |
| `cli/lib/budget.py` | pytest (unit) | — | 12 |
| `cli/lib/effort_classifier.py` | pytest | — | 10 |
| `cli/lib/model_fallback.py` | pytest | — | 8 |
| `cli/lib/budget_cli.py` | pytest (integration) | — | 5 |
| `cli/helix-codex` (--auto-thinking) | bats | 3 | — |
| `cli/helix-skill use` (--auto-thinking) | bats | 2 | — |
| マイグレーション (v5→v6) | bats | 4 | — |

**合計**: bats 20 件 / pytest 35 件 → **55 テスト新規追加**

### 1.2 対象外 (明示)

- ccusage 本体の挙動 (OSS 側責任)
- Codex CLI の挙動 (外部 CLI)
- OpenAI API 実応答 (mock で代替)
- Claude Code UI 側 (HELIX 範囲外)

---

## 2. 正常系

### 2.1 CLI 正常系 (bats)

| ID | テスト | 期待結果 |
|----|--------|---------|
| T-NH-01 | `helix budget status` | exit 0 + Claude/Codex % 表示 |
| T-NH-02 | `helix budget status --json` | 有効 JSON 出力 |
| T-NH-03 | `helix budget status --breakdown` | モデル別内訳表示 |
| T-NH-04 | `helix budget forecast --days 7` | 7 日後予測表示 |
| T-NH-05 | `helix budget classify --task "typo 修正" --size S` | effort=low 返却 |
| T-NH-06 | `helix budget classify --task "API 設計 + DB 変更"` | effort=high/xhigh 返却 |
| T-NH-07 | `helix budget simulate --task "..." --role se` | 推奨モデル + thinking 提示 |
| T-NH-08 | `helix budget cache status` | キャッシュ数 / 最終更新表示 |

### 2.2 Hook 正常系

| ID | テスト | 期待結果 |
|----|--------|---------|
| T-NH-09 | SessionStart hook 実行 | stdout にワンライナー表示、exit 0 |
| T-NH-10 | hook < 1.5 秒 | timeout 内完了 (NFR-P3) |
| T-NH-11 | 既存 settings.json への追加 | 既存 hook 破壊なし |

### 2.3 既存 CLI 拡張 (正常系)

| ID | テスト | 期待結果 |
|----|--------|---------|
| T-NH-12 | `helix-codex --role se --task ... --auto-thinking` | classifier 呼び出し + effort 自動決定 + 既存挙動維持 |
| T-NH-13 | `helix-codex --role se --task ...` (フラグなし) | 従来挙動 100% 一致 |
| T-NH-14 | `helix-skill use SKILL-ID --auto-thinking` | Codex ロール選択時のみ classifier 発火 |

### 2.4 マイグレーション正常系

| ID | テスト | 期待結果 |
|----|--------|---------|
| T-NH-15 | v5 → v6 forward | version=6, skill_usage 新カラム存在, budget_events 作成 |
| T-NH-16 | v6 → v5 rollback | version=5, 新カラム削除 |
| T-NH-17 | forward → rollback → forward | idempotent |
| T-NH-18 | 既存 skill_usage レコード数保持 | マイグレーション前後で COUNT 一致 |

### 2.5 Python unit 正常系 (pytest 抜粋)

- `ClaudeBudget.get()` が ccusage 正常応答から dict 返却
- `CodexBudget.get()` が state.db から five_hour / weekly 抽出
- `ForecastEngine.predict(days=7)` が線形外挿 + 現実的範囲 (0-200%)
- `score_task()` が 5 軸スコア dict 返却
- `call_classifier()` が 5.4-mini JSON 応答を effort に変換
- `map_to_effort(score=5)` → "medium"
- `load_rules()` が YAML から 3+ ルール読み込み
- `suggest_model(remaining={"spark":0.05}, task_effort="medium")` → "gpt-5.4-mini"

---

## 3. 異常系

### 3.1 依存障害 (bats)

| ID | テスト | 期待結果 |
|----|--------|---------|
| T-ER-01 | ccusage 未インストール | JSONL フォールバック動作、非ゼロ % 返却 |
| T-ER-02 | `~/.claude/projects/` 空 | エラー表示 + 0% + exit 0 |
| T-ER-03 | `~/.codex/state.db` 未存在 | 警告 + "取得不可" + exit 0 |
| T-ER-04 | `state.db` ロック中 | 前回キャッシュ返却 (NFR-R2) |
| T-ER-05 | Codex CLI 不在で `--auto-thinking` | ルールベース fallback + warning |
| T-ER-06 | `model-fallback.yaml` 不正 YAML | デフォルトルールで fallback + warning |

### 3.2 不正入力

| ID | テスト | 期待結果 |
|----|--------|---------|
| T-ER-07 | `helix budget classify` (task 欠落) | exit 2 + "—task は必須" |
| T-ER-08 | `--size X` (範囲外) | exit 2 + "S/M/L のいずれか" |
| T-ER-09 | `--days -1` | exit 2 + "正の整数" |
| T-ER-10 | `--role unknown` | exit 2 + 有効ロール一覧表示 |

### 3.3 セキュリティ異常系 (重要)

| ID | テスト | 期待結果 |
|----|--------|---------|
| T-ER-11 | ログ出力に access_token が含まれない | `grep -iE "access_token|eyJ|Bearer" log` → 0 件 |
| T-ER-12 | classifier 送信 payload に path 情報なし | payload サニタイザ検証 |
| T-ER-13 | `.helix/budget/` が `.gitignore` に含まれる | `git check-ignore .helix/budget/foo.json` → exit 0 |
| T-ER-14 | YAML にコード実行パターン | yaml.safe_load でエラー |

### 3.4 マイグレーション異常系

| ID | テスト | 期待結果 |
|----|--------|---------|
| T-ER-15 | バックアップ失敗時 | exit 1, マイグレーション中止 |
| T-ER-16 | SQLite < 3.35 環境 | "DROP COLUMN 未サポート、backup 方式のみ" 警告 |
| T-ER-17 | 並列マイグレーション (lock 競合) | 2 本目は exit 1 + "migration in progress" |

---

## 4. 境界値

| ID | ケース | 期待結果 |
|----|-------|---------|
| T-BD-01 | 残量 = 20% ちょうど | 警告発火 (20% が閾値) |
| T-BD-02 | 残量 = 19.99% | 警告発火 |
| T-BD-03 | 残量 = 20.01% | 警告非発火 |
| T-BD-04 | 残量 = 0% | "枯渇" 表示 |
| T-BD-05 | 残量 = 100% | "未使用" 表示 |
| T-BD-06 | score = 3 (low/medium 境界) | effort=low |
| T-BD-07 | score = 4 | effort=medium |
| T-BD-08 | score = 7 (medium/high 境界) | effort=medium |
| T-BD-09 | score = 8 | effort=high |
| T-BD-10 | score = 12 (high/xhigh 境界) | effort=high |
| T-BD-11 | score = 13 | effort=xhigh |
| T-BD-12 | `--days 0` | エラー (正の整数) |
| T-BD-13 | `--days 366` | 警告 (精度低下) + 計算続行 |
| T-BD-14 | JSONL 1 行のみ | ccusage なしでも parse 可 |
| T-BD-15 | JSONL 100万行 | 5 秒以内完了 (NFR-P4 下限) |

---

## 5. 回帰範囲

### 5.1 既存 CLI の動作保証 (非破壊)

| 既存 CLI | 検証内容 | 実行方法 |
|---------|---------|---------|
| `helix init` | 新 hook 追加で既存 settings.json 壊さない | settings diff 検証 bats |
| `helix test` | 全 453 テスト PASS 継続 | G4 前に必ず実行 |
| `helix-codex --role se ...` (auto なし) | 従来通り動作 | T-NH-13 |
| `helix-skill use` (auto なし) | 従来通り動作 | bats |
| `helix gate G2/G3/G4/G6` | 動作継続 | 既存 gate tests |
| `helix sprint` | 動作継続 | 既存 sprint tests |
| `helix scrum verify` | 動作継続 | 手動 smoke |
| `helix log report` (既存) | 動作継続 + 新規 `report budget` 追加 | bats |
| `helix pr` | 動作継続 | manual |

### 5.2 データ互換性

- v5 skill_usage レコードは v6 で NULL 埋め、集計で COALESCE 処理
- `.helix/cache/` の既存 skill 推挙キャッシュは変更なし
- phase.yaml / gate-checks.yaml スキーマ変更なし

### 5.3 回帰テスト実行方針

```bash
# L4 実装中 (各スプリント .5)
~/ai-dev-kit-vscode/cli/helix test

# G4 ゲート前
~/ai-dev-kit-vscode/cli/helix gate G4

# G6 RC 前 (full regression)
~/ai-dev-kit-vscode/cli/helix test
~/ai-dev-kit-vscode/cli/helix gate G6
pytest cli/lib/tests/ -v
```

---

## 6. テスト自動化

### 6.1 bats テスト配置

```
cli/tests/
├── helix-budget-status.bats          (T-NH-01~08, T-ER-01~04)
├── helix-budget-classify.bats        (T-NH-05~06, T-BD-06~11)
├── helix-budget-simulate.bats        (T-NH-07)
├── helix-budget-hook.bats            (T-NH-09~11)
├── helix-budget-migration.bats       (T-NH-15~18, T-ER-15~17)
├── helix-codex-auto-thinking.bats    (T-NH-12~13)
├── helix-skill-auto-thinking.bats    (T-NH-14)
├── helix-budget-security.bats        (T-ER-11~14)
└── helix-budget-boundary.bats        (T-BD-*)
```

### 6.2 pytest 配置

```
cli/lib/tests/
├── test_budget.py                    (ClaudeBudget, CodexBudget, ForecastEngine)
├── test_effort_classifier.py         (score_task, call_classifier, map_to_effort)
├── test_model_fallback.py            (load_rules, suggest_model, apply_rule)
└── test_budget_cli.py                (integration)
```

### 6.3 モック戦略

| 対象 | モック方法 |
|-----|----------|
| ccusage | `PATH` 操作 + mock script で JSON 返却 |
| Codex CLI | `CODEX_BIN=/tmp/mock-codex` で置換 |
| state.db | テンポラリ SQLite でスキーマ作成 |
| `~/.claude/projects/` | `HOME=/tmp/test-home` で分離 |
| gpt-5.4-mini 応答 | fixture JSON (`cli/lib/tests/fixtures/classifier-*.json`) |
| ネットワーク | 絶対呼ばない (モック強制) |

### 6.4 CI 統合

- GitHub Actions で PR 時に `helix test` + pytest 実行
- カバレッジ 80% 以上 (NFR-M3)
- 失敗時は PR マージブロック

---

## 7. 合否基準

### 7.1 G4 (実装凍結)

- 新規 55 テスト全 PASS
- 既存 453 テスト全 PASS (回帰なし)
- AC-A / AC-B / AC-D / AC-E / AC-F の自動検証項目 pass

### 7.2 G6 (RC)

- AC-Q 全 PASS (セキュリティ含む)
- pytest カバレッジ 80% 以上
- security-audit agent レビュー Critical/High 指摘ゼロ

### 7.3 L8 (受入)

- AC-U (1 週間実運用) は G7 と連動判定
- 本ドキュメントの回帰範囲すべて検証完了

---

## 8. 未検証項目 (Known Gaps)

- 非公式 API (wham/usage) の opt-in 動作は手動テストのみ (自動化困難)
- プロダクションで 6 か月運用時の長期安定性 (観測上限学習の収束)
- SQLite 3.35 未満の旧環境 (現時点で対象外、警告のみ)

これらは L8 ミニレトロで次期改善キューに積む。
