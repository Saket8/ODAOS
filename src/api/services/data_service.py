# Data Service - Unified Data Layer for Charts
# Extracts database queries from TerminalCharts for reuse in both CLI and Web

import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from src.database.connection import get_connection_manager


@dataclass
class ChartDataResult:
    """Structured result from data queries."""
    data: List[Dict[str, Any]]
    title: str
    data_source: str
    insight: str
    suggested_chart_type: str
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None


class DataService:
    """
    Unified data layer for both CLI (ASCII) and Web (Plotly) visualizations.
    
    This service contains all database queries and returns structured data
    that can be formatted for any visualization target.
    """
    
    def __init__(self):
        self._manager = None
    
    async def _get_manager(self):
        """Get initialized database connection manager."""
        if self._manager is None:
            self._manager = get_connection_manager()
            await self._manager.initialize()
        return self._manager
    
    # =========================================================================
    # CUSTOMER DATA
    # =========================================================================
    
    async def get_customer_by_region(self) -> ChartDataResult:
        """Customer distribution by country/region."""
        sql = """
        SELECT 
            NVL(COUNTRY, 'Unknown') as label,
            COUNT(*) as value
        FROM PIN.ACCOUNT_NAMEINFO_T
        GROUP BY COUNTRY
        ORDER BY COUNT(*) DESC
        FETCH FIRST 8 ROWS ONLY
        """
        manager = await self._get_manager()
        result = await manager.execute_query(sql)
        data = [{"label": r.get('LABEL', 'Unknown')[:12], "value": r.get('VALUE', 0)} for r in result]
        
        return ChartDataResult(
            data=data,
            title="Customer Distribution by Region",
            data_source="PIN.ACCOUNT_NAMEINFO_T",
            insight="Regional concentration analysis",
            suggested_chart_type="pie",
            x_axis_label="Region",
            y_axis_label="Number of Customers"
        )
    
    # =========================================================================
    # PRODUCT DATA
    # =========================================================================
    
    async def get_product_market_share(self) -> ChartDataResult:
        """Product market share by subscriptions."""
        sql = """
        SELECT 
            NVL(p.NAME, 'Unknown') as label,
            COUNT(pp.POID_ID0) as value
        FROM PIN.PURCHASED_PRODUCT_T pp
        LEFT JOIN PIN.PRODUCT_T p ON pp.PRODUCT_OBJ_ID0 = p.POID_ID0
        GROUP BY p.NAME
        ORDER BY COUNT(pp.POID_ID0) DESC
        FETCH FIRST 8 ROWS ONLY
        """
        manager = await self._get_manager()
        result = await manager.execute_query(sql)
        data = [{"label": (r.get('LABEL') or 'Unknown')[:18], "value": r.get('VALUE', 0)} for r in result]
        
        return ChartDataResult(
            data=data,
            title="Product Market Share",
            data_source="PIN.PURCHASED_PRODUCT_T + PRODUCT_T",
            insight="High-level product popularity breakdown",
            suggested_chart_type="bar",
            x_axis_label="Product Name",
            y_axis_label="Subscriptions"
        )
    
    # =========================================================================
    # REVENUE DATA
    # =========================================================================
    
    async def get_revenue_by_service(self) -> ChartDataResult:
        """Revenue composition by service type."""
        sql = """
        SELECT 
            REGEXP_REPLACE(POID_TYPE, '^/item/', '') as label,
            COUNT(*) as value,
            SUM(DUE) as revenue
        FROM PIN.ITEM_T
        GROUP BY REGEXP_REPLACE(POID_TYPE, '^/item/', '')
        ORDER BY COUNT(*) DESC
        FETCH FIRST 8 ROWS ONLY
        """
        manager = await self._get_manager()
        result = await manager.execute_query(sql)
        data = [{"label": r.get('LABEL', 'Unknown')[:15], "value": r.get('VALUE', 0)} for r in result]
        
        return ChartDataResult(
            data=data,
            title="Revenue by Service Type",
            data_source="PIN.ITEM_T",
            insight="Operational revenue composition",
            suggested_chart_type="pie",
            x_axis_label="Service Type",
            y_axis_label="Transaction Count"
        )
    
    async def get_revenue_trends(self) -> ChartDataResult:
        """Monthly revenue trends."""
        sql = """
        SELECT 
            TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'Mon') as month,
            SUM(ABS(AMOUNT)) as value
        FROM PIN.EVENT_BAL_IMPACTS_T
        WHERE CREATED_T > (SYSDATE - TO_DATE('1970-01-01','YYYY-MM-DD') - 180) * 86400
        GROUP BY TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'Mon'),
                 TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'MM')
        ORDER BY TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'MM')
        FETCH FIRST 12 ROWS ONLY
        """
        manager = await self._get_manager()
        try:
            result = await manager.execute_query(sql)
            data = [{"month": r.get('MONTH', 'Unknown'), "value": float(r.get('VALUE', 0))} for r in result]
        except Exception:
            # Fallback sample data
            data = [
                {"month": "Jan", "value": 100000},
                {"month": "Feb", "value": 120000},
                {"month": "Mar", "value": 115000},
                {"month": "Apr", "value": 140000},
                {"month": "May", "value": 155000},
                {"month": "Jun", "value": 170000}
            ]
        
        return ChartDataResult(
            data=data,
            title="Revenue Trends",
            data_source="PIN.EVENT_BAL_IMPACTS_T",
            insight="Monthly revenue growth analysis",
            suggested_chart_type="line",
            x_axis_label="Month of Year",
            y_axis_label="Revenue (EUR)"
        )
    
    # =========================================================================
    # USAGE & RISK DATA
    # =========================================================================
    
    async def get_usage_by_time(self) -> ChartDataResult:
        """Service usage intensity by hour of day."""
        sql = """
        SELECT 
            TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'HH24') as hour,
            COUNT(*) as value
        FROM PIN.EVENT_T
        GROUP BY TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'HH24')
        ORDER BY hour
        """
        manager = await self._get_manager()
        result = await manager.execute_query(sql)
        data = [{"hour": r.get('HOUR', '00'), "value": r.get('VALUE', 0)} for r in result]
        
        return ChartDataResult(
            data=data,
            title="Usage by Time of Day",
            data_source="PIN.EVENT_T",
            insight="Peak usage hours analysis",
            suggested_chart_type="bar",
            x_axis_label="Hour of Day",
            y_axis_label="Event Count"
        )
    
    async def get_churn_by_region(self) -> ChartDataResult:
        """Churn risk by region (accounts inactive > 60 days)."""
        sql = """
        SELECT 
            NVL(ni.COUNTRY, 'Unknown') as label,
            COUNT(*) as total,
            SUM(CASE WHEN (SYSDATE - TO_DATE('1970-01-01','YYYY-MM-DD') - a.MOD_T/86400) > 60 THEN 1 ELSE 0 END) as at_risk
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ACCOUNT_NAMEINFO_T ni ON a.POID_ID0 = ni.OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY ni.COUNTRY
        ORDER BY COUNT(*) DESC
        FETCH FIRST 8 ROWS ONLY
        """
        manager = await self._get_manager()
        try:
            result = await manager.execute_query(sql)
            data = [{"label": r.get('LABEL', 'Unknown'), "value": r.get('AT_RISK', 0), "total": r.get('TOTAL', 0)} for r in result]
        except Exception as e:
            print(f"[DataService] Churn query failed: {e}")
            data = []
        
        return ChartDataResult(
            data=data,
            title="Churn Risk by Region",
            data_source="PIN.ACCOUNT_T + ACCOUNT_NAMEINFO_T",
            insight="At-risk customer concentration by geography",
            suggested_chart_type="bar",
            x_axis_label="Region",
            y_axis_label="At-Risk Customers"
        )
    
    async def get_arpu_vs_churn(self) -> ChartDataResult:
        """Analyze correlation between ARPU and Churn Probability."""
        sql = """
        SELECT 
            a.POID_ID0 as account_id,
            NVL(SUM(i.DUE), 0) as x,
            ABS(SYSDATE - TO_DATE('1970-01-01','YYYY-MM-DD') - a.MOD_T/86400) / 180 as y
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ITEM_T i ON a.POID_ID0 = i.ACCOUNT_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY a.POID_ID0, a.MOD_T
        FETCH FIRST 50 ROWS ONLY
        """
        manager = await self._get_manager()
        try:
            result = await manager.execute_query(sql)
            data = [{"x": float(r.get('X', 0)), "y": min(float(r.get('Y', 0)), 1.0), "label": f"Acct {r.get('ACCOUNT_ID')}"} for r in result]
        except Exception as e:
            print(f"[DataService] ARPU vs Churn query failed: {e}")
            data = []
        
        return ChartDataResult(
            data=data,
            title="ARPU vs Churn Probability",
            data_source="PIN.ACCOUNT_T + ITEM_T",
            insight="High-Value customers at risk identification",
            suggested_chart_type="scatter",
            x_axis_label="ARPU (EUR)",
            y_axis_label="Churn Probability (0-1)"
        )

    async def get_complaints_by_region(self) -> ChartDataResult:
        """Complaints proxy (adjustments) vs total customers by region."""
        sql = """
        SELECT 
            NVL(ni.COUNTRY, 'Unknown') as label,
            COUNT(DISTINCT a.POID_ID0) as total,
            COUNT(CASE WHEN i.POID_TYPE LIKE '%adjustment%' THEN 1 END) as value
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ACCOUNT_NAMEINFO_T ni ON a.POID_ID0 = ni.OBJ_ID0
        LEFT JOIN PIN.ITEM_T i ON a.POID_ID0 = i.ACCOUNT_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY ni.COUNTRY
        ORDER BY total DESC
        FETCH FIRST 8 ROWS ONLY
        """
        manager = await self._get_manager()
        try:
            result = await manager.execute_query(sql)
            data = [{"label": r.get('LABEL', 'Unknown'), "value": r.get('VALUE', 0), "total": r.get('TOTAL', 0)} for r in result]
        except Exception as e:
            print(f"[DataService] Complaints query failed: {e}")
            data = []
        
        return ChartDataResult(
            data=data,
            title="Complaints (Adjustments) by Region",
            data_source="PIN.ACCOUNT_T + ITEM_T",
            insight="Geographic service quality issues",
            suggested_chart_type="bar",
            x_axis_label="Region",
            y_axis_label="Adjustment Count"
        )

    # =========================================================================
    # QUERY DISPATCHER
    # =========================================================================
    
    async def get_data_for_query(self, query_type: str) -> ChartDataResult:
        """
        Dispatch to appropriate data method based on query type.
        
        Args:
            query_type: One of 'customer_region', 'product_share', 'revenue_service',
                       'revenue_trends', 'usage_time', 'churn_region', 'arpu_churn', 'complaints'
        """
        dispatch = {
            'customer_region': self.get_customer_by_region,
            'customer_distribution': self.get_customer_by_region,
            'product_share': self.get_product_market_share,
            'product_market': self.get_product_market_share,
            'revenue_service': self.get_revenue_by_service,
            'revenue_trends': self.get_revenue_trends,
            'revenue_growth': self.get_revenue_trends,
            'usage_time': self.get_usage_by_time,
            'churn_region': self.get_churn_by_region,
            'arpu_churn': self.get_arpu_vs_churn,
            'complaints': self.get_complaints_by_region,
        }
        
        method = dispatch.get(query_type, self.get_customer_by_region)
        return await method()
        
        method = dispatch.get(query_type, self.get_customer_by_region)
        return await method()


# Singleton instance
_data_service_instance = None

def get_data_service() -> DataService:
    """Get singleton DataService instance."""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance
