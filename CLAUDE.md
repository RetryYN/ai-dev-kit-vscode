<!-- helix_template_version: 4 -->
# HELIX

@./helix/HELIX_CORE.md
@./helix/HELIX_RUNTIME_RULES.md
@./helix/CLAUDE_RUNTIME_ADAPTER.md

> skill は常時注入しない（SKILL_MAP は索引）。必要時に `helix skill chain "<タスク記述>"` / `helix skill search` で取得する。
> 委譲・オーケストレーション規律（モデル割当 / 並列 / 委譲トリガ / Agent guard / skill 推挙 / advisor / Codex コミット禁止 / ScheduleWakeup）は `helix/CLAUDE_RUNTIME_ADAPTER.md §2` を正本とする（ここには重複させない）。

## このプロジェクトの位置づけ（ハーネス製造元 / メタ・プロジェクト）

このリポジトリは、**他プロジェクトを円滑に進めるためのハーネスシステム（HELIX）そのものを作り・改修するメタ・プロジェクト**である。製品はハーネス（Opus=PM 全委譲・gate・V-model・workflow の規律一式）であり、それを取り込んだ**消費側の他プロジェクト**で規律が支配する。

進め方は消費側と製造元で異なる:

- **消費側の他プロジェクト**: ハーネス規律が支配する。Opus=PM は実装せず全委譲、gate を守る（global memory + `@import` した HELIX 正本がこれを効かせる）。
- **本プロジェクト（製造元）= ここ**: HELIX の内部（doc / policy / hook / CLI / skill）を改修するのが正業。「Opus は repo を編集するな」型の消費側規律を blanket 適用しない。
  - **枠組み・設計・policy・doc**（CLAUDE.md / runtime rules / hooks / 設計判断）→ PM / architect（Opus）が直接編集してよい。
  - **実装コード**（`cli/**` の Python / Bash）→ 役割表どおり Codex（se/pe）へ委譲する。
- `opus-repo-block` 等の「Opus 直接編集 block」は**消費側プロジェクト向けの規律**。製造元である本プロジェクトはプロジェクト名で除外し、内部改修を可能にする（hook 側の整合は別途）。

## 概要
HELIX は、AI エージェントを `plan` / `task` / `role` / `gate` / `handover` で制御する開発フロー・CLI・スキル群のリポジトリ。他プロジェクトはこれをハーネスとして取り込む。

## 技術スタック
- Frontend: なし。CLI とドキュメント中心
- Backend: Bash CLI + Python helper modules
- DB: SQLite (`.helix/helix.db` などの project-local runtime state)
- インフラ: Git hooks、Claude Code hooks、Codex CLI、Bats、pytest

## アーキテクチャ
- `cli/`: `helix` ルーターとサブコマンド実装
- `cli/lib/`: Python helper、SQLite access、learning / routing utilities
- `cli/templates/`: `helix init` が配布する project template
- `helix/`: HELIX core policy、runtime rules、runtime adapter、ユーザー向け設定例
- `skills/`: HELIX skill と skill map
- `docs/commands/`: CLI 利用導線の正本
- `.claude/`: Claude Code hook / command / agent runtime 設定
- 詳細レイアウトマップ: [docs/architecture/cli-layout.md](docs/architecture/cli-layout.md)

## 保存先ルール（4 tier）

HELIX 成果物・状態の保存先を固定する。repo 名・clone 先パスに依存させない。

### 最上位原則: 実装（G）は HELIX 本体に / 計画（P）はプロジェクトに

**実装（配布物 = G tier）は HELIX 本体の住所に、計画・設計記録（P tier）はプロジェクト側の住所に置く。** 配布物（全 project に効く harness）と dogfooding（この repo 固有の計画・設計記録）を住所で分離し、正本と副本の二重化・分類漏れを構造的に防ぐ。

- **G（実装・配布物）の住所**: `helix/`（core doc・runtime・manifest）/ `HELIX-workflows/`（工程定義正本）/ `cli/`（CLI 実装・template）/ `skills/`（skill 正本）/ `.claude/{agents,hooks,commands}`。これらは消費側へ install され、全 project の振る舞いを定義する。
- **P（計画・設計記録）の住所**: `docs/plans/`（PLAN = 進め方・軌跡）/ `docs/v2/`（この repo を HELIX で作る dogfooding の設計記録）/ `docs/{adr,research}`。配布しない。本 repo 固有。
- **判定**: 「これは全 project に配布されて効くか（→ G、本体住所）」「この repo を作るための計画・設計記録か（→ P、project 住所）」。迷ったら G/P のどちらの性質かを先に決め、住所をそれに従わせる。
- **drift 防止**: 同一内容を G と P の両方に書かない。G が正本なら P からは参照（リンク）で繋ぎ、再宣言しない。G↔P 重複を見つけたら正本（G）に一本化し副本を参照化する。
- 詳細な top-dir 分類は本書「### top-dir 分類（G=配布 / P=project専用 / S=runtime・local / B=build）」を参照。BC 境界は [document-topology.md](HELIX-workflows/helix-process/document-topology.md)。

