---
plan_id: process-2026-06-03-v2-implementation-roadmap
title: "Process Plan: V2 実装計画 — HELIX v2 PM型TDDベース生体モデルワークシステム開発ハーネス 開発工程"
plan_scope: process
workflow_chain: "Phase1(L0確認→L1/L3+対ペア) → Phase2(L4-L6+対ペア) → Phase3(L7実走+自動化+Python化本体改修) → Phase4(HELIX DB機能拡張) → Phase5(L8-テスト実走+トラブルシュート強化) → Phase6(テストプロジェクト透過フルrun+ボトルネック改善)"
kind: planning
layer: L0
drive: discovery
status: deprecated
deprecated_on: 2026-06-08
tl_review: approve  # 廃止はユーザー指示(2026-06-08「ロードマップは廃止」)。置換=process-2026-06-08-verification-forward-gate（検証=Forward 内在ゲート）。TL は置換設計を comprehensive review 済。
created: 2026-06-03
owner: PM
contains_action_plans:
  - docs/plans/reverse/reverse-2026-06-03-l1-l3-trace-hardening.md
  - docs/plans/discovery/poc-2026-06-03-trace-symmetry-detector.md
  # add-feature-2026-06-08-detector-failclose-ci-gate は廃止後 process-2026-06-08-verification-forward-gate へ再帰属（退化防止）
forward_return: "Forward V モデル L0-L14 への全 pair 収束。Phase1-2 で L0-L9 の設計↔検証ペアを完全密度で確立、Phase3-4 で L7 実装+自動化+HELIX DB を実体化、Phase5-6 で L8-L14 を実走完走。最終=V モデル DB に全 L-pair freeze + trace/coverage closure が登録された状態。"
agent_slots:
  - role: pm-advisor
    slot_label: "PM — Phase 行程設計・優先順位・Forward 昇格判断"
  - role: tl-advisor
    slot_label: "TL — Phase 境界/駆動耐性/forward_return/公開API保全 の adversarial check"
  - role: se
    slot_label: "SE — Phase3/4 の自動化・Python化・DB 機能拡張実装（Codex）"
  - role: qa
    slot_label: "QA — Phase5/6 テスト実走・トラブルシュート・ボトルネック計測"
generates:
  - artifact_path: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
    artifact_type: markdown_doc
  - artifact_path: CLAUDE.md
    artifact_type: markdown_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/v2/L0-helix-workflows/concept.md
  - helix/HELIX_CORE.md
  - HELIX-workflows/HELIX-process-L0-L14.md
  - HELIX-workflows/helix-process/plan-model.md
  - docs/v2/L4-basic-design/方式設計.md
  - docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md
---

# V2 実装計画 — HELIX v2 開発工程の統括 Process

> ⚠️ **DEPRECATED / 廃止（2026-06-08、ユーザー指示）**: 「6-phase ロードマップを常時目指す」進め方はアンチパターンとして**廃止**。
> 検証（L-pair のテスト実行・閉合）は**ロードマップの Phase として追いかけるのでなく、Forward V-model に内在する検証サイクル＝ゲートとして機能させる**（各層の凍結＝検証閉合をゲートで通す）。
> 置き換え方針: **検証 = Forward ゲート**（設計＋テスト設計＋テスト実行＋trace 閉合を fail-close ゲートで強制）。本書の Phase 分解・「最優先ゴール」framing は無効。past の進捗ログは history として残置。
> 本書配下で landed した V-model 作業（trace hardening / detector PoC 等）は有効資産だが、parent は本 Process でなく Forward の該当 L に再帰属する。

> 本書は **HELIX v2 = PM型 TDDベース 生体モデルワークシステム開発ハーネス** の開発工程を統括する Process 正本（親=工程行程）である。
> 6 Phase の連鎖を `workflow_chain` に、Forward 収束先を `forward_return` に宣言する。各 Phase が起動する具体作業は Action Plan（子）として `contains_action_plans` に追記される。

## 1. 目的と前提

### 1.1 この計画が解く問題
- 直近の検証で **V モデルの設計↔検証ペアの密度が不十分**であることが判明（L4↔L9 で確証: NFR 23ID→観点2個、IF-05 trace 欠落。他ペアも同条件生成で疑い濃厚）。これは「ドキュメントカバレッジ不足」の症状。
- Shell 依存で**環境差異に弱い**（GNU/BSD coreutils 差・bash 版差）。ただし Python 化は **機能修正＝L6 視座**の改修であり、独立した上流 redesign ではない。

### 1.2 絶対原則上の位置づけ（前提条件）
ドキュメントカバレッジと駆動機構が成立しない限り、**そもそも HELIX のコアが回らない**（`HELIX_CORE.md §0` = V モデルへ収束し DB に載らなければ「完了」が成立しない）。したがって本計画の最優先は **Phase 1-2 を「ドキュメント ↔ ワークフロー/ドライブ」の循環で回し切る**ことであり、上流設計の本格 redesign はその後段に置く。

