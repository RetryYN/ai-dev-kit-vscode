#!/usr/bin/env bats

setup() {
  REPO_ROOT="/home/tenni/ai-dev-kit-vscode"
  CLI="$REPO_ROOT/cli/helix-drift-check"
  TMP_ROOT="$(mktemp -d)"
  PROJ="$TMP_ROOT/proj"

  mkdir -p "$PROJ/.helix" "$PROJ/docs/D-DB"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

create_db() {
  python3 - "$PROJ/.helix/helix.db" <<'PY'
import sqlite3
import sys

path = sys.argv[1]
conn = sqlite3.connect(path)
conn.execute("CREATE TABLE hook_events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT, file TEXT, result TEXT, created_at TEXT)")
conn.commit()
conn.close()
PY
}

@test "D-DB: カラム差分ありで [schema-drift] を出力" {
  create_db
  python3 - "$PROJ/.helix/helix.db" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
conn.commit()
conn.close()
PY

  cat > "$PROJ/docs/D-DB/schema.md" <<'EOF'
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT,
  email TEXT
);
```
EOF

  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/D-DB/schema.md'"

  [ "$status" -eq 0 ]
  [[ "$output" == *"[schema-drift]"* ]]
}

@test "D-DB: インデックス差分ありで [index-drift] を出力" {
  create_db
  python3 - "$PROJ/.helix/helix.db" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
conn.commit()
conn.close()
PY

  cat > "$PROJ/docs/D-DB/schema.md" <<'EOF'
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT
);
CREATE INDEX idx_users_email ON users(email);
```
EOF

  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/D-DB/schema.md'"

  [ "$status" -eq 0 ]
  [[ "$output" == *"[index-drift]"* ]]
}

@test "D-DB: 孤児テーブルありで [orphan] を出力" {
  create_db
  python3 - "$PROJ/.helix/helix.db" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
conn.execute("CREATE TABLE legacy_table (id INTEGER PRIMARY KEY)")
conn.commit()
conn.close()
PY

  cat > "$PROJ/docs/D-DB/schema.md" <<'EOF'
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY
);
```
EOF

  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/D-DB/schema.md'"

  [ "$status" -eq 0 ]
  [[ "$output" == *"[orphan]"* ]]
}

@test "D-DB: 完全一致なら WARN なしで問題なしを出力" {
  create_db
  python3 - "$PROJ/.helix/helix.db" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
conn.execute("CREATE UNIQUE INDEX idx_users_email_unique ON users(email)")
conn.commit()
conn.close()
PY

  cat > "$PROJ/docs/D-DB/schema.md" <<'EOF'
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT
);
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);
```
EOF

  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/D-DB/schema.md'"

  [ "$status" -eq 0 ]
  [[ "$output" == *"問題なし"* ]]
  [[ "$output" != *"[helix-drift] WARN:"* ]]
}

@test "D-DB: helix.db 未存在時は簡易チェックのみで詳細差分をスキップ" {
  cat > "$PROJ/docs/D-DB/schema.md" <<'EOF'
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT
);
```
EOF

  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/D-DB/schema.md'"

  [ "$status" -eq 0 ]
  [[ "$output" == *"問題なし"* ]]
  [[ "$output" != *"[schema-drift]"* ]]
  [[ "$output" != *"[index-drift]"* ]]
  [[ "$output" != *"[orphan]"* ]]
}
