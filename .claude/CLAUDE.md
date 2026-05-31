# Global Settings

> Claude Code の global memory（全プロジェクト・毎セッションで読まれる入口）。読む正本を目的別に列挙する loader。
> SKILL_MAP.md は索引なので注入しない（skill は recommender = `helix skill search` / `helix skill chain` から必要分だけ）。
> 機能群 → 正本の参照表は `helix/HELIX_CORE.md §9 問い合わせ方法`、委譲・オーケストレーション規律は `helix/CLAUDE_RUNTIME_ADAPTER.md §2` を正本とする（ここには重複させない）。

## Core（概念・機能群・問い合わせ表）

@~/.helix/core/helix/HELIX_CORE.md

## ルール（実行規律・委譲規律・Claude 固有差分）

@~/.helix/core/helix/HELIX_RUNTIME_RULES.md
@~/.helix/core/helix/CLAUDE_RUNTIME_ADAPTER.md

## ワークフロー（工程 L0-L14）

@~/.helix/core/HELIX-workflows/HELIX-process-L0-L14.md
