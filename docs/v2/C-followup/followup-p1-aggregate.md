# Phase 1 followup P1 aggregate

最終更新: 2026-05-14

## 概要

- 本書は Phase 1 完了時点での **P1 (即対応必須)** を 1 枚に集約した横断 view。
- 既存 followup doc のうち、今回の workspace で実在確認できたのは `pmo-startup-debug.md` のみ。TASK_INPUT に列挙された残りの followup plan doc と `docs/v2/v2-gate-overlay.md` は現時点では未配置だったため、**既存 audit doc と既存 followup から復元可能な P1 のみ**を集約した。
- したがって本書は「現在ある一次資料に基づく P1 集約」であり、未配置 followup doc が追加された場合は追補が必要。
- 方針としては、新規提案ではなく既存監査・既存補助 doc に書かれている P1 を **カテゴリ / 承認境界 / Phase 紐付け / critical path** の形で再配置した。

## ソース

- `docs/v2/A-audit/audit-summary.md`
- `docs/v2/A-audit/folder-structure-audit.md`
- `docs/v2/A-audit/docs-integrity-audit.md`
- `docs/v2/A-audit/security-audit.md`
- `docs/v2/A-audit/hooks-commands-subagents.md`
- `docs/v2/A-audit/deprecated-aggregation.md`
- `docs/v2/A-audit/skill-quality-audit.md`
- `docs/v2/A-audit/memory-feedback-drift.md`
- `docs/v2/A-audit/reverse-scrum-audit.md`
- `docs/v2/A-audit/test-coverage-audit.md`
- `docs/v2/A-audit/cicd-audit.md`
- `docs/v2/A-audit/off-plan-implementations.md`
- `docs/v2/A-audit/capability-matrix.md`
- `docs/v2/C-followup/pmo-startup-debug.md`

## 前提と不確実性

- `docs/v2/C-followup/` 配下の completed followup plan 群は、この workspace では未配置ファイルが多い。
- `v2-gate-overlay.md` は `docs-integrity-audit.md` 上では「必要な overlay 正本」として参照されるが、現物は未存在。
- `agent-skills-vendor-plan.md` など未存在ファイルに由来する P1 は、本書では直接引用せず、既存 audit に現れた同等論点だけを採用した。
- P1 の境界は各監査の `P1` / `即` / `最優先` / `critical` 記述を優先し、明示がないものは `Phase 1 blocker` または `critical path` の文脈から補助的に採用した。

## §1 全 followup P1 一覧

