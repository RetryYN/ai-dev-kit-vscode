---
plan_id: L7-helix-workflows-parent-acceptedplan
title: "L7-helix-workflows-parent-acceptedplan: HELIX-workflows 親 doc (HELIX-process-L0-L14.md) の status draft → accepted retrofit"
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
  - role: pmo-sonnet
    slot_label: "PMO — 修正対象 file 確認・frontmatter lint・完遂 report"
generates:
  - artifact_path: HELIX-workflows/HELIX-process-L0-L14.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires:
    - L7-helix-workflows-status-acceptedplan
  blocks: []
related_docs:
  - HELIX-workflows/HELIX-process-L0-L14.md
  - docs/plans/L7/L7-helix-workflows-status-acceptedplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント (retrofit)
> **正本設計**: [HELIX-workflows/HELIX-process-L0-L14.md](../../../HELIX-workflows/HELIX-process-L0-L14.md)
> **本 PLAN の対象**: 兄弟 PLAN (L7-helix-workflows-status-acceptedplan、commit 8451f84) で `HELIX-workflows/helix-process/` 配下 46 file の accepted 化が完了した。残る **親 doc `HELIX-workflows/HELIX-process-L0-L14.md`** の `status: draft → accepted`、`accepted_date: 2026-05-24` 追加を本 PLAN で完遂する。

### 目的と背景

兄弟 PLAN (L7-helix-workflows-status-acceptedplan) の §6 後続候補として予告されていた。配下 46 file は accepted 化済だが、親 doc のみ `status: draft` のままであることは以下の不整合を生じさせる:

1. **整合性**: 子 file が accepted で親が draft という逆転状態
2. **V2 完全移行の最終 step**: 親 doc は V2 完全移行の設計正本。accepted 化により「設計凍結 = 正本確定」のセマンティクスを完遂する
3. **将来の lint**: parent_design が draft のまま実装 PLAN が参照し続ける状態を解消する

### retrofit kind を使う理由

- 親 doc の内容変更なし、frontmatter metadata のみ更新 = retrofit kind が適合
- 兄弟 PLAN と同じ判断根拠を継承する

### 修正対象の確定

HELIX-workflows 直下には `HELIX-process-L0-L14.md` 1 file のみ存在 (helix-process/ 配下は兄弟 PLAN 完了済)。修正対象は実質 1 file。

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 親 doc frontmatter 現在値確認 (status / accepted_date の有無) | PM | todo |
| 2 | status 書き換え + accepted_date 追加 (Opus 直接 Edit) | PM | todo |
| 3 | yaml.safe_load lint 確認 | PM | todo |
| 4 | helix plan lint (本 PLAN + 依存 PLAN 影響なし確認) | PM | todo |
| 5 | commit + push | PM | todo |

---

## §2 実装計画

### §2.A 修正対象 (1 file)

```
HELIX-workflows/HELIX-process-L0-L14.md
  - status: draft → accepted
  - accepted_date: 2026-05-24 (新規追加)
```

その他 HELIX-workflows 直下に .md は存在しないことを事前 ls で確認済。

### §2.B 修正方針

scope が 1 file かつ frontmatter 2 行変更のみのため、Opus 直接 Edit で対応する。
scripts/retrofit-helix-workflows-status.py は 46 file 向けに設計されており、1 file 単独実行にオーバーヘッドが大きいため不使用とする。

変更内容:
```yaml
# 変更前
status: draft

# 変更後
status: accepted
accepted_date: 2026-05-24
```

---

## §3 成果物

| 成果物 | パス | 変更内容 |
|---|---|---|
| 親 doc 更新 | HELIX-workflows/HELIX-process-L0-L14.md | status accepted + accepted_date 追加 |

---

## §4 受入条件 / DoD

- [ ] `HELIX-workflows/HELIX-process-L0-L14.md` の `status: accepted` 確認
- [ ] `accepted_date: 2026-05-24` 追加確認
- [ ] `python3 -c "import yaml; yaml.safe_load(open('HELIX-workflows/HELIX-process-L0-L14.md').read().split('---')[1])"` PASS
- [ ] `helix plan lint docs/plans/L7/L7-helix-workflows-parent-acceptedplan.md` PASS (または plan_validator.py 直接実行)
- [ ] helix doctor 既存 PASS 数 維持

---

## §5 関連 PLAN / docs

- 兄弟 PLAN: [L7-helix-workflows-status-acceptedplan](L7-helix-workflows-status-acceptedplan.md) (commit 8451f84、配下 46 file accepted 化完了)
- 正本: [HELIX-workflows/HELIX-process-L0-L14.md](../../../HELIX-workflows/HELIX-process-L0-L14.md)

---

## §6 後続 PLAN 候補

なし。本 PLAN 完遂により HELIX-workflows 全 doc (親 1 + 配下 46 = 47 file) の accepted 化が完了し、V2 完全移行関連の retrofit carry が解消される。
