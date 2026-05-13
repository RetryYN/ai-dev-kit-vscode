# FR-INV11: 正本 doc 整合性監査

最終更新: 2026-05-14  
監査者: Research (Codex)  
不確実性: 一部の drift は「文書が古い」のか「実装が先行した」のかを一次計画なしで断定できないため、`推奨修正` では正本優先順位に基づいて判断した。

## 1. 監査範囲とソース

### Tier 1 正本

- `CLAUDE.md`
- `AGENTS.md`
- `skills/SKILL_MAP.md`
- `helix/HELIX_CORE.md`
- `helix/CODEX_TL_MODE.md`
- `docs/v2/CONCEPT.md`
- `docs/v2/L1-REQUIREMENTS.md`

### Tier 2 参照

- `~/.claude/CLAUDE.md`
- `cli/ROLE_MAP.md`
- `cli/config/models.yaml`
- `cli/roles/*.conf`
- `docs/commands/index.md`
- `docs/commands/ai-harness.md`
- `docs/adr/ADR-014-roles-config-format.md`
- `docs/adr/ADR-015-helix-v2-orchestration.md`

### Tier 3 link / drift 確認

- `docs/commands/*.md`
- `docs/agent-skills/README.md`
- `docs/architecture/cli-layout.md`
- `docs/roadmap/*.md`
- `skills/*/SKILL.md` frontmatter
- `docs/v2/A-audit/*.md` 既存監査成果

### 監査メモ

- `helix code find` は環境側の session 初期化エラーで不使用。代替として `rg` と既存監査 doc を利用。
- `.helix/task-plan.yaml` / handover の該当行は検出できず、今回の正本は TASK_INPUT と既存 `docs/v2/A-audit/*.md`。

## 2. 軸別検出サマリ

| 軸 | P1 | P2 | P3 | 件数 |
|---|---:|---:|---:|---:|
| 1 model | 4 | 4 | 0 | 8 |
| 2 委譲 / 禁止 | 2 | 3 | 1 | 6 |
| 3 phase / gate | 2 | 2 | 1 | 5 |
| 4 link | 2 | 3 | 0 | 5 |
| 5 drift | 1 | 4 | 1 | 6 |
| **合計** | **11** | **16** | **3** | **30** |

## 3. Tier 1 要約 + 整合性スコア

| doc | 要約 | スコア |
|---|---|---:|
| `CLAUDE.md` | Claude 側の project context。PM/PMO/orchestration の運用原則は多いが、モデル表と PMO 権限が実体からズレる。 | 62 |
| `AGENTS.md` | Codex TL 向けの project rules。工程・承認・handover は比較的一貫しているが、PMO権限と TL 実装責務で他正本と衝突する。 | 68 |
| `skills/SKILL_MAP.md` | フェーズ・ゲート・drive の中核正本。全体像は最も明確だが、V2 要件追加や role 実体との差分が残る。 | 76 |
| `helix/HELIX_CORE.md` | 共通運用の圧縮正本。簡潔だが、role 正本順位と PMO allow-path の最新状態を反映していない。 | 72 |
| `helix/CODEX_TL_MODE.md` | Codex TL の読み替えルール。工程 discipline は強いが、PMO と TL の責務境界が role 実体とズレる。 | 70 |
| `docs/v2/CONCEPT.md` | V2 構想の価値連鎖定義。V2 独自概念は明確だが、既存正本との橋渡しが弱く、phase/gate 追加が孤立している。 | 61 |
| `docs/v2/L1-REQUIREMENTS.md` | V2 要件の網羅性は高いが、既存正本に未反映の gate/command/監査成果物を先行定義しており drift の発生源。 | 58 |

## 4. 検出一覧

### 軸1: model / role / thinking

