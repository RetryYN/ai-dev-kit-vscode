# FR-INV20 Reverse / Scrum 工程現状監査

最終更新: 2026-05-14

## 概要

- 対象:
  - Reverse HELIX: R0-R4 + RGC、5 type matrix、Forward 接続、運用痕跡
  - Scrum HELIX: S0-S4、trigger、`.helix/scrum/`、Forward 接続、運用痕跡
- 目的:
  - V2 §3.8 工程転換の Reverse / Scrum 対応 (`FR-VS07`) の入力を作る
  - 実装済み機能、未接続機能、運用実績の薄い機能を分離して可視化する
- 判定基準:
  - `機能している`: CLI / supporting module / verify or test / docs が揃い、fail-close 動作も確認できる
  - `部分機能`: 実装はあるが、schema 接続・運用痕跡・後段連動が不足
  - `仕組み倒れ`: 枠組みや docs はあるが、実運用または実データ接続が実質見えない
- 注記:
  - `helix` コマンドはこの作業環境で PATH 未設定だったため、`helix code find` などの規定コマンドは実行できず、ファイル読解で代替した
  - `origin_mode` / `evidence_status` は現状要件・助言・監査文書にはあるが、実 schema には未実装
  - 運用実績は `.helix/`、verify、review、retro、cache log に見える痕跡から判断した。見えないものを「なし」と断定できない箇所は「限定」または「不確実」とした

## サマリ

### 推奨

- **推奨方針**: Reverse / Scrum は V2 で廃止ではなく **modify + extend** が妥当
- 理由:
  - CLI とテストの骨格は既にある
  - V2 §3.8 が要求する `functional_freeze`、`origin_mode`、`evidence_status`、design sprint 連携は未接続
  - 特に Scrum confirmed → Forward、Reverse RG2/RG3 → Forward の bridge を schema と gate に落とせば再利用価値が高い

### 選択肢

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| as-is 維持 | 追加工数が最小 | V2 §3.8 / FR-VS07 を満たせない。運用が docs 依存のまま | 低 |
| modify | 既存 CLI/verify を活かして Forward bridge だけ強化できる | schema/gate 改修が必要 | 高 |
| extend | Reverse / Scrum を design sprint / V-model に正規接続できる | 変更点が広い。段階導入が必要 | 高 |
| deprecate | V1 複雑性を減らせる | 既存の Reverse / Scrum asset・test・docs を捨てることになる | 低 |
| new で作り直し | V2 専用 semantics を一から整理できる | 既存投資を捨てる。移行 cost が高い | 低 |

## 監査表

