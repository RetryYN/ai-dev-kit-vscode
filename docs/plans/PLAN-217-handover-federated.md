---
plan_id: PLAN-217
title: "PLAN-217: handover protocol federated (multi-repo handover hub)"
layer: L4
kind: impl
status: draft
size: L
drive: be
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl-advisor
    slot_label: "TL adversarial — federated hub アーキテクチャ選択 (local/git-based) + セキュリティ設計 adversarial check"
  - role: se
    slot_label: "SE — cli/lib/handover_federated.py + helix handover federate CLI 実装"
  - role: security
    slot_label: "Security — repo 間通信の認証・認可・secret 管理・PII 漏洩リスク監査"
  - role: qa
    slot_label: "QA — federated handover cycle test + multi-repo fixture + regression"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-128 依存整合・federated hub 設計整合確認・G4 review"
generates:
  - artifact_path: cli/lib/handover_federated.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_handover_federated.py
    artifact_type: test
  - artifact_path: docs/adr/ADR-048-handover-federated-transport.md
    artifact_type: adr_snapshot
  - artifact_path: docs/plans/PLAN-217-handover-federated.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-128
  requires:
    - PLAN-128
  blocks: []
related_plans:
  - PLAN-128-handover-schema-enhancement
related_adr:
  - ADR-048-handover-federated-transport
related_docs:
  - cli/lib/handover.py
  - helix/HELIX_CORE.md
  - CLAUDE.md
---

# PLAN-217: handover protocol federated (multi-repo handover hub)

> **kind**: impl | **layer**: L4 | **drive**: be | **parent**: PLAN-128
> **L2 凍結**: ADR-048 (transport 選択 + セキュリティ設計)

---

## §0. 本 PLAN の位置付け

HELIX の handover は single repo 前提 (`.helix/handover/CURRENT.json`)。
framework repo + product repo などの multi-repo 体制では repo 間の引き継ぎ情報が
断絶する。本 PLAN は `.helix/handover/federated/<repo-hash>/` を hub として
repo 間 handover を共有する federated 機構を実装する。

PLAN-128 (handover schema 強化) が parent であり、拡張 schema (plan_id /
agent_slot_history 等) を federated handover でもそのまま利用する。

---

## §1. 目的

1. `helix handover federate --target <repo>` CLI で handover を push / pull できる
2. federated hub (`.helix/handover/federated/<repo-hash>/`) が中継点として機能する
3. Security subagent が認証・PII・permission を監査し、ADR-048 で L2 凍結する
4. `helix handover federate --list` で登録済み repo と最終同期時刻を表示する

---

## §2. 設計方針

### 2.1 Transport 選択 (ADR-048 で凍結)

| 案 | 方式 | 採用判断 |
|---|---|---|
| C (primary) | local filesystem | 同一マシン multi-repo に最も単純。初期実装必須 |
| A (option) | git-based push/pull + branch | cross-machine 対応。ADR-048 確定後に拡張 |
| B | S3 / object storage | 外部依存追加。「外部 provider SDK を通常導線に追加しない」原則から scope 外 |

### 2.2 federated hub directory 構造

```
.helix/handover/federated/
  <repo-hash>/          # sha256 先頭 8 文字
    meta.json           # {repo_path, repo_hash, last_sync, direction}
    CURRENT.json        # target repo から pull した handover snapshot
    OUTBOX.json         # target repo に push 予定の handover draft
```

permission は 700 (owner only)。

### 2.3 CLI 設計

```
helix handover federate --target <repo-path> [--push | --pull | --sync]
helix handover federate --list
helix handover federate --remove <repo-hash>
```

push = 自 CURRENT.json を target の OUTBOX に書き込む。
pull = target の OUTBOX を自 CURRENT.json にマージ。
sync = push + pull 順に実行。

### 2.4 セキュリティ設計