| 検出 ID | 重要度 | doc A | doc B | 矛盾内容 | 推奨修正 | V2 変更計画 | V2 Phase |
|---|---|---|---|---|---|---|---|
| DOC-001 | P1 | `CLAUDE.md:82-95`, `AGENTS.md` 冒頭指示 | `ADR-014:Decision`, `docs/architecture/cli-layout.md:11,39` | `CLAUDE.md` / `HELIX_CORE.md` / `SKILL_MAP.md` が「真実は models.yaml」と書く一方、ADR-014 は `cli/roles/*.conf` を実行正本と定義。正本優先順位が二重。 | 実行正本は ADR-014 に合わせて `cli/roles/*.conf`、`models.yaml` は周知/監査用と全正本で統一。 | modify | Phase 1 |
| DOC-002 | P1 | `~/.claude/CLAUDE.md:25` | `cli/config/models.yaml:14`, `cli/ROLE_MAP.md:36`, `cli/roles/research.conf:1` | Research role が `.claude` では `Codex 5.2`、`models.yaml`/`ROLE_MAP` では `gpt-5.4`、実体 conf では `gpt-5.5`。三重不一致。 | まず `cli/roles/research.conf` を正として role catalog を再同期。Research はコード精読と技術調査を分離するなら role 分割を検討。 | modify | Phase 1 |
| DOC-003 | P1 | `cli/ROLE_MAP.md:31` | `cli/config/models.yaml:9`, `cli/roles/qa.conf:1` | QA が `ROLE_MAP` では `gpt-5.4`、実体は `gpt-5.5`。品質ゲート担当の周知が古い。 | `ROLE_MAP` を実体へ同期。QA を高コスト維持する理由も ADR/PLAN へ明示。 | modify | Phase 1 |
| DOC-004 | P1 | `CLAUDE.md:87-94` | `cli/ROLE_MAP.md:31-46`, `cli/config/models.yaml:6-25` | `CLAUDE.md` のモデル表は role を束ねすぎており、QA / Legacy / Perf / FE / advisor / impl-sonnet を落としている。運用判断に使うには粗すぎる。 | `CLAUDE.md` の表は簡略表をやめ、`ROLE_MAP.md` への参照中心に縮退。 | deprecate | Phase 1 |
| DOC-005 | P2 | `cli/ROLE_MAP.md:51` | `cli/roles/legacy.conf:2` | `ROLE_MAP` の effort map は legacy=`xhigh`、実モデル表は legacy=`gpt-5.4` のみで thinking を表に出していない。正本が split され認知負荷が高い。 | thinking の周知正本を `ROLE_MAP` か `models.yaml role_metadata` に一本化。 | extend | Phase 1 |
| DOC-006 | P2 | `HELIX_CORE.md:18-27`, `SKILL_MAP.md:9-18` | `cli/ROLE_MAP.md:44-46`, `cli/config/models.yaml:18-25` | advisor / impl-sonnet が Tier1 正本のモデル表から落ちている。V2 要件では PMO 5 role conf を要求しており不足。 | Tier1 表は最小でも `impl-sonnet` / `pm-advisor` / `tl-advisor` を含める。 | modify | Phase 1 |
| DOC-007 | P2 | `~/.claude/CLAUDE.md:16,30` | `ADR-014` | `.claude` は「workflow-core のモデル割当テーブル」「真実は models.yaml」とし、ADR-014 の conf 正本方針を参照していない。 | `.claude/CLAUDE.md` に ADR-014 を追加参照し、実行正本順を明記。 | modify | Phase 1 |
| DOC-008 | P2 | `docs/architecture/cli-layout.md:14,26` | `cli/ROLE_MAP.md:21-46` | `cli-layout` は `ROLE_MAP.md` を「12 role 一覧」と書くが、現実は 20+ role。 architecture doc が stale。 | `12 role` 表現を削除し、 role 数は自動生成または参照に切替。 | modify | Phase 1 |

### 軸2: 委譲ルール / 禁止事項

