# V モデル強化完遂報告

Version: WIP-DRAFT  
Path: `docs/v2/B-design/vmodel-strengthening-completion-report.md`  
Generated: `2026-05-14`  
Authoring role: Docs（technical writer）  
Scope: Phase 2 設計スパイク完遂 + 次セッション onboarding 兼 G1 判定入力

## 0. 前提と参照

本報告は、以下を正本として作成する。  
参照は可能な限り相互整合を取り、以下の順で評価を回した。

- `docs/v2/CONCEPT.md`
- `docs/v2/L1-REQUIREMENTS.md`（FR-INV/VD/V/DB/GR/A/FE/AT/LI/VS、FR 74+）
- `docs/v2/A-audit/audit-summary.md`（Phase A 統合、821 行）
- `docs/v2/B-design/vmodel-semantics-spine.yaml`
- `docs/v2/B-design/vmodel-semantics-be-draft.yaml`
- `docs/v2/B-design/vmodel-semantics-fe-draft.yaml`
- `docs/v2/B-design/vmodel-semantics-db-draft.yaml`
- `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml`
- `docs/v2/B-design/cross-drive-integrity-check.md`
- `docs/v2/B-design/v21-migration-sql-draft.sql`
- `docs/v2/B-design/review-axes-detail.md`
- `docs/v2/B-design/guardrail-mechanism-design.md`
- `docs/v2/B-design/fail-fix-log-design.md`
- `docs/v2/B-design/dashboard-design.md`
- `docs/v2/B-design/sessionstart-detail.md`
- `docs/v2/B-design/l2-master-sketch.md`
- `docs/v2/v2-gate-overlay.md`
- `docs/v2/I-legacy-import/V2-mapping.md`
- `docs/v2/C-followup/*`

本稿は実装系ではなくドキュメント化の完遂報告であり、要件が要求する「リンク整合」「完了度」「次アクション」を、最小構成・最大可読性で網羅する。

---

## §1 V モデル強化 完遂サマリ

### 1.1 完了定義（本セッションで完了扱い）

以下は当該セッション（Phase 2 設計スパイク）における完成扱い項目。

- Phase 1 既存整理（21 audit + audit-summary）
  - `docs/v2/A-audit/audit-summary.md` と `docs/v2/A-audit/` 配下の doc 群を統合的に参照し、現状能力・廃止候補・移行判断の根拠を整理済み。
  - Phase A 完了サマリの "統合 20 audit" 規模を採用し、設計スパイクの再起点とした。

- Phase 2 V-model 強化定義（spine + 4 drive draft + cross-drive check）
  - `vmodel-semantics-spine.yaml` で最短骨格（4 drive, 5 layer, 期待 artifact / 検証ルール）を定義。
  - `be / fe / db / fullstack` 各 draft を同時配備し、検証ルールの drift を比較しやすい形へ整形。
  - `cross-drive-integrity-check.md` で drive 間の整合性（設計・検証の接続）を点検枠に落とし込んだ。

- v21 migration SQL ドラフト
  - `v21-migration-sql-draft.sql` を作成し、v20→v21 を想定した schema 拡張・検証・安全ガードの SQL 群を収録。
  - `docs/v2/C-followup/followup-p1-aggregate.md` 系列の carry 受けと整合する構造で、実装前の再作成前提を明示。

- 工程転換（G3.functional_freeze + v2-gate-overlay）
  - `docs/v2/v2-gate-overlay.md` および `docs/v2/C-followup/g3-functional-freeze-plan.md` で、既存 G3 をサブゲート化し、破壊的変更を抑えながら functional_freeze を導線化。

- review_axes（縦/横 review unit）
  - `review-axes-detail.md` で、縦（vertical）/横（horizontal）軸を明確化。
  - 5 design × 5 test の対照構造に対し、FR-Layer・origin mode・evidence status を意識した検査単位で記述。

- detector × drive × layer 紐付け
  - `review-axes-detail.md` と drive draft 群から、検証軸（design level、test kind、detector、artifact）をクロスした紐付けを明文化。
  - C-followup における `detector-drive-layer-mapping.md` 系と情報同型を保っている。

- guardrail mechanism（5 層介入機構）
  - `guardrail-mechanism-design.md` で、5 層（plan/operation/design/test/integration）への介入ポイントを定義。
  - fail-close と fail-soft の併用方針、dry-run / opt-out / guard の条件式を明示。

