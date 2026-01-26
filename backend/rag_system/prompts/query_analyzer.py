"""Query analysis and answer synthesis prompts."""

QUERY_ANALYZER_PROMPT = """You are an intelligent query analyzer for a RAG system.
Your task is to classify the user query and determine if it requires decomposition into sub-queries.

Query to analyze: {query}

CLASSIFICATION RULES:

A query is SIMPLE if it:
- Has a single clear intent
- Asks one specific question
- Can be answered directly without breaking down

A query is COMPLEX if it:
- Contains multiple distinct sub-questions (e.g., "What is X and how does Y work?")
- Asks for a comparison between things (e.g., "Compare A vs B", "What's the difference between X and Y")
- Contains conjunctions linking separate questions (e.g., "and", "or", "also", "as well as")
- Asks for multiple pieces of information in one sentence
- Requires analyzing different aspects separately

EXTRACTION RULES (if complex):
1. Extract MAXIMUM {max_sub_queries} sub-queries
2. Each sub-query must be self-contained and answerable independently
3. Preserve the original intent and context in each sub-query
4. For comparisons, create separate sub-queries for each entity being compared
5. Keep sub-queries concise but complete

EXAMPLES:

Simple: "What is the attention mechanism in transformers?"
→ classification: "simple", sub_queries: []

Complex: "What is the attention mechanism and how does it differ from RNNs?"
→ classification: "complex", sub_queries: ["What is the attention mechanism?", "How does the attention mechanism differ from RNNs?"]

Complex: "Compare CNN and RNN architectures for NLP tasks"
→ classification: "complex", sub_queries: ["What are the key characteristics of CNN architecture for NLP tasks?", "What are the key characteristics of RNN architecture for NLP tasks?", "What are the differences between CNN and RNN for NLP tasks?"]

Provide your analysis."""


SYNTHESIZE_ANSWERS_PROMPT = """You are synthesizing a comprehensive answer from multiple sub-query results.

Original Question: {original_query}

Sub-Query Results:
{sub_query_results}

Instructions:
1. Combine the information from all sub-query answers coherently
2. Address the original question directly and completely
3. If this was a comparison query, clearly highlight the differences and similarities
4. Maintain consistency in terminology and references
5. Do not simply concatenate answers - synthesize them into a unified response
6. If sub-queries had citations, reference them appropriately
7. Be concise but comprehensive

Provide a unified, well-structured answer to the original question:"""
