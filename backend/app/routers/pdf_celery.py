from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ...oauth2 import get_current_user
from ..utils.file_utils import save_pdf_file
from ...tasks import process_pdf_task
import os
import shutil

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/upload_pdf", status_code=202)
async def upload_pdf(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    user_data = get_current_user(token)
    user_id = user_data.id

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        cleanup_existing_vectorstore(user_id)
        
        file_path = save_pdf_file(file, user_id)
        print(f"PDF saved to: {file_path}")

        # Queue the task with Celery
        task = process_pdf_task.delay(user_id, file_path, file.filename)
        
        return {
            "message": "PDF uploaded successfully and queued for processing",
            "task_id": task.id,
            "status": "queued"
        }

    except Exception as e:
        print(f"Error in upload_pdf: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task_status/{task_id}")
async def get_task_status(task_id: str, token: str = Depends(oauth2_scheme)):
    """Get the status of a specific task"""
    from ...celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'queued',
            'message': 'Task is waiting to be processed'
        }
    elif task.state == 'PROCESSING':
        response = {
            'state': task.state,
            'status': 'processing',
            'message': task.info.get('message', 'Processing...')
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'status': 'completed',
            'message': task.result.get('message', 'Completed'),
            'result': task.result
        }
    else:  # FAILURE
        response = {
            'state': task.state,
            'status': 'failed',
            'message': str(task.info)
        }
    
    return response

@router.get("/processing_status")
async def get_user_processing_status(token: str = Depends(oauth2_scheme)):
    """Get all active tasks for the current user - simplified version"""
    user_data = get_current_user(token)
    
    # This is a simplified version. In production, you'd want to store
    # user-task relationships in your database for better tracking
    return {
        "message": "Use the task_id returned from upload_pdf to check specific task status",
        "user_id": user_data.id
    }

def cleanup_existing_vectorstore(user_id: int):
    try:
        from ..services.rag_service import DocumentProcessor
        processor = DocumentProcessor()
        user_vector_dir = os.path.join(processor.vector_store_dir, f"user_{user_id}")
        if os.path.exists(user_vector_dir):
            shutil.rmtree(user_vector_dir)
            print(f"Cleaned up existing vector store for user {user_id}")
    except Exception as e:
        print(f"Warning: Could not clean up existing vector store: {e}")

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    user_data = get_current_user(token)
    cleanup_existing_vectorstore(user_data.id)
    return {"message": "Logged out successfully"} 