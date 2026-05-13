# V1 → V2 PLAN mapping 表起票（FR-LI02）

## 参照資料
- [legacy-plans-carry.md](docs/v2/A-audit/legacy-plans-carry.md)
- [deprecated-aggregation.md](docs/v2/A-audit/deprecated-aggregation.md)
- [L1-REQUIREMENTS.md](docs/v2/L1-REQUIREMENTS.md)

本表は `PLAN-001`〜`PLAN-068` の carry 状態を V2 Phase へ再分類し、V2 化時の吸収/保留・残件 carry を明示する。

採用ルール（本表）
- `V2 Phase 紐付け` は `legacy-plans-carry.md` の分類を正規化（例: `1 既存整理` → `Phase 1 既存整理`）。
- `carry 件数` は `P0/P1/P2/P3` を明示。
- `V2 で吸収` は carry の有無と保持方針で判断。
- `吸収方法` は必須語彙を固定利用（merge into FR-XX / 新規 PLAN-XXX / 廃止 / 保留）。
- `V2 完了後の保持` は FR-LI01 方針に従い既定 `履歴`。

## §1 mapping 表全件（PLAN-001〜068）

| PLAN ID | タイトル | V1 status | V2 Phase 紐付け | V2 で吸収 | 吸収方法 | carry 件数 (P0/P1/P2/P3) | V2 完了後の保持 |
|---|---|---|---|---|---|---|---|
| PLAN-001 | PoC Skill Canonical Fallback | draft | Phase 5 自動化 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-002 | HELIX フルオート化基盤 | draft | Phase 5 自動化 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-003 | auto-restart 基盤 | draft | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-004 | PM報奨設計 + Readiness | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-005 | 運用自動化スキル群 | completed | Phase 5 自動化 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-006 | 上流フェーズ拡張 | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-007 | Scrum 5 種トリガー設計 | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-008 | Reverse 5系統化 | completed | 派生 AT | yes | 新規 PLAN-XXX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-009 | Run 工程 L9-L11 | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-010 | 検証ツール選定エージェント | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-011 | コード index 登録 | completed | Phase 3 helix.db | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-012 | コード index 未カバレッジ計測 | completed | Phase 3 helix.db | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-013 | Eligibility Taxonomy | completed | Phase 3 helix.db | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-014 | Stop hook idempotency | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-015 | test guard hack 解消 | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-016 | session-summary 廃止 | completed | Phase 5 自動化 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-017 | core CLI bats coverage | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-018 | LLM Guard 事後ハードニング | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-019 | helix-migrate target 拡張 | draft | Phase 1 既存整理 | yes | 保留 | P0:0 / P1:0 / P2:1 / P3:0 | 履歴 |
| PLAN-020 | 最新基準適合化整備 | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-021 | 配布物 vs 作業履歴 分離 | draft | Phase 1 既存整理 | yes | 保留 | P0:0 / P1:0 / P2:1 / P3:0 | 履歴 |
| PLAN-022 | オーケストレーション層実機能化 | draft | Phase 5 自動化 | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:1 | 履歴 |
| PLAN-023 | PLAN-022 残課題解消 | draft | Phase 5 自動化 | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:1 | 履歴 |
| PLAN-024 | オーケストレーション層 穴ふさぎ集約 | draft | Phase 5 自動化 | yes | 保留 | P0:0 / P1:0 / P2:1 / P3:0 | 履歴 |
| PLAN-025 | 不明（trace 未特定） | draft | 永久 carry | no | 保留 | P0:0 / P1:0 / P2:0 / P3:1 | 履歴 |
| PLAN-026 | 不明（2段階実装の痕跡のみ） | draft | 永久 carry | no | 保留 | P0:0 / P1:0 / P2:0 / P3:1 | 履歴 |
| PLAN-027 | 相互監視・最適化システム | draft | Phase 3 helix.db | yes | 保留 | P0:0 / P1:0 / P2:1 / P3:0 | 履歴 |
| PLAN-028 | HELIX v2 orchestration 移行 | completed | Phase 5 自動化 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-029 | 11軸厳格化拡張 | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-030 | v2/29 carry 集約 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-031 | v2/30 carry 解消 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-032 | v2/31 carry 解消 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-033 | v2/32 carry 解消 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-034 | output tee + footer | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-035 | review read-only fix | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-036 | concurrent diff + template 統一 | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-037 | usage limit fallback + lint | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-038 | prompt 最終確認 + finalize 運用 | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-039 | 未発動機能の運用化 | completed | Phase 5 自動化 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-040 | plan split + summary 分離 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-041 | SUMMARY marker 強化 | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-042 | filter 原則 + lock PoC | completed | Phase 4 ガードレール | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-043 | retro carry 9 件集約解消 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-044 | 全フェーズ整合性監査 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-045 | runtime debt 4 件解消 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-046 | runtime quality 5 件解消 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-047 | DS-120 取り込み | completed | 派生 Legacy Import | yes | 新規 PLAN-XXX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-048 | Codex write default 化 | completed | Phase 4 ガードレール | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:3 | 履歴 |
| PLAN-049 | Reverse docs 強化 | completed | 派生 Legacy Import | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:1 | 履歴 |
| PLAN-050 | Codex review findings 解消 | completed | Phase 1 既存整理 | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:5 | 履歴 |
| PLAN-051 | bats-lite hidden failures 解消 | completed | Phase 1 既存整理 | yes | 保留 | P0:0 / P1:0 / P2:32 / P3:0 | 履歴 |
| PLAN-052 | schema migration tests fix | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-053 | helix code tests fix | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-054 | phase template L6.5-.9 fix | completed | Phase 2 V-model | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-055 | plan lint/reset + env failure | completed | Phase 1 既存整理 | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:1 | 履歴 |
| PLAN-056 | codex misc tests fix | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-057 | non-codex misc tests fix | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-058 | dead code / impl fix | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-059 | skill 解像度監査 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-060 | AI knowledge 重複検証 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-061 | dead code 実削除 | completed | Phase 1 既存整理 | yes | merge into FR-XX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-062 | helix code DB findings 3 件 fix | completed | Phase 3 helix.db | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:2 | 履歴 |
| PLAN-063 | helix DB detector 基盤 | completed | Phase 3 helix.db | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:4 | 履歴 |
| PLAN-064 | helix asset CLI | completed | 派生 Legacy Import | yes | 新規 PLAN-XXX | P0:0 / P1:0 / P2:0 / P3:0 | 履歴 |
| PLAN-065 | QA strictness | completed | Phase 2 V-model | yes | 保留 | P0:0 / P1:0 / P2:0 / P3:3 | 履歴 |
| PLAN-066 | security scan 体系化 | draft | Phase 4 ガードレール | yes | 保留 | P0:0 / P1:0 / P2:1 / P3:0 | 履歴 |
| PLAN-067 | 自動化レイヤー強化 | draft | Phase 5 自動化 | yes | 保留 | P0:0 / P1:0 / P2:1 / P3:0 | 履歴 |
| PLAN-068 | 対象ファイルなし | draft | 永久 carry | no | 保留 | P0:0 / P1:0 / P2:0 / P3:1 | 履歴 |

