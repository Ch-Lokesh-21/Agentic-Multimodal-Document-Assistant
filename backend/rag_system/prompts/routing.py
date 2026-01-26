"""Routing prompts for query classification."""

ROUTING_PROMPT = """You are an intelligent routing agent for a hybrid RAG system.
Your job is to analyze the user's query and decide the best path to answer it.

Available paths:
1. "llm": Use direct LLM knowledge (for general questions, explanations, reasoning)
2. "web_search": Search the web (for current events, latest information, real-time data)
3. "multimodal_rag": Retrieve from uploaded PDF documents (for specific document-based knowledge)

{history_context}

Current Query: {query}

Consider these factors:
- Does the query ask about current/real-time information? → web_search
- Does the query reference "the document", "the paper", "the PDF"? → multimodal_rag
- Is this a general knowledge or reasoning question? → llm
- Could multiple paths work? Recommend the most efficient one first.

IMPORTANT - Use session history to inform your decision:
- If previous queries used RAG successfully and current query is a follow-up → multimodal_rag
- If conversation context shows document-specific discussion → multimodal_rag
- If user says "what about...", "also", "and", check if it relates to prior document context
- If previous answers came from documents and user asks clarification → multimodal_rag
- Maintain consistency in routing for related follow-up questions

Respond with your routing decision."""