| ID | 出典 doc | カテゴリ | 内容 | 緊急度 | 承認 | Phase 紐付け |
|---|---|---|---|---|---|---|
| P1-001 | deprecated-aggregation | folder | `.helix/audit/codex-runs` など runtime 常駐物の Git 管理見直しを前提に、`.helix/tmp` を廃止対象として即整理する | 即 | 自動 | Phase 1 |
| P1-002 | deprecated-aggregation | folder | `.helix/cache/skill_classifier` を恒久 cache ではなく cleanup 対象へ寄せる | 即 | 自動 | Phase 1 |
| P1-003 | deprecated-aggregation | test | `__pycache__` 群と `.pytest_cache/` を追跡対象から外す | 即 | 自動 | Phase 1 |
| P1-004 | deprecated-aggregation | hook/command | `cli/helix-check-claudemd` deprecated wrapper を廃止対象として扱う | 即 | 自動 | Phase 1 |
| P1-005 | deprecated-aggregation | hook/command | `.git/hooks/pre-commit.helix.bak` を旧残骸として廃止対象に固定する | 即 | 自動 | Phase 1 |
| P1-006 | deprecated-aggregation | hook/command | `helix discover` legacy alias を廃止対象に固定する | 即 | 自動 | Phase 1 |
| P1-007 | deprecated-aggregation | hook/command | `helix learn` legacy alias を廃止対象に固定する | 即 | 自動 | Phase 1 |
| P1-008 | deprecated-aggregation | hook/command | `helix promote` legacy alias を廃止対象に固定する | 即 | 自動 | Phase 1 |
| P1-009 | deprecated-aggregation | doc | `CLAUDE.md` 固定 model 表を正本として扱う運用を廃止する | 即 | 自動 | Phase 1 |
| P1-010 | deprecated-aggregation | memory | stale archive memory 群 (`restructure-plan.md` など) の隔離または除去判断を先行する | 即 | PM | Phase 1 |
| P1-011 | docs-integrity-audit | doc | model 正本順位を `roles/*.conf` / `models.yaml` / `ROLE_MAP` で一元化する | 即 | PM | Phase 1 |
| P1-012 | docs-integrity-audit | doc | Research role の model drift を解消する | 高 | PM | Phase 1 |
| P1-013 | docs-integrity-audit | doc | QA role の model drift を解消する | 高 | PM | Phase 1 |
| P1-014 | docs-integrity-audit | doc | `CLAUDE.md` の簡略 model 表を参照中心へ縮退する | 高 | PM | Phase 1 |
| P1-015 | docs-integrity-audit | doc | PMO Sonnet を read-only 正本へ揃える | 高 | PM | Phase 1 |
| P1-016 | docs-integrity-audit | doc | PMO Haiku の `docs/**` / `skills/**` 許可範囲 drift を解消する | 高 | PM | Phase 1 |
| P1-017 | docs-integrity-audit | doc | `v2 gate overlay` 正本を追加し、既存正本から参照させる | 即 | PM | Phase 1 |
| P1-018 | docs-integrity-audit | hook/command | `helix gate G3 --subgate functional_freeze` など planned/current 境界を commands 正本で明示する | 高 | PM | Phase 1 |
| P1-019 | docs-integrity-audit | doc | `docs/agent-skills/README.md` の broken link 群を止血する | 即 | 自動 | Phase 1 |
| P1-020 | docs-integrity-audit | doc | `docs/agent-skills/README.md` の skill 数・配置 drift を upstream mirror 扱いへ落として是正する | 高 | PM | Phase 1 |
| P1-021 | docs-integrity-audit | doc | `L1-REQUIREMENTS.md` の監査成果物件数固定 (`4 audit doc`) を実態に合わせて修正する | 高 | PM | Phase 1 |
| P1-022 | security-audit | security | 中央 RBAC 不在を解消し、write 権限境界を env 例外頼みから脱却させる | 即 | PM | Phase 1 |
| P1-023 | security-audit | security | Bash guard の deny 結果を detector へ接続する | 即 | PM | Phase 1 |
| P1-024 | security-audit | security | `--allowed-files` を事後検知だけでなく事前統制へ寄せる | 即 | PM | Phase 1 |
| P1-025 | security-audit | security | secret scan をローカル pre-commit 依存から CI / server-side fail-close へ拡張する | 即 | PM | Phase 1 |
| P1-026 | security-audit | security | destructive git command を専用 detector として分類する | 即 | PM | Phase 1 |
| P1-027 | security-audit | security | hook disable / override を検知する detector を入れる | 即 | PM | Phase 1 |
| P1-028 | security-audit | security | `pip-audit` 相当の Python dependency audit を定常化する | 即 | PM | Phase 1 |
| P1-029 | security-audit | security | shell / prompt / tool injection を統合監査する | 即 | PM | Phase 1 |
| P1-030 | security-audit | security | AI 固有リスク detector 群を新設する | 即 | PM | Phase 1 |
| P1-031 | security-audit | security | sandbox 制御の bypass 試行を security event として集計する | 即 | PM | Phase 1 |
| P1-032 | pmo-startup-debug | pmo | `.claude/settings.local.json` に残る `/tmp/test-helix` stale 参照を除去する | 即 | 自動 | Phase 1 |
| P1-033 | pmo-startup-debug | pmo | plugin `SessionEnd` の `broker.json` cleanup を idempotent 化する | 高 | PM | Phase 1 |
| P1-034 | skill-quality-audit | skill | `SKILL_MAP.md` の 106 件表記と実体 104 件の不一致を解消する | 高 | PM | Phase 1 |
| P1-035 | skill-quality-audit | skill | `agent-skills/*` 23 件の frontmatter / triggers を HELIX 標準へ正規化する | 高 | PM | Phase 1 |
| P1-036 | skill-quality-audit | skill | `skill_usage=0` のため usage 計測未稼働を解消する | 高 | PM | Phase 1 |
| P1-037 | skill-quality-audit | skill | `project/ui` と `project/fe-*` の二重入口を統合方針に固定する | 高 | PM | Phase 1 |
| P1-038 | skill-quality-audit | skill | `workflow/research` と `tools/web-search` の分離を解消する | 高 | PM | Phase 1 |
| P1-039 | skill-quality-audit | skill | `workflow/incident` と `workflow/postmortem` の近接重複を整理する | 高 | PM | Phase 1 |
| P1-040 | skill-quality-audit | skill | `workflow/verification` など巨大 skill の分割方針を決める | 高 | PM | Phase 1 |
| P1-041 | memory-feedback-drift | memory | `MEMORY.md` 277 行肥大化を解消し、最新 index へ縮退する | 即 | PM | Phase 1 |
| P1-042 | memory-feedback-drift | memory | `MEMORY.md` の未掲載 4 件・死リンク 1 件を是正する | 高 | 自動 | Phase 1 |
| P1-043 | memory-feedback-drift | memory | top-level `type` 欠落 entry 2 件を補正または archive する | 高 | PM | Phase 1 |
| P1-044 | memory-feedback-drift | memory | plan registry の `draft/finalized/completed` と project memory の status drift を解消する | 即 | PM | Phase 1 |
| P1-045 | memory-feedback-drift | memory | stale memory (`project_next_wave.md` など) の archive / merge 判定を先に行う | 高 | PM | Phase 1 |
| P1-046 | memory-feedback-drift | memory | sample 認証値を含む memory を除外推奨ルールに寄せる | 高 | PM | Phase 1 |
| P1-047 | reverse-scrum-audit | reverse/scrum | `contract_entries.origin_mode` / `evidence_status` schema を追加する | 即 | PM | Phase 2 前 blocker |
| P1-048 | reverse-scrum-audit | reverse/scrum | Scrum confirmed → Forward contract bridge を実装する | 即 | PM | Phase 2 前 blocker |
| P1-049 | reverse-scrum-audit | reverse/scrum | Reverse R4 gap register と `functional_freeze` の条件連携を定義する | 即 | PM | Phase 2 前 blocker |
| P1-050 | reverse-scrum-audit | reverse/scrum | Reverse review artifact / Scrum handoff を DB 正規記録へ接続する | 高 | PM | Phase 2 |
| P1-051 | reverse-scrum-audit | reverse/scrum | design / normalization / fullback の fail-close 基準と実運用 evidence を整える | 高 | PM | Phase 2 |
| P1-052 | capability-matrix | capability matrix | PM 向け構造 debt view を追加し、PM × スパゲッティ防止の弱セルを埋める | 高 | PM | Phase 2 |
| P1-053 | capability-matrix | capability matrix | command 層の `edit -> sync -> detector -> gate` 一本化を進める | 即 | PM | Phase 2 |
| P1-054 | capability-matrix | capability matrix | Verify 層で FE / handover / docs drift まで含む契約検証へ拡張する | 即 | PM | Phase 2 |
| P1-055 | test-coverage-audit | test | uncovered top の `.claude/hooks/*` を shell contract test で埋める | 高 | 自動 | Phase 1 |
| P1-056 | test-coverage-audit | test | `cli/helix-plan-cmds/_shared.sh` の coverage gap を埋める | 高 | 自動 | Phase 1 |
| P1-057 | test-coverage-audit | test | manual shell check 2 本を CI 線に乗せるか廃止する | 高 | PM | Phase 1 |
| P1-058 | cicd-audit | hook/command | local `.git/hooks/pre-commit` を確実配備する installer / policy を整える | 即 | PM | Phase 1 |
| P1-059 | cicd-audit | hook/command | `helix sync` を統合入口として実装し、SessionStart / PostToolUse / Gate から共通呼び出しする | 即 | PM | Phase 2 前 blocker |
| P1-060 | cicd-audit | hook/command | GitHub Actions に nightly の detector / verify を載せる | 高 | PM | Phase 2 |
| P1-061 | cicd-audit | hook/command | advisory の drift-check を strict/loose policy 化する | 高 | PM | Phase 2 |
| P1-062 | off-plan-implementations | その他 | `helix-budget` を正式 PLAN または正本へ昇格する | 高 | PM | Phase 1 |
| P1-063 | off-plan-implementations | その他 | `helix-builder` を正式 PLAN または正本へ昇格する | 高 | PM | Phase 1 |
| P1-064 | off-plan-implementations | その他 | `helix-discover` を正式 PLAN または正本へ昇格する | 高 | PM | Phase 1 |
| P1-065 | off-plan-implementations | capability matrix | `helix-matrix` を正式 PLAN または正本へ昇格する | 高 | PM | Phase 1 |
| P1-066 | off-plan-implementations | その他 | `helix-team` を正式 PLAN または正本へ昇格する | 高 | PM | Phase 1 |
| P1-067 | off-plan-implementations | その他 | `helix plan reset` を archive proposal 依存から正本化する | 高 | PM | Phase 1 |
| P1-068 | audit-summary | doc | `model-policy` / `delegation-policy` / `v2 gate overlay` / `audit artifact set` を先に正本化する | 即 | PM | Phase 1 |

