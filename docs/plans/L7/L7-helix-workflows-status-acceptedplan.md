---
plan_id: L7-helix-workflows-status-acceptedplan
title: "L7-helix-workflows-status-acceptedplan: HELIX-workflows/helix-process 46 file の status frontmatter draft → accepted 一括 retrofit"
kind: retrofit
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — batch script 作成・dry-run 検証・46 file 一括 apply"
  - role: pmo-sonnet
    slot_label: "PMO — 除外 list 妥当性確認・frontmatter syntax 全件 lint・完遂 report"
generates:
  - artifact_path: scripts/retrofit-helix-workflows-status.py
    artifact_type: script
  - artifact_path: HELIX-workflows/helix-process/
    artifact_type: doc_update
dependencies:
  parent: null
  requires:
    - L7-vmodel-semantics-injection-setplan
    - L7-docs-integration-mappingplan
  blocks: []
related_docs:
  - HELIX-workflows/HELIX-process-L0-L14.md
  - HELIX-workflows/helix-process/integration-map.md
  - docs/plans/L7/L7-vmodel-semantics-injection-setplan.md
  - docs/plans/L7/L7-helix-recover-implplan.md
  - docs/plans/L7/L7-helix-route-implplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント (retrofit)
> **正本設計**: [HELIX-workflows/HELIX-process-L0-L14.md](../../../HELIX-workflows/HELIX-process-L0-L14.md)
> **本 PLAN の対象**: `HELIX-workflows/helix-process/` 配下 46 file の frontmatter `status: draft` を `status: accepted` へ一括更新する機械的 retrofit。`accepted_date: 2026-05-24` を同時追加する。

### 目的と背景

2026-05-24 commit `ee1a13a` による V2 完全移行で HELIX-workflows が正本化された。しかし各 process doc の frontmatter `status` は `draft` のままである。この状態は以下の問題を引き起こす:

1. **parent_design draft 採用の根拠文書化**: L7-helix-recover-implplan / L7-helix-route-implplan 等の実装 PLAN が `parent_design (draft status) を採用する理由` セクションを設けて例外説明を記述している。本 PLAN 完遂により例外記述が不要になる
2. **helix doctor / plan_validator の整合性**: parent_design が draft のまま実装 PLAN が accepted になることを将来の lint が警告する可能性がある
3. **V2 完全移行の最終 step**: 「正本化 = 設計凍結 = status accepted」というセマンティクスを担保する

### retrofit kind を使う理由

- 既存 doc の内容変更なし、frontmatter metadata のみ更新 = retrofit kind が適合
- refactor (振る舞い不変の構造改善) とは区別: refactor はコード構造、retrofit は依存・基盤・設定の段階改修
- V5 framework 確立済の種別正規化に従う

### 凍結条件の根拠

以下のカテゴリ別に「設計凍結済」判断:

| カテゴリ | 件数 | 凍結根拠 |
|---|---|---|
| L0-L14 工程 doc | 15 件 | HELIX-process-L0-L14.md 親 + V2 完全移行 commit ee1a13a で内容確定 |
| 9 mode workflow doc | 9 件 | 同上 (forward/scrum/discovery/reverse/incident/add-feature/refactor/retrofit/research/recovery) |
| 工程専門 doc | 2 件 | screen-design-workflow / frontend-design-workflow |
| 管理・自動化基盤 doc | 20 件 | integration-map 等の設計凍結済 (§2.A で除外 list を精査) |
| **合計** | **46 件** | |

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 46 file 全件 frontmatter 確認 (現在 status 値・除外候補把握) | PM | ✅ done |
| 2 | 除外 list 決定 (deprecated 固定や status 別値を望む file の仕分け) | PM | ✅ done (§2.A) |
| 3 | batch script 作成 (`scripts/retrofit-helix-workflows-status.py`) | SE | todo |
| 4 | dry-run 実行 (--apply なし、変更対象 preview + diff 出力) | SE | todo |
| 5 | PMO review: dry-run 出力の除外 list 整合確認 | PMO | todo |
| 6 | apply 実行 (--apply フラグ付き、46 file 一括更新) | SE | todo |
| 7 | frontmatter lint (yaml.safe_load 全件 PASS 確認) | SE | todo |
| 8 | helix plan lint (本 PLAN 自体 + 関連 PLAN 影響なし確認) | SE | todo |
| 9 | PMO 完遂 report (status 集計 + 残 draft 0 確認) | PMO | todo |
| 10 | commit (docs(retrofit): helix-workflows helix-process 46 file status accepted) | PM | todo |

