# FR-INV06: 廃止候補集約

最終更新: 2026-05-14

## 概要

- 対象: `docs/v2/A-audit/*.md` の既存 18 audit doc
- 集約条件: 各 audit doc の **V2 変更計画** が `deprecate` / `archive` / `merge` のものだけを廃止扱いで集約
- 除外条件: 既存 audit doc に書かれていない候補は追加しない
- 目的: V2 廃止 roadmap を、削除順・依存・承認要否まで含めて 1 枚で判断できる状態にする

## 前提と不確実性

- 本集約は **既存 audit の静的読解** に基づく。削除可否そのものの最終判断ではない。
- `reverse-scrum-audit.md` の `deprecate` は「選択肢比較」であり、採択済み計画ではないため **台帳には採用しない**。
- 次の 6 doc は読了したが、今回の抽出条件に合う `deprecate/archive/merge` 行を持たなかった:
  - `accumulated-knowledge.md`
  - `capability-matrix.md`
  - `fe-weakness-analysis.md`
  - `legacy-plans-carry.md`
  - `perf-cost-audit.md`
  - `reverse-scrum-audit.md`

## 選択肢

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| audit 判定どおりに即削除中心で進める | repo 縮小が速い | hook/runtime/PLAN 系の誤削除リスクが高い | 低 |
| 廃止台帳を作り、Phase 別に波状撤去する | 依存関係と承認境界を保てる | 先に台帳整備の手間がかかる | 高 |
| `merge` をすべて「物理削除なし」に寄せる | 運用事故が起きにくい | source-of-truth 重複が温存される | 中 |

## 推奨

- 推奨は **「台帳化して 4 wave で順次廃止」**。
- Phase 1 は wrapper / cache / stale doc / deprecated alias のような **局所影響で戻しやすいもの**に限定する。
- Phase 2-5 は source-of-truth 統合が前提の `merge` 群を処理する。
- V2 完了後は dogfood の観測が必要な runtime / DB / generated artifact を整理する。
- V3 / 永久 carry は upstream 参照や knowledge 統合作業のように、削除より「正本の縮退」を優先する。

## DEP 台帳

