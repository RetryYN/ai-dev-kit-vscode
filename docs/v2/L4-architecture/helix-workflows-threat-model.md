---
doc_id: l4-helix-workflows-threat-model
title: "HELIX-workflows V2 脅威分析 / セキュリティ設計書 (threat model)"
status: frozen
created: 2026-05-30
owner: PM
process_layer: L4
pairs_design: docs/v2/L4-architecture/helix-workflows-system-architecture.md
adr_snapshot:
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/adr/ADR-045-helix-workflows-v2-l4-function-design-snapshot.md
pairs_test_design: docs/v2/L9-test-design/helix-workflows-system-test-design.md
industry_standards:
  - IEEE 1016:2009 (security viewpoint)
  - ISO/IEC 42010:2022 (architecture viewpoint)
  - ISO/IEC 25010:2023 (Security / Safety 特性)
  - STRIDE threat model
---

# HELIX-workflows V2 脅威分析 / セキュリティ設計書 (threat model)

> (recovery-2026-05-30 独立化: system-architecture §9 から正本移設)

関連スキル: [`workflow/threat-model`](../../../skills/workflow/threat-model/SKILL.md)

## §0 概要

本文書は HELIX-workflows V2 の L4 セキュリティ viewpoint を定義する独立設計書です。

### §0.1 適用標準

| 標準 | 適用箇所 |
|---|---|
| **IEEE 1016:2009** | Software Design Description の Security viewpoint (§0.5 整合) |
| **ISO/IEC 42010:2022** | Architecture Viewpoint として本文書が Security View を提供 |
| **ISO/IEC 25010:2023** | Security 特性 5 サブ特性 (§3)、Safety 特性 4 サブ特性 (§4) へ直接対応 |
| **STRIDE** | 脅威モデリング手法として §2 STRIDE マトリクスに適用 |

### §0.2 IEEE 1016 §0.5 整合表

| IEEE 1016 要素 | 本文書での対応 |
|---|---|
| Design Viewpoint | Security Viewpoint — 信頼境界・脅威・セキュリティ対策を記述 |
| Design View | §1 信頼境界一覧 + §2 STRIDE マトリクス + §3/§4 ISO 25010 対応 |
| Design Elements | TB-1〜TB-6 (信頼境界)、STRIDE カテゴリ別脅威シナリオ、対策実装 |
| Design Rationale | CLAUDE.md §禁止事項 / HELIX gate fail-close / pretooluse guard が設計根拠 |

### §0.3 V-model pair

| 設計工程 (本文書) | テスト工程 |
|---|---|
| L4 脅威分析 / Security viewpoint | L9 §ST-9 security 観点テスト設計 (docs/v2/L9-test-design/helix-workflows-system-test-design.md) |

---

## §1 信頼境界一覧

HELIX-workflows V2 が持つセキュリティ上の信頼境界を 6 つ識別する。

| 境界 ID | 境界の説明 | 内側 | 外側 |
|---|---|---|---|
| TB-1 | AI エージェント ↔ repo files | HELIX CLI / hook / gate | Claude Code Opus / Codex (委譲) |
| TB-2 | subagent model 指定 | frontmatter で許可された model family | Agent tool の model 明示指定 |
| TB-3 | raw bypass 環境変数 | HELIX guard (fail-close) | `HELIX_ALLOW_RAW_CODEX/CLAUDE/AGENT` 保持者 |
| TB-4 | 委譲 Codex ↔ git | PM (Opus) が検証後 commit する経路 | 委譲 Codex が直接 `git commit` する経路 |
| TB-5 | docs/skills への secret/PII 混入 | 設計文書 / スキル文書 | credential / 個人情報 |
| TB-6 | budget / API cost | HELIX budget monitor | 過剰 API 呼び出し (DoS 相当) |

---

## §2 STRIDE 脅威マトリクス

**注**: STRIDE = Spoofing / Tampering / Repudiation / Information Disclosure / Denial of Service / Elevation of Privilege。

