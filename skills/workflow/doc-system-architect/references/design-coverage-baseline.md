---
title: 設計カバレッジ基準（業界標準対応表 + 粒度ペアリング原則）
doc_id: design-coverage-baseline
owner: doc-system-architect
status: active
created: 2026-05-30
updated: 2026-05-31
related:
  - L4-basic-design
  - L5-detailed-design
  - L6-functional-design
  - test-perspective-gate
standards:
  - ISO/IEC/IEEE 29148:2018   # 要求定義 (StRS/SRS) — https://www.iso.org/standard/72089.html
  - ISO/IEC/IEEE 42010:2022   # アーキテクチャ記述 — https://www.iso.org/standard/74393.html
  - IEEE Std 1016-2009        # Software Design Descriptions (viewpoints) — https://standards.ieee.org/ieee/1016/4502/
  - ISO/IEC/IEEE 29119-4:2021 # テスト設計技法 (境界値/同値/状態遷移 等)
  - ISO/IEC 25010:2023        # 製品品質モデル (9 特性)
  - arc42                     # アーキテクチャ doc 構成 — https://arc42.org/overview
  - "Design by Contract"      # 事前/事後/不変条件 — https://en.wikipedia.org/wiki/Design_by_contract
---

# 設計カバレッジ基準（業界標準対応表 + 粒度ペアリング原則）

> 各設計層 (L4/L5/L6) の設計成果物が、業界標準のどの viewpoint を、**どの粒度で**カバーすべきかの基準。
> 設計着工前にこのチェックリストで「カバー範囲の合意」を取り (entry 関所)、設計完了時に「カバー充足」を判定する (exit 関所)。
> **目的**: 「何を・どの粒度で書けばカバーした扱いになるか」を曖昧にしたまま設計を始めて、後で漏れ (特に L6 の薄化) に気づく事故を防ぐ。
> **適用範囲**: 詳細設計 (L5) までは業界標準をそのまま採用する。機能設計 (L6) は業界標準 (IEEE 1016 関数粒度 + Design by Contract) を **単体テスト粒度** に固定して採用する。

## §0 粒度ペアリング原則（本基準の背骨）

