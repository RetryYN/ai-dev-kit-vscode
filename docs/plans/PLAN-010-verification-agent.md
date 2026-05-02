# PLAN-010: 検証ツール選定 + 検証方法設計エージェント (v3.3)

## §1. 目的 / Why

PLAN-006〜PLAN-009 で整備された `上流メタ` / `Scrum 差し込み` / `Reverse 多系統化` / `Run 工程` の方針を接続し、
`VERIFY` エージェントを新規追加する。

本 PLAN は `helix verify-agent` が実装前の検証方式設計と実装後の検証連携を統一言語で扱うことを目的とする。

- 検証要件を PLAN から機械抽出し、候補ツールを収集する。
- PoC/検証シナリオごとに運用可能な検証スタックを提案する。
- 契約（D-CONTRACT）・API/DB（D-API / **D-DB = DB/データモデル成果物**）・導線（D-STATE / UI/UX flow）・設計の整合性まで含めた検証設計を提示する。
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

#### §3.1.2 候補 harvest 出力の必須フィールド (G1R 証跡 / P2 解消)

OSS / WebSearch / LLM suggestion から harvest した候補は、採用検討へ進める前に以下のフィールドを必須で記録する。これらは G1R (事前調査ゲート) 証跡として研究レポートに接続される。

| フィールド | 必須 | 内容 |
|---|---|---|
| `tool_id` | 必須 | 候補ツール ID (kebab-case) |
| `source` | 必須 | `oss` / `websearch` / `llm-suggest` / `.helix/patterns/verify-tools.yaml` (実パス) / **`fallback`** (§3.1.1 fallback 経路) |
| `official_source` | 必須 | 一次ソース URL (公式 repository / website) |
| `license` | 必須 | SPDX 識別子。不明時は `unknown` (採用不可) |
| `last_release_or_activity` | 必須 | 最終リリース or 主要 commit 日付 (ISO 8601) |
| `maintenance_signal` | 必須 | `active` / `maintenance` / `stale` / `deprecated` |
| `security_notes` | 必須 | CVE / GHSA / 既知の supply chain risk 列。なしの場合は空配列を明示 |
| `adoption_status` | 必須 | **`candidate_only`** で初期化。採用確定は PM 承認後 |
| `evidence_path` | 必須 | `.helix/research/<id>/verification.md` 内の該当章へのリンク |

`adoption_status` を `candidate_only` 以外に変更するには PLAN-006 §3.2.2 OSS license 承認境界に従い PM 承認 + `oss-approval.md` 記録を必須化する。証跡未充足のまま G1R 通過は fail-close。

#### 選定原則（3 軸）
- 契約適合: D-* と接続しやすいこと（型・エンドポイント・エラーモデルの扱い）
- 運用負荷: 導入後のメンテと CI/日次実行負荷が妥当であること
- 失敗検知力: 仕様差分・脆弱性・劣化シグナルを捕捉できること

#### 収集先ポリシー（固定+補完）
- 固定: `.helix/patterns/verify-tools.yaml` を前提に扱う（**未設置時は §3.1.1 fallback ルールに従う**）
- 補完: `workflow/poc`, `workflow/verification`, `workflow/research` 既存 skill と `matrix.yaml` マッピング

#### §3.1.1 verify-tools.yaml 正本化 (P2 解消)

固定ルールソースの正本化を Sprint L1 で完了させる。template / schema / owner / fallback を以下に固定する。

##### 配置・所有

- 配置: `.helix/patterns/verify-tools.yaml`
- owner: TL (作成 + 維持) / PM (採用判断承認)
- 作成タスク: PLAN-010 **Sprint L1** で template + schema を確定し、PR 単位で merge (PLAN-009 の `Run Sprint 1` とは別概念)

##### 最小 schema

