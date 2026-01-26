"""
RAG System - Production-ready architecture for document retrieval and question answering.

This module provides a well-structured RAG (Retrieval-Augmented Generation) system
with proper separation of concerns and modular design.
"""

from rag_system.workflow.graph import RAGWorkflow, ragGraph

__all__ = ["RAGWorkflow", "ragGraph"]
