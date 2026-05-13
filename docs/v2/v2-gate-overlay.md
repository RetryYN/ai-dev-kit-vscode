# V2 Gate Overlay（docs-integrity P1 対応）

作成日: 2026-05-14  
対象: docs/v2/L1-REQUIREMENTS.md §3.8 / skills/tools/ai-coding/references/gate-policy.md / skills/SKILL_MAP.md / docs/v2/A-audit/docs-integrity-audit.md  
ステータス: 起票専用（既存正本は変更しない）

## 0. 目的と適用範囲

この文書は、V1 正本である `skills/tools/ai-coding/references/gate-policy.md` の上に、V2 での追加制約と接続点を重ねる overlay として運用する。  

### 0.1 適用原則

1. V1 の規定は原則維持し、V2 追加分のみ補完する。  
2. 既存 CLI / Reverse / Scrum / FR-acceptance を壊さない。  
3. 既存正本は V1 のみ維持。V2 は同じ命名（Gx）を変更しない。  
4. V2 完了時（Phase J）に V2 追加分を統合判断し、本 overlay を削除候補化する。  
5. ゲートは `pair_status` と `origin_mode` / `evidence_status` / `direction` を含む V-model データ設計に接続する（L1-REQUIREMENTS §3.8, §10）。  

### 0.2 参照関係

- V1 正本: `skills/tools/ai-coding/references/gate-policy.md`
- V2 追加正本: `docs/v2/v2-gate-overlay.md`（本書）
- フロー定義: `skills/SKILL_MAP.md`
- 根拠要件: `docs/v2/L1-REQUIREMENTS.md`
- ドリフト証跡: `docs/v2/A-audit/docs-integrity-audit.md`

### 0.3 参照ルール（重要）

- 文書上で「V1」と「V2」の意味は「既存 gate-policy との対比」に限定する。  
- 互換性判断は「既存 gate-policy 条件を満たした上で、V2 追加条件を論理積で評価する」。  
- `gate-policy` と衝突する文言が発見された場合は、まず `docs/v2/A-audit/docs-integrity-audit.md` の P1/P2 リストを参照し、overlay 側では未確定なら `暫定` と明示する。  

## 1. §1 V2 で変わる gate / 変わらない gate

| ゲート | V1 | V2 | 変更 |
|---|---|---|---|
| G0.5 企画突合 | 既存 | 維持 | なし |
| G1 要件完了 | 既存 | 維持 + AC 拡張 (AC-15-17) | 内容追加 |
| G1.5 PoC | 既存 | 維持 | なし |
| G1R 事前調査 | 既存 | 維持 | なし |
| G2 設計凍結 | architecture 単独 | architecture + system_integration ペア凍結 | ペアリング追加 |
| G3 詳細設計凍結 | 詳細 + テスト | detailed + integration ペア凍結 + G3.functional_freeze（subgate） | サブゲート追加 |
| G3.functional_freeze（サブゲート） | — | functional + unit ペア凍結（L 案件/fe/fullstack/db 強制） | 新設 |
| G4 実装凍結 | 実装 + テスト | 実装 + テスト + レビュー | 内容明確化 |
| G5〜G11 | 既存 | 維持（細部 V2 拡張あり） | 微調整 |
| RG0〜RG3 / RGC | 既存 | 維持 + V-model 接続（FR-VS07） | 接続点追加 |
| Scrum S0-S4 | 既存 | confirmed 後に Forward contract 生成 | 接続点明確化 |

### 1.1 対応ルール（最短運用）

- G2・G3 は V2 でも同一 gate 名を使う（公開契約の破壊回避）。  
- G3.functional_freeze は `subgate='functional_freeze'` として実装する。  
- サブゲートを public gate として `phase.yaml.gates` へ昇格するのは、V3 以降の検討事項。  

## 2. §2 G3.functional_freeze サブゲート詳細

### 2.1 サブゲート定義

