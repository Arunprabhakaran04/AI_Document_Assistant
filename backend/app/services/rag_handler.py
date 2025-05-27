import os
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

_vector_store_cache = {}

def load_vectorstore_for_user(user_id: int):
    try:
        if user_id in _vector_store_cache:
            print(f"Using cached vector store for user {user_id}")
            return _vector_store_cache[user_id]
        
        from ..services.rag_service import DocumentProcessor
        processor = DocumentProcessor()
        vector_store_path = os.path.join(processor.vector_store_dir, f"user_{user_id}", "current_pdf")
        
        print(f"Looking for vector store at: {vector_store_path}")
        
        index_file = os.path.join(vector_store_path, "index.faiss")
        pkl_file = os.path.join(vector_store_path, "index.pkl")
        
        if not os.path.exists(index_file) or not os.path.exists(pkl_file):
            print(f"Vector store files not found for user {user_id}")
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
        #caching the vector store - faster inference
        _vector_store_cache[user_id] = vectorstore
        print(f"Loaded vector store for user {user_id} with {vectorstore.index.ntotal} vectors")
        return vectorstore
        
    except Exception as e:
        print(f"Error loading vector store for user {user_id}: {e}")
        return None


def clear_user_cache(user_id: int):
    if user_id in _vector_store_cache:
        del _vector_store_cache[user_id]
        print(f"Cleared cache for user {user_id}")


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
        print(f"Error in RAG query: {e}")
        raise e


def get_general_llm_response(query):
    try:
        llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
        return llm.invoke(query).content
    except Exception as e:
        print(f"Error in general LLM: {e}")
        raise e