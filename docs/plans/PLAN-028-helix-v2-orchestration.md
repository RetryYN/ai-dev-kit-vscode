# PLAN-028: HELIX v2 orchestration 移行

## メタデータ

- id: PLAN-028
- title: HELIX v2 orchestration 移行 (PM 実装禁止 + PMO 新設 + ロール再配置)
- status: draft
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

- **判断伴う作業** → Sonnet: 実装現状把握 / ドキュメントチェック / 簡易レビュー
- **軽作業** → Haiku: Web 検索 / 軽量ドキュメント更新
- **60% 超フォールバック** → GPT-5.4-mini (Claude 週間上限到達時)

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
- **実装の正本**: `cli/config/models.yaml` (本表との乖離時は実装側を正)

## 3. 引継ぎプロトコル拡張

PM ↔ TL モード切替時の引継ぎドキュメント生成義務:

- **PM → TL モード**: `helix handover dump --mode pm-to-tl --note "..."`
- **TL → PM モード**: `helix handover dump --mode tl-to-pm --note "..."`
- 既存 `.helix/handover/` 体系を拡張 (`mode` フィールドを `pm-to-tl` / `tl-to-pm` / `be-implementation` (既存) で区別)

## 4. PMO 起動経路 (CLI 拡張仕様)

`helix codex` と対称な `helix claude` シムを拡張:

```bash
helix claude --role pmo --model sonnet --task "実装現状把握: ..." [--thinking medium]
helix claude --role pmo --model haiku  --task "Web 検索: ..."
```

- 内部実装: `claude --print --model <claude-sonnet-4-6 | claude-haiku-4-5> -p "..."`
- Windows/WSL2 親和性◎ (helix CLI は bash、claude CLI はクロスプラットフォーム)
- 既存 `cli/helix-claude` shim を改修 (Sprint W-3)

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
| **W-2** | `cli/config/models.yaml` + `cli/roles/*.conf` 再定義 (TL/SE/PE/PMO/recommender 役割明示) | SE | W-1 | 1.0 |
| **W-3** | `helix-claude` 拡張 (`--role pmo` / `--model sonnet|haiku`) + `helix-handover` mode フィールド追加 | SE | W-2 | 1.5 |
| **W-4** | 主要 docs 一括更新 (CLAUDE.md / SKILL_MAP / HELIX_CORE / CODEX_TL_MODE / ROLE_MAP / AGENTS) | docs | W-2 | 2.0 |
| **W-5** | `.claude/agents/fe-*.md` 廃止 + 関連スキル参照削除 | docs | W-4 | 1.0 |
| **W-6** | 統合検証 (helix doctor / helix test / 主要 CLI smoke) + retrospective | qa | W-2..W-5 | 1.0 |

### 6.1 並列性

- W-2 ‖ W-3 (config と CLI 新設は独立、ファイル衝突なし、後段依存なし)
- W-4 ‖ W-5 (docs 更新と agents 廃止は別ファイル群)
- W-6 は最後の検証フェーズ

## 7. 移行戦略 (リスク管理)

### 7.1 段階的フェーズ

- **v1 退路維持期 (W-1 ~ W-3)**: v1 ルールが正本、v2 関連の追加 docs は draft 扱い
- **v2 試験運用期 (W-4 完了)**: 主要 docs が v2 に揃い、Sprint 単位で v2 適用開始
- **v2 正式運用期 (W-5 完了)**: native subagent 廃止 + v1 退路完全閉鎖
- **検証完了 (W-6 完了)**: helix test 全 PASS + retrospective 記録

### 7.2 transitional rule (W-1 ~ W-3 期間中)

- W-3 (helix-claude 拡張) 完了まで PMO 経路がない
- 暫定対応: PM が PMO 業務 (status check / docs review) を Codex docs role で代替実行可
- W-3 完了後にこの transitional rule を破棄

### 7.3 既存タスク互換

- 既存 PLAN-024 / PLAN-027 の残 Sprint は v1 ルールで継続実行
- 新タスクは PLAN-028 完了時点 (W-6 完了) から v2 適用

## 8. 完了条件

1. PLAN-028 finalize + ADR-015 finalize (W-1)
2. `helix doctor` で v2 ロール × モデル整合性 PASS (W-2 完了時点)
3. `helix claude --role pmo --task "ping"` smoke で Sonnet 起動確認 (W-3)
4. 主要 docs 7 件で v2 表記が一貫 (W-4)
5. `.claude/agents/fe-*.md` が 0 件 + `skills/SKILL_MAP` §責務境界の FE 5 種言及が削除 (W-5)
6. `helix test` 全 PASS + helix gate G2/G4 PASS (W-6)
7. 全 commit push 済 (5-7 commits 想定)

## 9. リスクと回避策

| リスク | 影響 | 回避策 |
|-------|------|--------|
| PMO 起動経路が CLI 新設依存 → 切替時に PMO が動かない | 高 | W-3 を W-2 と並列で最優先実行、それまで transitional rule (Codex docs 代替) を許容 |
| `.claude/agents/` 廃止で他プロジェクト (helix-init で配布) に影響 | 中 | helix-init の agents/ コピー部分を W-5 で除外、既存プロジェクトは v1 retain |
| Extra high 制限 (TL=解決不能時 / SE=リファク時) を運用で守らせる仕組み | 低 | tl.conf / se.conf に「extra-high はオーバーライド時のみ」明記、helix doctor で警告 |
| 60% フォールバック判定基準 (週間上限) の自動化 | 中 | helix budget status の ccusage ロジックを拡張、W-3 で `helix budget should-fallback-to` を追加 |
| 移行中に既存タスク (PLAN-024 残 / PLAN-027 残) が v1/v2 混在 | 中 | PLAN-028 完了まで既存タスクは v1 ルールで継続、新タスクのみ v2 適用 |
| ADR/SKILL/docs の参照 path 不整合 (大小文字 ADR/adr 等) | 中 | 既存 `rg` で path 確認、W-4 で一括 path 修正 |

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