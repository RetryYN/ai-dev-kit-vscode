# PLAN-029: HELIX フレームワーク厳格化拡張

## メタデータ

- id: PLAN-029
- title: HELIX 11 軸厳格化拡張 (デザイン後置 / Sprint 厳格化 / フェーズゲート / デプロイ前 3 フェーズ / 大規模 agent 2 段設計 / Scrum 拡張 / L1-L3 設計厳格化 / 追加実装流れ / Reverse 厳格化 / 拡張性 × 制約性 / docs+helix.db 強化)
- status: completed (2026-05-08, W-12 retrospective + 統合検証 PASS、12 Sprint 完遂)
- priority: high
- created: 2026-05-08
- owners: PM, TL
- related: [PLAN-028, ADR-014, ADR-015]
- plan_id: PLAN-029
- task_id: W-0-fix
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
- **参考**: §4 各事例参照（§4.2 Top 10 で直接対応する要件は未整理）

### 2.2 要件 1.2: Sprint 単位の厳格化

- 各 Sprint は必ず完了時に以下を実施し、`Gx` 側に反映する。
  1) 設計デグレチェック（D-shard 間整合、handover、phase.yaml）
  2) TL からの実装レビュー（approve 必須）
  3) テスト実行（pytest + bats + lint + 型 + smoke）
  4) ビルド（対象あり）
- Sprint-level 完走の定義を W-2 で制度化し、`helix sprint complete` の Hook 化を検討。
- 成果物は 1) WBS、2) gate 証跡、3) 変更差分、4) テスト要約を最小セットで記録。
- 失敗時は次 Sprint を blocked とし、carry または rework を明文化。
- **参考**: §4.2 Top 10 #1 (Project-specific AI review rules), §4.2 Top 10 #2 (Edit-test repair loop) / Sprint 2

### 2.3 要件 1.3: フェーズ単位ゲート + スプリント横断レビュー

- 既存の G1-G11 を「fail-close」で一段深め、現場側のスキップ定義を明確化。
- Sprint 完了時のみでなく、フェーズ終盤でも横断レビュー（仕様 / 実装 / リグレ）を行う。
- 横断レビューは 3 軸で採点: 
  - 仕様整合: WBS と要件マップ差分の有無
  - 実装品質: テスト/レビュー証跡の完全性
  - デグレ有無: 既存 plan 参照との矛盾チェック
- `helix gate --cross-sprint` を追加して、`Gx` 横断を CLI フラグ化。
- **参考**: §4.2 Top 10 #3 (SCM enforcement) / Sprint 3

### 2.4 要件 1.4: デプロイ前 3 フェーズ追加

- 現状の L7→L8 を L6 系に追加して、配備前検証を増量する。
  - **L6.5 Security Phase**: OWASP 全項目見直し、脅威モデリング再実施
  - **L6.7 Operations Phase**: scheduler / 運用ログ / リソース管理 / 開発者管理画面を実装接続
  - **L6.9 Visual Production Phase**: 画像・配色・アニメーションの最終実装（要件 1.1 の L5b と統合）
  - **L7**: 既存デプロイ工程
- Gate 追加: G6.5 / G6.7 / G6.9 を新設し、失敗時は L6 系に carry。
- この変更は run-phase（L9-L11）への接続を容易化し、受入前の「最後の手戻り」を減らす。
- **参考**: §4 各事例参照（§4.2 Top 10 で直接対応する要件は未整理）

### 2.5 要件 1.5: 大規模 agent 2 段設計

- 現在の 1 段構成は、agent の数・複雑性が増えると設計責務が混在しやすい。
- L2-L3 で 2 段を分離。
  - **インフラ層設計**: runtime、state mgmt、orchestrator、observability を固定。通常は BE として扱う。
  - **エージェント層設計**: ツール定義、プロンプト、decision tree、失敗復帰を固定。
