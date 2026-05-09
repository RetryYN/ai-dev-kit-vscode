# PLAN Template Status Rules

PLAN の status は frontmatter の `status` だけを正本とする。本文は設計説明と履歴のために使い、現在状態の断定には使わない。

## Canonical Source

```yaml
---
plan_id: PLAN-0NN
title: 例
status: draft
created: 2026-05-09
---
```

- `status` の許可値は `draft` `finalized` `completed` の 3 つだけ。
- 本文中に status を重複定義しない。
- status の更新は frontmatter のみを変更する。

## Transition Rules

- `draft`
  - 起票直後の状態。
  - W-0 の下書き整理、受入条件整理、TL review 前後を含む。
- `finalized`
  - W-0 完了後に設定する。
  - 条件は TL 2 ラウンド approve 完了。
- `completed`
  - W-N の統合検証と retro 完了後に設定する。
  - carry と受入結果が本文と整合していること。

遷移は `draft -> finalized -> completed` の順に進める。途中段階を飛ばして更新しない。

## Body Usage Rules

本文で status に触れてよいのは次の文脈だけ。

- 設計説明
  - 例: `draft -> finalized -> completed` の遷移を説明する文
- 引用
  - 例: 他 PLAN の完了時点を参照する文
- 更新履歴 / Approval ログ
  - 例: `2026-05-09 status finalized`
- Out of Scope
- Retro placeholder

本文で禁止するもの:

- 現在状態を断定する宣言
- frontmatter と別の status を正文として扱う文
- `status` の運用状態を本文で上書きする文

## Lint Policy

- `helix plan lint <plan-file>` は frontmatter の `status` と矛盾する断定文だけを検出する。
- 判定は narrow detection とし、設計説明や履歴は誤検知しない。
- 不整合時は exit 1 とし、該当行を表示する。

## Scope

- この運用は PLAN-036+ に適用する。
- PLAN-031 から PLAN-035 へ retroactive に本文修正を要求しない。
