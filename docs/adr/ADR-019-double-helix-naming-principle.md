# ADR-019: HELIX = DNA 二重らせん命名原則と 3 軸トライアングル

## Status

Accepted (2026-05-18)

> Proposed (2026-05-17) → Accepted (2026-05-18) PO 承認。PLAN-084 Phase 4 実装完遂後、PO (yoshiyuki0907yn@gmail.com) が「OK」と承認。

## Deciders

- PM (Opus)
- TL (Codex tl-advisor)
- PO (yoshiyuki0907yn@gmail.com、2026-05-18 承認)

---

## Context

HELIX という命名は当初、「開発フロー CLI のプロジェクト名」として発案されたが、
V2 構築の過程で命名の由来を **DNA 二重らせん構造** に対応させる設計原理が
memory [[project_2026_05_15_helix_spiral_final_form]] (2026-05-15) で確立された。

DNA は 2 本の strand (鎖) が塩基対で結合し、らせん状に巻かれた構造を持つ。
HELIX framework では:

- **artifact strand**: V-model 工程群が生む成果物の累積 (docs / code / test design / test code)
- **record strand**: CLI 操作・ゲート通過・Agent 呼び出しの event log 累積 (6 db)

の 2 本が、実行者 (Actor) + detector という「塩基対」で結合し、
Sprint 1 周 = 1 回転として時間軸で自己組織的に進化する構造が、
HELIX の命名原理と物理実装を統一的に説明する。

また、3 軸トライアングル原則 (memory [[project_2026_05_15_helix_triangle_principle]])
が「成果物 → 実行者 → 記録」の順序を確立し、
db 設計を最後段に置く判断の根拠となっている。
CONCEPT.md §3 の現状は「2 Base 軸 + 付随基盤: helix.db」を持ち、
3 軸トライアングルの明示記述はまだない。本 ADR 採択後の Phase 2.2
(CONCEPT.md 拡張) で §3-axis-triangle 章を追加し、本 ADR §Decision.3 を
上位概念として引用する形で命名由来と strand mapping を CONCEPT.md にも反映する。

本 ADR は PLAN-084 §2.5.0 G-08 を受けて Phase 2 で起票する概念定義 ADR であり、
物理実装 (6 db 分離 + Event Sourcing) を扱う ADR-018 と対をなす。

---

## Decision

以下 4 件を L2 として凍結する。

### 1. HELIX = DNA 二重らせん命名の由来正式化

HELIX という命名は **DNA 二重らせん構造** に由来することを正式化する。

```
artifact strand                       record strand
──────────────────────────            ──────────────────────────
L1 要件 / 受入テスト設計               orchestration.db
L2 全体設計 / 総合テスト設計     ◇◇◇  vmodel.db
L3 詳細設計 / 結合テスト設計     塩基対  scrum.db
L4 実装コード / 単体テストコード  ◇◇◇  plan.db
Sprint commit chain                   backend.db
docs/v2 docs hierarchy                frontend.db
──────────────────────────            ──────────────────────────
              ↑ Actor (helix CLI command) + detector が結合を維持 ↑
```

各 Sprint で artifact strand と record strand がそれぞれ 1 周分延伸し、
時間軸で自己組織的に進化する。

### 2. artifact strand × record strand 対応表

