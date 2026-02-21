# Prompt Library Service — SQLite storage + seed data

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from src.api.models.prompt import (
    Prompt,
    PromptSummary,
    PromptCategory,
    PromptParameter,
    PromptExecuteRequest,
    PromptExecuteResponse,
    PromptFavorite,
    PromptHistoryEntry,
    PromptCreate,
    PromptUpdate,
    PromptListResponse,
    FavoriteToggleResponse,
    PromptHistoryResponse,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Prompt Service
# ============================================================================

class PromptService:
    """Manages prompt library storage in SQLite.
    
    Follows the same pattern as SessionService:
    - Raw sqlite3 (no ORM)
    - Auto-create DB file + tables on init
    - Idempotent seed data
    """

    def __init__(self, db_path: str = "data/prompts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ========================================================================
    # Schema Initialization
    # ========================================================================

    def _init_db(self):
        """Initialize SQLite database with all prompt library tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    icon TEXT DEFAULT '📁',
                    sort_order INTEGER DEFAULT 0,
                    parent_category_id TEXT,
                    FOREIGN KEY (parent_category_id) REFERENCES prompt_categories(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_library (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    prompt_template TEXT NOT NULL,
                    parameters TEXT DEFAULT '[]',
                    default_values TEXT DEFAULT '{}',
                    expected_output TEXT,
                    tags TEXT DEFAULT '[]',
                    difficulty_level TEXT DEFAULT 'beginner',
                    estimated_runtime TEXT DEFAULT '< 30s',
                    requires_approval INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    usage_count INTEGER DEFAULT 0,
                    average_runtime REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_prompt_favorites (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES prompt_library(id) ON DELETE CASCADE,
                    UNIQUE(user_id, prompt_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_execution_history (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    parameters_used TEXT DEFAULT '{}',
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running',
                    result_summary TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES prompt_library(id) ON DELETE CASCADE
                )
            """)

            # Indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompts_category
                ON prompt_library(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompts_active
                ON prompt_library(is_active)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_favorites_user
                ON user_prompt_favorites(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_user
                ON prompt_execution_history(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_executed
                ON prompt_execution_history(executed_at)
            """)

            conn.commit()

        # Seed data on first run
        self._seed_categories()
        self._seed_prompts()

    # ========================================================================
    # Seed Data — Categories
    # ========================================================================

    def _seed_categories(self):
        """Seed 9 prompt categories. Idempotent via INSERT OR IGNORE."""
        categories = [
            ("cat-brm-revenue", "BRM_REVENUE", "Revenue Analytics", "Revenue analysis and trending", "💰", 1, None),
            ("cat-brm-customer", "BRM_CUSTOMER", "Customer Insights", "Customer behavior and segmentation", "👥", 2, None),
            ("cat-brm-payment", "BRM_PAYMENT", "Payment Operations", "Payment processing and collections", "💳", 3, None),
            ("cat-brm-operations", "BRM_OPERATIONS", "Business Operations", "General BRM operational queries", "📊", 4, None),
            ("cat-dba-health", "DBA_HEALTH", "Database Health", "Overall database health checks", "🏥", 5, None),
            ("cat-dba-performance", "DBA_PERFORMANCE", "Performance Tuning", "Query and system performance", "⚡", 6, None),
            ("cat-dba-capacity", "DBA_CAPACITY", "Capacity Planning", "Storage, tablespace, and growth", "💾", 7, None),
            ("cat-dba-security", "DBA_SECURITY", "Security & Locks", "Locks, sessions, and security", "🔒", 8, None),
            ("cat-dba-backup", "DBA_BACKUP", "Backup & Recovery", "Backup status and recovery", "🔄", 9, None),
        ]
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """INSERT OR IGNORE INTO prompt_categories
                   (id, name, display_name, description, icon, sort_order, parent_category_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                categories,
            )
            conn.commit()
        logger.info("Seeded %d prompt categories", len(categories))

    # ========================================================================
    # Seed Data — 35 Prompts
    # ========================================================================

    def _seed_prompts(self):
        """Seed 35 prompts (15 BRM + 20 DBA). Idempotent via INSERT OR IGNORE."""
        prompts = self._get_seed_prompts()
        with sqlite3.connect(self.db_path) as conn:
            for p in prompts:
                conn.execute(
                    """INSERT OR REPLACE INTO prompt_library
                       (id, category, title, description, prompt_template,
                        parameters, default_values, expected_output, tags,
                        difficulty_level, estimated_runtime, requires_approval)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        p["id"],
                        p["category"],
                        p["title"],
                        p["description"],
                        p["prompt_template"],
                        json.dumps(p.get("parameters", [])),
                        json.dumps(p.get("default_values", {})),
                        p.get("expected_output"),
                        json.dumps(p.get("tags", [])),
                        p.get("difficulty_level", "beginner"),
                        p.get("estimated_runtime", "< 30s"),
                        1 if p.get("requires_approval", False) else 0,
                    ),
                )
            conn.commit()
        logger.info("Seeded %d prompts", len(prompts))

    def _get_seed_prompts(self) -> List[Dict[str, Any]]:
        """Return all 35 seed prompt definitions."""
        return [
            # ==============================================================
            # BRM REVENUE (4 prompts)
            # ==============================================================
            {
                "id": "brm-revenue-001",
                "category": "BRM_REVENUE",
                "title": "Monthly Revenue Trend",
                "description": "Analyze monthly revenue trends over a specified period with growth rates and forecasting.",
                "prompt_template": "Show the monthly revenue trend for the last {months} months. Include month-over-month growth percentages and highlight any significant changes.\n\nProvide a structured analysis:\n1. DATA TABLE: Present the data in a markdown table with columns: Month, Revenue, MoM Growth %, Trend\n2. TREND ANALYSIS: Describe overall direction, seasonality patterns, and growth/decline periods\n3. KEY INSIGHTS: List 3-5 bullet points highlighting notable findings\n4. RECOMMENDATIONS: Suggest 2-3 actionable items based on the trends",
                "parameters": [
                    {"name": "months", "type": "integer", "description": "Number of months to analyze", "required": True, "default": 12}
                ],
                "default_values": {"months": 12},
                "expected_output": "Table with monthly revenue, MoM growth %, and a line chart",
                "tags": ["revenue", "trend", "monthly", "growth"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "brm-revenue-002",
                "category": "BRM_REVENUE",
                "title": "Revenue by Product Category",
                "description": "Break down revenue by product or service category for a given quarter.",
                "prompt_template": "Show revenue breakdown by product category for {quarter} {year}. Include percentages and compare with the previous quarter.\n\nProvide a structured analysis:\n1. DATA TABLE: Category, Revenue, % Share, QoQ Change\n2. ANALYSIS: Which categories are growing/declining and why\n3. KEY INSIGHTS: Top 3-5 findings about category performance\n4. RECOMMENDATIONS: Focus areas and potential opportunities",
                "parameters": [
                    {"name": "quarter", "type": "enum", "description": "Quarter", "required": True, "default": "Q4", "enum_values": ["Q1", "Q2", "Q3", "Q4"]},
                    {"name": "year", "type": "integer", "description": "Year", "required": True, "default": 2025}
                ],
                "default_values": {"quarter": "Q4", "year": 2025},
                "expected_output": "Pie chart with revenue per category + comparison table",
                "tags": ["revenue", "product", "category", "quarterly"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "brm-revenue-003",
                "category": "BRM_REVENUE",
                "title": "Top Revenue Generating Accounts",
                "description": "Identify the highest revenue-generating customer accounts with usage patterns.",
                "prompt_template": "List the top {count} revenue-generating accounts. Show their total revenue, product mix, and growth trend for the last {months} months.\n\nProvide a structured analysis:\n1. DATA TABLE: Rank, Account, Total Revenue, Primary Products, Growth Rate\n2. CONCENTRATION ANALYSIS: Revenue concentration risk (top 5, top 10 share)\n3. KEY INSIGHTS: Account-level patterns and risks\n4. RECOMMENDATIONS: Retention strategies for top accounts",
                "parameters": [
                    {"name": "count", "type": "integer", "description": "Number of top accounts", "required": True, "default": 20},
                    {"name": "months", "type": "integer", "description": "Period in months", "required": True, "default": 6}
                ],
                "default_values": {"count": 20, "months": 6},
                "expected_output": "Ranked table with revenue, products, and trend indicators",
                "tags": ["revenue", "accounts", "top", "ranking"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "30s - 1min",
            },
            {
                "id": "brm-revenue-004",
                "category": "BRM_REVENUE",
                "title": "Revenue Leakage Detection",
                "description": "Identify potential revenue leakage from unbilled services, rating errors, or discrepancies.",
                "prompt_template": "Analyze billing data for potential revenue leakage. Check for unbilled CDRs, rating mismatches, and service-charge discrepancies over the last {days} days.\n\nProvide a structured analysis:\n1. DATA TABLE: Leakage Type, Affected Records, Estimated Revenue Impact\n2. ROOT CAUSE: Identify patterns or systemic issues causing each leakage type\n3. KEY INSIGHTS: Severity ranking and business impact\n4. RECOMMENDATIONS: Remediation steps prioritized by financial impact",
                "parameters": [
                    {"name": "days", "type": "integer", "description": "Lookback period in days", "required": True, "default": 30}
                ],
                "default_values": {"days": 30},
                "expected_output": "Summary of potential leakage areas with estimated impact",
                "tags": ["revenue", "leakage", "billing", "audit"],
                "difficulty_level": "advanced",
                "estimated_runtime": "1 - 3min",
                "requires_approval": True,
            },

            # ==============================================================
            # BRM CUSTOMER (4 prompts)
            # ==============================================================
            {
                "id": "brm-customer-001",
                "category": "BRM_CUSTOMER",
                "title": "Customer Distribution by Region",
                "description": "Visualize customer distribution across geographical regions with density mapping.",
                "prompt_template": "Show customer distribution by region. Include total counts, percentage share, and growth rate for each region.\n\nProvide a structured analysis:\n1. DATA TABLE: Region, Customer Count, % Share, YoY Growth\n2. GEOGRAPHIC ANALYSIS: Distribution patterns and regional strengths\n3. KEY INSIGHTS: Underserved regions with growth potential\n4. RECOMMENDATIONS: Market expansion priorities",
                "parameters": [],
                "default_values": {},
                "expected_output": "Bar chart with regional distribution + table",
                "tags": ["customer", "region", "distribution", "geography"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "brm-customer-002",
                "category": "BRM_CUSTOMER",
                "title": "Customer Churn Analysis",
                "description": "Analyze customer churn rate, at-risk accounts, and common churn reasons.",
                "prompt_template": "Analyze customer churn over the last {months} months. Show churn rate trend, top {count} reasons for churn, and identify currently at-risk accounts.\n\nProvide a structured analysis:\n1. DATA TABLE: Month, Churned Customers, Churn Rate %, Revenue Lost\n2. CHURN REASON ANALYSIS: Top reasons ranked by frequency and revenue impact\n3. AT-RISK LIST: Currently at-risk accounts with risk indicators\n4. RECOMMENDATIONS: Targeted retention strategies per churn reason",
                "parameters": [
                    {"name": "months", "type": "integer", "description": "Analysis period in months", "required": True, "default": 6},
                    {"name": "count", "type": "integer", "description": "Top N churn reasons", "required": True, "default": 5}
                ],
                "default_values": {"months": 6, "count": 5},
                "expected_output": "Churn rate chart, reason breakdown, at-risk account list",
                "tags": ["customer", "churn", "retention", "risk"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "30s - 1min",
            },
            {
                "id": "brm-customer-003",
                "category": "BRM_CUSTOMER",
                "title": "New Customer Acquisition Trend",
                "description": "Track new customer sign-ups over time with source channel breakdown.",
                "prompt_template": "Show new customer acquisitions over the last {months} months. Break down by acquisition channel and compare with targets.\n\nProvide a structured analysis:\n1. DATA TABLE: Month, New Customers, Channel Breakdown, vs Target %\n2. CHANNEL ANALYSIS: Cost per acquisition and conversion rates by channel\n3. KEY INSIGHTS: Most effective channels and seasonal patterns\n4. RECOMMENDATIONS: Budget allocation adjustments",
                "parameters": [
                    {"name": "months", "type": "integer", "description": "Period in months", "required": True, "default": 12}
                ],
                "default_values": {"months": 12},
                "expected_output": "Line chart with acquisition trend + channel breakdown",
                "tags": ["customer", "acquisition", "growth", "channel"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "brm-customer-004",
                "category": "BRM_CUSTOMER",
                "title": "Customer Segmentation Analysis",
                "description": "Segment customers by ARPU, tenure, and product usage for targeted strategies.",
                "prompt_template": "Perform customer segmentation based on ARPU, tenure, and product usage. Identify the top {count} segments with their characteristics.\n\nProvide a structured analysis:\n1. DATA TABLE: Segment, Size, Avg ARPU, Avg Tenure, Primary Products, Growth Trend\n2. SEGMENT PROFILES: Detailed characteristics and behavior patterns per segment\n3. KEY INSIGHTS: Highest-value segments and underserved opportunities\n4. RECOMMENDATIONS: Targeted strategies per segment",
                "parameters": [
                    {"name": "count", "type": "integer", "description": "Number of segments", "required": True, "default": 5}
                ],
                "default_values": {"count": 5},
                "expected_output": "Segmentation chart with ARPU, size, and characteristics",
                "tags": ["customer", "segmentation", "ARPU", "targeting"],
                "difficulty_level": "advanced",
                "estimated_runtime": "1 - 3min",
            },

            # ==============================================================
            # BRM PAYMENT (4 prompts)
            # ==============================================================
            {
                "id": "brm-payment-001",
                "category": "BRM_PAYMENT",
                "title": "Overdue Payment Analysis",
                "description": "Analyze overdue payments, aging buckets, and collection effectiveness.",
                "prompt_template": "Show overdue payment analysis. Include aging buckets (30/60/90/120+ days), total overdue amount, and top {count} overdue accounts.\n\nProvide a structured analysis:\n1. DATA TABLE: Aging Bucket, Count, Total Amount, % of Total\n2. ACCOUNT LIST: Top overdue accounts with amount, days overdue, contact history\n3. KEY INSIGHTS: Trends in overdue patterns and collection effectiveness\n4. RECOMMENDATIONS: Priority collection actions and process improvements",
                "parameters": [
                    {"name": "count", "type": "integer", "description": "Top N overdue accounts", "required": True, "default": 20}
                ],
                "default_values": {"count": 20},
                "expected_output": "Aging bucket chart, overdue summary, top account list",
                "tags": ["payment", "overdue", "aging", "collections"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "brm-payment-002",
                "category": "BRM_PAYMENT",
                "title": "Payment Method Distribution",
                "description": "Break down payments by method (credit card, bank transfer, etc.) with success rates.",
                "prompt_template": "Show payment method distribution for the last {months} months. Include volume, value, success rate, and failure reasons per method.\n\nProvide a structured analysis:\n1. DATA TABLE: Method, Volume, Total Value, Success Rate %, Top Failure Reason\n2. TREND ANALYSIS: Shifts in payment method preference over time\n3. KEY INSIGHTS: Methods with low success rates requiring attention\n4. RECOMMENDATIONS: Steps to improve success rates and encourage preferred methods",
                "parameters": [
                    {"name": "months", "type": "integer", "description": "Period in months", "required": True, "default": 3}
                ],
                "default_values": {"months": 3},
                "expected_output": "Pie chart with method distribution + success rate table",
                "tags": ["payment", "method", "distribution", "success-rate"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "brm-payment-003",
                "category": "BRM_PAYMENT",
                "title": "Failed Payment Root Cause",
                "description": "Investigate patterns in failed payments and identify systemic issues.",
                "prompt_template": "Analyze failed payments over the last {days} days. Group by failure reason, identify trends, and flag any systemic issues.\n\nProvide a structured analysis:\n1. DATA TABLE: Failure Reason, Count, Total Value, Trend (Up/Down/Stable)\n2. PATTERN ANALYSIS: Time-based patterns (day/hour), customer segments affected\n3. KEY INSIGHTS: Systemic issues vs. one-off failures\n4. RECOMMENDATIONS: Technical fixes and process changes to reduce failures",
                "parameters": [
                    {"name": "days", "type": "integer", "description": "Lookback in days", "required": True, "default": 14}
                ],
                "default_values": {"days": 14},
                "expected_output": "Failure reason breakdown, trend chart, systemic issue flags",
                "tags": ["payment", "failed", "root-cause", "troubleshooting"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "30s - 1min",
            },
            {
                "id": "brm-payment-004",
                "category": "BRM_PAYMENT",
                "title": "Payment Reconciliation Report",
                "description": "Reconcile payments against invoices and flag mismatches or unallocated payments.",
                "prompt_template": "Run payment reconciliation for the last {days} days. Identify unmatched payments, overpayments, underpayments, and unapplied credits.\n\nProvide a structured analysis:\n1. DATA TABLE: Category (Unmatched/Over/Under/Unapplied), Count, Total Amount\n2. DETAIL LIST: Top mismatches with payment and invoice references\n3. KEY INSIGHTS: Common mismatch patterns and root causes\n4. RECOMMENDATIONS: Process improvements and system configuration changes",
                "parameters": [
                    {"name": "days", "type": "integer", "description": "Reconciliation period in days", "required": True, "default": 30}
                ],
                "default_values": {"days": 30},
                "expected_output": "Reconciliation summary with mismatch details and totals",
                "tags": ["payment", "reconciliation", "invoice", "audit"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "30s - 1min",
            },

            # ==============================================================
            # BRM OPERATIONS (3 prompts)
            # ==============================================================
            {
                "id": "brm-ops-001",
                "category": "BRM_OPERATIONS",
                "title": "Bill Cycle Status",
                "description": "Check status of current and recent billing cycles across all bill segments.",
                "prompt_template": "Show the status of billing cycles for the last {count} cycles. Include success rate, error counts, processing time, and any stuck jobs.\n\nProvide a structured analysis:\n1. DATA TABLE: Cycle, Start/End Time, Records Processed, Success Rate, Errors, Duration\n2. TREND ANALYSIS: Processing time and error rate trends across cycles\n3. KEY INSIGHTS: Recurring issues and performance bottlenecks\n4. RECOMMENDATIONS: Optimizations for faster and more reliable bill runs",
                "parameters": [
                    {"name": "count", "type": "integer", "description": "Number of recent cycles", "required": True, "default": 5}
                ],
                "default_values": {"count": 5},
                "expected_output": "Cycle status table with success rates and timing",
                "tags": ["billing", "cycle", "status", "operations"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "brm-ops-002",
                "category": "BRM_OPERATIONS",
                "title": "Service Provisioning Queue",
                "description": "Monitor the service provisioning pipeline for pending, in-progress, and failed orders.",
                "prompt_template": "Show the current service provisioning queue status. Include pending, in-progress, completed, and failed counts for the last {hours} hours.\n\nProvide a structured analysis:\n1. DATA TABLE: Status (Pending/In-Progress/Completed/Failed), Count, Avg Age, Oldest Order\n2. FAILURE ANALYSIS: Top reasons for failed provisioning orders\n3. KEY INSIGHTS: Queue health and throughput capacity\n4. RECOMMENDATIONS: Bottleneck resolution and capacity planning",
                "parameters": [
                    {"name": "hours", "type": "integer", "description": "Lookback in hours", "required": True, "default": 24}
                ],
                "default_values": {"hours": 24},
                "expected_output": "Queue status summary with counts and age of oldest pending",
                "tags": ["provisioning", "queue", "orders", "operations"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "brm-ops-003",
                "category": "BRM_OPERATIONS",
                "title": "Rating Engine Performance",
                "description": "Analyze the BRM rating engine throughput, latency, and error rates.",
                "prompt_template": "Show rating engine performance metrics for the last {days} days. Include throughput (events/sec), average latency, error rate, and peak loads.\n\nProvide a structured analysis:\n1. DATA TABLE: Date, Avg Throughput, Peak Throughput, Avg Latency, Error Rate %\n2. PATTERN ANALYSIS: Peak usage patterns, latency spikes, error correlation\n3. KEY INSIGHTS: Capacity utilization and performance trends\n4. RECOMMENDATIONS: Scaling recommendations and performance tuning",
                "parameters": [
                    {"name": "days", "type": "integer", "description": "Period in days", "required": True, "default": 7}
                ],
                "default_values": {"days": 7},
                "expected_output": "Performance dashboard with throughput, latency, and error charts",
                "tags": ["rating", "performance", "throughput", "latency"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "30s - 1min",
            },

            # ==============================================================
            # DBA HEALTH (4 prompts)
            # ==============================================================
            {
                "id": "dba-health-001",
                "category": "DBA_HEALTH",
                "title": "Database Health Check",
                "description": "Comprehensive database health overview including uptime, alerts, and key metrics.",
                "prompt_template": "Perform a comprehensive health check on the database. Include uptime, alert log warnings, SGA/PGA utilization, active sessions, and overall status.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. HEALTH SUMMARY: Overall status (Healthy/Warning/Critical) with a summary dashboard table showing: Metric, Current Value, Status, Threshold\n2. DETAILED METRICS: Uptime, SGA/PGA hit ratios, active sessions count, alert log warnings\n3. KEY FINDINGS: Top 3-5 observations about database health\n4. RECOMMENDATIONS: Immediate actions and monitoring improvements",
                "parameters": [],
                "default_values": {},
                "expected_output": "Health dashboard with status indicators and key metrics",
                "tags": ["health", "monitoring", "overview", "status"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-health-002",
                "category": "DBA_HEALTH",
                "title": "Alert Log Analysis",
                "description": "Parse and analyze recent Oracle alert log entries for errors and warnings.",
                "prompt_template": "Analyze the alert log for the last {hours} hours. Summarize ORA- errors, warnings, and notable events. Group by severity.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Timestamp, Severity, ORA Code, Message, Occurrence Count\n2. SEVERITY BREAKDOWN: Group errors by severity with counts and trends\n3. KEY FINDINGS: Most critical errors, recurring patterns, anomalies\n4. RECOMMENDATIONS: Remediation steps for top errors",
                "parameters": [
                    {"name": "hours", "type": "integer", "description": "Lookback in hours", "required": True, "default": 24}
                ],
                "default_values": {"hours": 24},
                "expected_output": "Grouped error summary with counts and timestamps",
                "tags": ["alert", "log", "errors", "ORA", "monitoring"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-health-003",
                "category": "DBA_HEALTH",
                "title": "Instance Parameter Review",
                "description": "Review key Oracle instance parameters and highlight non-default settings.",
                "prompt_template": "List all non-default Oracle instance parameters. Flag any settings that deviate from Oracle best practices for a {workload_type} workload.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Parameter Name, Current Value, Default Value, Oracle Recommended, Status (OK/Warning/Critical)\n2. ANALYSIS: Which parameters deviate from best practices and why it matters\n3. KEY FINDINGS: Most impactful misconfigurations\n4. RECOMMENDATIONS: Parameter changes with expected impact",
                "parameters": [
                    {"name": "workload_type", "type": "enum", "description": "Workload type", "required": True, "default": "OLTP", "enum_values": ["OLTP", "OLAP", "Mixed"]}
                ],
                "default_values": {"workload_type": "OLTP"},
                "expected_output": "Parameter table with current values, defaults, and recommendations",
                "tags": ["parameters", "configuration", "tuning", "best-practices"],
                "difficulty_level": "advanced",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-health-004",
                "category": "DBA_HEALTH",
                "title": "Database Uptime Report",
                "description": "Show database uptime, recent restarts, and availability percentage.",
                "prompt_template": "Show database uptime report for the last {days} days. Include startup times, planned/unplanned downtime, and availability percentage.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Date, Event Type (Startup/Shutdown), Time, Duration, Planned/Unplanned\n2. AVAILABILITY SUMMARY: Total uptime %, downtime hours, MTBF, MTTR\n3. KEY FINDINGS: Patterns in downtime, SLA compliance status\n4. RECOMMENDATIONS: Availability improvement suggestions",
                "parameters": [
                    {"name": "days", "type": "integer", "description": "Period in days", "required": True, "default": 30}
                ],
                "default_values": {"days": 30},
                "expected_output": "Uptime summary with availability % and downtime events",
                "tags": ["uptime", "availability", "restart", "SLA"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },

            # ==============================================================
            # DBA PERFORMANCE (4 prompts)
            # ==============================================================
            {
                "id": "dba-perf-001",
                "category": "DBA_PERFORMANCE",
                "title": "Top SQL by Elapsed Time",
                "description": "Identify the most resource-intensive SQL statements consuming the most elapsed time.",
                "prompt_template": "Show the top {count} SQL statements by total elapsed time. Include execution count, average elapsed, buffer gets, and the SQL text.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Rank, SQL ID, Elapsed Time (s), Executions, Avg Elapsed (ms), Buffer Gets, SQL Text (truncated)\n2. ANALYSIS: Common patterns among top SQL, optimization opportunities\n3. KEY FINDINGS: Most impactful queries and their resource consumption\n4. RECOMMENDATIONS: Tuning suggestions for top consumers",
                "parameters": [
                    {"name": "count", "type": "integer", "description": "Top N SQL statements", "required": True, "default": 10}
                ],
                "default_values": {"count": 10},
                "expected_output": "Ranked SQL table with performance metrics",
                "tags": ["SQL", "performance", "elapsed-time", "tuning"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-perf-002",
                "category": "DBA_PERFORMANCE",
                "title": "Wait Event Analysis",
                "description": "Analyze top database wait events to identify performance bottlenecks.",
                "prompt_template": "Show the top {count} wait events for the last {hours} hours. Include total waits, average wait time, and suggested actions.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Rank, Wait Event, Wait Class, Total Waits, Avg Wait (ms), % of Total, Time Waited (s)\n2. ANALYSIS: Wait event patterns, correlations, and root cause indicators\n3. KEY FINDINGS: Dominant bottlenecks and their impact\n4. RECOMMENDATIONS: Specific actions to reduce each top wait event",
                "parameters": [
                    {"name": "count", "type": "integer", "description": "Top N events", "required": True, "default": 10},
                    {"name": "hours", "type": "integer", "description": "Lookback in hours", "required": True, "default": 1}
                ],
                "default_values": {"count": 10, "hours": 1},
                "expected_output": "Wait event ranking with time breakdown + recommendations",
                "tags": ["wait-events", "performance", "bottleneck", "tuning"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-perf-003",
                "category": "DBA_PERFORMANCE",
                "title": "Active Session History",
                "description": "Analyze active session history (ASH) to understand workload patterns.",
                "prompt_template": "Analyze ASH data for the last {minutes} minutes. Show top sessions, SQL execution patterns, wait class distribution, and resource contention.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Session ID, Username, SQL ID, Wait Class, % Activity, Program\n2. WAIT CLASS DISTRIBUTION: Table showing each wait class and its % of total activity\n3. KEY FINDINGS: Hot sessions, resource contention points, workload patterns\n4. RECOMMENDATIONS: Workload balancing and contention resolution",
                "parameters": [
                    {"name": "minutes", "type": "integer", "description": "Lookback in minutes", "required": True, "default": 30}
                ],
                "default_values": {"minutes": 30},
                "expected_output": "ASH report with session activity, wait classes, and hot blocks",
                "tags": ["ASH", "sessions", "workload", "performance"],
                "difficulty_level": "advanced",
                "estimated_runtime": "30s - 1min",
            },
            {
                "id": "dba-perf-004",
                "category": "DBA_PERFORMANCE",
                "title": "I/O Performance Analysis",
                "description": "Analyze database I/O performance across datafiles and tablespaces.",
                "prompt_template": "Show I/O performance statistics. Include read/write IOPS per datafile, average latency, and identify any I/O bottleneck tablespaces.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Datafile, Tablespace, Read IOPS, Write IOPS, Avg Read Latency (ms), Avg Write Latency (ms), Status\n2. ANALYSIS: I/O distribution patterns, hot files, latency anomalies\n3. KEY FINDINGS: Bottleneck tablespaces and their impact\n4. RECOMMENDATIONS: Storage optimization and I/O improvement actions",
                "parameters": [],
                "default_values": {},
                "expected_output": "I/O stats per datafile with latency and IOPS",
                "tags": ["IO", "performance", "datafile", "latency"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },

            # ==============================================================
            # DBA CAPACITY (4 prompts)
            # ==============================================================
            {
                "id": "dba-cap-001",
                "category": "DBA_CAPACITY",
                "title": "Tablespace Usage Report",
                "description": "Show tablespace usage, free space, and growth projections.",
                "prompt_template": "Show tablespace usage for all tablespaces. Include used/free space in GB, percentage used, autoextend status, and project when each will hit {threshold}% full.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Tablespace, Size (GB), Used (GB), Free (GB), % Used, Autoextend, Projected Full Date\n2. ANALYSIS: Growth trends, tablespaces approaching threshold\n3. KEY FINDINGS: Critical tablespaces needing attention\n4. RECOMMENDATIONS: Resize actions and monitoring thresholds",
                "parameters": [
                    {"name": "threshold", "type": "integer", "description": "Alert threshold %", "required": True, "default": 85}
                ],
                "default_values": {"threshold": 85},
                "expected_output": "Tablespace table with usage bars and projected full dates",
                "tags": ["tablespace", "storage", "capacity", "growth"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-cap-002",
                "category": "DBA_CAPACITY",
                "title": "Segment Growth Analysis",
                "description": "Identify the fastest-growing database segments (tables, indexes, LOBs).",
                "prompt_template": "Show the top {count} fastest-growing segments over the last {days} days. Include segment type, current size, growth rate, and projected size in 30 days.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Rank, Segment Name, Type, Schema, Current Size (GB), Growth/Day (MB), Projected 30-Day Size (GB)\n2. ANALYSIS: Growth patterns, seasonal trends, anomalous growth\n3. KEY FINDINGS: Segments requiring immediate attention\n4. RECOMMENDATIONS: Archival, partitioning, or resize strategies",
                "parameters": [
                    {"name": "count", "type": "integer", "description": "Top N segments", "required": True, "default": 15},
                    {"name": "days", "type": "integer", "description": "Analysis period in days", "required": True, "default": 30}
                ],
                "default_values": {"count": 15, "days": 30},
                "expected_output": "Growth ranking table with projections",
                "tags": ["segments", "growth", "storage", "capacity", "projection"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "30s - 1min",
            },
            {
                "id": "dba-cap-003",
                "category": "DBA_CAPACITY",
                "title": "ASM Disk Group Usage",
                "description": "Show ASM disk group utilization and rebalance status.",
                "prompt_template": "Show ASM disk group usage. Include total/free/used space, redundancy type, and rebalance status for all disk groups.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Disk Group, Total (TB), Used (TB), Free (TB), % Used, Redundancy, Rebalance Status\n2. ANALYSIS: Utilization distribution, imbalanced groups, capacity trending\n3. KEY FINDINGS: Groups at risk of running out of space\n4. RECOMMENDATIONS: Disk addition or data redistribution actions",
                "parameters": [],
                "default_values": {},
                "expected_output": "ASM disk group summary with usage bars",
                "tags": ["ASM", "storage", "disk-group", "capacity"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-cap-004",
                "category": "DBA_CAPACITY",
                "title": "Temp Space Usage",
                "description": "Monitor temporary tablespace usage and identify heavy temp consumers.",
                "prompt_template": "Show current TEMP tablespace usage. List the top {count} sessions consuming temp space with their SQL and sort usage.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. TEMP OVERVIEW: Total TEMP size, current usage %, peak usage\n2. DATA TABLE: Rank, Session ID, Username, SQL ID, Temp Used (MB), Sort Used (MB), SQL Text (truncated)\n3. KEY FINDINGS: Heavy consumers, temp space pressure patterns\n4. RECOMMENDATIONS: Query optimization or TEMP resize suggestions",
                "parameters": [
                    {"name": "count", "type": "integer", "description": "Top N sessions", "required": True, "default": 10}
                ],
                "default_values": {"count": 10},
                "expected_output": "Temp usage summary + top consumer session list",
                "tags": ["temp", "tablespace", "sessions", "sorting"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },

            # ==============================================================
            # DBA SECURITY & LOCKS (4 prompts)
            # ==============================================================
            {
                "id": "dba-sec-001",
                "category": "DBA_SECURITY",
                "title": "Blocking Session Analysis",
                "description": "Identify blocking sessions and their wait chains to resolve lock contention.",
                "prompt_template": "Show all current blocking sessions. Include blocker/waiter chain, blocked SQL, lock type, and how long each session has been blocked.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. BLOCKING TREE: Visual representation of blocker → waiter chains\n2. DATA TABLE: Blocker SID, Waiter SID, Lock Type, Object, Wait Duration, Blocked SQL\n3. KEY FINDINGS: Root blocker sessions, impact scope, recurring patterns\n4. RECOMMENDATIONS: Resolution steps and prevention measures",
                "parameters": [],
                "default_values": {},
                "expected_output": "Blocking tree with session details and wait durations",
                "tags": ["blocking", "locks", "sessions", "contention"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-sec-002",
                "category": "DBA_SECURITY",
                "title": "Long Running Sessions",
                "description": "Find sessions running longer than a threshold with resource consumption details.",
                "prompt_template": "List all sessions running longer than {minutes} minutes. Include SQL text, elapsed time, CPU usage, and undo/temp consumption.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: SID, Username, SQL ID, Elapsed Time (min), CPU (s), Undo (MB), Temp (MB), Status, SQL Text\n2. ANALYSIS: Session patterns, resource consumption trends\n3. KEY FINDINGS: Sessions posing risk to system stability\n4. RECOMMENDATIONS: Which sessions to monitor, kill, or optimize",
                "parameters": [
                    {"name": "minutes", "type": "integer", "description": "Minimum runtime in minutes", "required": True, "default": 30}
                ],
                "default_values": {"minutes": 30},
                "expected_output": "Long-running session list with resource metrics",
                "tags": ["sessions", "long-running", "monitoring", "resources"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-sec-003",
                "category": "DBA_SECURITY",
                "title": "Kill Blocking Session",
                "description": "Generate commands to kill a specific blocking session safely.",
                "prompt_template": "Generate the ALTER SYSTEM KILL SESSION command for SID {sid}, SERIAL# {serial}. Include pre-kill validation checks and post-kill verification steps.",
                "parameters": [
                    {"name": "sid", "type": "integer", "description": "Session ID (SID)", "required": True},
                    {"name": "serial", "type": "integer", "description": "Serial number", "required": True}
                ],
                "default_values": {},
                "expected_output": "Pre-kill checks, KILL command, post-kill verification",
                "tags": ["kill", "session", "blocking", "remediation"],
                "difficulty_level": "advanced",
                "estimated_runtime": "< 30s",
                "requires_approval": True,
            },
            {
                "id": "dba-sec-004",
                "category": "DBA_SECURITY",
                "title": "User Privilege Audit",
                "description": "Audit database user privileges and identify excessive permissions.",
                "prompt_template": "Audit privileges for user {username}. Show system privileges, object privileges, roles, and flag any excessive permissions compared to least-privilege principles.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. SYSTEM PRIVILEGES TABLE: Privilege, Admin Option, Risk Level (Low/Medium/High)\n2. ROLES TABLE: Role Name, Privileges Count, Admin Option\n3. OBJECT PRIVILEGES TABLE: Object, Privilege, Grantor\n4. RISK ASSESSMENT: Excessive permissions flagged with explanations\n5. RECOMMENDATIONS: Privileges to revoke, roles to consolidate",
                "parameters": [
                    {"name": "username", "type": "string", "description": "Database username", "required": True, "default": "SYSTEM"}
                ],
                "default_values": {"username": "SYSTEM"},
                "expected_output": "Privilege summary with risk assessment",
                "tags": ["security", "privileges", "audit", "compliance"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },

            # ==============================================================
            # DBA BACKUP (4 prompts)
            # ==============================================================
            {
                "id": "dba-backup-001",
                "category": "DBA_BACKUP",
                "title": "RMAN Backup Status",
                "description": "Show recent RMAN backup status including completion, duration, and failures.",
                "prompt_template": "Show RMAN backup status for the last {days} days. Include backup type, status, duration, size, and any failures with error codes.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Date, Backup Type, Status, Duration (min), Size (GB), Error Code\n2. SUMMARY: Success rate %, total backup size, average duration\n3. KEY FINDINGS: Failed backups, performance trends, anomalies\n4. RECOMMENDATIONS: Backup schedule optimization and failure remediation",
                "parameters": [
                    {"name": "days", "type": "integer", "description": "Lookback in days", "required": True, "default": 7}
                ],
                "default_values": {"days": 7},
                "expected_output": "Backup history table with status, size, and duration",
                "tags": ["RMAN", "backup", "status", "recovery"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-backup-002",
                "category": "DBA_BACKUP",
                "title": "Archive Log Generation Rate",
                "description": "Monitor archive log generation rate and predict storage requirements.",
                "prompt_template": "Show archive log generation rate for the last {days} days. Include hourly rates, daily totals, and storage consumption. Project when the FRA will reach {threshold}% full.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Date, Hourly Avg Rate (MB/hr), Daily Total (GB), Peak Hour, Peak Rate (MB/hr)\n2. FRA PROJECTION: Current usage, growth trend, projected full date\n3. KEY FINDINGS: Unusual generation spikes, correlation with workload\n4. RECOMMENDATIONS: FRA sizing, archivelog management, backup frequency",
                "parameters": [
                    {"name": "days", "type": "integer", "description": "Analysis period in days", "required": True, "default": 7},
                    {"name": "threshold", "type": "integer", "description": "FRA alert threshold %", "required": True, "default": 80}
                ],
                "default_values": {"days": 7, "threshold": 80},
                "expected_output": "Hourly rate chart, daily summary, FRA projection",
                "tags": ["archivelog", "FRA", "storage", "monitoring"],
                "difficulty_level": "intermediate",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-backup-003",
                "category": "DBA_BACKUP",
                "title": "Recovery Point Objective Check",
                "description": "Verify the current RPO against backup policies and identify gaps.",
                "prompt_template": "Check recovery point objective (RPO). Show the most recent backup per backup type, calculate current RPO, and compare with target RPO of {target_minutes} minutes.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. DATA TABLE: Backup Type, Last Backup Time, Age (hours), Status, RPO Met (Yes/No)\n2. RPO COMPLIANCE: Current RPO vs target, compliance percentage\n3. KEY FINDINGS: Gaps in backup coverage, at-risk periods\n4. RECOMMENDATIONS: Backup schedule adjustments to meet RPO targets",
                "parameters": [
                    {"name": "target_minutes", "type": "integer", "description": "Target RPO in minutes", "required": True, "default": 60}
                ],
                "default_values": {"target_minutes": 60},
                "expected_output": "RPO compliance report with gaps highlighted",
                "tags": ["RPO", "recovery", "backup", "compliance"],
                "difficulty_level": "advanced",
                "estimated_runtime": "< 30s",
            },
            {
                "id": "dba-backup-004",
                "category": "DBA_BACKUP",
                "title": "Flash Recovery Area Usage",
                "description": "Monitor FRA usage, components, and projected fill rate.",
                "prompt_template": "Show Flash Recovery Area status. Include total/used/free space, component breakdown (archivelogs, backups, flashback logs), and space reclaimable.\n\nIMPORTANT: Use your database tools to query real data from the Oracle database. Present the results in a structured format.\n\nProvide a structured analysis:\n1. FRA OVERVIEW TABLE: Total Size (GB), Used (GB), Free (GB), % Used, Reclaimable (GB)\n2. COMPONENT BREAKDOWN: Component Type, Size (GB), % of Total, Files Count\n3. KEY FINDINGS: Components consuming most space, reclaimable opportunities\n4. RECOMMENDATIONS: Space management actions and FRA maintenance",
                "parameters": [],
                "default_values": {},
                "expected_output": "FRA usage breakdown with component sizes",
                "tags": ["FRA", "recovery", "storage", "monitoring"],
                "difficulty_level": "beginner",
                "estimated_runtime": "< 30s",
            },
        ]

    # ========================================================================
    # Read Operations
    # ========================================================================

    async def list_prompts(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        difficulty: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        user_id: str = "admin",
    ) -> PromptListResponse:
        """List prompts with optional filtering, search, and pagination."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            where_clauses = ["p.is_active = 1"]
            params: list = []

            if category:
                where_clauses.append("p.category = ?")
                params.append(category)
            if search:
                where_clauses.append(
                    "(p.title LIKE ? OR p.description LIKE ? OR p.tags LIKE ?)"
                )
                like = f"%{search}%"
                params.extend([like, like, like])
            if tag:
                where_clauses.append("p.tags LIKE ?")
                params.append(f'%"{tag}"%')
            if difficulty:
                where_clauses.append("p.difficulty_level = ?")
                params.append(difficulty)

            where = " AND ".join(where_clauses)

            # Total count
            count_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM prompt_library p WHERE {where}",
                params,
            ).fetchone()
            total = count_row["cnt"]

            # Paginated results
            offset = (page - 1) * per_page
            rows = conn.execute(
                f"""SELECT p.*, 
                       CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as is_favorited
                    FROM prompt_library p
                    LEFT JOIN user_prompt_favorites f 
                        ON p.id = f.prompt_id AND f.user_id = ?
                    WHERE {where}
                    ORDER BY p.category, p.title
                    LIMIT ? OFFSET ?""",
                [user_id] + params + [per_page, offset],
            ).fetchall()

            prompts = [
                PromptSummary(
                    id=row["id"],
                    category=row["category"],
                    title=row["title"],
                    description=row["description"],
                    tags=json.loads(row["tags"]),
                    difficulty_level=row["difficulty_level"],
                    estimated_runtime=row["estimated_runtime"],
                    requires_approval=bool(row["requires_approval"]),
                    usage_count=row["usage_count"],
                    is_favorited=bool(row["is_favorited"]),
                )
                for row in rows
            ]

        return PromptListResponse(
            prompts=prompts,
            total=total,
            page=page,
            per_page=per_page,
        )

    async def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a single prompt by ID with full details."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM prompt_library WHERE id = ? AND is_active = 1",
                (prompt_id,),
            ).fetchone()

            if not row:
                return None

            return Prompt(
                id=row["id"],
                category=row["category"],
                title=row["title"],
                description=row["description"],
                prompt_template=row["prompt_template"],
                parameters=[
                    PromptParameter(**p)
                    for p in json.loads(row["parameters"])
                ],
                default_values=json.loads(row["default_values"]),
                expected_output=row["expected_output"],
                tags=json.loads(row["tags"]),
                difficulty_level=row["difficulty_level"],
                estimated_runtime=row["estimated_runtime"],
                requires_approval=bool(row["requires_approval"]),
                is_active=bool(row["is_active"]),
                usage_count=row["usage_count"],
                average_runtime=row["average_runtime"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list_categories(self) -> List[PromptCategory]:
        """List all categories with prompt counts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT c.*, 
                       COUNT(p.id) as prompt_count
                   FROM prompt_categories c
                   LEFT JOIN prompt_library p 
                       ON c.name = p.category AND p.is_active = 1
                   GROUP BY c.id
                   ORDER BY c.sort_order""",
            ).fetchall()

            return [
                PromptCategory(
                    id=row["id"],
                    name=row["name"],
                    display_name=row["display_name"],
                    description=row["description"],
                    icon=row["icon"],
                    sort_order=row["sort_order"],
                    parent_category_id=row["parent_category_id"],
                    prompt_count=row["prompt_count"],
                )
                for row in rows
            ]

    # ========================================================================
    # Favorites
    # ========================================================================

    async def toggle_favorite(
        self, user_id: str, prompt_id: str
    ) -> FavoriteToggleResponse:
        """Toggle favorite status for a prompt. Returns new state."""
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM user_prompt_favorites WHERE user_id = ? AND prompt_id = ?",
                (user_id, prompt_id),
            ).fetchone()

            if existing:
                conn.execute(
                    "DELETE FROM user_prompt_favorites WHERE user_id = ? AND prompt_id = ?",
                    (user_id, prompt_id),
                )
                conn.commit()
                return FavoriteToggleResponse(prompt_id=prompt_id, favorited=False)
            else:
                conn.execute(
                    "INSERT INTO user_prompt_favorites (id, user_id, prompt_id) VALUES (?, ?, ?)",
                    (str(uuid4()), user_id, prompt_id),
                )
                conn.commit()
                return FavoriteToggleResponse(prompt_id=prompt_id, favorited=True)

    async def get_favorites(
        self, user_id: str
    ) -> List[PromptSummary]:
        """Get user's favorited prompts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT p.* FROM prompt_library p
                   INNER JOIN user_prompt_favorites f ON p.id = f.prompt_id
                   WHERE f.user_id = ? AND p.is_active = 1
                   ORDER BY f.added_at DESC""",
                (user_id,),
            ).fetchall()

            return [
                PromptSummary(
                    id=row["id"],
                    category=row["category"],
                    title=row["title"],
                    description=row["description"],
                    tags=json.loads(row["tags"]),
                    difficulty_level=row["difficulty_level"],
                    estimated_runtime=row["estimated_runtime"],
                    requires_approval=bool(row["requires_approval"]),
                    usage_count=row["usage_count"],
                    is_favorited=True,
                )
                for row in rows
            ]

    # ========================================================================
    # Execution History
    # ========================================================================

    async def log_execution(
        self,
        user_id: str,
        prompt_id: str,
        parameters_used: Dict[str, Any],
        execution_time_ms: int = 0,
        status: str = "success",
        result_summary: Optional[str] = None,
    ) -> str:
        """Log a prompt execution and increment usage count. Returns execution ID."""
        execution_id = str(uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO prompt_execution_history
                   (id, user_id, prompt_id, parameters_used, execution_time_ms, status, result_summary)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    execution_id,
                    user_id,
                    prompt_id,
                    json.dumps(parameters_used),
                    execution_time_ms,
                    status,
                    result_summary,
                ),
            )
            conn.execute(
                "UPDATE prompt_library SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (prompt_id,),
            )
            conn.commit()
        return execution_id

    async def get_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> PromptHistoryResponse:
        """Get paginated execution history for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM prompt_execution_history WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            total = count_row["cnt"]

            rows = conn.execute(
                """SELECT h.*, p.title as prompt_title
                   FROM prompt_execution_history h
                   LEFT JOIN prompt_library p ON h.prompt_id = p.id
                   WHERE h.user_id = ?
                   ORDER BY h.executed_at DESC
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            ).fetchall()

            history = [
                PromptHistoryEntry(
                    id=row["id"],
                    user_id=row["user_id"],
                    prompt_id=row["prompt_id"],
                    prompt_title=row["prompt_title"],
                    parameters_used=json.loads(row["parameters_used"]),
                    executed_at=row["executed_at"],
                    execution_time_ms=row["execution_time_ms"],
                    status=row["status"],
                    result_summary=row["result_summary"],
                )
                for row in rows
            ]

        return PromptHistoryResponse(
            history=history,
            total=total,
            limit=limit,
            offset=offset,
        )

    # ========================================================================
    # Admin CRUD
    # ========================================================================

    async def create_prompt(self, data: PromptCreate) -> Prompt:
        """Create a new prompt (admin only)."""
        prompt_id = str(uuid4())
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO prompt_library
                   (id, category, title, description, prompt_template,
                    parameters, default_values, expected_output, tags,
                    difficulty_level, estimated_runtime, requires_approval,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prompt_id,
                    data.category,
                    data.title,
                    data.description,
                    data.prompt_template,
                    json.dumps([p.model_dump() for p in data.parameters]),
                    json.dumps(data.default_values),
                    data.expected_output,
                    json.dumps(data.tags),
                    data.difficulty_level,
                    data.estimated_runtime,
                    1 if data.requires_approval else 0,
                    now,
                    now,
                ),
            )
            conn.commit()
        return await self.get_prompt(prompt_id)  # type: ignore

    async def update_prompt(
        self, prompt_id: str, data: PromptUpdate
    ) -> Optional[Prompt]:
        """Update an existing prompt (admin only)."""
        updates = []
        params: list = []
        update_dict = data.model_dump(exclude_none=True)

        # Handle JSON fields
        json_fields = {"parameters", "default_values", "tags"}
        bool_fields = {"requires_approval", "is_active"}

        for key, value in update_dict.items():
            if key in json_fields:
                if key == "parameters":
                    value = [p.model_dump() if hasattr(p, "model_dump") else p for p in value]
                updates.append(f"{key} = ?")
                params.append(json.dumps(value))
            elif key in bool_fields:
                updates.append(f"{key} = ?")
                params.append(1 if value else 0)
            else:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return await self.get_prompt(prompt_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(prompt_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE prompt_library SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()

        return await self.get_prompt(prompt_id)

    async def delete_prompt(self, prompt_id: str) -> bool:
        """Soft-delete a prompt by setting is_active = 0."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE prompt_library SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND is_active = 1",
                (prompt_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