| 検出 ID | 重要度 | doc A | doc B | 矛盾内容 | 推奨修正 | V2 変更計画 | V2 Phase |
|---|---|---|---|---|---|---|---|
| DOC-009 | P1 | `AGENTS.md:64`, `CODEX_TL_MODE.md:54-55` | `cli/roles/pmo-sonnet.conf:6-10` | AGENTS は PMO に「必要最小限のドキュメント起草」を許すが、PMO Sonnet 実体は `plan` + `Edit/Write` 禁止で完全 read-only。 | PMO Sonnet は read-only を正とし、起草は docs/impl-sonnet/Haiku のみと明文化。 | modify | Phase 1 |
| DOC-010 | P1 | `CLAUDE.md:93`, `CODEX_TL_MODE.md:55` | `cli/config/models.yaml:44-51`, `cli/roles/pmo-haiku.conf:6-10` | PMO Haiku を `docs/**` 限定と書く文書が多いが、実体は `docs/**,skills/**` 書込可。許可範囲が違う。 | 実体に合わせて `skills/**` を正本へ反映、または実装を `docs/**` のみに戻す。現状は実装優先で文書修正が妥当。 | modify | Phase 1 |
| DOC-011 | P2 | `AGENTS.md:64` | `cli/roles/pmo-haiku.conf:10` | AGENTS は PMO 一般として曖昧だが、Haiku は write-enabled。Sonnet と Haiku を同一「PMO」でまとめると誤運用を誘発。 | PMO を `PMO Sonnet(read-only)` と `PMO Haiku(light write)` に常に分けて記述。 | modify | Phase 1 |
| DOC-012 | P2 | `AGENTS.md:27-40`, `TL Driven Mode` | `cli/roles/tl.conf:11` | AGENTS/Codex TL 説明は TL が実装まで一気通貫に見えるが、`tl.conf` は実装禁止。TL role と TL mode が同名で意味が分裂。 | `TL mode` と `tl role` を明確に分離して説明し、実装は `se/pg/docs` へ委譲が原則と明記。 | modify | Phase 1 |
| DOC-013 | P2 | `CLAUDE.md:114-125` | `~/.claude/CLAUDE.md:56-90` | どちらも「Agent tool 完全禁止」を掲げるが、禁止理由・例外経路・許可対象の粒度が微妙に異なる。運用文言が複線化。 | 禁止ポリシーを `ai-harness.md` か単独 policy doc に集約し、他 doc は参照だけにする。 | new | Phase 1 |
| DOC-014 | P3 | `AGENTS.md:120-127` | `docs/commands/ai-harness.md:77-92` | `helix review --uncommitted` を優先する指示はあるが、レビュー工程の mandatory 条件が doc ごとに少し異なる。実害は小さいが drift。 | レビュー必須条件を `ai-harness.md` に一本化。 | as-is | Phase 1 |

### 軸3: phase / gate / drive

| 検出 ID | 重要度 | doc A | doc B | 矛盾内容 | 推奨修正 | V2 変更計画 | V2 Phase |
|---|---|---|---|---|---|---|---|
| DOC-015 | P1 | `docs/v2/CONCEPT.md:149-158`, `docs/v2/L1-REQUIREMENTS.md:232-284` | `SKILL_MAP.md` / `HELIX_CORE.md` 全体 | V2 は Phase A-J と `G3.functional_freeze` を導入するが、既存正本は L1-L11 / G0.5-G11 のまま。移行ガイドがない。 | `v2 gate overlay` を別正本化し、SKILL_MAP / HELIX_CORE から参照する。 | new | Phase 2 |
| DOC-016 | P1 | `docs/v2/L1-REQUIREMENTS.md:282,373` | `docs/commands/index.md:1-115` | `helix gate G3 --subgate functional_freeze` を要件化しているが、commands index に存在しない。要件だけ先行。 | 実装前提コマンドは `planned` / `future` 表示を明示するか、L1 で CLI 名を仮称扱いにする。 | modify | Phase 2 |
| DOC-017 | P2 | `docs/v2/L1-REQUIREMENTS.md:95,169,196,359-372` | `docs/commands/index.md` | `helix detect dashboard`, `helix report dev-state`, `helix qa vmodel-score` 等のコマンド群が commands 正本に未掲載。 | V2 planned command を `docs/commands/index.md` に planned セクションとして追加。 | extend | Phase 2 |
| DOC-018 | P2 | `docs/v2/L1-REQUIREMENTS.md:408` | `SKILL_MAP.md:81`, `HELIX_CORE.md:119-122` | 人間承認必須ゲートの列挙に V2 L1 は G9-G11 を含むが、既存正本では `自動/PM` や `PM` と書かれ、human approval の強度が揺れる。 | Run gate の HITL 要件を gate-policy 側で明文化し、全 doc 参照化。 | modify | Phase 2 |
| DOC-019 | P3 | `docs/v2/L1-REQUIREMENTS.md:123-126` | `SKILL_MAP.md:180-237` | V2 の drive 定義は BE/FE/DB/Fullstack を中心に再定義するが、既存 SKILL_MAP は scrum/agent を含む 6 drive。V2 文書が subset であることを言わない。 | V2 文書に「今回は 4 drive を主対象、scrum/agent は既存定義を継承」と追記。 | modify | Phase 2 |

