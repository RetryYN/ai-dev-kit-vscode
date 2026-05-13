# FR-INV08 Hook / Slash command / Subagent / Role 棚卸し

最終更新: 2026-05-14

## 概要

本書は Orchestration 層に関わる `Hook / Slash command / Subagent / Codex role / Claude role / Native skill` の現状棚卸しです。V2 Phase 4（検出ガードレール強化）と Phase 5（自動化）の入力として、実装の所在、起源 PLAN、稼働状態、V2 での扱いを固定します。

注記:

- `起源 PLAN` は実装ファイル、PLAN、ADR、関連 docs から引いたものです。明示根拠が薄い項目は `推定` と記載します。
- TASK 例示の `/loop` `/ultrareview` `/handover-resume` は現行 repo の `.claude/commands/` には存在せず、**実在する slash command は 7 件**です。
- `.codex/AGENTS.md` はこの repo 直下には存在しません。Codex 側の実運用正本は root `AGENTS.md` と `helix/CODEX_TL_MODE.md` 側にあります。
- `skills/` の `SKILL.md` 実数は **104 件**で、TASK 記述の `106 skill` とは差分があります。

## 選択肢

### Option A: 現状資産をそのまま温存

- メリット: 追加作業が最小。
- デメリット: `slash command` と `Agent tool 禁止` の矛盾、deprecated hook 参照、role/agent 二重定義が残る。
- 推奨度: 低。

### Option B: V2 で Hook/Role/Skill を正本化し、Slash/Subagent は縮退運用

- メリット: 現実の実行経路（`helix codex` / `helix claude` / hooks / skill chain）と監査対象を一致させやすい。
- デメリット: 既存 `.claude/commands/*.md` と `.claude/agents/*.md` の整理コストがかかる。
- 推奨度: 高。

### Option C: Claude native command / subagent も第一級 orchestration として維持

- メリット: 既存資産を最大活用できる。
- デメリット: ADR-015 / PLAN-028 の「Agent tool 禁止」と整合しにくく、ガード設計が複雑化する。
- 推奨度: 中。

## 推奨

V2 では **Option B** を推奨します。理由は 3 点です。

1. 実行正本はすでに `cli/roles/*.conf` と `cli/config/models.yaml`、および `.claude/settings.json` の hook 登録に寄っています。
2. `.claude/commands/ship.md` は依然として Agent tool fan-out を指示しており、ADR-015 / `.claude/CLAUDE.md` の禁止方針と衝突しています。
3. `skill chain` と `skill_usage` 記録、SessionStart の自動推挙ヒント、PostToolUse/Stop の telemetry 化が進んでおり、V2 Phase 4/5 の足場は hook+role+skill 側にあります。

## 1. Hook

### 1.1 登録点

