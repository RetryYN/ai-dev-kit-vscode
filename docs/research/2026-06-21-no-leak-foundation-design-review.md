---
title: "設計見直し（全面）: no-leak アーキテクチャの foundation 実機構レビュー"
date: 2026-06-21
status: review_complete
review_method: "5 cluster 並列 pmo-helix-explorer 調査（file:line 証拠）+ PM 直接 grep 検証（cluster E）"
related:
  - docs/plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md
  - docs/research/ut-tdd-fork-adoption-research-memo.md
  - HELIX-workflows/helix-process/db-auto-registration.md
  - docs/v2/L0-helix-workflows/concept.md
owner: PM
scope_exclusion: "右腕 G9/G12/G14 anchor 不足は GOAL-C-RIGHTARM-FULLCLOSE(owner=codex, in_progress)の担当範囲。本レビューの fix list から除外し連携。add-feature count-pin は触れない。"
---

# 設計見直し（全面）— no-leak foundation 実機構レビュー

> ユーザー指示（2026-06-21）「設計の不備を全面的に見直しせよ。修正したら設計部分の機械実装は駆動モデルのルールに従って先に実装せよ」。
> Process PLAN §1.5-§1.17 が描いた machine-precision アーキテクチャを、**実コード（file:line）に当てて設計意図 vs 実機構の乖離を全面検証**した結果。プラン起票より設計見直しを先行（§1.18 の方針を 5 cluster に拡張）。

## 0. メタ結論（最重要）

§1.5-§1.17 の全機構（検出・専門注入・自己改善・DB 脊椎）は、**3 つの foundation が「完全・自動」である前提**で成立する。実コード検証の結果、その **3 foundation は全て部分手動・空洞・未実装**であり、それを支えるはずの**ワークフロー強制も post-hoc のみ**、leak-class detector の中核も**未実装/dead-code**だった。つまり「絶対に漏らさない」は**根元の foundation で成立していない**。

| foundation（全機構が依存） | 設計意図 | 実機構 | 判定 |
|---|---|---|---|
| **F1 登録完全性**（§1.9） | 全作業（code/doc/test/PLAN）がファイル作成で自動登録 | PLAN のみ hook 自動。**code_catalog は自動 trigger 不在**（手動 `helix code rebuild`）。functional-registry は**二重手動 markdown**。設計**定義は未登録**（ID prefix 形式チェックのみ・advisory） | **部分手動** |
| **F2 実行証跡**（§1.6③） | 「やったっぽい」を弾き実行 green を gate で要求 | subcheck は実行可能（`HELIX_DOCTOR_SKIP_EXEC_TESTS!=1` なら test runner を呼ぶ）。**だが push gate / CI が `=1` で gate surface 時の実行を skip し、skip 時に未実行 anchor を `exec_pass` にカウント**（`g7_subcheck.py:274`）→ gate の瞬間に「実際に green」を再確認しない | **gate 時 bypass**（実行証跡が無いのでなく gate surface が再確認しない。TL: P0/P1 境界だが AI 駆動完了条件として P0） |
| **F3 定性レビュー健全性**（§1.6①） | LLM レビュー genuine pass を gate 化 | `tl_review=approve` は**手書き文字列の存在チェックのみ**。tl-advisor 実出力との link 無し → 改ざん（changes_required を approve と書く）検知不可。再レビュー強制無し。semantic_gate は脆い text match | **未検証（改ざん可能）** |

→ detector は「不完全・stale な期待集合」に漏れを測り、定性 gate は「genuine か不明な承認」を信頼し、実行 gate は「実際に走ったか不明な anchor」を通す。**プラン起票より設計見直しが先、は正しい。**

## 1. cluster 別 findings（設計 vs 実機構、file:line 証拠）

### Cluster A — 登録 foundation（§1.9 / §1.7①）

