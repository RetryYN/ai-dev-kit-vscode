# Phase A Audit Summary

最終更新: 2026-05-14  
作成: Research (Codex)  
用途:

1. L1 §3.0 既存整理 (FR-INV01-06) の統合正本
2. Phase 2 V-model 強化定義 (FR-VD01-09) の入力正本
3. 次セッション onboarding doc

前提:

- 本書は `docs/v2/A-audit/` 配下の 20 audit doc のみを横断集約した summary である
- 新規主張や新規要件は追加していない
- 数値は各 audit doc の記載を優先し、矛盾や未確定は §7 に留保した

---

## §1 Phase A 完了サマリ

### 1.1 20 audit doc 一覧

| No. | audit doc | 行数 | 主要発見 1 行 |
|---|---|---:|---|
| 1 | `capability-inventory.md` | 66 | V1 capability は 14 件棚卸しでき、強い核は detector / Reverse / Scrum / harness / code-index。 |
| 2 | `legacy-plans-carry.md` | 145 | 旧 PLAN carry は P2=38, P3=24 相当で、特に PLAN-019〜027 の正本不連続が深い。 |
| 3 | `capability-matrix.md` | 81 | 5 層 × 3 問題の全セルに何かはあるが、ほぼ全域が「部分機能」で自動接続不足。 |
| 4 | `fe-weakness-analysis.md` | 189 | FE は contract / detector / command / semantic registry が未接続で、BE と同等の fail-close がない。 |
| 5 | `accumulated-knowledge.md` | 155 | V1 learnings は 35 件あり、役割分担・委譲・hook・V-model 強化の実務知が蓄積済み。 |
| 6 | `deprecated-aggregation.md` | 179 | 廃止候補は 33 件で、Phase 1 即廃止 10 件、Phase 2-5 廃止 18 件に整理できる。 |
| 7 | `db-schema-current.md` | 197 | `helix.db` は 48 table / 433 records だが、V-model 中核 table はほぼ空運用。 |
| 8 | `hooks-commands-subagents.md` | 314 | Hook/role/skill は機能しているが、slash/subagent は V2 で縮退対象。 |
| 9 | `off-plan-implementations.md` | 111 | PLAN 外 capability は 10 件あり、builder/matrix/team/budget などが正本から浮いている。 |
| 10 | `folder-structure-audit.md` | 1923 | repo は 5,315 files、runtime 3,859 files で、構造整理候補 36 件が最重要。 |
| 11 | `docs-integrity-audit.md` | 171 | Tier 1 正本群に 30 件の drift があり、特に model 正本・PMO 権限・V2 gate overlay が弱い。 |
| 12 | `security-audit.md` | 226 | fail-close の土台は強いが、security detector 化と横断 telemetry 接続が未完。 |
| 13 | `test-coverage-audit.md` | 314 | core5 coverage 86.4% は強い一方、overall 7.9% で hook/automation/plan-cmd の薄さが目立つ。 |
| 14 | `cicd-audit.md` | 219 | CI と hooks はあるが、`helix sync`・scheduler・auto-record は未接続で自動化は断片的。 |
| 15 | `perf-cost-audit.md` | 240 | 速度より observability gap が大きく、budget / cost telemetry / benchmark 永続化が不足。 |
| 16 | `dependencies-audit.md` | 205 | 依存リスクの中心は Python ではなく shell / Node / LLM CLI / GitHub への運用依存。 |
| 17 | `cli-ux-audit.md` | 288 | `helix` top-level 58 command は help 完備だが、命名・alias・error 品質が揺れている。 |
| 18 | `skill-quality-audit.md` | 193 | skill 実体は 104 件で、入口重複と巨大 skill 分割不足が discoverability を下げている。 |
| 19 | `memory-feedback-drift.md` | 203 | memory は 86 entries で index 肥大、type 欠落、stale/重複があり governance が必要。 |
| 20 | `reverse-scrum-audit.md` | 213 | Reverse 69%、Scrum 67% の完成度で、Forward/V-model bridge 強化が V2 の焦点。 |

### 1.2 合計件数集計

| 集計項目 | 件数 / 値 | 出典 |
|---|---:|---|
| capability 棚卸し件数 | 14 | `capability-inventory.md` |
| 廃止候補件数 | 33 | `deprecated-aggregation.md` |
| 旧 PLAN 棚卸し行数 | 69 | `legacy-plans-carry.md` |
| 旧 PLAN completed | 54 | `legacy-plans-carry.md` |
| 旧 PLAN draft | 15 | `legacy-plans-carry.md` |
| V2 変更計画 `new-plan` | 6 | `off-plan-implementations.md` |
| V2 変更計画 `merge` | 2 | `off-plan-implementations.md` |
| V2 変更計画 `deprecate` | 1 | `off-plan-implementations.md` |
| V2 変更計画 `keep` | 1 | `off-plan-implementations.md` |
| Folder 整理候補 total | 36 | `folder-structure-audit.md` |
| security リスク件数 | 36 | `security-audit.md` |
| docs drift 件数 | 30 | `docs-integrity-audit.md` |
| skill 実体件数 | 104 | `skill-quality-audit.md` |
| memory entry 件数 | 86 | `memory-feedback-drift.md` |

### 1.3 capability / 廃止 / 変更計画の読み替え

| 観点 | 監査から読めること | V2 への意味 |
|---|---|---|
| capability | 強い核は既にある。弱いのは「不存在」より「接続不足」。 | V2 は再実装より統合設計が主戦場。 |
| 廃止候補 | 即削除できる局所残骸と、PM 判断が要る source-of-truth 統合案件が混在。 | 波状廃止で進める必要がある。 |
| 変更計画 | 新規 PLAN 起票が必要な off-plan capability が残る。 | V2 では「正本外 capability を残さない」ことが前提になる。 |

### 1.4 Phase A の期間と担当

| 項目 | 内容 |
|---|---|
| 監査成果物の更新日 | 全 20 doc は 2026-05-14 更新で揃っている |
| 文書上で確認できる Phase A 期間 | 2026-05-13 〜 2026-05-14 |
| 担当 LLM | Codex research + PMO Sonnet |
| 補足 | 期間の開始日は `L1-REQUIREMENTS.md` の作成日と audit 更新日から読める範囲に限定した。より早い下調べ期間は audit 本文からは確定できない。 |

### 1.5 Phase A の結論を 1 ページで言うと

1. V1 は「資産がない」のではなく、資産が散在し正本と自動連携が弱い。
2. V2 の中心課題は、新機能追加よりも `semantic / schema / hook / gate / docs / command` の再接続である。
3. 最重要の技術的ボトルネックは `4 layer chain の空運用`、`automation 未接続`、`正本 drift`、`FE の非対称性`。
4. 最重要の PM 判断は `runtime を Git 管理から外すか`、`skill vendor 境界をどう切るか`、`PLAN 正本をどこに固定するか`。
5. Phase 2 以降は、Phase A で棚卸し済みの 20 audit を入力にすれば、V2 の主論点はほぼ網羅できる。

---

## §2 V2 設計ドライバ top-20

