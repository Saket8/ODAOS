"""
Terminal Charts Module for ODAOS CLI.

Renders charts directly in the terminal using plotext library.
Queries live data from BRM database and displays inline.

Supported Visualizations:
1. Pie chart (simulated) - Customer by Region
2. Pie chart (simulated) - Product Market Share
3. Pie chart (simulated) - Revenue by Service Type
4. Heatmap - Overdue Balance vs ARPU
5. Heatmap - Service Usage by Time
6. Heatmap - Churn Risk by Region
7. Scatter - ARPU vs Churn Probability
8. Heatmap - Complaints vs Billing Errors
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import plotext as plt
from src.database.connection import get_connection_manager


class TerminalCharts:
    """Renders charts directly in the terminal from live BRM data."""
    
    def __init__(self):
        self.manager = None
        
    async def initialize(self):
        """Initialize database connection."""
        self.manager = get_connection_manager()
        await self.manager.initialize()
    
    # ==========================================================================
    # PIE CHARTS (Simulated with horizontal bar + percentages)
    # ==========================================================================
    
    async def pie_customer_by_region(self) -> str:
        """
        Create a pie chart of customer distribution by region.
        Derives region from account billing address attributes.
        """
        query = """
        SELECT 
            NVL(COUNTRY, 'Unknown') as region,
            COUNT(*) as customer_count
        FROM PIN.ACCOUNT_NAMEINFO_T
        GROUP BY COUNTRY
        ORDER BY customer_count DESC
        FETCH FIRST 8 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        regions = [r['REGION'][:12] for r in result]
        counts = [r['CUSTOMER_COUNT'] for r in result]
        total = sum(counts)
        
        # Build pie-style output
        plt.clear_figure()
        plt.simple_bar(regions, counts, title="🥧 Customer Distribution by Region", width=60)
        chart = plt.build()
        plt.clear_figure()
        
        # Add percentage breakdown
        breakdown = "\n**Percentage Breakdown:**\n"
        for i, (region, count) in enumerate(zip(regions, counts)):
            pct = (count / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 5)
            breakdown += f"  {region}: {bar} {pct:.1f}% ({count})\n"
        
        return f"""
{chart}
{breakdown}
**Data Source:** PIN.ACCOUNT_NAMEINFO_T
**Total Customers:** {total}
"""

    async def pie_product_market_share(self) -> str:
        """
        Generate a pie chart showing market share by product category.
        Uses product definitions from PDC and revenue attribution from PIN.
        """
        query = """
        SELECT 
            NVL(p.NAME, 'Unknown') as product_name,
            COUNT(pp.POID_ID0) as subscription_count
        FROM PIN.PURCHASED_PRODUCT_T pp
        LEFT JOIN PIN.PRODUCT_T p ON pp.PRODUCT_OBJ_ID0 = p.POID_ID0
        GROUP BY p.NAME
        ORDER BY subscription_count DESC
        FETCH FIRST 8 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        products = [r['PRODUCT_NAME'][:18] if r['PRODUCT_NAME'] else 'Unknown' for r in result]
        counts = [r['SUBSCRIPTION_COUNT'] for r in result]
        total = sum(counts)
        
        plt.clear_figure()
        plt.simple_bar(products, counts, title="🥧 Product Market Share", width=60)
        chart = plt.build()
        plt.clear_figure()
        
        breakdown = "\n**Market Share Breakdown:**\n"
        for product, count in zip(products, counts):
            pct = (count / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 5)
            breakdown += f"  {product}: {bar} {pct:.1f}%\n"
        
        return f"""
{chart}
{breakdown}
**Data Source:** PIN.PURCHASED_PRODUCT_T + PRODUCT_T
**Total Subscriptions:** {total}
"""

    async def pie_revenue_by_service_type(self) -> str:
        """
        Visualize revenue composition by service type as a pie chart.
        Maps revenue events to service classes or usage types.
        """
        query = """
        SELECT 
            REGEXP_REPLACE(POID_TYPE, '^/item/', '') as service_type,
            COUNT(*) as transaction_count,
            SUM(DUE) as revenue
        FROM PIN.ITEM_T
        GROUP BY REGEXP_REPLACE(POID_TYPE, '^/item/', '')
        ORDER BY transaction_count DESC
        FETCH FIRST 8 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        services = [r['SERVICE_TYPE'][:15] for r in result]
        counts = [r['TRANSACTION_COUNT'] for r in result]
        total = sum(counts)
        
        plt.clear_figure()
        plt.simple_bar(services, counts, title="🥧 Revenue by Service Type", width=60)
        chart = plt.build()
        plt.clear_figure()
        
        breakdown = "\n**Service Type Breakdown:**\n"
        for service, count in zip(services, counts):
            pct = (count / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 5)
            breakdown += f"  {service}: {bar} {pct:.1f}%\n"
        
        return f"""
{chart}
{breakdown}
**Data Source:** PIN.ITEM_T
**Total Transactions:** {total}
"""

    # ==========================================================================
    # HEATMAPS
    # ==========================================================================

    async def heatmap_overdue_vs_arpu(self) -> str:
        """
        Produce a heatmap of overdue balance vs. ARPU to identify high-risk customers.
        - Overdue balance: using open items or unpaid balances
        - ARPU: using rolling revenue averages
        """
        query = """
        SELECT 
            a.POID_ID0 as account_id,
            NVL(SUM(i.DUE), 0) as arpu,
            NVL(SUM(CASE WHEN i.DUE > 0 THEN i.DUE ELSE 0 END), 0) as overdue
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ITEM_T i ON a.POID_ID0 = i.ACCOUNT_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY a.POID_ID0
        FETCH FIRST 100 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        arpu_values = [float(r['ARPU'] or 0) for r in result]
        overdue_values = [float(r['OVERDUE'] or 0) for r in result]
        
        plt.clear_figure()
        plt.scatter(arpu_values, overdue_values, marker="dot")
        plt.title("🔥 Overdue Balance vs ARPU (High-Risk Identification)")
        plt.xlabel("ARPU (Average Revenue)")
        plt.ylabel("Overdue Balance")
        plt.plotsize(60, 15)
        chart = plt.build()
        plt.clear_figure()
        
        # Identify high-risk (high ARPU + high overdue)
        high_risk = sum(1 for a, o in zip(arpu_values, overdue_values) if a > 0 and o > 0)
        
        return f"""
{chart}
**Risk Analysis:**
- Total Accounts Analyzed: {len(result)}
- High-Risk (ARPU>0 & Overdue>0): {high_risk}
- Proxy Logic: Overdue = open items with positive due amount
- Data Source: PIN.ACCOUNT_T + ITEM_T
"""

    async def heatmap_usage_by_time(self) -> str:
        """
        Generate a heatmap of service usage intensity by time of day and service type.
        Aggregates usage events from rated events in PIN.
        
        NOTE: ECE.RATEDEVENT is empty, using PIN.EVENT_T as fallback.
        """
        query = """
        SELECT 
            TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'HH24') as hour_of_day,
            REGEXP_REPLACE(POID_TYPE, '^/event/', '') as event_type,
            COUNT(*) as event_count
        FROM PIN.EVENT_T
        GROUP BY 
            TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'HH24'),
            REGEXP_REPLACE(POID_TYPE, '^/event/', '')
        ORDER BY hour_of_day, event_count DESC
        FETCH FIRST 50 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        # Group by hour
        hour_data = {}
        for r in result:
            hour = r['HOUR_OF_DAY'] or '00'
            count = r['EVENT_COUNT']
            hour_data[hour] = hour_data.get(hour, 0) + count
        
        hours = sorted(hour_data.keys())
        counts = [hour_data[h] for h in hours]
        
        plt.clear_figure()
        plt.bar(hours, counts, width=0.8)
        plt.title("📊 Service Usage Intensity by Hour")
        plt.xlabel("Hour of Day")
        plt.ylabel("Event Count")
        plt.plotsize(60, 12)
        chart = plt.build()
        plt.clear_figure()
        
        peak_hour = max(hour_data, key=hour_data.get) if hour_data else "N/A"
        
        return f"""
{chart}
**Usage Analysis:**
- Peak Hour: {peak_hour}:00
- Total Events: {sum(counts)}
- Note: Using PIN.EVENT_T (ECE.RATEDEVENT is empty)
- Data Source: PIN.EVENT_T
"""

    async def heatmap_churn_by_region(self) -> str:
        """
        Visualize churn risk by region in a heatmap.
        Correlates churn indicators with geographic attributes.
        
        Churn Proxy: Accounts with no billing activity > 60 days
        """
        query = """
        SELECT 
            NVL(ni.COUNTRY, 'Unknown') as region,
            COUNT(*) as total_customers,
            SUM(CASE WHEN (SYSDATE - TO_DATE('1970-01-01','YYYY-MM-DD') - a.MOD_T/86400) > 60 THEN 1 ELSE 0 END) as at_risk
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ACCOUNT_NAMEINFO_T ni ON a.POID_ID0 = ni.OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY ni.COUNTRY
        ORDER BY total_customers DESC
        FETCH FIRST 6 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        regions = [r['REGION'][:12] for r in result]
        totals = [r['TOTAL_CUSTOMERS'] for r in result]
        at_risk = [r['AT_RISK'] for r in result]
        
        plt.clear_figure()
        plt.simple_multiple_bar(
            regions, 
            [totals, at_risk],
            title="🔥 Churn Risk by Region",
            width=60,
            labels=["Total", "At-Risk"]
        )
        chart = plt.build()
        plt.clear_figure()
        
        # Risk percentages
        risk_info = "\n**Churn Risk by Region:**\n"
        for region, total, risk in zip(regions, totals, at_risk):
            pct = (risk / total * 100) if total > 0 else 0
            risk_info += f"  {region}: {risk}/{total} ({pct:.1f}% at risk)\n"
        
        return f"""
{chart}
{risk_info}
**Churn Proxy:** Accounts inactive >60 days
**Data Source:** PIN.ACCOUNT_T + ACCOUNT_NAMEINFO_T
"""

    # ==========================================================================
    # SCATTER PLOTS
    # ==========================================================================

    async def scatter_arpu_vs_churn(self) -> str:
        """
        Create a scatter plot of ARPU vs. churn probability.
        Highlights the top 5% high-value customers at risk.
        
        Churn probability derived from:
        - Days since last activity / 180 (capped at 1.0)
        """
        query = """
        SELECT 
            a.POID_ID0 as account_id,
            NVL(SUM(i.DUE), 0) as arpu,
            (SYSDATE - TO_DATE('1970-01-01','YYYY-MM-DD') - a.MOD_T/86400) as days_inactive
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ITEM_T i ON a.POID_ID0 = i.ACCOUNT_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY a.POID_ID0, a.MOD_T
        FETCH FIRST 200 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        arpu_values = [float(r['ARPU'] or 0) for r in result]
        # Churn probability = days_inactive / 180, capped at 1.0
        churn_prob = [min(float(r['DAYS_INACTIVE'] or 0) / 180, 1.0) for r in result]
        
        plt.clear_figure()
        plt.scatter(arpu_values, churn_prob, marker="dot")
        plt.title("📈 ARPU vs Churn Probability")
        plt.xlabel("ARPU (Average Revenue)")
        plt.ylabel("Churn Probability")
        plt.plotsize(60, 15)
        
        # Add threshold line at 50%
        plt.hline(0.5, "red")
        
        chart = plt.build()
        plt.clear_figure()
        
        # Find top 5% high-value at risk
        high_arpu_threshold = sorted(arpu_values, reverse=True)[max(1, len(arpu_values)//20)] if arpu_values else 0
        high_value_at_risk = sum(1 for a, c in zip(arpu_values, churn_prob) if a >= high_arpu_threshold and c >= 0.5)
        
        return f"""
{chart}
**Analysis:**
- Total Customers: {len(result)}
- High-Value At Risk (Top 5% ARPU + Churn>50%): {high_value_at_risk}
- Red Line: 50% Churn Threshold
- Churn Proxy: Days inactive / 180 days
- Data Source: PIN.ACCOUNT_T + ITEM_T
"""

    async def heatmap_complaints_vs_errors(self) -> str:
        """
        Generate a heatmap of customer complaints vs. billing errors by region.
        
        Uses adjustment records as proxy for complaints/errors.
        Note: No dedicated complaint table found in BRM schema.
        """
        query = """
        SELECT 
            NVL(ni.COUNTRY, 'Unknown') as region,
            COUNT(DISTINCT a.POID_ID0) as customer_count,
            COUNT(CASE WHEN i.POID_TYPE LIKE '%adjustment%' THEN 1 END) as adjustments,
            COUNT(CASE WHEN i.POID_TYPE LIKE '%dispute%' THEN 1 END) as disputes
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ACCOUNT_NAMEINFO_T ni ON a.POID_ID0 = ni.OBJ_ID0
        LEFT JOIN PIN.ITEM_T i ON a.POID_ID0 = i.ACCOUNT_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY ni.COUNTRY
        ORDER BY customer_count DESC
        FETCH FIRST 6 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        regions = [r['REGION'][:12] for r in result]
        customers = [r['CUSTOMER_COUNT'] for r in result]
        adjustments = [r['ADJUSTMENTS'] for r in result]
        
        plt.clear_figure()
        plt.simple_multiple_bar(
            regions,
            [customers, adjustments],
            title="📊 Complaints/Adjustments by Region",
            width=60,
            labels=["Customers", "Adjustments"]
        )
        chart = plt.build()
        plt.clear_figure()
        
        return f"""
{chart}
**Analysis:**
- Proxy Logic: Using adjustment/dispute records as complaint indicator
- Note: No dedicated complaint table found in BRM
- Data Source: PIN.ACCOUNT_T + ITEM_T + ACCOUNT_NAMEINFO_T

**Regions Analyzed:**
{chr(10).join(f"  {r}: {c} customers, {a} adjustments" for r, c, a in zip(regions, customers, adjustments))}
"""

    # ==========================================================================
    # LINE CHARTS
    # ==========================================================================

    async def line_customer_acquisition(self) -> str:
        """Display line chart of customer acquisition trends over time."""
        query = """
        SELECT 
            TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'YYYY-MM') as month,
            COUNT(*) as new_customers
        FROM PIN.ACCOUNT_T
        GROUP BY TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'YYYY-MM')
        ORDER BY month
        """
        
        result = await self.manager.execute_query(query)
        
        months = [r['MONTH'] for r in result]
        customers = [r['NEW_CUSTOMERS'] for r in result]
        
        plt.clear_figure()
        plt.plot(customers, marker="braille")
        plt.title("📈 Customer Acquisition Trend")
        plt.xlabel("Time Period")
        plt.ylabel("New Customers")
        plt.xticks(range(len(months)), months)
        plt.plotsize(60, 15)
        chart = plt.build()
        plt.clear_figure()
        
        total = sum(customers)
        peak_idx = customers.index(max(customers)) if customers else 0
        peak_month = months[peak_idx] if months else "N/A"
        peak_count = max(customers) if customers else 0
        
        return f"""
{chart}
**Key Insights:**
- Total Customers Acquired: {total}
- Peak Acquisition: {peak_month} ({peak_count} customers)
- Data Source: PIN.ACCOUNT_T
"""

    async def line_revenue_growth(self) -> str:
        """Display line chart of monthly revenue growth."""
        query = """
        SELECT 
            TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + b.CREATED_T/86400, 'YYYY-MM') as month,
            SUM(b.CURRENT_TOTAL) as revenue
        FROM PIN.BILL_T b
        GROUP BY TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + b.CREATED_T/86400, 'YYYY-MM')
        ORDER BY month
        """
        
        result = await self.manager.execute_query(query)
        
        months = [r['MONTH'] for r in result]
        revenue = [float(r['REVENUE'] or 0) for r in result]
        
        plt.clear_figure()
        plt.plot(revenue, marker="braille")
        plt.title("📈 Monthly Revenue Growth")
        plt.xlabel("Time Period")
        plt.ylabel("Revenue")
        plt.xticks(range(len(months)), months)
        plt.plotsize(60, 15)
        chart = plt.build()
        plt.clear_figure()
        
        total = sum(revenue)
        
        return f"""
{chart}
**Key Insights:**
- Total Revenue: {total:.2f}
- Months Covered: {len(months)}
- Note: Test data may show negative values
- Data Source: PIN.BILL_T
"""


# Singleton instance
_terminal_charts = None

async def get_terminal_charts():
    """Get or create terminal charts instance."""
    global _terminal_charts
    if _terminal_charts is None:
        _terminal_charts = TerminalCharts()
        await _terminal_charts.initialize()
    return _terminal_charts


async def test_charts():
    """Test all terminal chart types."""
    charts = await get_terminal_charts()
    
    print("=" * 70)
    print("TESTING: Pie Chart - Customer by Region")
    print("=" * 70)
    print(await charts.pie_customer_by_region())
    
    print("\n" + "=" * 70)
    print("TESTING: Scatter Plot - ARPU vs Churn")
    print("=" * 70)
    print(await charts.scatter_arpu_vs_churn())
    
    print("\n" + "=" * 70)
    print("TESTING: Heatmap - Churn Risk by Region")
    print("=" * 70)
    print(await charts.heatmap_churn_by_region())


if __name__ == "__main__":
    asyncio.run(test_charts())