HELIX Core §1 の V モデル「設計⇔検証の対」は、**量 (Chargaff's rule) だけでなく粒度 (grain) でも閉じる**。
すなわち —

> **設計ドキュメントは、対になる検証層のテスト設計と同じ粒度で書く。機能設計 (L6) は単体テスト (L7) の粒度で書く。**

設計を「対の検証より粗い粒度」で書くと、設計とテストの量・対応が機械的に閉じず、片肺・カバレッジ薄化が発生する。
特に L6 を L5 (モジュール) 粒度で書くと、関数 1 個 ↔ 単体テストケース N 件の対応が取れず、L6 が「L5 の焼き直し」になって薄くなる (これが現状の薄化の根本原因)。

> 本 § は HELIX Core §1 V モデル「設計⇔検証の対」の粒度軸の正本 (参照: HELIX Core §0/§1)。量 (Chargaff) と粒度 (grain) の両方で対を閉じる拡張であり、Core §0 絶対原則の内側にある。

### 粒度ペアリング表（正本）

| pair | 設計層 | 検証層 | 粒度 (grain) | 設計成果物の単位 | テスト設計の単位 |
|---|---|---|---|---|---|
| L1↔L14 | L1 要求定義 | L14 運用学習 / 運用改善 | 運用 / ビジネス粒度 | 要求項目 (BR / FR) | 運用テストシナリオ |
| L2↔L10 | L2 画面設計 | L10 フロントUX | 画面 / UX 粒度 | 画面・ワイヤーフレーム | UX 検証シナリオ |
| L3↔L12 | L3 要件定義 | L12 受入テスト | 受入 / 外部仕様粒度 | 要件項目 (機能要件) | 受入テストケース |
| L4↔L9 | L4 基本設計 | L9 総合テスト | システム / コンポーネント粒度 | コンポーネント・外部 IF | 総合テストシナリオ |
| L5↔L8 | L5 詳細設計 | L8 結合テスト | モジュール / 結合粒度 | モジュール・モジュール間 IF | 結合テストケース |
| **L6↔L7** | **L6 機能設計** | **L7 単体テスト** | **関数 / 単体粒度** | **関数仕様 (DbC: 事前/事後/不変)** | **単体テストケース** |

> L2↔L10 は画面を持つプロダクトのみ有効 (Project profile で L2/L10 skip 時は除外)。HELIX-workflows 自身は UI を持たないため本 pair は N/A。
>
> 注: L4 の典拠は ISO/IEC/IEEE 42010:2022 + arc42 (アーキテクチャ記述標準)。IEEE Std 1016-2009 (SDD) は L5/L6 専用に割り当てる。L4 設計に 1016 viewpoint を主典拠として使わない。

### 粒度整合の判定規則（機械判定可能）

1. **同粒度規則**: 設計成果物の最小単位が、対の検証層のテスト設計の最小単位と一致すること。
   - L6 で「モジュール」「クラス」までしか分解していない (= L5 粒度) → **不合格** (粒度違反)。L6 は関数 / メソッド単位まで分解する。
2. **量保証規則 (Chargaff)**: `balance_ratio = (対の検証層の) テスト設計件数 / 設計項目件数 ≥ 1.0` を pair ごとに満たすこと。
   - 件数の計測単位は「項目数」(設計項目 = 成果物内の最小設計単位エントリ数、テスト設計 = テストケース数)。
   - L6 の実体: `balance_ratio(L6) = 単体テストケース件数 / 関数仕様件数 ≥ 1.0` (正常系最低 1 + 境界 + 異常系を推奨)。
3. **片肺禁止規則**: 設計層の成果物が存在して検証層が空、またはその逆を許さない (fail-close)。

## §1 日本 SI ↔ 英語圏標準 viewpoint 対応

| 工程 | HELIX 層 | 英語圏標準 | 主要 viewpoint | 業界基準の扱い |
|---|---|---|---|---|
| 基本設計（外部設計） | L4 | ISO/IEC/IEEE 42010:2022 / arc42 / C4 | Context, Building Block, Runtime, Deployment | そのまま採用 |
| 詳細設計（内部設計） | L5 | IEEE Std 1016-2009 | Logical, Dependency, Interface, Interaction, State, Information | そのまま採用 |
| 機能設計（プログラム設計） | L6 | IEEE 1016 Interface(関数) + Algorithm + **Design by Contract** | Interface(関数), Algorithm, State(機能), Data | **単体テスト粒度に固定して採用** |

> 出典は frontmatter `standards` 参照。L4/L5 は業界標準を viewpoint 単位でそのまま割り当てる。L6 は IEEE 1016 の Interface/Algorithm viewpoint を「関数 1 個 = 単体テスト対象 1 個」の粒度に落とし、Design by Contract (事前/事後/不変条件) で契約を明示する。

## §2 境界判定原則（機械判定可能）

| 設計レベル | 判定基準 | 粒度の例 | 対応テスト粒度 |
|---|---|---|---|
| L4 | コンポーネント間・外部 IF・主要技術判断 | 「認証サービスと API ゲートウェイ間の通信方式」 | 総合テスト (L9) |
| L5 | モジュール間の静的/動的関係・データ永続化 | 「UserService と UserRepository の依存関係」 | 結合テスト (L8) |
| L6 | 各関数のアルゴリズム・事前事後条件・単体テストが直接対応する粒度 | 「validateEmail() の事前条件・処理手順・境界値・例外」 | 単体テスト (L7) |

判定の決め手は「**対になるテストがどの粒度で書けるか**」。総合テストで検証する事項は L4、結合テストなら L5、単体テストで 1:1 に検証できる事項は L6。

## §3 カバー基準チェックリスト

### L4（基本設計）= ISO/IEC/IEEE 42010:2022 + arc42 + C4 — 粒度: システム/コンポーネント (↔ L9)

| ID | 成果物 | 典拠標準 | 必須/推奨 | HELIX-workflows V2 現状 |
|---|---|---|---|---|
| L4-01 | システムコンテキスト図 | ISO42010:2022 + arc42§3 (Context view) | 必須 | ✅ helix-workflows-system-context.md |
| L4-02 | ビルディングブロック図 | ISO42010:2022 + arc42§5 (Building Block view) | 必須 | ✅ 方式設計.md §1 |
| L4-03 | ADR | ISO42010 + arc42§9 + Nygard | 必須 | ✅ ADR-044/045 |
| L4-04 | デプロイ設計 | arc42§7 | 本番運用ありなら必須 | ⚠️ CLI ツールのため簡略 |
| L4-05 | Stakeholder×Concern | ISO42010 §5.2 | 推奨 | ✅ system-context.md §4 |
| L4-06 | NFR↔アーキ戦略 mapping | ISO42010 + arc42§4 + 25010:2023 | 推奨 | ⚠️ 部分的 |
| L4-07 | 依存関係マップ | IEEE1016 Dependency | 推奨 | ⚠️ L5 に委譲 |
| L4-08 | 総合テスト設計（L4↔L9 pair） | ISO29119-4 | 必須(HELIX) | ✅ L9-test-design/ |
| L4-09 | 脅威分析/セキュリティ viewpoint（独立doc） | threat-model(STRIDE) + arc42§10 + 25010:2023 Security/Safety | セキュリティ関心事あれば必須・**独立doc** | ✅ helix-workflows-threat-model.md |

最低充足: L4-01 + L4-02 + L4-03 + L4-08。セキュリティ関心事あれば L4-09 も必須。
粒度: 各成果物がコンポーネント/外部 IF 単位で、L9 総合テストシナリオと対応すること。

### L5（詳細設計）= IEEE Std 1016-2009 viewpoints — 粒度: モジュール/結合 (↔ L8)

| ID | 成果物 | 典拠標準 | 必須/推奨 | HELIX-workflows V2 現状 |
|---|---|---|---|---|
| L5-01 | モジュール/クラス構造図（静的関係・型設計） | IEEE1016 Logical | 必須 | ✅ モジュール分割設計.md |
| L5-02 | シーケンス/インタラクション図 | IEEE1016 Interaction | 必須 | ⚠️ 部分的 |
| L5-03 | API/IF契約（D-API） | IEEE1016 Interface | 必須 | ✅ IF詳細設計.md |
| L5-04 | データ設計（D-DB: ER/テーブル/永続化） | IEEE1016 Information | 必須 | ✅ 物理データ設計.md |
| L5-05 | 依存詳細・モジュール分割 | IEEE1016 Dependency | 推奨 | ✅ モジュール分割設計.md |
| L5-06 | 横断的関心事設計（ロギング/エラー/セキュリティ横断・独立doc） | IEEE1016 Patterns + arc42§8 | 推奨・**独立doc** | ✅ cross-cutting-design.md |
| L5-07 | 状態遷移図 | IEEE1016 State viewpoint | 状態を持つなら推奨 | ⚠️ 部分的 |
| L5-08 | リソース/性能設計 | IEEE1016 Resource | SLO あれば推奨 | ❌ 薄い |
| L5-09 | 結合テスト設計（L5↔L8 pair） | ISO29119-4 | 必須(HELIX) | ✅ 充足 |

最低充足: L5-01 + L5-02 + L5-03 + L5-04 + L5-09。
粒度: 各成果物がモジュール/モジュール間 IF 単位で、L8 結合テストケースと対応すること。

### L6（機能設計）= IEEE 1016 Interface(関数) + Algorithm + Design by Contract — 粒度: 関数/単体 (↔ L7)

> **L6 の粒度規律**: すべての成果物を「関数 / メソッド 1 個 = 単体テスト対象 1 個」の粒度まで分解する。
> モジュール / クラス止まり (L5 粒度) は粒度違反 → 不合格。各関数仕様は Design by Contract の 3 要素 (`requires:` 事前条件 / `ensures:` 事後条件 / `invariant:` 不変条件) を持ち (`requires`/`ensures` は全関数必須、`invariant` は状態を保持する unit で必須)、これが L7 単体テストの入力値・アサーション設計を直接導く。

| ID | 成果物 | 典拠標準 | 必須/推奨 | 粒度要件 | HELIX-workflows V2 現状 |
|---|---|---|---|---|---|
| L6-01 | 関数/メソッド仕様（入出力スキーマ + DbC: requires/ensures/invariant + 副作用） | IEEE1016 Interface(関数) + Design by Contract | 必須 | 関数 1 個 = 1 仕様 | ❌ 未着手 |
| L6-02 | アルゴリズム/処理ロジック仕様（手順・計算量・分岐） | IEEE1016 Algorithm | 複雑ロジックあれば必須 | 関数内処理単位 | ❌ 未着手 |
| L6-03 | エラー処理設計（エラーコード体系・例外方針・リトライ） | IEEE1016 Algorithm | 必須(全体統一) | エラーパス単位 | ❌ 未着手 |
| L6-04 | 状態・イベント定義（機能粒度） | IEEE1016 State viewpoint | 状態機械あれば推奨 | 状態遷移 1 個単位 (関数 scope に落とすか L5 State の詳細化) | ❌ 未着手 |
| L6-05 | 単体テスト設計（L6↔L7 pair・正常系/境界値/異常系/副作用） | ISO29119-4 | 必須(HELIX) | テストケース単位 | ❌ 未着手 |

最低充足: L6-01 + L6-05。複雑処理がある場合は L6-02 も必須。
**粒度充足判定**: L6-01 の関数仕様 1 件ごとに、L6-05 の単体テストケースが ≥ 1 件 (`balance_ratio ≥ 1.0`)。DbC の `requires/ensures` が空の関数仕様は不合格。

> **誤り例 (薄化アンチパターン)**: L6 を「モジュール XXX は YYY を行う」という L5 粒度の文で済ませる / 関数仕様に DbC を書かず L5 内部処理設計を引き写す / 単体テスト設計を「L5 結合テストでカバー」と先送りする。いずれも粒度ペアリング原則 (§0) 違反。

## §4 粒度カバレッジ薄化防止機構（L6 を薄くしない仕組み）

L6 が薄くなる構造的原因と、それを機械で塞ぐ機構を対応づける。

| 薄化原因 | 防止機構 | 機械判定 (carry: `helix doctor check_design_coverage`) |
|---|---|---|
| L4 機能構成設計が「関数仕様は L6 送り」と委任 → 概念だけ L4 に吸収 | L6 の物理ファイル存在を必須化 | `docs/v2/L6-functional-design/FR-*/` の存在検査 |
| L6 を L5 粒度で書いて単体テストに届かない | DbC 必須化 + 同粒度規則 (§0) | 各関数仕様に `requires:`/`ensures:` (状態保持 unit は `invariant:` も) フィールド存在検査 |
| 単体テスト設計を L5/L7 に先送り → pair 片肺 | Unit Interface Contract Matrix + 量保証 | `balance_ratio = 単体テスト件数 / 関数仕様件数 ≥ 1.0` 検査 |
| PLAN が generates 宣言だけで成果物未生成 | gate の file 存在 fail-close | G6 で L6/L7 物理ファイル不在なら gate fail |

### Unit Interface Contract Matrix（L6 trace の単位）

L6 では `unit_id → contract(requires/ensures/invariant) → test_id` の 3 列マトリクスを成果物に含める。
これにより HELIX DB の trace / drift 検出が関数単位で機械的に閉じ、`unit_id` 単位で「設計あり・テストあり」を双方向確認できる。

## §5 運用 — L 単位ワークフロー（entry / exit 関所）

各設計層 (L4/L5/L6) の進行は、本基準を entry / exit の関所として通す。**以降の設計工程はこの関所列に従えば、粒度違反・カバレッジ薄化・片肺を機械的に防げる。**

```
[entry 関所] ──→ [設計作業] ──→ [exit 関所] ──→ 次 L へ
  │                              │
  ├ §3 の必須成果物リストを合意    ├ §3 最低充足セットを満たすか
  ├ §0 粒度ペアリング表で          ├ §0 粒度整合の判定規則 3 つを満たすか
  │   「対の検証粒度」を確認        │   (同粒度 / 量保証 balance_ratio≥1.0 / 片肺禁止)
  └ 業界標準 viewpoint を割当       └ §4 薄化防止機構の機械判定を通す
```

| L | entry で合意する成果物 | exit で満たす条件 | 対の検証層 |
|---|---|---|---|
| L4 | §3 L4 必須 (L4-01/02/03/08) | システム粒度 + L9 pair balance_ratio≥1.0 | L9 総合テスト |
| L5 | §3 L5 必須 (L5-01/02/03/04/09) | モジュール粒度 + L8 pair balance_ratio≥1.0 | L8 結合テスト |
| L6 | §3 L6 必須 (L6-01/05) + DbC 規律 | 関数粒度 + L7 pair balance_ratio≥1.0 + DbC 充足 | L7 単体テスト |

- **将来の機械化 (carry)**: `helix doctor check_design_coverage` で entry/exit を機械チェック化する。検査対象 = ①§3 必須成果物の物理ファイル存在 ②§0 同粒度規則 (L6 の DbC フィールド存在) ③balance_ratio≥1.0 ④片肺検出。G6 ゲート (gate-policy.yaml) に組み込む。

> このドキュメントは doc-system-architect skill の参照資料であり、HELIX Core §1 V モデル「設計⇔検証 pair 凍結」の粒度軸の正本。各設計工程の entry/exit で参照する。