### 1.3 スコープ
- **機能要件 = 既存の全洗い出しを漏れなく内包**する（`cli/helix-*` 118本・hooks・`cli/lib` Python・SQLite・548機能の既存実態すべて）。
- **監査スコープ = 全 L・全 doc・全成果物 ＝「すべて」**（一部追補ではない）。ただし**各実作業の編集範囲は、その Action Plan の allowed_files / handover Next Action / task-plan に従う**（roadmap の広域スコープは個別作業の allowed_files 制約を弱めない。tl-advisor P1 反映）。
- このメタ定義（スコープ・優先順位・循環）は `CLAUDE.md` に焼き直す（製造元リポにつき Opus 直接編集 lane）。

## 2. 貫通要件

**Forward V モデル および 駆動モデル（Reverse/Discovery/Retrofit/Recovery 等）は、この 6 Phase をフル run しても耐える設計でなければならない。** 各 Phase で見つかる「プロセス機構が耐えられない箇所」を Forward / 駆動の改善として戻すことが、本計画の実体（= コードの redesign ではなく HELIX プロセス機構の堅牢化）。

## 3. Phase 全体像（確定版）

| Phase | 範囲 | 対ペア / 主眼 | 駆動の傾向 |
|---|---|---|---|
| **1** | L0 確認 → L1 / L3 設計を確実に回す | L1↔L14 運用テスト設計、L3↔L12 受入テスト設計 | Forward（document↔workflow 循環） |
| **2** | L4〜L6 設計を完璧に回す | L4↔L9 総合、L5↔L8 結合、L6↔L7 単体 | Forward + Retrofit（片肺解消） |
| **3** | L7 を実走＋**自動化**＋**Python化 本体改修**（機能修正＝L6 視座でここに内包） | L7 単体テスト実施 | Forward + Refactor |
| **4** | **HELIX DB 機能拡張**（自動化が回ってから＝確実性↑・DB ならではの解法が見える） | 永続化/監査/closure の DB 収束 | Forward + db |
| **5** | L8〜 のテスト設計を実地に回し、トラブルシュート経由で実装・設計を強化 | L8 結合〜 | Forward + Troubleshoot |
| **6** | テストプロジェクトを透過してフル run、全体機能のボトルネックを改善・強化 | 全体回帰 | Forward + Refactor |

> **L7/L8 用語固定**: HELIX 正本では L7 が V 字の谷（実装工程）であり、L6 単体テスト設計に基づく「テスト実装 → 本体実装 → 単体テスト実施」までを含む。L8 は L5 詳細設計 / 結合テスト設計に対応する結合テスト工程であり、「L8=本体実装」ではない。

> **工程契約の最終確認（2026-06-09）**: ユーザー確認により、本 Process は現行 HELIX 正本どおり `L6=機能設計 / 仕様書 + 単体テスト設計`、`L7=実装 + 単体テスト実装 + 単体テスト実施 + カバレッジ確認 / closure`、`L8=結合テスト` を維持する。`L8=単体テスト` への pair map migration は採用しない。

### 3.1 順序の根拠
- **Phase 1 → 2**: ドキュメントカバレッジを上流（L0/L1/L3）から固め、その対ペア検証設計まで密度を揃えてから設計層（L4-L6）へ降ろす。片肺（L4↔L9 で確証）はここで構造的に解消する。
- **Phase 3（自動化）→ Phase 4（DB）の分離**: 自動化を実走させると実際のデータ/永続化要求が観測でき、**DB ならではの解法（制約・index・トランザクションで解く類）が見えてから schema を確定**できる。先に DB を作ると観測前の推測 schema になる（HELIX 従来思想: DB schema 変更は escalation gate、closure DB は「正当化時に設計」と park と整合）。
- **Python 化を Phase 3 に内包**: L6 視座の機能修正であり、L7 実走の本体改修として自動化と同層で扱う。L4 方式の独立 redesign には昇格させない。

### 3.2 各 Phase の Action 起票時の最低受入条件（tl-advisor P1/P2 反映）
本 roadmap を anchor に子 Action を起票する際、各 Phase は以下を Action の entry / 受入条件に必須化する（親はこれを宣言し、判定実体は子へ分解）。

