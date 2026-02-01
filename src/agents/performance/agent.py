"""Performance LangGraph Agent.

LangGraph-based agent for Oracle Database performance analysis.
Uses the Performance MCP Server tools with Groq LLM.

Usage:
    from src.agents.performance.agent import PerformanceAgent
    
    agent = PerformanceAgent()
    response = await agent.chat("How is my database performing?")
    print(response)
"""
import asyncio
import logging
from typing import Annotated, Optional, Sequence
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from ...core.providers import create_llm
from ...mcp_servers.performance.server import (
    get_database_metrics_handler,
    analyze_top_sql_handler,
    check_tablespace_usage_handler,
)

logger = logging.getLogger(__name__)

# ============================================================================
# System Prompt
# ============================================================================

PERFORMANCE_AGENT_PROMPT = """You are an expert Oracle Database Performance Analyst and DBA assistant.
Your job is to analyze database performance metrics and provide actionable recommendations.

When analyzing performance:
1. Start by checking current metrics to get a baseline
2. Identify any anomalies or concerning trends (high CPU, memory pressure, slow I/O)
3. Analyze top SQL statements if performance issues are detected
4. Check tablespace usage for space-related issues
5. Provide clear, prioritized recommendations

Guidelines:
- Be concise but thorough in your analysis
- Prioritize critical issues over minor concerns
- Always provide specific actionable recommendations
- Explain findings in terms DBAs and management can understand
- Use the appropriate tools to gather data before making recommendations
- Format response with clear sections (Status, Findings, Recommendations)

Available Tools:
- get_database_metrics: Get CPU, memory, session, and I/O statistics
- analyze_top_sql: Find resource-intensive SQL statements with recommendations
- check_tablespace_usage: Check tablespace utilization and alerts

When asked about database health, systematically check all relevant metrics.
When asked about specific issues, focus on the relevant tools.
"""


# ============================================================================
# Tool Definitions (LangChain-compatible wrappers for MCP tools)
# ============================================================================

@tool
async def get_database_metrics() -> str:
    """Get comprehensive Oracle database performance metrics.
    
    Returns current CPU utilization, memory usage, active sessions,
    I/O statistics, and top wait events. Use this to get an overall
    picture of database health.
    """
    import json
    result = await get_database_metrics_handler()
    return json.dumps(result, indent=2, default=str)


@tool
async def analyze_top_sql(top_n: int = 10, order_by: str = "elapsed_time") -> str:
    """Analyze the most resource-intensive SQL statements.
    
    Args:
        top_n: Number of top SQL statements to analyze (1-50, default 10)
        order_by: Metric to order by - elapsed_time, cpu_time, executions, buffer_gets
    
    Returns SQL ID, text, execution statistics, and optimization recommendations
    for the most expensive queries. Use this when investigating slow performance.
    """
    import json
    result = await analyze_top_sql_handler(top_n, order_by)
    return json.dumps(result, indent=2, default=str)


@tool
async def check_tablespace_usage(threshold: int = 85) -> str:
    """Check tablespace usage and identify space issues.
    
    Args:
        threshold: Percentage threshold for alerting (0-100, default 85%)
    
    Returns tablespace utilization with alerts for those exceeding the threshold.
    Categorizes issues as CRITICAL (>95%) or WARNING (>threshold%).
    Use this when checking for space-related problems.
    """
    import json
    result = await check_tablespace_usage_handler(threshold)
    return json.dumps(result, indent=2, default=str)


# All available tools
PERFORMANCE_TOOLS = [get_database_metrics, analyze_top_sql, check_tablespace_usage]


# ============================================================================
# Performance Agent Class
# ============================================================================

class PerformanceAgent:
    """LangGraph-based Performance Analysis Agent."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        temperature: float = 0.0,  # Deterministic for analysis
        enable_memory: bool = True,
    ):
        """Initialize the Performance Agent.
        
        Args:
            provider: LLM provider (groq, ollama, anthropic). Uses env default if None.
            temperature: Model temperature. 0 for deterministic analysis.
            enable_memory: Whether to enable conversation memory.
        """
        # Create LLM
        self.llm = create_llm(provider=provider, temperature=temperature)
        
        # Setup memory
        self.memory = MemorySaver() if enable_memory else None
        
        # Create ReAct agent with tools
        # The prompt parameter accepts a string that becomes a SystemMessage
        self.agent = create_react_agent(
            model=self.llm,
            tools=PERFORMANCE_TOOLS,
            prompt=PERFORMANCE_AGENT_PROMPT,
            checkpointer=self.memory,
        )
        
        # Default thread ID for conversation tracking
        self._thread_id = "performance-agent-default"
        
        logger.info("Performance Agent initialized")
    
    async def chat(
        self, 
        message: str, 
        thread_id: Optional[str] = None,
    ) -> str:
        """Send a message to the agent and get a response.
        
        Args:
            message: User's question or request
            thread_id: Optional thread ID for conversation tracking
        
        Returns:
            Agent's response as a string
        """
        config = {
            "configurable": {
                "thread_id": thread_id or self._thread_id
            }
        }
        
        inputs = {"messages": [HumanMessage(content=message)]}
        
        logger.info(f"Agent processing: {message[:50]}...")
        
        result = await self.agent.ainvoke(inputs, config=config)
        
        # Extract the last AI message
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "I was unable to process your request."
    
    def chat_sync(self, message: str, thread_id: Optional[str] = None) -> str:
        """Synchronous version of chat for simple use cases."""
        return asyncio.run(self.chat(message, thread_id))
    
    async def stream(
        self, 
        message: str, 
        thread_id: Optional[str] = None,
    ):
        """Stream responses from the agent.
        
        Yields chunks of the response as they become available.
        """
        config = {
            "configurable": {
                "thread_id": thread_id or self._thread_id
            }
        }
        
        inputs = {"messages": [HumanMessage(content=message)]}
        
        async for chunk in self.agent.astream(inputs, config=config, stream_mode="messages"):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
    
    def new_conversation(self, thread_id: Optional[str] = None) -> str:
        """Start a new conversation thread.
        
        Args:
            thread_id: Optional custom thread ID. Generates one if not provided.
        
        Returns:
            The thread ID being used
        """
        if thread_id:
            self._thread_id = thread_id
        else:
            self._thread_id = f"perf-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        logger.info(f"New conversation started: {self._thread_id}")
        return self._thread_id


# ============================================================================
# Quick Test Function
# ============================================================================

async def quick_test():
    """Quick test of the Performance Agent."""
    agent = PerformanceAgent()
    
    print("\n" + "="*60)
    print("Performance Agent Quick Test")
    print("="*60)
    
    # Test 1: Basic health check
    print("\n[Test 1] Asking about database health...")
    response = await agent.chat("Give me a quick overview of database performance")
    print(f"\nResponse:\n{response}")
    
    return response


if __name__ == "__main__":
    asyncio.run(quick_test())
