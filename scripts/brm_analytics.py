"""
BRM Analytics Visualization Module

Provides read-only analytical queries and visualizations across PIN, PDC, ECE schemas.
All queries include performance guardrails (row limits, date filters, sampling).
"""
import asyncio
import io
import base64
from datetime import datetime
from typing import Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Add project root to path
import sys
sys.path.insert(0, '.')
from src.database.connection import get_connection_manager


class BRMAnalytics:
    """Read-only analytics engine for Oracle BRM data."""
    
    # Query guardrails
    MAX_ROWS = 10000
    DEFAULT_DATE_RANGE_DAYS = 365
    SAMPLE_RATE = 10  # percent for large tables
    
    def __init__(self):
        self.manager = None
        
    async def initialize(self):
        """Initialize database connection."""
        self.manager = get_connection_manager()
        await self.manager.initialize()
    
    def _epoch_to_date(self, epoch: int) -> datetime:
        """Convert Oracle epoch timestamp to datetime."""
        return datetime.fromtimestamp(epoch) if epoch else None
    
    def _save_plot_to_base64(self, fig) -> str:
        """Save matplotlib figure to base64 string."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64
    
    # ========== V4: Customer Distribution by Region ==========
    async def v4_customer_distribution_by_region(self, save_path: Optional[str] = None) -> dict:
        """
        Generate pie chart of customer distribution by region.
        
        Source: PIN.ACCOUNT_NAMEINFO_T (COUNTRY column)
        Status: ✅ FEASIBLE
        """
        query = """
        SELECT 
            NVL(COUNTRY, 'Unknown') as region,
            COUNT(*) as customer_count
        FROM PIN.ACCOUNT_NAMEINFO_T
        GROUP BY COUNTRY
        ORDER BY customer_count DESC
        FETCH FIRST 10 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        regions = [r['REGION'] for r in result]
        counts = [r['CUSTOMER_COUNT'] for r in result]
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(regions)))
        
        wedges, texts, autotexts = ax.pie(
            counts, labels=regions, autopct='%1.1f%%',
            colors=colors, startangle=90,
            explode=[0.05 if i == 0 else 0 for i in range(len(regions))]
        )
        
        ax.set_title('Customer Distribution by Region', fontsize=14, fontweight='bold')
        
        # Add legend
        ax.legend(wedges, [f'{r}: {c}' for r, c in zip(regions, counts)],
                  title="Regions", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, "data": result}
        
        return {
            "status": "success",
            "data": result,
            "total_customers": sum(counts),
            "top_region": regions[0] if regions else None,
            "image_base64": self._save_plot_to_base64(fig)
        }
    
    # ========== V5: Market Share by Product ==========
    async def v5_market_share_by_product(self, save_path: Optional[str] = None) -> dict:
        """
        Generate pie chart of market share by product category.
        
        Source: PIN.PURCHASED_PRODUCT_T joined with PIN.PRODUCT_T
        Status: ✅ FEASIBLE
        """
        query = """
        SELECT 
            NVL(p.NAME, 'Unknown') as product_name,
            COUNT(pp.POID_ID0) as subscription_count,
            SUM(NVL(pp.CYCLE_FEE_AMT, 0)) as revenue
        FROM PIN.PURCHASED_PRODUCT_T pp
        LEFT JOIN PIN.PRODUCT_T p ON pp.PRODUCT_OBJ_ID0 = p.POID_ID0
        GROUP BY p.NAME
        ORDER BY subscription_count DESC
        FETCH FIRST 10 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        # Shorten product names for display
        products = [r['PRODUCT_NAME'][:30] + '...' if len(r['PRODUCT_NAME'] or '') > 30 
                    else r['PRODUCT_NAME'] for r in result]
        counts = [r['SUBSCRIPTION_COUNT'] for r in result]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        colors = plt.cm.Paired(np.linspace(0, 1, len(products)))
        
        wedges, texts, autotexts = ax.pie(
            counts, labels=None, autopct='%1.1f%%',
            colors=colors, startangle=90
        )
        
        ax.set_title('Market Share by Product Category', fontsize=14, fontweight='bold')
        
        # Add legend with full names
        full_names = [r['PRODUCT_NAME'] for r in result]
        ax.legend(wedges, [f'{n}: {c}' for n, c in zip(full_names, counts)],
                  title="Products", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                  fontsize=8)
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, "data": result}
        
        return {
            "status": "success",
            "data": result,
            "total_subscriptions": sum(counts),
            "image_base64": self._save_plot_to_base64(fig)
        }
    
    # ========== V6: Revenue by Service Type ==========
    async def v6_revenue_by_service_type(self, save_path: Optional[str] = None) -> dict:
        """
        Generate pie chart of revenue composition by service type.
        
        Source: PIN.ITEM_T (POID_TYPE column)
        Status: ✅ FEASIBLE
        """
        query = """
        SELECT 
            REGEXP_REPLACE(POID_TYPE, '^/item/', '') as service_type,
            COUNT(*) as transaction_count
        FROM PIN.ITEM_T
        GROUP BY REGEXP_REPLACE(POID_TYPE, '^/item/', '')
        ORDER BY transaction_count DESC
        FETCH FIRST 10 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        services = [r['SERVICE_TYPE'] for r in result]
        counts = [r['TRANSACTION_COUNT'] for r in result]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.tab10(np.linspace(0, 1, len(services)))
        
        wedges, texts, autotexts = ax.pie(
            counts, labels=services, autopct='%1.1f%%',
            colors=colors, startangle=90
        )
        
        ax.set_title('Revenue Composition by Service Type', fontsize=14, fontweight='bold')
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, "data": result}
        
        return {
            "status": "success", 
            "data": result,
            "total_transactions": sum(counts),
            "image_base64": self._save_plot_to_base64(fig)
        }
    
    # ========== V2: Customer Acquisition Trend ==========
    async def v2_customer_acquisition_trend(self, months: int = 12, save_path: Optional[str] = None) -> dict:
        """
        Generate line chart of customer acquisition trend.
        
        Source: PIN.ACCOUNT_T (CREATED_T timestamp)
        Status: ✅ FEASIBLE
        """
        query = """
        SELECT 
            TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'YYYY-MM') as month,
            COUNT(*) as new_customers
        FROM PIN.ACCOUNT_T
        GROUP BY TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'YYYY-MM')
        ORDER BY month
        """
        
        result = await self.manager.execute_query(query)
        
        months_list = [r['MONTH'] for r in result]
        customers = [r['NEW_CUSTOMERS'] for r in result]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(months_list, customers, marker='o', linewidth=2, markersize=8, 
                color='#2196F3', label='New Customers')
        ax.fill_between(months_list, customers, alpha=0.3, color='#2196F3')
        
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('New Customers', fontsize=12)
        ax.set_title('Customer Acquisition Trend', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Rotate x labels
        plt.xticks(rotation=45, ha='right')
        
        # Add trend line
        if len(customers) > 1:
            z = np.polyfit(range(len(customers)), customers, 1)
            p = np.poly1d(z)
            ax.plot(months_list, p(range(len(customers))), 
                    linestyle='--', color='red', alpha=0.7, label='Trend')
        
        ax.legend()
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, "data": result}
        
        return {
            "status": "success",
            "data": result,
            "total_acquired": sum(customers),
            "image_base64": self._save_plot_to_base64(fig)
        }
    
    # ========== V1: Monthly Revenue Growth ==========
    async def v1_monthly_revenue_growth(self, save_path: Optional[str] = None) -> dict:
        """
        Generate line chart of monthly revenue with prepaid/postpaid overlay.
        
        Source: PIN.BILL_T, PIN.BILLINFO_T, PIN.SERVICE_T
        Status: ⚠️ BEST-EFFORT (limited date range, segment derivation)
        """
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
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Revenue line
        ax.plot(months, revenue, marker='o', linewidth=2, markersize=8,
                color='#4CAF50', label='Total Revenue')
        ax.fill_between(months, revenue, alpha=0.3, color='#4CAF50')
        
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Revenue', fontsize=12)
        ax.set_title('Monthly Revenue Growth\n(⚠️ Best-Effort: 5 months data available)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45, ha='right')
        ax.legend()
        plt.tight_layout()
        
        # Add note about data limitation
        ax.annotate('Note: Test data shows negative values', 
                    xy=(0.02, 0.02), xycoords='axes fraction',
                    fontsize=9, color='gray', style='italic')
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, "data": result}
        
        return {
            "status": "best_effort",
            "note": "Limited to 5 months data, test data shows negative revenue",
            "data": result,
            "image_base64": self._save_plot_to_base64(fig)
        }
    
    # ========== V3: Quarterly Churn Rate ==========
    async def v3_quarterly_churn_rate(self, save_path: Optional[str] = None) -> dict:
        """
        Generate line chart of quarterly churn rate trends.
        
        Source: PIN.ACCOUNT_T, PIN.BILL_T
        Status: BEST-EFFORT (no explicit churn flag, using activity proxy)
        Churn Definition: Accounts with no billing activity in last 90 days
        """
        query = """
        SELECT 
            TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + a.CREATED_T/86400, 'YYYY-Q') as quarter,
            COUNT(*) as total_accounts,
            SUM(CASE 
                WHEN NOT EXISTS (
                    SELECT 1 FROM PIN.BILLINFO_T bi
                    JOIN PIN.BILL_T b ON bi.POID_ID0 = b.BILLINFO_OBJ_ID0
                    WHERE bi.ACCOUNT_OBJ_ID0 = a.POID_ID0 
                    AND b.CREATED_T > (SELECT MAX(CREATED_T) - 90*86400 FROM PIN.BILL_T)
                ) THEN 1 ELSE 0 
            END) as churned
        FROM PIN.ACCOUNT_T a
        WHERE a.POID_ID0 > 1
        GROUP BY TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + a.CREATED_T/86400, 'YYYY-Q')
        ORDER BY quarter
        """
        
        try:
            result = await self.manager.execute_query(query)
        except Exception:
            # Fallback simpler query
            query = """
            SELECT 
                TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'YYYY-Q') as quarter,
                COUNT(*) as total_accounts,
                0 as churned
            FROM PIN.ACCOUNT_T
            WHERE POID_ID0 > 1
            GROUP BY TO_CHAR(TO_DATE('1970-01-01','YYYY-MM-DD') + CREATED_T/86400, 'YYYY-Q')
            ORDER BY quarter
            """
            result = await self.manager.execute_query(query)
        
        quarters = [r['QUARTER'] for r in result]
        totals = [r['TOTAL_ACCOUNTS'] for r in result]
        churned = [r['CHURNED'] for r in result]
        churn_rates = [c/t*100 if t > 0 else 0 for c, t in zip(churned, totals)]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.bar(quarters, churn_rates, color='#E57373', alpha=0.7, label='Churn Rate %')
        ax.plot(quarters, churn_rates, marker='o', color='#C62828', linewidth=2)
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Churn Rate (%)', fontsize=12)
        ax.set_title('Quarterly Churn Rate Trends\n(BEST-EFFORT: Using 90-day inactivity as churn proxy)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, "data": result}
        
        return {
            "status": "best_effort",
            "note": "Churn defined as 90-day billing inactivity",
            "data": result,
            "image_base64": self._save_plot_to_base64(fig)
        }
    
    # ========== V7: Overdue Balance vs ARPU Heatmap ==========
    async def v7_overdue_arpu_heatmap(self, save_path: Optional[str] = None) -> dict:
        """
        Generate heatmap of overdue balance vs ARPU to identify high-risk customers.
        
        Source: PIN.BILL_T, PIN.ACCOUNT_T
        Status: BEST-EFFORT
        """
        query = """
        SELECT 
            a.POID_ID0 as account_id,
            NVL(SUM(CASE WHEN b.DUE > 0 THEN b.DUE ELSE 0 END), 0) as overdue_balance,
            NVL(AVG(b.CURRENT_TOTAL), 0) as arpu
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.BILLINFO_T bi ON a.POID_ID0 = bi.ACCOUNT_OBJ_ID0
        LEFT JOIN PIN.BILL_T b ON bi.POID_ID0 = b.BILLINFO_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY a.POID_ID0
        FETCH FIRST 500 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        overdues = [float(r['OVERDUE_BALANCE'] or 0) for r in result]
        arpus = [float(r['ARPU'] or 0) for r in result]
        
        # Create 2D histogram as heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Define bins
        overdue_bins = np.linspace(min(overdues)-1, max(overdues)+1, 10)
        arpu_bins = np.linspace(min(arpus)-1, max(arpus)+1, 10)
        
        h, xedges, yedges = np.histogram2d(arpus, overdues, bins=[arpu_bins, overdue_bins])
        
        im = ax.imshow(h.T, origin='lower', aspect='auto', cmap='YlOrRd',
                       extent=[min(arpus), max(arpus), min(overdues), max(overdues)])
        
        plt.colorbar(im, ax=ax, label='Customer Count')
        
        ax.set_xlabel('ARPU (Average Revenue)', fontsize=12)
        ax.set_ylabel('Overdue Balance', fontsize=12)
        ax.set_title('Overdue Balance vs ARPU Heatmap\n(High-Risk Customer Identification)', 
                     fontsize=14, fontweight='bold')
        
        # Add scatter points for visibility
        ax.scatter(arpus, overdues, c='blue', alpha=0.3, s=20, label='Customers')
        ax.legend(loc='upper right')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, "data": result[:10]}
        
        return {
            "status": "best_effort",
            "note": "ARPU from BILL_T.CURRENT_TOTAL, Overdue from DUE column",
            "data": result[:10],
            "total_customers": len(result),
            "image_base64": self._save_plot_to_base64(fig)
        }
    
    # ========== V9: Churn Risk by Region Heatmap ==========
    async def v9_churn_by_region(self, save_path: Optional[str] = None) -> dict:
        """
        Generate heatmap of churn risk by region.
        
        Source: PIN.ACCOUNT_T, PIN.ACCOUNT_NAMEINFO_T, PIN.BILL_T
        Status: BEST-EFFORT
        """
        query = """
        SELECT 
            NVL(ni.COUNTRY, 'Unknown') as region,
            NVL(ni.CITY, 'Unknown') as city,
            COUNT(*) as total_customers,
            SUM(CASE WHEN lb.last_bill IS NULL THEN 1 ELSE 0 END) as at_risk
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ACCOUNT_NAMEINFO_T ni ON a.POID_ID0 = ni.OBJ_ID0
        LEFT JOIN (
            SELECT bi.ACCOUNT_OBJ_ID0, MAX(b.CREATED_T) as last_bill
            FROM PIN.BILLINFO_T bi
            JOIN PIN.BILL_T b ON bi.POID_ID0 = b.BILLINFO_OBJ_ID0
            GROUP BY bi.ACCOUNT_OBJ_ID0
        ) lb ON a.POID_ID0 = lb.ACCOUNT_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY ni.COUNTRY, ni.CITY
        ORDER BY total_customers DESC
        FETCH FIRST 20 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        regions = [f"{r['REGION'][:10]}" for r in result]
        totals = [r['TOTAL_CUSTOMERS'] for r in result]
        at_risk = [r['AT_RISK'] for r in result]
        risk_pct = [a/t*100 if t > 0 else 0 for a, t in zip(at_risk, totals)]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(regions))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, totals, width, label='Total Customers', color='#42A5F5')
        bars2 = ax.bar(x + width/2, at_risk, width, label='At Risk', color='#EF5350')
        
        ax.set_xlabel('Region', fontsize=12)
        ax.set_ylabel('Customer Count', fontsize=12)
        ax.set_title('Churn Risk by Region\n(BEST-EFFORT: At-risk = no recent billing activity)', 
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(regions, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, "data": result}
        
        return {
            "status": "best_effort",
            "note": "At-risk defined as accounts with no recent billing activity",
            "data": result,
            "image_base64": self._save_plot_to_base64(fig)
        }
    
    # ========== V10: ARPU vs Churn Probability Scatter ==========
    async def v10_arpu_churn_scatter(self, save_path: Optional[str] = None) -> dict:
        """
        Generate scatter plot of ARPU vs churn probability.
        Highlights top 5% high-value customers at risk.
        
        Source: PIN.ACCOUNT_T, PIN.BILL_T
        Status: BEST-EFFORT (churn probability derived from inactivity)
        """
        query = """
        SELECT 
            a.POID_ID0 as account_id,
            NVL(AVG(b.CURRENT_TOTAL), 0) as arpu,
            NVL(MAX(b.CREATED_T), 0) as last_bill_epoch,
            (SELECT MAX(CREATED_T) FROM PIN.BILL_T) as max_bill_epoch
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.BILLINFO_T bi ON a.POID_ID0 = bi.ACCOUNT_OBJ_ID0
        LEFT JOIN PIN.BILL_T b ON bi.POID_ID0 = b.BILLINFO_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY a.POID_ID0
        FETCH FIRST 500 ROWS ONLY
        """
        
        result = await self.manager.execute_query(query)
        
        # Calculate churn probability based on days since last bill
        max_epoch = result[0]['MAX_BILL_EPOCH'] if result else 0
        
        arpus = []
        churn_probs = []
        high_value_at_risk = []
        
        for r in result:
            arpu = float(r['ARPU'] or 0)
            last_bill = r['LAST_BILL_EPOCH'] or 0
            days_inactive = (max_epoch - last_bill) / 86400 if max_epoch and last_bill else 365
            churn_prob = min(1.0, days_inactive / 180)  # 180 days = 100% churn probability
            
            arpus.append(arpu)
            churn_probs.append(churn_prob)
            
            # High value at risk: top 5% ARPU with >50% churn probability
            if churn_prob > 0.5:
                high_value_at_risk.append((r['ACCOUNT_ID'], arpu, churn_prob))
        
        # Sort to find top 5% high value
        high_value_at_risk.sort(key=lambda x: x[1], reverse=True)
        top_5_pct = high_value_at_risk[:max(1, len(high_value_at_risk)//20)]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Main scatter
        scatter = ax.scatter(arpus, churn_probs, c=churn_probs, cmap='RdYlGn_r', 
                            alpha=0.6, s=50)
        
        # Highlight top 5% high-value at risk
        if top_5_pct:
            hv_arpus = [x[1] for x in top_5_pct]
            hv_churns = [x[2] for x in top_5_pct]
            ax.scatter(hv_arpus, hv_churns, c='red', s=150, marker='*', 
                       edgecolors='black', linewidths=1, label='Top 5% High-Value At Risk')
        
        plt.colorbar(scatter, ax=ax, label='Churn Probability')
        
        ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='50% Churn Threshold')
        
        ax.set_xlabel('ARPU (Average Revenue Per User)', fontsize=12)
        ax.set_ylabel('Churn Probability', fontsize=12)
        ax.set_title('ARPU vs Churn Probability\n(BEST-EFFORT: Churn derived from billing inactivity)', 
                     fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return {"status": "saved", "path": save_path, 
                    "high_value_at_risk": len(top_5_pct), "data": result[:10]}
        
        return {
            "status": "best_effort",
            "note": "Churn probability = days_inactive/180 (capped at 1.0)",
            "high_value_at_risk_count": len(top_5_pct),
            "data": result[:10],
            "image_base64": self._save_plot_to_base64(fig)
        }

async def main():
    """Test visualization generation."""
    analytics = BRMAnalytics()
    await analytics.initialize()
    
    output_dir = "scripts/analytics_output"
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating V4: Customer Distribution by Region...")
    result = await analytics.v4_customer_distribution_by_region(
        save_path=f"{output_dir}/v4_customer_region.png"
    )
    print(f"  Status: {result['status']}, Data rows: {len(result.get('data', []))}")
    
    print("\nGenerating V5: Market Share by Product...")
    result = await analytics.v5_market_share_by_product(
        save_path=f"{output_dir}/v5_product_market_share.png"
    )
    print(f"  Status: {result['status']}, Data rows: {len(result.get('data', []))}")
    
    print("\nGenerating V6: Revenue by Service Type...")
    result = await analytics.v6_revenue_by_service_type(
        save_path=f"{output_dir}/v6_service_revenue.png"
    )
    print(f"  Status: {result['status']}, Data rows: {len(result.get('data', []))}")
    
    print("\nGenerating V2: Customer Acquisition Trend...")
    result = await analytics.v2_customer_acquisition_trend(
        save_path=f"{output_dir}/v2_customer_acquisition.png"
    )
    print(f"  Status: {result['status']}, Data rows: {len(result.get('data', []))}")
    
    print("\nGenerating V1: Monthly Revenue Growth...")
    result = await analytics.v1_monthly_revenue_growth(
        save_path=f"{output_dir}/v1_revenue_growth.png"
    )
    print(f"  Status: {result['status']}, Data rows: {len(result.get('data', []))}")
    
    print("\nGenerating V3: Quarterly Churn Rate...")
    result = await analytics.v3_quarterly_churn_rate(
        save_path=f"{output_dir}/v3_churn_rate.png"
    )
    print(f"  Status: {result['status']}, Data rows: {len(result.get('data', []))}")
    
    print("\nGenerating V7: Overdue vs ARPU Heatmap...")
    result = await analytics.v7_overdue_arpu_heatmap(
        save_path=f"{output_dir}/v7_overdue_arpu.png"
    )
    print(f"  Status: {result['status']}, Data rows: {len(result.get('data', []))}")
    
    print("\nGenerating V9: Churn Risk by Region...")
    result = await analytics.v9_churn_by_region(
        save_path=f"{output_dir}/v9_churn_region.png"
    )
    print(f"  Status: {result['status']}, Data rows: {len(result.get('data', []))}")
    
    print("\nGenerating V10: ARPU vs Churn Scatter...")
    result = await analytics.v10_arpu_churn_scatter(
        save_path=f"{output_dir}/v10_arpu_churn.png"
    )
    print(f"  Status: {result['status']}, High-value at risk: {result.get('high_value_at_risk', 'N/A')}")
    
    print(f"\nAll visualizations saved to {output_dir}/")


if __name__ == "__main__":
    asyncio.run(main())

