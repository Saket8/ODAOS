# Task 1.9: Multi-Agent Orchestrator

## Objective
Build the LangGraph Multi-Agent Orchestrator that coordinates Performance, Self-Healing, and Cost agents.

## Prerequisites
- Task 1.4 completed (Performance Agent)
- Task 1.6 completed (Self-Healing Agent)
- Task 1.8 completed (Cost Agent)

## Tasks

### 1.9.1 Create Orchestrator Foundation
- [ ] Create `odaos_agents/orchestrator.py`
- [ ] Initialize Groq LLM with orchestrator persona
- [ ] Import all three specialized agents
- [ ] Setup routing logic for query classification

### 1.9.2 Implement Query Router
- [ ] Create `classify_query()` function using LLM
- [ ] Categories: performance, healing, cost, composite
- [ ] Map queries to appropriate agent(s)
- [ ] Test classification accuracy

### 1.9.3 Build LangGraph StateGraph
- [ ] Define `OrchestratorState` TypedDict
- [ ] Add nodes for each specialized agent
- [ ] Add conditional edges based on query type
- [ ] Implement parallel execution for independent tasks
- [ ] Add result synthesis node

### 1.9.4 Implement Composite Workflows
- [ ] Workflow: "Complete health check" → All 3 agents
- [ ] Workflow: "Why slow + what's the cost?" → Performance + Cost
- [ ] Workflow: "Fix issues and find savings" → Healing + Cost
- [ ] Implement result aggregation and synthesis

### 1.9.5 Add Conversation Memory
- [ ] Implement cross-agent conversation state
- [ ] Track context across agent calls
- [ ] Enable follow-up questions

### 1.9.6 Create CLI Interface
- [ ] Build interactive CLI with `rich` library
- [ ] Accept natural language queries
- [ ] Display formatted responses
- [ ] Support multi-turn conversations

## Completion Criteria
- [ ] Orchestrator routes queries correctly (95%+ accuracy)
- [ ] Parallel agent execution works
- [ ] Composite workflows produce synthesized results
- [ ] CLI interface functional and user-friendly
- [ ] Multi-turn conversations work correctly

## Estimated Duration
**6-8 hours**

## Orchestrator Architecture
```
User Query 
    ↓
Query Classifier (LLM)
    ↓
┌───────────────────────────────────┐
│         Route by category         │
├─────────┬─────────┬───────────────┤
│   perf  │  heal   │    cost       │
▼         ▼         ▼               │
Performance   Self-Healing   Cost   │
   Agent         Agent       Agent  │
└─────────┴─────────┴───────────────┘
              ↓
    Result Synthesizer
              ↓
    Formatted Response
```

## Example Workflows

| Query | Agents Called | Output |
|-------|--------------|--------|
| "Check database health" | All 3 | Comprehensive report |
| "Why is database slow?" | Performance | SQL analysis |
| "Fix blocking sessions" | Self-Healing | Remediation plan |
| "How much are we spending?" | Cost | Cost breakdown |
| "Optimize our database setup" | Performance + Cost | Combined analysis |

## Dependencies
- Task 1.4 (Performance Agent)
- Task 1.6 (Self-Healing Agent)
- Task 1.8 (Cost Agent)

## Phase 2 Considerations
- Expose orchestrator via FastAPI REST API
- Add async streaming for real-time responses
- Implement checkpointing for long-running workflows