`.claude/settings.json` に登録されている runtime hook は以下です。

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 発火条件 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|---|
| `helix-session-start` | Hook | PLAN-023, PLAN-022 | `.claude/settings.json:3`, `cli/helix-session-start:1`, `cli/libexec/helix-session-start:1` | SessionStart で HELIX context と skill hint を注入する | `SessionStart` | 機能している | extend | skill hint と session 記録があり、Phase 5 sync 起点にも転用しやすい |
| `helix-check-claudemd` | Hook | 推定: PLAN-019, PLAN-043 | `.claude/settings.json:16`, `cli/helix-check-claudemd:1` | `CLAUDE.md` 新規作成時のテンプレート逸脱を事前抑止する | `PreToolUse: Write` | 部分機能 | modify | 登録は現役だが実体は deprecated wrapper 参照 |
| `helix-pre-bash` | Hook | PLAN-018 | `.claude/settings.json:29`, `cli/libexec/helix-pre-bash:1` | raw `codex` / `claude` 実行や harness 逸脱を遮断する | `PreToolUse: Bash` | 機能している | as-is | LLM guard の fail-close 本体 |
| `helix-pre-research` | Hook | PLAN-018 | `.claude/settings.json:41`, `cli/libexec/helix-pre-research:1` | research role 外の WebSearch/WebFetch 利用を抑止する | `PreToolUse: WebSearch|WebFetch` | 機能している | extend | Phase 4 の research guard 強化の核 |
| `pretooluse-opus-repo-block.sh` | Hook | PLAN-043, PLAN-028 | `.claude/settings.json:53`, `.claude/hooks/pretooluse-opus-repo-block.sh:1` | Opus による repo 直 Edit/Write を block する | `PreToolUse: Edit|Write|MultiEdit` | 機能している | as-is | v2 PM 実装禁止を機械 enforce 済み |
| `helix-post-tool-use` | Hook | PLAN-067, PLAN-043 | `.claude/settings.json:63`, `cli/libexec/helix-post-tool-use:1` | 変更ファイル抽出後に post-hook router へ渡す | `PostToolUse: Edit|Write|MultiEdit` | 部分機能 | extend | file→DB sync の本丸は PLAN-067 側で draft |
| `helix-session-summary` | Hook | PLAN-014, PLAN-015, PLAN-016 | `.claude/settings.json:77`, `cli/helix-session-summary:1` | Stop 時に `cost_log` を記録する | `Stop` | 機能している | modify | 旧 summary 役割は廃止済みで、現状は accounting shim |

### 1.2 Hook 本体評価

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 発火条件 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|---|
| `cli/helix-session-start` | Hook | PLAN-023, PLAN-022 | `cli/helix-session-start:1` | deprecated wrapper として新パスへ転送 | `SessionStart` | 部分機能 | deprecate | 実体は `cli/libexec/helix-session-start` 側 |
| `cli/helix-check-claudemd` | Hook | 推定: PLAN-019, PLAN-043 | `cli/helix-check-claudemd:1` | deprecated wrapper として新パスへ転送 | `PreToolUse` | 部分機能 | deprecate | 実体は `cli/libexec/helix-check-claudemd` 側のはずだが今回未追跡 |
| `cli/libexec/helix-pre-bash` | Hook | PLAN-018 | `cli/libexec/helix-pre-bash:1` | `llm_guard.py check-bash` を実行 | `PreToolUse:Bash` | 機能している | as-is | fail-close wrapper が明確 |
| `cli/libexec/helix-pre-research` | Hook | PLAN-018 | `cli/libexec/helix-pre-research:1` | `research_tool_guard.py check-tool` を実行 | `PreToolUse:WebSearch/WebFetch` | 機能している | as-is | 役割境界が明確 |
| `.claude/hooks/pretooluse-opus-repo-block.sh` | Hook | PLAN-043 | `.claude/hooks/pretooluse-opus-repo-block.sh:31`, `.claude/hooks/pretooluse-opus-repo-block.sh:69` | Opus の repo 編集を拒否し、必要時のみ env で例外許可 | `PreToolUse:Edit/Write/MultiEdit` | 機能している | as-is | block reason と audit log 出力が揃う |
| `cli/libexec/helix-post-tool-use` | Hook | PLAN-067 | `cli/libexec/helix-post-tool-use:20`, `cli/libexec/helix-post-tool-use:27` | payload から path を抽出し `helix-hook` へ多重配送 | `PostToolUse` | 部分機能 | extend | router はあるが registrar 自動同期は未完 |
| `cli/helix-session-summary` | Hook | PLAN-016 | `cli/helix-session-summary:8`, `cli/helix-session-summary:37` | `cost_log` insert のみ行う静かな shim | `Stop` | 機能している | modify | summary 名称と実体が乖離 |
| `.claude/hooks/post-tool-use.sh` | Hook | PLAN-063 | `.claude/hooks/post-tool-use.sh:8`, `.claude/hooks/post-tool-use.sh:49` | PostToolUse invocation telemetry を `helix.db` へ残す | `PostToolUse` | 機能している | extend | detector / sync の event source として有用 |
| `.claude/hooks/stop.sh` | Hook | PLAN-063 | `.claude/hooks/stop.sh:8`, `.claude/hooks/stop.sh:49` | Stop invocation telemetry を `helix.db` へ残す | `Stop` | 機能している | extend | session accounting と detector 軸に接続できる |

