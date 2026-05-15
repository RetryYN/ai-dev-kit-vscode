---
plan_id: PLAN-069
title: "PLAN-069: G3 entry blocker 解消 (M-01〜M-04, spine 整合化 + draft.yaml 正規化)"
status: completed
size: M
drive: be
created: 2026-05-15
completed: 2026-05-15
owner: PM
phases: L1, L2, L3, L4, L6
gates: G2, G3
implementation_commit: 62ac1cd
acceptance:
  - M-01 解消: helix-db-v21-spec.md の origin_mode 値を spine.yaml の forward/reverse/scrum に揃える
  - M-02 解消: spine.yaml に allowed_detectors enum を追加し CI-006 を消す
  - M-03 解消: fullstack-draft.yaml の promotion schema を fe-draft.yaml と対称化し CI-002 を消す
  - M-04 解消: fullstack-draft.yaml の role 名を ROLE_MAP 正規名へ置換し CI-003 を消す
  - cross-drive-integrity-check.md の CI-002 / CI-003 / CI-006 が resolved になる
  - 関連 bats / pytest が PASS (spine schema validation, draft schema validation)
  - G3 entry 時点で M-01〜M-04 すべて resolved (Phase B 末判定)
related:
  - PLAN-068-vmodel-strengthening-improvements (L4 実装連携)
  - docs/v2/L2-MASTER.md §12 (M-01〜M-04 正本記述)
  - docs/v2/B-design/cross-drive-integrity-check.md (CI-001〜008 識別子)
  - docs/v2/B-design/vmodel-semantics-spine.yaml (M-01/M-02 対象)
  - docs/v2/B-design/vmodel-semantics-fe-draft.yaml (M-03 正本)
  - docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml (M-03/M-04 対象)
  - docs/v2/B-design/helix-db-v21-spec.md (M-01 対象)
---

# PLAN-069: G3 entry blocker 解消 (M-01〜M-04, spine 整合化 + draft.yaml 正規化)

## §1 背景・目的

L2 MASTER.md §12 で、P1 重大度の 4 件 (M-01〜M-04) を G3 entry blocker / Phase B 末で確定済みとして扱う方針が明文化されている。  
本 PLAN は、G3 進入時点で実運用を停止させていた整合性の阻害要因を 1 つの PLAN としてまとめ、フェーズ B 末の blocker 解除前提を文書ベースで固定するものである。

当該 4 件は、データモデル定義と実装起点ファイルの表現揺れ、そして role 名名寄せの不足によって、G3 entry の契約解釈がぶれる状態を招いている。  
この状態が継続した場合、次の工程で影響が生じる。

### M-01/M-02 の想定される詰まり

1. spine.yaml と helix-db-v21-spec.md で `origin_mode` 取り扱いが一致しないため、クロスドライブ整合検証で判定不一致が発生する。  
2. `detector` の許容列挙が無いため `spine` の schema validation が通らず、起点投入時点で CI が停止する。  
3. CI 側参照が不安定で `CI-006` の解決待ちが長引き、G3 entry 条件の満了判定ができない。

### M-03 の想定される詰まり

1. `fe-draft.yaml` と `fullstack-draft.yaml` の promotion schema が非対称のため、`mock_to_implementation` 以降の追跡判定が揃わない。  
2. `fullstack` 側の schema 条件が不足しているため、検証実行時に `append_only` の意味がズレる。  
3. `CI-002` が未消去のまま、G3 entry 時点の blocker 判定に抵触する。

### M-04 の想定される詰まり

1. `fullstack-draft.yaml` の role 名が正規名でないと、role 定義との照合が破綻し、監査用 CI が対象 role を解釈できない。  
2. `ROLE_MAP` と draft が不一致のままだと、受入時に担当ロール責任の紐付けが不明瞭になり、G3 での最終同意フローが止まる。  
3. `CI-003` が未消去のまま、Phase B 末の blocker 解除条件を満たせない。

