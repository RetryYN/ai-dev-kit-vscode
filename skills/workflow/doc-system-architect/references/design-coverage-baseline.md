# Design Coverage Baseline
> 目的: L4 基本設計 / L5 詳細設計 / L6 機能設計 を着工する前に「業界標準としてどの文書・どの viewpoint・どこまで揃えば充足か」を確定するカバー基準チェックリスト。doc-system-architect が L1/L2 で出す成果物であり、設計工程の前段関所。

## §1 日本 SI ↔ 英語標準 viewpoint 対応

| 日本 SI 用語 | HELIX 工程 | 英語標準 | 注意 |
|---|---|---|---|
| 基本設計(外部設計) | L4 | Architectural Design (ISO/IEC/IEEE 42010:2022 / arc42 / C4) | 日本 SI の「画面設計」は HELIX では L2、「ER設計」は L5 に分離 |
| 詳細設計(内部設計) | L5 | Detailed Design (IEEE Std 1016-2009 viewpoints) | クラス図/シーケンス図/モジュール構造図/ER が標準成果物 |
| 機能設計(プログラム設計) | L6 | Functional/Module Design | 関数・メソッド仕様。単体テストが直接対応する粒度 |

## §2 L4/L5/L6 境界の機械判定原則

- L4 基本設計: 外側向き。「何を・どこに・どう分割するか」。コンポーネント間・外部IF・主要技術判断(ADR)。
- L5 詳細設計: 内側向き。「どう協調するか・データ永続化・依存関係」。モジュール間の静的/動的関係。
- L6 機能設計: 実装直前。「各関数が何をどのアルゴリズムで処理するか」。単体テストが直接対応。
- 判定: シーケンス図が「コンポーネント間」=L4 Composition、「モジュール内部呼出」=L5 Interaction。「クラスの存在(型定義)」=L5 Logical、「メソッド内ロジック」=L6 Algorithm。

## §3 カバー基準チェックリスト

### L4 基本設計

| ID | 成果物 | 典拠標準 | 必須/推奨 | HELIX-workflows V2 現状 (grep 実証) |
|---|---|---|---|---|
| L4-01 | システムコンテキスト図(外部境界・アクター) | IEEE1016 Context + arc42§3 | 必須 | 充足: 独立設計書 helix-workflows-system-context.md §1-3 (recovery 独立化) |
| L4-02 | ビルディングブロック図(主要コンポーネント・責務割当) | IEEE1016 Composition + arc42§5(唯一の mandatory) | 必須 | 充足 (system-architecture §1) |
| L4-03 | ADR | ISO42010 Correspondence + arc42§9 + Nygard | 必須 | 充足 (ADR-044/045) |
| L4-04 | デプロイ/方式設計 | arc42§7 | 本番運用ありなら必須 | N/A 宣言が必要 (CLI ローカルツールで大半 N/A だが明示なし) |
| L4-05 | Stakeholder×Concern マトリクス | ISO42010 §5.2 | 推奨 | 充足: 独立設計書 helix-workflows-system-context.md §4 (6×6 matrix) |
| L4-06 | NFR(ISO25010:2023 9特性)↔アーキ設計戦略 mapping | ISO42010 + arc42§4 + 25010 | 推奨 | 薄い (arc42§10+Concern で言及あるが L3 への pointer 中心) |
| L4-07 | 依存関係マップ | IEEE1016 Dependency | 推奨 | L5 module-decomposition でカバー |
| L4-08 | 総合テスト設計(V-model L4↔L9 pair) | ISO29119-4 | 必須(HELIX) | 充足 |
| L4-09 | 脅威分析/セキュリティ viewpoint(攻撃面・信頼境界・STRIDE等) | threat-model(STRIDE) + arc42§10 + ISO25010:2023 Security/Safety | 必須(セキュリティ関心事あれば) | 充足: 独立設計書 helix-workflows-threat-model.md (recovery 独立化、L9 ST-9 pair) |

