---
plan_id: PLAN-210
title: agent budget allocation framework (Anthropic / Codex / Sonnet weekly budget 分配)
status: draft
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — budget-allocation.yaml スキーマ + BudgetAllocator クラス + helix budget allocate CLI 実装"
  - role: qa
    slot_label: "QA — role 別 / 期間別 limit 境界値テスト + WARN 発火タイミング検証"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 helix budget CLI との責務分離確認・設計整合・G4 review"
generates:
  - artifact_type: yaml_config
    path: cli/config/budget-allocation.yaml
  - artifact_type: python_module
    path: cli/lib/budget_allocator.py
  - artifact_type: cli_extension
    path: cli/helix-budget
  - artifact_type: test
    path: cli/lib/tests/test_budget_allocator.py
  - artifact_type: doc_update
    path: docs/commands/ai-harness.md
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - cli/helix-budget
  - cli/config/models.yaml
  - cli/lib/helix_db.py
  - docs/commands/ai-harness.md
acceptance_criteria:
  - "cli/config/budget-allocation.yaml が role 別 week_limit / session_limit / warn_threshold を定義する"
  - "helix budget allocate --role se --week-limit 20 で YAML を上書き保存できる"
  - "helix budget status が role 別の消費額・残額・warn_threshold に対する比率を表示する"
  - "消費額が warn_threshold (default 80%) を超えた role で WARN メッセージを出力する"
  - "python3 -m py_compile cli/lib/budget_allocator.py PASS"
  - "pytest test_budget_allocator.py (8 case) 全 PASS"
  - "既存 helix budget status / helix doctor pass 数に回帰なし"
---

# PLAN-210: agent budget allocation framework

## L2 凍結 (ADR snapshot)

既存 `helix budget` CLI の拡張であり新 framework 採用ではない。
YAML config 追加 + Python helper 追加のみで、設計上の大局判断変更はなし。
ADR snapshot 不要。

## 背景

2026-05-23 のセッションで Claude weekly $200 budget over を経験した。
現状の `helix budget` CLI は消費残量の **表示** 機能を提供するが、
role 別・期間別の **予算枠** を事前に設定し、枠接近時に WARN を出す
allocation framework が存在しない。

本 PLAN は以下を整備する:

1. role 別・週次/セッション別の budget limit を `cli/config/budget-allocation.yaml` で宣言的に管理
2. `helix budget allocate` コマンドで limit を CLI から更新できる
3. `helix budget status` に消費率 + WARN を追加し、枠超過を早期検出する
4. helix.db に消費イベントを記録し、集計クエリを提供する

## WebSearch skip 理由 (PLAN-087 ガードレール)

HELIX 内部 YAML config + Python helper のみ。外部ライブラリの新規依存なし。

## 設計方針

### budget-allocation.yaml スキーマ

```yaml
# cli/config/budget-allocation.yaml
version: 1
defaults:
  warn_threshold_pct: 80       # 消費が limit の 80% を超えたら WARN
  reset_period: weekly          # weekly / daily / session

roles:
  - role: opus
    week_limit_usd: 80
    session_limit_usd: 20
    warn_threshold_pct: 75     # role 別オーバーライド可
  - role: se
    week_limit_usd: 30
    session_limit_usd: 8
  - role: tl
    week_limit_usd: 20
    session_limit_usd: 5
  - role: pmo-sonnet
    week_limit_usd: 15
    session_limit_usd: 3
  - role: pmo-haiku
    week_limit_usd: 5
    session_limit_usd: 1
```

- `week_limit_usd`: 週次上限 (月曜 00:00 UTC リセット)
- `session_limit_usd`: 単一セッション上限
- `warn_threshold_pct`: 消費率がこの値 (%) を超えたら WARN (default は defaults.warn_threshold_pct)

### BudgetAllocator クラス

`cli/lib/budget_allocator.py` に以下を実装:

```python
class BudgetAllocator:
    def load_config(self) -> dict: ...
    def save_config(self, config: dict) -> None: ...
    def set_limit(self, role: str, week_limit: float | None,
                  session_limit: float | None) -> None: ...
    def get_limit(self, role: str) -> dict: ...        # {week_limit, session_limit, warn_threshold_pct}
    def get_usage(self, role: str, period: str) -> float: ...  # helix.db 集計
    def check_warn(self, role: str, period: str = "weekly") -> list[str]: ...  # WARN メッセージ一覧
    def status_report(self) -> list[dict]: ...        # 全 role の消費率サマリ
```

