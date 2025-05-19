from fastapi import FastAPI, HTTPException, status, APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from passlib.context import CryptContext
from psycopg2 import connect, errors
from psycopg2.extras import RealDictCursor
from app.schemas import UserCreate, UserOut, Post, TokenData
from app.database_connection import get_db_connection
from app.util import password_encrypt, password_verify
from app.OAuth2 import get_current_user

router = APIRouter()

conn = get_db_connection()
if conn is None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")
else:
    cursor = conn.cursor()

#create request -
@router.post("/posts")
async def create_post(post: Post, user_detail : TokenData = Depends(get_current_user)):
    
    cursor.execute("INSERT INTO posts (name, content, published) VALUES (%s, %s, %s) RETURNING *", (post.name, post.content, post.published))
    post = cursor.fetchone()
    conn.commit()
    return {"data inserted" : post, "status_code" : status.HTTP_201_CREATED}
   
     
#read request - 
@router.get("/posts")
async def get_posts():
    cursor.execute("SELECT * FROM posts")
    post = cursor.fetchall()
    return post

@router.get("/posts/{id}")
async def get_post(id: int):
    cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
    post = cursor.fetchone()
    if post:
        return post
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"post with id {id} not found")
    
#update request - 
@router.put("/posts/{id}")
async def update_post(id:int, post:Post):
    cursor.execute("update posts set name = %s, content = %s, published = %s where id = %s returning *", (post.name, post.content, post.published, id))
    updated_post = cursor.fetchone()
    print(updated_post)
    conn.commit()
    if updated_post:
        return {"post" : updated_post}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} not found")
    
#delete request - 
@router.delete("/posts/{id}")
async def delete_post(id: int):
    cursor.execute("delete from posts where id  = %s returning *", (id,))
    deleted_post = cursor.fetchone()
    conn.commit()
    if deleted_post:
        return {"message" : status.HTTP_200_OK}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} not found")