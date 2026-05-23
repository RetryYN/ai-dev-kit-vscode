---
plan_id: PLAN-204
title: "PLAN-204: secret rotation framework (API key 自動 rotation)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl-advisor
    slot_label: "TL — rotation cycle 設計・env/1Password/GitHub Secrets 統合方針 adversarial check"
  - role: se
    slot_label: "SE — helix secret rotate CLI 実装・rotation_store.py 起草・smooth rotation ロジック"
  - role: security
    slot_label: "Security — secret leakage 検出パターン設計・rotation trigger 条件設計"
  - role: qa
    slot_label: "QA — rotation シナリオ test 設計・mock key backend fixture 設計"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-153 との重複確認・helix doctor 統合整合・DoD チェック"
generates:
  - artifact_path: cli/helix-secret
    artifact_type: cli_extension
  - artifact_path: cli/lib/rotation_store.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_rotation_store.py
    artifact_type: test
  - artifact_path: cli/lib/migrations/v39_secret_rotation.py
    artifact_type: schema_migration
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-153
  blocks: []
related_plans:
  - PLAN-153
  - PLAN-089
related_adr:
  - ADR-056 候補 (secret rotation 統合方針 L2 snapshot、本 PLAN 起票後に起票)
related_docs:
  - cli/lib/helix_db.py
  - cli/helix-security
acceptance_criteria:
  - "helix secret rotate が current key を使い続けながら new key を parallel 有効化し、旧 key を失効させる"
  - "helix secret status が各 key の登録日・最終 rotation 日・次回期限を表示する"
  - "rotation cycle 90 days 経過時に helix doctor が WARN を出力する"
  - "env / 1Password / GitHub Secrets の 3 backend を --backend フラグで切り替え可能にする"
  - "python3 -m py_compile cli/lib/rotation_store.py PASS"
  - "pytest cli/lib/tests/test_rotation_store.py 全 PASS"
  - "backend 未設定時に graceful degradation (env fallback) する"
---

# PLAN-204: secret rotation framework (API key 自動 rotation)

## L2 凍結 (ADR snapshot)

本 PLAN tree は API key の自動 rotation という新規セキュリティ運用機能の統合を含む。
env / 1Password / GitHub Secrets の multi-backend 抽象化と smooth rotation の採用方針は L2 大局判断に該当するため、ADR snapshot を併設する。

| ADR | 凍結対象 | Status |
|---|---|---|
| ADR-056 (起票予定) | secret rotation 統合方針 (multi-backend + smooth rotation + 90-day cycle) | Proposed |

双方向 trace:
- 本 PLAN → ADR-056: frontmatter `related_adr` + 本 section
- ADR-056 → 本 PLAN: `## Related` に「PLAN-204 (実装 PLAN、本 ADR が L2 凍結する)」を記載

> ADR-056 は本 PLAN の L4 着手前 (G3 通過後) に起票する。WebSearch 3 query 必須 (API key rotation best practice / 1Password CLI secret management / GitHub Actions secret rotation 2025)。

---

## 0. 背景

helix-codex / helix-claude は OpenAI / Anthropic API key を環境変数から取得して使用している。
現状では以下のリスクが放置されている:

1. key の有効期限・最終更新日が追跡されていない (期限切れ検知なし)
2. 漏洩時の rotation 手順が存在しない (手動対応依存)
3. rotation 中に API 呼び出しが失敗するダウンタイムが発生しうる

本 PLAN は `helix secret` CLI を新設し、smooth rotation (新旧 key 並行期間 + 旧 key 失効) を framework 化する。

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| OWASP ASVS V2.10 | owasp.org/www-project-application-security-verification-standard | secret lifecycle 管理要件の根拠 |
| 1Password CLI Secrets Automation | developer.1password.com/docs/cli/secrets | 1Password backend integration の参照実装 |
| GitHub Actions encrypted secrets | docs.github.com/en/actions/security-guides/encrypted-secrets | GitHub Secrets backend の参照実装 |
| NIST SP 800-57 §5.3 | nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-57pt1r5.pdf | 暗号鍵のライフサイクル管理 (rotation cycle 根拠) |

## 2. 設計方針

### 2.1 アーキテクチャ

```
cli/helix-secret            bash dispatcher
  ├── rotate subcommand
  ├── status subcommand
  └── list subcommand
        └── cli/lib/rotation_store.py   Python ロジック
              ├── SecretBackend (abstract)
              │     ├── EnvBackend       環境変数 (.env / export)
              │     ├── OnePasswordBackend  op CLI ラッパー
              │     └── GitHubSecretsBackend  gh CLI ラッパー
              ├── RotationScheduler    90-day cycle + WARN 管理
              └── RotationStore        helix.db v39 secret_rotation table
```

### 2.2 smooth rotation フロー (4-Step)

(1) new key を backend に登録 (old key 維持) → (2) new key で API 疎通確認 → (3) helix.db に rotation 記録 → (4) grace period (default: 10 分) 後に old key 失効。

### 2.3 90-day cycle WARN

`check_rotation_due(last_rotated)` が `(now - last_rotated).days >= 90` を判定し、helix doctor hook から呼び出して期限超過 key を WARN 出力する。

### 2.4 multi-backend 抽象

`SecretBackend` ABC (get / set / delete) を `EnvBackend` / `OnePasswordBackend` / `GitHubSecretsBackend` で実装。`--backend env|1password|github` フラグで切り替え、未設定時は env fallback。

### 2.5 helix.db v39 schema

PLAN-153 (v38) の次バージョン。`secret_rotation` table に `key_name / backend / registered_at / last_rotated_at / next_due_at / status` を追加。key value は記録しない (漏洩防止)。

## 3. CLI インターフェース

```bash
# key 登録 / rotation
helix secret rotate <KEY_NAME> --backend env|1password|github [--grace-period N]

# status 一覧
helix secret status [--key KEY_NAME]

# helix doctor 統合 (期限切れ key を WARN)
helix doctor  # secret_rotation を WARN として統合表示

# 手動失効
helix secret revoke <KEY_NAME> --reason "..."
```

## 4. L4 実装 Sprint 計画

| Sprint | 実装内容 | Exit 条件 |
|---|---|---|
| .1 | `rotation_store.py` skeleton + EnvBackend | py_compile PASS / EnvBackend 動作確認 |
| .2 | OnePasswordBackend + GitHubSecretsBackend + graceful degradation | `--backend` フラグ動作確認 |
| .3 | v39 migration + RotationScheduler (90-day check_rotation_due) | `helix secret status` が DB から期限を返す |
| .4 | smooth rotation 4-Step + helix doctor 統合 | pytest 全 PASS / doctor WARN 確認 |
| .5 | セルフレビュー + pmo-sonnet review + docs/commands/index.md 追加 + ADR-056 起票 | DoD 全件 PASS |

## 5. リスクと緩和策

| リスク | 影響 | 緩和 |
|---|---|---|
| rotation 中の API 呼び出し失敗 | サービス中断 | grace period でダウンタイムゼロ rotation |
| op / gh CLI 未インストール | backend 切替不能 | graceful degradation + env fallback |
| v39 migration が PLAN-153 v38 と競合 | DB 破損 | requires: PLAN-153 を frontmatter で明示 |
| key value が helix.db に平文保存される | 機密漏洩 | key name のみ記録し value は記録しない |

## 6. DoD (Definition of Done)

- acceptance_criteria 全件 PASS
- smooth rotation 4-Step フローが pytest で検証済
- helix doctor に rotation due WARN が表示される
- ADR-056 起票済 (L2 凍結)
- `docs/commands/index.md` に `helix secret` コマンド追加済