本 PLAN は、L2 G2 凍結時点では M-01〜M-04 が未解消であることを維持しつつ、G3 着手前に確実に解消済み状態へ遷移させるための実施計画を示す。  
ロードマップは以下である。

1. L2 で確認済みの矛盾を変更単位で明文化  
2. `PLAN-069` で対象 file の更新順を固定（短時間でレビューしやすい粒度）  
3. 全矛盾の修正後、スキーマ/CI/CI-レポートの再評価で resolved を確認  
4. `cross-drive-integrity-check.md` の該当 CI を `resolved` へ更新（更新タイミングは PLAN 完了後の別 commit で追記）  
5. Phase B 末の G3 entry 判定を再評価し、`G3 entry` 時点で blocker が全件解消済みであることを判定

### cross-drive-integrity-check.md との紐付け

本 PLAN は cross-drive-integrity-check.md の CI-002/CI-003/CI-006 と直接対応する。

- CI-006: `detector` enum 欠落問題に対応する（M-02）
- CI-003: `fullstack-draft.yaml` role 名正規化で解決する（M-04）
- CI-002: `fe-draft.yaml` と `fullstack-draft.yaml` の promotion schema 差分を解消する（M-03）
- M-01 は CI 番号なしだが、`origin_mode` の一致が前提条件として `cross-drive` の全体整合を支える

### G3 着手前再評価のフロー

PLAN 起票後の再評価は「Plan 起票 → 変更完了 → 検証実行 → resolved 更新確認」の 4 段階で行う。  
以下の順で再評価する。

1. PLAN-069 の acceptance 7 項目を一次判定で確認  
2. `docs/v2/B-design` と `docs/v2/A-audit` の対象箇所差分量を取得  
3. `spine schema` と `draft schema` の自動検証コマンドを実行  
4. CI-002 / CI-003 / CI-006 の `resolved` ステータスを確認  
5. すべての結果を添えて G3 entry 再評価を実施し、次工程へ進めるかを決定

本 PLAN は最終的に `G3 entry block` を解除する前提で書かれているため、L2 MASTER §12 の状態は、`PLAN-069` 完了時点での L2 別コミットで `resolved` へ更新する前提を維持する。

## §2 各矛盾の詳細と解消方針

### §2.1 M-01: origin_mode 値不一致 (CI 番号なし)

現状:

- `docs/v2/B-design/vmodel-semantics-spine.yaml` は `origin_mode` を `forward / reverse / scrum` の値群で扱っている。  
- `docs/v2/B-design/helix-db-v21-spec.md` 側の記載は `origin_mode` と同等概念の語彙が一致していない可能性があり、設計文書と実行仕様で解釈差が発生しうる。

方針:

- `spine.yaml` を正本として採用し、`forward / reverse / scrum` を唯一の基準値として固定する。  
- `helix-db-v21-spec.md` の origin_mode カラム定義を spine と一致する語彙へ揃える。  
- 併せて説明文で、`origin_mode` の利用箇所・移行上の扱い・既知制約を明示し、運用解釈を明確にする。

対象 file:

- 修正: `docs/v2/B-design/helix-db-v21-spec.md`（origin_mode カラム定義箇所）
- 維持: `docs/v2/B-design/vmodel-semantics-spine.yaml`

解消条件:

- `docs/v2/B-design/helix-db-v21-spec.md` と `docs/v2/B-design/vmodel-semantics-spine.yaml` が `origin_mode` 値として同一集合  
  - `forward`
  - `reverse`
  - `scrum`

#### M-01 実施上のチェック

1. spine 設計上の `origin_mode` 列挙を固定値として記述している行を確認する  
2. helix-db 側の説明とカラム定義のズレを削除する  
3. `origin_mode` 列で forward/reverse/scrum の 3 形式以外が残っていないことを確認する  
4. CI 目線で判定が変わる説明文がないかを再読し、不要なら除去する

