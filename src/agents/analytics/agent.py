"""
BRM Analytics Agent for ODAOS CLI.

LangGraph-based agent for generating business analytics visualizations
from natural language queries. Displays charts directly in terminal.

SUPPORTED VISUALIZATIONS:
1. Pie Chart - Customer Distribution by Region
2. Pie Chart - Product Market Share
3. Pie Chart - Revenue by Service Type
4. Heatmap - Overdue Balance vs ARPU
5. Heatmap - Service Usage by Time
6. Heatmap - Churn Risk by Region
7. Scatter Plot - ARPU vs Churn Probability
8. Heatmap - Complaints vs Billing Errors
"""
import asyncio
import os
import sys
from typing import Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from src.core.providers import create_llm

# ============================================================================
# Analytics System Prompt
# ============================================================================

ANALYTICS_SYSTEM_PROMPT = """You are an Analytics Assistant for Oracle BRM (Billing and Revenue Management).
Your role is to help users visualize billing data through natural language commands.
Charts are displayed directly in the terminal with live data from the database.

AVAILABLE VISUALIZATIONS:

PIE CHARTS:
1. pie_customer_by_region - Customer distribution by country/region
2. pie_product_market_share - Product market share by subscriptions
3. pie_revenue_by_service - Revenue composition by service type

HEATMAPS:
4. heatmap_overdue_arpu - Overdue balance vs ARPU (high-risk customers)
5. heatmap_usage_time - Service usage intensity by time of day
6. heatmap_churn_region - Churn risk by geographic region
7. heatmap_complaints - Complaints vs billing errors by region

SCATTER PLOTS:
8. scatter_arpu_churn - ARPU vs churn probability (top 5% at risk highlighted)

Always call the appropriate tool to generate the chart.
"""


# ============================================================================
# Terminal Charts Singleton
# ============================================================================

_charts_instance = None

async def _get_charts():
    """Get initialized terminal charts instance."""
    global _charts_instance
    if _charts_instance is None:
        from scripts.terminal_charts import TerminalCharts
        _charts_instance = TerminalCharts()
        await _charts_instance.initialize()
    return _charts_instance


def _run_chart_async(chart_func):
    """Run async chart function and return result."""
    async def run():
        charts = await _get_charts()
        return await chart_func(charts)
    return asyncio.run(run())


# ============================================================================
# Tool Definitions - PIE CHARTS
# ============================================================================

@tool
def show_customer_distribution_pie() -> str:
    """Create a pie chart of customer distribution by region.
    
    Derives region from account billing address attributes.
    
    Use when user asks about:
    - Customer distribution by region
    - Geographic customer breakdown
    - Where are our customers
    - Customer by country
    """
    return _run_chart_async(lambda c: c.pie_customer_by_region())


@tool  
def show_product_market_share_pie() -> str:
    """Generate a pie chart showing market share by product category.
    
    Uses product definitions from PDC and revenue attribution from PIN.
    
    Use when user asks about:
    - Product market share
    - Which products are popular
    - Product distribution
    - Subscription breakdown
    """
    return _run_chart_async(lambda c: c.pie_product_market_share())


@tool
def show_revenue_by_service_pie() -> str:
    """Visualize revenue composition by service type as a pie chart.
    
    Maps revenue events to service classes or usage types.
    
    Use when user asks about:
    - Revenue by service type
    - Service revenue breakdown
    - Which services generate revenue
    """
    return _run_chart_async(lambda c: c.pie_revenue_by_service_type())


# ============================================================================
# Tool Definitions - HEATMAPS
# ============================================================================

@tool
def show_overdue_vs_arpu_heatmap() -> str:
    """Produce a heatmap of overdue balance vs. ARPU to identify high-risk customers.
    
    - Overdue balance: using open items or unpaid balances
    - ARPU: using rolling revenue averages
    
    Use when user asks about:
    - Overdue balance vs ARPU
    - High-risk customers
    - Payment risk analysis
    - Customer risk identification
    """
    return _run_chart_async(lambda c: c.heatmap_overdue_vs_arpu())


@tool
def show_usage_by_time_heatmap() -> str:
    """Generate a heatmap of service usage intensity by time of day.
    
    Aggregates usage events from ECE or rated events from PIN.
    
    Use when user asks about:
    - Usage by time of day
    - Service usage intensity
    - Peak usage hours
    - Time-based usage patterns
    """
    return _run_chart_async(lambda c: c.heatmap_usage_by_time())


@tool
def show_churn_by_region_heatmap() -> str:
    """Visualize churn risk by region in a heatmap.
    
    Correlates churn indicators with geographic attributes.
    Churn proxy: Accounts inactive > 60 days.
    
    Use when user asks about:
    - Churn risk by region
    - Regional churn analysis
    - At-risk customers by location
    - Geographic churn patterns
    """
    return _run_chart_async(lambda c: c.heatmap_churn_by_region())


