import fitz  # PyMuPDF
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EnhancedPDFExtractor:
    """Enhanced PDF text extractor using PyMuPDF for better Tamil support"""
    
    def __init__(self):
        logger.info("Initialized Enhanced PDF Extractor with PyMuPDF")
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text using PyMuPDF for better Unicode/Tamil support
        """
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            text = ""
            page_count = len(doc)  # Get page count before processing
            
            # Extract text from each page
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                if page_text:
                    text += page_text + "\n"
                    logger.debug(f"Extracted {len(page_text)} characters from page {page_num + 1}")
            
            doc.close()
            
            logger.info(f"Successfully extracted {len(text)} characters from {page_count} pages")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise e

    def extract_text_with_page_info(self, pdf_path: str, filename: str) -> list:
        """
        Extract text page by page with metadata for source tracking
        Returns a list of dicts with page text and metadata
        """
        try:
            logger.info(f"Extracting text with page info from PDF: {pdf_path}")
            
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            page_texts = []
            page_count = len(doc)
            
            # Extract text from each page with metadata
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                if page_text and page_text.strip():  # Only include pages with actual content
                    page_info = {
                        'text': page_text.strip(),
                        'metadata': {
                            'source': filename,
                            'page': page_num + 1,  # 1-indexed page numbers
                            'total_pages': page_count
                        }
                    }
                    page_texts.append(page_info)
                    logger.debug(f"Extracted {len(page_text)} characters from page {page_num + 1}")
            
            doc.close()
            
            total_chars = sum(len(page['text']) for page in page_texts)
            logger.info(f"Successfully extracted {total_chars} characters from {len(page_texts)} pages with content")
            return page_texts
            
        except Exception as e:
            logger.error(f"Error extracting text with page info from PDF {pdf_path}: {e}")
            raise e
    
    def normalize_tamil_text(self, text: str) -> str:
        """
        Basic Tamil text normalization
        """
        try:
            # Remove excessive whitespace
            import re
            
            # Normalize multiple spaces and newlines
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Preserve paragraph breaks
            text = re.sub(r'[ \t]+', ' ', text)  # Normalize spaces
            text = re.sub(r'\n ', '\n', text)  # Remove spaces after newlines
            
            # Remove zero-width characters that might interfere
            text = text.replace('\u200b', '')  # Zero-width space
            text = text.replace('\u200c', '')  # Zero-width non-joiner
            text = text.replace('\u200d', '')  # Zero-width joiner
            
            logger.info("Tamil text normalized")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error normalizing Tamil text: {e}")
            return text
    
    def extract_and_normalize(self, pdf_path: str, language: str) -> str:
        """
        Extract text and apply language-specific normalization
        """
        text = self.extract_text(pdf_path)
        
        if language == 'tamil':
            text = self.normalize_tamil_text(text)
        
        return text
    
    def get_text_preview(self, text: str, max_chars: int = 200) -> str:
        """
        Get a preview of the extracted text for logging
        """
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."