### §2.2 M-02: detector enum 未定義 (CI-006)

現状:

- `docs/v2/B-design/vmodel-semantics-spine.yaml` の `detector` 利用箇所は散見されるが、公式に許容リストとしての `allowed_detectors` がない。  
- draft 側は detector 参照を前提とする前提設計があるため、許容値がない状態では schema 検証・CI 判定で不確実性が残る。

方針:

- `docs/v2/B-design/vmodel-semantics-spine.yaml` に `allowed_detectors` enum を追加する。  
- 追加対象は全ての draft で参照される detector 名を網羅し、未許可名が混在しないよう一元管理する。

対象 file:

- 修正: `docs/v2/B-design/vmodel-semantics-spine.yaml`
- 維持: 各 `*-draft.yaml` の detector 定義（参照先）

解消条件:

- `vmodel-semantics-spine.yaml` に `allowed_detectors` enum が定義され、`fullstack/fe-draft.yaml` の detector 参照が全て enum に収まっている。

#### M-02 実施上のチェック

1. `spine.yaml` に `allowed_detectors` を追加し、既知 detector 名を明示する  
2. draft の detector 参照値を列挙抽出して照合する  
3. 未許可値があれば、`allowed_detectors` 追加前に追加可否を決定するか、draft 側を補正する  
4. CI-006 の条件と一致するかを再確認する

### §2.3 M-03: promotion schema 非対称 (CI-002)

現状:

- `docs/v2/B-design/vmodel-semantics-fe-draft.yaml` と  
  `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml` の promotion schema にズレがある。  
- 特に `mock_to_implementation` の整備、`append_only` の扱い、`twin_track` 関連の運用 flag が一致しない可能性が高い。

方針:

- `fe-draft.yaml` を正本として採用し、`fullstack-draft.yaml` 側を同形状に揃える。  
- `mock_to_implementation`、`append_only=true`、`twin_track` など運用 flag を fe と一致させる。

対象 file:

- 維持: `docs/v2/B-design/vmodel-semantics-fe-draft.yaml`
- 修正: `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml`

解消条件:

- `fe-draft.yaml` と `fullstack-draft.yaml` の promotion schema が同一（キー、型、運用 flag の規約が一致）  
- fullstack 側で `mock_to_implementation` と append 動作が fe 側と同値

#### M-03 実施上のチェック

1. promotion ノードのトップレベルキー集合を比較する  
2. 各 key のデータ型、既定値、必須キー、列挙値を突き合わせる  
3. `append_only` の状態と `twin_track` 的な設計制約を同値化する  
4. `diff` で差分 0 を確認し、CI-002 消去を想定

### §2.4 M-04: role 名不正 (CI-003)

現状:

- `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml` の role 名に、`cli/ROLE_MAP.md` の正規名と一致しない表記が含まれる。  
- 旧表記は運用上の取りまとめ時に混乱を生み、監査要件の判定に影響を与えうる。

方針:

- `cli/ROLE_MAP.md` の正規名へ統一し、全 role 記述を置換する。  
- 正規名一覧（17 役）は以下を正本として採用する。  
  `tl / se / pg / qa / security / dba / devops / docs / research / legacy / perf / fe / pmo-sonnet / pmo-haiku`

対象 file:

- 修正: `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml`
- 参照: `cli/ROLE_MAP.md`

解消条件:

- `fullstack-draft.yaml` 内の全 role 名が `ROLE_MAP` の正規 17 役に完全一致する

#### M-04 実施上のチェック

1. `role` で使用される値をすべて列挙する  
2. `ROLE_MAP.md` の正規名一覧との差分を取る  
3. 置換前後を diff で追跡可能にする  
4. CI-003 の `resolved` 期待状態を再現する

## §3 実装内容 (Sprint 案)