- **Phase 1-2（pair 密度）**: 各 L-pair の Action 受入に `design_id_count` / `test_id_count` / `missing_reverse_trace` / `balance_ratio` / `orphan_test_ids` の検査を必須化（ID 粒度 trace symmetry を先に固定）。
- **Phase 3（分割）**: 子 Action を「①自動化の検出/ゲート ②Python 化対象 ③L7 実装回帰」に分け、Refactor（振る舞い不変）と機能修正の混線を防ぐ。Python 化 Action ごとに **外部 CLI 出力互換 / exit code 互換 / frontmatter enum 非破壊 / `@~/.helix/core/<path>`・公開 API 非破壊**を acceptance に置く。
- **Phase 4（DB、escalation 対象）**: Phase4 Action の entry を「Phase3 観測結果 → L4/L5 D-DB/D-CONTRACT 追補 → migration/rollback 設計 → pair test 設計」の順に必須化。L8/L9 側に migration test / rollback test / idempotency test / schema drift test を先置きする。DB schema 変更は escalation gate を通す。
- **Phase 5（Troubleshoot の workflow 扱い）**: `troubleshoot` は `VALID_DRIVES` にはあるが plan-model の Action workflow enum（discovery/reverse/recovery/incident/add-feature/refactor/retrofit/research 系）には無い。Phase5 の子 Action は **Recovery / Incident / Refactor のいずれかへ routing** するか、Troubleshoot を非 workflow step（観測・切り分け活動）と明記して起票する。
- **Phase 6（full run）**: 「テスト project 透過」に加え、**失敗時の Forward 復帰先を自動記録できるか**を acceptance に入れる。

## 4. 循環（最優先メカニズム）
```
ドキュメントを埋める（カバレッジ完備）
  → それを回す駆動/ゲート/detector を改善
  → 結果をドキュメントに反映
  → （以下反復）
```
この **document ↔ workflow/drive の循環**を Phase 1-2 で回し切ることが、コアを起動させる前提。循環が回ってから上流設計の見直し（Phase 3 以降）に進む。

## 5. forward_return（Forward 収束）
本 Process は単一 workflow ではなく駆動連鎖の親。`forward_return`（frontmatter）のとおり、最終的に **V モデル L0-L14 の全 L-pair が完全密度で freeze され、trace / coverage / 契約整合が HELIX DB に closure 登録された状態**へ収束する。各 Phase の Action（子）は `parent_process` で本書を逆参照し、closure event で V モデル DB へ統合する。

**closure 判定は親では測らず子 Action に分解する**（tl-advisor 契約 P1 反映）。親の `forward_return` は umbrella の方向宣言であり、「完全密度 / trace closure」の測定式は持たない。各子 Action が `target_l_pairs`・対象 ID 群・`balance_ratio` / trace symmetry・exit gate を必須に持ち、その総和で親の収束を判定する。

