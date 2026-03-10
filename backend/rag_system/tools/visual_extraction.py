"""
Visual element extraction and description generation during ingestion.

This module extracts images and tables from PDFs and generates detailed
text descriptions using a vision model, which are then stored in the vector DB.
"""

import asyncio
import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractedVisualElement:
    """Represents an extracted visual element (image or table)."""
    
    content_type: str  # "image" or "table"
    page_number: int  # 1-indexed
    description: str  # Generated description from vision model
    bbox: tuple[float, float, float, float] | None  # (x0, y0, x1, y1) coordinates
    image_base64: str | None  # Base64 encoded image for processing
    element_index: int  # Index of element on the page
    confidence: float  # Confidence of extraction


IMAGE_DESCRIPTION_PROMPT = """Analyze this image extracted from a PDF document and provide a detailed description.

Your description should include:
1. **Type**: What type of visual is this? (diagram, chart, graph, photograph, illustration, screenshot, logo, etc.)
2. **Content Summary**: What does this image show or represent?
3. **Key Details**: List all important elements, labels, text, numbers, or data points visible
4. **Context**: What information does this visual convey? What is its purpose in the document?
5. **Data/Statistics** (if applicable): Extract any numerical data, trends, or statistics shown

Be thorough and precise. This description will be used for document search and question-answering, 
so include all searchable keywords and concepts visible in the image.

Provide the description in a clear, structured format."""


TABLE_DESCRIPTION_PROMPT = """Analyze this table image extracted from a PDF document and provide a comprehensive description.

Your description should include:
1. **Table Title/Caption**: If visible
2. **Column Headers**: List all column names
3. **Row Structure**: Describe the row organization
4. **Data Content**: Summarize the key data points and values
5. **Patterns/Trends**: Note any patterns, comparisons, or trends in the data
6. **Key Findings**: What are the most important takeaways from this table?

Format any numerical data clearly. This description will be used for search and Q&A,
so be comprehensive and include all searchable terms."""


