# PLAN-008: Reverse 5系統化（フルバック追加・設計 Reverse） (v3.3)

## 1. 目的 / Why

既存 `workflow/reverse-analysis` は現在、`Code から設計復元` の 1 系統（R0-R4）を中心に据えた復元ワークフローとして機能している。

`PLAN-008` は、運用上発生している 3 種類の設計ズレ・再構成ニーズを吸収するため、Reverse を 5 系統化し、実装前後の状態差を同じ実行基盤上で扱えるようにする。

追加する 5 系統は以下。

- Code 復元 Reverse（既存）: 設計書なしレガシーコードから現行設計を復元し、Forward へ接続する。
- バージョンアップ Reverse（新）: 次版実装予定を前提に、現行設計から実装上の想定差分を逆引きし、設計前提と移行計画の起点を作る。
- ノーマライゼーション Reverse（新）: 実装と設計の乖離（drift）を前提に、実装実態を起点として設計を再正規化する。
- フルバック Reverse（新）: 実装完了後に設計と文書を最終整合化し、管理ドキュメントとして成立する状態へ戻す。
- 設計 Reverse（新）: 既存設計書群から依存関係を逆引きし、実装順序（topological sort）と並列実装可能ペアを自動算出する。

## 2. スコープ

### 2.1 含む

- Reverse の処理系を `helix reverse <type>` で拡張し、5 系統の共通入口を持つ。
- 各系統の `Input / Output / 成功条件` を定義し、R0-R4 の既存成果物と RGC への接続を明文化。
- PLAN-004/006/007/009 への接続点を定義し、特に L9-L11 の後段設計整合に対する文脈を追加する。
- `フルバック` を R1-R4（As-Is 復元）と対になる前向き整理フローとして位置づける。

### 2.2 含まない

- 既存 Reverse スキル（reverse-r0/r1/r2/r3/r4/rgc）の具体実装変更。
- API/DB/スキーマの破壊的変更設計。
- 実装コードやテスト追加。
- 本ファイル範囲外の CLI コマンド本体実装。

## 3. 採用方針

### 3.1 5 系統の定義

#### 3.1.1 Code 復元 Reverse（既存）

- 入口: `helix reverse code`
- 観測: 設計書なしの既存コード・設定・運用実態
- 出力: R0→R4 の As-Is 生成物（Evidence / 契約 / ADR仮説 / GAP + Forward）
- 目的: 実装の正しさ検証を前提に、まず現状を仕様化して Forward に接続

#### 3.1.2 バージョンアップ Reverse（新）

- 入口: `helix reverse upgrade`
- 観測: 現行実装・運用制約・既知の障害情報・対象バージョン方針
- 出力: バージョン差分前提書（移行前提、破壊的変更候補、移行ゲート推奨）
- 目的: 将来実装前に「差分の見積もりと受け入れ条件」を作る。

#### 3.1.3 ノーマライゼーション Reverse（新）

- 入口: `helix reverse normalization`
- 観測: 実装 drift（実績と設計文書の不一致箇所）
- 出力: 設計再構成提案（更新必要セクション、依存優先順位、設計更新TODO）
- 目的: 実装差分吸収のための設計自己修正を設計側で先行完了。

#### 3.1.4 フルバック Reverse（新）

- 入口: `helix reverse fullback`
- 観測: `完了実装 + 既存設計 doc + 変更履歴`
- 出力: `management docs` の最終整合版（更新済みの PLAN/D-*/ADR と監査可能な差分履歴）
- 目的: 実装完了後の設計/文書不整合を解消し、L8 受入〜L11 検証側面を再固定する。

#### 3.1.5 設計 Reverse（新）

- 入口: `helix reverse design`
- 観測: `docs/plans/*.md`, `docs/design/D-*.md`, `docs/features/*/D-*.md` などの既存設計書群
- 出力: 依存 DAG（機械可読 YAML / Mermaid 図）、実装順序（topological sort, PLAN ID / D-* 単位）、並列実装可能ペア
- 対応 D-*: `D-DESIGN-DAG`（依存 DAG）, `D-IMPL-ORDER`（実装順序）
- 目的: 既存設計資産から実装順序を抽出し、PLAN-006 からの forward 構築を補完する。

