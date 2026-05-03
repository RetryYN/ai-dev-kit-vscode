# 2026-05-04 completion roadmap（実態反映版）

## §0 統合方針（実施基準を明記）

- 目的: PLAN-001〜016 と構想3件（Auto-thinking / Builder / Dashboard）の **実装実態を PLAN YAML + git log + docs + retros + メモリ記述** で再評価し、次フェーズ優先度を再構成する。
- DoD 充足度判定は以下を採用する。

| 判定ラベル | 条件 |
|---|---|
| `✅ 実装完了` | `yaml status=finalized` + `実装 commit >= 1` + `retro 有` |
| `🟡 部分実装` | `yaml status=finalized` + `実装 commit >= 1` + `retro 無` または `DoD残 >= 1` |
| `🟠 設計のみ` | `yaml status=finalized` + `実装 commit = 0` |
| `🔴 draft` | `yaml status=draft` または `!= finalized` |

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
- 取得済み: `PLAN-001` は draft、`PLAN-002`〜`PLAN-016` は finalized。

2) docs 起草有無

- PLAN 起草 md: `docs/plans/PLAN-XXX-*.md`
- `PLAN-001` は `mdなし`。
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
  - `PLAN-013`: DoD 合計=20 / 未解消=20
  - 上記以外: `DoD該当=0`（本集計では未解消0）

### A.2 構想 3 件の実装実態

#### Auto-thinking Phase B

- `cli/lib/effort_classifier.py` : 存在（存在証跡あり）。
- `cli/roles/effort-classifier.conf` : 存在（存在証跡あり）。
- `cli/helix-codex --help` : `--auto-thinking` フラグ確認。
- `cli/helix-skill --help` : `use ... --auto-thinking` を確認（トップレベルフラグではなく `use` サブコマンド）。
- 結論: **Phase B は導線の一部が有効、ただし telemetry 記録/実効実績の継続的更新は未確認**。

#### Builder System

- `cli/lib/builders/` 配下: `*.py` 14件（`__init__` を含む）。
- `cli/helix-builder` : 存在。
- `cli/helix-builder --help` で `type/action` モデル確認。
- `docs/commands/builder.md` : `generate` 記法が複数出現（例: `task generate`, `workflow generate`）。
- 関連 ADR: `docs/adr/ADR-002-builder-system-foundations.md`, `ADR-008-builder-abstraction.md`, `ADR-003-learning-engine.md`, `docs/adr/index.md`。
- 結論: **コア実装は存在するが、CLI 実態とドキュメント語彙の整合が弱い（hardening観点: generate/build 仕様ずれ、運用記述不足）。**

#### Dashboard

