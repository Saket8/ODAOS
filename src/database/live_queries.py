"""Live Database Queries Module.

Provides synchronous database queries for all ODAOS components.
Uses SSH tunnel with Oracle thick mode for NNE support.

Usage:
    from src.database.live_queries import LiveDBQueries
    
    with LiveDBQueries() as db:
        metrics = db.get_performance_metrics()
        sessions = db.get_blocking_sessions()
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv()

import oracledb
from datetime import datetime
from typing import Optional, List, Dict, Any

# Initialize thick mode for NNE
try:
    oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_20")
except:
    pass

from src.database.tunnel import SSHTunnelManager
from src.core.config import get_settings


class LiveDBQueries:
    """Live database query manager with SSH tunnel support."""
    
    def __init__(self):
        """Initialize connection components."""
        self.tunnel: Optional[SSHTunnelManager] = None
        self.conn = None
        self.settings = get_settings()
    
    def __enter__(self):
        """Context manager entry - establish connection."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()
    
    def connect(self):
        """Establish SSH tunnel and database connection."""
        self.tunnel = SSHTunnelManager()
        self.tunnel.start()
        
        self.conn = oracledb.connect(
            user=self.settings.oracle_user,
            password=self.settings.oracle_password.get_secret_value(),
            dsn=self.settings.oracle_dsn
        )
    
    def close(self):
        """Close connection and tunnel."""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        if self.tunnel:
            try:
                self.tunnel.stop()
            except:
                pass
    
    def query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dicts."""
        cursor = self.conn.cursor()
        cursor.execute(sql)
        cols = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return [dict(zip(cols, r)) for r in rows]
    
    def query_one(self, sql: str) -> Optional[Dict[str, Any]]:
        """Execute a query and return first row."""
        results = self.query(sql)
        return results[0] if results else None
    
    # =========================================================================
    # Database Information
    # =========================================================================
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database and instance information."""
        db = self.query_one("""
            SELECT d.name, d.created, d.open_mode, d.database_role,
                   (SELECT banner FROM v$version WHERE ROWNUM=1) as version,
                   (SELECT sys_context('USERENV','CON_NAME') FROM dual) as pdb
            FROM v$database d
        """)
        
        instance = self.query_one("""
            SELECT instance_name, host_name, startup_time, status, 
                   ROUND((SYSDATE - startup_time) * 24, 1) as uptime_hours
            FROM v$instance
        """)
        
        return {
            "database": db,
            "instance": instance,
            "timestamp": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Performance Metrics
    # =========================================================================
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        # Session counts
        sessions = self.query_one("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END) as active,
                   SUM(CASE WHEN status='INACTIVE' THEN 1 ELSE 0 END) as inactive
            FROM v$session WHERE type='USER'
        """)
        
        # SGA info
        sga = self.query("""
            SELECT name, ROUND(bytes/1024/1024, 2) as mb 
            FROM v$sgainfo 
            WHERE name IN ('Fixed SGA Size', 'Redo Buffers', 'Buffer Cache Size', 
                          'Shared Pool Size', 'Large Pool Size', 'Java Pool Size', 'Total SGA Size')
        """)
        
        # PGA (optional - may not have permission)
        try:
            pga = self.query_one("""
                SELECT ROUND(value/1024/1024, 2) as pga_mb 
                FROM v$pgastat WHERE name = 'total PGA allocated'
            """)
            pga_mb = pga['PGA_MB'] if pga else 0
        except:
            pga_mb = 0
        
        # Wait events
        waits = self.query("""
            SELECT event, wait_class, total_waits, ROUND(time_waited/100, 2) as time_secs
            FROM v$system_event WHERE wait_class != 'Idle'
            ORDER BY time_waited DESC FETCH FIRST 10 ROWS ONLY
        """)
        
        # System stats
        stats = self.query("""
            SELECT name, value FROM v$sysstat 
            WHERE name IN ('user commits', 'user rollbacks', 'execute count', 
                          'parse count (total)', 'physical reads', 'physical writes',
                          'db block gets', 'consistent gets')
        """)
        
        return {
            "sessions": sessions,
            "sga": {s['NAME']: s['MB'] for s in sga},
            "pga_mb": pga_mb,
            "wait_events": waits,
            "system_stats": {s['NAME']: s['VALUE'] for s in stats},
            "timestamp": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Tablespace Usage
    # =========================================================================
    
    def get_tablespace_usage(self, threshold: int = 85) -> Dict[str, Any]:
        """Get tablespace usage with alerts."""
        tablespaces = self.query("""
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
        
        alerts = []
        healthy = []
        
        for ts in tablespaces:
            pct = ts['USED_PCT'] or 0
            ts_info = {
                "name": ts['NAME'],
                "total_mb": ts['TOTAL_MB'],
                "used_mb": ts['USED_MB'],
                "used_pct": pct,
                "free_mb": (ts['TOTAL_MB'] or 0) - (ts['USED_MB'] or 0)
            }
            
            if pct >= 95:
                ts_info["severity"] = "CRITICAL"
                alerts.append(ts_info)
            elif pct >= threshold:
                ts_info["severity"] = "WARNING"
                alerts.append(ts_info)
            else:
                ts_info["severity"] = "OK"
                healthy.append(ts_info)
        
        return {
            "threshold": threshold,
            "summary": {
                "total": len(tablespaces),
                "critical": len([a for a in alerts if a.get("severity") == "CRITICAL"]),
                "warning": len([a for a in alerts if a.get("severity") == "WARNING"]),
                "healthy": len(healthy)
            },
            "alerts": alerts,
            "healthy": healthy,
            "timestamp": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Top SQL
    # =========================================================================
    
    def get_top_sql(self, top_n: int = 10, order_by: str = "elapsed_time") -> List[Dict[str, Any]]:
        """Get top SQL statements by resource usage."""
        order_col = {
            "elapsed_time": "elapsed_time",
            "cpu_time": "cpu_time",
            "executions": "executions",
            "buffer_gets": "buffer_gets"
        }.get(order_by, "elapsed_time")
        
        return self.query(f"""
            SELECT sql_id, 
                   ROUND(elapsed_time/1000000, 2) as elapsed_secs,
                   ROUND(cpu_time/1000000, 2) as cpu_secs,
                   executions,
                   buffer_gets,
                   disk_reads,
                   rows_processed,
                   ROUND(buffer_gets/NULLIF(executions,0)) as gets_per_exec,
                   SUBSTR(sql_text, 1, 100) as sql_preview
            FROM v$sql 
            WHERE executions > 0
            ORDER BY {order_col} DESC 
            FETCH FIRST {top_n} ROWS ONLY
        """)
    
    def get_sql_detail(self, sql_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific SQL ID."""
        return self.query_one(f"""
            SELECT sql_id, sql_text, elapsed_time, cpu_time, executions,
                   buffer_gets, disk_reads, rows_processed, plan_hash_value,
                   parsing_schema_name, first_load_time, last_active_time
            FROM v$sql 
            WHERE sql_id = '{sql_id}' AND ROWNUM = 1
        """)
    
    # =========================================================================
    # Blocking Sessions
    # =========================================================================
    
    def get_blocking_sessions(self) -> Dict[str, Any]:
        """Get blocking session information."""
        blocking = self.query("""
            SELECT s.sid, s.serial#, s.username, s.machine, s.program,
                   s.blocking_session, s.wait_class, s.event,
                   s.seconds_in_wait, s.sql_id
            FROM v$session s
            WHERE s.blocking_session IS NOT NULL
            ORDER BY s.seconds_in_wait DESC
        """)
        
        blockers = self.query("""
            SELECT DISTINCT s.sid, s.serial#, s.username, s.machine,
                   s.program, s.sql_id, s.status,
                   (SELECT COUNT(*) FROM v$session WHERE blocking_session = s.sid) as victims
            FROM v$session s
            WHERE s.sid IN (SELECT blocking_session FROM v$session WHERE blocking_session IS NOT NULL)
        """)
        
        return {
            "blocked_count": len(blocking),
            "blocker_count": len(blockers),
            "blocked_sessions": blocking,
            "blockers": blockers,
            "timestamp": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Resource Limits
    # =========================================================================
    
    def get_resource_limits(self) -> List[Dict[str, Any]]:
        """Get resource limit usage."""
        return self.query("""
            SELECT resource_name, current_utilization, max_utilization, 
                   limit_value, 
                   CASE WHEN limit_value != 'UNLIMITED' AND TO_NUMBER(limit_value) > 0 
                        THEN ROUND(max_utilization / TO_NUMBER(limit_value) * 100, 1)
                        ELSE 0 END as used_pct
            FROM v$resource_limit 
            WHERE max_utilization > 0
            ORDER BY max_utilization DESC
        """)
    
    # =========================================================================
    # Health Score
    # =========================================================================
    
    def calculate_health_score(self) -> Dict[str, Any]:
        """Calculate overall database health score (0-100)."""
        score = 100
        issues = []
        
        # Check tablespaces
        ts_data = self.get_tablespace_usage(85)
        for alert in ts_data['alerts']:
            if alert['severity'] == 'CRITICAL':
                score -= 20
                issues.append(f"CRITICAL: Tablespace {alert['name']} at {alert['used_pct']}%")
            elif alert['severity'] == 'WARNING':
                score -= 10
                issues.append(f"WARNING: Tablespace {alert['name']} at {alert['used_pct']}%")
        
        # Check blocking sessions
        blocking = self.get_blocking_sessions()
        if blocking['blocked_count'] > 0:
            score -= 15 * min(blocking['blocked_count'], 3)
            issues.append(f"CRITICAL: {blocking['blocked_count']} blocked sessions")
        
        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
        
        return {
            "score": max(0, min(100, score)),
            "grade": grade,
            "issues": issues[:5],
            "timestamp": datetime.now().isoformat()
        }


# Quick test
if __name__ == "__main__":
    print("Testing LiveDBQueries...")
    
    with LiveDBQueries() as db:
        print("\n1. Database Info:")
        info = db.get_database_info()
        print(f"   Database: {info['database']['NAME']}")
        print(f"   PDB: {info['database']['PDB']}")
        print(f"   Uptime: {info['instance']['UPTIME_HOURS']}h")
        
        print("\n2. Performance Metrics:")
        metrics = db.get_performance_metrics()
        print(f"   Sessions: {metrics['sessions']['ACTIVE']} active / {metrics['sessions']['TOTAL']} total")
        
        print("\n3. Health Score:")
        health = db.calculate_health_score()
        print(f"   Score: {health['score']} (Grade {health['grade']})")
        if health['issues']:
            print(f"   Issues: {len(health['issues'])}")
        
        print("\n✓ All tests passed!")
