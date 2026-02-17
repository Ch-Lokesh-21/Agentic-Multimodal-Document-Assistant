"""Message utility functions for conversation history optimization."""

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
    encoding = _get_encoding(settings.llm.model)
    
    total_tokens = 0
    
    for message in messages:
        content = str(message.content)
        total_tokens += len(encoding.encode(content))
        total_tokens += 4
    
    total_tokens += 2
    
    return total_tokens


def get_trimmed_messages(
    messages: Sequence[AnyMessage],
    max_messages: int | None = None,
    max_tokens: int | None = None,
    strategy: str | None = None,
    include_system: bool = True,
) -> list[BaseMessage]:
    """Trim conversation history to fit within token/message limits."""
    if not messages:
        return []
    
    max_messages = max_messages or settings.llm.max_history_messages
    max_tokens = max_tokens or settings.llm.max_history_tokens
    strategy = strategy or settings.llm.history_strategy
    
    messages_list = list(messages)
    original_count = len(messages_list)
    
    if len(messages_list) > max_messages:
        if strategy == "last":
            system_msgs = [m for m in messages_list if isinstance(m, SystemMessage)]
            non_system = [m for m in messages_list if not isinstance(m, SystemMessage)]
            
            if include_system and system_msgs:
                remaining_slots = max_messages - len(system_msgs)
                messages_list = system_msgs + non_system[-remaining_slots:]
            else:
                messages_list = non_system[-max_messages:]
        else:
            messages_list = messages_list[:max_messages]
    
    try:
        trimmer = trim_messages(
            max_tokens=max_tokens,
            strategy=strategy,
            token_counter=_estimate_tokens,
            include_system=include_system,
            allow_partial=False,
            start_on="human",
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
        logger.warning(f"[HISTORY] Token trimming failed, using count limit: {e}")
        return messages_list[-max_messages:]


def format_history_for_prompt(
    messages: Sequence[AnyMessage],
    max_messages: int | None = None,
    truncate_content: int = 500,
) -> str:
    """Format conversation history as a string for inclusion in prompts."""
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
    """Get a summary of conversation history for logging/debugging."""
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
