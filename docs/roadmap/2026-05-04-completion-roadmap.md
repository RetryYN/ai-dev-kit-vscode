# 2026-05-04 completion roadmap（実態反映版）

## §0 統合方針（実施基準を明記）

- 目的: PLAN-001〜016 と構想2件（Auto-thinking / Builder）の **実装実態を PLAN YAML + git log + docs + retros + メモリ記述** で再評価し、次フェーズ優先度を再構成する。
- DoD 充足度判定は以下を採用する。

| 判定ラベル | 条件 |
|---|---|
| `✅ 実装完了` | `yaml status=finalized` + `実装 commit >= 1` + `retro 有` + `主要受入テスト pass` |
| `🟡 部分実装` | `yaml status=finalized` + `実装 commit >= 1` + `retro 無`、`DoD残 >= 1`、または open deferred finding 残存 |
| `🟠 設計のみ` | `yaml status=finalized` + `実装 commit = 0` |
| `🔴 draft` | `yaml status=draft` または `!= finalized` |
| `⚪ archived` | `yaml status=draft` だが現行正本に supersede 済みで、completion denominator から除外 |

- Sprint 換算ルール
  - 該当 PLAN の `§4.1 Sprint` かそれに準じる Sprint 構成が明示されている場合: その表/列挙された Sprint 数を採用。
  - 非該当: `DoD残数 × 1 Sprint/DoD`。
  - 上限は 5 Sprint。
- finalize md 判定（実装証跡薄弱化ガード）
  - `docs/plans/PLAN-XXX-*.md` が存在すれば `finalize 起草済み`。
  - ファイルが無ければ `yaml ベースのみ` とみなし、実装証跡は弱くなる。

## §A 実態確認（証跡を明示）

### A.1 PLAN-001〜016 実体監査

1) YAML ソース

- 参照: `.helix/plans/PLAN-00{1..16}.yaml`
- 対象フィールド: `status / title / created_at / source_file`
- 取得済み: `PLAN-001` は draft だが PoC skill に supersede 済み、`PLAN-002`〜`PLAN-016` は finalized。

2) docs 起草有無

- PLAN 起草 md: `docs/plans/PLAN-XXX-*.md`
- `PLAN-001` は tracked fallback として `docs/plans/PLAN-001-poc-skill.md` を追加済み。PoC skill に supersede 済みのため、PLAN YAML は監査目的で `draft` のまま維持する。
- それ以外は `PLAN-002`〜`PLAN-016` のファイルが存在。

3) 実装 commit 件数

- `git log --all --oneline | rg "PLAN-XXX"` を PLAN 単位で集計。
- 追加で、`git log --all --oneline | rg -P '(?<![0-9])PLAN-(00[1-9]|01[0-6])(?![0-9])'` を全件保存。

4) retros 対象

- `ls .helix/retros/*.md` + `PLAN-XXX` grep。
- `PLAN-002`〜`PLAN-010` は該当なし。
- `PLAN-011`〜`PLAN-016` は retro が複数件または1件あり（PLAN-013/014/015/016 を含む）。

5) DoD 残数

- 該当 `docs/plans` の `§3.6` / `DoD` セクション配下の未完了チェックを確認。
- 集計結果:
  - `PLAN-013`: DoD 合計=20 / 未解消=0（2026-05-04 Codex 実装で seed metadata 契約と証跡同期を完了）
  - 上記以外: `DoD該当=0`（本集計では未解消0）

### A.2 構想 2 件の実装実態

#### Auto-thinking Phase B

- `cli/lib/effort_classifier.py` : 存在（存在証跡あり）。
- `cli/roles/effort-classifier.conf` : 存在（存在証跡あり）。
- `helix codex --help` : `--auto-thinking` フラグ確認。
- `helix skill --help` : `use ... --auto-thinking` を確認（トップレベルフラグではなく `use` サブコマンド）。
- `helix codex --auto-thinking --dry-run` : classifier 適用と thinking 選択を確認。
- `helix skill use ... --auto-thinking --dry-run --json` : Codex role routing 時に auto-thinking option が保持されることを確認。
- `helix skill stats --json` : usage 統計導線を確認。
- 結論: **Phase B の実行導線と統計導線は存在。長期 telemetry による継続学習は staged backlog 扱いで、active blocker ではない。**

#### Builder System

