---
plan_id: PLAN-161
title: "PLAN-161: helix-agent capability advertisement"
kind: impl
layer: L4
drive: agent
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-088-todowrite-agent-slot-framework.md   # from dependencies.parent
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — capability field 定義・helix agent suggest マッチングロジック実装"
  - role: pmo-sonnet
    slot_label: "PMO — capability 定義妥当性チェック・既存 agent frontmatter 整合確認"
  - role: docs
    slot_label: "Docs — .claude/agents/*.md frontmatter 更新・capability 定義ドキュメント"
generates:
  - artifact_path: cli/lib/agent_capability_matcher.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_agent_capability_matcher.py
    artifact_type: test
  - artifact_path: docs/commands/agent-capability-map.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-088
  requires:
    - PLAN-088
  blocks: []
related_adr: []
related_docs:
  - docs/plans/PLAN-088-todowrite-agent-slot-framework.md
  - .claude/agents/pmo-sonnet.md
  - .claude/agents/pmo-haiku.md
  - cli/lib/agent_mandatory.py
  - helix/HELIX_CORE.md
acceptance_criteria:
  - ".claude/agents/*.md frontmatter に capabilities フィールドが全 12 種追加済"
  - "helix agent suggest --task が capabilities ベースでマッチングし候補を返す"
  - "helix doctor が capability 重複・不足を advisory WARN として出力する"
  - "python3 -m py_compile cli/lib/agent_capability_matcher.py PASS"
  - "unit test 6 case 全 PASS"
---

# PLAN-161: helix-agent capability advertisement

## L2 凍結 (ADR snapshot)

本 PLAN は既存 agent slot framework (PLAN-088 / ADR-022) を拡張する機能追加のため、
新規 L2 大局判断は含まない。ADR snapshot は不要。

## 背景

現状の `helix agent suggest` は subagent_type 一覧を静的列挙するのみで、
task description に対してどの subagent が適切かの capability ベースマッチングができていない。
PMO subagent 12 種 (pmo-sonnet / pmo-haiku 等) と PdM subagent 3 種は
それぞれ得意領域が異なるにも関わらず、`.claude/agents/*.md` frontmatter に
能力を機械可読な形で記述する仕組みがない。

問題ケース:
- `helix agent suggest --task "OSS を調査して採用判断したい"` が全 subagent を並列候補として返す
- helix doctor が capability 重複（複数 agent が同一 capability を宣言）を検出できない
- 新規 subagent 追加時に既存 capability との整合確認が手動

## WebSearch 履歴

本 PLAN は内部 agent frontmatter 拡張と Python matcher 実装のみ。
外部ライブラリ新規依存なし。業界 standard 参照は不要と判断しスキップ。
（既存 `.claude/agents/*.md` + plan_validator.py パターンを流用）

## capability 定義

### 1.1 capability 種別

12 種の capability を定義する。各 subagent は該当する capability を複数宣言可能。

| capability | 説明 | 主担当 subagent |
|---|---|---|
| `code-review` | コードレビュー・品質チェック | pmo-sonnet |
| `doc-read` | 長文ドキュメント精読・構造化 | pmo-sonnet / pmo-project-explorer |
| `doc-write` | ドキュメント軽修正・起草補助 | pmo-haiku |
| `web-search` | Web 検索・外部情報収集 | pmo-haiku / pmo-tech-news |
| `oss-explore` | OSS/plugin 探索・転用判断 | pmo-tech-fork |
| `external-doc-read` | 外部設計手法・規格文書精読 | pmo-tech-docs |
| `helix-explore` | HELIX framework 内資産探索 | pmo-helix-explorer / pmo-helix-scout |
| `project-explore` | プロジェクト内資産探索 | pmo-project-explorer / pmo-project-scout |
| `tech-innovation` | 海外技術思想翻案・転用 | pdm-tech-innovation |
| `marketing-innovation` | 海外マーケ思想翻案・転用 | pdm-marketing-innovation |
| `pdm-integration` | 新方向性策定・PdM 統合判断 | pdm-innovation-manager |
| `status-check` | 進捗把握・ドキュメント整合チェック | pmo-sonnet |

### 1.2 frontmatter 拡張形式

`.claude/agents/*.md` の YAML frontmatter に `capabilities` フィールドを追加:

```yaml
capabilities:
  - doc-read
  - status-check
  - code-review
```

`capabilities` は list[string] 形式、空リスト `[]` は許容しない（最低 1 種必須）。

## 実装計画

