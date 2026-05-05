---
id: PLAN-019
title: "PLAN-019: helix-migrate 対象拡張 (CLAUDE.md / AGENTS.md / .claude/settings.json + 配布戦略明文化)"
status: draft
size: M
phases:
  - L1
  - L2
  - L3
  - L4
created: "2026-05-05"
owner: docs
reviewers:
  - TL
  - devops
depends_on: []
supersedes: []
reference_docs:
  - cli/helix-migrate
  - cli/lib/merge_settings.py
  - cli/helix-doctor
  - cli/helix-init
  - docs/plans/PLAN-017-bats-coverage-core-cli.md
acceptance:
  - "helix-migrate が CLAUDE.md / AGENTS.md / .claude/settings.json を 3-way merge で更新できる"
  - "backup 規約 (.helix/backup/<ts>/, 5 世代保持) を踏襲"
  - "helix-doctor の案内が helix init --force から helix migrate に切替"
  - "既存対象 (.helix/ YAML 5 種) の挙動を破壊しない"
  - "cli/templates/ と skills/ は HELIX_HOME 参照を維持し配布対象に含めない"
---

# PLAN-019: helix-migrate 対象拡張 (CLAUDE.md / AGENTS.md / .claude/settings.json + 配布戦略明文化) (draft v1)

## §1 メタ・背景

HELIX 本体の更新時、配布先プロジェクトに対して `helix init --force` が走るため、既存プロジェクトのローカル追記を保持しづらいという運用摩擦が発生している。  
ユーザーは現在、`backup` 取得 → 差分確認 → manual apply の手順で回避しているが、全体の反復作業コストが高い。

`cli/helix-migrate` は既に対話式 3-way merge と `backup` を前提にした安全な更新を実装済みであり、対象は現在 `.helix/` 配下の 5 種 YAML (`phase.yaml`, `gate-checks.yaml`, `doc-map.yaml`, `matrix.yaml`, `framework.yaml`) のみ。
そのため、配布対象で実害を起こしやすいファイル（`CLAUDE.md`, `AGENTS.md`, `.claude/settings.json`）だけが未対応のまま残り、実質的に更新導線として `helix init --force` に依存している。

また、`cli/templates/`（約 52 ファイル）および `skills/`（約 105 ファイル）については、既存実装で `HELIX_HOME` 参照を採用しつつ、配布先プロジェクトにスプレッドしない運用が成立している。  
ただし、現時点でその配布戦略がドキュメントとして明文化されていないため、本 PLAN で明文化する。

## §2 スコープ

## §2.1 in-scope

- `helix-migrate` の対象に `CLAUDE.md` / `AGENTS.md` / `.claude/settings.json` を追加する
- `merge_settings.py` を `helix-migrate` から呼ぶインターフェイスを定義・統合する
- `helix-doctor` の更新ガイダンスを `helix init --force` 依存から脱却し、`helix migrate` 起動へ切替える
- 配布戦略を文書化し、配布対象/非配布対象の正本マップを作成する

## §2.2 out-of-scope

- HELIX_HOME 参照化の追加拡大（例: `cli/*` への symlink 化）
- `helix-init` 本体の全面刷新
- `CLAUDE.md` / `AGENTS.md` の内容規約の再定義
- T2 (LLM Guard) 対応は本 PLAN の対象外（PLAN-018: LLM Guard 事後ハードニング で別途実施）

## §3 目的・受入条件

## §3.1 目的

`helix init --force` による「全件クリーンアップ」を避け、HELIX 本体更新→配布先反映を `helix migrate` 単体で実施可能にする。  
特に、`CLAUDE.md` / `AGENTS.md` / `.claude/settings.json` の 3 種を安全に同期しつつ、運用上の追従コストを下げる。

## §3.2 受入条件（draft v1）

- Sprint を 4 つで一括実施し、`Sprint .3` では配布マップ整備を重視して実装負荷を抑える
- 既存 3-way merge 行動（`.helix/ YAML 5 種`）を破壊しない
- `backup` 規約（`.helix/backup/<ts>/`, 世代 5）を新規対象にも同一適用
- `helix-doctor` のユーザー誘導文言を `helix migrate` に統一
- 配布戦略（配布対象と非配布対象）を公式文書として明文化する

## §4 Sprint 内訳

## §4.1 Sprint .1: CLAUDE.md / AGENTS.md 対応（text 3-way merge）

`helix-migrate` の `text` 対象を追加し、`CLAUDE.md` と `AGENTS.md` を 3-way merge 対象化する。  
`HELIX-MANAGED-START` / `HELIX-MANAGED-END` をテンプレート内に埋め込み、管理可能セクションのみ上書き対象とする設計をとる。

- 仕様
  - 既存 marker の有無を検出し、存在時は管理領域（managed）のみ merge
  - marker が存在しない旧版では、警告を発しつつ安全側の全置換 fallback を選択可能とする
  - `base` / `theirs` / `ours` の取得元を明確化し、ユーザー追記行の保全優先で merge 方針を固定する

## §4.2 Sprint .2: .claude/settings.json（merge_settings.py 統合）

`cli/lib/merge_settings.py` の 3-way merge を、`cli/helix-migrate` から呼ぶ実装方針を明文化する。  
JSON merge は hook 配列単位を主軸とし、ユーザー追加 hook（HELIX 管理外）を破壊しない。