| # | 設計意図 | 実機構（file:line） | GAP / 重大度 |
|---|---|---|---|
| A-1 | db-auto-registration.md: 「コード変更 → code_catalog（AST→FTS5）」をイベント駆動自動登録、「手動登録を排し」 | code_catalog 更新は `helix code rebuild` の**手動実行のみ**。git hook / PostToolUse hook に code 変更 trigger 無し（`code_catalog.py:912-930` rebuild は手動）。`posttooluse-skill-catalog-rebuild.sh` は SKILL.md のみ反応 | **P0**: .py/.sh を書いても code_index は古いまま。「作成→自動登録」未実装 |
| A-2 | functional-registry = 全機能 SSoT、機能追加で最新維持 | `functional_registry_seed.py:20` SOURCE_DOC = **手動 markdown**（`helix-workflows-functional-registry.md`）を読んで yaml seed。`SUMMARY_TOTAL=548` は手動定数。`_disk_counts()` は差分可視化のみ・書き戻し無し | **P1**: 機能追加ごとに「markdown 手編集 + seed 手実行」の二重手動。追記し忘れ＝検出の前段で漏れ |
| A-3 | registry_design_coverage: 設計定義の被覆を機械証明 | `registry_design_coverage_checks.py:51-55` `_resolved()` は **ID prefix のみ**判定（mode=advisory）。**ただし TL 反証: `design_id_existence_checks.py:85` が別 detector として FN の L6 doc 実在を検査** → 「prefix だけ」は不正確。残る穴 = 設計**定義の内容（DbC requires/ensures/invariant・FN spec body）が DB に構造化登録されない**（ID/doc 存在は見るが定義は載らない） | **P1（TL 訂正: P2→定義登録の穴は残る）** |
| A-4 | generates 宣言 → 成果物を code_catalog/doc に自動反映（db-auto-registration.md:45） | `plan_generates` に artifact_path 登録 + **存在チェック advisory はある**（TL 訂正: 「文字列だけ」は過大）。だが **生成→code_catalog/doc への自動反映ロジックは無い** | **P1**: generates 宣言と実体の自動同期が無い |
| A-5 | セッション停止 → handover dump 自動 | `stop.sh` は audit_log/session_telemetry のみ。`handover_auto_dump.py` 実装はあるが stop.sh から未呼出 | **P3**: 現在地の自動保全が機能せず（手動 dump 依存） |

### Cluster B — デグレ防止 + 依存漏れ（§1.7③④）

| # | 設計意図 | 実機構（file:line） | GAP / 重大度 |
|---|---|---|---|
| B-1 | CI detector-gate が V-model pair を機械保証 | `ci.yml:153` detector-gate が **`HELIX_DOCTOR_SKIP_EXEC_TESTS=1`** で実行 → **anchor 構造確認のみ、実テスト pass は CI で未保証** | **P0（F2）**: 実装が回帰しても anchor が在れば CI green |
| B-2 | requirement_drift: FR→L4-6→code→test の縦 trace 保証 | `vg_overview.py:221` `_requirement_drift_required_clean()` は **`focus="L6"` 固定** → FR→実装コードの縦 trace は VG-overview gate に**含まれない**。stale_check 常時 off | **P1**: コードに FR anchor 無くても gate 通過。設計更新→コード未更新のデグレ検知不可 |
| B-3 | 依存漏れ防止（コード粒度） | `dependency_cycle_checks.py` は AST import **循環のみ**（baseline-required, fail-close）。**依存方向・module 境界違反は非検出**。テスト/`__pycache__` 除外 | **P1**: §1.7④「コード粒度 dependency-direction」は循環止まり（ADR-002 方向 map 未実装） |
| B-4 | baseline ratchet で既知 warning を固定し劣化監視 | `plan_dependency_gate.py:298` / `dependency_cycle_checks.py` `expiry:"2026-09-12"` が JSON にあるが**期限超過を自動 fail にするロジック無し** | **P2**: 既知 bad-cycle が baseline 永続化リスク |
| B-5 | source_scan_vs_registry で未登録を fail-close | `vg_overview.py:41-49` `SOURCE_SCAN_ALLOWED_UNREGISTERED_PATHS` に subcheck/anchor_quality が "temporarily allowlisted" で**期限・担当なし固定化** | **P3**: 新 Python の silent allowlist 追加 guard 無し |
| (B-6) | 右腕 G9/G12/G14 anchor + exec | `g9/g12/g14_subcheck` anchored **5/18・5/57・1/20** 全 advisory、approved_deferred は overall_clean 不影響 | **GOAL-C 担当**（除外・連携） |

