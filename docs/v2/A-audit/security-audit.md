# FR-INV12: セキュリティ現状監査

最終更新: 2026-05-14  
監査者: Research (Codex)  
不確実性:

- `helix` CLI がこの実行環境に存在せず、`helix code find` / `helix review --uncommitted` / `pip-audit` は未実行。コード読解と既存監査 doc を代替証跡にした。
- `npm` は存在するが `package.json` / `package-lock.json` は repo 内で確認できず、Node 依存脆弱性の実監査は「対象なし寄りの未確認」とした。
- git hook は配布物 (`scripts/git-hooks/pre-commit`) と runtime hook 登録 (`.claude/settings.json`) を確認したが、各開発者環境で実際に有効化済みかは断定できない。

## 概要

HELIX にはすでに複数の fail-close ガードが存在する。強い領域は `PreToolUse` による raw CLI / Opus 直接編集 block、`allowed-files` 事後検証、observability / invocation telemetry の redaction、pre-commit の secret scan である。一方で、認証情報の権限分離、destructive operation の統一 deny policy、研究ツールの role 強制、依存脆弱性スキャンの常設化、AI 固有の prompt injection / tool abuse 検出はまだ部分実装に留まる。

V2 Phase 4 の入力としては「既存ガードを detector 化して横断監視に昇格する」方針が最も妥当で、全面再実装よりも `PLAN-018 / 043 / 063 / 067` の既存資産を伸ばす方がコスト効率が高い。

## 選択肢

### Option A: 現状ガードを維持し、監査だけ文書化

- メリット: 追加実装が最小。
- デメリット: hook / wrapper / pre-commit に散在する検出結果が Phase 4 detector と連動せず、再発学習が弱い。
- 推奨度: 低。

### Option B: 既存ガードを detector / telemetry へ接続して拡張

- メリット: 既存 fail-close を活かしつつ、Phase 4 で監視・集計・stop 判定を強化できる。
- デメリット: `PLAN-067` の file -> DB sync と detector routing の追加設計が必要。
- 推奨度: 高。

### Option C: hook を増やして個別に都度防御

- メリット: 単発の穴は早く塞げる。
- デメリット: ルールが各 wrapper に分散し、運用者が全体像を追えなくなる。誤検知 / 例外運用も増えやすい。
- 推奨度: 中。

## 推奨

**Option B** を推奨する。理由は 3 点。

1. 既存の強い制御点はすでに存在する。
   `cli/lib/llm_guard.py`、`.claude/hooks/pretooluse-opus-repo-block.sh`、`cli/lib/codex_post_validation.py`、`cli/lib/observability_helper.py`、`scripts/git-hooks/pre-commit`
2. Phase 4 の要件は「新しいガードを増やす」より「既存ガードを detector / stop / telemetry に昇格する」方が整合する。
   `docs/v2/L1-REQUIREMENTS.md`, `docs/plans/PLAN-063-helix-db-detector-system.md`, `docs/plans/PLAN-067-helix-automation-layer.md`
3. 現状の主な gap は未実装よりも「横断接続不足」である。
   例: hook の結果が detector verdict に入らない、dependency scan が常設コマンドに入らない、AI 特有 risk が review script 止まり

## 監査範囲とソース

### Tier 1 実装

- `.claude/settings.json`
- `.claude/hooks/pretooluse-opus-repo-block.sh`
- `cli/helix-codex`
- `cli/helix-claude`
- `cli/lib/llm_guard.py`
- `cli/lib/codex_post_validation.py`
- `cli/lib/helix_db.py`
- `cli/lib/observability_helper.py`
- `cli/lib/research_tool_guard.py`
- `cli/lib/agent_policy_guard.py`
- `cli/lib/global_store.py`
- `cli/libexec/helix-pre-bash`
- `cli/libexec/helix-post-tool-use`
- `scripts/git-hooks/pre-commit`
- `scripts/review-upstream-sync.sh`

### Tier 2 設計・既存監査

- `docs/plans/PLAN-018-llm-guard-retroactive-hardening.md`
- `docs/plans/PLAN-028-helix-v2-orchestration.md`
- `docs/plans/PLAN-043-consolidated-carry-resolution.md`
- `docs/plans/PLAN-063-helix-db-detector-system.md`
- `docs/plans/PLAN-067-helix-automation-layer.md`
- `docs/v2/L1-REQUIREMENTS.md`
- `docs/v2/A-audit/capability-inventory.md`
- `docs/v2/A-audit/hooks-commands-subagents.md`

