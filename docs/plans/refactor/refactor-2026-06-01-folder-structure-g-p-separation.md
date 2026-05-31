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
- **本 PLAN 自身は P tier（計画・設計記録）であり `dogfood` ブランチに置く**（main = 配布面には載せない、Phase 0 参照）。
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
| **P0** | **最高** | **ブランチ未分離（main = 配布面に P が混在）**。消費側は repo を丸ごと clone するため `main` が配布面そのもの。`docs/plans/`（多数）・`docs/v2/`・project `CLAUDE.md` 等の P tier が `main` に載り、配布 framework と dogfooding 作業場が同一に混ざる。runtime 注入は `core-manifest.tsv` で抑制済みだが、配布体験・探索性・誤読リスクで負ける。tl-advisor 判定（2026-06-01, changes_required）。 |

## 4. 段階的リファクタ手順

> 原則: G/P 住所分離。配布物（G）は HELIX 本体住所へ集約、計画・設計記録（P）はプロジェクト住所へ。各 Phase 独立コミット、各 Phase 後にテスト green。

### Phase 0（配布面分離・最高優先・破壊的）— 戦略C 確定 (2026-06-01)

消費側は repo を丸ごと clone するため `main` が配布面そのもの。配布 framework と dogfooding（P）の混在を解消する。

**確定戦略 = C（monorepo + dist publish）。ユーザー判断で確定 (2026-06-01)。**

> 補足（判断の経緯・正直な記録）: tl-advisor は第 1 ラウンドで「A 暫定 + C 後送り」、第 2 ラウンドで「**B-canonical（新 repo `helix-framework` を G 唯一正本にし現 repo を P/dogfood へ降格）**」を推奨に変えた。一方ユーザーは **戦略C を最終選択**。C は「現 repo を分割せず monorepo に G+P を保ち、release で G+B のみを dist 配布」する案で、B の「G を別 repo へ移す」とは異なる。ユーザー選好が最終決定。C を採る根拠: ①repo を 1 つに保つので G の単一正本性が維持される（drift しない、本 session の core-manifest SSoT 化と整合）②`docs/v2/` dogfooding が同一 repo に残り L0-L14 trace が切れない ③B の installer 契約破壊・履歴分断を回避。代償: dist publish の release automation が必要（P1）。

**戦略C の構成**:
- **monorepo（現 `ai-dev-kit-vscode`）= G の単一正本 + P（dogfooding）**。製造元はここで作業。
- **dist（artifact または別 `helix-dist` repo）= G+B のみを release で publish**。消費側はこれを取得。**dist の G は monorepo から自動生成され、人手編集しない（generated mirror、drift 防止）**。
- 公開 API `@~/.helix/core/<path>` は維持。setup.sh は dist 側 layout を `@~/.helix/core/...` に合わせ、消費側は dist root を `~/.helix/core` に張る。

**段階内タスク**:
1. **(本 session 実施済 / 暫定)** 現 main から `dogfood` を作成し、P 差分（本 PLAN + project `CLAUDE.md` の G/P 原則追記）を退避 commit（`db721fd`、未 push）。**戦略C では monorepo 1 つに G+P を保つため、dogfood ブランチ分離は C の必須要素ではない**。本退避は session 区切りの一時措置であり、C の dist 設計時に「dogfood を畳んで main 単一運用へ戻す / dogfood を残す」を再判断する。
2. **(別 session, P1)** dist publish を設計・実装。`helix release dist` 相当で G+B allowlist を抽出し artifact 化または `helix-dist` repo へ push（generated mirror、人手編集禁止）。
3. **(別 session, P1)** setup.sh を dist 対応に（dev=monorepo / consumer=dist の 2 モード）。公開 API path は不変に保つ。
4. **(別 session, P1)** dist の clean さを CI で gate（dist に P path が混入しないこと、core-manifest drift test、clean clone setup smoke）。
- **G 側昇格**: 「配布物は P を含まない」という消費側にも関わる短い契約は、別 commit で G 側（`README.md` / `AGENTS.md` / `helix/` 配下の配布方針文書）へ昇格してよい。

**本件の性質**: repo/配布構造の変更は refactor でなく **distribution architecture migration**。tl-advisor 指摘どおり、P1 着手前に **ADR（dist 配布方式の不可逆判断）+ migration PLAN** を起票し、ユーザー承認を得てから実行する。

リスク: 既存 push 済み G commit（`525b1b1`）・installer 契約（setup.sh の repo root symlink 前提）・release provenance に波及。緩和: 破壊的操作（dist repo 新設 / installer 変更 / publish 自動化）は本 session で行わず、ADR + migration PLAN 起票 → ユーザー承認 → P1 で段階実施。本 session は戦略確定と記録まで。

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