- push 時に secret pattern (API key / token) を scan。検出時は abort
- task_summary / notes に PII パターン (email 等) を検出 → warn + sanitize
- target repo が `.helix/` を持つことを push 前に identity check
- Security subagent が Sprint .3 で全項目を監査し、ADR-048 に evidence 追記

---

## §3. DoD

- [ ] ADR-048 を L2 大局判断 snapshot として起票 (transport 選択 + セキュリティ設計)
- [ ] `cli/lib/handover_federated.py` (`HandoverFederatedHub` + `FederatedMeta`) 実装
- [ ] `helix handover federate --push / --pull / --sync / --list / --remove` が動作する
- [ ] `.helix/handover/federated/` の permission が 700 であることを test で確認
- [ ] Security 監査が ADR-048 に記録されている (escalation なし)
- [ ] `cli/lib/tests/test_handover_federated.py` で push / pull / sync / list / remove が PASS
- [ ] `python3 -m py_compile cli/lib/handover_federated.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_handover_federated.py -v` 全件 PASS
- [ ] pytest 全体 sweep で regression なし

---

## §4. 実装計画

### Sprint .1 — ADR-048 + skeleton (TL-advisor + SE)

- `tl-advisor` を召喚し transport 選択の adversarial check を実施
- ADR-048 起票: transport 選択根拠 + セキュリティ設計 + fallback 方針
- `handover_federated.py` skeleton: `FederatedMeta` dataclass + `HandoverFederatedHub.__init__` + `register` stub
- 受入: ADR-048 に transport 選択根拠明記 / `py_compile` PASS

### Sprint .2 — push / pull / sync 実装 (SE)

- PLAN-128 生成の `cli/lib/handover.py` を Read し load/save API を確認
- `push` / `pull` / `sync` を実装。pull は `last_sync` より新しい OUTBOX のみマージ (idempotent)
- OUTBOX.json は tmp ファイル + atomic rename で書き込み (race condition 防止)
- permission 設定: `os.chmod(federated_dir, 0o700)` を `register` 内で実行
- secret scan + PII sanitize を push path に組み込む
- T1〜T4 (push / pull / sync / permission 700) を実装
- 受入: T1〜T4 PASS

### Sprint .3 — Security 監査 + CLI 統合 + 全体検証 (Security + SE + QA)

- `security` subagent を召喚し ADR-048 に evidence 追記
- `cli/helix-handover` に `federate` サブコマンドを追加 (routing のみ)
- T5〜T7 (list / remove / HELIX_DIR 不在の graceful error) を追加
- `bash -n cli/helix-handover` PASS + bats test
- pytest 全体 sweep で regression 確認
- 受入: Security 監査完了 (escalation なし) / 全件 PASS / regression なし

---

## §5. リスクと緩和策

| リスク | 緩和策 |
|---|---|
| PLAN-128 未完成で blocking | Sprint .1 entry 前に PLAN-128 DoD 確認必須 |
| push/pull の race condition | OUTBOX.json を tmp + atomic rename で書き込む |
| TL adversarial で transport 選択却下 | Sprint .1 早期に tl-advisor 召喚。C 案却下時は A 案に切り替えて ADR-048 更新 |
| Security 監査で secret 漏洩パターン発覚 | Sprint .2 で secret scan を先行実装し自己チェック済みにする |
| L サイズで Sprint .3 が scope 超過 | bats test + regression を Sprint .4 に切り出す carry rule を適用 |

---

## §6. V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 (本 PLAN) | docs/plans/PLAN-217-handover-federated.md |
| ② 実装コード | cli/lib/handover_federated.py |
| ③ テスト設計 (予定) | docs/v2/L4-test-design/PLAN-217-federated-test-design.md |
| ④ テストコード | cli/lib/tests/test_handover_federated.py |

双方向 reference: 実装コード docstring に「設計: PLAN-217」、テストコード docstring に
「DoD 検証: PLAN-217 §3」を追記する。本 PLAN → ADR-048:「L2 凍結: ADR-048 (transport
選択 + セキュリティ設計)」。

---

## §7. 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
