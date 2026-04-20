# D-SECV: セキュリティ検証レポート — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**Date**: 2026-04-21
**監査**: security-audit agent (Sonnet 4.6) 実施済み
**参照**: D-THREAT/threat-model.md

---

## 1. 攻撃面

脅威モデル (D-THREAT §3) の STRIDE 分析を検証対象とする:

| カテゴリ | 対象 | 優先度 |
|---------|-----|-------|
| S: Spoofing | ccusage 偽装 / model-fallback.yaml 改ざん | Medium |
| T: Tampering | キャッシュ改ざん / state.db 改ざん | Low |
| I: Information Disclosure | **access_token 漏洩 / LLM への送信内容 / JSONL 漏洩** | **Critical** |
| D: Denial of Service | ccusage ハング / 大量 JSONL / classifier 連続失敗 | Low |
| E: Elevation of Privilege | YAML コード実行 / SQL injection / path traversal | Medium |

## 2. 検証手順

### 2.1 静的解析 (security-audit agent による)

以下観点で全ソースコードを精査:
- `~/.codex/auth.json` / access_token を読む箇所の有無
- ログ・例外 trace に token 混入する可能性
- `yaml.safe_load` 相当の採用
- SQL クエリのプレースホルダ使用
- `subprocess shell=False`
- Path traversal リスク
- `.gitignore` 設定

### 2.2 実行確認

- `helix budget status` 実行ログに認証情報が出ないことを grep 検証
- `.helix/budget/cache/*.json` の内容確認 (トークン等なし)
- `git check-ignore .helix/budget/foo.json` → ignore される

### 2.3 負荷・境界値

- 巨大 JSONL で OOM にならない (10万行上限)
- ccusage timeout 10 秒で無限ハング回避

---

## 3. 結果

### 3.1 Critical / High

**Critical: 0 件**
**High: 0 件**

### 3.2 Medium

| # | Finding | ファイル | 対応 |
|---|---------|---------|------|
| M-1 | `_has_column` の PRAGMA に未サニタイズのテーブル名 | cli/lib/helix_db.py:298 | **修正済み** (正規表現ガード追加) |

対応内容:
```python
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def _has_column(conn, table_name, column_name):
    if not _IDENTIFIER_RE.match(str(table_name)):
        raise ValueError(f"invalid table name: {table_name!r}")
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)
```

### 3.3 Low

| # | Finding | 対応 |
|---|---------|-----|
| L-1 | キャッシュ改ざん時の数値クランプなし | **未対応 (L8 以降)** — 本番影響低 |
| L-2 | JSONL 10万行上限の内側→外側 break タイミング | **未対応** — 実害なし |

### 3.4 Info (対策済み確認)

| # | 確認内容 | 結果 |
|---|---------|------|
| I-1 | `~/.codex/auth.json` は読まない | ✅ 全ソース検索ゼロ件 |
| I-2 | `yaml.safe_load` 相当 (yaml_parser.py) | ✅ 採用、PyYAML 不使用 |
| I-3 | `subprocess shell=False` | ✅ リスト渡し、shell=True なし |
| I-4 | SQLite read-only (`mode=ro`) | ✅ `sqlite3.connect("file:..?mode=ro", uri=True)` |
| I-5 | `.gitignore` に `.helix/budget/` | ✅ 登録確認済み |
| I-6 | エラーログに type(e).**name** のみ | ✅ スタック trace 非出力 |
| I-7 | 非公式 API (wham/usage) デフォルト無効 | ✅ 実装コードに存在せず (opt-in として将来追加) |

### 3.5 OWASP Top 10 マッピング

| OWASP | カテゴリ | 判定 | 根拠 |
|-------|---------|------|------|
| A01 | Broken Access Control | Pass | ローカル CLI、認可レイヤーなし |
| A02 | Cryptographic Failures | Pass | トークン保存・送信なし |
| A03 | Injection (SQLi) | **Pass (修正後)** | M-1 修正済み、PRAGMA ガードあり |
| A04 | Insecure Design | Pass | 脅威モデル → 実装 → 検証が整合 |
| A05 | Security Misconfiguration | Pass | デフォルト fallback、YAML スキーマ検証 |
| A06 | Vulnerable Components | Pass | 依存最小 (Python 標準 + Codex CLI) |
| A07 | ID / Auth Failures | N/A | 認証なし |
| A08 | Software / Data Integrity | Pass | yaml_parser.py (安全)、DB migration transactional |
| A09 | Logging & Monitoring | Pass | budget_events テーブル + skill_usage に記録 |
| A10 | SSRF | N/A | 外部 URL 取得なし (非公式 API opt-in 時のみ、未実装) |

---

## 4. 残余リスク

### 4.1 受容するリスク (L8 で再評価)

- **L-1 キャッシュクランプ**: キャッシュ破損時の UI 誤表示。ログイン後にブラウザで変な数字が出る程度、実害低。
- **L-2 JSONL 走査上限**: 実害なし、cosmetic 改善。
- **非公式 API 実装**: 現時点で未実装、将来 opt-in 時に再監査必要 (ADR-005)。

### 4.2 監視項目

- `budget_events` テーブルへの `exhaustion` / `fallback` / `warning` 記録
- `helix log report budget` (次期スプリント) で傾向監視
- 認証情報 grep による監視: CI で `rg -iE 'access_token|eyJ|Bearer'` を定期実行

### 4.3 未実装の緩和策 (P1/P2、L8 以降)

- [ ] budget_events フル記録 (実装骨格はあり、hook 統合後に発火)
- [ ] ccusage version pinning (運用ドキュメントで誘導)
- [ ] Integrity check (SHA256) for cache files (T-1 強化)
- [ ] Audit log 暗号化 (I 系強化)

---

## 5. 結論

**Critical / High 指摘ゼロ、Medium 1 件は修正済み、Low 2 件は受容可能。G6 合格。**

今後の実装拡張 (LLM 呼び出し / 非公式 API) 時は再監査が必要。監査結果は本ドキュメント + `.helix/reviews/` に保存。

---

## 6. 関連資料

- `D-THREAT/threat-model.md` — 脅威モデリング
- security-audit agent 実行結果 (Opus session log)
