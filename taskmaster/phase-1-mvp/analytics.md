# BRM Analytics Module

## Overview

Natural language analytics for Oracle BRM (Billing and Revenue Management) data, integrated directly into the ODAOS CLI. Users can ask questions in plain English and get real-time visualizations rendered in the terminal.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ODAOS CLI                               │
│  /analytics mode                                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Analytics Agent                             │
│  • LangGraph + LLM (Groq/Gemini)                            │
│  • Natural language understanding                           │
│  • Tool selection based on intent                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               Terminal Charts Module                         │
│  • scripts/terminal_charts.py                               │
│  • plotext library for ASCII rendering                      │
│  • Live database queries                                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Oracle BRM Database (PIN Schema)                │
│  ACCOUNT_T, ITEM_T, BILL_T, PRODUCT_T, EVENT_T              │
└─────────────────────────────────────────────────────────────┘
```

## Supported Visualizations

| Chart Type | Visualization | Data Source |
|------------|--------------|-------------|
| 🥧 Pie | Customer Distribution by Region | ACCOUNT_NAMEINFO_T |
| 🥧 Pie | Product Market Share | PURCHASED_PRODUCT_T + PRODUCT_T |
| 🥧 Pie | Revenue by Service Type | ITEM_T |
| 🔥 Heatmap | Overdue Balance vs ARPU | ACCOUNT_T + ITEM_T |
| 🔥 Heatmap | Service Usage by Time | EVENT_T |
| 🔥 Heatmap | Churn Risk by Region | ACCOUNT_T + ACCOUNT_NAMEINFO_T |
| 🔥 Heatmap | Complaints vs Billing Errors | ITEM_T (adjustments) |
| 📈 Scatter | ARPU vs Churn Probability | ACCOUNT_T + ITEM_T |
| 📉 Line | Customer Acquisition Trend | ACCOUNT_T |
| 📉 Line | Revenue Growth | BILL_T |

## Usage

```bash
python odaos_cli.py
> /analytics

# Ask anything in natural language:
> "Show me where our customers are located"
> "Which products are selling best?"
> "Find high-risk customers"
> "How has revenue changed over time?"

> /back  # Return to normal mode
```

## Sample Output

```
────────────── 🥧 Customer Distribution by Region ──────────────
Netherlands  ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 105.00
USA          ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 49.00
NL           ▇▇ 5.00

**Percentage Breakdown:**
  Netherlands: █████████████ 65.2% (105)
  USA: ██████ 30.4% (49)
  NL:  3.1% (5)

**Data Source:** PIN.ACCOUNT_NAMEINFO_T
**Total Customers:** 161
```

## Files

| File | Purpose |
|------|---------|
| `src/agents/analytics/agent.py` | LangGraph agent with 11 tools |
| `scripts/terminal_charts.py` | Chart rendering with plotext |
| `odaos_cli.py` | CLI integration (`/analytics` command) |

## Data Limitations

- **Date Range**: ~5 months of test data available
- **Revenue**: Test environment shows negative values
- **Churn Proxy**: Uses days since last activity / 180
- **Complaints**: No dedicated table, uses adjustments as proxy
- **ECE Data**: RATEDEVENT table is empty

## Dependencies

```
plotext>=5.3.2
```
