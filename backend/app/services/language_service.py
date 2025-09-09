from langdetect import detect
from typing import Literal
import re
import logging

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Simple language detector for English and Tamil PDFs only"""
    
    def detect_language(self, text: str) -> Literal['english', 'tamil']:
        """
        Detect if text is English or Tamil
        Returns: 'english' or 'tamil'
        """
        try:
            # First check for Tamil Unicode characters
            tamil_pattern = r'[\u0B80-\u0BFF]'  # Tamil Unicode range
            has_tamil = bool(re.search(tamil_pattern, text))
            
            if has_tamil:
                # Check Tamil density - if more than 10% Tamil chars, consider it Tamil
                tamil_chars = len(re.findall(tamil_pattern, text))
                total_chars = len(re.sub(r'\s+', '', text))  # Remove whitespace for counting
                
                if total_chars > 0:
                    tamil_ratio = tamil_chars / total_chars
                    if tamil_ratio > 0.1:  # More than 10% Tamil characters
                        logger.info(f"Detected Tamil document (Tamil ratio: {tamil_ratio:.2%})")
                        return 'tamil'
            
            # Use langdetect as secondary check
            try:
                detected = detect(text)
                if detected == 'ta':
                    logger.info("Detected Tamil document via langdetect")
                    return 'tamil'
            except Exception as e:
                logger.warning(f"Langdetect failed: {e}")
            
            # Default to English
            logger.info("Detected English document")
            return 'english'
            
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            # Default fallback to English
            return 'english'
    
    def validate_text_quality(self, text: str) -> bool:
        """
        Check if extracted text has sufficient quality for processing
        """
        if not text or len(text.strip()) < 100:
            return False
        
        # Check if text is mostly garbled or contains too many special characters
        printable_chars = len(re.findall(r'[a-zA-Z0-9\u0B80-\u0BFF\s]', text))
        total_chars = len(text)
        
        if total_chars > 0:
            quality_ratio = printable_chars / total_chars
            return quality_ratio > 0.7  # At least 70% should be readable characters
        
        return False
    
    def get_text_stats(self, text: str) -> dict:
        """
        Get statistics about the text for debugging
        """
        tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(re.sub(r'\s+', '', text))
        
        return {
            'total_chars': len(text),
            'total_non_space_chars': total_chars,
            'tamil_chars': tamil_chars,
            'english_chars': english_chars,
            'tamil_ratio': tamil_chars / total_chars if total_chars > 0 else 0,
            'english_ratio': english_chars / total_chars if total_chars > 0 else 0
        }
