# FR-INV02: PLAN-001〜068 carry 棚卸し

## 概要

- 対象: `docs/plans/PLAN-001-*.md` 〜 `PLAN-068-*.md`、補助根拠として `.helix/audit/deferred-findings.yaml`、`.helix/plans/PLAN-020/021/024/027.yaml`、`docs/roadmap/2026-05-04-completion-roadmap.md`
- 走査日: 2026-05-14
- 注意:
  - `finalized` は本棚卸しでは `completed` に正規化した。
  - `.helix/audit/deferred-findings.yaml` 上の **未解決 deferred-finding は 0 件**。そのため下表の deferred/carry は、主に PLAN 本文の `carry` / `deferred` / `out-of-scope` / `候補` 記述から再集計している。
  - `PLAN-020`〜`027`、`068` は `docs/plans/` に canonical な markdown が欠けるものがある。trace-only のものは不確実性を明示した。
  - `PLAN-002B` は連番外の派生ファイルだが、`PLAN-002` の棚卸し実体として残っているため別行で記録した。

## PLAN 別棚卸し

| PLAN ID | タイトル | status | deferred-finding | 未実装 carry | V2 phase 紐付け候補 |
|---|---|---|---|---|---|
| PLAN-001 | PoC Skill Canonical Fallback | draft | P0:0/P1:0/P2:0/P3:0 | PoC 段階。後続実装 PLAN は本文から特定できず | 5 自動化 |
| PLAN-002 | HELIX フルオート化基盤 | draft | 0（deferred YAML 上は解決済） | triaged 残件は PLAN-003/004 へ分離前提。本文チェックリスト未完 | 5 自動化 |
| PLAN-002B | HELIX 棚卸し基盤 | draft | 0（deferred YAML 上は解決済） | 棚卸し基盤自体は draft のまま。`audit_decisions` 系の完遂証跡は別管理 | 1 既存整理 |
| PLAN-003 | auto-restart 基盤 | draft | 0（deferred YAML 上は解決済） | PLAN-002 分離残件を継承。Sprint .2 以降が未実装前提 | 4 ガードレール |
| PLAN-004 | PM報奨設計 + Readiness | completed | 0 | V1 内で完結 | 2 V-model |
| PLAN-005 | 運用自動化スキル群 | completed | 0 | `未完了なし` 明記 | 5 自動化 |
| PLAN-006 | 上流フェーズ拡張 | completed | 0 | research defer ルールは制度化済、未実装 carry なし | 2 V-model |
| PLAN-007 | Scrum 5 種トリガー設計 | completed | 0 | carry 明示なし | 2 V-model |
| PLAN-008 | Reverse 5系統化 | completed | 0 | Reverse gap carry ルールを制度化。個別残件なし | 派生 |
| PLAN-009 | Run 工程 L9-L11 | completed | 0 | `watch-continue` / `blocked` は運用分岐であり個別 carry なし | 2 V-model |
| PLAN-010 | 検証ツール選定エージェント | completed | 0 | severity/carry rule 制度化済 | 2 V-model |
| PLAN-011 | コード index 登録 | completed | 0 | `--uncovered` は PLAN-012 へ deferred 済み | 3 helix.db |
| PLAN-012 | コード index 未カバレッジ計測 | completed | 0 | suffixless / core5 外は将来 PLAN へ deferred | 3 helix.db |
| PLAN-013 | Eligibility Taxonomy | completed | 0 | heuristic/global は後続 PLAN へ deferred だが当該 PLAN は収束扱い | 3 helix.db |
| PLAN-014 | Stop hook idempotency | completed | 0 | V1 内で完結 | 4 ガードレール |
| PLAN-015 | test guard hack 解消 | completed | 0 | V1 内で完結 | 4 ガードレール |
| PLAN-016 | session-summary 廃止 | completed | 0 | carry なし | 5 自動化 |
| PLAN-017 | core CLI bats coverage | completed | 0 | retroactive。retro 未作成だが実装 carry なし | 2 V-model |
| PLAN-018 | LLM Guard 事後ハードニング | completed | 0 | retroactive plan。運用注意のみで未実装 carry なし | 4 ガードレール |
| PLAN-019 | helix-migrate target 拡張 | draft | P2:1 | 実装は roadmap 上で PLAN-020 Sprint .4 吸収済だが canonical md は draft のまま | 1 既存整理 |
| PLAN-020 | 最新基準適合化整備 | completed | 0 | `docs/plans` 不在。roadmap と `.helix/plans/PLAN-020.yaml` では完了 | 4 ガードレール |
| PLAN-021 | 配布物 vs 作業履歴 分離 | draft | P2:1 | canonical md 不在。`.helix/plans/PLAN-021.yaml` は draft / review pending | 1 既存整理 |
| PLAN-022 | オーケストレーション層実機能化 | draft | P3:1 | ADR 参照のみ。canonical source 不在 | 5 自動化 |
| PLAN-023 | PLAN-022 残課題解消 | draft | P3:1 | ADR / tmp 参照のみ。canonical source 不在 | 5 自動化 |
| PLAN-024 | オーケストレーション層 穴ふさぎ集約 | draft | P2:1 | `.helix/plans/PLAN-024.yaml` 上で .2 以降未完。PLAN-028/030 に一部継承 | 5 自動化 |
| PLAN-025 | 不明（trace 未特定） | draft | P3:1 | source 未発見。追跡不能 | 永久 carry |
| PLAN-026 | 不明（2段階実装の痕跡のみ） | draft | P3:1 | tmp の lifecycle 痕跡のみ。canonical source 不在 | 永久 carry |
| PLAN-027 | 相互監視・最適化システム | draft | P2:1 | `.helix/plans/PLAN-027.yaml` では残 Sprint 継続。PLAN-028 でも参照 | 3 helix.db |
| PLAN-028 | HELIX v2 orchestration 移行 | completed | 0 | 既存 PLAN-024/027 残 Sprint を参照するが本 PLAN 自体は完了 | 5 自動化 |
| PLAN-029 | 11軸厳格化拡張 | completed | 0 | retro/carry は PLAN-030 へ集約済み | 2 V-model |
| PLAN-030 | v2/29 carry 集約 | completed | 0 | 5 件 carry は PLAN-031 等で再配線済み | 1 既存整理 |
| PLAN-031 | v2/30 carry 解消 | completed | 0 | 残件は PLAN-032 へ再集約済み | 1 既存整理 |
| PLAN-032 | v2/31 carry 解消 | completed | 0 | 残件 3 件は PLAN-033 へ再集約済み | 1 既存整理 |
| PLAN-033 | v2/32 carry 解消 | completed | 0 | retro 3 件は PLAN-034 へ移送済み | 1 既存整理 |
| PLAN-034 | output tee + footer | completed | 0 | review sandbox 制約は PLAN-035 へ移送済み | 4 ガードレール |
| PLAN-035 | review read-only fix | completed | 0 | carry 3 件は PLAN-036 へ移送済み | 4 ガードレール |
| PLAN-036 | concurrent diff + template 統一 | completed | 0 | carry 4 件は PLAN-037 へ移送済み | 4 ガードレール |
| PLAN-037 | usage limit fallback + lint | completed | 0 | carry 4 件は PLAN-038 へ集約済み | 4 ガードレール |
| PLAN-038 | prompt 最終確認 + finalize 運用 | completed | 0 | lock 導入は別 PLAN carry 済み | 4 ガードレール |
| PLAN-039 | 未発動機能の運用化 | completed | 0 | 残件は次 Sprint 化済み | 5 自動化 |
| PLAN-040 | plan split + summary 分離 | completed | 0 | carry 2 件は PLAN-041 候補へ固定 | 1 既存整理 |
| PLAN-041 | SUMMARY marker 強化 | completed | 0 | lock 等は PLAN-042 へ carry 済み | 4 ガードレール |
| PLAN-042 | filter 原則 + lock PoC | completed | 0 | critical path 接続は PLAN-043 へ carry 済み | 4 ガードレール |
| PLAN-043 | retro carry 9 件集約解消 | completed | 0 | `helix.db` / `phase.yaml` lock は PLAN-044 carry | 1 既存整理 |
| PLAN-044 | 全フェーズ整合性監査 | completed | 0 | D-009 は PLAN-045 carry | 1 既存整理 |
| PLAN-045 | runtime debt 4 件解消 | completed | 0 | `allowed_files` 自動推定は PLAN-046+ 候補 | 1 既存整理 |
| PLAN-046 | runtime quality 5 件解消 | completed | 0 | carry は本文上閉じ済み | 1 既存整理 |
| PLAN-047 | DS-120 取り込み | completed | 0 | TODO/FIXME 残存なし明記 | 派生 |
| PLAN-048 | Codex write default 化 | completed | P3:3 | DS-120 統合版取得 / auto-thinking 統計 / mapping table 自動 link 検証が後続 carry | 4 ガードレール |
| PLAN-049 | Reverse docs 強化 | completed | P3:1 | DS-120 Reverse 反映は PLAN-050+ carry | 派生 |
| PLAN-050 | Codex review findings 解消 | completed | P3:5 | Reverse 反映 / worked-example / checklist / link 検証 / auto-thinking 統計が carry | 1 既存整理 |
| PLAN-051 | bats-lite hidden failures 解消 | completed | P2:32 | Category F 残り 32 件を PLAN-052+ へ carry | 1 既存整理 |
| PLAN-052 | schema migration tests fix | completed | 0 | PLAN-051 carry の担当カテゴリを解消 | 2 V-model |
| PLAN-053 | helix code tests fix | completed | 0 | 担当カテゴリ解消 | 1 既存整理 |
| PLAN-054 | phase template L6.5-.9 fix | completed | 0 | 担当カテゴリ解消 | 2 V-model |
| PLAN-055 | plan lint/reset + env failure | completed | P3:1 | `VAR=value` 本格 fix を別 PLAN へ route | 1 既存整理 |
| PLAN-056 | codex misc tests fix | completed | 0 | 担当カテゴリ解消 | 1 既存整理 |
| PLAN-057 | non-codex misc tests fix | completed | 0 | 担当カテゴリ解消 | 1 既存整理 |
| PLAN-058 | dead code / impl fix | completed | 0 | PLAN-051〜057 累積 carry を完遂と明記 | 1 既存整理 |
| PLAN-059 | skill 解像度監査 | completed | 0 | W-final 完了。carry 明示なし | 1 既存整理 |
| PLAN-060 | AI knowledge 重複検証 | completed | 0 | 廃止判定まで。追加 carry 明示なし | 1 既存整理 |
| PLAN-061 | dead code 実削除 | completed | 0 | 実削除完了。未解決 carry 明示なし | 1 既存整理 |
| PLAN-062 | helix code DB findings 3 件 fix | completed | P3:2 | vulture 残 100 件精査 / skill 解像度見直しが別 PLAN carry | 3 helix.db |
| PLAN-063 | helix DB detector 基盤 | completed | P3:4 | graph UI / AI 自動修正 / 外部連携 / tests-only callers 削除が carry | 3 helix.db |
| PLAN-064 | helix asset CLI | completed | 0 | carry 明示なし | 派生 |
| PLAN-065 | QA strictness | completed | P3:3 | retroactive test 追加 / perf baseline / 自動テスト生成が別 PLAN carry | 2 V-model |
| PLAN-066 | security scan 体系化 | draft | P2:1 | 8 Sprint 全体が未着手。security 成果物未生成 | 4 ガードレール |
| PLAN-067 | 自動化レイヤー強化 | draft | P2:1 | 7 Sprint まるごと未実装。file→DB 自動 sync は future carry | 5 自動化 |
| PLAN-068 | 対象ファイルなし | draft | P3:1 | 001-068 スキャン範囲上の欠番。source 未発見 | 永久 carry |

