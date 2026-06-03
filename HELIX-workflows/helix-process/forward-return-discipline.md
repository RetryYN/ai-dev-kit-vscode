# Forward 接続規律（駆動 workflow の引き戻し規律）

> 全駆動 workflow が Forward V-model へ戻る（`forward_return`）ときに満たすべき**共通規律の正本（SSoT）**。HELIX 絶対原則（`helix/HELIX_CORE.md §0/§1`: V-model へ収束・設計⇔検証を対で同時凍結・片肺禁止）を、駆動 workflow の戻し処理として operationalize する。各 workflow doc は本書を**参照**し、固有差分だけを書く（規律本体を再宣言しない）。

## 0. なぜ必要か

Forward は G6 等の関所で「設計層成果物が在って検証層が空（またはその逆）」を fail-close で止める。しかし**駆動 workflow（Reverse/Recovery/Incident/Retrofit/Add-feature/Refactor/Research/Discovery/Scrum）の戻し処理には同等の関所が無く**、実装層 L7 や検証層 L8/L9 へ戻すときに対の design 層（L6/L5/L4）を再凍結しないまま「完了」にできた。これは**片肺を V-model に持ち込む抜け穴**であり絶対原則と矛盾する。本規律はこの穴を全駆動 workflow で塞ぐ。

## 1. 適合基準（R1-R5）

駆動 workflow の戻しが「Forward へ収束した（完了）」と認められるには、戻し先 L とその対の design/検証 pair について次を満たす。

- **R1 同時凍結・片肺禁止**: 設計層と対の検証層を**対で同時に凍結**する。片方だけの成立を完了扱いにしない。
- **R2 粒度ペアリング**: L4↔L9（システム/コンポーネント）/ L5↔L8（モジュール/結合）/ L6↔L7（関数/単体・DbC）。設計は対の検証と同粒度で書く。
- **R3 design 層の物理存在 fail-close**: 戻し先が触れる層の design 成果物が物理的に存在し `design-coverage-baseline.md §5` の entry/exit 最低充足を満たす。
- **R4 trace 双方向宣言**: forward / backward リンクを frontmatter / trace matrix に**明示**する（「読めば分かる」は trace でない）。
- **R5 machine-clean + semantic-pass**: 対象 pair の `coverage=100 / uncovered=0 / missing_pair=0 / wrong_layer=0`（machine-clean）に加え、orphan/balance を含む semantic 判定（TL/PM）を通す。

## 2. forward_return contract（PLAN frontmatter）

駆動 PLAN の `forward_return` は「戻し先 L」だけでなく、再凍結の対象と証跡を宣言する（`plan-model.md` の contract を正とし、本書は意味を定義する）。

| フィールド | 意味 |
|---|---|
| `target_layer` | 主たる戻し先 L（L1/L3/L4/L5/L6/L7/L8-L14） |
| `touched_layers` | 実際に変更・復元・検証した層の集合 |
| `design_change_class` | `pure_impl` / `design_or_contract_changed` / `unknown`（§3） |
| `required_refreeze_pairs` | 再凍結が必要な対（例: `L6-L7`, `L5-L8`, `L4-L9`） |
| `refreeze_evidence` | detector 結果 + semantic gate 判定 + approver |
| `waiver` | 例外時のみ（§6）。PM/TL 承認 + 理由 + deferred finding |

## 3. design_change_class の判定（fail-close の核）

**default は「再凍結が必要（design_or_contract_changed）」。`pure_impl` は例外**で、次が**全て不変であることを証明できる**場合のみ宣言できる。

- 公開挙動 / 外部 I/O
- API / DB / 契約（schema・interface）
- 関数責務（DbC: requires / ensures / invariant）
- モジュール境界
- テスト期待値
- trace ID universe

一つでも証明できなければ `unknown` とし、**`design_or_contract_changed` 側に倒して**対の design 層を再凍結する。「設計は変えていないはず」という自己申告は証明ではない。

## 4. 再凍結対象（pair map）

`touched_layers` から再凍結すべき対を機械的に決める。

| touch した層 / 変更種別 | 再凍結する pair | 粒度判定 |
|---|---|---|
| L7（関数責務 / DbC / public callable 変更） | **L6↔L7** | L6 は DbC・関数粒度で **hard**（balance_ratio≥1.0 必須） |
| L8（モジュール境界 / 結合構造変更） | **L5↔L8** | detector + semantic 併用 |
| L9（システム / コンポーネント挙動変更） | **L4↔L9** | detector + semantic 併用 |
| L1/L3（要求・要件変更） | L1↔L14 / L3↔L12 | semantic 中心 |

