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
from ...oauth2 import create_access_token, verify_access_token, get_current_user

router = APIRouter()

conn = get_db_connection()
if conn is None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")
else:
    cursor = conn.cursor()

class PostSchema(BaseModel):
    title: str
    content: str
    published: Optional[bool] = True


@router.post("/create_post", status_code=status.HTTP_201_CREATED, response_model = Post)
async def create_post(post : PostSchema, token : str = Depends(get_current_user)):
    cursor.execute("INSERT INTO posts (name, content, published) VALUES (%s, %s, %s) RETURNING *", (post.title, post.content, post.published))
    new_post = cursor.fetchone()
    conn.commit()
    return new_post