## リスク一覧

| リスク ID | 軸 | 重要度 | 既存対策 | gap (不足箇所) | V2 変更計画 | V2 Phase 紐付け |
|---|---|---|---|---|---|---|
| SEC-001 | 認証 / 認可 | P1 | `.claude/hooks/pretooluse-opus-repo-block.sh`, `.claude/settings.json`, PLAN-043 | Opus block はあるが「誰が write 可能か」の中央 RBAC 定義がなく、環境変数例外に依存する。 | extend | Phase 1, Phase 4 |
| SEC-002 | 認証 / 認可 | P2 | `cli/helix-claude`, `cli/config/models.yaml`, PLAN-028 | PMO Sonnet/Haiku/impl-sonnet の権限差が runtime policy と文書に分散し、誤設定検知が弱い。 | modify | Phase 1 |
| SEC-003 | 認証 / 認可 | P2 | `cli/helix-codex`, `cli/helix-claude`, PLAN-028 | Claude/Codex token 自体の発行・期限・ローテーション方針は repo で管理されていない。 | as-is | Phase 1 |
| SEC-004 | 認証 / 認可 | P2 | `cli/scripts/setup-bats.sh` | `sudo` 使用は対話実行側に残るが、sudo 実行を一元記録・承認する仕組みがない。 | extend | Phase 4 |
| SEC-005 | 入力検証 | P1 | `cli/lib/llm_guard.py`, `cli/libexec/helix-pre-bash`, PLAN-018 | Bash command surface の検査は強いが deny 理由の構造化記録が detector 側へ未接続。 | extend | Phase 4 |
| SEC-006 | 入力検証 | P1 | `cli/lib/codex_post_validation.py`, `cli/helix-codex` | `--allowed-files` は post-validation 中心で、事前 deny ではない。誤編集は発生後にしか検出できない。 | extend | Phase 4, Phase 5 |
| SEC-007 | 入力検証 | P2 | `cli/lib/research_tool_guard.py`, `.claude/settings.json` | WebSearch/WebFetch guard は tool 種別しか見ず、role=research 強制や query 内容検査がない。 | modify | Phase 4 |
| SEC-008 | 入力検証 | P2 | `cli/lib/agent_policy_guard.py`, PLAN-018 | team 定義では research task を role=research に寄せるが、単発委譲やローカル直接実行までは強制しない。 | extend | Phase 4 |
| SEC-009 | 入力検証 | P2 | `cli/lib/observability_helper.py`, `cli/lib/helix_db.py` | JSON parse はあるが payload サイズ・ネスト深さ・巨大入力の DoS 抑止が明示されていない。 | modify | Phase 2 |
| SEC-010 | 入力検証 | P2 | `scripts/review-upstream-sync.sh` | prompt injection 検知は review script 内の正規表現のみで、runtime prompt 全般へは未展開。 | extend | Phase 4 |
| SEC-011 | secret 管理 | P1 | `scripts/git-hooks/pre-commit`, Sec-5 | secret scan は強いが git hook 未導入環境では素通りする。server-side / CI 側の fail-close がない。 | extend | Phase 4, Phase 5 |
| SEC-012 | secret 管理 | P2 | `cli/lib/helix_db.py`, PLAN-063 | `invocation_log.raw_meta` の allowlist は狭いが redact pattern が `sk-*` / `Bearer` / `token=` 中心で網羅不足。 | modify | Phase 4 |
| SEC-013 | secret 管理 | P2 | `cli/lib/observability_helper.py`, `docs/features/PLAN-063/D-TELEMETRY/redaction-rules.md` | redaction denylist は local file 依存で、project 標準 denylist の配布・検証がない。 | extend | Phase 3, Phase 4 |
| SEC-014 | secret 管理 | P2 | `cli/lib/global_store.py` | global store の redaction は単純 substring ベースで誤検知/見逃しの両方があり得る。 | modify | Phase 4 |
| SEC-015 | secret 管理 | P3 | `AGENTS.md`, `.claude/memory/constraints.md` | `.env` コミット禁止は規約中心で、`.env*` を検出する専用 hook は未確認。 | extend | Phase 4 |
| SEC-016 | destructive op | P1 | `cli/lib/llm_guard.py`, PLAN-018 | raw `git reset --hard` など shell 実行の遮断はあるが、destructive git command を明示分類した detector がない。 | extend | Phase 4 |
| SEC-017 | destructive op | P1 | `scripts/review-upstream-sync.sh` | `rm -rf` は review script の injection pattern で警告可能だが runtime 全体での専用 deny ルールは見えにくい。 | extend | Phase 4 |
| SEC-018 | destructive op | P2 | `scripts/git-hooks/pre-commit` | `git commit --no-verify` は警告文のみで、bypass 実績の telemetry / detector 化がない。 | extend | Phase 4 |
| SEC-019 | destructive op | P2 | `AGENTS.md`, `HELIX_CORE.md` | `DROP TABLE` や destructive DB 操作はポリシー上禁止だが、SQL 文字列に対する静的検知が未確認。 | new | Phase 4 |
| SEC-020 | destructive op | P3 | `cli/helix-codex` | `danger-full-access` は対話確認や env guard がある前提だが、実際の利用頻度監査が文書化されていない。 | extend | Phase 4 |
| SEC-021 | hook | P1 | `.claude/settings.json`, `.claude/hooks/pretooluse-opus-repo-block.sh`, PLAN-043 | Opus 直接 Edit block は強いが、local settings override や hook 無効化の検出がない。 | extend | Phase 4 |
| SEC-022 | hook | P2 | `cli/libexec/helix-post-tool-use`, PLAN-067 | PostToolUse は path 抽出と router 呼び出しまでで、security finding の自動集約・再評価が未実装。 | extend | Phase 5 |
| SEC-023 | hook | P2 | `.claude/settings.json` | Stop hook は `blockOnFailure=false` で fail-open。session telemetry 欠落が静かに見逃される。 | modify | Phase 4 |
| SEC-024 | hook | P3 | `cli/helix-check-claudemd`, `docs/v2/A-audit/hooks-commands-subagents.md` | deprecated wrapper を残したままで、監査対象の境界が曖昧。運用者が誤って古い hook を信頼しやすい。 | deprecate | Phase 1 |
| SEC-025 | 依存 | P1 | `requirements-dev.txt`, `.claude/agents/security-audit.md` | Python 依存は存在するが `pip-audit` が環境未導入で、定常 audit が実行経路に組み込まれていない。 | extend | Phase 4 |
| SEC-026 | 依存 | P2 | `npm` コマンド存在のみ確認 | Node audit 手順は agent prompt にあるが、repo に `package.json` が見当たらず監査対象の有無判定が自動化されていない。 | modify | Phase 1 |
| SEC-027 | 依存 | P2 | `scripts/git-hooks/pre-commit` | secret scan はあるが SBOM / lockfile integrity / hash pinning の仕組みは未確認。 | new | Phase 3, Phase 4 |
| SEC-028 | OWASP | P1 | `cli/lib/llm_guard.py`, `cli/lib/agent_policy_guard.py`, `scripts/review-upstream-sync.sh` | A03 Injection 対策は点在するが、shell/prompt/tool injection を統一モデルで監査していない。 | extend | Phase 4 |
| SEC-029 | OWASP | P2 | `.claude/hooks/pretooluse-opus-repo-block.sh`, `cli/helix-claude`, `cli/helix-codex` | A01 Broken Access Control 観点では role 境界はあるが、権限テストケースや matrix が不足。 | modify | Phase 2 |
| SEC-030 | OWASP | P2 | `cli/lib/observability_helper.py`, `cli/lib/helix_db.py`, PLAN-063 | A09 Logging/Monitoring は進んでいるが security event 専用 taxonomy と alert 条件が不足。 | extend | Phase 4 |
| SEC-031 | OWASP | P2 | `scripts/git-hooks/pre-commit`, `cli/lib/codex_post_validation.py` | A08 Software Integrity は pre-commit / post-validation に分散し、supply chain integrity の一貫ストーリーが弱い。 | extend | Phase 4, Phase 5 |
| SEC-032 | AI | P1 | `scripts/review-upstream-sync.sh`, `cli/lib/llm_guard.py`, PLAN-018 | prompt injection / tool use abuse / data exfiltration を AI 固有 axis として detector 化していない。 | new | Phase 4 |
| SEC-033 | AI | P2 | `cli/lib/research_tool_guard.py`, `cli/lib/agent_policy_guard.py` | 「外部調査は research role へ寄せる」方針はあるが、回答内容の一次ソース検証までは機械強制していない。 | extend | Phase 4 |
| SEC-034 | AI | P2 | `cli/lib/codex_post_validation.py`, summary marker discipline | output validation は diff_lines / summary block 中心で、危険提案や policy drift の semantic 検査がない。 | extend | Phase 4 |
| SEC-035 | sandbox | P1 | `cli/helix-codex`, `AGENTS.md`, `HELIX_CORE.md` | sandbox 制御は harness 依存で、raw 実行を完全に 0 にできない限り bypass 余地が残る。 | extend | Phase 4 |
| SEC-036 | sandbox | P2 | `cli/lib/llm_guard.py`, `cli/helix-codex` | network / sandbox / approval option の遮断ロジックは強いが、拒否イベントが phase/gate report に見えない。 | extend | Phase 4 |

