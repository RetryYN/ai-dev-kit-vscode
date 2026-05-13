# FR-INV05: V1 蓄積知見の正本化

最終更新: 2026-05-14  
目的: HELIX V1 で蓄積された運用判断・設計判断・trial and error を、起源参照付きで V2 After 設計の根拠として固定する。  
方針: 既存の PLAN / ADR / memory / 現行ルールを優先し、V1 で有効だったが V2 で廃止された運用は「V2 で変える」として明示する。

## 読み方

- **知見**: 1 行サマリ
- **起源**: 正本または一次証跡
- **理由 (Why)**: その判断に至った失敗経験または構造的根拠
- **適用範囲 (Where)**: どの phase / role / task に効くか
- **V2 でも維持**: `yes` / `no` / `修正して維持`
- **V2 で変える場合の修正案**: `yes` 以外のときに記載

---

## 1. Role 分担原則

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| PM = Opus はチャット専業。実装禁止、subagent 指定禁止。 | `docs/plans/PLAN-028-helix-v2-orchestration.md`, `docs/adr/ADR-015-helix-v2-orchestration.md`, `memory/feedback_pm_no_implementation_no_subagent.md` | V1 では PM が実装と委譲を兼務し、判断責任と実行責任が重複した。コスト超過と責務曖昧化が再発したため。 | 全 phase、特に L1-L8 の PM 作業 | yes | - |
| PMO は Sonnet/Haiku に分離し、Sonnet は read-only、Haiku は `docs/**` 限定。 | `PLAN-028`, `ADR-015`, `memory/project_helix_orchestration_v2.md` | PM の補助作業を切り出しつつ、コード編集の抜け道を作らないため。 | PM 補助、docs 点検、軽調査 | yes | - |
| TL / SE / PG(docs 上は PE) の責務を分け、`tl` と `qa` はレビュー寄り、実装は `docs` / `se` / `pg` で行う。 | `cli/ROLE_MAP.md`, `memory/feedback_codex_role_selection.md` | `tl` や `qa` に実装を投げると、変更ゼロで判定だけ返る事故が実運用で発生した。 | Codex 委譲全般 | yes | - |
| 実行時の role / model 正本は `cli/roles/*.conf`。`models.yaml` と Markdown は周知・監査用。 | `docs/adr/ADR-014-roles-config-format.md`, `PLAN-028`, `cli/ROLE_MAP.md` | `research.conf` / `models.yaml` / `CLAUDE.md` の 3 重不一致が起き、動作と文書が乖離したため。 | role 設定、doctor、委譲設計 | yes | - |
| CLI role 名はチーム命名と一致しない。`PE` ではなく `pg` を使う。 | `cli/ROLE_MAP.md`, `memory/feedback_codex_role_name_cli_vs_memory.md` | `--role pe` が invalid で即 fail し、再投入ロスが発生した。 | `helix codex --role ...` | yes | - |
| V1 の「PLAN 修正は終盤 Opus 直接 Edit が早い」は V2 では廃止。 | `memory/feedback_docs_role_vs_opus_edit.md`, `ADR-015`, `PLAN-043` | V1 では速度優先の例外運用があったが、V2 は PM 直接 Edit を mechanical block する前提へ変わった。 | PM の docs 更新、PLAN 修正 | no | PLAN / docs 修正も `docs` / `tl` / PMO へ委譲し、PM は判断と指示に限定する。 |

## 2. 委譲原則

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| raw `codex exec` / raw `claude` を通常導線にしない。`helix codex` / `helix claude` / `helix review` を使う。 | `helix/CODEX_TL_MODE.md`, `docs/commands/ai-harness.md`, `AGENTS.md`, `PLAN-018` | hard guard と plan/approval 文脈が入らず、工程表・権限制御が壊れるため。 | 全委譲タスク | yes | - |
| write を伴う Codex 委譲は `--approved --consent approved` を明示し、`--consent auto` は read-only のみ。 | `memory/feedback_codex_consent_rules.md`, `PLAN-042`, `PLAN-043` | 実装タスクが `auto` 誤分類で plan-only guard に落ち、read-only sandbox で blocked が再発したため。 | Codex 実装委譲 | yes | - |
| 依存関係がないタスクは並列が default。根拠なき直列化は禁止。 | `memory/feedback_parallel_dispatch_default.md`, `CLAUDE.md` | 「念のため直列」は作業時間だけを伸ばし、オーケストレーション規範に反するため。 | Sprint 分割、複数委譲 | yes | - |
| destructive 判断の前に、agent / subagent の調査結果を一次ソースで再検証する。 | `memory/feedback_agent_judgment_verification.md` | 「未使用」判定を鵜呑みにすると、実際は helix-test 等で使われている資産を誤削除する。 | 削除、rename、棚卸し、cleanup | yes | - |
| usage limit 到達時は role を切り替えて即 fallback する。 | `memory/feedback_codex_usage_limit_fallback.md`, `cli/config/models.yaml` | primary model ごとに利用枠が分かれており、同一 task を別 role で継続できるため。 | Codex 実装・レビュー | yes | - |

