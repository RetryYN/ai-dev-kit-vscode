---
plan_id: process-2026-06-03-v2-implementation-roadmap
title: "Process Plan: V2 実装計画 — HELIX v2 PM型TDDベース生体モデルワークシステム開発ハーネス 開発工程"
plan_scope: process
workflow_chain: "Phase1(L0確認→L1/L3+対ペア) → Phase2(L4-L6+対ペア) → Phase3(L7実走+自動化+Python化本体改修) → Phase4(HELIX DB機能拡張) → Phase5(L8-テスト実走+トラブルシュート強化) → Phase6(テストプロジェクト透過フルrun+ボトルネック改善)"
kind: planning
layer: L0
drive: discovery
status: draft
created: 2026-06-03
owner: PM
contains_action_plans:
  - docs/plans/reverse/reverse-2026-06-03-l1-l3-trace-hardening.md
  - docs/plans/discovery/poc-2026-06-03-trace-symmetry-detector.md
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
| 2026-06-03 | **Phase 1 実行**（/goal「Phase1 完遂」）。**重要発見=Phase1 ペアは健全**（L1↔L14 / L3↔L12 とも、当初の「両ペア片肺」は false positive 3 連発だった。実在片肺 L4↔L9 は Phase2）。詳細 [[reverse-2026-06-03-l1-l3-trace-hardening]]。**成果物**: ①検証戦略 doc 正本化 [[verification-strategy]]（Master Verification Strategy、ID universe / 双方向 trace / gap 指標 / false-positive 教訓 / 定量vs定性判定基準）②detector refine [[poc-2026-06-03-trace-symmetry-detector]]（cli/lib/trace_symmetry.py、L3↔L12 uncovered=0 / L4↔L9 片肺検出 を機械再現、pytest 3 passed）③L0→L1 遷移規律 [[planning-to-requirements-transition]]（PdM owner、Forward 内 transition discipline）④反芻機構 [[workflow-self-evaluation]]（skill/agent/command 発火評価 + 観測済改善点の要件 input）⑤GitHub HELIX-native 運用 [[github-operations]]（Forward 逸脱→Issue、CI↔gate 紐づけ）。**TL 一括諮問**（検証ロードマップ/L0→L1/GitHub）= 条件付き推奨 P0 なし。**carry**: L4↔L9 片肺(Phase2) / L1 verification_layers 契約+G1再凍結 / L0 inventory 数値 stale / detector L5-L6 抽出 / GitHub(ADR-029 reconcile・4-branch 統合・ISSUE_TEMPLATE・release-please)。 | PM (Opus) |

## 8. 次アクション
1. tl-advisor で本 roadmap の adversarial check（Phase 境界・駆動耐性・forward_return・公開 API/harness 契約の保全）。
   - **drive 値の注記**: VALID_DRIVES に Forward/process 統括を表す値がなく、deprecated `scrum` の移行先 `discovery` を暫定採用（既存 process PLAN 実例も discovery）。駆動耐性の観点で `forward`/`process` drive 値の新設是非は Phase 2 ワークフロー改善の検討対象。
2. Phase 1 着手: L0 概要確認 → 未検証ペアの ID-trace 対称チェック掃き → document カバレッジ scope 確定。
3. Phase ごとに Action Plan（子）を起票し `contains_action_plans` に追記（`parent_process` で本書を逆参照）。