### 軸4: link 切れ / outdated

| 検出 ID | 重要度 | doc A | doc B | 矛盾内容 | 推奨修正 | V2 変更計画 | V2 Phase |
|---|---|---|---|---|---|---|---|
| DOC-020 | P1 | `docs/agent-skills/README.md:67,74,93,102,109,121` | 参照先不存在 | `docs/cursor-setup.md` など setup 文書リンクが `docs/agent-skills/` 相対解決で全滅。導線が壊れている。 | repo root 相対に直すか、実ファイルを `docs/agent-skills/docs/` へ配置。 | modify | Phase 1 |
| DOC-021 | P1 | `docs/agent-skills/README.md:139-202,214-229,315` | 参照先不存在 | skills/agents/references/CONTRIBUTING への相対リンクが大量に broken。README 全体のリンク基盤が repo 構造と不整合。 | upstream README をそのまま置かず、HELIX repo 構造に合わせて path を全面再配線。 | modify | Phase 1 |
| DOC-022 | P2 | `docs/architecture/cli-layout.md:107-109` | 参照先不存在 | architecture doc が `docs/adr/...` を自身の相対 path で参照しており broken。 | `../adr/...` に修正。 | modify | Phase 1 |
| DOC-023 | P2 | `docs/adr/ADR-011-test-duplication.md:108` | `/.helix/reverse/R4-gap-register.md` 不存在 | repo ルート絶対 path で `.helix` を参照しており broken。 | relative path か「runtime file」の注記へ変更。 | modify | Phase 1 |
| DOC-024 | P2 | `docs/adr/ADR-013-r4-gate-design.md:109` | `/.helix/reverse/R4-gap-register.md` 不存在 | ADR-013 も同じ absolute path 問題。 | ADR-011 と同じ修正方針で統一。 | modify | Phase 1 |

### 軸5: drift / outdated / V1→V2移行

| 検出 ID | 重要度 | doc A | doc B | 矛盾内容 | 推奨修正 | V2 変更計画 | V2 Phase |
|---|---|---|---|---|---|---|---|
| DOC-025 | P1 | `docs/v2/L1-REQUIREMENTS.md:367` | `docs/v2/A-audit/*.md` | AC-10 が「4 audit doc 完備」と書く一方、既に `off-plan-implementations.md` 等が追加されている。受入条件が現実より古い。 | AC-10 を「必須 audit doc セット」に言い換え、固定件数をやめる。 | modify | Phase 1 |
| DOC-026 | P2 | `docs/v2/L1-REQUIREMENTS.md:114` | 実ファイル不存在 | FR-INV06 が `deprecated.md` 起票を要求するが、監査成果群に未作成。要件と監査実態がズレている。 | Phase A 成果物一覧を見直し、必要なら `deprecated.md` を追加、不要なら FR を削る。 | modify | Phase 1 |
| DOC-027 | P2 | `docs/v2/L1-REQUIREMENTS.md:421` | `cli/ROLE_MAP.md:42-46`, `cli/roles/*.conf` | DEP-03 は `ls cli/roles/pmo-*.conf` で PMO role conf 既存確認とするが、要件本文は `pm-advisor` / `tl-advisor` / `impl-sonnet` も含む。確認式が不足。 | dependency check を advisor/impl-sonnet まで含む形へ修正。 | modify | Phase 1 |
| DOC-028 | P2 | `docs/architecture/cli-layout.md:14,26` | `cli/ROLE_MAP.md:21-46` | `ROLE_MAP.md` を 12 role と書きつつ実測 20 conf を持つ。architecture doc 自身が stale count を抱える。 | role 数は静的記述をやめ、`17+拡張 role` などの非固定表現へ。 | modify | Phase 1 |
| DOC-029 | P2 | `docs/agent-skills/README.md:128,195` | 実 repo 実態 | `全25スキル` と書くが、repo の `skills/*/SKILL.md` は大幅に多い。upstream README を HELIX 用 README として流用しすぎ。 | `docs/agent-skills/README.md` は upstream skill pack README と明示し、HELIX skill 数の記述を分離。 | deprecate | Phase 1 |
| DOC-030 | P3 | `docs/v2/CONCEPT.md:205-215` | `off-plan-implementations.md`, `capability-inventory.md` | V2 構想は PMO 委譲で予算内完結を前提にするが、実際には off-plan command/role が多く orchestration の正本整理コストを過小評価している可能性。 | Concept のリスクに「正本整理コスト」を追加。 | extend | Phase 1 |

