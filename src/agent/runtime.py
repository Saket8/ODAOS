"""ODAOS Agent Runtime.

LangGraph-based agent that orchestrates tool execution and reasoning.
Uses the LLM provider abstraction to work with any supported LLM.
"""
from typing import Annotated, TypedDict, Sequence
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END

from ..core.providers import create_llm


class AgentState(TypedDict):
    """State maintained across agent execution steps."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_task: str
    tool_results: list


# System prompt for the ODAOS DBA Agent
SYSTEM_PROMPT = """You are ODAOS (Oracle Database Autonomous Operations Suite), an expert Oracle DBA AI agent.

Your capabilities include:
1. **Performance Analysis**: Analyze AWR/ASH reports, SQL tuning, execution plans
2. **Self-Healing Operations**: Monitor alerts, extend tablespaces, manage blocking sessions
3. **Cost Optimization**: Analyze utilization, recommend rightsizing, forecast costs

When responding:
- Be concise and actionable
- Provide specific Oracle commands or SQL when relevant
- Explain your reasoning for complex diagnostics
- Always consider the safety implications of any database changes

You have access to MCP tools for database operations. Use them when needed.
"""


class ODAOSAgent:
    """ODAOS Agent Runtime using LangGraph for orchestration."""
    
    def __init__(self, provider: str = None, temperature: float = 0.1):
        """Initialize the agent with the specified LLM provider.
        
        Args:
            provider: LLM provider name. If None, uses environment config.
            temperature: Model temperature for responses.
        """
        self.llm = create_llm(provider=provider, temperature=temperature)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])
        self.chain = self.prompt | self.llm
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for agent execution."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tools_node)
        
        # Define edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END,
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    async def _agent_node(self, state: AgentState) -> dict:
        """Process agent reasoning step."""
        messages = state["messages"]
        response = await self.chain.ainvoke({"messages": messages})
        return {"messages": [response]}
    
    async def _tools_node(self, state: AgentState) -> dict:
        """Execute tool calls from agent response."""
        # For now, return empty - tools will be implemented in MCP servers
        return {"tool_results": []}
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if agent should continue to tools or end."""
        last_message = state["messages"][-1]
        
        # Check if there are tool calls in the response
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"
    
    async def chat(self, user_message: str, history: list[BaseMessage] = None) -> str:
        """Send a message to the agent and get a response.
        
        Args:
            user_message: The user's input message.
            history: Optional conversation history.
        
        Returns:
            The agent's response text.
        """
        messages = history or []
        messages.append(HumanMessage(content=user_message))
        
        initial_state = AgentState(
            messages=messages,
            current_task="",
            tool_results=[],
        )
        
        result = await self.graph.ainvoke(initial_state)
        
        # Get the last AI message
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "No response generated."
    
    def chat_sync(self, user_message: str, history: list[BaseMessage] = None) -> str:
        """Synchronous version of chat for simple use cases."""
        import asyncio
        return asyncio.run(self.chat(user_message, history))


async def quick_test():
    """Quick test function to validate agent setup."""
    agent = ODAOSAgent()
    response = await agent.chat("What can you help me with as an Oracle DBA?")
    return response


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(quick_test())
    print(result)
