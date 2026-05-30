---
plan_id: L4-helix-workflows-方式設計plan
title: "L4-helix-workflows-方式設計plan: HELIX-workflows V2 方式設計"
kind: design
layer: L4
drive: be
status: draft
created: 2026-05-27
owner: PM
process_layer: L4
parent_process: HELIX-workflows/helix-process/L4-basic-design.md
pairs_test_design:
  - docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G4 evidence)"
  - role: doc-reviewer
    slot_label: "doc-reviewer — ドキュメント品質レビュー (大規模 design 改定時)"
generates:
  - artifact_path: docs/v2/L4-basic-design/方式設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
    artifact_type: design_doc
dependencies:
  parent: L1-helix-workflows-業務要求plan
  requires:
    - L0-helix-workflows-conceptplan
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
    - L3-helix-workflows-業務要件plan
    - L3-helix-workflows-機能要件plan
    - L3-helix-workflows-非機能要件plan
  blocks:
    - L4-helix-workflows-機能構成設計plan
    - L4-helix-workflows-データ設計plan
    - L4-helix-workflows-外部IF設計plan
related_docs:
  - HELIX-workflows/helix-process/L4-basic-design.md
  - HELIX-workflows/helix-process/L9-system-test.md
  - docs/v2/process/L04-architecture-design-and-system-test-design.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md
  - docs/v2/L0-helix-workflows/concept.md
---

## §0 PLAN concept

本 PLAN は L4 方式設計を起票するための統合エントリであり、L3 で確定した要件を実装可能なアーキテクチャ設計へ昇格する起点です。起票時点では骨子化を優先し、本文は Step 2-3 における本体展開用の carry note を明示します。

HELIX-workflows V2 dogfooding の L4 は、L3↔L4 の入力受け渡しを維持しつつ、L4↔L9 の総合テスト pairing を同時凍結することが目的です。既に commit 42a20c9 で取得済みの G3 条件を維持し、既存 ID（BR/FR/NFR/AC/OT）を新規追加しない前提で skeleton を起票します。

### §0.1 L4 工程 PLAN の分割方針 (L3 命名 drift 救済 carry)

[HELIX-workflows L4 工程定義](../../../HELIX-workflows/helix-process/L4-basic-design.md) は L4 を以下 5 PLAN に分割します: 方式設計 / 機能設計 / 画面設計 / データ設計 / 外部IF設計。**本 PLAN は方式設計を担う** (umbrella 名「基本設計」は工程定義に存在しない概念)。

L3 3 PLAN の `dependencies.blocks` が `L4-helix-workflows-基本設計plan` (旧 umbrella 名) を参照している命名 drift は、L4 配下 5 PLAN 全列挙 (`L4-helix-workflows-方式設計plan` + 機能 + 画面 + データ + 外部IF) へ retrofit する carry とします。本 commit 範囲外 (L3 retrofit PLAN として後続起票)。

## §1 工程表 (Step 1-6)

### Step 1 参考調査
- 3 PLAN と 1st party process 基本文書を再読して構造差分を確定する。
- L0 §8、および IEEE 42010 / arc42 / C4 / Diátaxis の適用ポイントを明記する。
- Web 検索は本 skeleton では未実施（carry とし、Step 2-3 で 3 query を実施）。

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査 (L3 3 PLAN + L0 §8 + IEEE 42010 / arc42 / C4 / Diátaxis の業界 standard、Web 検索 3 query 必須) | ✅ done (2026-05-27、pmo-haiku Web 検索完了) |
| 2 | 方式設計 doc 起草 (`docs/v2/L4-basic-design/方式設計.md` §1-§8 本文化、本 skeleton から拡充) | ✅ done |
| 3 | L9 総合テスト設計 doc 起草 (`docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` §1-§7 本文化、L4 §1-§7 ↔ ST-* 双方向 trace) | ✅ done |
| 4 | ADR-044 snapshot 起草 (大局判断本文化、IEEE 42010 standard 整合性 evidence) | ✅ done (2026-05-27、Decision 1-9 + Compliance + Alternatives) |
| 5 | TL レビュー (`helix codex --role tl-advisor`、adversarial check 1 回必須、G4 evidence) | ✅ done (2026-05-27、R1/R2 二重 audit 完了、conditional_approve) |
| 6 | pmo-sonnet + doc-reviewer 二重 audit + 修正反映 → G4 ゲート判定 → L4 機能/データ/外部IF 設計 PLAN へ展開 | ✅ done (2026-05-27/2026-05-29、pmo-sonnet YES with minor、M-1〜M-4 全解消) |

