# ADR-009: Hook 戦略（doc-map トリガー中心）

> Status: Accepted
> Date: 2026-04-14
> Deciders: PM, TL

---

## Context

HELIX CLI は複数のフックポイントで自動検証・ガイド提示を行う:

- **Claude Code hook**: SessionStart, PreToolUse(Write), PostToolUse(Edit/Write), Stop
- **Git hook**: pre-commit, commit-msg, post-merge
- **doc-map トリガー**: ファイル編集時の設計整合チェック（PostToolUse 経由）

フック戦略の選択肢:

1. **全ファイル編集時に全チェック実行**（heavy check）: 確実だが遅い
2. **doc-map パターンマッチで条件付き発火**（light check）: 高速だが見落としリスク
3. **Git pre-commit でのみ厳格チェック**: commit 単位、開発中の即時フィードバックなし

開発中の即時フィードバックと CI 的な厳格チェックの両立が必要。

---

## Decision

**doc-map トリガー中心の階層的フック戦略** を採用する:

### 3層フック構造

| 層 | タイミング | チェック内容 | 遅延許容 |
|----|-----------|-------------|---------|
| **Layer 1: PostToolUse (advisory)** | ファイル編集直後 | doc-map マッチ → 設計ドキュメント存在確認、契約ドリフト検知（helix-drift-check） | < 10秒 |
| **Layer 2: pre-commit (enforce)** | コミット前 | フェーズガード、CLAUDE.md テンプレート準拠、契約整合 | < 30秒 |
| **Layer 3: helix-gate (full)** | ゲート通過時 | 成果物存在・静的パターン・AI検証 | < 数分 |

### doc-map の役割

`.helix/doc-map.yaml` がフック発火条件を定義する:

```yaml
triggers:
  - pattern: "cli/helix-*"
    on_write:
      - gate: G4
        design_ref: docs/design/L2-cli-architecture.md
  - pattern: "D-API/**/*.md"
    on_write:
      - gate: G3
        check: helix-drift-check
```

### 現在実装済みフック（2026-04-14時点）

**Claude Code hooks** (`~/.claude/settings.json`):
- SessionStart → `helix-session-start` (コンテキスト注入・セットアップチェック)
- PreToolUse(Write) → `helix-check-claudemd` (CLAUDE.md テンプレート強制)
- PostToolUse(Edit/Write) → `helix-hook` (doc-map トリガー、drift-check、advisory)
- Stop → `helix-session-summary` (セッションサマリ生成)

**Git hooks** (`cli/templates/pre-commit-hook` 等):
- pre-commit → フェーズガード確認、大きすぎるファイル警告
- commit-msg → Conventional Commits 形式検証
- post-merge → 依存関係更新の検出

### doc-map 優先度（複数マッチ時）

複数トリガーが同時にマッチした場合の優先度（GAP-027 で明文化予定）:

1. 完全一致 > ワイルドカード一致
2. より長いパターン > 短いパターン
3. `on_write` 直接ゲート指定 > `advisory` のみ

---

## Alternatives

### A1: 全ファイル編集時に全チェック実行

- 利点: 見落としが絶対にない
- 欠点: 編集ごとに数秒〜数十秒の遅延、開発体験が悪化、AI エージェントのレスポンスが遅くなる

### A2: Git pre-commit でのみ厳格チェック

- 利点: 開発中は高速、commit 時に確実にチェック
- 欠点: AI エージェントが複数ファイルを編集して commit するまで問題に気づかない、修正コストが高くなる

### A3: CI/CD パイプラインでのみチェック

- 利点: ローカル環境に依存しない
- 欠点: PR 作成まで問題が見えない、修正ループが長い

---

## Consequences

### 正の影響

- **即時フィードバック**: 編集直後（< 10秒）に軽量 advisory 発火 → AI エージェントが即座に修正判断可能
- **コミット時保証**: pre-commit で強制チェック → 不整合のまま commit されない
- **ゲート時の最終確認**: `helix-gate` で包括的検証（静的+AI）→ フェーズ遷移の品質担保
- **設計ドキュメント連動**: doc-map 経由で実装と設計書の整合性を自動追跡

### 負の影響

- **フック設定の複雑さ**: Claude Code settings.json と Git hooks の両方を管理
- **doc-map メンテナンス負担**: パターン追加・更新が必要（設計文書追加時）
- **Advisory の見落とし**: AI エージェントが PostToolUse 警告を無視する可能性（pre-commit で最終防止）

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| PostToolUse フック失敗時の sub-hook 全体停止 | `\|\| true` で失敗を suppress（advisory 扱い） |
| doc-map 複数マッチ時の優先順位曖昧 | GAP-027 で優先度ルールを明文化、`doc_map_matcher.py` で実装 |
| Git hook と Claude Code hook の二重発火 | 異なる抽象度（ファイル単位 vs commit 単位）で分離、チェック内容の重複を許容 |
| フック遅延が UX を損なう | 各フックは専用タイムアウト（SessionStart 5s, PostToolUse 10s, Stop 8s） |

---

## References

- `cli/helix-hook` (PostToolUse フック本体)
- `cli/helix-check-claudemd` (PreToolUse フック)
- `cli/helix-session-start` (SessionStart フック)
- `cli/helix-session-summary` (Stop フック)
- `cli/templates/doc-map.yaml` (トリガー定義テンプレート)
- `cli/templates/pre-commit-hook` / `commit-msg-hook` / `post-merge-hook` (Git フック)
- `cli/lib/doc_map_matcher.py` (マッチングロジック)
- `cli/lib/phase_guard.py` (フェーズガード実装)
- ADR-004: Bash-Python Hybrid（実装方針）