---

## §2 実装計画

### §2.A 除外 list (status を accepted 以外に固定する file)

本 PLAN 実行時点の判定 (tl-advisor R1 P1-1 反映、実測ベース):

```
除外 file (status: accepted に変更しない):
  - なし (全 46 file が accepted 対象、README.md 含む)

実測結果 (2026-05-24 tl-advisor R1 検証):
  - files: 46
  - status_draft: 46 (全件)
  - status_missing: 0 (README.md も status: draft あり、当初の「フィールドなし」推測は誤り)
  - accepted_date_existing: 0 (上書き衝突なし)

根拠:
  - deprecated 相当の file は HELIX-workflows/helix-process/ には現時点で存在しない
  - README.md は status: draft フィールドが既に存在 (実測確認済)
  - HELIX-process-L0-L14.md は helix-process/ 配下ではなく HELIX-workflows/ 直下 (スコープ外、後続 PLAN で別途判断)
```

除外 list に追加すべき判断が生じた場合は、SE が dry-run 出力を PMO へ提示し、PM 承認後に除外 list を更新してから apply する。PMO review 用に file 別の `file / category / freeze_basis / exclude_reason` 一覧を dry-run report として併出する (tl-advisor P2-1 反映)。

### §2.B batch script 設計

**ファイル**: `scripts/retrofit-helix-workflows-status.py`

```
インターフェース:
  python3 scripts/retrofit-helix-workflows-status.py [--apply] [--verbose]

  --apply なし (デフォルト): dry-run mode。変更対象 file と before/after diff を表示して終了
  --apply: 実際に file 更新を実行
  --verbose: 全 file の処理結果を出力 (skip 含む)

処理フロー (tl-advisor R1 P1-2 + P2 反映、transaction + encoding 明示版):

  1. HELIX-workflows/helix-process/*.md を glob で収集 (46 件)
  2. 各 file に対して **メモリ上で** 処理:
     a. `path.read_text(encoding='utf-8')` で読み込み
     b. `splitlines(keepends=True)` で先頭 `---` から次の単独 `---` までを行単位で抽出 (regex DOTALL は使わない、行単位処理が安全)
     c. yaml.safe_load で frontmatter parse (本文は除く)
     d. status フィールドが 'draft' であれば変更対象に加える、'accepted' なら skip ログ
     e. 除外 list に含まれる場合は skip ログ
  3. 全 file の更新後内容を **メモリ上で構築** + 個別 yaml.safe_load で frontmatter syntax validation
  4. validation 全 PASS の場合のみ、**temp file + os.replace で atomic 書き込み**:
     a. 各 file につき `path.parent / f'.{path.name}.tmp.{pid}'` に utf-8 で書き込み
     b. `os.replace(tmp_path, path)` で atomic 置換 (rename は same-fs で atomic)
  5. validation 1 件でも fail の場合は **全件 abort、temp file 全削除、原 file は無変更**
  6. apply 後に `yaml.safe_load + frontmatter parse` を再度全件実行して double-check
  7. 処理サマリ: changed N / skipped N / errors N / status_missing N / accepted_date_conflict N

変更ルール (tl-advisor R1 P2-2 反映、idempotent):
  - `status: draft` → `status: accepted` (行頭マッチ)
  - `accepted_date` 既存値 == `2026-05-24` → no-op
  - `accepted_date` 既存値 != `2026-05-24` → error (上書きは `--force-date` フラグ明示時のみ)
  - `accepted_date` 不在 → status 行直後に挿入 (新規追加)

実装注意 (encoding / atomic / idempotent 三大原則):
  - 全 I/O で `encoding='utf-8'` 明示 (read_text/write_text/io.open すべて)
  - 行末 `newline=''` 維持 (LF/CRLF 混在しない)
  - temp file + os.replace で transaction (validation failure 時の復旧不能を防止)
  - yaml dump は使わない (frontmatter コメント・順序・クォートスタイルを破壊するため、行単位 string replace のみ)
  - 行単位処理は keepends=True で改行コード保持
```