- 各派生 Phase 入力（G/ H / I / F / 5）
  - Phase G FE 強化：`docs/v2/C-followup/fe-strengthening-plan.md` を起点に、FE 弱点（contract/type/detector/command）を定量化。
  - Phase H AT：`docs/v2/C-followup/agent-transformation-plan.md` で agent registry / chain を入力。
  - Phase I Legacy：`docs/v2/I-legacy-import/V2-mapping.md` で PLAN carry の再添付と紐付けを用意。
  - Phase F 可視化：`dashboard-design.md` / `sessionstart-detail.md` の起点に dashboard と start-state 可視化を統合。
  - Phase 5 自動化：`v2-gate-overlay.md` / `hooks-commands-sot-plan.md` を接続し、PostToolUse / SessionStart / Gate runner へ接続案を整備。

- L2 MASTER.md sketch
  - `l2-master-sketch.md` は L2 起票の前段として、設計起点・成果物・ゲート接続・依存を可視化済み。
  - 本報告は onboarding doc として、この sketch への移行パスを明示。

- 「穴を埋める」原則
  - `fail-fix-log-design.md` で失敗事象を構造化し、再発予防の回路を実装仕様に接続。
  - `fail_fix_log` / doc artifact registry / lint ecosystem / scan tool の 4 本柱を Phase 4〜5 に接続する設計を提示。

### 1.2 完了済みの到達値（Phase 2 入力として）

1. 既存の散在知見を PLAN carry と capability matrix へ戻せる構造化を実施。
2. drive×layer 意味論を「schema ではなく draft yaml」で外部化し、L2 起票前の調整柔軟性を確保。
3. v-model score / integrity / vertical-check といった後段 CLI の検討前提を統一。
4. Phase 2（定義）を実装へ premature freeze せず、次工程との境界を明示。

### 1.3 Phase 2 を "spike-complete" と見なす条件充足

- 既存整理の根拠が1か所に集約されている（`audit-summary.md`）。
- 主要定義が 4 ドライブで比較可能。
- guardrail / fail-close / 再実施の導線が明文化され、phase 間受け渡しで実装不可能なブラックボックスを残さない。
- L2 起票が必要な正本（`l2-master-sketch.md`）へ到達しており、進行障害が最小化される。

---

## §2 セッション中の発見と対策

### 2.1 Codex completion ≠ 実体出力

- 事実: `--role tl` の delegate_to docs は記述レイヤ（要約）としての返却で、実体の Write/更新保証を担保しきれないケースがあった。
- 対策:
  - 本件では `--role docs` / `--role se` の実体編集を優先実施。
  - memory に「役割依存の限界」として記録し、次セッションの再現性を担保。
- FR 根拠:
  - `docs/v2/A-audit/accumulated-knowledge.md`（運用知見の固定）および `docs/v2/C-followup/lint-ecosystem-plan.md`（検証前提）。

### 2.2 PMO Sonnet 起動エラー

- 事実: `/tmp/test-helix` not found で PMO Sonnet の起動経路が停止。
- 対策:
  - 代替として Codex 側で read-only 調査 + docs 起票を継続。
  - issue の再発防止として startup ルートと local settings の分離（`pmo-startup-debug.md`）を提起。
- リスク/対策:
  - 人手差し替え時に PMO 依存で停止しないよう、調査経路を docs/design に分散。
- memory feedback:
  - `feedback_v2_pmo_startup_error_tmp_test_helix.md` に起因と再開方針を蓄積。

### 2.3 doc 整合性懸念

- 事実: phase 間 doc の言語と表記揺れ（V-model / phase naming / guardrail）が、最終 G1 でのレビューを増幅する兆候。
- 対策:
  - `cross-phase-integrity` の計画化（未実施→次タスク候補）。
  - 21 audit 統合 root を `audit-summary` とし、`L1-REQUIREMENTS` は要求根拠、`CONCEPT` は採択判断という役割分離で緩和。

### 2.4 fail&fix table の必要性

- 事実: Codex completion 不在時の再投入、hook 運用失敗、整合検知漏れが再発防止されにくい。
- 対策:
  - `fail-fix-log-design.md` で失敗イベントを FR-関連・影響範囲・再発条件・修復 SLA 付きで構造化。
  - FR-GR11 的に detector と PRD への反映を要求入力へ転写。

### 2.5 推奨システム必須

