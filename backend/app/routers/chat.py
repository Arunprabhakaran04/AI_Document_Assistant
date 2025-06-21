# Updated chat.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional

from ...oauth2 import get_current_user
from ..services.rag_handler import load_vectorstore_for_user, get_user_query_response, get_general_llm_response, clear_user_cache

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class ChatRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    has_pdf: bool = False  

@router.post("/chat")
async def chat_with_rag(request: Request, data: ChatRequest, token: str = Depends(oauth2_scheme)):
    print(f"Received request data: {data}")
    print(f"Token: {token}")
    
    user_data = get_current_user(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        # OPTIMIZATION: Skip vectorstore loading if frontend indicates no PDF
        if not data.has_pdf:
            response = get_general_llm_response(data.query)
            return {"response": response, "source": "general"}
        
        # Only load vectorstore if frontend indicates PDF exists
        vectorstore = load_vectorstore_for_user(user_data.id)
        
        if vectorstore is None:
            # Fallback: PDF status says yes, but vectorstore missing (edge case)
            response = get_general_llm_response(data.query)
            return {"response": response, "source": "general"}
        
        response = get_user_query_response(vectorstore, data.query)
        return {"response": response, "source": "rag"}
            
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.post("/clear_cache")
async def clear_cache(token: str = Depends(oauth2_scheme)):
    user_data = get_current_user(token)
    clear_user_cache(user_data.id)
    return {"message": "Cache cleared"}