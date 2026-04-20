# D-THREAT: 脅威モデル — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**Layer**: L2 設計 (G2 脅威モデリング)

---

## 1. 資産 (守るべき対象)

| ID | 資産 | 所在 | 影響度 |
|----|------|------|-------|
| A-1 | Claude/OpenAI の認証情報 | `~/.claude/`, `~/.codex/auth.json` | Critical (漏洩でアカウント乗っ取り) |
| A-2 | セッション履歴 (ユーザーの会話内容) | `~/.claude/projects/*.jsonl`, `~/.codex/sessions/` | High (プライバシー) |
| A-3 | 残量・消費データ | `.helix/budget/cache/`, `skill_usage` テーブル | Low (プライベートな開発情報) |
| A-4 | 降格ルール設定 | `cli/config/model-fallback.yaml`, `~/.config/helix/` | Low (非機微) |
| A-5 | タスク説明テキスト | classifier への LLM リクエスト | Medium (機密プロジェクトの場合) |

---

## 2. 信頼境界

```
┌──────────────────────────────────────────────┐
│ ユーザーのローカル PC (信頼境界 ①)          │
│                                              │
│ ┌──────────────────────────────────┐        │
│ │ HELIX CLI プロセス (信頼境界 ②)   │        │
│ │                                  │        │
│ │ - cli/helix-budget               │        │
│ │ - cli/lib/*.py                   │        │
│ └──────────────────────────────────┘        │
│                                              │
│ [read-only] ~/.claude/projects/*.jsonl      │
│ [read-only] ~/.codex/state.db               │
│ [NEVER read] ~/.codex/auth.json (access_token) │
│ [read-write] .helix/budget/                  │
└──────────────────────────────────────────────┘
                    ↓ 境界越え (task text のみ)
┌──────────────────────────────────────────────┐
│ Codex CLI → OpenAI API (信頼境界 ③)         │
│   gpt-5.4-mini classifier 呼び出し           │
└──────────────────────────────────────────────┘
                    ↓ opt-in のみ (ADR-005)
┌──────────────────────────────────────────────┐
│ chatgpt.com/backend-api/wham/usage (境界 ④) │
│   非公式 API、デフォルト無効                 │
└──────────────────────────────────────────────┘
```

---

## 3. 攻撃面 (STRIDE)

### S: Spoofing (なりすまし)

| # | 攻撃 | 対策 |
|---|------|------|
| S-1 | 悪意ある ccusage 代替をインストールして消費偽装 | npm 署名確認、`ccusage` version pin (L6 で固定) |
| S-2 | `model-fallback.yaml` を改変して不適切モデル誘導 | スキーマ検証、壊れたら警告 + デフォルト fallback (ADR-004) |

### T: Tampering (改ざん)

| # | 攻撃 | 対策 |
|---|------|------|
| T-1 | `.helix/budget/cache/*.json` を改ざんして偽残量表示 | キャッシュハッシュ、`--no-cache` で強制更新 |
| T-2 | `observed-limits.json` を偽装して上限大きく見せる | 異常値 (> 100%, 負数) は破棄 + 再学習 |
| T-3 | `state.db` を他プロセスが書き換え | read-only open + ロック中は前回キャッシュ利用 (NFR-R2) |

### R: Repudiation (否認)

| # | 攻撃 | 対策 |
|---|------|------|
| R-1 | 降格提案に従ったが結果が悪かった責任所在不明 | `budget_events` テーブルに全降格イベントを記録 (NFR-O2) |
| R-2 | 枯渇予測のミスマッチで開発停止 | 予測精度を `observed-limits.json` と対比可能に |

### I: Information Disclosure (情報漏洩) — **最重要**

| # | 攻撃 | 対策 |
|---|------|------|
| I-1 | **access_token をログ出力してしまう** | サニタイザ (cli/lib/sanitizer.py) で `access_token`, `sess_`, `eyJ...` パターン除去 (NFR-S1) |
| I-2 | classifier への LLM 送信にパス名・API キー含まれる | payload サニタイザで `/home/`, `~/.env`, `API_KEY=` 除去 (NFR-S4) |
| I-3 | `.helix/budget/` が git commit される | `.gitignore` 強制追加 + helix-init で検証 (NFR-S3) |
| I-4 | `~/.claude/projects/*.jsonl` のプライベート会話が classifier 経由で外部送信 | 送信は `task` パラメータのみ、task 以外は読まない |
| I-5 | 非公式 API (wham/usage) 呼び出し時の token 漏洩 | opt-in + HTTPS + ログ禁止 + エラー trace でも token を出さない (ADR-005) |

### D: Denial of Service

| # | 攻撃 | 対策 |
|---|------|------|
| D-1 | ccusage / state.db が大量データで遅い | timeout 10 秒で skip、キャッシュ優先 (NFR-P4) |
| D-2 | classifier 呼び出しが連続失敗 → 実行ブロック | 3 回失敗でルールベースに fallback (NFR-R3) |
| D-3 | SessionStart hook が重くてセッション起動遅延 | 1.5 秒タイムアウト、exit 0 固定 (NFR-P3 / FR-C2) |

### E: Elevation of Privilege

| # | 攻撃 | 対策 |
|---|------|------|
| E-1 | YAML 読み込みで任意コード実行 | `yaml.safe_load` のみ使用 (既存 HELIX の pyyaml 不使用方針と整合) |
| E-2 | SQL インジェクション (state.db パラメータ) | プレースホルダ使用、ユーザー入力はクエリに埋め込まない |
| E-3 | ファイルパス traversal | `Path.resolve()` + プロジェクトルート配下チェック |

---

## 4. 緩和策 (優先度順)

### P0 (実装必須 / G4 までに)

- [ ] サニタイザ `cli/lib/sanitizer.py` 実装 (I-1, I-2 対策)
- [ ] `.gitignore` への `.helix/budget/` 強制追加 (helix-init で検証)
- [ ] `yaml.safe_load` + スキーマ検証 (E-1, S-2 対策)
- [ ] SQLite read-only open + プレースホルダ (E-2 対策)
- [ ] SessionStart hook の 1.5 秒タイムアウト (D-3 対策)
- [ ] 非公式 API は opt-in 必須 (ADR-005 整合)

### P1 (推奨 / G6 までに)

- [ ] `budget_events` ロギング (R-1, R-2 対策)
- [ ] classifier 失敗時のルールベース fallback (D-2 対策)
- [ ] 観測上限の異常値破棄 (T-2 対策)
- [ ] ccusage version pinning (S-1 対策)

### P2 (将来検討)

- [ ] Integrity check (SHA256) for cache files (T-1)
- [ ] Audit log 暗号化 (I-3 強化)

---

## 5. セキュリティレビュー依頼事項 (G2)

- [ ] security-audit agent に本ドキュメントをレビューしてもらう (G2 ミニレトロで発火)
- [ ] I-1 〜 I-5 の緩和策が十分か検証
- [ ] 脅威のカバレッジ (追加攻撃面の洗い出し)

## 6. 参考

- OWASP STRIDE: https://owasp.org/www-community/Threat_Modeling_Process
- HELIX security skill: `skills/common/security/SKILL.md`
- `skills/workflow/threat-model/SKILL.md`
