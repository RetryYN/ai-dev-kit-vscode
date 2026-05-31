---
plan_id: refactor-2026-06-01-folder-structure-g-p-separation
title: "refactor-2026-06-01: HELIX 本体フォルダ構成の G/P 住所分離 (実装=G本体 / 計画=Pプロジェクト)"
kind: refactor
layer: L7
drive: be
status: draft
owner: PM
created: 2026-06-01
generates: []
protects:
  - artifact_path: cli/lib/tests/
    artifact_type: test
  - artifact_path: cli/tests/
    artifact_type: test
verification:
  behavior_unchanged: true
  tests:
    - "python3 -m pytest cli/lib/tests/ -q"
    - "cli/helix test --no-pytest --bats-only"
    - "python3 -m pytest cli/lib/tests/test_core_manifest_drift.py -q"
---

# Refactor: HELIX 本体フォルダ構成の G/P 住所分離

> **整理原則（本 PLAN の背骨）**: 実装（配布物 = G tier）は HELIX 本体の住所に、計画・設計記録（P tier）はプロジェクト側の住所に置く。正本と副本・配布物と dogfooding を住所で分離し、二重化と分類漏れを構造的に防ぐ。
>
> 本 PLAN 自身が `docs/plans/`（P tier）に置かれているのは、この原則の実践。

## 0. 進め方（このPLANの位置づけ）

- 本 PLAN は **計画のみ**（起票時点で実行しない）。実行は別セッションで段階的に行う。
- **本 PLAN 自身は P tier（計画・設計記録）であり `docs/plans/`（配布されない P 住所）に置く**（配布面分離・ブランチ戦略は Phase 0 で park、本 PLAN のスコープは Phase 1-3 のフォルダ整理に縮小）。
- 各段階の着手前に保護網テスト green を確認し、段階内で振る舞い不変を維持する。
- **高リスク段階（Phase 3: docs/v2/process 正本二重化解消）は着手前に tl-advisor 諮問必須**。破壊的（参照 path 多数に波及・配布物の構造変更）のため PM 単独で確定しない。
- 設計内容（どの doc に何を書くか）は本 PLAN に書かない。本 PLAN は手順・要点・判断ポイントのみ（PLAN の役割）。

## 1. 振る舞い不変の宣言

このリファクタで以下は変わらない:

- 配布される実装（`cli/` の CLI 挙動、`helix/` core doc の内容、`HELIX-workflows/` 工程定義の内容）の振る舞い。
- 常時注入 core セット（`helix/core-manifest.tsv` が定める 5 import）の解決結果。
- 公開 API（`@~/.helix/core/<path>` import パス）。ファイル移動を伴う場合は参照を追従更新し、import 解決結果を不変に保つ。
- 全テスト（pytest / bats）の green 状態。

## 2. 保護網テスト

着手前に green を確認する:

- `python3 -m pytest cli/lib/tests/ -q`
- `cli/helix test --no-pytest --bats-only`
- `python3 -m pytest cli/lib/tests/test_core_manifest_drift.py -q`（manifest⇔setup.sh⇔loader drift ガード）
- ファイル移動を伴う段階では、移動対象を参照する test / bats / CLI を事前 grep で特定し、保護網に含める。

## 3. 現状の構造的問題（2026-06-01 フォルダ構成監査の検出）

| # | 重大度 | 問題 | 実態 |
|---|---|---|---|
| P1 | 高 | **L 工程 doc の正本二重化** | `HELIX-workflows/helix-process/L*.md`（正本・配布 G）と `docs/v2/process/L00-L14-*.md`（15 本）が別命名で並存。CLAUDE.md は「正本は HELIX-workflows」と宣言するが `docs/v2/process/` の位置付け（正本コピー or dogfooding 設計記録）が曖昧 = drift 温床。本 session で粒度原則を両方に書く二重作業が発生したのが実害例。 |
| P2 | 中 | **1 ファイル top-dir** | `harness/`（`g4-gate-harness.yaml` 1 本）/ `workflows/`（`l4-sprint-workflow.yaml` 1 本）。両者とも CLAUDE.md の G/P/S/B 分類表に未記載。`HELIX-workflows/` か `cli/templates/` への吸収候補。 |
| P3 | 低 | `public/` 実体なし（`generated/` のみ gitignore、dir 自体は追跡）/ `.commitlintrc.json` が分類表（B tier）に未記載 / `verify-output.txt` gitignore 漏れ（現時点 untracked 解消済、再発防止に gitignore 追加要検討）。 |
| P0※ | park | **ブランチ未分離（main = 配布面に P が混在）**。消費側は repo を丸ごと clone するため `main` が配布面そのもの。`docs/plans/`（多数）・`docs/v2/`・project `CLAUDE.md` 等の P tier が `main` に載り、配布 framework と dogfooding 作業場が同一に混ざる。runtime 注入は `core-manifest.tsv` で抑制済みだが、配布体験・探索性・誤読リスクで負ける。**→ 本 refactor では扱わない**: 解決策（配布面分離 / dist publish）は distribution architecture migration であり、L4 設計 + ADR + ユーザー承認を要する（Phase 0 park 参照）。 |

## 4. 段階的リファクタ手順

> 原則: G/P 住所分離。配布物（G）は HELIX 本体住所へ集約、計画・設計記録（P）はプロジェクト住所へ。各 Phase 独立コミット、各 Phase 後にテスト green。

### Phase 0（配布面分離 / distribution architecture）— 本 refactor スコープ外・park（凍結）

