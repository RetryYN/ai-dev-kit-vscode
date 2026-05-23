---
plan_id: PLAN-115
title: "PLAN-115: claude-brain pattern HELIX 独自実装 (UserPromptSubmit history 注入)"
layer: L4
kind: impl
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md   # from dependencies.parent
size: M
drive: be
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — SessionStart / UserPromptSubmit hook 実装 + transcript_summary.py"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・WebSearch evidence 検証・retention policy チェック"
  - role: qa
    slot_label: "QA — T4-001〜006 + secret guard テスト実装"
  - role: tl-advisor
    slot_label: "TL adversarial check — G4 凍結判定・secret/PII 設計 review"
generates:
  - artifact_path: .claude/hooks/sessionstart-history-injection.sh
    artifact_type: hook
  - artifact_path: cli/lib/transcript_summary.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_transcript_summary.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-115-claude-brain-pattern-helix-implementation.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-042-claude-brain-helix-adaptation-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-099
  requires:
    - PLAN-099
  blocks: []
related_adr:
  - ADR-042-claude-brain-helix-adaptation-decision
related_plans:
  - PLAN-099 (親 PLAN、Layer 4 定義)
  - PLAN-091 (frontmatter 語彙正本)
  - PLAN-081 (SessionStart hook 既存実装、共存)
test_design: docs/v2/L4-test-design/PLAN-115-unit-test-design.md (別 session 起票予定)
---

# PLAN-115: claude-brain pattern HELIX 独自実装

> **本 PLAN の位置付け**: PLAN-099 Layer 4 の子 PLAN。  
> `SessionStart(cleared|compacted) + UserPromptSubmit` で関連履歴を自動注入する実装を担当する。  
> TL v5 round 5 修正条件「HELIX 独自再実装が筋」を厳密遵守し、外部 OSS の全量キャプチャ手法は採用しない。

---

## 1. 目的

PLAN-099 §8 で設計した Layer 4 を実装する:

- `SessionStart(cleared|compacted)` 後に関連 PLAN / handover / memory feedback の bundle を自動注入し、context リセット後の再起動コストを最小化する
- `UserPromptSubmit` 時にキーワードマッチで関連 state を特定し、短い bundle (≤500 token) を additionalContext に追加する
- 全量 SQLite キャプチャ禁止・要約 state のみ保存・明示的 retention policy を実施する

---

## 2. 背景 (PLAN-099 Layer 4 子 PLAN)

PLAN-099 §8 が設計した claude-brain HELIX 独自再実装の実装フェーズ。

### 2.1 claude-brain 原典との差分

| 観点 | 原典 claude-brain | HELIX 独自再実装 (本 PLAN) |
|---|---|---|
| データ取得 | SQLite 全量キャプチャ | `transcript_path` 参照のみ |
| 保存形式 | raw 会話全量 | 要約 state のみ (raw 保存禁止) |
| retention | 設定なし (無限保存) | 7日 GC (設定可能) |
| secret 除外 | なし | grep guard で api_key / credential 等を除外 |
| 注入サイズ | 制限なし | ≤500 token (bundle 上限) |
| 保存先 | SQLite | `.helix/cache/prompt-bundle/<session-uuid>.md` |

### 2.2 TL v5 修正条件との整合

TL v5 round 5 修正条件 #5:

> 「claude-brain pattern: HELIX 独自再実装が筋。会話 SQLite 全量キャプチャは secret/PII/予算情報リスク → `transcript_path 参照 + 要約 state + 明示的 retention` 正本、UserPromptSubmit 注入は関連 PLAN/handover/memory feedback の短い bundle に制限」

---

## 3. 業界 standard 参照 (WebSearch 3 query 実施、PLAN-087 ガードレール遵守)

> PLAN-087 ガードレール: 設計 doc 新規作成時は WebSearch 3 query 以上が必須。  
> 本 PLAN は外部 OSS 採用判断 + 新 framework (HELIX 独自実装) を含む L2 大局判断を伴うため、WebSearch 必須。

| # | Query | Source URL | 参照意図 |
|---|---|---|---|
| Q1 | `claude-brain UserPromptSubmit history injection pattern 2026` | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.141) / claude-brain OSS README | Claude Code 2.1.141 で `transcript_path` が SessionStart hook に提供されることを確認。claude-brain は 6 Python hook で SQLite 全量キャプチャを実施するが、HELIX では secret/PII リスクから要約 state 独自実装を採用 |
| Q2 | `Claude Code SessionStart compacted cleared hook 2026` | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.139〜2.1.144) | SessionStart event に `session_type: cleared|compacted|new` が提供される仕様確認。`cleared` = /clear コマンド後、`compacted` = auto-compact 後。いずれも history 注入の発火点として適切 |
| Q3 | `AI prompt history context injection privacy retention pattern 2026` | https://owasp.org/www-project-top-10-for-large-language-model-applications/ (LLM06: Sensitive Information Disclosure) / https://arxiv.org/abs/2403.13722 (MemGPT / memory management 論文) | AI agent での history 保持における PII/secret 漏洩リスク (OWASP LLM06) と retention policy 設計パターン (MemGPT §4 の sliding window + summarization)。HELIX の「要約 state のみ保存 + 7日 GC + secret grep guard」は OWASP LLM06 対策と MemGPT 要約戦略を組み合わせた設計 |