- `cli/lib/builders/` 配下: `*.py` 14件（`__init__` を含む）、CLI 登録 builder type は 8件。
- `cli/helix-builder` : 存在。
- `cli/helix-builder --help` で `type/action` モデル確認。
- `docs/commands/builder.md` : `generate` 記法が複数出現（例: `task generate`, `workflow generate`）。
- 関連 ADR: `docs/adr/ADR-002-builder-system-foundations.md`, `ADR-008-builder-abstraction.md`, `ADR-003-learning-engine.md`, `docs/adr/index.md`。
- repo-local memory update: `docs/memory/2026-05-04-helix-completion-memory.md`
- 結論: **コア実装は存在し、CLI action 語彙・ADR-008・repo-local memory update は実態へ同期済み。外部 Claude auto memory は repo 完了条件から除外。**

### A.3 git 検索結果（全件）

以下は `git log --all --oneline | rg -n -P '(?<![0-9])PLAN-(00[1-9]|01[0-6])(?![0-9])'` の抜粋全件。

```text
1:73efb40 docs(plan): PLAN-016 v1.0 reviewed (approve) — session-summary md 廃止 → helix log report session 化
2:acd7141 feat(session-summary): PLAN-015 test guard hack 解消 — created_at 明示注入 + DoD #3 fixture redesign
3:27b373e docs(plan): PLAN-015 v1.0 reviewed (approve) — Stop hook test guard hack 解消
5:fbd8605 feat(gate): G10 outcome 詳細永続化 (PLAN-009 v3.3 §3.4.1 仕上げ)
6:a83fe6c feat(verify-agent): harvest/design/cross-check CLI (PLAN-010 v3.3 派生実装)
7:2325e9e feat(reverse): design 5 系統目 + type dispatch (PLAN-008 v3.3 派生実装)
8:3c34948 feat(scrum): trigger detect CLI + helix.db v12 (PLAN-007 v3 派生実装)
9:9c259cf feat(run): G9-G11 + L9-L11 schema 拡張 (PLAN-009 v3.3 派生実装)
10:cb51d90 docs(helix-core,skill-map,gate-policy): readiness + Phase 4 Run 反映 (PLAN-004 v5 / PLAN-009 v3 連動)
11:8b0e91c docs(plan-002,plan-003): readiness retro 反映 (PLAN-004 v5 連動)
12:aabd013 feat(plans): PLAN-004 (PM 報奨設計) + PLAN-005 (運用自動化スキル群) finalize
13:d53b235 feat(plans): PLAN-002 (棚卸し基盤) + PLAN-003 (auto-restart 基盤) finalize
14:a5b5bbf docs(retro): PLAN-013 G4 ミニレトロ — Code Index Eligibility Taxonomy
15:8c76062 feat(code-index): PLAN-011 Sprint .3 — redaction 本実装
16:9873bd1 feat(code-index): PLAN-011 Sprint .1b — helix-code CLI + dispatcher
17:3d9965f feat(code-index): PLAN-011 Sprint .2 — find / dup / stats 本実装
18:bf84194 docs(code-index): PLAN-011 Sprint .5 — SKILL_MAP / HELIX_CORE 反映
19:a5303d0 test(code-index): PLAN-011 Sprint .4 — pytest + bats 拡充
20:33ae912 fix(code-index): PLAN-011 Sprint .6 — TL findings P0+P1+P2 修正
21:8c1c83c test(code-index): PLAN-011 Sprint .6 — bats self-host E2E +5
22:c2157ec docs(plan): PLAN-011 表題を v1.2 に統一
23:8647ec6 feat(code-index): PLAN-011 Sprint .7 — deferred findings 4件解消
24:b12cc10 feat(plan): PLAN-013 v1.4 finalize (code-index eligibility taxonomy)
25:6b14b0a docs(plan): PLAN-013 v1.5
26:869de67 test(code-index): PLAN-013 Sprint .4 — DoD 未カバー領域のテスト追加
27:e0394d9 feat(code-index): PLAN-013 Sprint .3 — CLI flag + flat output 契約
28:bcf1519 feat(code-index): PLAN-013 Sprint .2 — helix.db v15 + 3-bucket classifier
29:24b4e44 docs(plan): PLAN-013 v1.5 schema freeze
30:b4923e6 feat(plan): PLAN-011 v1.1 finalize
31:878d691 docs(plan): PLAN-014 v1.1 reviewed
32:f28f7f1 feat(session-summary): PLAN-014 Stop hook idempotency — rewrite-aware 化
33:27b373e docs(plan): PLAN-015 v1.0 reviewed (approve)
34:acd7141 feat(session-summary): PLAN-015 test guard hack 解消
35:73efb40 docs(plan): PLAN-016 v1.0 reviewed (approve)
```