- 規模自動判定: `helix size --agent --large` で 2 段化を強制し、通常規模では既存 1 段まま。
- 変更は D-AGENT-INFRA / D-AGENT-EXEC で明示し、WIP の責務混線を防ぐ。
- **参考**: §4.2 Top 10 #6 (Two-tier agent architecture) / Sprint 5

### 2.6 要件 1.6: Scrum フェーズ拡張

- 既存 S0-S4 に前段の S0.5（Web 検索事例検証）を追加。
- S1 は S1a（Plan）と S1b（受入条件設計）を明示。
- S2 は PoC 検証設計を明示してから実装へ進める。
- コマンド候補: `helix scrum web-search`（検索事例収集）および `helix scrum acceptance-design`（受入条件設計）を新設。
- 効果: 要件不確実時に PoC の成功条件を先に凍結し、後追い追加の乱立を抑制。
- **参考**: §4.2 Top 10 #5 (Risk-first research gate) / Sprint 6

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
- **参考**: §4.2 Top 10 #7 (ADR + C4 design freeze) / Sprint 7

### 2.8 要件 1.8: 追加実装の流れ整備

- 進行中タスクへ追加要求が入る場合は正式 mini-PLAN として扱う。
- mini-PLAN 最低 4 フェーズ: L1 → L2 → L4 → L6。
- 親 PLAN と dependency を Helix DB に登録し、並列 Sprint の影響追跡対象とする。
- 目的は「小さな追加を本筋に埋めない」ための明示的ルート化。
- **参考**: §4 各事例参照（§4.2 Top 10 で直接対応する要件は未整理）

### 2.9 要件 1.9: Reverse 逆引き順序 + レビュー厳格化

- R0-R4 は既存構造を維持しつつ、Sprint レビュー責務を上位に追加。
- 各 R フェーズの完了条件に「レビュー記録」「引継ぎ資料」を必須化。
- `helix reverse rgc` に強化版オプションを追加し、閉塞状態を明示。
- Forward へ返す引継ぎは必須ドキュメント化し、未接続のまま次 L4 へ進まない。
- **参考**: §4.2 Top 10 #8 (Characterization-before-change) / Sprint 9

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
- **参考**: §4.2 Top 10 #4 (Gate state vocabulary), §4.2 Top 10 #9 (Extension point with constraints) / Sprint 10

### 2.11 要件 1.11: README + docs + helix.db 強化

- README を HELIX 全体図に合わせて更新し、Quick Start と運用導線を再整理。
- docs 構造を再構成し、architecture / adr / plans / research / runbook を明確化。
- helix.db schema migration を追加し、axis や design_decision / qa_result / security_audit を記録できるようにする。
- helix doctor を更新して、docs と DB の整合を自動チェック対象に追加。
- **参考**: §4.2 Top 10 #10 (Trace/span + event sourcing) / Sprint 11

### 2.11.1 helix.db v18 → v19 migration 詳細

- 目的: axis・ADR・監査結果を `entries` / 新規観測テーブルへ集約し、後段 DoD/retrospective で数値評価できるようにする（additive, idempotent, forward-only）。
- **既存実装パターンに準拠**: `cli/lib/helix_db.py` の `_migrate_v17_to_v18(conn)` 形式で `_migrate_v18_to_v19(conn)` を新設、`_has_column()` で冪等性を担保 (新規ディレクトリ `cli/lib/db/migrations/` は作成しない)
- 実装スケッチ:

```python
# cli/lib/helix_db.py に追記 (CURRENT_SCHEMA_VERSION = 18 → 19 へ更新)

def _migrate_v18_to_v19(conn):
    """v19: entries に 3 列追加 + sprint_metrics + phase_gate_runs テーブル新設

    PLAN-029 §2.11.1: axis / ADR / 監査結果集約。additive only, idempotent.
    """
    # entries への列追加 (重複追加を _has_column でガード = 冪等)
    for column, sql_type in [
        ("qa_result", "TEXT"),
        ("security_audit", "TEXT"),
        ("design_decision", "TEXT"),
    ]:
        if not _has_column(conn, "entries", column):
            conn.execute(f"ALTER TABLE entries ADD COLUMN {column} {sql_type}")

    # 観測テーブル (CREATE IF NOT EXISTS で冪等)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sprint_metrics (
            sprint_id TEXT PRIMARY KEY,
            test_pass_rate REAL,
            drift_count INTEGER,
            duration_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase_gate_runs (
            gate_id TEXT,
            phase TEXT,
            result TEXT CHECK(result IN ('passed','failed','blocked','interrupted')),
            ran_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (gate_id, ran_at)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sprint_metrics_sprint ON sprint_metrics(sprint_id)"
    )


# migrate() 内のディスパッチに以下追加 (v17→v18 の直後)
if current < 19:
    _migrate_v18_to_v19(conn)
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, applied_at) "
        "VALUES (19, datetime('now'))"
    )
```

- migration テスト方針 (`pytest cli/lib/tests/test_helix_db_v19.py`):
  - 冪等性: `init_db` を 2 回呼んで `schema_version` の v19 行が 1 件のみ + `PRAGMA table_info(entries)` の qa_result/security_audit/design_decision が各 1 件のみ
  - 既存 data 不変: v18 で entries に N 行 INSERT → v19 migration → SELECT count(*) = N
  - 観測テーブル整合: `sprint_metrics` / `phase_gate_runs` が存在し、CHECK 制約 (kind='invalid' 等) で IntegrityError
  - rollback: `v19 → v18` は未対応 (forward-only)、test では migration スキップ確認のみ

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
| W-10 | 拡張性×制約性（集約） | TL | W-2..W-9 完了後 [集約] | — | KPI 設計と gate 運用を集約し観測基準を確定 |
| W-11 | README/docs/helix.db 強化 | docs+SE | W-10 完了後 [集約] | — | docs 構造再整理と schema migration で基盤整合 |
| W-12 | 統合検証 + retrospective | qa | W-11 完了後 [集約] | — | 全 Gate/全セキュリティ/全レビューを統合して retrospective を保存 |

### 3.1 並列性計画

- 第 1 波: W-1, W-2, W-5, W-6, W-7, W-9（6 Sprint）
- 第 2 波: W-3, W-8（W-2 以降）
- 第 3 波: W-4（W-3 以降）
- 第 4 波: W-10 → W-11 → W-12（集約 (W-10 → W-11 → W-12) 直列固定）

### 3.2 総セッション想定

- 12-15 セッション（短集中で前半 4 波、後半 3 波）
- 1-2 週間を標準幅として見積るが、risk register を見ながら 1 波目を短縮も可。

## 5. 11 軸 × 12 Sprint 受入 DoD（実装条件）

### 5.1 W-1 デザイン後置

- [ ] `phase.yaml` に L5a/L5b を追加する（`grep -c "L5a" .helix/phase.yaml` と `grep -c "L5b" .helix/phase.yaml` が各 `1` 以上）。
- [ ] `helix gate G5` が `L5a` と `L5b` の両方で判定を実行（`helix gate G5 --phase L5a` / `helix gate G5 --phase L5b`）。
- [ ] `test-helix-phase-l5b.bats` を追加し、ケース件数が `1` 件以上。

### 5.2 W-2 Sprint 厳格化

- [ ] `helix-sprint` の `complete` hook に `drift-check` が紐付く（`grep -c "drift-check" cli/helix-sprint` が `1` 以上）。
- [ ] `test-helix-sprint-strict.bats` を追加し、ケース件数が `4` 件以上。
- [ ] `helix sprint complete` 実行時、`lint/test/build/drift-check` の 3 項目ログが出ること。

### 5.3 W-3 フェーズゲート + 横断レビュー

- [ ] `helix gate --cross-sprint` が実装され、`helix gate G2 --cross-sprint --dry-run` が成功（smoke 条件成立）。
- [ ] 横断レビュー結果をログ化し、再実行用の証跡が 1 件以上保存される。

### 5.4 W-4 デプロイ前 3 フェーズ追加