| tier | 住所 | 置くもの |
|---|---|---|
| MASTER（原本） | この repo（`<clone>/`） | core doc 原本・CLI・skill・template（git 管理） |
| GLOBAL-CORE（読む住所） | `~/.helix/core/` | 常時注入 core セット（MASTER から symlink/copy で解決） |
| GLOBAL-STATE | `~/.helix/` | `global.db` / `workspaces/` / `recipes/`（project 横断 runtime） |
| PROJECT-STATE | `<project>/.helix/` | handover / plans / config / cache（project 固有 runtime） |
| INJECTION（入口） | `~/.claude/CLAUDE.md` 等 | `@~/.helix/core/...` の参照のみ（実体を持たない） |

- **GLOBAL-CORE の解決**: `~/.helix/core` は harness master を指す path 非依存の mount。製造元（ここ）= **repo root への symlink**（`~/.helix/core` → `<clone>/`、編集は repo 側で即反映）。消費側 = clone を残して同じ symlink（clone を消す場合のみ copy）。`setup.sh` が clone 位置を検出して張る。INJECTION はどちらも `@~/.helix/core/...` 固定でパス非依存。
- **常時注入 core セット**の単一権威 (SSoT) は **`helix/core-manifest.tsv`**（setup.sh / global loader が参照。ここに列挙を二重定義しない）。`@~/.helix/core/<path>` は**配布の公開 API** であり、`~/.helix/core` 配置非依存 mount でパスを安定させる（path 変更 = 消費側 loader 破壊のため、移動は document-topology の将来移動 policy に従う）。`HELIX-workflows/helix-process/*` と `docs/**` は詳細注入（常時注入しない）。helix/（governance BC）と HELIX-workflows/（process model BC）の境界・越境理由は [document-topology.md](HELIX-workflows/helix-process/document-topology.md) を正本とする。
- **判断**: ①全 project 共通 → MASTER（原本）を `~/.helix/core/` 経由で読む / ②project 横断 runtime → `~/.helix/` / ③この project だけ → `<project>/.helix/` / ④入口 → 参照のみ。
- **禁止**: INJECTION に clone 先パスを直参照（`@~/ai-dev-kit-vscode/...` は廃止、必ず `@~/.helix/core/...`）/ runtime state を git に commit。
- **状態**: 可搬化 完了。global B の import を `@~/.helix/core/...` へ張替・`~/.helix/core`→repo root symlink・`setup.sh` を clone 位置検出 / `~/.helix/core` 基準 import / SKILL_MAP 除外 / 旧 import 除去へ修正・`~/.claude/agents` を `~/.helix/core` 経由で統合（commit `878170b` / `93af0e9`）。

### top-dir 分類（G=配布 / P=project専用 / S=runtime・local / B=build）

この repo は製造元なので大半が G（harness 配布物）。物理移動はせず、各 top エントリの区分だけ明示して global / project の見通しを保つ。

| 区分 | 意味 | top エントリ |
|---|---|---|
| **G** | harness 配布物（全 project に効く / 消費側へ install） | `helix/` `HELIX-workflows/` `cli/`（含 `cli/templates/`） `skills/` `harness/` `workflows/` `ai-code-review-kit/` `.claude/{agents,hooks,commands}` `setup.sh` `AGENTS.md` `README.md` `.claude/CLAUDE.md`(loader) |
| **P** | project 専用（この repo の dogfooding、配布しない） | `CLAUDE.md`（本 project context） `docs/plans/` `docs/v2/` `docs/adr` `docs/research` `src/`（feature scaffold） |
| **S** | runtime / local（生成物・機械固有、gitignored） | `.helix/` `.claude/{memory,agent-memory}` `settings.local.json` `public/` / root 直下 draft `.md` |
| **B** | build / test | `tests/` `verify/` `scripts/` `pyproject.toml` `package.json` `requirements-dev.txt` |

- **混在 dir（要注意）**: `docs/`（G=`docs/commands` 利用導線 ／ P=plans・v2・adr・research）、`.claude/`（G=agents/hooks/commands ／ S=memory・local）。
- G のうち `~/.helix/core` 経由で**常時注入**されるのは保存先ルールの core セットのみ。他 G は詳細注入か CLI 実体。

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

