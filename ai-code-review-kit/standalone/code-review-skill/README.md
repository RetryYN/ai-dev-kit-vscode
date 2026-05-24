# six-stage-code-review スキル

コード差分・PRを6段階（Format / Lint / Style / Logic / Design / Architecture）でレビューする Claude Agent Skill。
AIと人間の境界線を「問題の性質」で切り分け、特に Logic 層では「AIが指摘しなかった箇所こそ人間が念入りに見る」逆説ルールを適用する。

## ファイル構成

```
code-review-skill/
├── SKILL.md                          # スキル本体（6段階レビューのワークフロー）
├── README.md                         # このファイル
├── scripts/
│   ├── precommit-gate.sh             # Stage 1-2 を commit 前に強制する pre-commit フック
│   └── review_report.py              # 指摘を6段階で集計しMarkdownレポート化
├── references/
│   ├── stage-playbook.md             # 各段階の詳細チェックリスト・Approve判断テンプレート
│   └── claude-code-paths.md          # Claude Code レビュー3経路の使い分け
└── assets/
    ├── agents/                       # Claude Code サブエージェント定義（.claude/agents/ へ）
    │   ├── logic-reviewer.md         #   Stage 4 Logic（仕様照合・逆説ルール / model: opus）
    │   ├── security-reviewer.md      #   Stage 4 Security（全件ブロッキング / model: opus）
    │   └── design-reviewer.md        #   Stage 5 Design（機械的ヒントまで / model: sonnet）
    └── commands/
        └── six-stage-review.md       # /six-stage-review スラッシュコマンド（.claude/commands/ へ）
```

## 導入

### A. Claude Agent Skill として使う（claude.ai / Claude Code）

`SKILL.md` を含む `code-review-skill/` フォルダをスキルとして登録する。
「レビューして」「PRを見て」「Approveしていいか」等の依頼で起動し、6段階のレビュー結果と Approve 判断を出力する。

### B. Claude Code のサブエージェント＋コマンドとして使う

プロジェクトに以下を配置する（チームで版管理可能）。

```bash
mkdir -p .claude/agents .claude/commands
cp assets/agents/*.md      .claude/agents/
cp assets/commands/*.md    .claude/commands/
```

`/six-stage-review` で logic / security / design の3サブエージェントを並列起動し、結果を統合する。
`per-agent model` 指定により、高stakes推論（Logic / Security）は Opus、Design は Sonnet に振り分けてコスト最適化している。

### C. Stage 1-2 を pre-commit フックで固める

```bash
cp scripts/precommit-gate.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

検出されたツール（Prettier / gofmt / black / ESLint / Ruff / mypy / tsc / go vet）だけを実行する。
自動整形して再ステージしたい場合は `AUTO_FORMAT=1 git commit ...`。

### D. レビュー結果をレポート化する

```bash
python3 scripts/review_report.py findings.json --spec-available -o report.md
```

`findings.json` は指摘のリスト（形式は `review_report.py` の docstring を参照）。
ブロッキング指摘があると exit code 2 を返すので、CIゲートにも使える。

## 運用の核心

- AIのレビューを **Approve の根拠にしない**。仕様判断の最終責任は人間。
- **逆説ルール**: AIが指摘した箇所はAIに任せ、AIが指摘しなかった箇所こそ人間が念入りに見る。AIコメントがゼロのPRこそ仕様書を開く価値がある。
- AI比率（60%等）は目安であって定量ゲートではない。
- 設計の運用設計書は同梱の `../CODE_REVIEW_WORKFLOW.md` を参照。
