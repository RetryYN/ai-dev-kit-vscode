---
plan_id: PLAN-153
title: "PLAN-153: helix security audit framework (OWASP automated check)"
kind: impl
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
size: L
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G4, G6
agent_slots:
  - role: tl-advisor
    slot_label: "TL — semgrep/bandit/pip-audit 統合方針 adversarial check"
  - role: se
    slot_label: "SE — helix-security CLI 実装・OWASP A01-A10 チェック・python_module 起草"
  - role: security
    slot_label: "Security — OWASP Top 10 チェック項目設計・機密スキャン設計"
  - role: qa
    slot_label: "QA — pytest test 設計・false positive 境界テスト・fixture 設計"
  - role: pmo-sonnet
    slot_label: "PMO — helix doctor 統合整合・G2/G4/G6 ゲートとの連携確認"
generates:
  - artifact_path: cli/helix-security
    artifact_type: cli_extension
  - artifact_path: cli/lib/security_audit.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_security_audit.py
    artifact_type: test
  - artifact_path: cli/lib/migrations/v38_security_findings.py
    artifact_type: schema_migration
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-143
  blocks: []
related_plans:
  - PLAN-134
  - PLAN-143
  - PLAN-089
related_adr:
  - ADR-054
related_docs:
  - cli/lib/helix_db.py
  - cli/helix-gate
  - docs/v2/L1-REQUIREMENTS.md
reference_docs:
  - docs/plans/PLAN-143-helix-db-v37-event-telemetry.md
  - docs/plans/PLAN-089-gate-fail-close-design-doc-web-search-audit.md
  - docs/plans/PLAN-134-helix-metrics-cli.md
acceptance_criteria:
  - "helix security audit が OWASP A01-A10 自動チェックを実行し、findings を出力する"
  - "helix security audit --scan-secrets が api_key / token / private_key パターンを検出する"
  - "helix security audit --deps が pip-audit 結果を findings に統合する"
  - "helix doctor が security findings を WARN/FAIL として統合表示する"
  - "python3 -m py_compile cli/lib/security_audit.py PASS"
  - "pytest test_security_audit.py 全 PASS"
  - "sandbox fail 環境 (semgrep/bandit 未インストール) でも graceful degradation する"
  - "G4/G6 ゲートで helix security audit --gate-check が findings summary を返す"
---

# PLAN-153: helix security audit framework (OWASP automated check)

## L2 凍結 (ADR snapshot)

本 PLAN tree は OWASP automated check の新規統合を含む。semgrep / bandit / pip-audit の組み合わせと helix doctor 統合方針は L2 大局判断に該当するため、ADR snapshot を併設する。

| ADR | 凍結対象 | Status |
|---|---|---|
| ADR-054 (起票予定) | OWASP automated check 統合方針 (semgrep + bandit ベース、pip-audit 統合) | Proposed |

双方向 trace:
- 本 PLAN → ADR-054: frontmatter `related_adr` + 本 section
- ADR-054 → 本 PLAN: ADR-054 `## Related` に「PLAN-153 (実装 PLAN、本 ADR が L2 凍結する)」を記載

> ADR-054 は本 PLAN の L4 着手前 (G3 通過後) に起票する。WebSearch 3 query 必須 (OWASP Top 10 2021 / semgrep SAST / pip-audit 2026)。

---

## 0. 背景

G2/G4/G6 セキュリティゲートは現在、手動チェックリストと Codex security ロール委譲に依存している。HELIX プロジェクト自体の成長 (CLI 77 スクリプト / Python 111 モジュール / hook 15 件) により、手動審査の抜け漏れリスクが増大している。

本 PLAN は `helix security audit` CLI を新設し、以下を automated check に統合する:

1. OWASP A01-A10 自動チェック (semgrep + bandit ベース)
2. 機密スキャン (api_key / token / private_key / secret パターン検出)
3. 依存脆弱性スキャン (pip-audit)
4. helix doctor への findings 統合

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| OWASP Top 10 2021 | owasp.org/www-project-top-ten/ | A01-A10 チェック項目の根拠 |
| semgrep OSS rules | github.com/returntocorp/semgrep-rules | SAST ルールセット |
| bandit | bandit.readthedocs.io | Python AST ベース静的解析 |
| pip-audit | pypi.org/project/pip-audit/ | 依存脆弱性 (PyPI Advisory DB) |
| detect-secrets | github.com/Yelp/detect-secrets | 機密パターン検出 |

## 2. 設計方針

### 2.1 アーキテクチャ

```
cli/helix-security         bash dispatcher
  └── audit subcommand
        └── cli/lib/security_audit.py   Python ロジック
              ├── OWASPChecker           semgrep + bandit ラッパー
              ├── SecretsScanner         detect-secrets / gitleaks ラッパー
              ├── DepsScanner            pip-audit ラッパー
              └── FindingsStore          helix.db v38 security_findings table
```

### 2.2 OWASP A01-A10 チェック項目

