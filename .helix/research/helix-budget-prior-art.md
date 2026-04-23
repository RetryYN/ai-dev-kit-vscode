# helix-budget + auto-thinking 先行事例調査

**調査日**: 2026-04-21
**調査手法**: Codex (gpt-5.2-codex / research role) + WebSearch (9 クエリ)
**判定**: **HELIX 固有の統合領域は空白 / 構成要素は流用可**

---

## A. 残量管理 / 使用量追跡 OSS (Claude Code / Codex 向け)

| リポジトリ | URL | star | 機能範囲 | HELIX との差分 | 流用可否 |
|-----------|-----|------|---------|----------------|---------|
| **ryoppippi/ccusage** | https://github.com/ryoppippi/ccusage | — | JSONL parse で消費取得、CLI 出力 | ✅ HELIX 採用確定 (NFR-R1) | **subprocess 呼び出しで活用** |
| **xiangz19/codex-ratelimit** | https://github.com/xiangz19/codex-ratelimit | — | state.db から 5h window 解析 | ✅ HELIX 採用確定 | **logic 移植 or fork** |
| **phuryn/cc-usage-tracker** | (参考) | 71 | Claude Code 使用量ダッシュボード (Web UI) | 目的がダッシュボード寄り、CLI 統合なし | 参考のみ |
| **anthropic-insider/TokenTracker** | (参考) | 3 | トークン使用量の可視化 | star 少、継続性不明 | 参考のみ |
| **cc-statistics** | (参考) | 219 | Claude Code 統計 + predictor | **予測機能あり** — HELIX の枯渇予測の参考 | algorithm 参照 |
| **goccc** | (参考) | — | Go 製 ccusage 風 CLI | 機能的に ccusage と重複 | skip |
| **opencode-bar** | (参考) | — | status bar 表示系 | VS Code 寄り | skip |
| **cnighswonger/claude-code-cache-fix** | https://github.com/cnighswonger/claude-code-cache-fix | — | プロンプトキャッシュバグ対処 | 目的違い | skip |

**A 結論**: 使用量「取得 + 可視化」までは OSS 充実。`ccusage` + `codex-ratelimit` の組み合わせで HELIX は十分。自作は不要。

---

## B. タスク難度 → effort / model routing OSS

| リポジトリ | URL | star | 機能範囲 | HELIX との差分 | 流用可否 |
|-----------|-----|------|---------|----------------|---------|
| **LM-SYS/RouteLLM** | https://github.com/lm-sys/RouteLLM | ~2.4k | LLM コストベースルーティング (weak vs strong モデル) | **モデル2択の強弱分岐まで**、effort (thinking budget) 制御なし | アルゴリズム参照 |
| **BerriAI/litellm** | https://github.com/BerriAI/litellm | 多数 | LLM プロキシ、budget、routing、fallback | **プロキシサーバ前提** — CLI ネイティブ統合と路線違い | design 参照のみ |
| **LLMRouter** (汎用名) | — | ~1k | 複数モデル振り分け | 雑 routing、effort 連動なし | skip |
| **vllm-project/semantic-router** | — | — | 意味的タスク分類ベースのルーティング | **semantic 分類**で近い発想、LLM-as-classifier パターン | **概念流用**: gpt-5.4-mini classifier の方針 |
| **Portkey AI gateway** | — | — | マルチモデルゲートウェイ | プロキシ路線 | skip |

**B 結論**: 「タスク難度 → thinking/effort level」を**自動判定**する OSS は存在しない (2026-04 時点)。
- コストベース強弱ルーティング (RouteLLM) は近いが、同一モデル内の reasoning effort 調整という HELIX の軸と違う
- vllm semantic-router のパターン (LLM-as-classifier) を採用するのは妥当

---

## C. 統合系 (budget × routing × hook)

| リポジトリ | URL | star | 機能範囲 | HELIX との差分 | 流用可否 |
|-----------|-----|------|---------|----------------|---------|
| **LiteLLM** (再掲) | — | 多数 | budget 強制 + fallback + routing | ゲートウェイサーバ前提、CLI hook なし | 設計パターン参照 |
| **Routerly** | — | 不明 | budget enforcement LLM gateway | 情報少・継続性不明 | skip |
| **NadirClaw** 系 gateway | — | — | Claude 専用ゲートウェイ | ゲートウェイ前提、CLI ネイティブと路線違い | skip |
| **OpenRouter** | — | — | SaaS (OSS 化部分のみ) | SaaS 寄り、Max プラン活用不可 | skip |

**C 結論**: 「Claude Code / Codex CLI の hook に統合して、消費予測 + タスク難度 + モデル降格を一気通貫に扱う」という HELIX のスコープと一致する OSS は**存在しない**。

---

## 最終結論

### HELIX の独自性 (差別化)

1. **CLI ネイティブ統合**: ゲートウェイサーバを立てずに hook + subprocess で動く (Max プラン個人運用に最適)
2. **thinking/effort 軸の自動判定**: コスト (RouteLLM) や semantic (vllm) でなく、**reasoning budget** を task 難度から推定
3. **HELIX ゲート統合**: `skill_usage` 蓄積 + G4/G6 で ミスマッチ率を可視化して自己学習
4. **Claude + Codex 両側統合**: 多くの OSS は片側のみ

### 流用方針

| 領域 | 採用 | 理由 |
|------|------|------|
| Claude 消費取得 | `ccusage` (subprocess) | 成熟・メンテ継続中 |
| Codex 消費取得 | `codex-ratelimit` ロジック + `state.db` 直接 | state.db スキーマ変更リスクは自前管理が安全 |
| 枯渇予測 | cc-statistics の predictor 発想参照 | algorithm のみ |
| Task classifier | 新規実装 (gpt-5.4-mini + 5 軸スコア) | 先行 OSS なし、独自設計が妥当 |
| Budget 強制 | LiteLLM 発想参照のみ | ゲートウェイ化は HELIX の路線と違う |

### 避けるべき重複

- ccusage を自作で再実装 → `ccusage` subprocess 呼び出しで十分
- codex-ratelimit を完全 fork → state.db クエリは HELIX 側で最小限持つ程度
- ダッシュボード重視 → 別案件 (project_helix_dashboard_idea) に分離済み

### HELIX が埋める「隙間」

```
既存 OSS (A): ccusage / codex-ratelimit — 消費取得
                          ↓
        [ここが空白]  消費 + 難度 + 降格の統合判断
                          ↓
既存 OSS (B): RouteLLM — コスト強弱の2択ルーティング
```

HELIX は **消費 × 難度 × HELIX ゲート** の 3 軸統合で隙間を埋める。

---

## 参考資料

- `.helix/research/codex-usage-research.md` — Codex 利用量取得調査
- project_helix_budget.md (memory)
- project_auto_thinking.md (memory)
- feedback_codex_model_selection.md (memory)

## 調査の限界

- Codex research は 9 クエリ実行後に一部 timeout、本レポートは収集済みデータから Opus が要約した
- star 数は WebSearch スニペットからの抽出で、一部は「—」(未確認) と記載
- 新規 OSS (2026-04 以降リリース) は捕捉できていない可能性あり
- 確定判定は L6 統合検証時に再調査する
