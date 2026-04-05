# ADR-005: YAML-SQLite 二重状態管理

> Status: Accepted
> Date: 2026-04-05
> Deciders: PM, TL

---

## Context

HELIX CLI は 2 種類の状態を管理する必要がある:

1. **フェーズ状態**: 現在のフェーズ（L1-L8）、ゲート状態（pending/passed/failed/skipped/invalidated）、スプリント進捗、開発モード（Forward/Reverse/Scrum）
2. **実行履歴**: タスク実行ログ、アクション単位ログ、オブザーバー結果、フィードバック、技術負債、コスト記録

これらの特性は大きく異なる:

| 特性 | フェーズ状態 | 実行履歴 |
|------|-----------|---------|
| 更新頻度 | ゲート通過時（低頻度） | アクション単位（高頻度） |
| 可読性要件 | 人間が直接確認したい | 集計クエリで参照 |
| レコード数 | 1 ファイル（数十行） | 数百〜数千レコード |
| 並行アクセス | 低（基本的にシングルユーザー） | 高（複数エージェント並行実行） |

---

## Decision

**フェーズ状態は YAML ファイル（phase.yaml）、実行履歴は SQLite（helix.db）** の二重状態管理を採用する。

### phase.yaml（フェーズ状態）

- パス: `.helix/phase.yaml`
- 読み書き: `yaml_parser.py` 経由（PyYAML 不使用の独自パーサー）
- 排他制御: `fcntl.flock` による排他ロック + atomic rename（一時ファイルに書き込み後リネーム）
- 遷移ルール: `state-machine.yaml` で宣言的に定義

### helix.db（実行履歴）

- パス: `.helix/helix.db`
- 19 テーブル、WAL モード、スキーマバージョン管理（v1 -> v4）
- 読み書き: `helix_db.py` 経由
- 並行安全: WAL モード + busy_timeout 5000ms

### config.yaml（プロジェクト設定）

- パス: `.helix/config.yaml`
- gate_skip, sprint_skip_steps, ai_review, default_drive, lang 等の設定
- 読み書き: `yaml_parser.py` 経由

---

## Alternatives

### A1: 全て SQLite

- 利点: 統一的なクエリ、トランザクション、並行安全
- 欠点: フェーズ状態の可読性が低下。`cat .helix/phase.yaml` の手軽さが失われる。git diff で変更を追跡しにくい

### A2: 全て YAML

- 利点: 人間可読、git 管理が容易
- 欠点: 大量の実行ログを YAML で管理すると性能劣化。集計クエリが書けない。並行書き込みの安全性確保が困難

### A3: JSON ファイルベース

- 利点: プログラムからのパースが容易
- 欠点: YAML ほど人間可読でない。大量レコードの管理に不向き

### A4: SQLite + YAML ビューの自動生成

- 利点: 単一ソース of truth
- 欠点: 同期の複雑性。YAML ビューの更新タイミングの設計が困難

---

## Consequences

### 正の影響

- **可読性**: `cat .helix/phase.yaml` で現在のフェーズ・ゲート状態を即座に確認可能
- **git 追跡**: phase.yaml は git 管理可能。変更履歴を git log で追跡できる
- **コンテキスト効率**: SQLite に履歴を退避することで LLM のコンテキストウィンドウを消費しない。必要な行だけ SELECT で取得
- **集計の柔軟性**: `helix log report quality` 等の集計を SQL で記述可能
- **並行安全**: WAL モードにより複数エージェントの同時実行に対応

### 負の影響

- **二重の整合性管理**: phase.yaml と helix.db の間に不整合が生じる可能性がある（例: phase.yaml で G2 passed だが helix.db の gate_runs に記録がない）
- **2 つの読み書き手段**: YAML は yaml_parser.py、SQLite は helix_db.py と、アクセス方式が二重化
- **マイグレーション**: SQLite のスキーマ変更にはバージョン管理（schema_version テーブル）とマイグレーション関数が必要

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| phase.yaml と helix.db の不整合 | `helix doctor` で整合性チェックと修復を提供 |
| yaml_parser.py の YAML サブセット制限 | HELIX が使用する YAML 構造（key-value + inline dict）に限定して対応。複雑な構造は使わない |
| SQLite スキーマ変更 | schema_version テーブルで段階的マイグレーション。v1 -> v4 まで実績あり |
| 排他ロックのデッドロック | fcntl.flock はプロセス単位のロック。タイムアウトなしだが、HELIX の使用パターンではデッドロックは発生しにくい |

---

## 補足: state-machine.yaml による遷移ルールの外部化

ゲート間の遷移ルール（前提条件、通過時のフェーズ遷移、invalidation カスケード）をコードに埋め込まず `state-machine.yaml` に宣言的に定義する。これにより:

- 遷移ルールの変更がコード修正なしで可能
- ルールの可読性が向上（`cat .helix/state-machine.yaml` で全遷移を確認）
- テストでルール定義を差し替え可能

---

## References

- `cli/lib/yaml_parser.py` (YAML 読み書き)
- `cli/lib/helix_db.py` (SQLite 読み書き)
- `cli/templates/phase.yaml` (フェーズ状態テンプレート)
- `cli/templates/state-machine.yaml` (遷移ルール定義)
- `cli/templates/config.yaml` (プロジェクト設定テンプレート)
- `.helix/reverse/R2-as-is-design.md` (ADR-005)