### 3.2 共通基盤としての R0/R4/RGC 再利用

- **R0**（観測収集）を全系統の入り口前提として再利用する。
  - 対象証拠: `evidence map`, 実装ログ, 設計資産, 運用観測
- **R4**（Gap & Routing）を全系統の出力統合点として再利用する。
  - 差分の振り分け先（Forward/Backward）を共通ルールで集約。
- **RGC**（Gap Closure）を最終整合品質チェックとして接続する。
  - 特にフルバックでは、RGC で未解消項目を減らし、再発防止記録を残す。

### 3.3 系統別 I/O・成功条件

- Code 復元 Reverse
  - **Input**: 既存コード、設定、DB スキーマ断片、運用観測
  - **Output**: R1〜R4 成果物、Forward ルーティング
  - **成功条件**: 設計復元観測が明示的な信頼度で接続可能（最低95%トレーサビリティ）

- バージョンアップ Reverse
  - **Input**: 現行設計、移行目標、既知制約、既存依存
  - **Output**: 変更影響一覧、移行シーケンス、互換性判定
  - **成功条件**: 破壊変更を事前分類し、各移行ステップに検証条件が紐付く

- ノーマライゼーション Reverse
  - **Input**: 直近実装、現行設計、差分履歴
  - **Output**: 設計再正規化提案、優先順位付き是正アクション
  - **成功条件**: drift の再発リスクを低減する設計更新計画が定義される

- フルバック Reverse
  - **Input**: 完了実装、既存設計 doc、開発中変更履歴
  - **Output**: 整合済み管理文書（PLAN/ADR/D-API/D-CONTRACT/D-HANDOVER）
  - **成功条件**: 実装状態と文書状態が相互追跡可能で、L8/L9-L11 の受入条件に接続できる

- 設計 Reverse
  - **Input**: 既存設計書群（`docs/plans/*.md`、`docs/design/D-*.md`、`docs/features/*/D-*.md`）
  - **Output**: 依存 DAG（YAML / Mermaid）、実装順序（topological sort、PLAN ID / D-* 単位）、並列実装可能ペア
  - **成功条件**: 依存抽出が監査可能で、循環依存の検知・分割ルールに接続される

### 3.4 CLI `helix reverse <type>` の type 拡張

- 追加型: `code | upgrade | normalization | fullback | design`
- デフォルト継続: `code`
- 既存挙動（`reverse-r*` 系）は内部ルーティングとして吸収し、表示結果に `reverse_type` を明示。
- subcommand 省略時は **`run` alias**（§3.7.1 に準拠）。下記例示はすべて `run` 相当の動作を表す。
- 例:
  - `helix reverse code`（= `helix reverse code run`）
  - `helix reverse upgrade --from <ver> --to <ver>`（= `helix reverse upgrade run --from <ver> --to <ver>`）
  - `helix reverse normalization --target drift`（= `helix reverse normalization run --target drift`）
  - `helix reverse fullback --artifact <path>`（= `helix reverse fullback run --artifact <path>`）
  - `helix reverse design --plans docs/plans/ --design docs/design/ [--output dag.yaml]`（= `helix reverse design run ...`）
  - `helix reverse design --plans docs/plans/ --topological-sort`（= `helix reverse design run --topological-sort ...`）

### 3.5 5 系統ごとの Reverse gate mapping

5 系統の `reverse_type` と `R0/R1/R2/R3/R4/RGC` の対応を明示する。  
各行は `required / optional / skip`、成果物、`coverage / confidence / unknowns` 指標、owner、失敗時リダイレクト先を定義する。

#### 3.5.0 RGC 適用基準（required / optional / skip）

RGC は **Forward の L6/L8 pass 後に実行する後工程**として定義する（即時 `run` には含めない、§3.7.2 参照）。「Forward へ carry する未解消 gap を最終確認する閉鎖品質チェック」として位置づけ、type 別の差は以下の基準で判定する。

- 起動条件: code/normalization は **Forward L6 通過後**、fullback は **Forward L8 受入完了後**、design は **Forward L2 設計凍結後** に手動起動 (`helix reverse <type> rgc`)。
- 自動起動禁止: `helix reverse <type> run` は R0-R4 までで停止し、RGC は別 subcommand で明示起動する。
- skip 系統 (`upgrade`) では RGC を実行しない。代替は §3.5.2 の R4 routing に集約。