### DR-001

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-001 |
| **タイトル** | V-model 中核 table は schema だけ存在し、record writer が未接続 |
| **出典 audit** | `db-schema-current.md`, `test-coverage-audit.md`, `perf-cost-audit.md` |
| **問題** | `contract_entries`, `test_design_entries`, `design_review`, `test_baseline` は v20 に入っているが 0 record で、4 layer chain が空運用である。query は速いが、性能より前に「実データが流れない」状態が本質問題になっている。 |
| **解決方向** | V2 では schema 追加より writer 接続を優先し、contract→code→test_design→baseline の自動投入導線を先に通す。 |
| **Phase 紐付け** | Phase 2, Phase 3, Phase 5 |
| **FR 紐付け** | FR-VD01, FR-V01, FR-V04, FR-DB01, FR-DB06, FR-DB09, FR-A05, FR-A06 |

### DR-002

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-002 |
| **タイトル** | 既存 capability の弱点は「不存在」より「部分実装と接続不足」 |
| **出典 audit** | `capability-inventory.md`, `capability-matrix.md`, `hooks-commands-subagents.md` |
| **問題** | detector、Reverse、Scrum、handover、skill chain、harness など、核能力は既にある。しかし PM/Orch/Cmd/Skill/Verify の全層で「自動記録」「相互参照」「fail-close 接続」が弱く、運用力が capability の密度に追いついていない。 |
| **解決方向** | V2 は新規 subsystem の乱立ではなく、既存 capability を role / hook / DB / gate で再接続する統合設計を取る。 |
| **Phase 紐付け** | Phase 1〜5 |
| **FR 紐付け** | FR-INV01, FR-INV03, FR-VD03, FR-GR05, FR-A01, FR-A07 |

### DR-003

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-003 |
| **タイトル** | FE は V-model 上で BE と非対称で、専用 contract / detector / command が欠ける |
| **出典 audit** | `fe-weakness-analysis.md`, `capability-matrix.md`, `skill-quality-audit.md` |
| **問題** | FE には `state_events`, `component_props`, `visual_token`, `a11y_requirement`, `screen_transition` に相当する registry がなく、mock/promotion/visual/a11y/state drift を fail-close にする detector もない。結果として FE は skill と運用ノウハウ依存で、DB/gate の中心線から外れている。 |
| **解決方向** | FE を例外扱いせず、BE と同じく contract registry・semantic registry・detector・command namespace を用意して V-model へ一般化する。 |
| **Phase 紐付け** | Phase 2, 派生 FE |
| **FR 紐付け** | FR-VD02, FR-VD03, FR-VD04, FR-FE01, FR-FE02, FR-FE03, FR-FE04, FR-FE05, FR-FE06 |

### DR-004

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-004 |
| **タイトル** | 正本 doc 群の drift が高く、V2 要件が既存正本に overlay されていない |
| **出典 audit** | `docs-integrity-audit.md`, `folder-structure-audit.md`, `accumulated-knowledge.md` |
| **問題** | Tier 1 正本に 30 件の drift があり、特に model 正本順位、PMO 権限、phase/gate/drive overlay、planned/current command の境界が曖昧である。V2 future state を L1 が先行定義している一方、既存運用正本は古いままで、設計と運用の二重正本化が始まっている。 |
| **解決方向** | V2 では `model-policy`, `delegation-policy`, `v2 gate overlay`, `audit artifact set` を先に正本化し、L1/L2/L3 と runtime policy の橋を作る。 |
| **Phase 紐付け** | Phase 1, Phase 2 |
| **FR 紐付け** | FR-INV05, FR-INV06, FR-VD02, FR-VD09, FR-VS01 |

### DR-005

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-005 |
| **タイトル** | PLAN 正本が `docs/plans`, `docs/features`, `.helix/plans` に分散している |
| **出典 audit** | `legacy-plans-carry.md`, `folder-structure-audit.md`, `docs-integrity-audit.md` |
| **問題** | PLAN-019〜027 の canonical source が不連続で、`docs/plans/`, `.helix/plans/`, feature appendix のどれが正本か揺れている。carry 追跡や completion 判定の再現性が落ち、Phase A の監査ですら trace-only 行補完が必要だった。 |
| **解決方向** | V2 では PLAN retention と source-of-truth を固定し、carry / history / appendix を別軸に整理する。 |
| **Phase 紐付け** | Phase 1, 派生 Legacy Import |
| **FR 紐付け** | FR-INV02, FR-LI01, FR-LI02, FR-LI03 |

### DR-006

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-006 |
| **タイトル** | runtime (`.helix`) が repo file 数の大半を占め、構造汚染の中心にある |
| **出典 audit** | `folder-structure-audit.md`, `deprecated-aggregation.md`, `memory-feedback-drift.md` |
| **問題** | repo 全体 5,315 files のうち runtime が 3,859 files を占める。`.helix/tmp`, cache, generated artifacts, test runtime が Git 管理下に残り、正本と一時物の境界を壊している。 |
| **解決方向** | runtime を Git 管理から外すか、TTL / cleanup / keep policy を導入して常駐物を縮退する。 |
| **Phase 紐付け** | Phase 1, Phase 5 |
| **FR 紐付け** | FR-INV06, FR-A01, FR-A02, FR-A08, FR-EM04 |

### DR-007

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-007 |
| **タイトル** | hook / command / agent / skill の source-of-truth が多重化している |
| **出典 audit** | `hooks-commands-subagents.md`, `folder-structure-audit.md`, `deprecated-aggregation.md` |
| **問題** | `.claude/hooks`, `cli/templates/hooks`, `skills/agent-skills/hooks`, `scripts/git-hooks`、さらに `.claude/commands` と `docs/commands`、`.claude/agents` と template 群が並存し drift 余地が大きい。 |
| **解決方向** | V2 では Hook/Role/Skill を正本化し、slash/subagent は縮退運用または generated copy に寄せる。 |
| **Phase 紐付け** | Phase 1, Phase 4, Phase 5 |
| **FR 紐付け** | FR-INV06, FR-AT01, FR-AT02, FR-A07, FR-GR05 |

### DR-008

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-008 |
| **タイトル** | security は fail-close の点はあるが detector / telemetry と閉ループ化していない |
| **出典 audit** | `security-audit.md`, `cicd-audit.md`, `capability-inventory.md` |
| **問題** | raw CLI block、Opus repo edit block、allowed-files 監査、secret scan などは既に強い。しかし deny 理由や bypass 試行が detector verdict・DB record・gate report に一貫して残らず、再発学習と stop ループが弱い。 |
| **解決方向** | 既存 guard を `prompt-injection`, `destructive-op`, `secret-handling`, `hook-bypass`, `access-boundary`, `research-egress` などの detector に昇格する。 |
| **Phase 紐付け** | Phase 4, Phase 5 |
| **FR 紐付け** | FR-GR01, FR-GR02, FR-GR03, FR-GR04, FR-GR06, FR-GR07, FR-A03, FR-A04 |

### DR-009

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-009 |
| **タイトル** | CI/CD は存在するが、自動化は `sync` 不在で断片的 |
| **出典 audit** | `cicd-audit.md`, `db-schema-current.md`, `perf-cost-audit.md` |
| **問題** | SessionStart / PostToolUse / Stop / pre-commit / GitHub Actions / scheduler の各部品はあるが、`helix sync` 統合入口が未実装で、plan/skill/code/detector の auto-sync が構成概念に留まっている。 |
| **解決方向** | `helix sync --auto` を共通入口として、SessionStart・PostToolUse・Gate・scheduler から呼ぶ一本化を行う。 |
| **Phase 紐付け** | Phase 5 |
| **FR 紐付け** | FR-A01, FR-A02, FR-A03, FR-A04, FR-A05, FR-A07, FR-A08 |