---

## 4. L2 凍結 (ADR snapshot 候補)

本 PLAN は以下の L2 大局判断を含む:

1. **claude-brain 全量キャプチャ不採用 → HELIX 独自再実装の採用決定**
   - 根拠: secret/PII/予算情報リスク (OWASP LLM06)、TL v5 修正条件 #5
2. **transcript_path 参照 + 要約 state 方式の採用決定**
   - 根拠: Claude Code 公式 API (transcript_path) を使い、raw 会話保存を回避する

→ ADR-042-claude-brain-helix-adaptation-decision.md を本 PLAN と同時起票すること (PLAN-091 §7.1 ADR snapshot 必須化ルール準拠)。

---

## 5. 設計方針

### 5.1 SessionStart hook 設計

```bash
# .claude/hooks/sessionstart-history-injection.sh
# SessionStart event hook
# Input env: CLAUDE_SESSION_TYPE (cleared|compacted|new)
#            CLAUDE_TRANSCRIPT_PATH (optional)
# Output: stdout JSON {systemMessage: "<bundle>"}

BUNDLE_MAX_LINES=40  # ~500 token 相当

case "$CLAUDE_SESSION_TYPE" in
  cleared|compacted)
    # transcript_path から最新の要約を読む
    bundle=$(python3 cli/lib/transcript_summary.py \
      --transcript-path "$CLAUDE_TRANSCRIPT_PATH" \
      --mode bundle \
      --max-lines "$BUNDLE_MAX_LINES")
    echo "{\"systemMessage\": \"$bundle\"}"
    ;;
  new|*)
    # 新規セッションは注入なし
    exit 0
    ;;
esac
```

### 5.2 UserPromptSubmit hook 設計

```bash
# UserPromptSubmit event hook (既存 hook と共存)
# Input stdin: JSON {prompt: "<user input>"}
# Output: stdout JSON {additionalContext: "<bundle>"}

KEYWORDS="PLAN-[0-9]+|handover|carry|継続|続き|次のステップ"
prompt=$(jq -r '.prompt' < /dev/stdin)

if echo "$prompt" | grep -qE "$KEYWORDS"; then
  bundle=$(python3 cli/lib/transcript_summary.py \
    --mode context \
    --keywords "$prompt" \
    --max-lines 40)
  echo "{\"additionalContext\": \"$bundle\"}"
else
  exit 0
fi
```

### 5.3 transcript_summary.py 設計

```python
# cli/lib/transcript_summary.py
# 責務: 要約 state 生成 / bundle 生成 / retention GC / secret 除外

SENSITIVE_PATTERNS = [
    r"api_key\s*[:=]\s*\S+",
    r"credential\s*[:=]\s*\S+",
    r"password\s*[:=]\s*\S+",
    r"bearer_token\s*[:=]\s*\S+",
    r"pii_\w+",
]

RETENTION_DAYS = 7          # default、helix config で変更可能
MAX_BUNDLE_TOKENS = 500     # 注入 bundle の token 上限目安
BUNDLE_CACHE_DIR = ".helix/cache/prompt-bundle"

def generate_bundle(mode: str, transcript_path: str | None,
                    keywords: str | None, max_lines: int) -> str:
    """
    mode="bundle": SessionStart 用 (transcript から関連 PLAN/handover/memory を抽出)
    mode="context": UserPromptSubmit 用 (keyword で関連 state を検索)
    """
    ...

def purge_old_bundles(cache_dir: str, retention_days: int) -> int:
    """retention_days 経過した bundle cache を削除。削除件数を返す"""
    ...

def _is_sensitive(text: str) -> bool:
    """secret/PII 含有を正規表現で検出"""
    ...
```

---

## 6. 実装 Sprint

### Sprint .1: transcript_summary.py 実装

**担当**: se  
**scope**:
- `cli/lib/transcript_summary.py` 新規作成
  - `generate_bundle(mode, transcript_path, keywords, max_lines)` 実装
  - `purge_old_bundles(cache_dir, retention_days)` 実装
  - `_is_sensitive(text)` 正規表現 guard 実装 (SENSITIVE_PATTERNS 5 件)
  - `.helix/cache/prompt-bundle/` ディレクトリ管理
- `cli/lib/tests/test_transcript_summary.py` 新規作成
  - T4-001〜006 (PLAN-099 §11.2 参照) を実装
  - `fake_transcript` / `fake_sensitive_transcript` fixture

**Entry 条件**: PLAN-099 status=draft 確認済み  
**Exit 条件**: `python3 -m py_compile cli/lib/transcript_summary.py` PASS + pytest T4-001〜006 全 PASS