### §2.C accepted_date 追加の位置決め

`status: accepted` の直後の行に `accepted_date: 2026-05-24` を挿入する。

既存 frontmatter の例:
```yaml
status: draft
created: 2026-05-24
```

更新後:
```yaml
status: accepted
accepted_date: 2026-05-24
created: 2026-05-24
```

`accepted_date` フィールドが既に存在する場合は値を `2026-05-24` で上書き (重複挿入なし)。

### §2.D dry-run 出力仕様

tl-advisor R1 P2-3 反映、unified diff + 集計版:

```
=== DRY-RUN MODE (pass --apply to apply) ===

--- HELIX-workflows/helix-process/L0-concept.md
+++ HELIX-workflows/helix-process/L0-concept.md
@@ frontmatter @@
-status: draft
+status: accepted
+accepted_date: 2026-05-24

--- HELIX-workflows/helix-process/L1-requirements.md
+++ HELIX-workflows/helix-process/L1-requirements.md
@@ frontmatter @@
-status: draft
+status: accepted
+accepted_date: 2026-05-24

... (46 件分の unified diff)

[REPORT] file × category × freeze_basis × exclude_reason:
  L0-concept.md            | L0 工程 doc           | content_frozen_2026-05-24 | -
  L1-requirements.md       | L1 工程 doc           | content_frozen_2026-05-24 | -
  ... (46 件分)

Summary:
  changed: 46
  skipped: 0
  errors: 0
  status_missing: 0
  accepted_date_conflict: 0
```

### §2.E 46 file 一覧 (script の検索対象)

```
L0-concept.md
L1-requirements.md
L2-ui-design.md
L3-requirements-definition.md
L4-basic-design.md
L5-detailed-design.md
L6-functional-design.md
L7-implementation.md
L8-integration-test.md
L9-system-test.md
L10-ux-refinement.md
L11-final-review.md
L12-deployment.md
L13-post-deployment-verification.md
L14-operation-verification.md
add-feature-workflow.md
asset-mapping.md
automation-gate-map.md
ci-pr-workflow.md
continuous-run-context-management.md
cross-cutting-mechanisms.md
cross-detection.md
db-auto-registration.md
db-integration.md
detection-routing.md
deviation-plan-map.md
discovery-workflow.md
fe-detector-spec.md
folder-structure-review.md
frontend-design-workflow.md
incident-workflow.md
infra-readiness.md
integration-map.md
layer-context-injection.md
learning-engine.md
observability-metrics.md
README.md
recovery-workflow.md
refactor-workflow.md
research-workflow.md
retrofit-workflow.md
reverse-workflow.md
scrum-workflow.md
screen-design-workflow.md
test-perspective-gate.md
two-stage-agent-design.md
```

注: README.md も status: draft あり (tl-advisor R1 実測確認、§2.A 反映済)。全 46 件が accepted 対象。

---

## §3 成果物

| 成果物 | パス | 説明 |
|---|---|---|
| batch script | `scripts/retrofit-helix-workflows-status.py` | dry-run / apply 両モード対応 |
| 更新対象 doc | `HELIX-workflows/helix-process/*.md` | 46 file、status + accepted_date 更新 |

