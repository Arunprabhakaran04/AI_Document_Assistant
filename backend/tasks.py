from celery import current_task
from .celery_app import celery_app
from .app.services.rag_service import DocumentProcessor
from .app.services.task_service import TaskService
from .database_connection import get_db_connection
from .vector_store_db import save_vector_store_path
import os

@celery_app.task(bind=True)
def process_pdf_task(self, user_id: int, file_path: str, filename: str):
    """Celery task for PDF processing"""
    try:
        # Update task status
        self.update_state(state='PROCESSING', meta={'message': 'Starting PDF processing...'})
        TaskService.update_task_status(self.request.id, 'processing', 'Starting PDF processing...')
        
        processor = DocumentProcessor()
        
        # Update progress - Loading PDF
        self.update_state(state='PROCESSING', meta={'message': 'Loading and extracting text from PDF...'})
        TaskService.update_task_status(self.request.id, 'processing', 'Loading and extracting text from PDF...')
        raw_text = processor.process_pdf(file_path)
        
        # Update progress - Text splitting
        self.update_state(state='PROCESSING', meta={'message': 'Splitting text into chunks...'})
        TaskService.update_task_status(self.request.id, 'processing', 'Splitting text into chunks...')
        chunks = processor.split_text(raw_text)
        
        # Update progress - Creating embeddings
        self.update_state(state='PROCESSING', meta={'message': 'Creating embeddings...'})
        TaskService.update_task_status(self.request.id, 'processing', 'Creating embeddings...')
        vector_store = processor.create_vector_store(chunks)  # Use existing chunks
        print(f"Vector store created with {vector_store.index.ntotal} vectors")

        vector_store_dir = os.path.join(processor.vector_store_dir, f"user_{user_id}")
        os.makedirs(vector_store_dir, exist_ok=True)
        
        # Update progress - Saving vector store
        self.update_state(state='PROCESSING', meta={'message': 'Saving vector store...'})
        TaskService.update_task_status(self.request.id, 'processing', 'Saving vector store...')
        
        vector_store_path = os.path.join(vector_store_dir, "current_pdf")
        vector_store.save_local(vector_store_path, index_name="index")
        
        if not os.path.exists(os.path.join(vector_store_path, "index.faiss")):
            raise Exception("Vector store files not created properly")
            
        print(f"Vector store saved to: {vector_store_path}")

        # Update progress - Updating database
        self.update_state(state='PROCESSING', meta={'message': 'Finalizing...'})
        TaskService.update_task_status(self.request.id, 'processing', 'Finalizing...')

        with get_db_connection() as conn:
            save_vector_store_path(conn, user_id, vector_store_path)

        # Mark task as completed
        TaskService.update_task_status(self.request.id, 'completed', 'PDF processed successfully')

        return {
            'status': 'completed',
            'message': 'PDF processed successfully',
            'vector_count': vector_store.index.ntotal
        }
        
    except Exception as e:
        print(f"Error in PDF processing task: {str(e)}")
        
        # Update task status in database
        TaskService.update_task_status(self.request.id, 'failed', str(e))
        
        self.update_state(
            state='FAILURE',
            meta={'message': str(e)}
        )
        raise 