### DR-010

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-010 |
| **タイトル** | observability gap により性能 NFR と cost NFR が測定不能または不完全 |
| **出典 audit** | `perf-cost-audit.md`, `db-schema-current.md`, `cicd-audit.md` |
| **問題** | `bench_snapshots=0`, `budget_events=0`, `cost_log.tokens_est=0`, `cost_log.cost_est=0.0`, `Codex source=unavailable` であり、NFR-20〜22 を role 別・週次・イベント別に議論できる telemetry が不足している。 |
| **解決方向** | benchmark 永続化、budget event 永続化、role cost 記録、provider 集計との整合を優先し、速度最適化より先に観測面を成立させる。 |
| **Phase 紐付け** | Phase 5, 可視化 |
| **FR 紐付け** | FR-A05, FR-EM01, FR-EM03, FR-EM04, FR-EM05, FR-EM06 |

### DR-011

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-011 |
| **タイトル** | test の量は十分だが、hook / automation / plan-cmd / V-model chain の coverage が薄い |
| **出典 audit** | `test-coverage-audit.md`, `cicd-audit.md`, `perf-cost-audit.md` |
| **問題** | core5 coverage 86.4% は強い一方、overall 7.9% で uncovered top は hook と `cli/helix-plan-cmds/_shared.sh` に偏る。V-model schema と auto-record を担保する e2e test も不足する。 |
| **解決方向** | Phase 4 入力として `uncovered top-10`、`pair-check`、`drive semantic`、`contract auto-record`、`detector auto-run` の scenario test を増やす。 |
| **Phase 紐付け** | Phase 4, Phase 5 |
| **FR 紐付け** | FR-V05, FR-GR02, FR-A03, FR-A05, FR-VS04, FR-VS05 |

### DR-012

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-012 |
| **タイトル** | CLI は 58 command と十分広いが、命名・alias・公開境界が整理不足 |
| **出典 audit** | `cli-ux-audit.md`, `deprecated-aggregation.md`, `hooks-commands-subagents.md` |
| **問題** | `discover/learn/promote` の legacy alias、`session-summary` の名前ずれ、`gate-api-check` などの prefix 混乱、router 非公開 script の存在により discoverability が落ちている。 |
| **解決方向** | V2 Phase 1 で naming policy・alias policy・error copy 最低基準・public/private command 境界を固定する。 |
| **Phase 紐付け** | Phase 1, Phase 5 |
| **FR 紐付け** | FR-INV06, FR-A07, FR-EM03, FR-AT02 |

### DR-013

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-013 |
| **タイトル** | skill catalog は量より入口重複が問題で、usage telemetry も空 |
| **出典 audit** | `skill-quality-audit.md`, `hooks-commands-subagents.md`, `deprecated-aggregation.md` |
| **問題** | skill 実体は 104 件あるが `skill_usage` は 0 行で、入口重複 (`project/ui` と `project/fe-*`, `workflow/research` と `tools/web-search`) と巨大 skill の肥大で探索性が悪い。 |
| **解決方向** | usage telemetry をまず実運用化し、その上で UI・research・incident/postmortem・agent-skills vendor 境界を再編する。 |
| **Phase 紐付け** | Phase 1, Phase 5 |
| **FR 紐付け** | FR-INV05, FR-A02, FR-A07, FR-AT01, FR-AT02 |

### DR-014

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-014 |
| **タイトル** | Reverse / Scrum は廃止対象ではなく、V-model bridge が不足している |
| **出典 audit** | `reverse-scrum-audit.md`, `capability-inventory.md`, `db-schema-current.md` |
| **問題** | Reverse は 69%、Scrum は 67% の完成度で CLI・test・運用骨格はある。欠けているのは `origin_mode`, `evidence_status`, `confirmed -> Forward contract`, `functional_freeze` 連携である。 |
| **解決方向** | Reverse / Scrum を新設し直さず、schema と gate に bridge を追加し V-model の中心線へ接続する。 |
| **Phase 紐付け** | Phase 2, Phase 3, 工程転換 |
| **FR 紐付け** | FR-VD06, FR-DB06, FR-DB07, FR-DB08, FR-VS01, FR-VS02, FR-VS03, FR-VS04, FR-VS05, FR-VS06, FR-VS07 |

### DR-015

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-015 |
| **タイトル** | off-plan capability が正本 governance を壊す温床になっている |
| **出典 audit** | `off-plan-implementations.md`, `legacy-plans-carry.md`, `docs-integrity-audit.md` |
| **問題** | `helix-budget`, `helix-builder`, `helix-matrix`, `helix-team`, `helix plan reset` などが実体として重要なのに、PLAN 起源や V2 吸収先が固定されていない。 |
| **解決方向** | V2 では off-plan capability を禁止し、keep/merge/new-plan/deprecate を必ず PLAN と紐付ける。 |
| **Phase 紐付け** | Phase 1, Phase 5 |
| **FR 紐付け** | FR-INV02, FR-INV05, FR-INV06, FR-AT03, FR-AT04, FR-AT05 |

### DR-016

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-016 |
| **タイトル** | memory は知識資産だが、現状は governance 不足で drift source にもなる |
| **出典 audit** | `memory-feedback-drift.md`, `accumulated-knowledge.md`, `docs-integrity-audit.md` |
| **問題** | memory は 86 entries あり学習資産として有用だが、`MEMORY.md` 肥大、type 欠落、stale/重複、canonical status source 不在により、ルール昇格済み知識と雑多メモが混在している。 |
| **解決方向** | feedback / project / reference の用途固定、index 縮退、schema 必須化、canonical status source 導入で governance する。 |
| **Phase 紐付け** | Phase 1, 可視化 |
| **FR 紐付け** | FR-INV05, FR-EM01, FR-EM03, FR-EM06 |

### DR-017

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-017 |
| **タイトル** | dependency の実リスクは language package より CLI/toolchain drift |
| **出典 audit** | `dependencies-audit.md`, `security-audit.md`, `cicd-audit.md` |
| **問題** | Python 依存は少ない一方、`bash`, `git`, `node`, `npm`, `npx`, `@openai/codex`, `@anthropic-ai/claude-code`, GitHub 等の unpinned 前提が強く、環境差で再現性が壊れやすい。 |
| **解決方向** | 必須/optional の境界、pin policy、audit 実行導線、Node lockfile 方針を設計で先に決める。 |
| **Phase 紐付け** | Phase 1, Phase 4, Phase 5 |
| **FR 紐付け** | FR-GR01, FR-GR07, FR-A04, FR-A08 |