### Cluster C — 表記ゆれ防止 + DDD（§1.7⑤）

| # | 設計意図 | 実機構（file:line） | GAP / 重大度 |
|---|---|---|---|
| C-1 | `check_ubiquitous_language`（concept.md:870 §12.2）: L1-L14 doc の未定義用語/表記ゆれを検出 | **未実装**（`helix-doctor` / `ddd_registry_checks.py` に該当関数 grep 0 件）。`ddd-registry.yaml` の `grep_pattern` フィールドは存在するが**doc scan に未接続＝dead code** | **P0（⑤の中核）**: Glossary 未登録用語の doc 混入を誰も止めない |
| C-2 | `check_bc_anti_corruption`（concept.md:978 §14.3）: Forward 正本 doc への他 BC 用語未変換混入を検出 | 同名関数 `ddd_registry_checks.py:425` は**別物**（registry 内の例数/フィールド充足のみ検査、**Forward doc を scan しない**）。name-aliasing で「実装済み」に誤読される | **P0**: BC 越境を実行時/PR 時に検出不能 |
| C-3 | adapter rule-drift（CLAUDE.md⇔AGENTS.md⇔runtime adapter の規律一致） | **機構なし**。`test_core_manifest_drift.py` は import path 配線のみ。`axis_07_doc_drift` は model/role/phase token の canonical 一致のみ（規律内容の divergence 無反応） | **P1**: adapter 間で規律が矛盾/欠落しても検知不可 |
| C-4 | ddd registry 3 checks を fail-close | `check_ddd_registry_doctor()` は findings を **WARN のみ**（exit 0）。CI Required 未接続 | **P2**: advisory 止まり |

### Cluster D — 二重ゲート（定量∧定性∧実行、§1.6）

| # | 設計意図 | 実機構（file:line） | GAP / 重大度 |
|---|---|---|---|
| D-1 | G-review: tl_review=approve を push 条件に | `push_gate.py:825-839` は **`tl_review=="approve"` 文字列の有無のみ**。tl-advisor 実出力と frontmatter の間に手動書込が介在 → 改ざん検知不可。再レビュー強制は「当面手続き規律」（github-operations.md:55） | **P0（F3）**: 定性ゲートが genuine か機械保証されない |
| D-2 | 実行証跡を gate で要求 | `g7_subcheck.py` は実テスト実行するが、`push_gate.py:930` が **`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` をセットしてから collect_vg_overview** → push 時に実行 pass を再確認しない（B-1 と同根） | **P0（F2）** |
| D-3 | semantic_gate: 定性判断を構造化記録 | `trace_symmetry.py:749-750` は `"audit_verdict" in text and "pass" in text.lower()` の**脆い text match**。LLM 判定の構造化 DB 記録無し | **P1**: 本文の "pass" 誤検出余地。定性の構造化記録欠如 |
| D-4 | L2↔L10 FE ブラウザ検証 gate | `vg_overview.py:169-217` は **`ui_absent` waiver の存在確認のみ**。UI 実装時にブラウザ実行証跡を要求する gate **完全欠如**。waiver 置きっぱなしの抜け道 | **P1**: FE がブラウザ検証なしで通過 |

### Cluster E — ワークフロー強制 + 駆動選択（§1.10）