## §1 全体ステータスマトリクス（PLAN-001〜016）

### 1.1 PLAN-001〜016

| PLAN | title | yaml status | commit数 | retro | DoD残 | 残Sprint | 状態判定 | 備考 |
|---|---|---|---:|---|---:|---|---|
| PLAN-001 | poc | draft | 0 | no | 0 | 0 | ⚪ | superseded archival draft。source_file `docs/plans/PLAN-001-poc-skill.md`。original `/tmp/helix-plan-source-poc.txt` は欠落、PoC 運用正本は `skills/workflow/poc/SKILL.md` |
| PLAN-002 | HELIX 棚卸し基盤 (Phase 0 preflight + A0/A1 inventory + helix.db v8 audit_decisions migration) | finalized | 1 | yes | 0 | 0 | ✅ | retro追加済み。open deferred 0 |
| PLAN-003 | auto-restart 基盤 (HMAC + HOME DB + hook materialization + CURRENT v2 + 残量警告) | finalized | 1 | yes | 0 | 0 | ✅ | retro追加済み。open deferred 0 |
| PLAN-004 | PM 報奨設計 (philosophy shift: 速度 → 正確・精度志向への評価軸調整) | finalized | 3 | yes | 0 | 0 | ✅ | retro追加済み。P2/P3 文書 findings 解消済み |
| PLAN-005 | 運用自動化スキル群 (scheduler/job-queue/lock/init-setup/observability の 5 shared infra skills) | finalized | 1 | yes | 0 | 0 | ✅ | retro追加済み。open deferred 0 |
| PLAN-006 | 上流フェーズ拡張 (L-1 ドキュメント駆動メタフェーズ + リサーチ多様化 + パターンライブラリ) | finalized | 1 | yes | 0 | 0 | ✅ | `helix meta-phase` 実装、project-local pattern 検証、nested applies_when parser 対応、`helix init` pattern template 配置を完了 |
| PLAN-007 | Scrum 5 種化 (差し込みトリガー検出 + 通知中核 / PoC・UI・ユニット・スプリント・デプロイ後) | finalized | 1 | yes | 0 | 0 | ✅ | retro追加済み。P3 用語揺れ finding 解消済み |
| PLAN-008 | Reverse 5 系統化 (Code / Upgrade / Normalization / Fullback / Design) | finalized | 1 | yes | 0 | 0 | ✅ | retro追加済み |
| PLAN-009 | Run 工程フェーズ追加 (L9 デプロイ検証 / L10 観測 / L11 運用学習) | finalized | 3 | yes | 0 | 0 | ✅ | retro追加済み |
| PLAN-010 | 検証ツール選定 + 検証方法設計エージェント (実装検証・PoC 用ツール拾い + verify 設計) | finalized | 1 | yes | 0 | 0 | ✅ | retro追加済み |
| PLAN-011 | コード index 登録システム (PoC → M スコープ実装) | finalized | 12 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-011-code-index-system.md` |
| PLAN-012 | PLAN-011.1 code-index coverage expansion (--uncovered + 網羅 metadata) | finalized | 1 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-012-code-index-coverage.md` |
| PLAN-013 | PLAN-013 Code Index Eligibility Taxonomy and PoC Seed Contract | finalized | 7 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-013-code-index-eligibility-taxonomy.md`（seed metadata 契約と DoD 証跡を同期済み） |
| PLAN-014 | Stop hook idempotency — session-summary 重複行抑制 | finalized | 2 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-014-stop-hook-idempotency.md` |
| PLAN-015 | Stop hook test guard hack 解消 (DoD #3 fixture redesign) | finalized | 2 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-015-stop-hook-test-guard-hack.md` |
| PLAN-016 | session-summary md 廃止 — helix log report session 化 | finalized | 1 | yes | 0 | 0 | ✅ | `cli/helix-session-summary` を 153 → 39 行のシム化（stdout/stderr 完全静音 + cost_log INSERT のみ）、`cli/tests/test-helix-session-summary.bats` を 8 ケースで全面再設計、retro 追加 |
| PLAN-017 | bats coverage core CLI 補完 | finalized (retroactive) | 1 | no | 0 | 0 | 🟡 | 起草前に実装着手 (commit `d32c2d4` で spec+実装+テスト同時化)、retro 未作成 |
| PLAN-018 | LLM Guard 事後ハードニング | finalized (retroactive) | 1 | no | 0 | 0 | 🟡 | PLAN 不在状態で実装 (`3f703b7`) → 事後 PLAN 作成、retro 未作成 |
| PLAN-019 | helix-migrate target 拡張 (CLAUDE.md / AGENTS.md / .claude/settings.json) | finalized | 1 (impl: PLAN-020 Sprint .4) | no | 0 | 0 | ✅ | finalize は 2026-05-05、実装は PLAN-020 Sprint .4 で吸収 (commit `5185fb8`)、P2 finding 3 件全消化 |
| PLAN-020 | HELIX 最新基準適合化整備 (gpt-5.5 追従 / 委譲 Codex コミット禁止 / D-shard auto-skeleton + G2 / PLAN-019 実装) | finalized | 6 | no | 0 | 0 | ✅ | review round trip 省略 (skipped_by_user_directive)、Sprint .1〜.4 完走 (commits `2d1e96d` `2915757` `a97a37e` `5185fb8` `7f1d785` `fff7666`)、pytest 847 + bats 270 全 PASS |

### 1.2 構想2件（実態を反映）

| 構想 | 状態 | 実体確認 | 残課題 |
|---|---|---|---|
| Auto-thinking Phase B | staged | `effort_classifier.py` + `effort-classifier.conf` + `helix codex --auto-thinking` + `helix skill use --auto-thinking` + `helix skill stats --json` | 長期 telemetry による継続学習は staged backlog。active blocker ではない |
| Builder System | 実装中核あり | `cli/lib/builders/*` 実装 + `helix builder` 存在 + 8 registered builders | repo 内 docs/ADR と memory update は同期済み |

## §2 重要発見（P1: memory と実装実態のずれ）

1. **P1 resolved**: 本 checkout には `MEMORY.md` が存在しないため、旧式 memory 記述を active blocker として扱わない。共有可能な更新内容は `docs/memory/2026-05-04-helix-completion-memory.md` に保存済み。
2. **P3 resolved**: builder help の action 例と ADR-008 の登録 builder 数は実態に同期済み。

## §3 Minimum Completion Cut

### 3.1 含める PLAN / タスク

- `PLAN-011`
- `PLAN-012`
- `PLAN-013`
- `PLAN-014`
- `PLAN-015`
- `PLAN-016`

### 3.2 根拠

- `yaml status=finalized`
- `実装commit >= 1`
- `retro 有`
- `DoD残=0`

上記は本リポジトリの実装証跡と受入証跡が最も整合しているため、最小完了候補とする。

### 3.3 Sprint 内訳（再計算）

- 上記6件の `残Sprint`: 各 0（DoD残0、PLAN-013 は `.helix/sprint/PLAN-013-completion.yaml` に証跡化済み）
- 合計: **0 Sprint**

### 3.4 工期目安

- 現時点の Minimum Completion Cut は、追加実装よりも **状態確認と証拠整備の完了** が中心。
- 体感工数: **0.5〜1 Sprint 相当**（整合確認・受入条件反映）

## §4 Full Track（Minimum Cut 後）

### 4.1 追加対象

- 追加で `PLAN-002`〜`PLAN-010`
- `PLAN-013` は DoD 残 0 に同期済みのため Minimum Completion Cut へ昇格
- Dashboard は構想管理から除外し、既存の静的 CLI 表示コマンドとして扱う

### 4.2 受け入れ順序（提案）

1. ~~`PLAN-008/009/010` の retro 補完~~（2026-05-04 完了。PLAN-002〜010 まで補完済み）
2. ~~`PLAN-002` quarantine と `PLAN-003` HMAC/CURRENT/rate-limit の residual P2 deferred findings 解消、および `PLAN-005` の redacted P3 finding 判断~~（2026-05-04 完了）
3. ~~`PLAN-006` の最小実装化~~（2026-05-04 `helix meta-phase` 追加。project-local pattern 検証、nested `applies_when`、`helix init` template 配置まで完了）

## §5 PM 確認事項

- 前回 `P1-P6` に加え、追加で以下を確認したい。
- `PLAN-002`〜`PLAN-010` の retro 未作成は 2026-05-04 に補完済み。
- `PLAN-002/003/005` の deferred findings は 2026-05-04 に文書契約へ反映し、open 0 に同期済み。
- `helix skill --auto-thinking` を use 単位から運用系に拡張する方針。
- PLAN-001 は PoC skill に supersede 済み。正式 review/finalize は行わず、archival draft として維持する。

## §6 Memory Update

### 6.1 Auto-thinking 自動調整構想

- repo-local 記録: `-- 2026-04-21 Phase A 完了。Phase B は実装導線と stats 導線が存在する。長期 telemetry による継続学習は staged backlog。`
- Repo-local memory update: `docs/memory/2026-05-04-helix-completion-memory.md`
- Opus 用メモ素材: `cli/lib/effort_classifier.py` と `cli/roles/effort-classifier.conf`、`helix codex --auto-thinking`、`helix skill use --auto-thinking`、`helix skill stats --json`。

### 6.2 Builder System

- repo-local 記録: `-- 現在は実装済（`cli/lib/builders/*` + `cli/helix-builder`、8 registered builders）。repo 内 docs/ADR と memory update は実装仕様に同期済み。`
- Opus 用メモ素材: `docs/commands/builder.md`。

### 6.3 HELIX dashboard の扱い

- repo-local 記録: `-- Dashboard 構想は管理対象から外す。cli/helix-dashboard は静的 CLI 表示コマンドとして維持。`
- Opus 用メモ素材: `cli/helix-dashboard`, `docs/commands/dashboard.md`。

## §7 受入条件 / 検証コマンド

### 7.1 受入条件

- PLAN 状態判定が本ドキュメント定義（DoD/commit/retro/finalize md）と一致。
- A2 の構想実態が最新証跡と一致。
- dashboard は構想管理から除外され、通常の静的 CLI 表示コマンドとして扱われている。

### 7.2 検証コマンド

- `rg '^PLAN-[0-9]{3}\|' .helix/plans/*.yaml`（状態取得）
- `rg 'PLAN-(00[1-9]|01[0-6])' .helix/retros/*.md`（retro 有無）
- `git log --all --oneline | rg -P '(?<![0-9])PLAN-(00[1-9]|01[0-6])(?![0-9])' > /tmp/plan-grep.txt`
- `markdownlint-cli docs/roadmap/2026-05-04-completion-roadmap.md`
- `npx markdown-link-check docs/roadmap/2026-05-04-completion-roadmap.md`
- `git diff -- docs/roadmap/2026-05-04-completion-roadmap.md`
- `rg -n "\]\(" docs/roadmap/2026-05-04-completion-roadmap.md`（リンク参照確認）

### 7.3 参照ファイル一覧（本次版）

- `.helix/plans/*.yaml`
- `docs/plans/PLAN-*.md`
- `.helix/retros/*.md`
- `cli/lib/effort_classifier.py`
- `cli/roles/effort-classifier.conf`
- `cli/helix-codex`
- `cli/helix-skill`
- `cli/lib/builders/*.py`
- `cli/helix-builder`
- `docs/commands/builder.md`
- `cli/helix-dashboard`
- `docs/commands/dashboard.md`
- Memory files: `docs/memory/2026-05-04-helix-completion-memory.md`（外部 auto memory は repo 完了条件から除外）

## §8 overall_scores（5軸評価）

| dimension | level | comment |
|---|---:|---|
| density | 4 | 証跡（YAML/commit/log/retros) を PLAN 全件で集約し、欠落が明示されている。 |
| depth | 3 | DoD残数や構想別の統合検証は実施。ただし一部 PLAN の DoD セクション構文差の厳密集計は追加標準化が必要。 |
| breadth | 4 | PLAN本体＋構想2件＋Memory訂正＋検証コマンドまで含めた広域横断。 |
| accuracy | 3 | PLAN 008/009 の §4.1 Sprint 変換は保守的に扱っているため、将来の厳密解釈差が残る。 |
| maintainability | 4 | 単一ファイルへの統合と評価基準明文化で更新性は高い。 |

## §9 Findings（P0〜P3）

- P1: PLAN-013 の DoD 残は 2026-05-04 の同期で解消済み。Builder System の memory 差分は repo-local memory update に保存済み。
- P3: Builder CLI の help/docs と ADR-008 は実装実態へ同期済み。

## 付録: A の証跡保存

### A.1 read 対象一覧

- `.helix/plans/PLAN-*.yaml`
- `docs/plans/PLAN-*.md`
- `.helix/retros/*.md`
- `cli/lib/effort_classifier.py`
- `cli/roles/effort-classifier.conf`
- `cli/helix-codex`
- `cli/helix-skill`
- `cli/lib/builders/*.py`
- `cli/helix-builder`
- `docs/commands/builder.md`
- Memory update（`docs/memory/2026-05-04-helix-completion-memory.md`）

### A.2 Dashboard 構想除外確認

- `cli/helix-dashboard`: exists
- `docs/commands/dashboard.md`: exists
- `cli/helix dashboard --json`: parseable JSON を出力
- 方針: 構想管理から外し、静的 CLI 表示コマンドとして維持