class VisualExtractor:
    """Extracts and describes visual elements from PDF documents."""
    
    def __init__(
        self,
        vision_model: str | None = None,
        max_images_per_page: int | None = None,
        min_image_size: tuple[int, int] | None = None,
        image_zoom: int | None = None,
        max_image_width: int | None = None,
    ):
        """
        Initialize the visual extractor.
        
        Args:
            vision_model: OpenAI vision model to use (default from settings)
            max_images_per_page: Maximum images to extract per page
            min_image_size: Minimum (width, height) for image extraction
            image_zoom: Zoom factor for image rendering
            max_image_width: Maximum width for images sent to vision model
        """
        self.vision_model = (
            vision_model or 
            settings.visual_extraction.vision_model or 
            settings.llm.model
        )
        self.max_images_per_page = (
            max_images_per_page or 
            settings.visual_extraction.max_images_per_page
        )
        self.min_image_size = min_image_size or (
            settings.visual_extraction.min_image_width,
            settings.visual_extraction.min_image_height,
        )
        self.image_zoom = image_zoom or settings.image.zoom_factor
        self.max_image_width = max_image_width or settings.image.max_width
        
        self.llm = ChatOpenAI(
            model=self.vision_model,
            temperature=0.0,
            max_tokens=1500,
        )
    
    async def extract_and_describe(
        self,
        file_path: str | Path,
        extract_images: bool = True,
        extract_tables: bool = True,
    ) -> list[Document]:
        """
        Extract visual elements from a PDF and generate descriptions.
        
        Args:
            file_path: Path to the PDF file
            extract_images: Whether to extract embedded images
            extract_tables: Whether to extract tables as images
            
        Returns:
            List of LangChain Documents with visual descriptions and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        logger.info(f"[VISUAL_EXTRACT] Starting extraction from: {file_path.name}")
        
        visual_elements: list[ExtractedVisualElement] = []
        
        try:
            pdf_document = fitz.open(file_path)
            total_pages = len(pdf_document)
            
            for page_num in range(total_pages):
                page = pdf_document.load_page(page_num)
                
                if extract_images:
                    images = await self._extract_images_from_page(
                        page, page_num + 1, file_path.name
                    )
                    visual_elements.extend(images)
                
                # Tables are typically detected by the Unstructured loader
                # But we can also detect table regions for visual description
                if extract_tables:
                    tables = await self._extract_tables_from_page(
                        page, page_num + 1, file_path.name
                    )
                    visual_elements.extend(tables)
            
            pdf_document.close()
            
        except Exception as e:
            logger.error(f"[VISUAL_EXTRACT] Error processing PDF: {str(e)}")
            raise
        
        logger.info(f"[VISUAL_EXTRACT] Found {len(visual_elements)} visual elements")
        
        # Generate descriptions using vision model
        documents = await self._generate_descriptions(visual_elements, file_path)
        
        logger.info(f"[VISUAL_EXTRACT] Generated {len(documents)} visual descriptions")
        
        return documents
    
    async def _extract_images_from_page(
        self,
        page: fitz.Page,
        page_number: int,
        source_file: str,
    ) -> list[ExtractedVisualElement]:
        """Extract embedded images from a PDF page."""
        elements = []
        
        try:
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list[:self.max_images_per_page]):
                try:
                    xref = img_info[0]
                    base_image = page.parent.extract_image(xref)
                    
                    if not base_image:
                        continue
                    
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image to check size and process
                    img = Image.open(io.BytesIO(image_bytes))
                    
                    # Skip small images (likely icons, bullets, etc.)
                    if img.width < self.min_image_size[0] or img.height < self.min_image_size[1]:
                        logger.debug(f"[VISUAL_EXTRACT] Skipping small image: {img.size}")
                        continue
                    
                    # Resize if too large
                    if img.width > self.max_image_width:
                        ratio = self.max_image_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize(
                            (self.max_image_width, new_height),
                            Image.Resampling.LANCZOS
                        )
                    
                    # Convert to RGB if necessary (for PNG with transparency)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # Encode as base64
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=85)
                    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                    
                    # Try to get bounding box
                    bbox = self._get_image_bbox(page, xref)
                    
                    elements.append(ExtractedVisualElement(
                        content_type="image",
                        page_number=page_number,
                        description="",  # Will be filled by vision model
                        bbox=bbox,
                        image_base64=image_base64,
                        element_index=img_index,
                        confidence=0.9,
                    ))
                    
                    logger.debug(
                        f"[VISUAL_EXTRACT] Extracted image {img_index + 1} "
                        f"from page {page_number}: {img.size}"
                    )
                    
                except Exception as e:
                    logger.warning(
                        f"[VISUAL_EXTRACT] Error extracting image {img_index} "
                        f"from page {page_number}: {str(e)}"
                    )
                    continue
        
        except Exception as e:
            logger.error(
                f"[VISUAL_EXTRACT] Error getting images from page {page_number}: {str(e)}"
            )
        
        return elements
    
    async def _extract_tables_from_page(
        self,
        page: fitz.Page,
        page_number: int,
        source_file: str,
    ) -> list[ExtractedVisualElement]:
        """
        Extract table regions from a PDF page.
        
        Uses PyMuPDF's table detection or falls back to text block analysis.
        """
        elements = []
        
        try:
            # Try to find tables using PyMuPDF's table finder (if available)
            tables = page.find_tables()
            
            for table_index, table in enumerate(tables):
                try:
                    # Get the bounding box of the table
                    bbox = table.bbox  # (x0, y0, x1, y1)
                    
                    # Render the table region as an image
                    clip = fitz.Rect(bbox)
                    
                    # Increase resolution for better OCR
                    mat = fitz.Matrix(self.image_zoom, self.image_zoom)
                    pix = page.get_pixmap(matrix=mat, clip=clip)
                    
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # Skip very small tables
                    if img.width < 100 or img.height < 50:
                        continue
                    
                    # Resize if too large
                    if img.width > self.max_image_width:
                        ratio = self.max_image_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize(
                            (self.max_image_width, new_height),
                            Image.Resampling.LANCZOS
                        )
                    
                    # Encode as base64
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG", optimize=True)
                    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                    
                    elements.append(ExtractedVisualElement(
                        content_type="table",
                        page_number=page_number,
                        description="",  # Will be filled by vision model
                        bbox=bbox,
                        image_base64=image_base64,
                        element_index=table_index,
                        confidence=0.85,
                    ))
                    
                    logger.debug(
                        f"[VISUAL_EXTRACT] Extracted table {table_index + 1} "
                        f"from page {page_number}"
                    )
                    
                except Exception as e:
                    logger.warning(
                        f"[VISUAL_EXTRACT] Error extracting table {table_index} "
                        f"from page {page_number}: {str(e)}"
                    )
                    continue
        
        except AttributeError:
            # PyMuPDF version doesn't have find_tables()
            logger.debug("[VISUAL_EXTRACT] Table detection not available in this PyMuPDF version")
        except Exception as e:
            logger.error(
                f"[VISUAL_EXTRACT] Error finding tables on page {page_number}: {str(e)}"
            )
        
        return elements
    
    def _get_image_bbox(
        self,
        page: fitz.Page,
        xref: int,
    ) -> tuple[float, float, float, float] | None:
        """Get the bounding box of an image on the page."""
        try:
            for img in page.get_image_info():
                if img.get("xref") == xref:
                    bbox = img.get("bbox")
                    if bbox:
                        return tuple(bbox)
            return None
        except Exception:
            return None
    
    async def _generate_descriptions(
        self,
        elements: list[ExtractedVisualElement],
        file_path: Path,
    ) -> list[Document]:
        """Generate text descriptions for visual elements using vision model."""
        documents = []
        
        # Process in batches to avoid rate limits
        batch_size = 5
        
        for i in range(0, len(elements), batch_size):
            batch = elements[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self._describe_element(element, file_path)
                for element in batch
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for element, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(
                        f"[VISUAL_EXTRACT] Failed to describe {element.content_type} "
                        f"on page {element.page_number}: {str(result)}"
                    )
                    continue
                
                if result:
                    documents.append(result)
        
        return documents
    
    async def _describe_element(
        self,
        element: ExtractedVisualElement,
        file_path: Path,
    ) -> Document | None:
        """Generate a description for a single visual element."""
        if not element.image_base64:
            return None
        
        try:
            # Select appropriate prompt based on content type
            prompt = (
                TABLE_DESCRIPTION_PROMPT 
                if element.content_type == "table" 
                else IMAGE_DESCRIPTION_PROMPT
            )
            
            # Build vision request
            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{element.image_base64}",
                        "detail": settings.image.detail_level,
                    },
                },
            ]
            
            response = await self.llm.ainvoke([HumanMessage(content=content)])
            
            description = response.content.strip()
            
            if not description:
                logger.warning(
                    f"[VISUAL_EXTRACT] Empty description for {element.content_type} "
                    f"on page {element.page_number}"
                )
                return None
            
            element.description = description
            
            # Create Document with rich metadata
            metadata = {
                "content_type": element.content_type,
                "page_number": element.page_number,
                "source_file": file_path.name,
                "source_path": str(file_path),
                "element_index": element.element_index,
                "confidence": element.confidence,
                "category": f"{element.content_type}_description",
            }
            
            # Add bounding box if available (for citation positioning)
            if element.bbox:
                metadata["bbox_x0"] = element.bbox[0]
                metadata["bbox_y0"] = element.bbox[1]
                metadata["bbox_x1"] = element.bbox[2]
                metadata["bbox_y1"] = element.bbox[3]
            
            # Create a structured content including type marker for retrieval
            content_prefix = (
                f"[{element.content_type.upper()} - Page {element.page_number}]\n\n"
            )
            
            document = Document(
                page_content=content_prefix + description,
                metadata=metadata,
            )
            
            logger.info(
                f"[VISUAL_EXTRACT] Generated description for {element.content_type} "
                f"on page {element.page_number} ({len(description)} chars)"
            )
            
            return document
            
        except Exception as e:
            logger.error(
                f"[VISUAL_EXTRACT] Error generating description: {str(e)}"
            )
            return None


async def extract_visuals_from_pdf(
    file_path: str | Path,
    vision_model: str | None = None,
    extract_images: bool = True,
    extract_tables: bool = True,
) -> list[Document]:
    """
    Convenience function to extract and describe visual elements from a PDF.
    
    Args:
        file_path: Path to the PDF file
        vision_model: Optional vision model override
        extract_images: Whether to extract images
        extract_tables: Whether to extract tables
        
    Returns:
        List of Documents containing visual descriptions with metadata
    """
    extractor = VisualExtractor(vision_model=vision_model)
    return await extractor.extract_and_describe(
        file_path=file_path,
        extract_images=extract_images,
        extract_tables=extract_tables,
    )
