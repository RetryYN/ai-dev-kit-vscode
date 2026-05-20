<!-- helix_template_version: 4 -->
# HELIX

@./skills/SKILL_MAP.md
@./helix/HELIX_CORE.md
@./helix/CODEX_TL_MODE.md

## 概要
HELIX は、AI エージェントを `plan` / `task` / `role` / `gate` / `handover` で制御する開発フロー・CLI・スキル群のリポジトリ。

## 技術スタック
- Frontend: なし。CLI とドキュメント中心
- Backend: Bash CLI + Python helper modules
- DB: SQLite (`.helix/helix.db` などの project-local runtime state)
- インフラ: Git hooks、Claude Code hooks、Codex CLI、Bats、pytest

## アーキテクチャ
- `cli/`: `helix` ルーターとサブコマンド実装
- `cli/lib/`: Python helper、SQLite access、learning / routing utilities
- `cli/templates/`: `helix init` が配布する project template
- `helix/`: HELIX core policy、Codex TL mode、ユーザー向け設定例
- `skills/`: HELIX skill と skill map
- `docs/commands/`: CLI 利用導線の正本
- `.claude/`: Claude Code hook / command / agent runtime 設定
- 詳細レイアウトマップ: [docs/architecture/cli-layout.md](docs/architecture/cli-layout.md)

## コーディング規約
- 既存 CLI の Bash/Python 分担に合わせる。単純な CLI glue は Bash、状態集計や構造化処理は Python helper に寄せる。
- 実装前に対象ファイルを Read して、既存パターンへ合わせる。
- 変更範囲は要件に必要なファイルへ限定する。runtime state やユーザー未コミット変更を巻き戻さない。
- Codex / Claude Code は API 直叩きではなく、契約プラン + CLI / hook を HELIX が管理する前提で扱う。
- テストなしの完了宣言は禁止。Bash 変更は `bash -n`、Python 変更は `python3 -m py_compile`、CLI 変更は Bats / pytest を必要範囲で実行する。

## コミット規約
- 1 commit = 1 PLAN または 1 トピック。独立した責務 (例: 機械的 refactor + 新規ドキュメント追加 + 表記統一) を 1 commit に混ぜない。
- 大型 commit (>30 ファイル または +1500 行) は責務単位で分割する。分割を躊躇するときは、commit メッセージ body に「なぜ 1 commit にまとめたか」を明記する。
- `scope` はドメイン名 (例: `session-summary`, `code-catalog`, `helix-codex`) を 1 つに絞る。複数ファイル名のカンマ列挙 (`scope1,scope2`) は禁止。複数モジュールに跨る変更は本文 body に列記する。
- prefix は `feat / fix / chore / docs / test / refactor`。コード変更を伴わない PLAN ドキュメント更新は `docs(plan-NNN):` を使う。
- 自動生成物 (Stop hook によるセッション記録、Codex agent local state など) は手動 commit に取り込まない。`.gitignore` で除外するか、`git add` で対象を明示する。

## ディレクトリ構造
```text
cli/
  helix
  helix-*
  lib/
  tests/
docs/
  commands/
helix/
skills/
.claude/
```

## コマンド
- CLI help: `cli/helix help`
- 全体テスト: `cli/helix test`
- shell 回帰: `cli/helix test --no-pytest --bats-only`
- Python 回帰: `python3 -m pytest cli/lib/tests/ -q --tb=short`
- Claude Code prompt 生成: `cli/helix claude --role <role> --task "..." --dry-run`
- Codex 委譲: `helix codex --role <role> --task "..."`

## 禁止事項
- API key、secret、PII、credential を `CLAUDE.md` / `AGENTS.md` / skill / docs に書かない。
- 認証、認可、決済、PII、ライセンス、本番影響、destructive data operation は人間確認なしに仕様確定しない。
- 外部 provider SDK や認証情報を前提にした fallback を HELIX の通常導線として追加しない。
- `.helix/` runtime state、`.claude/settings.local.json`、`.codex` などのローカル副産物をドキュメント目的で追跡対象にしない。

## HELIX ワークフロー
- タスク受領時は `helix/HELIX_CORE.md`、`skills/SKILL_MAP.md`、`helix/CODEX_TL_MODE.md` を確認する。
- `.helix/handover/CURRENT.json` がある場合は `helix handover status --json` を確認し、stale でなければ Next Action に従う。
- Forward: `size` -> `plan` -> `matrix` -> `gate` -> `sprint` -> `test`
- Reverse: `reverse <type> R0` -> `R1` -> `R2` -> `R3` -> `R4` -> `rgc`
- Scrum: `scrum init` -> `backlog` -> `plan` -> `poc` -> `verify` -> `decide`
- AI harness: `plan` / `task` の文脈を `codex` / `claude` / `team` / `review` / `handover` で管理する。

