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

app = FastAPI()

class Post(BaseModel):
    id:int
    name:str
    content:str
    rating:Optional[int] = None

posts = [{"id" : 1, "name":"arun","content" : "hello world"}, {"id" : 2, "name":"turuun","content" : "hello darkness"}]
def getindex(id):
    for post in posts:
        if post["id"] == id:
            return posts.index(post)

#create request -
@app.post("/posts")
async def create_post(post: Post):
    post_dict = post.model_dump()
    posts.append(post_dict)
    return post_dict  # or return {"message": "Post created successfully"}
   
     
#read request - 
@app.get("/posts")
async def get_posts():
    return posts

@app.get("/posts/{id}")
async def get_post(id: int):
    index = getindex(id)
    if index != -1:
        return posts[index]
    else:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"post with id {id} not found")
    
#update request - 
@app.put("/posts/{id}")
async def update_post(id:int, post:Post):
    index = getindex(id)
    if index != -1:
        post_dict = post.model_dump()
        posts[index] = post_dict
        return {"message" : status.HTTP_200_OK}
    
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} not found")
    
#delete request - 
@app.delete("/posts/{id}")
async def delete_post(id: int):
    index = getindex(id)
    if index != -1:
        posts.pop(index)
        return {"message" : status.HTTP_200_OK}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} not found")
