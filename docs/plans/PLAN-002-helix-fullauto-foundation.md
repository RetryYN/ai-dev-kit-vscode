# PLAN-002: HELIX フルオート化基盤 (v34)

> サイズ: L (be駆動) / 推奨フェーズ: **[Phase 0 preflight]→Phase 0**→L1→G1→**[Phase 1.4: waiver]→G1R(B+D)→G1.5(B+D 結合 PoC)→L2→L3→[A1 分類 100% classified or 再ベースライン]**→**L4 Sprint 1-6**→L6→L7→L8 (L5 skip)
> 関連: PLAN-002.yaml / phase.yaml current_phase=L1
> 改訂: v34 (2026-04-28) — TL レビュー P1×2/P2×3 反映 (P1#1 G-2 受入条件統一、P1#2 HOME DB 検証追加、P2#1 CURRENT schema v2 入出力分離、P2#2 phase.yaml 集約を failed 化、P2#3 hash fixture 分離) / P3 タイトル・改訂履歴 v34

## 背景

HELIX フレームワークは CLI・スキル・ゲートが揃い、L1〜L8 と Phase R/Phase S が運用可能な段階に到達した。次の課題は **「企画以降のフルオート化」** であり、現状以下のギャップがある:

1. **セッション継続が手動**: Claude Code のコンテキスト上限到達時、`helix handover dump` は備わっているが、その後の「新セッション起動 → handover resume → 作業継続」が人間操作頼み。
2. **コンテキスト管理が受動的**: `context-memory` スキルはあるが警告層がなく、気付いた時には詰まっている。
3. **死蔵資産が増加傾向**: cli/ 37 コマンド・skills/ 100 スキル中、実装はあるが未使用 (skill_usage に記録なし) のものが混在。
4. **Reverse モードの発火条件が未整備**: `helix reverse <R0-R4>` は手動コマンドのみで、既存コード検出時の自動推奨がない。

これらを統合的に解決し、PM (Opus) の介入を最小化する基盤を整備する。

## 攻撃者モデル (脅威モデル前提、TL レビュー P1#1 反映)

本 PLAN の自動再起動機構は **ローカル単独利用** を前提とする。攻撃者モデル:

| 攻撃者 | 防御対象 | 備考 |
|--------|---------|------|
| 外部攻撃者 (ネットワーク経由) | ✅ 防御 | HMAC 署名 + replay 防止 |
| 別 OS ユーザー | ✅ 防御 | ファイル mode + プロセス権限分離 |
| **同 OS ユーザーで Bash 実行できる workspace 内プロセス** | ⚠️ **対象外** (脅威モデル外) | Claude Code 自身がこの能力を持つため、根本的に防御不可 |
| 物理アクセス | ❌ 対象外 | OS レベルの問題 |

**結論**: HMAC は「外部攻撃者・別ユーザー」までを防御範囲とし、workspace 内 Bash プロセスを脅威に含めない。鍵保管は OS keyring (利用可能時) + ファイル fallback の 2 段とする。HMAC を「ローカル workspace 攻撃者からの完全防御」とは呼ばない。

## 目的・ゴール

| ID | ゴール | 検証方法 (統一指標) |
|----|-------|---------|
| G-1 | セッション切れ後も次セッションが自動継続する | **3/3 end-to-end 連続成功** (resume id 整合 / 非対話起動 / hook 発火 / 復帰後継続のすべて) |
| G-2 | **対応 tool event 発火時** にコンテキスト残量が閾値を切ると警告/自動 dump が走る (TL レビュー v11P2#2 反映: tool hook 限定として明示) | **B approve / B separated で受入条件を分岐** (下記マトリクス参照): B approved = 30%/15%/5% 全段階発火 + 自動 dump + auto-restart 連携、B separated = 30%/15% 警告のみ + 5% は D-owned 自動 dump + **手動 restart（resume コマンド表示）**、いずれも Read/Bash/Edit/Write/Glob/Grep matcher でテスト通過。**残余リスク**: 非 tool 区間 (長応答中・hook 不発火期間) はカバー外。L8 受入レポートに残余リスクとして必須記載 |
| G-3 | 死蔵資産が **「検証済み decisions.yaml による分類確定」** される (TL レビュー v21P1#1 反映: 表現統一) | **L1/G1 で凍結した scope 内候補が 100% `classified` (keep/remove/merge/deprecate) に到達 + decisions.yaml が schema validator (G3 前凍結) で valid + dry-run import が pass**。triaged 残存時は **G-3 fail** (本 PLAN は未完了扱い、PLAN-004 移管)。**scope 変更は G3 前の L1/G1 再ベースラインのみ** (L8 conditional/PO 受容は撤廃) |
| G-4 | 既存コードに対し Reverse R0 が自動「推奨」される (自動発火しない) | 既存リポで `helix init` 実行 → Reverse 推奨プロンプト発火、R0 から順に開始 |

**B 用統一指標 (G-1 / G1.5(B) / B Kill Criteria 共通、TL レビュー P2#3 反映: B 専用に限定)**:
- pass: **3/3 end-to-end 連続成功** (連続必須)
- fail (試行単位): resume id 不整合 / 非対話実行失敗 / hook 未発火 / 復帰後継続不能 のいずれか 1 つでも発生
- 分離 (Kill): 3 回連続失敗 or 1 sprint (= 5 営業日) 超過

**D 用指標 (G1.5(D) / D Kill Criteria 共通、別定義、TL レビュー v24P1#1 反映: conditional/advisory 経路撤廃)**:
- **pass (full、唯一の達成経路)**: 全 matcher (Read/Bash/Edit/Write/Glob/Grep) で警告発火確認 + 重複 dump 抑止動作 + 残量計算成功 (**usage API or 誤差検証済み tokenizer (誤差率 ≤ 10%) で計算**)
- **stdlib-only fallback の扱い (TL レビュー v24P1#1 反映: conditional pass 撤廃)**:
  - 残量計算が usage API でも誤差検証済み tokenizer でも成立しない場合は **G-2 fail**
  - 例外: L1/G1 再ベースラインで「advisory warning goal」として scope を再定義し、別ゴール扱いとする場合のみ stdlib-only での運用を許容 (この場合は元の G-2 達成扱いではなく、別 ID の goal として扱う)
- **非 tool 補完の位置付け (TL レビュー v27P2#2 反映: G-2 達成条件から分離)**:
  - **tool hook full pass (Read/Bash/Edit/Write/Glob/Grep)** = G-2 本体達成条件 (必須)
  - **Stop/Session hook + 定期チェック** = **advisory 補強** (G-2 本体達成には不要、採用時の追加品質指標)
  - 採用時の判定表:
    | 補完採用 | Stop/Session hook | 定期チェック | 判定 |
    |---------|---|---|---|
    | 非採用 (G2 で確定) | — | — | G-2 残余リスクに「非 tool 区間カバー外」必須記載 |
    | 採用 + 両方 pass | ✅ | ✅ | G-2 full pass + advisory 補強あり (推奨状態) |
    | 採用 + 片方のみ pass | ✅ or ✅ | ✅ or ❌ | G-2 full pass (本体は無傷) + L8 残余リスクに「補完一部欠落」記載 |
    | 採用 + 両方 fail | ❌ | ❌ | **D fail / PLAN-005 分離** (補完を採用と宣言したのに動かない = 実装計画破綻) |
  - L8 チェックリストは **pass 必須項目** (tool hook full pass) と **残余リスク記載項目** (補完欠落・非採用時) を別行に分けて運用
- 非 tool 補完非採用時 (G2 で確定): L8 残余リスクに「非 tool 区間カバー外」を必須記載するのみ (scope 外明示)
- fail: いずれかの matcher で発火不能 / 残量計算が usage API でも誤差検証済み tokenizer でも不能 (stdlib-only は G-2 fail と等価) / 非 tool 補完採用時に補完が完全機能停止
- 分離 (Kill): 上記 fail 持続 or 1 sprint 超過

## スコープ

### 取り組み一覧 (5 件、依存粒度明記、TL レビュー P1#1 反映: A 分割)

| ID | 取り組み | 依存 | 規模 | 達成範囲 (L8) |
|----|---------|-----|------|------|
| **A0** | 死蔵資産 Discovery / Inventory (candidate 抽出) | (起点) | S | candidate 一覧化、初期トリアージまで |
| **A1** | 死蔵資産 Classification (classified 確定) | A0 | M | L1/G1 で凍結した scope 内候補 100% classified 到達 (TL レビュー v21P1#1 反映: 表現統一)。triaged 残存時は **G-3 fail** のみ。**scope 変更は G3 前の L1/G1 再ベースラインのみ**、L8 での scope 縮小・pass 再定義 / conditional / PO 受容は禁止 |
| B | 自動継続パイプライン (PoC 必須) | **A0 のみ** + G1R(B) + G1.5(B) | M | PoC 失敗時は **PLAN-003** へ分離 |
| C | Reverse 自動「推奨」(発火ではない) | A0 | S | 推奨と前提不足提示のみ |
| D | コンテキスト管理警告層 (PoC 必須) | **A0 のみ** + G1R(D) + G1.5(D) | S | 30%/15%/5%、Read/Bash/Edit/Write/Glob/Grep matcher で発火 |

**A 分割の意味 (依存粒度の明確化)**:
- B/C/D の **G1R/G1.5 段階** = A0 (candidate 抽出) のみ依存。A0 完了で B/D の調査・PoC を開始可能
- B/C/D の **L4 実装段階 / L8 受入段階** = A1 (classified 確定) 依存。A1 完了が L4 Sprint 2-4 の前提
- A1 自体の実装は L4 Sprint 1 で実施 (B/C/D Sprint 2-4 と並列ではなく前段)

### A0: 死蔵資産 Discovery / Inventory (TL レビュー P1#1/v7P1#2 反映: 手動棚卸し明記)

**実行方法 (Phase 0 では新規 CLI を作らない、TL レビュー v7P1#2/v8P2 反映)**:
- **既存ツール + 一時スクリプト** で手動棚卸し
- 既存 CLI: `helix log report quality` / `helix skill stats` / `git log --since` / `grep -rn`
- **一時スクリプト** (TL レビュー v8P2/v10P2#1 反映: 再現性確保 + secret/PII 漏洩防止):
  - 配置: `.helix/audit/scripts/inventory-once.sh` (**git 管理対象**、本 PLAN 完了後も保存)
  - **`.gitignore` allowlist 更新が必須** (TL レビュー v13P2#2/v14P1#1 反映: 現行 `.gitignore` は `**/.helix/**` 全体除外のため、親ディレクトリ再 include 明示):
    - **親ディレクトリの再 include (必須、TL レビュー v14P1#1 反映)**:
      - `!**/.helix/audit/`
      - `!**/.helix/audit/scripts/`
      - `!**/.helix/gate-waivers/`
      - `!**/.helix/baseline/`
    - 各ディレクトリ配下のファイル再 include:
      - `!**/.helix/audit/scripts/**`
      - `!**/.helix/audit/*.md`
      - `!**/.helix/audit/decisions.yaml`
      - **`!**/.helix/audit/allowlist.yaml`** (TL レビュー v15P2 反映: 検出ロジックが参照、git 管理必須)
      - **`!**/.helix/audit/redaction-denylist.example.yaml`** (非秘匿の汎用パターンのみ、初期配布)
      - **`!**/.helix/audit/redaction-denylist.hmac.yaml`** (必要時のみ、HMAC 化運用で git 管理可)
      - `.helix/audit/redaction-denylist.local.yaml` は .gitignore 対象（実運用値）
      - `!**/.helix/gate-waivers/**`
      - `!**/.helix/baseline/**`
    - **追加必須**: `.gitignore` に `**/.helix/audit/redaction-denylist.local.yaml` を追記
    - 引き続き除外: `.helix/audit/runs/**` (secret 含む可能性、ローカルのみ)
    - **検証 (TL レビュー v17P2#2/v24P3 反映: 正本パス一本化)**:
      - **`git check-ignore -v --non-matching <各対象パス>`** を使用 (`--non-matching` で tracked/non-ignored も明示記録、tracked 側で非ゼロ終了にならない)
      - 補助検証: `git status --ignored --short` で全体的な tracked/ignored 状態を一覧化
      - 期待結果: tracked 対象は `--non-matching` 出力 (パターンに合致しない)、ignored 対象は通常の check-ignore 出力 (パターン番号付き)
      - **保存先 (正本): `docs/research/preflight-gitignore-verification.log` (Phase 0 preflight 成果物)**。L1 では同ファイルを参照 (重複作成しない)
    - 本 PLAN の L1 成果物として `.gitignore` 更新パッチ + 検証ログを含める
  - 実行証跡: 実行時に `inventory-run-<head_sha>-<timestamp>.log` を `.helix/audit/runs/` に保存 (script 本文 hash + 実行コマンド + 対象 head_sha + DB snapshot 条件 + **集計結果のみ** を記録、stdout/stderr 全量保存はしない)
  - **secret/PII 対策 (TL レビュー v10P2#1/v11P2#1 反映: ファイル名漏洩も防止 + stream redaction)**:
    - **runs 配下を gitignore**: `.helix/audit/runs/**` を `.gitignore` に追加 (git 管理外、ローカルのみ)
    - **ファイル権限 0600**: 実行ログは owner-only 読み書き
    - **stream redaction (新)**: ログ書き込み **前** に redaction を適用。stdout/stderr を直接ファイルに書かず、redaction filter を経由
    - **redaction ルール (TL レビュー v20P2#3 反映: 決定的仕様)**: 以下の **具体的パターン** に合致するファイル名・本文は除外/hash 化 (曖昧語「顧客名らしき」を撤廃):
      - **ファイル名 patterns**: `.env*` / `*credentials*` / `*secret*` / `*token*` / `*api_key*` / `*.key` / `*.pem` / `*.crt` / `*.p12` / `*.pfx`
      - **本文 regex**: メールアドレス (`[\w.+-]+@[\w-]+\.[\w.-]+`)、IP v4 (`\b(?:\d{1,3}\.){3}\d{1,3}\b`)、AWS access key (`AKIA[0-9A-Z]{16}`)、JWT (`eyJ[\w-]+\.[\w-]+\.[\w-]+`)、Bearer token (`Bearer\s+[\w.-]+`)、credit card 様 (`\b\d{13,19}\b`)
      - **denylist 補助**: `.helix/audit/redaction-denylist.example.yaml` に非秘匿初期パターンを定義。プロジェクト固有語（顧客名/内部コード名/secret 断片）は `.helix/audit/redaction-denylist.local.yaml`（.gitignore 管理）で平文運用
      - **テストケース必須**: L1/L2 成果物に redaction テストケース (`.helix/audit/scripts/test-redaction.sh`) + サンプル期待値を追加 (合致/非合致を網羅)
        - **本文**: ログから完全除外 (記録しない)
      - **ファイル名 (TL レビュー v23P2#2 反映: HMAC-SHA256 + 専用キー)**: 名前列にも残さず、**HMAC-SHA256(redaction_key, filename) + 分類カウントのみ** 記録 (例: `secret-suspect-files: { count: 3, hashes: [a1b2..., c3d4..., e5f6...] }`)
      - **redaction key 管理**: `~/.config/helix/audit-redaction.key` (mode 0600、Tier A 検証対象、Phase 0 preflight で初期生成)、key rotation は手動 (rotation 時は過去 hash と比較不能になる旨を明示)、漏洩時は新 key 生成 + 既存 hash 無効化
      - **辞書攻撃耐性**: HMAC-SHA256 + 専用 key により固定 salt 方式の辞書攻撃を防御
      - **再現性**: 同一 key + 同一 filename → 同一 hash (key 変更なしなら run 間で比較可能、rotation で再現性は意図的に途切れる)
    - **除外対象**: `.git/` / `node_modules/` / `__pycache__/` / `*.lock` / `.env*` / `*.key` / `*.pem` / `*.crt` を grep 対象から除外 (そもそも読み込まない)
    - **secret scan + fail-closed**: `inventory-once.sh` 完了後、生成された run ログに対し `gitleaks detect --source <log>` を実行、検出ありなら **fail-closed + ログ削除**
    - **gitleaks 未導入時 fail-closed (新)**: gitleaks が未インストールの場合、A0 実行を **拒否** (`gitleaks` 必須依存として DEP-shared に追加検討、または手動インストールを Phase 0 前提条件とする)
    - **Phase 0 preflight 追加チェック**:
      - `.helix/audit/redaction-denylist.local.yaml` が tracked されていないことを検証（tracked であれば fail-closed）
      - gitleaks + custom check で local denylist の tracking 漏れを検知する
  - 再現可能性: head_sha + script hash + DB snapshot から再実行可能であること (ただし redaction 後のため完全 byte-identical でなくてよい、集計結果が一致すれば OK)
- **A0 段階で新規 CLI (`helix audit detect` 等) は実装しない**。実装は L4 Sprint 1 (A1 と同時) で行う

**達成範囲**: candidate 抽出 + 初期トリアージ完了まで。
- candidate 抽出 (手動 + 一時スクリプト、検出ロジックは下記参照)
- triaged まで進める (needs-human/unknown を含む)
- decisions.yaml に状態記録、fail-safe 適用
- B/C/D の G1R/G1.5 段階の依存先 (Phase 0 完了で開始可能)

**A0 の CLI**: なし (手動運用)。L4 Sprint 1 で A1 CLI と同時に実装する場合は `helix audit detect` / `helix audit triage <id>` を含める。

### A1: 死蔵資産 Classification (達成範囲 = classified まで)

**状態機械 (TL レビュー P2#4 反映、triaged/classified 分離)**:

```
candidate (検出)
  ↓ 初期トリアージ (allowlist/denylist 適用、参照グラフ確認)
triaged (情報不足 or 人間判断待ち):
  - needs-human: 自動判定不能、人間判断要求 (owner + 期限 + PLAN-004 引継ぎ条件必須)
  - unknown: 候補だが情報不足、追加調査必要 (owner + 期限 必須)
  ↓ 追加情報・人間判断
classified (確定):
  - keep / remove / merge / deprecate
  ↓ [本 PLAN-002 はここまで]
  ↓
  ↓ [PLAN-004 へ]
  ↓ quarantined (隔離アーカイブ)
  ↓ removed (7 日経過 + テスト GREEN)
```

**fail-safe ルール (TL レビュー P2#4 反映)**:
- 分類値とは独立した「実行アクションのフォールバック」: 証跡不足時は **実行アクションを `keep` 側に倒す** (削除しない)
- 状態は `triaged (unknown)` のままで、L8 G-3 達成にはカウントしない
- これにより「分類値の意味の曖昧さ」と「fail-safe の保守性」を分離

**L8 G-3 受入条件 (TL レビュー v20P1#3 反映: v19 方針に統一、conditional 撤廃):**
- **G-3 pass = L1/G1 で凍結した scope 内候補が 100% `classified` (keep/remove/merge/deprecate)** (G3 通過時点で達成済み、L8 では検証のみ)
- triaged (needs-human/unknown) が 1 件でも残っていれば **G-3 fail** (本 PLAN は未完了扱い、残件を PLAN-004 へ移管)
- **L8 では scope の縮小・pass 条件再定義を禁止** (G1/G2/G3 freeze の信頼性確保)
- **G-3 conditional は撤廃** (TL レビュー v19P2#3 反映)
- scope 変更が必要な場合の手続き:
  - **G2/G3 以前の change control** のみ (L1 受入条件を正式に修正、再度 G1 通過させる新 scope は 100% classified 必須)
  - **PO 明示受容は G3 前の L1/G1 再ベースラインで対処**、L8 では適用不可 (pass 代替ではない)

**検出ロジック (継続)**:
- `helix.db` の `skill_usage` / `task_runs` で 30 日以上記録なし
- ファイル間 grep で参照ゼロ
- CLI help / docs/ / templates/ / hooks / 動的ディスパッチ呼び出しを参照グラフに含める
- `helix audit allowlist.yaml` (将来用・手動実行ツール) で除外
- deprecated マーク残存実装あり
- SKILL_MAP.md 言及だが SKILL.md 不在 / SKILL.md 内 references 切れ

**出力**:
- `.helix/audit/orphans.md` (検出候補)
- `.helix/audit/refactor-candidates.md` (統合候補)
- `.helix/audit/integrity-breaks.md` (整合性破綻)
- `.helix/audit/decisions.yaml` (各候補の状態 + 分類結果 + 判断証跡 + fail-safe action)

**A1 CLI 追加 (TL レビュー v27P1#2 反映: quarantine 実装は PLAN-004 へ延期)**:
- `helix audit classify <id>` — classified 状態へ確定 (A1 のメイン動作)
- `helix audit status` — 全候補の状態一覧 (A0/A1 共通)
- **`helix audit quarantine` は本 PLAN では実装しない** (TL レビュー v27P1#2 反映: 破壊的操作面の早期増加を回避): quarantine/remove は PLAN-004 で初めて実装する。本 PLAN では quarantine 用の状態定義 (decisions.yaml schema) のみ凍結、実行 CLI は導入しない

### B: 自動継続パイプライン (PoC 必須)

**Phase 構造**:

```
G1R(B): 事前調査 (B 専用)
  ↓ Claude Code hook event の実在名・payload・timeout・blockOnFailure 検証
  ↓ → SessionEnd 実在しない場合は Stop adapter として設計可能性を確認
  ↓ claude --resume の非対話実行検証
  ↓ Codex 常駐 vs 都度起動の比較
  ↓ TTY/認証要件の調査
  ↓ resume id 取得方法
  ↓ プロセス終了時の子プロセス起動可否
  ↓ 失敗時 手動 restart（resume コマンド表示）設計

G1.5(B): PoC (最小再現)
  ↓ 統一指標 (3/3 end-to-end 連続成功) で判定
  ↓ kill criteria: 3 回連続失敗 or 1 sprint 超過 → PLAN-003 へ分離
```

**threat model (TL レビュー P1#1 反映、L2 で詳細化必須)**:

| 項目 | 仕様 |
|------|------|
| **攻撃者モデル** | 外部攻撃者 + 別 OS ユーザー (workspace 内 Bash プロセスは対象外、上記参照) |
| 鍵保管 | **OS keyring 優先** (Python `keyring` ライブラリで抽象化、gnome-keyring/Keychain/wincred)、未利用環境では `~/.config/helix/auto-restart.key` mode 0600 fallback (workspace 内攻撃者には防御不可と明示)。keyring 依存仕様 (license/backend/fallback/テスト) は **DEP-shared.md (L3 成果物)** で凍結 |
| 鍵 rotation | 30 日ごとに `helix auto rotate-key` で再生成、auto_restart_log に rotation 記録 |
| 署名対象 (canonical、TL レビュー v19P1#1 反映: handover manifest 方式) | `task_id` + `resume_id` + `cwd` + `branch` + `head_sha` + **`worktree_snapshot_hash`** (下記参照) + **`handover_manifest_hash`** (新、下記参照) + **`phase_yaml_hash` (`.helix/phase.yaml` の SHA-256)** + `expires_at` + `nonce` の JSON canonical 形式 |
| **handover_manifest_hash** (TL レビュー v27P2#1 反映: 計算順序・ロック境界凍結) | `.helix/handover/` 配下で auto-restart が読むファイルを manifest 化（`CURRENT.json` を必須とし、`CURRENT.md`/archive は運用で追加）。各要素を `{"path":"<base64-utf8>","content_sha256":"<hex>"}` として収集し、`path` を UTF-8 bytes + NFC 正規化後のバイト列順でソートした **canonical JSON** の SHA-256 を算出。**シリアライザー**は Python `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`、数値・モードは hex 固定。/ **計算順序の凍結**: `helix handover dump` 完了 (handover lock 保持) → manifest 対象確定 → manifest hash 算出 → 署名 → handover lock 解放 → auto-restart lock 取得 → 起動。並行 `helix handover update` は競合待機。**期待 SHA-256 テストベクタ（G1.5(B)/L3 D-HOOK-SPEC 必須）**: CURRENT.json 単体 / CURRENT.json + CURRENT.md / CURRENT.json + CURRENT.md + archive/PLAN-002-rebaseline-*.md / path NFC+base64 正規化（非 ASCII path） / 欠損ケース（CURRENT.md 不在 / archive 不在） / handover lock 競合。rename/symlink/submodule/untracked をワークツリ側へ移管 |
| **worktree_snapshot_hash** (TL レビュー v15P1#1 反映: untracked nested 完全展開) | **以下のアルゴリズムで生成 (D-HOOK-SPEC で凍結)**: 1. **`git status --porcelain=v2 -z --untracked-files=all`** + `git ls-files --cached -s` + **`git ls-files --others --exclude-standard -z`** で tracked/staged/modified/**untracked (nested directories の個別ファイルまで完全展開)**/deleted/renamed/symlink/submodule を明示列挙 (NUL 区切り、重複排除) / 2. 除外パターン適用 (下記 runtime artifact) / 3. 各エントリを以下の **canonical JSON レコード**に正規化: `{"status":"<XY_status>","type":"<type>","path":"<base64-utf8>","old_path":"<base64-utf8|->","index_mode":"<index_mode>","worktree_mode":"<worktree_mode>","index_repr":"<hash>","worktree_repr":"<hash>"}` (XY_status = porcelain v2 の X/Y 2 文字組、type=blob/symlink/submodule/tombstone、old_path = rename 元パス or `-`、**index_repr** = staging area の **content SHA-256** (TL レビュー v22P2#1 反映: Git object format 非依存。`git cat-file blob <oid>` で blob 内容を取り出してから SHA-256 計算、Git object id (SHA-1/SHA-256) と混同しない / symlink=`link:`+target SHA-256 / submodule=`subm:`+commit_id (固定 hex format) / staged-deleted=`tombstone:`+old content SHA-256 / **unmerged は `unmerged:` プレフィックス、intent-to-add は `iat:` プレフィックス**)、**worktree_repr** = working tree の **content SHA-256** (working file から直接 SHA-256 計算 / symlink=`link:`+target SHA-256 / submodule=`subm:`+commit_id / unstaged-deleted=`tombstone:`+last known content SHA-256)) / 4. `path` / `old_path` を NFC 正規化した UTF-8 byte sequence で path-wise sort し、canonical JSON 配列化して SHA-256 を算出 / 5. **これにより**: 同一内容で staging 状態のみ変化 (例: `git add` 済 vs 未 add) でも hash が変わる、rename 元/先が分離される / **runtime artifact 除外**: `.helix/handover/**` / `*.db-wal` / `*.db-shm` / `.helix/audit/runs/**` / 一時ファイル (`*~` `*.swp` `.DS_Store` `__pycache__`)。lock は $HOME 配下 (`~/.helix/auto-restart/locks/`) のため project-local snapshot 対象外 (TL レビュー v24P1#2 反映、旧 `.helix/auto-restart.lock` は廃止)。**unreadable file** (permission denied) は `unreadable:`+path で fail-closed (snapshot 生成自体を拒否)。`git stash create` は **使わない** (untracked カバー不能のため)。**G1.5(B) と L3 D-HOOK-SPEC に rename / symlink / submodule / untracked nested / tab/newline fixture を必須化** |
| HMAC アルゴリズム | HMAC-SHA256 |
| **HMAC 防御範囲** | 外部攻撃者 + 別 OS ユーザー (workspace 内 Bash 攻撃者は脅威モデル外と明示) |
| replay 防止 | nonce + auto_restart_log で重複検出、expires_at 超過は拒否 / **auto_restart_log の trust boundary**: 既定は `~/.helix/auto-restart/log.db`（`~/.helix/auto-restart/` mode <=0700、file mode <=0600、owner=current user、symlink 禁止）で保存。起動時に owner/mode/symlink を再検証し、逸脱時は **fail-closed**。project-local 運用時は `.helix/helix.db` 全体への mode 制約は課さず、`.helix/auto-restart/log.db`（dir mode 0700、DB 0600、symlink 禁止）へ分離保存 |
- **fresh checkout テスト要件**: project-local オプション採用時は、G1.5(D) / L8 の受入テストとして fresh checkout における `~/.helix/auto-restart/log.db` の owner/mode/symlink 期待値を追加（`owner=current user`, `dir <=0700`, `file <=0600`, no symlink）
| コマンド実行 | **shell 文字列ではなく argv 配列** (`subprocess.run(args, shell=False)`) |
| workspace 検証 (TL レビュー v19P1#1 反映: manifest hash) | 起動時に `cwd` / `branch` / `head_sha` / **`worktree_snapshot_hash`** / **`handover_manifest_hash`** / **`phase_yaml_hash`** が記録と一致すること。**いずれか不一致時は fail-closed** + 人間確認プロンプト (内容差分があれば人間が再判断、自動 resume は禁止)。runtime artifact (handover/lock/WAL/SHM/audit-runs) は worktree snapshot から除外済みだが、**handover ファイルは manifest 側で別途検証** されるため改変を検出可能 |
| 署名失敗時 | **fail-closed** (拒否してログ + ユーザー通知) |
| ログ redaction | secret/PII を含む可能性のあるフィールドをログに残さない、redaction 対象一覧を D-DB に明記 / 分離保存を選択しない場合は **L3 D-DB/D-HOOK-SPEC** に上記 trust boundary enforcement（helix.db モード再検証含む）を凍結 |
| kill switch | `helix auto off` で即時停止 (永続フラグ + lock file 維持) |
| 再入ロック (TL レビュー v23P1#2 反映: $HOME 配下に移動) | **`~/.helix/auto-restart/locks/<workspace_hash>.lock`** (PID + 起動時刻記録、workspace_hash は cwd の SHA-256 先頭 16 文字)。project-local の `.helix/auto-restart.lock` は使わない (Tier A の $HOME 限定方針と整合) |
| rate limit | `~/.helix/auto-restart/log.db` の `auto_restart_log` で 1 時間 N 回制限 (永続)。`auto_restart_log` を security-critical state として上記 trust boundary / owner/mode/symlink 再検証前提で運用。 |

- **CLI 追加**:
  - `helix auto on/off/status/rotate-key`
  - `helix auto-restart` (内部用、hook から呼ぶ)
- **hook 追加**:
  - hook event 名は **G1R(B) で確定** (SessionEnd 固定をやめる、Stop adapter の可能性も含める)
  - 成果物: `.claude/hooks/<確定した event 名>.sh`
- **hook 信頼境界検証 (TL レビュー v9P1#3/v10P1#2 反映、D-HOOK-SPEC 必須項目)**:
  - **設定ファイルの分離 (TL レビュー v27P1#1 反映: Claude Code 公式設定パスと HELIX secret を分離)**:
    - **Claude Code 用 hook 登録設定** (Claude Code が読むファイル): 公式対応パスのみ使う:
      - `~/.claude/settings.json` (user-global)
      - `.claude/settings.json` (project shared)
      - `.claude/settings.local.json` (project user-private)
      - これらには **hook 登録 + 許可コマンドリストのみ** を記載 (secret/HMAC 鍵参照/rate limit 等は含めない)
      - G1R(B/D) で「Claude Code が当該設定を読み込むこと」の証跡を必須化
    - **HELIX 専用 secret 設定** (Claude Code は読まない、HELIX CLI のみが読む):
      - **`~/.config/helix/auto-restart.local.yaml` ($HOME 限定、Tier A 検証対象、mode 0600)**
      - 内容: HMAC 鍵参照、許可コマンドテンプレート、rate limit、kill switch 状態 等
      - 公式 settings 経由で漏洩する経路を断つ
    - **project settings** (`.claude/settings.json`): tracked / shared 前提、mode <= 0644 許容、Tier B 検証対象
    - 既存 `.claude/settings.json` migration: 機密情報を含む既存設定を **`~/.config/helix/auto-restart.local.yaml`** に移動 (Claude Code 公式 settings には機密情報を残さない) する手順を D-HOOK-SPEC に明記
  - hook ファイル (`.claude/hooks/*.sh`、TL レビュー v16P2#1 反映: fresh checkout 互換):
    - tracked script は **mode 0644** で OK (Git 標準復元)
    - 起動時、`helix auto on` が **private runtime copy を `~/.helix/auto-restart/runtime/<hash>.sh` (TL レビュー v22P1 反映: $HOME 配下に移動) に mode 0700 で複製** し、絶対パスで実行 (project-local からの移動で snapshot 自己変更による誤 fail-closed を回避、Tier A 検証対象に追加)
    - tracked script の hash と private copy の hash 一致を検証 (改ざん検出)
    - private copy は session 毎に再生成、別 OS ユーザーから読めない (0700 + parent dir 0700)
    - fresh checkout テストを **G3/L6 受入条件に追加**: 新規 clone 後に `helix auto on` → private copy 生成 → 起動が成功することを確認
    - 不一致は fail-closed
  - **user-private settings のみ** mode <= 0600 を強制、project settings は緩和 (group/world writable のみ拒否)
  - config ファイル (`.helix/config.yaml`): tracked OK、mode <= 0644 許容 (機密は **`~/.config/helix/auto-restart.local.yaml`** に分離、TL レビュー v29P1#1 反映: project-local secret 表記を撤廃、$HOME 配下に一本化)
  - lock ファイル (`~/.helix/auto-restart/locks/<workspace_hash>.lock`、TL レビュー v24P1#2 反映: $HOME 配下、project-local の旧パスは廃止): owner = current user、mode <= 0600 確認
  - 実行バイナリ (`helix-codex`, `claude` etc): **絶対パスで起動** (`PATH` lookup 禁止)、起動前に realpath + owner/mode 検証 (mode <= 0755)
  - **path 全 component の信頼境界検証 (TL レビュー v19P1#2 反映: 対象種別で mode 要件分離)**:
    - **Tier A: secret/pending 系 (高信頼必須、TL レビュー v20P1#1 反映: $HOME 配下に限定)**:
      - 対象: HMAC 鍵 (`~/.config/helix/auto-restart.key` ファイル fallback 時)、pending payload ディレクトリ (`~/.helix/auto-restart/pending/`)、手動 restart 表示用ファイル (`~/.helix/restart-pending.txt`)、**HELIX secret 設定 (`~/.config/helix/auto-restart.local.yaml`)** (TL レビュー v27P1#1 反映: Claude Code 公式 settings から分離)、**lock ファイル (`~/.helix/auto-restart/locks/<workspace_hash>.lock`)**、**private runtime copy (`~/.helix/auto-restart/runtime/`)**、親ディレクトリ (`~/.config/helix/`、`~/.helix/auto-restart/`、`~/.helix/auto-restart/locks/`)
      - 検証: realpath 後、以下を確認:
        - **`$HOME` 配下の secret subtree** (例: `$HOME` から対象ファイルまでの component):
          - owner = current user (trusted owner)
          - **親ディレクトリ mode <= 0700** (group/world アクセス禁止)
        - **`$HOME` より上位の ancestor** (例: `/`, `/home`, `/Users`、TL レビュー v20P1#1 反映):
          - owner = root or current user (trusted owner)
          - **group/world writable 禁止** (mode 制約: world writable bit 不可、典型的 0755 は許容)
        - **対象ファイル mode (TL レビュー v23P1#1 反映: artifact 種別で分離)**:
          - **secret/payload/settings (HMAC 鍵 / pending payload / restart-pending.txt / settings.local.json / lock)**: file mode <= 0600
          - **private runtime executable (`~/.helix/auto-restart/runtime/*.sh`)**: file mode 0500 or 0700 (実行可能必須、group/world アクセス禁止)
        - **symlink 不可** (`O_NOFOLLOW` 相当)
        - 作成は atomic (`O_CREAT|O_EXCL|O_NOFOLLOW`)
      - これにより `/`, `/home`, `/Users` 等の root 所有 0755 が原因で常に fail-closed する問題を解消、かつ runtime script が実行可能
    - **Tier B: executable/project 系 (中信頼、TL レビュー v20P2#1 反映: symlink chain 検証)**:
      - 対象: 実行バイナリ (`helix-codex`, `claude` etc、`/usr/bin`, `/usr/local/bin`, `/opt/homebrew/bin` 等のシステム配置)、project settings (`.claude/settings.json`)、tracked hook ファイル (`.claude/hooks/*.sh`)
      - 検証 (realpath 解決後):
        - owner = current user **or root** (trusted owner)
        - **親ディレクトリ mode <= 0755** (世界書き込み禁止だが世界読み取り/実行は許容)
        - 対象ファイル mode <= 0755 (tracked script は 0644 OK、バイナリは 0755 OK)
        - **symlink 許容、ただし chain 検証必須** (TL レビュー v20P2#1 反映: brew/apt の symlink 配置との互換):
          - symlink chain の **各 link** の lstat (mode/owner) を検証 (link 自体は world-writable 不可)
          - **最終 target** の owner/mode を上記基準で検証
          - **解決後の絶対パス** + 任意で content hash を記録 (改ざん検出)
          - 検証中に non-trusted な link が混入したら fail-closed
    - 上記いずれの Tier も **不一致 = unsafe → fail-closed** + ユーザー通知 + auto-restart 抑止
    - **起動時再検証**: `helix auto status` / `helix auto-restart` 起動時に毎回上記検証
    - hook script の実行は **Tier A の private runtime copy 0700** で行う (前述、tracked 0644 を runtime 0700 に複製)
  - **unsafe (改ざん検出 / 権限緩和 / 親ディレクトリ unsafe / symlink 介在) 時は fail-closed** + ユーザー通知 + auto-restart 抑止
  - 上記検証は `helix auto status` 時にも実行可能
- **手動 restart（resume コマンド表示）(TL レビュー v12P3 反映: opaque request id ベース、shell history/process list 露出防止)**:
  - 自動失敗時の動作:
    - **payload (HMAC/expires/snapshot/nonce 等)** は `~/.helix/auto-restart/pending/<request_id>.json` に **0600** で保存
    - **ユーザー向け実行コマンド** は `~/.helix/restart-pending.txt` に **opaque request id のみ** を書き出す: `helix auto-restart --pending <request_id>`
    - これにより shell history / process argv に payload が露出しない
  - **ディレクトリ権限**: `~/.helix/auto-restart/pending/` を `0700` で作成 (別 OS ユーザーから読めない)
  - **ファイル権限**: payload JSON は `0600`、`restart-pending.txt` も `0600` (request id のみだが念のため)
  - **再検証**: `helix auto-restart --pending <id>` 実行時に payload を 0600 ファイルから読み、HMAC / expires_at / snapshot hash / nonce を **再検証** (replay 防止 + replay 検出時 fail-closed)
  - **期限**: payload に `expires_at` を記載、期限切れ payload は起動時に自動削除 + 警告
  - **nonce 検証**: 古い pending payload は nonce 重複として無効化 (HOME DB `auto_restart_log` と照合)
  - **redaction**: ログ出力時は request_id 末尾 4 文字以外と payload 全体を redaction
  - **古い pending 無効化**: `helix auto status` 実行時に期限切れ・nonce 不一致を検出して自動削除
  - 仕様凍結場所: D-HOOK-SPEC + DEP-shared (権限・redaction)、HOME DB (`~/.helix/auto-restart/log.db auto_restart_log`)。`auto_restart_log` は `id INTEGER PRIMARY KEY, task_id TEXT, nonce TEXT, occurred_at TEXT, event_type TEXT` を想定し、`UNIQUE(task_id, nonce)` を必須化。検証→挿入は 1 transaction 内の atomic insert-or-reject、retention は 90 日（VACUUM を定期実行）

### C: Reverse 自動「推奨」(発火ではない)

- **方針**: `helix reverse detect` は **実行ではなく推奨と前提不足の提示のみ**
- **推奨トリガー**:
  | トリガー | 動作 (推奨のみ) |
  |---------|------|
  | `helix init` 時に既存コードあり | 「Reverse モード推奨。`helix reverse r0` から開始してください」 |
  | `helix size --uncertain` + 既存実装あり | R0 提案メッセージ |
  | 死蔵資産検出 (取り組み A 連動) | A の出力に「Reverse R0 から開始することを検討」と注記 |
  | 契約ドリフト連続失敗 | 「R0 から開始 (RG0 通過必要) → R1 で契約再抽出推奨」 |
  | ゲート fail-close で「設計書なし」原因 | 「R0 から開始 (RG0/RG1 通過必要) → R2 As-Is 推奨」 |
- **routing**: 未通過ゲート (RG0/RG1/RG2) があれば必ず R0 から開始させる、直接 R1/R2 推奨はしない
- **CLI 追加**:
  - `helix reverse detect` — 推奨判定 + 前提ゲート確認 + 推奨開始ステップ表示
  - `helix reverse status --detect-orphans` — 棚卸しと連動

### D: コンテキスト管理警告層 (PoC 必須、TL レビュー P2#3 反映)

**Phase 構造追加**:

```
G1R(D): 事前調査 (D 専用)
  ↓ Claude Code usage API の有無・形式
  ↓ PreToolUse / PostToolUse の各 matcher 名 (Read/Bash/Edit/Write/Search 系/Glob/Grep など)
  ↓ payload 形式 (token usage 取得可否)
  ↓ 既存 `.claude/settings.json` との merge 方針
  ↓ tiktoken 依存の license 確認 + stdlib fallback 設計
  ↓ fail-open 時の観測ログ仕様

G1.5(D): 最小 PoC + 結合 PoC (TL レビュー v8P1#3 反映: 5% 結合検証を前倒し)
  ↓ 各 matcher で残量計算が動くか検証
  ↓ 重複 dump 抑止が動くか検証
  ↓ 30%/15% で警告表示できるか確認
  ↓ pass 条件 (D 用): Read / Bash / Edit / Write / Glob / Grep 各 matcher で警告発火確認
  ↓ **5% 結合 PoC (TL レビュー v28P1#1 反映: 入力契約凍結)**:
  ↓   ・B approved 分岐: 5% で `helix handover dump` 自動実行 → 再入抑止 → auto-restart 起動 → resume の連携確認 (B 連携あり)
  ↓   ・B separated 分岐: 5% で `helix handover dump` **自動実行** (D-owned) → **手動再開コマンドテキスト表示のみ** (auto-restart 起動 / restart-pending.txt 生成は waive、D 単独完結)
  ↓   ※ B approved/separated 両分岐とも `helix handover dump` 自体は **D が自動実行** する点を統一、差分は auto-restart 連携の有無のみ
  ↓   **5% 自動 dump 入力契約 (D-HOOK-SPEC 必須項目、TL レビュー v28P1#1 反映)**:
  ↓     - **CURRENT schema v2 契約（入力/出力を分離）**:
  ↓       - **legacy input**: v1 のトップレベル構造を維持し、`schema_version` は欠落または `1` を許容（欠落時も v1 扱い）。
  ↓       - **normalized output**: `schema_version` を `2` で必須化、top-level 構造は移動なし（lossless 継続）。`current_schema_version` は不採用。
  ↓       - `helix handover resume` / `status` / `update` は CURRENT.json のみを読み、legacy input は読み込み時に normalized output（`schema_version=2`）へ ad-hoc 変換して保存。
  ↓       - `task.title`, `task.next_action`, `tests` は `CURRENT-redacted-preview.md` へ分離（運用可能時）。CURRENT.json には resume/status/update 用の最小 redacted 機械情報のみ保持。
  ↓     - **migration/backward compatibility fixture（G1.5(D) 必須）**:
  ↓       - **legacy-input/**:
  ↓         - `schema_version` 欠落の CURRENT.json
  ↓         - `schema_version: 1` の CURRENT.json
  ↓         - 自由テキスト混在（`task.title` / `task.next_action` / `task.tests`）の CURRENT.json
  ↓       - **normalized-output/**:
  ↓         - `schema_version: 2` の CURRENT.json（preview 分離あり/なし）
  ↓       - **互換テスト**: legacy-input → normalized-output へ変換 → resume / status / update が同一動作すること
  ↓ ※ G1.5(D) はもはや「最小 PoC」だけでなく「結合 PoC」を含む
```

**閾値仕様 (統一) + B 分離マトリクス (TL レビュー v7P1#4 反映)**:

| 閾値 | B approved | B separated (PLAN-003 へ分離時) |
|-----|-----------|-------------------------------|
| 30% | 緩警告 (情報のみ) | 同左 |
| 15% | handover dump 推奨 (PreToolUse hook で表示) | 同左 |
| 5% | **自動 dump + auto-restart 起動 (G1.5(D) 結合 PoC で検証済み)** | **D-owned: 自動 dump (`helix handover dump` 自動実行) + 手動再開コマンドテキスト表示**(B 由来の `~/.helix/restart-pending.txt` 生成と auto-restart 連携は **waive**、TL レビュー v27P1#3 反映: dump 自体は D が自動実行)、auto-restart 連携は waive |

- **G-2 受入条件 (L1 で固定、TL レビュー v26P1#2 反映: conditional pass 撤廃):**
  - B approved 時: 30%/15%/5% 全段階発火 + 5% で自動 dump + auto-restart 連携が動作
  - **B separated 時 (L1/G1 再ベースライン後の新受入条件)**: 30%/15% 警告 + 5% で **D-owned 自動 dump (`helix handover dump` 実行) + 手動再開コマンドテキスト表示** が動作 (auto-restart 連携 + restart-pending.txt 生成は **PLAN-003 deferred** として scope 外、再ベースライン後の新 G-2 として pass、conditional pass という第3経路は撤廃、dump は B approved/separated 両分岐で同じく D が自動実行)
  - いずれも Read/Bash/Edit/Write/Glob/Grep 全 matcher でテスト通過必須

**hook matcher 仕様 (Search 系を正式スコープ化、TL レビュー P3#5 反映)**:

| matcher | 動作 | テスト対象 |
|---------|------|------|
| Read | 残量計算 + 閾値判定 | ✅ |
| Bash | 残量計算 + 閾値判定 | ✅ |
| Edit | 残量計算 + 閾値判定 | ✅ |
| Write | 残量計算 + 閾値判定 | ✅ |
| Search 系 (Glob/Grep) | 残量計算 + 閾値判定 | ✅ (G-2 受入条件に追加) |
| 非 tool 時 (長応答中) | hook では捕捉不能、限界として明記 | (対象外) |

## dump 抑止と token 計算の凍結値 (G1R(D) / D-HOOK-SPEC 必須)

- dump cooldown 既定: `auto_restart.dump_cooldown_seconds = 300`（5 分）  
  - override 可: 60〜1800
  - 同一 `task_id` について直近 window 内の再 dump はスキップ（`helix.db context_warnings` で判定）
- token sampling window 既定: `auto_restart.token_sampling_window = 20`  
  - override 可: 5〜100
- 境界値テスト: cooldown しきい値前後（`300` / `301`）と window 5/20/100 の 3 点で残量誤差を検証

- 重複 dump 抑止: `auto_restart.dump_cooldown_seconds` 内は dump 発火を抑止 (helix.db `context_warnings` テーブルで管理)
- テスト: 各 matcher で発火確認 + 重複抑止確認 + 残量取得失敗時の fail-open 確認 + boundary value 回帰

**計測ソース + tiktoken 依存方針 + 入力契約 (TL レビュー v9P2 反映)**:

| ソース | 信頼度 | 必須入力 | 取得元 | model context limit 決定 | 取得不能時 | **G-2 acceptance** |
|--------|--------|---------|--------|------------------------|----------|------------------|
| 1. Claude Code 公開 usage API | high | usage API レスポンス (input_tokens / output_tokens / total_tokens / model name) | hook payload or 環境変数 | API レスポンス内 model name → 静的マッピング (`models.yaml` で管理) | fallback to 2 | **G-2 達成経路 (full pass)** |
| 2. tiktoken (Claude 適合性 **要検証**、TL レビュー v10P2#2 反映) | low-medium | 直近 `auto_restart.token_sampling_window` メッセージのテキスト + model name + **Claude 用補正係数** | hook payload (transcript) + `.helix/config.yaml` の model 設定 + `models.yaml` の補正係数 | 静的マッピング (`models.yaml`) | fallback to 3 | **誤差率 ≤ 10% を確認できた場合のみ G-2 達成経路、それ以外は advisory のみ** |
| 3. **stdlib fallback** (heuristic) | low | 直近 `auto_restart.token_sampling_window` メッセージのテキスト + 既定 context limit (`.helix/config.yaml` の `default_context_limit`) | hook payload (transcript) | `.helix/config.yaml` 既定値 (デフォルト 200000) | fail-open (警告できなかった旨ログ + 処理続行) | **advisory 専用、G-2 達成経路ではない** (TL レビュー v25P1#2 反映: stdlib のみで動作する状況は G-2 fail と等価、L1/G1 再ベースラインで別ゴール化のみ許容) |

- **stdlib fallback**: メッセージ文字数 / 4 をトークン推定 (簡易 heuristic、信頼度 low の警告と共に表示)
- **入力契約凍結場所**: G1R(D) 成果物 (`docs/research/D-feasibility.md`) で各層の必須入力フィールド + 取得元 + payload 形式を確定、L2 D-HOOK-SPEC で正式仕様化
- **kill 判定 (TL レビュー v26P2#1 反映: stdlib advisory と整合)**: **usage API でも誤差検証済み tokenizer (誤差率 ≤ 10%) でも残量計算不能** なら G1.5(D) Kill Criteria に該当 → D 分離 (PLAN-005)。stdlib のみで動作する状況は G-2 達成経路ではない (advisory-only) ため、stdlib 動作は kill 回避の根拠にならない
- **tiktoken の Claude 適合性検証 (TL レビュー v22P2#3 反映: 外部 API 利用条件)**:
  - tiktoken は OpenAI 系 tokenizer のため、Claude の context usage と一致する保証なし
  - G1R(D) で **provider/model 別 tokenizer 適合性 + 許容誤差** を検証する条件を追加
  - **検証時の外部 API 利用ポリシー (新、TL レビュー v22P2#3 反映)**:
    - **既定では外部 Claude API は使わない** (hook payload + ローカル fixture のみで advisory 検証)
    - 外部 Claude API を使う場合は **以下すべて必須**:
      - **PM 承認** (`docs/research/D-feasibility.md` に「外部 API 利用承認: PM 署名 + 日付 + 理由」を記載)
      - **credential 保管**: 環境変数 or `~/.config/helix/anthropic-api-key` (mode 0600、Tier A 検証対象)
      - **非 PII fixture**: 検証用サンプルは public/synthetic データのみ、実 transcript や個人情報を送信しない
      - **費用上限**: G1R(D) 全体で $5 上限、超過時は abort (helix.db `dep_review_log` で記録)
      - **ログ redaction**: API レスポンスからトークン数のみ抽出、本文は記録しない
    - 承認なしの場合は hook payload / ローカル fixture の advisory 検証のみ (誤差検証は省略、tiktoken は advisory-only として扱う)
  - 検証手順 (外部 API 利用時): 既知の長文サンプル N 種を Claude 公開 API と tiktoken 推定で比較、誤差率を測定
  - acceptance への使用可否 (TL レビュー v24P2#1 反映: G-2 と整合):
    - 誤差率 ≤ 10%: tiktoken を G-2 acceptance 判定に使用可 (G-2 full pass の経路)
    - 誤差率 10-30%: **モデル別補正係数** (`models.yaml` で管理) を tiktoken 結果に乗じ、**別 fixture で再測定して誤差率 ≤ 10% を再検証できた場合のみ G-2 full pass に使用可**。再検証で 10% 以下を確認できなければ advisory 専用 (acceptance 判定には使わない)
    - 誤差率 > 30%: tiktoken を **advisory 専用** に降格 (acceptance 判定には使わず、stdlib fallback と同等扱い)
  - usage API 不在時は **誤差検証済み tokenizer（誤差率 ≤ 10%）** が必須。tokenizer も成立しない（誤差率 > 10% または誤差検証不能）場合は **D separated（PLAN-005 分離）**。stdlib/advisory は L1/G1 再ベースライン済みの別ゴールのみ許容する。
- **tiktoken 導入条件**: DEP-shared に license 確認 (MIT)、導入手順 (`pip install tiktoken`)、未導入時挙動 (stdlib fallback で代替)
- **失敗時挙動 (TL レビュー v28P2 反映: 障害分類で fail-open と G-2 fail を分離)**:
  - **capability absence (恒久的)**: usage API 不在 + tokenizer 誤差検証不能 + stdlib のみ可能、の状況は **G1.5 fail / D PLAN-005 分離** (G-2 達成不可、L1/G1 再ベースラインで別ゴール化のみ)
  - **transient runtime error (一時的)**: hook 実行中の I/O エラー / SQLite busy / 計算タイムアウト等は **fail-open** (tool 実行は継続、degraded event を `context_warnings` テーブルに記録、警告できなかった旨ログ)
  - **受入扱い**: G-2 full pass 条件 (fixture テスト) と fail-open 動作確認 (安全挙動確認 fixture) は **L8 受入チェックリストで別項目** とする (fail-open は安全挙動として pass、G-2 達成は別項目で判定)
- **CLI 追加**: `helix context status`
- **hook 追加**: `.claude/hooks/<確定した PreToolUse hook>.sh`

### スコープ外

- helix.db スキーマの大規模再設計 (今回は **追加テーブルのみ** = `audit_decisions` / `context_warnings` / `dep_review_log`、L3 D-DB で詳細仕様凍結)
- VSCode 拡張側の UX (CLI モード前提)
- Codex CLI 自体の改修 (helix 側でラップする)
- **A の quarantine/remove の実行** (PLAN-004 として分離)

## L3 DEP-shared 必須項目 (TL レビュー P2#4 反映: keyring 依存追加)

L3 で凍結すべき新規依存ライブラリの仕様。tiktoken / keyring / gitleaks を統合管理 (TL レビュー v12P1#2 反映: gitleaks 追加):

| 項目 | tiktoken | keyring | gitleaks (新) |
|------|---------|---------|---------------|
| 用途 | コンテキスト残量計算 (取り組み D) | 自動再起動 HMAC 鍵保管 (取り組み B) | A0 audit ログの secret scan |
| license | MIT (要確認) | MIT (要確認) | MIT (要確認) |
| 対応 OS | クロスプラットフォーム (Python 純粋計算) | Linux (gnome-keyring/KWallet) / macOS (Keychain) / Windows (wincred) | Linux/macOS/Windows (Go バイナリ単独配布) |
| backend | (依存なし) | OS ごとに異なる、auto-detect | (依存なし) |
| インストール | `pip install tiktoken` | `pip install keyring` | バイナリダウンロード (`brew install gitleaks` / `apt install gitleaks` / GitHub release) |
| 未導入時 fallback | **stdlib heuristic** (文字数 / 4 でトークン推定、信頼度 low) | **ファイル fallback** (`~/.config/helix/auto-restart.key` mode 0600、workspace 内攻撃者には防御不可と明示) | **fallback なし、A0 を fail-closed (Phase 0 prerequisite)** |
| version | (任意) | (任意) | **>= 8.18 必須** (新しい detect API 利用) |
| check コマンド | `python -c 'import tiktoken'` | `python -c 'import keyring'` | `gitleaks version` |
| 未導入時メッセージ | warn + advisory モード | warn + ファイル fallback | **fail: "gitleaks (>= 8.18) を導入してください: <install URL>"** |
| 代替不可条件 | tiktoken は advisory のみで動作可、未導入なら stdlib | keyring 未導入はファイルで動作可 | **代替不可: secret scan を別ツールで代替する場合は本 PLAN スコープ外** |
| 人間承認者 | PM (= ユーザー本人) | PM (= ユーザー本人) | **PM (= ユーザー本人)** |
| テストマトリクス | tiktoken あり / なし の 2 ケース | keyring あり (各 OS) / なし の N ケース | gitleaks あり (>= 8.18) / なし (fail-closed 確認) の 2 ケース |
| packaging 影響 | 既存 helix 配布物に追加 | 既存 helix 配布物に追加、OS keyring backend は OS 標準依存 | helix 同梱せず、ユーザー手動インストール (Phase 0 prerequisite) |
| **Phase 0 prerequisite (新、TL レビュー v13P1#1 反映)** | (不要、L4 で導入) | (不要、L4 で導入) | **必須**: A0 開始前に **Phase 0 preflight 承認証跡** が要る (`docs/plans/PLAN-002-phase0-preflight.md` に license=MIT 確認 + version >= 8.18 確認 + install source 確認 + PM 署名)。**承認証跡なしでは A0 開始不可** (HELIX エスカレーション境界遵守、L3 DEP-shared での再承認は L4 製品実装時の最終承認として位置付ける) |

**L3 凍結条件 (TL レビュー v7P2 反映: 人間承認者 + G3 停止条件追加)**:
- license 確認完了 (両ライブラリとも MIT 想定だが実物確認必須)
- 対応 OS / backend テストマトリクス完了
- 未導入時 fallback 動作確認
- packaging への影響評価
- インストール手順がドキュメント化
- **人間承認者 (新)**: license / packaging 影響の最終承認は **PM (= Opus 介在の上でユーザー本人)** が行う
- **承認証跡 (TL レビュー v14P1#2 反映: gitleaks 追加)**: `docs/design/DEP-shared.md` 末尾に「approved-by: <ユーザー名>, date: <YYYY-MM-DD>, license-verified: **tiktoken=MIT, keyring=MIT, gitleaks=MIT**, phase0-preflight-ref: docs/plans/PLAN-002-phase0-preflight.md」記載 (gitleaks は Phase 0 preflight 承認との二重承認、L3 で再確認)
- **G3 停止条件 (TL レビュー v29P1#2 反映: stdlib-only での G3 通過を不可化、G-2 達成と整合)**:
  - **承認証跡 (DEP-shared 末尾の approved-by 行) なし → G3 fail-closed**
  - **stdlib-only fallback (tiktoken 不在) で G3 通過可能なケース** (限定):
    - **(a) usage API で G-2 full pass 済み**: その場合 stdlib は **非必須依存** として fallback 継続 (G-2 達成は usage API 経由)
    - **(b) L1/G1 再ベースライン済みで「advisory warning goal」として scope 再定義**: 別ゴール扱いで G3 通過可
  - **上記 (a)(b) のどちらにも該当しない場合 (= usage API なし + tokenizer 誤差検証不能 + 再ベースラインなし)**: **G3 前に D を separated として PLAN-005 へ分離**、本 PLAN は A/B/C のみで継続 (G-2 達成は不可、stdlib-only での G3 通過は禁止)
  - keyring fallback (ファイル fallback) は workspace 内攻撃者非対象モデルとして明記済み、PM 承認 + Phase 0 preflight で許容

## L3 D-DB 必須項目 (TL レビュー P1#2 反映: rollback 方針確定)

L3 で凍結すべき DB 設計の必須項目:

| 項目 | 内容 |
|------|------|
| schema_version | **次番号予約 (現 v7 → v8)**、衝突回避のため PLAN レベルで番号確保 |
| 追加テーブル DDL | `audit_decisions` / `context_warnings` / **`dep_review_log`** (TL レビュー v25P2#1 反映: 外部 API 利用時の費用上限・PM 承認・呼び出し履歴を記録) の完全 DDL |
| index | 検索パターンに基づく index 設計 (created_at, task_id, etc.) |
| retention | 各テーブルの保持期間 (例: `~/.helix/auto-restart/log.db auto_restart_log` = 90 日、`audit_decisions` = 永続、`context_warnings` = 30 日、**`dep_review_log` = 永続** TL レビュー v25P2#1 反映) |
| redaction | secret/PII を含むカラムを明示、redaction 対象一覧 |
| forward migration | v7 → v8 migration script + 既存データ互換テスト |
| **rollback 方針 (改訂)** | **既存 D-DB-MIGRATION 方針 (downgrade 非対応・非破壊変更原則) に準拠**。「rollback = backup restore」と再定義し、downgrade script は作らない |
| migration tests | empty DB / current v7 DB / old DB (v6 等) の各ケースで forward migration 動作確認 |
| backup/restore | migration 前の自動 backup (`.helix/helix.db.backup-v7-<timestamp>`)、failure 時の restore 手順 |
| 並行書き込み | hook 並行書き込み時の WAL/lock 方針 (SQLite WAL mode、busy_timeout) |
| 並行書き込みテスト | 複数 hook 同時発火時の整合性テスト |
| **replay 防止 / 原子性 (新、TL レビュー v7P1#5 反映)** | `~/.helix/auto-restart/log.db` の `auto_restart_log` テーブルに **`UNIQUE(task_id, nonce)`** 制約を必須化。検証→挿入は 1 つの transaction 内で **atomic insert-or-reject** (`INSERT ... ON CONFLICT DO NOTHING` + 影響行数チェック)、conflict 時は replay として fail-closed |
| **rate limit 既定値 (新、TL レビュー v8P1#2 反映: SQLite 互換)** | 1 時間に **6 回** (10 分に 1 回相当) を既定、`.helix/config.yaml` の `auto_restart.rate_limit.per_hour` で上書き可能。`created_at` カラム型は **UTC epoch integer** (秒単位) として固定。cutoff 算出は **アプリ側で計算** (`cutoff = int(time.time()) - 3600`) してパラメータバインドで `WHERE created_at >= ?` を実行。SQLite ネイティブ書式 `datetime('now','-1 hour')` は使わない (タイムゾーン依存性回避)。UNIQUE(task_id, nonce) 制約で重複除外 |
| **並行 hook テスト (新)** | 同時 N=10 hook 発火で replay 拒否 + rate limit 動作 + 二重起動なしを検証 (pytest fixture で sqlite 並行アクセス再現) |

**rollback 方針再定義 (TL レビュー P1#2 反映)**:
- 既存方針との整合: 非破壊変更・追加のみ・downgrade 非対応
- 「rollback」は「backup restore」と同義。migration 前の DB を `.helix/helix.db.backup-v7-<timestamp>` に保存し、問題発生時はファイル replace で復旧
- v8→v7 downgrade script は作らない (D-DB-MIGRATION 方針との衝突回避)
- 不可逆カラム・データ損失条件は無し (追加のみのため)

## フェーズ計画 (改訂版、TL レビュー P1#1/P2#2 反映: 正式ゲート順序 + G1R 先行例外明記)

### G1R/G1.5 順序の例外宣言 (TL レビュー P2#2 反映)

HELIX 正本フロー (SKILL_MAP / gate-policy) では **G1.5 → G1R** の順序が標準。本 PLAN-002 では **G1R → G1.5** の順を採用する (PLAN 固有の例外):

- **理由**: B/D は技術前提 (Claude Code hook event 名・usage API・matcher・keyring backend) が未検証で、PoC 設計自体が前提検証なしには成立しない
- **正本フローへの影響**: 本 PLAN 限定の例外。SKILL_MAP / gate-policy の更新は **本 PLAN の成果物に含めない** (将来の別 PLAN で扱う)
- **gate 運用** (TL レビュー v17P1#1 反映: 現行 phase.schema 互換):
  - **CLI への waiver 機能追加 + phase.schema 変更は本 PLAN では行わない** (HELIX 設計→実装順序を維持)
  - 代わりに **手動 waiver 証跡 (外部ファイル完結)** で運用:
    - `.helix/gate-waivers/PLAN-002-G1R-first.md` に PM (= ユーザー) + TL (Codex 5.4) 双方の署名付き waiver を作成
    - waiver 内容: 例外理由 (技術前提が未検証で PoC 設計が成立しない) + 影響範囲 (本 PLAN-002 のみ) + 期限 (PLAN 完了まで) + 対象ゲート (G1R, G1.5)
    - **phase.yaml は既存 enum のみ使用、note は書かない** (TL レビュー v19P2#2 反映: 実行・通過なら passed、未実施・waive なら skipped):
      - **G1R を正式実施して通過した場合**: `gates.G1R.status: passed` + `gates.G1R.date: <YYYY-MM-DD>` (実行された事実を機械判定可能に)
      - **未実施で waive する場合のみ**: `gates.G1R.status: skipped` を使う
      - 本 PLAN では **G1R は正式実施するため `passed` を使う** (順序例外は外部 waiver ファイルで証跡)
      - **note フィールドは書かない** (現行 phase.schema gateState は status/date のみ許容、additionalProperties=false で検証 fail するため)
    - **waiver の意味の再定義 (TL レビュー v19P2#2 反映)**: waiver は「**G1R を G1.5 より先に実施する順序例外**」の証跡 (実施した事実は phase.yaml passed で記録、waiver は順序のみを正当化)
    - **waiver 監査の正本は `.helix/gate-waivers/PLAN-002-G1R-first.md` のみ** (phase.yaml には waiver 詳細を一切書かない、PM が手動 checklist で外部ファイルを確認)
    - phase.schema 変更を入れたい場合は **別 PLAN として切り出す** (本 PLAN スコープ外)
  - **G2/G3 前提チェック (TL レビュー v17P1#1 反映)**:
    - G2/G3 通過前に **`.helix/gate-waivers/PLAN-002-G1R-first.md` の存在 + 期限確認** (PM が手動チェック、checklist 化)
    - waiver_expires が切れていれば G2/G3 fail-closed
    - これにより phase.schema 変更なしに「正当な例外」と「単なる未通過」を区別
  - **Phase 1.4 (待機なし、TL レビュー v20P1#2 反映: phase.yaml は触らない)**: waiver ファイル作成のみ (5 分作業)。**phase.yaml は触らない** (G1R 実施前のため status は pending のまま)。G1R 実施完了後に `gates.G1R.status: passed` を記録する
  - waiver 機能を CLI/schema に組み込みたい場合は **将来の独立 PLAN** として扱う (本 PLAN スコープ外)


```
Phase 0 preflight (TL レビュー v13P1#1/v19P2#1 反映、A0 開始前の必須前提):
  ↓ 1. gitleaks 承認証跡作成: docs/plans/PLAN-002-phase0-preflight.md に license/version/install/PM 署名を記録
  ↓ 2. **`.gitignore` allowlist 更新 (新、TL レビュー v19P2#1 反映)**: A0 が git 管理対象を生成する前に allowlist パッチを適用、`git check-ignore --non-matching` で検証
  ↓ 承認証跡 + allowlist 更新が両方揃わなければ A0 開始不可 (HELIX エスカレーション境界遵守)

Phase 0: A0 Discovery / Inventory (前倒し棚卸し、正式ゲート扱いではない)
  ↓ preflight 承認後: A0: candidate 抽出 (材料収集)
  ↓ orphans.md / refactor-candidates.md / integrity-breaks.md 生成
  ↓ Opus + TL で初期トリアージ (decisions.yaml 起こし、fail-safe 適用)
  ↓ 注: ここでの調査は L1 要件定義のインプット。正式 G1R 証跡ではない

Phase 1: 要件定義 (L1 + G1)
  ↓ L1 要件定義 (G-1〜G-4 受入条件 v7、A1 の scope 凍結、仮説/kill criteria 明示)
  ↓ G1 要件完了

Phase 1.4: 手動 waiver 証跡作成 (TL レビュー v20P1#2 反映: phase.yaml は触らない)
  ↓ .helix/gate-waivers/PLAN-002-G1R-first.md 作成 (PM + TL 署名)
  ↓ waiver 内容: 例外理由 + 影響範囲 + 期限
  ↓ 完了基準: waiver ファイルが存在し PM + TL が署名済み (5 分作業、CLI 変更なし、phase.yaml 編集なし)
  ↓ G1R 実施完了後に `gates.G1R.status: passed` を記録 (Phase 1.5 の最後)

Phase 1.5: 事前調査 + PoC (G1R + G1.5、B + D 並列、A0 のみ依存、TL レビュー v25P2#2 反映: 集約規則明記)
  ↓ B/D 別 PoC 結果の machine-readable 形式: `docs/poc/B-result.json` + `docs/poc/D-result.json` (各 verdict: pass/fail/separated)
  ↓ phase.yaml への単一 status 集約規則:
  ↓   - G1R: `phase.yaml gates.G1R.status` を以下のロジックで決定:
  ↓     - B/D 両方 verdict=pass → **passed**
  ↓     - B/D いずれか fail → **failed**
  ↓     - B/D いずれか separated → **failed**
  ↓   - **separated 判別**: `B-result.json` / `D-result.json` の `verdict`（pass/fail/separated）+ `scope_hash` + `.helix/baseline/PLAN-002-rebaseline-<outcome>.md` の存在で行う。  
  ↓     - outcome は `Bseparated` / `Dseparated` / `both-separated` を使用し、rebaseline 時の `scope_hash` と突合して再実行判定を行う。
  ↓   - **rebaseline 完了時**: 再実行可能性が確定し `gates.G1R/G1.5` の再実行で `passed` 条件を満たせる場合は status 更新。再実行不能なら `failed` 維持。
  ↓   - これにより state-machine/template/helix-gate の CLI 変更は不要、本 PLAN スコープを守る。  
  ↓   - 集約結果は `phase.yaml` の `gates.G1R.status` / `gates.G1.5.status` のみで管理（スキーマ拡張なし）。機械判別は `B-result.json` / `D-result.json` / `scope_hash` を参照。
  ↓   - G1.5: 同上のロジック
  ↓ G1R(B): hook event 実在 / claude --resume 非対話 / Codex 常駐 / keyring backend 調査
  ↓ G1R(D): usage API / matcher 一覧 / payload / settings.json merge / tiktoken+keyring license / **非 tool 区間補完 hook (Stop/Session 系) + 定期チェック方式 (TL レビュー v11P2#2 反映)**
  ↓ G1R(D) 結論を G2/G3/L8 凍結条件に接続 (TL レビュー v12P2#2 反映):
  ↓   ・補完方式 採用: L8 受入条件にテスト項目追加 (Stop/Session hook 発火確認、定期チェック動作確認)
  ↓   ・補完方式 非採用: L8 残余リスク欄に「非 tool 区間カバー外」を **必須記載**
  ↓   ・採用/非採用は G2 (L2 設計凍結) で確定、G3 通過の前提条件
  ↓ 成果物: docs/research/{B,D}-feasibility.md (G1R 正式証跡)
  ↓ G1R 通過判定 (※正本フロー G1.5→G1R の例外として運用、上記宣言参照)
  ↓ G1.5(B): 自動再起動 3/3 連続成功 → B 用統一指標で kill criteria 判定
  ↓ G1.5(D): 全 matcher (Read/Bash/Edit/Write/Glob/Grep) で警告発火確認 → D 用指標で kill criteria 判定
  ↓ G1.5 通過判定

Phase 2: 設計 (L2 + L3)
  ↓ L2 全体設計: A0/A1 状態機械 / B threat model 完全版 / C 推奨 routing / D 閾値+matcher / D-HOOK-SPEC
  ↓ G2 設計凍結 (threat model レビュー条件)
  ↓ L3 詳細設計 + 工程表 (D-DB 完全版含む、rollback = backup restore、DEP-shared 完全版)
  ↓ G3 実装着手 (API/Schema Freeze、schema_version v8 予約、依存ライブラリ凍結)

Phase 3: 実装 (L4、TL レビュー v23P2#3 反映: 分類運用は G3 前完了済み、L4 は A1 CLI / Shared 基盤 / B/C/D 実装 / 統合まで)
  ↓ Sprint 1: A1 **CLI/状態機械実装のみ** (人間判断は G3 前完了済みのため不要、ここでは production code 化のみ)
  ↓ **Sprint 2 (新、TL レビュー v22P2#2 反映): Shared 基盤スプリント** — B/D が共有する基盤を **先行実装**:
  ↓   - hook registry / settings merge ロジック (project-local + user-private の merge)
  ↓   - `.helix/config.yaml` schema 拡張
  ↓   - helix.db migration (v7→v8、**audit_decisions + context_warnings + dep_review_log** 追加、TL レビュー v26P2#2 反映: 3 テーブル全部、並行書き込みテスト + retention/redaction テストも全テーブル対象)
  ↓   - shared utility (信頼境界検証 / canonical hash 計算 / payload 署名検証)
  ↓ Sprint 3-5: B/C/D 並列実装 (Shared 基盤完了後、B/D は G1.5 通過時のみ)
  ↓   - 並列可能なのは **契約凍結済みの独立ファイル** に限定 (L3 工程表で書き込み範囲を明示)
  ↓   - shared 基盤への変更は B/D 個別 sprint で行わない (差戻しルール明記)
  ↓ Sprint 6: 統合テスト + DB migration rehearsal (empty/current/old + backup/restore)
  ↓ G4 実装凍結

★ A1 分類運用 (人間判断含む) の完了タイミング:
  - **L3 と G3 の間で完了する** (TL レビュー v11P1#3 反映)
  - 流れ: A0 candidate 抽出 (Phase 0) → triaged 状態 → L3 期間中に PM + TL で分類運用 → classified or PLAN-004 移管決定
  - **G3 通過条件 (TL レビュー v17P1#2 反映、二者択一に厳格化、PO deferred acceptance は除外)**:
    - (a) **scope 内候補 100% classified**: triaged 残存ゼロ
    - (b) **正式な L1/G1 再ベースライン**: triaged 残存があるなら、scope 縮小 + L1/G1 再凍結 (新 scope は 100% classified)
  - **PO deferred acceptance の扱い**: PO deferred acceptance は **G3 conditional/failed 扱い** (= G3 通過させない)。または「G-3 未達の明示的 deferred」として L4 対象範囲を縮小し L8 受入条件を再定義 (L1/G1 再ベースラインで対処、当該プロセスを経ない PO 受容のみでは G3 通過不可)
  - **triaged 残存を PLAN-004 移管しただけでは G3 通過しない** (L8 で未達を後発見する構造を回避)
  - G3 通過時点で A1 は "完了 + 凍結"、L4 では CLI/状態機械実装のみ (人間判断不要)
  - 分類運用に新 CLI は不要 (一時スクリプト + 手動 decisions.yaml 編集で完結)

★ G3 前必須成果物 (TL レビュー v12P2#1/v13P1#2/v18P2#2 反映: 正本・同期規則も凍結):
  - `docs/design/A1-decisions-schema.yaml` — decisions.yaml の JSON Schema 凍結 (**設計のみ**)
  - `docs/design/A1-validator-spec.md` — validator の振る舞い仕様 (production code ではなく **設計仕様**)
  - `docs/design/A1-state-transition-tests.md` — 分類状態遷移テスト仕様 (candidate → triaged → classified の遷移、L4 実装で網羅すべきテスト)
  - **dry-run import 手順書** (`docs/design/A1-dry-run-procedure.md`) — 一時検証スクリプトでの実行手順を記述
  - **dry-run 一時検証ツール** (`scripts/temp/A1-validate-decisions.py`、TL レビュー v13P1#2 反映: G1.5 一時検証スコープ): scope/テスト/廃棄条件を明記、L4 で `cli/lib/audit/decisions_validator.py` への昇格 or 廃棄、production code として扱わない
  - `decisions-yaml-dry-run-import.log` — 一時検証ツールでの validation + dry-run import 結果 (G3 前の凍結証跡)
  - **`docs/design/A1-source-of-truth.md` (新、TL レビュー v18P2#2 反映)**: decisions.yaml と audit_decisions テーブルの正本・同期規則を凍結
    - **G3 前**: 正本 = `decisions.yaml` (手動編集 + dry-run import で検証)
    - **L4 後**: 正本 = `decisions.yaml` を継続 (DB は cache + 監査ログ用途)、または DB を正本化 (要 ADR)
    - **import 方向**: YAML → DB の一方向 (DB → YAML は禁止)
    - **idempotency key (TL レビュー v25P2#3 反映: scope_hash 包含)**: **`(candidate_id, schema_version, scope_hash)`** の三組を主キーとし、再 import で衝突なし。L1/G1 再ベースラインで scope_hash が変わると新規エントリ扱い (旧エントリは履歴として保持)
    - **schema_version + scope_hash**: decisions.yaml の `metadata.schema_version` と `metadata.scope_hash` を必須化、import 時に DB と照合
    - **再ベースライン時の挙動**: scope_hash 変更を検出したら、新 scope_hash 配下の candidate_id を新規 import、旧 scope_hash 配下のエントリは「historical (read-only)」マークで保持 (履歴喪失なし)
    - **DB/YAML 照合コマンド**: `helix audit verify-sync` で differences を表示、差分時 fail-close
    - **衝突時挙動**: import 中に検出した衝突 (重複 candidate_id / 矛盾する分類値) は **fail-closed** (rollback + ユーザー通知)
  - これにより G3 時点の分類結果が後続実装の状態機械・DB 制約と一致することを保証 (production validator 実装は L4 Sprint 1)

Phase 4: 検証・リリース (L6-L8)
  ↓ G6 RC → マージ → G7 安定性 → L8 受入 (G-1〜G-4 全達成、G-3 は scope 内 100% classified)
```

## 成果物

| Phase | 成果物 |
|-------|-------|
| **Phase 0 preflight (TL レビュー v23 反映)** | `docs/plans/PLAN-002-phase0-preflight.md` (gitleaks license/version/install/PM 署名) + **`.gitignore` パッチ** + **`docs/research/preflight-gitignore-verification.log`** (`git check-ignore --non-matching` 検証結果、`.helix/audit/redaction-denylist.local.yaml` が ignore されることを必須記録) + **`.helix/audit/redaction-denylist.example.yaml`**、**`.helix/audit/redaction-denylist.local.yaml`（gitignore）**、**`.helix/audit/redaction-denylist.hmac.yaml`** の 3 構成 + **`.helix/audit/scripts/test-redaction.sh` (redaction テストケース)** + **`~/.config/helix/audit-redaction.key` 初期生成** (HMAC-SHA256 用、mode 0600、Tier A 管理、TL レビュー v23P2#2 反映) |
| Phase 0 | `.helix/audit/{orphans,refactor-candidates,integrity-breaks}.md` + `decisions.yaml` + `inventory-once.sh` (git 管理) + `inventory-run-<head_sha>-<timestamp>.log` (gitignore) |
| **L1** | `docs/requirements/L1-requirements.md` + Phase 0 preflight 検証ログへの参照 (再検証なら追加 log) |
| **Phase 1.4 (新)** | `.helix/gate-waivers/PLAN-002-G1R-first.md` (PM + TL 署名済み waiver、G1R 先行例外) |
| G1R(B) | `docs/research/B-feasibility.md` (hook event 確定含む) |
| G1R(D) | `docs/research/D-feasibility.md` (usage API / matcher / settings.json merge / tiktoken license) |
| G1.5(B) | `docs/poc/B-auto-restart/` (PoC コード + 3/3 連続成功記録) |
| G1.5(D) | `docs/poc/D-context-warn/` (各 matcher 発火テスト) |
| L1 | `docs/requirements/L1-requirements.md` (4 取り組み統合要件 v4) |
| L2 | `docs/design/L2-design.md` + `docs/design/threat-model.md` (攻撃者モデル明示) + `docs/design/D-HOOK-SPEC.md` |
| L3 | `docs/design/L3-detailed-design.md` + `docs/design/D-DB.md` (schema_version v8 + DDL/index/retention/redaction/forward migration/backup-restore/並行書き込み) + `docs/design/DEP-shared.md` (**tiktoken + keyring + gitleaks 統合**依存方針: license / 対応 OS / backend / 未導入 fallback / インストール / テストマトリクス) + **G3 前 A1 設計成果物 (TL レビュー v14P2#2/v24P2#2 反映)**: `docs/design/A1-decisions-schema.yaml` + `docs/design/A1-validator-spec.md` + `docs/design/A1-state-transition-tests.md` + `docs/design/A1-dry-run-procedure.md` + **`docs/design/A1-source-of-truth.md`** (decisions.yaml と audit_decisions の正本・同期規則 / schema_version + scope_hash / import 方向 / verify-sync コマンド / 衝突時 fail-closed) + `decisions-yaml-dry-run-import.log` |
| L4 | 実装コード + helix.db forward migration script (v7→v8) + backup script |
| L6 | 統合テストレポート + DB migration rehearsal レポート (empty/current/old + backup/restore) + **fresh checkout テスト実行レポート** (TL レビュー v20P2#2 反映: G3 で凍結した検証仕様を実施) + **HOME DB (`~/.helix/auto-restart/log.db` `auto_restart_log`) 検証** (owner/mode/symlink、`UNIQUE(task_id, nonce)`、rate limit、90 日 retention、VACUUM/cleanup 整合性) |
| L8 | 受入レポート + ミニレトロ |

## リスク (改訂版)

| ID | リスク | 影響 | 対策 |
|----|-------|-----|------|
| R-1 | Codex 中継の信頼性 | 自動継続不能 | G1R(B)/G1.5(B) で実証、kill criteria 失敗時は B 分離。手動 restart（resume コマンド表示） |
| R-2 | 自動再起動の無限ループ | リソース食い潰し | rate limit (永続)、kill switch、再入ロック、backoff |
| R-3 | リファクタの破壊範囲 | 既存機能退行 | 本 PLAN は classified までで止める、quarantine/remove は PLAN-004。fail-safe で証跡不足は keep |
| R-4 | Reverse 自動発火の誤判定 | UX 悪化 | 発火しない (推奨のみ)、未通過ゲートあれば必ず R0 から |
| R-5 | コンテキスト残量推定の精度 | 警告無効化 | G1R(D)/G1.5(D) で実証、3 段階フォールバック、信頼度明示、fail-open |
| R-6 | スコープ過大で G2 凍結遅延 | スケジュール延伸 | B/D 分離オプション、A 完了時点で再評価 |
| R-7 | hook 実行による意図しない外部影響 | セキュリティ | workspace opt-in、引数固定、HMAC 署名 (鍵 keyring)、replay 防止、kill switch、監査ログ + redaction、攻撃者モデル明示 |
| R-8 | helix.db migration 失敗 | データ消失 | rehearsal、自動 backup、restore 手順、追加のみ (downgrade なし)、schema_version v8 予約 |
| R-9 | hook event SessionEnd が実在しない | B 設計やり直し | G1R(B) で確定、Stop adapter 可能性も並行検証 |
| R-10 | tiktoken 新規依存追加でライセンス問題 | 法的リスク | DEP-shared で MIT 確認 (TL レビュー v26P2#3 反映: stdlib は advisory 専用)。**G-2 達成には usage API または誤差検証済み tokenizer が必須** (stdlib fallback は advisory のみで G-2 達成経路ではない)。tiktoken 未導入かつ usage API 不可なら L1/G1 再ベースラインで別ゴール化 or D fail |
| R-11 (新) | D の hook matcher が想定と違う名前 | D 機能不全 | G1R(D) で各 matcher 名を確定 |
| R-12 (新) | OS keyring 利用不能環境 | 鍵保管劣化 | ファイル fallback (workspace 内攻撃者には防御不可と明示)、ユーザー通知 |

## 受入条件 (L8 で検証、改訂版)

- [ ] G-1: セッション切れ後の自動継続が **3/3 end-to-end 連続成功** (B が approve 時のみ、B separated 時は L1/G1 再ベースラインで PLAN-003 deferred として pass 条件再定義済みであることを確認)
- [ ] G-2 (TL レビュー v13P3/v15P1#2 反映: outcome matrix 別 + 非 tool 補完 + 計測ソース信頼度別):
  - [ ] **B approved 分岐**: 30%/15%/5% 全段階発火 + 5% 自動 dump + auto-restart 連携が動作 + Read/Bash/Edit/Write/Glob/Grep 全 matcher テスト通過
  - [ ] **B separated 分岐**: 30%/15% 警告 + 5% で **D-owned 自動 dump (`helix handover dump`) + 手動再開コマンドテキスト表示** 証跡 + 全 matcher テスト通過 (auto-restart 連携 + restart-pending.txt は waive)
  - [ ] **計測ソース pass 判定 (TL レビュー v23P2#1 反映: G-2 達成保証 vs advisory deferred を明確分離)**:
    - **G-2 full pass**: 残量計算が usage API または誤差検証済み tokenizer (誤差率 ≤ 10%) で動作 — **これが G-2 達成の唯一の経路**
    - **stdlib-only fallback で動作する場合**: G-2 は **deferred (達成保証外)** として扱う:
      - L1/G1 で「stdlib-only advisory scope」として再ベースラインが必要
      - 再ベースラインなしで stdlib-only に落ちた場合は **G-2 fail** (advisory のみでは G-2 ゴール「閾値を切ると警告/自動 dump が走る」を保証できない)
      - 再ベースライン済みなら scope は「advisory warning goal」として再定義され、別ゴール扱い (G-2 conditional pass という第3経路は撤廃)
  - [ ] **非 tool 区間補完 (G2 で採用確定なら)**: Stop/Session 系 hook 発火確認 + 定期チェック動作確認
  - [ ] **非 tool 区間補完 (G2 で非採用なら)**: L8 受入レポートに「非 tool 区間カバー外」を残余リスクとして必須記載
- [ ] **HOME DB (auto_restart_log) 検証 (TL レビュー P1#2)**:
  - [ ] fresh checkout / `~/.helix/auto-restart/` で `~/.helix/auto-restart/log.db` が `owner=current user`、`dir mode <= 0700`、`file mode <= 0600`、symlink なしを満たす
  - [ ] `log.db` 起動時 symlink 検証（symlink を検知した場合は fail-closed）
  - [ ] `UNIQUE(task_id, nonce)` 制約で duplicate INSERT が `replay` として reject される
  - [ ] 1 時間 N 回の rate limit が `auto_restart_log` の `COUNT` クエリで動作する
  - [ ] 90 日超過レコードが retention/VACUUM で削除される
  - [ ] VACUUM/cleanup 実行時の並行書き込みで一貫性が維持される
- [ ] G-3 (TL レビュー v19P2#3 反映: G3 通過条件と一意化):
  - [ ] **G-3 pass**: L1/G1 で凍結した scope (再ベースライン後の場合は新 scope) 内候補が **100% `classified`** (keep/remove/merge/deprecate) に到達 (triaged 残存ゼロ)。**G3 通過時点で達成済みのため、L8 では検証のみ**
  - [ ] **G-3 fail**: 上記 pass を満たさない場合。本 PLAN は未完了扱い、残件を PLAN-004 へ移管 (残件数・owner・期限・PLAN-004 移管条件を受入レポートに必須記載)
- **G-3 conditional は撤廃** (TL レビュー v19P2#3 反映: G3 通過条件で PO deferred を除外しているため、L8 conditional は通常経路で到達不能)
- **PO 明示受容が必要な場合**: G3 前に L1/G1 再ベースラインで scope 縮小を正式手続きする (新 scope は 100% classified、conditional は不要)
- **L8 での scope 縮小・pass 条件再定義は禁止** (G3 通過条件と整合、line 87 の禁止ルールと一致)
- [ ] G-4: 既存コードリポでの Reverse **自動推奨** が動作 (発火ではない)
- [ ] `helix test` 全 GREEN 維持
- [ ] DB migration rehearsal 完了 (empty/current/old + backup/restore + 並行書き込み)
- [ ] threat model レビュー完了 (攻撃者モデル / 鍵管理 / 署名 / replay / argv / fail-closed / redaction の全項目)
- [ ] hook event 名確定 (G1R(B) 成果物で SessionEnd or Stop adapter のいずれかに確定)
- [ ] D の matcher 確定 (G1R(D) 成果物で Read/Bash/Edit/Write/Search 系の各 matcher 名確定)
- [ ] DEP-shared 完了 (**tiktoken + keyring + gitleaks** license / 対応 OS / backend / 未導入 fallback / テストマトリクス全て確認、TL レビュー v14P1#2 反映)
- [ ] **fresh checkout テスト合否** (TL レビュー v20P2#2 反映): 新規 clone 環境で `helix auto on` → private runtime copy 生成 → auto-restart 起動が成功することを確認、L6 実行レポート + L8 合否チェックを記録
- [ ] **gitleaks Phase 0 preflight 承認証跡** (`docs/plans/PLAN-002-phase0-preflight.md`) が存在し PM 署名済み
- [ ] ミニレトロ完了 (G2/G4/L8 通過時)

## 開発方針

- **委譲ルール準拠**: BE/設計/レビュー/テストは Codex (TL/SE/QA)、PM 判断は Opus
- **破壊的変更 OK だが段階的に**: ユーザー単独利用前提、本 PLAN は **分類確定まで** (削除は PLAN-004)
- **段階的リリース**: A → G1R(B+D)/G1.5(B+D) → B/C/D → 統合 の順
- **Kill criteria 厳守 (B/D 別指標、TL レビュー v7P3 反映)**:
  - **B 用**: G-1 / G1.5(B) / B Kill Criteria は同一指標 (3/3 end-to-end 連続成功)
  - **D 用**: G1.5(D) / D Kill Criteria は別指標 (全 matcher 警告発火 + 重複 dump 抑止 + 残量計算成功)
  - **誤適用禁止**: D に B の 3/3 end-to-end 指標を適用してはならない
- **ドッグフード**: 自分自身の HELIX フレームワーク改良なので、自分のフローで自分を改善する
- **攻撃者モデル明示**: workspace 内 Bash 攻撃者は脅威モデル外 (ローカル単独利用前提)

## Kill Criteria

### B (自動継続) 専用
G1.5(B) PoC で以下のいずれかが満たせない場合、B を本 PLAN から分離し PLAN-003 として別途扱う:
1. **3/3 end-to-end 連続成功できない** (3 回連続失敗)
2. PoC 期間 (1 sprint = 5 営業日) を超過
3. G1R(B) で hook event が実在しない (SessionEnd も Stop adapter も使えない場合)

分離時、本 PLAN は A/C/D のみのスコープで継続。

### D (コンテキスト警告) 専用 (TL レビュー v25P1#1 反映: conditional 降格を完全削除)
G1.5(D) PoC で以下のいずれかが満たせない場合、D を本 PLAN から分離し PLAN-005 として別途扱う:
1. **全 matcher で警告発火が確認できない (Read / Bash / Edit / Write / Glob / Grep のいずれか不能)** — Search 系含む
2. **usage API でも誤差検証済み tokenizer (誤差率 ≤ 10%) でも残量計算不能** (stdlib fallback のみで動作する状況は G-2 達成不可と等価、D fail 扱い)
3. PoC 期間 (1 sprint) を超過
4. **非 tool 区間補完を G2 で採用した場合**:
   - **両方未達** (Stop/Session hook **かつ** 定期チェック が両方失敗) → D fail / PLAN-005 分離
   - **片方のみ未達** → 残余リスクとして L8 受入レポートに「非 tool 区間カバー一部欠落」を必須記載 (G-2 full pass 判定自体には影響しない、conditional 降格はしない、D 全体は本 PLAN 内で完了可能)

分離時、本 PLAN は A/B/C のみのスコープで継続 (D 機能は手動運用)。

## 派生 PLAN

| PLAN ID | 内容 | 発生条件 |
|---------|-----|---------|
| PLAN-003 (将来) | 自動継続パイプライン (B 単独) | G1.5(B) Kill Criteria 該当時 |
| PLAN-004 (将来) | 棚卸し実行編 (quarantine/remove) | 本 PLAN-002 完了後 |
| PLAN-005 (将来) | コンテキスト警告層 (D 単独) | G1.5(D) Kill Criteria 該当時 |

## B/D 分離時 Outcome Matrix (TL レビュー v10P1#1 反映、L1/G1 で凍結、L8 の判定指針)

Kill Criteria 発火時、本 PLAN-002 のスコープが変動する。L1/G1 で以下の 4 outcome matrix を **凍結し、L8 受入条件を再ベースラインする**:

| Outcome | 本 PLAN-002 残存 scope | L1/G1 再通過要否 | L8 受入条件 |
|---------|----------------------|-----------------|-----------|
| **A: B approved + D approved** | A0/A1/B/C/D 全部 | 不要 (初期 scope のまま) | G-1〜G-4 全達成 |
| **B: B separated, D approved** | A0/A1/C/D | **要 L1/G1 再ベースライン** (G-1 を「PLAN-003 へ deferred」として再凍結、G-2 を B separated 分岐に再凍結) | G-2 (B separated 分岐) + G-3 + G-4。G-1 は PLAN-003 deferred を pass 条件に再定義 |
| **C: B approved, D separated** | A0/A1/B/C | **要 L1/G1 再ベースライン** (G-2 を「PLAN-005 へ deferred」として再凍結) | G-1 + G-3 + G-4。G-2 は PLAN-005 deferred を pass 条件に再定義 |
| **D: B separated + D separated** | A0/A1/C のみ | **要 L1/G1 再ベースライン** (G-1/G-2 を deferred、scope を A+C に縮小) | G-3 + G-4 のみ。G-1/G-2 は deferred を pass 条件に再定義 |

**運用ルール**:
- Kill Criteria 発火時、PM (= ユーザー本人) が outcome を確認し、L1/G1 再ベースライン手順を実行
- 再ベースライン手順: 上記 matrix の該当行を `.helix/baseline/PLAN-002-rebaseline-<outcome>.md` に明示的 rebaseline acceptance 証跡として記録 (PM + TL 署名)
- 証跡なしでの L8 判定は禁止 (L8 で pass/fail 判定不能になるため)

## 想定外作業

- 既存修正 `fix/helix-gate-stage-float-comparison` は本 PLAN 着手前に取り込み済み (`9d0c02e`)。

## 改訂履歴

| 版 | 日付 | 内容 |
|---|------|------|
| v1 | 2026-04-28 | 初版 |
| v2 | 2026-04-28 | TL レビュー P1×4/P2×2 反映: G1R/G1.5 追加、A 段階制、threat model 章、D-DB 追加、閾値統一 30/15/5、Reverse 自動発火→推奨化、kill criteria |
| v3 | 2026-04-28 | TL レビュー P1×2/P2×4 反映: 統一指標、threat model 詳細化、SessionEnd→hook event 確定 (G1R)、PreToolUse matcher 拡張 + tiktoken 依存方針、D-DB 必須項目化、A 達成範囲を classified までに固定、分類値に needs-human/unknown 追加、fail-safe |
| v4 | 2026-04-28 | TL レビュー P1×2/P2×2/P3×1 反映: 攻撃者モデル明示 (workspace 内 Bash は対象外)、鍵保管 keyring 優先、D 専用 G1R/G1.5 追加、triaged/classified 分離 (G-3 受入条件改訂)、DB rollback = backup restore 再定義、Search 系 matcher を G-2 受入条件に追加、D Kill Criteria 追加 (PLAN-005) |
| v5 | 2026-04-28 | TL レビュー P1×2/P2×2 反映: Phase 順序修正 (L1/G1 → G1R(B+D) → G1.5(B+D) → L2)、G-3 受入条件一意化 (scope 内 100% classified、triaged 残存は scope 縮小 + PLAN-004 移管)、G1.5(D) pass 条件と D Kill Criteria に Glob/Grep 追加、DEP-shared.md (tiktoken + keyring 統合依存設計) を L3 必須成果物化 |
| v6 | 2026-04-28 | TL レビュー P1×1/P2×2/P3×1 反映: A を A0 (Discovery) / A1 (Classification) に分割し依存粒度明確化 (B/C/D の G1R/G1.5 → A0、L4/L8 → A1)、G1R 先行を PLAN 固有例外として明記 (正本フロー G1.5→G1R との差分)、統一指標を B 専用 (G-1/G1.5(B)/B Kill) に限定し D 用指標を別定義、manual fallback の権限 (0700/0600)・期限 (expires_at)・nonce 検証・redaction・古い pending 無効化を仕様化 |
| v7 | 2026-04-28 | TL レビュー P1×5/P2×1/P3×1 反映: (P1#1) G1R 例外対応を Phase 1.4 として前倒し + waiver 方式 / (P1#2) A0 を「既存ツール + 一時スクリプトでの手動棚卸し」と明記、新規 CLI は L4 Sprint 1 で実装 / (P1#3) L8 での scope 縮小・pass 再定義を禁止し PO 明示受容 or G-3 fail/conditional の 2 択に / (P1#4) G-2 受入条件に B approve / B separated マトリクス追加 / (P1#5) D-DB に UNIQUE(task_id, nonce) + atomic insert-or-reject + rate limit 既定値 6/h + 並行 hook テスト追加 / (P2) DEP-shared に license 人間承認者 (PM = ユーザー本人) + 承認証跡形式 + G3 停止条件追加 / (P3) 開発方針の旧「統一指標」表現を B/D 別指標に修正 |
| v8 | 2026-04-28 | TL レビュー P1×4/P2×1 反映: (P1#1) L8 受入条件 G-3 の line 425 と line 87 の矛盾を解消 (scope 再定義禁止、2 択のみ: G-3 fail/conditional or PO 明示受容) / (P1#2) rate limit SQL を SQLite 互換に変更 (UTC epoch integer + アプリ側 cutoff、`now() - interval` 表記を排除) / (P1#3) 5% 結合 PoC を G1.5(D) に前倒し (B approved/separated 両分岐検証) / (P1#4) Phase 1.4 を手動 waiver 証跡のみに限定 (CLI 変更は本 PLAN スコープ外) / (P2) A0 一時スクリプトを git 管理対象化 + 実行証跡 (head_sha/hash/DB snapshot) 保存要件 |
| v9 | 2026-04-28 | TL レビュー P1×3/P2×1 反映: (P1#1) A1 達成範囲の line 57 を G-3 受入条件と完全一致 (scope 変更は G2/G3 以前限定) / (P1#2) B separated 時の D 独立性確保: D-owned 手動 dump + 手動再開手順テキスト表示で完結、restart-pending.txt 生成は B 専用で waive / (P1#3) D-HOOK-SPEC に hook 信頼境界検証追加 (hook/settings/config/lock/binary の owner/mode 検証 + 絶対パス起動 + unsafe 時 fail-closed) / (P2) context 残量計測の入力契約凍結 (各層の必須入力フィールド + 取得元 + model context limit 決定 + 取得不能時挙動) |
| v10 | 2026-04-28 | TL レビュー P1×2/P2×3 反映: (P1#1) B/D 分離時の 4 outcome matrix を L1/G1 で凍結し L8 受入条件を再ベースライン (B approved/separated × D approved/separated の 4 ケース) / (P1#2) hook 信頼境界を user-private settings (0600) と project settings (0644 緩和) に分離、既存運用との衝突解消 + migration 手順 / (P2#1) A0 audit ログに redaction ルール + 除外パターン + gitignore + 0600 + gitleaks secret scan + 集計結果のみ記録 / (P2#2) tiktoken の Claude 適合性検証を G1R(D) に追加 (誤差率閾値で acceptance 用途を分岐、advisory 専用降格条件) / (P2#3) canonical payload に worktree_hash + handover_dump_hash + phase_yaml_hash を追加し起動時検証で fail-closed |
| v11 | 2026-04-28 | TL レビュー P1×3/P2×2 反映: (P1#1) worktree_hash を content-addressed snapshot (git stash create or 全 blob+untracked content hash) に変更、runtime artifact (handover/lock/WAL/SHM/audit-runs/swp) 除外を D-HOOK-SPEC で凍結 / (P1#2) hook/binary 検証に **path 全 component の信頼境界検証** 追加 (parent dir owner/mode/symlink 不可、atomic create + O_NOFOLLOW 相当) / (P1#3) A1 分類運用を **L3-G3 間で完了**、L4 Sprint 1 は CLI/状態機械実装のみに限定 / (P2#1) A0 redaction にファイル名漏洩防止 (salted hash + 分類カウントのみ) + stream redaction + gitleaks 未導入時 fail-closed / (P2#2) G-2 を「対応 tool event 発火時」と限定明示、非 tool 区間は残余リスクとして L8 受入レポートに必須記載、補完 hook (Stop/Session + 定期チェック) を G1R(D) 調査項目に追加 |
| v12 | 2026-04-28 | TL レビュー P1×2/P2×2/P3×1 反映 ("P0 はなし" 明記): (P1#1) snapshot algorithm を明示化 (`git ls-files --cached --modified --others --exclude-standard` + 除外 + path/mode/SHA-256 lexical sort、`git stash create` は使わない) / (P1#2) gitleaks を DEP-shared と Phase 0 prerequisite に統合 (>= 8.18 必須、未導入時 fail-closed、人間承認者明記) / (P2#1) G-3 表現を「検証済み decisions.yaml による分類確定」に修正、G3 前必須成果物に decisions schema/validator/dry-run import/状態遷移テストを追加 / (P2#2) 非 tool 区間補完 hook を G2 で採用/非採用確定 → L8 にテスト or 残余リスク必須記載で接続 / (P3) manual fallback を opaque request id ベースに変更 (shell history/argv 露出防止)、payload は 0600 ファイル、実行時 HMAC/snapshot/nonce 再検証 |
| v13 | 2026-04-28 | TL レビュー P1×2/P2×2/P3×1 反映 ("P0 なし" 継続): (P1#1) gitleaks 承認証跡を **Phase 0 preflight に前倒し** (`docs/plans/PLAN-002-phase0-preflight.md` で license/version/install/PM 署名)、承認なしでは A0 開始不可 / (P1#2) G3 前必須成果物から **production validator 実装を除外**、schema/spec/状態遷移テスト仕様 + 一時検証ツール (scripts/temp/ にスコープ + 廃棄/昇格条件明記) のみに限定、production code は L4 Sprint 1 / (P2#1) snapshot algorithm に削除/symlink/submodule 正規化追加 (`git status --porcelain=v2 -z`、tombstone/link target/commit id、unreadable は fail-closed) / (P2#2) `.gitignore` allowlist 更新を L1 成果物化 (`.helix/audit/scripts/**` 等を追跡対象、runs/** は除外) / (P3) L8 受入チェックリストを outcome matrix 別 (B approved/separated) + 非 tool 補完 (採用/非採用) で再整理 |
| v14 | 2026-04-28 | TL レビュー P1×2/P2×2 反映: (P1#1) `.gitignore` allowlist に **親ディレクトリの再 include 明示** (`!**/.helix/audit/` 等)、`git check-ignore` 検証ログを L1 成果物化 / (P1#2) gitleaks を **承認証跡 (`license-verified: tiktoken=MIT, keyring=MIT, gitleaks=MIT`) + L3 成果物 (DEP-shared) + L8 受入条件** に明示追加、Phase 0 preflight との二重承認 / (P2#1) snapshot canonical 表現を **index_repr / worktree_repr に分離** (porcelain v2 XY 状態、rename old_path、staged/unstaged deletion を別フィールド canonical 化、staging 状態変更も hash 差分に含める) / (P2#2) 成果物表に Phase 0 preflight + L1 (.gitignore パッチ + 検証ログ) + Phase 1.4 waiver + G3 前 A1 設計成果物を追加し、必須ゲート証跡を網羅 |
| v15 | 2026-04-28 | TL レビュー P1×2/P2×1 反映: (P1#1) snapshot algorithm に **`--untracked-files=all`** 明示 + `git ls-files --others` で untracked nested directory の個別ファイルまで完全展開、内容 hash 取り逃がし防止 / (P1#2) D pass 判定を計測ソース信頼度別に分離: **full pass = usage API or 誤差検証済み tokenizer (≤ 10%)**, **conditional pass = stdlib-only (advisory のみ、L8 残余リスクに必須記載)**、stdlib heuristic だけで G-2 を保証しない / (P2) `.gitignore` allowlist に audit `allowlist.yaml` / `denylist.yaml` を追加 (検出ロジック参照入力の git 管理) |
| v16 | 2026-04-28 | TL レビュー P1×2/P2×2 反映: (P1#1) A1 G3 通過条件を **二者択一 (100% classified or L1/G1 再ベースライン or PO deferred acceptance)** に厳格化、triaged 残存の PLAN-004 移管だけでは G3 通過しない / (P1#2) waiver を **phase.yaml に `passed-with-waiver` ステータスで監査記録**、G2/G3 前提チェックで waiver_expires 切れなら fail-closed、機械的に正当例外と未通過を区別 / (P2#1) tracked hook 権限要件を fresh checkout 互換に修正 (tracked 0644 → `helix auto on` で private runtime copy 0700 生成、絶対パス実行 + hash 検証、fresh checkout テスト G3/L6 追加) / (P2#2) 非 tool 区間補完採用時の D 用指標に Stop/Session hook + 定期チェック PoC 成功条件 + 補完 fail 時の降格ルール (advisory-only conditional pass) を追加 |
| v17 | 2026-04-28 | TL レビュー P1×2/P2×2 反映: (P1#1) waiver 記録を **現行 phase.schema 互換に修正** (`gates.G1R.status: skipped` + 既存 note フィールドへの参照記載のみ、未定義 status `passed-with-waiver` と additionalProperties 違反を解消、waiver 詳細は外部ファイル `.helix/gate-waivers/PLAN-002-G1R-first.md` で完結、phase.schema 変更は本 PLAN スコープ外) / (P1#2) G3 通過条件から **PO deferred acceptance を除外** (二者択一: 100% classified or L1/G1 再ベースライン)、PO deferred acceptance は G3 conditional/blocked 扱い / (P2#1) D Kill Criteria に **非 tool 補完失敗時の分離/降格条件追加** (両方未達=PLAN-005 分離、片方未達=advisory-only conditional 降格) / (P2#2) `git check-ignore` 検証コマンドに **`--non-matching`** 追加、tracked 側も安定記録 + `git status --ignored --short` を補助検証 |
| v18 | 2026-04-28 | TL レビュー **P1×1**/P2×3 反映 (P1 1 件まで減少): (P1) hook 信頼境界検証対象に **HMAC 鍵 + pending payload + restart-pending.txt + 親ディレクトリ** を追加 (~/.config/helix/ + ~/.helix/auto-restart/ も 0700/owner/no-symlink/atomic 検証) / (P2#1) phase.yaml の note 削除を明記、waiver 監査正本を **外部ファイルのみ** に固定 (phase.yaml は status=skipped + date のみ、note は書かない) / (P2#2) decisions.yaml と audit_decisions の **正本・同期規則を G3 前凍結** (`A1-source-of-truth.md` 必須化、import 方向 / idempotency key / schema_version + scope_hash / verify-sync コマンド / 衝突時 fail-closed) / (P2#3) L8 G-3 を **pass / conditional / fail の 3 分岐** に再整理 (PO 明示受容は conditional、pass の代替ではない) |
| v19 | 2026-04-28 | TL レビュー P1×2/P2×3 反映: (P1#1) handover 署名対象を **manifest hash 方式** に拡張 (CURRENT.json 単体ではなく CURRENT.md + 補助ファイルも含む、auto-restart 入力一覧は G1R(B) で確定) / (P1#2) 信頼境界検証の mode 要件を **Tier A (secret/pending: 親 0700/file 0600)** と **Tier B (executable/project: 親 0755/file 0755 許容)** に分離、`/usr/bin` 等のシステム配置との衝突を解消 / (P2#1) `.gitignore` allowlist 更新を **Phase 0 preflight に前倒し** (A0 が git 管理対象を生成する前に適用、`git check-ignore --non-matching` で検証) / (P2#2) G1R phase.yaml status を **`passed`** に修正 (実行・通過の事実を機械判定可能に、`skipped` は未実施 waive 専用、waiver は順序例外証跡のみ) / (P2#3) L8 G-3 から **conditional 分岐を撤廃** (G3 通過条件で PO deferred 除外しているため通常経路到達不能、必要時は G3 前 L1/G1 再ベースラインで対処) |
| v20 | 2026-04-28 | TL レビュー P1×3/P2×3 反映 (前修正で混入した矛盾解消): (P1#1) Tier A path 検証を **`$HOME` 配下 secret subtree のみ 0700 必須**、`$HOME` より上位 ancestor は root/current user owner + group/world writable 禁止で許容 (`/`, `/home` 等の標準 0755 を許容) / (P1#2) Phase 1.4 で **phase.yaml は触らない** (waiver ファイル作成のみ)、G1R 実施完了後に `gates.G1R.status: passed` 一本化、`skipped` 表記の混在を解消 / (P1#3) L8 G-3 受入条件から **古い conditional/PO 受容表現を撤廃**、v19 方針 (G3 通過不可 or G3 前 L1/G1 再ベースラインのみ) に統一 / (P2#1) Tier B の symlink を **chain 検証に変更** (brew/apt の symlink 配置を許容、各 link + 最終 target の owner/mode 検証) / (P2#2) fresh checkout テストを **L6 成果物 + L8 受入条件に明示追加** / (P2#3) A0 redaction の「顧客名らしき」を撤廃し **具体的 regex (メール/IP/AWS key/JWT/Bearer/credit card 様) + denylist + テストケース必須** に決定的仕様化 |
| v21 | 2026-04-28 | TL レビュー P1×2/P2×3 反映 ("P0 なし" 継続): (P1#1) ゴール表 G-3 と A1 scope 表の conditional/PO 受容表現を **完全撤廃**、「triaged 残存=G-3 fail、scope 変更=G3 前 L1/G1 再ベースラインのみ」に統一 / (P1#2) G3 依存承認の fail-close 条件を **一意化** (承認証跡なし=blocked/fail 固定、fallback モードは PM 承認 + gitleaks Phase 0 preflight 済みの両方で初めて G3 通過可) / (P2#1) user-private settings を **`~/.claude/settings.local.json` のみ ($HOME 限定)** に統一、project-local は秘密情報配置先として禁止 / (P2#2) `redaction-denylist.yaml` を `.gitignore` allowlist に追加 (git 管理必須化) / (P2#3) `.gitignore` パッチ + 検証ログ + redaction-denylist 初期セット + redaction テストスクリプトを **Phase 0 preflight 成果物に前倒し**、L1 は参照のみ |
| v22 | 2026-04-28 | TL レビュー **P1×1**/P2×3 反映 (G2 conditional 評価): (P1) private runtime copy を **`~/.helix/auto-restart/runtime/` ($HOME 配下) に移動**、Tier A 検証対象に追加 (project-local 配置による snapshot 自己変更 fail-closed を回避) / (P2#1) snapshot の index_repr/worktree_repr を **Git object format 非依存の content SHA-256** に統一 (`git cat-file blob <oid>` 経由、SHA-1/SHA-256 リポでも同一結果、unmerged/intent-to-add も明示) / (P2#2) L4 に **Shared 基盤スプリント (Sprint 2) を先行追加** (hook registry / settings merge / config schema / DB migration / shared utility)、B/D 並列は契約凍結済み独立ファイル限定、shared 基盤への変更は個別 sprint で行わない / (P2#3) G1R(D) 外部 Claude API 利用条件を **明文化** (既定使わない、使うなら PM 承認 + credential 0600 + 非 PII fixture + 費用上限 $5 + ログ redaction の全必須) |
| v23 | 2026-04-28 | TL レビュー P1×2/P2×3 反映: (P1#1) Tier A の file mode を **artifact 種別で分離** (secret/payload/settings: 0600 / private runtime executable: 0500-0700)、parent dir 0700 は維持、fresh checkout テストに権限期待値固定 / (P1#2) lock ファイルを **`~/.helix/auto-restart/locks/<workspace_hash>.lock` ($HOME 配下) に移動**、Tier A の $HOME 限定方針と整合 / (P2#1) G-2 から conditional pass (advisory-only) を **撤廃**、stdlib-only は L1/G1 再ベースラインで「advisory warning goal」として再定義 (G-2 達成保証経路は usage API or 誤差検証済み tokenizer のみ) / (P2#2) redaction を **HMAC-SHA256 + 専用キー (`~/.config/helix/audit-redaction.key`、Tier A 管理)** に変更、辞書攻撃耐性 + run 間比較可能性、Phase 0 preflight で key 初期生成 / (P2#3) Phase 3 見出しを「分類運用は G3 前完了。L4 は A1 CLI / Shared 基盤 / B/C/D / 統合まで」に修正、Sprint 計画との矛盾解消 |
| v24 | 2026-04-28 | TL レビュー P1×2/P2×2/P3×1 反映 (残存矛盾の最終クリーンアップ): (P1#1) D 用指標から **conditional pass / advisory-only 降格を完全削除**、stdlib-only fallback は G-2 fail と等価 (例外: L1/G1 再ベースラインで別ゴール化のみ)、補完 fail も降格ではなく残余リスクのみに変更 / (P1#2) lock 旧パス `.helix/auto-restart.lock` を全箇所で **新パス `~/.helix/auto-restart/locks/<workspace_hash>.lock` に置換**、runtime artifact 除外リストからも削除 / (P2#1) tokenizer 誤差 10-30% を **「補正後別 fixture で再測定し誤差率 ≤ 10% を確認した場合のみ G-2 full pass」** に明確化、再検証なしは advisory 専用 / (P2#2) `A1-source-of-truth.md` を L3 成果物表に追加 / (P3) gitignore 検証ログを **正本 `preflight-gitignore-verification.log`** に一本化、L1 は参照のみ |
| v25 | 2026-04-28 | TL レビュー P1×2/P2×3 反映 (最終整合): (P1#1) D Kill Criteria の advisory-only 降格を完全削除 (片方未達は残余リスク記載のみ、conditional pass は撤廃)、Kill Criteria #2 を「stdlib のみで動作する状況は D fail」に明示 / (P1#2) 計測ソース表に **G-2 acceptance 列追加**、stdlib を「advisory 専用、G-2 達成経路ではない」と明記、tiktoken も誤差率 ≤ 10% 確認時のみ達成経路 / (P2#1) `dep_review_log` を D-DB 追加テーブルに含める (DDL/retention/redaction/migration 対象)、スコープ外の記載とも整合 / (P2#2) B/D 別 PoC 結果の machine-readable 形式 (B-result.json/D-result.json) と phase.yaml 単一 status 集約ロジックを明記 / (P2#3) audit_decisions の idempotency key を **`(candidate_id, schema_version, scope_hash)` の三組** に変更、再ベースライン時の historical エントリ保持で履歴喪失なし |
| v26 | 2026-04-28 | TL レビュー P1×2/P2×3 反映: (P1#1) phase.yaml 集約規則で **separated 含む場合は blocked**、L1/G1 再ベースライン完了 (rebaseline artifact + 新 scope_hash) まで passed にしない / (P1#2) B separated 時 G-2 受入条件から **conditional pass 表現を削除**、「再ベースライン後の新受入条件として pass」と明記 / (P2#1) D kill 判定を「usage API でも誤差検証済み tokenizer でも残量計算不能なら fail」に修正、stdlib 動作は kill 回避根拠にならない / (P2#2) Sprint 2 migration 対象に **dep_review_log を追加** (4 テーブル全部、並行書き込み + retention/redaction テストも全対象) / (P2#3) R-10 リスク対策を「stdlib は advisory 専用、G-2 達成には usage API or 誤差検証済み tokenizer 必須」に修正、過大評価を解消 |
| v27 | 2026-04-28 | TL レビュー P1×3/P2×2 反映: (P1#1) Claude Code **公式設定パスと HELIX secret を分離** (`~/.claude/settings.local.json` 不存在問題解消、HELIX secret は `~/.config/helix/auto-restart.local.yaml` に分離、公式 settings には hook 登録のみ、G1R で読み込み証跡必須) / (P1#2) `helix audit quarantine` を **PLAN-002 で実装しない** (PLAN-004 で実装、破壊的操作面の早期増加回避、本 PLAN は schema 凍結のみ) / (P1#3) B separated 時の **5% 動作を「D が `helix handover dump` 自動実行 + 手動再開コマンドテキスト表示」で一意化** (B approved/separated 両分岐で dump 自動実行は同じ、差分は auto-restart 連携の有無のみ) / (P2#1) handover manifest hash の **計算順序とロック境界を凍結** (handover dump → manifest 確定 → hash 算出 → 署名 → handover lock 解放 → auto-restart lock → 起動) / (P2#2) 非 tool 補完を G-2 達成条件から **完全分離**、4 ケース判定表 (採用/非採用 × 両方/片方/両 fail) で pass 必須項目と残余リスク項目を明確化 |
| v28 | 2026-04-28 | TL レビュー P1×2/P2×1 反映 ("P0 なし" continuing): (P1#1) D の 5% 自動 dump **入力契約を凍結** (入力ソース / 必須フィールド task_id+files / 任意フィールド / 既存 update vs 新規 / fail-closed / redaction / G1.5(D) fixture) / (P1#2) separated 時 phase.yaml status を **`failed` に寄せる** (`blocked` は phase.schema 未対応のため使わない、解除は G1R/G1.5 再実行経路、CLI/state-machine 変更不要で本 PLAN スコープ維持) / (P2) D の fail-open と G-2 fail を **障害分類で明確分離** (capability absence = G1.5 fail/PLAN-005、transient runtime error = fail-open + degraded event 記録、L8 受入チェックリストで別項目) |
| v29 | 2026-04-28 | TL レビュー P1×3 反映 (P2 ゼロ): (P1#1) secret 設定パスを **`~/.config/helix/auto-restart.local.yaml` ($HOME 配下) に一本化**、project-local 表記 (`.helix/auto-restart.local.yaml`) を撤廃、Tier A の HOME 限定方針と整合 / (P1#2) G3 停止条件で **stdlib-only での G3 通過を不可化**: (a) usage API で G-2 full pass 済み、(b) L1/G1 再ベースラインで advisory 別ゴール、のいずれかのみ stdlib fallback 許容、それ以外は G3 前に D separated (PLAN-005 分離) / (P1#3) handover dump の **redaction を機械契約 lossless に修正**: CURRENT.json は resume 用機械フィールドのため redaction 適用不可、redaction は表示ログ・監査ログ・外部出力のみ、必要なら別途 redacted preview を分離 |
| v30 | 2026-04-28 | TL レビュー P1×1/P2×2 反映: (P1) lossless を機械 ID (task_id, 正規化済み file path, enum status) に限定、自由テキストは CURRENT.json へ直接保存しない方針へ / (P2#1) `handover_manifest_hash` / `worktree_snapshot_hash` を RFC8785 相当 canonical JSON（path は UTF-8 base64 表現、byte-wise sort）に固定 / (P2#2) separated 後 passed は縮小 scope の pass と明記し、rebaseline 認定時の `gates.G1R.scope_state` / `gates.G1.5.scope_state` と再ベースライン証跡、B/D 結果・scope_hash を必須参照証跡化 |
| v31 | 2026-04-28 | TL レビュー P1×3/P2×1 反映: (P1#1) `gates.G1R.scope_state` / `gates.G1.5.scope_state` を削除し、`B-result.json` / `D-result.json` と `.helix/baseline/PLAN-002-rebaseline-<outcome>.md` の `scope_state` セクションへ集約（phase.yaml スキーマ変更なし） / (P1#2) `auto_restart_log` を security-critical state として helix.db/.helix の owner/mode/symlink 再検証・fail-closed を追加、分離保存 option を L3 D-DB/D-HOOK-SPEC で凍結 / (P1#3) CURRENT schema v2 契約、`CURRENT-redacted-preview.md` 生成規則、v1/v2 互換、migration/backward fixture を追加 / (P2) handover hash の canonical serializer を `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)` へ固定し、rename/symlink/submodule/untracked/tab/newline fixture を期待値付きで L3/G1.5(B) 必須化 |
| v32 | 2026-04-28 | TL レビュー P1×2/P2×2 反映: (P1#1) auto_restart_log 既定を `~/.helix/auto-restart/log.db` 分離保存へ統一 / (P1#2) CURRENT schema v2 を additive migration（`current_schema_version` 追加）で v1 互換+ lossless 機械フィールド固定、redaction preview 運用と v1/v2 併存互換を明確化 / (P2#1) `auto_restart.dump_cooldown_seconds=300` / `auto_restart.token_sampling_window=20` の固定値と範囲を D-HOOK-SPEC・G1.5(D) fixture で凍結 / (P2#2) redaction-denylist を `redaction-denylist.example.yaml` + `.gitignore` 対応 `.local.yaml` / `redaction-denylist.hmac.yaml` に再編 / 改訂履歴順序 v30→v31→v32 を明記 |
| v34 | 2026-04-28 | TL レビュー P1×2/P2×3 反映: (P1#1) G-2 ゴール表/閾値/文言を HOME DB 仕様と整合し、B separated の 5% を「D-owned 自動 dump + 手動 restart（resume コマンド表示）」に統一 / (P1#2) HOME DB (`~/.helix/auto-restart/log.db` `auto_restart_log`) 受入項目を L8/L6 に追加、fresh checkout/所有者・mode・symlink・replay 拒否・rate limit・90 日 retention/VACUUM を必須化 / (P2#1) CURRENT schema v2 を `legacy input` と `normalized output` に分離定義、fixture を `legacy-input` / `normalized-output` に再編、`helix handover resume` 等で互換テストを必須化 / (P2#2) phase.yaml 集約を `failed` 固定化、`blocked` 表現を撤回、`separated` 判別は B/D-result と scope_hash / rebaseline artifact 参照に収斂 / (P2#3) `handover_manifest_hash` / `worktree_snapshot_hash` 期待 fixture を分離反映 |
| v33 | 2026-04-28 | TL レビュー P1×2/P2×3/P3×1 反映: (P1#1) auto_restart_log を `~/.helix/auto-restart/log.db` のみに統一、helix.db 追加テーブルと Sprint2/L4 migration から削除。 `auto_restart_log` DDL は HOME DB（`UNIQUE(task_id, nonce)` + transaction + retention 90 日）として L3/D-HOOK-SPEC + L8 受入条件へ明記 / (P1#2) CURRENT schema 契約を `schema_version` 一本化、`current_schema_version` を撤廃、v1 構造移動なし / (P2#1) phase.yaml 集約規則を `blocked` 対応へ更新（rebaseline 完了まで）、(P2#2) usage API 不在時の advisory 要件を tokenizer 必須/PLAN-005 分離へ明確化、(P2#3) redaction-denylist 成果物を `.example`/`.local`/`.hmac` の3構成へ更新 / (P3) タイトル・改訂履歴を v33 化 |
