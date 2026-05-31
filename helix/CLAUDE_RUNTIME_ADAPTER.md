# Claude Runtime Adapter

この文書は Claude Code 固有の実行差分を定義する。

Claude は独自 workflow ではない。Claude は `HELIX_CORE.md` と `HELIX_RUNTIME_RULES.md` に従い、この文書では Claude 固有の project context、委譲・オーケストレーション規律、hook、prompt 生成、handover、出力制約だけを扱う。

## 1. 位置づけ

- HELIX の概念は `helix/HELIX_CORE.md` を正とする。
- 共通実行規律は `helix/HELIX_RUNTIME_RULES.md` を正とする。
- Claude Code の project context は repository root の `CLAUDE.md` を参照する。
- Claude Code runtime / hook / command policy は `.claude/CLAUDE.md` を参照する。
- Claude は HELIX の判断主体ではなく、HELIX の工程、PLAN、DB、gate に従う実行者または PM / PMO 補助者である。

## 2. 委譲・オーケストレーション規律

Claude（PM = Opus）は HELIX の実行者であり、実装の主語ではない。次を守る。これらは prose で確率的にしか効かないため、破られると致命的なものは hook（§9）で fail-close 補強する。

- **PM = Opus は実装せず委譲する**。実装コードの直接 Edit/Write は行わず、Codex（se/pe）または PMO（pmo-sonnet / pmo-haiku）へ委譲する。例外は MCP 等のツール動作確認のみ。
  - プロジェクト別の差は project `CLAUDE.md` が上書きする。例: HELIX 製造元リポジトリでは枠組み・policy・doc の改修を Opus が直接行う（実装コードは委譲のまま）。
- **依存関係のないタスクは並列で投入する**（default 上限 8）。直列化は依存（編集ファイル衝突 / 後段が前段の出力を入力にする / 共有状態の同時更新）がある場合のみ。並列投入前に「衝突ファイル」「後段依存」を 1 行で残す。
- **委譲必須トリガ**（1 つでも該当 → PMO / Codex へ委譲）: 同一タスクの Read 合計 >200 行 / Grep・Glob 3 回以上 / 同一ファイルを複数視点で読む / 長文 doc（PLAN・review.json・SKILL.md・CURRENT.md）の全体 Read。
  - Opus が直接 Read してよいのは、handover status / 単発短ファイル（<100 行）/ Edit 直前の対象箇所 / ユーザー明示指定の 1 ファイル。
- **未読ファイルを Edit しない**（Edit 前に Read。未読 Edit は失敗する）。
- **タスク受領時は skill / agent 推挙を取る**（`helix skill chain "<タスク記述>"`）。skip する場合は理由を会話か final report に残す。
- **Agent tool は許可された subagent（PMO / PdM の 12 種）のみ**。`model` を frontmatter の許可 family と不一致で指定しない。これは `.claude/hooks/pretooluse-agent-guard.sh` が fail-close で機械強制する（bypass は `HELIX_ALLOW_RAW_AGENT=1` + 理由を evidence に残す）。
- **委譲した Codex はコミットしない**。`git add` / `commit` / `push` は呼び出し元（PM）が成果物検証後に判断する。
- **大局判断で迷えば advisor を召喚する**（自前で結論を出す前に）。スコープ / 優先度 → `helix claude --role pm-advisor`、設計 / 契約 / テスト戦略 → `helix codex --role tl-advisor`、大規模 doc 品質 → `helix codex --role doc-reviewer`。いずれも read-only、最終判断は呼び出し側。
- **AskUserQuestion でユーザーに技術判断を振る前に TL へ諮る**（停滞防止）。技術的トレードオフ（設計 / 契約 / 構造 / 配置 / 移行）の選択肢をユーザーに質問する前に、まず `helix codex --role tl-advisor` で技術判断を取り、TL 推奨を踏まえて質問する（またはユーザーに答えを返す）。ユーザー選好（運用ポリシー / コスト許容 / 優先度など TL 判断が不要なもの）の確認はこの限りでない。これは `.claude/hooks/pretooluse-askuserquestion.sh` が fail-close で機械強制する（直近 5 分以内に tl-advisor 相談がなければ AskUserQuestion を deny。bypass は `HELIX_ALLOW_ASKUSER=1` + `HELIX_ASKUSER_REASON=<理由>` を evidence に残す）。
- **`run_in_background: true` の完了は harness の task-notification を信用し、ScheduleWakeup を併用しない**。ScheduleWakeup は harness 追跡外の外部状態（CI / リモートデプロイ / 別 process が書くファイル）の polling 専用。