## 6. 既知の検出事項（Phase 1-2 で解消対象）
- L4↔L9 片肺（確証 P1×2）: NFR 23ID→観点2個 / IF-05 個別 trace 欠落 → Phase 2 で TV/ST/TR 追補 + 再凍結。
- 根本原因: 設計ID↔テスト trace の対称性を ID 粒度で機械検出する detector 不在 → ワークフロー改善（`helix doctor check_pair_trace_symmetry` 相当）として Forward 新設。
- 未検証ペア（L1↔L14 / L3↔L12 / L5↔L8 / L6↔L7）: Phase 1-2 冒頭で同 ID-trace 対称チェックを掃き、真の片肺だけに scope を絞る（L6↔L7 は単体98ケースありで密度足り得る反例候補）。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-03 | V2 実装計画 Process 起票（6 Phase 確定 / 貫通要件 / 循環 / forward_return 宣言）。CLAUDE.md にスコープ・優先順位・循環を反映。 | PM (Opus) |
| 2026-06-03 | tl-advisor adversarial check = **条件付き推奨 / P0 なし / P1×3**。P1 反映: ①§3.2 に Phase4 DB entry 条件（観測→D-DB/D-CONTRACT→migration/rollback→pair test、escalation gate）②§3.2 に Phase5 Troubleshoot routing（Recovery/Incident/Refactor へ、または非 workflow step 明記）③§1.3・CLAUDE.md に「監査スコープ=全体 / 編集範囲=allowed_files 準拠」を明文化。契約 P1: §5 に closure 判定を子 Action へ分解（target_l_pairs / balance_ratio / exit gate）。plan_validator / plan_lint --strict-frontmatter PASS。 | PM (Opus) |
| 2026-06-08 | **Phase 3 着手の誤フレーミング → 是正**（/goal「1と2の完遂」）。当初 Phase3 着手を「detector fail-close gate化（機能実装）」として起票（[[add-feature-2026-06-08-detector-failclose-ci-gate]]、TL round1→round2 approve まで実施）。**ユーザー指摘で誤りを認識**: roadmap §3 の Phase3 主眼 = **「L7 単体テスト実施」= 検証実走**であり、機能実装ではない。Phase2 は「設計 + テスト設計」の凍結で**検証実行は未実施**（＝検証は Phase3 の仕事）。**実測**: coverage_layer = L4 290 / L5 105 / L6 65 / excluded 89 / unknown 0（全機能 L6 ではなく層別被覆）。L6↔L7 は設計 balanced（FN 88 ↔ UT 88）だが**検証実行が片肺**（実テスト trace される UT = 31/88、58 untraced）。→ **是正**: detector-gate を「自動化サブ項目」として park（PLAN/TL approve は資産保持）。**Phase3 着手を「L7 検証実走の片肺解消」に再定義**（① 58 untraced UT を verify-first で実体確認 → ② 真 gap の単体テスト実装・実走 → ③ L6↔L7 を検証実行まで閉じる）。Codex se 実装は着手前に停止（git 未書き込み）。 | PM (Opus) |
| 2026-06-09 | **DF-G7-MISSING-001 closure**。真 missing 4 件（UT-WSC-07 / 08 / 10 / 11）を `cli/tests/test-wsc-hooks-pretooluse-agent-and-design-guards.bats` で L7 単体テスト実装し、`g7-test-anchor-map.yaml` に anchor 登録。G7 subcheck 実走で `anchored=88/88`、`exec_pass=88/88`、`missing=0`、`unanchored_but_exists=0` を確認。追加検証: `bats cli/tests/test-wsc-hooks-pretooluse-agent-and-design-guards.bats` PASS、`python3 -m pytest cli/lib/tests/test_g7_subcheck.py cli/lib/tests/test_vg_overview.py -q` PASS。L1〜L6 バランス監査: `trace_symmetry` は L1-L14/L3-L12/L5-L8/L6-L7 clean、`registry_design_coverage` は active_entries=551 / L6_required=67 / findings=0。L7/L8 定義を再確認し、L7=実装の谷（単体テスト実装・本体実装・単体テスト実施）、L8=結合テストで固定。Codex/ClaudeCode 差分: Claude の `pretooluse-design-doc-web-search-guard.sh` と同等条件を Codex post-validation に追加。`helix-codex` 終了後、`docs/adr/ADR-*.md` の新規/変更に WebSearch/WebFetch 証跡が無い場合は fail-close、`HELIX_CODEX_DESIGN_WEB_EVIDENCE=<path[:path...]>` で transcript/evidence を渡す。検証: `python3 -m pytest cli/lib/tests/test_codex_post_validation.py -q` PASS、`bats cli/tests/test-helix-codex-write-audit.bats` PASS。Web evidence: ISO/IEC 25010:2023 は品質モデルを要件定義の網羅性検証・テスト目的・受入基準に使えると明示、NASA SE Handbook は要求・設計・テスト計画間の bidirectional traceability 維持を要求、OpenTelemetry は logs/metrics/traces と stable schema の structured logs を運用分析基盤として推奨。 | Codex |
| 2026-06-09 | **HELIX gate state closure + L4-L9 semantic detector closure**。`helix gate G6.5 --static-only --readiness-mode skip` → `G6.7` → `G6.9` → `G7` を順次実行してすべて PASS。`.helix/phase.yaml` 上は parser dotpath で `gates.G6.5/G6.7/G6.9.status=passed`、`gates.G7.status=passed`。再確認 dry-run でも G6.7/G6.9/G7 の前提未通過エラーなし。G7 実行時の `feedback_hook` は当初 `plan_id` 不明で skip したが、`.helix/phase.yaml plan_id=process-2026-06-08-verification-forward-gate` を設定し、`feedback_hook.resolve_plan_id()` が同 PLAN を返すことを確認。実 Codex TL 5軸 feedback 生成は次回 actual gate 実行時に発火する。復帰後の current-state 再監査では `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --json` が `overall_clean=true` / G7 `anchored=88`・`exec_pass=88`・`missing=0`、`trace_symmetry` は L1-L14 / L3-L12 / L4-L9 / L5-L8 / L6-L7 clean。L4-L9 は `orphan_test=0`、`semantic_excluded_orphan=18`、balance0.67。`registry_design_coverage` findings=0。 | Codex |
| 2026-06-03 | **Phase 1 実行**（/goal「Phase1 完遂」）。**重要発見=Phase1 ペアは健全**（L1↔L14 / L3↔L12 とも、当初の「両ペア片肺」は false positive 3 連発だった。実在片肺 L4↔L9 は Phase2）。詳細 [[reverse-2026-06-03-l1-l3-trace-hardening]]。**成果物**: ①検証戦略 doc 正本化 [[verification-strategy]]（Master Verification Strategy、ID universe / 双方向 trace / gap 指標 / false-positive 教訓 / 定量vs定性判定基準）②detector refine [[poc-2026-06-03-trace-symmetry-detector]]（cli/lib/trace_symmetry.py、L3↔L12 uncovered=0 / L4↔L9 片肺検出 を機械再現、pytest 3 passed）③L0→L1 遷移規律 [[planning-to-requirements-transition]]（PdM owner、Forward 内 transition discipline）④反芻機構 [[workflow-self-evaluation]]（skill/agent/command 発火評価 + 観測済改善点の要件 input）⑤GitHub HELIX-native 運用 [[github-operations]]（Forward 逸脱→Issue、CI↔gate 紐づけ）。**TL 一括諮問**（検証ロードマップ/L0→L1/GitHub）= 条件付き推奨 P0 なし。**carry**: L4↔L9 片肺(Phase2) / L1 verification_layers 契約+G1再凍結 / L0 inventory 数値 stale / detector L5-L6 抽出 / GitHub(ADR-029 reconcile・4-branch 統合・ISSUE_TEMPLATE・release-please)。 | PM (Opus) |

