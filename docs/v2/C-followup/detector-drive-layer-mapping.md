# Detector × Drive × Layer Mapping

最終更新: 2026-05-14  
用途: V2 Phase 4 検出ガードレール強化の入力正本。`PLAN-063` の 14 axis detector と、`FR-FE02` で追加された FE 専用 5 axis を、`drive (be / fe / db / fullstack) × layer (planning / requirement / architecture / detailed / functional)` に割り付ける。

## 0. 前提と読み方

- 本書の主対象は `drives.<drive>.layers.<layer>.design.detectors` である。
- `docs/v2/B-design/vmodel-semantics-*-draft.yaml` に既にある detector 列挙を優先し、未記載箇所だけを `PLAN-063` と `FR-FE02` から補完した。
- `axis-15` 〜 `axis-19` は未実装 detector であり、役割・gate・threshold は `docs/v2/L1-REQUIREMENTS.md` と FE / fullstack draft からの推論を含む。
- `db` drive の `axis-12` は draft 上では `axis-12-migration-safety` と表現されている。本書では `PLAN-063` の軸名 `axis-12-connection-deficiency` を親概念とし、DB では migration / schema safety へ特殊化されたものとして扱う。
- 記号の意味:
  - `✓`: その drive/layer の `design.detectors` に採用する
  - `△`: 直接の明記は弱いが、cross-drive 接続または gate 連動上で採用推奨
  - `✗`: 適用対象外

## 1. 19 axis × drive × layer マトリクス

### 1.1 be drive

| axis | planning | requirement | architecture | detailed | functional |
|---|---|---|---|---|---|
| axis-01 dead-code-drift | ✗ | ✗ | ✗ | ✗ | ✓ |
| axis-02 coverage-erosion | ✗ | ✗ | ✓ | ✗ | ✓ |
| axis-03 real-duplicate | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-04 skill-decay | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-05 plan-debt-loop | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-06 naming-confusion | ✗ | ✗ | ✗ | ✓ | ✗ |
| axis-07 contract-drift | ✗ | ✓ | ✓ | ✓ | ✗ |
| axis-08 plan-integrity | ✓ | ✓ | ✗ | ✗ | ✗ |
| axis-09 refactor-opportunity | ✗ | ✗ | ✗ | ✗ | ✓ |
| axis-10 relation-graph | ✗ | ✗ | ✓ | ✗ | ✗ |
| axis-11 regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-12 connection-deficiency | ✗ | ✓ | ✗ | ✓ | ✗ |
| axis-13 model-skill-analytics | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-14 orchestration-integrity | ✓ | ✗ | ✗ | ✗ | ✗ |
| axis-15 mock-promotion | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-16 design-token-drift | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-17 a11y-regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-18 visual-regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-19 state-transition-drift | ✗ | ✗ | ✗ | ✗ | ✗ |

### 1.2 fe drive

| axis | planning | requirement | architecture | detailed | functional |
|---|---|---|---|---|---|
| axis-01 dead-code-drift | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-02 coverage-erosion | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-03 real-duplicate | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-04 skill-decay | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-05 plan-debt-loop | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-06 naming-confusion | ✗ | ✗ | ✗ | ✓ | ✗ |
| axis-07 contract-drift | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-08 plan-integrity | ✓ | ✓ | ✗ | ✗ | ✗ |
| axis-09 refactor-opportunity | ✗ | ✗ | ✗ | ✗ | ✓ |
| axis-10 relation-graph | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-11 regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-12 connection-deficiency | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-13 model-skill-analytics | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-14 orchestration-integrity | ✓ | ✗ | ✗ | ✗ | ✗ |
| axis-15 mock-promotion | ✗ | ✗ | ✓ | ✗ | ✓ |
| axis-16 design-token-drift | ✗ | ✗ | ✓ | ✓ | ✗ |
| axis-17 a11y-regression | ✗ | ✓ | ✗ | ✓ | ✓ |
| axis-18 visual-regression | ✗ | ✗ | ✗ | ✗ | ✓ |
| axis-19 state-transition-drift | ✓ | ✓ | ✓ | ✓ | ✗ |

### 1.3 db drive

