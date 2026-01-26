"""
Document retriever for vector store operations.

This module handles document retrieval from the vector store
with support for various search strategies including hybrid search and reranking.
"""

import logging
import json
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from schemas import RetrievedContext, RetrievedChunk
from vectorstore import ChromaManager

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """Handles document retrieval from vector store."""
    
    def __init__(self, collection_name: str):
        """
        Initialize document retriever.
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.collection_name = collection_name
        self.retriever = ChromaManager(collection_name=collection_name)
    
    async def retrieve(
        self,
        query: str,
        k: int | None = None,
        search_type: str | None = None,
        lambda_mult: float | None = None,
    ) -> Optional[RetrievedContext]:
        """
        Retrieve documents from vector store asynchronously.
        
        Args:
            query: Search query
            k: Number of documents to retrieve (defaults to config)
            search_type: Type of search (defaults to config)
            lambda_mult: MMR lambda parameter (defaults to config)
            
        Returns:
            Retrieved context or None if retrieval fails
        """
        # Use config defaults
        k = k or settings.vectorstore.retrieval_k
        search_type = search_type or settings.vectorstore.search_type
        lambda_mult = lambda_mult if lambda_mult is not None else settings.vectorstore.mmr_lambda
        
        logger.info(f"[RAG] Retrieving documents for: {query}")
        
        try:
            retrieved_docs = await self.retriever.retrieve(
                query,
                k=k,
                search_type=search_type,
                lambda_mult=lambda_mult,
            )
            
            if not retrieved_docs:
                logger.warning("[RAG] No documents retrieved")
                return None
            
            # Build chunks with per-document metadata
            chunks = [
                RetrievedChunk(
                    content=doc["content"],
                    page_number=doc.get("page_number"),
                    source_file=doc.get("source", "unknown"),
                    category=doc.get("category"),
                )
                for doc in retrieved_docs
            ]
            
            # Extract unique page numbers and source files
            unique_page_numbers = self.retriever.extract_page_numbers(retrieved_docs)
            source_files = self.retriever.extract_source_files(retrieved_docs)
            
            context = RetrievedContext(
                chunks=chunks,
                unique_page_numbers=unique_page_numbers,
                source_files=source_files,
            )
            
            logger.info(f"[RAG] Retrieved {len(chunks)} chunks, unique pages: {unique_page_numbers}")
            
            return context
            
        except Exception as e:
            logger.error(f"[RAG] Error: {str(e)}")
            raise

    async def retrieve_hybrid(
        self,
        query: str,
        k: int | None = None,
        semantic_weight: float = 0.6,
        lexical_weight: float = 0.4,
    ) -> Optional[RetrievedContext]:
        """
        Retrieve using hybrid search (semantic + lexical).
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            semantic_weight: Weight for semantic search
            lexical_weight: Weight for lexical search
            
        Returns:
            Retrieved context or None
        """
        k = k or settings.vectorstore.retrieval_k
        logger.info(f"[RAG] Hybrid retrieval for: {query}")
        
        try:
            retrieved_docs = await self.retriever.hybrid_retrieve(
                query=query,
                k=k,
                semantic_weight=semantic_weight,
                lexical_weight=lexical_weight,
            )
            
            if not retrieved_docs:
                logger.warning("[RAG] No documents in hybrid search")
                return None
            
            chunks = [
                RetrievedChunk(
                    content=doc["content"],
                    page_number=doc.get("page_number"),
                    source_file=doc.get("source", "unknown"),
                    category=doc.get("category"),
                )
                for doc in retrieved_docs
            ]
            
            unique_page_numbers = self.retriever.extract_page_numbers(retrieved_docs)
            source_files = self.retriever.extract_source_files(retrieved_docs)
            
            context = RetrievedContext(
                chunks=chunks,
                unique_page_numbers=unique_page_numbers,
                source_files=source_files,
            )
            
            logger.info(f"[RAG] Hybrid search: {len(chunks)} chunks")
            return context
            
        except Exception as e:
            logger.error(f"[RAG] Hybrid error: {str(e)}")
            raise

    async def retrieve_and_rerank(
        self,
        query: str,
        k: int | None = None,
        rerank_top_k: int = 5,
        use_hybrid: bool = False,
    ) -> Optional[RetrievedContext]:
        """
        Retrieve and rerank by LLM relevance.
        
        Args:
            query: Search query
            k: Number of documents to retrieve initially
            rerank_top_k: Number of top documents after reranking
            use_hybrid: Whether to use hybrid search
            
        Returns:
            Retrieved context with reranked chunks
        """
        if use_hybrid:
            context = await self.retrieve_hybrid(query=query, k=k or settings.vectorstore.retrieval_k * 2)
        else:
            context = await self.retrieve(query=query, k=k or settings.vectorstore.retrieval_k * 2)
        
        if not context or not context.chunks:
            return context
        
        logger.info(f"[RAG] Reranking {len(context.chunks)} chunks")
        reranked_chunks = await self.rerank_chunks(
            query=query,
            chunks=context.chunks,
            top_k=rerank_top_k,
        )
        
        return RetrievedContext(
            chunks=reranked_chunks,
            unique_page_numbers=context.unique_page_numbers,
            source_files=context.source_files,
            images=context.images,
            images_justification=context.images_justification,
        )

    async def rerank_chunks(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """
        Rerank retrieved chunks using LLM relevance scoring.
        
        Args:
            query: Search query
            chunks: List of retrieved chunks
            top_k: Number of top chunks to return
            
        Returns:
            Reranked list of chunks
        """
        if not chunks:
            return []
        
        if len(chunks) <= top_k:
            return chunks
        
        logger.info(f"[RAG] Reranking {len(chunks)} chunks...")
        
        try:
            llm = ChatOpenAI(
                model=settings.llm.model,
                temperature=0.0,  # Deterministic scoring
            )
            
            # Format chunks for LLM evaluation
            chunks_text = "\n\n".join([
                f"[Chunk {i+1}] (Page {c.page_number}, {c.source_file})\n{c.content[:300]}..."
                for i, c in enumerate(chunks)
            ])
            
            prompt = ChatPromptTemplate.from_template(
                """Given the user query and retrieved chunks, score each chunk's relevance to the query.
                
Query: {query}

Chunks:
{chunks}

Return a JSON list with chunk indices and relevance scores (0-1), sorted by score descending.
Example: [{"chunk_index": 0, "score": 0.95}, ...]

JSON:"""
            )
            
            response = await llm.ainvoke(prompt.format_prompt(
                query=query,
                chunks=chunks_text
            ).to_messages())
            
            # Parse scores
            try:
                scores = json.loads(response.content)
                ranked_chunks = []
                for item in scores[:top_k]:
                    idx = item.get("chunk_index", 0)
                    if 0 <= idx < len(chunks):
                        ranked_chunks.append(chunks[idx])
                
                logger.info(f"[RAG] Reranked to top {len(ranked_chunks)} chunks")
                return ranked_chunks
            except json.JSONDecodeError:
                logger.warning("[RAG] Could not parse LLM reranking response")
                return chunks[:top_k]
                
        except Exception as e:
            logger.error(f"[RAG] Reranking error: {str(e)}")
            return chunks[:top_k]
