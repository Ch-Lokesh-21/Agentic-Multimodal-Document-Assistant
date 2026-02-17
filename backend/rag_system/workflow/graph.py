"""Main RAG workflow orchestration using LangGraph."""

from rag_system.utils import LightweightCheckpointSerializer
from rag_system.workflow.routes import (
    visual_route,
    query_analysis_route,
    sub_query_loop_route,
    quality_or_collect_route,
    web_answer_route,
)
from rag_system.workflow.nodes import (
    create_rag_retrieve_node,
    create_retrieve_images_node,
    create_add_user_message_node,
)
from rag_system.retrievers import DocumentRetriever, ImageRetriever
from rag_system.agents import (
    VisualDecisionAgent,
    RAGAnswerAgent,
    QualityCheckAgent,
    WebSearchAgent,
    ResponseFormattingAgent,
    QueryAnalyzerAgent,
    SubQueryProcessorAgent,
    SubQueryCollectorAgent,
    AnswerSynthesisAgent,
)
from schemas import GraphState
from config import settings
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import StateGraph, END
import logging
from typing import AsyncGenerator, Optional
from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)


class RAGWorkflow:
    """RAG workflow orchestrator using LangGraph."""

    def __init__(
        self,
        session_id: str,
        collection_name: str,
        model: Optional[str] = None,
    ):
        """Initialize RAG workflow."""
        self.session_id = session_id
        self.collection_name = collection_name
        self.model = model or settings.llm.model

        self.visual_agent = VisualDecisionAgent(
            model=self.model, session_id=session_id)
        self.rag_agent = RAGAnswerAgent(
            model=self.model, session_id=session_id)
        self.quality_agent = QualityCheckAgent()
        self.web_agent = WebSearchAgent(
            model=self.model, session_id=session_id)
        self.formatter_agent = ResponseFormattingAgent()

        self.query_analyzer_agent = QueryAnalyzerAgent(
            model=self.model, session_id=session_id)
        self.sub_query_processor = SubQueryProcessorAgent(
            session_id=session_id)
        self.sub_query_collector = SubQueryCollectorAgent(
            session_id=session_id)
        self.answer_synthesis_agent = AnswerSynthesisAgent(
            model=self.model, session_id=session_id)

        self.doc_retriever = DocumentRetriever(collection_name=collection_name)
        self.img_retriever = ImageRetriever(session_id=session_id)

        self._add_user_message_node = create_add_user_message_node(session_id)
        self._rag_retrieve_node = create_rag_retrieve_node(
            self.doc_retriever, session_id)
        self._retrieve_images_node = create_retrieve_images_node(
            self.img_retriever, session_id)

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with all nodes and edges."""

        workflow = StateGraph(GraphState)

        workflow.add_node("add_user_message", self._add_user_message_node)
        workflow.add_node(
            "analyze_query", self.query_analyzer_agent.analyze_query)
        workflow.add_node("prepare_sub_query",
                          self.sub_query_processor.prepare_sub_query)
        workflow.add_node("collect_sub_query_result",
                          self.sub_query_collector.collect_result)
        workflow.add_node("synthesize_answers",
                          self.answer_synthesis_agent.synthesize_answers)
        workflow.add_node("rag_retrieve", self._rag_retrieve_node)
        workflow.add_node(
            "visual_decide", self.visual_agent.decide_visual_context)
        workflow.add_node("retrieve_images", self._retrieve_images_node)
        workflow.add_node("generate_rag_answer",
                          self.rag_agent.generate_answer)
        workflow.add_node("check_rag_quality",
                          self.quality_agent.check_quality)
        workflow.add_node("web_search", self.web_agent.search)
        workflow.add_node("generate_web_answer",
                          self.web_agent.generate_answer)
        workflow.add_node("format_response",
                          self.formatter_agent.format_response)

        workflow.set_entry_point("add_user_message")

        workflow.add_edge("add_user_message", "analyze_query")

        workflow.add_conditional_edges(
            "analyze_query",
            query_analysis_route,
            {
                "simple_rag": "rag_retrieve",
                "complex_rag": "prepare_sub_query",
                "too_complex": "format_response",
            },
        )

        workflow.add_edge("prepare_sub_query", "rag_retrieve")

        workflow.add_edge("rag_retrieve", "visual_decide")
        workflow.add_conditional_edges(
            "visual_decide",
            visual_route,
            {
                "retrieve_images": "retrieve_images",
                "generate_rag_answer": "generate_rag_answer",
            },
        )
        workflow.add_edge("retrieve_images", "generate_rag_answer")
        workflow.add_edge("generate_rag_answer", "check_rag_quality")

        workflow.add_conditional_edges(
            "check_rag_quality",
            quality_or_collect_route,
            {
                "web_search": "web_search",
                "format_response": "format_response",
                "collect_sub_query": "collect_sub_query_result",
            },
        )

        workflow.add_conditional_edges(
            "collect_sub_query_result",
            sub_query_loop_route,
            {
                "continue_loop": "prepare_sub_query",
                "synthesize": "synthesize_answers",
            },
        )

        workflow.add_edge("synthesize_answers", "format_response")

        workflow.add_edge("web_search", "generate_web_answer")
        workflow.add_conditional_edges(
            "generate_web_answer",
            web_answer_route,
            {
                "format_response": "format_response",
                "collect_sub_query": "collect_sub_query_result",
            },
        )

        workflow.add_edge("format_response", END)

        return workflow

    async def ainvoke(self, query: str) -> dict:
        """Invoke workflow asynchronously with MongoDB checkpointing."""
        initial_state = {"query": query}

        serde = LightweightCheckpointSerializer()
        with MongoDBSaver.from_conn_string(
            conn_string=settings.mongodb.uri.get_secret_value(),
            db_name=settings.mongodb.database,
            collection_name=settings.mongodb.checkpoints_collection,
            serde=serde,
        ) as checkpointer:
            compiled = self.graph.compile(checkpointer=checkpointer)
            result = await compiled.ainvoke(
                initial_state,
                config={
                    "configurable": {"thread_id": self.session_id},
                    "metadata": {"session_id": self.session_id},
                    "run_name": "RAG_Workflow"
                }
            )
            return result

    async def astream(self, query: str) -> AsyncGenerator[dict, None]:
        """Stream workflow execution asynchronously."""
        initial_state = {"query": query}

        serde = LightweightCheckpointSerializer()
        with MongoDBSaver.from_conn_string(
            conn_string=settings.mongodb.uri.get_secret_value(),
            db_name=settings.mongodb.database,
            collection_name=settings.mongodb.checkpoints_collection,
            serde=serde,
        ) as checkpointer:
            compiled = self.graph.compile(checkpointer=checkpointer)
            async for step in compiled.astream(
                initial_state,
                config={
                    "configurable": {"thread_id": self.session_id},
                    "metadata": {"session_id": self.session_id},
                    "run_name": "RAG_Workflow"
                }
            ):
                yield step

    async def invoke(self, query: str) -> dict:
        """Invoke workflow (alias for ainvoke)."""
        return await self.ainvoke(query)


ragGraph = RAGWorkflow