---

## §4 受入条件 / DoD

### 機械チェック (mandatory)

```bash
# 1. status: draft が残存しないこと
grep -l 'status: draft' HELIX-workflows/helix-process/*.md | wc -l
# → 0

# 2. accepted_date が全件付与されていること (README.md 等 status なし file は除く)
grep -l 'status: accepted' HELIX-workflows/helix-process/*.md | xargs grep -L 'accepted_date:' | wc -l
# → 0

# 3. frontmatter syntax valid (yaml.safe_load 全件 PASS)
python3 -c "
import yaml, pathlib, sys
errors = []
for f in sorted(pathlib.Path('HELIX-workflows/helix-process').glob('*.md')):
    text = f.read_text()
    if not text.startswith('---'):
        continue
    end = text.find('---', 3)
    if end < 0:
        errors.append(f'{f}: no closing ---')
        continue
    fm = text[3:end]
    try:
        yaml.safe_load(fm)
    except yaml.YAMLError as e:
        errors.append(f'{f}: {e}')
if errors:
    print('FAIL:', errors); sys.exit(1)
print(f'PASS: all frontmatter valid')
"
# → PASS: all frontmatter valid

# 4. 本 PLAN の lint
python3 -m pytest cli/lib/tests/test_plan_validator.py -q --tb=short 2>/dev/null || \
  python3 cli/lib/plan_validator.py docs/plans/L7/L7-helix-workflows-status-acceptedplan.md
```

### review チェック (mandatory)

- [ ] PMO dry-run 出力レビュー: 除外 list の妥当性、変更対象 46 件の意図整合
- [ ] apply 後: 関連実装 PLAN (L7-helix-recover / L7-helix-route 等) の parent_design 参照が accepted になったことを確認
- [ ] 後続 PLAN への影響なし: 他 PLAN の `requires` / `parent_design` に draft 前提の記述がないことを確認

### on-demand チェック

- [ ] helix doctor: warn 件数が適用前から増加していないこと
- [ ] tl-advisor: batch script の yaml 操作安全性 (frontmatter 保持 / encoding 破壊なし) を確認 (規模が小さいため skip 可)

---

## §5 関連 doc

- `HELIX-workflows/HELIX-process-L0-L14.md` — 正本設計、V2 完全移行の根拠
- `HELIX-workflows/helix-process/integration-map.md` — 設計凍結判断の根拠
- `docs/plans/L7/L7-vmodel-semantics-injection-setplan.md` — 本 PLAN 予告元 (§6 後続 PLAN 候補に記載)
- `docs/plans/L7/L7-helix-recover-implplan.md` — parent_design draft 採用説明を含む実装 PLAN (本 PLAN 完遂で解消)
- `docs/plans/L7/L7-helix-route-implplan.md` — 同上
- `docs/plans/L7/L7-docs-template-phase1-implplan.md` — 同上
- `docs/plans/L7/L7-docs-template-phase2-implplan.md` — 同上
- `cli/lib/plan_validator.py` — lint 検証に使用

---

## §6 後続 PLAN 候補

本 PLAN 完遂後に検討が必要な関連作業:

1. **HELIX-workflows/ 直下 doc の status 更新** (`HELIX-process-L0-L14.md` 等): 本スコープは helix-process/ のみ。親 doc は別途判断
2. **L7 実装 PLAN 群の parent_design draft 採用説明セクション削除**: L7-helix-recover-implplan / L7-helix-route-implplan 等の `parent_design (draft status) を採用する理由` セクションが不要になる。機械的削除か注記追記かは PM 判断
3. **plan_validator に parent_design status チェック追加**: parent_design が draft の PLAN を lint 警告する rule の導入 (helix doctor 強化)
4. **docs/v2 series との整合確認**: docs/v2/process/ の関連 doc が HELIX-workflows に倣い status 更新を要するか確認
