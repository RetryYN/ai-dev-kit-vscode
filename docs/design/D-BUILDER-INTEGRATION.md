# D-BUILDER-INTEGRATION: Builder System と CLI の統合設計

> Status: Draft
> Date: 2026-04-14
> Authors: TL
> 参照: [ADR-002 Builder System Foundations](../adr/ADR-002-builder-system-foundations.md), [ADR-008 ビルダー抽象化](../adr/ADR-008-builder-abstraction.md), [L2-builder-system.md](./L2-builder-system.md)

---

## 1. 目的

Builder System（`cli/lib/builders/`）と HELIX CLI（`cli/helix-*`）の統合アーキテクチャを明文化する。GAP-033「Builder System と CLI の接続が設計構想段階」の解消を目的とする。

本文書の対象読者:

- Builder System に新しいビルダーを追加する開発者
- `helix` CLI から Builder を呼び出すコマンドを実装する開発者
- 現在の統合状況と将来計画を知りたい PM/TL

---

## 2. 現在のアーキテクチャ

### 2.1 エントリポイント階層

```
ユーザー
  ↓
┌───────────────────────────────────────────┐
│  helix builder <subcommand>               │  ← Bash エントリポイント
│  (cli/helix-builder, 21行)                │     薄いラッパー
└───────────────┬───────────────────────────┘
                ↓ python3 <args>
┌───────────────────────────────────────────┐
│  cli/lib/builders/cli.py (220行)          │  ← Python CLI 本体
│  argparse でサブコマンド分岐              │
│  - list / schema / build / validate /     │
│    history                                │
└───────────────┬───────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│  BuilderRegistry (registry.py)            │
│  - 登録されたビルダーを名前で解決         │
└───────────────┬───────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│  具象ビルダー (9種類)                     │
│  - base.py の BuilderBase を継承         │
└───────────────┬───────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│  BuilderStore / BuilderHistory            │  ← SQLite 永続化
│  (store.py, history.py)                   │
└───────────────────────────────────────────┘
```

### 2.2 CLI サブコマンド

`helix builder <subcommand>` で利用可能な操作:

| サブコマンド | 説明 | 実装 |
|------------|------|------|
| `list` | 登録されたビルダー一覧表示 | `_cmd_list()` |
| `<builder> schema` | ビルダーの INPUT_SCHEMA を JSON で出力 | `_cmd_schema()` |
| `<builder> build` | ビルダーを実行（generate + validate） | `_cmd_build()` |
| `<builder> validate <path>` | 既存の成果物を検証 | `_cmd_validate()` |
| `<builder> history` | 実行履歴を表示（SQLite から） | `_cmd_history()` |

### 2.3 ビルダー登録方式

各具象ビルダーはモジュール末尾で自己登録する:

```python
# cli/lib/builders/agent_loop.py
class AgentLoopBuilder(BuilderBase):
    BUILDER_TYPE = "agent-loop"
    ...

BuilderRegistry.register(AgentLoopBuilder)
```

`cli.py` は `_auto_discover_builders()` で `cli/lib/builders/` 配下を import し、全ビルダーを登録する。

### 2.4 現在登録されている9ビルダー

```bash
$ helix builder list
Available builders:
  - agent-loop
  - agent-pipeline
  - agent-skill
  - json-converter
  - sub-agent
  - task
  - verify-script
  - workflow
```

（cli は Builder ではなく dispatcher なのでリストに含まれない）

---

## 3. 他 CLI コマンドとの接続状況

### 3.1 直接接続されているコマンド

**`helix-builder`** → Builder System のメインエントリ
- 実装: `cli/helix-builder` (21行の薄いラッパー)
- 動作: `python3 cli/lib/builders/cli.py "$@"` を呼び出す

### 3.2 間接的に Builder を利用するコマンド

以下のコマンドは、将来的に Builder System 経由で成果物生成を統一する候補:

| コマンド | 現状 | 将来の統合方針 |
|---------|------|--------------|
| `helix-task` | 独自のタスク実行ロジック | `task` ビルダーに委譲（部分的に既に連携） |
| `helix-team` | 独自のチーム実行ロジック | `workflow` ビルダーに委譲 |
| `helix-init` | テンプレートコピー | Builder化しない（ADR-006 cp 方式を維持） |
| `helix-codex` | Codex CLI 呼び出し | Builder化しない（ツール起動は対象外） |

### 3.3 接続されていない領域

以下は現時点で Builder System と無関係:

- **Gate 検証系** (`helix-gate`, `helix-gate-api-check`, `helix-drift-check`) — 検証タスクは Builder の責務外
- **状態管理系** (`helix-status`, `helix-mode`, `helix-sprint`) — phase.yaml 更新が主目的
- **Hook 系** (`helix-hook`, `helix-check-claudemd`, `helix-session-*`) — イベント駆動型

---

## 4. 統合の拡張ポイント

### 4.1 新規ビルダー追加手順

1. `cli/lib/builders/<name>.py` を作成
2. `BuilderBase` を継承して `BUILDER_TYPE`, `INPUT_SCHEMA`, `generate`, `validate_output` を実装
3. モジュール末尾で `BuilderRegistry.register(<ClassName>)`
4. テスト追加（`cli/lib/tests/test_builders_concrete.py` にパラメタ化エントリ）
5. ドキュメント更新（本文書 §2.4 のリストに追加）

### 4.2 CLI コマンドから Builder を呼び出す方法

Python コード内から直接呼び出す場合:

```python
from builders.registry import BuilderRegistry
from builders.store import BuilderStore

store = BuilderStore(db_path=".helix/helix.db")
builder_cls = BuilderRegistry.get("agent-loop")
builder = builder_cls(store=store, project_root=".")
artifacts, validation = builder.build(
    task_id="my-task-001",
    input_params={...},
)
```

Bash から呼び出す場合（subprocess で Python CLI 経由）:

```bash
helix builder agent-loop build --input-payload "$(cat params.json)"
```

### 4.3 Builder Hooks（将来検討）

以下のフックポイントで Builder を介入させる拡張案:

- **Pre-build hook**: 入力検証の前処理（環境変数展開、テンプレート補完）
- **Post-build hook**: 生成直後の整形（linter 適用、フォーマッタ）
- **Validation hook**: `validate_output` を拡張する外部チェッカー

これらは ADR-009 の Hook 戦略と整合する形で設計する。

---

## 5. 既知の制約

| 制約 | 詳細 | 対応 |
|------|------|------|
| Python 依存 | Bash CLI から Python 経由で呼ぶためオーバーヘッドがある | ADR-004 に従う。短命プロセスの起動コストは許容 |
| quality_score の算出基準がビルダー間で不統一 | AgentLoop と Workflow で `quality_score` の計算式が異なる | GAP-028 で統一基準 D-QUALITY-SPEC.md を策定予定 |
| ビルダー履歴の表示制約 | `helix builder history` は JSON 出力のみ。Human-readable な表示がない | 将来 `--format markdown` オプション追加を検討 |
| 並列実行時の履歴書き込み競合 | SQLite WAL モードで緩和、ただし高頻度並列は未検証 | `test_builders.py` に並列書き込みテストを追加予定 |

---

## 6. 関連文書

- [ADR-002: Builder System Foundations](../adr/ADR-002-builder-system-foundations.md) — 基盤方針
- [ADR-008: ビルダー抽象化](../adr/ADR-008-builder-abstraction.md) — 抽象化の決定
- [L2-builder-system.md](./L2-builder-system.md) — 全体設計
- [L2-learning-engine.md](./L2-learning-engine.md) — Builder 履歴 → 学習エンジンの接続
- `cli/lib/builders/base.py` — BuilderBase 実装
- `cli/lib/builders/cli.py` — Python CLI 実装
- `cli/lib/tests/test_builders_concrete.py` — 具象ビルダーテスト

---

## 7. 未解決事項

- [ ] Builder と `helix-task` の責務分担明確化（現状は部分重複）
- [ ] Builder quality_score の統一基準（GAP-028）
- [ ] 並列実行時の SQLite 競合検証
- [ ] Builder Hooks の具体設計（必要性の評価含む）
