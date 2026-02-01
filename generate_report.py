"""ODAOS Static Report Generator.

Generates a static HTML report that opens instantly in browser.
No real-time API calls - just a single query-and-render.
"""
import warnings
warnings.filterwarnings("ignore")

import sys
import os
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

# Initialize Oracle thick mode
import oracledb
try:
    oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_20")
except:
    pass

from datetime import datetime
import webbrowser
import json

from src.database.tunnel import SSHTunnelManager
from src.core.config import get_settings

print("="*60)
print("  🔮 ODAOS Static Report Generator")
print("="*60)

# Connect
print("\n1. Connecting to database...")
tunnel = SSHTunnelManager()
tunnel.start()
print("   ✓ SSH Tunnel active")

settings = get_settings()
conn = oracledb.connect(
    user=settings.oracle_user,
    password=settings.oracle_password.get_secret_value(),
    dsn=settings.oracle_dsn
)
print("   ✓ Connected to BRMPDB")

cursor = conn.cursor()

def query(sql):
    cursor.execute(sql)
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, r)) for r in cursor.fetchall()]

# Gather all data
print("\n2. Gathering metrics...")

# Database info
db_info = query("""
    SELECT d.name, d.created, d.open_mode, d.database_role,
           (SELECT banner FROM v$version WHERE ROWNUM=1) as version,
           (SELECT sys_context('USERENV','CON_NAME') FROM dual) as pdb
    FROM v$database d
""")[0]
print("   ✓ Database info")

# Instance
instance = query("""
    SELECT instance_name, host_name, startup_time, status, 
           ROUND((SYSDATE - startup_time) * 24, 1) as uptime_hours
    FROM v$instance
""")[0]
print("   ✓ Instance info")