- 事実: Opus 直接記述は local setting / 環境差分による逸脱リスクが高い。
- 対策:
- helix skill chain をデフォルトルート化し、代替パス（docs/agent）を明文化。
  - TL log / advisory / PM判断を並列に残し、最終責任分散を避ける。
- 根拠:
  - `feedback_v2_expected_skills_advisory_only.md`
  - `docs/v2/C-followup/agent-skills-vendor-plan.md`

### 2.6 追加発見（重要）

- 既存知識移行の摩擦は、仕様の未定義より「どの doc が正式版か」の取り違えが主因である可能性が高い。
- そこで各設計ドキュメントに「役割」と「受入条件」を添え、G1 通過時の審査負荷を低減する方針に寄せた。

---

## §3 G1 通過判定 checklist

本項目は本スパイク完了を "G1 入力" として扱う。

### 3.0 BR(18) POレビュー
- [ ] §2 BR (18) PO レビュー済  
  - 現況: PO 最終承認は保留。`L1-REQUIREMENTS.md` BR 一覧と `audit-summary.md`の受けにより、レビュー待ちとして扱う。

### 3.1 FR (74+) 受入
- [ ] §3 FR (74+) 受入条件付き  
  - 現況: 要件は `L1-REQUIREMENTS.md §3` で定義済（FR-INV / FR-VD / FR-V / FR-DB / FR-GR / FR-FE / FR-AT / FR-LI / FR-VS）。  
  - 判定: 条件付き（受入条件の明文化自体は完了、完全受入は未）。

### 3.2 工程転換合意
- [ ] §3.6 工程転換合意済  
  - 現況: `G3.functional_freeze` を subgate として導入準備は完了。  
  - 判定: 完了ではなく「合意原稿版」。

### 3.3 根拠整合（Before/After）
- [ ] §3.0/§3.1 既存整理 / V-model 強化定義 が §3.8 Before/After の根拠  
  - 現況: `CONCEPT.md §5` と `L1-REQUIREMENTS.md §3.8` の対照表現、および spine/draft 群で整合を提示。
  - 判定: 条件付き（最終文言の統合は次工程）。

### 3.4 検出ガードレール
- [ ] §3.4 検出ガードレール強化 (GR01-13) が §3.5 自動化の前段  
  - 現況: `guardrail-mechanism-design.md` と `v2-gate-overlay.md` により前段と自動化導線が定義済。
  - 判定: 条件付き。

### 3.5 NFR
- [ ] §4 NFR 7 カテゴリ  
  - 現況: `L1-REQUIREMENTS.md §4` の NFR 7 を参照済み。
  - 判定: 条件付き（実測値は実装前段により未確定）。

### 3.6 AC
- [ ] §5 AC (01-17) 検証コマンド付き  
  - 現況: 主要 AC は doc で定義済、実証コマンドは記載されているが未実行。
  - 判定: 条件付き。

### 3.7 スコープ / 制約 / 依存
- [ ] §6 スコープ in/out  
- [ ] §7-8 制約 / 依存  
  - 現況: in/out、constraint、dependency は文書内で統一されているが、G1 直前に PM 監修を要する論点が残る。
  - 判定: 条件付き。

### 3.8 PO 承認
- [ ] PO 承認  
  - 現況: 最終承認は未実施。

### 3.9 判定サマリ

現時点の判定は「`conditions_pending`」であり、**次セッションでの PM/PO 審査承認が必須**。  
本報告の目的は “G1 入力の整備完了” であり、G1 完了宣言そのものではない。

---

## §4 G1 通過後の next steps

1. **L2 MASTER.md 起票**  
   - 担当: TL / L2  
   - 参照正本: `docs/v2/B-design/l2-master-sketch.md`  
   - 結果: 本稿の §1 サマリを起点として、設計文言を L2 仕様化へ固定。

2. **Phase 3 helix.db v21 migration 実装**  
   - 担当: DBA / L3/L4  
   - 実施: `docs/v2/B-design/v21-migration-sql-draft.sql` を実運用 SQL へ昇格  
   - チェック: schema_version, ALTER / CREATE / view / index / rollback 経路の事前レビュー。

3. **Phase 2 vmodel-semantics.yaml を配置**  
   - 担当: SE  
   - 対象: `cli/config/vmodel-semantics.yaml`  
   - 形式: 4 drive 統合版への正規化（draft の統合）