## 3. Gate 運用

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| G1-G11 は fail-close を基本とし、readiness / carry rule を明示する。 | `helix/HELIX_CORE.md`, `skills/SKILL_MAP.md`, `PLAN-029` | 「通るべき手順を満たすだけ」で再現性が上がらない問題があり、carry の揺れも大きかったため。 | 全 phase / gate | yes | - |
| Sprint 完了条件は、設計整合・TL レビュー・テスト・ビルド証跡の 4 点セットで持つ。 | `PLAN-029 §2.2`, `PLAN-043`, `HELIX_CORE.md` | Sprint を終えたつもりでも、レビューや証跡欠落で後続が壊れる事例が続いたため。 | L4, G4, 統合検証 | yes | - |
| FE/fullstack は mock 駆動 debt を gate へ接続し、`MOCK-*` 未解消を fail-close にする。 | `skills/tools/ai-coding/references/gate-policy.md`, `PLAN-029`, `skills/agent-skills/mock-driven-development/SKILL.md` | mock を throw-away にせず本実装へ漏らすと、契約・コード・UX がドリフトしやすいため。 | FE / fullstack の G2, G4, G6 | 修正して維持 | V2 では `origin_mode` や drive 列を監査可能にし、mock 起源 debt がどこから来たかを DB / gate 証跡に残す。 |

## 4. コスト管理

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| PMO fallback の 60% 閾値は `weekly_used_pct` 基準で判断し、5h block 指標と混同しない。 | `memory/feedback_pmo_fallback_threshold_weekly.md`, `memory/project_helix_orchestration_v2.md` | 短期 burst を weekly quota と誤認すると、必要な Sonnet/Haiku を早期に切って品質を落とすため。 | PMO 委譲、予算判断 | yes | - |
| PM/TL を上位モデルに寄せ、recommender / classifier / effort-classifier は `gpt-5.4-mini` に寄せる。 | `cli/ROLE_MAP.md`, `PLAN-028`, `ADR-015` | 高コスト役割と軽量判定役割を分けないと、PM 管理コストが先に飽和するため。 | role 設計全般 | yes | - |

## 5. Handover 運用

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| handover は `CURRENT.json` を機械正本、`CURRENT.md` を人間ログとする。owner / stale / escalate を明確に持つ。 | `memory/project_2026_04_23_handover_feature.md`, `AGENTS.md`, `helix/CODEX_TL_MODE.md` | セッション上限で BE 実装が断絶しないよう、再開可能な state machine を固定する必要があったため。 | handover 継続時全般 | yes | - |
| handover の Next Action は作業メモとして扱い、出典不明な具体化を鵜呑みにしない。 | `memory/feedback_handover_unverified_specifics.md` | 前セッションの仮置き概念を真に受けて、スコープ外の仕様を勝手に拡張する事故が実際に起きたため。 | handover 再開時、調査・設計・実装 | yes | - |
| handover / lock の critical path には共通 lock primitive を段階適用し、ad-hoc lock を減らす。 | `docs/adr/ADR-016-concurrent-lock-primitive.md`, `PLAN-043` | handover 内ローカル lock だと timeout / retry / path 規約が統一されず、critical path ごとに race window が揺れるため。 | handover, `.helix/phase.yaml`, `helix.db` | 修正して維持 | V2 では handover だけでなく phase / DB まで同一 primitive と観測項目へ統一する。 |

