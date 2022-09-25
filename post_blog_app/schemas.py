from pydantic import BaseModel, EmailStr
from datetime import datetime


# Schemas
class User(BaseModel):
    login: str
    email: EmailStr
    password: str


class UserToConfirm(BaseModel):
    login: str
    email: EmailStr
    code: int
    valid_time: datetime


class Post(BaseModel):
    #author
    created: datetime
    edited: datetime


class Paragraph(BaseModel):
    #post
    paragraph_number: int
    paragraph_type: str
    paragraph_style: str
    url: str
    paragraph_content: str


class Likes(BaseModel):
    #post
    #author
    value: int


class Comments(BaseModel):
    #post
    #comment
    #author
    content: str
    created: datetime


class CommentsLikes(BaseModel):
    #comment
    #author
    value: int


class Messages(BaseModel):
    #sender
    #reciver
    created: datetime
    seen: bool
    content: str
