# ODAOS - Oracle Database AI Operations System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0+-green.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, multi-agent AI system for Oracle Database operations, built with LangGraph and powered by Groq LLM.

> **Project Status: MVP In Progress** — Core agents operational, live database and OCI integrations complete.

---

## 💡 Problem, Differentiation, and Business Value

### What Solutions Exist Today

Organizations typically rely on a combination of tools to manage Oracle databases and cloud infrastructure:

- **Monitoring & Alerting** — Dashboards that display metrics and trigger alerts when thresholds are breached
- **Runbooks & Playbooks** — Static documentation that operators follow to diagnose and resolve issues
- **Cost Management Portals** — Reporting tools that show historical cloud spend by service or project
- **Manual Scripting** — Custom scripts for common tasks like killing sessions or extending tablespaces

**Limitations of these approaches:**
- Alerts require human interpretation and action
- Runbooks become outdated and are not context-aware
- Cost reports are retrospective, not predictive or actionable
- Scripts lack intelligence and cannot adapt to changing conditions

### What Problem This Solves

Database and cloud operations teams face recurring challenges:

- **Slow incident response** — Alerts fire, but root cause analysis requires manual investigation across multiple tools
- **Knowledge silos** — Expert knowledge lives in people's heads, not in systems
- **Reactive cost management** — Overspending is discovered after the fact, not prevented proactively
- **Toil and repetition** — Operators spend time on routine tasks that could be automated

ODAOS addresses these pain points by providing an AI-powered assistant that can reason about operational context, suggest actions, and execute safe remediations.

### Why This Solution Is Unique

| Aspect | Traditional Tools | ODAOS |
|--------|------------------|-------|
| **Analysis** | Metrics + manual interpretation | AI reasons about patterns and context |
| **Actions** | Human executes scripts/commands | AI suggests and (when approved) executes |
| **Knowledge** | Static runbooks | Conversational, adaptive guidance |
| **Scope** | Single domain (DB or cloud) | Unified view across performance, healing, and cost |

**Key differentiators:**
- **Oracle-aware operations** — Understands Oracle-specific concepts like wait events, ASH, and AWR
- **Safe execution model** — Generates commands for review before execution; no autonomous destructive actions
- **Natural language interface** — Operators ask questions in plain English instead of navigating dashboards
- **Multi-agent coordination** — Specialized agents collaborate on cross-domain problems

### How Businesses Benefit

| Benefit | Description |
|---------|-------------|
| **Faster resolution** | AI-assisted triage reduces mean time to resolution (MTTR) |
| **Reduced manual effort** | Routine diagnostics and recommendations are automated |
| **Better cost visibility** | Proactive identification of idle resources and rightsizing opportunities |
| **Knowledge continuity** | Institutional knowledge is embedded in the system, not lost with attrition |
| **Consistent operations** | Standardized investigation and remediation workflows |

### Hard-Dollar Savings Potential

Cost savings can be realized in several areas:

- **Reduced downtime** — Faster incident response means less revenue impact and fewer SLA breaches
- **Optimized cloud spend** — Identifying and eliminating idle resources, right-sizing over-provisioned instances
- **Productivity gains** — Operators spend less time on repetitive diagnostics and more on strategic work
- **Avoided incidents** — Proactive alerts on capacity and performance trends prevent outages before they occur

> **Note:** Actual savings depend on environment size, incident frequency, and cloud spend. This system provides the visibility and automation to capture these savings.

---

## 🚀 Features

### Three Specialized AI Agents

| Agent | Capabilities |
|-------|-------------|
| **Performance Agent** | Database metrics analysis, SQL tuning, wait event diagnostics |
| **Self-Healing Agent** | Incident detection, blocking session resolution, remediation automation |
| **Cost Optimization Agent** | OCI cost analysis, rightsizing recommendations, idle resource cleanup |

### Multi-Agent Orchestrator
- Intelligent query routing
- Cross-agent coordination
- Composite workflow support
- Conversation memory

### MCP Server Architecture
- Model Context Protocol (MCP) compliant
- 12 specialized tools across 3 servers
- Live database integration via secure tunneling
- Live OCI API integration for cost analysis

## 📦 Installation