## 6. テスト原則

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| Codex の `decision: passed` は自己申告に過ぎない。PM/TL は clean checkout で full self-test を再実行する。 | `memory/feedback_codex_completion_distrust.md`, `PLAN-035`, `PLAN-038`, `PLAN-039` | 完了報告が PASS でも、実際には self-test fail や副作用バグが残っていた事例が複数回あったため。 | 実装完了確認、commit 前 | yes | - |
| commit message の verification 文や「全件網羅」主張は独立再検証する。 | `memory/feedback_commit_msg_verification_distrust.md`, `CLAUDE.md` | dirty workspace 混入で verification が通って見え、次 PLAN で退行が発覚したため。 | commit 前、release 前 | yes | - |
| bats hidden failure を許さない。テストランナーや skip 運用も正本化し、失敗を見えなくしない。 | `docs/plans/PLAN-051-bats-lite-and-hidden-failures.md` | `bats-lite` の errexit bug により 58 件の hidden failure が埋もれていた。CI integrity を壊すため。 | shell / bats / self-test | yes | - |
| filter / parser / mock 設計では、specification domain と output domain を分離し、placeholder 例示を使う。 | `memory/feedback_filter_design_principle.md`, `PLAN-041`, `PLAN-042` | literal marker を仕様書に書いた結果、mock 経由で本物の output と誤認される副作用が起きたため。 | prompt footer、filter、mock test | yes | - |

## 7. commit / PR 原則

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| 委譲 Codex は commit しない。編集・テストまでで止め、commit 判断は PM/TL が行う。 | `memory/feedback_codex_no_commit.md`, `AGENTS.md`, `HELIX_CORE.md` | commit 粒度・メッセージ・最終レビュー責任は呼び出し元が持つべきで、委譲先に渡すと履歴が崩れるため。 | `helix codex` / 委譲 Codex 全般 | yes | - |
| 1 commit = 1 PLAN または 1 トピック。独立責務を混ぜない。 | `CLAUDE.md`, `memory/project_2026_05_08_plan024_sprint3_release.md` | 機械的 refactor、docs 追従、機能追加が混ざると rollback / retro / carry 起源の追跡が困難になるため。 | commit / PR 構成 | yes | - |

## 8. PreToolUse hook

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| 「文書で禁止」だけでは不足。Opus の repo 直接 Edit/Write は PreToolUse hook で mechanical block する。 | `PLAN-043 §3.6`, `PLAN-028 §7.2`, `.claude/memory/decisions.md` | policy 明文化後も Opus 直接 Edit 違反が複数回発生し、人間レビューだけでは止まらなかったため。 | PM / Opus 実行環境 | yes | - |
| raw CLI block, context guard, research guard も hook / wrapper で fail-close する。 | `docs/commands/ai-harness.md`, `PLAN-018`, `HELIX_CORE.md` | prompt 指示だけでは守られず、調査漏れや raw 実行が再発するため。 | PreToolUse / PostToolUse / Bash wrapper | yes | - |

## 9. skill 推挙運用

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| skill 推挙 / classifier / effort-classifier は `gpt-5.4-mini` を使う。 | `cli/ROLE_MAP.md`, `cli/config/models.yaml`, `PLAN-028` | 軽量判定を高コストモデルに載せる理由が薄く、PMO fallback 先とも整合するため。 | `helix skill`, task classification | yes | - |
| 推挙結果はキャッシュし、1 時間 TTL を基本にする。 | `docs/plans/PLAN-011-code-index-system.md`, `cli/config/defaults.yaml`, `cli/helix-skill` | 低コスト維持と応答速度の両立が必要で、都度 LLM 呼び出しは過剰なため。 | skill search / code find / recommender | yes | - |
| 推挙や自動連鎖は補助であって正本ではない。最終判断は role / phase / gate 文脈で人間または TL が持つ。 | `HELIX_CORE.md`, `cli/ROLE_MAP.md`, `memory/project_2026_05_06_plan022_023_release.md` | 推挙ロール不整合や invalid role のような運用ミスがあり、完全自動化前提は危険だったため。 | SessionStart, skill chain, research | yes | - |