## §2 Phase 別集計

| V2 Phase | 紐付け件数 | 主要 PLAN |
|---|---:|---|
| Phase 1 既存整理 | 21 | PLAN-030 / PLAN-031 / PLAN-043 / PLAN-051 / PLAN-061 |
| Phase 2 V-model | 10 | PLAN-004 / PLAN-029 / PLAN-052 / PLAN-054 / PLAN-065 |
| Phase 3 helix.db | 6 | PLAN-011 / PLAN-012 / PLAN-013 / PLAN-062 / PLAN-063 |
| Phase 4 ガードレール | 14 | PLAN-014 / PLAN-018 / PLAN-034 / PLAN-035 / PLAN-048 |
| Phase 5 自動化 | 10 | PLAN-001 / PLAN-002 / PLAN-039 / PLAN-047 / PLAN-067 |
| 派生 FE | 0 | 該当なし |
| 派生 AT | 1 | PLAN-008 |
| 派生 Legacy Import | 3 | PLAN-047 / PLAN-049 / PLAN-064 |
| 永久 carry | 3 | PLAN-025 / PLAN-026 / PLAN-068 |
| V3 候補 | 0 | 該当なし（PLAN-066/067 の一部要素は V3 先送り） |

### §2.1 Phase別 carry 内訳（補助）

