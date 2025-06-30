from fastapi import FastAPI
from backend.app.routers import users, chat, pdf
from backend.database_connection import get_connection_pool, close_connection_pool

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool on startup"""
    get_connection_pool()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown"""
    close_connection_pool()

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(pdf.router)