### DR-018

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-018 |
| **タイトル** | detector は強い核だが、blocked/failed/rc=1 の意味論と baseline 接続が未成熟 |
| **出典 audit** | `capability-inventory.md`, `test-coverage-audit.md`, `perf-cost-audit.md`, `security-audit.md` |
| **問題** | 14 detector system 自体は強いが、`axis-03` 例外、`axis-10` path resolve error、baseline 未接続、blocked の意味不統一があり、Phase 4 guardrail の基盤としては安定化が必要である。 |
| **解決方向** | detector の成功条件・blocked 意味論・writer 接続・security/FE axis 拡張を V2 の検出ガードレール本体として再定義する。 |
| **Phase 紐付け** | Phase 4 |
| **FR 紐付け** | FR-GR01, FR-GR02, FR-GR03, FR-GR04, FR-GR06, FR-GR07, FR-FE02 |

### DR-019

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-019 |
| **タイトル** | QA strictness の思想はあるが、pairing を sprint/gate へ制度的に落とし切れていない |
| **出典 audit** | `accumulated-knowledge.md`, `db-schema-current.md`, `reverse-scrum-audit.md`, `test-coverage-audit.md` |
| **問題** | architecture↔system_integration、detailed↔integration、functional↔unit のペアリング思想はあるが、現状は schema 空運用と review記録不足により、工程 discipline と DB evidence が離れている。 |
| **解決方向** | design sprint table、pair status、subgate `functional_freeze`、design review writer を合わせて sprint 単位の pair freeze を実装する。 |
| **Phase 紐付け** | Phase 2, Phase 3, 工程転換 |
| **FR 紐付け** | FR-VD01, FR-VD05, FR-VD07, FR-DB07, FR-DB08, FR-VS01, FR-VS02, FR-VS04, FR-VS05 |

### DR-020

| 項目 | 内容 |
|---|---|
| **DR-ID** | DR-020 |
| **タイトル** | Phase A 監査自体が V2 の可視化・正本化の必要性を証明している |
| **出典 audit** | 全 20 audit doc |
| **問題** | 今回の 20 audit はそれぞれ正しいが、単体では新規参画者が全体像を掴みにくい。つまり V1 の情報構造は「詳細 doc はあるが cross-cut 統合面がない」ことを監査自身が示している。 |
| **解決方向** | V2 では dashboard / relation graph / dev-state report / audit summary のような cross-cut 可視化を第一級成果物として持つ。 |
| **Phase 紐付け** | Phase 1, 可視化 |
| **FR 紐付け** | FR-INV05, FR-EM01, FR-EM02, FR-EM03, FR-EM04, FR-EM05, FR-EM06 |

### 2.1 Top-20 の読み取り方

| 観点 | 読み方 |
|---|---|
| 構造系ドライバ | DR-001, 004, 005, 006, 007, 015 が source-of-truth と構造整理を規定する |
| 技術中核ドライバ | DR-001, 003, 008, 009, 010, 011, 014, 018, 019 が V2 の実装核を規定する |
| 運用/可視化ドライバ | DR-012, 013, 016, 017, 020 が人間と agent の運用負荷を下げる |
| 最優先順位 | DR-001, 004, 005, 008, 009, 014, 019 が依存の上流にある |

---

## §3 5 層 × 3 問題 マトリクス (現状 → V2 後)

注記:

- `capability-matrix.md` は要件文の「9 セル」と異なり、実際には `5 層 × 3 問題 = 15 セル` で整理している
- 本書も audit 本文に合わせて 15 セルで再現する
- 健全度スコアは `capability-matrix.md` の状態分類と他 audit の cross-cut 所見から 0-10 で再評価した summary 値である

| 層 | 問題 | 現状 capability | V2 後追加 capability | 健全度 |
|---|---|---|---|---:|
| PM | バグ防止 | gate 運用、advisor、handover blocker | bug density / flaky / detector verdict の PM 向け summary | 4 |
| PM | スパゲッティ防止 | role 分担、PLAN/WBS discipline | structure debt の PM 意思決定レポート | 4 |
| PM | 契約漏れ防止 | D-API/D-DB/D-CONTRACT 変更時の HITL | PM 向け contract drift report、PLAN 正本固定 | 4 |
| Orchestration | バグ防止 | consent/approved/allowed-files、role routing | role failure pattern 学習、routing 最適化、budget-aware reroute | 5 |
| Orchestration | スパゲッティ防止 | task injection、allowed-files で範囲制限 | structure debt と delegation quality の feedback loop | 4 |
| Orchestration | 契約漏れ防止 | plan_id/reference-doc 注入 | contract impact を routing 判断へ戻す layer | 5 |
| Command | バグ防止 | `helix gate`, `helix test`, `helix review` | planned/current command 整理、error quality 最低基準 | 6 |
| Command | スパゲッティ防止 | code find/stats、doctor、review | naming policy、alias policy、public/private 境界 | 5 |
| Command | 契約漏れ防止 | `drift-check`, `gate-api-check`, verify 群 | `helix sync`, FE command namespace, V-model score command | 5 |
| Skill | バグ防止 | coding/testing/code-review/verification skill | usage telemetry と入口統合 | 5 |
| Skill | スパゲッティ防止 | design-doc/refactoring/research skill | UI / research / incident の重複統合 | 4 |
| Skill | 契約漏れ防止 | api/api-contract/db/reverse-analysis skill | FE contract workflow と transition-design skill | 4 |
| Verify | バグ防止 | 14 detector、pytest/Bats/verify、CI | security/FE/research-egress detector、pair-check e2e | 6 |
| Verify | スパゲッティ防止 | code stats, relation graph, refactor detector | structure debt detector の PM 可視化と false positive 制御 | 5 |
| Verify | 契約漏れ防止 | contract registry、pair-check、doc drift detector | origin_mode/evidence_status、full chain writer、functional_freeze | 5 |

### 3.1 平均健全度

| 集計 | 値 |
|---|---:|
| 15 セル合計 | 72 |
| 平均健全度 | 4.8 / 10 |

### 3.2 最弱セル

1. PM × 契約漏れ防止  
   ルールはあるが、PM が一目で contract drift を把握する capability がない。
2. Skill × 契約漏れ防止  
   skill はあるが FE/Reverse/Scrum を DB/gate の中心線に接続する標準がない。
3. Orchestration × スパゲッティ防止  
   role routing はあるが、構造 debt を routing へフィードバックする仕組みがない。

### 3.3 V2 後の目標値

| 目標 | 内容 |
|---|---|
| 目標平均 | 7.0 以上 |
| 最低セル | 5 未満を残さない |
| 高優先セル | PM×契約漏れ、Skill×契約漏れ、Orchestration×スパゲッティ、Verify×契約漏れ |

---

## §4 廃止 roadmap (Phase 1〜V3)

### 4.1 Wave 1 (Phase 1 即廃止)

| 指標 | 値 |
|---|---:|
| 件数 | 10 |
| 性質 | wrapper / cache / stale doc / deprecated alias / local residue |

