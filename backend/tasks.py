from celery import current_task
from .celery_app import celery_app
from .app.services.rag_service import DocumentProcessor
from .app.services.task_service import TaskService
from .database_connection import get_db_connection
from .vector_store_db import save_vector_store_path
from loguru import logger
import os

@celery_app.task(bind=True)
def process_pdf_task(self, user_id: int, file_path: str, filename: str):
    """Celery task for PDF processing"""
    task_id = self.request.id
    
    logger.info(f"Starting PDF processing task for user {user_id}")
    logger.info(f"Task ID: {task_id}")
    logger.info(f"File: {filename}")
    logger.info(f"Path: {file_path}")
    
    try:
        # Update task status
        self.update_state(state='PROCESSING', meta={'message': 'Starting PDF processing...'})
        TaskService.update_task_status(task_id, 'processing', 'Starting PDF processing...')
        
        processor = DocumentProcessor()
        
        # Update progress - Loading PDF
        logger.info("Loading and extracting text from PDF...")
        self.update_state(state='PROCESSING', meta={'message': 'Loading and extracting text from PDF...'})
        TaskService.update_task_status(task_id, 'processing', 'Loading and extracting text from PDF...')
        raw_text = processor.process_pdf(file_path)
        logger.success(f"PDF text extracted successfully - {len(raw_text)} characters")
        
        # Update progress - Text splitting
        logger.info("Splitting text into chunks...")
        self.update_state(state='PROCESSING', meta={'message': 'Splitting text into chunks...'})
        TaskService.update_task_status(task_id, 'processing', 'Splitting text into chunks...')
        chunks = processor.split_text(raw_text)
        logger.success(f"Text split into {len(chunks)} chunks")
        
        # Update progress - Creating embeddings
        logger.info("Creating embeddings...")
        self.update_state(state='PROCESSING', meta={'message': 'Creating embeddings...'})
        TaskService.update_task_status(task_id, 'processing', 'Creating embeddings...')
        vector_store = processor.create_vector_store(chunks)
        logger.success(f"Vector store created with {vector_store.index.ntotal} vectors")

        vector_store_dir = os.path.join(processor.vector_store_dir, f"user_{user_id}")
        os.makedirs(vector_store_dir, exist_ok=True)
        
        # Update progress - Saving vector store
        logger.info("Saving vector store...")
        self.update_state(state='PROCESSING', meta={'message': 'Saving vector store...'})
        TaskService.update_task_status(task_id, 'processing', 'Saving vector store...')
        
        vector_store_path = os.path.join(vector_store_dir, "current_pdf")
        vector_store.save_local(vector_store_path, index_name="index")
        
        if not os.path.exists(os.path.join(vector_store_path, "index.faiss")):
            raise Exception("Vector store files not created properly")
            
        logger.success(f" Vector store saved to: {vector_store_path}")

        # Update progress - Updating database
        logger.info("Finalizing database update...")
        self.update_state(state='PROCESSING', meta={'message': 'Finalizing...'})
        TaskService.update_task_status(task_id, 'processing', 'Finalizing...')

        with get_db_connection() as conn:
            save_vector_store_path(conn, user_id, vector_store_path)

        # Mark task as completed
        TaskService.update_task_status(task_id, 'completed', 'PDF processed successfully')

        logger.success(f"PDF processing completed successfully for user {user_id}")
        logger.info(f"Final stats: {vector_store.index.ntotal} vectors, {len(chunks)} chunks")

        return {
            'status': 'completed',
            'message': 'PDF processed successfully',
            'vector_count': vector_store.index.ntotal
        }
        
    except Exception as e:
        error_msg = f"Error in PDF processing task: {str(e)}"
        logger.error(f"{error_msg}")
        logger.exception("Full error traceback:")
        
        # Update task status in database
        TaskService.update_task_status(task_id, 'failed', str(e))
        
        self.update_state(
            state='FAILURE',
            meta={'message': str(e)}
        )
        raise 