## 4.1 Completion audit（2026-06-09 Codex）

Goal「要件定義漏れ洗い出し / L1〜L6 設計・テスト設計バランス / Codex-guard 差分 / 自動登録・検出・改善 loop」を、現行 evidence で分解した監査結果。

| 要求 | 現在判定 | Evidence / next |
|---|---|---|
| 指定 L0〜L14 flow へ完全対応 | 部分達成 | §3 で `L6=機能設計+単体テスト設計`、`L7=実装+単体実施+coverage closure`、`L8=結合` を固定。HELIX 正本と整合。 |
| L1〜L6 の設計 / テスト設計バランス | machine-clean | `trace_symmetry`: L1-L14 / L3-L12 / L5-L8 / L6-L7 は coverage100%・missing_pair0・orphan0。`registry_design_coverage`: active_entries=551、l6_required=67、unknown=0、wrong_layer=0、findings=0。 |
| L4↔L9 の総合設計 pair | semantic evidence 付きで detector clean / G9 実行 carry | coverage100% / missing_pair0 / orphan_test0。ST→TV→L4 の 2 段 trace 18件は `semantic_excluded_orphan=18` として機械出力化済み。balance0.67 は補助指標。残 carry は G9 の ST anchor / 総合テスト実行 gate。 |
| L7 単体実装 / 実施 / coverage closure | 達成（advisory） | G7 subcheck: anchored=88/88、exec_pass=88/88、missing=0、unanchored_but_exists=0。`DF-G7-MISSING-001` は closure。 |
| HELIX gate state として L6 まで通過 | 達成（static gate） | 2026-06-09 Codex で `helix gate G6.5/G6.7/G6.9/G7 --static-only --readiness-mode skip` を順次実行し pass。`.helix/phase.yaml` は parser dotpath 上 `gates.G6.5/G6.7/G6.9.status=passed`、`gates.G7.status=passed`。再 dry-run でも G6.7/G6.9/G7 の前提エラーなし。`feedback_hook` の plan 解決は `.helix/phase.yaml plan_id=process-2026-06-08-verification-forward-gate` で接続済み。`HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor --gate --json` 実測は pass=33 / fail=0 / warn=103、`VG-overview pre-push` advisory なし。 |
| requirement_drift detector | MVP 実装 / fail-close 接続済み / L6 drift 0 | `docs/v2/L6-functional-design/requirement-drift-機能設計.md` と `docs/v2/L7-test-design/requirement-drift-単体テスト設計.md` で FR 縦 trace の MVP scope、Output Contract、RD-UT-01〜17（G7 inventory の `UT-*` には未昇格）を固定。`cli/lib/requirement_drift.py`、`helix doctor check_requirement_drift --json`、`VG-overview.required_clean.requirement_drift` を実装し、`helix doctor --gate` / `helix push --gate` の `G-vg-overview` が L6 requirement drift を block する。2026-06-09 実リポジトリ evidence は `requirements=31` / `design_links=31` / `blocking_findings=0` / `advisory_findings=0`。mtime stale は `--check-stale` 明示時のみ advisory 集計する。 |
| ClaudeCode では効くが Codex で効かない guard | 達成 | Claude `pretooluse-design-doc-web-search-guard.sh` と同等の設計 doc Web evidence check を Codex post-validation に追加。ADR 変更は WebSearch/WebFetch 証跡なしなら fail-close、証跡ありなら pass。 |
| HELIX DB 自動登録 / トラブル検出 / 改善 feedback loop | 部分達成 / gate 未接続 carry | 既存 `agent_slots`、`harness_check_events`、`hook_events`、`feedback`、`events/metrics`、`drift-check`、`harness_monitor.record_event` が存在。2026-06-09 Codex で `helix harness feedback-loop` を top-level 配線し、route / learning / PLAN draft / PR candidate を生成。実行時に feedback-loop snapshot を既存 `events` / `metrics` へ append し、`feedback` が空なら missing feedback input を既存 `feedback` table に自動登録する。最新 snapshot schema は `plan_candidates` を PLAN draft 候補の正式キーとし、current read-only evidence は route_candidates=20、learning_candidates=8、plan_candidates=20、pr_candidates=8、VG deferred=4。残 carry は gate / detector 直接変更を別 PLAN + TL 確認に分離する点。schema 変更は escalation gate 対象。 |
| Web 検索使用 | 達成 | 2026-06-09 Codex で公式一次情報を再確認。ISO/IEC/IEEE 12207:2026、ISO/IEC/IEEE 29148:2018（2026-02-16 時点で改訂予定 stage）、IEEE 1012 / P1012、NIST SP 800-218 SSDF official pages を L0-L14 / L1-L6 / V&V / secure SDLC evidence として使用。 |