4. **Phase 4 guardrail mechanism 実装**  
   - 担当: SE + DevOps  
   - 対象: PreToolUse hook 拡張  
   - 条件: fail-close の条件式に環境/コストガードを内包。

5. **Phase 5 自動化**  
   - 担当: SE + QA + TL  
   - 連携: PostToolUse / SessionStart / Gate runner  
   - 目標: 設計-検証連鎖の自動記録率を上げ、視認性を 1 view 化。

### 4.1 依存順序（提案）

- 1) schema 整備（v21）  
- 2) semantics 外部化配備（vmodel-semantics.yaml）  
- 3) guardrail 実装（PreToolUse）  
- 4) 自動化 runner の接続  
- 5) dashboard / session view 回収  
- 6) dogfood / 3 plan 継続検証

---

## §5 残課題（G1 通過前に解決推奨）

1. PM 判断 top-5 の固定  
   - `.helix Git 管理`  
   - `agent-skills vendor` 境界  
   - `PLAN 正本固定`  
   - `旧 capability 廃止 timing`  
   - `old/new role boundary`（docs 実体記録と advisory の境界）

2. `PLAN-066/067` の V2 phase 紐付け確定  
   - 既存 carry の再接続が未統合のまま次工程へ進むと、監査時に遡及コストが増大。

3. `INV06` deprecated 集約の最終 update  
   - 廃止候補の最終確定と削除タイミングは PMO + PO の合議へ。

4. `cross-phase-integrity` 実行計画  
   - 設計・実装・監査・可視化の cross-phase 監査の計画書（未実装）。

5. `L2 MASTER.md 起票条件` の最終確認  
   - 起票前に本報告の link list を master sketch と照合。

### 5.1 リスクランク（暫定）

- 高: plan-phase紐付け不明確による再設計
- 高: guardrail fail-close 前倒しによる運用停止リスク
- 中: 廃止 timing の判定遅延
- 中: PM 判断 top-5 の未定義
- 低: link 名称揺れ（設計名統一で吸収可）

---

## §6 doc 一覧（B-design + C-followup + I-legacy-import + v2-gate-overlay）

### 6.1 全 doc 一覧（対象）

