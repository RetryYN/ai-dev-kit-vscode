# PLAN-029: HELIX フレームワーク厳格化拡張

## メタデータ

- id: PLAN-029
- title: HELIX 11 軸厳格化拡張 (デザイン後置 / Sprint 厳格化 / フェーズゲート / デプロイ前 3 フェーズ / 大規模 agent 2 段設計 / Scrum 拡張 / L1-L3 設計厳格化 / 追加実装流れ / Reverse 厳格化 / 拡張性 × 制約性 / docs+helix.db 強化)
- status: draft
- priority: high
- created: 2026-05-08
- owners: PM, TL
- related: [PLAN-028, ADR-014, ADR-015]
- plan_id: PLAN-029
- task_id: W-0-outline
- sprints: W-1..W-12
- acceptance: 11 軸×12 Sprint の明示、Sprint 概要と DoD 抜粋、関連調査 stub、関連リンク整合

## 1. 背景・動機 (Why)

### 1.1 背景

HELIX v1 → v2 移行（PLAN-028）で orchestration と責務分離は定着したが、運用品質面は「通るべき手順を満たすだけで再現性・品質の底上げが追いついていない」状態が残る。

特に PMO 分離により作業分担は明文化された一方で、以下が残課題として露見している。

- 仕様品質と実装品質を同時に維持するゲート設計の厚み不足
- 受入前の検証順序と失敗時の carry/p0 ルールのばらつき
- L1-L3 の設計フェーズで、同一要件を跨いだ整合性（D-API / D-DB / D-CONTRACT / D-UI）が弱いケース
- docs と helix.db の記録粒度が異なり、追跡整合コストが増えている

### 1.2 目的

PLAN-029 は「品質側の厳格化拡張」を前提に、11 軸を横断した設計ルールを 12 Sprint で順序起草する。

目的は次の 3 点。

- フレームワークの柔軟性（拡張性）を守りつつ、逸脱抑止を強化（制約性）する。
- Sprint/フェーズ/Gate の実装ルールを統一し、再現可能な品質プロセスを標準化する。
- research と実装設計の接続を設計の前提（事前調査、実装設計、運用検証）として明文化する。

### 1.3 適用スコープ

- 対象: HELIX framework における L1-L3、L4-L7、L8、Run、Reverse 接続まで。
- 非対象: 設定値そのものの運用仕様（PLAN-028 以降で扱う）と、既存の実装既存資産の直接改修。
- 本文書は outline レベルで、詳細仕様は Sprint ごとの派生 SPEC で分離する。

### 1.4 進め方

- 1 つの Sprint で 1 つの主要要件（または 1 クラスタ）を扱う。
- 各 Sprint は 1 行要旨、依存、DoD、関連調査接続キーを持つ。
- 12 Sprint を終えた時点で、次の plan を W-1 〜 W-12 受入に接続して統合仕様化する。

## 2. 厳格化 11 軸の対応設計

### 2.1 要件 1.1: デザインを工程最後に配置

- 現状: FE driver の場合、ワイヤーと見た目色合わせの境界が薄く、L5 の後段でデザイン確定する一方で、早期モック変更が L4 実装へ引きずられやすい。
- 改善: L2-L4 で情報設計 + ワイヤー + UX を固定し、L5 を L5a/L5b に再分割する。
  - **L5a**: Visual Refinement（情報密度、構造、遷移優先度、アクセシビリティを定義）
  - **L5b**: Visual Production（配色、画像、アニメーション、最終見た目を L6.x 以降と整合）
- Sprint 反映: W-1 を中核に、W-10 で KPI 監査へ接続。
- 追記ルール: WIP の mock 版は承認前実装に使わず、W4 以降で L5b 固定。

### 2.2 要件 1.2: Sprint 単位の厳格化

- 各 Sprint は必ず完了時に以下を実施し、`Gx` 側に反映する。
  1) 設計デグレチェック（D-shard 間整合、handover、phase.yaml）
  2) TL からの実装レビュー（approve 必須）
  3) テスト実行（pytest + bats + lint + 型 + smoke）
  4) ビルド（対象あり）
- Sprint-level 完走の定義を W-2 で制度化し、`helix sprint complete` の Hook 化を検討。
- 成果物は 1) WBS、2) gate 証跡、3) 変更差分、4) テスト要約を最小セットで記録。
- 失敗時は次 Sprint を blocked とし、carry または rework を明文化。

