---
plan_id: PLAN-175
title: "PLAN-175: agent-team marketplace framework (template share + import)"
kind: design
layer: L3
drive: agent
status: draft
size: L
created: "2026-05-23"
revised: "2026-05-23"
owner: PM
agent_slots:
  - role: tl
    slot_label: "TL — marketplace CLI 設計・GitHub Gist API 連携設計・import/validate 仕様"
  - role: se
    slot_label: "SE — helix team marketplace サブコマンド実装・template import ロジック"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 helix team / agent slot 設計との整合確認・import セキュリティ観点"
  - role: docs
    slot_label: "Docs — marketplace コマンドリファレンス・template 投稿ガイドライン起草"
generates:
  - artifact_path: docs/plans/PLAN-175-agent-team-marketplace.md
    artifact_type: design_doc
  - artifact_path: docs/design/PLAN-175-marketplace-api-contract.md
    artifact_type: design_doc
  - artifact_path: cli/lib/team_marketplace.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_team_marketplace.py
    artifact_type: test
  - artifact_path: docs/commands/team-marketplace.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-165
  requires:
    - PLAN-165
  blocks: []
related_adr: []
related_docs:
  - docs/plans/PLAN-165-helix-team-workflow-framework.md
  - cli/lib/agent_mandatory.py
  - helix/HELIX_CORE.md
acceptance_criteria:
  - "helix team marketplace search '<query>' が公開 template を返す"
  - "helix team marketplace import <template-id> で .helix/team-templates/ に保存される"
  - "import 時に schema validation + hash 検証が通る"
  - "python3 -m py_compile cli/lib/team_marketplace.py PASS"
  - "unit test 8 case 全 PASS"
  - "docs/commands/team-marketplace.md 作成済"
---

# PLAN-175: agent-team marketplace framework (template share + import)

## L2 凍結 (ADR snapshot)

本 PLAN は **新規 marketplace 経路 (GitHub Gist API 連携 + 公開 template hub)** を採用する。
外部 API との接続方針は L2 大局判断に該当するため、実装着手前に ADR snapshot を起票する。

ADR snapshot 要否判定:
- 外部 API 新規依存 (GitHub Gist API): **L2 大局判断あり → ADR 必要**
- template の信頼性検証方式 (hash/schema): **セキュリティ観点あり → ADR 必要**

→ L3 詳細設計着手前に ADR-035 (marketplace 外部 API 採用判断) を起票する。

## 背景

PLAN-165 (helix-team workflow framework) で team workflow template の定義・共有基盤が整備された。
次のステップとして、チーム間 / community 間での template 共有を可能にする
marketplace framework が必要になった。

現状の課題:
- team workflow template は `.helix/team-templates/` に局所保存のみ
- 他プロジェクト / community から有用な template を取り込む公式経路がない
- template の品質・安全性を評価する仕組みがない (野良 template の混入リスク)

## WebSearch 調査 (PLAN-087 ガード遵守)

agent template marketplace / hub の 2026 年トレンドを調査した。

調査クエリ 3 件を実施:
1. "agent template marketplace GitHub 2026": GitHub Workflow Templates (Organization-scoped) + Gist が主流
2. "LLM agent prompt template registry 2026": LangChain Hub が public/private namespace + star + version tag で先行
3. "template import security validation hash checksum": npm/pip の SHA-256 + 署名検証が業界標準

採用方針: GitHub Gist backend (依存追加ゼロ) + SHA-256 hash 必須 (署名は将来拡張) + LangChain Hub 思想参考

## 設計方針

### marketplace backend 選択

| 方式 | メリット | デメリット | 採用 |
|---|---|---|---|
| GitHub Gist | 依存追加ゼロ・公開 URL 固定 | star 数 API call 必要 | **採用 (初版)** |
| 専用 OSS registry | 機能豊富 | HELIX 外部サービス依存 | 将来候補 |
| awesome-list | 低コスト | 機械的 import 困難 | 不採用 |

初版 backend: GitHub Gist + HELIX community index JSON
(`https://raw.githubusercontent.com/helix-marketplace/index/main/index.json`)

### CLI インタフェース

```bash
# 検索
helix team marketplace search "Python TDD"
helix team marketplace search --tag ci-cd --min-stars 5

# 詳細確認
helix team marketplace show <template-id>

# import
helix team marketplace import <template-id>
helix team marketplace import <template-id> --as my-python-tdd

# 公開 (将来拡張)
helix team marketplace publish .helix/team-templates/my-template/
```