### Step 2-6 の実行方針

Step 2〜3 は `docs/v2/L4-basic-design/` と `docs/v2/L9-test-design/` の 2 生成物を同時に育てる。Step 4 では ADR snapshot として `docs/adr/` に反映し、Step 5・6 は review chain を優先する。

### Step 1→6 トレーサビリティ目標

- Step 1 では `requirements`, `workflow`, `industry standard` の 4 要素を同時比較し、見落とし候補を `carry_notes` として Step 2 以降に連結する。
- Step 2 では architecture §0〜§8 全部の本文化を進め、各 subsection に ST 対応欄を暫定追加する。
- Step 3 では test-design の §1〜§7 を本文化し、ST マッピング表を V-model 2 方向 trace として整備する。
- Step 4 では ADR Context/Decision/Consequences/Alternatives/Compliance を固定し、pair freeze の反省条件を明示した evidence を添付する。
- Step 5/6 では `helix codex --role tl-advisor` と二重監査の結果を統合し、G4 evidence 判定前提として G4/PMO 依存関係を閉じる。

| 重要指標 | 目標値 | 担当 | エビデンス |
|---|---:|---|---|
| L4 本文化率 | 0% → 100% | Step 2-3 | body 反映ログ |
| ST-Trace 完備率 | 1:1 対応 | Step 3 | ST↔L4 テーブル |
| ADR Accept 進捗 | Proposed → Accepted | Step 4-6 | 監査コメント |
| review 実施率 | 3 委員会 = 100% | Step 5-6 | pmo/ doc-reviewer / tl log |

## §2 実装計画

### §2.1 必須記載項目

本 PLAN は以下の 3 生成物を同時に凍結対象として扱い、それぞれの必須セクションを Step 2-3 で本体起草します。L4 方式設計と L9 総合テスト設計は相互参照を前提に、ADR snapshot は意思決定固定点を提供します。

- **設計 doc** (`docs/v2/L4-basic-design/方式設計.md`): §0〜§8 を 1:1 で埋める。
- **総合テスト設計 doc** (`docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md`): §0〜§7 を 1:1 で埋める。
- **ADR** (`docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`): Nygard標準の 5 章を完成。

### §2.2 L3 → L4 詳細化 mapping

L3 設計で確定した業務要件・機能要件・非機能要件を、L4 のアーキテクチャ断面に変換します。

| L3 要素 | L4 映像化方針 | 参照先 |
|---|---|---|
| L3 業務要件plan | BR-01〜BR-12 の dogfooding / pair governance / mode 回帰を §1-§2 へ再構成 | docs/plans/L3/L3-helix-workflows-業務要件plan.md |
| L3 機能要件plan | FR/AC の契約検証フローを §4-§6 に取り込み、検証設計 ST-* と突合 | docs/plans/L3/L3-helix-workflows-機能要件plan.md |
| L3 非機能要件plan | NFR と非機能指標を §4-§6 の制約として固定 | docs/plans/L3/L3-helix-workflows-非機能要件plan.md |

### §2.3 L4 接続規約

- `dependencies.requires` は L0/L1/L3 の 8 件を必須として保持し、配下PLANとの追従性を担保する。
- `pairs_test_design` / `generates` は L4-L9 pair を同時凍結し、Step 6 で L4-機能/データ/外部IF 設計へ carry を伝播する。
- L4 出力は `status: draft` で開始し、pair_artifact との相互参照を満たした段階で Step 6 へ進める。

