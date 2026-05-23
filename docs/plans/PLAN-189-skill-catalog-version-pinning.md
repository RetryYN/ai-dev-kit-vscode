---
plan_id: PLAN-189
title: "skill catalog version pinning (skills/ 変更時の互換性保証)"
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — catalog_version semver 管理ロジック実装 (cli/lib/skill_catalog.py + cli/helix-skill) + pytest 起草"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 catalog 生成ロジック精読・version bump 基準設計レビュー・SKILL_MAP.md 整合確認"
generates:
  - artifact_type: python_module
    path: cli/lib/skill_catalog.py
  - artifact_type: script
    path: cli/helix-skill
  - artifact_type: test
    path: cli/lib/tests/test_skill_catalog_version_pinning.py
dependencies:
  requires:
    - PLAN-157
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - cli/lib/skill_catalog.py
  - cli/helix-skill
  - SKILL_MAP.md §自動推挙システム
acceptance_criteria:
  - ".helix/cache/skill-catalog.json に catalog_version (semver) フィールドが記録される"
  - "description 全変更 / trigger 削除 (breaking change) で major version が bump される"
  - "description 部分変更 / trigger 追加 (non-breaking) で minor version が bump される"
  - "内容変更なし (mtime 更新のみ) では version が変化しない"
  - "helix skill chain --catalog-version <semver> が指定 version のみで動作し、不一致時に WARN を出す"
  - "python3 -m py_compile cli/lib/skill_catalog.py PASS"
  - "pytest cli/lib/tests/test_skill_catalog_version_pinning.py -q 全 PASS (8 scenario)"
  - "bash -n cli/helix-skill PASS"
---

# PLAN-189: skill catalog version pinning (skills/ 変更時の互換性保証)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 skill catalog framework の互換性強化** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- skill catalog 機構は SKILL_MAP.md §自動推挙システムで凍結済
- semver による version pinning は既存 HELIX パターンの延長 (helix.db schema_version と同方式)
- 外部ライブラリ新規導入なし (Python stdlib hashlib / json のみ使用)

## 背景

`helix skill catalog rebuild` が SKILL.md から自動生成する `skill-catalog.json` は version 管理がない。
`description` 全変更 / `triggers` 削除 (breaking change) で recommender / chain が旧 semantic を参照し続けるリスクがある。
`catalog_version` (semver) を catalog に記録し `--catalog-version <ver>` で固定することで互換性を保証する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は HELIX 内部 CLI の互換性改善。外部ライブラリ新規依存なし。WebSearch **skip**。
semver 管理は Python stdlib (hashlib.sha256 + JSON 比較)、helix.db の schema_version 管理パターンを踏襲。

## 設計方針

### 1. catalog_version の管理単位

`skill-catalog.json` に `catalog_version` (semver 文字列) と
各エントリの `content_hash` (SHA-256 先頭 8 桁) を追加する。

```python
# skill-catalog.json 追加フィールド
{
  "catalog_version": "1.2.0",
  "generated_at": "2026-05-23T00:00:00Z",
  "entries": [
    {
      "skill_id": "common/testing",
      "content_hash": "a3f2b1c4",  # description + triggers の SHA-256
      ...
    }
  ]
}
```

### 2. version bump 基準

| 変化の種類 | バンプ種別 | 判定ロジック |
|---|---|---|
| trigger 削除 | **major** | 旧 catalog に存在した trigger が新 catalog に不在 |
| description 全変更 (hash 不一致 + 共通 token < 30%) | **major** | content_hash 変化 + Jaccard 類似度閾値 |
| description 部分変更 (hash 不一致 + 共通 token >= 30%) | **minor** | content_hash 変化のみ |
| trigger 追加 | **minor** | trigger 件数増加 |
| 内容変更なし (mtime 更新のみ) | **none** | content_hash 一致 |

```python
def _detect_bump_level(old_entries: dict, new_entries: dict) -> str:
    """Return 'major', 'minor', or 'none'."""
    ...
```

### 3. helix skill chain --catalog-version フラグ

```bash
helix skill chain "<task>"                          # catalog version 問わず動作 (現行と同等)
helix skill chain "<task>" --catalog-version 1.2.0 # 指定 version と不一致なら WARN
```

