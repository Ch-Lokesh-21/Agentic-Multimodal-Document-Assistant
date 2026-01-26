"""
PDF processing tools for image extraction.

This module provides utilities for converting PDF pages to images.
"""

import base64
import io
import logging
from typing import Optional

import fitz  # PyMuPDF
from PIL import Image

from config import settings

logger = logging.getLogger(__name__)


def pdf_pages_to_images(
    file_path: str,
    page_numbers: list[int],
    zoom: int | None = None,
    max_width: int | None = None,
) -> list[str]:
    """
    Convert PDF pages to base64-encoded PNG images.
    
    Args:
        file_path: Path to PDF file
        page_numbers: List of page indices (0-based) to convert
        zoom: Zoom factor for rendering (defaults to config)
        max_width: Maximum image width (defaults to config)
        
    Returns:
        List of base64-encoded PNG images
    """
    # Use config defaults
    zoom = zoom or settings.image.zoom_factor
    max_width = max_width or settings.image.max_width
    
    images = []
    
    try:
        pdf_document = fitz.open(file_path)
        total_pages = len(pdf_document)
        
        for page_num in page_numbers:
            # Validate page number
            if page_num < 0 or page_num >= total_pages:
                logger.warning(f"[IMAGES] Invalid page number {page_num}, skipping")
                continue
            
            try:
                page = pdf_document.load_page(page_num)
                
                # Create transformation matrix with zoom
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert pixmap to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Resize if too large
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to base64 PNG
                buffer = io.BytesIO()
                img.save(buffer, format="PNG", optimize=True)
                image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                
                images.append(image_base64)
                logger.debug(f"[IMAGES] Converted page {page_num + 1} to image")
                
            except Exception as e:
                logger.error(f"[IMAGES] Error converting page {page_num}: {str(e)}")
                continue
        
        pdf_document.close()
        
    except Exception as e:
        logger.error(f"[IMAGES] Error opening PDF {file_path}: {str(e)}")
    
    return images
