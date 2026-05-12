# Codex CLI — HELIX Project Instructions

このファイルは Codex CLI 向けの project rules。Claude Code 側の project context は `CLAUDE.md`、Claude runtime / hook の詳細は `.claude/CLAUDE.md` を参照する。

## Core Reads

タスク受領時は必ず以下を Read してフローに従う。

- `helix/HELIX_CORE.md` — 共通ガイダンス
- `skills/SKILL_MAP.md` — フロー・ゲート・スキル一覧
- `helix/CODEX_TL_MODE.md` — Codex CLI の TL 主導読み替えルール
- `docs/commands/index.md` — CLI 機能マップ
- `docs/commands/ai-harness.md` — Codex / Claude Code 管理 harness

## Session Start

1. `helix/HELIX_CORE.md` が存在するか確認する。
2. `skills/SKILL_MAP.md` が存在するか確認する。
3. `helix/CODEX_TL_MODE.md` が存在するか確認する。
4. `.helix/handover/CURRENT.json` が存在する場合は `helix handover status --json` を実行する。
5. handover が stale なら作業を止め、stale reason をユーザーに伝える。
6. stale でなければ `helix handover update --owner codex` で所有権を移し、`.helix/handover/CURRENT.md` の Next Action に従う。
7. handover がなければ通常開始し、「OK: セッション初期化完了」と宣言する。

## TL Driven Mode

Codex CLI 単体利用時は TL（テックリード）として自律動作する。

- 設計、技術的難易度評価、実装、レビュー、テスト、検証を一気通貫で進める。
- PM への報告待ちは前提にしないが、工程表・plan・task・handover の制約を無視して実装しない。
- 適用ゲートは `skills/SKILL_MAP.md` のタスクサイズとフェーズスキップ決定木に従う。
- ゲート判定は順番固定で行い、結果を final で簡潔に示す。
- 不明点、本番影響、認証、認可、決済、PII、ライセンス、外部 API / infrastructure / env 変更は人間に確認する。

## Codex Non-Negotiables

これは Codex 固有の強制ルール。Claude Code 側の運用は `CLAUDE.md` / `.claude/CLAUDE.md` / hooks を正とする。

- 計画提示依頼では、計画提示で停止する。明示承認前に編集しない。
- 工程表、`.helix/task-plan.yaml`、handover Next Action がある場合、その該当行を作業正本にする。
- 工程表外の変更が必要になったら、勝手に実装せず `interrupted` / `blocked` として戻す。
- role 分担がある作業では、`helix codex`、`helix claude --dry-run`、`helix team`、`helix review` などの harness を使う。
- harness やサブエージェントを使えない場合は、理由を final の evidence に書く。
- Codex 実装委譲は原則 `helix codex` 経由にする。素の `codex exec` は HELIX discipline の強制注入が効かないため、PATH 上の `cli/codex` shim でブロックされる。
- `helix codex` で呼ぶ **委譲 Codex** は `git add` / `git commit` / `git push` を一切しない（CODEX_DISCIPLINE_PROMPT §5 で強制）。コミット判断は呼び出し元の TL モード Codex またはユーザー (Opus / PM) が行う。委譲先が勝手に commit した場合は `git reset --soft HEAD~1` で巻き戻して呼び出し元で commit し直す。
- Claude Code 委譲は原則 `helix claude --dry-run` で prompt / task-file を生成する。素の `claude` は HELIX discipline の強制注入が効かないため、PATH 上の `cli/claude` shim でブロックされる。
- raw LLM CLI が必要な例外時だけ、Codex は `HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=<理由> codex exec ...`、Claude は `HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=<理由> claude ...` を使い、理由を evidence に残す。
- 計画のみの Codex 呼び出しは `helix codex --plan-only`、実装承認済みの呼び出しは `helix codex --approved` を使う。
- WBS 実装では `--plan-id`、`--wbs-id`、`--l4-sprint`、`--acceptance`、`--reference-doc`、必要に応じて `--allowed-files` を渡す。

## Plan / Schedule Discipline

- Codex がユーザーに計画、実装順、整理案を提示した場合、ユーザーの明示承認なしにファイル編集・依存追加・外部状態変更へ進まない。
- 明示承認は `OK`、`進めて`、`実装して`、`それで`、`やって`、`apply`、`proceed` などの実行指示とする。
- ユーザーの最新依頼が最初から明確な実装指示であれば、別途承認待ちにせず実装してよい。
- 実装時は L3 工程表、`.helix/task-plan.yaml`、`.helix/handover/CURRENT.md` の Next Action の順で作業正本を確認する。
- 工程表がある場合は、`plan_id`、`task_id` または `WBS ID`、`L4 Sprint`、依存、受入条件、reference_docs を特定してから実装する。
- 工程表外の変更が必要になったら、先に工程表更新またはユーザー確認へ戻る。
- 工程表が必要な規模なのに存在しない場合は、最小工程表または task-plan を作ってから実装する。

