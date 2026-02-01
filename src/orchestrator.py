"""ODAOS Multi-Agent Orchestrator.

LangGraph-based orchestrator that coordinates Performance, Self-Healing, and Cost agents.
Routes queries to appropriate agents and synthesizes results.

Usage:
    from src.agents.orchestrator import ODAOSOrchestrator
    
    orchestrator = ODAOSOrchestrator()
    response = await orchestrator.chat("Give me a complete health check")
    print(response)
"""
import asyncio
import logging
from typing import Optional, Literal, Annotated
from datetime import datetime
import operator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from .core.providers import create_llm
from .agents.performance import PerformanceAgent
from .agents.self_healing import SelfHealingAgent
from .agents.cost_optimization import CostOptimizationAgent

logger = logging.getLogger(__name__)


# ============================================================================
# Query Classification
# ============================================================================

class QueryClassification(BaseModel):
    """Classification result for routing queries."""
    category: Literal["performance", "healing", "cost", "composite", "general"] = Field(
        description="The primary category for routing the query"
    )
    agents_needed: list[str] = Field(
        description="List of agents needed: performance, healing, cost"
    )
    confidence: float = Field(
        description="Confidence score 0-1"
    )
    reasoning: str = Field(
        description="Brief explanation of classification"
    )


CLASSIFICATION_PROMPT = """You are a query router for an Oracle Database Operations AI System (ODAOS).
Classify the user's query to determine which specialized agent(s) should handle it.

Categories:
- **performance**: Database performance, SQL analysis, wait events, metrics, slow queries
- **healing**: Errors, incidents, blocking sessions, tablespace issues, remediation, fixes
- **cost**: OCI costs, spending, optimization, utilization, idle resources, budget
- **composite**: Queries needing multiple agents (e.g., "complete health check", "overall status")
- **general**: Greetings, general questions, not database-specific

Examples:
- "Check database metrics" → performance
- "Fix blocking sessions" → healing  
- "How much are we spending?" → cost
- "Complete health check" → composite (all agents)
- "Why slow and is it expensive?" → composite (performance + cost)
- "Hello" → general

Query: {query}

Respond with a JSON object containing:
- category: one of [performance, healing, cost, composite, general]
- agents_needed: list of agents to call (empty for general)
- confidence: 0.0 to 1.0
- reasoning: brief explanation
"""


async def classify_query(llm, query: str) -> QueryClassification:
    """Classify a query to determine routing."""
    prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
    
    # Use structured output if available, otherwise parse manually
    try:
        structured_llm = llm.with_structured_output(QueryClassification)
        result = await structured_llm.ainvoke(prompt.format(query=query))
        return result
    except Exception as e:
        logger.warning(f"Structured output failed, using fallback: {e}")
        # Fallback: simple keyword-based classification
        query_lower = query.lower()
        
        if any(w in query_lower for w in ["metric", "performance", "slow", "sql", "wait"]):
            return QueryClassification(
                category="performance",
                agents_needed=["performance"],
                confidence=0.8,
                reasoning="Query contains performance-related keywords"
            )
        elif any(w in query_lower for w in ["block", "error", "fix", "heal", "kill", "extend"]):
            return QueryClassification(
                category="healing",
                agents_needed=["healing"],
                confidence=0.8,
                reasoning="Query contains healing-related keywords"
            )
        elif any(w in query_lower for w in ["cost", "spend", "budget", "idle", "utilization"]):
            return QueryClassification(
                category="cost",
                agents_needed=["cost"],
                confidence=0.8,
                reasoning="Query contains cost-related keywords"
            )
        elif any(w in query_lower for w in ["health", "complete", "overview", "status", "all"]):
            return QueryClassification(
                category="composite",
                agents_needed=["performance", "healing", "cost"],
                confidence=0.8,
                reasoning="Query requires comprehensive analysis"
            )
        else:
            return QueryClassification(
                category="general",
                agents_needed=[],
                confidence=0.7,
                reasoning="No specific category detected"
            )


# ============================================================================
# Orchestrator State
# ============================================================================