| 境界 | STRIDE 脅威 | 具体的脅威シナリオ | 対策 (実装済 / 計画) | implementation_status |
|---|---|---|---|---|
| TB-1 | **T**: Tampering | AI エージェントが想定外ファイルを独断変更 | `pretooluse-agent-guard.sh` subagent allowlist (12 種) fail-close、gate fail-close、Recovery mode | implemented |
| TB-1 | **T**: Tampering | 工程外・承認前のコード編集 | Plan Consent Gate (`awaiting_plan_consent` stop)、commit 禁止ルール | implemented (policy) |
| TB-2 | **S**: Spoofing / **E**: Elevation | 許可 model family と異なる model 指定で Opus を想定外発火 | frontmatter model family 一致強制 (不一致 → exit 2 block)、`pretooluse-agent-guard.sh` T2/T3/T12 block 確認済 (commit 3ae4af3) | implemented |
| TB-3 | **E**: Elevation of Privilege | guard 迂回による無制限操作 | bypass 時に `HELIX_ALLOW_RAW_*=1` + 理由 evidence 必須、会話 / final report への証跡義務 | implemented (policy) |
| TB-4 | **T**: Tampering | 委譲 Codex が git add/commit/push を直接実行し、PM 検証をスキップ | 委譲 Codex commit 禁止ルール (CLAUDE.md §委譲 Codex のコミット禁止)、`helix codex` hard guard (`--plan-only` / `--consent auto`) | implemented |
| TB-5 | **I**: Information Disclosure | credential / PII が docs や skills に混入 | CLAUDE.md §禁止事項、gitleaks / semgrep 候補 lint (L14 carry) | partial (policy implemented, CI lint planned) |
| TB-6 | **D**: Denial of Service | 過剰 API 呼び出しによる budget 枯渇 | `helix budget status` / `helix budget simulate`、80% 到達で追加予算申請ルール | implemented |

---

## §3 ISO/IEC 25010:2023 Security 特性 × HELIX 対応

ISO/IEC 25010:2023 Security 特性の 5 サブ特性に対し、HELIX-workflows V2 の設計対応を示す。

| 25010:2023 Security サブ特性 | HELIX 対応 |
|---|---|
| **Confidentiality** (機密性) | docs/skills への credential 混入禁止、TB-5 guard |
| **Integrity** (完全性) | TB-1/TB-4 fail-close で想定外変更を阻止、pre-commit hook で lint / schema 検証 |
| **Non-repudiation** (否認防止) | helix.db event_log への監査記録、audit YAML retention 90 日、bypass 時 evidence 義務 |
| **Accountability** (責任追跡性) | agent_role / event_log_id / owner field による操作トレース、handover owner 遷移記録 |
| **Authenticity** (真正性) | subagent frontmatter model family 一致強制、Plan Consent Gate による承認フロー |

---

## §4 ISO/IEC 25010:2023 Safety 特性 × HELIX 対応

ISO/IEC 25010:2023 Safety 特性 (2023 新追加) の 4 サブ特性に対し、HELIX-workflows V2 の設計対応を示す。

| Safety サブ特性 | HELIX 対応 |
|---|---|
| **Operational Constraint Satisfaction** | gate fail-close (G2/G4/G7) で工程逸脱を構造的に阻止 |
| **Risk Identification** | Recovery mode 発火条件 4 種 (想定外大規模変更 / 工程逸脱 / 認識ズレ / 予算超過) で事前検出 |
| **Fail Safe** | fail-close exit 2 (block) / fail-open exit 0 (pass + advisory) の 2 段設計、hook timeout は fail-open |
| **Hazard Warning** | statusLine debounce + hysteresis で重要警告の連打を防止しつつ見落とし回避 |

---

## §5 L9 security pair trace (ST-9)

本文書は L9 総合テスト設計と V-model pair freeze されており、以下の対応関係を持つ。

| 本文書の節 | L9 テスト設計 ID | テスト観点 |
|---|---|---|
| §1 信頼境界一覧 (TB-1〜TB-6) | ST-9-TB | 各信頼境界の guard 動作確認 |
| §2 STRIDE マトリクス | ST-9-STRIDE | 脅威シナリオの対策実装確認 |
| §3 Security 5 サブ特性 | ST-9-SEC | ISO 25010:2023 Security サブ特性の充足確認 |
| §4 Safety 4 サブ特性 | ST-9-SAF | ISO 25010:2023 Safety サブ特性の充足確認 |

pair テスト設計正本: `docs/v2/L9-test-design/helix-workflows-system-test-design.md` §ST-9 (security 観点、planned)
