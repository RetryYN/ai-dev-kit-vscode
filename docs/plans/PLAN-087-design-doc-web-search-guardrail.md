---
plan_id: PLAN-087
title: "PLAN-087: 設計 doc 作成時の Web 検索 + OSS 探索ガードレール工程組み込み"
layer: L2
status: draft
size: M
drive: be
created: 2026-05-19
revised: 2026-05-19
owner: PM
phases: L1, L2, L3, L4
gates: G3, G4
related_plans:
  - PLAN-085 (ADR/PLAN scope down 再書き直しで本ガードレールを試行運用)
  - PLAN-086 (同上)
related_docs:
  - .claude/hooks/pretooluse-design-doc-web-search-guard.sh (新規実装)
  - .claude/hooks/pretooluse-agent-guard.sh (既存、参考 pattern)
  - .claude/settings.json (hook 登録)
  - docs/templates/adr-template.md (業界 standard 参照 section 必須化)
  - docs/templates/plan-template.md (同上)
  - cli/helix-gate (G2/G3 audit 拡張)
---

# PLAN-087: 設計 doc 作成時の Web 検索 + OSS 探索ガードレール工程組み込み

## 1. 目的

設計 doc (ADR / PLAN / spec) を新規起票・大幅 scope 変更する **前に** 業界 standard / 既存 OSS の慣行 / best practice を WebSearch / pmo-tech-fork / pmo-tech-docs で必ず確認する工程を機械強制する。memory feedback [[feedback-design-doc-web-search-required]] (2026-05-19 確立) を構造化ガードレールに昇格し、思いつき設計の再発を fail-close で防止する。

memory feedback の確立背景:
- 2026-05-19 PLAN-085 / PLAN-086 / ADR-020 で SaaS 本番運用テンプレートを HELIX (local CLI tool) に過剰適用 (初版 commit 445b27e / 996c05f / 5d730ec / b94395b)
- ユーザー指摘で scope down を試みたが、scope down 版自体も Web 検索なしで思いつき書き
- ユーザー指摘「だから設計ドキュメント作るときに Web 検索をはさめって言ってんだろ」「工程内に組み込んでWeb検索をせずに設計に入らないようにガードレール入れたほうがいいんじゃないの？ギットハブとかも」で構造化必要を認識

## 2. 業界 standard 参照 (本 PLAN が引用する根拠)

| 参照 | source | 引用箇所 |
|---|---|---|
| Claude Code Hooks 公式 doc | https://code.claude.com/docs/en/hooks | PreToolUse / PostToolUse イベント定義、`exit code 2` の意味、`stderr` 返却 |
| Issue #21988 (PreToolUse hook exit code 無視事象) | https://github.com/anthropics/claude-code/issues/21988 | 「非ゼロ終了＝原則 abort」期待との差分と当初の不一致 |
| Issue #24327 (PreToolUse 2 後の model 挙動) | https://github.com/anthropics/claude-code/issues/24327 | ブロック受信後の model 挙動差異と改善方針 |
| 既存 HELIX hook 実装 pattern | .claude/hooks/pretooluse-agent-guard.sh (commit 3ae4af3、subagent guard、PMO+PdM 12 種 fail-close、12-case strict smoke PASS) | Phase 2 実装の base pattern |
| **MADR (Markdown Architecture Decision Record)** | https://adr.github.io/madr/ ; https://github.com/adr/madr/blob/develop/template/adr-template.md | ADR section の構造化要素（Context/Decision/Consequences など） |
| **adr-tools (GitHub)** | https://github.com/npryce/adr-tools | CLI 運用時の ADR 命名・番号化・履歴保持 |
| **Michael Nygard 原典** | https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions | ADR-XXX 由来の `Context/Decision/Consequences/Status` 構成 |
| **alembic process_revision_directives** | https://alembic.sqlalchemy.org/en/latest/cookbook.html | Phase 2 fail-close hook 設計の最上位参照実装 (生成前 block hook) |
| **pressly/goose annotation parse** | https://pressly.github.io/goose/documentation/annotations/ | Phase 1 必須 section 検出 bash script の移植元 (`-- +goose Up` 必須 annotation → file invalid 判定) |
| **amacneil/dbmate 2 section 必須** | https://github.com/amacneil/dbmate | Phase 1 template 必須 section の仕様根拠 (`-- migrate:up` + `-- migrate:down` 両方必須) |
| sqitchers/sqitch Issue #799 (fail-close 未実装の反面教師) | https://github.com/sqitchers/sqitch/issues/799 | warn のみでは検出できない実例として L1 要件補強 |
| 既存 memory feedback | [[feedback_subagent_guard_hook_fail_close]] | hook 実装前に frontmatter / 正本 grep で事実確認 |
| 既存 memory feedback | [[feedback_helix_fill_holes_principle]] | HELIX = 穴を埋めるシステム原則 |
| 既存 memory feedback | [[feedback_codex_parallel_dependency_check]] | Codex 並列投入前の file 衝突依存判定 (本 PLAN Wave 2 で再発・確立) |