## OWASP Top 10 マッピング

| OWASP | 関連リスク | 現状評価 |
|---|---|---|
| A01 Broken Access Control | SEC-001, 002, 021, 029, 035 | 部分機能。role 境界と Opus block はあるが、権限マトリクスと検証が弱い。 |
| A02 Cryptographic Failures | SEC-012, 013, 014 | 部分機能。redaction はあるが secret lifecycle 管理までは未到達。 |
| A03 Injection | SEC-005, 007, 008, 010, 028, 032 | 部分機能。shell / prompt / tool injection を個別に見ており統合検知がない。 |
| A04 Insecure Design | SEC-001, 016, 019, 032 | 部分機能。禁止事項は多いが destructive / AI misuse を architecture decision に格上げできていない。 |
| A05 Security Misconfiguration | SEC-020, 021, 023, 024, 035 | 部分機能。settings override と fail-open 点が残る。 |
| A06 Vulnerable Components | SEC-025, 026, 027 | 弱い。audit 手順はあるが常設化不足。 |
| A07 Identification and Authentication Failures | SEC-001, 002, 003, 004 | 部分機能。role/engine は管理するが token / sudo 運用は repo 外依存。 |
| A08 Software and Data Integrity Failures | SEC-011, 018, 027, 031 | 部分機能。pre-commit / post-validation はあるが end-to-end integrity ではない。 |
| A09 Security Logging and Monitoring Failures | SEC-022, 023, 030, 036 | 部分機能。telemetry はあるが security verdict と alert が薄い。 |
| A10 SSRF / External Resource Risk | SEC-007, 033 | 弱い。research tool guard はあるが query / destination 監査が弱い。 |