## GitHub 運用ルール

このリポは GitHub で配布される HELIX framework 本体 (製造元)。消費側は repo を clone + `setup.sh` で取り込む。配布物の品質を守るため、以下を規律とする。

### 配布戦略 (戦略C: monorepo + dist publish) — 2026-06-01 確定

- **monorepo (この repo) = G の単一正本 + P (dogfooding)**。製造元はここで作業する。G を複数 repo に実体コピーしない (drift 防止、`helix/core-manifest.tsv` SSoT と整合)。
- **dist (artifact または別 `helix-dist` repo) = G+B のみを release で publish**。消費側はこれを取得する。**dist の G は monorepo から自動生成し、人手編集しない (generated mirror)**。
- dist publish の実装・`setup.sh` の dev/consumer 2 モード化は未整備 (P1)。**repo/配布構造の変更は refactor でなく distribution architecture migration であり、ADR + migration PLAN + ユーザー承認を経てから着手する** (正本: [docs/plans/refactor/refactor-2026-06-01-folder-structure-g-p-separation.md](docs/plans/refactor/refactor-2026-06-01-folder-structure-g-p-separation.md) Phase 0)。

### ブランチ

- `main`: 既定ブランチ。protected 想定、tag/release 対象。PR は通常 `main` を base にする。
- 作業は `main` から branch を切る。デフォルトブランチへの直 push は、製造元の枠組み・policy・doc 改修で PM (Opus) が成果物検証後に判断する場合に限る (実装コードは別、下記)。
- `dogfood`: 製造元の dogfooding 退避用 (P 中心の作業)。戦略C では恒久必須ではなく、dist 設計確定時に運用を見直す。

### 公開 API (破壊禁止)

- **`@~/.helix/core/<path>` import は配布の公開 API**。消費側の global loader (`~/.claude/CLAUDE.md` 等) が直接読む。**path 変更 = 既存消費側の参照切れ (breaking)**。
- 常時注入 core セットの SSoT は `helix/core-manifest.tsv`。変更時は `cli/lib/tests/test_core_manifest_drift.py` で manifest⇔setup.sh⇔loader 一致を保証する。
- core ファイルの物理移動はしない (配置非依存 mount `~/.helix/core` でパス安定)。やむを得ない場合は [document-topology.md](HELIX-workflows/helix-process/document-topology.md) の将来移動 policy (メジャー境界 + 旧 path shim ≥2 minor + migration detector) に従う。

### push / PR

- **push・PR 作成・merge はユーザーが明示的に依頼したときのみ行う** (commit はローカル、push は別判断)。
- 委譲した Codex は commit / push しない。`git add` / `commit` / `push` は呼び出し元 (PM) が成果物検証後に判断する。
- 外部公開操作 (push / PR / release / tag) は外向きアクションのため、durable な許可がない限り都度確認する。
- PR body 末尾には `🤖 Generated with [Claude Code](https://claude.com/claude-code)` を付ける。GitHub 操作は `gh` CLI を使う。

### gitignore / 追跡対象

- S tier (runtime/local: `.helix/`・`.claude/{memory,agent-memory}`・`settings.local.json`・生成物) は git 追跡しない。
- secret / API key / PII / credential を commit しない (`## 禁止事項` 参照)。
- 自動生成物 (session 記録・Codex local state) は手動 commit に混ぜない。

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
- **工程・workflow 判断時はまず [HELIX-workflows/](HELIX-workflows/) を正本として参照する** (2026-05-24 V2 完全移行で確立、commit `35a901c / ee1a13a`)。L0-L14 の工程定義は [HELIX-workflows/HELIX-process-L0-L14.md](HELIX-workflows/HELIX-process-L0-L14.md)、各工程詳細・workflow 別文書は [HELIX-workflows/helix-process/](HELIX-workflows/helix-process/) (L0-L14 工程 doc / workflow doc / 工程専門 (screen-design/frontend-design) / 管理・自動化基盤 (integration-map / asset-mapping / folder-structure-review / detection-routing / layer-context-injection / cross-cutting-mechanisms / automation-gate-map / continuous-run-context-management / fe-detector-spec / observability-metrics / cross-detection / db-auto-registration / db-integration / learning-engine / deviation-plan-map / test-perspective-gate / two-stage-agent-design / infra-readiness) 等)。
- タスク受領時は `helix/HELIX_CORE.md`、`helix/HELIX_RUNTIME_RULES.md`、`helix/CLAUDE_RUNTIME_ADAPTER.md` を確認する。これらは HELIX-workflows と HELIX Core を正本として参照する形で同期されている (drift 発見時は HELIX-workflows と HELIX Core を正、本ファイル群を retrofit)。
- 新規 PLAN 起票・workflow 判断・コマンド整備など、企画・設計判断に入る前に [HELIX-workflows/helix-process/integration-map.md](HELIX-workflows/helix-process/integration-map.md) §結論と優先順位 を必ず確認する (整理済み企画書を読まずに自前 carry list を並べないこと、[[feedback_read_integrated_plan_before_carry_list]])。
- `.helix/handover/CURRENT.json` がある場合は `helix handover status --json` を確認し、stale でなければ Next Action に従う。
- 文書統合 INDEX 兼 appendix は [docs/architecture/helix-workflows-appendix.md](docs/architecture/helix-workflows-appendix.md) を参照する。domain 別の導線は `docs/{adr,research,runbook,rollback,postmortem,slo,design}/helix-workflows-appendix.md` に集約する。