### 2.3 要件 1.3: フェーズ単位ゲート + スプリント横断レビュー

- 既存の G1-G11 を「fail-close」で一段深め、現場側のスキップ定義を明確化。
- Sprint 完了時のみでなく、フェーズ終盤でも横断レビュー（仕様 / 実装 / リグレ）を行う。
- 横断レビューは 3 軸で採点: 
  - 仕様整合: WBS と要件マップ差分の有無
  - 実装品質: テスト/レビュー証跡の完全性
  - デグレ有無: 既存 plan 参照との矛盾チェック
- `helix gate --cross-sprint` を追加して、`Gx` 横断を CLI フラグ化。

### 2.4 要件 1.4: デプロイ前 3 フェーズ追加

- 現状の L7→L8 を L6 系に追加して、配備前検証を増量する。
  - **L6.5 Security Phase**: OWASP 全項目見直し、脅威モデリング再実施
  - **L6.7 Operations Phase**: scheduler / 運用ログ / リソース管理 / 開発者管理画面を実装接続
  - **L6.9 Visual Production Phase**: 画像・配色・アニメーションの最終実装（要件 1.1 の L5b と統合）
  - **L7**: 既存デプロイ工程
- Gate 追加: G6.5 / G6.7 / G6.9 を新設し、失敗時は L6 系に carry。
- この変更は run-phase（L9-L11）への接続を容易化し、受入前の「最後の手戻り」を減らす。

### 2.5 要件 1.5: 大規模 agent 2 段設計

- 現在の 1 段構成は、agent の数・複雑性が増えると設計責務が混在しやすい。
- L2-L3 で 2 段を分離。
  - **インフラ層設計**: runtime、state mgmt、orchestrator、observability を固定。通常は BE として扱う。
  - **エージェント層設計**: ツール定義、プロンプト、decision tree、失敗復帰を固定。
- 規模自動判定: `helix size --agent --large` で 2 段化を強制し、通常規模では既存 1 段まま。
- 変更は D-AGENT-INFRA / D-AGENT-EXEC で明示し、WIP の責務混線を防ぐ。

### 2.6 要件 1.6: Scrum フェーズ拡張

- 既存 S0-S4 に前段の S0.5（Web 検索事例検証）を追加。
- S1 は S1a（Plan）と S1b（受入条件設計）を明示。
- S2 は PoC 検証設計を明示してから実装へ進める。
- コマンド候補: `helix scrum web-search`（検索事例収集）および `helix scrum acceptance-design`（受入条件設計）を新設。
- 効果: 要件不確実時に PoC の成功条件を先に凍結し、後追い追加の乱立を抑制。

### 2.7 要件 1.7: L1-L3 設計フェーズ厳格化

- L1 で企画デグレ禁止ルールを明文化。
  - 企画項目は要件・受入条件・除外条件を明記。
- L1 の G0.5 を PoC 必要性判定強化へ拡張。
- L2 は技術スタック選定を ADR 付き正式フェーズへ。
  - 候補比較表、評価基準、選定根拠を ADR 化。
  - 各 L での Web 調査（または既存検索資産）を必須連携。
- L3 は D-shard 順序を固定。
  - D-API → D-DB → D-CONTRACT → D-UI
  - 各 shard 間ドリフトを drift-check で確認。
  - lint/formatter 方針は L3 で事前確定。
- G1.5 / G2 / G3 は整合性チェック項目を増やす。

### 2.8 要件 1.8: 追加実装の流れ整備

- 進行中タスクへ追加要求が入る場合は正式 mini-PLAN として扱う。
- mini-PLAN 最低 4 フェーズ: L1 → L2 → L4 → L6。
- 親 PLAN と dependency を Helix DB に登録し、並列 Sprint の影響追跡対象とする。
- 目的は「小さな追加を本筋に埋めない」ための明示的ルート化。

### 2.9 要件 1.9: Reverse 逆引き順序 + レビュー厳格化

- R0-R4 は既存構造を維持しつつ、Sprint レビュー責務を上位に追加。
- 各 R フェーズの完了条件に「レビュー記録」「引継ぎ資料」を必須化。
- `helix reverse rgc` に強化版オプションを追加し、閉塞状態を明示。
- Forward へ返す引継ぎは必須ドキュメント化し、未接続のまま次 L4 へ進まない。

### 2.10 要件 1.10: 拡張性 × 制約性両軸見直し