| DEP-ID | 項目名 | 出典 audit | 種別 | 理由 | 影響範囲 | 代替 | 廃止 timing | 依存 | 承認要否 |
|---|---|---|---|---|---|---|---|---|---|
| DEP-001 | `cli/helix-session-summary` + `.helix/session-summaries/` | `capability-inventory.md`, `folder-structure-audit.md` | hook | md session summary は `cost_log` / `helix log report` へ責務移送済み | Stop hook 互換、運用履歴参照 | `cost_log`, `helix log report session` | V2 完了後 | - | PM 判断 |
| DEP-002 | `cli/helix-session-start` wrapper | `cicd-audit.md` | hook | libexec 実体に対する旧 entrypoint 互換だけが残る | `SessionStart` 呼び出し、shell wrapper 参照 | `cli/libexec/helix-session-start` | Phase 2-5 | - | PM 判断 |
| DEP-003 | `cli/helix-check-claudemd` wrapper | `hooks-commands-subagents.md`, `security-audit.md` | hook | deprecated wrapper が監査境界を曖昧にする | PreToolUse hook、旧呼び出し経路 | `cli/libexec/helix-check-claudemd` | Phase 1 (即) | - | 自動廃止 |
| DEP-004 | `.git/hooks/pre-commit.helix.bak` | `cicd-audit.md` | hook | 手動復旧用の残骸で通常運用に不要 | ローカル git hook 復旧手順 | `cli/templates/hooks/pre-commit` | Phase 1 (即) | - | 自動廃止 |
| DEP-005 | `helix discover` legacy alias | `cli-ux-audit.md` | command | `recipe discover` と二重で入口を増やすだけ | command help、既存 alias 呼び出し | `helix recipe discover` | Phase 1 (即) | - | 自動廃止 |
| DEP-006 | `helix learn` legacy alias | `cli-ux-audit.md` | command | `recipe learn` と二重で命名政策を乱す | command help、既存 alias 呼び出し | `helix recipe learn` | Phase 1 (即) | - | 自動廃止 |
| DEP-007 | `helix promote` legacy alias | `cli-ux-audit.md` | command | `recipe promote` と二重で命名政策を乱す | command help、既存 alias 呼び出し | `helix recipe promote` | Phase 1 (即) | - | 自動廃止 |
| DEP-008 | `debt_items` table | `db-schema-current.md` | config / runtime | YAML 正本が強く、DB table は未使用で二重管理 | `helix-dashboard` の debt 読み出し、将来 migration | YAML debt source | V2 完了後 | - | PM 判断 |
| DEP-009 | `CLAUDE.md` 内の固定 model 表 | `docs-integrity-audit.md` | doc | `ROLE_MAP` / `models.yaml` と三重不一致の温床 | `CLAUDE.md` 読者、role 周知 | `cli/ROLE_MAP.md`, `cli/config/models.yaml` | Phase 1 (即) | - | 自動廃止 |
| DEP-010 | `docs/agent-skills/README.md` を HELIX 正本として扱う運用 | `docs-integrity-audit.md` | doc | upstream README を HELIX 正本として流用し過ぎている | skill 数説明、導線文書 | HELIX skill docs / `skills/SKILL_MAP.md` | V3 / 永久 carry | - | PM 判断 |
| DEP-011 | `.helix/tmp` | `folder-structure-audit.md` | config / runtime | 一時出力が repo 常駐し runtime 汚染が大きい | debug 手順、差分比較、一時成果物 | runtime TTL cleanup | Phase 1 (即) | - | 自動廃止 |
| DEP-012 | `.helix/cache/skill_classifier` | `folder-structure-audit.md` | config / runtime | cache 永続化が repo 常駐している | skill 推挙 cache | runtime TTL cleanup | Phase 1 (即) | - | 自動廃止 |
| DEP-013 | `__pycache__` 群 + `.pytest_cache/` | `folder-structure-audit.md` | test | 生成 cache が追跡対象になっている | pytest/import、ローカル開発 | `gitignore` + clean target | Phase 1 (即) | - | 自動廃止 |
| DEP-014 | `cli/tests/.helix/` + `cli/tests/`/`cli/lib/tests/`/`tests/` + `verify/` の分散 | `folder-structure-audit.md` | test | test 入口と fixture runtime が分散し責務境界が曖昧 | CI matrix、Bats fixture、verify shell | `tests/{bats,pytest,integration,verify}` などの統合配置 | Phase 2-5 | - | PM 判断 |
| DEP-015 | hook 定義 3+1 系統 (`.claude/hooks`, `cli/templates/hooks`, `skills/agent-skills/hooks`, `scripts/git-hooks`) | `folder-structure-audit.md` | hook | source-of-truth が複数あり drift しやすい | Claude/Codex install、git hook 配布 | `hooks/` source-of-truth + generated copy | Phase 2-5 | DEP-033 | PM 判断 |
| DEP-016 | `.claude/commands` と `docs/commands` の二重正本 | `folder-structure-audit.md` | command | slash command 実体と説明 docs が分離して drift 余地がある | Claude command UX、docs sync | `docs/commands/` 正本 + generated `.claude/commands` | Phase 2-5 | - | PM 判断 |
| DEP-017 | `/ship` slash command | `hooks-commands-subagents.md` | command | Agent tool fan-out 前提で v2 方針と衝突 | `.claude/commands/ship.md`、review/security/qa fan-out | `helix review --uncommitted` + role-based flow | Phase 2-5 | DEP-016 | PM 判断 |
| DEP-018 | native subagent 4 件 (`be-api`, `be-logic`, `db-schema`, `devops-deploy`) | `hooks-commands-subagents.md` | config / runtime | v2 は native subagent 非推奨で role 重複が大きい | `.claude/agents/*.md`、旧運用ドキュメント | `se`, `dba`, `devops` role | Phase 2-5 | DEP-019 | PM 判断 |
| DEP-019 | `.claude/agents` と `cli/templates/agents` の二重管理 | `folder-structure-audit.md` | config / runtime | agent prompt の source が 2 系統あり統制できない | template install、agent prompt 更新 | `agents/` source-of-truth | Phase 2-5 | - | PM 判断 |
| DEP-020 | `skills/*/references` の過細分化 | `folder-structure-audit.md` | skill | reference 分割が多すぎ探索コストが高い | skill docs、参照導線 | skill 単位 index 再編 | Phase 2-5 | - | PM 判断 |
| DEP-021 | `project/fe-*` 5 分割 + `project/ui` の二重入口 | `folder-structure-audit.md`, `skill-quality-audit.md` | skill | FE skill が微粒度で散在し `project/ui` と二重化 | FE skill docs、references、dispatch | `skills/project/ui/` 配下再編 | Phase 2-5 | DEP-020 | PM 判断 |
| DEP-022 | `automation/init-setup` と `automation/observability` の分離 | `skill-quality-audit.md` | skill | 小粒 skill のまま分裂し価値密度が低い | automation skill 導線 | どちらかを統合パック化 | Phase 2-5 | DEP-020 | 自動廃止 |
| DEP-023 | `workflow/research` と `tools/web-search` の分離 | `skill-quality-audit.md` | skill | 調査実務と検索手段が分断され G1R 導線が遠い | research skill 導線 | 一体化した research skill chain | Phase 2-5 | DEP-020 | PM 判断 |
| DEP-024 | `workflow/incident` と `workflow/postmortem` の分離 | `skill-quality-audit.md` | skill | 障害対応と学習が近接し過ぎている | incident/postmortem 導線 | 同一パック化 | Phase 2-5 | DEP-020 | PM 判断 |
| DEP-025 | `skills/workflow/reverse-r0..rgc` の 6 分割 | `folder-structure-audit.md` | skill | reverse 導線が深く、dispatch に対して粒度が細かい | reverse dispatch、skill docs | `workflow/reverse-analysis/` subdocs | Phase 2-5 | DEP-020 | PM 判断 |
| DEP-026 | `docs/features/PLAN-*` と `docs/plans/PLAN-*` の二重軸 | `folder-structure-audit.md` | PLAN doc | PLAN 軸 docs が二重化して追跡コストが高い | plan lookup、feature maintainability、links | feature doc を plan appendix へ統合 | Phase 2-5 | - | PM 判断 |
| DEP-027 | `docs/v2/A-audit/` という audit 島 | `folder-structure-audit.md` | doc | audit docs が局所ディレクトリ化し taxonomy が分断 | audit links、参照導線 | `docs/audit/v2/` | Phase 2-5 | - | PM 判断 |
| DEP-028 | `public/generated/codex` | `folder-structure-audit.md` | config / runtime | 生成物が repo に常駐している | asset reference、build 導線 | build artifact 化 | V2 完了後 | - | PM 判断 |
| DEP-029 | `helix/sync-codex-skills.sh` | `off-plan-implementations.md`, `folder-structure-audit.md` | command | 単発 script が root policy と installer 導線から孤立 | setup docs、暫定セットアップ | installer / migrate workflow | Phase 2-5 | - | 自動廃止 |
| DEP-030 | stale archive memory 群 (`restructure-plan.md`, `reference_codex_plugin_cc.md`, `project_builder_system.md`, `project_next_wave.md`) | `memory-feedback-drift.md` | doc | stale / schema外 / 現行 PLAN 外で残存価値が低い | memory index、過去参照 | archive 領域へ隔離または除去 | Phase 1 (即) | - | PM 判断 |
| DEP-031 | stale merge memory 群 (`project_helix_v2_deliverable_matrix.md`, `project_helix_vision.md`, `feedback_*` cluster) | `memory-feedback-drift.md` | doc | concept / feedback が分散し memory に重複している | memory index、feedback cluster、V2 concept | V2 concept / common rule へ統合 | V3 / 永久 carry | - | PM 判断 |
| DEP-032 | `pm-advisor`, `tl-advisor`, `impl-sonnet` role config の off-plan 独立管理 | `off-plan-implementations.md` | config / runtime | 実体は必要だが PLAN 正本から浮いている | role catalog、orchestration docs | PLAN-028 系へ統合 | Phase 2-5 | - | PM 判断 |
| DEP-033 | `.claude/settings.json` の hook 配線を独立 capability として持つ状態 | `off-plan-implementations.md` | hook | 複数 PLAN に散在し最終配線の正本がない | SessionStart/PreToolUse/PostToolUse/Stop 配線 | hook source-of-truth へ統合 | Phase 2-5 | - | PM 判断 |

