"""Visual context decision and page selection prompts."""

VISUAL_DECISION_PROMPT = """Analyze whether this query EXPLICITLY requires visual context from a PDF document.

Query: {query}

Available document metadata:
- Total pages: {total_pages}
- Retrieved text chunks mention visual elements: {visual_elements_mentioned}

IMPORTANT: Only set requires_visual=true if the query:
1. EXPLICITLY asks about a figure, diagram, table, chart, image, or visual element
2. Uses words like "show me", "what does X look like", "the diagram shows", "in figure X"
3. Cannot be answered without seeing the actual visual content

Do NOT require visual context for:
- General questions about concepts (even if diagrams exist)
- Questions that can be answered from text alone
- Questions about architecture or flow unless specifically asking to SEE a diagram

Be conservative - only request images when truly necessary."""


PAGE_SELECTION_PROMPT = """You are an intelligent page selection agent. Based on the user's query and retrieved document context, 
decide which specific PDF pages should be converted to images for visual analysis.

Query: {query}

Retrieved Documents (grouped by source file):
{retrieved_docs_summary}

Your task:
1. Analyze which pages from which documents are MOST relevant to answering the query
2. Consider the content snippets and metadata of each retrieved chunk
3. Select up to 5 total pages across all documents
4. Prioritize pages mentioned in multiple retrieved chunks
5. If the query asks about specific topics (diagrams, tables, figures), select pages likely to contain them

IMPORTANT:
- Each document has its own page numbering (page 1 in doc A is different from page 1 in doc B)
- Page numbers are 1-indexed (first page of document = page 1)
- Return selections grouped by source_file
- Fewer high-quality pages are better than many irrelevant ones
- If only 1-2 pages are highly relevant, select only those

OUTPUT FORMAT:
Return a list of selections, where each selection specifies:
- source_file: the filename (e.g., "attention_paper.pdf")
- pages: list of page numbers from that file

Example: If page 3 from "doc1.pdf" and pages 2,5 from "doc2.pdf" are relevant,
return selected_pages with two SourcePageSelection items.

Provide your page selection decision."""