詳細は [docs/commands/index.md](docs/commands/index.md) と [docs/commands/ai-harness.md](docs/commands/ai-harness.md) を参照。

## Codex との対応
Codex CLI 向けの正本は [AGENTS.md](AGENTS.md)。プロジェクト知識はこの `CLAUDE.md` と揃え、Codex 固有の TL 動作・検証・handover ルールは `AGENTS.md` に寄せる。

## モデル割当（真実は `cli/config/models.yaml`）

| 委譲先 | ロール | 主な担当 |
|--------|------|---------|
| Opus (自身) | PM | チャットのみ。言語化・タスク分解・統合・エスカレーション判断。コード編集禁止 |
| Codex 5.5 | TL | 設計・技術判断・レビュー・高度実装・検証 |
| Codex 5.3-codex-spark | PE | 単機能実装・速度重視実装 |
| Codex 5.4 | SE | 契約・複雑実装・リファクタリング |
| Codex 5.3 | Security / DBA / DevOps / Perf | セキュリティ監査・DB・インフラ・性能 |
| Codex 5.4-mini | Recommender / Classifier | スキル推挙・タスク分類 |
| Sonnet | PMO（判断伴う） | 構造化チェック、ドキュメント状況把握（read-only）。`.claude/agents/pmo-sonnet` (sonnet) 経由 |
| Haiku 4.5 | PMO（軽作業） | Web 検索・`docs/**` 限定軽作業（read-write）。`.claude/agents/pmo-haiku` (haiku) 経由 |

- ドキュメントと実装が乖離した場合は **実装 (`cli/config/models.yaml`) を正** とする。本表は周知用。
- ロール定義の正本は [cli/ROLE_MAP.md](cli/ROLE_MAP.md)。

## Advisor 召喚ルール（運用）

チャット PM (Opus / Sonnet いずれも) と実装担当が **大局判断 / 技術選択で迷ったとき** は、自前で結論を出す前にアドバイザーを召喚する。最終判断は呼び出し側 (PM またはユーザー) が下す。

| アドバイザー | model | 召喚コマンド | 召喚タイミング |
|---|---|---|---|
| **pm-advisor** | claude-opus-4-7 (read-only) | `helix claude --role pm-advisor --execute --task "..."` | スコープ / 優先度 / 大局リスク / HELIX フェーズ整合 / 委譲先選択 で迷う |
| **tl-advisor** | gpt-5.5 high (read-only) | `helix codex --role tl-advisor --task "..."` | 設計選択 / 契約・API 妥当性 / テスト戦略 / リファクタ判断 で迷う |

運用原則:
- **PM が Sonnet で動いているチャット** では、難判断に当たったら必ず pm-advisor (Opus) に相談する。Sonnet 単独で大局判断を確定させない
- **PM が Opus でも**、自分の判断に確信が持てない技術判断は tl-advisor を呼んで反論を取る (adversarial check)
- 実装担当 (Sonnet / Codex) は契約や設計で迷ったら tl-advisor、スコープで迷ったら pm-advisor を呼ぶ
- アドバイザーは read-only。コード編集や状態変更は行わない (構造化助言のみ返す)
- 呼び出した task / 助言内容は会話または final report に残し、判断トレースを失わない

## Agent tool は PMO + PdM 限定許可（v2.2、2026-05-15 改訂）

PMO subagent (`pmo-sonnet` / `pmo-haiku`) と PdM subagent (`pdm-tech-innovation` / `pdm-marketing-innovation` / `pdm-innovation-manager`) のみ許可。
それ以外の subagent (`be-api` / `be-logic` / `db-schema` / `qa-test` / `security-audit` / `code-reviewer` / `devops-deploy`) は引き続き禁止する。Codex 委譲または Opus 直接で対応する。

判定:
- PMO subagent OK: `Agent({ subagent_type: "pmo-sonnet", ... })` または `pmo-haiku`
- 他 subagent 禁止: 過去 v2 規約継続。Codex / Opus 直接で対応
- 判断基準は変更なし: 同一タスク Read 200+ 行 / Grep 3+ / 複数視点 / 長文 doc 全体 Read で委譲必須

