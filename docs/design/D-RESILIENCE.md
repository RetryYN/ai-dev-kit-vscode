# D-RESILIENCE: Codex 依存のレジリエンス強化

> Status: Draft（段階実装）
> Date: 2026-04-14
> Authors: TL

---

## 1. 目的

HELIX CLI の Codex 依存部分におけるリジリエンス（障害耐性）を強化する。GAP-038「Codex 依存のレジリエンス不足（リトライ2回のみ・代替モデルなし）」の解消を目的とする。

---

## 2. 現状分析

### 2.1 現状のリトライ機構

`helix-codex` は以下のリトライ機構を持つ:

```bash
# cli/helix-codex L200 付近（推定）
for attempt in 1 2; do
    codex exec "$prompt" ...
    if [[ $? -eq 0 ]]; then break; fi
    if [[ $attempt -eq 1 ]]; then
        echo "[helix-codex] リトライ ($attempt/2)..."
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
| OpenAI API 混雑（429/503） | 中 | 2回リトライで失敗してタスク中断 |
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
│ Layer 3: Claude Sonnet  │  ← Claude API 経由で別プロバイダ
│   (FE/ドキュメント限定)  │
└───────────┬─────────────┘
            ↓ 失敗
┌─────────────────────────┐
│ Layer 4: エラー報告     │  ← ユーザーに状態共有、手動介入要請
└─────────────────────────┘
```

### 3.2 段階的リトライ

各 Layer 内で以下のリトライ戦略を適用:

```python
# cli/lib/codex_resilience.py（新規実装案）
RETRY_CONFIG = {
    "network_error":       {"max_retries": 3, "backoff": "exponential"},  # 1s, 2s, 4s
    "rate_limit":          {"max_retries": 5, "backoff": "jittered"},     # 30s ± 10s
    "model_error":         {"max_retries": 0, "fallback": True},          # 即フォールバック
    "timeout":             {"max_retries": 1, "extend_timeout": 1.5},     # タイムアウトを1.5倍
    "syntax_error":        {"max_retries": 1, "self_correction": True},   # 自己修正プロンプト
}
```

### 3.3 フォールバック制御

`helix-codex` に以下のオプションを追加（提案）:

```bash
helix codex --role se --task "..." \
  --fallback-model gpt-5.2-codex \        # Layer 2 の代替モデル指定
  --fallback-provider claude-sonnet-4-6 \  # Layer 3 の代替プロバイダ指定
  --max-retries 3 \                        # 最大リトライ回数（デフォルト 2）
  --timeout 600                            # タイムアウト秒数（デフォルト 300）
```

### 3.4 ロール別フォールバック許容

全ロールで同一戦略を取らず、ロール特性に応じてフォールバックを許可/禁止:

| ロール | Layer 2 フォールバック | Layer 3 (Claude) フォールバック | 備考 |
|-------|---------------------|-----------------------------|------|
| tl | ✓ | ✗ | 設計判断は Codex 限定（品質優先） |
| se | ✓ | ✗ | 上級実装は Codex 限定 |
| pg | ✓ | ✓ | 通常実装は Claude 代替可 |
| fe | ✓ | ✓ | FE は元々 Claude Sonnet が主力 |
| qa | ✓ | ✓ | テスト生成は Claude 代替可 |
| security | ✓ | ✗ | セキュリティ判断は Codex 限定 |
| dba | ✓ | ✓ | DB 実装は Claude 代替可 |
| devops | ✓ | ✓ | インフラ設定は Claude 代替可 |
| docs | ✓ | ✓ | ドキュメントは Claude 向き |
| research | ✓ | ✓ | 調査系は Claude Haiku 代替可 |
| legacy | ✓ | ✗ | レガシー分析は Codex 5.2 限定 |
| perf | ✓ | ✗ | 性能分析は Codex 限定 |

---

## 4. 実装計画

### Phase 1: 基盤（1 Sprint）

- `cli/lib/codex_resilience.py` を新規作成
  - エラー分類関数（`classify_error()`）
  - リトライ戦略関数（`get_retry_strategy()`）
  - バックオフ計算（`calculate_backoff()`）
- `helix-codex` に `--max-retries` / `--timeout` オプション追加
- 既存のリトライロジックを `codex_resilience` 経由に変更

### Phase 2: Layer 2 フォールバック（1 Sprint）

- `helix-codex` に `--fallback-model` オプション追加
- ロール別設定を `cli/roles/*.conf` に追加:
  ```
  # cli/roles/pg.conf
  codex_model=gpt-5.3-codex-spark
  fallback_model=gpt-5.2-codex
  ```
- エラー分類に基づく自動フォールバック

### Phase 3: Layer 3 フォールバック（2-3 Sprint）

- Claude API クライアント実装（または既存 SDK 使用）
- `cli/lib/claude_fallback.py` 新規作成
- ロール別 Claude プロンプト変換ロジック
- `--fallback-provider` オプション追加

### Phase 4: 観測・アラート（1 Sprint）

- フォールバック発生時に `hook_events` へ記録
- `helix bench` でフォールバック率を可視化
- フォールバック率が閾値超え → `helix doctor` で警告

---

## 5. 後方互換性

- デフォルト挙動は現状維持（2回リトライ、フォールバックなし）
- 新オプションは opt-in（明示指定時のみ有効）
- 既存テストは変更不要

---

## 6. リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| フォールバック時に品質低下 | ロール別に厳格な許容設定、品質 ADR でガード |
| Claude API 追加コスト | 環境変数で Layer 3 有効化を制御（`HELIX_ENABLE_CLAUDE_FALLBACK=1`） |
| プロンプト非互換 | Codex と Claude で同じタスクが異なる出力になる可能性 → フォールバック時に警告表示 |
| リトライ無限ループ | max_retries 上限厳守、timeout での強制終了 |
| フォールバック先 API 障害 | Layer 4（エラー報告）で最終的には人間に委譲 |

---

## 7. 既知の制約・今後の課題

| 項目 | 内容 | 優先度 |
|------|------|------|
| Phase 1-2 未実装 | 設計のみ、実装は将来スプリント | P2（GAP-038 本体） |
| Claude API 統合 | Phase 3 は API キー管理等の運用作業も必要 | P3 |
| フォールバック品質評価 | 実運用データ蓄積後に配分ロジック調整 | P3 |
| プロンプト翻訳 | Codex ↔ Claude の自動変換機構は未実装 | P3 |

---

## 8. References

- `cli/helix-codex` (319行, 現状実装)
- `cli/roles/*.conf` (12ロール設定)
- [ADR-002: Builder System Foundations](../adr/ADR-002-builder-system-foundations.md)
- [ADR-004: Bash-Python ハイブリッド](../adr/ADR-004-bash-python-hybrid.md)
- Codex CLI ドキュメント: ~/.codex/AGENTS.md
