# helix reverse 判定管理ガイド

`helix reverse` は既存コードや既存設計から事実を集め、Forward HELIX に安全に接続するための逆引きフローです。通常の新規開発ではなく、現状理解・設計復元・差分整理が主目的です。

## 入口判定

| 状況 | 使う type | 理由 |
|---|---|---|
| 既存コードから設計を復元したい | `code` | コード、DB、設定、外部接続から R0-R4 を作る |
| 設計文書群の依存順や接続漏れを整理したい | `design` | docs/plans, docs/design, docs/features から DAG と routing を作る |
| バージョンアップや依存更新の影響を見たい | `upgrade` | compatibility / impact / routing を作る |
| 実装と設計文書の drift を正規化したい | `normalization` | drift evidence から設計更新候補を作る |
| 実装完了後に文書・受入・運用引継ぎを揃えたい | `fullback` | 完了実装から文書整合と handover checklist を作る |

迷った場合は、対象がコードなら `code`、設計資産なら `design`、完了後の整合なら `fullback` を選びます。

## 基本フロー

```bash
helix setup preflight --profile reverse --reverse-type code --target src/
helix reverse code R0 --target src/
helix reverse code R1
helix reverse code R2
helix reverse code R3
helix reverse code R4
helix reverse code rgc
```

`code` は後方互換のため type 省略もできます。

```bash
helix reverse R0 --target src/
helix reverse status
```

## Type 別成果物

| type | 主な成果物 |
|---|---|
| `code` | `R0-evidence-map.yaml`, `R1-observed-contracts.yaml`, `R2-as-is-design.md`, `R3-intent-hypotheses.md`, `R4-gap-register.yaml` |
| `design` | `D0-design-evidence-map.yaml`, `D2-design-dag.yaml`, `D3-impl-order.yaml`, `D4-design-routing.yaml` |
| `upgrade` | `U0-upgrade-context.yaml`, `U1-upgrade-contracts.yaml`, `U2-assessment-impact.yaml`, `U3-upgrade-hypotheses.md`, `U4-upgrade-routing.md` |
| `normalization` | `N0-drift-evidence.yaml`, `N2-normalization-drift.yaml`, `N3-normalization-hypotheses.md`, `N4-normalization-gap-register.yaml` |
| `fullback` | `F0-fullback-evidence.yaml`, `F1-fullback-contracts.yaml`, `F2-fullback-as-is-review.md`, `F3-fullback-handover-checklist.yaml`, `F4-fullback-routing.md` |

## Gate 判定

| Gate | 判定対象 | pass の意味 | fail 時 |
|---|---|---|---|
| `RG0` | 証拠収集 | 対象範囲の evidence が作られた | R0 をやり直す。対象 path / source を増やす |
| `RG1` | 観測契約 | API / DB / 型 / 互換契約の観測が揃った | R1 をやり直す。契約抽出対象を追加する |
| `RG2` | As-Is / DAG / impact | 現状設計、DAG、影響評価が説明できる | R2 をやり直す。矛盾や unknown を潰す |
| `RG3` | 仮説 / routing | Forward に渡す仮説・gap・routing がある | R3/R4 を見直す。PO/TL 確認質問を追加する |
| `RGC` | gap closure | Forward 側で gap の閉塞状態を確認した | open / partial を Forward の debt / plan に戻す |

`design` と `normalization` は `RG1` を持たず、`RG0 -> RG2 -> RG3 -> RGC` の形で進みます。`upgrade` は RGC を持たず、R4 routing を Forward 接続点として扱います。

各 stage の gate は、委譲コマンドの終了だけでは pass しません。指定された成果物ファイルが存在し、空でなく、YAML 成果物なら top-level mapping として解析できることを最低条件として validation します。空ファイルや壊れた YAML は failed 扱いになり、`retry` または手動修正が必要です。

## 状態確認と再実行

```bash
helix reverse code status
helix reverse code status --json
helix reverse code retry --last-failed
helix reverse design retry R2 --dry-run
```

`status --json` は dashboard や外部集計用です。`retry --last-failed` は failed gate に対応する stage を再実行します。

