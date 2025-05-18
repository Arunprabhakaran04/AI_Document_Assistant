from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email : EmailStr
    password : str
    
class UserOut(BaseModel): 
    id : int
    email : EmailStr
    
class Post(BaseModel):
    id:Optional[int] = 1
    name:str
    content:str
    published:Optional[bool] = True