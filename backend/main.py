from fastapi import FastAPI, HTTPException, status, APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from passlib.context import CryptContext
from psycopg2 import connect, errors
from psycopg2.extras import RealDictCursor
from app.schemas import UserCreate, UserOut, Post
from app.database_connection import get_db_connection
from app.util import password_encrypt, password_verify
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .app.routers import posts, users, chat, pdf
app = FastAPI()

app.include_router(users.router)
app.include_router(posts.router)
app.include_router(chat.router)
app.include_router(pdf.router)