本 PLAN は Codex の Sprint 参照を `PLAN-069` 内で明示し、担当分離を保ちつつ file-level の競合リスクを管理する。  
Sprint と検証は以下を前提にする。

| Sprint | 担当 | 対象 | 並列性 | 成果物 |
|---|---|---|---|---|
| .1 (M-01) | Codex pg | helix-db-v21-spec.md の origin_mode 修正 | independent | origin_mode 値を spine へ揃えた差分 |
| .2 (M-02) | Codex pg | spine.yaml に allowed_detectors enum 追加 | independent | `allowed_detectors` 追加と参照整合 |
| .3 (M-03) | Codex pg | fullstack-draft.yaml promotion schema 対称化 | independent (M-04 と同 file 衝突注意) | promotion schema 同値化 |
| .4 (M-04) | Codex pg | fullstack-draft.yaml role 名 ROLE_MAP 整合 | sequential | role 名一斉置換 |
| .5 (検証) | Opus / pmo-sonnet | bats / pytest / grep 検証 + CI-002/003/006 resolved 確認 | all sprints complete | 検証ログと判定結果 |

### 並列性と実施順の明示

- Sprint .1 と .2 は並列実施可能。  
- Sprint .3 と .4 は同一ファイル `fullstack-draft.yaml` を触るため、**.3→.4 の逐次実施**。  
- .1/.2 終了後に .3 を開始し、.3 完了後に .4、最終的に .5 へ進む。  
- .5 は全 Sprint 完了を前提として CI / 検証を集約する。

### Sprint ごとの成果定義

- Sprint .1: `origin_mode` 記述と補足説明の整合
- Sprint .2: `allowed_detectors` が追加され、draft 側 detector 参照を enum 内に収束
- Sprint .3: `promotion` ノードのキー配列・値仕様を fe-draft と同値
- Sprint .4: role 名の完全置換と未準拠値の除去
- Sprint .5: 5 つの検証対象（schema validation、`grep` 検証、CI 解消確認）を PASS かつ文書化

## §4 完了結果・検証

本項では、PLAN 実施後に出力される成果を、受入条件に沿って確認する。

### 4.1 差分成果

受入時に以下の diff 監査を行う。

1. `docs/v2/B-design/helix-db-v21-spec.md` の差分行数  
   - 目的: M-01 の起点仕様を spine に同期したことを確認  
   - 期待: origin_mode の値語彙と説明変更のみでノイズを最小化

2. `docs/v2/B-design/vmodel-semantics-spine.yaml` の差分行数  
   - 目的: M-02 の `allowed_detectors` 追加を確認  
   - 期待: 列挙定義と必要なら関連説明の最小追加

3. `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml` の差分行数  
   - 目的: M-03/M-04 の schema 正規化・role 正規名化を確認  
   - 期待: fullstack 側 promotion schema の対称化と role 名置換を完了

### 4.2 自動検証結果

- pytest が PASS していること  
  - 対象: `spine schema validation`, `draft schema validation`  
- bats が PASS していること  
  - 対象: cross-drive ルールと整合性チェックに関わるシナリオ

### 4.3 CI 解消確認

- `docs/v2/A-audit/cross-drive-integrity-check.md` の CI-002/CI-003/CI-006 が `resolved` になっていること。  
- CI の表現が「保留 (pending)」「要調整 (needs_fix)」で残っていないことを確認する。  
- M-01 については CI 番号なしだが、`origin_mode` 一貫性を受け入れ基準に合わせて L2 別更新時に反映する。

### 4.4 L2 MASTER 更新条件

- PLAN 完了時点で `L2 MASTER.md §12` の状態は、実装をまたいだ状態更新として `resolved` を想定  
- ただし本 PLAN の本文に直接は更新しない。  
- 本 PLAN 完了後の L2 別コミットで `M-01〜M-04` の状態更新を行う（受入責任範囲の明示として）。

### 4.5 G3 entry 再評価

以下を満たすときに、G3 entry 再評価を「APPROVE」へ進める。

