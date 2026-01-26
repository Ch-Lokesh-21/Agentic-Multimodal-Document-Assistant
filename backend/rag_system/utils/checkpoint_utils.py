"""
Checkpoint serialization for MongoDB persistence optimization.

This module provides lightweight serialization for graph checkpoints
to reduce storage requirements in MongoDB.
"""

import logging
from typing import Any, Callable

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

logger = logging.getLogger(__name__)

TRANSIENT_FIELDS = {
    "retrieved_context",
    "sub_query_results",
    "web_results",
    "visual_decision",
    "query_analysis",
    "intermediate_reasoning",
}


def _minimize_final_answer(value: Any) -> Any:
    """Keep only essential audit fields from final_answer."""
    if value is None:
        return None
    if hasattr(value, 'model_dump'):
        data = value.model_dump()
    elif isinstance(value, dict):
        data = value
    else:
        return value
    
    return {
        "answer": data.get("answer", ""),
        "answer_type": data.get("answer_type", "direct"),
        "uncertainty": data.get("uncertainty", 0.0),
        "citations_count": len(data.get("citations", [])),
        "citations_summary": [
            {"source": c.get("source_id", ""), "page": c.get("page_number")}
            for c in data.get("citations", [])[:3]
        ]
    }


MINIMAL_FIELDS: dict[str, Callable[[Any], Any]] = {
    "final_answer": _minimize_final_answer,
}


class LightweightCheckpointSerializer(JsonPlusSerializer):
    """Excludes large transient fields from MongoDB checkpoints."""
    
    def dumps(self, obj: Any) -> bytes:
        if isinstance(obj, dict):
            obj = self._filter_state(obj)
        return super().dumps(obj)
    
    def _filter_state(self, data: dict) -> dict:
        filtered = {}
        for key, value in data.items():
            if key == "channel_values":
                filtered[key] = self._filter_channel_values(value)
            elif key in TRANSIENT_FIELDS:
                continue
            else:
                filtered[key] = value
        return filtered
    
    def _filter_channel_values(self, channel_values: dict) -> dict:
        if not isinstance(channel_values, dict):
            return channel_values
        
        filtered = {}
        bytes_saved = 0
        
        for key, value in channel_values.items():
            if key in TRANSIENT_FIELDS:
                if value is not None:
                    size = self._estimate_size(value)
                    bytes_saved += size
                    logger.debug(f"[CHECKPOINT] Excluding {key} ({size} bytes)")
                
                if key in ("sub_query_results", "web_results"):
                    filtered[key] = []
                elif key == "intermediate_reasoning":
                    filtered[key] = ""
                else:
                    filtered[key] = None
            elif key in MINIMAL_FIELDS:
                filtered[key] = MINIMAL_FIELDS[key](value)
            else:
                filtered[key] = value
        
        if bytes_saved > 0:
            logger.info(f"[CHECKPOINT] Saved ~{bytes_saved / 1024:.1f}KB")
        
        return filtered
    
    def _estimate_size(self, value: Any) -> int:
        if value is None:
            return 0
        try:
            import json
            serialized = json.dumps(value, default=str)
            return len(serialized.encode('utf-8'))
        except Exception:
            return len(str(value))


def create_lightweight_checkpointer():
    """
    Create a MongoDBSaver with lightweight serialization.
    
    Returns:
        Configured MongoDBSaver context manager
    """
    from langgraph.checkpoint.mongodb import MongoDBSaver
    from config import settings
    
    serde = LightweightCheckpointSerializer()
    
    return MongoDBSaver.from_conn_string(
        conn_string=settings.mongodb.uri.get_secret_value(),
        db_name=settings.mongodb.database,
        collection_name=settings.mongodb.checkpoints_collection,
        serde=serde,
    )