## 5. 最も drift が大きい doc top-3

1. `docs/agent-skills/README.md`
   相対リンクが大量に切れており、skill 数・配置・agent path も repo 実態とズレる。参照 doc というより upstream README の残骸に近い。
2. `docs/v2/L1-REQUIREMENTS.md`
   V2 future state を先行定義しているが、commands / gate / audit acceptance が既存正本へ未接続。After 正本としては強いが migration bridge が弱い。
3. `CLAUDE.md`
   PM/PMO/orchestration の方針は豊富だが、モデル表と PMO 権限範囲が role 実体からズレ、運用者が誤解しやすい。

## 6. V2 で正本一元化が必要な領域 top-5

1. モデル割当と thinking
   推奨: 実行正本=`cli/roles/*.conf`、周知/監査=`cli/config/models.yaml`、人間向け説明=`ROLE_MAP.md` に固定。
2. 委譲禁止 / PMO 権限 / Agent tool policy
   推奨: `docs/commands/ai-harness.md` または専用 policy doc を正本にし、`CLAUDE.md`/`AGENTS.md`/`.claude/CLAUDE.md` は参照だけにする。
3. フェーズ / ゲート / drive 定義
   推奨: `SKILL_MAP.md` + `gate-policy.md` を唯一の正本にし、V2 追加分は overlay doc を作ってから昇格する。
4. CLI コマンドカタログ
   推奨: `docs/commands/index.md` を planned/current の二層で管理し、V2 要件の仮コマンド名をそこで凍結する。
5. 監査成果物セット
   推奨: `docs/v2/A-audit/README.md` か `L1-REQUIREMENTS.md` の成果物一覧を SSOT 化し、「4件」など固定件数をやめる。

## 7. PMO 視点での次アクション

### P1 即修正

- `DOC-001`-`004`: model 正本順位を一本化し、Research/QA/PMO の表を同期。
- `DOC-009`-`010`: PMO Sonnet/Haiku の権限を文書へ反映。
- `DOC-015`-`016`: V2 gate/command の overlay 正本を追加。
- `DOC-020`-`021`: `docs/agent-skills/README.md` の broken link を止血。

### Phase 1 で集中対応

- `DOC-022`-`030`: architecture/ADR/V2 audit acceptance の stale 更新。
- `ROLE_MAP` / `models.yaml` / `roles/*.conf` の doctor ベース同期チェックを docs integrity audit に組み込む。

### V2 全体で正本構造刷新

- `model-policy.md` または `role-catalog.md`
- `delegation-policy.md`
- `v2-gate-overlay.md`
- `docs/v2/A-audit/README.md`

## 推奨

- 最優先の推奨は「モデル正本」「PMO 権限」「V2 gate overlay」の 3 領域を先に固定すること。ここが曖昧なままだと、以後の V2 docs は drift を増幅する。
- link 修正は P1 だが、単なる cleanup ではなく「どの doc を正本として残すか」を先に決めてから直すべき。特に `docs/agent-skills/README.md` は HELIX 正本ではなく upstream mirror 扱いに落とす方が自然。
- 不確実な点は、V2 文書の future command 名が「実装予定」なのか「既存前提」なのかの境界。これは `planned/current` ラベルを docs/commands 側へ導入すれば解消できる。