- 種別: `helix gate G3 --subgate functional_freeze`
- 目的: 機能設計（`functional`）と単体テスト設計（`unit`）を同一タイミングで paired へ凍結する。  
- 対象規模: `size=L` で基本必須、`size=S/M` 例外運用可。  
- 対象 drive: `fe` / `fullstack` / `db` を必須化、`be` は通常 `size` 依存で例外。  
- 失敗モード: `pair_status != paired` または `pair_status` 欠落。  

### 2.2 enforce 条件

- `size=L` かつ `drive in (fe, fullstack, db)` の場合、`pair_status='paired'` が hard fail-close 条件。  
- `G3` が pass しても `functional_freeze` を未満を許容しない。  
- `size=L` で `drive` が未定義（空）なら、最小 fail-close として plan の再取得を要求する。  

### 2.3 fail-close 例外

- `size=S` / `size=M` は plan ポリシーに応じて skip 可。  
- `size=S/M` かつ `drive=fe/fullstack/db` でも `drive` が明示される場合は、`waived` の判断記録がない限り通過不可。  
- `pair_status='waived'` を通過扱いにする場合は、gate 前提で `waived_reason` を evidence に残す。  

### 2.4 CLI 例

- `helix gate G3 --subgate functional_freeze --plan-id PLAN-XYZ`  
- `helix gate G3 --subgate functional_freeze --plan-id PLAN-XYZ --json`  
- `helix gate G3 --subgate functional_freeze --plan-id PLAN-XYZ --require pairing`（実装未対応時は planned へフォールバック）  

### 2.5 合格条件（最小）

1. `design_sprint_entries` に該当 sprint が存在し、`pair_status='paired'`。  
2. `track in (fe, fullstack, db, be?)` と `sprint_type='functional'` / `test_type='unit'` が整合。  
3. FR-VS06 / FR-VS07 と矛盾しない状態。  
4. `origin_mode='forward'` 以外を許容する場合は `evidence_status` を含む監査追跡を追加。  

## 3. §3 ペアリング凍結ルール (G2/G3 enforce)

### 3.1 ペアルール

- `G2`: `architecture`（design） ∥ `system_integration`（test design）が同時凍結。  
- `G3`: `detailed`（design） ∥ `integration`（test design）が同時凍結。  
- `G3.functional_freeze`: `functional`（design） ∥ `unit`（test design）が同時凍結。  

### 3.2 pair_status 遷移ガード

- 受け入れ対象: `pending` / `design_only` / `test_only` / `paired` / `waived` / `failed`  
- V2 の有効な遷移:  
  - `pending -> design_only`  
  - `pending -> test_only`  
  - `design_only -> paired`  
  - `test_only -> paired`  
  - `design_only -> waived` / `test_only -> waived`  
  - `paired -> waived`（再審要）  
- 不正遷移（paired→design_only など）はゲート fail-close。  

### 3.3 データ接続

- `design_sprint_entries` を正規の起点（`track`, `layer`, `sprint_type`, `pair_status`）で参照する。  
- `design_sprint_artifact_links` を併用し、`covers` / `derives_from` / `implements` のリンク欠落を検知。  
- G2/G3 のペア判定で、両レイヤー artifacts が未提出は fail-close。  

## 4. §4 横断 review ルール

### 4.1 vertical_review

- 目的: planning → requirement → architecture → detailed → functional の同一脚内連鎖整合を強制。  
- 連鎖対象: 企画（FR-INV）→要件（FR/BR）→設計（architecture）→詳細（detailed）→機能（functional）。  
- 重要点: いずれかで fail が出た場合、直下位の gate へ逆流させる。  

### 4.2 horizontal_review

- 目的: 設計 ↔ 対応テスト設計の 1:1 ペアレビュー。  
- 対象ペア:  
  - architecture ↔ system_integration  
  - detailed ↔ integration  
  - functional ↔ unit  
- 監査要件: 1 対 1 のレビューが missing なら fail-close。  

### 4.3 axis fail-close 連動