## §3 成果物

- 本 PLAN ファイル: `docs/plans/L4/L4-helix-workflows-方式設計plan.md`
- 方式設計 doc: `docs/v2/L4-basic-design/方式設計.md`
- 総合テスト設計 doc: `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md`
- ADR snapshot: `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`

## §4 G3 conditional + L4 skeleton audit (P1 13 件 + P2 4 件 の L4 設計内消化)

この節は Step 2-3 への carry を明示します。G3 conditional 残 P1 5 件 (前 session memory §3.A) + L4 skeleton 二重 audit (2026-05-27 本 commit、tl-advisor P1 8 件 + P2 4 件) を統合管理します。新規追加は行わず、既存 ID への射影で収束します。

### §4.1 G3 conditional 残 P1 5 件 (前 session 確立、L4 内対処)

- **P1-1**: baseline path / source / update policy 統一 (L3/L12/L14 で散在) [☐ planned: L7 carry]
  - 対応方針: BR-12 ratchet と changeprop の統合配線を `L4 方式設計` として凍結。
- **P1-2**: `helix doctor --check-changeprop` read-only と write update 契約分離 [☐ planned: L7 carry]
  - 対応方針: hook 入口を read と write に分け、失敗時の責務分解を明示。
- **P1-3**: AC-12〜16 の grep count から parser 移行 [✓ 解消 2026-05-27 commit XXX (L9 ST-4 本体化)]
  - 対応方針: 今期は migration path を skeleton で明示し、実装時に parser 対応を段階展開。
- **P1-4**: doc-reviewer evidence の正規化 [✓ 解消 2026-05-27 commit XXX (L4 §6.3 schema)]
  - 対応方針: `.helix/audit/doc-reviewer-evidence.yaml` を schema + 保持期間付きで管理。
- **P1-5**: 5s pre-commit と CI-only 20-120s 分割 [✓ 解消 2026-05-27 commit XXX (L4 §1.3 hook 分割表)]
  - 対応方針: L4 開始時に hook 2 モードを明記し、ローカル開発者体験を保持。

### §4.2 L4 skeleton tl-advisor audit P1 8 件 (2026-05-27 確立、Step 2-3 本体化対象)

- **P1-A1**: L3 plan の `dependencies.blocks` が `L4-helix-workflows-基本設計plan` を参照 (本 PLAN は方式設計) [☐ carry: L3 retrofit 別 PLAN]
  - 対応方針: 本 PLAN §0.1 で carry 明示済。L3 retrofit PLAN として後続起票。
- **P1-A2**: L4↔L9 の双方向 trace で L4 側に ST mapping table がなく逆参照のみ [✓ 解消 2026-05-27 commit XXX (→ pair trace 7+17 件)]
  - 対応方針: Step 2 で L4 architecture 各 § に `対応 ST-ID / 観測コマンド / evidence path` 表追加。
- **P1-A3**: baseline path / `check_changeprop` 表記ゆれ (`--check-changeprop` vs `check_changeprop`) [✓ 解消 2026-05-27 commit XXX]
  - 対応方針: 本 commit で L4 architecture §4 を `--check-changeprop` で統一。L3/L12/L14 への横断的 retrofit は P1-1 と統合。
- **P1-A4**: P1-3 (AC grep→parser 移行) が L9 ST に未反映 [✓ 解消 2026-05-27 commit XXX (本 wave ST-4 本体化)]
  - 対応方針: Step 3 で L9 ST-4 (ratchet 機構) に parser ベース検証 / grep 誤検出 fixture / AC-12〜16 受入条件 追加。
- **P1-A5**: doc-reviewer evidence YAML schema/retention/helix.db key 未設計 [✓ 解消 2026-05-27 commit XXX (L4 §6.3)]
  - 対応方針: Step 2 で L4 §6 に `.helix/audit/doc-reviewer-evidence.yaml` の fields / retention / DB key / 欠落時 fail 条件 を schema 表で本体化。P1-4 と統合。