| 区分 | 適用条件 | 代替 exit criteria | unknowns 許容量 | Forward への carry 条件 |
|---|---|---|---|---|
| required | 出力が **管理文書として確定保存**される (`code` / `normalization` / `fullback`) | なし | `unresolved gap = 0` を原則。impact=high の open gap は carry 禁止 | resolved/partial のみ carry、open は再実行 |
| optional | 出力が **forward 接続後の追跡で代替可能** (`design`) | `D4-design-routing.yaml` の Forward 接続承認率 ≥ 0.9 | **impact=high の未接続は 0 件が原則**。1 件以上を carry する場合は `P1 deferred-finding` として PM 承認必須、かつ DAG/実装順序出力を `non-authoritative=true` で発行 | 未接続 design は PLAN-006 forward 進行で再評価。P1 carry 中は forward に依存しない |
| skip | 出力が **assessment only**（管理文書 freeze なし、`upgrade`） | `R4` の `routing_to_forward` 完了で代替 | upgrade routing で `freeze_pending=0` 必須 | 全 finding は L2/L3/G3 へ routing。Reverse 内 close 不可 |

skip / optional 適用時も `R4` の `routing_to_forward` には全項目を残し、carry 経路は **deferred-finding 化**して `helix-readiness` で追跡する。

#### 3.5.1 全体方針

- `code` は `R0/R1/R2/R4` を必須で実行する。`R3` は **optional**（PO 仮説検証が必要なときのみ）。`RGC` は Forward の L6/L8 pass 後の後工程として実行する。  
- `upgrade` は `assessment-only` とし、`R0/R1/R2/R3/R4` は評価寄りの実行。`R2/R3` は optional。`RGC` は skip。  
- `normalization` は設計ドリフト補正寄りで、`R1` は skip、`R3` は optional。`RGC` は Forward 後工程。  
- `fullback` は `R0` 起点の独立フローとして実行する。`RGC` は Forward L8 受入完了後の最終整合工程として実施し、残件を明示する。  
- `design` は設計書ベースの導線補助で、`R0/R2/R4` が主経路。`R1` は skip、`R3` は optional、`RGC` は optional。

#### 3.5.2 進捗ゲート定義（`reverse_type × stage`）

