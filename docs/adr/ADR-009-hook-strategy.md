# ADR-009: Hook 戦略（doc-map トリガー中心）

> Status: Accepted
> Date: 2026-04-14
> Deciders: PM, TL

---

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

### クエリ結果

- `phase gate readiness entry exit criteria CMMI / DO-178C / Stage-Gate process`
  - Stage-Gate（Cooper系）: 各ゲートで「deliverables」と「exit criteria」を設定し、判断基準を満たせない場合は次段階へ進まない運用を示す。
    - https://cio-wiki.org/wiki/Stage-Gate
  - NASA Software Engineering Handbook: 13レベルのライフサイクルレビューに対し、Entrance / Exit / Success Criteria（製品分類に合わせたテイラリング）を定義。
    - https://swehb.nasa.gov/download/attachments/76447896/SWE_Handbook_Rel0.1_March2011_RevC.pdf?api=v2
  - CMMI: プロセス目標（specific / generic goals）と成熟度管理を用いた予測可能性向上を目的とし、ゲート的レビューと評価を前提とした品質・リスク管理を説明。
    - https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/cmmi/guidance-background-to-cmmi?view=azure-devops
  - DO-178C（Ansys summary）: プランニング／開発／検証・QA/CM等のプロセスを objective based で定義し、プロセス毎に成果物と検証責務を明確化。
    - https://www.ansys.com/en-gb/simulation-topics/what-is-do-178c

- `technical debt prioritization carry over policy Martin Fowler / Ward Cunningham original / SAFe Agile`
  - Technical Debt は Ward Cunningham 由来の比喩で、クルト（将来コスト）が増える欠陥管理を「払う・先送りする」の意思決定として扱う。
    - https://martinfowler.com/bliki/TechnicalDebt.html
  - Google SRE PRRは、サービス運用移譲前に受入基準をレビューして欠陥（運用観点）を事前潰しを促進。
    - https://sre.google/sre-book/evolving-sre-engagement-model/
  - Launch Checklist は実装・監視・セキュリティ・リリース工程の項目を明示。
    - https://sre.google/sre-book/launch-checklist/

- `release readiness review SRE production-readiness Google SRE book / Microsoft / DORA metrics`
  - Google SRE PRR では「production setup/operational readiness」の確認と SRE と所有者体制の準備を要件化。
    - https://sre.google/sre-book/evolving-sre-engagement-model/
  - Google SRE の Release Engineering 章は本番配備速度・利用状況観点の運用指標を継続的に観測する重要性を示唆。
    - https://sre.google/sre-book/release-engineering/
  - Microsoft Well-Architected（mission-critical）：本番運用 readiness の自己評価質問票を想定し、運用品質を段階的に成熟させるアセスメントを提供。
    - https://learn.microsoft.com/en-us/azure/well-architected/mission-critical/mission-critical-assessment
  - DORA metrics（4指標）を開発・デリバリ品質の共通指標として採用する代表系資料。
    - https://www.thoughtworks.com/en-us/radar/techniques/four-key-metrics

### HELIX 採用根拠

- **readiness entry / exit**: ゲートごとの「進入可否」と「終了可否」を明示する現行 HELIX の方針（`docs/adr` の他 ADR でも共通）と、NASA/Stage-Gate の criteria 型レビューを合わせる。
  - 参考: `helix/HELIX_CORE.md`
- **P0-P3 carry rule**: 重要度別 carry をそのまま運用し、未解決事項を deferred-finding に記録。
  - 参考: `helix/HELIX_CORE.md`
- **carry rule（deferred-finding）と accuracy_score 反映**: deferred-finding は `accuracy_score` 減点へ反映されるため、W5c のキャリー判断を「再現可能・監査可能」なデータへ統合する。
  - 参考: `helix/HELIX_CORE.md`

## Revision History

| 日付 | 版 | 内容 | 変更者 |
|---|---|---|---|
| 2026-05-19 | WIP | 業界 standard 引用 retrofit（W5c-3、PLAN-087 ガードレール準拠、query 3 件結果反映、P0-P3 carry / accuracy_score 反映ルール明確化、Revision History 追加） | Codex |


## Context

HELIX CLI は複数のフックポイントで自動検証・ガイド提示を行う:

- **Claude Code hook**: SessionStart, PreToolUse(Write/Bash), PostToolUse(Edit/Write/MultiEdit), Stop
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
| **Layer 1: PostToolUse (advisory)** | ファイル編集直後 | doc-map マッチ → 設計ドキュメント存在確認、契約ドリフト検知（`helix drift-check`） | < 10秒 |
| **Layer 2: pre-commit (enforce)** | コミット前 | フェーズガード、CLAUDE.md テンプレート準拠、契約整合 | < 30秒 |
| **Layer 3: helix gate (full)** | ゲート通過時 | 成果物存在・静的パターン・AI検証 | < 数分 |

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
        check: helix drift-check
```

### 現在実装済みフック（2026-05-04時点）

**Claude Code hooks** (`~/.claude/settings.json`):
- SessionStart → `helix session-start` (コンテキスト注入・セットアップチェック)
- PreToolUse(Write) → `helix check-claudemd` (CLAUDE.md テンプレート強制)
- PreToolUse(Bash) → `cli/libexec/helix-pre-bash` (raw LLM CLI 直叩き防止、HELIX harness 誘導)
- PostToolUse(Edit/Write/MultiEdit) → `helix-post-tool-use` → `helix hook` (payload 抽出、doc-map トリガー、drift-check、advisory)
- Stop → `helix session-summary` (セッションサマリ生成)

**Git hooks** (`cli/templates/hooks/pre-commit` 等):
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
- **ゲート時の最終確認**: `helix gate` で包括的検証（静的+AI）→ フェーズ遷移の品質担保
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
| raw LLM CLI 直叩きで HELIX discipline が外れる | PreToolUse(Bash) と PATH shim で `codex exec` / `claude` を止め、`helix codex --plan-only/--approved` / `helix claude --dry-run` へ誘導 |
| context が膨張してフックや LLM 指示が読まれなくなる | `helix context check` / `cli/lib/context_guard.py` で AGENTS/CLAUDE/Hook docs の肥大化を検出 |

---

## References

- `cli/libexec/helix-post-tool-use` (PostToolUse payload wrapper)
- `cli/libexec/helix-pre-bash` (PreToolUse Bash guard)
- `cli/helix-hook` (PostToolUse フック本体)
- `cli/helix-check-claudemd` (PreToolUse フック)
- `cli/helix-context` / `cli/lib/context_guard.py` (context budget guard)
- `cli/lib/llm_guard.py` (raw LLM command guard)
- `cli/helix-session-start` (SessionStart フック)
- `cli/helix-session-summary` (Stop フック)
- `cli/templates/doc-map.yaml` (トリガー定義テンプレート)
- `cli/templates/hooks/pre-commit` / `cli/templates/hooks/commit-msg` / `cli/templates/hooks/post-merge` (Git フック)
- `cli/lib/doc_map_matcher.py` (マッチングロジック)
- `cli/lib/phase_guard.py` (フェーズガード実装)
- ADR-004: Bash-Python Hybrid（実装方針）