class OrchestratorState(TypedDict):
    """State for the orchestrator graph."""
    query: str
    classification: Optional[QueryClassification]
    performance_result: Optional[str]
    healing_result: Optional[str]
    cost_result: Optional[str]
    final_response: Optional[str]
    error: Optional[str]


# ============================================================================
# Multi-Agent Orchestrator
# ============================================================================

class ODAOSOrchestrator:
    """Multi-Agent Orchestrator for ODAOS.
    
    Coordinates Performance, Self-Healing, and Cost optimization agents
    to provide unified database operations assistance.
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        temperature: float = 0.0,
        enable_memory: bool = True,
    ):
        """Initialize the orchestrator with all specialized agents."""
        self.llm = create_llm(provider=provider, temperature=temperature)
        self.memory = MemorySaver() if enable_memory else None
        
        # Initialize specialized agents
        self._performance_agent = None
        self._healing_agent = None
        self._cost_agent = None
        
        # Build the orchestration graph
        self.graph = self._build_graph()
        self._thread_id = "orchestrator-default"
        
        logger.info("ODAOS Orchestrator initialized")
    
    @property
    def performance_agent(self) -> PerformanceAgent:
        """Lazy-load performance agent."""
        if self._performance_agent is None:
            self._performance_agent = PerformanceAgent(enable_memory=False)
        return self._performance_agent
    
    @property
    def healing_agent(self) -> SelfHealingAgent:
        """Lazy-load self-healing agent."""
        if self._healing_agent is None:
            self._healing_agent = SelfHealingAgent(enable_memory=False)
        return self._healing_agent
    
    @property
    def cost_agent(self) -> CostOptimizationAgent:
        """Lazy-load cost optimization agent."""
        if self._cost_agent is None:
            self._cost_agent = CostOptimizationAgent(enable_memory=False)
        return self._cost_agent
    
    def _build_graph(self) -> StateGraph:
        """Build the orchestration state graph."""
        graph = StateGraph(OrchestratorState)
        
        # Add nodes
        graph.add_node("classify", self._classify_node)
        graph.add_node("performance", self._performance_node)
        graph.add_node("healing", self._healing_node)
        graph.add_node("cost", self._cost_node)
        graph.add_node("synthesize", self._synthesize_node)
        graph.add_node("general", self._general_node)
        
        # Set entry point
        graph.set_entry_point("classify")
        
        # Add conditional routing
        graph.add_conditional_edges(
            "classify",
            self._route_by_classification,
            {
                "performance": "performance",
                "healing": "healing",
                "cost": "cost",
                "composite": "performance",  # Start with performance for composite
                "general": "general",
            }
        )
        
        # Agent nodes go to synthesize
        graph.add_edge("performance", "synthesize")
        graph.add_edge("healing", "synthesize")
        graph.add_edge("cost", "synthesize")
        graph.add_edge("general", END)
        graph.add_edge("synthesize", END)
        
        return graph.compile(checkpointer=self.memory)
    
    async def _classify_node(self, state: OrchestratorState) -> dict:
        """Classify the query to determine routing."""
        classification = await classify_query(self.llm, state["query"])
        return {"classification": classification}
    
    def _route_by_classification(self, state: OrchestratorState) -> str:
        """Route based on classification."""
        classification = state.get("classification")
        if classification:
            return classification.category
        return "general"
    
    async def _performance_node(self, state: OrchestratorState) -> dict:
        """Call the performance agent."""
        try:
            result = await self.performance_agent.chat(state["query"])
            
            # For composite queries, also call other agents
            classification = state.get("classification")
            if classification and classification.category == "composite":
                # Continue with healing if needed
                if "healing" in classification.agents_needed:
                    healing_result = await self.healing_agent.chat(state["query"])
                    state["healing_result"] = healing_result
                if "cost" in classification.agents_needed:
                    cost_result = await self.cost_agent.chat(state["query"])
                    state["cost_result"] = cost_result
            
            return {"performance_result": result}
        except Exception as e:
            logger.error(f"Performance agent error: {e}")
            return {"error": str(e)}
    
    async def _healing_node(self, state: OrchestratorState) -> dict:
        """Call the self-healing agent."""
        try:
            result = await self.healing_agent.chat(state["query"])
            return {"healing_result": result}
        except Exception as e:
            logger.error(f"Healing agent error: {e}")
            return {"error": str(e)}
    
    async def _cost_node(self, state: OrchestratorState) -> dict:
        """Call the cost optimization agent."""
        try:
            result = await self.cost_agent.chat(state["query"])
            return {"cost_result": result}
        except Exception as e:
            logger.error(f"Cost agent error: {e}")
            return {"error": str(e)}
    
    async def _general_node(self, state: OrchestratorState) -> dict:
        """Handle general queries."""
        response = """Hello! I'm ODAOS, your Oracle Database AI Operations System.