| # | 設計意図 | 実機構（file:line / grep） | GAP / 重大度 |
|---|---|---|---|
| E-1 | 逸脱検出 → 有効駆動 menu から選択を強制、未選択は block | `route_engine.py` に fail-close/menu/forced/select マーカー **皆無**（routing helper, advisory） | **P1**: forced drive selection は convention。逸脱したまま進める |
| E-2 | Process⊃Action + forward_return 機械強制 | `plan_validator.py:445-489` process=workflow_chain+forward_return 必須、action=parent_process 必須、child→process 逆参照(626-634) を**lint 時 post-hoc 検証** | **部分（強み）**: 構造は検証されるが、work を block する gate でなく PLAN lint |
| E-3 | deprecated Process を新 Action の parent にしない（退化防止）/ workflow_chain valid-link | detector **実在せず**（grep 0）。CLAUDE.md 既出候補のまま未実装 | **P1**: 退化（deprecated parent）機械防止なし |
| E-4 | drive-model-passage（全駆動が passage+forward_return を DB 登録）| detector **実在せず**（grep 0） | **P1**: 駆動の DB 登録完全性が未検証 |
| E-5 | Forward 逸脱 → GitHub Issue 起票強制 / escalation-stale surfacing / branch-protection-emit | Issue テンプレート 8 種は存在（`.github/ISSUE_TEMPLATE/`）。だが**起票強制・escalation-stale・emit script は未実装**（grep 0） | **P1（AI-safe GitHub ③④）**: silent rot surface 無し |

## 2. §1.7 no-leak 5 機構の honest 再ベースライン（訂正）

Process PLAN §1.7 の現状評価を実機構に合わせて訂正する（楽観評価を是正）:

| # | 機構 | §1.7 旧評価 | **honest 訂正（本レビュー）** |
|---|---|---|---|
| ① | DB 自動登録 | 「部分（§1.18）」 | **部分手動（維持）**: code_catalog 自動 trigger 不在(A-1) + functional-registry 二重手動(A-2) + 設計定義未登録(A-3) + generates 実体未照合(A-4) |
| ② | 設計/実装/テスト 0 漏れ | 「強」 | **部分**: fn_ut_pair/vg_overview は強いが、**期待集合の登録が①で部分手動**＝0 漏れの前提が崩れる。requirement_drift L7 が gate 外(B-2) |
| ③ | デグレ絶対防止 | 「部分」 | **部分（維持・悪化点追加）**: CI/push が実行スキップ(B-1/D-2)＝回帰が gate を通る。baseline expiry 未強制(B-4) |
| ④ | 依存 0 漏れ | 「部分」 | **部分（維持）**: PLAN 粒度は強、コード粒度は**循環のみ**で方向/境界未検出(B-3) |
| ⑤ | 表記ゆれ 0 | 「弱」 | **未実装（弱より下方訂正）**: 中核 `check_ubiquitous_language` が spec-only(C-1)、BC 越境は name-aliased(C-2)、rule-drift 不在(C-3) |

→ 加えて **定性ゲート(F3/D-1)と実行ゲート(F2/B-1/D-2)が foundation 級の穴**。§1.6 の「定量∧定性∧実行」AND は、定性が改ざん可能・実行が gate 時 skip のため**現状 AND が成立していない**。

## 3. 設計 FIX 優先順（foundation 先行）

「修正」の対象 = 設計を honest 状態へ正し、foundation の穴を塞ぐ機構を**設計として確定**する。依存順（下が上に依存）:

**第0層（foundation、最優先 — 全機構が依存）**
- **F1 登録自動化 + 設計定義登録**（A-1〜A-4）: ①code/doc/test を PostToolUse hook で code_catalog へ増分自動登録（SKILL.md rebuild hook と同型）②functional-registry を**実ファイル + 設計 doc scan から derive**（手動 markdown 依存を排す）③設計**定義（DbC requires/ensures/invariant・FN spec）を設計 doc から抽出し構造化登録** → registry_design_coverage を「ID prefix」から「定義実在」へ。
- **F2 gate 時 実行証跡**（B-1/D-2）: 「実際に green」を検証する場所を設計で確定。`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` の CI/push skip を、変更 pair について **実行証跡 artifact（run id + green + timestamp）の gate チェック**へ置換（CI 速度と実行保証の両立設計）。
- **F3 review-evidence 健全性**（D-1）: `tl_review=approve` を **review-evidence schema（worker≠reviewer + review_kind=cross_agent + tests_green_at≤reviewed_at + 実レビュー出力への link）**へ。改ざん検知を機械化（§1.17 Sequencing① の review_evidence ADR と同一）。

**第1層（leak-class、foundation 確定後）**
- **F4 表記ゆれ**（C-1/C-2/C-3）: `check_ubiquitous_language` を実装（`ddd-registry.yaml` の dead `grep_pattern` を doc scan に接続）。BC 越境の name-aliasing 解消。rule-drift（adapter marker 一致）。
- **F5 ワークフロー/駆動強制**（E-1/E-3/E-4/E-5）: route_engine forced-selection、deprecated-not-parent、drive-passage、escalation-stale/emit。**①登録 foundation が前提**（登録されて初めて非迂回が意味を持つ）。
- **F6 依存方向 + requirement_drift L7**（B-2/B-3/B-4）: code dependency-direction map、requirement_drift L7 focus を gate へ、baseline expiry 自動強制。

**除外（GOAL-C 担当）**: 右腕 G9/G12/G14 anchor + exec（B-6）は verification-forward-gate process が進行中 → 重複させず連携。

## 4. 機械実装の sequencing（駆動モデルのルールに従う）

ユーザー指示「修正したら設計部分の機械実装は駆動モデルのルールに従って先に実装」を以下で満たす:

1. **駆動選択**: F1〜F6 は「既存ハーネスに欠落していた強制を追加」= **Add-feature 駆動**（既存正本に差分機能、戻し先 L4-L7）。ただし F1/F2/F3 のうち「db-auto-registration.md が auto と書くのに未実装」= 設計 doc と実装の乖離是正は **Reverse の性質**も持つ → drive 選択は tl-advisor 諮問で確定（CLAUDE_RUNTIME_ADAPTER §2: 技術判断は TL 経由）。
2. **pair_closure 厳守**: 各 detector 追加は L6 機能設計（関数粒度 DbC）+ L7 UT anchor + exec pass + trace_symmetry + semantic_gate。設計⇔検証を片肺にしない（foundation を作る機構自身が foundation 規律に従う）。
3. **forward_return**: 各 Action は Process PLAN を parent_process にし、forward_return（採用 detector を既存検出群へ統合）を宣言。
4. **Codex 委譲**: detector 実装コード（Python）は se/pe へ委譲。Opus（PM）は設計 doc・PLAN・policy のみ直接編集（製造元 repo 規律）。
5. **GOAL-C 衝突回避**: add-feature PLAN 起票は count-pin ripple を起こし GOAL-C in-flight と衝突 → **add-feature 起票は GOAL-C 着地後**。それまでは設計 doc 修正（本レビュー + F1〜F3 の設計確定）を先行（count ripple なし）。
6. **段階導入**: foundation detector も big-bang fail-close でなく shadow → advisory → required（§1.17 P0-1 と同方針）。

## 5. このレビューの位置づけ（forward_return）

本レビューは Process PLAN §1.18「設計見直し先行」の**証拠基盤**。§1.7 table の honest 訂正（§2）と FIX 優先順（§3）・実装 sequencing（§4）を Process PLAN に反映し、foundation（F1/F2/F3）の設計確定 → GOAL-C 着地後に Add-feature 起票 → Codex 実装、の順で V-model へ収束させる。**人間チームゲートは導入しない**（単独 AI-PM 前提維持、§1 orientation）。

