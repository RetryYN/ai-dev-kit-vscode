---
adr_id: ADR-044
title: "HELIX-workflows V2 dogfooding 方式設計 snapshot"
status: Proposed
author: PM
created: 2026-05-27
owner: PM
parent_plan: L4-helix-workflows-方式設計plan
process_layer: L4
related_design: docs/v2/L4-architecture/helix-workflows-system-architecture.md
industry_standards:
  - IEEE 42010:2022
---

# ADR-044: HELIX-workflows V2 方式設計 snapshot

## Context

この ADR は、HELIX-workflows V2 の dogfooding を L4 基本設計で採択するための方式設計 snapshot を、L4 PLAN の中核成果物として本文として確定するためのもの。
対象は L3 で固定された業務要件を、L4 方式設計・監査・test 設計・handover の実行可能な連携として一度に凍結し、後続 L9 総合テストと受入ゲートで参照できる状態にすること。

### 1.1 L4 における背景

HELIX-workflows V2 は、L4 基本設計で方式の凍結ポイントを明示しないまま dogfooding を進めると、parent design を直接変更せずに運用を始める判断が散逸するリスクが高い。
このため Step 4 では、L4 方式の全体意思決定を ADR snapshot として本体化し、`docs/v2/L4-architecture/helix-workflows-system-architecture.md` と同一スコープで使えるようにする。

既に決まっている前提は以下。

1. L3 条件取得 (commit 42a20c9) により BR 条件は dogfooding 実行可能レベルに達している。
2. `docs/plans/L3/` 系は既に BR-01 〜 BR-12 の要求を満たした状態で、L4 への受け渡し条件を満たしている。
3. V1 PLAN-NNN-slug 体系から V2 方式体系へ移行済み (2026-05-24, commit 35a901c)。
4. L4 PLAN は `L4-helix-workflows-方式設計plan` を起点に Step 2/3/4/6 が分離されている。
5. L4 → L9 pair の実装/監査/レビュー証跡は同一 snapshot で再現できる必要がある。

### 1.2 方式設計 snapshot が必要な理由

HELIX の運用では parent design の accept 状態が高価であり、accepted parent design を壊さずに新規判断を反映するには ADR 併存が必要である。
過去の事例として以下がある。

1. ADR-021 で Web 検索ガードレールを snapshot 化し、設計の追加要件を受け口設計の破壊 without break で運用。
2. ADR-022 で agent slot framework を導入し、PMO 構造へ追加しつつ既存 parent design を維持。
3. ADR-023/024 で gate staged adoption や continueOnBlock ループを snapshot 化し、parent design 凍結を尊重。
4. ADR-041 では drift 分類を追加しつつ前提を上位 ADR に閉じた。
5. ADR-043 で mode enum 追加時の direct edit を回避し ADR 併存で freeze break を回避。

これらと同様、ADR-044 で 4 方式判断を本体化することで、accepted 設計の安定性を守りながら V2 dogfooding を継続する。

### 1.3 事業要求との接続

本 ADR は `docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md` の決定入力を、L4 の実装前提に変換する。
L3 では `G3 conditional` を満たすことを前提に、STEP 進行を決める条件が整理済みである。

要求接続は下表。

| 要求領域 | L3 由来 | L4 snapshot での扱い |
|---|---|---|
| BR-09 | parent design freeze break 回避 | snapshot ADR で併存方針を固定 |
| BR-10 | existing 資産整備 | skills 層の独立進化で段階移行 |
| BR-11 | command / mode 安定化 | 実装層と知識層の責務分離で対応 |
| BR-12 | ratchet / audit trace | 永続化 4 種 + hook/doctor 2 段構成で固定 |
| FR-01 | CLI 運用再現性 | helix.db と YAML 並列永続化 |
| FR-08 | session handover 継続 | `.helix/handover/` を受け渡し基準に固定 |
| NFR-01 | 開発速度 | pre-commit fast lane を維持 |
| NFR-05 | 監査速度 | CI deep lane で深掘り検証 |
| NFR-07 | 読解性 | `.helix/audit/*.yaml` を追加の可視化資産化 |

### 1.4 証跡保存の原則

本 snapshot では、設計判断を以下の 3 ルートで同時に保存する。

- 設計ルート: `docs/v2/L4-architecture/helix-workflows-system-architecture.md`
- ADR ルート: `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`
- 実装ルート: `cli/` 内の実装と `docs/v2/L9-test-design/helix-workflows-system-test-design.md` の整合

加えて、失敗 trace と handover state は `.helix/audit/*.yaml` と `.helix/handover/*.json` によって保全される。

### 1.5 3 主要原則

1. accepted parent design は原則不変更。
2. 追加判断は ADR snapshot 併存または親 doc の計画的更新で明文化。
3. 監査設計は `implementation_status` を付与し、BR-RULE-09 で要求される trace 可能性を担保。

### 1.6 影響範囲

本 ADR は L4 architecture と L9 system test design の間で参照され、将来の L5/ L6 への展開時にも `implementation_status` 列の継承条件として参照する。
`docs/plans/L4/L4-helix-workflows-方式設計plan.md` の Step 4 に直接紐づくため、未反映状態は Step 6 進行条件として停止理由になる。

## Decision

以下の 4 大方式判断を採択する。
全 Decision で実装主張には `implementation_status` を明記し、BR-RULE-09 要件を満たす。

### Decision-1: 三層構造（HELIX-workflows / cli / skills）

#### implementation_status

`implemented`

#### 1.1 選択構造

- HELIX-workflows レイヤ
  - 正本文書、workflow 定義、工程ルールの権威 source
  - `HELIX-workflows/` 配下に保管
  - 設計方針と V-model pair freeze の根拠を保持
- cli レイヤ
  - Bash + Python 実装、ローカル実行と CI 実行の実体
  - コマンド、hook、doctor、plan などの運用実装
  - `cli/` 配下に実装
- skills レイヤ
  - 116 以上の知識資産、role とレビュー手順の再利用拠点
  - `skills/` 配下で学習・運用・監査知識を拡張

#### 1.2 採用理由

この 3 層は、正本と実装を混在しない明確な責務分離を提供する。
正本（HELIX-workflows）が頻度高く更新される一方、実装（cli）は挙動の再現性が求められる。
skills は運用知識を独立進化させる資産として、workflow 更新と同時に壊れない。

#### 1.3 実装要件

- 3 層の起点を plan_validator, helix doctor, pmo 観点で明示。
- 観点上位:
  - 正本参照の明示は `related_design` と `parent_plan` 参照で明快化。
  - cli 実装変更時は skills 指南と整合することを必須化。
- 監査時は層横断で一貫 trace を採る。
  - 設計根拠: ADR
  - 実装実体: cli
  - 運用知識: skills

#### 1.4 L4 §1 適用

L4 §1 ではこの構造を導入前提とし、文書名/コマンド名/運用指標をこの 3 層で解釈する。
STEP 2 の architecture doc はこの層図を採点表として持ち、Step 4 は本 ADR に収束する。

#### 1.5 期待効果

1. 正本 drift の抑制
2. 実装と knowledge の独立更新
3. 監査時の説明責任分担明確化
4. cross-layer 干渉の最小化

### Decision-2: 永続化 4 種を責務分離で導入

#### implementation_status

`implemented`

#### 2.1 導入対象

4 種の永続化を明示し、それぞれを役割別に運用する。