| reverse_type | stage | required | output artifact | coverage | confidence | unknowns | owner | fail 先 |
|---|---|---|---|---|---|---|---|---|
| code | R0 | required | `R0-evidence-map.yaml` | 証拠カテゴリ網羅率（code/db/config/ops） | 初回収集再現性スコア | `unknowns` 件数 | legacy | R0 |
| code | R1 | required | `R1-observed-contracts.yaml` | 契約抽出 completeness | 再現テスト適合率 | 不明な型/エンドポイント件数 | legacy | R1 |
| code | R2 | required | `R2-as-is-design.md` | 構成・依存の抽出率 | ADR 仮説妥当性 | 不明要件数 | legacy / TL | R2 |
| code | R3 | optional | `R3-intent-hypotheses.md` | 仮説件数 completeness | 信頼度分布（high/med/low） | unresolved 仮説数 | TL | R3 |
| code | R4 | required | `R4-gap-register.yaml` | gap 種別分類率 | Forward 振り分け合意率 | 未分類 gap | TL | R4 |
| code | RGC | required | `R4-gap-register.md`（閉鎖注記） | open/partial/resolved 集計率 | 再開可能性評価 | 未解消 gap / impact 高 | TL | R4 |
| upgrade | R0 | required | `U0-upgrade-context.yaml` | 調査範囲網羅率（コード/依存/運用） | 観測信頼度 | 未確定観測件数 | TL / SE | R0 |
| upgrade | R1 | required | `U1-upgrade-contracts.yaml` | 互換分類 completeness | 互換判定 confidence | 未分類差分 | TL / SE | R1 |
| upgrade | R2 | optional | `U2-assessment-impact.yaml` | 変更影響の識別率 | 影響推定精度 | migration 候補の unknown | TL / DB | R2 |
| upgrade | R3 | optional | `U3-upgrade-hypotheses.md` | シナリオ採択率 | 想定成功率 | 未確定前提 | TL | R3 |
| upgrade | R4 | required | `U4-upgrade-routing.md` | 変更種別→Forward ルーティング率 | API/DB/D-CONTRACT 分岐精度 | `freeze_pending` 件数 | TL / PM / G2 | R4 |
| upgrade | RGC | skip | — | — | — | — | TL | R4 |
| normalization | R0 | required | `N0-drift-evidence.yaml` | drift 根拠網羅率 | drift 再検出可能性 | 未検証差分 | TL | R0 |
| normalization | R1 | skip | — | — | — | — | TL | R0 |
| normalization | R2 | required | `N2-normalization-drift.yaml` | 仕様ズレ検出率 | 再現性 score | 未特定ズレ | TL / SE | R2 |
| normalization | R3 | optional | `N3-normalization-hypotheses.md` | 仮説優先度 coverage | 変更影響妥当性 | open 仮説 | TL | R3 |
| normalization | R4 | required | `N4-normalization-gap-register.yaml` | 調整予定反映率 | 調整案妥当性 | 未反映項目 | TL | R4 |
| normalization | RGC | required | `N4-normalization-gap-register.yaml`（収束注記） | unresolved 比率低下 | close 判定一致率 | 再発リスク | TL | R4 |
| fullback | R0 | required | `F0-fullback-evidence.yaml` | 入力源（実装/doc/git）網羅率 | 証跡一貫性 | 禁止情報検出数 | TL / SE | R0 |
| fullback | R1 | required | `F1-fullback-contracts.yaml` | doc 差分一致率（PLAN/D-API/D-CONTRACT） | 差分比較 confidence | 未検証差分 | TL | R1 |
| fullback | R2 | required | `F2-fullback-as-is-review.md` | 監査追跡率 | 再現レビュー同意率 | 未確定整合項目 | TL | R2 |
| fullback | R3 | required | `F3-fullback-handover-checklist.yaml` | L8/L11 受入接続率 | 受入前合意率 | 引継ぎ未完了項目 | PM / TL | R3 |
| fullback | R4 | required | `F4-fullback-routing.md` | 統合移行先の completeness | 接続完了確度 | 運用未接続項目 | PM / TL | R4 |
| fullback | RGC | required | `RGC-fullback-closure.md` | unresolved gap 削減率 | 閉鎖証跡一致率 | open gap | TL | R4 |
| design | R0 | required | `D0-design-evidence-map.yaml` | 設計資産収集率 | 抽出可能性 | 抽出不能参照 | TL | R0 |
| design | R1 | skip | — | — | — | — | TL | R0 |
| design | R2 | required | `D2-design-dag.yaml` | 依存抽出率（dep/scc） | DAG 正当性 | 未解決 cycle | TL | R2 |
| design | R3 | optional | `D3-impl-order.yaml` | 実装順序の妥当率 | 並列安全性 | unknown edge | TL | R3 |
| design | R4 | required | `D4-design-routing.yaml` | Forward 接続適合率 | 接続確度 | 未接続設計 | TL | R4 |
| design | RGC | optional | `D4-design-routing.yaml`（受入注記） | 受入未確定率 | 接続承認率 | 未確定未接続 | TL | R4 |

### 3.6 フルバック証跡収集と redaction 境界

#### 3.6.1 input source allowlist

- `.helix/reviews/` / `git log` / `git show <tag>`（履歴）
- `docs/plans/*.md`, `docs/design/D-*.md`, `docs/features/*/D-*`（設計 doc）
- `.helix/` 配下の実施成果物、完成時の実装成果
- `.helix/reverse/` の reverse 成果物

#### 3.6.2 保存禁止情報と raw 取り扱いの確定

**raw 証跡は HELIX 内部に保存しない**。HELIX の管理文書・helix.db・audit state には以下のみ保存する。

| 保存可 | 保存不可 (raw 扱い) |
|---|---|
| `evidence_id` / `source_path` / `source_line_start` / `source_line_end` / `content_hash` / `redacted_summary` / `secret_patterns_hit_count` | 候補本文の raw text、auth credentials raw、PII 平文、runtime log raw、env vars 平文 |