# Sessions
sessions = query("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END) as active,
           SUM(CASE WHEN status='INACTIVE' THEN 1 ELSE 0 END) as inactive
    FROM v$session WHERE type='USER'
""")[0]
print("   ✓ Sessions")

# SGA
sga = query("""
    SELECT name, ROUND(bytes/1024/1024, 0) as mb 
    FROM v$sgainfo 
    WHERE name IN ('Fixed SGA Size', 'Redo Buffers', 'Buffer Cache Size', 
                  'Shared Pool Size', 'Large Pool Size', 'Total SGA Size')
""")
print("   ✓ SGA Memory")

# Tablespaces
tablespaces = query("""
    SELECT ts.tablespace_name as name,
           ROUND(df.bytes/1024/1024) as total_mb,
           ROUND((df.bytes - NVL(fs.bytes, 0))/1024/1024) as used_mb,
           ROUND((df.bytes - NVL(fs.bytes, 0))/df.bytes * 100, 1) as used_pct
    FROM dba_tablespaces ts
    LEFT JOIN (SELECT tablespace_name, SUM(bytes) bytes FROM dba_data_files GROUP BY tablespace_name) df 
        ON ts.tablespace_name = df.tablespace_name
    LEFT JOIN (SELECT tablespace_name, SUM(bytes) bytes FROM dba_free_space GROUP BY tablespace_name) fs 
        ON ts.tablespace_name = fs.tablespace_name
    WHERE ts.contents = 'PERMANENT' AND df.bytes IS NOT NULL
    ORDER BY used_pct DESC NULLS LAST
""")
print("   ✓ Tablespaces")

# Top SQL
top_sql = query("""
    SELECT sql_id, 
           ROUND(elapsed_time/1000000, 2) as elapsed_secs,
           executions,
           ROUND(buffer_gets/NULLIF(executions,0)) as buffer_per_exec,
           SUBSTR(sql_text, 1, 80) as preview
    FROM v$sql WHERE executions > 0
    ORDER BY elapsed_time DESC FETCH FIRST 10 ROWS ONLY
""")
print("   ✓ Top SQL")

# Wait events
waits = query("""
    SELECT event, wait_class, total_waits, ROUND(time_waited/100, 2) as time_secs
    FROM v$system_event WHERE wait_class != 'Idle'
    ORDER BY time_waited DESC FETCH FIRST 10 ROWS ONLY
""")
print("   ✓ Wait events")

# Blocking
blocking = query("""
    SELECT COUNT(*) cnt FROM v$session WHERE blocking_session IS NOT NULL
""")[0]['CNT']
print("   ✓ Blocking check")

# System stats
stats = query("""
    SELECT name, value FROM v$sysstat 
    WHERE name IN ('user commits', 'user rollbacks', 'execute count', 
                  'parse count (total)', 'physical reads', 'physical writes')
""")
print("   ✓ System stats")

# Close connection
cursor.close()
conn.close()
tunnel.stop()
print("\n   Connection closed")

# Calculate health score
print("\n3. Calculating health score...")
score = 100
issues = []
for ts in tablespaces:
    pct = ts['USED_PCT'] or 0
    if pct >= 95:
        score -= 20
        issues.append(f"CRITICAL: {ts['NAME']} at {pct}%")
    elif pct >= 85:
        score -= 10
        issues.append(f"WARNING: {ts['NAME']} at {pct}%")
if blocking > 0:
    score -= 15 * blocking
    issues.append(f"CRITICAL: {blocking} blocked sessions")
    
grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
print(f"   Health Score: {score} (Grade {grade})")

# Generate HTML
print("\n4. Generating HTML report...")

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ODAOS Report - {db_info['NAME']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        h1 {{
            font-size: 2rem;
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .timestamp {{ color: #888; }}
        .score-container {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .score-circle {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            background: {"linear-gradient(135deg, #00ff88, #00cc6a)" if grade == "A" else "linear-gradient(135deg, #88ff00, #00ff88)" if grade == "B" else "linear-gradient(135deg, #ffaa00, #ff8800)" if grade == "C" else "linear-gradient(135deg, #ff4444, #cc0022)"};
        }}
        .score-value {{ font-size: 1.8rem; color: #000; }}
        .score-grade {{ font-size: 0.8rem; color: rgba(0,0,0,0.6); }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card h2 {{
            font-size: 0.9rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 1rem;
        }}
        .metric {{ font-size: 2.5rem; font-weight: 700; color: #00d9ff; }}
        .metric-label {{ color: #888; font-size: 0.875rem; margin-top: 0.25rem; }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .info-label {{ color: #888; }}
        .progress-row {{
            display: flex;
            align-items: center;
            padding: 0.5rem 0;
        }}
        .progress-name {{ width: 120px; }}
        .progress-bar {{
            flex-grow: 1;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            margin: 0 1rem;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00d9ff);
        }}
        .progress-fill.warning {{ background: linear-gradient(90deg, #ffaa00, #ff8800); }}
        .progress-fill.critical {{ background: linear-gradient(90deg, #ff4444, #cc0022); }}
        .progress-value {{ width: 150px; text-align: right; color: #888; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        th {{ color: #888; font-weight: 500; font-size: 0.8rem; text-transform: uppercase; }}
        .sql-id {{ color: #00d9ff; font-family: monospace; }}
        .sql-preview {{ font-family: monospace; font-size: 0.75rem; color: #888; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .full-width {{ grid-column: 1 / -1; }}
        .badge {{ 
            display: inline-block; 
            padding: 0.25rem 0.75rem; 
            border-radius: 4px; 
            font-size: 0.75rem; 
            font-weight: 600; 
        }}
        .badge-ok {{ background: rgba(0,255,136,0.2); color: #00ff88; }}
        .badge-warn {{ background: rgba(255,170,0,0.2); color: #ffaa00; }}
        .badge-crit {{ background: rgba(255,68,68,0.2); color: #ff4444; }}
        .issues {{ margin-top: 1rem; }}
        .issue {{ padding: 0.5rem 1rem; background: rgba(255,170,0,0.1); border-left: 3px solid #ffaa00; margin-bottom: 0.5rem; border-radius: 4px; }}
        .issue.critical {{ background: rgba(255,68,68,0.1); border-color: #ff4444; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🔮 ODAOS Database Report</h1>
                <div class="timestamp">Generated: {timestamp}</div>
            </div>
            <div class="score-container">
                <div class="score-circle">
                    <span class="score-value">{score}</span>
                    <span class="score-grade">Grade {grade}</span>
                </div>
                <div>
                    <div style="font-size: 1.2rem; font-weight: 600;">Database Health</div>
                    <div style="color: #888;">{db_info['NAME']} / {db_info['PDB']}</div>
                </div>
            </div>
        </div>
        
        <!-- Quick Metrics -->
        <div class="grid" style="margin-bottom: 1.5rem;">
            <div class="card">
                <h2>👥 Sessions</h2>
                <div class="metric">{sessions['ACTIVE'] or 0}</div>
                <div class="metric-label">Active / {sessions['TOTAL'] or 0} Total</div>
            </div>
            <div class="card">
                <h2>⏱️ Uptime</h2>
                <div class="metric">{int(instance['UPTIME_HOURS'] or 0)}h</div>
                <div class="metric-label">Since {instance['STARTUP_TIME']}</div>
            </div>
            <div class="card">
                <h2>🔒 Blocking</h2>
                <div class="metric" style="color: {'#00ff88' if blocking == 0 else '#ff4444'};">{blocking}</div>
                <div class="metric-label">{'✓ No blocks' if blocking == 0 else '⚠ Action needed!'}</div>
            </div>
        </div>
        
        <!-- Database Info & Issues -->
        <div class="grid" style="margin-bottom: 1.5rem;">
            <div class="card">
                <h2>🗄️ Database Information</h2>
                <div class="info-row"><span class="info-label">Database</span><span>{db_info['NAME']}</span></div>
                <div class="info-row"><span class="info-label">Container</span><span>{db_info['PDB']}</span></div>
                <div class="info-row"><span class="info-label">Version</span><span>{db_info['VERSION'].split(' - ')[0] if db_info['VERSION'] else 'N/A'}</span></div>
                <div class="info-row"><span class="info-label">Open Mode</span><span>{db_info['OPEN_MODE']}</span></div>
                <div class="info-row"><span class="info-label">Role</span><span class="badge badge-ok">{db_info['DATABASE_ROLE']}</span></div>
                <div class="info-row"><span class="info-label">Host</span><span>{instance['HOST_NAME']}</span></div>
            </div>
            <div class="card">
                <h2>💾 SGA Memory</h2>
                {''.join(f'<div class="info-row"><span class="info-label">{s["NAME"]}</span><span>{s["MB"]:,} MB</span></div>' for s in sga)}
            </div>
        </div>
        
        <!-- Issues if any -->
        {f'''<div class="card full-width" style="margin-bottom: 1.5rem;">
            <h2>⚠️ Issues Detected</h2>
            <div class="issues">
                {''.join(f'<div class="issue {"critical" if "CRITICAL" in i else ""}">{i}</div>' for i in issues)}
            </div>
        </div>''' if issues else ''}
        
        <!-- Tablespaces -->
        <div class="card full-width" style="margin-bottom: 1.5rem;">
            <h2>📊 Tablespace Usage</h2>
            {''.join(f'''<div class="progress-row">
                <span class="progress-name">{ts['NAME']}</span>
                <div class="progress-bar">
                    <div class="progress-fill {'critical' if (ts['USED_PCT'] or 0) >= 90 else 'warning' if (ts['USED_PCT'] or 0) >= 80 else ''}" style="width: {ts['USED_PCT'] or 0}%"></div>
                </div>
                <span class="progress-value">{ts['USED_PCT'] or 0}% ({ts['USED_MB'] or 0:,} / {ts['TOTAL_MB'] or 0:,} MB)</span>
            </div>''' for ts in tablespaces)}
        </div>
        
        <!-- Top SQL -->
        <div class="card full-width" style="margin-bottom: 1.5rem;">
            <h2>🔍 Top SQL by Elapsed Time</h2>
            <table>
                <thead>
                    <tr><th>SQL ID</th><th>Elapsed (s)</th><th>Executions</th><th>Gets/Exec</th><th>Preview</th></tr>
                </thead>
                <tbody>
                    {''.join(f'''<tr>
                        <td class="sql-id">{sql['SQL_ID']}</td>
                        <td>{sql['ELAPSED_SECS']}</td>
                        <td>{sql['EXECUTIONS']:,}</td>
                        <td>{sql['BUFFER_PER_EXEC'] or 0:,}</td>
                        <td class="sql-preview">{sql['PREVIEW'] or ''}</td>
                    </tr>''' for sql in top_sql)}
                </tbody>
            </table>
        </div>
        
        <!-- Wait Events & Stats -->
        <div class="grid">
            <div class="card">
                <h2>⏳ Top Wait Events</h2>
                <table>
                    <thead><tr><th>Event</th><th>Time (s)</th></tr></thead>
                    <tbody>
                        {''.join(f'<tr><td>{w["EVENT"][:40]}</td><td>{w["TIME_SECS"]:,.2f}</td></tr>' for w in waits[:7])}
                    </tbody>
                </table>
            </div>
            <div class="card">
                <h2>📈 System Statistics</h2>
                {''.join(f'<div class="info-row"><span class="info-label">{s["NAME"]}</span><span>{s["VALUE"]:,}</span></div>' for s in stats)}
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 2rem; color: #666; font-size: 0.875rem;">
            ODAOS - Oracle Database AI Operations System | Report generated at {timestamp}
        </div>
    </div>
</body>
</html>
"""

# Save report
report_path = os.path.abspath("odaos_report.html")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"   ✓ Report saved: {report_path}")

# Open in browser
print("\n5. Opening in browser...")
webbrowser.open(f"file://{report_path}")

print("\n" + "="*60)
print("  ✅ REPORT COMPLETE!")
print("="*60)
print(f"\n  Database: {db_info['NAME']} / {db_info['PDB']}")
print(f"  Health Score: {score} (Grade {grade})")
print(f"  Report: {report_path}")
print("\n  The report has opened in your default browser.")
print("="*60)
