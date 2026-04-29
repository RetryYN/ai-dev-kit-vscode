# PLAN-003: auto-restart 基盤 (HMAC + HOME DB + hook materialization + CURRENT v2 + 残量警告) (v1)

## 1. 目的
- PLAN-002 から auto-restart 関連の複雑領域を切り出し、継続制御（HMAC、再開安全性、HOME DB、CURRENT schema v2）を集中実装する。
- 手動運用＋再起動トリガまでを自動化しつつ、復旧監査可能な HOME DB を前提に運用する。
- B/D outcome 分岐を明文化し、approved/separated の判定条件と再ベースラインループを一貫させる。

## 2. スコープ

### 2.1 含める範囲（この PLAN の対象）
- `worktree_snapshot_hash` / `handover_manifest_hash` / `phase_yaml_hash` を使った HMAC canonical 検証
- HOME DB（`~/.helix/auto-restart/log.db`）
  - `auto_restart_log` テーブル
  - `UNIQUE(task_id, nonce)` と transaction atomic insert
  - 1h rate limit / 90日 retention / VACUUM
- hook registration
- settings merge
- private runtime copy
- CURRENT schema v2（legacy input / normalized output）
- `tiktoken` / `keyring` 依存（未導入時の fallback 定義）
- 30%/15%/5% 残量閾値 + 5% D-owned 自動 dump 契約
- B/D outcome matrix、scope_hash、rebaseline、B-result/D-result
- `context_warnings` / `dep_review_log` の `helix.db v9` 側分離保存（PLAN-002 の v8 完了後）

### 2.2 含めない範囲
- Phase 0 preflight / A0 / A1 / `audit_decisions` migration（PLAN-002 の前提）
- 破壊的操作・既存 `helix.db` の大規模再設計

### 2.3 依存
- `PLAN-002` 完了後に着手。
- `PLAN-002` で決めた candidate scope、`scope_hash`、A1 分類方針を前提とする（本 PLAN への移管は B/D のみに限定。C は除外）。

## 3. 関連 PLAN
- [PLAN-002-helix-inventory-foundation.md](PLAN-002-helix-inventory-foundation.md) が完了済みであることを前提とする。
- 特に `schema_version` と `decisions.yaml` / `audit_decisions` 同期ルールは PLAN-003 の起点整合性検査条件。
- PLAN-002 で未実装の以下を継承
  - auto-restart 仕様
  - CONTINUATION 系フラグ
  - `worktree_snapshot_hash` 以前の抽出要件
  - PLAN-002 の継続分離結果（B/D）のうち、B（自動継続）と D（残量警告）に関係する分のみを継承

## 4. Phase 構成

### L1 要件
- B/D PoC 前提と安全境界の仕様化
- 脅威モデル（外部攻撃者／別 OS ユーザー）と防御境界の再確認
- key ring / fallback key / lock / trust boundary を受入条件化

### L2 設計
- D-HOOK-SPEC 相当の仕様設計
  - HMAC canonical の canonical JSON 定義
  - payload 構造・nonce・expires の検証順序
- D-DB 設計（HOME DB + auto_restart_log）
- D-CURRENT 設計（CURRENT schema v2）
- D-DEPENDENCY 設計（tiktoken / keyring / gitleaks の依存方針）

### L3 詳細
- DDL / migration / retention を本文に確定
- hook registration と private runtime copy のファイル権限制約を明文化
- B と D の独立判定フローを確定（最終結果は cross product）
- 残量警告の matcher / threshold の検証手順と失敗時挙動

### L4 Sprint 構成（v34 と同等）

#### Sprint 1: Shared + D-HOOK-SPEC 固定
- HMAC 署名キー、nonce/replay、snapshot/handoff hash 検証の共通実装
- payload 受け渡しと settings merge

#### Sprint 2: B 自動継続 core
- hook 登録
- private runtime copy
- home DB への起動履歴記録

#### Sprint 3: D 残量警告 core
- matcher 実装（Read/Bash/Edit/Write/Glob/Grep）
- 30%/15%/5% の閾値分岐

#### Sprint 4: 統合 + B/D 接続
- B/D outcome matrix の実装
- restart pending 表示（手動再開）
- B approved / B separated / D branch の分離処理

#### Sprint 5-6: 回帰・耐障害
- 並行 hook テスト
- migration rehearsal / retention / VACUUM 一貫性検証

### L6 検証
- G1R（事前調査）と G1.5（PoC）の結合検証（B、D、B+D の3段階）
- 自動再開・警告発火・retry/replay を観測
- fresh checkout で HOME DB と runtime copy が再現できることを確認

### L7 デプロイ
- auto-restart on/off、鍵の設定、runtime copy 生成
- 依存ライブラリ（keyring/tiktoken/gitleaks）未導入時の運用モード

