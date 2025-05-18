from fastapi import FastAPI, HTTPException, status, APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from passlib.context import CryptContext
from psycopg2 import connect, errors
from psycopg2.extras import RealDictCursor
from app.schemas import UserCreate, UserOut, Post
from app.database_connection import get_db_connection
from app.util import password_encrypt, password_verify

router = APIRouter()

conn = get_db_connection()
if conn is None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")
else:
    cursor = conn.cursor()

#creating a new user - 
@router.post("/users", status_code=status.HTTP_201_CREATED, response_model = UserOut)
async def create_user(user : UserCreate):
    try:
        password = password_encrypt(user.password)
        user.password = password
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s) RETURNING *", (user.email, user.password))
        new_user = cursor.fetchone()
        conn.commit()
        return new_user
    except errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
        
        
#retriving the users - 
@router.get("/users")
async def get_users():
    cursor.execute("SELECT * FROM users")
    all_users = cursor.fetchall()
    return all_users

#retriving individual users - 
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    fetched_user = cursor.fetchone()
    if fetched_user:
        return fetched_user
    else:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user with id {user_id} is not found")
    
#updating an user - 
@router.put("/users/{user_id}")
async def update_user(user_id:int, user:UserCreate):
    cursor.execute("UPDATE users SET email = %s, password = %s where id = %s RETURNING *", (user.email, user.password, user_id))
    updated_user = cursor.fetchone()
    conn.commit()
    if updated_user:
        return updated_user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user with id {user_id} not found ")
    
#delete an user - 
@router.delete("/users/{user_id}", response_model=UserOut)
async def delete_user(user_id:int):
    cursor.execute("DELETE FROM users WHERE id = %s returning *", (user_id,))
    deleted_user = cursor.fetchone()
    conn.commit()
    if deleted_user:
        return deleted_user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "user not found ")
    
    