I can help you with:
- **Performance Analysis**: Database metrics, slow SQL queries, wait events
- **Self-Healing Operations**: Error detection, blocking sessions, remediation
- **Cost Optimization**: OCI costs, resource utilization, savings opportunities

Try asking me things like:
- "How is my database performing?"
- "Are there any blocking sessions?"
- "What are our top cost categories?"
- "Give me a complete health check"

What would you like to know?"""
        return {"final_response": response}
    
    async def _synthesize_node(self, state: OrchestratorState) -> dict:
        """Synthesize results from multiple agents."""
        parts = []
        
        classification = state.get("classification")
        if classification and classification.category == "composite":
            parts.append("# 📊 ODAOS Comprehensive Analysis\n")
        
        if state.get("performance_result"):
            if classification and classification.category == "composite":
                parts.append("## Performance Analysis\n")
            parts.append(state["performance_result"])
        
        if state.get("healing_result"):
            if classification and classification.category == "composite":
                parts.append("\n---\n## Self-Healing Assessment\n")
            parts.append(state["healing_result"])
        
        if state.get("cost_result"):
            if classification and classification.category == "composite":
                parts.append("\n---\n## Cost Optimization\n")
            parts.append(state["cost_result"])
        
        if state.get("error"):
            parts.append(f"\n⚠️ Error during analysis: {state['error']}")
        
        return {"final_response": "\n".join(parts) if parts else "I couldn't generate a response."}
    
    async def chat(self, message: str, thread_id: Optional[str] = None) -> str:
        """Send a message to the orchestrator and get a response."""
        config = {"configurable": {"thread_id": thread_id or self._thread_id}}
        
        initial_state = OrchestratorState(
            query=message,
            classification=None,
            performance_result=None,
            healing_result=None,
            cost_result=None,
            final_response=None,
            error=None,
        )
        
        logger.info(f"Orchestrator processing: {message[:50]}...")
        result = await self.graph.ainvoke(initial_state, config=config)
        
        return result.get("final_response") or "I was unable to process your request."
    
    def chat_sync(self, message: str, thread_id: Optional[str] = None) -> str:
        """Synchronous version of chat."""
        return asyncio.run(self.chat(message, thread_id))
    
    async def health_check(self) -> str:
        """Perform a complete database health check using all agents."""
        return await self.chat(
            "Perform a comprehensive database health check: "
            "analyze performance metrics, check for incidents or blocking sessions, "
            "and review cost optimization opportunities."
        )
    
    def new_conversation(self, thread_id: Optional[str] = None) -> str:
        """Start a new conversation thread."""
        if thread_id:
            self._thread_id = thread_id
        else:
            self._thread_id = f"orch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        logger.info(f"New conversation started: {self._thread_id}")
        return self._thread_id


# ============================================================================
# Quick Test Function
# ============================================================================

async def quick_test():
    """Quick test of the orchestrator."""
    orchestrator = ODAOSOrchestrator()
    
    print("\n" + "="*60)
    print("ODAOS Orchestrator Quick Test")
    print("="*60)
    
    print("\n[Test 1] General query...")
    response = await orchestrator.chat("Hello, what can you do?")
    print(f"\nResponse:\n{response[:500]}...")
    
    return response


if __name__ == "__main__":
    asyncio.run(quick_test())