### template index 構造

Community index JSON (`https://raw.githubusercontent.com/helix-marketplace/index/main/index.json`):
各エントリに `id / name / gist_id / sha256 / stars / tags / verified / helix_version_min` を持つ。
`verified: true` は HELIX maintainer が schema + security review 済みを示す。

### import セキュリティモデル

import フロー: index → gist_id + sha256 取得 → GitHub Gist fetch → SHA-256 検証 → YAML schema 検証
→ `.helix/team-templates/<id>/` 保存 → meta.json (imported_at / source_sha256 / gist_id) 記録。

セキュリティ制約: `exec:` / `bash:` / `shell:` キー含む template は import 拒否 + path traverse sanitize。
`REQUIRED_TEMPLATE_FIELDS = {"name", "version", "roles", "workflow_steps"}`

## 実装計画

### Sprint .1: 設計書・API 契約 (TL 委譲、size M)

**Entry 条件**: ADR-035 起票済・PLAN-165 実装完了確認

- GitHub Gist API 連携仕様 (rate limit: unauth 60/h / token 5000/h、network 不能時 cached fallback)
- `docs/design/PLAN-175-marketplace-api-contract.md` 起草
- template index JSON schema 定義 (JSON Schema draft-07)

受入条件: API 契約 doc 存在 / rate limit + fallback 方針明記 / schema validation ルール定義済

### Sprint .2: Python module 実装 (SE 委譲、size M)

**Entry 条件**: Sprint .1 API 契約 doc PASS

`cli/lib/team_marketplace.py`: `fetch_index` / `search` / `import_template` / `validate_template_schema` / `verify_sha256` の 5 関数。
単体テスト 8 case (T1: index cache hit / T2-T3: keyword+tag filter / T4-T5: SHA-256 PASS+FAIL / T6: exec キー拒否 / T7: path traverse / T8: network fallback)。

受入条件: `python3 -m py_compile` PASS / unit test 8 case PASS

### Sprint .3: CLI 統合 + docs (SE / Docs 委譲、size S)

**Entry 条件**: Sprint .2 module PASS

`cli/helix-team` に `marketplace` サブコマンド (`search` / `show` / `import` / `--json`) 追加。
`docs/commands/team-marketplace.md` + bats smoke test。

受入条件: `helix team marketplace search/import` 動作確認 (stub index) / bats PASS

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/team_marketplace.py` PASS
- [ ] unit test 8 case PASS
- [ ] bats smoke test PASS
- [ ] pmo-sonnet review (Sprint .3 完了後)
- [ ] セキュリティ観点確認 (exec キー排除 / path traverse sanitize)

## DoD

- [ ] ADR-035 起票済
- [ ] `docs/design/PLAN-175-marketplace-api-contract.md` 作成済
- [ ] `cli/lib/team_marketplace.py` 実装・`python3 -m py_compile` PASS
- [ ] unit test 8 case PASS
- [ ] `helix team marketplace search/import` 動作確認
- [ ] `docs/commands/team-marketplace.md` 作成済
- [ ] bats smoke test PASS
- [ ] helix doctor pass 数現行以上維持

## V-model 4 artifact trace

| artifact | パス |
|---|---|
| ① 設計 | docs/plans/PLAN-175-agent-team-marketplace.md + docs/design/PLAN-175-marketplace-api-contract.md |
| ② 実装コード | cli/lib/team_marketplace.py / cli/helix-team (marketplace 追加) |
| ③ テスト設計 | 本文 §Sprint .2 T1-T8 + §mandatory in sprint |
| ④ テストコード | cli/lib/tests/test_team_marketplace.py + bats smoke |

## carry / リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| GitHub Gist API rate limit 超過 | index fetch 失敗 | TTL キャッシュ 1h + token 設定オプション |
| community index メンテ負荷 | template が陳腐化 | `helix_version_min` フィールドで互換性明示 |
| 悪意ある template の混入 | セキュリティリスク | exec キー排除 + SHA-256 検証 + verified フラグ |
| PLAN-165 未完了時の依存 | Sprint .1 entry 不能 | PLAN-165 status 確認を Sprint .1 Entry 条件に明記 |

## 関連 reference

- PLAN-165 (helix-team workflow framework、parent)
- PLAN-088 (TodoWrite × agent slot framework)
- cli/lib/agent_mandatory.py (参考実装パターン)
- helix/HELIX_CORE.md §工程別 subagent 起動マップ
- LangChain Hub 設計参考 (public/private namespace + star + version tag)