| artifact strand (V-model 成果物累積) | record strand (6 db event log / state) |
|---|---|
| docs/v2/L1-REQUIREMENTS.md (要件 + 受入テスト設計) | orchestration.db — phase / gate / sprint 遷移 event |
| docs/v2/L2-MASTER.md + ADR-* (全体設計 + 総合テスト設計) | vmodel.db — artifact / test_design / review event |
| D-API / D-DB / D-CONTRACT (詳細設計 + 結合テスト設計) | scrum.db — hypothesis / poc / verify / decide event |
| cli/lib/*.py + cli/helix-* (実装コード + 単体テストコード) | plan.db — PLAN doc 進行 state snapshot + change log |
| docs/v2/L4-test-design/*.md + cli/lib/tests/test_*.py | backend.db — be coverage / drive 切替 state |
| .claude/agents/*.md + cli/templates/agents/*.md | frontend.db — visual mock / FE 成果物 state |

strand 接続ルール:
- Actor (PM / TL / SE / PE / QA / PMO / PdM) が helix CLI command を実行すると、
  artifact strand の成果物変化と record strand への event write が同時に発生する
- detector (lint / audit / advisor) が record strand の anomaly を検知し、
  artifact strand の修正要求として Actor へフィードバックする
- Reverse 機能 (R0-R4 + RGC) は **record strand を持たない例外**:
  既存 code の逆引きであり新規 event を生成しないため (FR-DB-SEP-07 参照)

#### strand の延伸モデル (Sprint 単位)

Sprint 1 周を「らせん 1 回転」と定義する。各 Sprint で以下が同時進行する:

```
Sprint N
  artifact strand 延伸:
    - Sprint Plan 文書追記 (docs/plans/*.md)
    - 実装コード追加 (cli/lib/*.py)
    - テスト追加 (cli/lib/tests/test_*.py)
    - commit chain 延伸 (git log)

  record strand 延伸:
    - orchestration.db: sprint_start / sprint_complete event 追記
    - vmodel.db: artifact_created / test_baseline event 追記
    - plan.db: plan_state snapshot 更新 + change log 追記

  塩基対 (binding):
    - Actor: helix sprint complete --auto-check (両 strand 同時更新を保証)
    - detector: vmodel_lint / sprint_lint が artifact vs record の divergence を検知

  → Sprint N+1 に向けて両 strand が 1 段積まれ、らせんが 1 回転進む
```

この繰り返しが「自己組織的進化」の物理的実体であり、
V2 完了状態 = らせんが L1-L11 + Run (L9-L11) を 1 周したことを意味する。

### 3. 3 軸トライアングル原則と順序の確定

HELIX の設計判断は以下の 3 軸で構成され、**順序は固定**:

```
① 成果物 (V-model 工程群)
   ↓  成果物が決まって初めて
② 実行者 (Actor = subagent 14 種 + CLI roles 30 種)
   ↓  実行者が決まって初めて
③ 記録 (DB = 6 db 分離後の event log + state snapshot)
```

各軸の内訳:

| 軸 | 内容 | HELIX 実体 |
|---|---|---|
| ① 成果物 | HELIX 4 phase (計画 / 実装 / 仕上げ / Run) で生まれる docs + code + test | docs/v2/L1〜L11 doc 群 / cli/lib/*.py / cli/helix-* |
| ② 実行者 | mandatory 10 種 + on-demand 4 種 の subagent + CLI roles 30 種 | .claude/agents/*.md / cli/roles/*.conf |
| ③ 記録 | orchestration / vmodel / scrum / plan / backend / frontend の 6 db | cli/lib/helix_db.py → 6 db 分離後 |

**順序違反の禁止**: db 設計 (③) を成果物定義 (①) より先に議論・実装してはならない。
「db 設計から始める」提案は 3 軸トライアングル違反として reject する
(memory [[feedback_v2_basic_design_first_not_plan_level]] 参照)。

#### 3 軸トライアングルと 二重らせんの対応

3 軸トライアングルと二重らせんは同一モデルの 2 つの見方:

| 観点 | 二重らせん表現 | 3 軸トライアングル表現 |
|---|---|---|
| 成果物 | artifact strand (左鎖) | ① 成果物 (V-model 工程群) |
| 記録 | record strand (右鎖) | ③ 記録 (6 db) |
| 結合媒体 | 塩基対 (Actor + detector) | ② 実行者 (subagent 14 種 + CLI roles 30 種) |
| 時間軸 | らせん回転 (Sprint 周期) | 3 軸の反復サイクル |

らせんモデルは「成長の動的な側面」を、トライアングルは「構造の静的な側面」を強調する。
設計議論では用途に応じて使い分ける:
- **新規 PLAN の成果物分類** → トライアングル (どの軸に属するかを先に決める)
- **Sprint 進行の可視化** → らせん (回転数 = Sprint 完了数として表現する)
- **db エンティティの帰属確認** → strand mapping 表 (上記対応表で確認する)

### 4. HELIX 命名の運用ガイド

| 区分 | 使用ルール |
|---|---|
| **HELIX** (大文字) | 命名の正本。framework 全体 / 本 ADR の概念説明 / 公式ドキュメント見出しで使用 |
| **helix** (小文字) | CLI コマンド名 / Python package / project リポジトリ名として限定使用 |
| **strand / 塩基対** 等の生物学的比喩 | 概念図・本 ADR・CONCEPT.md §double-helix-strand セクション内のみで使用。CLI / file 名 / Python 変数名には持ち込まない |
| **らせん / helix** の再利用 | PLAN-079 SRF (Scrum → Reverse → Forward chain) 等、別意で使う既存 PLAN は本 ADR の定義に従い概念整合を確認する |

命名審査チェック (新規 file / 変数 / PLAN でらせん関連語を使う場合):

1. DNA 由来の strand / coil / replication / nucleotide → 概念図 / ADR 外での使用禁止
2. 「helix で管理する」「helix に登録する」→ CLI コマンド名として適切 (helix 小文字)
3. 「HELIX の原則として」→ framework 概念として適切 (HELIX 大文字)

**運用例**:

| 表現 | 判定 | 修正案 |
|---|---|---|
| `def artifact_strand_append(...)` | NG (CLI 実装にらせん用語持ち込み) | `def append_artifact(...)` |
| `# artifact strand に登録する` コメント | OK (コメントは概念説明として許容) | — |
| PLAN-XXX 本文「artifact strand として扱う」 | OK (PLAN 文書は概念説明の場) | — |
| `class StrandManager:` | NG (Python クラス名にらせん用語持ち込み) | `class ArtifactRegistry:` |
| `helix strand list` (仮想 CLI コマンド) | NG (CLI コマンド名にらせん用語持ち込み) | `helix artifact list` |

---

### 既存文書との整合要件

本 ADR 採択後、以下の整合作業を P2/P3 carry として記録する (表中の優先度に従う):

| 対象 | 整合確認内容 | 優先度 |
|---|---|---|
| PLAN-079 SRF | 「Scrum → Reverse → Forward chain」の「らせん」用法が本 ADR と矛盾しないか確認 | P3 |
| CONCEPT.md §3 | 「2 Base 軸 + 付随基盤」現状記述に §3-axis-triangle + §double-helix-strand 章を Phase 2.2 で追記、本 ADR §Decision.3 を引用 | P2 |
| docs/plans/PLAN-084-*.md | G-08 参照箇所が本 ADR の section 番号と一致するか確認 | P2 |
| docs/operator/helix-spiral-operations.md | 「helix-spiral / らせん」用法が本 ADR の HELIX 命名運用ガイドと矛盾しないか確認 (tl-advisor Round 2 minor #5 反映) | P3 |
| docs/plans/PLAN-027-*.md | 「entries / links」基盤の strand 概念表記が本 ADR の artifact strand × record strand 命名と整合するか確認 | P3 |
| docs/plans/PLAN-078-*.md | agent_slots 関連の「らせん」用法 (もしあれば) が本 ADR の塩基対モデルと整合するか確認 | P3 |
| memory ファイル群 | [[project_2026_05_15_helix_spiral_final_form]] 等の記述と本 ADR の乖離チェック | P3 |
| 包括的棚卸し | `rg "らせん\|strand\|helix" docs/ skills/ memory/` を Phase 2 完了時に全件棚卸し、本表に未列挙の用例も確認 (broaden 方針、tl-advisor Round 2 minor #5 反映) | P3 |

---

## Consequences

### Positive

- HELIX framework の命名・概念・物理実装が DNA 二重らせんモデルで一元説明可能になる
- 新規 PLAN 起票時に「どの strand に属するか」で文書間整合を機械的に判断できる
- 3 軸トライアングルの順序確定により、db 設計より先に成果物・実行者を決める判断基準が明文化される
- ADR-018 (物理 db 分離) と ADR-019 (概念命名) が対になることで、
  概念レイヤーと実装レイヤーの分離が維持される

### Negative

- 既存 docs / PLAN の「らせん」「helix」用法を本 ADR に合わせて整理する負担が生じる
  (PLAN-079 SRF 等、最低 2 件の文書確認が必要)
- 概念モデル (DNA 比喩) を理解しないと strand / 塩基対の意味が伝わらない認知コストがある
- 命名審査チェックが新規ファイル命名の意思決定に追加ステップを加える

### Risks

- **概念過剰リスク**: DNA 比喩への過度な依存により、実装判断が遅れる
  → 緩和策: ADR-018 (物理実装) と ADR-019 (概念) を分離し、実装判断は ADR-018 を優先参照する
- **既存文書との不整合**: らせん関連語を別意で使っている PLAN が本 ADR 後に混乱する
  → 緩和策: PLAN-084 Phase 2 完遂時点で `grep -rn "らせん\|strand\|coil" docs/` を実行し、
    逸脱箇所をリスト化して P3 carry として処理する

---

## Alternatives considered

### A. DNA 由来概念を不採用 (HELIX = 略号扱い)

- 内容: HELIX を単純なプロジェクト名として扱い、命名由来の正式化を行わない
- 却下理由: 3 軸トライアングルとの整合性が説明できない。
  「成果物 → 実行者 → 記録」の順序根拠が「らせん」の物理的性質
  (strand が積み上がるにつれ構造が安定する) と一致しており、
  命名由来の正式化なしには設計判断の言語化が冗長になる

### B. strand mapping を物理 db 分離と連動させない

- 内容: 二重らせん概念は採用するが、artifact strand / record strand と
  6 db の対応関係を本 ADR では規定しない (ADR-018 のみで規定)
- 却下理由: strand mapping を物理 db 分離と連動させないと、
  ADR-018 と ADR-019 の概念モデルが冗長化し、どちらを参照すべきか曖昧になる。
  本 ADR が概念定義を担い、ADR-018 が物理設計を担う分業構造こそが
  2 ADR 並行起票の意義であるため不採用

---

## Related

- PLAN-084 §2.5.0 G-08 (本 ADR の起票要件を確定した L1 要件箇所)
- FR-DB-SEP-08 (L1-REQUIREMENTS.md §3.9、二重らせん命名の L1 FR)
- ADR-015 (HELIX v2 orchestration、本 ADR の概念前提となる V2 ロール再配置)
- ADR-018 (db 分離 + Event Sourcing、本 ADR と同時起票、物理実装側)
- CONCEPT.md §3 (3 軸トライアングル + 付随基盤の既存記述、本 ADR が L2 で補強)

## References

- memory [[project_2026_05_15_helix_spiral_final_form]] (二重らせん概念の出発点、Sprint 1 周 = 1 回転の原型)
- memory [[project_2026_05_15_helix_triangle_principle]] (3 軸トライアングル根本構造、順序の確立)
- memory [[project_2026_05_15_vmodel_as_db_separation_foundation]] (V-model 強化 = db 分離基盤、artifact strand の前提)
- memory [[feedback_v2_basic_design_first_not_plan_level]] (db 設計先行禁止の根拠インシデント)