いずれの type でも R4 成果物の validation に通ると `.helix/phase.yaml` の `reverse.status=completed` と `reverse.types.<type>.status=completed` が更新されます。`helix mode forward` はこの aggregate status を見て Forward への切替可否を判断します。

## Forward 接続

R4 で作った routing は Forward HELIX のどこへ戻すかを決める材料です。

| Reverse の結論 | Forward 側 |
|---|---|
| 要件そのものが曖昧 | L1 / `helix plan` 前に再定義 |
| 設計判断が不足 | L2 / ADR / design-doc |
| API / DB / contract が不明 | L3 / api-contract / db |
| 実装だけで閉じる | L4 / sprint |
| 運用・受入・文書整合 | L8-L11 / fullback |

`--invalidate-forward` は `code` type の R2/R3/R4/run/retry で使えます。Reverse の結果が Forward の既存 gate 前提を崩す場合に、G2-G11（G8 は存在しない）を invalidated に戻します。

```bash
helix reverse code R4 --invalidate-forward
```

## RGC の扱い

```bash
helix reverse code rgc
helix reverse design rgc
helix reverse normalization rgc
helix reverse fullback rgc
```

RGC は「Reverse で見つけた gap が Forward 側で閉じたか」を確認する閉塞チェックです。open が残る場合は `debt`、`readiness defer`、または新しい `plan` に戻します。

---

## Worked Example: legacy CRUD アプリ → Forward L4

設計書なし legacy CRUD アプリ（Express + PostgreSQL + 1k LOC）を Reverse → Forward に接続する完走シナリオ。

### シナリオ概要

- 対象: Express + PostgreSQL + 単一テナント CRUD
- 規模: 1k LOC / 20 endpoints / 12 tables
- 完走時間目安: 4-8h (small)、10k LOC なら 1-2 day (medium)

### R0: Evidence Acquisition (1-2h)

```bash
helix code build
helix code stats --by domain
helix reverse code R0 --target src/
```

成果物: `docs/reverse/R0-evidence-map.yaml`（modules / db_schema / runtime_topology / unknowns）

### R1: Observed Contracts (1-2h)

```bash
swagger-jsdoc -d swaggerDef.js src/routes/*.js > openapi.yaml
psql -d app_db -c '\d+' > db-schema.txt
tsc --emitDeclarationOnly --outDir types/
helix reverse code R1
```

成果物: `docs/reverse/R1-observed-contracts.yaml`（api / db / types）

### R2: As-Is Design (1h)

ADR 仮説を 3 件起票: ADR-101 draft-reverse（session-cookie based auth）、ADR-102 draft-reverse（cache layer なし）、ADR-103 draft-reverse（error handling は middleware 集約）。

成果物: `docs/reverse/R2-as-is-design.md`

### R3: Intent Hypotheses (1h、PO 検証)

PO 検証で 5 intent / 2 accidental / 1 unknown を確定。例: マルチテナント未対応は意図的、cache 層欠落は偶発、rate limit ポリシーは PO 要確認。

### R4: Gap & Routing (30min)

gap_register 4 件:

| gap_id | severity | gap kind | primary_routing | post_forward_action |
|---|---|---|---|---|
| GAP-001 | critical | rate limit 要件未定義 | L1 | - |
| GAP-002 | high | cache 層実装欠落 | L4 | observability (L10) |
| GAP-003 | high | マルチテナント受入条件 | L1 | - |
| GAP-004 | medium | error log 仕様不足 | L2 | runbook (L11) |

### Forward 接続 (5min)

```bash
helix plan draft --title 'rate limit 要件定義 (GAP-001)' --plan-id PLAN-NNN
helix sprint next --task 'cache layer 実装 (GAP-002)'
```

critical gap（L1）は Forward で要件定義へ、high gap（L4）は sprint へ投入する。

### 完走後

```bash
helix reverse code rgc
```

primary_routing で投入した gap が Forward 側で closed / partial / open のどれになったかを集計し、post_forward_action は L8-L11 の plan / debt_register に carry する。
