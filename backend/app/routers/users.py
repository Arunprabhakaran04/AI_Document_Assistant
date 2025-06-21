from fastapi import FastAPI, HTTPException, status, APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from passlib.context import CryptContext
from psycopg2 import connect, errors
from psycopg2.extras import RealDictCursor
from ...schemas import usercreate, userout, Post
from ...database_connection import get_db_connection
from ...util import encrypt, verify
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ...oauth2 import create_access_token, verify_access_token

router = APIRouter()

conn = get_db_connection()
if conn is None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")
else :
    cursor = conn.cursor()
    
class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register", status_code = status.HTTP_201_CREATED, response_model = userout)
async def create_user(user : usercreate):
    password = encrypt(user.password)
    user.password = password
    cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s) RETURNING *", (user.email, user.password))
    new_user = cursor.fetchone()
    conn.commit()
    return new_user

@router.post("/login")
async def login_user(userdata : UserLogin):
    cursor.execute("SELECT * FROM users WHERE users.email = %s",(userdata.email,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
    if not verify(userdata.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "password incorrect")
    else:
        access_token = create_access_token(data = {"user_id" : user["id"], "email" : user["email"]})
        return {"access_token":  access_token, "token_type" : "bearer"}
    