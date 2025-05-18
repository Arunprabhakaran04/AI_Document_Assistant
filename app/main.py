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
app = FastAPI()

conn = get_db_connection()
if conn is None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")
else:
    cursor = conn.cursor()
# posts = [{"id" : 1, "name":"arun","content" : "hello world"}, {"id" : 2, "name":"turuun","content" : "hello darkness"}]


# def getindex(id):
#     for post in posts:
#         if post["id"] == id:
#             return posts.index(post)

#create request -
@app.post("/posts")
async def create_post(post: Post):
    
    cursor.execute("INSERT INTO posts (name, content, published) VALUES (%s, %s, %s) RETURNING *", (post.name, post.content, post.published))
    post = cursor.fetchone()
    conn.commit()
    return {"data inserted" : post, "status_code" : status.HTTP_201_CREATED}
   
     
#read request - 
@app.get("/posts")
async def get_posts():
    cursor.execute("SELECT * FROM posts")
    post = cursor.fetchall()
    return post

@app.get("/posts/{id}")
async def get_post(id: int):
    cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
    post = cursor.fetchone()
    if post:
        return post
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"post with id {id} not found")
    
#update request - 
@app.put("/posts/{id}")
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
@app.delete("/posts/{id}")
async def delete_post(id: int):
    cursor.execute("delete from posts where id  = %s returning *", (id,))
    deleted_post = cursor.fetchone()
    conn.commit()
    if deleted_post:
        return {"message" : status.HTTP_200_OK}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} not found")
    
#creating a new user - 
@app.post("/users", status_code=status.HTTP_201_CREATED, response_model = UserOut)
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
@app.get("/users")
async def get_users():
    cursor.execute("SELECT * FROM users")
    all_users = cursor.fetchall()
    return all_users

#retriving individual users - 
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    fetched_user = cursor.fetchone()
    if fetched_user:
        return fetched_user
    else:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user with id {user_id} is not found")
    
#updating an user - 
@app.put("/users/{user_id}")
async def update_user(user_id:int, user:UserCreate):
    cursor.execute("UPDATE users SET email = %s, password = %s where id = %s RETURNING *", (user.email, user.password, user_id))
    updated_user = cursor.fetchone()
    conn.commit()
    if updated_user:
        return updated_user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user with id {user_id} not found ")
    
#delete an user - 
@app.delete("/users/{user_id}", response_model=UserOut)
async def delete_user(user_id:int):
    cursor.execute("DELETE FROM users WHERE id = %s returning *", (user_id,))
    deleted_user = cursor.fetchone()
    conn.commit()
    if deleted_user:
        return deleted_user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "user not found ")
    
    