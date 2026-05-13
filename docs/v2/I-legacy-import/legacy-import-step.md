# Phase I Legacy Import Detailed Step
Status: draft
Phase: I Legacy Import
Scope: `FR-LI01` `FR-LI02` `FR-LI03` を実行可能 step に詳細化
Mode: read-only planning / no archive / no physical delete

## 0. 概要
Phase I Legacy Import の目的は、V1 の PLAN 資産を壊さずに保持しつつ、V2 の phase / FR / follow-up へ再配線することにある。対象は旧 PLAN markdown の retention、V1 → V2 mapping、未実装 carry の吸収先整理であり、物理 archive や rename はこの phase では行わない。

推奨:
1. `docs/plans/PLAN-001`〜`068` は削除せず history を保持したまま棚卸しする。
2. mapping は「全 PLAN が少なくとも 1 つの V2 phase に紐付く」を合格条件にする。
3. carry は `V2 吸収可` `V2 吸収不可` `永久 carry / V3 候補` に分けて reasoning を残す。

不確実性:
- 入力指定の `docs/v2/I-legacy-import/V2-mapping.md` は 2026-05-14 時点の repo 上で未確認だった。
- `legacy-plans-carry.md` では `PLAN-020`〜`027`、`068` に canonical source 不連続がある。

## 1. 入力と成果物
入力正本:
- `docs/v2/L1-REQUIREMENTS.md`
  - `FR-INV02`: PLAN-001〜068 carry 棚卸し
  - `BR-D2`: V1 知見の V2 集大成
- `docs/v2/A-audit/legacy-plans-carry.md`
- `docs/v2/I-legacy-import/V2-mapping.md` または同等の mapping 草案

補助根拠:
- `docs/plans/PLAN-001-*.md` 〜 `PLAN-068-*.md`
- `.helix/plans/PLAN-019.yaml`, `020.yaml`, `021.yaml`, `024.yaml`, `027.yaml`
- `git log --summary --follow -- docs/plans`

成果物:
- retention policy
- V1 → V2 mapping 完成表
- carry 吸収表
- dependency chain メモ
- Phase J archive 検討条件

## 2. 実行前チェック
### Step 2.1 ファイル存在確認
1. `docs/plans` に `PLAN-001`〜`PLAN-068` 系が残っているか確認する。
2. `docs/v2/A-audit/legacy-plans-carry.md` が棚卸し正本であることを確認する。
3. `docs/v2/I-legacy-import/V2-mapping.md` が存在するか確認する。

判定:
- `V2-mapping.md` が存在する場合: その内容を主入力にする。
- 存在しない場合: `legacy-plans-carry.md` を仮入力として mapping 草案を再構成し、最終版へ「入力不足」を注記する。

### Step 2.2 保持数確認
1. `docs/plans` の markdown 一覧を採取する。
2. `PLAN-002B` のような派生番号を別行で記録する。
3. 欠番、lock file、trace-only PLAN を区別する。

期待値:
- 実ファイル数と一意 PLAN ID 数は一致しなくてもよい。
- `legacy-plans-carry.md` との差分は理由が説明できればよい。

## 3. FR-LI01: 旧 PLAN markdown を削除せず history 保持
目的:
- V1 PLAN 資産を V2 へ取り込む際に、旧 file を rename / delete して provenance を壊さない。

実行 step:
1. `docs/plans/PLAN-001`〜`068` の存在一覧を固定する。
2. `git log --summary --follow -- docs/plans` から rename / delete / create 履歴を抽出する。
3. `PLAN-002` → `PLAN-002B` の rename を retention note に記録する。
4. `delete mode` が出た場合は lock file か markdown 本体かを切り分ける。
5. markdown 本体の削除が見つかった場合は `retention policy 逸脱候補` として別表へ記録する。
6. archive は実施せず、Phase J の検討条件だけ定義する。

合格条件:
- V1 PLAN markdown が保持されている。
- rename / delete 履歴が説明できる。
- `archive は Phase J` と `物理削除なし` が明文化されている。

## 4. FR-LI02: V1 → V2 mapping 表の完成
目的:
- 全旧 PLAN を V2 phase / FR / follow-up へ再配線し、取りこぼしをなくす。

実行 step:
1. `V2-mapping.md` があればその表を基準に確認する。
2. `legacy-plans-carry.md` の `V2 phase 紐付け候補` を抽出する。
3. 1 PLAN につき最低 1 つの V2 phase を割り当てる。
4. phase だけでは粗い場合は `FR-XX` または具体 doc へ粒度を落とす。
5. `completed だが参照価値のある PLAN` と `未実装 carry を持つ PLAN` を分ける。
6. `PLAN-019`〜`027`、`068` は `trace-only` 列を追加して区別する。

