# Task 1.7: Cost Optimization MCP Server

## Objective
Build the Cost Optimization MCP Server with OCI cost analysis and resource utilization tools.

## Prerequisites
- Task 1.1 completed (environment setup)
- OCI CLI configured with CTSISGCMTPAAS profile

## Tasks

### 1.7.1 Create MCP Server Skeleton
- [ ] Create `odaos_mcp_servers/cost_optimization_server.py`
- [ ] Initialize MCP Server with `mcp` SDK
- [ ] Setup OCI SDK client with CTSISGCMTPAAS profile
- [ ] Setup logging and error handling

### 1.7.2 Implement `get_oci_costs` Tool
- [ ] Use OCI UsageApi for cost queries
- [ ] Query costs for last 30/60/90 days
- [ ] Group by service, compartment, tag
- [ ] Calculate daily/weekly trends
- [ ] Return cost breakdown with forecast

### 1.7.3 Implement `analyze_compute_utilization` Tool
- [ ] Query OCI Monitoring for CPU/memory metrics
- [ ] Aggregate metrics by DB system
- [ ] Identify underutilized resources (<30% avg)
- [ ] Calculate potential rightsizing savings

### 1.7.4 Implement `list_idle_resources` Tool
- [ ] Query for stopped compute instances
- [ ] Find unattached block volumes
- [ ] Identify unused boot volumes
- [ ] Calculate cost of idle resources
- [ ] Generate cleanup recommendations

### 1.7.5 Implement `forecast_costs` Tool
- [ ] Implement simple trend-based forecasting
- [ ] Project costs for next 30/60/90 days
- [ ] Compare to budget thresholds
- [ ] Alert on projected budget overruns

### 1.7.6 Test MCP Server
- [ ] Test cost queries with real OCI data
- [ ] Verify utilization metrics accuracy
- [ ] Test idle resource detection
- [ ] Validate cost forecasting

## Completion Criteria
- [ ] MCP server starts without errors
- [ ] All 4 tools registered and callable
- [ ] OCI API calls successful with credentials
- [ ] Cost data accurate and current
- [ ] Recommendations actionable

## Estimated Duration
**6-8 hours**

## Tool Specifications

| Tool | Input | Output | SLA |
|------|-------|--------|-----|
| `get_oci_costs` | days (30/60/90) | Cost breakdown + trends | <30s |
| `analyze_compute_utilization` | compartment_id | Utilization analysis | <20s |
| `list_idle_resources` | compartment_id | Idle resource list | <15s |
| `forecast_costs` | days_ahead | Cost projection | <10s |

## Dependencies
- Task 1.1 (Environment Setup - OCI credentials)

## Phase 2 Considerations
- Add OCI Budget integration for real-time alerts
- Cache cost data to reduce API calls
- Export reports to OCI Object Storage