| top | 項目 | 出典 | コメント |
|---|---|---|---|
| 1 | `cli/helix-check-claudemd` wrapper | `deprecated-aggregation.md` | 旧 wrapper を正本 capability とみなさない |
| 2 | `.git/hooks/pre-commit.helix.bak` | `deprecated-aggregation.md` | 実機能なしの予約残骸 |
| 3 | `helix discover` alias | `deprecated-aggregation.md`, `cli-ux-audit.md` | `recipe discover` に統合 |
| 4 | `helix learn` alias | `deprecated-aggregation.md`, `cli-ux-audit.md` | `recipe learn` に統合 |
| 5 | `helix promote` alias | `deprecated-aggregation.md`, `cli-ux-audit.md` | `recipe promote` に統合 |
| 6 | `CLAUDE.md` の固定 model 表 | `deprecated-aggregation.md`, `docs-integrity-audit.md` | `ROLE_MAP/models.yaml/roles.conf` 参照へ縮退 |
| 7 | `.helix/tmp` | `deprecated-aggregation.md`, `folder-structure-audit.md` | runtime 汚染の代表 |
| 8 | `.helix/cache/skill_classifier` | `deprecated-aggregation.md`, `folder-structure-audit.md` | TTL / cleanup 管理へ移送 |
| 9 | `__pycache__` + `.pytest_cache/` | `deprecated-aggregation.md`, `folder-structure-audit.md` | 生成 cache を Git 正本から外す |
| 10 | stale archive memory 群 | `deprecated-aggregation.md`, `memory-feedback-drift.md` | memory governance 整理の入口 |

### 4.2 Wave 2 (Phase 2-5)

| 指標 | 値 |
|---|---:|
| 件数 | 18 |
| 性質 | source-of-truth 統合、layout 統合、command/skill/subagent の整理 |

| top | 項目 | 出典 | コメント |
|---|---|---|---|
| 1 | SessionStart wrapper | `deprecated-aggregation.md`, `cicd-audit.md` | 実体と wrapper の二重管理解消 |
| 2 | test layout 分散 | `deprecated-aggregation.md`, `folder-structure-audit.md` | `cli/tests`, `cli/lib/tests`, `tests`, `verify` を再編 |
| 3 | hook source-of-truth 多重化 | `deprecated-aggregation.md`, `folder-structure-audit.md` | 最重要の critical 廃止候補 |
| 4 | command docs 二重正本 | `deprecated-aggregation.md`, `folder-structure-audit.md` | `.claude/commands` と `docs/commands` の統合 |
| 5 | `/ship` slash command | `deprecated-aggregation.md`, `hooks-commands-subagents.md` | v2 方針と衝突 |
| 6 | native subagent 4件 | `deprecated-aggregation.md`, `hooks-commands-subagents.md` | role-based flow へ吸収 |
| 7 | agent template 二重管理 | `deprecated-aggregation.md`, `folder-structure-audit.md` | `.claude/agents` と template の統合 |
| 8 | skill `references` 過細分化 | `deprecated-aggregation.md`, `folder-structure-audit.md` | 導線コストが高い |
| 9 | `project/fe-*` 5分割 + `project/ui` | `deprecated-aggregation.md`, `skill-quality-audit.md` | UI 入口統合 |
| 10 | reverse 6分割 skill | `deprecated-aggregation.md`, `folder-structure-audit.md` | reverse-analysis 中心へ整理 |

### 4.3 Wave 3 (V2 完了後)

| 指標 | 値 |
|---|---:|
| 件数 | 3 |
| 性質 | 実運用観測が必要な runtime / generated / DB 残骸 |

| 項目 | コメント |
|---|---|
| session summary md/shim | telemetry / log report へ責務移送できるか観測後に停止 |
| `debt_items` table | YAML 正本で十分かを V2 運用後に確定 |
| `public/generated/codex` | build artifact 化の安全性確認後に整理 |

### 4.4 Wave 4 (V3 / 永久 carry)

| 指標 | 値 |
|---|---:|
| 件数 | 2 |
| 性質 | upstream/vendor または concept 統合待ち |

| 項目 | コメント |
|---|---|
| `docs/agent-skills/README.md` を HELIX 正本として扱う運用 | upstream/vendor mirror として残し、HELIX 正本からだけ退役させる可能性が高い |
| stale merge memory 群 | memory schema と concept 正本が決まるまで carry が妥当 |

### 4.5 PM 判断必要 top-5 (destructive 廃止)

| No. | 論点 | 主な関連項目 | 判断理由 |
|---|---|---|---|
| 1 | `.helix/` runtime を Git 管理から外すか | DEP-001, 011, 012 | 再現性・監査履歴・repo 汚染のトレードオフが大きい |
| 2 | `skills/agent-skills` を vendor 扱いへ寄せるか | DEP-015, 020 | core skill と upstream mirror の境界設計が要る |
| 3 | PLAN 正本固定先をどこにするか | DEP-026, `legacy-plans-carry.md` | carry 追跡・appendix・history の設計が変わる |
| 4 | 旧 hook (`.claude/hooks/`) の物理削除 timing | DEP-015, 033 | fail-close を壊すと事故になる |
| 5 | 廃止 capability の実装ファイル削除 timing | DEP-002, 017, 018, 029 | rename/deprecate期間を置くか一括削除かで運用負荷が変わる |

### 4.6 廃止 roadmap の解釈

1. Wave 1 は「局所・戻しやすい・正本を増やさない」ものだけに限定する。
2. Wave 2 は source-of-truth 統合そのものであり、設計と実装を同時に進める必要がある。
3. Wave 3 は V2 dogfood 後にしか決められないため、Phase 1 で消さない。
4. Wave 4 は「削除しない」より「HELIX 正本から外す」判断が中心になる。

---

## §5 V2 Phase 1〜5 への入力マッピング

注記:

- 本節は 74 FR-ID 全件を最低 1 つ以上の audit 出典へ紐付ける
- 既存 audit に書かれていない根拠は追加していない
- 1 FR を複数 audit に紐付けるのは、cross-cut 入力として妥当なものに限定した

### 5.1 Phase / 派生ごとの正本入力

| Phase | 正本入力 (audit doc 出典) | 主要要件 (FR) |
|---|---|---|
| Phase 1 既存整理 | `audit-summary.md`, `capability-inventory.md`, `legacy-plans-carry.md`, `deprecated-aggregation.md`, `folder-structure-audit.md`, `docs-integrity-audit.md`, `off-plan-implementations.md`, `cli-ux-audit.md`, `skill-quality-audit.md`, `memory-feedback-drift.md` | INV01-06 |
| Phase 2 V-model 強化 | `db-schema-current.md`, `capability-matrix.md`, `fe-weakness-analysis.md`, `reverse-scrum-audit.md`, `accumulated-knowledge.md`, `test-coverage-audit.md` | VD01-09, V01-07, VS01-07 |
| Phase 3 helix.db | `db-schema-current.md`, `off-plan-implementations.md`, `reverse-scrum-audit.md`, `perf-cost-audit.md` | DB01-10 |
| Phase 4 検出ガードレール | `security-audit.md`, `test-coverage-audit.md`, `hooks-commands-subagents.md`, `capability-matrix.md`, `perf-cost-audit.md`, `dependencies-audit.md` | GR01-07 |
| Phase 5 自動化 | `cicd-audit.md`, `hooks-commands-subagents.md`, `perf-cost-audit.md`, `db-schema-current.md`, `off-plan-implementations.md` | A01-08 |
| 可視化 | `folder-structure-audit.md`, `capability-matrix.md`, `perf-cost-audit.md`, `memory-feedback-drift.md` | EM01-06 |
| 派生 FE | `fe-weakness-analysis.md`, `skill-quality-audit.md`, `cli-ux-audit.md` | FE01-06 |
| 派生 AT | `hooks-commands-subagents.md`, `skill-quality-audit.md`, `off-plan-implementations.md`, `dependencies-audit.md` | AT01-05 |
| 派生 Legacy Import | `legacy-plans-carry.md`, `off-plan-implementations.md`, `folder-structure-audit.md` | LI01-03 |
| 工程転換 | `reverse-scrum-audit.md`, `test-coverage-audit.md`, `db-schema-current.md`, `accumulated-knowledge.md` | VS01-07 |