**充足判定**: L4-01+L4-02+L4-03+L4-08 で最低充足。本番運用あれば L4-04 必須。セキュリティ関心事(認証/権限/guard/fail-close 等)があれば L4-09 必須。HELIX-workflows V2 は hook guard / fail-close を持つため L4-09 該当。

### L5 詳細設計

| ID | 成果物 | 典拠標準 | 必須/推奨 | HELIX-workflows V2 現状 (grep 実証) |
|---|---|---|---|---|
| L5-01 | モジュール/クラス構造図(静的関係・型設計) | IEEE1016 Logical | 必須 | module-decomposition + L6 class-module-command でカバー |
| L5-02 | シーケンス/インタラクション図 | IEEE1016 Interaction | 必須 | internal-processing に擬似コード+状態遷移 mermaid あり、明示シーケンス図は薄い |
| L5-03 | API/IF契約(D-API) | IEEE1016 Interface | 必須 | 充足 (interface-detailed-design) |
| L5-04 | データ設計(D-DB: ER/テーブル/永続化) | IEEE1016 Information | 必須 | 充足 (physical-data-design) |
| L5-05 | 依存詳細・モジュール分割 | IEEE1016 Dependency | 推奨 | 充足 (module-decomposition) |
| L5-06 | 横断的関心事設計(ロギング/エラー/トランザクション/セキュリティ横断) | IEEE1016 Patterns use + arc42§8 | 推奨 | 充足: 独立設計書 helix-workflows-cross-cutting-design.md (recovery 独立化) |
| L5-07 | 状態遷移図 | IEEE1016 State Dynamics | 状態を持つなら推奨 | internal-processing でカバー(mode transition/evolution lifecycle) |
| L5-08 | リソース/性能設計 | IEEE1016 Resource | SLO あれば推奨 | 薄い |
| L5-09 | 結合テスト設計(V-model L5↔L8 pair) | ISO29119-4 | 必須(HELIX) | 充足 |

**充足判定**: L5-01+L5-02+L5-03+L5-04+L5-09 で最低充足。

### L6 機能設計

| ID | 成果物 | 典拠標準 | 必須/推奨 | HELIX-workflows V2 現状 (grep 実証) |
|---|---|---|---|---|
| L6-01 | エンドポイント/関数仕様(入出力スキーマ・事前事後条件・副作用) | IEEE1016 Interface(機能粒度) | 必須 | 充足 (function-spec-design 型注釈付き signature) |
| L6-02 | アルゴリズム/処理ロジック仕様 | IEEE1016 Algorithm | 複雑ロジックあれば必須 | internal-processing(L5)+function-spec でカバー |
| L6-03 | エラー処理設計(エラーコード体系・例外方針・リトライ) | IEEE1016 Algorithm | 必須(全体統一) | edge-case-design でカバー(exit code 体系+EP-001〜008) |
| L6-04 | 状態・イベント定義(機能粒度) | IEEE1016 State Dynamics | 状態機械あれば推奨 | 部分 |
| L6-05 | 単体テスト設計(V-model L6↔L7 pair・境界値・異常系) | ISO29119-4 | 必須(HELIX) | 充足 (edge-case-design 71件) |

**充足判定**: L6-01+L6-05 で最低限。複雑処理は L6-02 必須。

## §4 採用上の注意 (アンチパターン)

- arc42 で mandatory は §5 のみ。「12 章全部書く」は誤解。
- IEEE1016 12 viewpoint は選択的に使う標準。全 viewpoint を揃えることの目的化(形式主義)を避ける。
- 日本 SI の「基本設計=画面設計+ER設計」と HELIX L4 は一致しない(画面設計=L2、ER=L5)。混同すると V-model が崩れる。

## §5 ゲートとしての運用

- 設計工程 (L4/L5/L6) entry で本チェックリストを通す。各層「最低充足」セットを満たさず frozen 化しない。
- helix doctor 機械 lint 候補 (本 recovery の L14 carry): `check_design_coverage` (脅威分析節/NFR↔arch mapping/context view の有無を frozen 前に検査)。
- 関連: この基準が未確定のまま設計着工した工程逸脱が recovery-2026-05-30-design-coverage-baseline の発火原因。