## カテゴリ別集計

| カテゴリ | 件数 | Phase 1 即廃止 | Phase 2-5 | V2 後 | V3 / 永久 |
|---|---:|---:|---:|---:|---:|
| code (`cli/lib/*`) | 0 | 0 | 0 | 0 | 0 |
| hook | 6 | 2 | 4 | 0 | 0 |
| command | 6 | 3 | 3 | 0 | 0 |
| skill | 6 | 0 | 6 | 0 | 0 |
| PLAN doc | 1 | 0 | 1 | 0 | 0 |
| doc (other) | 5 | 2 | 1 | 0 | 2 |
| dependency | 0 | 0 | 0 | 0 | 0 |
| config / runtime | 7 | 2 | 3 | 2 | 0 |
| test | 2 | 1 | 1 | 0 | 0 |
| 合計 | 33 | 10 | 18 | 3 | 2 |

## 廃止 roadmap

### Phase 1 (即廃止、Wave 1)

- DEP-003 `cli/helix-check-claudemd` wrapper
- DEP-004 `.git/hooks/pre-commit.helix.bak`
- DEP-005/006/007 legacy recipe alias (`discover`, `learn`, `promote`)
- DEP-009 `CLAUDE.md` の固定 model 表
- DEP-011 `.helix/tmp`
- DEP-012 `.helix/cache/skill_classifier`
- DEP-013 `__pycache__` 群 + `.pytest_cache/`
- DEP-030 stale archive memory 群

