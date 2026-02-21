"""Fix the Kill Blocking Session prompt (dba-sec-003) — add default values for sid/serial."""
import sqlite3

db = sqlite3.connect("data/prompts.db")
cursor = db.cursor()

# Revert dba-sec-002 back to empty defaults
cursor.execute("UPDATE prompt_library SET default_values = '{}' WHERE id = 'dba-sec-002'")

# Fix dba-sec-003 (Kill Blocking Session) — add default values
cursor.execute(
    "UPDATE prompt_library SET default_values = ? WHERE id = 'dba-sec-003'",
    ('{"sid": "123", "serial": "45678"}',)
)
db.commit()

# Verify
cursor.execute("SELECT id, title, default_values FROM prompt_library WHERE category = 'DBA_SECURITY'")
for r in cursor.fetchall():
    print(f"  {r[0]} | {r[1]} | defaults: {r[2]}")
        
db.close()