## §2 カテゴリ別集計

| カテゴリ | P1 件数 | 即実行可 | PM 承認必要 | PO 承認必要 |
|---|---:|---:|---:|---:|
| folder | 3 | 3 | 0 | 0 |
| doc | 15 | 2 | 13 | 0 |
| security | 10 | 0 | 10 | 0 |
| hook/command | 14 | 5 | 9 | 0 |
| skill | 7 | 0 | 7 | 0 |
| memory | 6 | 1 | 5 | 0 |
| reverse/scrum | 5 | 0 | 5 | 0 |
| capability matrix | 4 | 0 | 4 | 0 |
| pmo | 2 | 1 | 1 | 0 |
| test | 3 | 2 | 1 | 0 |
| その他 | 6 | 0 | 6 | 0 |
| **合計** | **68** | **14** | **54** | **0** |

補足:

- 本集約では P1 を `即` または `Phase 2 着手前 blocker` として広めに採用した。
- `PO 承認必要` は今回読めた一次資料では明示されなかった。多くは PM 判断または PM 承認境界として記載されている。

### §2.1 カテゴリ別補足

#### folder

- 量としては 3 件だが、repo 肥大の主因に直結するため影響は大きい。
- `folder-structure-audit.md` の主結論と整合し、個別 cleanup ではなく runtime policy とセットで扱う必要がある。

