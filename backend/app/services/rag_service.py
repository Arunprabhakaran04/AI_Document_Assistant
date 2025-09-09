import os
import hashlib
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from loguru import logger

# Import new services for multilingual support
from .language_service import LanguageDetector
from .enhanced_pdf_extractor import EnhancedPDFExtractor
from .dual_embedding_manager import DualEmbeddingManager
from .language_aware_text_splitter import LanguageAwareTextSplitter

# Global cache for embeddings model (legacy - will be replaced by DualEmbeddingManager)
_embeddings_model = None

class DocumentProcessor:
    def __init__(self, groq_api_key=None):
        self.api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not provided or set in environment")
        os.environ["GROQ_API_KEY"] = self.api_key

        # Initialize new multilingual services
        self.language_detector = LanguageDetector()
        self.pdf_extractor = EnhancedPDFExtractor()
        self.embedding_manager = DualEmbeddingManager()
        self.text_splitter = LanguageAwareTextSplitter()
        
        # Keep legacy embeddings for backward compatibility
        self.embeddings = self._initialize_embeddings()
        self.llm = self._initialize_llm()
        self.vector_store_dir = os.path.join(os.path.dirname(__file__), '../../vector_stores')
        os.makedirs(self.vector_store_dir, exist_ok=True)
        
        logger.info("🚀 DocumentProcessor initialized with multilingual support (English + Tamil)")

    def _initialize_embeddings(self):
        global _embeddings_model
        if _embeddings_model is None:
            logger.info("🤖 Initializing embeddings model for the first time - this may take a few minutes...")
            logger.info("📥 Downloading/loading BAAI/bge-small-en-v1.5 model...")
            _embeddings_model = HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.success("✅ Embeddings model loaded successfully - subsequent uploads will be faster!")
        else:
            logger.info("⚡ Using cached embeddings model - fast loading!")
        return _embeddings_model

    def _initialize_llm(self):
        return ChatGroq(
            model_name="llama-3.3-70b-versatile", 
            temperature=0.1
        )

    def get_document_hash(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def process_pdf(self, pdf_path):
        """Enhanced PDF processing with language detection"""
        try:
            # Extract text using PyMuPDF for better Tamil support
            raw_text = self.pdf_extractor.extract_text(pdf_path)
            
            # Validate text quality
            if not self.language_detector.validate_text_quality(raw_text):
                raise ValueError("Extracted text quality is insufficient for processing")
            
            # Detect language
            language = self.language_detector.detect_language(raw_text)
            logger.info(f"📝 Detected language: {language}")
            
            # Get text statistics for debugging
            stats = self.language_detector.get_text_stats(raw_text)
            logger.info(f"📊 Text stats: {stats['total_chars']} chars, "
                       f"Tamil: {stats['tamil_ratio']:.1%}, English: {stats['english_ratio']:.1%}")
            
            # Apply language-specific normalization
            if language == 'tamil':
                raw_text = self.pdf_extractor.normalize_tamil_text(raw_text)
                logger.info("🔧 Applied Tamil text normalization")
            
            return raw_text, language
            
        except Exception as e:
            logger.error(f"❌ Error processing PDF {pdf_path}: {e}")
            raise e

    def split_text(self, text, language='english'):
        """Language-aware text splitting"""
        try:
            chunks = self.text_splitter.split_text(text, language)
            
            # Validate chunks
            validation = self.text_splitter.validate_chunks(chunks, language)
            if not validation['valid']:
                raise ValueError(f"Text splitting validation failed: {validation.get('reason', 'Unknown error')}")
            
            if 'warning' in validation:
                logger.warning(f"⚠️ Text splitting warning: {validation['warning']}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error splitting {language} text: {e}")
            raise e

    def embed_pdf(self, pdf_path, filename):
        """Process PDF with language detection and appropriate embeddings"""
        try:
            # Enhanced PDF processing with language detection
            raw_text, language = self.process_pdf(pdf_path)
            logger.info(f"📄 Processing {language} PDF: {filename}")
            
            # Language-aware text splitting
            chunks = self.split_text(raw_text, language)
            logger.info(f"✂️ Split into {len(chunks)} chunks for {language} processing")
            
            # Create vector store with appropriate embeddings
            vector_store = self.create_vector_store(chunks, language)
            
            return vector_store, language
            
        except Exception as e:
            logger.error(f"❌ Error embedding PDF {filename}: {e}")
            raise e

    def create_vector_store(self, chunks, language='english'):
        """Create vector store with appropriate embeddings for the language"""
        try:
            # Get appropriate embeddings model for the language
            embeddings = DualEmbeddingManager.get_embeddings_static(language)  # Use class method
            
            # Create vector store
            vector_store = FAISS.from_texts(chunks, embeddings)
            
            logger.info(f"✅ Created {language} vector store with {vector_store.index.ntotal} vectors")
            return vector_store
            
        except Exception as e:
            logger.error(f"❌ Error creating {language} vector store: {e}")
            raise e

    # Legacy method for backward compatibility
    def process_pdf_legacy(self, pdf_path):
        """Legacy PDF processing method using PyPDF2 (for backward compatibility)"""
        reader = PdfReader(pdf_path)
        raw_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                raw_text += text
        return raw_text