"""Self-Healing LangGraph Agent.

LangGraph-based agent for Oracle Database incident detection and remediation.
Uses the Self-Healing MCP Server tools with Groq LLM.

Usage:
    from src.agents.self_healing.agent import SelfHealingAgent
    
    agent = SelfHealingAgent()
    response = await agent.chat("Are there any database issues I should know about?")
    print(response)
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from ...core.providers import create_llm
from ...mcp_servers.self_healing.server import (
    monitor_alert_log_handler,
    check_blocking_sessions_handler,
    get_tablespace_status_handler,
    extend_tablespace_handler,
    kill_session_handler,
    get_long_running_sessions_handler,
    get_user_privileges_handler,
    get_rman_backup_status_handler,
    get_archive_log_rate_handler,
    get_flash_recovery_area_handler,
)

logger = logging.getLogger(__name__)

# ============================================================================
# System Prompt
# ============================================================================

SELF_HEALING_AGENT_PROMPT = """You are an expert Oracle Database Operations Engineer and Incident Response Specialist.
Your job is to detect database incidents, analyze their impact, and provide safe remediation steps.

IMPORTANT SAFETY RULES:
1. NEVER auto-execute destructive commands (kill sessions, alter tablespaces)
2. ALWAYS provide commands for human review and approval
3. ALWAYS explain the impact before recommending actions
4. Prioritize database stability and data integrity

When investigating incidents:
1. Check alert log for recent errors and patterns
2. Look for blocking sessions causing application impact
3. Monitor tablespace usage for space issues
4. Correlate multiple symptoms to identify root cause

For each issue found:
- Explain what the error/issue means
- Assess severity (CRITICAL, WARNING, INFO)
- Describe potential business impact
- Provide specific remediation steps
- Generate ready-to-execute DDL/commands (but DO NOT execute)

Response Format:
📊 **Status Summary**: Quick overview
🔍 **Findings**: Detailed analysis per issue
⚠️ **Impact Assessment**: Business/technical impact
🔧 **Remediation Plan**: Step-by-step fix with commands
⏱️ **Priority**: Immediate/Urgent/Scheduled