| axis | planning | requirement | architecture | detailed | functional |
|---|---|---|---|---|---|
| axis-01 dead-code-drift | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-02 coverage-erosion | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-03 real-duplicate | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-04 skill-decay | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-05 plan-debt-loop | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-06 naming-confusion | ✗ | ✗ | ✗ | ✓ | ✗ |
| axis-07 contract-drift | ✓ | ✓ | ✓ | ✓ | ✓ |
| axis-08 plan-integrity | ✓ | ✓ | ✗ | ✗ | ✗ |
| axis-09 refactor-opportunity | ✗ | ✗ | ✗ | ✗ | ✓ |
| axis-10 relation-graph | ✗ | ✗ | ✓ | ✗ | ✗ |
| axis-11 regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-12 connection-deficiency / migration-safety | ✗ | ✓ | ✓ | ✓ | ✓ |
| axis-13 model-skill-analytics | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-14 orchestration-integrity | ✓ | ✗ | ✗ | ✗ | ✗ |
| axis-15 mock-promotion | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-16 design-token-drift | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-17 a11y-regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-18 visual-regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-19 state-transition-drift | ✗ | ✗ | ✗ | ✗ | ✗ |

### 1.4 fullstack drive

| axis | planning | requirement | architecture | detailed | functional |
|---|---|---|---|---|---|
| axis-01 dead-code-drift | ✗ | ✗ | ✗ | ✗ | ✓ |
| axis-02 coverage-erosion | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-03 real-duplicate | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-04 skill-decay | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-05 plan-debt-loop | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-06 naming-confusion | ✗ | ✗ | ✗ | ✓ | ✗ |
| axis-07 contract-drift | ✗ | ✓ | ✓ | ✓ | ✗ |
| axis-08 plan-integrity | ✓ | ✓ | ✗ | ✗ | ✗ |
| axis-09 refactor-opportunity | ✗ | ✗ | ✗ | ✗ | ✓ |
| axis-10 relation-graph | ✗ | ✗ | ✓ | ✗ | ✗ |
| axis-11 regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-12 connection-deficiency | ✓ | ✓ | ✓ | ✓ | ✗ |
| axis-13 model-skill-analytics | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-14 orchestration-integrity | ✓ | ✗ | ✓ | ✗ | ✗ |
| axis-15 mock-promotion | ✗ | ✗ | ✗ | ✗ | ✓ |
| axis-16 design-token-drift | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-17 a11y-regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-18 visual-regression | ✗ | ✗ | ✗ | ✗ | ✗ |
| axis-19 state-transition-drift | ✗ | ✗ | ✗ | ✓ | ✗ |

### 1.5 マトリクス読解メモ

- 280 セルのうち `✓` は 43 セル、`△` は 0 セル、`✗` は 237 セル。
- BE / DB は `axis-07`, `axis-08`, `axis-12`, `axis-14` を中核にし、doc / contract / orchestration から先に fail-close を掛ける構造になっている。
- FE / fullstack は `axis-15` 〜 `axis-19` が主軸で、既存 14 軸だけでは FE drift を取り切らない。
- `axis-03`, `axis-04`, `axis-05`, `axis-11`, `axis-13` は Phase 4 guardrail では dashboard / analytics / run 後監視に寄るため、`design.detectors` への常時列挙対象にはしていない。

## 2. axis ごとの drive × layer 適用根拠

### 2.1 axis-01 dead-code-drift

| 項目 | 内容 |
|---|---|
| axis name | axis-01-dead-code-drift |
| 役割 | vulture と `code_entries` の差分から dead code drift を検出する。 |
| 適用 drive | be / fullstack |
| 適用 layer | functional |
| G ゲート fail-close | G4 |
| threshold | `--fail-under N` と allowlist 調整。固定値は未凍結。 |
| 根拠 | `axis-01-dead.md`, `vmodel-semantics-be-draft.yaml`, `vmodel-semantics-fullstack-draft.yaml` |

### 2.2 axis-02 coverage-erosion

| 項目 | 内容 |
|---|---|
| axis name | axis-02-coverage-erosion |
| 役割 | coverage 未達と連続悪化を検知する。 |
| 適用 drive | be / fullstack |
| 適用 layer | architecture / functional |
| G ゲート fail-close | G4 |
| threshold | uncovered 増分と連続悪化回数。具体閾値は未凍結。 |
| 根拠 | `axis-02-coverage.md`, `PLAN-063` G4 記述, be/fullstack draft |

