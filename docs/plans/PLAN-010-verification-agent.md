# PLAN-010: 検証ツール選定 + 検証方法設計エージェント (v1)

## §1. 目的 / Why

PLAN-006〜PLAN-009 で整備された `上流メタ` / `Scrum 差し込み` / `Reverse 多系統化` / `Run 工程` の方針を接続し、
`VERIFY` エージェントを新規追加する。

本 PLAN は `helix verify-agent` が実装前の検証方式設計と実装後の検証連携を統一言語で扱うことを目的とする。

- 検証要件を PLAN から機械抽出し、候補ツールを収集する。
- PoC/検証シナリオごとに運用可能な検証スタックを提案する。
- 契約（D-CONTRACT）・API/DB・導線（D-DB）・設計の整合性まで含めた検証設計を提示する。
- PLAN 間 cross-check を組み込み、実装乖離を可観測化する。

## §2. スコープ

### §2.1 含む

- `helix verify-agent harvest --plan PLAN-XXX` 相当のツール収集ポリシー
- 検証要件とツールを紐づける `matrix.yaml` 連携ルール
- PLAN-007 の 5 種 Scrum トリガーとの接続方針（不確定事項差し込み）
- `helix verify-agent design --contract ...` における `D-CONTRACT / D-API / D-DB` 起点の検証戦略（テストピラミッド・境界
  設計・性能目標）
- `helix verify-agent cross-check --impl ... --spec ...` の drift 検出方針（仕様・実装ギャップの可視化）
- `workflow/poc` / `workflow/verification` / `workflow/research` / `workflow/verification-agent(新規)` の接続方式
- Plan 横断の導線（PLAN-001(PoC) 接続、PLAN-006/007/008/009 への反映）

### §2.2 含まない

- CLI コマンドの実装コード
- 既存 OSS ツール本体の導入（PoC フェーズの plan ドラフトに限定）
- 実装コード変更・テスト追加・デプロイ配備
- ライセンス監査の最終判断（法務判断が必要な場合は escalate 対象）

## §3. 採用方針

### §3.1 検証ツール harvesting

#### 目的
- 既存 PLAN/skill / 既定ルール（PLAN-006 upstream）に記載された検証要件を対象化し、抜け漏れなく候補化する。

#### 対象入力
- `docs/plans/PLAN-*.md`
- `skills/{workflow,tools,advanced}/`
- `cli/templates/matrix.yaml` と `.helix/matrix.yaml`
- 必要に応じた関連 skill（PoC / verification / research）

#### ツール候補源
- 既存 OSS: lint/test/format/security/dependency/perf/contract/golden/fuzz
- skill catalog: `workflow/verification`, `workflow/research`, `workflow/poc` 等
- `WebSearch + skill catalog` の二軸（本 PLAN レベルでは候補カテゴリの列挙まで）

#### 選定原則（3 軸）
- 契約適合: D-* と接続しやすいこと（型・エンドポイント・エラーモデルの扱い）
- 運用負荷: 導入後のメンテと CI/日次実行負荷が妥当であること
- 失敗検知力: 仕様差分・脆弱性・劣化シグナルを捕捉できること

#### 収集先ポリシー（固定+補完）
- 固定: `.helix/patterns/verify-tools.yaml` を前提に扱う（現時点で本リポジトリ未所蔵）
- 補完: `workflow/poc`, `workflow/verification`, `workflow/research` 既存 skill と `matrix.yaml` マッピング

### §3.2 PoC 用ツール選定

PoC の verify 用スクリプト（`verify/*.sh`）は用途別に分離し、`PLAN-007` の差し込み経路へ接続する。

#### §3.2.1 PoC/UI/Unit/Sprint/Post-deploy への接続

- PoC: `helix verify-agent design` の設計前提検証を中心に、最小再現スクリプトを優先
- UI: 画面遷移・視認性・a11y の検出に重み
- Unit: 契約境界・エッジケース・例外系を最短再現で検証
- Sprint: 差し込みイベント後の前提崩れ検証を即時発火可能にする
- Post-deploy: PLAN-009/デプロイ後 Scrum へ接続して観測期間の基準を受ける

#### §3.2.2 `--llm-suggest` と `gpt-5.4-mini`

- 方針: `.helix/patterns/verify-tools.yaml` が示す固定ルールを最優先
- `--llm-suggest` は候補拡張として `gpt-5.4-mini` を使用
- 出力は最終結論ではなく「候補+採否推奨」を提示し、kill/accept 判定は PLAN 側承認で確定

### §3.3 検証方法設計（design）

#### §3.3.1 契約起点統合
- `D-CONTRACT` / `D-API` / `D-DB` を起点に `test pyramid` と `mock vs integration` 境界を定義。
- 目安: `Unit >=60%`, `Integration <=30%`, `E2E <=10%` は現時点の初期準拠目安。