### ADR format 業界 standard

比較対象は `MADR / Michael Nygard 原典 / adr-tools` を前提にする。

- **MADR**: `Status`/`Context`/`Decision`/`Consequences` など、意思決定の選択肢・採用理由を明示しやすい構造を標準化。テンプレート変更と GitHub template の追跡性が高い。
- **Michael Nygard 原典**: ADR を「短く 1-2 ページ」「単一決定」「文脈・決定・結果の 4 要素」で記述する原則を提示し、`doc` と一体運用できる設計知識の維持原則を示す。
- **adr-tools**: ADR の番号付与 (`ADR-001` 系) と履歴保持（置換ではなく `supersede`）の運用を CLI 化し、既存の `ADR-XXX` 形式との整合を取りやすい。

HELIX 採用根拠:

- `ADR-XXX` 形式を採用する理由は、既存 PLAN/ADR の識別子体系（`ADR-020` 等）との同型性が高く、`carry list` や `revision` 監査で自動参照しやすいため。
- 本 PLAN の DoD 系・carry 系運用は「決定の背景/代替/理由/影響」を継続して追跡する必要があるため、MADR/原典の構造を踏襲し、`## 業界 standard 参照` への明示リンクを前提とする。

### Claude Code hook API 業界 standard

- **Claude Code 公式 docs** では `PreToolUse` は実行前ブロック対象、`PostToolUse` は実行後通知を示すと定義され、`exit code 2` はブロッキングを示す。
- **Issue #21988** は過去の非整合（非ゼロ終了が拒否を保証しない）を示した経緯として本 PLAN が検証対象化すべき失敗事例。
- **Issue #24327** はブロック後に model が `stop` に対してどう振る舞うかというモデル側挙動の差異を示し、`continue` 期待値を明示化する必要性を示す。

HELIX 採用根拠:

- `exit code 2` を fail-close として明示採用し、`stderr` を human-readable に提示する運用を採る。
- さらに model 応答不一致のリスク対策として、ブロック時メッセージは「human 介入ではない automated policy block」であることを明示し、必要時は PostToolUse で事後再チェックを併用する。


## 3. 前提と制約

- 既存 hook 機構 (Claude Code PreToolUse) を活用、新規外部依存追加なし
- exit 2 = fail-close は Issue #21988 (`exit 2` 無視 bug) workaround を Phase 2 で検証
- bypass: `HELIX_ALLOW_DESIGN_DOC_NO_WEB=1` 環境変数 + 理由 evidence (subagent guard hook と同じ pattern)
- 対象: `docs/adr/ADR-*.md` (新規 + 大幅 scope 変更) と `docs/plans/PLAN-*.md` (新規 + 大幅 scope 変更)
- 対象外: 既存 doc の typo / formatting / 小 edit、bug fix 系の局所修正、CLI flag 追加

## 4. Phase 構成

### Phase 1: template 「業界 standard 参照」section 必須化 (size: S、1 セッション)

#### DoD
- `docs/templates/adr-template.md` (新規 or 既存更新) に「## 業界 standard 参照」section をテンプレートとして組み込み
- `docs/templates/plan-template.md` (同上)
- section 構造:
  ```markdown
  ## 業界 standard 参照 (本 ADR / PLAN が引用する根拠)
  
  | 参照 | source | 引用箇所 |
  |---|---|---|
  | <名前> | <URL> | <doc 内引用箇所> |
  ```
- template 内に「Web 検索 / OSS 探索を skip する場合は明示的に注記」とコメント記入
- 既存 ADR / PLAN の retrofit は本 Phase scope 外 (別 PLAN carry)

#### 委譲
- Codex docs (gpt-5.3-codex-spark) or Opus 直接 Write (S スケール)

### Phase 2: PreToolUse hook 実装 (.claude/hooks/pretooluse-design-doc-web-search-guard.sh、size: M、1-2 セッション)

#### 仕様
- PreToolUse matcher = `Edit` / `Write` / `MultiEdit`
- 対象 path glob:
  - `docs/adr/ADR-*.md` (template / index.md 除外)
  - `docs/plans/PLAN-*.md` (template 除外)
