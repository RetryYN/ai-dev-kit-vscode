# V2 dogfood 計画（Phase J）

更新日: 2026-05-14
作成者: Docs（TL-Design）
対象: HELIX V2（Phase A〜I 完了後）

## 目的

Phase J は、HELIX V2 で整備した機能を **HELIX 自身が対象**として使い、フレームワークの自己証明を行う実務フェーズ。

本書は `docs/v2/C-followup/v2-dogfood-plan.md` として、V2 完了後の dogfood を再現可能に実行するための計画を定義する。

### 参照

- [`docs/v2/CONCEPT.md`](docs/v2/CONCEPT.md)
- [`docs/v2/L1-REQUIREMENTS.md`](docs/v2/L1-REQUIREMENTS.md)
- [`docs/v2/A-audit/audit-summary.md`](docs/v2/A-audit/audit-summary.md)

---

## §1. dogfood とは

### 1.1 dogfood の定義

**dogfood** とは、HELIX の開発・検証を HELIX V2 framework で実施し、その自己有効性を実測する活動である。

- HELIX 本体が対象（HELIX 自身の改修）
- L1 → L2 → L3 → L4 → L5 → L6 → L7 → L8 → Run を実際に実施
- 既存の「外部ユーザー向け品質基準」ではなく「開発母体品質基準」を検証
- 導入したガードレール（V-model / detector / auto-sync / hook）を同一レイヤで検証

### 1.2 適用対象の範囲

Phase J は「開発可能性検証フェーズ」として、次を対象とする。

1. 文書フロー（L2 / L3）
2. 実装フロー（L4）
3. 自動化・検知（hook/command/gate）
4. 可視化（dashboard / report）
5. ガバナンス（handover / delegation / runup-down）

### 1.3 dogfood での検証ゴール

- HELIX 自体が **V2 framework で全工程完走**できること
- V-model の設計-検証一致率が数値で現れること
- 14 detector が実行経路上で実体 record を伴って働くこと
- 自動化が「機能」だけでなく「開発行為」に接続すること
- dashboard によって HELIX 全容が可視化され、意思決定に使える状態となること

### 1.4 V-model 適用時の dogfood ルール

- PLAN 起票時、`vmodel-semantics.yaml` が読み取られ、`design_level` と `test_kind` が 1 対 1 で対応
- `plan` / `gate` / `test` の各レベルで、設計と検証の整合差分が可視
- `design_review` と `test_baseline` の auto-record が有効でないシナリオは dogfood 条件外とみなす
- PLAN の終了条件は `G2〜G11` に加え、`KPI実測` を追加して判定

---

## §2. dogfood 成功条件

### 2.1 成功の定義

以下のすべてを満たした場合を成功とする。

1. **HELIX 新規 PLAN（PLAN-070 以降）** が V2 framework で全段を完走
2. **V-model 整合度スコア ≥ 80%** を HELIX 自体で連続 3 PLAN 測定
3. **14 detector が HELIX 開発時の実行経路で有効稼働**
4. **自動 record（auto-register / auto-sync / auto-detect）** が 1 セッション内に 2 件以上の新規 write を生む
5. **dashboard で HELIX 全容が可視化**され、run 前後の状態差分が 1 秒以内で観測可能

### 2.2 受入条件（Acceptance）

| ID | 条件 | 測定方法 | 合否基準 |
|---|---|---|---|
| AC-01 | dogfood PLAN 起票 | `docs/plans/` + `helix plan list` | PLAN-070 以降 1 件以上 |
| AC-02 | plan 全段完走 | `helix gate` 実行ログ | G1〜G11 の pass / skip 判定 |
| AC-03 | V-model score | `helix qa vmodel-score --plan-id <PLAN>` | 平均スコア ≥ 80 |
| AC-04 | detector 有効性 | `detector_runs` / `design_review` | 14 axis うち 12 以上が有効実行 |
| AC-05 | auto record 効果 | `helix db query`（日次） | 自動 record 件数の増加率 ≥ 1.5%/PLAN |
| AC-06 | dashboard 可視化 | `helix detect dashboard --all` | vmodel + detector + delegation の 3 視点が 1 view |

### 2.3 達成しない場合の扱い

- AC-03 が未達時: `blocked` とし、`Phase J.2` は延期
- AC-04 が未達時: 該当 axis を再検証し、再実施（対象 PLAN を入れ替え）
- AC-05 が未達時: auto-sync のフックルート再点検（`PostToolUse`, `SessionStart`, `Gate runner`）
- AC-06 が未達時: dashboard 表現仕様の見直し（view 仕様を修正）

---

## §3. dogfood 前提条件（Phase A-I）

### 3.1 技術前提