1. M-01 origin_mode が `forward/reverse/scrum` に完全一致  
2. CI-006 が不成立状態から消え、`allowed_detectors` が検証可能  
3. CI-002 が fullstack と fe で対称化済みとして消失  
4. CI-003 が role 名一意化で消失  
5. Phase B 末でのまとめ判断として P1 4 件全件 resolved に反映

## §5 検証手順

以下コマンドを実行し、PLAN acceptance を実証する。

```bash
# spine 整合性
python3 -c "import yaml; spine=yaml.safe_load(open('docs/v2/B-design/vmodel-semantics-spine.yaml')); print('allowed_detectors:', 'allowed_detectors' in spine)"

# fullstack ↔ fe promotion schema 対称性
diff <(python3 -c "import yaml; d=yaml.safe_load(open('docs/v2/B-design/vmodel-semantics-fe-draft.yaml')); print(sorted(d.get('promotion',{}).keys()))") \
     <(python3 -c "import yaml; d=yaml.safe_load(open('docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml')); print(sorted(d.get('promotion',{}).keys()))")

# role 名 ROLE_MAP 整合
grep -oE "role:\\s*[a-z\\-]+" docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml | sort -u
# → ROLE_MAP.md の正規名と突合

# origin_mode 整合
grep -E "origin_mode|forward|reverse|scrum" docs/v2/B-design/helix-db-v21-spec.md docs/v2/B-design/vmodel-semantics-spine.yaml

# CI-002 / CI-003 / CI-006 resolved 確認
grep -A1 "CI-002\\|CI-003\\|CI-006" docs/v2/A-audit/cross-drive-integrity-check.md
```

### §5 補助確認（任意）

- role 名照合:
  - `grep -E '^\\s*-\\s*(tl|se|pg|qa|security|dba|devops|docs|research|legacy|perf|fe|pmo-sonnet|pmo-haiku)'` で値集合を可視化  
- 変更差分量:
  - `git diff -- docs/v2/B-design/helix-db-v21-spec.md docs/v2/B-design/vmodel-semantics-spine.yaml docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml | sed -n '1,220p'`

## §6 carry / 関連 PLAN

- PLAN-068 (V-model 強化 L4 実装) を前提として carry。  
- M-05/M-06/M-07/M-08 は P2/P3 として Phase C 以降 carry とし、別 PLAN で起票する。  
- 本 PLAN の完了後、L2 MASTER.md §12 の status 更新は別 commit で行う。  
- `helix-db v22+ migration`（`source_entry_id` の drive 切替記録列追加）は L3 schema 直下で別 PLAN として起票する。

## §7 受入時の最終チェックリスト

- acceptance 7 項目を本文内で個別に追跡し、根拠行をPLAN内の該当節と紐付ける  
- `frontmatter` に plan_id/drive/size/acceptance/related が正しく記載されている  
- §1 で背景と再評価条件を明文化している  
- §2 で M-01〜M-04 の現状・方針・解消条件を明示する  
- §3 で Sprint 並列性を `.1/.2 parallel` と `.3→.4 sequential` の 2 系列で明示する  
- §4 で差分量と検証結果の構成を明確にする  
- §5 の検証手順がそのまま実行可能である  
- §6 で carry と関連 PLAN を明示し、次工程移行の切断面を作る

## 参照

- 文字列上の基盤文書:
  - `docs/v2/L2-MASTER.md §12`
  - `docs/v2/A-audit/cross-drive-integrity-check.md`
  - `docs/v2/B-design/vmodel-semantics-spine.yaml`
  - `docs/v2/B-design/vmodel-semantics-fe-draft.yaml`
  - `docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml`
  - `docs/v2/B-design/helix-db-v21-spec.md`
- 役割正本:
  - `cli/ROLE_MAP.md`
  - `docs/v2/B-design/*-draft.yaml`

