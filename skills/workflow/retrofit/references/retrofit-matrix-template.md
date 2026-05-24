> 目的: retrofit-matrix の詳細テンプレート。SKILL.md Step 2 から参照する。旧→新のマッピング + 影響範囲 + ロールバック単位を標準化する

# retrofit-matrix テンプレート

保存先: `docs/plans/<slug>-retrofit-matrix.md`

---

## メタデータ

```yaml
retrofit_matrix:
  slug: "<プロジェクト・タスクの識別子>"
  plan_id: "PLAN-XXX"
  created: "YYYY-MM-DD"
  owner: "TL"
  status: draft | active | completed
  baseline_test_pass_count: <移行前の全テスト PASS 件数>
  target_env:
    from: "<旧環境の概要>"
    to: "<新環境の概要>"
```

---

## 影響評価テーブル

```markdown
| # | 対象コンポーネント | 旧バージョン / 旧構成 | 新バージョン / 新構成 | 影響ファイル | 優先度 | 破壊的変更 | Migration 手順 URL |
|---|------|------|------|------|------|------|------|
| 1 | FastAPI | 0.99.x | 0.115.x | routes/*.py | High | startup_event → lifespan | https://fastapi.tiangolo.com/release-notes/ |
| 2 | Python | 3.9 | 3.12 | 全体 | Critical | type hint 変更 / asyncio 挙動差異 | https://docs.python.org/3/whatsnew/3.12.html |
| 3 | pytest | 7.x | 8.x | cli/lib/tests/ | Medium | なし | https://docs.pytest.org/en/stable/changelog.html |
```

優先度の定義:

| 優先度 | 定義 |
|---|---|
| Critical | SLO・セキュリティ・認証に影響、最優先移行 |
| High | 複数モジュールに影響、phase 早期に対応 |
| Medium | 単一モジュールに閉じる、通常 phase で対応 |
| Low | テスト・ドキュメントのみ、最終 phase で対応 |

---

## Phase 構成

```yaml
phases:
  - id: phase-1
    name: "<フェーズ名>"
    targets:
      - "<移行対象ファイル / モジュール>"
    rollback: "<ロールバック手順>"
    acceptance:
      - "<受入条件>"
    owner: "<担当ロール: TL / SE / dba>"
    estimated_effort: "<工数見積: hours>"
    status: not_started | in_progress | completed | rolled_back

  - id: phase-2
    name: "<フェーズ名>"
    targets: []
    rollback: ""
    acceptance: []
    owner: ""
    estimated_effort: ""
    status: not_started
```

Phase 設計のルール:

1. 依存が少ないコンポーネントを先行 phase に配置する
2. 各 phase は独立してロールバックできる単位に分割する
3. 本番移行 phase には SLO 監視 24h が受入条件に含まれる

---

## ロールバック手順詳細

```markdown
## Phase N ロールバック手順

### トリガー条件
- 受入テストで FAIL が X 件以上
- 本番エラー率が Y % 超過
- ロールバック判断: TL + PM の合意

### 実行手順
1. `git revert <移行 commit hash>` で旧コードに戻す
2. `pip install -r requirements.lock` で旧ライブラリを復元
3. `helix test` で全回帰テストを再実行し PASS を確認
4. blue-green の旧環境へ traffic を切り戻す

### 確認チェック
- [ ] 旧環境で smoke test PASS
- [ ] DB の整合性確認（移行伴う場合）
- [ ] SLO モニタリング正常
```

---

## 完了記録

```yaml
completion:
  completed_at: "YYYY-MM-DD"
  baseline_test_pass_count_after: <移行後の全テスト PASS 件数>
  performance_comparison:
    p50_before: "<ms>"
    p50_after: "<ms>"
    p95_before: "<ms>"
    p95_after: "<ms>"
  issues_encountered:
    - "<発生した問題と対応>"
  deprecated_artifacts:
    - "<廃止した旧設定・旧環境のパス>"
```