#### §3.3.2 境界設定
- Unit: 純粋関数・バリデーション・変換・エッジケース
- Integration: サービス間契約・DB 参照・認可境界
- E2E: 主要ユーザートリガー + API 成功/失敗分岐

#### §3.3.3 性能・品質閾値
- p95/p99、エラーレート、回帰再現率、契約 drift 率（最小 1 指標を必須化）
- L6/L9 系は `PLAN-009` のゲート条件へ接続

#### §3.3.4 PLAN-007 連携
- 差し込みトリガー時（不確実性・境界崩れ）に `verify-agent design` 再実行
- トリガー種別ごとに `verify profile` を切替え（UI/Unit/PoC/Sprint/Post-deploy）

### §3.4 PLAN 間 cross-validation

#### §3.4.1 接続要件
- PLAN-002/003/006/007/008/009 の対象成果物 ID を `matrix.yaml` または PLAN ID ベースで対応付け
- `PLAN-X impl` と `PLAN-Y spec` の比較を主観ではなく可視レポート化
- 差分カテゴリ: 仕様欠落、過剰実装、契約不一致、運用指標不一致

#### §3.4.2 Drift 検出
- `spec-only`, `impl-only`, `contract-only`, `behavior-only` の 4 タイプ分類
- 差分重大度：P1/P2/P3/P4 を付与して次施策へルーティング
- `Phase 2-3` の検証連鎖: `PLAN-002/003 完了` 後に `PLAN-009/L9-L11` へ接続

### §3.5 CLI / skill 配置方針

- skill 追加: `workflow/verification-agent`（新規）
- 既存代替: `workflow/verification`, `workflow/poc`, `workflow/research`
- 実行インターフェース（予定）
  - `helix verify-agent harvest --plan PLAN-XXX`
  - `helix verify-agent design --contract path/to/D-CONTRACT.md`
  - `helix verify-agent cross-check --impl PLAN-X --spec PLAN-Y`
- レポート出力: 失敗事例（tool, reason, severity, next_action）を固定スキーマ化

## §4. 関連 PLAN

- `docs/plans/PLAN-001-poc-skill.md`（未作成のため次タスクで確認が必要）
- `docs/plans/PLAN-004-pm-reward-design.md`
- `docs/plans/PLAN-006-upstream-meta-phase.md`
- `docs/plans/PLAN-007-scrum-multitype-trigger.md`
- `docs/plans/PLAN-008-reverse-multitype.md`
- `docs/plans/PLAN-009-run-phase-l9-l11.md`
- `skills/workflow/verification/SKILL.md`
- `skills/workflow/poc/SKILL.md`
- `skills/workflow/research/SKILL.md`
- `cli/roles/recommender.conf`
- `cli/templates/matrix.yaml`

## §5. リスク

- R1: LLM 参照提案の過剰化（候補数増大）
  - 対応: 固定ルール（まず既定ルール、次に `llm-suggest`）で選定の優先順位を固定
- R2: ツールロックイン（特定 OSS への過依存）
  - 対応: 候補を候補群で保持し、PLAN ごとの採用理由を明示
- R3: Cross-check の誤検知（仕様差分のノイズ）
  - 対応: severity 分類とトリアージ窓（Sprint 単位）を明示
- R4: PLAN-007 差し込み連携の過多（頻発）
  - 対応: 5 種 Scrum の条件満たし時のみ再実行する（条件不一致は観測扱い）
- R5: `.helix/patterns/verify-tools.yaml` の未設置
  - 対応: 本 PLAN では「未所在」を明示し、代替ソースを暫定採用

## §6. Sprint 計画概要（L1〜L4）

### Sprint L1: 骨格確立
- PLAN-010 の目的・境界・採択基準を確定
- PoC/profile 分類（PoC/UI/Unit/Sprint/Post-deploy）
- `matrix.yaml` 連携要件を確定

### Sprint L2: 方針固定
- `harvest/design/cross-check` の入出力仕様
- severity / trigger / next_action の固定フォーマット
- PLAN-006/007 接続ルールを確定

### Sprint L3: 運用シミュレーション
- PLAN-007 差し込みケースへの接続手順をシミュレーション
- PLAN-009/L9-L11、PLAN-008 方向の回収ルートを追試
- 欠測（TODO）を最小化し、例外運用を定義

### Sprint L4: 受入前整備
- 関連 PLAN 断面のリンク整合を確認
- レビュー観点を 5 軸評価で事前定義
- 実装/テンプレート側チームへの引き継ぎ文書を整備

## §7. 改訂履歴

| 日付 | バージョン | 変更内容 | 変更者 |
| --- | --- | --- | --- |
| 2026-05-01 | v1 | PLAN-010 を新規ドラフト作成（検証ツール選定、PoC 用 verify ツール選定、検証方法設計、PLAN 間 cross-check、CLI 配置） | Docs (Codex) |
