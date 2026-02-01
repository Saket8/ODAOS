"""ODAOS Advanced AI Dashboard.

Enterprise-grade Oracle database monitoring with AI-powered insights.
Features:
- Real-time metrics with trend analysis
- AI-powered performance recommendations (Groq LLM)
- Interactive charts and visualizations
- Automated health scoring and alerts
- SQL tuning suggestions
- Capacity planning forecasts
"""
import warnings
warnings.filterwarnings("ignore")

import sys
import os
sys.path.insert(0, ".")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Oracle thick mode FIRST
import oracledb
try:
    oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_20")
except:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import os
import json

from src.database.tunnel import SSHTunnelManager
from src.core.config import get_settings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# Global
tunnel = None
conn = None
llm = None
metrics_history = []

# Cache for faster API responses
_cache = {}
_cache_time = None
CACHE_TTL_SECONDS = 30  # Refresh cache every 30 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tunnel, conn, llm
    
    print("Starting ODAOS Advanced AI Dashboard...")
    tunnel = SSHTunnelManager()
    tunnel.start()
    print("✓ SSH Tunnel active")
    
    settings = get_settings()
    conn = oracledb.connect(
        user=settings.oracle_user,
        password=settings.oracle_password.get_secret_value(),
        dsn=settings.oracle_dsn
    )
    print("✓ Connected to database")
    
    # Initialize Groq LLM with explicit API key
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("⚠ GROQ_API_KEY not found - AI analysis will be disabled")
        llm = None
    else:
        llm = ChatGroq(
            api_key=groq_key,
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        print("✓ AI Engine (Groq) initialized")
    
    yield
    
    if conn: conn.close()
    if tunnel: tunnel.stop()


app = FastAPI(title="ODAOS AI Dashboard", lifespan=lifespan)


def query(sql: str) -> list:
    cursor = conn.cursor()
    cursor.execute(sql)
    cols = [c[0] for c in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return [dict(zip(cols, r)) for r in rows]


def safe_query(sql: str, default=None) -> list:
    """Execute query with error handling."""
    try:
        return query(sql)
    except Exception as e:
        print(f"Query error: {e}")
        return default if default is not None else []


def get_cached_data(key: str, fetch_func, ttl: int = CACHE_TTL_SECONDS):
    """Get data from cache or fetch if expired."""
    import time
    global _cache, _cache_time
    
    now = time.time()
    if key in _cache and _cache_time and (now - _cache_time.get(key, 0)) < ttl:
        return _cache[key]
    
    # Initialize cache time dict if needed
    if _cache_time is None:
        _cache_time = {}
    
    try:
        data = fetch_func()
        _cache[key] = data
        _cache_time[key] = now
        return data
    except Exception as e:
        print(f"Cache fetch error for {key}: {e}")
        return _cache.get(key, None)


def calculate_health_score() -> dict:
    """Calculate overall database health score 0-100."""
    score = 100
    issues = []
    
    # Check tablespace usage
    ts = query("""
        SELECT ts.tablespace_name,
               ROUND((df.bytes - NVL(fs.bytes, 0))/df.bytes * 100, 1) as used_pct
        FROM dba_tablespaces ts
        LEFT JOIN (SELECT tablespace_name, SUM(bytes) bytes FROM dba_data_files GROUP BY tablespace_name) df 
            ON ts.tablespace_name = df.tablespace_name
        LEFT JOIN (SELECT tablespace_name, SUM(bytes) bytes FROM dba_free_space GROUP BY tablespace_name) fs 
            ON ts.tablespace_name = fs.tablespace_name
        WHERE ts.contents = 'PERMANENT' AND df.bytes IS NOT NULL
    """)
    
    for t in ts:
        pct = t['USED_PCT'] or 0
        if pct >= 95:
            score -= 20
            issues.append(f"CRITICAL: {t['TABLESPACE_NAME']} at {pct}%")
        elif pct >= 85:
            score -= 10
            issues.append(f"WARNING: {t['TABLESPACE_NAME']} at {pct}%")
    
    # Check blocking sessions
    blocking = query("SELECT COUNT(*) CNT FROM v$session WHERE blocking_session IS NOT NULL")[0]['CNT']
    if blocking > 0:
        score -= 15 * blocking
        issues.append(f"CRITICAL: {blocking} blocked sessions")
    
    # Check resource limits
    limits = query("""
        SELECT resource_name, current_utilization, max_utilization, limit_value
        FROM v$resource_limit 
        WHERE limit_value NOT LIKE '%UNLIMITED%' AND max_utilization > 0
    """)
    
    for r in limits:
        try:
            limit = int(r['LIMIT_VALUE'])
            used = int(r['MAX_UTILIZATION'])
            if limit > 0 and used / limit > 0.9:
                score -= 10
                issues.append(f"Resource {r['RESOURCE_NAME']} near limit")
        except:
            pass
    
    return {
        "score": max(0, min(100, score)),
        "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
        "issues": issues[:5]  # Top 5 issues
    }


@app.get("/api/health-score")
async def get_health_score():
    return calculate_health_score()


@app.get("/api/ai-analysis")
async def get_ai_analysis():
    """Get AI-powered database analysis and recommendations."""
    
    # Gather metrics
    ts_data = query("""
        SELECT ts.tablespace_name,
               ROUND((df.bytes - NVL(fs.bytes, 0))/df.bytes * 100, 1) as used_pct
        FROM dba_tablespaces ts
        LEFT JOIN (SELECT tablespace_name, SUM(bytes) bytes FROM dba_data_files GROUP BY tablespace_name) df 
            ON ts.tablespace_name = df.tablespace_name
        LEFT JOIN (SELECT tablespace_name, SUM(bytes) bytes FROM dba_free_space GROUP BY tablespace_name) fs 
            ON ts.tablespace_name = fs.tablespace_name
        WHERE ts.contents = 'PERMANENT' AND df.bytes IS NOT NULL
        ORDER BY used_pct DESC
    """)
    
    top_sql = query("""
        SELECT sql_id, ROUND(elapsed_time/1000000, 2) as elapsed_secs, executions,
               ROUND(buffer_gets/NULLIF(executions,0)) as buffer_per_exec
        FROM v$sql WHERE executions > 0
        ORDER BY elapsed_time DESC FETCH FIRST 5 ROWS ONLY
    """)
    
    wait_events = query("""
        SELECT event, wait_class, ROUND(time_waited/100, 2) as time_secs
        FROM v$system_event WHERE wait_class != 'Idle'
        ORDER BY time_waited DESC FETCH FIRST 5 ROWS ONLY
    """)
    
    sessions = query("""
        SELECT COUNT(*) total, SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END) active
        FROM v$session WHERE type='USER'
    """)[0]
    
    # Build context for AI
    context = f"""
    Database: Oracle 19c on OCI Base Database System (BRMPDB)
    
    Tablespace Usage:
    {json.dumps(ts_data, indent=2)}
    
    Top SQL by Elapsed Time:
    {json.dumps(top_sql, indent=2)}
    
    Top Wait Events:
    {json.dumps(wait_events, indent=2)}
    
    Sessions: {sessions['TOTAL']} total, {sessions['ACTIVE']} active
    """
    
    # Get AI analysis
    system_prompt = """You are an expert Oracle DBA AI assistant. Analyze the database metrics and provide:
    1. An executive summary (2-3 sentences)
    2. Top 3 actionable recommendations with priority (HIGH/MEDIUM/LOW)
    3. Any immediate concerns that need attention
    
    Format your response as JSON with keys: summary, recommendations (array of {priority, title, action}), concerns (array)
    Be specific and actionable. Reference actual tablespace names and SQL IDs when relevant."""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        
        # Parse response
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content)
    except Exception as e:
        return {
            "summary": f"AI analysis temporarily unavailable: {str(e)[:50]}",
            "recommendations": [],
            "concerns": []
        }


@app.get("/api/sql-tuning/{sql_id}")
async def get_sql_tuning(sql_id: str):
    """Get AI-powered SQL tuning suggestions for a specific SQL."""
    
    sql_info = query(f"""
        SELECT sql_id, sql_text, elapsed_time, executions, buffer_gets, 
               disk_reads, rows_processed, plan_hash_value
        FROM v$sql WHERE sql_id = '{sql_id}' AND ROWNUM = 1
    """)
    
    if not sql_info:
        return {"error": "SQL ID not found"}
    
    sql = sql_info[0]
    
    prompt = f"""Analyze this Oracle SQL statement and provide tuning recommendations:

SQL ID: {sql['SQL_ID']}
Elapsed Time: {sql['ELAPSED_TIME']/1000000:.2f} seconds
Executions: {sql['EXECUTIONS']}
Buffer Gets: {sql['BUFFER_GETS']}
Disk Reads: {sql['DISK_READS']}
Rows Processed: {sql['ROWS_PROCESSED']}

SQL Text:
{sql['SQL_TEXT'][:2000]}

Provide specific tuning suggestions including:
1. Index recommendations
2. SQL rewrite suggestions
3. Potential execution plan improvements
4. Parameter adjustments if applicable

Format as JSON with: issue, recommendations (array), estimated_improvement"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are an Oracle SQL tuning expert. Provide specific, actionable recommendations."),
            HumanMessage(content=prompt)
        ])
        
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content)
    except Exception as e:
        return {"error": str(e), "sql_info": sql}


@app.get("/api/full-metrics")
async def get_full_metrics():
    """Get comprehensive database metrics."""
    
    # Database info
    db_info = query("""
        SELECT d.name, d.created, d.open_mode, d.database_role,
               (SELECT banner FROM v$version WHERE ROWNUM=1) as version,
               (SELECT sys_context('USERENV','CON_NAME') FROM dual) as pdb
        FROM v$database d
    """)[0]
    
    # Instance info
    instance = query("""
        SELECT instance_name, host_name, startup_time, status, 
               ROUND((SYSDATE - startup_time) * 24, 1) as uptime_hours
        FROM v$instance
    """)[0]
    
    # SGA
    sga = query("""
        SELECT name, ROUND(bytes/1024/1024, 2) as mb 
        FROM v$sgainfo 
        WHERE name IN ('Fixed SGA Size', 'Redo Buffers', 'Buffer Cache Size', 
                      'Shared Pool Size', 'Large Pool Size', 'Java Pool Size', 'Total SGA Size')
    """)
    
    # Sessions
    sessions = query("""
        SELECT status, COUNT(*) cnt FROM v$session WHERE type='USER' GROUP BY status
    """)
    
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
    
    # Top SQL
    top_sql = query("""
        SELECT sql_id, 
               ROUND(elapsed_time/1000000, 2) as elapsed_secs,
               executions,
               ROUND(buffer_gets/NULLIF(executions,0)) as buffer_per_exec,
               SUBSTR(sql_text, 1, 100) as preview
        FROM v$sql WHERE executions > 0
        ORDER BY elapsed_time DESC FETCH FIRST 10 ROWS ONLY
    """)
    
    # Wait events
    waits = query("""
        SELECT event, wait_class, total_waits, ROUND(time_waited/100, 2) as time_secs
        FROM v$system_event WHERE wait_class != 'Idle'
        ORDER BY time_waited DESC FETCH FIRST 10 ROWS ONLY
    """)
    
    # System stats
    stats = query("""
        SELECT name, value FROM v$sysstat 
        WHERE name IN ('user commits', 'user rollbacks', 'execute count', 
                      'parse count (total)', 'physical reads', 'physical writes',
                      'db block gets', 'consistent gets')
    """)
    
    # Blocking
    blocking = query("""
        SELECT COUNT(*) cnt FROM v$session WHERE blocking_session IS NOT NULL
    """)[0]['CNT']
    
    # Health score
    health = calculate_health_score()
    
    return {
        "database": db_info,
        "instance": instance,
        "sga": {s['NAME']: s['MB'] for s in sga},
        "sessions": {s['STATUS']: s['CNT'] for s in sessions},
        "tablespaces": tablespaces,
        "top_sql": top_sql,
        "wait_events": waits,
        "system_stats": {s['NAME']: s['VALUE'] for s in stats},
        "blocking_count": blocking,
        "health": health,
        "timestamp": datetime.now().isoformat()
    }


# Enhanced Dashboard HTML
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ODAOS AI Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-primary: #0a0a1a;
            --bg-secondary: rgba(255,255,255,0.03);
            --bg-card: rgba(255,255,255,0.05);
            --accent-cyan: #00d9ff;
            --accent-green: #00ff88;
            --accent-orange: #ffaa00;
            --accent-red: #ff4455;
            --accent-purple: #a855f7;
            --text-primary: #ffffff;
            --text-secondary: #888;
            --border: rgba(255,255,255,0.1);
        }
        
        body {
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            background-image: 
                radial-gradient(ellipse at top left, rgba(0,217,255,0.1) 0%, transparent 50%),
                radial-gradient(ellipse at bottom right, rgba(168,85,247,0.1) 0%, transparent 50%);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0,0,0,0.3);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .ai-badge {
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan));
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 1px;
        }
        
        .health-score {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .score-circle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            position: relative;
        }
        
        .score-circle.grade-A { background: linear-gradient(135deg, var(--accent-green), #00cc6a); }
        .score-circle.grade-B { background: linear-gradient(135deg, #88ff00, var(--accent-green)); }
        .score-circle.grade-C { background: linear-gradient(135deg, var(--accent-orange), #ff8800); }
        .score-circle.grade-D { background: linear-gradient(135deg, #ff6600, var(--accent-orange)); }
        .score-circle.grade-F { background: linear-gradient(135deg, var(--accent-red), #cc0022); }
        
        .score-value { font-size: 1.5rem; color: #000; }
        .score-grade { font-size: 0.7rem; color: rgba(0,0,0,0.6); }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
        }
        
        .full-width { grid-column: 1 / -1; }
        
        .card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid var(--border);
            backdrop-filter: blur(10px);
        }
        
        .card h2 {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .card h2 .icon { font-size: 1.2rem; }
        
        .metric {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .metric-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        
        .ai-card {
            background: linear-gradient(135deg, rgba(168,85,247,0.1), rgba(0,217,255,0.1));
            border: 1px solid rgba(168,85,247,0.3);
        }
        
        .ai-card h2 {
            color: var(--accent-purple);
        }
        
        .recommendation {
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            border-left: 3px solid var(--accent-cyan);
        }
        
        .recommendation.high { border-color: var(--accent-red); }
        .recommendation.medium { border-color: var(--accent-orange); }
        .recommendation.low { border-color: var(--accent-green); }
        
        .priority-badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.65rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }
        
        .priority-badge.high { background: rgba(255,68,85,0.2); color: var(--accent-red); }
        .priority-badge.medium { background: rgba(255,170,0,0.2); color: var(--accent-orange); }
        .priority-badge.low { background: rgba(0,255,136,0.2); color: var(--accent-green); }
        
        .rec-title { font-weight: 600; margin-bottom: 0.5rem; }
        .rec-action { font-size: 0.875rem; color: var(--text-secondary); }
        
        .summary-box {
            background: rgba(0,217,255,0.1);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(0,217,255,0.2);
        }
        
        .summary-box p { line-height: 1.6; }
        
        .progress-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
        }
        
        .progress-bar {
            flex-grow: 1;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            margin: 0 1rem;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-green), var(--accent-cyan));
            transition: width 0.5s;
        }
        
        .progress-fill.warning { background: linear-gradient(90deg, var(--accent-orange), #ff8800); }
        .progress-fill.critical { background: linear-gradient(90deg, var(--accent-red), #cc0022); }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        
        th { 
            color: var(--text-secondary); 
            font-weight: 500;
            font-size: 0.8rem;
            text-transform: uppercase;
        }
        
        .sql-id {
            font-family: 'JetBrains Mono', monospace;
            color: var(--accent-cyan);
            cursor: pointer;
        }
        
        .sql-id:hover { text-decoration: underline; }
        
        .sql-preview {
            font-family: monospace;
            font-size: 0.75rem;
            color: var(--text-secondary);
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }
        
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem;
            background: rgba(255,255,255,0.02);
            border-radius: 8px;
        }
        
        .info-label { color: var(--text-secondary); }
        .info-value { font-weight: 600; }
        
        .chart-container {
            height: 200px;
            margin-top: 1rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-green);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 10px var(--accent-green); }
            50% { opacity: 0.5; box-shadow: none; }
        }
        
        .refresh-btn {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            border: none;
            padding: 0.5rem 1.25rem;
            border-radius: 8px;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,217,255,0.3);
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }
        
        .loading::after {
            content: '';
            animation: dots 1.5s infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        @media (max-width: 1200px) {
            .grid-3 { grid-template-columns: repeat(2, 1fr); }
        }
        
        @media (max-width: 768px) {
            .grid-3, .grid-2 { grid-template-columns: 1fr; }
            .header { flex-direction: column; gap: 1rem; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <h1>🔮 ODAOS</h1>
            <span class="ai-badge">AI-POWERED</span>
        </div>
        
        <div class="health-score" id="health-container">
            <div class="score-circle grade-A" id="score-circle">
                <span class="score-value" id="score-value">--</span>
                <span class="score-grade" id="score-grade">--</span>
            </div>
            <div>
                <div style="font-weight: 600;">Database Health</div>
                <div style="color: var(--text-secondary); font-size: 0.8rem;" id="db-name">Loading...</div>
            </div>
        </div>
        
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div class="status-dot"></div>
            <span id="last-update" style="color: var(--text-secondary); font-size: 0.8rem;">--</span>
            <button class="refresh-btn" onclick="refreshAll()">↻ Refresh</button>
        </div>
    </div>
    
    <div class="container">
        <!-- AI Analysis Section -->
        <div class="card ai-card full-width" style="margin-bottom: 1.5rem;">
            <h2><span class="icon">🤖</span> AI-Powered Analysis (Groq LLM)</h2>
            <div id="ai-analysis">
                <div class="loading">Analyzing database metrics with AI</div>
            </div>
        </div>
        
        <!-- Quick Metrics -->
        <div class="grid-3" style="margin-bottom: 1.5rem;">
            <div class="card">
                <h2><span class="icon">👥</span> Active Sessions</h2>
                <div class="metric" id="active-sessions">--</div>
                <div class="metric-label">of <span id="total-sessions">--</span> total user sessions</div>
            </div>
            
            <div class="card">
                <h2><span class="icon">⏱️</span> Uptime</h2>
                <div class="metric" id="uptime">--</div>
                <div class="metric-label" id="startup-time">Since startup</div>
            </div>
            
            <div class="card">
                <h2><span class="icon">🔒</span> Blocking Sessions</h2>
                <div class="metric" id="blocking-count">--</div>
                <div class="metric-label" id="blocking-status">Checking...</div>
            </div>
        </div>
        
        <!-- Database Info & SGA -->
        <div class="grid-2" style="margin-bottom: 1.5rem;">
            <div class="card">
                <h2><span class="icon">🗄️</span> Database Information</h2>
                <div class="info-grid" id="db-info">
                    <div class="loading">Loading...</div>
                </div>
            </div>
            
            <div class="card">
                <h2><span class="icon">💾</span> SGA Memory</h2>
                <canvas id="sga-chart"></canvas>
            </div>
        </div>
        
        <!-- Tablespaces -->
        <div class="card" style="margin-bottom: 1.5rem;">
            <h2><span class="icon">📊</span> Tablespace Usage</h2>
            <div id="tablespaces">
                <div class="loading">Loading tablespaces</div>
            </div>
        </div>
        
        <!-- Top SQL & Wait Events -->
        <div class="grid-2" style="margin-bottom: 1.5rem;">
            <div class="card">
                <h2><span class="icon">🔍</span> Top SQL by Elapsed Time</h2>
                <table id="top-sql">
                    <thead>
                        <tr>
                            <th>SQL ID</th>
                            <th>Elapsed</th>
                            <th>Execs</th>
                            <th>Gets/Exec</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            
            <div class="card">
                <h2><span class="icon">⏳</span> Top Wait Events</h2>
                <canvas id="waits-chart"></canvas>
            </div>
        </div>
        
        <!-- System Stats -->
        <div class="card">
            <h2><span class="icon">📈</span> System Statistics</h2>
            <div class="grid-3" id="system-stats">
                <div class="loading">Loading statistics</div>
            </div>
        </div>
    </div>
    
    <script>
        let sgaChart = null;
        let waitsChart = null;
        
        async function fetchJson(url) {
            const res = await fetch(url);
            return res.json();
        }
        
        function formatNumber(n) {
            if (!n) return '0';
            if (n >= 1000000000) return (n/1000000000).toFixed(1) + 'B';
            if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
            if (n >= 1000) return (n/1000).toFixed(1) + 'K';
            return n.toString();
        }
        
        async function loadAll() {
            const data = await fetchJson('/api/full-metrics');
            
            // Health score
            const circle = document.getElementById('score-circle');
            circle.className = 'score-circle grade-' + data.health.grade;
            document.getElementById('score-value').textContent = data.health.score;
            document.getElementById('score-grade').textContent = 'Grade ' + data.health.grade;
            
            // DB name
            document.getElementById('db-name').textContent = 
                data.database.NAME + ' / ' + data.database.PDB;
            
            // Sessions
            const active = data.sessions['ACTIVE'] || 0;
            const inactive = data.sessions['INACTIVE'] || 0;
            document.getElementById('active-sessions').textContent = active;
            document.getElementById('total-sessions').textContent = active + inactive;
            
            // Uptime
            document.getElementById('uptime').textContent = 
                Math.floor(data.instance.UPTIME_HOURS) + 'h';
            document.getElementById('startup-time').textContent = 
                'Since ' + new Date(data.instance.STARTUP_TIME).toLocaleDateString();
            
            // Blocking
            document.getElementById('blocking-count').textContent = data.blocking_count;
            document.getElementById('blocking-status').textContent = 
                data.blocking_count === 0 ? '✓ No blocks detected' : '⚠ Action required!';
            document.getElementById('blocking-count').style.background = 
                data.blocking_count === 0 
                    ? 'linear-gradient(135deg, var(--accent-green), var(--accent-cyan))' 
                    : 'linear-gradient(135deg, var(--accent-red), var(--accent-orange))';
            
            // Database info
            document.getElementById('db-info').innerHTML = `
                <div class="info-item"><span class="info-label">Database</span><span class="info-value">${data.database.NAME}</span></div>
                <div class="info-item"><span class="info-label">Container</span><span class="info-value">${data.database.PDB}</span></div>
                <div class="info-item"><span class="info-label">Open Mode</span><span class="info-value">${data.database.OPEN_MODE}</span></div>
                <div class="info-item"><span class="info-label">Role</span><span class="info-value">${data.database.DATABASE_ROLE}</span></div>
                <div class="info-item"><span class="info-label">Instance</span><span class="info-value">${data.instance.INSTANCE_NAME}</span></div>
                <div class="info-item"><span class="info-label">Host</span><span class="info-value">${data.instance.HOST_NAME}</span></div>
            `;
            
            // SGA Chart
            const sgaLabels = Object.keys(data.sga).filter(k => k !== 'Total SGA Size');
            const sgaValues = sgaLabels.map(k => data.sga[k]);
            
            if (sgaChart) sgaChart.destroy();
            sgaChart = new Chart(document.getElementById('sga-chart'), {
                type: 'doughnut',
                data: {
                    labels: sgaLabels,
                    datasets: [{
                        data: sgaValues,
                        backgroundColor: [
                            '#00d9ff', '#00ff88', '#a855f7', 
                            '#ffaa00', '#ff4455', '#0088ff'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { color: '#888', font: { size: 10 } }
                        }
                    }
                }
            });
            
            // Tablespaces
            document.getElementById('tablespaces').innerHTML = data.tablespaces.map(ts => {
                const pct = ts.USED_PCT || 0;
                const cls = pct >= 90 ? 'critical' : pct >= 80 ? 'warning' : '';
                return `
                    <div class="progress-row">
                        <span style="width: 150px;">${ts.NAME}</span>
                        <div class="progress-bar">
                            <div class="progress-fill ${cls}" style="width: ${pct}%"></div>
                        </div>
                        <span style="width: 180px; text-align: right;">
                            ${pct}% (${formatNumber(ts.USED_MB)} / ${formatNumber(ts.TOTAL_MB)} MB)
                        </span>
                    </div>
                `;
            }).join('');
            
            // Top SQL
            document.querySelector('#top-sql tbody').innerHTML = data.top_sql.slice(0, 7).map(sql => `
                <tr>
                    <td><span class="sql-id" onclick="analyzeSql('${sql.SQL_ID}')">${sql.SQL_ID}</span></td>
                    <td>${sql.ELAPSED_SECS}s</td>
                    <td>${formatNumber(sql.EXECUTIONS)}</td>
                    <td>${formatNumber(sql.BUFFER_PER_EXEC || 0)}</td>
                </tr>
            `).join('');
            
            // Wait Events Chart
            const waitLabels = data.wait_events.slice(0, 6).map(w => w.EVENT.substring(0, 25));
            const waitValues = data.wait_events.slice(0, 6).map(w => w.TIME_SECS);
            
            if (waitsChart) waitsChart.destroy();
            waitsChart = new Chart(document.getElementById('waits-chart'), {
                type: 'bar',
                data: {
                    labels: waitLabels,
                    datasets: [{
                        label: 'Wait Time (s)',
                        data: waitValues,
                        backgroundColor: 'rgba(168,85,247,0.6)',
                        borderColor: 'rgba(168,85,247,1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#888' } },
                        y: { grid: { display: false }, ticks: { color: '#888', font: { size: 9 } } }
                    }
                }
            });
            
            // System Stats
            document.getElementById('system-stats').innerHTML = Object.entries(data.system_stats).map(([name, value]) => `
                <div class="info-item">
                    <span class="info-label">${name}</span>
                    <span class="info-value">${formatNumber(value)}</span>
                </div>
            `).join('');
            
            // Update timestamp
            document.getElementById('last-update').textContent = 
                'Updated: ' + new Date().toLocaleTimeString();
        }
        
        async function loadAiAnalysis() {
            document.getElementById('ai-analysis').innerHTML = 
                '<div class="loading">Analyzing database metrics with AI</div>';
            
            const data = await fetchJson('/api/ai-analysis');
            
            let html = '';
            
            if (data.summary) {
                html += `<div class="summary-box"><p>${data.summary}</p></div>`;
            }
            
            if (data.recommendations && data.recommendations.length > 0) {
                html += '<div style="margin-bottom: 0.5rem; font-weight: 600;">Recommendations:</div>';
                data.recommendations.forEach(rec => {
                    const priority = (rec.priority || 'medium').toLowerCase();
                    html += `
                        <div class="recommendation ${priority}">
                            <span class="priority-badge ${priority}">${priority.toUpperCase()}</span>
                            <span class="rec-title">${rec.title}</span>
                            <div class="rec-action">${rec.action}</div>
                        </div>
                    `;
                });
            }
            
            if (data.concerns && data.concerns.length > 0) {
                html += '<div style="margin-top: 1rem; padding: 1rem; background: rgba(255,68,85,0.1); border-radius: 8px;">';
                html += '<div style="font-weight: 600; color: var(--accent-red); margin-bottom: 0.5rem;">⚠️ Immediate Concerns</div>';
                data.concerns.forEach(c => {
                    html += `<div style="margin-left: 1rem; margin-bottom: 0.25rem;">• ${c}</div>`;
                });
                html += '</div>';
            }
            
            document.getElementById('ai-analysis').innerHTML = html || '<p>No issues detected. Database is healthy.</p>';
        }
        
        async function analyzeSql(sqlId) {
            alert('Analyzing SQL ' + sqlId + '...\\nThis feature fetches AI-powered tuning suggestions.\\nCheck /api/sql-tuning/' + sqlId + ' for details.');
        }
        
        async function refreshAll() {
            await Promise.all([loadAll(), loadAiAnalysis()]);
        }
        
        // Initial load
        refreshAll();
        
        // Auto refresh every 60s
        setInterval(loadAll, 60000);
        setInterval(loadAiAnalysis, 120000);
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  🔮 ODAOS AI-Powered Dashboard")
    print("  Oracle Database AI Operations System")
    print("="*60)
    print("\n  Starting server: http://localhost:8000")
    print("  Features:")
    print("    • AI-powered analysis (Groq LLM)")
    print("    • Real-time metrics & charts")
    print("    • Health scoring & recommendations")
    print("    • SQL tuning suggestions")
    print("\n  All operations are READ-ONLY")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
