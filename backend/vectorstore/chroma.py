import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple
from collections import Counter

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_unstructured import UnstructuredLoader
from langchain_community.vectorstores.utils import filter_complex_metadata

from config import settings

logger = logging.getLogger(__name__)


class ChromaManager:
    """Session-scoped ChromaDB manager with document isolation."""

    def __init__(
        self,
        collection_name: str,
        persist_directory: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """Initialize ChromaDB manager for a session."""
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.vectorstore.persist_directory
        self.embedding_model = embedding_model or settings.embedding.model

        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    async def ingest_pdf(
        self,
        file_path: str,
        use_api: bool | None = None,
    ) -> Tuple[int, int]:
        """Ingest a PDF file into the collection asynchronously."""
        use_api = use_api if use_api is not None else settings.chunking.use_api

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Ingesting PDF: {file_path}")

        docs, page_numbers = await asyncio.to_thread(
            self._load_and_process_pdf,
            file_path,
            use_api
        )

        if not docs:
            raise ValueError(f"No content extracted from: {file_path}")

        await asyncio.to_thread(
            self.vectorstore.add_documents,
            documents=docs
        )

        chunk_count = len(docs)
        page_count = len(page_numbers) if page_numbers else None

        logger.info(f"Ingested {chunk_count} chunks from {file_path.name}")

        return chunk_count, page_count

    def _load_and_process_pdf(self, file_path: Path, use_api: bool) -> Tuple[list, set]:
        """Synchronous PDF loading helper for thread pool execution."""
        loader = UnstructuredLoader(
            file_path=str(file_path),

            strategy=settings.chunking.partition_strategy,
            partition_via_api=use_api,
            infer_table_structure=True,

            chunking_strategy=settings.chunking.strategy,

            max_characters=settings.chunking.max_characters,
            new_after_n_chars=settings.chunking.new_after_n_chars,
            combine_text_under_n_chars=settings.chunking.combine_under_n_chars,
        )

        docs = []
        page_numbers = set()

        for doc in loader.lazy_load():
            docs.append(doc)
            page_num = doc.metadata.get("page_number")
            if page_num is not None:
                page_numbers.add(page_num)

        docs = filter_complex_metadata(docs)

        for doc in docs:
            doc.metadata["source_file"] = file_path.name
            doc.metadata["source_path"] = str(file_path)

        return docs, page_numbers

    async def retrieve(
        self,
        query: str,
        k: int | None = None,
        search_type: str | None = None,
        lambda_mult: float | None = None,
    ) -> list[dict]:
        """
        Retrieve documents using MMR search asynchronously.

        Args:
            query: Search query
            k: Number of documents to retrieve (defaults to config)
            search_type: Search type (defaults to config)
            lambda_mult: MMR diversity parameter (defaults to config)

        Returns:
            List of retrieved document dicts
        """
        k = k or settings.vectorstore.retrieval_k
        search_type = search_type or settings.vectorstore.search_type
        lambda_mult = lambda_mult if lambda_mult is not None else settings.vectorstore.mmr_lambda

        retriever = self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k, "lambda_mult": lambda_mult},
        )

        docs = await asyncio.to_thread(retriever.invoke, query)

        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "page_number": doc.metadata.get("page_number"),
                "source": doc.metadata.get("source_file", "unknown"),
                "category": doc.metadata.get("category"),
                "metadata": doc.metadata,
            })

        return results

    async def hybrid_retrieve(
        self,
        query: str,
        k: int | None = None,
        semantic_weight: float = 0.6,
        lexical_weight: float = 0.4,
    ) -> list[dict]:
        """Retrieve documents using hybrid search (semantic + BM25 lexical)."""
        k = k or settings.vectorstore.retrieval_k

        semantic_results = await self.retrieve(query=query, k=k*2)

        lexical_results = await self._bm25_search(query=query, k=k*2)

        combined = self._reciprocal_rank_fusion(
            semantic_results=semantic_results,
            lexical_results=lexical_results,
            semantic_weight=semantic_weight,
            lexical_weight=lexical_weight,
            k=k,
        )

        logger.info(
            f"Hybrid search: {len(combined)} results (semantic + BM25)")
        return combined

    async def _bm25_search(self, query: str, k: int) -> list[dict]:
        """Perform BM25 lexical search (fallback to all docs sorted by word overlap)."""
        try:
            all_docs = await asyncio.to_thread(
                self.vectorstore._collection.get,
                include=["documents", "metadatas"]
            )

            if not all_docs["documents"]:
                return []

            query_words = set(query.lower().split())
            scored_docs = []

            for i, doc_text in enumerate(all_docs["documents"]):
                doc_words = set(doc_text.lower().split())
                overlap = len(query_words & doc_words)
                metadata = all_docs["metadatas"][i] if all_docs["metadatas"] else {
                }

                if overlap > 0:
                    scored_docs.append({
                        "content": doc_text,
                        "score": overlap / len(query_words) if query_words else 0,
                        "page_number": metadata.get("page_number"),
                        "source": metadata.get("source_file", "unknown"),
                        "category": metadata.get("category"),
                        "metadata": metadata,
                    })

            scored_docs.sort(key=lambda x: x["score"], reverse=True)
            return scored_docs[:k]

        except Exception as e:
            logger.error(f"BM25 search error: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        semantic_results: list[dict],
        lexical_results: list[dict],
        semantic_weight: float,
        lexical_weight: float,
        k: int,
    ) -> list[dict]:
        """Combine semantic and lexical results using RRF scoring."""
        scores = {}
        content_map = {}

        for rank, doc in enumerate(semantic_results, 1):
            content = doc["content"]
            rrf_score = 1.0 / (rank + 60)  
            scores[content] = scores.get(
                content, 0) + (rrf_score * semantic_weight)
            content_map[content] = doc

        for rank, doc in enumerate(lexical_results, 1):
            content = doc["content"]
            rrf_score = 1.0 / (rank + 60)
            scores[content] = scores.get(
                content, 0) + (rrf_score * lexical_weight)
            content_map[content] = doc

        sorted_results = sorted(
            [(content, scores[content]) for content in scores],
            key=lambda x: x[1],
            reverse=True
        )[:k]

        return [content_map[content] for content, _ in sorted_results]

    def build_context(self, retrieved_docs: list[dict]) -> str:
        """
        Build formatted context string from retrieved documents.

        Args:
            retrieved_docs: List of retrieved document dicts

        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No relevant context found."

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc.get("source", "unknown")
            page = doc.get("page_number", "?")
            content = doc.get("content", "")

            section = f"[Document {i}] ({source}, page {page})\n{content}"
            context_parts.append(section)

        return "\n\n".join(context_parts)

    def extract_page_numbers(self, retrieved_docs: list[dict]) -> list[int]:
        """Extract unique page numbers from retrieved documents."""
        page_numbers = set()
        for doc in retrieved_docs:
            page = doc.get("page_number")
            if page is not None:
                page_numbers.add(page)
        return sorted(list(page_numbers))

    def extract_source_files(self, retrieved_docs: list[dict]) -> list[str]:
        """Extract unique source file names from retrieved documents."""
        sources = set()
        for doc in retrieved_docs:
            source = doc.get("source")
            if source:
                sources.add(source)
        return list(sources)

    async def delete_by_source(self, source_file: str) -> int:
        """
        Delete all documents from a specific source file asynchronously.

        Args:
            source_file: Source filename to delete

        Returns:
            Number of documents deleted
        """
        try:
            results = await asyncio.to_thread(
                self.vectorstore._collection.get,
                where={"source_file": source_file}
            )

            if results and results["ids"]:
                await asyncio.to_thread(
                    self.vectorstore._collection.delete,
                    ids=results["ids"]
                )
                return len(results["ids"])

            return 0

        except Exception as e:
            logger.warning(f"Error deleting documents: {e}")
            return 0

    async def delete_collection(self) -> bool:
        """
        Delete the entire collection asynchronously.

        Returns:
            True if deleted successfully
        """
        try:
            await asyncio.to_thread(
                self.vectorstore._client.delete_collection,
                self.collection_name
            )
            return True
        except Exception as e:
            logger.warning(f"Error deleting collection: {e}")
            return False

    async def get_document_count(self) -> int:
        """Get total number of documents in collection asynchronously."""
        try:
            return await asyncio.to_thread(self.vectorstore._collection.count)
        except Exception:
            return 0


def get_chroma_manager(session_id: str) -> ChromaManager:
    """
    Factory function to get ChromaManager for a session.

    Args:
        session_id: Session identifier (used as collection name)

    Returns:
        ChromaManager instance
    """
    return ChromaManager(collection_name=session_id)