| 項目名 | 実装ファイル | 状態 | 運用実績 | V-model 接続点 | V2 変更計画 | V2 Phase 紐付け | 監査メモ |
|---|---|---|---|---|---|---|---|
| Reverse 全体入口 | `cli/helix-reverse:9-12`, `cli/helix-reverse:38-82` | 機能している | 限定 | `origin_mode=reverse` の入口候補 | modify | Phase 2, §3.8 | `helix reverse <type>` grammar と usage は実装済み |
| Reverse 5 type matrix | `cli/helix-reverse:44-49`, `docs/plans/PLAN-008-reverse-multitype.md:24-30` | 機能している | 限定 | type ごとの sprint / freeze 条件に接続余地 | as-is | Phase 1, Phase 2 | code/design/upgrade/normalization/fullback を実装と PLAN の両方で確認 |
| Reverse code R0 | `cli/helix-reverse:95-98`, `cli/helix-reverse:642`, `verify/010-helix-reverse.sh:23-25` | 機能している | 限定 | `observed` 候補 | modify | Phase 2, Phase 3 | dry-run smoke あり。観測証拠の YAML 出力先も固定 |
| Reverse code R1 | `cli/helix-reverse:99-102`, `cli/helix-reverse:643`, `docs/commands/reverse.md:51-53` | 機能している | 限定 | `observed` 候補 | modify | Phase 2, Phase 3 | observed contracts 概念は明確だが DB record 化は未実装 |
| Reverse code R2 | `cli/helix-reverse:103-106`, `cli/helix-reverse:589-590`, `docs/commands/reverse.md:52-53` | 機能している | 限定 | `inferred` 候補、RG2 | extend | Phase 2, §3.8 | As-Is 設計復元はあるが `functional_freeze` 接続なし |
| Reverse code R3 | `cli/helix-reverse:107-110`, `cli/helix-reverse:591`, `docs/commands/reverse.md:53-55` | 部分機能 | なし | `confirmed` 候補、RG3 | extend | Phase 2, §3.8 | intent hypothesis まではあるが PO 確認結果の永続化がない |
| Reverse code R4 | `cli/helix-reverse:111-114`, `cli/helix-reverse:646`, `docs/commands/reverse.md:73-89` | 機能している | 限定 | Forward routing | extend | Phase 2, §3.8 | L1/L2/L3/L4 へ routing する docs は強い |
| Reverse design R0 | `cli/helix-reverse:115-118`, `cli/helix-reverse:647`, `docs/commands/reverse.md:56-58` | 機能している | なし | design evidence 起点 | modify | Phase 2 | 実装あり。運用痕跡は未確認 |
| Reverse design R1 skip | `cli/helix-reverse:119-123`, `cli/helix-reverse:457-460`, `cli/tests/test-helix-reverse-multitype.bats:67-80` | 機能している | あり | RG1 非適用 | as-is | Phase 2 | skip を help / validator / test で固定できている |
| Reverse design R2 | `cli/helix-reverse:124-127`, `cli/helix-reverse:648`, `docs/commands/reverse.md:56-58` | 部分機能 | なし | architecture / detailed 側への bridge 候補 | extend | Phase 2, §3.8 | DAG 出力はあるが design sprint table へ未接続 |
| Reverse design R3 | `cli/helix-reverse:128-131`, `cli/helix-reverse:649`, `cli/helix-reverse:447-450` | 部分機能 | なし | impl-order → sprint_type 候補 | extend | Phase 2, §3.8 | topological sort option はあるが downstream 連携なし |
| Reverse design R4 | `cli/helix-reverse:132-135`, `cli/helix-reverse:650`, `cli/helix-reverse:595` | 部分機能 | なし | routing → Forward | extend | Phase 2, §3.8 | gate mapping が `RGC` に寄っており naming の再整理が必要 |
| Reverse upgrade flow | `cli/helix-reverse:136-155`, `cli/helix-reverse:651-655`, `docs/commands/reverse.md:56-58` | 機能している | なし | Forward 前の impact 評価 | modify | Phase 2 | assessment-only 境界は明確 |
| Reverse upgrade RGC skip | `cli/helix-reverse:202`, `cli/helix-reverse:465-468`, `docs/commands/reverse.md:56-58` | 機能している | あり | Forward routing のみ | as-is | Phase 2 | PLAN-008 方針どおり skip を validator で強制 |
| Reverse normalization flow | `cli/helix-reverse:156-175`, `cli/helix-reverse:656-659`, `docs/commands/reverse.md:56-58` | 機能している | なし | drift → Forward routing | modify | Phase 2 | 実装あり、運用痕跡は未確認 |
| Reverse normalization R1 skip | `cli/helix-reverse:160-163`, `cli/helix-reverse:461-464`, `cli/tests/test-helix-reverse-multitype.bats:82-88` | 機能している | あり | RG1 非適用 | as-is | Phase 2 | skip の仕様化と test は揃う |
| Reverse fullback flow | `cli/helix-reverse:177-195`, `cli/helix-reverse:660-664`, `docs/commands/reverse.md:82-83` | 部分機能 | なし | L8-L11 / docs alignment | extend | Phase 2, Phase 5 | 文書整合用として有望だが実運用痕跡がない |
| Reverse gate status 管理 | `cli/helix-reverse:500-516`, `cli/helix-reverse:842-875` | 機能している | 限定 | RG0-RG3/RGC status | modify | Phase 2, Phase 4 | phase.yaml に gate 状態を書ける |
| Reverse prerequisite fail-close | `cli/helix-reverse:1094-1103`, `verify/010-helix-reverse.sh:27-33` | 機能している | あり | gate prerequisite | as-is | Phase 4 | 前段 gate 未通過で fail-close |
| Reverse output validation | `cli/helix-reverse:1033-1076` | 機能している | 限定 | artifact quality | as-is | Phase 4 | YAML 非空 mapping / Markdown 最低長で validation |
| Reverse review artifact (`--review`) | `cli/helix-reverse:63-69`, `cli/helix-reverse:669-706`, `.helix/cache/plan029-w12/reverse-r0.log:1-8` | 部分機能 | 限定 | design_review 候補 | extend | Phase 3, Phase 5 | JSON artifact は出せるが `design_review` table 未接続 |
| Reverse RGC code | `cli/helix-reverse:903-983`, `docs/commands/reverse.md:91-100` | 機能している | 限定 | gap closure | modify | Phase 2, §3.8 | R4 gap register 集計はあるが V-model score には未統合 |
| Reverse RGC design | `cli/helix-reverse:985-999`, `cli/tests/test-helix-reverse-multitype.bats:90-96` | 部分機能 | あり | design routing closure | modify | Phase 2 | fail-close はあるが受入注記の表示だけで自動判定は弱い |
| Reverse RGC generic (normalization/fullback) | `cli/helix-reverse:1001-1031` | 部分機能 | なし | deferred finding / close note | extend | Phase 2, Phase 5 | 案内文はあるが structured close 判定が薄い |
| Reverse stage-to-role dispatch | `cli/helix-reverse:568-581` | 機能している | 限定 | Research / TL / SE の role 境界 | as-is | Phase 5 | design R0=research など妥当な分配 |
| Reverse observed/inferred/confirmed lifecycle | `docs/v2/L1-REQUIREMENTS.md:128`, `docs/v2/L1-REQUIREMENTS.md:457-458` | 仕組み倒れ | なし | `origin_mode`, `evidence_status` | new | Phase 1, Phase 3, §3.8 | 要件はあるが実 schema / writer がない |
| Reverse → Forward invalidation | `cli/helix-reverse:518-524`, `docs/commands/reverse.md:85-89` | 部分機能 | なし | G2-G11 invalidation | modify | Phase 4 | code type 限定。Reverse 全 type に一般化されていない |
| Reverse 実運用痕跡 | `.helix/retros/2026-05-04-G4-PLAN-008.md:1-21`, `.helix/cache/plan029-w12/reverse-r0.log:1-8` | 部分機能 | 限定 | bridge 実績 | modify | Phase 1 | docs/test/dry-run 痕跡はあるが本番案件の継続運用は薄い |
| Scrum 全体入口 | `cli/helix-scrum:4-5`, `docs/commands/scrum.md:17-27` | 機能している | 限定 | `origin_mode=scrum` 入口候補 | modify | Phase 2, §3.8 | S0-S4 の基本線は安定 |
| Scrum S0 init | `cli/helix-scrum:30-60`, `verify/009-helix-scrum.sh:19-21` | 機能している | あり | scrum mode 初期化 | as-is | Phase 2 | backlog/sprint/verify dir を生成 |
| Scrum backlog add/list | `cli/helix-scrum:63-158`, `verify/009-helix-scrum.sh:23-29` | 機能している | あり | hypothesis 起点 | as-is | Phase 2 | verify script 雛形まで自動生成 |
| Scrum S1 plan | `cli/helix-scrum:160-197`, `verify/009-helix-scrum.sh:31-33` | 機能している | あり | sprint_id 候補 | modify | Phase 2, §3.8 | current_sprint と hypothesis status を更新 |
| Scrum S2 poc | `cli/helix-scrum:199-242` | 部分機能 | なし | PoC → verify → delegate | modify | Phase 2, Phase 5 | `helix-codex` 委譲はあるが運用痕跡は未確認 |
| Scrum S3 verify | `cli/helix-scrum:245-309`, `verify/009-helix-scrum.sh:34-50` | 機能している | あり | regression baseline 候補 | modify | Phase 2, Phase 3 | 全 verify/*.sh を回して fail-close |
| Scrum S4 confirmed gate | `cli/helix-scrum:314-365`, `docs/commands/scrum.md:29-31` | 機能している | あり | `confirmed` 起点 | extend | Phase 2, §3.8 | verify 成功必須で強い |
| Scrum strict-promote | `cli/helix-scrum:381-405`, `cli/helix-test:1191` | 部分機能 | 限定 | productionization checklist | modify | Phase 2, Phase 5 | warning 中心で gate ではない |
| Scrum confirmed → handoff | `cli/helix-scrum:407-488`, `docs/commands/scrum.md:84-94` | 部分機能 | あり | Forward contract 生成前段 | extend | Phase 2, §3.8 | handoff/task/plan draft 生成まで、schema 書込なし |
| Scrum review | `cli/helix-scrum:505-591` | 機能している | なし | sprint closure | modify | Phase 2, Phase 4 | verify fail-close で sprint 完了を防ぐ |
| Scrum status | `cli/helix-scrum:593-629`, `verify/009-helix-scrum.sh:56-58` | 機能している | あり | sprint / backlog 可視化 | as-is | Phase 2 | 現状把握として十分 |
| Scrum trigger engine | `cli/helix-scrum:631-636`, `cli/lib/scrum_trigger.py:19-58`, `cli/lib/tests/test_scrum_trigger.py:57-93` | 機能している | 限定 | trigger → sprint_type 候補 | extend | Phase 2, §3.8 | 5 type, 4象限, DB persistence を持つ |
| Scrum trigger persistence | `cli/lib/scrum_trigger.py:30-58`, `docs/plans/PLAN-007-scrum-multitype-trigger.md:125-150` | 部分機能 | 限定 | `design_sprint_entries` 前段 | modify | Phase 3 | 独自 table はあるが design sprint schema と別系統 |
| Scrum trigger redaction | `cli/lib/scrum_trigger.py:60-66`, `cli/lib/tests/test_scrum_trigger.py:96-112` | 機能している | あり | audit-safe evidence | as-is | Phase 4 | raw body 非保存を test で確認 |
| Scrum trigger lifecycle | `cli/lib/scrum_trigger.py:19-28`, `cli/lib/tests/test_scrum_trigger.py:128-187` | 機能している | あり | pending→triaged→adopted | modify | Phase 3, Phase 4 | lifecycle はあるが Forward gate 連動は弱い |
| Scrum trigger → backlog adopt | `cli/lib/tests/test_scrum_trigger.py:141-151` | 機能している | 限定 | trigger 起点 hypothesis | modify | Phase 2 | adopted 時の backlog 化を test で確認 |
| Scrum web-search | `cli/helix-scrum:639-702`, `cli/tests/test-helix-scrum-extended.bats:23-47`, `.helix/scrum/research/H001/20260508-052216.md:1-12` | 部分機能 | 限定 | research evidence | modify | Phase 1, Phase 2 | placeholder 保存まではあるが実 Web 連携ではない |
| Scrum acceptance-design | `cli/helix-scrum:705-777`, `cli/tests/test-helix-scrum-extended.bats:49-53` | 部分機能 | 限定 | confirmed 後の contract 設計前段 | modify | Phase 1, Phase 2 | テンプレ生成はあるが gate / DB 連動なし |
| Scrum confirmed → Forward contract 生成 | `docs/v2/L1-REQUIREMENTS.md:286`, `docs/commands/scrum.md:86-94` | 仕組み倒れ | なし | `origin_mode=scrum`, sprint 開始 | new | Phase 3, §3.8 | 要件上は必要だが現実装は handoff/task/plan draft 止まり |
| Scrum 実運用痕跡 | `.helix/scrum/research/H001/20260508-052216.md:1-12`, `.helix/cache/plan029-w12/scrum.log:1-2` | 部分機能 | 限定 | 研究メモのみ | modify | Phase 1 | 実案件の confirmed / review / multi-sprint 痕跡は薄い |

## 観察事項

### Reverse HELIX

1. 5 type と type 別 skip / RGC 方針は、CLI・docs・test が揃っており V1 capability としては成立している。
2. ただし `observed / inferred / confirmed` は語彙としては存在しても、`contract_entries` や `design_review` へ記録されないため、V-model から見ると lifecycle が不在。
3. `design`, `normalization`, `fullback` は help / validator / RGC 入口まである一方、運用痕跡がほぼ見えず、実装済みでも「仕組み倒れ寄りの部分機能」が混ざる。
4. `cli/helix-reverse:584-607` の gate mapping では `design:R4 -> RGC` など、stage と gate の意味がやや混線しており、V2 の `functional_freeze` 接続時に再定義が必要。
5. Reverse review artifact (`--review`) は、将来 `design_review.direction='reverse'` に接続しやすい種だが、今は JSON を置くだけで閉じている。

### Scrum HELIX

1. S0-S4 は verify fail-close を伴うため、PoC Scrum としての骨格は Reverse より運用度が高い。
2. confirmed 後に `.helix/scrum-handoff.md`、`.helix/tasks/scrum-<HID>-forward.md`、promotion plan draft を作る実装はあるが、V2 §3.8 が求める「Forward contract 生成と同時に sprint 開始」には達していない。
3. trigger engine はむしろ V1 の中では先進的で、5 type、4象限、TTL、dedup、redaction、backlog adopt まで揃っている。
4. ただし trigger は独自 DB / backlog に閉じ、`design_sprint_entries` や `contract_entries.origin_mode='scrum'` に昇格しないため、V-model の中心線には入っていない。
5. `.helix/scrum/research/H001/...` と cache log に見える運用痕跡は smoke / placeholder 性が強く、実案件の長期運用 evidence は薄い。

## V-model 強化との接続点

### 1. Reverse で `origin_mode='reverse'` / `evidence_status` を扱う schema 必要性

- 必要性: 高
- 根拠:
  - Reverse R0/R1 は `observed`、R2 は `inferred`、R3 を経て `confirmed` に近づく概念を既に docs が要求している
  - しかし実 schema は `design_level` までで止まり、起源と確度を記録できない (`cli/lib/helix_db.py:587-599`)
- 推奨:
  - `contract_entries.origin_mode` と `contract_entries.evidence_status` を追加し、R0/R1/R2/R3 の writer を段階導入する

### 2. Scrum で `origin_mode='scrum'` confirmed 後の contract 生成パターン

- 必要性: 高
- 現状:
  - confirmed 後に handoff/task/plan draft は出る
  - contract record 生成は未実装
- 推奨:
  - `decide --confirmed` 成功時に `contract_entries` へ仮登録するのではなく、Forward 側の `plan finalize` または `functional_freeze` 開始時に正式登録する
  - その際 `origin_mode='scrum'`, `evidence_status='confirmed'`, `origin_ref=<HID>` を付与する

### 3. Reverse の RG2/RG3 と Forward `G3.functional_freeze` の関係

- 現状:
  - Reverse R2/R3 は As-Is 設計と intent hypothesis を扱う
  - V2 §3.8 では `G3.functional_freeze` が size / drive 条件付きで必須
- 推奨:
  - Reverse のすべてに `functional_freeze` を課すのではなく、`R4-gap-register` に `requires_functional_freeze: true/false` を追加する
  - `FR-VS07` の要件どおり、必要 gap のみ Forward functional sprint に昇格する

### 4. Scrum の confirmed と `sprint_type='impl'` 起動条件

- 現状:
  - confirmed は hypothesis status と handoff 生成で終わる
  - `design_sprint_entries` は未実装
- 推奨:
  - confirmed 後に即 `impl` を始めるのではなく、まず contract / acceptance を Forward 化し、size / drive 判定後に `sprint_type=architecture|detailed|functional|impl` のどこから始めるかを決める
  - S/M/L と drive に応じて `impl` 直行を許すのは S 案件のみが妥当

## 完成度評価

### Reverse 5 type 別 完成度 (%)

| type | 完成度 | 根拠 |
|---|---:|---|
| code | 80 | R0-R4/RGC、status、prereq、validation、docs、verify がある |
| design | 68 | R1 skip と RGC fail-close まであるが実運用痕跡が薄い |
| upgrade | 72 | assessment-only 境界が明快、RGC skip も強制。運用痕跡は薄い |
| normalization | 66 | flow はあるが実運用 / output 実例が見えない |
| fullback | 58 | docs alignment の思想は強いが、実運用と structured closure が弱い |

**Reverse 総合完成度: 69%**

### Scrum 完成度 (%)

| 領域 | 完成度 | 根拠 |
|---|---:|---|
| S0-S4 core flow | 82 | init/backlog/plan/verify/decide/review/status が揃う |
| trigger engine | 78 | 5 type、DB、TTL、dedup、redaction、test がある |
| research / acceptance adjunct | 50 | placeholder / template 中心 |
| Forward bridge | 56 | handoff/task/plan draft まで。contract / sprint schema 未接続 |

**Scrum 総合完成度: 67%**

### Reverse / Scrum 運用実績 件数

- Reverse:
  - 明示 PLAN / review / retro 痕跡: 1 件以上 (`PLAN-008`, review JSON, G4 retro)
  - 実行 cache / dry-run 痕跡: 1 件以上 (`.helix/cache/plan029-w12/reverse-r0.log`)
- Scrum:
  - 研究メモ / cache 痕跡: 1 件 (`.helix/scrum/research/H001/...`, `.helix/cache/plan029-w12/scrum.log`)
  - confirmed 後の実案件昇格 evidence: 0 件を確認

## V2 で強化すべき項目 top-5

1. `contract_entries.origin_mode` / `evidence_status` の schema 追加と writer 実装
2. Scrum confirmed → Forward contract / design sprint 起動の bridge 実装
3. Reverse R4 gap register と `G3.functional_freeze` の条件連携
4. Reverse review artifact / Scrum handoff を `design_review` / `design_sprint_entries` に正規接続
5. design / normalization / fullback の実運用 evidence 収集と fail-close 基準の concretize

## §3.8 工程転換 (FR-VS07) で対応すべき具体要件

1. Reverse:
   - `RG2` / `RG3` の結果から、Forward へ渡す gap に `required_sprint_type` と `requires_functional_freeze` を付与する
   - `origin_mode='reverse'`、`evidence_status='observed|inferred|confirmed'` を contract / review record に保存する
2. Scrum:
   - `confirmed` までは design sprint 対象外とし、confirmed 後にだけ Forward artifact を生成する
   - `origin_mode='scrum'` と `origin_ref=<HID>` を保存できる bridge を追加する
3. Gate:
   - `helix gate G3 --subgate functional_freeze` が Reverse/Scrum 起源 artifact を理解できるようにする
   - `pair_status` を Reverse/Scrum bridge でも `pending/design_only/test_only/paired/waived/failed` で統一する
4. Automation:
   - Reverse `--review` JSON と Scrum handoff/task を PostToolUse / sync / gate のいずれかで DB へ auto-register する

## ソース

- Reverse 実装: `cli/helix-reverse`, `docs/commands/reverse.md`, `docs/plans/PLAN-008-reverse-multitype.md`
- Scrum 実装: `cli/helix-scrum`, `cli/lib/scrum_trigger.py`, `docs/commands/scrum.md`, `docs/plans/PLAN-007-scrum-multitype-trigger.md`
- V2 要件: `docs/v2/L1-REQUIREMENTS.md` §3.1, §3.3, §3.8
- 運用痕跡: `.helix/retros/2026-05-04-G4-PLAN-008.md`, `.helix/cache/plan029-w12/reverse-r0.log`, `.helix/cache/plan029-w12/scrum.log`, `.helix/scrum/research/H001/20260508-052216.md`