### 1.3 配布用 git hooks

`cli/templates/hooks/*.sh` は Claude/Codex runtime hook ではなく git hook 配布物です。

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 発火条件 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|---|
| `commit-msg` | Hook | 不明 | `cli/templates/hooks/commit-msg:1` | Conventional Commits を強制する | `git commit-msg` | 機能している | as-is | orchestration 補助だが単純で安定 |
| `post-merge` | Hook | 推定: PLAN-002/003 | `cli/templates/hooks/post-merge:1` | merge 後に matrix compile/auto-detect を走らせる | `git post-merge` | 機能している | modify | matrix 中心で、V2 では sync layer に吸収候補 |
| `pre-commit` | Hook | GAP-034, Sec-5, PLAN-067 関連 | `cli/templates/hooks/pre-commit:4`, `cli/templates/hooks/pre-commit:71`, `cli/templates/hooks/pre-commit:115` | secret scan / drift-check / skip annotation lint を実行する | `git pre-commit` | 機能している | extend | Phase 4 detector 連動の前段として有効 |

### 1.4 Hook fail-close / 出力先

- `SessionStart`: `.claude/settings.json:11` は `blockOnFailure=true` だが、`cli/libexec/helix-session-start:95` 以降は内部失敗を極力 warning 化して session 起動停止を避ける設計。
- `PreToolUse Bash/WebSearch`: `.claude/settings.json:25`, `.claude/settings.json:37`, `.claude/settings.json:49` で fail-close。
- `Opus repo block`: `.claude/hooks/pretooluse-opus-repo-block.sh:98` で exit 2。必要なら `.helix/audit/opus-block-events.log` に記録。
- `PostToolUse`: `.claude/settings.json:72` で fail-close。内部 router は `cli/libexec/helix-post-tool-use:26` 以降で最初の失敗 code を返す。
- `Stop`: `.claude/settings.json:85` で fail-open。`cli/helix-session-summary:37` も DB insert 失敗を握り潰す。

## 2. Slash command

### 2.1 一覧

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|
| `/build` | Slash | Upstream agent-skills, HELIX 接続は推定: PLAN-028 | `.claude/commands/build.md:1` | incremental 実装と test-driven-development を起動する | 部分機能 | modify | commit 指示を含み、現行 HELIX の no-commit discipline と衝突 |
| `/code-simplify` | Slash | Upstream agent-skills | `.claude/commands/code-simplify.md:1` | 振る舞い不変の簡素化を行う | 機能している | as-is | role 依存が薄く矛盾も小さい |
| `/plan` (`sdd-plan`) | Slash | Upstream agent-skills | `.claude/commands/sdd-plan.md:1` | task breakdown と acceptance 定義を行う | 機能している | modify | ファイル保存先が `tasks/` 固定で HELIX 工程表と二重管理になりやすい |
| `/review` (`sdd-review`) | Slash | Upstream agent-skills | `.claude/commands/sdd-review.md:1` | 5 軸レビューを実施する | 機能している | as-is | `helix review --uncommitted` 連携が明示されている |
| `/ship` | Slash | Upstream agent-skills | `.claude/commands/ship.md:1` | review/security/qa fan-out から go/no-go を作る | 仕組み倒れ | deprecate | `Agent tool` fan-out を前提にし、ADR-015 / `.claude/CLAUDE.md` と衝突 |
| `/spec` | Slash | Upstream agent-skills | `.claude/commands/spec.md:1` | spec-driven development を始める | 機能している | as-is | L1/L3 入口として素直 |
| `/test` | Slash | Upstream agent-skills | `.claude/commands/test.md:1` | TDD / Prove-It を起動する | 機能している | as-is | HELIX test/gate 連携がある |

### 2.2 引数 / 役割 / 起源補足

