from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import security
import schemas
import models
from database import engine, get_db, Base

app = FastAPI(
    title="Music Collection API",
    description="Управление личной музыкальной коллекцией: исполнители, альбомы, плейлисты",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ===== АУТЕНТИФИКАЦИЯ =====

@app.post(
    "/register", 
    response_model=schemas.User,
    summary="Регистрация пользователя",
    description="Создает нового пользователя. Первый пользователь с username='admin' становится администратором."
)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверка существующего пользователя
    result = await db.execute(
        select(models.User).filter(
            (models.User.username == user.username) | 
            (models.User.email == user.email)
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(status_code=400, detail="Username already registered")
        else:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Первый пользователь с username="admin" становится админом
    is_admin = (user.username == "admin")
    
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_admin=is_admin
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@app.post(
    "/login", 
    response_model=schemas.Token,
    summary="Вход в систему",
    description="Проверяет логин и пароль, возвращает JWT токен."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.User).filter(models.User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    
    access_token = security.create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ===== ARTISTS (ПОЛНЫЙ CRUD) =====

@app.post(
    "/artists", 
    response_model=schemas.Artist,
    summary="Создать исполнителя",
    description="Добавляет нового исполнителя в коллекцию."
)
async def create_artist(
    artist: schemas.ArtistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_artist = models.Artist(
        **artist.model_dump(),
        owner_id=current_user.id
    )
    
    db.add(db_artist)
    await db.commit()
    await db.refresh(db_artist)
    
    return db_artist

@app.get(
    "/artists", 
    response_model=list[schemas.Artist],
    summary="Получить список исполнителей",
    description="Возвращает список исполнителей текущего пользователя. Можно фильтровать по жанру."
)
async def get_artists(
    genre: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = select(models.Artist).filter(models.Artist.owner_id == current_user.id)
    
    if genre:
        query = query.filter(models.Artist.genre == genre)
    
    result = await db.execute(query)
    artists = result.scalars().all()
    return artists

@app.get(
    "/artists/{artist_id}", 
    response_model=schemas.Artist,
    summary="Получить исполнителя по ID",
    description="Возвращает информацию об исполнителе по его ID."
)
async def get_artist(
    artist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    result = await db.execute(
        select(models.Artist).filter(
            models.Artist.id == artist_id,
            models.Artist.owner_id == current_user.id
        )
    )
    artist = result.scalar_one_or_none()
    
    if artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    return artist

@app.put(
    "/artists/{artist_id}", 
    response_model=schemas.Artist,
    summary="Обновить исполнителя",
    description="Изменяет данные существующего исполнителя."
)
async def update_artist(
    artist_id: int,
    artist: schemas.ArtistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    result = await db.execute(
        select(models.Artist).filter(
            models.Artist.id == artist_id,
            models.Artist.owner_id == current_user.id
        )
    )
    db_artist = result.scalar_one_or_none()
    
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    db_artist.name = artist.name
    db_artist.genre = artist.genre
    
    await db.commit()
    await db.refresh(db_artist)
    
    return db_artist

@app.delete(
    "/artists/{artist_id}", 
    summary="Удалить исполнителя",
    description="Удаляет исполнителя по ID."
)
async def delete_artist(
    artist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    result = await db.execute(
        select(models.Artist).filter(
            models.Artist.id == artist_id,
            models.Artist.owner_id == current_user.id
        )
    )
    db_artist = result.scalar_one_or_none()
    
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    await db.delete(db_artist)
    await db.commit()
    
    return {"message": "Artist deleted successfully"}

# ===== ALBUMS =====

@app.post(
    "/albums", 
    response_model=schemas.Album,
    summary="Создать альбом",
    description="Добавляет новый альбом в коллекцию."
)
async def create_album(
    album: schemas.AlbumCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_album = models.Album(
        **album.model_dump(),
        owner_id=current_user.id
    )
    
    db.add(db_album)
    await db.commit()
    await db.refresh(db_album)
    
    return db_album

@app.get(
    "/albums", 
    response_model=list[schemas.Album],
    summary="Получить список альбомов",
    description="Возвращает список альбомов текущего пользователя."
)
async def get_albums(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    result = await db.execute(
        select(models.Album).filter(models.Album.owner_id == current_user.id)
    )
    albums = result.scalars().all()
    return albums

@app.delete(
    "/albums/{album_id}", 
    summary="Удалить альбом",
    description="Удаляет альбом по ID."
)
async def delete_album(
    album_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    result = await db.execute(
        select(models.Album).filter(
            models.Album.id == album_id,
            models.Album.owner_id == current_user.id
        )
    )
    db_album = result.scalar_one_or_none()
    
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    
    await db.delete(db_album)
    await db.commit()
    
    return {"message": "Album deleted successfully"}

# ===== PLAYLISTS =====

@app.post(
    "/playlists", 
    response_model=schemas.Playlist,
    summary="Создать плейлист",
    description="Создает новый плейлист."
)
async def create_playlist(
    playlist: schemas.PlaylistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_playlist = models.Playlist(
        **playlist.model_dump(),
        owner_id=current_user.id
    )
    
    db.add(db_playlist)
    await db.commit()
    await db.refresh(db_playlist)
    
    return db_playlist

@app.get(
    "/playlists", 
    response_model=list[schemas.Playlist],
    summary="Получить список плейлистов",
    description="Возвращает список плейлистов текущего пользователя."
)
async def get_playlists(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    result = await db.execute(
        select(models.Playlist).filter(models.Playlist.owner_id == current_user.id)
    )
    playlists = result.scalars().all()
    return playlists

@app.delete(
    "/playlists/{playlist_id}", 
    summary="Удалить плейлист",
    description="Удаляет плейлист по ID."
)
async def delete_playlist(
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    result = await db.execute(
        select(models.Playlist).filter(
            models.Playlist.id == playlist_id,
            models.Playlist.owner_id == current_user.id
        )
    )
    db_playlist = result.scalar_one_or_none()
    
    if db_playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    await db.delete(db_playlist)
    await db.commit()
    
    return {"message": "Playlist deleted successfully"}

# ===== АДМИН-ПАНЕЛЬ =====

@app.get(
    "/admin/users",
    response_model=list[schemas.User],
    summary="Просмотр всех пользователей",
    description="Список всех пользователей в системе. Доступно только администраторам."
)
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    result = await db.execute(select(models.User))
    users = result.scalars().all()
    return users

@app.delete(
    "/admin/users/{user_id}",
    summary="Удаление пользователя",
    description="Удаляет пользователя и все его данные по ID. Доступно только администраторам."
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    await db.delete(user)
    await db.commit()
    
    return {"message": f"Пользователь {user.username} удален"}

@app.get(
    "/admin/artists",
    response_model=list[schemas.Artist],
    summary="Просмотр всех исполнителей",
    description="Список исполнителей всех пользователей. Доступно только администраторам."
)
async def get_all_artists(
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    result = await db.execute(select(models.Artist))
    artists = result.scalars().all()
    return artists

@app.delete(
    "/admin/artists/{artist_id}",
    summary="Удаление исполнителя",
    description="Удаляет любого исполнителя по ID. Доступно только администраторам."
)
async def admin_delete_artist(
    artist_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    result = await db.execute(
        select(models.Artist).filter(models.Artist.id == artist_id)
    )
    artist = result.scalar_one_or_none()
    
    if artist is None:
        raise HTTPException(status_code=404, detail="Исполнитель не найден")
    
    await db.delete(artist)
    await db.commit()
    
    return {"message": f"Исполнитель {artist.name} удален"}

@app.put(
    "/admin/users/{user_id}/promote",
    summary="Дать права администратора",
    description="Делает пользователя администратором. Доступно только администраторам."
)
async def promote_to_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Пользователь уже администратор")
    
    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    
    return {"message": f"{user.username} теперь администратор"}

@app.put(
    "/admin/users/{user_id}/demote",
    summary="Снять права администратора",
    description="Убирает права администратора у пользователя. Доступно только администраторам."
)
async def demote_from_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if not user.is_admin:
        raise HTTPException(status_code=400, detail="Пользователь и так не администратор")
    
    user.is_admin = False
    await db.commit()
    await db.refresh(user)
    
    return {"message": f"У {user.username} забрали права администратора"}