| Phase | P2件数 | P3件数 | 備考 |
|---|---:|---:|---|
| Phase 1 | 34 | 5 | PLAN-051 の 32 件、PLAN-050 の 5 件、PLAN-055/062/063/065 は別フェーズで再配線 |
| Phase 2 | 0 | 3 | PLAN-019/021/027/066/067 は P2 または P3 が残る一部項目に接続 |
| Phase 3 | 1 | 8 | PLAN-062, PLAN-063 が主。PLAN-027 は P2 1 件 |
| Phase 4 | 1 | 3 | PLAN-048/066 の P3、PLAN-022/023 は保留 |
| Phase 5 | 3 | 3 | PLAN-022/023, PLAN-067 は保留。PLAN-067 の file→DB sync がV3候補 |
| 派生 | 0 | 7 | PLAN-049/050/025/026/068 の carry を主に保留 |
| 永久 carry | 0 | 3 | PLAN-025/026/068 は追跡不能・欠番 |

## §3 carry 状態の集計

| carry レベル | 件数 | V2 で処理 | V2 完了後 carry |
|---|---:|---|---|
| P0 | 0 | 該当なし | 該当なし |
| P1 | 0 | 該当なし | 該当なし |
| P2 | 38 | 保留（P2 分割 carry の再配線） | 履歴 |
| P3 | 24 | 保留（P3 分割 carry の引き継ぎ） | 履歴 |

### §3.1 carry 詳細（PLAN 別）

- P2: PLAN-019 / PLAN-021 / PLAN-024 / PLAN-027 / PLAN-051 / PLAN-066 / PLAN-067
- P3: PLAN-022 / PLAN-023 / PLAN-025 / PLAN-026 / PLAN-048 / PLAN-049 / PLAN-050 / PLAN-055 / PLAN-062 / PLAN-063 / PLAN-065 / PLAN-068

## §4 V2 吸収できない PLAN

- PLAN-025: source trace 未発見、PLAN-001〜068 監査で欠番補完不可。`V2` 単体では対象化不能。
- PLAN-026: trace 未特定、実体不明。PLAN-013 以前の 2段階痕跡のみで canonical md 不在。
- PLAN-068: 001〜068 スキャン範囲上の欠番（`対象ファイルなし`）、現行実装追跡不能。
- PLAN-066（security scan 体系化）の一部（スプリント全体 8 本未着手分）は V2内完了せず、V3 候補要素として保留。
- PLAN-067（自動化レイヤー強化）で file→DB 自動同期の 7 スプリント分は現行 V2 定義の自動化フェーズを超え、V3/将来フェーズへ先送り。
- 廃止対象: `docs/features/PLAN-*` と `docs/plans/PLAN-*` の二重管理（DEP-026）および `pm-advisor/tl-advisor/impl-sonnet` の役割設定の off-plan 独立管理（DEP-032）については PLAN 正本上の廃止処理対象。

## §5 PLAN file retention policy

- FR-LI01 に従い、旧 PLAN markdown は削除しない。
- 既存の `docs/plans/` 配下ファイルはそのまま保持する。
- 本 mapping は「運用起票」として新規作成のみ。旧 PLAN 実体の物理 archive は行わない。
- V2 完了後（Phase J）に `archive` 方針の再検討を行う。
- 廃棄対象は `履歴` 扱いとし、削除ではなく参照可否を `Phase J` で判定する。

## §6 リンク整合チェック

- 入力 `legacy-plans-carry.md` との行数差分: 68件（PLAN-001〜068）を 1:1 で反映
- 入力 `deprecated-aggregation.md` の DEP 行: 2件を §4 の理由表記へ反映
- 入力 `L1-REQUIREMENTS.md` の FR-LI01〜03 要件語彙（既存整理〜自動化、保持方針）を §1〜§5 に反映
- 相互リンク: 本ファイル内の参照は 3 ファイルすべてが存在確認済み

## §7 TODO 残存（本表内）

- [ ] PLAN-025, PLAN-026, PLAN-068: canonical source 未確定（永久 carry のまま）
- [ ] PLAN-019, PLAN-021, PLAN-024, PLAN-027, PLAN-048, PLAN-049, PLAN-050, PLAN-055, PLAN-062, PLAN-063, PLAN-065, PLAN-066, PLAN-067: carry 分解の V2 再吸収計画（PLAN 再配線）
- [ ] V3 候補: PLAN-066/067 の未着手/未実装領域の次フェーズ受け渡し（DEP-026/032 の廃止整備含む）

