#what we are going to build now is a basic CRUD application 
"""
c - create - post request
r - read - get request
u - update - put request 
d - delete - delete request
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from passlib.context import CryptContext
from psycopg2 import connect, errors
from psycopg2.extras import RealDictCursor
from app.schemas import UserCreate, UserOut, Post
from app.database_connection import get_db_connection
from app.util import password_encrypt, password_verify
from app.routers import posts, users

app = FastAPI()

app.include_router(posts.router)
app.include_router(users.router)