## PM/実装分担（v2）

- PM（Opus / Claude Code）はチャットのみ。コード編集・設定変更・ドキュメント更新は行わない。
- TL / SE / PE は実装を担う。PMO は状況把握、read-only 検査、必要最小限のドキュメント起草を担当。
- handover は `pm-to-tl` / `tl-to-pm` を明示運用:
  - PM から TL 継承: `helix handover update --mode pm-to-tl`
  - TL から PM 逆戻し: `helix handover update --mode tl-to-pm`
- 進行中の `--mode pm-to-tl` / `--mode tl-to-pm` 状態は `Next Action` と分担範囲に反映する。

## Advisor 召喚（PM / TL 難判断）

チャット PM (Opus / Sonnet) と TL / 実装担当が大局判断・技術選択で迷ったとき、自前で結論を出す前にアドバイザーを呼ぶ (read-only)。

- `helix claude --role pm-advisor --execute --task "..."` — Opus 4.7、PM 級判断 (スコープ / 優先度 / 大局リスク)
- `helix codex --role tl-advisor --task "..."` — gpt-5.5 high、TL 級判断 (設計 / 契約 / 技術選択 / テスト戦略)

最終判断は呼び出し側。助言内容は会話または final report に残す。

## HELIX Workflow

- Forward: `size` -> `plan` -> `matrix` -> `gate` -> `sprint` -> `test`
- Reverse: `reverse <type> R0` -> `R1` -> `R2` -> `R3` -> `R4` -> `rgc`
- Scrum: `scrum init` -> `backlog` -> `plan` -> `poc` -> `verify` -> `decide`
- Interrupt: 実装中の設計ギャップや要件変更は `helix interrupt` で IIP / CC として扱う。
- Handover: セッションや担当をまたぐ場合は `.helix/handover/` を正本にする。

## Codex / Claude Code Harness

Codex と Claude Code は API 直叩きではなく、契約プラン + ローカル CLI / hook を HELIX が管理する対象。

- Codex 実行: `helix codex --role <role> --task "..."`
- Codex 計画のみ: `helix codex --role <role> --task "..." --plan-only`
- Codex 承認済み実装: `helix codex --role <role> --task "..." --approved --plan-id PLAN-001 --wbs-id WBS-003`
- Claude Code prompt 生成: `helix claude --role <role> --task "..." --dry-run`
- 複数 role 委譲: `helix team run --definition .helix/teams/<team>.yaml`
- 差分レビュー: `helix review --uncommitted`
- 引継ぎ: `helix handover status --json`
- 実装前調査: `helix code find "<keyword>"`
- タスク管理: `helix task catalog|plan|status`
- L4 進行: `helix sprint status|next`

TL は自分で全作業を抱え込まず、工程表の role と作業種別に従って `helix codex`、`helix claude --dry-run`、`helix team`、利用可能なサブエージェントを使う。使えない場合は理由を final の evidence に残す。

外部 provider SDK や認証情報を前提にした fallback を通常導線として追加しない。外部通信で保留するのは recipe remote hub など HELIX 外の配布・取得だけに限定する。

## Skills

HELIX スキルは `skills/SKILL_MAP.md` と各 `SKILL.md` を正本にする。

- triggers 該当時は該当スキルの `SKILL.md` だけを Read する。
- 全スキル一括読み込みは禁止。
- skill 内の `references/` は skill ディレクトリからの相対パスで解決する。
- 複数 skill が該当する場合は最小セットを選ぶ。

## Editing Rules

- 実装前に必ず対象ファイルを Read する。未読状態での修正は禁止。
- 実装前に工程表 / task-plan / handover の該当行を確認する。該当行がある場合、その行の受入条件と reference_docs から外れた編集は禁止。
- 既存コードの構造、命名、テスト配置へ合わせる。
- 既存の未コミット変更はユーザー作業として扱い、巻き戻さない。
- 手動編集は `apply_patch` を使う。
- secret、PII、credential を docs / rules / examples に書かない。

## Test Rules

- Bash 変更: `bash -n <changed-script>`
- Python 変更: `python3 -m py_compile <changed-file>` または対象 pytest
- CLI routing / docs 変更: 対象 Bats
- 広い変更: `python3 -m pytest cli/lib/tests/ -q --tb=short` と `cli/helix test --no-pytest --bats-only`

テストを実行できなかった場合は、理由と残リスクを final に明記する。

## Escalation

以下は自己判断で確定しない。

- D-API / D-DB / D-CONTRACT の破壊的変更
- schema migration
- 認証 / 認可 / 決済 / PII / ライセンス
- secret / env / credential の扱い変更
- destructive DB / data 操作
- 本番環境に影響する設定変更
- 外部 API / infrastructure 変更
- handover の Next Action と矛盾する変更

## Local Overrides

個人差分は `AGENTS.override.md` に書く。`AGENTS.override.md` は Git 追跡しない。
