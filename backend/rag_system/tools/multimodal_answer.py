"""
Multimodal answer generation tool.

This module provides utilities for generating answers
using both text and image context via vision models.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from config import settings
from rag_system.prompts import build_multimodal_prompt


async def generate_multimodal_answer(
    query: str,
    context_text: str,
    images: list[str],
    images_justification: str = "",
    history_context: str = "",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
):
    """
    Generate answer using both text and image context via vision model.
    
    Args:
        query: User's question
        context_text: Retrieved text context
        images: List of base64-encoded images
        images_justification: Explanation of image selection
        history_context: Formatted conversation history
        model: LLM model name (defaults to config)
        temperature: Temperature for generation (defaults to config)
        max_tokens: Maximum tokens (defaults to config)
        
    Returns:
        LLM response with answer
    """
    # Build multimodal message content
    prompt_text = build_multimodal_prompt(
        query=query,
        context_text=context_text,
        num_images=len(images),
        images_justification=images_justification,
        history_context=history_context,
    )
    
    content = [{"type": "text", "text": prompt_text}]
    
    # Add images to the message (limit from config)
    max_images = settings.image.max_images
    for idx, img_base64 in enumerate(images[:max_images]):
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_base64}",
                "detail": settings.image.detail_level,
            },
        })
    
    # Use vision-capable model
    vision_llm = ChatOpenAI(
        model=model or settings.llm.model,
        temperature=temperature or settings.llm.temperature,
        max_tokens=max_tokens or settings.llm.max_tokens,
    )
    
    response = await vision_llm.ainvoke([HumanMessage(content=content)])
    
    return response