- `helix.db` の `v21` migration が完了（schema_version=21）
- `vmodel-semantics.yaml` の 4 drive 定義が完了
- 14 detector が導入・運用化され、`helix detect run --axis` が実行可能
- `PostToolUse`, `SessionStart`, Gate runner の auto-detect / auto-record 経路が有効

### 3.2 ドキュメント前提

- Phase A〜I の L1〜L3 ドキュメントが完了していること
- `docs/v2/C-followup/*` で関連設計の追従更新が完了
- `audit-summary.md` と L1 requirements の BR-D3 / AC-14 の実装状態を確認済み

### 3.3 組織前提

- 委譲ルール（`helix codex/claude`）と allowed-files が実運用で一致
- `helix handover` の更新が前後連携可能
- CI / hooks / plan import の最低要件が成立

### 3.4 データ・インフラ前提

- `helix.db` 書込み権限とバックアップ方針が成立
- `budget/cost telemetry` を取り込む基盤が稼働
- テスト・品質結果保存先（`docs/tests`、`artifacts`）が残留ポリシーに従って保存される

### 3.5 監査前提

- 監査ログの保存先が揺れない
- `docs-integrity` と `folder-structure` の drift が未登録のまま進まない状態
- 未解決項目が「計画ノート」に切り分け

---

## §4. dogfood test シナリオ Top-10

### 4.1 進め方

- まず `S-01`〜`S-05` を Plan size small で実施し、実行遅延と自動化効果を観測
- 次に `S-06`〜`S-10` を medium で実施
- その後に `S-11`〜`S-15` を large / 複合実装として再検証

### 4.2 シナリオ一覧

| シナリオ | 内容 | 期待結果 |
|---|---|---|
| S-01 | 新規 BE 機能追加（例: `helix audit` の出力形式拡張） | L1〜L4 全工程を V2 で完走、V-model 整合度 80%+ |
| S-02 | FE 機能追加（mock-driven） | mock promotion lifecycle が mock_frozen→promoted を満たす |
| S-03 | 既存 gate 追加（新規 subgate） | 対応 detector が自動起動し、review 証跡が残る |
| S-04 | 14 detector うち 1 軸のみ失敗誘発 | `critical axis` として事前警告 + 修正要求が出る |
| S-05 | L2-L3 のペア設計追加 | 設計レビューとテスト設計の同一 sprint 証跡を生成 |
| S-06 | `docs` 追記を伴う PLAN 起票 | auto-register が `doc_artifacts` を更新 |
| S-07 | PostToolUse フックを通じた code 変更 | 該当 PLAN に code / test baseline の record が自動追加 |
| S-08 | SessionStart で catalog auto-sync | 全 catalog 差分が 1 セッションで反映 |
| S-09 | G3.5（functional_freeze）適用 | 詳細設計と単体テスト設計の同時凍結が pass 判定 |
| S-10 | L7 デプロイ検証想定（mock） | 実行指示ログ・観測 plan が残る |
| S-11 | 大規模 PLAN（データ + FE + CLI 同時） | 3 軌道の委譲と detector 連携が壊れない |
| S-12 | 既存 PLAN 参照での逆参照検証 | 旧 PLAN との `state-events` 整合が壊れない |
| S-13 | Reverse 由来 evidence を含む PLAN | L3 以降の受入条件に起点由来情報を反映 |
| S-14 | CI/フック fail-close 緊急シナリオ | detector fail 時に write/edit が抑止される |
| S-15 | KPI リアルタイム監視（dashboard） | vmodel score と detector success/warn/fail を同時表示 |

### 4.3 シナリオ実行テンプレート（共通）

- PLAN 起票 → `helix plan finalize` → `helix gate G3` → L4 実装 → `vmodel-score` 取得 → detector 14 軸評価 → dashboard 反映

### 4.4 失敗条件の定義

- S-01〜S-15 のうち 2 シナリオ以上で成功条件を満たせない場合、Phase J を停止し `Phase J.4` に戻る
- `detector false positive` が 20% を超える場合は観測方法を見直す
- `auto-record` の未実行が 1 つでもある場合は `blocked` を付与

---

## §5. dogfood で発見されうる問題

### 5.1 フレームワーク使用性の問題

- 実装者観点: PLAN 起票→gate→テストの認知負荷が高い
- 目標: `plan template` と `run checklist` の簡素化

### 5.2 文書不足・命名混乱

- section 名称、artifact 種別、drive 名が揺れやすい
- 対応: 用語表（glossary）を本計画前提として固定し、全 PLAN で準拠

### 5.3 detector false positive

- 仕様変更時の境界不一致による誤検知
- 対応: 1) 新規 PR への誤報率
 2) false positive と誤検知の切替理由
 3) 軽微誤報（許容）と重大誤報（stop）を分離

