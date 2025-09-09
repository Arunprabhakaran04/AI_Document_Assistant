from langchain_huggingface import HuggingFaceEmbeddings
from typing import Literal
import logging

logger = logging.getLogger(__name__)

# Global cache for embedding models - shared across ALL instances
_GLOBAL_EMBEDDING_CACHE = {}

class DualEmbeddingManager:
    """
    Manages English and Tamil embedding models with global caching
    English: BAAI/bge-small-en-v1.5 (existing)
    Tamil: l3cube-pune/tamil-sentence-similarity-sbert (Tamil-specific)
    """
    
    MODELS = {
        'english': "BAAI/bge-small-en-v1.5",
        'tamil': "l3cube-pune/tamil-sentence-similarity-sbert"
    }
    
    def __init__(self):
        # No instance-level cache - use global cache only
        logger.info("Initialized Dual Embedding Manager")
    
    @classmethod
    def _check_redis_cache(cls, language: str) -> bool:
        """Check if model exists in Redis cache"""
        try:
            from ...redis_cache import cache
            key = f"embedding_model_loaded:{language}"
            cached = cache.get(key)
            if cached:
                logger.info(f"🔄 {language} model was previously loaded in another process")
                return True
            return False
        except Exception as e:
            logger.debug(f"Redis cache check failed: {e}")
            return False
    
    @classmethod
    def _mark_redis_cache(cls, language: str):
        """Mark model as loaded in Redis cache"""
        try:
            from ...redis_cache import cache
            key = f"embedding_model_loaded:{language}"
            cache.set(key, True, expire=3600 * 24)  # 24 hours
            logger.info(f"✅ Marked {language} model as loaded in Redis")
        except Exception as e:
            logger.debug(f"Redis cache marking failed: {e}")

    @classmethod
    def get_embeddings_static(cls, language: Literal['english', 'tamil']) -> HuggingFaceEmbeddings:
        """
        Class method to get appropriate embedding model for the language with Redis awareness
        Models are cached globally after first load for maximum performance
        """
        global _GLOBAL_EMBEDDING_CACHE
        
        if language not in cls.MODELS:
            raise ValueError(f"Unsupported language: {language}. Supported: {list(cls.MODELS.keys())}")
        
        # Return cached model if available (GLOBAL CACHE)
        if language in _GLOBAL_EMBEDDING_CACHE:
            logger.info(f"⚡ Using globally cached {language} embedding model")
            return _GLOBAL_EMBEDDING_CACHE[language]
        
        # Check if model was loaded in another process (REDIS AWARENESS)
        model_name = cls.MODELS[language]
        if cls._check_redis_cache(language):
            logger.info(f"🔄 {language} model exists in another process, loading to this process...")
        else:
            logger.info(f"🤖 Loading {language} embedding model: {model_name} (first time across all processes)")
        
        try:
            embedding_model = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            
            # Cache the model GLOBALLY
            _GLOBAL_EMBEDDING_CACHE[language] = embedding_model
            
            # Mark as loaded in Redis for other processes
            cls._mark_redis_cache(language)
            
            logger.info(f"✅ {language.title()} embedding model loaded and cached globally")
            logger.info(f"📊 Global cache now contains: {list(_GLOBAL_EMBEDDING_CACHE.keys())}")
            
            return embedding_model
            
        except Exception as e:
            logger.error(f"❌ Failed to load {language} embedding model {model_name}: {e}")
            raise e
    
    def get_embeddings(self, language: Literal['english', 'tamil']) -> HuggingFaceEmbeddings:
        """Instance method that calls the class method for backward compatibility"""
        return self.__class__.get_embeddings_static(language)
    
    @classmethod
    def get_model_info(cls, language: Literal['english', 'tamil']) -> dict:
        """
        Get information about the embedding model for a language
        """
        global _GLOBAL_EMBEDDING_CACHE
        return {
            'language': language,
            'model_name': cls.MODELS.get(language),
            'is_cached': language in _GLOBAL_EMBEDDING_CACHE,
            'global_cache_size': len(_GLOBAL_EMBEDDING_CACHE)
        }
    
    @classmethod
    def clear_cache(cls):
        """
        Clear all cached models to free memory
        """
        global _GLOBAL_EMBEDDING_CACHE
        cache_size = len(_GLOBAL_EMBEDDING_CACHE)
        _GLOBAL_EMBEDDING_CACHE.clear()
        logger.info(f"Cleared global embedding model cache ({cache_size} models removed)")
    
    @classmethod
    def preload_models(cls):
        """
        Preload both models for faster access
        """
        logger.info("Preloading all embedding models...")
        for language in cls.MODELS.keys():
            cls.get_embeddings_static(language)
        logger.info("All embedding models preloaded and cached globally")
    
    @classmethod
    def get_cache_status(cls) -> dict:
        """
        Get current global cache status
        """
        global _GLOBAL_EMBEDDING_CACHE
        return {
            'cached_languages': list(_GLOBAL_EMBEDDING_CACHE.keys()),
            'total_cached': len(_GLOBAL_EMBEDDING_CACHE),
            'available_languages': list(cls.MODELS.keys())
        }
