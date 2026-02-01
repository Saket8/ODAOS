# Task 1.8: Cost Optimization LangGraph Agent

## Objective
Build LangGraph-based Cost Optimization Agent that analyzes OCI spending and recommends optimizations.

## Prerequisites
- Task 1.7 completed (Cost Optimization MCP Server)
- Groq API key configured

## Tasks

### 1.8.1 Create Agent Foundation
- [ ] Create `odaos_agents/cost_agent.py`
- [ ] Initialize Groq LLM with FinOps persona
- [ ] Configure LLM temperature (0 for deterministic)
- [ ] Setup agent system prompt for cost analyst

### 1.8.2 Define LangChain Tools
- [ ] Create `@tool` decorated function: `get_oci_costs`
- [ ] Create `@tool` decorated function: `analyze_compute_utilization`
- [ ] Create `@tool` decorated function: `list_idle_resources`
- [ ] Create `@tool` decorated function: `forecast_costs`

### 1.8.3 Build ReAct Agent
- [ ] Use `langgraph.prebuilt.create_react_agent`
- [ ] Configure state modifier with FinOps persona
- [ ] Register all tools with agent
- [ ] Test basic agent invocation

### 1.8.4 Implement Cost Analysis Workflow
- [ ] Analyze spending trends over time
- [ ] Compare actual vs baseline/budget
- [ ] Identify top cost drivers
- [ ] Generate savings opportunities

### 1.8.5 Generate Cost Reports
- [ ] Create structured cost analysis report
- [ ] Include ROI calculations for recommendations
- [ ] Support export to CSV/JSON
- [ ] Test report generation

## Completion Criteria
- [ ] Agent responds to cost-related queries
- [ ] Correctly analyzes OCI spending
- [ ] Provides actionable savings recommendations
- [ ] ROI calculations accurate
- [ ] Reports exportable

## Estimated Duration
**4-6 hours**

## Agent System Prompt
```
You are an expert Cloud FinOps Analyst specializing in Oracle Cloud Infrastructure.
Your job is to analyze cloud spending and recommend cost optimization strategies.

Cost Analysis Process:
1. Analyze: Query current and historical spending
2. Identify: Find wasteful or underutilized resources
3. Recommend: Propose specific optimizations with ROI
4. Forecast: Project future costs based on trends

Always include:
- Current monthly spend
- Top cost drivers
- Savings opportunities with dollar amounts
- Implementation difficulty (Easy/Medium/Hard)
- Payback period

Express savings as both percentages and dollar amounts.
```

## Dependencies
- Task 1.7 (Cost Optimization MCP Server)

## Phase 2 Considerations
- Add scheduled cost reports via cron
- Implement budget alerts integration
- Export to OCI Object Storage for archival
