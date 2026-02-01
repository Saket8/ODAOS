"""Cost Optimization LangGraph Agent.

LangGraph-based agent for OCI cost analysis and optimization recommendations.
Uses the Cost Optimization MCP Server tools with Groq LLM.

Usage:
    from src.agents.cost_optimization.agent import CostOptimizationAgent
    
    agent = CostOptimizationAgent()
    response = await agent.chat("How much are we spending on OCI this month?")
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
from ...mcp_servers.cost_optimization.server import (
    get_oci_costs_handler,
    analyze_compute_handler,
    list_idle_resources_handler,
    forecast_costs_handler,
)

logger = logging.getLogger(__name__)

# ============================================================================
# System Prompt
# ============================================================================

COST_OPTIMIZATION_AGENT_PROMPT = """You are an expert Cloud FinOps Analyst specializing in Oracle Cloud Infrastructure (OCI) cost optimization.
Your job is to analyze cloud spending, identify savings opportunities, and provide actionable recommendations.

When analyzing costs:
1. Start with current spending trends and comparisons
2. Identify the biggest cost drivers
3. Look for underutilized resources that can be rightsized
4. Find idle resources that can be cleaned up
5. Project future costs and compare to budgets

For each finding:
- Quantify the potential savings ($)
- Explain the business impact
- Provide specific actionable steps
- Prioritize by impact vs effort

Response Format:
💰 **Cost Summary**: Current spending overview
📊 **Analysis**: Detailed breakdown by service/resource
🎯 **Savings Opportunities**: Ranked by potential impact
📈 **Forecast**: Future cost projections
✅ **Recommendations**: Prioritized action items

Financial Reporting Guidelines:
- Always show costs in USD with proper formatting ($X,XXX.XX)
- Calculate monthly and annual projections
- Compare to budgets when available
- Highlight cost increases above 10%

Available Tools:
- get_oci_costs: Get spending breakdown by service/compartment
- analyze_compute_utilization: Find underutilized resources
- list_idle_resources: Find stopped/unused resources
- forecast_costs: Project future spending
"""


# ============================================================================
# Tool Definitions (LangChain-compatible wrappers)
# ============================================================================

@tool
async def get_oci_costs(days: int = 30, group_by: str = "service") -> str:
    """Get OCI cost breakdown and trends.
    
    Args:
        days: Number of days to analyze (1-90, default 30)
        group_by: Group by 'service' or 'compartment'
    
    Returns spending breakdown, daily trends, and cost insights.
    Use to understand where money is being spent.
    """
    import json
    result = await get_oci_costs_handler(days, group_by)
    return json.dumps(result, indent=2, default=str)


@tool
async def analyze_compute_utilization(threshold: int = 30) -> str:
    """Analyze compute and database resource utilization.
    
    Args:
        threshold: CPU threshold for underutilized (default 30%)
    
    Finds underutilized resources and calculates potential savings
    from rightsizing. Use to find cost reduction opportunities.
    """
    import json
    result = await analyze_compute_handler(None, threshold)
    return json.dumps(result, indent=2, default=str)


@tool
async def list_idle_resources() -> str:
    """Find idle and unused OCI resources.
    
    Identifies stopped compute instances, unattached block volumes,
    and orphan boot volumes. Returns cleanup recommendations with
    cost savings estimates.
    """
    import json
    result = await list_idle_resources_handler(None)
    return json.dumps(result, indent=2, default=str)


@tool
async def forecast_costs(days_ahead: int = 30, budget_amount: Optional[float] = None) -> str:
    """Forecast future OCI costs based on current trends.
    
    Args:
        days_ahead: Days to forecast (7-90, default 30)
        budget_amount: Optional monthly budget for comparison
    
    Projects future spending and compares to budget if provided.
    Use for budget planning and cost projections.
    """
    import json
    result = await forecast_costs_handler(days_ahead, budget_amount)
    return json.dumps(result, indent=2, default=str)


# All available tools
COST_OPTIMIZATION_TOOLS = [
    get_oci_costs,
    analyze_compute_utilization,
    list_idle_resources,
    forecast_costs,
]


# ============================================================================
# Cost Optimization Agent Class
# ============================================================================

class CostOptimizationAgent:
    """LangGraph-based Cost Optimization Agent."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        temperature: float = 0.0,
        enable_memory: bool = True,
    ):
        """Initialize the Cost Optimization Agent."""
        self.llm = create_llm(provider=provider, temperature=temperature)
        self.memory = MemorySaver() if enable_memory else None
        
        self.agent = create_react_agent(
            model=self.llm,
            tools=COST_OPTIMIZATION_TOOLS,
            prompt=COST_OPTIMIZATION_AGENT_PROMPT,
            checkpointer=self.memory,
        )
        
        self._thread_id = "cost-optimization-agent-default"
        logger.info("Cost Optimization Agent initialized")
    
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
    
    async def generate_cost_report(self, budget: Optional[float] = None) -> str:
        """Generate a comprehensive cost optimization report."""
        prompt = (
            "Generate a comprehensive cost optimization report: "
            "1) Current spending by service, "
            "2) Underutilized resources, "
            "3) Idle resources to clean up, "
            "4) 30-day cost forecast"
        )
        if budget:
            prompt += f", 5) Compare to monthly budget of ${budget:,.2f}"
        
        return await self.chat(prompt)
    
    def new_conversation(self, thread_id: Optional[str] = None) -> str:
        """Start a new conversation thread."""
        if thread_id:
            self._thread_id = thread_id
        else:
            self._thread_id = f"cost-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        logger.info(f"New conversation started: {self._thread_id}")
        return self._thread_id


# ============================================================================
# Quick Test Function
# ============================================================================

async def quick_test():
    """Quick test of the Cost Optimization Agent."""
    agent = CostOptimizationAgent()
    
    print("\n" + "="*60)
    print("Cost Optimization Agent Quick Test")
    print("="*60)
    
    print("\n[Test] Asking about OCI costs...")
    response = await agent.chat("What are our top 3 cost categories?")
    print(f"\nResponse:\n{response}")
    
    return response


if __name__ == "__main__":
    asyncio.run(quick_test())