```yaml
version: 1
tools:
  - id: vitest                     # 必須、kebab-case 一意
    category: unit-test            # 必須: unit-test|integration|e2e|lint|format|security|dependency|perf|contract|golden|fuzz
    languages: [ts, js]            # 必須、対象言語
    license: MIT                   # 必須、SPDX 識別子
    last_release_or_activity: 2026-04-15  # 必須、ISO 8601 日付 (§3.1.2 harvest 出力 schema と同一フィールド名で統一)
    maintenance_signal: active     # 必須: active|maintenance|stale|deprecated
    official_source: https://vitest.dev    # 必須、一次ソース
    security_notes: []             # 必須、CVE / GHSA / supply chain risk 等。未検出時は `[]` を必ず明示 (空配列は lint pass)
    adoption_status: candidate_only        # 必須: candidate_only|approved|rejected
    helix_alignment: [PLAN-010, workflow/verification]   # 任意、紐付く HELIX 資産
```

##### fallback 挙動 (未設置時)

- harvest 結果に `source=fallback` を必ず付与
- `欠測理由` (例: `verify-tools.yaml not yet provisioned`) を `fallback_reason` に記録
- fallback 出力は **採用確定不可**、PM 承認かつ verify-tools.yaml 整備後に再 harvest 必須
- fallback 状態のまま G1R 通過は **fail-close**

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
- 差分重大度: **P0/P1/P2/P3** を付与して次施策へルーティング (HELIX レビュー / 割り込み / 計画レビュー文脈の P0-P3 と統一、PLAN-004 v5 の deferred-finding carry rule に接続)
- `Phase 2-3` の検証連鎖: `PLAN-002/003 完了` 後に `PLAN-009/L9-L11` へ接続

#### §3.4.3 Drift severity と次施策ルーティング (P2 解消)

差分重大度の保存 schema と次施策を以下に固定する。`P4` は使用しない。

| severity | 条件 | 次施策 | carry rule (PLAN-004 v5) | 例 |
|---|---|---|---|---|
| `P0` | 致命的不整合 (実装が契約に違反、本番影響あり) | 即停止、incident 起票 | stop | API 戻り値が D-CONTRACT と非互換、認証スキップ |
| `P1` | 重大不整合 (機能差し戻し or 仕様凍結見直し) | G2/G3 fail-close、scrum (Unit/Sprint) 起票 | carry-with-pm-approval | 必須フィールド欠落、エラーモデル不一致 |
| `P2` | 中度不整合 (是正計画あり、carry 可) | 次工程開始前に解消 or readiness defer | auto-carry | optional フィールドの命名揺れ、ログ形式差 |
| `P3` | 軽微不整合 (記録のみ) | 任意 carry、deferred 台帳記録 | optional | コメント差分、サンプル値の表記揺れ |

`severity` 判定不能時は canonical 値 **`unclassified`** を出力 (alias `triage_required` は廃止) し、`requires_pm_triage=true` を必須付与する。PM/TL 再判定完了まで G2/G3/G4 および cross-check 完了判定を **fail-close** とし、auto-carry 経路には流さない。`drift_severity` を report 出力 schema の必須フィールドとし、`P0`/`P1`/`unclassified` は **fail-close 条件**に直結する。

### §3.5 CLI / skill 配置方針

- skill 追加: `workflow/verification-agent`（新規）
- 既存代替: `workflow/verification`, `workflow/poc`, `workflow/research`
- 実行インターフェース（予定）
  - `helix verify-agent harvest --plan PLAN-XXX`
  - `helix verify-agent design --contract path/to/D-CONTRACT.md`
  - `helix verify-agent cross-check --impl PLAN-X --spec PLAN-Y`
- レポート出力: 失敗事例（tool, reason, severity, next_action）を固定スキーマ化

## §4. 関連 PLAN

