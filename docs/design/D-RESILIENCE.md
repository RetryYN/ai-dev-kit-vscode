# D-RESILIENCE: Codex / Claude Code プラン利用前提のレジリエンス強化

> Status: Staged（plan-based harness v1 実装済み）
> Date: 2026-04-14
> Authors: TL

---

## 1. 目的

HELIX CLI の Codex 依存部分におけるリジリエンス（障害耐性）を強化する。GAP-038「Codex 依存のレジリエンス不足（リトライ2回のみ・代替モデルなし）」の解消を目的とする。

本設計で扱う Codex / Claude Code は、どちらも各ツールの契約プランとローカル CLI 利用を HELIX が `helix plan` / `helix task` / role / hook / handover で管理する前提とする。HELIX が外部プロバイダ呼び出しや認証情報を直接扱うフォールバックは本設計の対象外。

---

## 2. 現状分析

### 2.1 現状のリトライ機構

`helix codex` は以下のリトライ機構を持つ:

```bash
# cli/helix-codex L200 付近（推定）
for attempt in 1 2; do
    codex exec "$prompt" ...
    if [[ $? -eq 0 ]]; then break; fi
    if [[ $attempt -eq 1 ]]; then
        echo "[helix codex] リトライ ($attempt/2)..."
    fi
done
```

限界:
- 2回固定のリトライ（3回目以降はエラー終了）
- Codex CLI の指数バックオフなし
- 代替モデルへのフォールバックなし
- ネットワーク障害とモデルエラーを区別しない

### 2.2 観測される障害パターン

実運用で観測された障害:

| パターン | 頻度 | 現状の挙動 |
|---------|------|----------|
| ネットワーク一時切断 | 中 | リトライで回復することが多い |
| Codex CLI 側の rate limit / サービス混雑 | 中 | 2回リトライで失敗してタスク中断 |
| モデル非対応（gpt-5.x 新版問題） | 低 | 即エラー終了 |
| タイムアウト（長大タスク） | 中 | 現状は 300 秒固定、延長機能なし |
| 構文エラー（出力 YAML 不正） | 低 | エラー表示のみ、自動修復なし |

---

## 3. リジリエンス設計

### 3.1 多層フォールバック戦略

```
┌─────────────────────────┐
│ Primary: Codex 5.x      │  ← --role で指定された Codex モデル
│   (GPT-5.3/5.4/5.2)     │
└───────────┬─────────────┘
            ↓ 失敗
┌─────────────────────────┐
│ Layer 2: Codex 代替モデル │  ← 同じ Codex 系の別モデル
│   (5.3 Spark / 5.2)     │
└───────────┬─────────────┘
            ↓ 失敗
┌─────────────────────────┐
│ Layer 3: Claude Code CLI│  ← 契約プラン/CLI を HELIX harness で委譲
│   (plan/task fallback)  │
└───────────┬─────────────┘
            ↓ 失敗
┌─────────────────────────┐
│ Layer 4: エラー報告     │  ← ユーザーに状態共有、手動介入要請
└─────────────────────────┘
```

### 3.2 段階的リトライ

`cli/helix-codex` は Primary model の実行で以下の分類と backoff を適用する:

```python
timeout_exit_124 -> backoff 0s
network_exit_7_8_28 -> exponential backoff (1s, 2s, 4s ...)
other -> backoff 1s
```

`--max-retries` の上限は 10。Primary が失敗した場合は Layer 2 の Codex 代替モデルへ 1 回だけ進む。

### 3.3 フォールバック制御

`helix codex` は以下のオプションを実装済み:

```bash
helix codex --role pg --task "..." \
  --fallback-model gpt-5.3-codex \        # Layer 2 の代替モデル指定
  --fallback-provider claude-code \        # Layer 3 の Claude Code harness 指定
  --max-retries 3 \                        # 最大リトライ回数（デフォルト 2）
  --timeout 600                            # タイムアウト秒数（デフォルト 1800）
```

Layer 3 は `--fallback-provider claude-code` 指定時のみ有効になる。`helix claude` が Claude Code 用 prompt/task-file を生成し、`.helix/tasks/` に引き渡す。v1 は Claude Code を自動実行せず、HELIX は外部向けの直接呼び出しを行わない。

### 3.4 ロール別フォールバック許容