- `vertical_review` 側 fail: 直上位の gate で `interrupted` or `failed` を発行。  
- `horizontal_review` 側 fail: pair が揃わない状態 (`pair_status != paired`) かつ test design 参照欠落の場合 `blocked` に格上げ。  
- `BR-V3`（水平/垂直両 axis の連動）: 2 方向のレビューが揃うまで L3/L4 の中核ゲートは pass 扱い不可。  

## 5. §5 既存 gate-policy.md との関係

### 5.1 役割分担

- `gate-policy.md`: V1 の正本（変更しない）。  
- `v2-gate-overlay.md`: V2 の追加正本（本書）。  
- 既存 CLI / 参照先が V1 のままでも、追加判定は本書が上位規約として評価する。  

### 5.2 リンク関係の固定

- `G0.5/G1/G1.5/G1R/G2/G3/G4/G5〜G11` は基本定義を `gate-policy.md` 参照。  
- `pairing/track/sprint_type/pair_status` 追加判定は `v2-gate-overlay.md` を参照。  
- Reverse / Scrum 接続は本書でのみ定義。  

### 5.3 V2 完了後の移行

- Phase J 判定後、`gate-policy.md` に `functional_freeze` と V2 の追加接続を統合する。  
- 統合前提: docs-integrity 監査で link drift 0 近傍を確認。  
- 統合後は本 overlay の deprecate 方針または削除。  

## 6. §6 Reverse / Scrum gate 接続

### 6.1 Reverse 接続

- R4（Gap & Routing）完了後、Forward ルーティングの接続先を決定する。  
- 追加規約（V2）: Reverse からの接続でも、Functional Freeze 追加が必要な gap については最小限 `G3.functional_freeze` を評価する。  
- FR-VS07 との対応: Reverse で必要な gap が機能面（`functional/unit`）へ波及した場合のみ subgate 条件を追加する。  

### 6.2 Scrum 接続

- Scrum は `confirmed` 前は V2 gate 追加接続の対象外。  
- `scrum S4` の `decide --confirmed` で Forward 接続し、Forward contract を生成した時点で該当 sprint を開始する。  
- その時点で、V2 では `G2` と同時進行条件（`G2` エントリ）を満たす必要がある。  

### 6.3 evidence_status × gate 条件

| evidence_status | Forward 初期ゲート | 条件 |
|---|---|---|
| observed | G3/G4 一部参照可 | 追加証跡の取りこぼしを warning として記録しつつ通過可 |
| inferred | G2/G3 通過時の補助 | G3.functional_freeze は必須条件ではなく、補助条件として `paired` 再証跡を要求 |
| confirmed | Reverse/Scrum confirmed 連携 | confirmed かつ evidence が揃えば G2 接続可 |

### 6.4 連携 CLI 例

- `helix reverse rg4`（gap routing）  
- `helix scrum decide --hypothesis H-001 --confirmed`  
- `helix gate G2 --plan-id <id> --origin-mode reverse --evidence-status confirmed`（今後実装想定時）  
- `helix gate G3 --subgate functional_freeze --plan-id <id> --evidence-status inferred`  

### 6.5 接続前提（実務）

1. Reverse でも Scrum でも、Forward へ接続する evidence が不足する場合は gate で fail。  
2. confirmed 前の Scrum は G2 前提を要求せず、confirmed 後に Forward を起動。  
3. FR-VS07 は接続点追加のみとし、既存 Reverse 流儀（RG0〜RG3）は維持。  

## 7. §7 PM 判断必要事項

- `G3.functional_freeze` の public gate 昇格タイミング（Phase J / V3 / 永久 subgate）。  
- `gate-policy.md` 統合タイミング（Phase J またはその直近）。  
- `origin_mode` / `evidence_status` / `direction` を 1 管理する方針を docs-integrity 監査側で再検証する時期。  
- `docs/commands` 側の planned/current 区分で、`helix gate G3 --subgate functional_freeze` を current として公開する時期。  
- Reverse で必要な gap のみ functional_freeze を要求する実績の閾値（観測開始は `AC-16` 先行実行）。  

## 8. §8 Gate overlay 全件明細（CLI + fail-close）

本節は `gates` の運用を 1 つずつ正規化し、V2 的に追加される条件を最小で明示する。