| OWASP | 項目 | 検出手段 |
|---|---|---|
| A01 | Broken Access Control | semgrep (path traversal / IDOR pattern) |
| A02 | Cryptographic Failures | bandit (B501-B509 crypto rules) |
| A03 | Injection | semgrep (SQL injection / shell injection) |
| A04 | Insecure Design | bandit (hardcoded password / B104-B108) |
| A05 | Security Misconfiguration | bandit (B101 assert / B110 try-except-pass) |
| A06 | Vulnerable Components | pip-audit (PyPI Advisory DB) |
| A07 | Auth Failures | semgrep (token in URL / weak JWT) |
| A08 | Software Integrity | (外部依存 hash 検証、Phase 2 carry) |
| A09 | Logging Failures | bandit (B303-B304) |
| A10 | SSRF | semgrep (requests without allowlist) |

### 2.3 機密スキャン パターン

```python
SECRET_PATTERNS = [
    r"api[_-]?key\s*=\s*['\"][^'\"]{8,}",
    r"(secret|token|password)\s*=\s*['\"][^'\"]{8,}",
    r"private[_-]?key\s*=\s*-----BEGIN",
    r"(ANTHROPIC|OPENAI|AWS)[_A-Z]*_KEY\s*=\s*['\"][^'\"]{16,}",
]
```

`.helix/` / `.git/` / `tests/fixtures/` は除外対象。

### 2.4 helix.db v38 schema

PLAN-143 (v37) の次バージョンとして v38 migration を追加:

```sql
CREATE TABLE IF NOT EXISTS security_findings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT NOT NULL,
    run_at      TEXT NOT NULL,
    owasp_id    TEXT,           -- "A01" 〜 "A10" または NULL
    category    TEXT NOT NULL,  -- "owasp" / "secrets" / "deps"
    severity    TEXT NOT NULL,  -- "critical" / "high" / "medium" / "low" / "info"
    file_path   TEXT,
    line_no     INTEGER,
    rule_id     TEXT,
    message     TEXT,
    suppressed  INTEGER DEFAULT 0
);
```

### 2.5 graceful degradation

semgrep / bandit / pip-audit が未インストールの場合、各チェックを skip して WARN を出力。`--require-all-tools` フラグ指定時のみ abort する。

## 3. CLI インターフェース

```bash
# 全チェック実行
helix security audit [--path PATH] [--format text|json] [--gate-check]

# 個別チェック
helix security audit --owasp-only
helix security audit --scan-secrets
helix security audit --deps

# helix doctor 統合
helix doctor  # security_findings を WARN/FAIL として統合表示

# サプレス管理
helix security suppress <finding_id> --reason "..."
helix security list [--severity high] [--since YYYY-MM-DD]
```

## 4. L4 実装 Sprint 計画

### Sprint .1: skeleton + OWASPChecker

- Entry: PLAN-143 v37 migration 完了確認
- 実装: cli/helix-security skeleton + cli/lib/security_audit.py OWASPChecker
- チェック: py_compile PASS / bats help PASS
- Exit: `helix security audit --owasp-only` が semgrep/bandit を呼び出し findings を返す

### Sprint .2: SecretsScanner + DepsScanner

- 実装: SecretsScanner (detect-secrets ラッパー) + DepsScanner (pip-audit ラッパー)
- graceful degradation (未インストール WARN)
- Exit: `helix security audit --scan-secrets` / `--deps` が動作する

### Sprint .3: FindingsStore + helix.db v38 migration

- 実装: v38 migration (cli/lib/migrations/v38_security_findings.py)
- FindingsStore で findings を helix.db に記録
- Exit: `helix security list` が DB から findings を返す

### Sprint .4: helix doctor 統合 + G4/G6 gate-check

- 実装: helix doctor への findings 統合 (severity=critical → FAIL / high → WARN)
- `helix security audit --gate-check` が findings summary JSON を返す
- G4/G6 ゲート呼び出しフローを helix-gate に追加
- Exit: pytest test_security_audit.py 全 PASS / helix doctor 統合動作確認

### Sprint .5: レビュー + ドキュメント整合

- セルフレビュー + pmo-sonnet review
- docs/commands/index.md に helix security コマンド追加
- OWASP A08 (外部依存 hash 検証) を debt-register に carry note

## 5. リスクと緩和策

| リスク | 影響 | 緩和 |
|---|---|---|
| semgrep 大規模 repo でのタイムアウト | G4 阻害 | `--timeout 60s` / `--max-target-bytes 1MB` デフォルト設定 |
| false positive 多発による WARN 無視 | セキュリティ形骸化 | severity 閾値調整 + suppress 機能 |
| pip-audit が外部ネットワーク依存 | sandbox 環境で fail | graceful degradation (offline WARN) |
| v38 migration が PLAN-143 v37 と競合 | DB 破損 | requires: PLAN-143 を frontmatter で明示 |

## 6. DoD (Definition of Done)

- acceptance_criteria 全件 PASS
- helix doctor に findings が表示される
- G4/G6 ゲート呼び出しフローが helix-gate に追加済
- OWASP A08 carry note が debt-register に記録済
- ADR-054 起票済 (L2 凍結)
