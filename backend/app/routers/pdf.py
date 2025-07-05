from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ...oauth2 import get_current_user
from ..utils.file_utils import save_pdf_file
from ..services.rag_service import DocumentProcessor
from ...database_connection import get_db_connection
from ...vector_store_db import save_vector_store_path
from ..services.rag_handler import clear_user_cache
from loguru import logger
import os
import shutil

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/upload_pdf", status_code=201)
async def upload_pdf(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    user_data = get_current_user(token)
    user_id = user_data.id

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        cleanup_existing_vectorstore(user_id)
        
        file_path = save_pdf_file(file, user_id)
        logger.info(f"📁 PDF saved to: {file_path}")

        processor = DocumentProcessor()
        vector_store = processor.embed_pdf(file_path, file.filename)
        logger.success(f"🔢 Vector store created with {vector_store.index.ntotal} vectors")

        vector_store_dir = os.path.join(processor.vector_store_dir, f"user_{user_id}")
        os.makedirs(vector_store_dir, exist_ok=True)
        
        vector_store_path = os.path.join(vector_store_dir, "current_pdf")
        vector_store.save_local(vector_store_path, index_name="index")
        
        if not os.path.exists(os.path.join(vector_store_path, "index.faiss")):
            raise Exception("Vector store files not created properly")
            
        logger.success(f"💾 Vector store saved to: {vector_store_path}")

        with get_db_connection() as conn:
            save_vector_store_path(conn, user_id, vector_store_path)

        return {"message": "PDF uploaded and embedded successfully."}

    except Exception as e:
        logger.error(f"❌ Error in upload_pdf: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def cleanup_existing_vectorstore(user_id: int):
    try:
        processor = DocumentProcessor()
        user_vector_dir = os.path.join(processor.vector_store_dir, f"user_{user_id}")
        if os.path.exists(user_vector_dir):
            shutil.rmtree(user_vector_dir)
            logger.info(f"🗑️ Cleaned up existing vector store for user {user_id}")
    except Exception as e:
        logger.warning(f"⚠️ Could not clean up existing vector store: {e}")
    
    # Clear the in-memory cache for this user
    clear_user_cache(user_id)


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    user_data = get_current_user(token)
    cleanup_existing_vectorstore(user_data.id)
    return {"message": "Logged out successfully"}