- command frontmatter は `description` のみで、引数 schema は持ちません。引数は本文プロンプト解釈頼みです。
- 起源は repo 内では **upstream `agent-skills` ベース** が主で、HELIX 独自 PLAN は接続注記の後付けです。`docs/agent-skills/README.md:20` で 7 command 構成が固定されています。
- `/ship` だけは `.claude/CLAUDE.md:56` の `Agent tool 完全禁止` と真正面から衝突するため、V2 では置換対象です。

## 3. Subagent

### 3.1 現存定義

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|
| `be-api` | Subagent | 不明 | `.claude/agents/be-api.md:1` | API 実装担当 | 部分機能 | deprecate | 定義はあるが v2 は native subagent 非推奨 |
| `be-logic` | Subagent | 不明 | `.claude/agents/be-logic.md:1` | ビジネスロジック担当 | 部分機能 | deprecate | 同上 |
| `code-reviewer` | Subagent | Upstream agent-skills / v2 では PLAN-028 影響 | `.claude/agents/code-reviewer.md:1` | 5 軸レビュー担当 | 部分機能 | modify | role `tl` に役割移譲済みだが `/ship` 互換のため残存 |
| `db-schema` | Subagent | 不明 | `.claude/agents/db-schema.md:1` | DB 設計担当 | 部分機能 | deprecate | `dba` role と重複 |
| `devops-deploy` | Subagent | 不明 | `.claude/agents/devops-deploy.md:1` | deploy/infra 担当 | 部分機能 | deprecate | `devops` role と重複 |
| `qa-test` | Subagent | Upstream agent-skills / v2 では PLAN-028 影響 | `.claude/agents/qa-test.md:1` | QA/coverage 担当 | 部分機能 | modify | `qa` role と重複、`/ship` 互換のため残存 |
| `security-audit` | Subagent | Upstream agent-skills / v2 では PLAN-028 影響 | `.claude/agents/security-audit.md:1` | security audit 担当 | 部分機能 | modify | `security` role と重複、`/ship` 互換のため残存 |

### 3.2 effort level

- `high`: `be-api`, `be-logic`, `code-reviewer`, `db-schema`, `devops-deploy`, `security-audit`
- `medium`: `qa-test`
- 読み取り根拠: `.claude/agents/*.md` frontmatter と `.claude/CLAUDE.md:124`

### 3.3 なぜ残っているか

- `PLAN-028` は `.claude/agents/fe-*.md` 廃止を明示していますが、review/security/qa 系は「個別評価」「Codex role に移譲済なら削除可」と留保しています。根拠: `docs/plans/PLAN-028-helix-v2-orchestration.md:169`.
- `PLAN-063` では entrypoint から `subagent type` を独立扱いせず、hook 経路へ統合したと明記しています。根拠: `docs/plans/PLAN-063-helix-db-detector-system.md:14`.
- したがって現状は **v2 方針上は縮退対象だが、互換資産として残存**している状態です。

## 4. Codex role

### 4.1 Codex role 17 件