@tool
def show_complaints_vs_errors_heatmap() -> str:
    """Generate a heatmap of customer complaints vs. billing errors by region.
    
    Uses adjustment/dispute records as proxy for complaints.
    Note: No dedicated complaint table in BRM schema.
    
    Use when user asks about:
    - Complaints vs billing errors
    - Adjustments by region
    - Billing disputes
    - Customer complaints
    """
    return _run_chart_async(lambda c: c.heatmap_complaints_vs_errors())


# ============================================================================
# Tool Definitions - SCATTER PLOTS
# ============================================================================

@tool
def show_arpu_vs_churn_scatter() -> str:
    """Create a scatter plot of ARPU vs. churn probability.
    
    Highlights the top 5% high-value customers at risk.
    Churn probability derived from: days inactive / 180 days.
    
    Use when user asks about:
    - ARPU vs churn probability
    - High-value at-risk customers
    - Revenue at risk
    - Churn scatter analysis
    """
    return _run_chart_async(lambda c: c.scatter_arpu_vs_churn())


# ============================================================================
# Tool Definitions - LINE CHARTS
# ============================================================================

@tool
def show_customer_acquisition_trend() -> str:
    """Display a line chart showing customer acquisition trends over time.
    
    Use when user asks about:
    - Customer acquisition
    - New customers over time
    - Growth trends
    """
    return _run_chart_async(lambda c: c.line_customer_acquisition())


@tool
def show_revenue_growth_trend() -> str:
    """Display a line chart showing monthly revenue growth.
    
    Use when user asks about:
    - Revenue trends
    - Monthly revenue
    - Revenue growth
    """
    return _run_chart_async(lambda c: c.line_revenue_growth())


@tool
def list_available_analytics() -> str:
    """List all available analytics visualizations with example queries.
    
    Use when user asks:
    - What analytics are available
    - What charts can you show
    - Help with analytics
    """
    return """
**📊 Available Analytics Visualizations (Real-time from BRM Database):**

**PIE CHARTS 🥧**
| Visualization | Example Query |
|---------------|---------------|
| Customer by Region | "Create a pie chart of customer distribution by region" |
| Product Market Share | "Generate a pie chart showing market share by product" |
| Revenue by Service | "Visualize revenue composition by service type" |

**HEATMAPS 🔥**
| Visualization | Example Query |
|---------------|---------------|
| Overdue vs ARPU | "Produce a heatmap of overdue balance vs ARPU" |
| Usage by Time | "Generate a heatmap of service usage by time of day" |
| Churn by Region | "Visualize churn risk by region in a heatmap" |
| Complaints/Errors | "Generate a heatmap of complaints vs billing errors" |

**SCATTER PLOTS 📈**
| Visualization | Example Query |
|---------------|---------------|
| ARPU vs Churn | "Create a scatter plot of ARPU vs churn probability" |

**LINE CHARTS 📉**
| Visualization | Example Query |
|---------------|---------------|
| Acquisition Trend | "Show customer acquisition trends" |
| Revenue Growth | "Display monthly revenue growth" |
"""


ANALYTICS_TOOLS = [
    # Pie Charts
    show_customer_distribution_pie,
    show_product_market_share_pie,
    show_revenue_by_service_pie,
    # Heatmaps
    show_overdue_vs_arpu_heatmap,
    show_usage_by_time_heatmap,
    show_churn_by_region_heatmap,
    show_complaints_vs_errors_heatmap,
    # Scatter Plots
    show_arpu_vs_churn_scatter,
    # Line Charts
    show_customer_acquisition_trend,
    show_revenue_growth_trend,
    # Help
    list_available_analytics,
]


# ============================================================================
# Analytics Agent Class
# ============================================================================

class AnalyticsAgent:
    """LangGraph-based Analytics Agent for BRM data visualization."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        temperature: float = 0.3,
        enable_memory: bool = True,
    ):
        """Initialize the Analytics Agent."""
        self.llm = create_llm(
            provider=provider,
            temperature=temperature,
            max_tokens=2048
        )
        
        self.memory = MemorySaver() if enable_memory else None
        
        self.agent = create_react_agent(
            self.llm,
            ANALYTICS_TOOLS,
            checkpointer=self.memory,
            prompt=ANALYTICS_SYSTEM_PROMPT,
        )
        
        self.thread_id = f"analytics-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    async def chat(
        self, 
        message: str, 
        thread_id: Optional[str] = None,
    ) -> str:
        """Send a message to the agent and get a response."""
        config = {"configurable": {"thread_id": thread_id or self.thread_id}}
        
        try:
            response = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            
            if response and "messages" in response:
                for msg in reversed(response["messages"]):
                    if isinstance(msg, AIMessage) and msg.content:
                        return msg.content
            
            return "I processed your request but couldn't generate a response."
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat_sync(self, message: str, thread_id: Optional[str] = None) -> str:
        """Synchronous version of chat."""
        return asyncio.run(self.chat(message, thread_id))
    
    def new_conversation(self, thread_id: Optional[str] = None) -> str:
        """Start a new conversation thread."""
        self.thread_id = thread_id or f"analytics-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return self.thread_id


if __name__ == "__main__":
    async def test():
        agent = AnalyticsAgent()
        print(await agent.chat("What analytics are available?"))
    asyncio.run(test())