Available Tools:
- monitor_alert_log: Scan for ORA- errors and patterns
- check_blocking_sessions: Find lock contention and blockers
- get_tablespace_status: Check space usage and predictions
- extend_tablespace: Generate DDL to add space (approval required)
- kill_session: Generate command to terminate session (approval required)
- get_long_running_sessions: Find sessions exceeding execution time threshold
- get_user_privileges: Audit system privileges and roles for a specific user
- get_rman_backup_status: Check recent RMAN backup jobs (success/failure)
- get_archive_log_rate: Analyze daily archive log generation rate in GB
- get_flash_recovery_area: Check FRA space utilization and components
"""


# ============================================================================
# Tool Definitions (LangChain-compatible wrappers)
# ============================================================================

@tool
async def monitor_alert_log(hours: int = 24) -> str:
    """Monitor Oracle alert log for errors and incidents.
    
    Args:
        hours: Number of hours to analyze (1-168, default 24)
    
    Scans alert.log for ORA- errors, categorizes by severity,
    detects error patterns, and provides remediation suggestions.
    """
    import json
    result = await monitor_alert_log_handler(hours)
    return json.dumps(result, indent=2, default=str)


@tool
async def check_blocking_sessions() -> str:
    """Check for blocking sessions and lock contention.
    
    Identifies sessions holding locks that block other sessions.
    Returns blocker details, wait times, and kill recommendations.
    Use when applications report slow queries or timeouts.
    """
    import json
    result = await check_blocking_sessions_handler()
    return json.dumps(result, indent=2, default=str)


@tool
async def get_tablespace_status() -> str:
    """Get detailed tablespace status for space management.
    
    Returns usage percentages, autoextend settings, and 
    predictions for when each tablespace will fill up.
    Use for proactive space management.
    """
    import json
    result = await get_tablespace_status_handler()
    return json.dumps(result, indent=2, default=str)


@tool
async def extend_tablespace(tablespace_name: str, size_mb: int = 1024) -> str:
    """Generate DDL to extend a tablespace.
    
    Args:
        tablespace_name: Name of the tablespace to extend
        size_mb: Size to add in MB (default 1024)
    
    IMPORTANT: This generates the DDL script for review - it does NOT
    auto-execute. The DBA must approve and run the command manually.
    """
    import json
    result = await extend_tablespace_handler(tablespace_name, size_mb)
    return json.dumps(result, indent=2, default=str)


@tool
async def kill_session(sid: int, serial: int, immediate: bool = False) -> str:
    """Generate command to kill a blocking session.
    
    Args:
        sid: Session ID to kill
        serial: Session serial number
        immediate: Use IMMEDIATE option for forceful disconnect
    
    IMPORTANT: This generates the command for review - it does NOT
    auto-execute. The DBA must approve and run the command manually.
    Uncommitted transactions will be rolled back.
    """
    import json
    result = await kill_session_handler(sid, serial, immediate)
    return json.dumps(result, indent=2, default=str)


@tool
async def get_long_running_sessions(minutes_threshold: int = 60) -> str:
    """Find long running user sessions in the database that exceed a specified execution threshold.
    
    Args:
        minutes_threshold: Minimum active minutes to be considered long running (default 60)
    """
    import json
    result = await get_long_running_sessions_handler(minutes_threshold)
    return json.dumps(result, indent=2, default=str)


@tool
async def get_user_privileges(username: str) -> str:
    """Audit and retrieve all system privileges and roles granted to a specific database user.
    
    Args:
        username: Database username to audit
    """
    import json
    result = await get_user_privileges_handler(username)
    return json.dumps(result, indent=2, default=str)


@tool
async def get_rman_backup_status(days: int = 7) -> str:
    """Check the status of recent RMAN database backup jobs, including success/failure rates.
    
    Args:
        days: Number of days to look back for backup jobs (default 7)
    """
    import json
    result = await get_rman_backup_status_handler(days)
    return json.dumps(result, indent=2, default=str)


@tool
async def get_archive_log_rate(days: int = 7) -> str:
    """Analyze the daily generation rate of archive logs in GB to identify abnormal redo generation.
    
    Args:
        days: Number of days of history to analyze (default 7)
    """
    import json
    result = await get_archive_log_rate_handler(days)
    return json.dumps(result, indent=2, default=str)


@tool
async def get_flash_recovery_area() -> str:
    """Check the Flash Recovery Area (FRA) space usage, limits, and component breakdown."""
    import json
    result = await get_flash_recovery_area_handler()
    return json.dumps(result, indent=2, default=str)


# All available tools
SELF_HEALING_TOOLS = [
    monitor_alert_log,
    check_blocking_sessions,
    get_tablespace_status,
    extend_tablespace,
    kill_session,
    get_long_running_sessions,
    get_user_privileges,
    get_rman_backup_status,
    get_archive_log_rate,
    get_flash_recovery_area,
]


# ============================================================================
# Self-Healing Agent Class
# ============================================================================

class SelfHealingAgent:
    """LangGraph-based Self-Healing Operations Agent."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        temperature: float = 0.0,
        enable_memory: bool = True,
    ):
        """Initialize the Self-Healing Agent.
        
        Args:
            provider: LLM provider (groq, ollama, anthropic)
            temperature: Model temperature
            enable_memory: Whether to enable conversation memory
        """
        self.llm = create_llm(provider=provider, temperature=temperature)
        self.memory = MemorySaver() if enable_memory else None
        
        self.agent = create_react_agent(
            model=self.llm,
            tools=SELF_HEALING_TOOLS,
            prompt=SELF_HEALING_AGENT_PROMPT,
            checkpointer=self.memory,
        )
        
        self._thread_id = "self-healing-agent-default"
        logger.info("Self-Healing Agent initialized")
    
    async def chat(self, message: str, thread_id: Optional[str] = None) -> str:
        """Send a message to the agent and get a response."""
        config = {"configurable": {"thread_id": thread_id or self._thread_id}}
        inputs = {"messages": [HumanMessage(content=message)]}
        
        logger.info(f"Agent processing: {message[:50]}...")
        result = await self.agent.ainvoke(inputs, config=config)
        
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "I was unable to process your request."
    
    def chat_sync(self, message: str, thread_id: Optional[str] = None) -> str:
        """Synchronous version of chat."""
        return asyncio.run(self.chat(message, thread_id))
    
    async def triage(self) -> str:
        """Run a comprehensive health triage.
        
        Checks all major health indicators and returns a summary.
        """
        return await self.chat(
            "Perform a comprehensive database health triage: "
            "1) Check alert log for recent errors, "
            "2) Look for blocking sessions, "
            "3) Check tablespace usage. "
            "Summarize all findings with priority recommendations."
        )
    
    def new_conversation(self, thread_id: Optional[str] = None) -> str:
        """Start a new conversation thread."""
        if thread_id:
            self._thread_id = thread_id
        else:
            self._thread_id = f"healing-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        logger.info(f"New conversation started: {self._thread_id}")
        return self._thread_id


# ============================================================================
# Quick Test Function
# ============================================================================

async def quick_test():
    """Quick test of the Self-Healing Agent."""
    agent = SelfHealingAgent()
    
    print("\n" + "="*60)
    print("Self-Healing Agent Quick Test")
    print("="*60)
    
    print("\n[Test] Asking about database issues...")
    response = await agent.chat("Check for any blocking sessions in the database")
    print(f"\nResponse:\n{response}")
    
    return response


if __name__ == "__main__":
    asyncio.run(quick_test())
