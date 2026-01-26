"""
Node creation functions for the RAG workflow graph.

This module provides factory functions for creating workflow nodes.
"""

import logging
from langchain_core.messages import HumanMessage
from langsmith import traceable

from config import settings
from schemas import GraphState, VisualDecision

logger = logging.getLogger(__name__)


def create_add_user_message_node(session_id: str):
    """Create a node that adds user message to state."""
    @traceable(name="add_user_message_node", metadata={"session_id": session_id, "step": "add_user_message"})
    async def add_user_message_node(state: GraphState) -> dict:
        """Add user's query as a HumanMessage to conversation history."""
        query = state.get("query", "")
        
        return {
            "messages": [HumanMessage(content=query)],
        }
    
    return add_user_message_node


def create_rag_retrieve_node(doc_retriever, session_id: str):
    """Create a RAG retrieval node."""
    @traceable(name="rag_retrieve_node", metadata={"session_id": session_id, "step": "rag_retrieval"})
    async def rag_retrieve_node(state: GraphState) -> dict:
        """Retrieve documents from vector store asynchronously."""
        query = state.get("query", "")
        query_analysis = state.get("query_analysis")
        
        try:
            # Detect if this is a complex query
            is_complex = (
                query_analysis is not None and
                query_analysis.classification == "complex"
            )
            
            # Complex query with hybrid + reranking
            if is_complex and settings.vectorstore.enable_hybrid_search:
                logger.info("[RAG] Complex query - using hybrid search + reranking")
                if settings.vectorstore.enable_reranking:
                    retrieved_context = await doc_retriever.retrieve_and_rerank(
                        query=query,
                        k=settings.vectorstore.retrieval_k * 2,
                        rerank_top_k=settings.vectorstore.rerank_top_k,
                        use_hybrid=True,
                    )
                else:
                    retrieved_context = await doc_retriever.retrieve_hybrid(
                        query=query,
                        k=settings.vectorstore.retrieval_k,
                        semantic_weight=settings.vectorstore.hybrid_semantic_weight,
                        lexical_weight=settings.vectorstore.hybrid_lexical_weight,
                    )
            # Complex query with reranking only
            elif is_complex and settings.vectorstore.enable_reranking:
                logger.info("[RAG] Complex query - using standard retrieval + reranking")
                retrieved_context = await doc_retriever.retrieve_and_rerank(
                    query=query,
                    k=settings.vectorstore.retrieval_k * 2,
                    rerank_top_k=settings.vectorstore.rerank_top_k,
                    use_hybrid=False,
                )
            else:
                logger.info("[RAG] Simple query - using standard retrieval")
                retrieved_context = await doc_retriever.retrieve(
                    query=query,
                    k=settings.vectorstore.retrieval_k,
                    search_type=settings.vectorstore.search_type,
                    lambda_mult=settings.vectorstore.mmr_lambda,
                )
            
            if not retrieved_context:
                return {"retrieved_context": None}
            
            return {"retrieved_context": retrieved_context}
            
        except Exception as e:
            logger.error(f"[RAG] Error: {str(e)}")
            return {
                "error_message": f"RAG retrieval failed: {str(e)}",
                "route": "web_search",
            }
    
    return rag_retrieve_node


def create_retrieve_images_node(img_retriever, session_id: str):
    """Create an image retrieval node."""
    @traceable(name="retrieve_images_node", metadata={"session_id": session_id, "step": "image_retrieval"})
    async def retrieve_images_node(state: GraphState) -> dict:
        """Generate PDF page images using ImageRetriever asynchronously."""
        visual_decision: VisualDecision | None = state.get("visual_decision")
        retrieved_context = state.get("retrieved_context")
        query = state.get("query", "")
        
        if not visual_decision or not visual_decision.requires_visual:
            return {}
        
        if not retrieved_context:
            logger.info("[IMAGES] No retrieved context available")
            return {}
        
        try:
            # Use config values via retriever defaults
            updated_context = await img_retriever.retrieve(
                retrieved_context=retrieved_context,
                query=query,
                max_images=settings.image.max_images,
                max_pages=settings.image.max_pages,
            )
            
            if updated_context:
                return {"retrieved_context": updated_context}
            else:
                return {}
                
        except Exception as e:
            logger.error(f"[IMAGES] Error: {str(e)}")
            return {}
    
    return retrieve_images_node