- Extension map を明文化。
  - skills / agents / hooks の拡張ポイントを示し、拡張自由度を保つ。
- 同時に fail-close を強化。
  - `helix doctor` / `drift-check` / gate の違反を未通過扱い。
- KPI（拡張性）
  - skill 推奨 hit_rate ≥ 80%
  - role 利用多様性
  - PLAN 種類分布
- KPI（制約性）
  - regress 0 維持
  - design drift 0 件
  - Sprint 完遂時間の上限監視
- 実装では「新機能拡張を許可」しつつ「逸脱は即時検知」を両立。

### 2.11 要件 1.11: README + docs + helix.db 強化

- README を HELIX 全体図に合わせて更新し、Quick Start と運用導線を再整理。
- docs 構造を再構成し、architecture / adr / plans / research / runbook を明確化。
- helix.db schema migration を追加し、axis や design_decision / qa_result / security_audit を記録できるようにする。
- helix doctor を更新して、docs と DB の整合を自動チェック対象に追加。

## 3. Sprint 分割（12 Sprint）

| Sprint | テーマ | 担当 | 依存 | 並列 | 1行概要 |
|---|---|---|---|---|---|
| W-1 | デザイン後置 + Visual Refinement 強化 | docs+SE | 単独 | ‖ W-2,W-5,W-6,W-7,W-9 | L5 を L5a/L5b 分離し、最終デザイン適用を後置化する |
| W-2 | Sprint 単位厳格化 | SE | 単独 | 同上 | Sprint 完了条件の必須項目を仕様化し、hook 自動化検討を開始 |
| W-3 | フェーズゲート強化 + 横断レビュー | SE | W-2 | — | 失敗時に再work する cross-sprint gate ループを設計 |
| W-4 | デプロイ前 3 フェーズ追加 | SE | W-3 | — | L6.5 / L6.7 / L6.9 を追加し、G6 系を拡張 |
| W-5 | 大規模 agent 2 段設計 | docs+SE | 単独 | ‖ W-1,W-2,W-6,W-7,W-9 | D-AGENT-INFRA と D-AGENT-EXEC を分離し、サイズ判定で強制切替 |
| W-6 | Scrum 拡張 | docs+SE | 単独 | 同上 | S0.5 と S1a/S1b を追加し、PoC 受入条件を明文化 |
| W-7 | L1-L3 設計厳格化 | docs+SE | 単独 | 同上 | D-shard順と ADR 化を設計フェーズに埋め込む |
| W-8 | 追加実装流れ整備 | docs | W-2 | — | mini-PLAN を helix plan 構文として公式化し、依存追跡を追加 |
| W-9 | Reverse 厳格化 | docs | 単独 | ‖ W-1..W-7 | R0-R4 関係の sprint-review と handover 義務を追加 |
| W-10 | 拡張性×制約性（集約） | TL | W-2..W-9 | — | KPI 設計と gate 運用を集約し観測基準を確定 |
| W-11 | README/docs/helix.db 強化 | docs+SE | 全完了後 | — | docs 構造再整理と schema migration で基盤整合 |
| W-12 | 統合検証 + retrospective | qa | 全完了後 | — | 全 Gate/全セキュリティ/全レビューを統合して retrospective を保存 |

### 3.1 並列性計画

- 第 1 波: W-1, W-2, W-5, W-6, W-7, W-9（6 Sprint）
- 第 2 波: W-3, W-8（W-2 以降）
- 第 3 波: W-4（W-3 以降）
- 第 4 波: W-10, W-11, W-12（全完了後）

### 3.2 総セッション想定

- 12-15 セッション（短集中で前半 4 波、後半 3 波）
- 1-2 週間を標準幅として見積るが、risk register を見ながら 1 波目を短縮も可。

## 4. 11 軸 × 12 Sprint 受入 DoD 概要（outline）