「raw 参照」とは外部 source（git/log/file）への監査付き参照のみを意味し、HELIX 内に raw を保持しない。具体的な保存禁止情報は以下:

- `auth credentials`（`token`/`password`/`secret`）  
- `PII`（個人情報・ユーザ識別情報）  
- `runtime log raw`（機密本文・フルスタックログ）  
- `env vars`（未匿名化環境変数）  

#### 3.6.3 redaction 手順

- `PLAN-007 §3.5.2` と同等の redaction 方針を採用。
- `cli/lib/deferred_findings.py` の `SECRET_EXTRA_PATTERNS` を `redact_value` と同時適用する。
- 対象フィールド: `title` / `body` / `recommendation` / `evidence.summary` / `source_hint`  
- `auth` / `env` / `PII` を含む候補は redaction 完了後に `security_review_required: true` を付与して保存。
- `auth/env/PII` を含む証跡がある場合は保存時点で `security review required` を明記し、PM + TL で承認後に次段へ進む。

#### 3.6.4 retention と削除ジョブ

- retention: 180 日
- 180 日経過後に `archived` 化。`archived` からは監査参照のみ許可。
- 削除ジョブ: `cli/helix-scheduler` の月次ジョブ `audit-retention: fullback` で次回起点削除を実行。

#### 3.6.5 閲覧権限

HELIX 内部には redaction 済みのみが存在するため、各ロールの閲覧範囲は HELIX 管理データに対して定義する。「raw proxy 参照」とは §3.6.6 の監査トークン経由で **外部 source へ一時アクセスする** ことを指す。HELIX 内部には raw を持たない。

- PM: 全 redaction 済みデータ閲覧 + `raw proxy 参照` 許可（監査ログ記録必須）  
- TL: redaction 済み閲覧 + `raw proxy 参照` 許可（`pending/triaged/adopted` のみ、監査ログ記録必須）  
- SE: `adopted` または `resolved` の redaction 済みのみ閲覧。raw proxy 参照不可。  
- DBA: メタ情報（`evidence_id` / `content_hash` / `secret_patterns_hit_count`）のみ。redacted body も raw proxy も不可。

#### 3.6.6 監査参照形式

- HELIX は raw を保持しないため、外部 source への参照のみが「raw proxy」となる。
- raw proxy 参照は監査イベント `audit.evidence_view` を発行し、証跡キー（`evidence_id` + `source_path` + `line_range`）で追跡。
- raw proxy 参照は 72 時間 TTL の監査 token を発行し、TTL 経過後は token 無効化（`audit.evidence_token_revoked` を記録）。
- export 制約（HELIX 内部に raw を持たないため、`redacted=false` export は **存在しない**）:
  - すべての export は **redacted 済みデータ限定** (`redacted=true` のみ)
  - PM/TL/SE すべてのロールで raw / 平文 secret / 平文 PII の export は禁止
  - export 先は HELIX リポジトリ内 `.helix/audit/exports/` に限定（外部送信は別途 PM 承認 + 暗号化必須）
  - PM が外部 source の raw を確認する必要がある場合は §3.6.6 の raw proxy 参照（72h TTL audit token）を経由するのみで、HELIX 内への複製・export は禁止

### 3.7 CLI grammar（互換ルール）

既存実行形式は維持し、新規構文を追加する。

```text
helix reverse <type> [<stage|run|rgc|status|retry>] [--invalidate-forward]
helix reverse <type> status [--json]
helix reverse <type> retry [<stage>|--last-failed]
helix reverse <type> rgc           # §3.5.0 の起動条件を満たした後の後工程
```

`type`: `code|upgrade|normalization|fullback|design`

#### 3.7.1 デフォルト挙動の固定

- `helix reverse <type>` (subcommand 省略) は **`helix reverse <type> run` の alias** として動作する。usage error にはしない。  
- `helix reverse code` は既存挙動を維持し `helix reverse code run` と同等。  
- §3.4 の例示 (`helix reverse upgrade --from <ver> --to <ver>` など) は **すべて `run` alias** として読む。

#### 3.7.1a option 配置と parse precedence

subcommand 省略時の type 別 option (例: `--from`, `--to`, `--target`, `--artifact`, `--plans`, `--design`, `--output`, `--topological-sort`) は内部的に `run` の option として吸収する。L3 で確定する parse precedence は以下:

1. `helix reverse <type> <subcommand> <options>` を **正規形** とする
2. `helix reverse <type> <options>` (subcommand 省略形) は parser が `<subcommand>=run` を補完してから option を解釈する
3. グローバル option (`--invalidate-forward`, `--json`, `--last-failed`) は subcommand の後に配置するのを必須とする
4. type 別 option (`--from`, `--target` など) は subcommand の後・グローバル option の前に配置
5. `--invalidate-forward` は `code` + `run/retry` 限定。他 type / 他 subcommand に付与した場合は parse error
6. `--last-failed` は `retry` 限定。他 subcommand では parse error

option schema 詳細 (各 type で受け付ける option 列挙、必須/任意、依存関係) は L3 で D-CONTRACT として確定する。

#### 3.7.2 subcommand 別の挙動

- `run`: 型ごとに対応した **R0-R4 stage のみ**実行。**RGC は含まない**（§3.5.0 参照）。`fullback` は `R0` 起点の独立フローとして実行。  
- `rgc`: §3.5.0 の起動条件を満たした後の後工程として明示起動する。`run` 自動連鎖はしない。  
- `status`: type ごとの個別ステータス表示。既存の `helix reverse status` は `helix reverse code status` の alias。  
- `retry`: 指定 stage の再実行（`code` のみ `--invalidate-forward` 有効）。  
  - `code`: R2/R3/R4 で失敗時に forward gate invalidation 可。  
  - `upgrade/normalization/design/fullback`: 再実行は `forward invalidation` なし。  
- `--invalidate-forward` は `code` のみ実行時に既存挙動を維持し、`R2|R3|R4` 成功時に G2-G7 を invalidated にする。  

#### 3.7.3 既存互換

- `helix reverse R0|R1|R2|R3|R4` は内部で `helix reverse code <stage>` と同等扱い。  
- `helix reverse status` は `helix reverse code status` と同等。  
- `helix reverse rgc` は `helix reverse code RGC` と同等。  

### 3.8 upgrade Reverse の責務境界

- `upgrade` Reverse の成果物は **assessment only** とし、実装確定やロック（migration/rollback）を行わない。  
- API/DB/D-CONTRACT の破壊的変更疑義が高い場合は `R4` で `G3` 向け routing / L2/L3 へ回し、`routing_to_forward` に記録。  
- migration/rollback 判断は `L2/L3/G3` の後続設計 gate でのみ決定する。  
- `fullback` の最終文書更新は `L8` 後続受入で `L9-L11` を接続し、設計 Freeze は Reverse で行わない。

### 3.9 PLAN-009 参照の解消

- `docs/plans/PLAN-009-run-phase-l9-l11.md` へ統一した。
- placeholder 表記は本バージョンで解消し、暫定表示は残さない。

## 4. 関連 PLAN

- `docs/plans/PLAN-004-pm-reward-design.md`
  - `L1 / 設計前提` と `G2/G3/G4 の受け渡し条件` を前提として反映。
- `docs/plans/PLAN-006-upstream-meta-phase.md`
  - メタフェーズにおける前提解像度とドキュメント依存管理を継承。
  - `設計 Reverse` は PLAN-006 の forward 構築を reverse 補完し、`D-DESIGN-DAG / D-IMPL-ORDER` を相互参照。
- `docs/plans/PLAN-007-scrum-multitype-trigger.md`
  - 差し込み条件と Q5 トリガーの思想を、5 系統の例外処理・遅延処理に接続。
- `docs/plans/PLAN-010-verification-agent.md`
  - 設計 Reverse の依存 DAG から `cross-validation` 対象ペアを自動列挙する連携を追加。
- `docs/plans/PLAN-009-run-phase-l9-l11.md`
  - フルバック後段（デプロイ後工程）の接続先として参照。

## 5. リスク

- フルバック工数膨張
  - 対策: 実施対象を `Sprint` 単位に分割し、I/O と成功条件を `exit criteria` 化。
- バージョンアップ Reverse の影響面見落とし
  - 対策: 互換性カテゴリ（互換/保守/破壊）を前提評価に必須化し、移行シナリオを分離記録。
