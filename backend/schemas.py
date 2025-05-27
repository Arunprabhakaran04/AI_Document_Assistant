from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class usercreate(BaseModel):
    email: EmailStr
    password: str
    
class userout(BaseModel):
    id : int
    created_at : str
    
class Post(BaseModel):
    id:Optional[int] = 1
    title : str
    content : str
    published : Optional[bool] = True
    
class user_message(BaseModel):
    user_message : str
    
class TokenData(BaseModel):
    id : Optional[int]
    email : EmailStr