| 活用領域 | Agent | 補足 |
|---|---|---|
| HELIX 内目星付け (skills/templates/cli 軽量検索) | Agent({subagent_type: "pmo-helix-scout"}) | 候補列挙 |
| project 内目星付け (code/docs 軽量検索) | Agent({subagent_type: "pmo-project-scout"}) | 候補列挙 |
| 海外技術思想翻案 (G0.5 前後) | Agent({subagent_type: "pdm-tech-innovation"}) | 翻案 |
| 海外マーケ思想翻案 (G0.5 前後) | Agent({subagent_type: "pdm-marketing-innovation"}) | 翻案 |
| PdM 統合・新方向性策定 (L1 接続) | Agent({subagent_type: "pdm-innovation-manager"}) | 統合判断 |
| OSS/plugin 探索・転用判断 | Agent({subagent_type: "pmo-tech-fork"}) | 外部 GitHub 探索 |
| 設計手法/概念の外部精読 | Agent({subagent_type: "pmo-tech-docs"}) | 外部 doc 精読 |
| 最新 Tech 動向 sweep (週次想定) | Agent({subagent_type: "pmo-tech-news"}) | 時事収集 |
| HELIX framework 内資産探索 (skills/templates/cli/docs) | Agent({subagent_type: "pmo-helix-explorer"}) | 詳細探索 |
| 現在 project 内資産探索 (code/docs/config) | Agent({subagent_type: "pmo-project-explorer"}) | 設計整合 |