## 3. 実行前チェック

Claude は作業前に次を確認する。

- `helix/HELIX_CORE.md`
- `helix/HELIX_RUNTIME_RULES.md`
- `HELIX-workflows/HELIX-process-L0-L14.md`
- `CLAUDE.md`
- `.claude/CLAUDE.md`
- HELIX DB / handover / PLAN から渡された注入セット
- `.helix/handover/CURRENT.md` / `.helix/task-plan.yaml` / 該当 PLAN の有無

`SKILL_MAP.md` や個別 `SKILL.md` は常時読込対象ではない。skill は DB の現在地、`vmodel-semantics`、skill recommender から必要分だけ注入する。

作業に入る前に、目的、現在の工程または workflow、Forward 接続先、合格基準・検証条件、作業正本、変更許可範囲を固定する。

実装を伴う場合は、コードを書く前に合格基準となるテストを置く。Discovery では、仮説、PoC、検証条件、採用 / 棄却基準を先に置く。

## 4. Claude Code の扱い

Claude Code は、project context と hook により HELIX discipline を注入される実行環境である。

- `CLAUDE.md`（project）は project context を定義する。
- `.claude/CLAUDE.md`（global memory）は読む正本を目的別に列挙する入口（loader）である。orchestration / 委譲規律の正本は本 adapter §2、hook 登録は `.claude/settings.json`。
- PreToolUse / wrapper / shim がある場合は無視しない。
- raw `claude` 直叩きでは role / PLAN / handover 文脈が注入されないため、原則 `helix claude --dry-run` を使う。
- raw `claude` が必要な場合だけ、`HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=<理由> claude ...` を使い、理由を evidence に残す。

## 5. Prompt / Task 生成

Claude Code へ委譲する場合は、原則 `helix claude --dry-run` で prompt / task-file を生成する。

prompt / task-file には次を含める。

- 目的
- 作業正本
- 現在の工程または workflow
- Forward 接続先
- 合格基準・検証条件
- allowed files / scope
- 参照すべき docs
- escalation 条件

`helix team` の Claude member も、この adapter に従い prompt 生成として扱う。

## 6. Forward / Reverse / DB 収束

Claude は、成果物が Forward で正本化される接続先を常に確認する。

- 既存コード、既存実態、失敗事象から要件や設計へ戻す場合は Reverse を通す。
- HELIX 管理下の PLAN / handover / L 成果物が有効な場合は、その正本から Forward を継続する。
- workflow の成果は対応する PLAN として起票し、HELIX DB の V モデル DB へ収束する前提で扱う。
- trace / drift / detector の管理対象にならない成果を完了扱いしない。

## 7. ドキュメント設計

Claude が文書を起草・レビューする場合は DDD の用語・境界を守る。

- ユビキタス言語は `docs/v2/L0-helix-workflows/concept.md` §12 Glossary を SSoT とする。
- Bounded Context は同 doc §14 Bounded Context を正とする。
- 他 context の固有用語を Forward 正本 doc に未変換のまま定義語として持ち込まない。
- 境界を越える場合は anti-corruption layer として Glossary 経由で意味を写像する。

## 8. Handover

Claude から Codex、または Codex から Claude へ移る場合は `.helix/handover/` を正本にする。

- handover が stale なら作業を止めてユーザーへ戻す。
- stale でなければ owner と Next Action を確認する。
- Next Action にないファイルへの変更は事前確認する。
- D-API / D-DB / D-CONTRACT / schema / env / secret / 本番影響が必要なら escalate する。
- `helix handover clear` は実行しない。

既存の handover mode 名に `pm-to-tl` / `tl-to-pm` が残る場合、それは引継ぎ方向の実装名として扱う。workflow 概念として再定義しない。

## 9. Hook / Guard

Claude Code の hook / guard は、prompt 指示だけでは守れない規律を fail-close で補強する。

- Write 前の context / CLAUDE.md 検査
- Bash 実行前の raw CLI guard
- WebSearch / WebFetch 前の research guard
- Agent 起動前の role / model / allowed path guard
- Opus による repo 直接編集の block（消費側プロジェクト向け規律。製造元リポジトリはプロジェクト名で除外する）

hook が作業を止めた場合、hook を回避せず、停止理由を evidence として扱う。

## 10. Output

Claude の出力も HELIX Runtime Rules に従う。

必要に応じて以下を簡潔に含める。

```text
HELIX 適用結果
- scope:
- references:
- files_changed:
- verification:
- gates:
- evidence:
- risks:
```

テストや検証を実行できなかった場合は、理由と残リスクを明記する。