### L8 受入
- 受入は G1.5(B)、G1.5(D)、G1.5(B+D) を通して実施
- B/D 最終行列を通し、PLAN-002 からの引継ぎデータに整合があることを確認

## 5. ゲート

### G1R(B)
- hook event と claude 再開経路の事前調査
- `SessionEnd` 固定の可否、Stop adapter 代替まで含める
- `docs/research/B-feasibility.md` で成果固定

### G1R(D)
- usage API / matcher / settings merge / tiktoken/keyring license / 非 tool 区間補完 hook
- `docs/research/D-feasibility.md` で成果固定

### G1.5(B)
- PoC: 3/3 連続成功
- 失敗時は B separated へ分岐

### G1.5(D)
- PoC: Read/Bash/Edit/Write/Glob/Grep matcher の 6 matcher 全通過
- 30% / 15% / 5% 閾値を順次発火させ、5% での D-owned dump を実施
- 失敗時は D separated へ分岐
- B separated 時でも 5% 時点の手動再開表示を維持

### G1R(B+D)
- 事前調査完了（B または D を先に実施しても順序が成立する証拠）
- ここでは `PLAN-002` での A0/A1 との依存を確認

### G1.5(B+D)
- PoC の結合検証（B と D の並行動作整合性）
- B と D の結果を outcome matrix（B_result × D_result）に反映
- 再現性のある再実行基準（scope_hash）を前提に通過判定

## 6. B/D outcome matrix（判定軸分離）

- B 軸: 3/3 連続成功、restart 経路成功、HMAC/replay 安全性検証により
  - Bapproved / Bseparated
- D 軸: 6 matcher 全通過、30%/15%/5% 閾値発火、5% D-owned dump により
  - Dapproved / Dseparated
- 最終 outcome は `B_result × D_result` の 4 ケースで評価

| outcome | B_result | D_result | 該当 deferred PLAN | rebaseline 範囲 |
| --- | --- | --- | --- | --- |
| both-approved | Bapproved | Dapproved | PLAN-003 全体（A） | rebaseline 不要 |
| b_approved-d_separated | Bapproved | Dseparated | D側（matcher/threshold） | D axis の再ベースライン |
| b_separated-d_approved | Bseparated | Dapproved | B側（restart/hmac） | B axis の再ベースライン |
| both-separate | Bseparated | Dseparated | 両軸（共通） | B/D 両軸の再ベースライン |

## 7. HMAC + hash 仕様

### 7.1 署名対象
- canonical JSON に格納するフィールド
  - `task_id`
  - `resume_id`
  - `cwd`
  - `branch`
  - `head_sha`
  - `worktree_snapshot_hash`
  - `handover_manifest_hash`
  - `phase_yaml_hash`（`.helix/phase.yaml`）
  - `expires_at`
  - `nonce`

### 7.2 ハッシュ算出
- `HMAC-SHA256`
- `worktree_snapshot_hash`: git porcelain v2 + untracked 完全展開 + canonical JSON レコード + path/base path 正規化
- `handover_manifest_hash`: `CURRENT.json` を含む `.helix/handover/` 参照ファイルの path/content sha256 を canonical 並び替えしハッシュ
- `phase_yaml_hash`: `.helix/phase.yaml` の SHA-256

### 7.3 replay / 検証
- `nonce` と `auto_restart_log` の `(task_id, nonce)` で replay 防止
- `expires_at` 期限切れは拒否
- 起動時 workspace snapshot、branch、head_sha の一致を再検証

## 8. HOME DB: `~/.helix/auto-restart/log.db`

### 8.1 DDL（HOME DB v1 / 所有境界）
```sql
CREATE TABLE IF NOT EXISTS home_db_schema_version (
  component TEXT PRIMARY KEY,
  version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS auto_restart_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL,
  nonce TEXT NOT NULL,
  payload_sha TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  decision TEXT NOT NULL,
  source TEXT,
  UNIQUE(task_id, nonce)
);
```

### 8.2 運用
- 1時間あたり 6 回を既定 rate limit とし、UTC epoch で計算
- 90 日 retention
- VACUUM + cleanup で古いレコードを削除
- retention は HOME DB 単体（`auto_restart_log`）を 90 日で維持
- `auto_restart_log` は home DB 専有。`helix.db` へ移行しない
- `home_db_schema_version` は HOME DB で v1 から開始
- `helix.db` 側の schema 変更は PLAN-002 の v8 構成維持後、PLAN-003 で `D-DB-MIGRATION` を参照して v9 を追加

### 8.3 追加仕様ファイル
- HOME DB: `docs/design/D-HOME-DB.md`（本 PLAN で HOME DB v1 スキーマとして明文化）
- helix.db: `docs/design/D-DB-MIGRATION.md`（`context_warnings` / `dep_review_log` を v9 で追加）

### 8.3 trust boundary
- DB と directory 権限を確認
  - `~/.helix/auto-restart/`：owner current user、dir mode <= 0700、symlink 禁止
  - `~/.helix/auto-restart/log.db`：mode <= 0600