## AI 特有リスク評価

| 観点 | 現状 | gap | 推奨 |
|---|---|---|---|
| Prompt injection | `scripts/review-upstream-sync.sh` にパターン検知、`llm_guard.py` に shell surface 検査 | runtime prompt 全体・skill / doc ingest への統一検知がない | detector 化し、review / hook / post-validation を横断集計する |
| Tool use abuse | raw `codex` / `claude` 遮断、Opus repo edit block、allowed-files 監査 | role outside tool usage の横断ポリシーが弱い | tool usage taxonomy を `invocation_log` / detector へ追加する |
| Data exfiltration | redaction, allowlist, global store sanitize あり | export / no-redact / include-secrets の使用を強制承認化していない | P1 detector と PM/TL approval evidence を追加する |
| Output validation | summary marker / diff_lines / allowed-files はある | semantic risk 判定がない | dangerous suggestion detector を導入する |
| Sandbox escape | harness と option guard がある | raw 実行 0 化の保証が弱い | bypass 試行を security event として集計する |

## V2 Phase 4 で追加すべき security detector

1. `SECDET-01 prompt-injection`
   shell / skill / upstream diff / doc payload から injection pattern を統合検知。
2. `SECDET-02 destructive-op`
   `git reset --hard`, `rm -rf`, `DROP TABLE`, `--no-verify`, `danger-full-access` を集計。
3. `SECDET-03 secret-handling`
   `--no-redact`, `--include-secrets`, secret-like string, `.env*` 変更を検知。
4. `SECDET-04 hook-bypass`
   PreToolUse / PostToolUse / Stop hook の未発火、override、disable を検知。
5. `SECDET-05 access-boundary`
   role と実操作の乖離、PMO/Opus/impl-sonnet の権限逸脱を検知。
6. `SECDET-06 dependency-hygiene`
   `pip-audit` 未実施、lockfile 不在、監査対象不明の dependency path を検知。
