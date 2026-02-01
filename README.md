# ODAOS - Oracle Database AI Operations System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0+-green.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, multi-agent AI system for Oracle Database operations, built with LangGraph and powered by Groq LLM.

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
- Mock data for testing without live database

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
- [ ] Live database integration

### Phase 2 - Production
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] OCI deployment automation
- [ ] REST API with FastAPI
- [ ] Streamlit dashboard

### Phase 3 - Advanced
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
