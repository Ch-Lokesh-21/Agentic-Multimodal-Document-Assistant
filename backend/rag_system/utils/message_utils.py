"""
Message utility functions for conversation history optimization.

This module provides functions to trim and manage conversation history
to prevent unbounded token growth while maintaining context quality.
"""

import logging
from functools import lru_cache
from typing import Sequence

import tiktoken
from langchain_core.messages import (
    AnyMessage,
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    trim_messages,
)

from config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_encoding(model: str):
    """Get tiktoken encoding for a model."""
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        logger.debug(f"Model {model} not found in tiktoken, using cl100k_base")
        return tiktoken.get_encoding("cl100k_base")


def _estimate_tokens(messages: list[BaseMessage]) -> int:
    """Count tokens for messages using tiktoken."""
    # Get cached encoding (fast after first call)
    encoding = _get_encoding(settings.llm.model)
    
    total_tokens = 0
    
    for message in messages:
        # Count tokens in message content
        content = str(message.content)
        total_tokens += len(encoding.encode(content))
        
        # Add overhead for message formatting
        # OpenAI's format uses ~4 tokens per message for role, separators, etc.
        total_tokens += 4
    
    # Add final overhead
    total_tokens += 2
    
    return total_tokens


def get_trimmed_messages(
    messages: Sequence[AnyMessage],
    max_messages: int | None = None,
    max_tokens: int | None = None,
    strategy: str | None = None,
    include_system: bool = True,
) -> list[BaseMessage]:
    """
    Trim conversation history to fit within token/message limits.
    
    Args:
        messages: Sequence of messages to trim
        max_messages: Maximum number of messages (defaults to config)
        max_tokens: Maximum tokens (defaults to config)
        strategy: Trimming strategy (defaults to config)
        include_system: Whether to include system messages
        
    Returns:
        Trimmed list of messages
    """
    if not messages:
        return []
    
    # Use config defaults if not specified
    max_messages = max_messages or settings.llm.max_history_messages
    max_tokens = max_tokens or settings.llm.max_history_tokens
    strategy = strategy or settings.llm.history_strategy
    
    messages_list = list(messages)
    original_count = len(messages_list)
    
    # First, apply message count limit (fast, no tokenization needed)
    if len(messages_list) > max_messages:
        if strategy == "last":
            # Keep system messages + last N messages
            system_msgs = [m for m in messages_list if isinstance(m, SystemMessage)]
            non_system = [m for m in messages_list if not isinstance(m, SystemMessage)]
            
            if include_system and system_msgs:
                # Reserve space for system messages
                remaining_slots = max_messages - len(system_msgs)
                messages_list = system_msgs + non_system[-remaining_slots:]
            else:
                messages_list = non_system[-max_messages:]
        else:
            # Keep first N messages (less common)
            messages_list = messages_list[:max_messages]
    
    # Then apply token-based trimming using LangChain's trim_messages
    # This provides more precise control over context size
    try:
        trimmer = trim_messages(
            max_tokens=max_tokens,
            strategy=strategy,
            token_counter=_estimate_tokens,  # Use simple estimation
            include_system=include_system,
            allow_partial=False,  # Don't truncate individual messages
            start_on="human",  # Ensure we start with a human message for context
        )
        trimmed = trimmer.invoke(messages_list)
        
        final_count = len(trimmed)
        if final_count < original_count:
            logger.info(
                f"[HISTORY] Trimmed messages: {original_count} → {final_count} "
                f"(max_messages={max_messages}, max_tokens={max_tokens})"
            )
        
        return trimmed
        
    except Exception as e:
        # Fallback to simple message count limit if trimming fails
        logger.warning(f"[HISTORY] Token trimming failed, using count limit: {e}")
        return messages_list[-max_messages:]


def format_history_for_prompt(
    messages: Sequence[AnyMessage],
    max_messages: int | None = None,
    truncate_content: int = 500,
) -> str:
    """
    Format conversation history as a string for inclusion in prompts.
    
    Args:
        messages: Sequence of messages to format
        max_messages: Maximum number of messages to include
        truncate_content: Maximum length of message content
        
    Returns:
        Formatted string representation of history
    """
    if not messages:
        return "No prior conversation history."
    
    max_messages = max_messages or settings.llm.max_history_messages
    recent = list(messages)[-max_messages:]
    
    lines = ["Recent conversation history:"]
    
    for msg in recent:
        if isinstance(msg, HumanMessage):
            role = "User"
        elif isinstance(msg, AIMessage):
            role = "Assistant"
        elif isinstance(msg, SystemMessage):
            role = "System"
        else:
            role = "Unknown"
        
        content = str(msg.content)
        if len(content) > truncate_content:
            content = content[:truncate_content] + "..."
        
        lines.append(f"- {role}: {content}")
    
    return "\n".join(lines)


def get_history_summary(messages: Sequence[AnyMessage]) -> dict:
    """
    Get a summary of conversation history for logging/debugging.
    
    Args:
        messages: Sequence of messages to summarize
        
    Returns:
        Dictionary with summary statistics
    """
    if not messages:
        return {"total": 0, "human": 0, "ai": 0, "system": 0, "estimated_tokens": 0}
    
    human_count = sum(1 for m in messages if isinstance(m, HumanMessage))
    ai_count = sum(1 for m in messages if isinstance(m, AIMessage))
    system_count = sum(1 for m in messages if isinstance(m, SystemMessage))
    
    return {
        "total": len(messages),
        "human": human_count,
        "ai": ai_count,
        "system": system_count,
        "estimated_tokens": _estimate_tokens(list(messages)),
    }