## §8 PLAN-001〜PLAN-068 監査ノート（参照用）

| PLAN ID | audit note | carry | phase/remarks |
|---|---|---|---|
| PLAN-001 | PoC Skill Canonical Fallback｜V1=P0:0/P1:0/P2:0/P3:0｜absorb対象可否=yes | draft | 5 自動化 |
| PLAN-002 | HELIX フルオート化基盤｜V1=0（deferred YAML 上は解決済）｜absorb対象可否=yes | draft | 5 自動化 |
| PLAN-003 | auto-restart 基盤｜V1=0（deferred YAML 上は解決済）｜absorb対象可否=yes | draft | 4 ガードレール |
| PLAN-004 | PM報奨設計 + Readiness｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-005 | 運用自動化スキル群｜V1=0｜absorb対象可否=yes | completed | 5 自動化 |
| PLAN-006 | 上流フェーズ拡張｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-007 | Scrum 5 種トリガー設計｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-008 | Reverse 5系統化｜V1=0｜absorb対象可否=yes | completed | 派生 |
| PLAN-009 | Run 工程 L9-L11｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-010 | 検証ツール選定エージェント｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-011 | コード index 登録｜V1=0｜absorb対象可否=yes | completed | 3 helix.db |
| PLAN-012 | コード index 未カバレッジ計測｜V1=0｜absorb対象可否=yes | completed | 3 helix.db |
| PLAN-013 | Eligibility Taxonomy｜V1=0｜absorb対象可否=yes | completed | 3 helix.db |
| PLAN-014 | Stop hook idempotency｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-015 | test guard hack 解消｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-016 | session-summary 廃止｜V1=0｜absorb対象可否=yes | completed | 5 自動化 |
| PLAN-017 | core CLI bats coverage｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-018 | LLM Guard 事後ハードニング｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-019 | helix-migrate target 拡張｜V1=P2:1｜absorb対象可否=yes | draft | 1 既存整理 |
| PLAN-020 | 最新基準適合化整備｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-021 | 配布物 vs 作業履歴 分離｜V1=P2:1｜absorb対象可否=yes | draft | 1 既存整理 |
| PLAN-022 | オーケストレーション層実機能化｜V1=P3:1｜absorb対象可否=yes | draft | 5 自動化 |
| PLAN-023 | PLAN-022 残課題解消｜V1=P3:1｜absorb対象可否=yes | draft | 5 自動化 |
| PLAN-024 | オーケストレーション層 穴ふさぎ集約｜V1=P2:1｜absorb対象可否=yes | draft | 5 自動化 |
| PLAN-025 | 不明（trace 未特定）｜V1=P3:1｜absorb対象可否=no | draft | 永久 carry |
| PLAN-026 | 不明（2段階実装の痕跡のみ）｜V1=P3:1｜absorb対象可否=no | draft | 永久 carry |
| PLAN-027 | 相互監視・最適化システム｜V1=P2:1｜absorb対象可否=yes | draft | 3 helix.db |
| PLAN-028 | HELIX v2 orchestration 移行｜V1=0｜absorb対象可否=yes | completed | 5 自動化 |
| PLAN-029 | 11軸厳格化拡張｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-030 | v2/29 carry 集約｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-031 | v2/30 carry 解消｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-032 | v2/31 carry 解消｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-033 | v2/32 carry 解消｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-034 | output tee + footer｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-035 | review read-only fix｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-036 | concurrent diff + template 統一｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-037 | usage limit fallback + lint｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-038 | prompt 最終確認 + finalize 運用｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-039 | 未発動機能の運用化｜V1=0｜absorb対象可否=yes | completed | 5 自動化 |
| PLAN-040 | plan split + summary 分離｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-041 | SUMMARY marker 強化｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-042 | filter 原則 + lock PoC｜V1=0｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-043 | retro carry 9 件集約解消｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-044 | 全フェーズ整合性監査｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-045 | runtime debt 4 件解消｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-046 | runtime quality 5 件解消｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-047 | DS-120 取り込み｜V1=0｜absorb対象可否=yes | completed | 派生 |
| PLAN-048 | Codex write default 化｜V1=P3:3｜absorb対象可否=yes | completed | 4 ガードレール |
| PLAN-049 | Reverse docs 強化｜V1=P3:1｜absorb対象可否=yes | completed | 派生 |
| PLAN-050 | Codex review findings 解消｜V1=P3:5｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-051 | bats-lite hidden failures 解消｜V1=P2:32｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-052 | schema migration tests fix｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-053 | helix code tests fix｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-054 | phase template L6.5-.9 fix｜V1=0｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-055 | plan lint/reset + env failure｜V1=P3:1｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-056 | codex misc tests fix｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-057 | non-codex misc tests fix｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-058 | dead code / impl fix｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-059 | skill 解像度監査｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-060 | AI knowledge 重複検証｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-061 | dead code 実削除｜V1=0｜absorb対象可否=yes | completed | 1 既存整理 |
| PLAN-062 | helix code DB findings 3 件 fix｜V1=P3:2｜absorb対象可否=yes | completed | 3 helix.db |
| PLAN-063 | helix DB detector 基盤｜V1=P3:4｜absorb対象可否=yes | completed | 3 helix.db |
| PLAN-064 | helix asset CLI｜V1=0｜absorb対象可否=yes | completed | 派生 |
| PLAN-065 | QA strictness｜V1=P3:3｜absorb対象可否=yes | completed | 2 V-model |
| PLAN-066 | security scan 体系化｜V1=P2:1｜absorb対象可否=yes | draft | 4 ガードレール |
| PLAN-067 | 自動化レイヤー強化｜V1=P2:1｜absorb対象可否=yes | draft | 5 自動化 |
| PLAN-068 | 対象ファイルなし｜V1=P3:1｜absorb対象可否=no | draft | 永久 carry |