PMO subagent (pmo-sonnet / pmo-haiku) の使い分け:
- pmo-sonnet: 判断伴う read-only / docs/PLAN 構造化チェック / 長文解析
- pmo-haiku: Web 検索目星付け（初期 sweep） / docs/** 軽修正 / コスト重視軽作業

helix-claude --role pmo は deprecated。新規呼び出しは `Agent({subagent_type: "pmo-sonnet"})` または `Agent({subagent_type: "pmo-haiku"})` 推奨。既存 dispatch は段階的に移行。

委譲必須の判定基準 (変更なし):
- 同一タスクで Read 合計が 200 行を超える見込み
- Grep / Glob が 3 回以上必要
- 同じファイルを複数視点で見る
- 長文ドキュメント (PLAN.md / review.json / SKILL.md / CURRENT.md) の全体 Read

Opus 直接 Read してよい範囲:
- handover status / phase.yaml / 単発短ファイル (< 100 行)
- Edit 直前の対象箇所
- ユーザー明示指定の 1 ファイル

**禁止**: PMO 以外の subagent 呼び出し / Opus がバックエンドコード直接 Edit / 「自分でやった方が早い」を理由とする委譲基準超え / **subagent frontmatter の許可 model family と異なる model 指定** (想定外 Opus 発火防止)

### Agent tool guard hook (2026-05-19、fail-close)

`.claude/hooks/pretooluse-agent-guard.sh` (PreToolUse matcher=Agent) が以下を fail-close で機械強制:

| 条件 | 挙動 |
|------|------|
| subagent_type 未指定 (general-purpose default) | exit 2 で block |
| subagent_type が許可 12 種 (PMO 9 + PdM 3) 外 | exit 2 で block |
| `tool_input.model` 省略 | pass (frontmatter で自動起動) |
| `tool_input.model` 明示 + frontmatter と family 一致 | pass |
| **`tool_input.model` 明示 + frontmatter と family 不一致** | **exit 2 で block (想定外 Opus 発火防止)** |

subagent ごとの許可 model family (frontmatter 正本、`.claude/agents/*.md`):
- **opus**: pdm-tech-innovation / pdm-marketing-innovation / pdm-innovation-manager (PdM 3)
- **sonnet**: pmo-sonnet / pmo-helix-explorer / pmo-project-explorer / pmo-tech-docs / pmo-tech-fork / pmo-tech-news (PMO Sonnet 6)
- **haiku**: pmo-haiku / pmo-helix-scout / pmo-project-scout (PMO Haiku 3)

挙動例:
- `Agent({subagent_type: "pmo-sonnet"})` → pass (frontmatter sonnet 自動起動)
- `Agent({subagent_type: "pmo-sonnet", model: "opus"})` → **block** (Sonnet 系を Opus override 禁止)
- `Agent({subagent_type: "pmo-haiku", model: "opus"})` → **block** (Haiku 系を Opus override 禁止)
- `Agent({subagent_type: "pdm-tech-innovation", model: "opus"})` → pass (frontmatter Opus 一致)
- `Agent({subagent_type: "pdm-tech-innovation", model: "sonnet"})` → **block** (PdM を Sonnet override 禁止)

bypass: `HELIX_ALLOW_RAW_AGENT=1` 環境変数 + 理由を evidence (会話 / final report) に残すこと。

検証: 12-case strict smoke 全 PASS (commit 3ae4af3、想定外 Opus 発火 T2/T3/T12 完全 block 確認済)。

## 並列実行ルール（必須、default 上限 8 並列）

依存関係がないタスクは **必ず並列** で投入。直列にしない。**default 上限 = 8 並列**、これを下回る運用 (1-2 並列で済ます) は怠慢として禁止する。

判定（1 つでも該当 → 直列、全て NO → 並列）:
- 編集対象ファイルが衝突する
- 後段が前段の出力を入力にする
- 共有状態 (helix.db / phase.yaml / handover の同フィールド) を同時更新する

並列投入前に「衝突するファイル」「後段依存」を 1 行で書き出して根拠を残す。

### 8 並列達成のための構成パターン
- **Codex 委譲 N 並列 + Opus 軽量タスク並行**: ファイル衝突しない範囲で最大化
- **subagent (pmo-sonnet) + Codex pg/se 同時投入**: pmo は read-only/docs、Codex は code 実装
- **前段 task 走行中の独立 followup 並走**: TL spine 凍結待ち / E2E test 待ち中でも独立タスクは並走
- **prompt 作成は Write 並列で先行**: Codex 投入の事前に N 個の prompt file を並列 Write、その後一括投入

8 並列に達しないとき、必ず「依存判定で何件直列必須か」「8 まで埋められない理由」を会話に書き出す。出さずに 1-2 並列で済ませるのは禁止。

## V-model 4 artifact 双方向 trace 原則 (2026-05-17 確立 / 訂正、PLAN-075)

4 artifact は別文書として存在し、双方向 trace で繋ぐ:

```
① 設計 (D-API EXT 等)  ←対応→  ③ テスト設計 (test-design/*.md)
       ↓                              ↓
② 実装コード            ←対応→  ④ テストコード
```

| HELIX 層 | ① 設計 | ③ 対応するテスト設計 |
|---|---|---|
| L1 要件定義 | 要件 / 受入条件 | **受入テスト設計** |
| L2 全体設計 | CONCEPT / ADR | **総合テスト設計** |
| L3 詳細設計 | D-API / D-DB | **結合テスト設計** |
| L3-L4 機能設計 | endpoint / 関数 schema | **単体テスト設計** |

詳細: `helix/HELIX_CORE.md §設計⇔テスト対応`。

**禁止**: 4 artifact のうち 2 つ以上を 1 文書に統合 (例: 設計とテスト設計を同じ文書、テスト設計とテストコードを同じ文書)。**正解**: 4 artifact を別文書、双方向 reference で trace

## subagent 工程マッピング (2026-05-17、PLAN-076)

subagent 14 種を 2 分類:

- **mandatory by phase (10 種)**: pdm-* / pmo-tech-fork/docs/explorer/scout/sonnet。工程で必須、`helix agent fire-mandatory --phase Lx` で一括投入、helix.db で audit、G2-G4 で lint
- **on-demand by judgment (4 種)**: pmo-haiku / pmo-tech-news / pm-advisor / tl-advisor。判断に応じて任意、`helix agent suggest`

詳細: `helix/HELIX_CORE.md §工程別 subagent 起動マップ`。

## Sprint Plan 標準構造 (2026-05-17、PLAN-077)

L4 実装中の Sprint Plan は標準 8 ステップに固定化:

- Step 1-3: Entry / 着手前調査 / 実装
- **Step 4-6 (mandatory in sprint)**: 機械チェック (py_compile / lint) + テスト起動 (該当 test / 全回帰) + レビュー (セルフ / pmo-sonnet)
- Step 7-8: commit + Exit 条件確認

Sprint Exit 前に mandatory 全通過必須、`helix sprint complete --auto-check` で機械化。詳細: `helix/HELIX_CORE.md §Sprint Plan 標準構造`。

## ScheduleWakeup 運用ルール (task-notification 信用、2026-05-16 確立、2026-05-19 適用条件補強)

`Bash(run_in_background: true)` で投入した command は **harness が完了時に task-notification を自動送信** する。ScheduleWakeup を併用するな:

- `run_in_background: true` の結果待ち → **ScheduleWakeup 不要**。task-notification 自動通知を信用して他の作業を進める
- 並行タスクが無くなったら turn を終え、harness が完了通知で自動再開させる ← **適用条件**: (a) 全 carry 消化済 AND (b) ユーザー時間枠指示が満たされている、両方 AND の時のみ
- carry が残っている / ユーザー時間枠 (例「24 時まで連続作業」) が満たされていない場合は turn を終えず、次の wave を投入し続ける (2026-05-19 14h アイドル事故で確立、[[feedback_dont_stop_with_carry_remaining]] 参照)
- ScheduleWakeup は **harness 追跡外の外部状態 polling 専用** (GitHub Actions / CI / リモートデプロイ監視 / 別 process が書き出すファイルの polling)
- 上記以外で ScheduleWakeup を使うのは禁止 (cache miss + cost + 「動いてない」印象 の三重損失)

## PLAN ⊃ ADR レイヤー併存 (2026-05-19 訂正確立、HELIX 思想 = PLAN は implementation tree、ADR は L2 snapshot)

**前提訂正**: PLAN は「L4 実装計画」ではなく **1 トピックの implementation tree (L1〜L4 全範囲を内包)**。ADR は PLAN tree 内で大局判断が必要な箇所の **L2 snapshot (任意、必要時のみ)**。「ADR 先 / PLAN 後」順序ではなく、**同じ PLAN trunk 内でレイヤー併存** (L2-MASTER §0 line 36 の正規 pattern「PLAN-084 で L1 確定、ADR-018/019 で L2 凍結」)。

```
PLAN-NNN = 1 トピックの implementation tree
├── L1 確定: PLAN.md §背景 / 要件 / DoD
├── L2 凍結: ADR-NNN snapshot (大局判断を別 file 永続化、必要時のみ)
├── L3 詳細: D-API / D-DB (PLAN.md 内 or 別 file)
└── L4 実装: Sprint .1〜.5 (PLAN.md §実装計画)
```

判定: 新規 PLAN 起票時 + 既存 PLAN 進行中、**L2 大局判断が含まれるか** を確認 → Yes なら ADR snapshot を併設する。

- ADR snapshot が必要なケース (PLAN tree 内に L2 大局判断あり):
  - 新 framework 採用判断 (例: Web 検索ガードレール採用、TodoWrite × agent slot 連動採用、active guidance loop pattern 採用)
  - fail-close 化 / advisory→fail-close 段階遷移判断
  - 外部新仕様の採用判断 (例: Claude Code 2.1.139 continueOnBlock、新 SDK バージョン)
  - 既存方針転換 (例: PRAGMA user_version → schema_version table)
  - 既存 framework 大規模変更 (例: hook 出力形式変更、subagent 許可リスト変更)
- PLAN のみ (ADR snapshot 不要) なケース:
  - 既存 ADR で凍結された方針の実装 (PLAN-085/086 が ADR-020 を実装する形)
  - bug fix / refactor (機能変更なし)
  - 既存 framework 内 Phase 拡張 (新方針なし)
- 違反検出: `helix doctor check_plan_adr_snapshot` (新設予定) で PLAN tree 内に L2 大局判断が含まれるのに ADR snapshot 不在を fail-close 化
- 詳細 + 逆引き救済 4 件 (本 session で発覚): [[feedback_adr_before_plan_violation]]

## PLAN 規約 framework v5 (2026-05-20 確立、TL 4 ラウンド + ユーザー 12+ ターン訂正経緯)

詳細 = `docs/v2/V5-plan-outlines.md` (pmo-sonnet 起票予定) + `memory/project_2026_05_20_v5_framework_evolution_recovery.md`。

### V5 framework 18 要素 (2026-05-20 拡張、turn 14-15 で 18 番追加)
1. PLAN = self-contained workflow ルール doc (TodoWrite → PLAN 永続化置換)
2. V-model layer (L0-L11、L3.5/L4.5 追加) × drive (be/fe/fullstack/scrum/reverse/db/agent/poc/troubleshoot) matrix
3. 種別正規化 (design / impl / poc / reverse / troubleshoot / refactor / retrofit / research / add-design / add-impl / **recovery**)
4. matrix 外 / kind 不在を helix plan CLI で fail-close
5. 生成物 trace (frontmatter `generates`、V2 BR-V1 4 layer chain 直結)
6. 依存関係 graph (frontmatter `dependencies`: requires/parent/blocks)
7. agent slot 割当 (frontmatter `agent_slots`)
8. PostToolUse hook で PLAN.md → helix.db 自動登録
9. PLAN ↔ 設計 doc drift 検出 (helix doctor)
10. 進捗 trace (plan.db sprint_progress)
11. ADR snapshot 必須化 (L2 大局判断あれば、PLAN ⊃ ADR レイヤー併存)
12. kind 別 workflow template embed (Step 1-N)
13. V-model TDD 駆動 (設計⇔テスト設計対 pair freeze + 実装 TDD + QA 追加テスト)
14. PoC = Scrum × Reverse 連携 matrix (Scrum 6 type × Reverse 5 type)
15. GitHub 運用ルール統合 (`helix_github_workflow_rules.md` ベース)
16. helix_improvement_plan_draft.md 6 Phase 統合
17. リカバリープラン kind (recovery、turn 13 確立)
18. **自動走行 framework 5-layer** (turn 14-15 確立、claw0 + agent_farm + claude-brain + learn-claude-code 4 OSS シナジー):
    - Layer 1: PostToolUse(Write|Edit + PLAN.md) → helix.db.task_queue auto-enqueue
    - Layer 2: statusLine hook で context % 先回り監視 (>50% / 30-50% / ≤30% / ≤20% の 4 段階)
    - Layer 3: PreCompact hook (v1.0.48+) で auto-compact 前 state 永続化、必要時 decision:block
    - Layer 4: SessionStart(cleared|compacted) + UserPromptSubmit で関連履歴自動注入 (claude-brain pattern)
    - Layer 5: ScheduleWakeup 15min heartbeat (claw0 cold-start) で carry check + 自動 task pop
    - 解決問題: 14h idle 事故 + context 枯渇による中断 + carry 残し放置の 3 課題同時解消
    - 実装事例: claude-brain (6 Python hook で SQLite 無損失キャプチャ + UserPromptSubmit 履歴注入)
    - /clear /compact の発火は不可確定 (Anthropic Feature Request #20267) → 「発火」ではなく「前後の state capture + 復元」を 100% 自動化

### V5 framework 3 層構造 (turn 19、ユーザー指摘で確立、Layer A→B→C 着手順序)

V モデル強化構想は 3 層: **工程管理ハーネス + helix.db 型ハーネス + 連携自動化ハーネス**。DB schema や hook 設計の前に、工程と管理 doc のルール整備 + どう動かすかが決まらないと start できない。V5 18 要素を 3 層に分解し、依存順序を遵守:

```
[Layer A] 工程・ドキュメント運用ルール整備 ← V2 企画書反映、Layer B/C の前提
  V5 要素 1-7 (PLAN self-contained / matrix / 種別 / fail-close / generates / dependencies / agent_slots)
  V5 要素 11-17 (ADR snapshot / template embed / V-model TDD / PoC=Scrum×Reverse / GitHub / helix_improvement / recovery)
       ↓
[Layer B] helix.db 型ハーネス ← Layer A の実体化
  V5 要素 8 (DB 受け側) / 9 (drift) / 10 (進捗 trace)
  単一実行正本決定 (task_queue / TodoWrite / helix job / handover 競合解消、TL v5 P1)
       ↓
[Layer C] 連携自動化ハーネス ← Layer A/B を hook で動かす
  V5 要素 8 (hook 本体) / 18 (自動走行 framework 5-layer)
  PoC C 案 (Layer 4+5) のみ並行可、本実装 (Layer 1-3) は A/B 確定後
```

**次 session 正順 (Layer A→B→C 遵守)**:
0. V2 企画書見直し (`docs/v2/CONCEPT.md` / L1-REQUIREMENTS / L2-MASTER §0/§12) ← Layer A 正本確認
1. Layer A 確定: V5 要素 1-7, 11-17 を企画書に反映 + ADR-021〜024 後追い snapshot 起票
2. Layer B 確定: 単一実行正本決定 + helix.db schema 設計
3. Layer C 並行: PoC C 案 (Layer 4+5) を Layer A/B 確定待たず先行
4. PLAN 起票: Layer A 確定後に PLAN-MM-001 → PLAN-091(A) → PLAN-092/093(B) → PLAN-099(C) → PLAN-100(retrofit)

### 9 PLAN + 8 ADR 起票案 (次 session 開始時、PLAN-099 を turn 14 で追加)
```
parent: PLAN-MM-001 (設計プラン、V5 全体構想)
├── PLAN-091 ↔ ADR-025: framework 本体 (matrix + 種別 + template embed)
├── PLAN-092 ↔ ADR-026: PostToolUse 自動登録 + helix.db v35 schema
├── PLAN-093 ↔ ADR-027: drift 検出 + 進捗 trace + Curator
├── PLAN-100 ↔ ADR-021〜024: 既存 retrofit + V2 全面見直し (★ PLAN-099 完遂後の後段、V5 framework 実装 scope = PLAN-091〜099 に限定)
├── PLAN-095 ↔ ADR-028: PoC = Scrum × Reverse matrix
├── PLAN-096 ↔ ADR-029: GitHub Actions + ブランチタイプ別パイプライン
├── PLAN-097 ↔ ADR-030: 抽象化層 (スキル/ワークフロー/ハーネス) + エスカレーション
├── PLAN-098 ↔ ADR-031: リカバリープラン kind 正規化
└── PLAN-099 ↔ ADR-032: 自動走行 framework 5-layer (turn 14-15 追加、statusLine + PreCompact + SessionStart cleared + UserPromptSubmit + heartbeat、14h idle + context 枯渇 + carry 放置の三課題同時解決)
```

### TL 5 ラウンド全 passed (V5 確定、turn 17 で round 5 完了)
- v1 (matrix + 種別): passed (bs9wuvqcs)
- v2 (+ 依存 + agent slot + 自動登録): passed (PLAN-091〜093 分割推奨、bppaf3fwe)
- v3 (+ template embed): passed (bkac94gnw)
- v4 (+ V-model TDD + PoC リバース合流): passed (baq742e62)
- **v5 (+ 自動走行 framework 18 番要素): passed_with_minor_changes** (bdnmyhznq、修正条件付き次 session 起票 OK)

### TL v5 round 5 修正条件 (起票時必須遵守、5 重要 + 8 補助 + P0/P1 指摘)

**5 重要項目**:
1. **設計選択**: V5 に統合、実装単位は分離。PLAN-091 (規約本体) と PLAN-099 (runtime substrate) を **独立子 PLAN** として並行起票、feature flag / warn-only / fail-close 段階導入
2. **PoC 戦略**: **C 案 = Layer 4 (復元) + Layer 5 (heartbeat) を先行 PoC** (0.5-1 session)、Layer 1-3 は PLAN-091/092/093 の schema・hook 正本確定後接続。A 案 (2-3 session) / B 案 (4-6 session) は非効率
3. **PreCompact decision:block 制限**: 「`重要 state 永続化失敗` AND `未保存の L2/L3/ADR 判断がある` AND `一回だけ`」に限定。常用は context 枯渇継続事故リスク、通常は backup + warning
4. **statusLine + Stop 役割分担**: 両方必要。Stop は軽量化 (handover snapshot / telemetry / stale release のみ)、statusLine に debounce + hysteresis hysteresis 必須 (警告連打防止)
5. **claude-brain pattern**: **HELIX 独自再実装** が筋。会話 SQLite 全量キャプチャは secret/PII/予算情報リスク → `transcript_path 参照 + 要約 state + 明示的 retention` 正本、UserPromptSubmit 注入は関連 PLAN/handover/memory feedback の **短い bundle** に制限

**8 補助項目**:
6. **依存衝突**: PLAN-091 → PLAN-099 が正順 (frontmatter dependencies 語彙は PLAN-091 定義)。ただし Layer 4/5 PoC は暫定 schema なしで既存 handover/SessionStart/scheduler 上に作れるので並行着手可能
7. **PLAN-088 関係**: 重複ではない。PLAN-088 = 「誰が担当、WIP 可視化」、Layer 1 = 「PLAN から runnable work item queue 化」。task_queue 新設なら責務明文化必須 (PLAN 定義 = `plan_registry`、実行待ち = 既存 `helix job`/scheduler に寄せる)
8. **15min heartbeat**: **adaptive** (通常 15min / 低予算 30min / critical/hotfix 5min / active task 中無効)。固定値禁止、ScheduleWakeup は `carry>0 AND bg task なし AND budget healthy` の時だけ

**P0 指摘 (絶対遵守)**:
- 承認なし task pop は Plan Consent / WBS / handover Next Action を超える設計 → HELIX discipline 破壊。**queue worker は必ず plan guard を通すこと**

**P1 指摘 (設計時要考慮)**:
- task_queue / TodoWrite / helix job / handover が競合する恐れ → **単一の実行正本を決める**
- PreCompact block の無限ループ、context 枯渇継続、manual compact 妨害リスク
- claude-brain 型履歴保存は secret/PII/ライセンス判断 = **人間確認対象**

**P2/P3 指摘**:
- P2: hook foreground 処理肥大化 → SessionStart は fail-open、重い sync は background
- P2: statusLine warning / heartbeat のノイズ化、重要警告無視リスク
- P3: PLAN-081 等の古い hook 設計との docs drift → PLAN-099 起票時に obsolete/superseded 明記

**テスト戦略 (最小 PoC)**:
- fake transcript / fake handover / fake carry を使った hook fixture test 先行
- Layer 4: SessionStart cleared/compacted + UserPromptSubmit 注入の snapshot test
- Layer 5: fake timer で 5/15/30min + budget low + bg task active + carry 0 no-op 検証
- Layer 1-3 本実装時: migration idempotent / queue atomic claim / PreCompact one-shot block / statusLine threshold hysteresis / hook timeout

### session 終了前チェックリスト (4 項目 全充足必須)
1. carry == 0 (または時間枠満了)
2. リカバリープラン (kind=recovery) 起票済
3. handover updated
4. memory feedback 永続化済

→ 4 項目満たさず turn 終了は禁止 ([[feedback_dont_stop_with_carry_remaining]] 14h idle 事故防止)。

## 次 session 最優先 carry (2026-05-19 末確立、CLAUDE.md 永続化)

本 session で起票した PLAN-087〜090 は PLAN tree 内に L2 大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含むのに **ADR snapshot 不在** = HELIX レイヤー併存違反。次 session 開始直後に snapshot 併設救済を着手する (V-model 4 artifact 解消 / PLAN-088 Phase 1 等の他 carry より優先):

1. **ADR-021 snapshot 起票**: 設計 doc Web 検索ガードレール採用 (PLAN-087 tree の L2 凍結)
2. **ADR-022 snapshot 起票**: TodoWrite × agent slot framework 採用 (PLAN-088 tree の L2 凍結)
3. **ADR-023 snapshot 起票**: gate fail-close advisory→fail-close 段階遷移採用 (PLAN-089 tree の L2 凍結)
4. **ADR-024 snapshot 起票**: Claude Code 2.1.139 continueOnBlock / active guidance loop pattern 採用 (PLAN-090 tree の L2 凍結)
5. 各 PLAN.md 冒頭に「## L2 凍結 (ADR snapshot)」section 追加で PLAN ↔ ADR の双方向 trace 確立 (L2-MASTER §0 line 36 の PLAN-084↔ADR-018/019 を範例にする)
6. `helix doctor check_plan_adr_snapshot` 新設で PLAN tree 内 L2 大局判断あり + ADR snapshot 不在を fail-close 化 (PLAN-091? として起票候補)

ADR snapshot 起票時も WebSearch 3 query 以上必須 ([[feedback_design_doc_web_search_required]])。V2 企画書 (docs/v2/CONCEPT.md §2 痛点「PLAN 累積による散在」/ §5 Phase I「Legacy Import」/ L1-REQUIREMENTS FR-LI01-03 / L2-MASTER §0 line 36 PLAN↔ADR 範例 / §12 既知矛盾 M-01〜M-04 PLAN-069 resolved pattern) を着手前に必ず精読し、**PLAN は implementation tree (L1〜L4 内包)・ADR は L2 大局判断 snapshot** という layer 併存を維持する。

## タスク受領時の skill 推挙呼び出し (必須)

新規タスク受領時、実装着手前に必ず以下を実行する:

1. `helix skill chain "<タスク記述>"` を呼び、上位スキルと推奨 agent を確認する
2. 推挙された skill / agent に従って委譲先を決定し、Opus 自身が直接実装しない原則を優先する
3. skip する場合は、自明な小修正または既知 skill のみ使用である理由を会話または final report に記録する

これは PLAN-022 で確立されたランタイム原則である。skill 推挙は gpt-5.4-mini 経由で 1 時間キャッシュされるため、コスト負担はほぼない。

## 委譲 Codex のコミット禁止

`helix codex` / `codex exec` で呼ぶ **委譲 Codex** は `git add` / `git commit` / `git push` を一切しない。Opus (PM) が成果物検証後に commit する。チャット (TL モード) Codex は対象外。