全ロールで同一戦略を取らず、ロール特性に応じてフォールバックを許可/禁止:

| ロール | Layer 2 フォールバック | Layer 3 (Claude Code CLI) フォールバック | 備考 |
|-------|---------------------|-----------------------------|------|
| tl | ✓ | ✗ | 設計判断は Codex 限定（品質優先） |
| se | ✓ | ✗ | 上級実装は Codex 限定 |
| pg | ✓ | ✓ | 通常実装は Claude Code 委譲候補 |
| fe | ✓ | ✓ | FE は Claude Code 委譲候補 |
| qa | ✓ | ✓ | テスト生成は Claude Code 委譲候補 |
| security | ✓ | ✗ | セキュリティ判断は Codex 限定 |
| dba | ✓ | ✓ | DB 実装は Claude Code 委譲候補 |
| devops | ✓ | ✓ | インフラ設定は Claude Code 委譲候補 |
| docs | ✓ | ✓ | ドキュメントは Claude Code 委譲候補 |
| research | ✓ | ✓ | 調査系は Claude Code 委譲候補 |
| legacy | ✓ | ✗ | レガシー分析は Codex 5.2 限定 |
| perf | ✓ | ✗ | 性能分析は Codex 限定 |

---

## 4. 実装状態

### Phase 1: 基盤

- `cli/helix-codex` に `--max-retries` / `--timeout` を実装済み
- `timeout` / `network` / `other` の分類とバックオフ計算を同 wrapper 内で実装済み
- `--max-retries` は 0-10 の整数に制限

### Phase 2: Layer 2 フォールバック

- `helix codex` に `--fallback-model` を実装済み
- `cli/config/models.yaml` の `default_fallback` を自動採用
- 許可モデルは `models.yaml` から検証

### Phase 3: Layer 3 フォールバック

- `cli/helix-claude` による Claude Code 用ローカル委譲 harness を実装済み
- `--task` / `--task-file` / `--plan-id` / `--handover` による plan/task 文脈の受け渡しを実装済み
- `helix codex --fallback-provider claude-code` は Codex 失敗時に `.helix/tasks/codex-fallback-*.claude.md` を生成
- Claude Code の自動実行と結果取込は v1 では未実施

### Phase 4: 観測・アラート

- `cost_log` に最終モデル・リトライ回数・exit code を記録
- フォールバック率の専用可視化と閾値アラートは今後の課題

---

## 5. 後方互換性

- `--max-retries` のデフォルトは 2
- Layer 2 は `models.yaml` の `default_fallback` を使う。明示 `--fallback-model` で上書き可能
- Layer 3 は opt-in（`--fallback-provider claude-code` 指定時のみ）

---

## 6. リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| フォールバック時に品質低下 | ロール別に厳格な許容設定、品質 ADR でガード |
| Claude Code 利用量増加 | 契約プラン範囲内の CLI 利用として扱い、HELIX は API key/env を管理しない |
| プロンプト非互換 | Codex と Claude Code で同じタスクが異なる出力になる可能性 → フォールバック時に警告表示 |
| リトライ無限ループ | max_retries 上限厳守、timeout での強制終了 |
| Claude Code CLI 利用不可 | Layer 4（エラー報告）で最終的には人間に委譲 |

---

## 7. 既知の制約・今後の課題

| 項目 | 内容 | 優先度 |
|------|------|------|
| GAP-038 残件 | retry/backoff・結果取込・品質評価は将来スプリント | P2（GAP-038 本体） |
| Claude Code harness | v1 は dry-run / prompt 生成中心。自動実行・結果取込は将来拡張 | P3 |
| フォールバック品質評価 | 実運用データ蓄積後に配分ロジック調整 | P3 |
| プロンプト翻訳 | Codex ↔ Claude Code の変換は v1 テンプレート整形まで | P3 |

---

## 8. References

- `cli/helix-codex` (Codex wrapper / retry / fallback 実装)
- `cli/helix-claude` (Claude Code 用 plan/task prompt harness)
- `cli/roles/*.conf` (`cli/roles/` 配下のロール設定)
- [ADR-002: Builder System Foundations](../adr/ADR-002-builder-system-foundations.md)
- [ADR-004: Bash-Python ハイブリッド](../adr/ADR-004-bash-python-hybrid.md)
- Codex CLI ドキュメント: ~/.codex/AGENTS.md