### 4.1.1 External standard evidence（2026-06-09 Codex WebSearch / WebFetch）

2026-06-09 Codex で公式一次情報を再検索し、以下の status / scope を再確認した。

| Source | Official URL | Confirmed version / date | HELIX mapping |
|---|---|---|---|
| ISO/IEC/IEEE 12207:2026 | https://www.iso.org/standard/90219.html | Edition 2, Published, publication date 2026-04, stage 60.60 | Software life cycle processes cover conception, development, operation, support, retirement, and process improvement. HELIX L0-L14 maps this into the local Forward lifecycle and keeps L14 operation learning / improvement explicit. |
| ISO/IEC/IEEE 29148:2018 | https://www.iso.org/standard/72089.html | Edition 2, 2018-11; stage 90.92 to be revised as of 2026-02-16 | Requirements engineering specifies required processes, information items, required contents, and formats. HELIX L1-L6 plus requirement_drift uses this as evidence for requirements-to-design trace and information item closure, while the revision status is tracked as watch evidence rather than a current contract change. |
| IEEE 1012 / P1012 V&V | https://standards.ieee.org/ieee/1012/12536/ | P1012 Active PAR; Standard for System, Software, and Hardware Verification and Validation | V&V determines whether work products conform to requirements and satisfy intended use / user needs through analysis, review, inspection, assessment, and testing. HELIX pair gates L6-L7 through L1-L14 use this as evidence for paired verification rather than design-only closure. |
| NIST SP 800-218 SSDF v1.1 | https://csrc.nist.gov/pubs/sp/800/218/final | Final, Version 1.1, date published 2022-02 | Secure software development practices should be integrated into each SDLC implementation. HELIX keeps security requirements, gate evidence, and recurrence feedback in scope for L1-L6 design and L7-L14 execution closure. |

外部標準から見た現在判定: L6 focus は `overall_clean=true` でよいが、12207/1012 が求める full lifecycle / V&V の観点では L8/L9/L12/L14 の実行 gate が残るため、`--strict-full-flow` では `overall_clean=false` として deferred 4 件を維持する。29148 の改訂予定は L1-L6 要件情報項目の watch 条件として保持し、SSDF はセキュリティ要件と再発防止 feedback を L1-L14 から外さないための外部 control として扱う。

### 4.1.2 Completion guard（goal 完了扱いの禁止条件）

L6 focus の `overall_clean=true` は「L0-L6 の要求・設計・テスト設計バランスが local evidence 上 clean」という意味に限定する。Goal 全体を complete 扱いしてよい条件ではない。

Goal completion は、少なくとも次を満たすまで禁止する。

| Guard | Required closure |
|---|---|
| strict full-flow | `helix doctor check_vg_overview --strict-full-flow --json` の `overall_clean=true` |
| right-arm execution gates | G8 / G9 / G12 / G14 の execution gate が implemented かつ pass |
| CI connection | `helix doctor --gate` / `G-vg-overview` が CI または同等の自動 gate surface に接続済み |
| L2-L10 | `ui_absent` waiver が継続妥当、または FE/UI 追加時に L2↔L10 detector / UX gate が実装済み |
| DB feedback loop | `plan_candidates` / `pr_candidates` が生成されるだけでなく、採用された改善が PLAN / PR / gate evidence へ戻る運用が確認済み |

現時点では strict full-flow が `overall_clean=false`、`deferred_count=4`（G8/G9/G12/G14）であるため、goal は active のまま扱う。

### 4.2 Phase4 DB loop 復帰棚卸し（2026-06-09 Codex）

定義修正後の復帰として、schema 変更なしで既存 DB / CLI 資産を棚卸しした。

| 観点 | 現在地 | 判定 / next |
|---|---|---|
| 自動登録 | `agent_slots`、`hook_events`、`harness_check_events`、`automation_runs` は蓄積済み。`helix harness status --json` で active slot / running task / warning を読める。`helix harness feedback-loop` は snapshot を既存 `events` / `metrics` に append する。 | top-level `helix harness` 配線済み。schema migration なし。 |
| トラブル検出 | stale lock release、`automation_runs.id=16` の長期 `running`、過去 `hook_events` の `drift_check_db_* warn` を DB から観測できる。 | `helix route` は `long_running_task -> auto_run(P1)`、`drift(schema) -> Reverse(P1)`、`regression_dev -> Recovery(P3)` を返せる。検出結果を route 入力へ自動変換する adapter が不足。 |
| 改善 feedback loop | `helix log feedback` と `helix observe log/metric` は存在する。Codex 復帰後の実 DB では `events` / `metrics` / `verify_runs` / `feedback` すべてに入力あり。`helix learn` は成功 task_run recipe 生成が中心。 | no-schema aggregator 実装済み。最新 snapshot は route candidate / PLAN draft candidate / PR candidate を出す。`missing_feedback_input` は `feedback-loop` 実行時の自動登録で解消し、次 snapshot では `feedback_pattern` として learning 候補化。gate/detector 直接変更は別 PLAN + TL 確認。 |
| schema 変更 | `detector_runs`、`event_envelope`、`failure_log` など既存 table はあるが、本棚卸しでは schema migration は行わない。 | DB schema 変更、migration、rollback 設計は Phase4 Action として D-DB/D-CONTRACT 追補後に escalation gate を通す。 |