### Phase 2-5 (V2 中、Wave 2)

- DEP-002 SessionStart wrapper
- DEP-014 test layout / fixture runtime の統合
- DEP-015 hook source-of-truth の一本化
- DEP-016 `/commands` 正本の一本化
- DEP-017 `/ship` 廃止
- DEP-018/019 native subagent と agent template 二重管理の解消
- DEP-020〜025 skill 分割・重複群の統合
- DEP-026 PLAN doc 二重軸解消
- DEP-027 audit docs の配置統合
- DEP-029 `helix/sync-codex-skills.sh`
- DEP-032 advisor / impl-sonnet role config の PLAN 統合
- DEP-033 hook 配線の正本化

### V2 完了後 (Wave 3)

- DEP-001 session summary md/shim の停止
- DEP-008 `debt_items` table
- DEP-028 `public/generated/codex`

### V3 / 永久 carry (Wave 4)

- DEP-010 `docs/agent-skills/README.md` は upstream/vendor 文書として残し、HELIX 正本からだけ退役させる
- DEP-031 memory merge 群は memory schema と concept 正本整理が終わるまで carry

## PM 判断必要 top-5

次の 5 件は destructive で、PM または PO の明示判断なしに実施しない。

1. `.helix/` runtime を Git 管理から外す  
   関連: DEP-001, DEP-011, DEP-012
2. `skills/agent-skills` を vendor 扱いに寄せる再編  
   関連: DEP-015, DEP-020
3. `docs/plans/PLAN-NNN-*.md` の retention policy 変更  
   関連: DEP-026
4. 旧 hook (`.claude/hooks/`) の物理削除  
   関連: DEP-015, DEP-033
5. 廃止 capability の実装ファイル削除 timing  
   関連: DEP-002, DEP-017, DEP-018, DEP-029

## サマリ

- 全廃止項目件数: **33**
- Phase 1 即廃止件数: **10**
- PM 判断必要件数: **22**
- 「廃止しないと V2 移行が破綻」する critical 廃止 top-3:
  1. **DEP-015 hook 定義多重化**
     - hook の source-of-truth が 4 系統に分かれ、v2 ガードレールの正本が固定できない
  2. **DEP-026 PLAN doc 二重軸**
     - `docs/features/PLAN-*` と `docs/plans/PLAN-*` が共存し、plan 起源追跡が壊れる
  3. **DEP-020〜025 skill 分割・重複群**
     - role/skill dispatch が過密化し、G1R / reverse / FE 導線の discoverability を継続的に損なう

## ソース

- `docs/v2/A-audit/capability-inventory.md`
- `docs/v2/A-audit/legacy-plans-carry.md`
- `docs/v2/A-audit/capability-matrix.md`
- `docs/v2/A-audit/fe-weakness-analysis.md`
- `docs/v2/A-audit/accumulated-knowledge.md`
- `docs/v2/A-audit/db-schema-current.md`
- `docs/v2/A-audit/hooks-commands-subagents.md`
- `docs/v2/A-audit/off-plan-implementations.md`
- `docs/v2/A-audit/folder-structure-audit.md`
- `docs/v2/A-audit/docs-integrity-audit.md`
- `docs/v2/A-audit/test-coverage-audit.md`
- `docs/v2/A-audit/security-audit.md`
- `docs/v2/A-audit/cicd-audit.md`
- `docs/v2/A-audit/perf-cost-audit.md`
- `docs/v2/A-audit/cli-ux-audit.md`
- `docs/v2/A-audit/skill-quality-audit.md`
- `docs/v2/A-audit/memory-feedback-drift.md`
- `docs/v2/A-audit/reverse-scrum-audit.md`
