"""
Visual element detection tool.

This module provides utilities for detecting mentions
of visual elements in text.
"""


def detect_visual_elements(text_chunks: list[str]) -> bool:
    """
    Check if text chunks mention visual elements.
    
    Args:
        text_chunks: List of text chunks to analyze
        
    Returns:
        True if visual keywords are found, False otherwise
    """
    visual_keywords = [
        "figure", "diagram", "table", "chart", "graph", "image",
        "photo", "illustration", "visual", "picture", "snapshot"
    ]
    return any(
        any(kw in chunk.lower() for kw in visual_keywords)
        for chunk in text_chunks
    )