- 仕様
  - 設定種別別 merge の責務分離（T2 で改善されたマージロジックを呼び出す）
  - `merge_strategy=json_hooks` として設計し、汎用 YAML/text merge と同列に扱わない
  - invalid JSON 受領時は fail-close（merge 中断 → backup + ユーザー事前確認フローへ）
  - 既存の HELIX 管理外 hook（ユーザー追加分）は保持し、削除・上書きしない
  - `exit code 3`（衝突/確認不可）発生時の分岐とユーザー選択提示を `helix-migrate` 側で設計
  - secret / PII を含む可能性のある backup は `.helix/backup/<ts>/` 配下に閉じ、外部送信しない
  - マージ不可時は backup + 事前確認フローを維持して停止
- 受入条件（追加）
  - invalid JSON / non-HELIX hook 保持 / remove / rollback のテストケースを bats と pytest の双方で実装

## §4.3 Sprint .3: 配布戦略明文化 + target registry 設計

`HELIX_HOME` 参照の実装棚卸しを実施し、配布対象を明文化する。あわせて `cli/lib/migrate.py:28-34` の hardcoded TARGETS を **target registry** に移行し、対象拡張時の分岐増加を抑制する。

- 主要確認内容
  - 配布対象: `.helix/*` および プロジェクトルート 2 ファイル（`CLAUDE.md`, `AGENTS.md`）と `.claude/settings.json`
  - 非配布対象: `cli/templates/`, `skills/`, `cli/*`（主要スクリプト群）
  - 配布 map の真価値を定義し、今後の PLAN 改定時の判定基準を定める
- target registry 仕様（L2 で確定、L3 で実装契約化）
  - 各 target に以下のフィールドを持たせる:
    - `root`: `project` / `.claude` / `.helix` の区分
    - `path`: root 相対パス
    - `template`: `HELIX_HOME` 側テンプレートのパス
    - `merge_strategy`: `yaml_merge` / `json_hooks` / `text_with_marker` / `text_overwrite`
    - `backup_policy`: backup 対象範囲と secret / PII の扱い
    - `rollback_policy`: rollback 単位（target 単位 / 全体）
    - `tracked`: git tracked / local 区分
  - 既存 `cli/lib/migrate.py` の hardcoded TARGETS を registry 駆動に置換し、新規対象追加は registry エントリ追加のみで完結させる
- 配置先候補
  - `docs/operations/helix-distribution-scope.md`（新規作成対象、配布 map と registry を併記）
  - または `docs/plans/PLAN-019-...` 付録として初期版を固定

## §4.4 Sprint .4: helix-doctor 案内切替

`cli/helix-doctor` の更新メッセージを切替し、誤誘導を排除する。

- `helix-doctor` の既存警告文（`cli/helix-doctor:176` 想定）を `helix migrate` 起点へ変更
- `check_template_version` の WARN で `helix init --force` を示す箇所を `helix migrate` 起動に誘導
- `--force` は緊急運用経路として残す（非標準推奨として明記）

## §5 DoD

- DoD #1: `helix-migrate` の拡張対象として `CLAUDE.md` / `AGENTS.md` / `.claude/settings.json` の全件追加を設計・実装する
- DoD #2: 3-way merge により「ユーザー追記行」を保護できることを実証（テストで検証）
- DoD #3: backup 規約（`.helix/backup/<ts>/`, 5 世代）を新規対象にも適用し rollback を示す
- DoD #4: `helix-doctor` の案内が `helix migrate` に切替済み
- DoD #5: 配布マップを `docs/operations` または同等の公式ドキュメントへ記載
- DoD #6: `helix-migrate` 関連既存 tests を回帰含めて PASS
- DoD #7: 受入時に DoD #1-#6 とリンク整合チェック結果を memory/retro に反映

## §6 リスク

## §6.1 主要リスク

1. CLAUDE.md のテキスト 3-way merge が難度高  
   緩和: managed/unmanaged を marker で分離し、未整備ファイルは fallback しつつ警告を残す
2. `merge_settings.py` 統合時の依存方向逆転  
   緩和: `helix-migrate → merge_settings.py` の一方向依存に限定し、戻り値と exit code 仕様を厳密化
3. `helix-migrate` rollback の回帰破壊  
   緩和: 対象拡張時に rollback テストを追加・更新し、既存ケースを維持

## §6.2 運用リスク

1. marker を利用者が編集し、merge 不可領域を破損  
   緩和: `CLAUDE.md` に marker 読み取り専用運用（推奨）を明示
2. 差分が大きく、差分確認負荷が増える  
   緩和: `helix migrate --dry-run` と interactive で事前レビューを前提化

## §7 参考

## §7.1 参照

- `cli/helix-migrate`（既存実装: 対話式 3-way merge / backup）
- `cli/lib/merge_settings.py`（JSON merge、T2 改善版）
- `cli/helix-doctor`（更新案内・template_version 判定）
- `cli/helix-init`（現行 cp 配布の比較対象）
- `docs/plans/PLAN-017-bats-coverage-core-cli.md`（PLAN 形状の参照）

## §7.2 関連

- PLAN-018（`LLM Guard 事後ハードニング`）: T2 で導入された配布物増加への安全性補強
- `PLAN-016`（`helix-codex consent gate`）: 配布拡張の前例として参照

## §7.3 リンク整合チェック

- `cli/helix-migrate`: 存在確認済み
- `cli/lib/merge_settings.py`: 存在確認済み
- `cli/helix-doctor`: 存在確認済み
- `cli/helix-init`: 存在確認済み
- `docs/plans/PLAN-017-bats-coverage-core-cli.md`: 存在確認済み
- 未解決保留項目: `0`（未完了項目なし）