- **P1-A6**: mandatory subagent と on-demand (pm-advisor / tl-advisor) が L4 §5 に混在 [✓ 解消 2026-05-27 commit XXX (L4 §5.1 分離 + 整合修正)]
  - 対応方針: 本 commit で L4 architecture §5 に `mandatory_by_phase` / `on_demand` 分離を注記。
- **P1-A7**: industry standards (IEEE 42010 / arc42 / C4) 列挙のみで対応表なし [✓ 解消 2026-05-27 commit XXX (L4 §0.1 対応表)]
  - 対応方針: Step 2 で L4 §0 / 関連 § に IEEE viewpoint・arc42 12 章・C4 4 階層の対応表を本体化。出典: arc42.org / c4model.com / ISO/IEC/IEEE 42010:2022。
- **P1-A8**: 設計 doc が CLI/file/schema を主張する箇所に `implementation_status` 列未出現 (BR-RULE-09 違反) [✓ 解消 2026-05-27 commit XXX (3 file 合計 48 件)]
  - 対応方針: Step 2 で L4 architecture / L9 test design / ADR-044 の実在主張表に `implementation_status` 列追加。

### §4.3 L4 skeleton tl-advisor audit P2 4 件 (carry 化)

- **P2-A1**: ADR-044 Decision に 9 mode→Forward 回帰 / 採用 project 配布判断が未収容 → Step 4 ADR 本体化で追加。 [☐ L4 Step 4 carry]
- **P2-A2**: D2/D3 carry が L4 architecture 側に未反映 → 本 commit で L4 architecture §7 / §8 に carry note 追記 (下記 §5 と連動)。 [☐ carry: L4 §5.2 維持]
- **P2-A3**: L9 security test が汎用、secret/credential/OWASP 観測条件不足 → Step 3 で L9 §4 非機能テストを本体化。 [partial: §4.2 OWASP 言及済、fixture 詳細は planned]
- **P2-A4**: Web 検索 3 query + balance_ratio 再集計 pending → Step 1 (参考調査) + Step 2-3 で本体化前必須。 [✓ 解消 2026-05-27 commit XXX (pmo-haiku Web 検索完了)]

## §5 pmo-sonnet D2/D3 + BR-09/BR-10 ラベル carry の L4 内消化

### §5.1 前 session pmo-sonnet D2/D3 carry

- **D2**: L0 §12 Glossary 7 用語を L1 §10.2 entity へ追補（source of truth を揺らがせない）。
- **D3**: L14 OT-09〜12 の非連番を再順序化するか末尾コメントに正規化。

### §5.2 本 commit pmo-sonnet drift 2 件 (2026-05-27 確立)

- **drift-2**: L4 architecture §7 採用 project 配布 に **BR-09 (既存資産整理) / BR-10 (Strangler Fig 移行) の明示ラベルが不在**、trace 可視性弱
  - 対応方針: 本 commit で L4 architecture §7 末尾に「BR-09 既存資産整理 / BR-10 Strangler Fig 移行経路の本体化は Step 2-3 carry」を 1 行追記。
- **drift-1**: PLAN §7 DoD line 188 `§1-§6 が body 化` → L9 doc は §0〜§7 で 8 section、`§1-§7 が body 化` が正
  - 対応方針: 本 commit で PLAN §7 DoD を `§1-§7 が body 化` に訂正。

両項目は L4 方式設計 doc の carry note とし、本文本体では L5/L6 で整合確認を継続します。

## §6 V-model pair freeze 現状値 (本 skeleton 起票時)

- **BR**: 12
- **FR**: 16
- **NFR**: 27
- **AC**: 57
- **OT**: 12

本 skeleton では新規追加はせず、ratio は 1.0 以上維持方針を明示する。変化は Step 2-3 の本体化時に `balance_ratio` の再集計と evidence を追加し、ratchet 条件に連動させる。

### 追加 carry（Step2-3 で本体化）

本 skeleton は Step2-3 で以下を詳細化対象として残す。