### Sprint .2: SessionStart hook + UserPromptSubmit hook 実装

**担当**: se  
**scope**:
- `.claude/hooks/sessionstart-history-injection.sh` 新規作成
  - `CLAUDE_SESSION_TYPE` 判定 (cleared|compacted → bundle 注入、new → skip)
  - `transcript_summary.py --mode bundle` 呼び出し
  - 既存 `sessionstart-harness-summary.sh` との共存確認
- UserPromptSubmit hook 実装 (既存 hook に追記 or 別 hook)
  - keyword 検出 → `transcript_summary.py --mode context` 呼び出し
- `.claude/settings.json` への hook 登録
- `bash -n` + `shellcheck` PASS

**Entry 条件**: Sprint .1 完遂 (test_transcript_summary.py 全 PASS)  
**Exit 条件**: hook 登録後の smoke test PASS (T4-001/T4-002 手動確認)

### Sprint .3: retention policy + GC + pmo-sonnet review

**担当**: se + pmo-sonnet  
**scope**:
- retention GC の cron / 定期実行設定 (SessionStart 時に purge_old_bundles を呼ぶ)
- `helix config set prompt_bundle_retention_days <N>` 対応 (optional、helix config 既存 CLI に委ねる)
- pmo-sonnet で設計整合確認 (§5 設計 ↔ 実装一致、secret guard 動作確認)
- tl-advisor adversarial check (secret/PII 設計の妥当性、G4 凍結判定)
- V-model 4 artifact trace 確立
  - テスト設計 doc 起票 (docs/v2/L4-test-design/PLAN-115-unit-test-design.md)

**Entry 条件**: Sprint .2 完遂 (hook smoke test PASS)  
**Exit 条件**: 全回帰 PASS + pmo-sonnet review 承認 + tl-advisor G4 passed

---

## 7. DoD (Definition of Done)

- [ ] `cli/lib/transcript_summary.py` 実装済み (generate_bundle / purge_old_bundles / _is_sensitive)
- [ ] `cli/lib/tests/test_transcript_summary.py` で T4-001〜T4-006 全 PASS
  - T4-001: SessionStart cleared → bundle 注入 (≤500 token)
  - T4-002: SessionStart compacted → bundle 注入 (≤500 token)
  - T4-003: SessionStart new → bundle 注入なし
  - T4-004: sensitive_fields 含む transcript → 除外後に要約
  - T4-005: retention 7日 経過 → purge
  - T4-006: UserPromptSubmit で keyword match → top-5 注入
- [ ] `.claude/hooks/sessionstart-history-injection.sh` 実装済み + settings.json 登録済み
- [ ] 既存 hook (sessionstart-harness-summary.sh) とのデグレなし確認
- [ ] `bash -n` + `shellcheck` PASS
- [ ] `python3 -m py_compile cli/lib/transcript_summary.py` PASS
- [ ] 全回帰 PASS (`helix test`)
- [ ] ADR-042 起票済み + 双方向 reference 確立
- [ ] pmo-sonnet review 承認
- [ ] tl-advisor G4 passed (secret/PII 設計確認)

---

## 8. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-115-claude-brain-pattern-helix-implementation.md |
| ② 実装コード | 未着手 (Sprint .1-.2) | cli/lib/transcript_summary.py / .claude/hooks/sessionstart-history-injection.sh |
| ③ テスト設計 | 未起票 (Sprint .3) | docs/v2/L4-test-design/PLAN-115-unit-test-design.md |
| ④ テストコード | 未着手 (Sprint .1) | cli/lib/tests/test_transcript_summary.py |

双方向 reference:
- 本 PLAN → ADR-042: `related_adr: [ADR-042-claude-brain-helix-adaptation-decision]`
- ADR-042 → 本 PLAN: `Related: PLAN-115 (実装 tree)`
- 本 PLAN → PLAN-099: `dependencies.parent: PLAN-099`
- PLAN-099 §8 → 本 PLAN: PLAN-115 が Layer 4 実装担当と明記 (別 session で更新予定)
- 実装コード → 本 PLAN: docstring に `# 契約: PLAN-115 §5 設計方針` を明示 (実装時)

---

## 9. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-099 (親 PLAN、Layer 4 設計) | docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md |
| ADR-042 (本 PLAN の L2 snapshot、candidate) | docs/adr/ADR-042-claude-brain-helix-adaptation-decision.md |
| PLAN-091 (frontmatter 語彙正本) | docs/plans/PLAN-091-v5-framework-core.md |
| PLAN-081 (SessionStart 既存 hook、共存) | docs/plans/PLAN-081-stop-hook-auto-handover.md |
| OWASP LLM06 (secret 漏洩リスク参照) | https://owasp.org/www-project-top-10-for-large-language-model-applications/ |
| PLAN-087 (WebSearch ガードレール) | docs/plans/PLAN-087-design-doc-web-search-guardrail.md |