### 2.3 axis-03 real-duplicate

| 項目 | 内容 |
|---|---|
| axis name | axis-03-real-duplicate |
| 役割 | 実害のあるロジック重複のみを duplicate として抽出する。 |
| 適用 drive | なし（Phase 4 入力では dashboard / run-on-demand 扱い） |
| 適用 layer | なし |
| G ゲート fail-close | D-DETECTORS 上は G4 接続だが、現行 semantic draft には未反映。 |
| threshold | 類似度と entrypoint 除外。 |
| 根拠 | `axis-03-dup.md` と semantic draft の未採用状態の差分から判断。 |

### 2.4 axis-04 skill-decay

| 項目 | 内容 |
|---|---|
| axis name | axis-04-skill-decay |
| 役割 | `SKILL.md` の trigger / verification / usage quality 劣化を検知する。 |
| 適用 drive | なし |
| 適用 layer | なし |
| G ゲート fail-close | なし。warning のみ。 |
| threshold | 5 軸スコア低下と sample window。 |
| 根拠 | `axis-04-skill-decay.md`, task §5 warning 指定 |

### 2.5 axis-05 plan-debt-loop

| 項目 | 内容 |
|---|---|
| axis name | axis-05-plan-debt-loop |
| 役割 | deferred finding と retro carry の循環を検知する。 |
| 適用 drive | なし（design.detectors には未採用） |
| 適用 layer | なし |
| G ゲート fail-close | G6 接続だが、warning 寄り運用を推奨。 |
| threshold | recurring debt 件数と carry 期限。 |
| 根拠 | `axis-05-plan-debt.md`, task §5 warning 軸の明示 |

### 2.6 axis-06 naming-confusion

| 項目 | 内容 |
|---|---|
| axis name | axis-06-naming-confusion |
| 役割 | role / symbol / banned name の不一致を検知する。 |
| 適用 drive | be / fe / db / fullstack |
| 適用 layer | detailed |
| G ゲート fail-close | G2 で早期警告、G3 の詳細契約層で fail-close 入力。 |
| threshold | banned name hit と role mismatch。 |
| 根拠 | `axis-06-naming.md` と 4 drive draft の detailed 共通採用 |

### 2.7 axis-07 contract-drift

| 項目 | 内容 |
|---|---|
| axis name | axis-07-contract-drift |
| 役割 | 正本文書や contract 定義間の drift を検知する。 |
| 適用 drive | be / db / fullstack |
| 適用 layer | requirement / architecture / detailed |
| G ゲート fail-close | G2 fail-close の critical 軸 |
| threshold | schema / role / model / contract の差分。具体数値閾値なし。 |
| 根拠 | `axis-07-doc-drift.md`, task §5 critical 軸指定, be/db/fullstack draft |

### 2.8 axis-08 plan-integrity

| 項目 | 内容 |
|---|---|
| axis name | axis-08-plan-integrity |
| 役割 | PLAN status / retro / 実コミット整合を検知する。 |
| 適用 drive | be / fe / db / fullstack |
| 適用 layer | planning / requirement |
| G ゲート fail-close | G6 接続だが、Phase 4 入力では planning/requirement guard として先置きする。 |
| threshold | finalized PLAN の整合違反有無。 |
| 根拠 | `axis-08-plan-integrity.md` と 4 drive draft の planning/requirement 採用 |

### 2.9 axis-09 refactor-opportunity

| 項目 | 内容 |
|---|---|
| axis name | axis-09-refactor-opportunity |
| 役割 | god file / layer violation / argument explosion を分類して示す。 |
| 適用 drive | be / fe / db / fullstack |
| 適用 layer | functional |
| G ゲート fail-close | task §6 では G3 追加、通常は G4 入力。 |
| threshold | ファイル肥大、責務集中、層越境。 |
| 根拠 | `axis-09-refactor.md`, 4 drive draft functional 採用, PLAN-063 G4 記述 |

### 2.10 axis-10 relation-graph