`cli/roles/*.conf` 全体は 20 ファイルありますが、純粋な Codex role は 17 件です。内訳は `Codex role 17 + Claude role 3` です。

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|
| `tl` | Codex role | PLAN-028 | `cli/roles/tl.conf:1`, `cli/config/models.yaml:6` | 設計・レビュー・ゲート判定 | 機能している | as-is | v2 TL の正本 |
| `se` | Codex role | PLAN-028 | `cli/roles/se.conf:1`, `cli/config/models.yaml:7` | 高度実装 | 機能している | as-is | v2 SE の正本 |
| `pg` | Codex role | PLAN-028 | `cli/roles/pg.conf:1`, `cli/config/models.yaml:8` | 速度重視の通常実装 | 機能している | as-is | PE 相当の実行名として定着 |
| `qa` | Codex role | PLAN-028, PLAN-065 | `cli/roles/qa.conf:1`, `cli/config/models.yaml:9` | テスト・品質ゲート | 機能している | extend | strictness 強化の中心 |
| `security` | Codex role | PLAN-028, PLAN-066 | `cli/roles/security.conf:1`, `cli/config/models.yaml:10` | セキュリティ監査 | 機能している | extend | systematic scan へ接続余地あり |
| `dba` | Codex role | PLAN-028 | `cli/roles/dba.conf:1`, `cli/config/models.yaml:11` | DB 設計・migration | 機能している | as-is | native subagent 代替 |
| `devops` | Codex role | PLAN-028 | `cli/roles/devops.conf:1`, `cli/config/models.yaml:12` | deploy / infra / SRE | 機能している | as-is | native subagent 代替 |
| `docs` | Codex role | PLAN-028, PLAN-030, PLAN-048 | `cli/roles/docs.conf:1`, `cli/config/models.yaml:13` | docs 実装・整備 | 機能している | as-is | review/implementation 振る舞いが明文化済み |
| `research` | Codex role | PLAN-028 | `cli/roles/research.conf:1`, `cli/config/models.yaml:14` | 技術調査・比較 | 機能している | as-is | G1R の正規入口 |
| `legacy` | Codex role | PLAN-028, PLAN-049 | `cli/roles/legacy.conf:1`, `cli/config/models.yaml:15` | Reverse HELIX / legacy 分析 | 機能している | as-is | reverse 系の正規入口 |
| `perf` | Codex role | PLAN-028 | `cli/roles/perf.conf:1`, `cli/config/models.yaml:16` | 性能計測・最適化 | 機能している | as-is | 専用責務が明確 |
| `fe` | Codex role | PLAN-028 | `cli/roles/fe.conf:1`, `cli/config/models.yaml:17` | FE 実装 | 機能している | as-is | `@fe-*` 廃止後の受け皿 |
| `recommender` | Codex role | PLAN-028, PLAN-024 | `cli/roles/recommender.conf:1`, `cli/config/models.yaml:19` | skill 推挙 | 機能している | extend | Phase 5 automation の中核 |
| `classifier` | Codex role | PLAN-028, PLAN-024 | `cli/roles/classifier.conf:1`, `cli/config/models.yaml:20` | task/skill 分類 | 機能している | extend | skill chain 精度向上余地あり |
| `effort-classifier` | Codex role | PLAN-028, PLAN-024 | `cli/roles/effort-classifier.conf:1`, `cli/config/models.yaml:21` | 工数/難易度分類 | 機能している | extend | budget / auto-thinking 系の前段 |
| `tl-advisor` | Codex role | PLAN-028 | `cli/roles/tl-advisor.conf:1`, `cli/config/models.yaml:25` | TL 級難判断の read-only 助言 | 機能している | as-is | v2 advisory に整合 |
| `impl-sonnet` | Codex role 扱いではなく Claude role 相当 | PLAN-028 | `cli/roles/impl-sonnet.conf:1`, `cli/config/models.yaml:18` | Sonnet write-enabled 実装 | 機能している | modify | 実ファイルは `cli/roles/` 配下だが provider=claude_code |

### 4.2 model / thinking の要点

- TL / QA / TL-advisor: `gpt-5.5` high
- SE / FE / Research / Legacy / Perf / Security: `gpt-5.4`
- PG / Docs: `gpt-5.3-codex-spark`
- DBA / DevOps: `gpt-5.3-codex`
- Recommender / Classifier / Effort-classifier: `gpt-5.4-mini`
- 正本: `cli/config/models.yaml:5`

## 5. Claude role

### 5.1 Claude role 5 件