#### doc

- 件数が最も多い。
- 実態としては「文書修正」より `正本順位の固定` が主論点。
- `model-policy`, `delegation-policy`, `v2 gate overlay`, `audit artifact set` の 4 本柱に集約できる。

#### security

- 単独件数は 10 件で、いずれも detector / telemetry / fail-close への昇格が中心。
- 新規 guard を増やすより、既存 guard を「記録できる」「再評価できる」状態へ上げるのが主要テーマ。

#### hook/command

- alias 整理のような軽い論点と、`helix sync` のような構造論点が混在する。
- 即 cleanup と Phase 2 bridge を同じ波で処理しない方が安全。

#### skill

- ほとんどが metadata 補修と入口統合。
- vendor/upstream mirror と HELIX 正本の境界が曖昧なままでは、skill 数や trigger が継続的に drift する。

#### memory

- 技術的負債というより governance debt に近い。
- `index`, `schema`, `status source`, `archive rule` の 4 点を決めると一気に整理しやすい。

#### reverse/scrum

- V2 Phase 2 の blocker に最も近いカテゴリ。
- ここが未整備だと Reverse / Scrum 起源 artifact が V-model 強化線へ乗らない。

#### capability matrix

- 問題は capability 不在ではなく、層間接続不足。
- P1 は主に `PM view`, `command loop`, `verify contract coverage` の 3 点に集約される。

#### pmo

- 件数は少ないが、PMO 起動不能だと Sonnet/Haiku 補助経路が止まる。
- `/tmp/test-helix` stale 参照除去は小さな修正で効果が大きい。

#### test

- coverage 総量ではなく uncovered top の局所穴埋めが主題。
- hook と plan-cmds の shell contract test は、低コストで guardrail の信頼性を上げやすい。

#### その他

- ここでは off-plan capability の正本化をまとめた。
- いずれも現役 capability であり、削除より先に `誰の計画配下に置くか` を決める必要がある。

## §3 実行ロードマップ

### Wave 1.1 (即実行、自動承認)

- 件数: 14
- 主要項目:
  - `.claude/settings.local.json` の `/tmp/test-helix` stale 参照除去
  - `docs/agent-skills/README.md` broken link 止血
  - `__pycache__` / `.pytest_cache` / `.helix/tmp` / `skill_classifier` 整理
  - deprecated alias / deprecated wrapper / backup hook 残骸の縮退
  - `MEMORY.md` の死リンク、未掲載、cache 系の即修正
  - hook / plan-cmds uncovered の最小テスト追加