- W-1 DoD 概要: L5 を L5a/L5b に明確分割し、phase.yaml 拡張と G5 追加要件を draft。
- W-2 DoD 概要: `helix sprint complete` で lint/test/build/drift-check の自動実行を確認する設計。
- W-3 DoD 概要: `helix gate --cross-sprint` を実装し、デグレ検知チェックを明示。
- W-4 DoD 概要: phase.yaml に L6.5/L6.7/L6.9 を追加、各 G6 新設で fail-close 設計。
- W-5 DoD 概要: D-AGENT-INFRA / D-AGENT-EXEC を 2 段化し、`helix size --agent --large` 連動を確認。
- W-6 DoD 概要: `helix scrum web-search` と `acceptance-design` subcommand の stub 実装に必要項目を整理。
- W-7 DoD 概要: 研究連動・tech-stack ADR・D-shard 順序の L3 固定を設計 DoD として確立。
- W-8 DoD 概要: mini-PLAN を親 PLAN 依存追跡付きで helix plan 拡張。
- W-9 DoD 概要: 逆引き各 R の sprint review 追加と handover 義務化。
- W-10 DoD 概要: 拡張性 KPI と制約性 KPI の観測設計を ADR 化。
- W-11 DoD 概要: README 改稿、docs 再編、helix.db migration を確定方針化。
- W-12 DoD 概要: 全 gate pass + full test + retrospective 記録。

### 4.1 依存/整合の軸チェック

- Axis 1.1, 1.2, 1.3 は W-1〜W-4 で連続検証。
- Axis 1.4, 1.5 は W-4〜W-5 で設計-実装接続。
- Axis 1.6, 1.7 は W-6〜W-7 でリードタイムを圧縮。
- Axis 1.8, 1.9 は W-8〜W-10 で運用移行。
- Axis 1.10, 1.11 は W-10〜W-11 で評価・保存基盤へ反映。

## 5. 関連調査（research integration ストブ）

本 outline は research dispatch 並行成果を取り込む前提として、以下を `TBD` stub で残す。

- A. Sprint-level rigorous review: TBD
- B. Phase gate enforcement: TBD
- C. Multi-stage agent system 2-tier: TBD
- D. Scrum hypothesis validation: TBD
- E. L1-L3 design rigor: TBD
- F. Reverse engineering review: TBD
- G. 拡張性×制約性: TBD
- H. agent observability: TBD
- I. helix.db / event log: TBD
- J. design drift detection: TBD
- K. AI-driven development best practice 2026: TBD

## 6. リスクと回避策

| リスク | 影響 | 回避策 |
|---|---|---|
| 12 Sprint が 1-2 週間で収束しない | ユーザー期待と進捗乖離 | W-1〜W-7 を優先実行し、W-3〜W-4 と W-10〜W-12 は次 PLAN へ分離する判断条件を事前明記 |
| L5b / L6.5 / L6.7 / L6.9 の追加で既存 PLAN と衝突 | 既存ルールとの互換崩れ | phase.yaml semver bump と既存運用 v1 対応を並走。新規 PLAN のみ新フェーズ適用 |
| migration 増加による破壊的変更 | DB 整合破壊 | v18→v19 migration を W-11 で分離実行し、既存 entries 互換移行手順を事前公開 |
| research と spec の食い違い | 仕様の先行誤差 | research 完了後に §4 を refreshする追加 pass を W-12 前提条件に加える |
| 要件解釈の個別差 | 承認遅延・rework 増 | axis 1.10 の指標と受入言語を user-facing 言語で確認し、W-10 で最終合意 |
| 実装を要する task への過剰拡張 | スコープ拡大 | PLAN-029 は outline とし、詳細は W-11 以降で個別 Sprint spec 化 |

### 6.1 エスカレーション基準

- 要件 1.4 と 1.11 は helix.db migration に関わるため、破壊的変更の可能性がある場合は事前にユーザー確認を要求。
- 変更対象が既存 PLAN の既定動作を直接置換する場合は `interrupted` とし、事前合意を追加する。

## 7. 関連ドキュメント

- [PLAN-028-helix-v2-orchestration.md](docs/plans/PLAN-028-helix-v2-orchestration.md)
- [ADR-014-roles-config-format.md](docs/adr/ADR-014-roles-config-format.md)
- [ADR-015-helix-v2-orchestration.md](docs/adr/ADR-015-helix-v2-orchestration.md)
- メモ: `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/project_2026_05_08_plan029_helix_rigor.md`
- 研究結果: `docs/research/PLAN-029-research-findings.md`（並行作成、後で integrate）

---

## 8. 章立て整合ノート（作成時確認）

- メタデータ
- 1. 背景・動機
- 2. 厳格化 11 軸の対応設計
- 3. Sprint 分割（12 Sprint）
- 4. 11 軸 × 12 Sprint 受入 DoD 概要
- 5. 関連調査（research integration stub）
- 6. リスクと回避策
- 7. 関連ドキュメント