7. `SECDET-07 research-egress`
   WebSearch/WebFetch の role、query、出力引用の不足を検知。
8. `SECDET-08 telemetry-redaction`
   `raw_meta`, observability export, global store に対する redaction 漏れを検知。

## 即修正必須 (P1)

- SEC-001: 権限境界が env 例外頼みで中央 RBAC 不在
- SEC-005: Bash guard の deny 結果が detector に入らない
- SEC-006: `--allowed-files` が事後検知中心
- SEC-011: secret scan がローカル hook 依存
- SEC-016: destructive git command の専用 detector 不在
- SEC-021: hook disable / override 検知不足
- SEC-025: Python dependency audit 常設化不足
- SEC-028: OWASP A03 を統合監査していない
- SEC-032: AI 固有リスク detector 不在
- SEC-035: sandbox 制御が harness 依存

## リスク件数集計

### 重要度別

| 重要度 | 件数 |
|---|---:|
| P1 | 10 |
| P2 | 23 |
| P3 | 3 |
| **合計** | **36** |

### 軸別

| 軸 | P1 | P2 | P3 | 件数 |
|---|---:|---:|---:|---:|
| 認証 / 認可 | 1 | 3 | 0 | 4 |
| 入力検証 | 2 | 4 | 0 | 6 |
| secret 管理 | 1 | 3 | 1 | 5 |
| destructive op | 2 | 3 | 0 | 5 |
| hook | 1 | 2 | 1 | 4 |
| 依存脆弱性 | 1 | 2 | 0 | 3 |
| OWASP マッピング起点 | 1 | 3 | 0 | 4 |
| AI 特有 | 1 | 2 | 0 | 3 |
| sandbox | 1 | 1 | 0 | 2 |
| **合計** | **10** | **23** | **3** | **36** |

## ソース

- [`.claude/settings.json`](/home/tenni/ai-dev-kit-vscode/.claude/settings.json:1)
- [`.claude/hooks/pretooluse-opus-repo-block.sh`](/home/tenni/ai-dev-kit-vscode/.claude/hooks/pretooluse-opus-repo-block.sh:1)
- [`cli/helix-codex`](/home/tenni/ai-dev-kit-vscode/cli/helix-codex:1)
- [`cli/helix-claude`](/home/tenni/ai-dev-kit-vscode/cli/helix-claude:1)
- [`cli/lib/llm_guard.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/llm_guard.py:1)
- [`cli/lib/codex_post_validation.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/codex_post_validation.py:1)
- [`cli/lib/helix_db.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/helix_db.py:679)
- [`cli/lib/observability_helper.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/observability_helper.py:1)
- [`cli/lib/research_tool_guard.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/research_tool_guard.py:1)
- [`cli/lib/agent_policy_guard.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/agent_policy_guard.py:1)
- [`cli/lib/global_store.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/global_store.py:1)
- [`cli/libexec/helix-pre-bash`](/home/tenni/ai-dev-kit-vscode/cli/libexec/helix-pre-bash:1)
- [`cli/libexec/helix-post-tool-use`](/home/tenni/ai-dev-kit-vscode/cli/libexec/helix-post-tool-use:1)
- [`scripts/git-hooks/pre-commit`](/home/tenni/ai-dev-kit-vscode/scripts/git-hooks/pre-commit:1)
- [`scripts/review-upstream-sync.sh`](/home/tenni/ai-dev-kit-vscode/scripts/review-upstream-sync.sh:1)
- [`docs/plans/PLAN-018-llm-guard-retroactive-hardening.md`](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-018-llm-guard-retroactive-hardening.md:1)
- [`docs/plans/PLAN-043-consolidated-carry-resolution.md`](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-043-consolidated-carry-resolution.md:1)
- [`docs/plans/PLAN-063-helix-db-detector-system.md`](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-063-helix-db-detector-system.md:1)
- [`docs/plans/PLAN-067-helix-automation-layer.md`](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-067-helix-automation-layer.md:1)
- [`docs/v2/L1-REQUIREMENTS.md`](/home/tenni/ai-dev-kit-vscode/docs/v2/L1-REQUIREMENTS.md:1)
- [`docs/v2/A-audit/capability-inventory.md`](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/capability-inventory.md:1)
- [`docs/v2/A-audit/hooks-commands-subagents.md`](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/hooks-commands-subagents.md:1)
