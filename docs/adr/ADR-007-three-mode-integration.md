# ADR-007: 3モード統合（Forward / Reverse / Scrum）

> Status: Accepted
> Date: 2026-04-14
> Deciders: PM, TL

---

## Context

HELIX フレームワークは3つの開発モードを持つ:

- **Forward HELIX**: 要件→設計→実装→検証の標準フロー（L1〜L8 + G0.5〜G7）
- **Reverse HELIX**: 既存コードからの設計復元（R0〜R4 + RG0〜RG3）
- **Scrum HELIX**: 検証駆動開発（仮説→PoC→確認→Forward接続）

各モードは異なるゲート体系・異なる成果物を持つが、同一プロジェクトで併用されることがある:

- Reverse で As-Is 設計を復元した後、Forward で Gap Closure を行う
- Scrum で仮説検証した後、confirmed hypothesis を Forward L1 要件に接続
- Forward 実装中に既存コードの理解が必要になり、Reverse 部分解析を差し込む

モード間の状態管理方式として、以下の選択肢があった:

1. **モードごとに独立した状態ファイル** (`phase.yaml`, `reverse-phase.yaml`, `scrum-phase.yaml`)
2. **統合状態ファイル** (`phase.yaml` 1つで全モードの状態を保持)
3. **データベース統合** (SQLite で全モード状態を管理)

---

## Decision

**1つの `phase.yaml` で3モードの状態を共存管理する方式** を採用する。

### 状態構造

```yaml
# .helix/phase.yaml
project: <name>
current_mode: forward | reverse | scrum    # ← 現在アクティブなモード
current_phase: L1 | R0 | ...               # ← モード内のフェーズ

# Forward モード状態
gates:
  G0.5: { status: pending | passed | failed | skipped }
  G1:   { status: ... }
  ...
  G7:   { status: ... }

sprint:
  current_step: .1a | .1b | ... | .5
  status: active | complete | paused
  drive: be | fe | db | fullstack | agent
  steps: { .1a: { status: ... }, ... }

# Reverse モード状態
reverse_gates:
  RG0: { status: ... }
  ...
  RG3: { status: ... }
reverse: { status: completed | in-progress | null, completed_at: ... }

# Scrum モード状態（scrum/ サブディレクトリで管理）
# .helix/scrum/backlog.yaml, .helix/scrum/sprint.yaml
```

### モード切替

- `helix mode forward|reverse|scrum` で `current_mode` を切替
- 各モードの状態はフェーズ進行とは独立に保持される
- Reverse 完了後に Forward に切り替えても、Reverse の成果（R0-R4）は保持

### モード間接続

| 接続元 | 接続先 | 方法 |
|--------|--------|------|
| Reverse R4 | Forward L1〜L4 | Gap Register を参照して Forward ルーティング |
| Scrum confirmed | Forward L1 | `helix scrum decide --confirmed` で仮説を要件に昇格 |
| Forward 中断 | Reverse 部分 | `helix mode reverse` で一時切替 → 完了後 Forward 復帰 |

---

## Alternatives

### A1: モードごとに独立した状態ファイル

- 利点: モード間の状態が混ざらない、独立してバージョン管理可能
- 欠点: `current_mode` の同期が複雑、モード切替時のアトミック性が保証できない、`helix status` 実装が煩雑

### A3: SQLite で全モード状態を管理

- 利点: トランザクション保証、複雑なクエリが可能
- 欠点: 人間が読めない、git で追跡しづらい、YAML の単純さを失う

---

## Consequences

### 正の影響

- **単一 Source of Truth**: `.helix/phase.yaml` 1ファイルで全モード状態を確認可能
- **モード切替の簡潔さ**: `current_mode` の書き換え1箇所で切替完了
- **Git 追跡**: モード進行の履歴が単一 YAML の diff として残る
- **モード間接続**: Reverse R4 Gap → Forward ルーティング、Scrum confirmed → Forward L1 など、モード横断の接続が同一ファイル内で完結

### 負の影響

- **YAML サイズの増大**: 3モード分の状態を1ファイルに保持するため、`phase.yaml` は約40行
- **モード独立性の制約**: 1モードの状態破損が他モードに波及するリスク（ただし yaml_parser.py のキー単位書き込みで緩和）

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| モード切替時の不整合 | `helix-mode` が切替前に `phase.yaml` 構造を検証 |
| モード間データ競合 | Reverse/Forward/Scrum のキー名プレフィックスで名前空間を分離（`reverse_gates`, `gates`, `scrum/`） |
| モード依存のゲート実行ミス | `helix-gate` が `current_mode` を参照し、モードに応じた valid_values をチェック |

---

## References

- `cli/templates/phase.yaml` (状態テンプレート)
- `cli/helix-mode` (モード切替コマンド)
- `cli/helix-reverse` (Reverse モード)
- `cli/helix-scrum` (Scrum モード)
- `.helix/reverse/R4-gap-register.md` (Reverse→Forward 接続の実例)
- ADR-005: YAML-SQLite Dual State（状態管理の上位方針）