- 検出ロジック:
  1. tool_input から target file path 抽出
  2. path が対象 glob か確認 (else exit 0)
  3. 大幅変更検出: 新規 file (path 不在) または diff 行数 > 50 (大幅変更閾値、調整可)
  4. session 内 WebSearch / WebFetch 実行履歴を確認 (transcript scan or hook log)
  5. session 内 pmo-tech-fork / pmo-tech-docs subagent 起動履歴を確認
  6. いずれも未検出 → exit 2 (fail-close、stderr に「先に WebSearch / pmo-tech-fork / pmo-tech-docs で業界 standard 確認」)
- bypass: `HELIX_ALLOW_DESIGN_DOC_NO_WEB=1` + 理由必須 (環境変数 unset なら exit 2、set のみで bypass 可)

#### Issue #21988 workaround
- exit 2 が無視される bug 報告に対し、smoke test で exit code が実際に block するか検証必須
- 検証手順:
  1. 仮 hook で常に exit 2 を返す
  2. Edit/Write を実行
  3. block されるか確認
  4. block されない場合: PostToolUse hook で revert する補助機構を追加 (二重防御)

#### smoke test
- T1: 対象外 path (CLAUDE.md 等) → pass
- T2: 対象 path + Web 検索なし + 新規 file → block (exit 2)
- T3: 対象 path + Web 検索あり + 新規 file → pass
- T4: 対象 path + Web 検索なし + 既存 file 小 edit (<50 行) → pass (小 edit 除外)
- T5: 対象 path + Web 検索なし + 既存 file 大幅変更 (>50 行) → block
- T6: bypass (`HELIX_ALLOW_DESIGN_DOC_NO_WEB=1`) + Web 検索なし → pass
- T7: pmo-tech-fork subagent 起動済 + 対象 path 新規 → pass

#### 委譲
- Codex se (gpt-5.4) で hook script + smoke test 実装

### Phase 3: helix-gate G2/G3 audit 拡張 (size: S、1 セッション、Phase 2 後)

#### DoD
- `cli/helix-gate` の G2 (設計凍結) / G3 (実装着手) audit に「対象 PLAN の WebSearch / OSS 探索履歴有無」確認を追加
- helix.db v32 schema 追加: `design_doc_web_search_audit` テーブル
  - columns: id / plan_id (or adr_id) / hook_session_id / web_search_executed (bool) / oss_search_executed (bool) / created_at
- G2/G3 で該当 plan の web_search_executed = 0 なら advisory warn (将来 fail-close 化、PLAN-088 carry)
- helix-doctor で「設計 doc 引用 section 空欄」detect (advisory)

#### 委譲
- Codex se (gpt-5.4) で gate audit + schema migration v32

### Phase 4: memory feedback 統合 + 既存 doc retrofit 方針 (size: S、1 セッション)

#### DoD
- memory file [[feedback_design_doc_web_search_required]] と本 PLAN を相互 link
- 既存 ADR / PLAN の retrofit 方針を策定 (PLAN-085 / PLAN-086 / ADR-020 は本 PLAN と同 wave で書き直し、他は段階的)
- CLAUDE.md / SKILL_MAP.md に本ガードレール仕様を明文化
- Issue #21988 monitor: 修正 commit / changelog で fix 確認時、本 hook の workaround 機構 (Phase 2) を撤去判断

## 5. 受入条件 (Acceptance Criteria)

- AC-087-01: docs/templates/adr-template.md + plan-template.md に「業界 standard 参照」section 必須化
- AC-087-02: .claude/hooks/pretooluse-design-doc-web-search-guard.sh が exit 2 で block 動作、7-case smoke (T1-T7) PASS
- AC-087-03: bypass (`HELIX_ALLOW_DESIGN_DOC_NO_WEB=1`) + 理由 evidence の運用が memory feedback と一致
- AC-087-04: helix-gate G2/G3 で WebSearch 履歴 audit が advisory mode で動作 (将来 fail-close 化は PLAN-088 carry)
- AC-087-05: CLAUDE.md / SKILL_MAP.md に本ガードレール仕様明文化
- AC-087-06: PLAN-085 / PLAN-086 / ADR-020 の Web 検索ベース scope down 再書き直しで本ガードレールが実運用試行され、smoke で block ↔ pass が期待通り動作

## 6. リスク

- R-087-01: Issue #21988 (exit code 2 無視 bug) で hook が実際に block しない
  - 緩和: Phase 2 で smoke test 必須、必要なら PostToolUse 二重防御 (revert hook) 追加
- R-087-02: WebSearch / WebFetch / subagent 起動履歴を session 内で検出する logic が信頼性低い (transcript scan ベース)
  - 緩和: hook log file (`.helix/hooks/design-doc-web-search.log`) を別途記録、複数ソース突合