version 不一致時の動作:
- `[WARN] catalog version mismatch: expected=1.2.0, actual=1.3.0` を STDERR 出力
- 処理は継続 (fail-close ではなく advisory)
- `--strict-version` を付けた場合のみ exit 1 で abort (optional、Sprint .2 で追加)

### 4. 初期 version

既存 catalog に `catalog_version` が存在しない場合は `0.1.0` を初期値として書き込む。
以降の rebuild 時に bump 判定が適用される。

## 実装計画

### Sprint .1: skill_catalog.py 改修 (se 委譲)

Entry 条件: `cli/lib/skill_catalog.py` の既存 `rebuild()` と catalog JSON 構造を Read して確認

1. `_compute_content_hash(entry: dict) -> str` 追加 (description + triggers の SHA-256 先頭 8 桁)
2. `_detect_bump_level(old_entries, new_entries) -> str` 追加 (major / minor / none)
3. `_bump_semver(current: str, level: str) -> str` 追加
4. `rebuild()` 内で bump 判定 → `catalog_version` 自動更新
5. 初期 version `0.1.0` の fallback 処理
6. `python3 -m py_compile cli/lib/skill_catalog.py` PASS

### Sprint .2: helix-skill CLI フラグ追加 (se 委譲)

1. `cli/helix-skill` の `chain` 節に `--catalog-version <ver>` フラグ追加
2. version チェック helper `check_catalog_version` を `skill_catalog.py` に追加
3. 不一致時 STDERR WARN 出力 / `--strict-version` で exit 1
4. `bash -n cli/helix-skill` PASS

### Sprint .3: pytest + 動作実証 (se 委譲)

`cli/lib/tests/test_skill_catalog_version_pinning.py` 新規作成 (8 scenario):
- initial_version_0_1_0 / major_bump_trigger_deletion / major_bump_description_full_replace
- minor_bump_description_partial / minor_bump_trigger_addition / no_bump_unchanged
- warn_on_version_mismatch / strict_version_exit_1

`pytest cli/lib/tests/test_skill_catalog_version_pinning.py -q` 全 PASS

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/skill_catalog.py` PASS
- [ ] `bash -n cli/helix-skill` PASS
- [ ] pytest 全 8 scenario PASS
- [ ] `helix skill catalog rebuild` 後に `catalog_version` が `skill-catalog.json` に記録されること
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)

## DoD (Definition of Done)

- [ ] `skill-catalog.json` に `catalog_version` (semver) と各 entry の `content_hash` が記録される
- [ ] trigger 削除 / description 全変更 で major bump、部分変更 / trigger 追加 で minor bump が発動する
- [ ] 内容変更なしの rebuild では version が変化しない
- [ ] `helix skill chain --catalog-version <ver>` が不一致時に WARN 出力 / `--strict-version` で exit 1
- [ ] pytest 8 scenario 全 PASS / `python3 -m py_compile` + `bash -n` 全 PASS
- [ ] 既存 `helix skill chain` (version フラグなし時) が regression しない

## V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 (本 PLAN) | docs/plans/PLAN-189-skill-catalog-version-pinning.md |
| ② 実装コード | cli/lib/skill_catalog.py / cli/helix-skill |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-189-version-pinning-test-design.md (予定) |
| ④ テストコード | cli/lib/tests/test_skill_catalog_version_pinning.py |

双方向 reference: 実装コード docstring に「設計: PLAN-189」/ テストコード docstring に「DoD 検証: PLAN-189 §DoD」を追記。

## リスク

| リスク | 緩和策 |
|---|---|
| Jaccard 閾値 30% が誤分類 | 初期は conservative (多め major bump)。threshold を config 化して運用後に調整 |
| WARN 過多 | advisory (WARN のみ) がデフォルト。fail-close は `--strict-version` opt-in |
| PLAN-157 incremental との干渉 | incremental 時も bump 判定を実行。変更 entry のみを旧 catalog と比較 |
| 既存 catalog に catalog_version 不在 | 初期値 `0.1.0` を自動付与して seamless に migration |

## 関連 reference

- PLAN-157 (依存元: incremental update)
- SKILL_MAP.md §自動推挙システム / cli/lib/skill_catalog.py / cli/helix-skill