### 5.4 自動化の暴走

- pre-commit / G-runner が頻繁に失敗し作業を止める
- 対応: `dry-run`, `opt-out`, `80-100% guard`, `cost guard` の順で段階運用

### 5.5 token / cost 想定外

- 反復的な再実行で token が想定値を超える
- 対応: PLAN サイズ別予算と、`80%` / `100%` 予兆時の自動 pause を監視する

### 5.6 実装者依存ドリフト

- 機能追加時に「HELIX を改善するのではなく迂回する」運用が残る
- 対応: dogfood 時は原則 `dogfood ルール` に従い、迂回手順の利用を禁止

### 5.7 運用面の問題

- dashboard の数値と実測差
- handover / task-plan との追従不足
- 対応: 監査 step を毎シナリオで固定記録

---

## §6. dogfood Phase 構成

### Phase J.1（初回）: 小規模 PLAN の実証

- 目的: 既存ループ（plan→gate→review→record）が回ることを確認
- 対象: S-01 〜 S-05（small）
- 受入: AC-01/AC-02 を最優先、AC-03 を暫定達成
- 成果: `dogfood-playbook-v1`（最短実行手順）を作成

### Phase J.2（中規模）: V-model 整合度の測定

- 目的: 実データで v-model が有効に機能するかを測る
- 対象: S-06 〜 S-10（medium）
- 受入: AC-01/AC-02/AC-03 が全件
- 成果: `vmodel-score` 計測値をPLAN横で比較、KPI基礎値を確定

### Phase J.3（大規模）: fullstack 検証

- 目的: 実運用規模に近い複合施策で dogfood を実行
- 対象: S-11 〜 S-15（large）
- 受入: AC-01〜AC-06 を同時達成
- 成果: `Phase J 統合レポート` 作成、V2.1 計画を起票

### Phase J.4（反映）: V2.1 改修計画

- 目的: 観測結果に基づく V2.1 改修を要件化
- アクション: 構文、フック、スキーマ、dashboard それぞれの改善を issue 化
- 成果: `docs/v2/C-followup/v2.1-roadmap.md` の起点に接続（未作成時は本節に暫定保存）

### Phase J 進行原則

- 1シナリオの完了 = 成功/失敗の証跡を必ず PLAN record 化
- シナリオ間で KPI の baseline を固定（前提値更新禁止）
- `intermediate errors` を必ず separate note 化し、最終判定には含めない

---

## §7. KPI / トラッキング目標

### 7.1 Plan 件数・進行

- dogfood PLAN 件数: **≥ 5**（3 段階合計）
- PLAN 種別内訳: S=2件, M=2件, L=1件以上（初期目標）
- 完了率: 100%（Phase J 目標）

### 7.2 Gate / 品質

- 全 PLAN で G1〜G11 通過率: **≥ 80%**
- `vmodel 整合度` 平均: **≥ 80%**
- `vmodel score` 90+ の PLAN 割合: **≥ 30%**（暫定）

### 7.3 Detector / 回帰

- false positive 率: **≤ 10%**
- detector warning / fail 分離率: **fail ≤ 15%** かつ **warn ≤ 20%**
- 14 axis 実行率: **100%（想定実行） / 60%（実質実行）**

### 7.4 自動化・コスト

- `auto-record` 実行率: **≥ 95%**（該当イベント）
- `auto-detect` 実行率: **≥ 90%**（G・pre-commit 経路）
- 実行時間: 1 セッションあたり 30 分以内で core loop 完走
- Token 使用: 100% 上限に対し 85% を超えたら要分割

### 7.5 可視化・運用価値

- dashboard で「V-model, detector, delegation」を一画面統合: **100%**
- run 前後の state 差分表示: **1 秒以内**
- 次 PLAN 起点資料が自動生成される割合: **100%（dogfood 対象 PLAN）**

---

## Phase J ロードマップ（暫定）

### 2026-05-14 〜 2026-05-28

- Week 1: Phase J.1（小規模）
- Week 2: Phase J.2（中規模）
- Week 3: Phase J.3（大規模）

### マイルストーン

- M-01（Week 1 終了）: S-05 成功記録、dogfood-playbook-v1 発行
- M-02（Week 2 終了）: AC-03/AC-05 一次集計完了
- M-03（Week 3 終了）: AC-06 + dashboard 1 view 完走

---

## 参考リンク

- [BR-D3 / AC-14 参照](docs/v2/L1-REQUIREMENTS.md)
- [Phase J 記述（CONCEPT）](docs/v2/CONCEPT.md)
- [audit ドライバ集約](docs/v2/A-audit/audit-summary.md)