### Prerequisites
- Python 3.11+
- Git
- Groq API key (free at [groq.com](https://console.groq.com))

### Quick Start

```powershell
# Clone the repository
git clone https://github.com/yourusername/ODAOS.git
cd ODAOS

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Environment Configuration

Create a `.env` file with:

```env
# LLM Provider (groq recommended)
ODAOS_LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# OCI Configuration (optional for cost optimization)
OCI_CONFIG_PATH=~/.oci/config
OCI_PROFILE=DEFAULT

# Database (optional - uses mock data if not configured)
ORACLE_DSN=localhost:1521/ORCL
ORACLE_USER=system
ORACLE_PASSWORD=your_password
```

## 🎮 Usage

### Interactive CLI

```powershell
python odaos_cli.py
```

Commands:
- `/help` - Show available commands
- `/health` - Run comprehensive health check
- `/performance` - Check database metrics
- `/incidents` - Check for blocking sessions
- `/costs` - Get OCI cost breakdown
- `/quit` - Exit

### Programmatic Usage

```python
import asyncio
from src.orchestrator import ODAOSOrchestrator

async def main():
    orchestrator = ODAOSOrchestrator()
    
    # Ask a question
    response = await orchestrator.chat("How is my database performing?")
    print(response)
    
    # Run health check
    report = await orchestrator.health_check()
    print(report)

asyncio.run(main())
```

### Individual Agents

```python
from src.agents import PerformanceAgent, SelfHealingAgent, CostOptimizationAgent

# Performance analysis
perf_agent = PerformanceAgent()
result = await perf_agent.chat("Analyze top SQL queries")

# Incident response
healing_agent = SelfHealingAgent()
result = await healing_agent.triage()

# Cost optimization
cost_agent = CostOptimizationAgent()
result = await cost_agent.generate_cost_report(budget=10000)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                        │
│            (CLI / REST API / Streamlit)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Multi-Agent Orchestrator                       │
│         (Query Classification & Routing)                    │
└─────┬───────────────┬───────────────┬───────────────────────┘
      │               │               │
┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
│Performance│   │Self-Heal  │   │   Cost    │
│   Agent   │   │   Agent   │   │   Agent   │
└─────┬─────┘   └─────┬─────┘   └─────┬─────┘
      │               │               │
┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
│Performance│   │Self-Heal  │   │   Cost    │
│MCP Server │   │MCP Server │   │MCP Server │
└───────────┘   └───────────┘   └───────────┘
      │               │               │
      └───────────────┴───────────────┘
                      │
              ┌───────▼───────┐
              │ Oracle DB /   │
              │    OCI APIs   │
              └───────────────┘
```

## 📁 Project Structure

```
ODAOS/
├── src/
│   ├── agents/
│   │   ├── performance/      # Performance analysis agent
│   │   ├── self_healing/     # Incident response agent
│   │   └── cost_optimization/# Cost analysis agent
│   ├── mcp_servers/
│   │   ├── performance/      # 3 performance tools
│   │   ├── self_healing/     # 5 remediation tools
│   │   └── cost_optimization/# 4 cost tools
│   ├── core/
│   │   ├── config.py         # Pydantic settings
│   │   └── providers/        # LLM provider abstraction
│   ├── database/
│   │   └── connection.py     # Oracle connection manager
│   └── orchestrator.py       # Multi-agent orchestrator
├── tests/
│   └── test_integration.py   # Integration tests
├── taskmaster/               # Task definitions
├── odaos_cli.py             # Interactive CLI
├── requirements.txt
├── .env.example
└── README.md
```

## 🛠️ MCP Tools Reference

### Performance MCP Server

| Tool | Description |
|------|-------------|
| `get_database_metrics` | CPU, memory, session stats |
| `analyze_top_sql` | Top N SQL by execution time |
| `check_tablespace_usage` | Space usage by tablespace |

### Self-Healing MCP Server

| Tool | Description |
|------|-------------|
| `monitor_alert_log` | Scan for ORA- errors |
| `check_blocking_sessions` | Detect lock contention |
| `get_tablespace_status` | Space status for healing |
| `extend_tablespace` | Generate ADD DATAFILE DDL |
| `kill_session` | Generate KILL SESSION command |

### Cost Optimization MCP Server

| Tool | Description |
|------|-------------|
| `get_oci_costs` | Cost by service/compartment |
| `analyze_compute_utilization` | Find underutilized resources |
| `list_idle_resources` | Stopped instances, orphan volumes |
| `forecast_costs` | 30/60/90 day projections |

## 🧪 Testing

```powershell
# Run integration tests
python tests/test_integration.py

# Run individual MCP server tests
python test_performance_mcp.py
python test_self_healing_mcp.py
python test_cost_optimization_mcp.py

# Test agents
python test_performance_agent_quick.py
python test_self_healing_agent_quick.py
python test_cost_optimization_agent_quick.py
```

## 🔧 Configuration

### LLM Providers

ODAOS supports multiple LLM providers:

| Provider | Environment Variable | Notes |
|----------|---------------------|-------|
| Groq | `GROQ_API_KEY` | Recommended (fast, free tier) |
| Ollama | `OLLAMA_BASE_URL` | Local, private |
| Anthropic | `ANTHROPIC_API_KEY` | Claude models |

### Database Connection

For live database analytics (optional):

```env
# Direct connection
ORACLE_DSN=hostname:1521/service_name
ORACLE_USER=username
ORACLE_PASSWORD=password

# Via SSH tunnel (Bastion)
BASTION_HOST=bastion.example.com
BASTION_KEY_PATH=~/.ssh/bastion_key.pem
DB_PRIVATE_IP=10.0.1.100
```

## 📊 Example Output

```
You: Check database performance

ODAOS: 📊 **Database Performance Summary**

| Metric | Value | Status |
|--------|-------|--------|
| CPU Usage | 45.2% | ✅ Normal |
| Memory Usage | 72.5% | ⚠️ Monitor |
| Active Sessions | 48 | ✅ Normal |
| Wait Events | 3 | ✅ Low |

**Top SQL by Execution Time:**
1. `SELECT * FROM orders...` - 2.3s avg
2. `UPDATE inventory...` - 1.8s avg

**Recommendations:**
- Consider indexing on orders.customer_id
- Review memory allocation for SGA
```

## 🚀 Roadmap

### Phase 1 (Current) - MVP
- [x] MCP Server architecture
- [x] Three specialized agents
- [x] Multi-agent orchestrator
- [x] CLI interface
- [x] Live database integration (secure tunneling)
- [x] Live OCI cost API integration
- [x] Web dashboard (read-only analysis)
- [ ] Integration testing
- [ ] User acceptance testing

### Phase 2 - Production (Planned)
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] OCI deployment automation
- [ ] REST API with FastAPI

### Phase 3 - Advanced (Planned)
- [ ] ML-based anomaly detection
- [ ] Predictive maintenance
- [ ] Auto-remediation workflows
- [ ] Slack/Teams integration

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📞 Support

For issues and feature requests, please use the GitHub issue tracker.

---

Built with ❤️ using [LangGraph](https://langchain-ai.github.io/langgraph/) and [Groq](https://groq.com)
