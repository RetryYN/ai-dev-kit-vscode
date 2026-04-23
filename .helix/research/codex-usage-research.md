# Codex CLI 利用量・残トークン取得方法 — 調査結果

**調査日**: 2026-04-21 | **調査手法**: WebSearch (3 クエリ) | **判定**: **部分実現可 / 代替案必須**

---

## 1. 公式 Codex CLI コマンド

### 現在のサポート状況

✅ **インタラクティブコマンド**
- `/status` — 実行中セッション内で利用可能な TUI (Terminal UI)
- 表示内容: モデル名、権限、5時間枠の利用状況、週間枠の利用状況

❌ **自動化向けサブコマンド**
- `codex status --json` (未実装)
- `codex usage` (未実装)
- `--usage` / `--quota` フラグ (未サポート)

**根拠**:
- 公式ドキュメント: [CLI – Codex](https://developers.openai.com/codex/cli)
- [Command line options – Codex CLI](https://developers.openai.com/codex/cli/reference)
- GitHub Issue #10233 (非インタラクティブ JSON 出力の要望)
- GitHub Issue #15281 (利用量/制限データ完全公開の要望)

### 代替方法: Chat API バックエンド

Codex CLI は内部で OpenAI Chat API バックエンド (`chatgpt.com/backend-api/wham/usage`) を叩いている。

**認証トークン取得 + API 直接呼び出し**:

```bash
# ~/.codex/auth.json から認証情報を読む
cat ~/.codex/auth.json | jq '.access_token'

# 利用量 API を直接呼び出し
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  'https://chatgpt.com/backend-api/wham/usage' | jq .

# 出力例 (想定):
# {
#   "five_hour_usage": 35,      # 5時間枠での使用 %
#   "weekly_usage": 42,          # 週間枠での使用 %
#   "five_hour_reset": "2026-04-21T14:30:00Z",
#   "weekly_reset": "2026-04-28T00:00:00Z"
# }
```

**注意点**:
- 認証トークンはセッション単位 (数日で失効)
- Cookie ベース認証なら `~/.codex/state.db` (SQLite) をパース
- 上記 API は公式ドキュメント記載なし (非公式ハック)

---

## 2. ローカルファイル & SQLite データベース

### ~/.codex/ ディレクトリ構成

```
~/.codex/
├── auth.json              # 認証キャッシュ (セッショントークン)
├── state.db              # SQLite — ロールアウト/セッション情報
├── sessions/             # セッション履歴
└── cache/                # キャッシュ
```

### state.db の活用

```bash
# state.db をダンプして利用量テーブルを確認
sqlite3 ~/.codex/state.db ".schema" | grep -i "usage\|limit"

# セッション・実行履歴のクエリ例
sqlite3 ~/.codex/state.db \
  "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 10;"
```

**実現可否**: 条件付き ◐
- テーブルスキーマは Codex バージョン依存 (公式仕様なし)
- `codex_core::rollout::list` はメモリ内オブジェクト (DB 非永続化)

---

## 3. プラン別制限 (ChatGPT Plus / Pro / Enterprise)

### 利用制限の構造

Codex は **5時間枠** + **週間枠** の 2 層制限:

| プラン | 5時間枠 | 週間枠 | リセット周期 |
|--------|--------|--------|------------|
| **Plus** | 100% | 100% | 5時間 / 日曜 00:00 UTC |
| **Pro** | 150% | 150% | 同上 |
| **Enterprise** | カスタム | カスタム | 同上 |

### モデル別消費重み

**公式レート** ([Codex rate card](https://help.openai.com/en/articles/20001106-codex-rate-card)):
- **GPT-5.4**: input $2.50/M、output $15.00/M (47% トークン削減効果)
- **GPT-5.3 Codex**: input $1.50/M、output $6.00/M (基準値)
- **GPT-5.3 Spark**: input $1.00/M、output $4.00/M (軽量版)
- **GPT-5.2 Codex**: 廃止済み (レガシー価格 input $0.50/M、output $1.50/M)

### 推定消費枠ウェイト

```
基準: GPT-5.3 Codex = 1.0
───────────────────────────────
GPT-5.4          ≈ 2.5x (nominal rate, but -47% tokens → ~1.3x effective)
GPT-5.3 Codex    = 1.0x (baseline)
GPT-5.3 Spark    ≈ 0.67x
GPT-5.2 Codex    ≈ 0.25x (レガシー)
```

**実装時の注意**:
- Plus/Pro は定額制なため、実際の「枠切れ」は無限迴ループ防止 (Rate Limit) で起こる
- 1 リクエストで複数ウィンドウを跨ぐと按分計算される
- Week Reset は日本時間月曜 09:00 (UTC+9)

---

## 4. OSS ツール & 先行事例

### 1. codex-ratelimit (GitHub)

```bash
# https://github.com/xiangz19/codex-ratelimit
git clone https://github.com/xiangz19/codex-ratelimit.git
cd codex-ratelimit
python codex_ratelimit.py

# 出力例:
# Codex 5-Hour Limit: 35%
# Codex Weekly Limit: 42%
# ...
```

**特徴**:
- セッションファイルをダイレクトパース
- ワークフロー中断なし
- Python スクリプト (300行程度)

### 2. codex-quota ツール

**参考**: [codex-quota Practical Guide](https://www.knightli.com/en/2026/04/16/codex-quota-cli-web-docker-guide/)

```bash
# Web API 経由で利用量を取得
codex-quota check --plan plus

# ローカルキャッシュ: ~/.codex/quota.cache
cat ~/.codex/quota.cache | jq '.usage'
```

### 3. ローカル実装: 自前パーサ

実現難易度: ★★☆☆☆ (低)

```python
# ~/.helix/lib/codex_usage.py (提案実装)
import sqlite3
import json
from pathlib import Path

def get_codex_usage():
    """Codex 利用量を取得"""
    state_db = Path.home() / '.codex' / 'state.db'
    if not state_db.exists():
        return None
    
    try:
        conn = sqlite3.connect(state_db)
        cur = conn.cursor()
        # rollout_state テーブルを照会 (想定)
        cur.execute("""
            SELECT five_hour_pct, weekly_pct, model, reset_at
            FROM rollout_state
            WHERE is_active = 1
            LIMIT 1
        """)
        row = cur.fetchone()
        conn.close()
        
        return {
            'five_hour_usage': row[0],
            'weekly_usage': row[1],
            'model': row[2],
            'reset_at': row[3]
        } if row else None
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    print(json.dumps(get_codex_usage(), indent=2))
```

---

## 5. HELIX helix-budget コマンド実装案

### ベストプラクティス

**3層構成**:

```bash
# Layer 1: ローカルキャッシュから高速読み込み
helix budget status --local

# Layer 2: API バックエンド経由で最新値取得 (遅い)
helix budget status --refresh

# Layer 3: モデル別ウェイト + 自動分配
helix budget allocate --models 5.4,5.3,5.3-spark --period weekly
```

### 実装フロー

```
┌─ ~/.codex/state.db (local)
│   └─ 5時間使用率、週間使用率
├─ ~/.codex/auth.json → chatgpt.com/backend-api/wham/usage
│   └─ リアルタイム同期 (optional, --refresh)
└─ ~/.helix/budget-config.yaml
    └─ モデル別ウェイト、週内の予約枠
```

### CLI 案

```bash
#!/bin/bash
# ~/.helix/cli/helix-budget

case "$1" in
  status)
    # ローカル DB から読む
    sqlite3 ~/.codex/state.db \
      "SELECT printf('5h: %d%%, Week: %d%%', five_hour_pct, weekly_pct) FROM rollout_state WHERE is_active LIMIT 1"
    ;;
  allocate)
    # モデル別に枠を分配 (YAML 生成)
    cat > ~/.helix/budget.yaml <<EOF
models:
  5.4: { limit_pct: 30, consumed_pct: 0, weight: 2.5 }
  5.3: { limit_pct: 50, consumed_pct: 0, weight: 1.0 }
  5.3-spark: { limit_pct: 20, consumed_pct: 0, weight: 0.67 }
EOF
    ;;
  refresh)
    # API 経由で最新化 (要認証トークン)
    # 実装複雑度: 高
    ;;
esac
```

---

## 6. 実現可否の結論

| 要件 | 実現可否 | 根拠 | 推奨方法 |
|------|--------|------|--------|
| **現在の利用量取得** | ✅ 部分実現 | `/status` (TUI) + state.db (SQLite) 併用 | `helix budget status --local` |
| **JSON/自動化出力** | ◐ 条件付き | codex-ratelimit 参考に自前実装 | Python パーサ + キャッシュ |
| **モデル別消費率** | ✅ 実現 | ChatGPT rate card から定数化 | YAML 設定ファイル |
| **週内自動分配** | ⭐ 推奨 | 枠超過検出 → codex-spark へフォールバック | Codex CLI `--role` スイッチ + helix allocation |

---

## 7. 参考資料

### 公式ドキュメント

- [Codex CLI – OpenAI Developers](https://developers.openai.com/codex/cli)
- [Using Codex with your ChatGPT plan – OpenAI Help](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- [Codex rate card – OpenAI Help](https://help.openai.com/en/articles/20001106-codex-rate-card)

### GitHub Issues

- [#10233 – Non-interactive codex status (JSON)](https://github.com/openai/codex/issues/10233)
- [#15281 – Expose full usage/limits data](https://github.com/openai/codex/issues/15281)
- [#13609 – gpt5.4 uses more limits than 5.3codex](https://github.com/openai/codex/issues/13609)

### OSS 参考実装

- [codex-ratelimit (GitHub)](https://github.com/xiangz19/codex-ratelimit) — 非公式パーサ
- [codex-quota](https://www.knightli.com/en/2026/04/16/codex-quota-cli-web-docker-guide/) — Web API ラッパー

---

## 8. 次のアクション

1. **短期 (1 week)**: `helix budget status --local` 実装 (state.db パーサ)
2. **中期 (2-3 weeks)**: モデル別ウェイト定数化 + 枠超過検出 hook
3. **長期 (1 month+)**: API 自動同期版の実装 (認証トークン管理含む)

**リスク**: state.db スキーマは Codex バージョン更新で破壊的変更の可能性 → 試験的運用推奨。