## 複雑 carry の詳細

### 1. PLAN-019〜027 は canonical source が不連続

- `PLAN-019` は `docs/plans` に draft が残る一方、`docs/roadmap/2026-05-04-completion-roadmap.md` では「実装は PLAN-020 Sprint .4 に吸収、P2 finding 3 件全消化」とされる。
- `PLAN-020` は `docs/plans` に本文が無いが、roadmap と `.helix/plans/PLAN-020.yaml` では completed 相当の実績が残る。
- `PLAN-021` / `024` / `027` は `.helix/plans/*.yaml` が残っており、いずれも draft / pending review。
- `PLAN-022` / `023` / `025` / `026` は ADR / tmp / log に痕跡はあるが canonical plan source を確認できない。
- V2 着手前に、`docs/plans/` と `.helix/plans/` の正本整理を一度入れないと、過去 carry の追跡可能性が継続的に落ちる。

### 2. PLAN-030〜046 は carry を別 PLAN へ再配線して収束

- この帯域は「carry を新 PLAN へ集約し直して解く」運用が一貫している。
- したがって現時点の未解決 carry は各 PLAN 本体ではなく、**最終到達先の PLAN にのみ残る**と読むのが妥当。
- V2 ではこの系列を「Phase 1 既存整理」でまとめて閉じるのが最も管理しやすい。