- [ ] `phase.yaml` に `L6.5 / L6.7 / L6.9` の 3 項目を追加（`grep -c "L6\\.[579]" .helix/phase.yaml` が `3` 以上）。
- [ ] `helix-gate` に `G6.5 / G6.7 / G6.9` を追加。
- [ ] `test-helix-phase-deploy-3stages.bats` を追加し、ケース件数が `6` 件以上。

### 5.5 W-5 大規模 agent 2 段

- [ ] `cli/templates/D-AGENT-INFRA.md` と `cli/templates/D-AGENT-EXEC.md` を追加（ファイル存在: 各 1 件以上）。
- [ ] `helix-size --agent --large` で 2 段化判定が行われる（`grep -c "2 段"` などの判定ログが 1 件以上）。
- [ ] `test-helix-size-agent.bats` を追加し、ケース件数が `1` 件以上。

### 5.6 W-6 Scrum 拡張

- [ ] `helix scrum web-search` と `helix scrum acceptance-design` の subcommand が追加。
- [ ] `helix scrum web-search --query` 実行時に 1 件以上の reference 結果を保存。
- [ ] `test-helix-scrum-extended.bats` を追加し、ケース件数が `1` 件以上。

### 5.7 W-7 L1-L3 設計厳格化

- [ ] `cli/templates/D-TECH-STACK.md` と ADR テンプレが拡張される。
- [ ] `helix research --layer L2 --auto` 実行時、要件 1.7 の対象項目が自動連動（`grep -c "layer: L2" cli/helix-research` が `1` 以上）。

### 5.8 W-8 追加実装流れ整備

- [ ] `helix plan` の `--mini` オプションが追加され、mini-PLAN 作成が実行可能。
- [ ] `helix.db` の `entries` に parent_plan_id / child_plan_id を持つレコードが 1 件以上。
- [ ] 依存ループ防止チェック（`grep -n "cycle"`）で循環を検知し、`false` 条件を満たすこと。

### 5.9 W-9 Reverse 厳格化

- [ ] `helix-reverse` の各 R で `--review` オプションを追加（`grep -c "r[0-9] --review" cli/helix-reverse` が 5 件以上）。
- [ ] `handover --mode reverse-r{0,1,2,3,4}` が実行可能（各モード 1 回以上）。
- [ ] `test-helix-reverse-review.bats` を追加し、ケース件数が `1` 件以上。

### 5.10 W-10 拡張性 × 制約性（集約）

- [ ] `docs/architecture/helix-flexibility-constraint.md` を新規作成（ファイル存在 1 件以上）。
- [ ] KPI ダッシュボード仕様（KPI schema）は W-11 で DB 仕様化する前提で、項目定義数が 2 軸分以上あること。

### 5.11 W-11 README/docs/helix.db 強化

- [ ] `README.md` の大幅更新（見出し構成・Quick Start・運用導線・コマンド一覧が含まれること）。
- [ ] `docs` 配下で `architecture / adr / plans / research / runbook` の 5 ディレクトリ構成が成立（`find docs -maxdepth 1 -type d | grep -E "architecture|adr|plans|research|runbook"` で 5 件以上）。
- [ ] `cli/lib/helix_db.py` に `_migrate_v18_to_v19(conn)` 関数を追加し、`CURRENT_SCHEMA_VERSION = 18 → 19` に更新。`_has_column()` で冪等性を担保（既存 `_migrate_v17_to_v18` 形式準拠、§2.11.1 参照）。
- [ ] `pytest cli/lib/tests/test_helix_db_v19.py` が 3 方向（idempotency / data migration / forward-only）で実行できる。

### 5.12 W-12 統合検証 + retrospective

- [ ] `helix doctor` 実行が pass（最終状態で fail 件数 0）。
- [ ] `helix test` 実行が pass（コマンド失敗 0、全件 green）。
- [ ] retrospective 記録（例: `.helix/retro/W-12.md`）が 1 件以上保存。

### 5.13 依存/整合の軸チェック

