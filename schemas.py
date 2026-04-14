from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserOut(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class BoardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=30, examples=['My Board'])

class BoardCreate(BoardBase):
    pass

class BoardOut(BoardBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)

class ListBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=50, examples=['To-do'])

class ListCreate(ListBase):
    position: Optional[float] = 100.0

class ListOut(ListBase):
    id: int
    board_id: int
    position: float

    model_config = ConfigDict(from_attributes=True)

class CardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=50, examples=['I need to do something'])
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator('description')
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str) and not v.strip():
            return None
        else:
            return v

class CardCreate(CardBase):
    position: Optional[float] = 100.0

class CardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=50, examples=['I need to do something'])
    description: Optional[str] = Field(None, max_length=2000)
    list_id: Optional[int] = None
    position: Optional[float] = None


    @field_validator('description')
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str) and not v.strip():
            return None
        else:
            return v

class CardOut(CardBase):
    id: int
    list_id: int
    position: float

    model_config = ConfigDict(from_attributes=True)