- `cli/helix-dashboard`: 実体未存在（未実装）。
- `docs/commands/dashboard.md`: 実体未存在（未実装）。
- 関連 grep: `dashboard` 記述は主に PLAN-009、ROADMAP や記憶メモの企画文脈に限定。
- 結論: **現時点は「構想のみ / 未実装」。**

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
| PLAN-001 | poc | draft | 0 | no | 0 | 0 | 🔴 | source_file `/tmp/helix-plan-source-poc.txt` |
| PLAN-002 | HELIX 棚卸し基盤 (Phase 0 preflight + A0/A1 inventory + helix.db v8 audit_decisions migration) | finalized | 1 | no | 0 | 0 | 🟡 | 起草: `docs/plans/PLAN-002-helix-inventory-foundation.md` |
| PLAN-003 | auto-restart 基盤 (HMAC + HOME DB + hook materialization + CURRENT v2 + 残量警告) | finalized | 1 | no | 0 | 0 | 🟡 | 起草: `docs/plans/PLAN-003-auto-restart-foundation.md` |
| PLAN-004 | PM 報奨設計 (philosophy shift: 速度 → 正確・精度志向への評価軸調整) | finalized | 3 | no | 0 | 0 | 🟡 | 起草: `docs/plans/PLAN-004-pm-reward-design.md` |
| PLAN-005 | 運用自動化スキル群 (scheduler/job-queue/lock/init-setup/observability の 5 shared infra skills) | finalized | 1 | no | 0 | 0 | 🟡 | 起草: `docs/plans/PLAN-005-ops-automation-skills.md` |
| PLAN-006 | 上流フェーズ拡張 (L-1 ドキュメント駆動メタフェーズ + リサーチ多様化 + パターンライブラリ) | finalized | 0 | no | 0 | 0 | 🟠 | 起草: `docs/plans/PLAN-006-upstream-meta-phase.md` |
| PLAN-007 | Scrum 5 種化 (差し込みトリガー検出 + 通知中核 / PoC・UI・ユニット・スプリント・デプロイ後) | finalized | 1 | no | 0 | 0 | 🟡 | 起草: `docs/plans/PLAN-007-scrum-multitype-trigger.md` |
| PLAN-008 | Reverse 5 系統化 (Code / Upgrade / Normalization / Fullback / Design) | finalized | 1 | no | 0 | 0 | 🟡 | 起草: `docs/plans/PLAN-008-reverse-multitype.md` |
| PLAN-009 | Run 工程フェーズ追加 (L9 デプロイ検証 / L10 観測 / L11 運用学習) | finalized | 3 | no | 0 | 0 | 🟡 | 起草: `docs/plans/PLAN-009-run-phase-l9-l11.md` |
| PLAN-010 | 検証ツール選定 + 検証方法設計エージェント (実装検証・PoC 用ツール拾い + verify 設計) | finalized | 1 | no | 0 | 0 | 🟡 | 起草: `docs/plans/PLAN-010-verification-agent.md` |
| PLAN-011 | コード index 登録システム (PoC → M スコープ実装) | finalized | 12 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-011-code-index-system.md` |
| PLAN-012 | PLAN-011.1 code-index coverage expansion (--uncovered + 網羅 metadata) | finalized | 1 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-012-code-index-coverage.md` |
| PLAN-013 | PLAN-013 Code Index Eligibility Taxonomy and PoC Seed Contract | finalized | 7 | yes | 20 | 5 | 🟡 | 起草: `docs/plans/PLAN-013-code-index-eligibility-taxonomy.md`（DoD 残が残存） |
| PLAN-014 | Stop hook idempotency — session-summary 重複行抑制 | finalized | 2 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-014-stop-hook-idempotency.md` |
| PLAN-015 | Stop hook test guard hack 解消 (DoD #3 fixture redesign) | finalized | 2 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-015-stop-hook-test-guard-hack.md` |
| PLAN-016 | session-summary md 廃止 — helix log report session 化 | finalized | 1 | yes | 0 | 0 | ✅ | 起草: `docs/plans/PLAN-016-session-summary-helix-log-report.md` |

### 1.2 構想3件（実態を反映）

| 構想 | 状態 | 実体確認 | 残課題 |
|---|---|---|---|
| Auto-thinking Phase B | 部分実装 | `effort_classifier.py` + `effort-classifier.conf` + `helix-codex --auto-thinking` あり | `helix-skill` は `use` 配下フラグのみ。統計/学習反映、運用観測連携は未確認 |
| Builder System | 実装中核あり | `cli/lib/builders/*` 実装 + `helix-builder` 存在 + 14 builder | `docs/commands/builder.md` の generate/build 用語齟齬、ADR 運用と実装の差分吸収 |
| Dashboard | 未実装 | `cli/helix-dashboard` 無し、`docs/commands/dashboard.md` 無し | 本番可視化経路未存在。構想文書（保留）との差分大 |

## §2 重要発見（P1: memory と実装実態のずれ）

1. **P1**: `MEMORY.md` が「Builder System」を構想として記載しつつ、実体では cli/lib/builders と helix-builder が既に実装済み。記述が旧式。`PLAN-013` の DoD 実残が 20 のまま `yaml status=finalized` / docs 起草済みで進捗解像度が低い。
2. **P2**: Dashboard は memory で構想が継続される一方、実装本体とコマンド doc が未作成。
3. **P2**: builder doc の `generate` と builder CLI 実装の `create/list/show` の語彙不一致。

## §3 Minimum Completion Cut

### 3.1 含める PLAN / タスク

- `PLAN-011`
- `PLAN-012`
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

- 上記5件の `残Sprint`: 各 0（DoD残0、§4.1 明示されていないため）
- 合計: **0 Sprint**

### 3.4 工期目安

- 現時点の Minimum Completion Cut は、追加実装よりも **状態確認と証拠整備の完了** が中心。
- 体感工数: **0.5〜1 Sprint 相当**（整合確認・受入条件反映）

## §4 Full Track（Minimum Cut 後）

### 4.1 追加対象

- 追加で `PLAN-002`〜`PLAN-010`（`PLAN-006` は設計のみ）
- `PLAN-013` は実装commitはあるが DoD 残 20 のため次フェーズに留置
- Dashboard 構想: 実装前提が未完（構想管理のみ）

### 4.2 受け入れ順序（提案）

