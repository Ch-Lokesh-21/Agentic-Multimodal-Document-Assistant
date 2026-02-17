"""Image retriever for PDF page extraction."""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from collections import Counter, defaultdict

from langchain_openai import ChatOpenAI

from config import settings
from schemas import (
    RetrievedContext,
    RetrievedChunk,
    PageSelectionDecision,
    SourcePageSelection,
)
from rag_system.tools.pdf_processing import pdf_pages_to_images
from rag_system.prompts import PAGE_SELECTION_PROMPT

logger = logging.getLogger(__name__)


class ImageRetriever:
    """Handles image extraction from PDF documents."""
    
    def __init__(self, session_id: str):
        """Initialize the image retriever."""
        self.session_id = session_id
        self.upload_dir = Path(settings.upload.directory) / session_id
        self.llm = ChatOpenAI(
            model=settings.llm.model,
            temperature=settings.llm.temperature,
        )
    
    async def retrieve(
        self,
        retrieved_context: RetrievedContext,
        query: str,
        max_images: int | None = None,
        max_pages: int | None = None,
    ) -> Optional[RetrievedContext]:
        """Generate PDF page images from retrieved context asynchronously."""
        max_images = max_images or settings.image.max_images
        max_pages = max_pages or settings.image.max_pages
        
        if not retrieved_context.unique_page_numbers:
            logger.info("[IMAGES] No page numbers available in retrieved context")
            return None
        
        logger.info("[IMAGES] Generating PDF page images...")
        
        try:
            if not self.upload_dir.exists():
                logger.warning(f"[IMAGES] Upload directory not found: {self.upload_dir}")
                return None
            
            page_selection = await self._select_pages_with_llm(
                query=query,
                retrieved_context=retrieved_context,
                max_pages=max_pages,
            )
            
            if not page_selection or not page_selection.selected_pages:
                logger.warning("[IMAGES] No pages selected by LLM")
                return None
            
            logger.info(f"[IMAGES] LLM selection reasoning: {page_selection.reasoning}")
            
            all_images = []
            processed_selections = []
            total_pages_extracted = 0
            
            for source_selection in page_selection.selected_pages:
                if total_pages_extracted >= max_images:
                    break
                    
                source_file = source_selection.source_file
                pages = source_selection.pages
                
                valid_pages = [p for p in pages if p >= 1]
                if not valid_pages:
                    logger.warning(f"[IMAGES] No valid pages for {source_file}: {pages}")
                    continue
                
                pdf_path = self.upload_dir / source_file
                if not pdf_path.exists():
                    logger.warning(f"[IMAGES] PDF not found: {pdf_path}")
                    continue
                
                page_indices = [p - 1 for p in valid_pages]
                
                remaining_slots = max_images - total_pages_extracted
                page_indices = page_indices[:remaining_slots]
                valid_pages = valid_pages[:remaining_slots]
                
                logger.info(
                    f"[IMAGES] Extracting pages {valid_pages} (1-indexed) from {source_file}, "
                    f"PyMuPDF indices: {page_indices}"
                )
                
                try:
                    images = await asyncio.to_thread(
                        pdf_pages_to_images,
                        str(pdf_path),
                        page_indices,
                        settings.image.zoom_factor,
                        settings.image.max_width,
                    )
                    all_images.extend(images)
                    processed_selections.append(f"{source_file}:pages{valid_pages}")
                    total_pages_extracted += len(images)
                    
                    logger.info(f"[IMAGES] Extracted {len(images)} images from {source_file}")
                    
                except Exception as e:
                    logger.error(f"[IMAGES] Error processing {source_file}: {str(e)}")
                    continue
            
            if all_images:
                updated_context = RetrievedContext(
                    chunks=retrieved_context.chunks,
                    unique_page_numbers=retrieved_context.unique_page_numbers,
                    source_files=retrieved_context.source_files,
                    images=all_images,
                    images_justification=(
                        f"Extracted from {processed_selections}. "
                        f"Selection reasoning: {page_selection.reasoning}"
                    ),
                )
                
                logger.info(f"[IMAGES] Generated {len(all_images)} total images")
                return updated_context
            else:
                logger.info("[IMAGES] No images could be generated")
                return None
                
        except Exception as e:
            logger.error(f"[IMAGES] Error generating images: {str(e)}")
            return None
    
    async def _select_pages_with_llm(
        self,
        query: str,
        retrieved_context: RetrievedContext,
        max_pages: int | None = None,
    ) -> Optional[PageSelectionDecision]:
        """Use LLM to intelligently select which pages to convert to images."""
        max_pages = max_pages or settings.image.max_pages
        try:
            source_page_frequency: dict[str, Counter[int]] = defaultdict(Counter)
            for chunk in retrieved_context.chunks:
                if chunk.page_number is not None and chunk.source_file:
                    source_page_frequency[chunk.source_file][chunk.page_number] += 1
            
            if not source_page_frequency:
                logger.warning("[IMAGES] No pages with page numbers found in chunks")
                return None
            
            retrieved_docs_summary = self._build_docs_summary_multi_source(
                retrieved_context, source_page_frequency
            )
            
            prompt = PAGE_SELECTION_PROMPT.format(
                query=query,
                retrieved_docs_summary=retrieved_docs_summary,
            )
            
            structured_llm = self.llm.with_structured_output(PageSelectionDecision)
            decision: PageSelectionDecision = await structured_llm.ainvoke(prompt)
            
            validated_selections = []
            total_pages = 0
            
            for selection in decision.selected_pages:
                if total_pages >= max_pages:
                    break
                    
                source_file = selection.source_file
                if source_file not in source_page_frequency:
                    logger.warning(f"[IMAGES] Unknown source file: {source_file}")
                    continue
                
                available_pages = set(source_page_frequency[source_file].keys())
                valid_pages = [p for p in selection.pages if p in available_pages]
                
                remaining = max_pages - total_pages
                valid_pages = valid_pages[:remaining]
                
                if valid_pages:
                    validated_selections.append(SourcePageSelection(
                        source_file=source_file,
                        pages=valid_pages,
                    ))
                    total_pages += len(valid_pages)
            
            if validated_selections:
                decision.selected_pages = validated_selections
                logger.info(f"[IMAGES] LLM selected {total_pages} pages across {len(validated_selections)} documents")
                return decision
            else:
                logger.warning("[IMAGES] LLM selected no valid pages")
                return None
                
        except Exception as e:
            logger.error(f"[IMAGES] Error in LLM page selection: {str(e)}")
            return self._create_fallback_selection(source_page_frequency, max_pages)
    
    def _create_fallback_selection(
        self,
        source_page_frequency: dict[str, Counter[int]],
        max_pages: int,
    ) -> PageSelectionDecision:
        """Create fallback page selection based on frequency."""
        all_pages = []
        for source_file, page_counts in source_page_frequency.items():
            for page, count in page_counts.items():
                all_pages.append((source_file, page, count))
        
        all_pages.sort(key=lambda x: x[2], reverse=True)
        
        source_to_pages: dict[str, list[int]] = defaultdict(list)
        total = 0
        for source_file, page, _ in all_pages:
            if total >= max_pages:
                break
            source_to_pages[source_file].append(page)
            total += 1
        
        selections = [
            SourcePageSelection(source_file=src, pages=pages)
            for src, pages in source_to_pages.items()
        ]
        
        logger.info(f"[IMAGES] Falling back to frequency-based selection: {selections}")
        
        return PageSelectionDecision(
            selected_pages=selections,
            reasoning="Fallback selection based on page frequency in retrieved chunks",
        )
    
    def _build_docs_summary_multi_source(
        self,
        retrieved_context: RetrievedContext,
        source_page_frequency: dict[str, Counter[int]],
    ) -> str:
        """Build a summary of retrieved documents for LLM analysis, grouped by source file."""
        summary_lines = []
        
        source_page_to_chunks: dict[str, dict[int, list[RetrievedChunk]]] = defaultdict(lambda: defaultdict(list))
        for chunk in retrieved_context.chunks:
            if chunk.page_number is not None and chunk.source_file:
                source_page_to_chunks[chunk.source_file][chunk.page_number].append(chunk)
        
        for source_file in sorted(source_page_to_chunks.keys()):
            page_to_chunks = source_page_to_chunks[source_file]
            page_freq = source_page_frequency.get(source_file, Counter())
            available_pages = sorted(page_to_chunks.keys())
            
            summary_lines.append(f"\n=== Source: {source_file} ===")
            summary_lines.append(f"Available pages: {available_pages}")
            
            for page_num in sorted(page_to_chunks.keys()):
                chunks = page_to_chunks[page_num]
                content_preview = chunks[0].content[:200] if chunks else ""
                
                summary_lines.append(
                    f"\n  Page {page_num} (appears {page_freq[page_num]} times in retrieval):\n"
                    f"    Category: {chunks[0].category or 'N/A'}\n"
                    f"    Content preview: {content_preview}...\n"
                )
        
        return "\n".join(summary_lines)
