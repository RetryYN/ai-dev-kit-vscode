# Claude Code レビュー3経路の使い分け

Stage 4（Logic）を実行する手段として、Claude Code には2026年時点で3つのレビュー経路がある。
PRの重要度・チームのプラン・コスト許容度で使い分ける。情報は2026年5月時点。

---

## 経路の比較

| 経路 | 対象プラン | 仕組み | コスト | 特性 | 推奨用途 |
|------|-----------|--------|--------|------|----------|
| 自作サブエージェント | 任意の有料 | `.claude/commands/` に slash command を置き、複数サブエージェントを並列起動 | APIトークンのみ | ローカル実行・完全カスタム、提案の約75%がactionable（単一エージェントは50%未満） | 日常のローカルレビュー、Stage 3–4 |
| `/ultrareview` | Pro / Max | クラウドのマルチエージェント bug hunter | 約 $5–20 / run | 検証済みバグのみ報告、research preview | リリース前の重点 Logic レビュー |
| 公式 Code Review | Team / Enterprise | GitHub統合（5ステップ）、マネージド | 約 $15–25 / review | false positive < 1%、結果まで約20分 | PR自動レビューの恒常運用 |

---

## 1. 自作サブエージェント（推奨: 日常運用）

`.claude/agents/`（プロジェクト共有）または `~/.claude/agents/`（個人）に Markdown でサブエージェントを定義する。
最大10エージェントを並列実行でき、`per-agent model` 指定で高stakes推論を Opus、高volume処理を Haiku に振り分けてコスト最適化できる。

設定手順:

1. プロジェクトルートに `.claude/commands/` と `.claude/agents/` を作成
2. `assets/agents/` のサブエージェント定義（logic-reviewer / design-reviewer / security-reviewer）を `.claude/agents/` にコピー
3. `.claude/commands/six-stage-review.md` に、複数サブエージェントを並列起動して結果を統合する slash command を定義
4. `/six-stage-review` で起動

利点: APIトークンのみで完結、ローカル実行、チームで版管理可能。
単一エージェントより複数エージェントで角度を変えるほうが見落としが減る。

---

## 2. `/ultrareview`（推奨: リリース前の勝負どころ）

Pro / Max アカウント向けのクラウドマルチエージェント。検証済みのバグのみを報告するため、ノイズが少ない。
1回あたり $5–20 とコストはかかるが、リリース前の重点的な Logic レビューに向く。research preview のため挙動は変わりうる。

使いどころ: 本番影響の大きいPR、データ整合性・課金・認証に触れる変更。

---

## 3. 公式 Code Review（推奨: 恒常的なPR自動レビュー）

Team / Enterprise 向けのマネージドサービス。GitHub と5ステップで統合し、PRに自動でレビューが付く。
false positive が 1% 未満と低く、結果まで約20分。1レビュー $15–25。

使いどころ: PRごとに自動でAIレビューを回す恒常運用。CodeRabbit/Copilot の代替・併用。

---

## 共通の鉄則

どの経路を使っても、6段階モデルの原則は変わらない。

- AIのレビューは **Approve の根拠にしない**。仕様判断の最終責任は人間。
- Stage 4 の逆説ルールを適用する: AIが指摘した箇所はAIに任せ、**AIが指摘しなかった箇所こそ人間が念入りに見る**。
- AIは Stage 1–4 の支援に使い、Stage 5（Design）は補助ヒントまで、Stage 6（Architecture）には踏み込ませない。

---

## 他ツールとの併用

Claude Code経路と、PR常設のAIレビュー（CodeRabbit / GitHub Copilot Code Review）は併用できる。

- CodeRabbit: 多プラットフォーム対応・低ノイズ（false positive少）。Stage 3–4 の常設レビューに。
- GitHub Copilot Code Review: GitHubネイティブ・ゼロ設定。Copilot契約があれば追加費用なし。2026年3月にフルエージェント化（ディレクトリ構造を読む）。
- Greptile: catch rate は高い（82%報告）が false positive が多い。recall重視のチーム向け。

バグ検出 recall は現状どのツールも半分強が上限。「6割見つかれば上等」を前提に、Stage 4 の人間レビューを設計する。
