# ADR-031: リカバリープラン kind 正規化採用判断

## Status

Proposed (2026-05-20、本 session 起票、PO 承認待ち)

## Deciders

- PM (Opus, Claude Code)
- PO (yoshiyuki0907yn@gmail.com)

## Supersedes

なし (新規 kind 追加)

## Related

- ADR-025 (V5 framework 本体、recovery は V5 要素 #17)
- ADR-027 (drift 検出 + Curator、本 ADR は check_recovery_plan_freshness 追加)
- ADR-032 (自動走行 framework、Layer 4 SessionStart 連動)
- PLAN-091 (kind 11 種で recovery 定義、frontmatter 語彙の正本)
- PLAN-098 (本 ADR の対応 PLAN、template + check 実装)
- PLAN-093 (helix doctor 拡張の base)
- PLAN-099 (Layer 4 SessionStart cleared/compacted で recovery PLAN を context 再構築 source として利用)

## 業界 standard 参照

| 参照 | source | 引用箇所 |
|---|---|---|
| Google SRE Blameless Postmortem | https://sre.google/sre-book/postmortem-culture/ | Decision 5 セクション構造 (timeline / root cause / action items) |
| Atlassian Incident Postmortem | https://www.atlassian.com/incident-management/postmortem/templates | Decision metadata 必須化 |
| dastergon postmortem-templates (GitHub) | https://github.com/dastergon/postmortem-templates | Decision template 構造 |
| incident.io SRE best practices | https://incident.io/blog/sre-incident-postmortem-best-practices | Decision blameless 原則 + 24-72h window |
| Indium 7 State Persistence Strategies for AI Agents | https://www.indium.tech/blog/7-state-persistence-strategies-ai-agents-2026/ | Decision context 再構築の必要性 |
| Augment Code Session-End Spec Update | https://www.augmentcode.com/guides/session-end-spec-update-ai-agents | Decision session 終了前 5 分 update 原則 |
| XTrace AI Agent Context Handoff | https://xtrace.ai/blog/ai-agent-context-handoff | Context: context loss が pipeline 破綻の主因 |
| GitScrum Definition of Done | https://gitscrum.com/en/solutions/pains/unclear-definition-of-done | Decision 4 項目 fail-close (DoD enforcement) |
| 内部 reference: feedback_recovery_plan_kind_missing | MEMORY.md | Context: 本 session 確立の事故記録 |
| 内部 reference: feedback_dont_stop_with_carry_remaining | MEMORY.md | Context: 14h idle 事故 |

## Context

本 session (2026-05-20) で発覚した **session 断絶問題群**:

1. **中間結論消失**: V5 framework V1→V5 確立過程の議論順序が CLAUDE.md にしか永続化されず、独立 recovery PLAN として保存されなかった (ユーザー指摘「順序メモしておけよ。リカバリープランみたいなのでプランをつくるといいという君がミスったまさに設計上の穴」で発覚)
2. **carry 残件不明確**: handover に Tier A (V-model retrofit) + Tier B (ADR-021〜024 後追い) + Tier D (recovery 個別起票) を carry として書いたが、ユーザー指摘「V5 framework 9 PLAN が本命、それ以外破棄」で「Tier A/B/D は前提誤りに基づく不要作業」と認識訂正
3. **14h idle 事故** (`feedback_dont_stop_with_carry_remaining`): 2026-05-19 09:57-23:49 で並行タスクなしと誤判断して turn 終了、harness 通知待ちのまま 14h アイドル化
4. **認識訂正履歴の揮発**: 「吸収」→「前提誤り → 置換」の認識訂正が chat のみで永続化なし、次 session で再発するリスク

既存 HELIX 資産 (handover / memory feedback / helix doctor) は session 断絶からの再開を扱わない:
- handover: state snapshot 中心、議論順序 / 認識訂正履歴は扱わない
- memory feedback: 個別 lesson learned、断絶リカバリーの構造化なし
- helix doctor: PLAN drift 検出はあるが recovery PLAN freshness check なし

session 断絶からの再開を **1 つの PLAN doc に集約** する仕組みが必要。

## Decision

**recovery kind を正規化、PLAN-091 §5.1 で kind 11 種の 11 番目として定義し、本 PLAN-098 で template / check / fail-close enforcement を具体化する**:

### D1: recovery kind 追加

- PLAN-091 §5.1 kind 11 種に `recovery` を追加 (本 ADR は PLAN-091 の定義を前提)
- drive: `troubleshoot` を default (障害復旧 driven)
- layer: `cross` (全層に影響、session 断絶は工程横断的)

### D2: recovery template 7 必須セクション

`cli/templates/plan/recovery/template.md` に以下 7 セクション必須化:
1. 事故記録 (event_type / severity / impact)
2. 議論順序 timeline (turn 番号と内容)
3. 認識訂正履歴 (V1→Vn の遷移)
4. 中間結論 list (3 列: Conclusion / 状態 / 根拠)
5. context 再構築チェックリスト (5 項目)
6. 再開ポイント (next session 着手 task + 前提条件)
7. 再発防止策 (proximate + root cause + rule / hook 追加)

### D3: session 終了前チェックリスト 4 項目 fail-close

session 終了 (Stop hook 発火時) に以下 4 項目を機械 check:
1. 中間結論が docs に永続化されているか
2. carry 残件が PLAN or handover に明記されているか
3. 認識訂正があった場合 memory feedback が更新されているか
4. recovery kind PLAN が必要な場合 draft 起票済みか

P1 (warn) → P2 (advisory) → P3 (fail-close 強制) の段階導入。

### D4: helix doctor check_recovery_plan_freshness

- `status: active` AND `kind: recovery` の PLAN を抽出
- 最終更新日 (frontmatter `revised` or file mtime) から経過日数判定
- default 7 日超過 warn / 14 日超過 fail (exit code 2)

### D5: PLAN-099 Layer 4 連動

- SessionStart(cleared|compacted) hook で **直近の recovery PLAN を context 再構築 source として注入**
- UserPromptSubmit hook で「次 session 開始時に最初に Read すべき recovery PLAN」を systemMessage 表示

## Consequences

### Positive

- **session 断絶リカバリーの標準化**: 7 セクション template で再開手順が機械的に揃う
- **14h idle 事故防止**: 4 項目 fail-close で「carry 残しで turn 終了」を機械的に防ぐ
- **context 再構築自動化**: PLAN-099 Layer 4 連動で次 session 開始時に recovery PLAN が自動注入
- **認識訂正履歴の永続化**: V1→Vn 遷移を 1 doc に集約、次 session で再発防止
- **helix doctor 統合**: stale recovery PLAN を機械検出、放置 1 月超 fail-close で清算強制

### Negative

- **recovery template の書式コスト**: 7 セクション全件記述で 30 分-1h、頻発 session では負担
- **freshness check の false positive リスク**: 長期 carry (1 月超 PLAN) を誤って fail にする可能性 → frontmatter `freshness_exempt: true` で個別除外を提供
- **fail-close で turn 終了制限**: P3 段階で「実装途中で session 終了せざるを得ない」場合の bypass が必要 → `HELIX_RECOVERY_BYPASS=<理由>` env で短期 bypass 許可
- **既存 handover との重複懸念**: handover との責務分離が必要 → handover = state snapshot / recovery = 議論と認識訂正の構造化、で分離

## Alternatives

### Alt 1: handover 拡張のみ (棄却)

handover に「議論順序」「認識訂正履歴」「中間結論」フィールドを追加。

**棄却理由**: handover は session continuity (現在状態) 中心、議論や認識訂正は時系列 doc であり handover の構造 (state snapshot) と相性悪い。handover が肥大化して読みづらくなる。

### Alt 2: memory feedback のみ (棄却)

session 断絶リカバリーは memory feedback `feedback_session_recovery_*` で個別記録。

**棄却理由**: memory feedback は個別 lesson learned で、PLAN level の構造化 / freshness check / fail-close enforcement との連動がない。複数 session 跨いだ recovery を集約しにくい。

### Alt 3: 本 Decision 採用 (recovery kind 正規化)

recovery kind を PLAN-091 §5.1 で正規定義、本 PLAN-098 で template + check + fail-close 化。

**採用理由**: PLAN level で構造化されることで helix doctor / helix plan / hook の全 framework と統合可能。template 標準化で recovery PLAN 起票コストが低減。fail-close で機械強制可能。

### Alt 4: 既存 troubleshoot kind に統合 (棄却)

troubleshoot kind 内に「recovery sub-type」として運用。

**棄却理由**: troubleshoot は実装中の障害対応 (bug fix / incident response) 中心、session 断絶リカバリー (議論 / 認識訂正の永続化) とは性質が異なる。kind を分離した方が template が単純化できる。

## Implementation Plan

PLAN-098 の Phase に従う:

- **P1 (1 session)**: cli/templates/plan/recovery/template.md + cli/lib/recovery_plan_check.py + helix doctor check_recovery_plan_freshness 配置 (warn-only)
- **P2 (2-3 session)**: Stop hook で 4 項目 advisory check 表示 (強制なし)
- **P3 (3-5 session)**: Stop hook + PreCompact hook (PLAN-099 Layer 3) で 4 項目 fail-close 化

PLAN-099 Layer 4 (SessionStart 履歴注入) の本実装後 (別 session) に、recovery PLAN の自動 context 再構築機構が完成する。

## Notes

- 本 ADR は **Status: Proposed**、PO 承認後に Accepted 遷移
- 本 session で発覚した「Tier A/B/D 前提誤り」自体も recovery PLAN 候補 (将来別 session で起票)
- 本 ADR の起票過程自体が PLAN-098 §5 recovery template の test case (本 session を recovery 視点で記述する練習)