## 6. TL adversarial review 反映（tl-advisor verdict=changes_required、2026-06-21）

tl-advisor 諮問（read-only）の結果。**方向性 approve（foundation 3点最優先・FIX 優先順は妥当）だが本文に過大表現あり → 訂正**。

**6.1 過大表現の訂正（§0/§1 に反映済）**
- **A-3**: `registry_design_coverage` は prefix のみだが、**`design_id_existence_checks.py:85` が別 detector で FN の L6 doc 実在を検査**。「prefix だけ」は不正確 → 残る穴は**定義内容の構造化登録不在**に限定（P2→P1 だが穴の性質を正確化）。
- **A-4**: `plan_generates` に**存在チェック advisory あり** → 「文字列だけ」は過大。穴は**生成→自動反映の不在**。
- **F2**: subcheck は実行可能。「実行証跡が全く無い」でなく**「push/CI gate surface が gate 時実行 green を再確認しない + skip 時に未実行 anchor を `exec_pass` カウント（`g7_subcheck.py:274`）」**。重大度 P0/P1 境界、AI 駆動完了条件としては P0 妥当。

**6.2 駆動モデル選択（TL 推奨、§4.1 確定）**
- **F1 = Reverse → Add-feature**: `db-auto-registration.md` が accepted で auto と断言する一方 impl が追いつかない設計-実装乖離 → まず **Reverse/normalization で乖離を記録**、その closure として **Add-feature 実装**を切る。
- **F2 = Add-feature**: 既存 `g7/g8/g9/g12/g14_subcheck` + `vg_overview` の**契約拡張**（gate surface に実行証跡再確認を追加）。L4-L6 設計追補 + L7 実装。
- **F3 = Add-feature + ADR**: `review_evidence` schema は gate 契約**拡張/hardening**（replacement でない）。ADR/adversarial-review を先置。
- **Forward は過剰**（新規全体設計でなく既存正本への差分 hardening）。

**6.3 schema 具体案（TL 提示、実装時の契約）**
- **F3 review_evidence**（最低限）: `review_id` / `review_kind` / `reviewer_role` / `reviewer_model` / `worker_model` / `reviewed_commit` / `review_output_path` / `review_output_sha256` / `tests_green_at` / `reviewed_at` / `verdict`。**改ざん検知は frontmatter だけでなく review output の content hash + reviewer identity + reviewed commit SHA まで持つ**（後からの差し替えを封じる）。
- **F2 実行証跡 artifact**: `run_id` / `target` / `command` / `commit_sha` / `started_at` / `ended_at` / `exit_code` / `artifact_sha256`。

**6.4 追加 foundation hole（TL 指摘、P1）**
- **`exec_pass` 命名が危険**: skip 時にも pass count を返す → 証跡語彙を `structurally_counted_as_pass_when_skip_exec` 等に分離すべき（F2 と同根）。
- **review evidence tamper**: 6.3 の content hash / reviewer identity / commit SHA がないと後から差し替え可能（F3 に内包）。
- **`helix code find` が read-only で `sqlite unable to open database file`**: DB locator/read-only mode の弱さ。sandbox 由来の可能性もあるが調査候補（DB 能動脊椎 §1.15 doc-locator の前提）。

**6.5 テスト戦略（TL 必須）**
- **F1**: hook unit + integration（作成→自動登録の e2e）。
- **F2**: **skip/execute の二重テスト** — `HELIX_DOCTOR_SKIP_EXEC_TESTS=1` 時に gate が pass しない、or pass しても「execution not verified」として区別されるテストを必須。
- **F3**: **tamper test**（approve 改ざん・output 差し替えを検知）。