> 注: `balance_ratio` は L6 では hard 指標（DbC/関数粒度の対称性）として強く見る。L4/L5 は detector clean に semantic 判定を併用する（`verification-strategy.md §11`）。

## 5. exit 条件（戻しが「完了」と認められる条件）

1. `design_change_class` を判定し、`required_refreeze_pairs` を確定（§3/§4）。
2. 各 required pair が R1-R5 を満たす（machine-clean + semantic-pass + design 物理存在 + trace 双方向）。
3. 機能追加系（Add-feature / Reverse / Retrofit）は functional-registry 同期を併せて exit 条件にする（`functional-registry §1.5`）。
4. `refreeze_evidence` を PLAN に記録（detector 結果 + semantic gate + approver）。

これを満たさない戻しは **`completed` にしない**。

## 6. waiver（例外）

`pure_impl` を detector / semantic evidence で証明できる場合のみ、対の design 再凍結を skip できる。条件:

- PM/TL 承認 + skip 理由を `waiver` に明記。
- 証明根拠（trace ID universe 不変 / テスト期待値不変 / 既存対層 green 等）を evidence に残す。
- 証明できないなら skip 不可。`completed` 放置せず **deferred finding** または **retroactive refreeze decision** を残す。

## 7. 段階導入（enforcement roadmap）

機械強制は段階的に上げる（一気に全面 fail-close にしない）。

- **Phase A**（文書正本化）: 本書 + `plan-model.md` contract + `HELIX-process-L0-L14.md` 参照 + 9 workflow 参照化。
- **Phase B**: PLAN lint が `forward_return` 拡張フィールド（touched_layers / design_change_class / required_refreeze_pairs）欠落を **warning**。
- **Phase C**: `trace_symmetry.py` + `design-coverage-baseline.md §5` で対象 pair の machine-clean を**必要条件**化。
- **Phase D**: gate / RGC / G6 等価へ **fail-close** 接続。semantic 判定は機械化せず、**detector clean AND TL/PM semantic gate** の AND とする。

## 8. 各駆動 workflow の固有差分（参照表）

各 workflow doc は本書を参照し、下記の固有点だけ自 doc に書く。

| workflow | 本書適用上の固有点 |
|---|---|
| Reverse | 「実装だけで閉じる→L7」は §3 で `pure_impl` 証明できる時のみ。証明不可なら L6↔L7 再凍結。 |
| Recovery | 再開点が実装層のとき、逸脱前後で design 対が整合するか §5 で確認してから Forward 再開。 |
| Incident | hotfix で L7/L8/L9 を先行しても、恒久化時に §3/§4 で対 design を再凍結するまで close しない。 |
| Retrofit | 「要件維持」でも環境/構成変更で IF・境界が変われば `design_or_contract_changed`。 |
| Add-feature | design pair freeze を registry 同期と**同等の exit 条件**にする（非対称を解消）。 |
| Refactor | 「設計 PLAN 起票せず」は **pure_impl に限る**。structural（境界→L5↔L8 / 責務・DbC→L6↔L7）は再凍結、契約/DB に触れたら Retrofit/Add-feature/Reverse へ差し戻し。 |
| Research | ADR が L4 判断を変えるなら L4↔L9 再凍結 owner を **TL+PM** に固定し、接続完了を exit にする。 |
| Discovery | 設計層昇格時に対の検証層（L6→L7 等）を**同時凍結**する。 |
| Scrum | 昇華先に **L6↔L7（単体）** を含める。`reverse fullback` 後は本書を必須適用し Reverse の穴を継承しない。 |

## 9. 関連

- 絶対原則: `helix/HELIX_CORE.md §0/§1`
- 工程・粒度: `HELIX-workflows/HELIX-process-L0-L14.md`
- entry/exit 関所: `skills/workflow/doc-system-architect/references/design-coverage-baseline.md §5`
- gap 指標・semantic: `docs/v2/L1-requirements/helix-workflows-verification-strategy.md §4/§11`
- PLAN 契約: `HELIX-workflows/helix-process/plan-model.md`