- Axis 1.1, 1.2, 1.3 は W-1〜W-4 で連続検証。
- Axis 1.4, 1.5 は W-4〜W-5 で設計-実装接続。
- Axis 1.6, 1.7 は W-6〜W-7 でリードタイムを圧縮。
- Axis 1.8, 1.9 は W-8〜W-10 で運用移行。
- Axis 1.10, 1.11 は W-10〜W-11 で評価・保存基盤へ反映。

## 4. 関連調査 (research integration、2026-05-08 完了)

詳細は `../research/PLAN-029-research-findings.md` (391 行) 参照。本セクションは HELIX への取り入れ判断と Top 10 パターンを要約する。

### 4.1 軸別 Top 1-2 事例 (要約)

- **A. Sprint-level rigorous review** (要件 1.2 関連): Cursor Bugbot（Diff レビューの AI 自動検出）  
  URL: https://docs.cursor.com/en/bugbot, 公開日: 不明（GitHub changelog: 2026-02-26）。  
  例として aider の auto-lint/auto-test は L4 での編集後検証ループを標準化し、lint/test 失敗時の再実行を加速する。
- **B. Phase gate enforcement** (要件 1.3 関連): Stage-Gate の go/kill/hold/recycle 概念でフェーズ停止・保留を機械化。  
  URL: https://www.stage-gate.com/about/stage-gate-innovation-performance-framework/discovery-to-launch-process/, 公開日: 不明（overview: 2026 初頭）。  
  GitHub の protected branches/required checks を merge 前 gate へ接続し、最終投入前に SCM enforcement を担保する。
- **C. Multi-stage agent system 2-tier** (要件 1.5 関連): LangGraph Supervisor は上位制御層と実行層を分離し、role 専門化と監査しやすさを高める。  
  URL: https://reference.langchain.com/javascript/modules/_langchain_langgraph-supervisor.html, 公開日: 不明。  
  補助として AutoGen Core / CrewAI は manager-validation 構造を示すが、採用は原理レベルに限定する。
- **D. Scrum hypothesis validation** (要件 1.6 関連): Lean Startup の Build-Measure-Learn で仮説→PoC→測定→判断を明文化。  
  URL: https://www.lean.org/lexicon-terms/lean-startup/, 公開日: 不明。  
  Scrum.org spike 時間制約と終了条件を組み合わせ、無目的な調査を防止する。
- **E. L1-L3 design rigor** (要件 1.7 関連): ADR は設計判断の意図・代替案・結果の必須化を担保。C4 は設計階層を共通言語化。  
  URL: https://github.com/phillduffy/architecture_decision_record（公開日不明）,  
  https://c4model.com/（公開日不明）。  
  技術選定は Thoughtworks Radar の ring を参照し、採用/保留の透明性を上げる（https://www.thoughtworks.com/en-us/radar）。
- **F. Reverse engineering review** (要件 1.9 関連): Strangler Fig / 7Rs は段階的移行の経路を提示し、R4 から Forward へ安全に戻す。  
  URL: https://martinfowler.com/bliki/StranglerFigApplication.html, 公開日: 2024-08-22（原著: 2004-06-29）。  
  補助に characterization tests（Feathers）で現状挙動を固定する前提を加える。
- **G. 拡張性 × 制約性** (要件 1.10 関連): VS Code Extension API / IntelliJ extension point を参照し、拡張点と制約条件を明示的に定義。  
  URL: https://code.visualstudio.com/api/extension-capabilities/overview, 公開日: 2026-04-15。  
  併せて Boehm Spiral / PMI DAD でリスク優先度と移行順序を整理する。
- **H. agent observability** (要件 1.4 / 1.5 関連): Langfuse と Arize Phoenix は agent span / eval / metrics を一元可視化。  
  URL: https://langfuse.com/docs, 公開日: 不明。  
  OpenAI Agents SDK tracing/guardrails は handoff / tool call の停止条件を明示し、HELIX guard と整合しやすい。