**6.6 FIX 優先順の補足（TL）**: 第0層 F1/F2/F3 → 第1層は妥当。**第1層内の F4/F5/F6 順序は固定不要**: F5 workflow 強制は F1 に強依存、F4 表記ゆれは shadow/advisory なら**並行設計可**（fail-close 実装は F1 後に限定）。

→ verdict=changes_required は「本文訂正 + foundation の ADR/PLAN 確定が残」を意味する。**6.1 訂正は反映済**、6.2-6.5 は GOAL-C 着地後の Add-feature/ADR 起票時の契約として確定。

## 7. F3 実装結果 — 「F1 が F3 の clean landing をブロックする」の実証（2026-06-21）

ユーザー指示「設計部分の機械実装を駆動モデルのルールに従って先に実装せよ」を受け、foundation の中で最も独立した **F3（review-evidence detector）から実装を試みた**。結果は **F3 を clean に landing できない**こと、そしてその原因が **F1（登録 foundation）の欠如そのもの**であることの実証だった。

**実装済（検証済）:**
- `cli/lib/review_evidence_checks.py` — `check_review_evidence(plan_paths, repo_root)` advisory detector。§6.3 schema を機械検証（必須フィールド欠落 / cross_agent genuineness reviewer≠worker / reviewed_before_tests_green / **output sha256 tamper**）。
- `cli/lib/tests/test_review_evidence_checks.py` — **7 UT pass**。
- detector は完成し動作する（F3 の「定性レビュー genuine 性の機械検証」を実現）。

**clean landing をブロックした 2 つの障壁（両方とも F1）:**

1. **counted add-feature PLAN → GOAL-C 単一 objective audit を破壊**: F3 を `docs/plans/add-feature/` に起票すると、`objective-l1-l6-coverage` audit が「全 add-feature ファイル = 現 objective ticket ∪ excluded_inventory」を要求するため（`test_helix_l0_l14_flow_contract.py:4534`）、別 objective（no-leak foundation）の F3 が「Extra item」で contract test を破る。GOAL-C の objective audit に F3 を「parked」分類で押し込むのは意味的に誤り（F3 は parked でなく別 objective の能動作業）。**= §1.17 P1-3「並行 objective が単一 objective audit / 共有 count-pin state で衝突」の実証**。
2. **新 detector コードファイル → 登録の手動性**: 新規 `cli/lib/*.py` は code_catalog/registry に自動登録されない（A-1）ため、source_scan 系で「未登録」になり得る。= F1 の別側面。

→ **決定的所見**: 「設計部分の機械実装を先に」を文字通り実行しようとした結果、**最初の foundation detector を clean に追加することすら F1（自動登録の不在 + 単一 objective audit）がブロックした**。これは設計レビューの最重要結論「**foundation（特に F1）を先に直さねば、新機構を clean に足せない**」を、実装の現場で機械的に証明している。よって順序は **F1 登録自動化 + objective-collision を解く shared-state contract（§1.17 P1-3）→ しかる後に F2/F3/他 detector**。

**staged F3 add-feature PLAN（GOAL-C objective close 後 / F1 後に起票）:**
- plan_id: `add-feature-2026-06-21-review-evidence-detector`、parent_process = 本 Process、drive=add-feature、design_change_class=contract_extension（schema は §6.3 で確定済）。
- generates: review_evidence_checks.py + test（実装済）。pair_closure: L6↔L7 = check_review_evidence 関数(§6.3 schema) ↔ 7 UT。
- 段階導入: advisory(現状) → gate_profile ADR 後に required。
- 起票時の税（F1 未修正なら手動）: count pin ×16（discovered×3/checked/glob、audit 6 + py/bats mirror）+ deferred-coverage 分類 + objective audit reconcile。**F1 修正後はこの税が自動化される** = F1 の価値の定量的根拠。

→ tree に detector + test を staged 保持（uncommitted）。formal counted add-feature 起票は GOAL-C objective close + F1（または objective-collision を解く最小 shared-state contract）後。