### 5.2 FR-INV01〜06

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-INV01 | `capability-inventory.md`, `hooks-commands-subagents.md` | capability 14件と role/hook/skill 実体の棚卸しが完了している |
| FR-INV02 | `legacy-plans-carry.md`, `off-plan-implementations.md` | PLAN-001〜068 carry と正本外 capability の流入源が確認できる |
| FR-INV03 | `capability-matrix.md`, `fe-weakness-analysis.md` | 5層×3問題の現状と FE 非対称性が見える |
| FR-INV04 | `fe-weakness-analysis.md`, `skill-quality-audit.md` | FE contract/detector/command/semantic の不足が明示済み |
| FR-INV05 | `accumulated-knowledge.md`, `memory-feedback-drift.md`, `docs-integrity-audit.md` | learnings と drift source が整理済み |
| FR-INV06 | `deprecated-aggregation.md`, `folder-structure-audit.md`, `cli-ux-audit.md` | 廃止候補 33件と rename/deprecate 群が明示済み |

### 5.3 FR-VD01〜09

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-VD01 | `db-schema-current.md`, `accumulated-knowledge.md`, `reverse-scrum-audit.md` | pairing 思想と schema gap が揃う |
| FR-VD02 | `capability-matrix.md`, `fe-weakness-analysis.md`, `reverse-scrum-audit.md` | BE/FE/DB/Fullstack と scrum/reverse の接続境界が見える |
| FR-VD03 | `fe-weakness-analysis.md`, `hooks-commands-subagents.md`, `cli-ux-audit.md` | artifacts/review/detector/command の必須項目候補が読める |
| FR-VD04 | `fe-weakness-analysis.md`, `accumulated-knowledge.md` | mock promotion lifecycle を fail-close 化すべき根拠がある |
| FR-VD05 | `test-coverage-audit.md`, `accumulated-knowledge.md` | pairing とテスト層接続の重点不足が明示されている |
| FR-VD06 | `reverse-scrum-audit.md`, `db-schema-current.md` | `origin_mode`, `evidence_status` が未実装で必要性が高い |
| FR-VD07 | `accumulated-knowledge.md`, `test-coverage-audit.md`, `perf-cost-audit.md` | gate/coverage/benchmark を pair evidence に接続する必要がある |
| FR-VD08 | `docs-integrity-audit.md`, `hooks-commands-subagents.md` | role/gate/command の overlay と review-axis の正本化が必要 |
| FR-VD09 | `docs-integrity-audit.md`, `folder-structure-audit.md`, `deprecated-aggregation.md` | source-of-truth と配置整理が semantic 正本化の前提になる |

### 5.4 FR-V01〜07

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-V01 | `db-schema-current.md`, `test-coverage-audit.md` | 4 layer chain が空運用で writer 不足 |
| FR-V02 | `test-coverage-audit.md`, `perf-cost-audit.md` | baseline / flaky / verify の接続不足と性能観測不足 |
| FR-V03 | `capability-matrix.md`, `security-audit.md` | vertical/horizontal review と fail-close 接続を強化すべき |
| FR-V04 | `reverse-scrum-audit.md`, `db-schema-current.md` | Reverse/Scrum 起源 artifact の DB 接続が必要 |
| FR-V05 | `test-coverage-audit.md`, `cicd-audit.md` | pair-check と detector auto-run の e2e test が不足 |
| FR-V06 | `fe-weakness-analysis.md`, `cli-ux-audit.md` | FE command / detector / contract namespace 不在 |
| FR-V07 | `perf-cost-audit.md`, `db-schema-current.md` | V-model score / dashboard を成り立たせる telemetry gap がある |

### 5.5 FR-DB01〜10

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-DB01 | `db-schema-current.md` | v20→v21 additive migration の主論点が整理済み |
| FR-DB02 | `db-schema-current.md`, `folder-structure-audit.md` | `er_diagrams` の新規 table 必要性が出ている |
| FR-DB03 | `db-schema-current.md`, `reverse-scrum-audit.md` | `process_maps` と工程可視化の必要性が確認できる |
| FR-DB04 | `db-schema-current.md`, `folder-structure-audit.md` | `managed_products` は runtime/配布整理とも関係する |
| FR-DB05 | `db-schema-current.md`, `hooks-commands-subagents.md` | `agent_registry` と role/agent の整理が対応する |
| FR-DB06 | `db-schema-current.md`, `reverse-scrum-audit.md` | `origin_mode` / `evidence_status` の中心要件 |
| FR-DB07 | `db-schema-current.md`, `reverse-scrum-audit.md`, `accumulated-knowledge.md` | `design_sprint_entries` が工程転換の核になる |
| FR-DB08 | `db-schema-current.md`, `reverse-scrum-audit.md` | `design_sprint_artifact_links` の必要性が明示済み |
| FR-DB09 | `db-schema-current.md`, `test-coverage-audit.md` | links と writer を増やさないと full chain が成立しない |
| FR-DB10 | `db-schema-current.md`, `perf-cost-audit.md` | query は速いが空運用で、有効性を上げる必要がある |

### 5.6 FR-GR01〜07

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-GR01 | `security-audit.md`, `capability-inventory.md` | detector の新規 security axis が必要 |
| FR-GR02 | `security-audit.md`, `cicd-audit.md`, `test-coverage-audit.md` | gate/pre-commit/CI での auto-run 接続が不足 |
| FR-GR03 | `security-audit.md`, `db-schema-current.md` | feedback を agent に返す telemetry ループが弱い |
| FR-GR04 | `security-audit.md`, `accumulated-knowledge.md` | destructive op / hook bypass / role逸脱の stop が必要 |
| FR-GR05 | `capability-matrix.md`, `hooks-commands-subagents.md` | PM/Orch/Cmd/Skill/Verify 各層の介入機構が整理済み |
| FR-GR06 | `security-audit.md`, `cicd-audit.md`, `perf-cost-audit.md` | record→detect→feedback→stop の閉ループ不足が明確 |
| FR-GR07 | `security-audit.md`, `perf-cost-audit.md`, `dependencies-audit.md` | false positive・budget・dry-run・opt-out の制御が必要 |

### 5.7 FR-A01〜08

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-A01 | `cicd-audit.md`, `db-schema-current.md` | PostToolUse auto-record の未接続が主論点 |
| FR-A02 | `cicd-audit.md`, `skill-quality-audit.md`, `folder-structure-audit.md` | SessionStart auto-sync と catalog rebuild の必要性 |
| FR-A03 | `cicd-audit.md`, `security-audit.md`, `test-coverage-audit.md` | gate runner と detector auto-run の統合が不足 |
| FR-A04 | `cicd-audit.md`, `security-audit.md`, `dependencies-audit.md` | pre-commit の適用漏れと staged diff 連動不足 |
| FR-A05 | `db-schema-current.md`, `perf-cost-audit.md` | design_review / test_baseline 自動 record が未実装 |
| FR-A06 | `db-schema-current.md`, `test-coverage-audit.md` | acceptance→test_design_entries 抽出導線が未接続 |
| FR-A07 | `cicd-audit.md`, `hooks-commands-subagents.md`, `cli-ux-audit.md` | `helix sync` 統合入口と command exposure の整理が必要 |
| FR-A08 | `cicd-audit.md`, `security-audit.md`, `perf-cost-audit.md` | cost guard / dry-run / atomicity の暴走防止が要る |