### 実装済み CLI mode

- Forward: `size` -> `plan` -> `matrix` -> `gate` -> `sprint` -> `test`
- Reverse: `reverse <type> R0` -> `R1` -> `R2` -> `R3` -> `R4` -> `rgc`
- Discovery (検証駆動 / 旧: helix scrum): `discovery init` -> `backlog` -> `plan` -> `poc` -> `verify` -> `decide`
- Research: `helix research` で技術調査・意思決定 (ADR 連携)
- AI harness: `plan` / `task` の文脈を `codex` / `claude` / `team` / `review` / `handover` で管理する。

### workflow doc 正本のみの mode (dedicated CLI 未整備)

以下 mode は workflow doc を正本とし、PLAN kind + template で運用する。**`helix refactor` / `helix retrofit` / `helix recovery` 等の CLI は存在しないため叩かない**:

- Refactor (kind=`refactor`) → [HELIX-workflows/helix-process/refactor-workflow.md](HELIX-workflows/helix-process/refactor-workflow.md)
- Retrofit (kind=`retrofit`) → [HELIX-workflows/helix-process/retrofit-workflow.md](HELIX-workflows/helix-process/retrofit-workflow.md)
- Incident (hotfix) → [HELIX-workflows/helix-process/incident-workflow.md](HELIX-workflows/helix-process/incident-workflow.md)
- Add-feature → [HELIX-workflows/helix-process/add-feature-workflow.md](HELIX-workflows/helix-process/add-feature-workflow.md)
- Recovery (AI 暴走ガード+収束、kind=`recovery`) → [HELIX-workflows/helix-process/recovery-workflow.md](HELIX-workflows/helix-process/recovery-workflow.md)

### workflow doc 直接参照 index（CLAUDE）

- [Forward（Vモデル）正本](HELIX-workflows/HELIX-process-L0-L14.md)
- [Scrum](HELIX-workflows/helix-process/scrum-workflow.md)
- [Discovery](HELIX-workflows/helix-process/discovery-workflow.md)
- [Reverse](HELIX-workflows/helix-process/reverse-workflow.md)
- [Incident](HELIX-workflows/helix-process/incident-workflow.md)
- [Add-feature](HELIX-workflows/helix-process/add-feature-workflow.md)
- [Refactor](HELIX-workflows/helix-process/refactor-workflow.md)
- [Retrofit](HELIX-workflows/helix-process/retrofit-workflow.md)
- [Research](HELIX-workflows/helix-process/research-workflow.md)
- [Recovery](HELIX-workflows/helix-process/recovery-workflow.md)
- [画面設計（UI / ワイヤーフレーム）](HELIX-workflows/helix-process/screen-design-workflow.md)
- [フロントデザイン（UX / ビジュアル）](HELIX-workflows/helix-process/frontend-design-workflow.md)
- [HELIX W（2 段V 合流）](HELIX-workflows/helix-process/two-stage-agent-design.md)
- [自動化・ゲート・運用基盤](HELIX-workflows/helix-process/automation-gate-map.md)

9 workflow + HELIX W (2 段 V 合流) + 検証条件先行 / 実装時 TDD 共通原則の詳細は [HELIX-workflows/HELIX-process-L0-L14.md](HELIX-workflows/HELIX-process-L0-L14.md) と `helix/HELIX_RUNTIME_RULES.md` を正本とする。

詳細は [docs/commands/index.md](docs/commands/index.md) と [docs/commands/ai-harness.md](docs/commands/ai-harness.md) を参照。

## Codex との対応
Codex CLI 向けの正本は [AGENTS.md](AGENTS.md) と `helix/CODEX_RUNTIME_ADAPTER.md`。プロジェクト知識はこの `CLAUDE.md` と揃え、Codex 固有の編集・検証・handover ルールは `helix/CODEX_RUNTIME_ADAPTER.md` に寄せる。
