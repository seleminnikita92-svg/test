from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)

class User(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool

    class Config:
        from_attributes = True
class ArtistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    genre: str = Field(min_length=1, max_length=100)

class Artist(BaseModel):
    id: int
    name: str
    genre: str
    owner_id: int

    class Config:
        from_attributes = True
class AlbumCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    release_year: int = Field(gt=1900, lt=2100)
    artist_name: str = Field(min_length=1, max_length=200)

class Album(BaseModel):
    id: int
    title: str
    release_year: int
    artist_name: str
    owner_id: int

    class Config:
        from_attributes = True
class PlaylistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)

class Playlist(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int

    class Config:
        from_attributes = True
class Token(BaseModel):
    access_token: str
    token_type: str