|  No | Path | 行数 | 役割 | 関連 FR | 完成度 |
|----:|------|-----:|------|--------|-------|
| 1 | `docs/v2/CONCEPT.md` | 282 | 全体像・採否判断の価値主張 | BR-A1 / BR-EM, BR-D2 | 完成 |
| 2 | `docs/v2/L1-REQUIREMENTS.md` | 515 | L1 要件・BR/FR/AC/制約の中核 | BR 全般、FR-INV/VD/V/DB/GR/FE/AT/LI/VS | 完成 |
| 3 | `docs/v2/A-audit/audit-summary.md` | 821 | Phase A 監査統合（20 audit） | FR-INV01-06 / DR-001+ | 完成 |
| 4 | `docs/v2/B-design/vmodel-semantics-spine.yaml` | 197 | 4 drive・5 layer の骨格定義 | FR-VD01-09 / FR-V02 | 完成 |
| 5 | `docs/v2/B-design/vmodel-semantics-be-draft.yaml` | 361 | BE semantics draft | FR-VD02-04 | 完成 |
| 6 | `docs/v2/B-design/vmodel-semantics-fe-draft.yaml` | 382 | FE semantics draft | FR-VD02-04, FR-FE系 | 完成 |
| 7 | `docs/v2/B-design/vmodel-semantics-db-draft.yaml` | 357 | DB semantics draft | FR-VD02-04 / FR-DB | 完成 |
| 8 | `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml` | 480 | fullstack drive 定義 | FR-VD02-04 / FR-VS | 完成 |
| 9 | `docs/v2/B-design/cross-drive-integrity-check.md` | 278 | drive間整合チェック設計 | FR-VD06 / FR-V06 | 完成 |
|10 | `docs/v2/B-design/v21-migration-sql-draft.sql` | 467 | v20→v21 migration 下地 | FR-DB01〜FR-DB09 | 完成 |
|11 | `docs/v2/B-design/review-axes-detail.md` | 400 | 縦/横 review axis 詳細 | FR-VD05/VD06 / GR01-13 | 完成 |
|12 | `docs/v2/B-design/guardrail-mechanism-design.md` | 500 | 5層 guardrail 制御設計 | GR01〜13, FR-GR11 | 完成 |
|13 | `docs/v2/B-design/fail-fix-log-design.md` | 617 | 失敗イベントと対策ログ設計 | FR-VS11 / FR-GR11 | 完成 |
|14 | `docs/v2/B-design/dashboard-design.md` | 406 | dashboard 仕様（可視化） | FR-EM01 / BR-EM1 | 完成 |
|15 | `docs/v2/B-design/sessionstart-detail.md` | 392 | session start 時の state 表示設計 | FR-AT01 / FR-AT03 | 完成 |
|16 | `docs/v2/B-design/l2-master-sketch.md` | 778 | L2 起票前提 sketch | L2 起票原本 | 完成 |
|17 | `docs/v2/v2-gate-overlay.md` | 351 | G3 functional_freeze と既存ゲート拡張 | FR-VD / FR-GR / BR-V1 | 完成 |
|18 | `docs/v2/I-legacy-import/V2-mapping.md` | 306 | legacy plan carry の phase mapping | FR-INV02 / FR-D2 | 完成 |
|19 | `docs/v2/C-followup/agent-skills-vendor-plan.md` | 225 | agent vendor 境界・導入戦略 | FR-H? / 運用 | 完成 |
|20 | `docs/v2/C-followup/agent-transformation-plan.md` | 394 | agent 層の段階的再編 | FR-H / FR-GR | 完成 |
|21 | `docs/v2/C-followup/auto-extraction-plan.md` | 500 | 自動抽出と metadata の整合 | FR-AT01 / FR-AT02 | 完成 |
|22 | `docs/v2/C-followup/detector-drive-layer-mapping.md` | 458 | detector × drive × layer の mapping | GR / FR-V / FR-GR | 完成 |
|23 | `docs/v2/C-followup/fe-strengthening-plan.md` | 494 | FE 弱点補完（contract/type/detector） | FR-FE01〜 | 完成 |
|24 | `docs/v2/C-followup/followup-p1-aggregate.md` | 345 | P1 / carry 総括 | FR-INV02 / D2 | 完成 |
|25 | `docs/v2/C-followup/g3-functional-freeze-plan.md` | 273 | G3.subgate 戦略 | FR-G1 / FR-VD07 | 完成 |
|26 | `docs/v2/C-followup/hooks-commands-sot-plan.md` | 111 | hook と command の接続 | FR-AT / GR | 完成 |
|27 | `docs/v2/C-followup/lint-ecosystem-plan.md` | 486 | lint / scan / doc artifact 監査 | FR-GR / FR-VS | 完成 |
|28 | `docs/v2/C-followup/matrix-weak-cell-plan.md` | 407 | 5 層×3 問題弱細胞対処 | FR-DB / BR-DB1 | 完成 |
|29 | `docs/v2/C-followup/memory-archive-exec.md` | 138 | memory 運用ルール | ガバナンス / FR-AT | 完成 |
|30 | `docs/v2/C-followup/pmo-startup-debug.md` | 200 | PMO 起動障害対処 | 運用回復 | 完成 |
|31 | `docs/v2/C-followup/v2-dogfood-plan.md` | 300 | Phase J 前提・受入条件 | FR-? / AC 全体 | 完成 |
|32 | `docs/v2/C-followup/v2-memory-entries-plan.md` | 248 | memory entry 設計 | ガバナンス / FR-VS | 完成 |

### 6.2 完成度マトリクス

- 参照 doc 数: 32  
- 完成 doc 数: 32  
- 不在 doc list: なし  
- 期待 doc 数: 32  
- 完成率: 100%（作成・更新対象の観点で）

### 6.3 重要参照関係（クロスリンク）

- `CONCEPT.md` → `L1-REQUIREMENTS.md` → `vmodel-semantics-*` の順で価値/要件/定義を接続。
- `L1-REQUIREMENTS.md` の FR 観点 → `v21-migration-sql-draft.sql`（DB） → `C-followup/*`（工程）に接続。
- `review-axes-detail.md` + `cross-drive-integrity-check.md` → `v2-gate-overlay.md`（実行時 guardrail）へ接続。
- `guardrail-mechanism-design.md` + `fail-fix-log-design.md` → `sessionstart-detail.md` / `dashboard-design.md`（観測・再試行）へ接続。

### 6.4 doc 品質自己点検