- `docs/plans/PLAN-001-poc-skill.md`（**draft 状態 = 未 finalize**。PLAN-001 が finalize されるまでは PoC 接続を `skills/workflow/poc/SKILL.md` への参照に置換し、PLAN-010 Sprint L3/L4 で PLAN-001 確定後に正規化する）
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
  - 対応: §3.1.1 で正本化 (PLAN-010 **Sprint L1** で template+schema 確定。PLAN-009 の `Run Sprint 1` とは別概念)。未設置時は fallback 出力 (`source=fallback` + `fallback_reason` 必須)、採用確定不可、G1R fail-close で運用。

## §6. Sprint 計画概要（L1〜L4）

### Sprint L1: 骨格確立
- PLAN-010 の目的・境界・採択基準を確定
- PoC/profile 分類（PoC/UI/Unit/Sprint/Post-deploy）
- `matrix.yaml` 連携要件を確定
- **`.helix/patterns/verify-tools.yaml` の template + schema 確定 + 初版 commit** (Sprint L1 タスク、§3.1.1。PLAN-009 の `Run Sprint 1` とは別概念のため混同しないこと)

### Sprint L2: 方針固定
- `harvest/design/cross-check` の入出力仕様
- severity / trigger / next_action の固定フォーマット (`P0/P1/P2/P3` 統一、§3.4.3 mapping)
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
| 2026-05-02 | v3 | TL レビュー finding 解消。P2-1: §3.4.2 で drift severity を `P0/P1/P2/P3` に統一 (P4 撤廃)、§3.4.3 で severity → 次施策ルーティング表 + carry rule (PLAN-004 v5) 接続を新設。P2-2: §3.1.1 で `.helix/patterns/verify-tools.yaml` 正本化 (配置 / owner / 最小 schema (id/category/license/maintenance_signal 等) / fallback 挙動 (`source=fallback` 必須・採用確定不可・G1R fail-close)) を新設、§5 R5 を更新。P2-3: §3.1.2 候補 harvest 出力の必須フィールド (tool_id/source/official_source/license/last_release_or_activity/maintenance_signal/security_notes/adoption_status/evidence_path) を新設、PLAN-006 §3.2.2 OSS 承認境界と接続。P3: §1 で D-DB を「DB/データモデル成果物」と明示し、導線を D-STATE / UI/UX flow に振り分け。 | PM (Opus) |
| 2026-05-02 | v3.1 | TL v3 review finding 解消。P2-1: §3.1.2 `source` enum に `fallback` を追加、§3.1.1 fallback 経路と整合。P2-2: §3.4.3 severity 判定不能時のデフォルトを `P2 + auto-carry` から **`unclassified` + `requires_pm_triage=true` + fail-close** に変更、auto-carry 迂回を防止。P3: §3.1.1 verify-tools.yaml schema で `security_notes` を必須化 (未検出時は `[]` 必須)、harvest 出力 schema との整合確保。 | PM (Opus) |
| 2026-05-02 | v3.2 | TL v3.1 review finding 解消。P2-1: §3.1.2 `source` enum の固定ルール参照値を実パス `.helix/patterns/verify-tools.yaml` に統一。P2-2: §4 関連 PLAN で `PLAN-001-poc-skill.md` の draft 状態を明記、PLAN-001 finalize までは `skills/workflow/poc/SKILL.md` 参照に置換し PLAN-010 Sprint L3/L4 で再正規化する条件を明示。P3: §3.1.1 / §6 Sprint L1 の Sprint 名を `Sprint L1` に統一 (PLAN-009 の `Run Sprint 1` と別概念であることを明記)。 | PM (Opus) |
| 2026-05-02 | v3.3 | TL v3.2 review finding 解消。P2-1: §3.1.1 verify-tools.yaml schema の `last_release` を `last_release_or_activity` に統一し §3.1.2 harvest 出力 schema とフィールド名整合。P2-2: §3.4.3 判定不能 drift の値を canonical `unclassified` 1 つに固定 (alias `triage_required` 廃止)、fail-close 条件と統一。P3: §5 R5 リスク欄の `Run Sprint 1` を `Sprint L1` に統一 (Sprint 名混在解消)。 | PM (Opus) |