- **I. helix.db / event log** (要件 1.11 関連): Event Sourcing により状態変化を append-only で追跡し、監査と再現を両立。  
  URL: https://www.martinfowler.com/eaaDev/EventSourcing.html, 公開日: 2005-12-12。  
  PostgreSQL audit trigger の考え方を SQLite 方針に取り込みつつ限界（DDL/SELECT 系）を明記する。
- **J. 設計デグレ防止** (要件 1.2 / 1.3 関連): Architectural fitness function は設計健全性を継続検査として機械化。  
  URL: https://www.oreilly.com/library/view/building-evolutionary-architectures/9781491986356/, 公開日: 2017。  
  ArchUnit / dependency-cruiser は特定言語や依存方向での逸脱検知を補強する。
- **K. AI 駆動開発 2026 ベストプラクティス** (全要件): Claude Code best practices と Codex full-auto/approval モデルを context discipline / handover と同期。  
  URL: https://code.claude.com/docs/en/best-practices, 公開日: 不明。  
  OpenAI Codex CLI の approval モードは HELIX の consent と approved 運用に直接寄与する。

### 4.2 取り入れる Top 10 パターン (research §統合観点 抜粋)

1. Project-specific AI review rules → 要件 1.2 / Sprint 2（AGENTS/skill/gate への導入ルール）
2. Edit-test repair loop → 要件 1.2 / Sprint 2（L4 実行ループの標準化）
3. SCM enforcement → 要件 1.3 / Sprint 3（merge 条件としての gate fail-close）
4. Gate state vocabulary → 要件 1.10 / Sprint 10（go/kill/hold の状態語彙）
5. Risk-first research gate → 要件 1.6 / Sprint 6（G1R/G1.5 発火条件）
6. Two-tier agent architecture → 要件 1.5 / Sprint 5（TL/実行層分離）
7. ADR + C4 design freeze → 要件 1.7 / Sprint 7（設計凍結成果物）
8. Characterization-before-change → 要件 1.9 / Sprint 9（Reverse から Forward 接続の安全化）
9. Extension point with constraints → 要件 1.10 / Sprint 10（plugin/skill 拡張設計）
10. Trace/span + event sourcing → 要件 1.11 / Sprint 11（helix.db event schema 強化）

### 4.3 取り入れない / 慎重なパターン (理由付き)

- AutoGen 本体依存: maintenance mode で将来保守リスクが高いため、実装依存ではなく参照パターンとして採用抑制。
- SaaS AI review 全面依存: ネットワーク・権限境界が HELIX のローカル fail-close 方針と衝突するため、必須機能にはしない。
- Spike の乱用: Scrum spikes は終了条件を付けないと出荷を遅らせるだけの工数消費になるため、timebox と問いの明確化が必要。
- DORA 単独評価: 品質監査を DORA のみで代替すると設計整合・agent 安全性を見落とすため補助指標に限定。
- In-database audit 直下の監査一本化: SELECT / DDL / superuser tampering を捕捉できず、OS / Git / 追加ログと併用しないと監査欠落になる。

### 4.4 HELIX 独自で設計する空白領域

- LLM 用 phase gate schema: tool call / handoff / context exhaustion といった LLM 実行状態を扱う状態機械は OSS には未整備。HELIX 独自のイベント仕様が必要。
- docs/code/db 三位一体監査: ADR/C4/depcheck + helix.db/drift を同じ gate-trace で証跡化する一体型ルールは既存 OSS で未成熟。
- Role delegation audit: allowed_files / 分担責任 / 承認境界を runtime で追跡するスキーマとレポートの標準化。
- Reverse to Forward の接続 DSL: R0-R4 の証跡を forward の §3/§4 に自動接続するルーティング DSL は独自実装対象。

## 6. リスクと回避策

