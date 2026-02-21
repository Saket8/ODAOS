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
Charts are generated using live data from the database and rendered as ASCII/ANSI art in the terminal.

### CRITICAL RULES:
1. **NEVER OMIT THE CHART**: When you call a visualization tool, you MUST include the FULL chart output (the ASCII art) in your final response.
2. **USE CODE BLOCKS**: Always wrap the ASCII chart output in triple backticks (```) so it renders correctly with fixed-width fonts.
3. **RESPECT CHART TYPE**: If the user asks for a "pie chart", pass `chart_type='pie'` to the tool. If they ask for a "bar chart", pass `chart_type='bar'`. Default to 'pie' if unspecified for region/market/service breakdowns.
4. **DO NOT SUMMARIZE ONLY**: While you should provide a brief analysis of the data, the chart itself is the primary deliverable. Do not replace the chart with a text summary.

### Response Template:
"Here is the visualization for [User Request]:

```
[INSERT FULL CHART OUTPUT HERE]
```

[Provide 2-3 bullet points of analysis/insights]"

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

LINE CHARTS:
9. show_customer_acquisition_trend - Customer acquisition over time
10. show_revenue_growth_trend - Monthly revenue growth

Always call the appropriate tool to generate the chart and present the result as specified above.
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
def show_customer_distribution_pie(chart_type: str = "pie") -> str:
    """Create a pie chart or bar chart of customer distribution by region.
    
    Args:
        chart_type: The type of chart to generate ('pie' or 'bar').
    
    Derives region from account billing address attributes.
    """
    return _run_chart_async(lambda c: c.pie_customer_by_region(chart_type))


@tool  
def show_product_market_share_pie(chart_type: str = "pie") -> str:
    """Generate a pie chart or bar chart showing market share by product category.
    
    Args:
        chart_type: The type of chart to generate ('pie' or 'bar').
        
    Uses product definitions from PDC and revenue attribution from PIN.
    """
    return _run_chart_async(lambda c: c.pie_product_market_share(chart_type))


@tool
def show_revenue_by_service_pie(chart_type: str = "pie") -> str:
    """Visualize revenue composition by service type as a chart.
    
    Args:
        chart_type: The type of chart to generate ('pie' or 'bar').
        
    Maps revenue events to service classes or usage types.
    """
    return _run_chart_async(lambda c: c.pie_revenue_by_service_type(chart_type))


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
        self._data_service = None
    
    async def _get_data_service(self):
        """Get DataService instance."""
        if self._data_service is None:
            from src.api.services.data_service import get_data_service
            self._data_service = get_data_service()
        return self._data_service
    
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
    
    async def get_viz_data(self, query: str, preferred_chart_type: str = "auto", thread_id: Optional[str] = None) -> dict:
        """
        Return structured chart data for web (Plotly) rendering.
        
        Uses LLM-powered query understanding to determine:
        1. What data to fetch (customer, revenue, product, etc.)
        2. What chart type to use (pie, bar, line, etc.)
        3. Appropriate title and narrative
        
        Args:
            query: Natural language query from user
            preferred_chart_type: Override chart type if specified
            thread_id: Thread ID for conversation context
        
        Returns:
            Dict with: chart_type, title, data, narrative, data_source
        """
        config = {"configurable": {"thread_id": thread_id or self.thread_id}}
        
        # Determine data type and chart type using LLM to handle context (e.g. "same data")
        intent = await self._detect_intent_with_llm(query, config)
        
        data_type = intent.get("data_type", "customer_region")
        chart_type = preferred_chart_type if preferred_chart_type != "auto" else intent.get("chart_type", "auto")
        
        # Fetch data from DataService
        data_service = await self._get_data_service()
        result = await data_service.get_data_for_query(data_type)
        
        # Final chart type selection
        final_chart_type = chart_type if chart_type != "auto" else result.suggested_chart_type
        
        # Generate narrative from data
        narrative = self._generate_data_narrative(result.data, result.title)
        
        return {
            "chart_type": final_chart_type,
            "title": result.title,
            "data": result.data,
            "data_source": result.data_source,
            "insight": result.insight,
            "narrative": narrative,
            "x_axis_label": result.x_axis_label,
            "y_axis_label": result.y_axis_label
        }

    async def _detect_intent_with_llm(self, query: str, config: dict) -> dict:
        """Use LLM to detect data_type and chart_type from query and context."""
        system_msg = """Identify the user's visualization intent. 
        Available data_types: 
        - 'customer_region' (regional distribution)
        - 'revenue_trends' (monthly metrics)
        - 'revenue_service' (service breakdown)
        - 'product_share' (product popularity)
        - 'usage_time' (temporal activity)
        - 'churn_region' (geographic risk)
        - 'arpu_churn' (correlation between revenue and risk)
        - 'complaints' (service issues)
        - 'top_accounts' (highest revenue customers)
        - 'revenue_leakage' (unbilled usage, leakage)
        - 'customer_churn' (churn rate trends)
        - 'acquisition_trend' (new signups, acquisition)
        - 'customer_segments' (segmentation by arpu/tenure)
        - 'overdue_payments' (aging buckets, overdue)
        - 'payment_methods' (credit card, channels)
        - 'failed_payments' (payment failures)
        - 'payment_recon' (reconciliation, matched)
        - 'bill_cycle' (billing cycle success)
        - 'provisioning_queue' (service orders, provisioning)
        - 'rating_performance' (throughput, latency)

        Available chart_types: 'pie', 'bar', 'line', 'scatter', 'heatmap', 'auto'.

        CRITICAL DIRECTION:
        1. If the query starts with 'show me', 'what is', or mentions a specific metric (revenue, churn, arpu), PRIORITIZE the current query over previous context.
        2. ONLY use previous context if the user says 'same data', 'that one', 'as well', or 'how about [chart_type]'.
        3. 'ARPU vs Churn' or 'Correlation' MUST return 'arpu_churn' and 'scatter'.

        Return ONLY a JSON object: {"data_type": "...", "chart_type": "..."}"""

        try:
            # We'll read history but let the LLM decide priority
            history = []
            if self.memory:
                state = await self.agent.aget_state(config)
                if state and "messages" in state.values:
                    # Get last 3 messages for context (don't over-context)
                    history = state.values["messages"][-3:]
            
            messages = [SystemMessage(content=system_msg)]
            if history:
                messages.extend(history)
            
            # Ensure the current query is the last human message
            if not history or history[-1].content != query:
                messages.append(HumanMessage(content=query))
            
            print(f"[AnalyticsAgent] Detecting intent for: {query}")
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            # Basic cleanup of LLM output
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                intent = json.loads(json_match.group(0))
                print(f"[AnalyticsAgent] Detected intent: {intent}")
                return intent
            
            # Fallback to key-word matching
            fallback = {
                "data_type": self._detect_data_type(query.lower()),
                "chart_type": self._detect_chart_type(query.lower(), "auto")
            }
            print(f"[AnalyticsAgent] Fallback intent: {fallback}")
            return fallback
        except Exception as e:
            print(f"[AnalyticsAgent] Intent detection failed: {e}")
            return {"data_type": self._detect_data_type(query.lower()), "chart_type": "auto"}

    def _detect_data_type(self, query: str) -> str:
        """Fallback keyword-based data type detection."""
        q = query.lower()
        if any(word in q for word in ["payment method", "channel"]): return "payment_methods"
        if any(word in q for word in ["overdue payment", "aging"]): return "overdue_payments"
        if any(word in q for word in ["failed payment", "root cause"]): return "failed_payments"
        if any(word in q for word in ["reconciliation", "unmatched"]): return "payment_recon"
        if any(word in q for word in ["leakage", "unbilled"]): return "revenue_leakage"
        if any(word in q for word in ["top", "highest revenue"]): return "top_accounts"
        if any(word in q for word in ["acquisition", "new customer"]): return "acquisition_trend"
        if any(word in q for word in ["segmentation", "tenure"]): return "customer_segments"
        if any(word in q for word in ["bill cycle", "success rate", "errors"]): return "bill_cycle"
        if any(word in q for word in ["provisioning", "queue"]): return "provisioning_queue"
        if any(word in q for word in ["rating engine", "throughput"]): return "rating_performance"
        if any(word in q for word in ["customer churn analysis", "churn rate trend"]): return "customer_churn"
        
        if any(word in q for word in ["customer", "region", "country", "distribution"]): return "customer_region"
        if any(word in q for word in ["revenue trend", "growth", "monthly"]): return "revenue_trends"
        if any(word in q for word in ["revenue by service", "service revenue"]): return "revenue_service"
        if any(word in q for word in ["product", "market share", "subscription"]): return "product_share"
        if any(word in q for word in ["usage", "time of day", "peak"]): return "usage_time"
        if any(word in q for word in ["churn", "risk", "inactive"]):
            if any(word in q for word in ["arpu", "scatter", "scatter plot", "correlation"]): return "arpu_churn"
            return "churn_region"
        if any(word in q for word in ["arpu", "scatter"]): return "arpu_churn"
        if any(word in q for word in ["complaint", "adjustment", "error", "issue"]): return "complaints"
        return "revenue_trends"

    def _detect_chart_type(self, query: str, preferred: str) -> str:
        """Fallback keyword-based chart type detection."""
        if preferred != "auto": return preferred
        q = query.lower()
        if "pie" in q: return "pie"
        if "bar" in q: return "bar"
        if "line" in q: return "line"
        if "scatter" in q: return "scatter"
        if "heatmap" in q: return "heatmap"
        return "auto"
    
    def _generate_data_narrative(self, data: list, title: str) -> dict:
        """Generate narrative insights from data."""
        if not data:
            return {
                "summary": f"No data available for {title}.",
                "key_insights": ["Database returned zero records."],
                "recommendations": ["Check if the data range exists in the current environment."]
            }
        
        # Calculate stats for standard charts
        values = [d.get('value', d.get('y', 0)) for d in data]
        total = sum(values)
        
        # Handle all-zero case
        if total == 0 and len(data) > 0:
            return {
                "summary": f"Data retrieved for {title.lower()} is currently at baseline (zero).",
                "key_insights": [
                    "All monitored segments are showing zero activity.",
                    f"Sampled {len(data)} segments with no variance."
                ],
                "recommendations": [
                    "Verify if event processing is active.",
                    "Review filter criteria for potential over-restriction."
                ]
            }
            
        max_val = max(values) if values else 0
        max_idx = values.index(max_val) if values else 0
        top_label = data[max_idx].get('label') or data[max_idx].get('month', 'Top segment')
        top_pct = (max_val / total * 100) if total > 0 else 0
        
        return {
            "summary": f"Analysis of {title.lower()} from live Oracle BRM database.",
            "key_insights": [
                f"{top_label} leads with {top_pct:.1f}% ({max_val:,.0f} total)" if total > 0 else "Baseline data detected",
                f"Total aggregated value: {total:,.0f}",
                f"Dataset contains {len(data)} distinct data points"
            ],
            "recommendations": [
                f"Prioritize resources for {top_label}" if total > 0 else "Verify data ingestion pipelines",
                "Monitor for further variance over coming periods"
            ]
        }
        
        # Handle all-zero case
        if total == 0 and len(data) > 0:
            return {
                "summary": f"Data retrieved for {title.lower()} is currently at baseline (zero).",
                "key_insights": [
                    "All monitored segments are showing zero activity.",
                    f"Sampled {len(data)} segments with no variance."
                ],
                "recommendations": [
                    "Verify if event processing is active.",
                    "Review filter criteria for potential over-restriction."
                ]
            }
            
        max_val = max(values) if values else 0
        max_idx = values.index(max_val) if values else 0
        top_label = data[max_idx].get('label') or data[max_idx].get('month', 'Top segment')
        top_pct = (max_val / total * 100) if total > 0 else 0
        
        return {
            "summary": f"Analysis of {title.lower()} from live Oracle BRM database.",
            "key_insights": [
                f"{top_label} leads with {top_pct:.1f}% ({max_val:,.0f} total)" if total > 0 else "Baseline data detected",
                f"Total aggregated value: {total:,.0f}",
                f"Dataset contains {len(data)} distinct data points"
            ],
            "recommendations": [
                f"Prioritize resources for {top_label}" if total > 0 else "Verify data ingestion pipelines",
                "Monitor for further variance over coming periods"
            ]
        }
    
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


