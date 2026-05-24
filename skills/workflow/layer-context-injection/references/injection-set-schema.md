> 目的: injection-set の 6 field 契約と 20 セル実体キー構造を固定する

# Injection Set Schema

## 実体キー

```yaml
drives:
  <drive>:
    layers:
      <layer>:
        injection:
          owner_role: tl
          mandatory_agents: []
          recommended_agents: []
          recommended_skills: []
          recommended_commands: []
          orchestration_mode: claude_judge_codex_impl
```

`layer` は injection field ではなく、`drives.{drive}.layers.{layer}.injection` の親キーとして表現する。

## 6 field 定義

| field | 型 | 意味 |
|---|---|---|
| `owner_role` | scalar | 工程の責任ロール |
| `mandatory_agents` | list | 必須 agent |
| `recommended_agents` | list | 推奨 agent |
| `recommended_skills` | list | 推奨 skill ID |
| `recommended_commands` | list | 推奨 command |
| `orchestration_mode` | scalar | 協調方式 |

## 値の扱い

- `owner_role`: PM/TL/SE/QA/DBA など工程責任を表す
- `mandatory_agents`: 空配列可。ただし不要な理由を説明できること
- `recommended_agents`: on-demand 系を入れる
- `recommended_skills`: `workflow/...` や `common/...` の skill ID を使う
- `recommended_commands`: 実在する `helix ...` command に限定する
- `orchestration_mode`: 人間判断と実装委譲の境界を表す

## 20 セル構造

- drive: `be`, `fe`, `db`, `fullstack`
- layer: `planning`, `requirement`, `architecture`, `detailed`, `functional`

この 20 セルが実体であり、L0-L14 はその上位概念として読む。
