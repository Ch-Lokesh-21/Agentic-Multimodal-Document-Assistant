"""
State utility functions for monitoring graph state size.

This module provides functions to estimate and analyze
the size of graph state for debugging and optimization.
"""

import json


def estimate_state_size(state: dict) -> dict:
    """
    Estimate graph state size per field for monitoring.
    
    Args:
        state: Graph state dictionary
        
    Returns:
        Dictionary with size estimates and warnings
    """
    sizes = {}
    total_size = 0
    
    for key, value in state.items():
        if value is None:
            sizes[key] = 0
            continue
            
        try:
            if key == "messages":
                msg_sizes = []
                for msg in value:
                    content = str(msg.content) if hasattr(msg, 'content') else str(msg)
                    msg_sizes.append(len(content.encode('utf-8')))
                sizes[key] = sum(msg_sizes)
                sizes[f"{key}_count"] = len(value)
            elif key == "retrieved_context" and value:
                if hasattr(value, 'images') and value.images:
                    img_size = sum(len(img) for img in value.images)
                    sizes[f"{key}_images_bytes"] = img_size
                    sizes[f"{key}_images_count"] = len(value.images)
                if hasattr(value, 'chunks') and value.chunks:
                    chunk_size = sum(len(c.content) for c in value.chunks if c.content)
                    sizes[f"{key}_chunks_bytes"] = chunk_size
                    sizes[f"{key}_chunks_count"] = len(value.chunks)
                sizes[key] = sizes.get(f"{key}_images_bytes", 0) + sizes.get(f"{key}_chunks_bytes", 0)
            elif key == "sub_query_results" and value:
                total_sub = 0
                for result in value:
                    if hasattr(result, 'answer'):
                        total_sub += len(result.answer)
                sizes[key] = total_sub
                sizes[f"{key}_count"] = len(value)
            else:
                serialized = json.dumps(value, default=str)
                sizes[key] = len(serialized.encode('utf-8'))
        except Exception:
            sizes[key] = -1
        
        if sizes[key] > 0:
            total_size += sizes[key]
    
    sizes["_total_bytes"] = total_size
    sizes["_total_kb"] = round(total_size / 1024, 2)
    
    warnings = []
    if sizes.get("retrieved_context_images_bytes", 0) > 100_000:
        warnings.append("Large base64 images in retrieved_context!")
    if sizes.get("retrieved_context_chunks_bytes", 0) > 50_000:
        warnings.append("Large text chunks in retrieved_context")
    if sizes.get("messages", 0) > 50_000:
        warnings.append("Large message history")
    if sizes.get("_total_kb", 0) > 500:
        warnings.append(f"Total state {sizes['_total_kb']}KB is large")
    
    sizes["_warnings"] = warnings
    
    return sizes