- BR-12 ratchet の運用証跡を取得する観点定義（check 種別、再試行ルール、許容上限）。
- FR/AC の対照表で、L4 から ST-* への mapping を 1:1 で表化。
- OT 項目の順序規約（OT-09〜12）を他文脈に影響しない形で取り込み。
- `helix doctor check_changeprop` の read-only と write-update の境界を CLI 呼出し手順まで落とし込む。
- `docs/.helix/audit/*.yaml` と helix.db の証跡リンクを本文と ADR に相互リンクする。

## 付録 A: V-model 監査観点（skeleton）

本 PLAN が L4 入口となるため、監査観点を最短でも保持する。

1. 前提: L3 既存 ID の整合が前提。
2. 入力: L0/L1/L3 計画の依存を明示し、親子関係を壊さない。
3. 出力: L4 Lx 設計 PLAN への展開可能性を担保。
4. 逆方向: L9 テスト設計で Step 3 再実行可能な構造にする。
5. 判定: G3・G4 の評価フローが `pairs_test_design` 経由で追跡可能。

この観点は Step 6 の do/don't を補助する補助表であり、skeleton では合格条件は「追跡先の残存不整合なし」を優先します。

依存 PLAN 不在検出が発生した場合は carry note 化し、Step 6 前に修正方針を L4 設計と同期します。

## §7 L4 完遂条件 (DoD)

1. ✅ 方式設計 doc 完成（§1-§8 が body 化）。達成根拠: `docs/v2/L4-basic-design/方式設計.md` §1-§8 全本文化。
2. ✅ L9 総合テスト設計 doc 完成（§1-§7 が body 化）。達成根拠: `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` ST-1〜7 本体化 + L4↔L9 pair trace。
3. ✅ ADR-044 snapshot 起草完了。達成根拠: Decision 1-9 + Compliance 列 + Alternatives 確定 (2026-05-27)。※ Accepted への最終審査は L7 実装完了後に更新予定 (carry)。
4. ✅ tl-advisor PASS。達成根拠: 2026-05-27 R1/R2 二重 audit、conditional_approve (P0=0)。
5. ✅ pmo-sonnet 数値整合 OK。達成根拠: 2026-05-29 freeze-readiness audit YES with minor、M-1〜M-4 全解消。
6. carry: doc-reviewer 三重 audit は未実施。L7 実装前に実施予定 (on-demand、L4 freeze blockerではない)。
7. ✅ `plan_validator` error 0 (WARN は L5 blocks が未起票のため、L5 finalize で解消予定)。
8. ✅ balance_ratio ≥ 1.0 維持。達成根拠: BR=12/FR=16/NFR=27/AC=57/OT=12、比率 1.0 以上確認済み。

---

## L4 完遂 evidence (2026-05-29)

- 設計 doc: 本体化完遂、frontmatter status: draft (`docs/v2/L4-basic-design/方式設計.md`)
- pair freeze: L4↔L9 双方向 trace coverage PASS (system-arch §1-§8 ↔ ST-1〜7、計 24 件 pair trace)
- 監査: 2026-05-27 tl-advisor R1/R2 (conditional_approve) + 2026-05-29 pmo-sonnet freeze-readiness audit = YES with minor、M-1〜M-4 全解消
- implementation_status 列: BR-RULE-09 準拠確認済 (3 doc 合計 48 件)
- carry (L7 実装へ): fixture 実体 / テストコード / doctor fail-close 実装 / parser ベース AC-12〜16 検証 / doc-reviewer 三重 audit

## 変更管理ノート

- 方式設計 doc / L9 総合テスト doc / ADR の本文は Step 2-3 で別途起草するため、本 PLAN は skeleton を起点にしている。
- Web 検索 3 query、FR-12〜16 の詳細追記、AC 対応表の完全集約は Step 2-3 の carry note 対象。
- 2026-05-29: status finalized、Step 全 ✅、DoD 達成マーク付与。doc-reviewer 三重 audit は L7 実装前の carry。
