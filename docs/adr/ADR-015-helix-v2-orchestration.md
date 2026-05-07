# ADR-015: HELIX v2 orchestration (PM 実装禁止 + PMO 新設 + ロール再配置)

## Status

Accepted (2026-05-08)

## Deciders

PO (ユーザー), PM (Opus), TL

---

## Context

PLAN-028 以前の v1 運用では、PM（Opus）が実装と委譲を兼務するケースが継続し、判断責任と実行責任が重複していた。
特に FE 設計レビュー、軽微修正、PLAN 変更のたびに Opus が直接 Edit/Write を行い、PM と実装ロールの責務が曖昧化していた。

この運用は Opus のトークン消費を増やし、PM が本来担うべき判断・計画管理領域と、実装実行との境界が不明瞭であるという問題を顕在化させた。

PLAN-024 Sprint .3 で CLI / 設定の基盤は整備済みとなり、orchestration を一段上で再設計する条件が揃った。

2026-05-08 に、PM と Opus から運用結論として
「PM 実装の禁止」「サブエージェント指定の禁止」「PMO 新設」「TL/SE/PE 分離」を含む v2 方針が提示された。

この ADR はその方針を正本化し、PLAN-028 の Sprint 実行単位（W-1 〜 W-6）における責務・ロール再配置の技術/運用ルールを固定する。

## Decision

1. **PM = Opus はチャットのみ**: Edit/Write によるコード修正を原則禁止し、サブエージェントを `subagent_type` 指定で呼び出す作業も禁止する。
2. **PMO 新設（Sonnet/Haiku）**:
   - Sonnet は判断伴う作業（read-only）を担当。
   - Haiku は軽作業として `docs/**` 限定編集を許可。
   - Claude 週間 60% 上限到達時は `GPT-5.4-mini` へフォールバック。
3. **TL = GPT-5.5** を設計・レビュー・検証・方針相談・セキュリティ・エージェント実装・DB 判断の中核に固定し、通常実行外の `extra high` は例外のみ。
4. **SE = GPT-5.4** を高度実装、契約整備、リファクタリング、長期実装、技術スタック検索、検証に責務集中。
5. **PE = Codex 5.3-spark** を単機能・速度重視実装へ優先配置し、必要時 `Codex 5.3` をフォールバック。
6. **推挙用途** を `GPT-5.4-mini` とし、PM 60% 超時には PM タスク代行として補完運用できるようする。
7. **PMO 起動経路拡張**: `helix claude` を実行モード対応へ拡張し、`HELIX_CLAUDE_INTERNAL=1 + --permission-mode plan + --disallowedTools` の二段階制限を実装契約で明示。
8. **モデル世代と実行正本順序**: 最新モデルは PM/TL 上位を最上位に、`cli/roles/*.conf` を実行正本、`cli/config/models.yaml` は `synch catalog + doctor` 参照とする。
9. **`cli/roles` と docs エージェントの再整理**:
   - `cli/config/models.yaml` は `cli/roles/*.conf` と同期。
   - `.claude/agents/fe-*.md` と `cli/templates/agents/fe-*.md`（配布元）を廃止し、PMO は `docs/**` のみを操作可能とする構造に合わせる。
10. **PM ↔ TL モード切替**:
    - 変更時は `helix handover --mode pm-to-tl|tl-to-pm` による引継ぎ文書生成を必須化し、責務境界の再確認を運用的に担保する。
11. **W-6 までの暫定運用**:
    - W-1~W-3 は PMO 完全運用前提に到達していないため、PM の PMO 業務代替は read-only ベースレビューのみに限定。
12. **段階移行原則**:
    - 既存 PLAN-024 / PLAN-027 の残タスクは v1 ルール継続。
    - PLAN-028 完了後（W-6）に新規タスクへ v2 適用へ移行。

## Consequences

1. **正本の優先順位は明確化**: `cli/roles/*.conf` が実行時正本、`cli/config/models.yaml` は周知カタログ＋整合監査基準。
2. **権限境界が明文化**: Sonnet は read-only、Haiku は `docs/**` 編集限定。`cli/` などコード領域への直接編集は双方禁止。
3. **PMO 実行性を担保**: `helix claude` の二段階 fail-close 制御を導入し、人間レビューと併せて運用違反の検知を強化。
4. **移行ルールの安全性**: W-1~W-3 は transitional rule を採用し、PMO 不在期間の運用逸脱を限定。
5. **Sprint 連携の安定化**: WBS/DoD と対応させた担当分離により、PLAN-028（W-1 ドキュメント起票を含む）間の整合を確保。
6. **既存 task との互換**: 既存タスクは v1 継続、v2 は PLAN 完了後に切替えることで既存進行の破壊を回避。

## Alternatives considered

### A: v1 を維持（PM が実装兼務）

- 利点: 移行コストが低い。
- 欠点: PM 責務の境界不明瞭が継続し、資源消費制御と監査可能性を損なう。

### B: PMO 新設なし（PM 直接 TL/SE/PE 委譲のみ）

- 利点: ロール数が少なく単純。
- 欠点: docs/軽作業の代替工数が増え、PM の判断コストを再増大。

### C: PMO 新設 + サブエージェント許容

- 利点: 現行資材の流用が容易。
- 欠点: 監査と責務境界が崩れやすく、再帰的呼び出しや責務移譲抜け道を生む。

### D: PMO 新設 + サブエージェント完全禁止 + helix claude 拡張（採用）

- 利点: ロール境界を CLI レベルで拘束し、運用上の再現性を高める。
- 欠点: PMO 経路実装に W-3 分だけセッション資源を要する。

## Related

- ADR-014: cli/roles/*.conf 正本維持
- PLAN-028: HELIX v2 orchestration 移行（PM 実装禁止・PMO 新設）
- メモ: `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/project_helix_orchestration_v2.md`

## References

- `cli/roles/*.conf`（実行正本）
- `cli/config/models.yaml`（同期カタログ）
- `cli/helix-claude`（W-3 で実行モード対応）
- `cli/helix-handover`（W-3 で `--mode` フィールド追加）
- `cli/templates/prompts/pmo-base.md`（PMO no-write ポリシー固定）