mapping 表の最低列:
- `PLAN ID`
- `Title`
- `Status`
- `Retention`
- `V2 Phase`
- `Target FR / Doc`
- `Carry 有無`
- `Source Confidence`
- `Notes`

合格条件:
- 68+ PLAN がすべて V2 phase に紐付いている。
- trace-only / source 不明 PLAN が明示されている。
- `永久 carry` または `closed as untraceable` の扱いが定義されている。

## 5. FR-LI03: 未実装 carry の V2 取り込み
目的:
- 旧 PLAN に散在した carry を、V2 実装フェーズの受入対象へ変換する。

実行 step:
1. `legacy-plans-carry.md` の `未実装 carry` 列を PLAN ごとに確認する。
2. carry を `V2 吸収可` `V2 吸収不可` `永久 carry / V3 候補` に分類する。
3. 吸収可能な carry は `V2 phase` だけでなく `FR-XX` まで落とし込む。
4. 吸収不可 carry は `非機能` `source 不足` `方針変更済` `追跡不能` で理由分類する。
5. `PLAN-025`, `026`, `068` は永久 carry 候補として別枠管理する。
6. `PLAN-066`, `067` は既存 draft 再利用候補として扱う。

carry 吸収表の最低列:
- `PLAN ID`
- `Carry Summary`
- `V2 吸収先 FR`
- `Phase`
- `吸収可否`
- `吸収不可理由`
- `Reasoning`

合格条件:
- 全 carry に吸収先または非吸収理由がある。
- `永久 carry` と `V3 候補` が混同されていない。
- reasoning が引き継げる粒度で残っている。

## 6. PLAN 改名 / archive / retention ルール
命名:
- V1 PLAN は既存 file 名を保持する。
- V2 PLAN は `PLAN-070` 以降の別 namespace を使う。
- `PLAN-001`〜`068` を V2 用に rename しない。

archive:
- archive 検討は Phase J で行う。
- 着手条件は `V2 完了` かつ `1 年経過`。
- 物理削除は行わない。

retention:
1. V2 完了後も全 PLAN を保持する。
2. 保持対象は markdown 本体と provenance 情報を含む。
3. lock file は本体 retention と分けて扱う。
4. physical delete は禁止する。

## 7. mapping 表の確認 step
### Step 7.1 全件紐付け
1. `PLAN-001`〜`068` を行として並べる。
2. `V2-mapping.md` の有無に関係なく空欄行をゼロにする。
3. `PLAN-002B` は派生として別行管理し、`PLAN-002` との関係を notes に書く。

### Step 7.2 数値整合
1. 総 PLAN 数
2. V2 吸収件数
3. V1 完結件数
4. 永久 carry / V3 候補件数
5. trace-only 件数

上記 5 数値が相互に説明できることを確認する。

### Step 7.3 差分検証
1. `legacy-plans-carry.md` の集計値と mapping 表の件数を照合する。
2. 差分は `欠番` `派生行` `canonical 不在` `status 正規化差` のどれかで説明する。

## 8. dependency chain 整理
目的:
- 旧 PLAN 同士の前提関係を見て、V2 で同 phase に束ねられるかを判断する。

実行 step:
1. PLAN 本文または carry 棚卸しから `PLAN-A depends on PLAN-B` を抽出する。
2. 同系列 carry 連鎖は 1 本の chain としてまとめる。
3. `PLAN-030`〜`046` の carry 再配線系列は Phase 1 既存整理でまとめて扱う。
4. `PLAN-066` は Phase 4、`PLAN-067` は Phase 5 の母艦として独立維持する。
5. chain を同 phase に統合する場合でも起源 PLAN は notes に残す。

判定原則:
- 同じ問題を段階的に再配線した PLAN 群は同 phase 統合可。
- schema / detector / automation は phase 分離を維持する。
- source 不連続群は Phase I で正本整理してから次 phase へ送る。

## 9. 推奨
| 項目 | 内容 |
|---|---|
| 推奨度 | 高 |
| 推奨 | `legacy-plans-carry.md` を現行正本、`V2-mapping.md` を完成表として二層管理する |
| メリット | 既存棚卸しを再利用でき、provenance を壊さず V2 へ接続できる |
| デメリット | `V2-mapping.md` 不在時は manual 補完が必要 |
| ソース | `docs/v2/L1-REQUIREMENTS.md`, `docs/v2/A-audit/legacy-plans-carry.md`, `git log --summary --follow -- docs/plans` |

## 10. 完了条件
1. retention policy が文書化されている。
2. 68+ PLAN が V2 phase に紐付いている。
3. carry 吸収先または非吸収理由が全件にある。
4. archive 条件が Phase J / 1 年後 / 物理削除なしで固定されている。
5. mapping 数値整合と dependency chain の確認手順が記述されている。