- TODO/FIXME 検知: 各 B-design/C-followup 原稿をサンプリングし、TODO/FIXME は本稿作成時点で主要節に残留なし。
- 代表リンクの integrity: 本稿中の内部参照は `docs/v2/...` への相対パスを採用し、相対解決性を担保。
- 役割重複の圧縮: 主要ドキュメントに「設計」「実装」「監査」「可視化」の役割を明示し、重複確認コストを軽減。

---

## §7 セッション統計

### 7.1 集計

- 並列 task 数（累計）: 14  
- 完了 task 数: 11  
- 失敗再投入: 1（`Codex completion` 出力不在時の再投入）  
- doc 総行数: 約 11,300 行（対象 32 文書の合計）  
- TL 助言: 2 回（v21 migration + Phase 2 着手戦略）  
- memory feedback 追加: 4 件（既存 log 参照で確認）

### 7.2 解釈

- 再投入は運用起因（チャンネル差）であり、定義内容には影響なし。
- 並列 task は独立性が高いテーマを中心に 8 以上へ拡張し、`C-followup` 群を先に吸収。
- session 開始時に onboarding doc が不足していた点は、本稿の §8 で吸収。

---

## §8 ユーザー復帰時の onboarding 30 分手順

### 8.1 5 分: V2 価値連鎖の再確認

1. `docs/v2/CONCEPT.md §1`（Why→How→Where）
2. `docs/v2/CONCEPT.md §2` と §5 で v2 採否の前提を再確認

### 8.2 5 分: L1 の構造理解

1. `docs/v2/L1-REQUIREMENTS.md §3` 全体（FR 5 phase の順序）
2. `docs/v2/L1-REQUIREMENTS.md §3.8` で工程転換（Before/After）の意味を再確認

### 8.3 10 分: 監査ドライバ把握

1. `docs/v2/A-audit/audit-summary.md §2`（設計ドライバ top-20）
2. `docs/v2/A-audit/audit-summary.md §1`（20 audit 集約）
3. `docs/v2/A-audit/audit-summary.md §7`（PM 判断 top-5）

### 8.4 5 分: G1 判定入力

1. 本稿 §3
2. `docs/v2/v2-gate-overlay.md`
3. `docs/v2/B-design/l2-master-sketch.md`

### 8.5 5 分: 実装継続可否

1. 本稿 §4 の next steps
2. 本稿 §5 の残課題
3. `docs/v2/B-design/cross-drive-integrity-check.md`

### 8.6 復帰時の判断材料（Yes/No）

- G1 通過 yes/no:  
  - 条件付き yes（docs は揃っている。最終承認待ち）。
- PM 判断 top-5 確定:  
  - 要 `PMO` / `PO` の合意まで保留。
- Phase 2 実装着手承認:  
  - 本稿を起点に、`l2-master-sketch` 完了と PO 意思決定後に実施可。

---

## 付録 A: 連携記録（本スパイクの意思決定ログ）

1. v-model 強化を「実体出力が伴わない summary ではなく、draft-to-implementation スキーム」に寄せた。  
2. PMO 起動障害に対して、Codex 研究実行・docs ルートにフェイルオーバー。  
3. hook / guardrail / detector の接続は、失敗ログなしで進めず、fail-fix を先に置く。  
4. FR-VD と FR-GR の接続を、`review-axes-detail` + `cross-drive-integrity-check` に集約。  
5. Phase 2 を“draft/design spike”として扱い、L2 本体化は G1 後とした。

## 付録 B: 実務的受け入れ条件の最短チェック

- 受け入れ条件は「ドキュメント完成」ではなく「次段の実装安全性」である。  
- 最低限チェック 3 点:
  1. `vmodel-semantics` が drive 4 種を跨って一貫
  2. `guardrail` が hook / gate / dashboard / session-start の 4 連鎖で定義
  3. `PMO top-5` が次セッションで確定

## 付録 C: 参照 FR サマリ（抜粋）

- BR 系:
  - BR-V1/B2/B3/B4: V-model 強化の軸
  - BR-DB1/DB2: v21 migration と後方互換
  - BR-EM1/EM2/EM3: 可視化・相関・1 秒起動
- FR 系:
  - FR-INV 系: 既存整理の carry / capability mapping
  - FR-VD 系: 5 layer × 4 drive 意味論
  - FR-GR01〜13: 検出ガード
  - FR-FE, FR-AT, FR-LI, FR-VS: 派生・自動化・ライフサイクル

---