### 3. 2026-05-11 以降の carry は P3 中心で次機能の種別待ち

- `PLAN-048` は guardrail 強化後の派生 backlog を 3 件残す。
- `PLAN-049` / `050` は Reverse / DS-120 / tooling ドキュメントの派生 carry。
- `PLAN-051` は 32 件と件数が大きいが、その後 `PLAN-052`〜`058` で大半が分割消化されたため、現時点の実害は低い。
- `PLAN-062` / `063` / `065` は P3 carry が残るが、いずれも新機能・UI・perf・外部連携寄りで、V2 の中核 blocker ではない。

## 集計サマリ

- 全 PLAN 数:
  - `docs/plans` 実ファイル: 60
  - 一意 PLAN ID: 59
  - 棚卸し行数: 69
  - 注: `PLAN-002B` を別行採用、`PLAN-020`〜`027` / `068` は trace-only 行を補完
- status 集計:
  - completed: 54
  - draft: 15
  - abandoned: 0
  - in-progress: 0
- 未実装 carry 件数（再集計、推定含む）:
  - P0: 0
  - P1: 0
  - P2: 38
  - P3: 24
- V2 phase 別 carry 件数:
  - Phase 1 既存整理: 5
  - Phase 2 V-model: 1
  - Phase 3 helix.db: 3
  - Phase 4 ガードレール: 2
  - Phase 5 自動化: 5
  - 派生: 1
  - 永久 carry: 3
- 分類:
  - V1 で完結: 44
  - V2 で吸収: 20
  - V3 以降 / 永久 carry: 5

## 推奨

1. 先に `PLAN-019`〜`027` の正本整理を行う。これをしないと carry 集計そのものの再現性が低い。
2. V2 Phase 1 は `PLAN-030`〜`046` の carry 系列よりも、むしろ `019`〜`027` と `051` 残骸の metadata 整合を優先したほうが監査効果が高い。
3. V2 Phase 4 は `PLAN-066`、Phase 5 は `PLAN-067` をそのまま母艦にできる。新規起票より既存 draft 再利用のほうがよい。
4. `PLAN-025` / `026` / `068` は source 不在のため、V2 で回収しないなら「永久 carry / closed as untraceable」を明示決定したほうがよい。