- 5 系統運用時の責務境界混線
  - 対策: 各 type の入出力と最終成果物を固定し、R0-R4-RGC の共通出口で再統合。RGC 適用基準は §3.5.0 で type 別に分岐。
- 逆引き誤判定
  - 対策: 人手レビュー（docs/verification）と PO 依存前提の明示的再確認を強制。
- 設計 Reverse 特有: 既存設計書の記述揺れによる DAG 誤検出
  - 対策: 参照表現の同義語正規化、低信頼度検出の再確認ループを追加。
- 設計 Reverse 特有: 循環依存の検出と解消手順不足
  - 対策: SCC 分解手順と再実行順序定義を D-IMPL-ORDER に明示。
- 設計 Reverse 特有: 頻繁な再生成コスト
  - 対策: 差分再生成、キャッシュ、再生成頻度ガードを設計運用として明文化。

## 6. Sprint 計画概要（L1〜L4）

### Sprint L1

- 5 系統定義の最終確定
- `helix reverse <type>` 入力/出力仕様の固定
- 既存 `workflow/reverse-analysis` との接続ポリシー更新

### Sprint L2

- バージョンアップ Reverse とノーマライゼーション Reverse の観測テンプレート整備
- 設計 Reverse の設計書抽出ルール（識別子正規化/同義語）整備

### Sprint L3

- フルバック Reverse の成功条件検証（実装完了前提）
- 進捗/例外の監査ログ設計
- PLAN-004/006/007/010 への接続イベント定義

### Sprint L4

- 5 系統を通した `L1〜L11` 受入連携レビュー
- 運用ガイドラインと実施可否境界の確定

## 7. 改訂履歴

| 日付 | バージョン | 変更内容 | 変更者 |
| --- | --- | --- | --- |
| 2026-05-01 | v3.3 | TL 第3ラウンド P1 矛盾解消: §3.5.1 で `code` の R3 を **optional**（PO 仮説検証時のみ）に修正し §3.5.2 表と整合 (P1)、§3.5.0 / §3.7.2 で `run` は R0-R4 のみ実行、**RGC は Forward L6/L8 pass 後の後工程として `helix reverse <type> rgc` で明示起動**と分離 (P1)、§3.6.6 で `redacted=false` export を撤廃し全 export を redacted 済み限定に統一、PM の raw 確認は 72h TTL audit token 経由の raw proxy 参照のみ (P1)。 | PM (Opus) |
| 2026-05-01 | v3.2 | TL 第2ラウンド finding 解消: PLAN registry title を「Reverse 5 系統化 (Code/Upgrade/Normalization/Fullback/Design)」に統一 (P2)、§3.5.0 design RGC optional の high-impact 未接続を 0 件原則 + 例外時 P1 deferred-finding + non-authoritative 出力に強化 (P2)、§3.7.1a で type 別 option の配置と parse precedence を明文化 (P3)。 | PM (Opus) |
| 2026-05-01 | v3.1 | TL レビュー新 finding 解消: §3.5.0 RGC 適用基準 (required/optional/skip) と代替 exit criteria を新章追加 (P2)、§3.5 タイトルと §4/§5 の 4→5 系統表記統一 (P2)、§3.6.2/§3.6.5/§3.6.6 で raw 取り扱いを「HELIX 内部に保存しない、外部 source への監査付き参照のみ」に固定 (P1)、§3.7.1 で `helix reverse <type>` 単体を `run` alias と明文化し §3.4 例示と一致させる (P3)。 | PM (Opus) |
| 2026-05-01 | v3 | §3.5 〜 §3.9 を追加し、5 系統別 gate mapping、fullback redaction とセキュリティ境界、CLI 互換 grammar、upgrade assessment boundary、および PLAN-009 正規参照を明文化。 | Docs (Codex) |
| 2026-04-30 | v1 | Reverse 4 系統（Code/Upgrade/Normalization/Fullback）定義を追加し、フルバック Reverse を L8↔L11 区間の管理整合プロセスとして定義。 | Docs (Codex) |
| 2026-05-01 | v2 | 設計 Reverse を第5系統として追加。PLAN-006 補完関係、PLAN-010 連携、CLI `design` type、および `D-DESIGN-DAG / D-IMPL-ORDER` を明示。 | Docs (Codex) |