- `get_usage` は helix.db の `budget_events` (既存 or 新規 table) から集計
- period="weekly" は月曜 00:00 UTC 以降の累積、period="session" は current session_id 限定

### helix budget CLI 拡張

```
helix budget allocate --role <role> [--week-limit <USD>] [--session-limit <USD>]
helix budget status [--role <role>]     # 既存コマンドに消費率 + WARN 列を追加
helix budget warn-check                 # WARN 対象 role のみ表示 (CI / hook 向け)
```

- `allocate`: `budget-allocation.yaml` を更新し、変更内容を echo する
- `status`: 全 role または指定 role の [消費額 / 週次 limit / 消費率% / WARN 判定] を表形式で出力
- `warn-check`: WARN 対象が 1 件以上あれば exit 1 (helix doctor 向け hook 接続用)

### helix doctor 統合

`check_budget_allocation`:
- `budget-allocation.yaml` が存在しない → advisory WARN
- WARN 対象 role が 1 件以上 → advisory WARN (role 名と消費率を列挙)

## 実装計画

### Sprint .1: YAML config + BudgetAllocator (Codex se、size S)

`cli/config/budget-allocation.yaml` を新規作成 (初期値 5 role)。
`cli/lib/budget_allocator.py` に load_config / save_config / set_limit / get_limit を実装。
`python3 -m py_compile` PASS + yaml.safe_load 読み込み確認が完了条件。

### Sprint .2: get_usage / check_warn / status_report (Codex se、size S-M)

helix.db の budget 集計クエリを実装 (既存 budget_events table を使用、不在時は table 新規作成)。
check_warn / status_report を実装し、warn_threshold_pct との比較ロジックを確認。
`helix budget status` の出力に消費率列と WARN マーカーを追加。

### Sprint .3: helix budget allocate / warn-check CLI (Codex se、size S)

`cli/helix-budget` に allocate / warn-check サブコマンドを追加。
`bash -n cli/helix-budget` PASS + 手動動作確認が完了条件。

### Sprint .4: pytest + helix doctor + docs (Codex qa + PMO、size S)

`cli/lib/tests/test_budget_allocator.py` で 8 case:
T1: set_limit で YAML 更新 / T2: get_limit で dict 返却 / T3: 期間内イベントのみ集計
T4: 消費率 79% で WARN なし / T5: 消費率 80% で WARN あり / T6: status_report 全 role 返却
T7: budget_events 不在時に 0.0 silent fail / T8: `datetime.now(timezone.utc)` 動的週次判定

`helix doctor check_budget_allocation` が yaml 不在で advisory WARN を出すことも確認。
`docs/commands/ai-harness.md` に allocate / warn-check コマンドを追記。
pmo-sonnet で既存 `helix budget` との責務境界・二重カウント防止を確認。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/budget_allocator.py` PASS
- [ ] `bash -n cli/helix-budget` PASS
- [ ] pytest 8 PASS / `helix doctor` pass 数現行以上
- [ ] pmo-sonnet review (Sprint .4)

## DoD

- [ ] `budget-allocation.yaml` が role 別 limit を定義 / `BudgetAllocator` が全 public メソッドを実装
- [ ] `helix budget allocate` で limit 更新 / `status` に消費率 + WARN 追加 / `warn-check` が exit 1
- [ ] `helix doctor check_budget_allocation` が yaml 不在で advisory WARN を出す
- [ ] pytest 8 PASS / docs/commands/ai-harness.md に新コマンド追記済み

## carry / 学び

- `budget-allocation.yaml` の role 名は `cli/config/models.yaml` の role 定義と揃える。
- get_usage は budget_events 不在時 silent fail (0.0)。全 timestamp は `datetime.now(timezone.utc)` で統一。
- session_limit 超過時の自動 block は本 PLAN スコープ外 (phase 2 以降)。

## 関連 reference

- cli/helix-budget (既存) / cli/config/models.yaml / cli/lib/helix_db.py
- PLAN-099 (自動走行 framework、budget check 統合候補)
