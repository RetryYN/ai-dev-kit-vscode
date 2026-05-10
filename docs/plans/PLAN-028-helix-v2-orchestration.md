---
plan_id: PLAN-028
title: "PLAN-028: HELIX v2 orchestration 移行"
status: completed
created: 2026-05-08
author: Legacy migration
---
# PLAN-028: HELIX v2 orchestration 移行

## メタデータ

- id: PLAN-028
- title: HELIX v2 orchestration 移行 (PM 実装禁止 + PMO 新設 + ロール再配置)
- status: completed (2026-05-08, W-6 retrospective + 統合検証 PASS)
- priority: high
- created: 2026-05-08
- owners: PM, TL
- related: docs/adr/ADR-014 (cli/roles/*.conf 正本維持), PLAN-024 (Sprint .3 完了済), 全主要 docs

## 1. 背景・動機 (Why)

v1 で Opus PM が実装も委譲も両方担当した結果、PM の判断責任が曖昧化した。FE 設計・小修正・PLAN 修正で Opus 直接 Edit が常態化し、コスト面でも Opus トークン消費が PM 業務範囲を超過していた。

v2 では PM 責務を「プロジェクト管理 (工程・ドキュメント・実装テスト・コード/DB・コスト)」に純化し、実装は TL/SE/PE、補助は PMO に分散する。本 PLAN-028 はこの v2 移行を Sprint 単位で段階実行する正本ドキュメントとなる。

## 2. v2 ロール × モデル設計

### 2.1 PM = Opus (チャットのみ・実装禁止・サブエージェント禁止)

- **責務**: 工程管理 / ドキュメント管理 / 実装テスト管理 / コード/DB 管理 / コスト管理
- **禁止事項**:
  - Edit/Write でのコード修正 (実装一切禁止)
  - Agent tool での subagent_type 指定呼び出し (一切禁止)
- **許可事項**: チャット応答 / メモリ操作 / handover 操作 / phase.yaml と短ファイル Read /
  helix CLI 実行

### 2.2 PMO = Sonnet (判断伴う) / Haiku (軽作業) — 新設ロール

- **判断伴う作業** → Sonnet: 実装現状把握 / ドキュメントチェック / 簡易レビュー (read-only、報告のみ)
- **軽作業** → Haiku: Web 検索 / 軽量ドキュメント更新
- **60% 超フォールバック** → GPT-5.4-mini (Claude 週間上限到達時)

### 2.2.1 PMO 権限境界 (§4.2 と整合)

| サブロール | code 編集 | docs/ 編集 | Web 検索 | 報告 | 用途例 |
|----------|---------|----------|---------|------|------|
| Sonnet (判断伴う) | ❌禁止 | ❌禁止 (read-only) | ✅ | ✅ | 実装現状把握、docs チェック、簡易レビュー |
| Haiku (軽作業) | ❌禁止 | ✅許可 (docs/* のみ、対象 path 明示時) | ✅ | ✅ | Web 検索、軽量 docs 更新 (typo 修正、リンク追加など) |

- **共通制約**: コード (`cli/`、`tests/`、`scripts/`、その他 code 系) への Edit/Write は **両者とも禁止**
- **Haiku の docs 編集**: `--allow-paths "docs/**,skills/**"` で対象 glob を明示的に許可した時のみ。
  デフォルトは read-only。コード編集が必要な作業は TL/SE/PE に切り出す
- **実装の正本**: `cli/templates/prompts/pmo-base.md` (W-3 で作成) で no-write policy + path
  whitelist を prompt と CLI option (`--permission-mode plan` / `--disallowedTools`) の二段階で固定

### 2.3 TL = GPT-5.5

- **担当**: 設計ドキュメント / FE UI/UX ワイヤー / 検証 / レビュー / 方針相談 / セキュリティ / エージェント実装 / DB
- **thinking**: high / middle / low で対応
- **Extra high**: 問題が解決不能な時のみ (通常使用禁止)
- **責務**: スプリント単位でのレビュー責務

### 2.4 SE = GPT-5.4

- **担当**: 高度実装 (複数コード作成 / 契約周り / リファクタリング / 検証 / 技術スタック系検索 / 長期実装)
- **thinking**: high / middle / low で対応
- **Extra high**: リファクタリング時のみ (通常使用禁止)

### 2.5 PE = Codex 5.3-spark (優先) / Codex 5.3 (フォールバック)

- **単機能実装**: Codex 5.3
- **速度重視**: Codex 5.3-spark
- **優先順位**: 5.3-spark を優先選択、上限到達時 5.3 にフォールバック

### 2.6 推挙システム = GPT-5.4-mini

- **通常**: skill 推挙 / classifier 用途
- **60% 超**: PMO の代替で PM タスク代行 (Claude 週間上限到達時)

### 2.7 フロントデザイン (FE) v2 フロー

1. PM が要件提示
2. TL (Codex 5.5) が UI/UX ワイヤーを作成
3. PM がワイヤーをレビュー → 修正指示
4. Sonnet (PMO) に修正実装を依頼
5. 画像生成必要時:
   - TL に Codex 内蔵の画像生成 LLM で画像作成依頼
   - または PO (ユーザー) に外部画像生成プロンプトを提出して依頼

### 2.8 モデル世代ポリシー

- **最新モデルを PM/TL を最上位として 3 世代まで** Claude / GPT 系列を更新
- Claude = Opus + Sonnet + Haiku の 3 階層、各最新版
- GPT = 5.5 / 5.4 / 5.3 + 派生 (spark / mini)
- **実装の正本順序** (ADR-014 準拠):
  1. **`cli/roles/*.conf`** が **唯一の実行正本** (helix-codex / helix-claude が直接読む)
  2. `cli/config/models.yaml` は **同期カタログ + helix doctor 整合チェック基準** (周知用途)
  3. CLAUDE.md / AGENTS.md / 本 PLAN-028 の表は **周知用**
- **食い違い時は conf を正**、yaml/Markdown は後追い同期 (ADR-014 確定方針)
- W-2 の作業順: **conf 作成・更新 → models.yaml 同期 → helix doctor 整合確認**

## 3. 引継ぎプロトコル拡張

PM ↔ TL モード切替時の引継ぎドキュメント生成義務:

- **PM → TL モード**: `helix handover dump --mode pm-to-tl --note "..."`
- **TL → PM モード**: `helix handover dump --mode tl-to-pm --note "..."`
- 既存 `.helix/handover/` 体系を拡張 (`mode` フィールドを `pm-to-tl` / `tl-to-pm` / `be-implementation` (既存) で区別)

## 4. PMO 起動経路 (CLI 拡張仕様)

既存 `cli/helix-claude` は **prompt 生成 harness** として動作している (docs/commands/ai-harness.md
参照、API/SDK 直叩きはしない方針)。本 PLAN-028 では `helix claude` に **実行モード** を追加する。

### 4.1 CLI シグネチャ (W-3 で実装)

```bash
# プロンプト生成のみ (既存挙動、デフォルト)
helix claude --role pmo --model sonnet --task "..." --dry-run

# 実行モード (新設)
helix claude --role pmo --model sonnet --task "..." --execute [--thinking medium]
helix claude --role pmo --model haiku  --task "Web 検索: ..." --execute
```

### 4.2 実行モード契約 (W-3 DoD)

- **デフォルト**: `--dry-run` (prompt 生成のみ、既存互換)
- **--execute** 指定時:
  - 内部実装: `HELIX_CLAUDE_INTERNAL=1 claude --print --model <id> --permission-mode plan --disallowedTools "Edit,Write,NotebookEdit" -p "..."`
  - **shim 整合**: `cli/claude` は raw claude を通常ブロックする shim。helix-claude 内部呼び出しは `HELIX_CLAUDE_INTERNAL=1` を必須化 (raw 抜け道防止)
  - **permission-mode**: 既定 `plan` (read-only equivalent、§2.2.1 Sonnet)。Haiku の docs 編集モードは別オプション (下記)
  - **disallowedTools**: 既定 `"Edit,Write,NotebookEdit"` で固定。tool 制限は **prompt + CLI 二段階** で強制 (prompt 単独ではなく Claude Code CLI 仕様で fail-close)
  - **--allow-paths `<glob,...>`**: Haiku の docs 編集時のみ指定。指定時は permission-mode を `acceptEdits` に切替え + disallowedTools を `"Edit,Write" 以外に` 緩和、ただし `--allow-paths` で path whitelist を強制
  - **モデル ID**: `claude-sonnet-4-6` / `claude-haiku-4-5-20251001` (cli/config/models.yaml と同期、conf 正本)
  - **auth 前提**: `~/.claude/auth` 既存セッション or 環境変数で claude CLI が認証済み
  - **timeout**: 300 秒デフォルト (`--timeout` で上書き可)
  - **ログ**: `.helix/cache/pmo/<timestamp>-<sha>.log` に stdout/stderr を保存
  - **失敗コード**: claude CLI の exit code を踏襲 (auth fail = 2、timeout = 124、tool denied = 4 等)
  - **human approval 条件**: 本番影響 / 認証 / PII / 決済を含むタスクは `--require-approval` で
    人間確認を要求 (helix-codex の --approved と対称)
- Windows/WSL2 親和性: helix CLI は bash、claude CLI はクロスプラットフォーム
- ADR-015 で「helix-claude を実行モード対応 harness に拡張する決定」を明文化

## 5. 影響範囲 (15+ ファイル)

### 5.1 docs (8 件)

- `~/.claude/CLAUDE.md` (user global) — モデル割当 / 委譲ルール
- `CLAUDE.md` (project) — モデル割当 / 並列実行ルール / Agent コスト制御
- `AGENTS.md` (Codex 向け)
- `helix/HELIX_CORE.md`
- `helix/CODEX_TL_MODE.md`
- `skills/SKILL_MAP.md` (§正本宣言・モデル割当)
- `cli/ROLE_MAP.md`
- `docs/architecture/cli-layout.md` (微修正、PMO 経路追記)

### 5.2 config (3 件 + roles)

- `cli/config/models.yaml` — roles 再定義 (TL=5.5 / SE=5.4 / PE=5.3-spark / PMO=sonnet/haiku)
- `cli/roles/*.conf` (12+ 件) — role 別モデル / thinking 更新
- `cli/config/defaults.yaml` — PMO 関連 default 追加 (必要に応じて)

### 5.3 CLI (新設・改修)

- `cli/helix-claude` — `--role pmo` / `--model sonnet|haiku` / `--thinking` 拡張
- `cli/helix-handover` — `--mode pm-to-tl | tl-to-pm | be-implementation` 追加

### 5.4 agents (廃止)

- `.claude/agents/fe-design.md` (削除)
- `.claude/agents/fe-component.md` (削除)
- `.claude/agents/fe-style.md` (削除)
- `.claude/agents/fe-a11y.md` (削除)
- `.claude/agents/fe-test.md` (削除)
- `.claude/agents/code-reviewer.md` / `security-audit.md` / `qa-test.md` — 個別評価
  (Codex の対応 role に役割移譲済なら削除可)

### 5.5 ADR

- `docs/adr/ADR-015-helix-v2-orchestration.md` (新規起票)
- `docs/adr/index.md` (ADR-015 を追記)

## 6. Sprint 分割

| Sprint | 内容 | 担当 | 依存 | セッション数 |
|--------|------|------|------|--------------|
| **W-1** | PLAN-028 spec finalize + ADR-015 起票 + index.md 追記 | docs | なし | 1.0 |
| **W-2** | `cli/roles/*.conf` 再定義 (conf 正本、TL/SE/PE/PMO/recommender 役割明示) → `cli/config/models.yaml` 同期 → helix doctor 整合確認 | SE | W-1 | 1.0 |
| **W-3** | `helix-claude` 拡張 (`--role pmo` / `--model sonnet\|haiku` / `--execute` / `--dry-run` / auth/log/timeout/no-write 契約) + `helix-handover` mode フィールド追加 | SE | W-1 (PMO contract spec を W-1 で固定済) | 1.5 |
| **W-4** | 主要 docs 一括更新 (CLAUDE.md / SKILL_MAP / HELIX_CORE / CODEX_TL_MODE / ROLE_MAP / AGENTS) | docs | W-2 | 2.0 |
| **W-5a** | `.claude/agents/fe-*.md` + `cli/templates/agents/fe-*.md` (配布元) 廃止 — docs 系参照に依存しない物理削除 | docs | W-1 | 0.5 |
| **W-5b** | 関連スキル/SKILL_MAP 参照削除 (W-4 の表記更新と整合) | docs | W-4 | 0.5 |
| **W-6** | 統合検証 (helix doctor / helix test / 主要 CLI smoke) + retrospective | qa | W-2..W-5 | 1.0 |

### 6.1 並列性

- **W-2 ‖ W-3**: PMO 契約を W-1 で先に固定するため、W-3 は W-2 の conf 結果に依存しない
  (PMO role 名 / model 指定のみ依存、これらは W-1 spec で確定)。config と CLI 新設は独立、
  ファイル衝突なし
- **W-2 ‖ W-5a**: agents 物理削除は config 変更に依存しない (別ファイル群、後段依存なし)
- **W-4 → W-5b 直列**: W-5b は W-4 で確定した v2 docs 表記と整合させる必要があるため直列
- W-6 は最後の検証フェーズ

## 7. 移行戦略 (リスク管理)

### 7.1 段階的フェーズ

- **v1 退路維持期 (W-1 ~ W-3)**: v1 ルールが正本、v2 関連の追加 docs は draft 扱い
- **v2 試験運用期 (W-4 完了)**: 主要 docs が v2 に揃い、Sprint 単位で v2 適用開始
- **v2 正式運用期 (W-5 完了)**: native subagent 廃止 + v1 退路完全閉鎖
- **検証完了 (W-6 完了)**: helix test 全 PASS + retrospective 記録

### 7.2 transitional rule (W-1 ~ W-3 期間中)

- W-3 (helix-claude 拡張) 完了まで PMO 経路がない
- **暫定対応 (read-only 限定)**:
  - PM の PMO 業務代替は **`helix codex --role docs --read-only --plan-only` 相当のレビュー機能のみ** に限定
  - **Edit / Write が必要な作業は移行期でも TL / SE / PE の承認済み WBS に切り出す** (PM 実装禁止と整合)
  - status check / docs review (読み取り) のみ Codex docs role で代替可
- W-3 完了後にこの transitional rule を破棄
- **抜け道防止**: 移行期の例外を恒常運用に持ち込まない。W-3 DoD で transitional rule 破棄を明示確認

### 7.3 既存タスク互換

- 既存 PLAN-024 / PLAN-027 の残 Sprint は v1 ルールで継続実行
- 新タスクは PLAN-028 完了時点 (W-6 完了) から v2 適用

## 8. 完了条件

### W-1 DoD
- `docs/plans/PLAN-028-helix-v2-orchestration.md` finalize (TL approve)
- `docs/adr/ADR-015-helix-v2-orchestration.md` 起票 + `docs/adr/index.md` 追記
- `helix plan draft --plan-id PLAN-028 --file docs/plans/PLAN-028-helix-v2-orchestration.md` 相当の登録 (運用 task tracker への反映、または該当機構がない場合は本 PLAN 内に登録要否を判定して記録)

### W-2 DoD
- `cli/roles/*.conf` (TL/SE/PE/PMO/recommender) を v2 役割で更新 (conf 正本)
- `cli/config/models.yaml` を conf に同期 (周知カタログとして整合)
- `helix doctor` が **全 codex roles の conf ↔ models.yaml 不整合を検出** (PASS = 不整合 0 件)
- PMO は `pmo-sonnet` / `pmo-haiku` の 2 系統を別 role として登録、または models.yaml schema を `model_variants` 拡張で表現

### W-3 DoD
- `helix claude --role pmo --model sonnet --task "ping" --execute` smoke で Sonnet 起動 + 出力ログ生成確認
- `helix claude --role pmo --model haiku --task "ping" --execute` smoke で Haiku 起動確認
- `--dry-run` 既存挙動が後方互換 (regress 0)
- auth fail / timeout / no-write 違反の各失敗ケースで適切な exit code を返す
- `helix-handover` の `--mode` フィールドが `pm-to-tl / tl-to-pm / be-implementation` の 3 値を受け取り、JSON にシリアライズされる
- `cli/templates/prompts/pmo-base.md` で no-write policy の prompt 固定
- transitional rule 破棄宣言を本 PLAN-028 内に追記

### W-4 DoD
- 主要 docs **8 件** (`~/.claude/CLAUDE.md` (user global) / `CLAUDE.md` / `AGENTS.md` / `helix/HELIX_CORE.md` / `helix/CODEX_TL_MODE.md` / `skills/SKILL_MAP.md` / `cli/ROLE_MAP.md` / `docs/architecture/cli-layout.md`) で v2 表記が一貫
  - 注: 5.1 の docs 件数を 8 件に統一済 (本 DoD で参照件数を一致させる)

### W-5a / W-5b DoD
- W-5a: `.claude/agents/fe-*.md` (5 件) + `cli/templates/agents/fe-*.md` (配布元) が 0 件
- W-5b: 以下の **runtime routing / test / template catalog / SKILL_MAP** から fe-* 参照が削除:
  - `cli/helix-task` / `cli/helix-skill` / `cli/lib/skill_dispatcher.py`
  - `cli/libexec/helix-session-start`
  - `cli/templates/task-catalog.yaml`
  - `cli/helix-test`
  - `skills/SKILL_MAP.md` §責務境界の FE 5 種言及 + 関連スキルの fe-* 言及
  - 上記以外で fe-* を参照する箇所が `rg "fe-(design|component|style|a11y|test)"` で 0 件
- `helix-init` の agents/ コピー処理が fe-* を含まない (新規プロジェクトに廃止 agent が再配布されない)
- W-5b 開始前に `rg` で全参照リストを生成し、漏れなく更新する

### W-6 DoD
- `helix test` 全 PASS (pytest + bats、regress 0)
- `helix gate G2` PASS (設計凍結、v2 表記の整合)
- `helix gate G4` PASS (実装凍結、PMO smoke 含む)
- `helix doctor` 全 PASS
- retrospective 記録を `.helix/retros/PLAN-028.md` に保存

### 全体
- 全 commit push 済 (W-1 ~ W-6 で 6-8 commits 想定)

## 9. リスクと回避策

| リスク | 影響 | 回避策 |
|-------|------|--------|
| PMO 起動経路が CLI 新設依存 → 切替時に PMO が動かない | 高 | W-3 を W-2 と並列で最優先実行、それまで transitional rule (Codex docs 代替) を許容 |
| `.claude/agents/` 廃止で他プロジェクト (helix-init で配布) に影響 | 中 | helix-init の agents/ コピー部分を W-5 で除外、既存プロジェクトは v1 retain |
| Extra high 制限 (TL=解決不能時 / SE=リファク時) を運用で守らせる仕組み | 低 | tl.conf / se.conf に「extra-high はオーバーライド時のみ」明記、helix doctor で警告 |
| 60% フォールバック判定基準 (週間上限) の自動化 | 中 | helix budget status の ccusage ロジックを拡張、W-3 で `helix budget should-fallback-to` を追加 |
| 移行中に既存タスク (PLAN-024 残 / PLAN-027 残) が v1/v2 混在 | 中 | PLAN-028 完了まで既存タスクは v1 ルールで継続、新タスクのみ v2 適用 |
| ADR/SKILL/docs の参照 path 不整合 (大小文字 ADR/adr 等) | 中 | 既存 `rg` で path 確認、W-4 で一括 path 修正 |
| **PM 禁止事項 (Edit/Write/Agent) が文書だけで enforcement されない** | **高** | W-6 で hook ベースの guard を検討 (PreToolUse hook で Opus セッションの subagent_type 検出 → block / 警告)。当面はレビュー時の人間確認を必須化、helix doctor で「Opus セッション履歴に subagent 呼び出し有無」を warning レベルで報告 |
| **`cli/templates/agents/` から廃止 agent が再配布される** | **高** | W-5a で `cli/templates/agents/fe-*.md` の物理削除を含める (helix-init の copy 処理は fe-* 不在で正常動作する設計)。W-5a DoD で配布元と参照先の両方が 0 件確認 |

## 10. 残課題 (PLAN-028 完了後の次フェーズ)

- AT 統合: helix budget の自動フォールバック実装 (60% 検出 → 推挙 GPT-5.4-mini 委譲)
- 画像生成 LLM 起動: Codex 内蔵の画像生成機能の具体コマンド調査 (W-2 で別途確認)
- 引継ぎドキュメント自動化: PM ↔ TL モード切替を hook 化 (将来検討)
- v2 retrospective: W-6 完了後に v2 移行の効果測定 (Opus トークン消費 / Sprint 完遂時間)

## 11. 関連ドキュメント

- docs/adr/ADR-014: cli/roles/*.conf 正本維持の決定
- docs/adr/ADR-015 (新規予定): HELIX v2 orchestration 採用決定
- PLAN-024: HELIX 内部 lib 整理 (Sprint .3 完了済)
- メモ: `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/project_helix_orchestration_v2.md`