| 項目 | 内容 |
|---|---|
| axis name | axis-10-relation-graph |
| 役割 | impl / test / doc / db の trace を graph 化し断線を見つける。 |
| 適用 drive | be / db / fullstack |
| 適用 layer | architecture |
| G ゲート fail-close | 基本は warning。task §5 でも warning 軸。 |
| threshold | edge 欠落と soft link only。 |
| 根拠 | `axis-10-relation-graph.md`, task §5 warning 指定, be/db/fullstack draft |

### 2.11 axis-11 regression

| 項目 | 内容 |
|---|---|
| axis name | axis-11-regression |
| 役割 | test pass→fail、contract diff、silent error 増を検知する。 |
| 適用 drive | なし（test.detectors 側で主に使用） |
| 適用 layer | なし |
| G ゲート fail-close | G6 |
| threshold | baseline 差分と flaky 切り分け。 |
| 根拠 | `axis-11-regression.md` と draft 群での test 側優先利用 |

### 2.12 axis-12 connection-deficiency

| 項目 | 内容 |
|---|---|
| axis name | axis-12-connection-deficiency |
| 役割 | import broken / schema drift / hook 不発火 / role mismatch を検知する。 |
| 適用 drive | be / db / fullstack |
| 適用 layer | be=requirement+detailed, db=requirement+architecture+detailed+functional, fullstack=planning+requirement+architecture+detailed |
| G ゲート fail-close | G2 の中心軸。G6 でも再実行推奨。 |
| threshold | orphan / dead option / hook 不発火件数。 |
| 根拠 | `axis-12-connection.md`, `PLAN-063` 12-G, db draft の migration-safety 特殊化 |

### 2.13 axis-13 model-skill-analytics

| 項目 | 内容 |
|---|---|
| axis name | axis-13-model-skill-analytics |
| 役割 | role 別 model / skill usage と cost trend を分析する。 |
| 適用 drive | なし |
| 適用 layer | なし |
| G ゲート fail-close | なし。analytics / advisory。 |
| threshold | 使用率帯域と cost imbalance。 |
| 根拠 | `axis-13-model-skill.md`, semantic draft 未採用 |

### 2.14 axis-14 orchestration-integrity

| 項目 | 内容 |
|---|---|
| axis name | axis-14-orchestration-integrity |
| 役割 | 工程スキップ / stagnation / role bypass / concurrency violation を検知する。 |
| 適用 drive | be / db / fullstack / fe |
| 適用 layer | planning を基本、fullstack は architecture も追加 |
| G ゲート fail-close | G4、G6 でも再評価推奨 |
| threshold | role bypass、concurrency violation は即 fail-close 候補。 |
| 根拠 | `axis-14-orchestration.md`, be/fe/db/fullstack draft |

### 2.15 axis-15 mock-promotion

| 項目 | 内容 |
|---|---|
| axis name | axis-15-mock-promotion |
| 役割 | mock 凍結済み証跡から component implementation への昇格不備を検知する。 |
| 適用 drive | fe / fullstack |
| 適用 layer | fe=architecture+functional, fullstack=functional |
| G ゲート fail-close | G4 で fail-close 推奨 |
| threshold | mock_frozen → promoted の append-only 証跡欠落。 |
| 根拠 | `FR-FE02`, `vmodel-semantics-fe-draft.yaml`, `vmodel-semantics-fullstack-draft.yaml` |

### 2.16 axis-16 design-token-drift

| 項目 | 内容 |
|---|---|
| axis name | axis-16-design-token-drift |
| 役割 | mock / design token / 実装 token binding の drift を検知する。 |
| 適用 drive | fe |
| 適用 layer | architecture / detailed |
| G ゲート fail-close | G4 前の warning、G4 以降 fail-close 候補 |
| threshold | token baseline 差分件数。具体値未確定。 |
| 根拠 | `FR-FE02`, fe draft のみ。fullstack design 側にはまだ未反映。 |

### 2.17 axis-17 a11y-regression

| 項目 | 内容 |
|---|---|
| axis name | axis-17-a11y-regression |
| 役割 | state / component / journey 単位の accessibility 回帰を検知する。 |
| 適用 drive | fe |
| 適用 layer | requirement / detailed / functional |
| G ゲート fail-close | G4 と G6 で fail-close 候補 |
| threshold | axe / scenario baseline 差分。具体値未確定。 |
| 根拠 | `FR-FE02`, fe draft。fullstack では test 側優先で design 側未反映。 |