Phase4 の最小実装単位は、DB schema を変えない `harness feedback-loop` 相当の read + append-light aggregator とする。入力は既存 `harness_check_events` / `hook_events` / `automation_runs` / `feedback` / `events` / `metrics` / `verify_runs`、出力は route candidate と learning candidate の JSON。実行時に snapshot 要約だけを `events` / `metrics` に append する。自動実行・状態変更・gate/detector 変更は行わない。

2026-06-09 Codex で上記 no-schema aggregator を実装済み。`helix harness feedback-loop --json` を top-level に配線し、既存 DB 入力から route candidate / learning candidate / PLAN draft candidate / PR candidate を出す。JSON schema の正式キーは `plan_candidates`。current read-only evidence では route_candidates=20、learning_candidates=8、plan_candidates=20、pr_candidates=8、`vg_overview.deferred_count=4`、`plan_draft_candidates` key は存在しない。`missing_feedback_input` は自動 feedback 登録後の次 snapshot で消え、`feedback_pattern` として learning / PR candidate 化する。安全条件は `schema_migration=false`、`auto_apply=false`、`writes_detector_or_gate=false`。

### 4.2.1 Deferred gate adoption queue（2026-06-09 Codex）

`helix harness feedback-loop --json --days 30` の `vg_overview:full_flow_deferred_execution_gate` 候補は、現時点では自動適用しない。以下を PLAN / PR / gate evidence へ戻す採用待ち queue として保持する。採用時は各 gate の design/test-design/anchor/execution evidence を該当 L-pair へ戻し、`helix doctor check_vg_overview --strict-full-flow --json` の `overall_clean=true` で閉じる。

| Pair | Gate | Feedback-loop candidate summary | Adoption target |
|---|---|---|---|
| L5-L8 | G8 | L5-L8 remains deferred for G8; implement G8 integration-test execution gate | L8 結合テスト execution gate / L5 詳細設計↔結合テスト設計 closure |
| L4-L9 | G9 | L4-L9 remains deferred for G9; implement G9 system-test execution gate | L9 総合テスト execution gate / L4 基本設計↔総合テスト設計 closure |
| L3-L12 | G12 | L3-L12 remains deferred for G12; implement G12 acceptance-test execution gate | L12 受入テスト execution gate / L3 要件定義↔受入テスト設計 closure |
| L1-L14 | G14 | L1-L14 remains deferred for G14; implement G14 operational-learning execution gate | L14 運用学習 / 運用改善 execution gate / L1 要求定義↔運用テスト設計 closure |

この queue は completion guard の DB feedback loop 条件に対する採用待ち evidence であり、採用完了ではない。`plan_candidates` / `pr_candidates` が生成されているだけの状態では goal complete にしない。安全条件は引き続き `schema_migration=false`、`auto_apply=false`、`writes_detector_or_gate=false` とし、gate / detector 本体変更は別 PLAN + TL 確認で扱う。

### 4.2.1.1 Deferred gate PLAN materialization draft（2026-06-09 Codex）

以下は `candidate_generated` から `plan_materialized` へ進めるための draft である。現 handover では gate / detector 本体変更は行わず、実装着手時は各 PLAN を正式起票し、allowed_files / acceptance / rollback を task-plan または PLAN frontmatter に写す。