| 要件軸 | リスク | 影響 | 回避策 |
|---|---|---|---|
| 1.1 | L5b 判定が L5a に混線し、表示後置の意図が薄れる | L4 早期実装との混在で品質低下 | `grep -c "L5a"`, `grep -c "L5b"` と 2 段階レビューを必須化 |
| 1.2 | Sprint 合格条件が `drift-check` 前提ではなく省略される | テスト抜け・再work の増加 | W-2 で hook / bats / grep 条件を全件必須化 |
| 1.3 | cross-sprint option 未実装で横断レビューが形骸化 | フェーズ越えの不整合検知漏れ | `helix gate --cross-sprint` 未成功を 0 でない合否として受理禁止 |
| 1.4 | L6.5/L6.7/L6.9 が追加後に実行順序を崩す | run 前提品質の監査漏れ | 3段階で順序固定し、順序違反時に `helix gate G6.9` を stop |
| 1.5 | D-AGENT-INFRA と D-AGENT-EXEC の責務境界が曖昧化 | 2 段化設計の監査不能、責務衝突 | 企画要件に責務マトリクスを必須化（`1` つ以上の責務別項目を添付） |
| 1.6 | web-search hook が信頼できない URL 由来 | 仕様誤導で手戻り増 | URL 検証 hook を追加し、`http_status` 400 以上は除外 |
| 1.7 | L1-L3 設計順序監査の不足 | 設計軸で D-API/D-DB/D-CONTRACT/D-UI が錯綜 | 逆順参照を検知し、L3 で必須レビューを固定化 |
| 1.8 | mini-PLAN と親 PLAN の関連付けが省略 | 追加実装が親子分離不能 | `--mini` は parent_plan_id 必須で受入条件化 |
| 1.9 | Reverse→Forward 接続モード未定義 | 受入時に仕様ロスト | `handover --mode reverse-to-forward` を W-12 で必須化 |
| 1.10 | KPI gaming（hit_rate 操作、skill 偏り） | 指標品質悪化・監査不全 | 推奨 audit log と role 多様性 KPI の二軸評価 |
| 1.11 | README/docs/helix.db のリンク drift | 実行手順や依存参照が壊れる | `helix doctor` の link integrity check を追加し、broken link=0 を必須化 |

### 6.1 エスカレーション基準

- 要件 1.4 と 1.11 は helix.db migration に関わるため、破壊的変更の可能性がある場合は事前にユーザー確認を要求。
- 変更対象が既存 PLAN の既定動作を直接置換する場合は `interrupted` とし、事前合意を追加する。

## 7. 関連ドキュメント

- [PLAN-028-helix-v2-orchestration.md](PLAN-028-helix-v2-orchestration.md)
- [ADR-014-roles-config-format.md](../adr/ADR-014-roles-config-format.md)
- [ADR-015-helix-v2-orchestration.md](../adr/ADR-015-helix-v2-orchestration.md)
- メモ: `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/project_2026_05_08_plan029_helix_rigor.md`
- 研究結果: `../research/PLAN-029-research-findings.md`（並行作成、後で integrate）

---

## 8. 章立て整合ノート（作成時確認）

- メタデータ
- 1. 背景・動機
- 2. 厳格化 11 軸の対応設計
- 3. Sprint 分割（12 Sprint）
- 4. 関連調査（research integration）
- 5. 11 軸 × 12 Sprint 受入 DoD（実装条件）
- 6. リスクと回避策
- 7. 関連ドキュメント

## 9. 進捗検証用サマリ（アウトライン）

- 作成済み: `PLAN-029-helix-rigor-expansion.md`
- 想定行数: 約 450-500 行
- Sprint 数: 12（W-1〜W-12）
- 11 軸: 2.1〜2.11 で明示
- research 統合: §4 を参照し、要件 1.1〜1.11 の反映を更新
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
- 章構成: Metadata + 7 章相当 + 11 軸 + Sprint 12件 + 研究反映
- 11 軸: 2.1〜2.11 を確認
- Sprint: W-1〜W-12 の全行が存在
- 参照: PLAN-028, ADR-014, ADR-015 のリンク整備
- 依存: 研究反映が §4 と一致していること
- 行数: 450-500行前後（本文規模で 1 パス読了が可能）

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