1. `PLAN-013` の DoD 解消（20）
2. `PLAN-008/009/010` の retro 補完
3. `PLAN-006` の実装化
4. Dashboard 方針の着手可否判断（構想→PoC）

## §5 PM 確認事項

- 前回 `P1-P6` に加え、追加で以下を確認したい。
- `PLAN-013` の DoD 残20を次スプリントで消化するか、再定義するか。
- `PLAN-002`〜`PLAN-010`（retro未作成）を Minimum Cut から外す基準を維持するか。
- `helix-skill --auto-thinking` を use 単位から運用系に拡張する方針。
- Builder docs の `generate` 呼称を `create` 系に統一するか、実 CLI を generate 系へ合わせるか。
- Dashboard を先行実装する基準（TUI/serve/静的出力）を PM と合意。

## §6 MEMORY.md 訂正案

### 6.1 Auto-thinking 自動調整構想

- 現行（該当行）: `-- 2026-04-21 Phase A 完了 / Phase B 保留`
- 訂正案: `-- 2026-04-21 Phase A 完了。Phase B は実装導線は存在するが、telemetry/観測と運用運用条件の最終化待ち。`
- Opus 用メモ素材: `cli/lib/effort_classifier.py` と `cli/roles/effort-classifier.conf`、`helix-codex --auto-thinking`、`helix-skill use --auto-thinking`。

### 6.2 Builder System

- 現行（該当行）: `-- エージェント系タスクの設計・実装時にこの構想を前提にする。cli/lib/builders/ に Python モジュールとして配置予定。`
- 訂正案: `-- 現在は実装済（`cli/lib/builders/*` + `cli/helix-builder`）。ドキュメントは `docs/commands/builder.md` の語彙を実装仕様に合わせた整合化が必要。`
- Opus 用メモ素材: `docs/commands/builder.md`。

### 6.3 HELIX 開発ダッシュボード構想

- 現行（該当行）: `-- 動的 dashboard (serve/TUI) で状態可視化、2026-04-21 保留、後着手予定`
- 訂正案: `-- 2026-04-21 保留の構想。現時点では実装コマンド(`cli/helix-dashboard`)・コマンド仕様書(`docs/commands/dashboard.md`)とも未作成。`
- Opus 用メモ素材: `cli/helix-dashboard` 不在、`docs/commands/dashboard.md` 不在。

## §7 受入条件 / 検証コマンド

### 7.1 受入条件

- PLAN 状態判定が本ドキュメント定義（DoD/commit/retro/finalize md）と一致。
- A2 の構想実態が最新証跡と一致。
- dashboard 構想は「未実装」を明示し、着手判定がPMと一致。

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
- Memory files: `project_auto_thinking.md`, `project_builder_system.md`, `project_helix_dashboard_idea.md`, `MEMORY.md`

## §8 overall_scores（5軸評価）

| dimension | level | comment |
|---|---:|---|
| density | 4 | 証跡（YAML/commit/log/retros) を PLAN 全件で集約し、欠落が明示されている。 |
| depth | 3 | DoD残数や構想別の統合検証は実施。ただし一部 PLAN の DoD セクション構文差の厳密集計は追加標準化が必要。 |
| breadth | 4 | PLAN本体＋構想3件＋Memory訂正＋検証コマンドまで含めた広域横断。 |
| accuracy | 3 | PLAN 008/009/013 の §4.1 Sprint 変換は保守的に扱っているため、将来の厳密解釈差が残る。 |
| maintainability | 4 | 単一ファイルへの統合と評価基準明文化で更新性は高い。 |

## §9 Findings（P0〜P3）

- P1: PLAN-013 は finalized で retro ありでも DoD 残 20 が未解消のまま残存。実装証跡だけで完了とみなされるリスクがある。
- P1: Dashboard は構想文書上存在するが、`cli/helix-dashboard` / `docs/commands/dashboard.md` が未作成。運用投入前提と実装の乖離が大きい。
- P2: Builder ドキュメントに `generate` 表現が残り、`helix builder` 実装の `create/list/show` 体系との一致不足がある。

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
- Memory 一式（`MEMORY.md`, `project_auto_thinking.md`, `project_builder_system.md`, `project_helix_dashboard_idea.md`）

### A.2 Dashboard 実装未完了確認

- `cli/helix-dashboard`: non-existent
- `docs/commands/dashboard.md`: non-existent
- 実装 grep でも `dashboard` は企画/PLAN 文脈の参照が中心で、実体コマンド定義は見当たらない