TASK 例示の `pm-advisor / tl-advisor / pmo-sonnet / pmo-haiku / impl-sonnet` は、実体としては `cli/roles/*.conf` に定義されています。

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|
| `pmo-sonnet` | Claude role | PLAN-028 | `cli/roles/pmo-sonnet.conf:1`, `cli/config/models.yaml:22` | 判断伴う read-only PMO | 機能している | as-is | v2 PMO の正規経路 |
| `pmo-haiku` | Claude role | PLAN-028 | `cli/roles/pmo-haiku.conf:1`, `cli/config/models.yaml:23` | docs/** 限定軽作業 PMO | 機能している | as-is | 許可パスが明確 |
| `pm-advisor` | Claude role | PLAN-028 | `cli/roles/pm-advisor.conf:1`, `cli/config/models.yaml:24` | PM 級難判断の read-only 助言 | 機能している | as-is | ADR-015 と整合 |
| `impl-sonnet` | Claude role | PLAN-028 | `cli/roles/impl-sonnet.conf:1`, `cli/config/models.yaml:18` | Sonnet write-enabled 実装 | 機能している | modify | PMO read-only 例外として扱いを明確化すべき |
| `tl-advisor` | Claude role ではないが cross-provider advisor | PLAN-028 | `cli/roles/tl-advisor.conf:1`, `cli/config/models.yaml:25` | TL 級助言 | 機能している | as-is | 実行主体は Codex、CLAUDE side からも参照される |

## 6. Native skill

### 6.1 カテゴリ別件数

実測: `find skills -type f -name SKILL.md | wc -l` = **104**

| カテゴリ | 件数 |
|---|---:|
| `workflow` | 31 |
| `agent-skills` | 23 |
| `common` | 12 |
| `automation` | 8 |
| `project` | 8 |
| `advanced` | 6 |
| `design-tools` | 5 |
| `tools` | 4 |
| `writing` | 4 |
| `integration` | 3 |

### 6.2 評価

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|
| `skills/` catalog 全体 | Skill | 複数 PLAN、正本宣言は `SKILL_MAP` | `skills/SKILL_MAP.md:1` | phase/gate/role を横断する知識正本 | 機能している | extend | Phase 4/5 で detector と sync の対象になる |
| `agent-skills` 群 | Skill | Upstream + HELIX 接続 | `docs/agent-skills/README.md:127` | slash command 背景知識 | 部分機能 | modify | `/ship` 系と v2 方針の差分整理が必要 |
| HELIX core skill 群 (`workflow/*`, `common/*`, `project/*`) | Skill | HELIX 本体 | `skills/SKILL_MAP.md:1` | 実務フローの正本 | 機能している | as-is | role conf から直接参照される |

## 7. Slash command と Skill の対応

### 7.1 slash command → skill

| Slash command | 主 skill |
|---|---|
| `/spec` | `agent-skills:spec-driven-development` |
| `/plan` | `agent-skills:planning-and-task-breakdown` |
| `/build` | `agent-skills:incremental-implementation`, `agent-skills:test-driven-development` |
| `/test` | `agent-skills:test-driven-development` |
| `/review` | `agent-skills:code-review-and-quality` |
| `/code-simplify` | `agent-skills:code-simplification` |
| `/ship` | `agent-skills:shipping-and-launch` |

根拠: `.claude/commands/*.md`

### 7.2 `helix skill chain` の推挙経路

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|
| `helix skill chain` | Skill | PLAN-024, PLAN-022 | `cli/helix-skill:61`, `cli/helix-skill:101`, `cli/lib/skill_dispatcher.py:223` | task 文から skill 推挙し、そのまま role/agent dispatch へ接続する | 機能している | extend | Role/Skill orchestration の正規入口 |
| `SessionStart 自動推挙ヒント` | Skill | PLAN-022 | `cli/libexec/helix-session-start:135`, `cli/libexec/helix-session-start:171` | handover task から top-1 skill/agent を自動提示する | 機能している | extend | Phase 5 自動化の下地 |

### 7.3 `skill_usage` 記録機構

| 項目名 | 層 | 起源 PLAN | 実装ファイル | 役割 | 状態 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|
| `skill_usage` insert/update | Skill | PLAN-024, PLAN-063 で活用拡大 | `cli/lib/skill_dispatcher.py:323`, `cli/lib/skill_dispatcher.py:340` | skill 実行の usage / outcome / session_id を DB 記録する | 機能している | extend | detector 軸や budget 学習の基盤 |
| detector 参照 | Skill | PLAN-063 | `docs/features/PLAN-063/D-DETECTORS/axis-04-skill-decay.md:7`, `docs/features/PLAN-063/D-DETECTORS/axis-13-model-skill.md:7` | skill decay / model-skill detector が `skill_usage` を読む | 機能している | extend | Phase 4 の検出ガードレールに直結 |

## 8. doc 末尾サマリ

### 8.1 層別件数

| 層 | 件数 | 備考 |
|---|---:|---|
| Hook (runtime 登録) | 7 | `.claude/settings.json` 登録分 |
| Hook (git template) | 3 | `cli/templates/hooks/*` |
| Slash command | 7 | `.claude/commands/*.md` 実数 |
| Subagent | 7 | `.claude/agents/*.md` 実数 |
| Codex role | 17 | `cli/roles/*.conf` から Claude role を除いた数 |
| Claude role | 4 | `pmo-sonnet`, `pmo-haiku`, `pm-advisor`, `impl-sonnet` |
| Cross-provider advisor | 1 | `tl-advisor` |
| Native skill | 104 | `skills/**/*.md` の `SKILL.md` 実数 |

### 8.2 「機能している」「仕組み倒れ」分類

- 機能している:
  - `helix-pre-bash`, `helix-pre-research`, `pretooluse-opus-repo-block`, `helix-session-start`
  - Codex role 群、Claude role 群
  - `helix skill chain` + `skill_usage`
- 仕組み倒れ:
  - `/ship`
    - Agent tool fan-out 前提で、現行 v2 方針では標準経路に載らない
  - deprecated wrapper のまま残る `cli/helix-session-start`, `cli/helix-check-claudemd`
    - 呼び出しは通るが、正本とズレた古い導線

### 8.3 V2 で廃止予定

- native subagent の恒常運用
  - 理由: `PLAN-028` / `ADR-015` が Agent tool 依存の orchestration を縮退対象化
- `/ship` の現行 fan-out 実装
  - 理由: Agent tool 禁止と衝突
- `Stop hook session-summary` という命名
  - 理由: 現実には `cost_log` accounting shim

### 8.4 V2 で新規追加 / 強化候補

- detector feedback hook
  - 根拠: `PLAN-067` 軸 C/D、`PLAN-063` detector integration
- agent stop hook / session telemetry hook の統合
  - 根拠: `.claude/hooks/stop.sh`, `.claude/hooks/post-tool-use.sh`
- file→DB sync hook
  - 根拠: `PLAN-067` 軸 A/B/E

### 8.5 5 層 (PM / Orch / Cmd / Skill / Verify) への配置マッピング

| 5 層 | 主な配置 |
|---|---|
| PM | `pmo-sonnet`, `pmo-haiku`, `pm-advisor`, handover / approval 系 |
| Orch | `.claude/settings.json` hooks, `cli/libexec/helix-session-start`, `cli/libexec/helix-post-tool-use`, `helix codex` / `helix claude` |
| Cmd | `.claude/commands/*.md`, `cli/helix-skill`, git hooks |
| Skill | `skills/**/SKILL.md`, `skill chain`, recommender/classifier |
| Verify | `qa`, `security`, `code-reviewer`, detector / `skill_usage` / telemetry |

## ソース

- `.claude/settings.json:1`
- `.claude/commands/*.md`
- `.claude/agents/*.md`
- `.claude/CLAUDE.md:56`
- `cli/roles/*.conf`
- `cli/config/models.yaml:1`
- `cli/helix-skill:61`
- `cli/lib/skill_dispatcher.py:223`
- `cli/libexec/helix-session-start:135`
- `docs/plans/PLAN-028-helix-v2-orchestration.md:28`
- `docs/adr/ADR-015-helix-v2-orchestration.md:27`
- `docs/plans/PLAN-043-consolidated-carry-resolution.md:235`
- `docs/plans/PLAN-063-helix-db-detector-system.md:14`
- `docs/plans/PLAN-067-helix-automation-layer.md:63`
