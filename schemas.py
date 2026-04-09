from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class BoardBase(BaseModel):
    title: str

class BoardCreate(BoardBase):
    pass

class BoardOut(BoardBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True