### 2.18 axis-18 visual-regression

| 項目 | 内容 |
|---|---|
| axis name | axis-18-visual-regression |
| 役割 | visual baseline と snapshot / diff の差分を検知する。 |
| 適用 drive | fe |
| 適用 layer | functional |
| G ゲート fail-close | G4 / G6 候補 |
| threshold | visual diff 許容幅。具体値未確定。 |
| 根拠 | `FR-FE02`, fe draft。fullstack は test 側の detector として先行。 |

### 2.19 axis-19 state-transition-drift

| 項目 | 内容 |
|---|---|
| axis name | axis-19-state-transition-drift |
| 役割 | state-events, screen transition, runtime state guard の drift を検知する。 |
| 適用 drive | fe / fullstack |
| 適用 layer | fe=planning+requirement+architecture+detailed, fullstack=detailed |
| G ゲート fail-close | G2〜G4 を跨ぐ継続監視候補 |
| threshold | state-event 欠落、遷移不一致、trace 欠落。 |
| 根拠 | `FR-FE02`, fe/fullstack draft。fullstack は architecture/test では見えるが design 側は detailed に集約。 |

## 3. 不足 axis (FE 強化 5 軸) の扱い

### 3.1 推奨一覧

| axis | 役割 | 推奨 drive | 推奨 layer | 推奨 gate |
|---|---|---|---|---|
| axis-15 | mock promotion drift | fe / fullstack | architecture / functional | G4 |
| axis-16 | design token drift | fe | architecture / detailed | G4 |
| axis-17 | a11y regression | fe | requirement / detailed / functional | G4, G6 |
| axis-18 | visual regression | fe | functional | G4, G6 |
| axis-19 | state transition drift | fe / fullstack | planning / requirement / architecture / detailed | G2, G3, G4 |

### 3.2 不確実性

- 5 軸とも個別 `D-DETECTORS/*.md` がまだ無く、threshold と blocking 条件は未凍結である。
- fullstack への反映は `vmodel-semantics-fullstack-draft.yaml` で一部 test 側先行になっており、design 側の完全反映は未完である。
- `axis-16`, `axis-17`, `axis-18` は fullstack design 側へ未採用なので、Phase 4 入力では FE 優先、fullstack は carry とするのが安全である。

## 4. spine.yaml 反映用の具体列挙

以下は `drives.<drive>.layers.<layer>.design.detectors` へそのまま転記できる形の canonical list である。

```yaml
be:
  planning: [axis-08-plan-integrity, axis-14-orchestration-integrity]
  requirement: [axis-07-contract-drift, axis-08-plan-integrity, axis-12-connection-deficiency]
  architecture: [axis-02-coverage-erosion, axis-07-contract-drift, axis-10-relation-graph]
  detailed: [axis-06-naming-confusion, axis-07-contract-drift, axis-12-connection-deficiency]
  functional: [axis-01-dead-code-drift, axis-02-coverage-erosion, axis-09-refactor-opportunity]

fe:
  planning: [axis-08-plan-integrity, axis-14-orchestration-integrity, axis-19-state-transition-drift]
  requirement: [axis-08-plan-integrity, axis-17-a11y-regression, axis-19-state-transition-drift]
  architecture: [axis-15-mock-promotion, axis-16-design-token-drift, axis-19-state-transition-drift]
  detailed: [axis-06-naming-confusion, axis-16-design-token-drift, axis-17-a11y-regression, axis-19-state-transition-drift]
  functional: [axis-15-mock-promotion, axis-17-a11y-regression, axis-18-visual-regression, axis-09-refactor-opportunity]

db:
  planning: [axis-07-contract-drift, axis-08-plan-integrity, axis-14-orchestration-integrity]
  requirement: [axis-07-contract-drift, axis-08-plan-integrity, axis-12-migration-safety]
  architecture: [axis-07-contract-drift, axis-10-relation-graph, axis-12-migration-safety]
  detailed: [axis-06-naming-confusion, axis-07-contract-drift, axis-12-migration-safety]
  functional: [axis-07-contract-drift, axis-09-refactor-opportunity, axis-12-migration-safety]

fullstack:
  planning: [axis-08-plan-integrity, axis-12-connection-deficiency, axis-14-orchestration-integrity]
  requirement: [axis-07-contract-drift, axis-08-plan-integrity, axis-12-connection-deficiency]
  architecture: [axis-07-contract-drift, axis-10-relation-graph, axis-12-connection-deficiency, axis-14-orchestration-integrity]
  detailed: [axis-06-naming-confusion, axis-07-contract-drift, axis-12-connection-deficiency, axis-19-state-transition-drift]
  functional: [axis-01-dead-code-drift, axis-09-refactor-opportunity, axis-15-mock-promotion]
```