### 5.8 FR-EM01〜06

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-EM01 | `perf-cost-audit.md`, `capability-matrix.md`, `memory-feedback-drift.md` | KPI / detector / dev-state を統合表示する必要 |
| FR-EM02 | `db-schema-current.md`, `capability-matrix.md`, `perf-cost-audit.md` | relation graph はあるが record が薄い |
| FR-EM03 | `perf-cost-audit.md`, `cicd-audit.md`, `docs-integrity-audit.md` | export/report 一元化の必要が高い |
| FR-EM04 | `perf-cost-audit.md`, `cicd-audit.md` | SessionStart quick dashboard の headroom はある |
| FR-EM05 | `db-schema-current.md`, `test-coverage-audit.md` | plan別 V-model score は DB writer 前提 |
| FR-EM06 | `audit-summary.md`, `perf-cost-audit.md`, `memory-feedback-drift.md` | cross-plan / cross-doc summary が今まさに不足していた |

### 5.9 FR-FE01〜06

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-FE01 | `fe-weakness-analysis.md` | FE contract type 5種の必要性が明示済み |
| FR-FE02 | `fe-weakness-analysis.md`, `security-audit.md` | FE detector 5本の必要性が明示済み |
| FR-FE03 | `fe-weakness-analysis.md`, `cli-ux-audit.md` | `helix fe` command namespace の必要性 |
| FR-FE04 | `fe-weakness-analysis.md`, `accumulated-knowledge.md` | mock promotion / design gate を fail-close 化する根拠 |
| FR-FE05 | `fe-weakness-analysis.md`, `test-coverage-audit.md` | visual/axe/playwright/snapshot baseline の拡張が必要 |
| FR-FE06 | `fe-weakness-analysis.md`, `reverse-scrum-audit.md` | FE drive semantics を DB/phase/gate に結び直す必要 |

### 5.10 FR-AT01〜05

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-AT01 | `hooks-commands-subagents.md`, `off-plan-implementations.md` | role/agent/subagent の散在を統合する必要 |
| FR-AT02 | `hooks-commands-subagents.md`, `cli-ux-audit.md` | Codex/Claude/router の集約経路が必要 |
| FR-AT03 | `off-plan-implementations.md`, `perf-cost-audit.md` | cost guard 集約は off-plan capability 整理と直結 |
| FR-AT04 | `off-plan-implementations.md`, `db-schema-current.md` | contract export を一級 command にする必要 |
| FR-AT05 | `db-schema-current.md`, `hooks-commands-subagents.md` | `agent_registry` と allowed_tools schema の必要性 |

### 5.11 FR-LI01〜03

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-LI01 | `legacy-plans-carry.md`, `folder-structure-audit.md` | 旧 PLAN retain と source-of-truth 整理の両立が必要 |
| FR-LI02 | `legacy-plans-carry.md`, `audit-summary.md` | 旧 PLAN→V2 phase 対応表の基礎データが揃う |
| FR-LI03 | `legacy-plans-carry.md`, `off-plan-implementations.md` | deferred/carry を V2 に吸収する routing 根拠がある |

### 5.12 FR-VS01〜07

| FR-ID | 監査入力 | 根拠メモ |
|---|---|---|
| FR-VS01 | `reverse-scrum-audit.md`, `db-schema-current.md` | design sprint entries の必要性が明示済み |
| FR-VS02 | `reverse-scrum-audit.md`, `db-schema-current.md` | artifact link と pairing を DB 化する必要 |
| FR-VS03 | `reverse-scrum-audit.md`, `accumulated-knowledge.md` | architecture/detailed/functional の段階分け根拠がある |
| FR-VS04 | `test-coverage-audit.md`, `accumulated-knowledge.md` | pair-check と review/test 同時完了の必要性 |
| FR-VS05 | `reverse-scrum-audit.md`, `db-schema-current.md` | `functional_freeze` と Reverse/Scrum bridge の必要性 |
| FR-VS06 | `reverse-scrum-audit.md`, `capability-matrix.md` | drive/size 別 route と sprint 起動条件の差異が見える |
| FR-VS07 | `reverse-scrum-audit.md`, `test-coverage-audit.md`, `db-schema-current.md` | Reverse/Scrum を V-model sprint に繋ぐための核心要件 |

### 5.13 FR 74件マッピングの総括

1. FR-INV 群は `Phase A audit 自身` が一次入力である。
2. FR-VD / FR-V / FR-DB / FR-VS は `db-schema-current`, `reverse-scrum`, `test-coverage`, `accumulated-knowledge` が核になる。
3. FR-GR / FR-A は `security`, `cicd`, `hooks-commands`, `perf-cost` の4本柱でほぼ説明できる。
4. FR-EM / FE / AT / LI は派生要求だが、すべて既存 audit に入力根拠がある。

---

## §6 PM 判断必要 top-5 (大局判断)

### 6.1 判断論点

#### 1. `.helix/` runtime を Git 管理から外すか

- (a) 完全に Git 管理から外し、TTL/cleanup と export のみ残す  
  メリット: repo 汚染を大幅削減  
  デメリット: audit 再現性の別設計が必要  
  推奨度: 高
- (b) 一部だけ残し、cache/tmp/generated は外す  
  メリット: 監査履歴を一定保持  
  デメリット: ルールが複雑化する  
  推奨度: 中
- (c) 現状維持  
  メリット: 移行コスト最小  
  デメリット: 3,859 runtime files 問題が残る  
  推奨度: 低

#### 2. `skills/agent-skills` を vendor 扱いへ寄せるか

- (a) `skills/vendor/` 等へ分離し、HELIX core skill と正本境界を切る  
  メリット: catalog drift と frontmatter 品質問題を隔離できる  
  デメリット: 既存導線の修正が要る  
  推奨度: 高
- (b) 現配置のまま metadata 正規化だけ行う  
  メリット: 低コスト  
  デメリット: core と mirror の境界が曖昧なまま  
  推奨度: 中
- (c) 大幅廃止する  
  メリット: 入口は細くなる  
  デメリット: upstream 知識資産を失う  
  推奨度: 低

#### 3. PLAN 正本固定先をどこに置くか

- (a) `docs/plans/` を正本、`docs/features/PLAN-*` は appendix、`.helix/plans` は runtime に限定  
  メリット: 人間可読・Git 管理・履歴保持のバランスがよい  
  デメリット: appendix 再編コストがある  
  推奨度: 高
- (b) `.helix/plans` を正本、docs 側は export に寄せる  
  メリット: runtime と構造を統一できる  
  デメリット: Git 外し方針と衝突しやすい  
  推奨度: 低
