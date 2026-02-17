"""Routing agent for query classification and path selection."""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from rag_system.core.base_agent import BaseAgent
from rag_system.prompts import ROUTING_PROMPT
from rag_system.utils.message_utils import (
    get_trimmed_messages,
    format_history_for_prompt,
    get_history_summary,
)
from schemas import GraphState, RoutingDecision

logger = logging.getLogger(__name__)


class RoutingAgent(BaseAgent):
    """Agent responsible for routing queries to appropriate handlers."""
    
    @traceable(name="route_query_node", metadata={"step": "routing"})
    async def route_query(self, state: GraphState) -> dict:
        """Route the query to appropriate handler using session history + current query."""
        query = state.get("query", "")
        messages = list(state.get("messages", []))
        
        history_stats = get_history_summary(messages)
        logger.info(f"[ROUTE] Processing query: {query}")
        logger.info(f"[ROUTE] Full history: {history_stats['total']} messages (~{history_stats['estimated_tokens']} tokens)")
        
        trimmed_messages = get_trimmed_messages(messages)
        logger.info(f"[ROUTE] Using trimmed history: {len(trimmed_messages)} messages")
        
        history_context = format_history_for_prompt(trimmed_messages)
        
        structured_llm = self.llm.with_structured_output(RoutingDecision)
        prompt = ChatPromptTemplate.from_template(ROUTING_PROMPT)
        chain = prompt | structured_llm
        
        decision: RoutingDecision = await chain.ainvoke({
            "query": query,
            "history_context": history_context,
        })
        
        logger.info(f"[ROUTE] Decision: {decision.route} (confidence: {decision.confidence:.2f})")
        logger.info(f"[ROUTE] Reasoning: {decision.reasoning}")
        
        return {
            "routing_decision": decision,
            "route": decision.route,
            "intermediate_reasoning": f"\n[ROUTING] {decision.reasoning} (based on {len(messages)} prior messages)",
        }