### 8.1 G0.5 企画突合

- V1条件: 要件突合完了（plan 先行）。  
- V2追加: 既存条件を維持。  
- CLI: `helix gate G0.5 --plan-id <id>`  
- fail-close: 企画情報欠如、D-REQ/D-ACC 未突合時。  
- V2備考: PM 観点を崩さず、V-model 追加は本 gate では未追加。  

### 8.2 G1 要件完了

- V1条件: 要件/非要件/受入条件の 100% 定義、未解決 blocker 0。  
- V2追加: AC-15/16/17 を要件監査へ拡張（FR-VS 系）。  
- CLI: `helix gate G1 --plan-id <id>`  
- fail-close: AC-15/AC-16/AC-17 未満は fail。  
- V2備考: 要件更新と gate 条件の整合を docs-integrity 監査で追跡。  

### 8.3 G1.5 PoC

- V1条件: 技術不確実性時のみ評価。  
- V2追加: 変更なし。  
- CLI: `helix gate G1.5 --plan-id <id>`  
- fail-close: 技術不確実性に対する仮説 / kill criteria の欠落。  
- V2備考: 結果は `evidence_status` を添えて Forward へ送る。  

### 8.4 G1R 事前調査

- V1条件: research レポート整備、採否理由の根拠記録。  
- V2追加: 変更なし。  
- CLI: `helix gate G1R --plan-id <id>`  
- fail-close: 公式情報不備、open blocker 残存。  
- V2備考: Reverse / Scrum の evidence 連携を前提化。  

### 8.5 G2 設計凍結

- V1条件: 仕様追従、ADR/設計/threat model 完了。  
- V2追加: architecture と system_integration のペア凍結。  
- CLI: `helix gate G2 --plan-id <id>`  
- CLI（V2追加）: `helix gate G2 --pair-check architecture,system_integration --plan-id <id>`（planned / 運用実績に応じて）  
- fail-close: architecture と system_integration が片側未凍結。  
- V2備考: fullstack/fe でモック/UX 追加条件は既存条件に重畳。  

### 8.6 G3 詳細設計凍結

- V1条件: 詳細設計 + API/Schema/Test Plan Freeze。  
- V2追加: detailed と integration をペア凍結、さらに `G3.functional_freeze` を同時運用。  
- CLI: `helix gate G3 --plan-id <id>`  
- CLI（V2追加）: `helix gate G3 --subgate functional_freeze --plan-id <id>`  
- fail-close: detailed/integration が片寄り、もしくは subgate 不達。  
- V2備考: G3 pass は pair_status 検査に fail-close を追加。  

### 8.7 G3.functional_freeze（subgate）

- 条件: `size=L` × `drive in (fe/fullstack/db)` で `pair_status='paired'`。  
- CLI: `helix gate G3 --subgate functional_freeze --plan-id <id>`  
- fail-close: pairing 失敗・サイズ/drive 判定不足・`origin_mode` 未整備（必要時）。  
- V2備考: `size=S/M` は waiving ルールを明示すれば skip 可能。  
- 実装仕様（サブゲート）:
  - `--subgate functional_freeze` かつ `--plan-id` 必須。  
  - `design_sprint_entries` と `test_design_entries` の `pair_status='paired'` を検査。  
  - `functional` レイヤーの design と `unit` レイヤーの test design がそろうこと。  
- リリース監査連携:
  - 通常運用では `review_axes` の vertical/horizontal を通過要件として扱う。  
  - 監査では `pair_status` 欠落を high risk として記録する。  

### 8.7.1 V2 実装 Step

- Step 1: `cli/helix-gate` の arg parse に `--subgate` を追加（既存 `G3` 互換維持）。  
- Step 2: `cli/lib/helix_db.py` に `query_functional_pair_status(plan_id, drive)` を追加。  
- Step 3: L1 `requires_functional_freeze` を参照し、size/drive 条件（`fe/fullstack/db`）と連結。  
- Step 4: bats/pytest テストを追加し、pass/fail/skip を実証。  
- Step 5: `v2-gate-overlay` / `gate-policy` 参照を更新（本節・§9 と整合）。  