## 10. V-model 強化方針

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| HELIX 工程と V-model の設計層 / テスト層を 1:1 対応させ、縦レビューと横レビューを gate に接続する。 | `docs/plans/PLAN-065-qa-strictness.md` | acceptance, contract, code, test の対応が曖昧だと、G2-G4 を通っても実質的な検証抜けが残るため。 | L1-L11, G1-G11, QA | yes | - |
| L4 code review は V の底 apex として、実装コードとテストコードの両方を review 対象にする。 | `PLAN-065` | テスト自体にもバグが入り得るため、コードだけ review しても片手落ちになる。 | L4, G4, TL review | yes | - |
| FE/fullstack の mock は append-only で昇格させるのではなく、起源 debt を明示して fail-close で除去する。 | `gate-policy.md`, `PLAN-029`, `mock-driven-development/SKILL.md` | mock が本実装に漏れると契約ドリフトが増えるため。 | FE/fullstack | 修正して維持 | V2 では `origin_mode` や artifact lineage を残し、mock 由来のまま残っていないかを SQL / gate で追跡可能にする。 |

## 11. その他

| 知見 | 起源 | 理由 (Why) | 適用範囲 (Where) | V2 でも維持 | V2 で変える場合の修正案 |
|---|---|---|---|---|---|
| 調査・レビュー・計画の wording は plan-only guard と衝突しやすい。文面と実行モードを分離して扱う。 | `memory/feedback_codex_consent_rules.md`, `helix/CODEX_TL_MODE.md` | task 説明文に「review」「設計」「PoC」が入るだけで write task が read-only 扱いに落ちたため。 | task prompt 設計、委譲テンプレート | yes | - |
| read-only / sandbox / hook の差異は「実装の制約」そのものとして記録し、単なる環境ノイズとして捨てない。 | `PLAN-043`, `PLAN-044`, `memory/project_2026_05_10_plan039_completion.md` | 環境差による blocked / false fail が運用ルールを変える直接の起源になっているため。 | Codex / Claude / test harness | yes | - |

---

## 集計

- 全知見件数: 35
- カテゴリ別件数:
  - Role 分担原則: 6
  - 委譲原則: 5
  - Gate 運用: 3
  - コスト管理: 2
  - handover 運用: 3
  - テスト原則: 4
  - commit / PR 原則: 2
  - PreToolUse hook: 2
  - skill 推挙運用: 3
  - V-model 強化方針: 3
  - その他: 2

## 「V2 で変える」リスト

1. V1 の「Opus が終盤だけ直接 Edit する」は廃止し、PM は常に委譲者へ固定する。
2. handover / phase / DB の lock は handover 局所実装から共通 primitive へ拡張する。
3. FE/fullstack の mock debt は artifact lineage を残し、`origin_mode` などの起源情報まで追跡する。
4. Gate 上の mock 起源 debt は `drive` / artifact lineage / DB record と接続し、どの mock がどこへ昇格したかを監査可能にする。

## V2 で新規追加すべき知見ガイドライン

- memory に残すのは「一度の事故報告」ではなく、**再発防止ルールに昇格したもの**だけに絞る。
- 各知見は最低でも `Why` と `How to apply` を持たせ、可能なら失敗事例の日付または PLAN ID を添える。
- 環境差 (`read-only`, hook, cache, mock, clean checkout) を原因とする learnings は優先的に記録する。
- 「モデル選択」「fallback」「guard」「hook」のルールは、文書だけでなく **実際に block / fail-close へ接続したか** を記録する。
- V2 After では、memory feedback を PLAN / ADR / DB schema のどれに昇格したかを逆引きできるよう、`origin -> enforcement -> audit` の 3 点セットで残す。

## 主要ソース

- `docs/plans/PLAN-028-helix-v2-orchestration.md`
- `docs/plans/PLAN-029-helix-rigor-expansion.md`
- `docs/plans/PLAN-043-consolidated-carry-resolution.md`
- `docs/plans/PLAN-051-bats-lite-and-hidden-failures.md`
- `docs/plans/PLAN-065-qa-strictness.md`
- `docs/adr/ADR-014-roles-config-format.md`
- `docs/adr/ADR-015-helix-v2-orchestration.md`
- `docs/adr/ADR-016-concurrent-lock-primitive.md`
- `helix/HELIX_CORE.md`
- `skills/SKILL_MAP.md`
- `helix/CODEX_TL_MODE.md`
- `cli/ROLE_MAP.md`
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/*.md` の関連 feedback / project entries