| 種別 | 格納 | 役割 | 保持期間方針 | 主要用途 |
|---|---|---|---|---|
| helix.db | SQLite store | PLAN / 実行履歴 / audit event | 長期 | 機械判定と fail-close 判定 |
| .helix/audit/*.yaml | YAML | review evidence / failure trace / baseline | 中期〜長期 | 人間可読の監査根拠 |
| git history | Git 履歴 | PLAN / ADR / 設計 doc の不変監査 | 永続 | 変更起点と承認証跡 |
| .helix/handover/*.json | JSON | ownership / sprint / status 受け渡し | セッション間短期〜中期 | 再開可能性と引継ぎ整合 |

#### 2.2 設計上の理由

単一永続化では、監査時の説明と再現の両立が難しい。
helix.db は機械検証向けで正確だが、人的レビューには YAML が必要。
git history は不変性に強いが runtime 更新の粒度は粗い。
handover は状態を実行時に扱うが、履歴として不十分。
したがって 4 種は補完関係で導入する。

#### 2.3 L4 §1.2 / §5.3 / §6.2 適合

- L4 §1.2: plan history と手続き証跡を DB + Git + YAML で分離する方針。
- L4 §5.3: audit event の階層化保存を明確化。
- L4 §6.2: handover 併走時の受け渡し再現性を YAML + JSON で担保。

#### 2.4 保存・参照ルール

1. 実装判定で使う値は helix.db を一次真実源として扱う。
2. 異常判定の説明と復旧手順は YAML に保存する。
3. 重要決定文書は git 履歴に反映し、ADR と PLAN の同一 commit 観点を保つ。
4. handover は ownership と state を最短で更新し、再開時の曖昧性を防ぐ。

#### 2.5 監査フロー

1. `pre-commit` または `helix doctor` は runtime 判定を行い、`helix.db` へ結果を記録。
2. 監査 evidence は `implementation_status` と合わせて `.helix/audit/*.yaml` に保存。
3. 重大差分は handover block/unblock 情報へ昇格。

#### 2.6 運用上の制約

- YAML は人間編集で保守しやすいが、破損時は DB 再現手順を優先。
- git history は不可逆性を担保するが、構造化判定には向かないため DB と併用必須。
- handover JSON は実行時一時性を持つが、L4 設計決定の唯一保管源にはしない。

### Decision-3: BR-12 ratchet 機構（baseline YAML + read/write CLI + 二段 hook + 違反永続化）

#### implementation_status

`partial`

#### 3.1 ratchet 方針

balance_ratio を 1.0 未満へ下げない ratchet を、段階的に適用する。
ベースラインとして `.helix/audit/balance-ratio-baseline.yaml` を使用し、更新は `--check-changeprop --update` に限定する。
read-only 判定は `helix doctor --check-changeprop` で定義し、開発者体験と監査性能を両立する。

#### 3.2 CLI 契約

2 種を運用する。

- `helix doctor --check-changeprop`
  - read-only mode
  - 速度優先で pre-commit から呼び出し
  - 見込み違反時は diff を返し commit から阻止

- `helix doctor --check-changeprop --update`
  - write mode
  - baseline の再取得または明示更新のみ許可
- `balance_ratio` の更新タイミングは plan carry-in/out 時を優先

#### 3.3 hook 二段構成

| Hook | 目的 | 目標時間 | 判定 | 用途 |
|---|---|---:|---|---|
| pre-commit fast | 初期検知 | 0.5-2 sec | fail-close 推奨 | 開発者ローカルでの防波堤 |
| CI deep | 詳細検知 | 20-120 sec | fail-close 必須 | policy / parser / trace 一貫性 |

#### 3.4 違反永続化

違反は `.helix/audit/changeprop-violations.yaml` に時系列で追記する。
時系列保存をすることで次条件を満たす。

1. 再試行可能条件の明示
2. 前回違反原因の再現
3. plan 進行への影響範囲の可視化
4. pmo-sonnet 監査と doc-reviewer の補完検証

#### 3.5 導入効果

- ローカル開発をブロックしすぎない
- CI での厳密検証を確保
- 観測可能性のある失敗履歴を維持
- BR-12 の ratchet 証跡を audit レイヤで一元化

#### 3.6 まだ残る課題

現時点では ratchet 自体は実装の一部が別 PLAN に依存し、完全自動化は Step 2-3 に carry。
特に `check-changeprop` parser 直系の安定度と例外パスは、CLI 実装変更の完了と同期して検証する。

### Decision-4: 二重/三重 audit pattern（tl-advisor + pmo-sonnet + doc-reviewer）

#### implementation_status

`implemented`

#### 4.1 監査役割

- tl-advisor (Codex gpt-5.5 high)
  - 技術判断と adversarial check
  - L4 決定の整合性、plan drift、counterfactual を検証
- pmo-sonnet (Claude Sonnet 4.6 medium)
  - 数値整合、構造整合、表現の一貫性を検査
  - balance_ratio や ST mapping の観測を行う
- doc-reviewer (Codex gpt-5.5 high)
  - ドキュメント品質を 4 視点で検査
  - Correctness / Completeness / Consistency / Clarity

#### 4.2 並列召喚プロトコル

- 監査プロンプトは rollout JSONL bypass で SUMMARY 省略を回避
- 3 役割の出力を決定前に比較 merge
- 矛盾があれば `intermediate audit note` として Step 4 carry に保留
- fail-close 条件:
  - 技術 drift は tl-advisor で止める
  - 数値 drift は pmo-sonnet で止める
  - 設計表現 drift は doc-reviewer で止める

#### 4.3 運用理由

1 層だけの監査では検出不能な drift があるため、責務分離が必要。
2026-05-26 session3 の BR-12 ratchet self-audit 逸脱は、single role では見落としが発生し、三者並列で発見できたことが実績としてある。
この実績を一般化し、L4 Step 6 以降でも必須化する。

#### 4.4 L4 §6 適用

- Step 5 では tl-advisor を先行実行し、技術 drift と parent design 参照の破綻を排除。
- Step 6 は pmo-sonnet + doc-reviewer を統合実行し、`g4` 判定の証拠を追加。
- 監査結果は ADR へ反映し、`implementation_status` が proposal → partial → implemented へ遷移する条件を記載。

#### 4.5 期待される利点

- 単一監査での盲点削減
- 数値・技術・文書品質を同一 sprint 内で固定
- pmo-sonnet / doc-reviewer の監査差分が CI 監査と相互検証可能

## Consequences

### 5.1 ポジティブ効果

#### 5.1.1 設計側

- L4 snapshot が親設計の freeze break を避けながら運用上必要な意思決定を併記できる。
- PLAN と ADR の関係が可観測となり、受入監査で説明コストが減る。
- `docs/v2/L4-architecture/helix-workflows-system-architecture.md` が snapshot と同一主張で凍結されるため、後続 L4-L9 参照時の再解釈コストが下がる。

#### 5.1.2 運用側

- dogfooding の自己監査が現実的に実行可能（fast lane + deep lane）。
- handover 受け渡し時に受け側が意思決定履歴と違反履歴を一目で追える。
- 監査レポートの比較可能性が増し、運用品質の横断評価が容易になる。

#### 5.1.3 事業側

- 既存運用への導入障害を小さくしつつ、採用 project 向けに再利用しやすい ADR snapshot を得る。
- `implementation_status` と compliance table の存在が、運用監査時の説明時間を短縮。

### 5.2 ネガティブ効果

#### 5.2.1 文書負荷

- ADR 4 件分（ここに含まれる 4 Decision/4 Alternatives/Compliance）を継続維持するコストが増加する。
- Step 4 本体化後、関連 L4 / L9 / Plan 更新時に同期工数が増える。

#### 5.2.2 監査時間

- 二重/三重監査構成により、レビュー時間が増加する。
- pmo-sonnet と doc-reviewer の再走回数分、作業フローが長期化しやすい。

#### 5.2.3 実装整合工数

- 実装・YAML・DB の 3 形式更新が必要で、更新漏れリスクに対するチェック工数が発生する。
- 旧運用（単一記録）から移行する場合、移行中は認知負荷が上がる。

### 5.3 リスク

#### 5.3.1 PLAN ⊃ ADR 併存の破綻

- 設計が PLAN 側で更新され ADR 側で遅れると、監査整合性が崩れる。
- 予防として `helix doctor check_plan_adr_snapshot` を fail-close 化し、差分更新時にブロック。

#### 5.3.2 fail-close 誤検知リスク

- CI deep lane が厳密化しすぎた場合、実装者の再試行コストが急増する可能性。
- baseline 更新ルールと差分説明ルールを明確にして、運用上の誤検知を最小化する。

#### 5.3.3 監査役割依存の単点障害

- 監査 3 役割のいずれかが遅延した場合、G4 が遅れる。
- 例外時は fallback として既存ログを参照し、役割結果の再実行まで進行抑制を維持する。

### 5.4 リスク軽減アクション

1. `.helix/audit/*` と helix.db の二重保存で drift の復元性を確保。
2. 違反履歴に retry 条件を明記し、再実行の再現性を担保。
3. doc-reviewer の evidence 列に `implementation_status` を必須化し、受入時の trace 断絶を防ぐ。
4. 変更可能性の高い項目には受入条件と例外条件を Plan へ carry 化。

## Alternatives

### Alt-1: 永続化を helix.db 一元化（YAML 廃止）

#### Alt-1 判定

### 1.1 主張

YAML を廃止し、`.helix/audit/*.yaml` と handover 情報をすべて helix.db のテーブルへまとめる。

#### 1.2 反対理由

- YAML の可読性が失われ、reviewer が差分レビューしづらくなる。
- `.helix/audit/*.yaml` の手動追補が困難になり、incident 解析の初速が落ちる。
- git diff が難解化し、PR 上での trace 確認工数が増える。

#### 1.3 追加検証

- 3 層構造の観点で、skills や運用ハンドブックからの参照が DB 直 SQL 依存に寄りすぎる。
- 実行時事故時に "人間が原因を説明する速度" が落ちる。
- よって採択しない。

### Alt-2: ratchet を Python 単発 script + CI 統合のみ

#### Alt-2 判定

### 2.1 主張

`scripts/check_ratchet.py` を実装し、CI だけで periodic check を行う。

#### 2.2 反対理由

- pre-commit fast lane が無く、ローカルでの early fail ができない。
- 開発者が違反を CI で初検知し、コミット反復コストが増える。
- advisory→fail-close への移行が難しいため、運用現実性が低い。

#### 2.3 比較結果

速度面: ローカル即時フィードバックがない  
再現面: CI 再実行でのコスト増  
運用面: チーム習熟コスト増加  
以上より採択しない。

### Alt-3: tl-advisor のみで audit を完結

#### Alt-3 判定

### 3.1 主張

tl-advisor のみで構造+数値+文書監査を終了させる。

#### 3.2 反対理由

- pmo-sonnet 型の数値整合検証を担保できない。
- doc-reviewer 型の文書品質検証が欠落し、G4 で要求される品質指標に沿いにくい。
- 2026-05-26 session3 で実際に発生した drift（balance_ratio header レベル drift）を本 ADR で再現せず検知できない事例がある。

#### 3.3 判定

単点監査は速度は高いが、検出率が低い。三者並列を継続採用する。

### Alt-4: 二層構造（HELIX-workflows + cli、skills 統合）

#### Alt-4 判定

### 4.1 主張

skills を HELIX-workflows 配下へ統合し、3 層を 2 層化する。

#### 4.2 反対理由

- 既存 116+ skill の高速追加が遅延する。
- 専門知識更新と workflow 正本更新が干渉しやすい。
- skill retrofit や god-writing 追加時に親 doc の再設計が伴いやすい。

#### 4.3 判定

2 層は短期的にはシンプルに見えるが、長期運用品質と独立開発速度を損なうため採択しない。

### Alt-5: V1 PLAN-NNN-slug 体系に戻して snapshot を継続しない

#### Alt-5 判定

### 5.1 主張

既存 V1 構成に従い、PLAN のみを更新し ADR 併存を止める。

### 5.2 反対理由

- V1 は参照体系の移行を完了した後であり、製本/継続運用には不適合。
- 今回の Step 4 本体化は V2 plan_validator / handover / review 方針を前提としており、V1 戻しは不整合を生む。

### 5.3 判定

V1 戻しは非推奨。V2 併存運用を継続する。
scope 外、本 ADR では非採択。carry: 後続 ADR で扱う。

## Compliance

L4 §0.1 industry standards alignment と pair で運用する。

### 6.1 業界標準対応表

| 標準 / 項目 | 対応範囲 | 参照 ADR 章 | 監査方法 |
|---|---|---|---|
| IEEE 42010:2022 | Architecture view と concern 対応 | Decision-1, Decision-2, Decision-3, Decision-4 | viewpoint × view × concern の 3 軸で mapping |
| arc42 | Architecture Decision と Block/Runtime/Crosscutting | Decision-1, Decision-2, Decision-3 | Decision を arc42 §5/6/8 に対応付け、Compliance section で明文化 |
| C4 model | コンテナ/コンポーネント/コード対応 | Decision-1, Decision-2 | Decision-1 で Container Diagram、Decision-2 で Component、コード化は L5 へ引き継ぎ |
| BR-RULE-09 | implementation_status 必須 | 全 Decision | 各 Decision 見出し内 `implementation_status` を追加 |

### 6.2 IEEE 42010:2022 対応 map

| Viewpoint | Concern | L4 section | L9 対応 |
|---|---|---|---|
| Process governance | BR-09〜12 の監査安定性 | Decision-2, Decision-3 | L9 ST-1, ST-4 |
| Operational governance | pre-commit/CI 二段、handover 安定性 | Decision-3, Decision-4 | L9 ST-4, ST-6 |
| Information governance | 受入・監査根拠管理 | Context, Decision-2, Compliance | L9 ST-7 |
| Tooling governance | CLI/skills 設計分離 | Decision-1, Decision-4 | L9 ST-3, ST-5 |
| Project governance | PLAN/ADR 併存運用 | Context, Consequences, Alt-1 | L9 ST-2, ST-7 |

### 6.3 arc42 対応 map

| arc42 section | 本 ADR 対応決定 | 根拠 | 証跡 |
|---|---|---|---|
| 5 Building Block View | Decision-1 | 3 層構造 | ADR 本文 §Decision-1 と architecture doc |
| 6 Runtime View | Decision-3 | ratchet/hook/doctor 実行フロー | ADR 本文 §Decision-3 と CLI docs |
| 8 Crosscutting Concepts | Decision-2, Decision-4 | 永続化分離と監査並列化 | ADR 本文 §Decision-2/4 |
| 9 Design Decisions | 全 Decision / Alt | 方式採否の比較 | 本 ADR 全文 |

### 6.4 C4 model 対応 map

| C4 level | 主要要素 | 本 ADR 適用 | 実装先 |
|---|---|---|---|
| Level 1 Context | HELIX-workflows / cli / skills 系の境界 | Decision-1 | HELIX-workflows, cli, skills |
| Level 2 Container | 永続化 4 種 / handover | Decision-2 | helix.db, `.helix/audit`, git, handover |
| Level 3 Component | ratchet checker / doctor / hook | Decision-3 | cli 監査コンポーネント |
| Level 4 Code | review pattern / policy 実装 | Decision-4 | 監査実行スクリプト、gating 設定 |

### 6.5 BR-RULE-09 実装主張管理

以下の 4 Decision で実装主張を明示し、`implementation_status` を付与。

| Decision | implementation_status | 更新対象 | 対応 evidence |
|---|---|---|---|
| Decision-1 | implemented | layered architecture | architecture doc + ADR |
| Decision-2 | implemented | persistence split | persistence mapping table + audit schema |
| Decision-3 | partial | ratchet 2 段 hook + baseline 更新 | doctor command + baseline/violations yaml |
| Decision-4 | implemented | audit role 分担 | Step 5/6 audit chain |

### 6.6 Plan/ADR 併存ガバナンス

`PLAN-044` と本 ADR は次条件で併存し、互いに更新し続ける。

1. Step 4/5/6 で ADR を更新した場合、PLAN の carry note を必ず更新。
2. PLAN 側の依存変更時は `docs/plans/...` から ADR 対応欄へ反映。
3. acceptance 条件:
   - Decision 1-4 の implementation_status が更新されていること
   - Compliance table が更新されていること
   - Step 4 自体が proposed 状態であること（accepted は Step 6 以降）

### 6.7 L4 §1-§7 対応チェック

| L4 section | 本 ADR 対応 | 実装/監査状態 |
|---|---|---|
| §1 | 前提・方針 | Context に反映 |
| §2 | 構造定義 | Decision-1 で実体化 |
| §3 | 監査基盤 | Decision-2/3 で保存 |
| §4 | BR-12 ratchet | Decision-3 で運用 |
| §5 | サブエージェント/監査 | Decision-4 で実装 |
| §6 | plan_validator/evidence 連携 | Compliance と Alternatives で補完 |
| §7 | 導入条件/効果 | Consequences と Alternatives で記載 |

### 6.8 追加証跡

必要最小の補足として、関連コマンドと関連ファイルを以下に固定する。

| タイプ | コマンド / ファイル | 用途 |
|---|---|---|
| ドキュメント | docs/v2/L4-architecture/helix-workflows-system-architecture.md | L4 §1-§8 との trace |
| ドキュメント | docs/v2/L9-test-design/helix-workflows-system-test-design.md | L9 ST 対応 trace |
| 実装 | cli/lib/doctor/check_changeprop.py (該当実装を持つ可能性) | BR-12 実装責務 |
| audit | .helix/audit/balance-ratio-baseline.yaml | baseline source |
| audit | .helix/audit/changeprop-violations.yaml | 監査違反履歴 |
| 実行状態 | .helix/handover | ownership / sprint / status |

数値基準参照: BR 12, FR 16, NFR 27, AC 57, OT 12

## 関連 ADR 参照

### 7.1 継続参照

- ADR-021  Web search guardrail（snapshot）
- ADR-022  Todowrite と agent slot framework（snapshot）
- ADR-023  gate staged adoption（snapshot）
- ADR-024  continueOnBlock active guidance（snapshot）
- ADR-025〜032  V5 framework 系
- ADR-041  drift type 7 categories
- ADR-043  mode enum retrofit freeze break 対応
- **ADR-045  F6-F10 governance and survival operations snapshot (sibling、本 ADR の運用統治軸を補完)**

### 7.2 併走参照

本 ADR は parent plan の Step 4 と Step 6 の evidence につなぐため、以下を同時参照する。

1. docs/plans/L4/L4-helix-workflows-方式設計plan.md
2. HELIX-workflows/helix-process/L4-basic-design.md
3. docs/v2/L4-architecture/helix-workflows-system-architecture.md
4. docs/v2/L9-test-design/helix-workflows-system-test-design.md

## 実装状況ノート

`implementation_status` は現時点では以下。

- Decision-1: implemented
- Decision-2: implemented
- Decision-3: partial
- Decision-4: implemented

Decision-3 は ratchet の CLI 完全反映を段階移行し、Step 2-3 の本体実装で完了させる設計を維持。

## TODO 残存

### 8.1 Step 4 以降の carry

1. Step 2-3 で `docs/v2/L4-architecture/helix-workflows-system-architecture.md` の該当 section を ADR と完全一致させる。
2. L9 system test design の ST mapping table を全項目同等化。
3. `helix doctor --check-changeprop` の parser 例外ルートの回収（既知 commit b03695f / 277f760 を参照）。
4. `changeprop-violations.yaml` のスキーマ変更時に `plan_validator` と lint を同期。
5. `implementation_status` 列の `partial -> implemented` 更新を Step 6 で完了。
6. Alt-5 は scope 外として注記のみ採択、詳細は後続 ADR へ carry。Summary へ scope 注記を明示。
6. `status: Proposed` のまま Step 4 受入証跡を維持し、G4 通過時に Step 6 で Accepted 判定を検討。

### 8.2 受け渡し条件

- Step 4 が完了した段階で `proposal -> pending accepted` は発生しない。
- Step 6 の audit 合格後のみ accepted 化対象とする。
- 受け渡し時は handover 受信側に本節（TODO）と compliance table を明示する。
