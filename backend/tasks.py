from celery import current_task
from .celery_app import celery_app
from .app.services.rag_service import DocumentProcessor
from .app.services.dual_embedding_manager import DualEmbeddingManager
from .app.services.task_service import TaskService
from .database_connection import get_db_connection
from .vector_store_db import save_vector_store_path
from loguru import logger
import os

@celery_app.task(bind=True)
def process_pdf_task(self, user_id: int, file_path: str, filename: str):
    """Enhanced Celery task with language support and improved caching"""
    task_id = self.request.id
    
    logger.info(f"🚀 Starting PDF processing task for user {user_id} in Celery worker")
    logger.info(f"📋 Task ID: {task_id}")
    logger.info(f"📄 File: {filename}")
    logger.info(f"📂 Path: {file_path}")
    logger.info(f"🔧 Process ID: {os.getpid()}")  # Show which process is running
    
    try:
        # Validate file exists before processing
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Update task status
        self.update_state(state='PROCESSING', meta={'message': 'Starting PDF processing...'})
        TaskService.update_task_status(task_id, 'processing', 'Starting PDF processing...')
        
        processor = DocumentProcessor()
        
        # Update progress - Loading PDF with language detection
        logger.info("Loading and extracting text from PDF with language detection...")
        self.update_state(state='PROCESSING', meta={'message': 'Loading and extracting text from PDF...'})
        TaskService.update_task_status(task_id, 'processing', 'Loading and extracting text from PDF...')
        
        # Enhanced PDF processing with language detection
        raw_text, language = processor.process_pdf(file_path)
        logger.info(f"PDF text extracted successfully - {len(raw_text)} characters, Language: {language}")
        
        # Update progress - Language-aware text splitting
        logger.info(f"Splitting {language} text into chunks...")
        self.update_state(state='PROCESSING', meta={'message': f'Splitting {language} text into chunks...'})
        TaskService.update_task_status(task_id, 'processing', f'Splitting {language} text into chunks...')
        chunks = processor.split_text(raw_text, language)
        logger.info(f"Text split into {len(chunks)} chunks for {language} processing")
        
        # Update progress - Creating language-specific embeddings
        logger.info(f"Creating {language} embeddings...")
        self.update_state(state='PROCESSING', meta={'message': f'Creating {language} embeddings...'})
        TaskService.update_task_status(task_id, 'processing', f'Creating {language} embeddings...')
        vector_store = processor.create_vector_store(chunks, language)
        logger.info(f"Vector store created with {vector_store.index.ntotal} vectors using {language} embeddings")

        vector_store_dir = os.path.join(processor.vector_store_dir, f"user_{user_id}")
        os.makedirs(vector_store_dir, exist_ok=True)
        
        # Update progress - Saving vector store
        logger.info(f"Saving {language} vector store...")
        self.update_state(state='PROCESSING', meta={'message': 'Saving vector store...'})
        TaskService.update_task_status(task_id, 'processing', 'Saving vector store...')
        
        vector_store_path = os.path.join(vector_store_dir, "current_pdf")
        vector_store.save_local(vector_store_path, index_name="index")
        
        if not os.path.exists(os.path.join(vector_store_path, "index.faiss")):
            raise Exception("Vector store files not created properly")
            
        logger.info(f"Vector store saved to: {vector_store_path}")

        # Update progress - Updating database with language info
        logger.info("Finalizing database update with language information...")
        self.update_state(state='PROCESSING', meta={'message': 'Finalizing...'})
        TaskService.update_task_status(task_id, 'processing', 'Finalizing...')

        # Get embedding model name for saving
        embedding_model = DualEmbeddingManager.MODELS[language]  # Use class attribute

        with get_db_connection() as conn:
            save_vector_store_path(conn, user_id, vector_store_path, language, embedding_model)

        # Mark task as completed
        TaskService.update_task_status(task_id, 'completed', f'{language.title()} PDF processed successfully')

        logger.info(f"{language.title()} PDF processing completed successfully for user {user_id}")
        logger.info(f"Final stats: {vector_store.index.ntotal} vectors, {len(chunks)} chunks, Language: {language}")
        logger.info(f"Embedding model used: {embedding_model}")

        return {
            'status': 'completed',
            'message': f'{language.title()} PDF processed successfully',
            'vector_count': vector_store.index.ntotal,
            'language': language,
            'embedding_model': embedding_model,
            'chunks_count': len(chunks)
        }
        
    except Exception as e:
        error_msg = f"Error in PDF processing task: {str(e)}"
        logger.error(f"{error_msg}")
        logger.exception("Full error traceback:")
        
        # Update task status in database
        try:
            TaskService.update_task_status(task_id, 'failed', str(e))
        except Exception as db_error:
            logger.error(f"Failed to update task status: {db_error}")
        
        # Update Celery state with proper format
        self.update_state(
            state='FAILURE',
            meta={
                'message': str(e),
                'error': error_msg,
                'exc_type': type(e).__name__,
                'exc_message': str(e)
            }
        )
        
        # Re-raise the exception with proper Celery format
        raise Exception(error_msg) 