## §9 PLAN-001〜PLAN-068 監査チェック票（設計レビュア向け）

| PLAN ID | 受入確認 | carry 根拠 | 追加判定 |
|---|---|---|---|
| PLAN-001 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-002 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-003 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-004 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-005 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-006 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-007 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-008 | 済 | 新規 PLAN-XXX / carry=P0:0 / P1:0 / P2:0 / P3:0 | 新規/派生起票 |
| PLAN-009 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-010 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-011 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-012 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-013 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-014 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-015 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-016 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-017 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-018 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-019 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:1 / P3:0 | 保留 |
| PLAN-020 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-021 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:1 / P3:0 | 保留 |
| PLAN-022 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:1 | 保留 |
| PLAN-023 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:1 | 保留 |
| PLAN-024 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:1 / P3:0 | 保留 |
| PLAN-025 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:1 | 保留 |
| PLAN-026 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:1 | 保留 |
| PLAN-027 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:1 / P3:0 | 保留 |
| PLAN-028 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-029 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-030 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-031 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-032 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-033 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-034 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-035 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-036 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-037 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-038 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-039 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-040 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-041 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-042 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-043 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-044 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-045 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-046 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-047 | 済 | 新規 PLAN-XXX / carry=P0:0 / P1:0 / P2:0 / P3:0 | 新規/派生起票 |
| PLAN-048 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:3 | 保留 |
| PLAN-049 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:1 | 保留 |
| PLAN-050 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:5 | 保留 |
| PLAN-051 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:32 / P3:0 | 保留 |
| PLAN-052 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-053 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-054 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-055 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:1 | 保留 |
| PLAN-056 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-057 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-058 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-059 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-060 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-061 | 済 | merge into FR-XX / carry=P0:0 / P1:0 / P2:0 / P3:0 | merge |
| PLAN-062 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:2 | 保留 |
| PLAN-063 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:4 | 保留 |
| PLAN-064 | 済 | 新規 PLAN-XXX / carry=P0:0 / P1:0 / P2:0 / P3:0 | 新規/派生起票 |
| PLAN-065 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:3 | 保留 |
| PLAN-066 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:1 / P3:0 | 保留 |
| PLAN-067 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:1 / P3:0 | 保留 |
| PLAN-068 | 要対応 | 保留 / carry=P0:0 / P1:0 / P2:0 / P3:1 | 保留 |