- R-087-03: 大幅変更閾値 50 行が arbitrary、誤判定の可能性
  - 緩和: 閾値は config (`.helix/config/hooks.yaml`) で変更可能化、初期値 50 行で運用後調整
- R-087-04: bypass の誤用 (理由なしで `HELIX_ALLOW_DESIGN_DOC_NO_WEB=1`)
  - 緩和: bypass 利用記録を helix.db `bypass_audit` テーブルに残し、G2/G3 で頻度 audit

## 7. carry list

- [ ] PLAN-089?: helix-gate G2/G3 で WebSearch 履歴 audit を advisory → fail-close 化 (本 PLAN Phase 3 後の段階的 enforcement)
- [ ] CLAUDE.md / SKILL_MAP.md の本ガードレール仕様明文化 (Phase 4 内)
- [ ] **retrofit 候補 P0 6 件** (pmo-sonnet Wave 2-7 報告、2026-05-19):
  - ADR-018 (helix.db 6 分離 + Event Sourcing): Martin Fowler EventSourcing / CQRS / Greg Young 公式 + DDD Bounded Context per DB 引用
  - ADR-020 (cutover-rollback gates): 既存 URL を `## 業界 standard 参照` section に昇格 (本 PLAN と同 wave で実施済)
  - PLAN-084 (helix.db 6 分離): Event Sourcing / CQRS / Projector pattern (Fowler / MSDN CQRS Journey) + UUID v7 RFC 9562 + SQLite ATTACH 公式
  - PLAN-085 (cutover staging): Forward-only migration (alembic / flyway docs) + SQLite WAL mode 公式 (本 PLAN と同 wave で部分実施済)
  - PLAN-086 (rollback drill): Chaos Engineering (Netflix Principles of Chaos / Simian Army) + fault injection (NIST SP 800-190) 引用
  - PLAN-087 (本 PLAN): Claude Code hook API + ADR format standard (MADR / Nygard original) 引用 (本 wave で部分実施済)
- [ ] **retrofit 候補 P1 13 件 + P2 6 件** (pmo-sonnet 報告詳細は memory feedback [[project_2026_05_19_plan087_web_search_guardrail_birth]] 参照、段階的 retrofit)
- [ ] ~~Issue #21988 fix monitor~~ → **2026-05-19 pmo-tech-news 調査で CLOSED 判明** (bug ではなく仕様整備、exit 2 が block / exit 1 が non-blocking)。HELIX hook は exit 2 使用済で現行仕様準拠 → PostToolUse 二重防御は **実装不要**。Claude Code 2.1.139 (2026-05-11) で追加された `continueOnBlock` (PostToolUse で reject reason を Claude に返しつつターン継続) を検討する方が適切 (別 PLAN carry)
- [ ] **Issue #24327** (exit 2 後に Claude が待機する model 挙動変化、2.1.32 Opus 4.6 境界) は **model 側問題でフックで解決不可** → 動作観察 carry
- [ ] **Wave 2 依存衝突 retrofit**: cli/lib/migrations/v32_design_doc_web_search_audit.py が detector_runs と統合された messy 構造を Phase 4 で分離検討 (別 migration に分離 or 設計意図明文化)

## 8. 関連 memory

- [[feedback_design_doc_web_search_required]] (本 PLAN の確立背景)
- [[feedback_subagent_guard_hook_fail_close]] (hook 実装前 frontmatter / 正本 grep + smoke test 必須)
- [[feedback_helix_fill_holes_principle]] (HELIX = 穴を埋めるシステム原則)
- [[feedback_tl_advisor_index_md_side_effect]] (review-only role 副作用 pattern)

## 9. 参照

- Claude Code Hooks 公式: https://code.claude.com/docs/en/hooks
- MADR公式: https://adr.github.io/madr/
- MADR template: https://github.com/adr/madr/blob/develop/template/adr-template.md
- ADRツール: https://github.com/npryce/adr-tools
- Michael Nygard original: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- Issue #21988 (PreToolUse exit code 2 無視 bug): https://github.com/anthropics/claude-code/issues/21988
- Issue #24327 (PreToolUse 2 後 model 挙動): https://github.com/anthropics/claude-code/issues/24327
- .claude/hooks/pretooluse-agent-guard.sh (既存 hook、参考 pattern)
- docs/plans/PLAN-085-cutover-staging-rehearsal.md (本 wave で同時 scope down)
- docs/plans/PLAN-086-rollback-fault-injection-drill.md (同上)
- docs/adr/ADR-020-cutover-rollback-gates.md (同上)

## Revision History

- 2026-05-19 業界 standard 引用 micro-retrofit (W5b-C、ADR format + Claude Code hook API)
