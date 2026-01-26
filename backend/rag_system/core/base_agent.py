"""
Base agent class for all RAG system agents.

This module provides the foundational agent class with common
LLM initialization and configuration.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from config import settings


class BaseAgent:
    """
    Base class for all agents with common LLM initialization.
    
    Attributes:
        model: LLM model name
        session_id: Session ID for tracking
        llm: Initialized ChatOpenAI instance
    """
    
    def __init__(self, model: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize base agent with LLM configuration.
        
        Args:
            model: LLM model name (defaults to config)
            session_id: Session ID for tracking
        """
        self.model = model or settings.llm.model
        self.session_id = session_id
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=settings.llm.temperature,
        )
