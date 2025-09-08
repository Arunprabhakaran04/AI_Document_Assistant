import os
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger
from ...redis_cache import cache

_vector_store_cache = {}  # Keep in-memory cache as fallback

def load_vectorstore_for_user(user_id: int):
    try:
        # Check in-memory cache first (fastest)
        if user_id in _vector_store_cache:
            logger.info(f"Using in-memory cached vector store for user {user_id}")
            return _vector_store_cache[user_id]
        
        # Check Redis cache second (persistent across restarts)
        redis_key = f"vectorstore:user:{user_id}"
        cached_vectorstore = cache.get(redis_key)
        if cached_vectorstore:
            logger.info(f"Using Redis cached vector store for user {user_id}")
            _vector_store_cache[user_id] = cached_vectorstore  # Also cache in memory
            return cached_vectorstore
        
        # Load from disk if not in cache
        from ..services.rag_service import DocumentProcessor
        processor = DocumentProcessor()
        vector_store_path = os.path.join(processor.vector_store_dir, f"user_{user_id}", "current_pdf")
        
        logger.info(f"Loading vector store from disk: {vector_store_path}")
        
        index_file = os.path.join(vector_store_path, "index.faiss")
        pkl_file = os.path.join(vector_store_path, "index.pkl")
        
        if not os.path.exists(index_file) or not os.path.exists(pkl_file):
            logger.warning(f"Vector store files not found for user {user_id}")
            return None
            
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

        vectorstore = FAISS.load_local(
            vector_store_path, 
            embeddings, 
            index_name="index", 
            allow_dangerous_deserialization=True
        )
        
        # Cache in both Redis and memory
        _vector_store_cache[user_id] = vectorstore
        cache.set(redis_key, vectorstore, expire=3600)  # Cache for 1 hour
        
        logger.success(f"Loaded and cached vector store for user {user_id} with {vectorstore.index.ntotal} vectors")
        return vectorstore
        
    except Exception as e:
        logger.error(f"Error loading vector store for user {user_id}: {e}")
        # Clear the cache entries if loading fails
        if user_id in _vector_store_cache:
            del _vector_store_cache[user_id]
        cache.delete(f"vectorstore:user:{user_id}")
        return None


def clear_user_cache(user_id: int):
    """Clear the vector store cache for a specific user"""
    # Clear in-memory cache
    if user_id in _vector_store_cache:
        del _vector_store_cache[user_id]
        logger.info(f"Cleared in-memory cache for user {user_id}")
    
    # Clear Redis cache
    redis_key = f"vectorstore:user:{user_id}"
    cache.delete(redis_key)
    logger.info(f"Cleared Redis cache for user {user_id}")


def clear_all_cache():
    """Clear all vector store cache - useful for maintenance"""
    global _vector_store_cache
    cache_size = len(_vector_store_cache)
    _vector_store_cache = {}
    
    # Clear all vectorstore keys from Redis
    cleared_count = cache.clear_pattern("vectorstore:user:*")
    
    logger.info(f"Cleared all cache - {cache_size} in-memory entries and {cleared_count} Redis entries removed")


def get_cache_info():
    """Get information about current cache state"""
    redis_info = cache.get_cache_info()
    return {
        "in_memory": {
            "cached_users": list(_vector_store_cache.keys()),
            "cache_size": len(_vector_store_cache)
        },
        "redis": redis_info
    }


def get_user_query_response(vectorstore, query):
    try:
        llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm, 
            retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=False
        )
        return qa_chain.invoke(query)
    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        raise e


def get_general_llm_response(query):
    try:
        llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
        return llm.invoke(query).content
    except Exception as e:
        logger.error(f"Error in general LLM: {e}")
        raise e