- 不一致は fail-closed

## 9. hook registration / settings merge / private runtime copy

### 9.1 hook registration
- hook event を G1R(B) と G1R(D) の調査結果で固定
- hook は許可コマンドリスト（最小限）を保持
- `helix auto-restart` を実行 entry とする

### 9.2 settings merge
- `~/.config/helix/auto-restart.local.yaml` へ機密情報を集約
- `.claude/settings.json` 等は機密を残さない構成に変更
- merge は whitelist ベースで実施
- trust boundary（`~/.config/helix/`）
  - 配置: `~/.config/helix/` 配下のみ（project-local 配置禁止）
  - `~/.config/helix` 配下の機密ファイル: owner current user、dir mode = 0700、file mode = 0600、symlink 禁止
  - 起動時に owner/mode/symlink を検証し、不一致時は fail-closed
  - 適用対象:
    - `~/.config/helix/auto-restart.local.yaml`
    - `~/.config/helix/auto-restart.key`
    - `~/.config/helix/redaction-denylist.hmac.yaml`
  - 検証: gitleaks は HOME 配下を対象外扱い。project `.gitignore` での `.config/helix/auto-restart.local.yaml` 除外規則は不要

### 9.3 private runtime copy
- 起動時に runtime copy を `~/.helix/auto-restart/runtime/<hash>.sh` へ複製
- mode 0700 で絶対パス実行
- project-local 依存パスを固定し、起動中 snapshot 変動を回避

## 10. CURRENT schema v2

### 10.1 分離方針
- legacy input / normalized output の入力構造を分離
- 互換時は adapter を保持し、既存挙動との段階的接続を維持

### 10.2 受入条件
- 旧形式互換を維持したまま、normalized output で検証ログを取りやすくする
- 変換失敗は fail-closed とし、再試行ガイダンスを提示

## 11. 残量警告・5% D-owned 自動 dump

### 11.1 閾値
- 30%: 事前警告
- 15%: 強化警告
- 5%: 自動対応（approved: auto-restart 連携、separated: D-owned dump + 手動再開表示）

### 11.2 依存
- tiktoken と keyring は依存登録
  - tiktoken 未導入時は heuristic fallback
  - keyring 未導入時は key fallback を明示（OS keyring優先）

### 11.3 D-owned dump 契約
- 5% 時点で dump を契約化
- restart-pending は request id のみを提示
- `helix handover dump` 再起動導線は手動 or 自動分離を outcome で切替

## 12. Phase 0（PLAN-002 完了前提）

- Phase 0 preflight、A0/A1、`audit_decisions` 追加 migration は PLAN-002 完了済とみなす。
- L4 実装前提として次を参照する
  - `docs/plans/PLAN-002-helix-inventory-foundation.md`
  - `~/.helix/audit/decisions.yaml`
  - `helix.db` v8 migration（audit_decisions 部分）

## 13. リスク

- R-1: key/rsa 同様の署名管理失敗
  - 対応: keyring 優先、ファイル fallback は明示制約
- R-2: hash の不一致再現性
  - 対応: fixture ベースの hash fixture 分離と再現順序固定
- R-3: hook 監査対象の event mismatch
  - 対応: G1R で 2 系統（SessionEnd/Stop）を検証し固定
- R-4: matcher 差分で残量警告漏れ
  - 対応: 6 matcher fixture (Read/Bash/Edit/Write/Glob/Grep) + 非 tool 区間補完を L3/L4 で検証
- R-5: HOME DB 破壊
  - 対応: backup/restore + VACUUM 併走 + owner/mode の fail-closed

## 14. リリース前提テスト
- auto-restart replay test（N=10 同時 hook）
- insert-or-reject atomicity
- rate limit 6/h
- 90 日 retention と cleanup を L6 で連続検証
- fresh checkout で trust boundary を再生成確認
- B/D matcher と hooks を再起動ログ付きで検証

## 15. 改訂履歴

| 日付 | バージョン | 変更内容 |
| --- | --- | --- |
| 2026-04-29 | v1 | PLAN-002 v34 の auto-restart・残量警告・hook 運用を抽出し、独立計画として新設 |
| 2026-04-29 | v2 | TL レビュー（P1×2/P2×3/P3×1）反映。C を除外し B/D に統一、G1.5(D) 追加、判定軸分離、信頼境界と DB 所有境界を明文化 |

## 16. 参照
- `.helix/plans/PLAN-002.yaml`（source_file 参照設定は既存）
- `.helix/plans/PLAN-003.yaml`（source_file 参照設定は既存）
- `docs/design/D-HOOK-SPEC.md`
- `docs/design/D-DB-MIGRATION.md`
- `docs/design/D-STATE-SPEC.md`
- `docs/design/DEP-shared.md`
- `docs/research/B-feasibility.md`
- `docs/research/D-feasibility.md`