### Wave 1.2 (PM 承認後)

- 件数: 40
- 重点:
  - model 正本統一
  - PMO 権限・委譲 policy 正本化
  - security detector 群の設計凍結
  - skill catalog 再編方針
  - memory governance ルール化
  - off-plan capability の PLAN 昇格

### Wave 1.3 (PO 承認後)

- 件数: 0
- 補足:
  - 現在の一次資料では PO 明示承認境界は確認できなかった
  - ただし Phase 2 詳細設計で API/DB/契約破壊を伴う場合は別途 PO/HITL 境界が追加されうる

### Wave 1.4 (Phase 2 完了後)

- 件数: 14
- 主要項目:
  - `origin_mode` / `evidence_status` を含む Reverse/Scrum bridge
  - `helix sync` 実装と scheduler / nightly detector の統合
  - FE / handover / docs drift を含む contract verify 拡張
  - automation / telemetry / security detector の DB 正規接続

## §4 PM 判断必要 top-N

### PM 判断必要 top-10

| Rank | 項目 | 主出典 | 理由 |
|---|---|---|---|
| 1 | runtime (`.helix`) を Git 管理からどこまで外すか | audit-summary, folder-structure-audit | repo 肥大の主因であり、V2 の運用前提を左右する |
| 2 | model 正本を `roles/*.conf` 中心に寄せるか | docs-integrity-audit | role / model / thinking の drift が全方位に波及している |
| 3 | PMO Sonnet / Haiku / impl-sonnet の権限境界をどう固定するか | docs-integrity-audit, security-audit | 誤運用するとアクセス境界が崩れる |
| 4 | `v2 gate overlay` を既存正本へどう差し込むか | docs-integrity-audit | Phase 2 以降の gate 解釈が割れる |
| 5 | hook / command / agent / skill の source-of-truth 一本化 | audit-summary, hooks-commands-subagents, deprecated-aggregation | drift の最大発生源の一つ |
| 6 | `helix sync` を V2 自動化の中核 command に据えるか | cicd-audit, capability-matrix | command / detector / gate の閉ループを左右する |
| 7 | skill vendor 境界と `agent-skills` 正規化の扱い | skill-quality-audit, deprecated-aggregation | upstream mirror と HELIX 正本の境界が曖昧 |
| 8 | memory governance を index 縮退 + schema 強制へ寄せるか | memory-feedback-drift | stale / type 欠落 / status drift が大きい |
| 9 | off-plan capability 6 件を個別 PLAN 化するか既存 PLAN に統合するか | off-plan-implementations | orchestration 中核が plan 正本外に浮いている |
| 10 | Reverse/Scrum bridge を schema 拡張で吸収するか別 artifact として扱うか | reverse-scrum-audit | Phase 2 工程転換の設計境界を決める必要がある |

### audit-summary §6 + folder-structure-audit top-3 を踏まえた統合メモ

- `runtime Git 管理`、`skill vendor 境界`、`PLAN 正本の所在` は audit-summary 側の top 論点と整合する。
- folder 側では `runtime 常駐物`、`hook/command/agent/skill の多重化`、`PLAN doc 二重軸` が structural blocker。
- したがって PM 判断は個別 cleanup より **正本と保存場所の原則決め** を先行すべき。

## §5 Phase 2 着手 blockers

Phase 2 (V-model 強化定義 / 実装) に進む前に解消すべき P1:

1. `v2 gate overlay` 正本が未存在
2. model / PMO 権限 / delegation policy の正本順位が未固定
3. `origin_mode` / `evidence_status` を持つ Reverse/Scrum bridge 設計が未定
4. `helix sync` の planned/current 境界が未整理
5. hook / command / skill / agent の source-of-truth 多重化が残存
6. security detector 方針が「監査メモ」止まりで実装単位へ落ちていない
7. runtime / memory / stale artifacts の cleanup policy が決まっていない
8. off-plan capability の正本化方針が未確定

結論:

- Phase 2 の blocker は「未実装」より **正本未固定** が中心。
- したがって Phase 2 着手前の最優先は cleanup 単体ではなく、**policy と overlay の固定**。

## §6 critical path

「これを解消しないと V2 移行が破綻」する P1 top-5:

| Rank | P1 | 理由 |
|---|---|---|
| 1 | model / role / PMO 権限の正本一元化 (`P1-011`-`P1-018`, `P1-068`) | 誰がどの権限で何を実行できるかが曖昧なままだと、V2 の role-based orchestration が成立しない |
| 2 | `v2 gate overlay` 正本追加 (`P1-017`) | V2 の gate / phase / functional freeze が既存正本へ反映されず、設計と運用が二重化する |
| 3 | Reverse/Scrum bridge schema (`P1-047`-`P1-050`) | `origin_mode` / `evidence_status` がないと V-model 強化の工程転換が記録できず、FR-VS07 が閉じない |
| 4 | `helix sync` 統合入口 (`P1-059`) | command / hook / detector / gate の閉ループが未完成のままでは、自動化 Phase に進んでも drift を増やす |
| 5 | runtime / hook / command / skill の source-of-truth 多重化解消 (`P1-001`-`P1-009`, `P1-053`, `P1-058`) | cleanup を局所実施しても、正本が複数ある限り drift が再発し続ける |

### critical path 補足

- security detector 群 (`P1-022`-`P1-031`) は重要だが、正本と bridge が未固定だと設置先がぶれる。
- memory / stale docs は痛点だが、critical path としては「再発させない保存原則」の後段。
- off-plan capability は運用上重要だが、まず正本構造を決めてから PLAN 昇格する方が事故が少ない。

## 推奨

- Phase 1 の残タスクは、cleanup を個別に進めるより **正本化 batch** と **即 cleanup batch** に二分して処理するのが良い。
- 先に決めるべきは `model-policy`, `delegation-policy`, `v2 gate overlay`, `runtime cleanup policy`, `off-plan capability の正本化方針`。
- その後に自動承認で進められる stale file / alias / broken link / cache / minimal test を Wave 1.1 として一括処理するのが最短。

## 参照対応表

| 参照元 | 本書で主に反映した節 |
|---|---|
| `audit-summary.md` | §1, §4, §5, §6 |
| `folder-structure-audit.md` | §1 folder / hook / runtime 系、§4、§6 |
| `docs-integrity-audit.md` | §1 doc 系、§4、§5、§6 |
| `security-audit.md` | §1 security 系、§5、§6 |
| `hooks-commands-subagents.md` | §1 hook/command 系、§4、§6 |
| `deprecated-aggregation.md` | §1 の先頭 10 件、§3 Wave 1.1 |
| `skill-quality-audit.md` | §1 skill 系、§2.1 skill |
| `memory-feedback-drift.md` | §1 memory 系、§2.1 memory |
| `reverse-scrum-audit.md` | §1 reverse/scrum 系、§5、§6 |
| `test-coverage-audit.md` | §1 test 系、§2.1 test |
| `cicd-audit.md` | §1 hook/command / automation 系、§3、§6 |
| `off-plan-implementations.md` | §1 その他系、§4 |
| `capability-matrix.md` | §1 capability matrix 系、§6 |
| `pmo-startup-debug.md` | §1 pmo 系、§3 Wave 1.1 |

## 更新ガイド

- 未配置 followup plan doc が追加されたら、まず `§1` に出典 row を追加する。
- 新規 row を追加した場合は、必ず `§2` のカテゴリ集計を更新する。
- PM 判断が増えた場合は `§4` の top-N を見直す。
- Phase 2 blocker に関わる項目が増えた場合は `§5` と `§6` の順位を再評価する。
- 本書は横断 view のため、実装手順や細部設計は個別 followup plan 側に戻す。

## 追補が必要な未配置 followup doc

現時点で未配置を確認したため、本集約へ未反映の doc:

- `folder-cleanup-wave1.md`
- `docs-integrity-p1-plan.md`
- `security-p1-plan.md`
- `hooks-commands-sot-plan.md`
- `skill-cleanup-plan.md`
- `memory-cleanup-plan.md`
- `reverse-scrum-bridge-plan.md`
- `matrix-weak-cell-plan.md`
- `wave1-execution-plan.md`
- `v2-dogfood-plan.md`
- `pm-judgment-top5-detail.md`
- `v2-mapping.md`
- `agent-skills-vendor-plan.md`
- `docs/v2/v2-gate-overlay.md`

これらが追加された場合の想定差分:

- `§1` の ID 再番
- `§2` のカテゴリ集計更新
- `§4` PM top-N の根拠強化
- `§5` blocker 優先順位の微調整
