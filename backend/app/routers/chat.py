from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import os
from loguru import logger

from ...oauth2 import get_current_user
from ...schemas import TokenData
from ..services.rag_handler import load_vectorstore_for_user, get_user_query_response, get_general_llm_response, clear_user_cache, get_cache_info
from ..services.chat_db_service import ChatDBService
from ..services.rag_service import DocumentProcessor

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class ChatRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    has_pdf: bool = False

class ChatTitleUpdate(BaseModel):
    title: str

@router.post("/chat")
async def chat_with_rag(request: Request, data: ChatRequest, current_user: TokenData = Depends(get_current_user)):
    logger.info(f"💬 Chat request from user {current_user.email}")
    logger.debug(f"📝 Request data: {data}")
    
    try:
        # Create or get chat record
        if data.chat_id:
            chat_info = ChatDBService.create_or_get_chat(current_user.id, data.chat_id, data.query)
        
        # Save user message
        if data.chat_id:
            ChatDBService.save_message(data.chat_id, "user", data.query)
        
        # Get AI response
        if not data.has_pdf:
            logger.info("🤖 Using general LLM response")
            response = get_general_llm_response(data.query)
            source = "general"
        else:
            logger.info("📄 Attempting to use PDF context")
            vectorstore = load_vectorstore_for_user(current_user.id)
            if vectorstore is None:
                logger.warning("⚠️ No vector store found, falling back to general LLM")
                response = get_general_llm_response(data.query)
                source = "general"
            else:
                logger.success("📄 Using PDF context for response")
                response = get_user_query_response(vectorstore, data.query)
                source = "rag"
        
        # Handle response format
        if isinstance(response, dict):
            response = response.get("result") or next((v for v in response.values() if isinstance(v, str)), "[No response]")
        
        # Save assistant message
        if data.chat_id:
            ChatDBService.save_message(data.chat_id, "assistant", response, source)
        
        logger.success(f"✅ Chat response sent (source: {source})")
        return {"response": response, "source": source}
            
    except Exception as e:
        logger.error(f"❌ Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/list_chats")
async def list_user_chats(current_user: TokenData = Depends(get_current_user)):
    """Get all chats for the current user"""
    try:
        chats = ChatDBService.get_user_chats(current_user.id)
        return {"chats": chats}
    except Exception as e:
        print(f"Error fetching chats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching chat history")

@router.get("/chat_history/{chat_id}")
async def get_chat_history(chat_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get message history for a specific chat"""
    try:
        messages = ChatDBService.get_chat_messages(chat_id, current_user.id)
        return {"messages": messages}
    except Exception as e:
        print(f"Error fetching chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching chat history")

@router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: str, current_user: TokenData = Depends(get_current_user)):
    """Delete a specific chat"""
    try:
        ChatDBService.delete_chat(chat_id, current_user.id)
        return {"message": "Chat deleted successfully"}
    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting chat")

@router.put("/chat/{chat_id}/title")
async def update_chat_title(chat_id: str, data: ChatTitleUpdate, current_user: TokenData = Depends(get_current_user)):
    """Update chat title"""
    try:
        ChatDBService.update_chat_title(chat_id, current_user.id, data.title)
        return {"message": "Chat title updated successfully"}
    except Exception as e:
        print(f"Error updating chat title: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating chat title")

@router.post("/clear_cache")
async def clear_cache(current_user: TokenData = Depends(get_current_user)):
    clear_user_cache(current_user.id)
    return {"message": "Cache cleared"}

@router.get("/cache_status")
async def get_cache_status(current_user: TokenData = Depends(get_current_user)):
    """Get cache status for debugging"""
    cache_info = get_cache_info()
    return {
        "user_id": current_user.id,
        "user_has_cache": current_user.id in cache_info["cached_users"],
        "cache_info": cache_info
    }

@router.post("/clear_pdf")
async def clear_pdf(current_user: TokenData = Depends(get_current_user)):
    """Clear PDF data for the current user"""
    try:
        logger.info(f"🗑️ Clearing PDF data for user {current_user.id}")
        
        # Clear the in-memory cache
        clear_user_cache(current_user.id)
        
        # Clean up vector store files
        processor = DocumentProcessor()
        user_vector_dir = os.path.join(processor.vector_store_dir, f"user_{current_user.id}")
        if os.path.exists(user_vector_dir):
            import shutil
            shutil.rmtree(user_vector_dir)
            logger.info(f"🗑️ Cleaned up vector store for user {current_user.id}")
        
        logger.success(f"✅ PDF data cleared successfully for user {current_user.id}")
        return {"message": "PDF data cleared successfully"}
    except Exception as e:
        logger.error(f"❌ Error clearing PDF data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error clearing PDF data")