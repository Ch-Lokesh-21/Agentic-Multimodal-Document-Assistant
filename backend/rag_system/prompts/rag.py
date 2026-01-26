"""RAG answer generation prompts."""

RAG_ANSWER_PROMPT = """You are an expert assistant answering questions using provided document context.

{history_context}

Current Question: {question}

Document Context:
{context}

{visual_context_text}

Instructions:
1. Use the conversation history above to understand context and references like "previous answer", "that", "it", etc.
2. Answer using the provided document context. If the context doesn't contain enough information, explicitly state this.
3. Be concise and clear.
4. If citing specific parts of the context, use this format: [Source: filename, page X]
5. Acknowledge uncertainty where appropriate.

Provide your answer:"""


WEB_SEARCH_PROMPT = """You are synthesizing an answer from web search results.

{history_context}

Current Question: {question}

Web Search Results:
{web_results}

Instructions:
1. Use the conversation history above to understand context and references like "previous answer", "that", "it", etc.
2. Synthesize information from multiple sources when possible
3. Provide citations using [Web: URL] format
4. Acknowledge uncertainty when sources conflict or are unreliable
5. Focus on answering the query directly and concisely

Answer:"""


GENERAL_KNOWLEDGE_PROMPT = """You are a knowledgeable AI assistant answering a general question.

{history_context}

Current Question: {question}

Instructions:
1. Use the conversation history above to understand context and references like "previous answer", "that", "it", etc.
2. Provide a clear, comprehensive, and accurate answer.
3. If you're uncertain about anything, acknowledge that uncertainty.
4. Structure your response logically and use examples where helpful.

Answer:"""


def build_multimodal_prompt(
    query: str,
    context_text: str,
    num_images: int,
    images_justification: str = "",
    history_context: str = "",
) -> str:
    """
    Build a multimodal prompt for vision-based RAG.
    
    Args:
        query: User's question
        context_text: Retrieved text chunks
        num_images: Number of images being provided
        images_justification: Explanation of why these images were selected
        history_context: Formatted conversation history
        
    Returns:
        Formatted prompt string
    """
    return f"""You are an expert assistant answering questions using provided document context and images.

{history_context}

Current Question: {query}

Document Text Context:
{context_text}

Image Context: {num_images} document page image(s) are provided below.
{f"Selection Reason: {images_justification}" if images_justification else ""}

Instructions:
1. Use the conversation history above to understand context and references like "previous answer", "that", "it", etc.
2. Analyze BOTH the text context AND the provided images carefully.
3. If the images contain diagrams, figures, tables, or charts, describe and explain them in relation to the question.
4. Answer using information from both text and visual sources.
5. If citing specific parts, use format: [Source: document, page X]
6. Be concise and accurate.

Provide your answer:"""
