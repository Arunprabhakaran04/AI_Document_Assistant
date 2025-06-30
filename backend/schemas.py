from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class usercreate(BaseModel):
    email: EmailStr
    password: str
    
class userout(BaseModel):
    id : int
    created_at : datetime
    
class Post(BaseModel):
    id:Optional[int] = 1
    title : str
    content : str
    published : Optional[bool] = True
    
class user_message(BaseModel):
    user_message : str
    
class TokenData(BaseModel):
    id : int
    email : EmailStr