| Plan draft ID | Gate | Allowed implementation files | Acceptance evidence | Rollback / safety |
|---|---|---|---|---|
| `PLAN-G8-INTEGRATION-EXECUTION-GATE` | G8 | `cli/lib/vg_overview.py`, `cli/helix-doctor`, `cli/lib/tests/test_vg_overview.py`, `cli/tests/helix-doctor-json.bats`, `docs/v2/L8-test-design/` | L5-L8 が `execution_gate_not_implemented` を返さず、結合テスト execution evidence と L5↔L8 trace closure で pass。`helix doctor check_vg_overview --strict-full-flow --json` から G8 deferred が消える。 | DB schema migration なし。既存 L6 focus `overall_clean=true` と G7 88/88 を壊さない。問題時は G8 strict enforcement を advisory deferred へ戻す。 |
| `PLAN-G9-SYSTEM-EXECUTION-GATE` | G9 | `cli/lib/vg_overview.py`, `cli/lib/trace_symmetry.py`, `cli/helix-doctor`, `cli/lib/tests/test_vg_overview.py`, `cli/lib/tests/test_trace_symmetry.py`, `docs/v2/L9-test-design/` | L4-L9 semantic evidence が維持され、総合テスト execution evidence で G9 pass。`semantic_excluded_orphan=18` は根拠付き補助指標として残し、G9 deferred が消える。 | ST→TV→L4 semantic trace を破壊しない。semantic exclusion を消す場合は L4/L9 evidence を同時更新する。 |
| `PLAN-G12-ACCEPTANCE-EXECUTION-GATE` | G12 | `cli/lib/vg_overview.py`, `cli/helix-doctor`, `cli/lib/tests/test_vg_overview.py`, `cli/tests/helix-doctor-json.bats`, `docs/v2/L12-test-design/` | L3-L12 受入テスト execution evidence が存在し、L3 要件定義↔受入テスト設計 closure で pass。strict full-flow から G12 deferred が消える。 | 受入基準・要件 ID の再解釈は行わない。要件変更が必要なら L3 へ interrupt / escalation。 |
| `PLAN-G14-OPERATIONAL-LEARNING-GATE` | G14 | `cli/lib/vg_overview.py`, `cli/helix-harness`, `cli/lib/harness_monitor.py`, `cli/lib/tests/test_vg_overview.py`, `cli/lib/tests/test_harness_monitor_unit.py`, `cli/tests/test-helix-harness-feedback-loop.bats`, `docs/v2/L14-test-design/` | L1-L14 運用テスト / 運用学習 evidence が HELIX DB events / metrics / feedback に戻り、G14 pass。feedback_closed state で adoption result が再発検出へ接続される。 | 自動適用は禁止。`schema_migration=false`, `auto_apply=false`, `writes_detector_or_gate=false` の候補状態から gate 実装状態へ進める場合は別 PLAN + TL 確認。 |

PLAN materialization draft が存在しても、`gate_implemented` / `gate_passed` / `ci_enforced` / `feedback_closed` を満たすまでは completion guard は解除しない。

### 4.2.2 Additional discovered improvement backlog（2026-06-09 Codex）

ユーザー goal の「定義に含まれていないができることも探し出す」に対し、現時点の read-only / no-schema 棚卸しから次の改善候補を採用待ち backlog として保持する。いずれも自動適用せず、採用時は PLAN / PR / gate evidence へ戻す。

| Candidate | Source evidence | Adoption condition |
|---|---|---|
| Route adapter for feedback-loop candidates | `helix harness feedback-loop` は route / learning / PLAN / PR candidates を出すが、検出結果を `helix route` 入力へ自動変換する adapter が不足。 | `long_running_task` / `drift` / `regression_dev` を route input として安定 JSON 化し、dry-run と DB append を分離した PLAN を起票する。 |
| L2-L10 ui_absent unskip detector | 現在は `ui_absent` waiver で not_applicable。UI / docs site / dashboard 追加時は L2 画面要求↔L10 UX gate が必要。 | FE/UI 追加を検出する条件を `unskip_required_when` と同期し、L2-L10 detector / UX gate を別 PLAN で実装する。 |
| Feedback candidate adoption materialization | `plan_candidates` / `pr_candidates` は生成済みだが、採用された改善が PLAN / PR / gate evidence へ戻る運用は未完了。 | candidate -> PLAN draft -> PR -> gate evidence の trace を DB / docs で閉じ、completion guard の DB feedback loop 条件を満たす。 |
| CI gate surface hardening | `helix doctor --gate` / `G-vg-overview` の接続は文書・Bats で固定済みだが、CI equivalent の常時実行は completion guard に残る。 | 対象 CI / local required gate surface を決め、strict full-flow ではなく L6 focus gate と full-flow carry を分離して表示する。 |
| Schema-backed detector history | `detector_runs` / `event_envelope` / `failure_log` など候補 table はあるが、本棚卸しでは schema migration を避けた。 | D-DB / D-CONTRACT / rollback を先に追補し、migration escalation gate を通した後に detector history を採用する。 |

この backlog は「できること」の発見記録であり、採用完了ではない。`schema_migration=false`、`auto_apply=false`、`writes_detector_or_gate=false` を維持し、gate / detector 本体や DB schema の変更は別 PLAN + TL 確認で扱う。

## 8. 次アクション
1. tl-advisor で本 roadmap の adversarial check（Phase 境界・駆動耐性・forward_return・公開 API/harness 契約の保全）。
   - **drive 値の注記**: VALID_DRIVES に Forward/process 統括を表す値がなく、deprecated `scrum` の移行先 `discovery` を暫定採用（既存 process PLAN 実例も discovery）。駆動耐性の観点で `forward`/`process` drive 値の新設是非は Phase 2 ワークフロー改善の検討対象。
2. Phase 1 着手: L0 概要確認 → 未検証ペアの ID-trace 対称チェック掃き → document カバレッジ scope 確定。
3. Phase ごとに Action Plan（子）を起票し `contains_action_plans` に追記（`parent_process` で本書を逆参照）。