- (c) `docs/features/PLAN-*` を正本に寄せる  
  メリット: feature appendix と近い  
  デメリット: carry / plan catalog / roadmap 追跡が難しい  
  推奨度: 低

#### 4. 旧 V1 capability の廃止 timing を一括にするか漸進にするか

- (a) Wave 1/2/3/4 の波状廃止で進める  
  メリット: fail-close と互換性を壊しにくい  
  デメリット: 一時的に二重管理期間が残る  
  推奨度: 高
- (b) Phase 1 で一括整理する  
  メリット: repo は早く軽くなる  
  デメリット: hook/agent/command 誤削除リスクが高い  
  推奨度: 低
- (c) V2 完了まで維持する  
  メリット: リスク最小  
  デメリット: source-of-truth drift を抱え続ける  
  推奨度: 中

#### 5. Reverse / Scrum を V2 中心線に格上げするか、派生扱いに留めるか

- (a) `origin_mode` / `evidence_status` / bridge を実装して中心線に格上げする  
  メリット: 既存投資を活かせる  
  デメリット: schema/gate 設計の広がりがある  
  推奨度: 高
- (b) 派生モードとして温存し、中心線は BE/FE/DB/Fullstack だけで設計する  
  メリット: Phase 2 設計は単純になる  
  デメリット: Reverse/Scrum の再利用価値を捨てる  
  推奨度: 中
- (c) V3 まで凍結する  
  メリット: 当面の設計負荷を下げられる  
  デメリット: 既存 capability と §3.8 要件が乖離する  
  推奨度: 低

### 6.2 PM 判断を急ぐ順

1. PLAN 正本固定先
2. `.helix/` runtime の Git 管理方針
3. hook / agent / skill vendor 境界
4. 旧 capability 廃止 timing
5. Reverse / Scrum の中心線化

---

## §7 リスクと未解決事項

### 7.1 監査横断で未解決の論点

1. `capability-matrix.md` は「9 セル」要件に対して実態は 15 セルで整理している  
   本書は audit 本文を優先して 15 セルで扱った。
2. `FR-INV06` の受入条件が参照する `deprecated.md` と、実際に作られた `deprecated-aggregation.md` の名前がずれている  
   要件書か成果物名のどちらかを Phase 1 で正規化する必要がある。
3. `docs/agent-skills/README.md` は broken link が多く、HELIX 正本として扱うべきか upstream mirror とみなすべきか未確定。
4. `PLAN-019`〜`027` の canonical source 不連続は carry 棚卸しで補完できたが、再現性のある正本構造は未回復。
5. `routing_decisions` は要件や detector が前提化している一方、schema 本体には未収載で扱いが未確定。

### 7.2 V2 中に re-audit が必要な領域

| 領域 | 理由 |
|---|---|
| `helix.db` v21 | writer 接続後に record 流量と query 性能を再評価する必要がある |
| security detector | 既存 fail-close を detector 化した後、false positive と stop 条件の妥当性を再監査する必要がある |
| FE subsystem | contract/detector/command 追加後に BE 対称性が本当に回復したかを再監査する必要がある |
| automation layer | `helix sync` / SessionStart / PostToolUse / Gate auto-run が接続された後に、fail-open/strict の境界を再監査する必要がある |
| skill catalog | usage telemetry 稼働後に、hit 0 を「未計測」から「死蔵」へ再判定する必要がある |
| memory governance | index 縮退後に stale/duplicate/type 欠落がどれだけ減ったかを再監査する必要がある |

### 7.3 監査精度に対する留保

| 領域 | 留保内容 |
|---|---|
| 性能 | `perf-cost-audit.md` の測定値は単発 snapshot であり、継続 benchmark ではない |
| cost | provider 集計と DB telemetry が不整合で、role 別 cost は未観測が多い |
| dependency | `pip-audit` 等の脆弱性 DB 照会を伴う確定監査は未実施で、多くが `unknown` のまま |
| CI/CD | `helix` PATH 不足の制約があり、実際の runtime 実行ではなく静的読解中心の箇所がある |
| security | local hook が各開発者環境で有効化済みかは断定できない |
| Reverse/Scrum | 実運用痕跡は smoke/placeholder が混ざるため、「未確認」と「未運用」を完全には分けられない |

### 7.4 重要な矛盾・ズレ

1. skill 件数  
   `SKILL_MAP.md` 106 件 vs 実体 104 件
2. role / model 正本  
   `ROLE_MAP`, `models.yaml`, `roles/*.conf`, `CLAUDE.md` 群でズレがある
3. PMO 権限  
   PMO Sonnet/Haiku の write 権限説明が文書ごとに異なる
4. command catalog  
   V2 L1 が planned command を先行定義し、現行 `docs/commands/index.md` と乖離している
5. memory / plan status  
   memory 上の完了主張と plan registry の状態が一致しない例がある

### 7.5 現時点の最大リスク

1. source-of-truth 固定前に Phase 2 へ進み、V2 文書自体が新たな drift source になること
2. writer 未接続のまま schema や detector だけ増やし、空運用 table / blocked detector を増やすこと
3. Wave 2 の統合作業を Phase 1 の局所 cleanup と同じ感覚で進め、hook/agent/command を壊すこと

---

## §8 次セッション onboarding チェックリスト

新規参画者が 30 分で Phase A 結論を掴むための最短読書順。

- [ ] `docs/v2/CONCEPT.md` §0-§1 を読み、V2 の価値連鎖を把握した
- [ ] `docs/v2/L1-REQUIREMENTS.md` §3 の 5 Phase 順序と派生要件の構造を把握した
- [ ] 本書 `audit-summary.md` §1 を読み、20 audit 全体像と集計値を把握した
- [ ] 本書 §2 の DR-001〜020 を読み、V2 の設計ドライバ top-20 を把握した
- [ ] `folder-structure-audit.md` §6 `整理計画` と末尾 `PM判断 top-3` を確認した
- [ ] `deprecated-aggregation.md` の Wave 1/2/3/4 と PM 判断必要 top-5 を確認した
- [ ] `capability-matrix.md` と本書 §3 を見て、5 層 × 3 問題の弱点を把握した
- [ ] `db-schema-current.md` の `V-model 強化で変更必須 table` と `v21 で新規追加する table` を確認した
- [ ] `security-audit.md` の `V2 Phase 4 で追加すべき security detector` を確認した
- [ ] `reverse-scrum-audit.md` の `V-model 強化との接続点` と `FR-VS07` 入力を確認した

### 8.1 30分 onboarding の推奨順

1. 本書 §1
2. `CONCEPT.md` §0-§1
3. `L1-REQUIREMENTS.md` §3
4. 本書 §2
5. `folder-structure-audit.md` Part 6-8
6. `db-schema-current.md` 集計と推奨
7. `deprecated-aggregation.md` roadmap
8. `security-audit.md` detector 提案
9. `reverse-scrum-audit.md` 接続点
10. 本書 §6-§7

### 8.2 新規参画者が最初に理解すべきこと

1. V2 は「ゼロから作り直す」のではなく「既存能力を中心線へ再接続する」改革である。
2. 最優先は source-of-truth と writer 接続であり、UI や command 名の表層変更ではない。
3. FE、Reverse、Scrum、security、automation はすべて V-model にどう接続するかで評価される。