### 8.7.2 段階的 enforce（Phase 4.x）

- Phase 4.1: warning only（false positive 調整）  
- Phase 4.2: `fe` のみ fail-close（`size=L`）  
- Phase 4.3: `fe/fullstack/db` を fail-close 対象へ拡張（`size=L`）  
- Phase 4.4: 全 drive へ適用（`size=L` を基準）

### 8.8 G4 実装凍結

- V1条件: 実装、テスト、セキュリティ、debt の整合。  
- V2追加: レビューを同時条件に明文化。  
- CLI: `helix gate G4 --plan-id <id>`  
- CLI（V2補助）: `helix review --uncommitted`（評価済）  
- fail-close: レビュー未完了、レビュー debt の非解決、CI/回帰不合格。  
- V2備考: 既存 `helix review --uncommitted` との整合を維持。  

### 8.9 G5〜G11（共通ルール）

- V1条件: 既存規約を維持。  
- V2追加: 各 gate の entry/exit で `evidence_status × pair_status` の追跡を optional tag として追加可能。  
- 代表 CLI:
  - `helix gate G5 --plan-id <id>`  
  - `helix gate G6 --plan-id <id>`  
  - `helix gate G7 --plan-id <id>`  
  - `helix gate G9 --plan-id <id>`  
  - `helix gate G10 --plan-id <id>`  
  - `helix gate G11 --plan-id <id>`  
- fail-close: V1 条件を満たさない + 追跡属性を欠いたための疑義がある場合。  
- V2備考: V1 破壊を避けるため、追加属性は必須化しない。  

## 9. §9 監査・整合チェック計画

### 9.1 link 整合

- `gate-policy.md` へのリンクは固定参照（1/2 方向）。  
- `L1-REQUIREMENTS §3.8` の FR-VS / AC-15〜17 が overlay の最上位根拠。  
- `SKILL_MAP.md` の Reverse/Scrum 定義を維持参照。  
- `docs/v2/A-audit/docs-integrity-audit.md` のリンク崩れは本書開始時点の監査結果として記録。  

### 9.2 監査対象

1. G2/G3 pair チェック: `architecture/system_integration`, `detailed/integration` が揃っているか。  
2. G3.functional_freeze の pair_status が L 案件で paired か。  
3. RG4 → Forward 接続で evidence を持つか。  
4. Scrum confirmed 後の Forward 契約生成が有るか。  
5. `docs/v2/` 配下の link が正本を参照しているか。  

### 9.3 TODO 残存

- TODO: `helix gate G3 --subgate functional_freeze` の CLI 安定版実装可否（command 仕様は overlay として先行記載）。  
- TODO: `origin_mode` / `evidence_status` を gate 判定入力として必須化する場合の閾値定義（V3 候補）。  
- TODO: Phase J 統合後の `gate-policy.md` 追記内容（最終版）。  

## 10. §10 運用上の注意（破壊変更回避）

- 本書は V1 を上書きせず、追加 overlay として参照される。  
- 既存 CLI の仕様を変更しない。  
- PM/PO/TT への説明時は「公開契約 = gate-policy」かつ「V2 追加 = overlay」で分離して説明する。  
- 実装時のガードポイント:
  - `pair_status` が未定義の sprint は fail 対象に追加。  
  - `track` 交差時の `fullstack` は gate 連携点を分けて評価。  
  - `functional_freeze` は `public gate` として扱わず、`subgate` として運用。  

## 11. §11 合意済み制約（再掲）

- read-only 起票（本書は新規作成のみ）。  
- `docs/v2/v2-gate-overlay.md` の行数目標は 300-500 を守る。  
- 変更は `git add` / `git commit` 禁止。  
- 実装対象は overlay の新規作成のみ。  

## 12. §12 変更ログ

- 2026-05-14: 初版起票。L1-REQUIREMENTS §3.8 / gate-policy / SKILL_MAP / audit doc を overlay 化。  
- 以後の更新: Phase J まで追補。  
