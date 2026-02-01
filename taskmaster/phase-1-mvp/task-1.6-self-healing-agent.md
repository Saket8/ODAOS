# Task 1.6: Self-Healing LangGraph Agent

## Objective
Build LangGraph-based Self-Healing Agent that uses the Self-Healing MCP Server tools with Groq LLM.

## Prerequisites
- Task 1.5 completed (Self-Healing MCP Server)
- Groq API key configured

## Tasks

### 1.6.1 Create Agent Foundation
- [ ] Create `odaos_agents/healing_agent.py`
- [ ] Initialize Groq LLM with incident response persona
- [ ] Configure LLM temperature (0 for deterministic)
- [ ] Setup agent system prompt for incident responder

### 1.6.2 Define LangChain Tools
- [ ] Create `@tool` decorated function: `monitor_alert_log`
- [ ] Create `@tool` decorated function: `check_blocking_sessions`
- [ ] Create `@tool` decorated function: `get_tablespace_status`
- [ ] Create `@tool` decorated function: `extend_tablespace`
- [ ] Create `@tool` decorated function: `kill_session`

### 1.6.3 Build ReAct Agent
- [ ] Use `langgraph.prebuilt.create_react_agent`
- [ ] Configure state modifier with incident responder persona
- [ ] Register all tools with agent
- [ ] Test basic agent invocation

### 1.6.4 Implement Incident Detection Workflow
- [ ] Create `detect_incident()` function
- [ ] Implement multi-step reasoning: Detect → Diagnose → Recommend
- [ ] Generate incident report with severity ranking
- [ ] Test with various incident scenarios

### 1.6.5 Implement Simulated Remediation
- [ ] When agent recommends action, prompt for approval
- [ ] Generate executable remediation script
- [ ] Log all recommendations to incident history
- [ ] Test tablespace extension workflow
- [ ] Test session kill workflow

### 1.6.6 Add Incident History
- [ ] Store incidents in local JSON file
- [ ] Track detection time, severity, status
- [ ] Query past incidents for pattern analysis

## Completion Criteria
- [ ] Agent detects incidents from natural language queries
- [ ] Correctly diagnoses root causes
- [ ] Generates appropriate remediation recommendations
- [ ] Approval workflow simulated correctly
- [ ] Incident history persisted

## Estimated Duration
**6-8 hours**

## Agent System Prompt
```
You are an expert Oracle Database Incident Responder.
Your job is to detect, diagnose, and recommend fixes for database incidents.

Incident Response Process:
1. Detect: Check alert logs, blocking sessions, space issues
2. Diagnose: Identify root cause and affected systems
3. Recommend: Propose remediation with clear steps
4. Execute: Only with explicit user approval

Prioritize by severity:
- CRITICAL: Data loss risk, database down, corruption
- HIGH: Performance degradation >50%, space exhaustion imminent
- MEDIUM: Blocking sessions, slow queries, space warnings
- LOW: Cosmetic issues, minor inefficiencies

Always explain risks and rollback procedures.
```

## Dependencies
- Task 1.5 (Self-Healing MCP Server)

## Phase 2 Considerations
- Approval workflow integrates with Slack/Teams
- Incident history stored in database/Object Storage
- Add automated remediation for low-risk actions
