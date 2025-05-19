from fastapi import FastAPI, APIRouter, HTTPException, status, Depends
from passlib.context import CryptContext
from passlib.context import CryptContext
from psycopg2 import connect, errors
from psycopg2.extras import RealDictCursor
from app.schemas import UserCreate, UserOut, Post
from app.database_connection import get_db_connection
from app.util import password_encrypt, password_verify
from .. OAuth2 import create_access_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

conn = get_db_connection()
if conn:
    cursor = conn.cursor()
else:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")

@router.post("/login")
async def login_user(userdetails : OAuth2PasswordRequestForm = Depends()):
    cursor.execute("SELECT * FROM users WHERE users.email = %s", (userdetails.username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
    if not password_verify(userdetails.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "password incorrect")
    else:
        access_token = create_access_token(data = {"user_id" : user["id"], "email" : user["email"]})
        return {"access_token":  access_token, "token_type" : "bearer"}     
        