> **この Phase は本 refactor PLAN のスコープから除外し凍結する。** 配布面分離（monorepo vs dist publish、ブランチ戦略）は構造改善（refactor / L7）ではなく **distribution architecture migration** であり、Forward の L4（基本設計）+ ADR を通すべき判断（本 PLAN 89 行の自己認識どおり）。
>
> **経緯**: 未承認・V2 移行スコープ外の「戦略C（monorepo + dist publish）」を、ADR も L4 設計も経ずに常時注入 context（project CLAUDE.md / PM memory）へ「確定」として記述した結果、毎 session PM が dist publish を優先 backlog として誤って復唱する context injection（自己永続ドリフト）が発生した。その収束は [recovery-2026-06-01-context-injection-dist-strategy](../recovery/recovery-2026-06-01-context-injection-dist-strategyplan.md) を正本とする。
>
> **着手の前提条件（3 つ揃うまで実装禁止）**:
> 1. 配布戦略の **L4 基本設計 PLAN**（住所は `docs/v2/L4-.../` または `docs/design/`。CLAUDE.md 等の常時注入 context には戦略本文を置かず、ポインタのみ）。
> 2. **ADR**（dist 配布方式の不可逆判断。`docs/adr/ADR-0xx-helix-distribution-architecture.md`）。
> 3. **ユーザー明示承認**。
>
> **関連孤児**: PLAN-218（npm/pip package export、`is_reference:true`、実体なし ADR-057 を参照）は distribution architecture 確定まで park。新 distribution PLAN/ADR 起票時に supersede / 廃止を判断する。
>
> 本 PLAN は以降 **Phase 1-3（フォルダ整理 / 住所明示）に縮小**する。配布構造そのものは扱わない。

### Phase 1（低リスク・即実行可）

1. `.commitlintrc.json` を CLAUDE.md top-dir 分類表（B tier）に追記。
2. `public/` の扱いを決定（`.gitignore` に `public/` 追加 or 意図を README/.gitkeep で明示）。
3. `verify-output.txt` 等の生成物を `.gitignore` に追加（再発防止）。

リスク: ほぼなし（doc + gitignore のみ、コード参照に影響しない）。

### Phase 2（中リスク・参照追従が必要）

1. `harness/g4-gate-harness.yaml` / `workflows/l4-sprint-workflow.yaml` の参照元を全 grep（CLI / bats / py / doc）。
2. 参照ゼロまたは追従可能なら、`HELIX-workflows/` または `cli/templates/` の適切な住所へ移動し、参照を追従更新。top-dir `harness/` `workflows/` を廃止。
3. CLAUDE.md 分類表を更新。

リスク: 参照 path の追従漏れ → CLI / test の breakage。緩和: 移動前 grep で全参照特定 + 移動後にテスト green 確認。

### Phase 3（高リスク・tl-advisor 諮問必須・破壊的）

1. **tl-advisor 諮問**: `docs/v2/process/L*.md`（15 本）の正本扱いを廃止すべきか、どう分離するか。選択肢: (a) `HELIX-workflows/helix-process/` 正本に一本化（副本削除）/ (b) dogfooding 設計記録（P）として `docs/v2/` 内に明示隔離し「正本ではない」と frontmatter 明記。
2. TL 判定に従い、G（配布正本）と P（dogfooding 記録）の住所を分離。
3. 参照（CLAUDE.md / AGENTS.md / test / 他 doc のリンク）を追従更新。
4. `document-topology.md` を実態に同期（本 session で 2 BC を追記済、Phase 3 後に再整合）。

リスク: docs 参照構造全体に波及・配布物構造変更。緩和: TL 判定を起点に段階実行、各段階で参照 grep + テスト green。

## 5. 振る舞い不変の検証

各 Phase 後に実行:

- §2 保護網テスト全 green。
- `git grep` で移動対象への参照切れ（dead link）がゼロ。
- 配布契約: `python3 -m pytest cli/lib/tests/test_core_manifest_drift.py -q` で manifest⇔setup.sh⇔loader 一致維持。
- `bash -n setup.sh` / 変更 Python の `py_compile`。

## 6. Forward 復帰接続先

- フォルダ構成の構造改善は主に L7（実装）の構造改善 → Forward L7 へ復帰。
- `docs/v2/process` の正本二重化解消（Phase 3）は設計レベルの整理 → L4-L6 の document-topology 整合として Forward へ反映。
- 完了時、`folder-structure-review.md` と `document-topology.md` を実態に同期し、CLAUDE.md 保存先ルール（G/P/S/B 分類表）を最新化。

## 7. リスクと緩和

| リスク | 影響 | 緩和 |
|---|---|---|
| 配布物の path 移動 = 公開 API 破壊 | 消費側 loader 参照切れ | core ファイル（manifest 記載の 5 本）は移動しない。移動は非 core の整理に限定。やむを得ない場合は document-topology の将来移動 policy（メジャー境界 + shim）に従う。 |
| 参照追従漏れ | CLI / test breakage | 各 Phase 移動前に全参照 grep、移動後テスト green を gate に。 |
| Phase 3 を PM 単独で確定 | 設計判断の誤り・大規模 drift | tl-advisor 諮問を Phase 3 着手の必須 entry 条件にする。 |
| スコープ無限拡大 | recovery 暴走の再発 | 本 PLAN の P1/P2/P3 以外に手を広げない。新規発見は carry 化し本 PLAN に追記、勝手に実行しない。 |