### Sprint .1: Python capability matcher 実装 (Codex se、size S)

`cli/lib/agent_capability_matcher.py`:
- `load_agent_capabilities(agents_dir: Path) -> dict[str, list[str]]`
  `.claude/agents/*.md` を glob して frontmatter の `capabilities` を抽出
- `match_by_task(task: str, agent_caps: dict[str, list[str]]) -> list[str]`
  task description に含まれるキーワードを capability とスコアリングして候補順に返す
  （keyword → capability の静的マッピングテーブルを実装、ML は不要）
- `detect_capability_issues(agent_caps: dict[str, list[str]]) -> list[str]`
  capability が未宣言（空）の agent と重複超過（同一 capability を 3 種以上宣言）を検出

単体テスト `cli/lib/tests/test_agent_capability_matcher.py` 6 case:
- T1: frontmatter 正常読み込み
- T2: task keyword マッチング上位 3 件
- T3: capabilities 未宣言の agent を検出
- T4: capability 重複（3 種以上）の検出
- T5: 未知 capability の graceful skip
- T6: agents_dir 空ディレクトリで空結果

完了条件: `python3 -m py_compile` PASS + 単体テスト 6 PASS

### Sprint .2: frontmatter 更新 (Codex docs、size S)

`.claude/agents/` 配下全 15 ファイルに `capabilities` フィールドを追加。
各 subagent の担当領域に対応する capability を上記テーブルから選択して付与。
YAML syntax check (`python3 -c "import yaml; yaml.safe_load(open('<file>').read())"`) で全件 PASS。

完了条件: 全 15 agent に capabilities 追加済・yaml.safe_load PASS

### Sprint .3: helix agent suggest 連携 + helix doctor 統合 (Codex se、size S)

`cli/helix-agent suggest` サブコマンドに `--task "<description>"` オプション追加:
- agent_capability_matcher.match_by_task を呼び出し、スコア順上位 3 件を返す
- 既存の静的候補列挙と両立（`--task` 未指定時は既存動作を維持）

`helix doctor check_agent_capabilities` 追加:
- capabilities 未宣言の agent → advisory WARN
- 同一 capability を 3 種以上宣言する場合 → advisory WARN
- 未知 capability 値 → advisory WARN

docs/commands/agent-capability-map.md 起草:
- capability 種別一覧・各 agent の capability 対応表・`helix agent suggest --task` 利用例

完了条件: `helix agent suggest --task "..."` 動作確認 + helix doctor WARN 表示確認

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/agent_capability_matcher.py` PASS
- [ ] unit test 6 case PASS
- [ ] `.claude/agents/` 全 15 件 yaml.safe_load PASS
- [ ] `helix agent suggest --task "..."` 動作確認
- [ ] helix doctor check_agent_capabilities advisory WARN 出力確認
- [ ] pmo-sonnet review (Sprint .3 完了後)

## DoD

- [ ] `.claude/agents/*.md` 全 15 ファイルに capabilities フィールド追加済
- [ ] `cli/lib/agent_capability_matcher.py` 実装・`python3 -m py_compile` PASS
- [ ] 単体テスト 6 case PASS
- [ ] `helix agent suggest --task "..."` が capability ベースの候補を返す
- [ ] `helix doctor check_agent_capabilities` が重複・不足を advisory WARN で出力
- [ ] docs/commands/agent-capability-map.md 作成済
- [ ] helix doctor pass 数現行以上

## V-model 4 artifact trace

| artifact | パス |
|---|---|
| ① 設計 | docs/plans/PLAN-161-helix-agent-capability-advertisement.md |
| ② 実装コード | cli/lib/agent_capability_matcher.py / .claude/agents/*.md |
| ③ テスト設計 | 本文 §Sprint .1 T1-T6 + §mandatory in sprint |
| ④ テストコード | cli/lib/tests/test_agent_capability_matcher.py |

## carry / リスク

- capability keyword マッピングテーブルの精度は初版 advisory のみ。ML/embedding への発展は別 PLAN
- `.claude/agents/` の追加・削除時に capabilities 更新漏れが起こりうる → helix doctor で継続監視
- `helix agent suggest --task` 未指定時の既存動作への影響は Sprint .3 で regression test 必須

## 関連 reference

- PLAN-088 (TodoWrite × agent slot framework、parent)
- PLAN-100 (existing retrofit master)
- cli/lib/agent_mandatory.py (mandatory subagent 実装、参考実装)
- helix/HELIX_CORE.md §工程別 subagent 起動マップ
