# D-INTERRUPT-SPEC: 割り込み管理仕様（IIP / CC）

> Status: Accepted
> Date: 2026-04-14
> Authors: TL

---

## 1. 目的

`helix-interrupt`（890行）の IIP（Implementation Interrupt Protocol）と CC（Change Control）の分類アルゴリズム・処理フローを明文化する。GAP-026 の解消を目的とする。

---

## 2. 割り込み種別

HELIX では開発中に発生する変更要求を2種類に分類する:

| 種別 | 正式名 | 用途 |
|------|--------|------|
| **IIP** | Implementation Interrupt Protocol | 実装中に発覚した技術課題・設計ギャップへの一時対応 |
| **CC** | Change Control | PO/ステークホルダーからの要件変更・新規追加 |

---

## 3. 分類アルゴリズム

### 3.1 入力パラメータ

`helix interrupt start --kind <kind> --mode <iip|cc>` が受け取る `kind` に基づき、mode に応じて分類する。

**kind 種別（共通）:**
- `design_gap` — 設計文書と実装の齟齬
- `new_requirement` — 新規要件の発覚
- `constraint` — 外部制約の変更（API 仕様変更、ライブラリ制限等）
- `po_change` — PO の方針変更

### 3.2 IIP 分類（実装実装）

`classify_iip()` の決定ロジック（cli/helix-interrupt L123-135）:

| kind | IIP 分類 | 意味 | 緊急度 |
|------|---------|------|--------|
| `design_gap` | **P1** | 設計文書の不備で実装が進まない | 高 |
| `new_requirement` | **P2** | 実装中に発覚した追加要件 | 中 |
| `constraint` | **P1** | 外部制約による技術的ブロッカー | 高 |
| `po_change` | **P3** | PO 意向での方向修正 | 低（計画再編） |

IIP は `P0`〜`P3` の優先度レベルを持つ:

- **P0**: 即時対応必須（本番障害レベル、現スプリント停止）
- **P1**: 当該 sprint 内で対応（`.1a` に復帰）
- **P2**: 次 sprint 以降で対応（`.1a` に復帰）
- **P3**: 後続計画に組み込み（sprint 再開せず）

### 3.3 CC 分類（実装実装）

`classify_cc()` の決定ロジック（cli/helix-interrupt L137-149）:

| kind | CC 分類 | 意味 | 影響層 |
|------|---------|------|--------|
| `design_gap` | **CC-M** | 設計レベルの変更が必要 | L3, L4 |
| `new_requirement` | **CC-M** | 新規要件の取り込み | L3, L4 |
| `constraint` | **CC-S** | 実装レベルの調整で済む | L4 |
| `po_change` | **CC-L** | 要件定義から再検討が必要 | L1, L2, L3, L4 |

CC-S/M/L は影響範囲を示す:

- **CC-S (Small)**: 実装層のみ調整（L4 局所）
- **CC-M (Medium)**: 設計+実装層に影響（L3, L4）
- **CC-L (Large)**: 要件層から再検討（L1-L4 全層）

### 3.4 分類結果による sprint 復帰ステップ

`resume_step_for()` の決定ロジック（cli/helix-interrupt L151-167）:

| 分類 | resume step | 意味 |
|------|-----------|------|
| `P0` | 現在の sprint_step or `.1a` | 現在作業継続 or 初期化 |
| `P1` / `P2` / `CC-S` / `CC-M` | `.1a` | sprint 初期化して再開 |
| `P3` / `CC-L` | `null` | sprint 再開せず、計画再編を優先 |

---

## 4. 処理フロー

```
helix interrupt start --id INT-001 --reason "..." --kind design_gap --mode iip
  ↓
1. IDチェック（INT-### 形式、重複禁止）
  ↓
2. classify_iip(design_gap) → "P1"
  ↓
3. resume_step_for(P1, current_sprint_step) → ".1a"
  ↓
4. .helix/interrupts/INT-001.yaml 作成
  ↓
5. matrix.yaml に追加 deliverable 提案（layers=[L4]）
  ↓
6. sprint の current_step を保存 → sprint.status = paused
  ↓
7. 割り込み処理のため phase を L4 に固定、新規 deliverable 対応を開始
```

```
helix interrupt apply --id INT-001
  ↓
1. INT-001.yaml を読み取り
  ↓
2. matrix.yaml に確定された deliverable を追加
  ↓
3. gate-checks.yaml に該当 gate のチェック追加（例: G4 に新規 static check）
  ↓
4. sprint resume_step を次実行可能ステップに設定
```

```
helix interrupt resume --id INT-001
  ↓
1. INT-001.yaml から resume_step を取得
  ↓
2. sprint.current_step を resume_step に設定
  ↓
3. sprint.status = active に復帰
  ↓
4. 「追加 deliverable 対応完了、sprint 再開」を通知
```

---

## 5. 影響層マッピング

```python
# cli/helix-interrupt L287-289
layers_by_class = {
    "CC-S": ["L4"],                     # 実装層のみ
    "CC-M": ["L3", "L4"],              # 詳細設計+実装
    "CC-L": ["L1", "L2", "L3", "L4"],  # 要件層から全層
}
```

IIP の P0-P3 は主に `L4` 層対応（実装時の割り込み）。matrix.yaml に追加 deliverable を挿入して管理する。

---

## 6. エラーハンドリング

| 条件 | 挙動 |
|------|------|
| 同一 ID 重複 | エラー終了 |
| kind が未定義値 | エラー終了（"kind が不正です"） |
| 現在 sprint なし | 新規開始として .1a に設定 |
| P0 で sprint_step が null | `.1a` にフォールバック |

---

## 7. 既知の制約・今後の課題

| 項目 | 内容 | 優先度 |
|------|------|------|
| 分類の自動提案なし | 現状は kind 指定必須、AI 補助で自動分類は未実装 | P3 |
| 履歴分析機能なし | 過去の IIP/CC 傾向分析、類似パターン検索が未実装 | P3 |
| CC-L での L1 対応フロー未整備 | L1 要件層の再定義手順が不明確（PO との連携プロトコル要） | P2 |
| 並列割り込み未対応 | 同一 sprint に複数 IIP 同時発生時の扱い | P3 |

---

## 8. References

- `cli/helix-interrupt` (890行, 割り込み管理本体)
- [SKILL_MAP.md §セキュリティゲート強制条件]
- [ADR-001: Deliverable Matrix as Source of Truth](../adr/ADR-001-deliverable-matrix-as-source-of-truth.md)
- [D-STATE-SPEC.md](./D-STATE-SPEC.md)