### 4.1 整合メモ

- `be` は現行 `vmodel-semantics-be-draft.yaml` と一致する。
- `fe` は現行 `vmodel-semantics-fe-draft.yaml` と一致する。
- `db` は現行 `vmodel-semantics-db-draft.yaml` と一致するが、`axis-12` の表記だけ `migration-safety` に特殊化されている。
- `fullstack` は現行 `vmodel-semantics-fullstack-draft.yaml` と一致する。

## 5. fail-close vs warning

### 5.1 fail-close 推奨

| 区分 | axis | 理由 |
|---|---|---|
| critical | axis-01 | dead code は G4 の構造劣化を直接表すため |
| critical | axis-02 | coverage erosion はテスト安全網の劣化を直接表すため |
| critical | axis-07 | contract drift は doc / schema / role の正本破壊に直結するため |
| critical | axis-12 | 接続断は gate 通過後の破綻確率が高いため |
| critical | axis-14 | role bypass / concurrency violation は HELIX discipline 自体を壊すため |
| FE critical | axis-15 | mock 凍結違反は FE / fullstack の設計正本破壊に当たるため |
| FE critical | axis-17 | a11y 回帰は受入不能欠陥になりやすいため |
| FE critical | axis-18 | visual baseline 破壊は FE guardrail の中核であるため |
| FE critical | axis-19 | state transition drift は FE/fullstack 契約ズレの直結要因であるため |

### 5.2 warning 推奨

| axis | 理由 |
|---|---|
| axis-04 | skill 品質の劣化は advisory から始めるのが安全 |
| axis-05 | debt loop は PM / retro の判断余地が大きい |
| axis-10 | relation graph は可視化価値は高いが false positive を含みやすい |
| axis-13 | analytics 系であり直接 fail-close には向かない |
| axis-16 | token drift は FE 初期導入では warning 運用が妥当 |

## 6. G ゲート連動

| gate | 自動 run する axis | ねらい |
|---|---|---|
| G2 | axis-02, axis-07, axis-10 | architecture / contract / relation の早期逸脱検知 |
| G3 | axis-02, axis-07, axis-09, axis-10, axis-12 | detailed 契約と接続断の凍結前検知 |
| G4 | 全 axis-01〜14、FE 専用導入後は axis-15〜19 も対象 | 実装凍結時の fail-close 本体 |
| G6 | 全 axis + axis-12 / axis-14 を再強調 | RC 判定時の regression / orchestration / connection 再検査 |

### 6.1 補足

- task 指示の `G2: axis-02 / axis-07 / axis-10` は、現行 semantic draft と整合する最小セットとして妥当。
- `PLAN-063` 原文では gate integration は `axis-06,7,9-A,9-B,12-A,12-E,12-G` など sub-axis ベースで記述されている。V2 Phase 4 入力ではそれを axis 親レベルへ正規化している。
- FE 追加 5 軸は現時点では G4 中心でよい。G2/G3 への前倒しは `axis-19` のみ先行採用が安全である。

## 7. 推奨

1. `spine.yaml` 反映の canonical source は本書 §4 とし、個別 draft との差分が出たら draft 側を更新する。
2. `axis-15` 〜 `axis-19` は `D-DETECTORS` 個票を作り、gate / threshold / baseline policy を明文化する。
3. `axis-03`, `axis-11`, `axis-13` は有用だが、`design.detectors` ではなく dashboard / test.detectors / run 後解析に寄せる。
4. `db` の `axis-12-migration-safety` は alias 化を明示し、`connection-deficiency` との命名差を残さない。
5. Phase 4 では `G2/G3/G4/G6` の run set を固定し、`blocked` と `warning` の意味論も合わせて凍結する。
