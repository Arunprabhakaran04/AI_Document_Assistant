#!/usr/bin/env python3
"""
Script to start Celery worker for PDF processing
Usage: python start_celery.py
"""

import os
import sys
from backend.celery_app import celery_app

if __name__ == "__main__":
    # Set the log level
    log_level = os.getenv("CELERY_LOG_LEVEL", "info")
    
    # Start the worker with pool=solo for Windows compatibility
    celery_app.worker_main([
        "worker",
        "--loglevel=" + log_level,
        "--pool=solo",  # Use solo pool for Windows
        "--queues=pdf_processing",
        "--without-gossip",  # Disable gossip for better Windows compatibility
        "--without-mingle",  # Disable mingle for better Windows compatibility
        "--without-heartbeat"  # Disable heartbeat for better Windows compatibility
    ]) 