## 9. 進捗検証用サマリ（アウトライン）

- 作成済み: `docs/plans/PLAN-029-helix-rigor-expansion.md`
- 想定行数: 約 340-360 行
- Sprint 数: 12（W-1〜W-12）
- 11 軸: 2.1〜2.11 で明示
- research 統合: §5 を stub のまま維持
- TODO/FIXME: 本稿では `TBD` を研究未確定プレースホルダとして使用。`TODO`/`FIXME` は本文に未使用

## 10. 11 軸 × Sprint 参照マップ（詳細）

### 10.1 軸-スプリント割当

- Axis 1.1: W-1, W-10（KPI で効果確認）
- Axis 1.2: W-2, W-10（全体品質報告）
- Axis 1.3: W-3, W-10, W-12
- Axis 1.4: W-4, W-12（安全性検証含む）
- Axis 1.5: W-5, W-7（設計順接続）
- Axis 1.6: W-6
- Axis 1.7: W-7, W-10（ADR とレビュー接続）
- Axis 1.8: W-8, W-9（引継ぎ）
- Axis 1.9: W-9, W-12（逆引きの受入）
- Axis 1.10: W-10
- Axis 1.11: W-11, W-12（整合チェック）

### 10.2 監査観点（各軸）

- 1.1: ワイヤー先行/見た目後置が L4 前に混入していないか
- 1.2: Sprint 完了時に 1 つでも必須項目欠落していないか
- 1.3: cross-sprint gate の定義が Gx リストへ接続されているか
- 1.4: L6.5/L6.7/L6.9 の順序と責務境界が定義済みか
- 1.5: 2段設計における責務分離（infra/prompt）が明示されているか
- 1.6: Scrum 追加フェーズに受入条件が紐づいているか
- 1.7: 技術スタック ADR と D-shard 順序が同一ドキュメントで固定されているか
- 1.8: mini-PLAN が親PLAN依存と同居で追跡されるか
- 1.9: R0-R4 引継ぎが forward に必須提出されるか
- 1.10: 制約性 KPI が受入条件に含まれ、更新ログが残るか
- 1.11: helix.db migration とドキュメント整合チェックが同時で実行されるか

### 10.3 Sprint 毎の補助チェック

- W-1: L5a/L5b の境界線を phase yaml で確認
- W-2: hook 化可能性チェックリストの起票
- W-3: cross-sprint オプションの失敗時リカバリ指針確認
- W-4: L6.x と L7 のハンドオーバー条件確認
- W-5: `--large` 判定条件の説明責任（なぜ 2 段なのか）を記録
- W-6: S0.5 の入力（検索）と S1b の受入条件の同期確認
- W-7: D-API/D-DB/D-CONTRACT/D-UI の順序違反アラート定義
- W-8: mini-PLAN で依存グラフが循環しないこと
- W-9: Reverse 各 R で必須テンプレートと引継ぎの有無
- W-10: 2 指標（拡張性/制約性）を採点式で保存
- W-11: docs 再編時の既存リンク切れと重複参照の監査
- W-12: 12 Sprint 全体で gate pass と sprint pass の整合

## 11. 受入チェックテンプレ（レビュー/Docs向け）

- 作成済みか: ファイル存在有無
- 章構成: Metadata + 7 章相当 + 11 軸 + Sprint 12件 + 研究 stub
- 11 軸: 2.1〜2.11 を確認
- Sprint: W-1〜W-12 の全行が存在
- 参照: PLAN-028, ADR-014, ADR-015 のリンク整備
- 依存: research stub が §5 に残っていること
- 行数: 350行前後（本文規模で 1 パス読了が可能）

## 12. 追加メモ（実装方針）

### 12.1 ドキュメント運用

- 主要変更は outline 文書で受け止め、詳細は Sprint-1〜Sprint-12 の派生ドキュメントに委譲。
- 研究反映時は §4 を更新し、TBD を確定内容に置換する。

### 12.2 追加実装との分離

- 本 PLAN はあくまで実施順起票。
- 実コード変更（CLI/DB/Phase schema）は W-11 の別 SPEC で扱い、PLAN-029 本体から分離。

### 12.3 承認想定の明示

- 本 outline は draft であり、総合承認は W-12 統合検証時に行う。
- 重要決定（DB migration、runbook 変更、gate 追加）は次 Sprint 仕様で再確認し、受入条件を再確定。
