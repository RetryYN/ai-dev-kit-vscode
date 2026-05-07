# D-HOOK-SPEC: Hook 仕様と doc-map トリガー優先度

> Status: Accepted
> Date: 2026-04-14
> Authors: TL

---

## 1. 目的

HELIX の Hook システム（Claude Code hooks + Git hooks + doc-map triggers）の仕様を明文化し、複数トリガーが同時にマッチした場合の優先度ルールを確定する。GAP-027 の解消を目的とする。

---

## 2. Hook 全体像

### 2.1 Hook 種別と発火タイミング

| Hook 種別 | 発火タイミング | 実装 | 遅延許容 |
|----------|-------------|------|---------|
| **SessionStart** | Claude Code セッション開始時 | `helix session-start` | < 5秒 |
| **PreToolUse(Write)** | Write ツール呼び出し直前 | `helix check-claudemd` | < 2秒 |
| **PreToolUse(Bash)** | Bash ツール呼び出し直前 | `cli/libexec/helix-pre-bash` | < 2秒 |
| **PostToolUse** | Edit/Write/MultiEdit ツール呼び出し直後 | `cli/libexec/helix-post-tool-use` → `helix hook` | < 10秒 |
| **Stop** | Claude Code セッション終了時 | `helix session-summary` | < 8秒 |
| **Git pre-commit** | `git commit` 実行直前 | `cli/templates/hooks/pre-commit` | < 30秒 |
| **Git commit-msg** | コミットメッセージ作成時 | `cli/templates/hooks/commit-msg` | < 2秒 |
| **Git post-merge** | `git merge` 完了後 | `cli/templates/hooks/post-merge` | < 5秒 |

### 2.2 Hook チェーン例（ファイル編集時）

```
Claude Code が Write ツール呼び出し
  ↓
PreToolUse(Write): helix check-claudemd     ← CLAUDE.md テンプレート強制
  ↓ (allowed)
ファイル書き込み完了
  ↓
PostToolUse: helix-post-tool-use      ← payload から変更ファイルを抽出
  ↓
helix hook                            ← doc-map トリガー判定
  ↓ emit: GATE_READY|G4|cli/helix-test
  ↓ emit: DESIGN_SYNC|docs/design/L2-cli-architecture.md|cli/helix-test
  ↓ (バックグラウンド): helix drift-check
  ↓
（編集継続、または commit へ）
  ↓
Git pre-commit: phase_guard チェック  ← フェーズ整合性
  ↓ (allowed)
Git commit-msg: Conventional Commits 検証
  ↓
コミット完了
```

### 2.3 Hook チェーン例（Bash 実行時）

```
Claude Code が Bash ツール呼び出し
  ↓
PreToolUse(Bash): helix-pre-bash      ← コマンド文字列を検査
  ↓
llm_guard.py                          ← raw LLM CLI を検出
  ↓ allowed: helix codex --plan-only / --approved、helix claude --dry-run 等の harness 経由
  ↓ blocked: codex exec / claude 等の HELIX discipline を迂回する実行
```

---

## 3. doc-map トリガー仕様

### 3.1 トリガー定義（doc-map.yaml）

```yaml
triggers:
  - pattern: "cli/helix-*"
    on_write: gate_ready
    gate: G4
  - pattern: "docs/design/**/*.md"
    on_write: design_sync
    design_ref: docs/design/L2-cli-architecture.md
  - pattern: "cli/lib/tests/**/*.py"
    on_write: coverage_check
  - pattern: "docs/adr/ADR-*.md"
    on_write: adr_index
```

### 3.2 on_write アクション種別

| アクション | 用途 | emit フォーマット |
|-----------|------|----------------|
| `gate_ready` | ゲート準備完了通知 | `GATE_READY|<gate>|<file>` |
| `design_sync` | 設計書同期チェック | `DESIGN_SYNC|<design_ref>|<file>` |
| `coverage_check` | カバレッジ再計測 | `COVERAGE_CHECK|<file>` |
| `adr_index` | ADR index 再生成 | `ADR_INDEX|<file>` |

### 3.3 マッチングアルゴリズム

現行実装（`cli/lib/doc_map_matcher.py`）:

```python
def _glob_match(file_path: str, pattern: str) -> bool:
    # * → [^/]* （1階層内ワイルドカード）
    # ** → .* （複数階層ワイルドカード）
    escaped = re.escape(pattern)
    escaped = escaped.replace(r"\*\*", ".*")
    escaped = escaped.replace(r"\*", "[^/]*")
    return bool(re.match(f"^{escaped}$", file_path))
```

---

## 4. 複数トリガーの優先度ルール（本 ADR で確定）

### 4.1 優先度原則

複数トリガーが同一ファイルにマッチした場合、以下の優先度で処理する:

**Priority 1: 特異性（Specificity）**
1. 完全一致（`cli/helix-test`）
2. 部分ワイルドカード（`cli/helix-*`）
3. 再帰ワイルドカード（`cli/**/*.py`）
4. フル再帰ワイルドカード（`**/*.md`）

**Priority 2: パターンの長さ（Length）**
- 同一特異性レベル内では、パターン文字列がより長いものを優先

**Priority 3: アクション優先度（Action Priority）**
1. `gate_ready`（ゲート発火は最優先）
2. `design_sync`（設計整合性）
3. `adr_index`（メタデータ更新）
4. `coverage_check`（メトリクス更新）

### 4.2 優先度適用の実例

`cli/helix-gate` が編集された場合:

```yaml
# マッチするトリガー3件
- pattern: "cli/helix-gate"           # 完全一致（Priority 1.1）
  on_write: gate_ready
  gate: G4
- pattern: "cli/helix-*"              # 部分ワイルドカード（Priority 1.2）
  on_write: design_sync
  design_ref: docs/design/L2-cli-architecture.md
- pattern: "**/*"                     # フル再帰（Priority 1.4）
  on_write: coverage_check
```

→ 優先度順に処理:
1. `GATE_READY|G4|cli/helix-gate` （Priority 1.1 + action gate_ready）
2. `DESIGN_SYNC|docs/design/L2-cli-architecture.md|cli/helix-gate` （Priority 1.2）
3. `COVERAGE_CHECK|cli/helix-gate` （Priority 1.4）

### 4.3 重複の扱い

- **完全同一のトリガー**: 最初のマッチのみ処理（doc-map.yaml 内で重複しないことが望ましい）
- **異なる gate / design_ref を持つ同パターン**: 全て処理（gate1, gate2 を別イベントとして emit）

---

## 5. 現行実装との差分

`doc_map_matcher.py` はマッチしたトリガーを **特異性 → パターン長 → アクション優先度 → 記述順** で emit する。
実装済みの優先度ルールは以下に対応する:

```python
def _emit_matches_prioritized(triggers, file_path):
    matched = []
    for trigger in triggers:
        pattern = trigger.get("pattern", "")
        if pattern and _glob_match(file_path, pattern):
            matched.append({
                "trigger": trigger,
                "specificity": _calc_specificity(pattern),
                "length": len(pattern),
                "action_priority": _action_priority(trigger.get("on_write", "")),
            })
    # 優先度順ソート
    matched.sort(key=lambda m: (-m["specificity"], -m["length"], m["action_priority"]))
    for m in matched:
        _emit_single(m["trigger"], file_path)
```

同一優先度のトリガーだけは YAML 記述順を維持する。

---

## 6. 観測・ログ

Hook 発火時に `helix.db` の `hook_events` テーブルへ記録:

```sql
CREATE TABLE hook_events (
    id INTEGER PRIMARY KEY,
    event_type TEXT,           -- "gate_ready", "design_sync", etc.
    file TEXT,
    result TEXT,               -- "ok", "warn", "blocked"
    created_at TEXT
);
```

`helix bench` / `helix session-summary` で可視化される。

---

## 7. 既知の制約・今後の課題

| 項目 | 内容 | 優先度 |
|------|------|------|
| 優先度ソート | 実装済み。特異性 → パターン長 → アクション優先度 → 記述順で処理 | — |
| パターン構文の制限 | glob 方式のみ、正規表現は未サポート | P3 |
| doc-map.yaml スキーマ検証 | 実装済み。不正な `on_write` / 必須キー欠落 / 完全重複は warning 出力 | — |
| 並列 hook 発火時の競合 | 同一ファイル編集が高速連続発火した場合の動作未検証 | P3 |
| raw LLM CLI 直叩き | PreToolUse(Bash) と PATH shim で `helix codex` / `helix claude --dry-run` へ誘導 | — |
| context budget 超過 | `helix context check` で AGENTS / CLAUDE / hook docs の肥大化を検出 | — |

---

## 8. References

- [ADR-009: Hook 戦略（doc-map トリガー中心）](../adr/ADR-009-hook-strategy.md)
- `cli/libexec/helix-post-tool-use` (PostToolUse payload wrapper)
- `cli/libexec/helix-pre-bash` (PreToolUse Bash guard)
- `cli/helix-hook` / `cli/libexec/helix-hook` (PostToolUse hook 本体)
- `cli/helix-check-claudemd` (PreToolUse hook)
- `cli/helix-context` / `cli/lib/context_guard.py` (context budget guard)
- `cli/lib/llm_guard.py` (raw LLM command guard)
- `cli/helix-session-start` / `helix-session-summary`
- `cli/lib/doc_map_matcher.py` (マッチングロジック)
- `cli/templates/doc-map.yaml` (トリガー定義テンプレート)
- `cli/templates/hooks/pre-commit` / `cli/templates/hooks/commit-msg` / `cli/templates/hooks/post-merge`
