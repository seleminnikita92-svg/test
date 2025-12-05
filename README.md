# Personal Music Collection API

## Описание проекта

REST API для управления личной музыкальной коллекцией. Позволяет создавать и управлять исполнителями, альбомами и плейлистами.

## Технологии

- **Python 3.10+**
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL** - основная база данных
- **asyncpg** - асинхронный драйвер PostgreSQL
- **JWT** - аутентификация через токены
- **bcrypt** - хеширование паролей

## Функциональность

### Основные возможности:
- Регистрация и аутентификация пользователей
- CRUD операции для исполнителей (Artists)
- Управление альбомами (Albums)
- Создание и управление плейлистами (Playlists)
- Админ-панель для управления пользователями и контентом

### Эндпоинты:

**Аутентификация:**
- `POST /register` - регистрация
- `POST /login` - вход и получение JWT токена

**Исполнители (полный CRUD):**
- `POST /artists` - создать исполнителя
- `GET /artists` - список своих исполнителей
- `GET /artists/{artist_id}` - получить по ID
- `PUT /artists/{artist_id}` - обновить
- `DELETE /artists/{artist_id}` - удалить

**Альбомы:**
- `POST /albums` - создать альбом
- `GET /albums` - список своих альбомов
- `DELETE /albums/{album_id}` - удалить

**Плейлисты:**
- `POST /playlists` - создать плейлист
- `GET /playlists` - список своих плейлистов
- `DELETE /playlists/{playlist_id}` - удалить

**Админ-панель:**
- `GET /admin/users` - все пользователи
- `DELETE /admin/users/{user_id}` - удалить пользователя
- `GET /admin/artists` - все исполнители
- `DELETE /admin/artists/{artist_id}` - удалить исполнителя
- `PUT /admin/users/{user_id}/promote` - дать права админа
- `PUT /admin/users/{user_id}/demote` - снять права админа

## Установка и запуск локально

### 1. Клонирование репозитория

```bash
git clone https://github.com/seleminnikita92-svg/test.git
cd test
```

### 2. Создание виртуального окружения

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/music_db
SECRET_KEY=your-secret-key-here-change-in-production
```

**Генерация SECRET_KEY:**

```python
import secrets
print(secrets.token_urlsafe(32))
```

### 5. Создание базы данных PostgreSQL

```bash
# Подключитесь к PostgreSQL
psql -U postgres

# Создайте базу данных
CREATE DATABASE music_db;
```

### 6. Запуск приложения

```bash
uvicorn main:app --reload
```

Приложение будет доступно по адресу: `http://localhost:8000`

Документация API: `http://localhost:8000/docs`

## Деплой на PythonAnywhere

### 1. Регистрация и создание аккаунта

- Зарегистрируйтесь на [www.pythonanywhere.com](https://www.pythonanywhere.com)
- Выберите бесплатный тариф (Beginner)

### 2. Настройка базы данных

- Перейдите в раздел **Databases**
- Создайте PostgreSQL базу данных (доступно на платных тарифах)
- Или используйте MySQL (бесплатно)
- Сохраните credentials

### 3. Загрузка кода

Откройте Bash консоль на PythonAnywhere:

```bash
git clone https://github.com/seleminnikita92-svg/test.git
cd test
```

### 4. Создание виртуального окружения

```bash
mkvirtualenv --python=/usr/bin/python3.10 music-api-env
pip install -r requirements.txt
```

### 5. Настройка переменных окружения

Создайте `.env` файл:

```bash
nano .env
```

Вставьте:

```env
DATABASE_URL=postgresql+asyncpg://username:password@host:port/dbname
SECRET_KEY=your-production-secret-key
```

### 6. Настройка Web App

- Перейдите в раздел **Web**
- Создайте новое приложение: **Manual configuration**
- Выберите **Python 3.10**

**Настройка WSGI файла:**

Откройте WSGI configuration file и замените содержимое:

```python
import sys
import os
from pathlib import Path

# Путь к проекту
project_home = '/home/yourusername/test'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Загрузка переменных окружения
from dotenv import load_dotenv
env_path = Path(project_home) / '.env'
load_dotenv(dotenv_path=env_path)

# Импорт приложения FastAPI
from main import app as application
```

**Настройка виртуального окружения:**

- В разделе **Virtualenv** укажите путь:
  ```
  /home/yourusername/.virtualenvs/music-api-env
  ```

### 7. Перезапуск приложения

Нажмите кнопку **Reload** в разделе Web

Ваше API будет доступно по адресу: `https://yourusername.pythonanywhere.com`

## Использование API

### 1. Регистрация первого админа

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepassword123"
  }'
```

**Важно:** Первый пользователь с username="admin" автоматически получает права администратора.

### 2. Получение токена

```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=securepassword123"
```

Ответ:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Создание исполнителя

```bash
curl -X POST "http://localhost:8000/artists" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "The Beatles",
    "genre": "Rock"
  }'
```

### 4. Получение списка исполнителей

```bash
curl -X GET "http://localhost:8000/artists" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Структура проекта

```
music_api/
│
├── main.py          # FastAPI приложение и все роуты
├── models.py        # SQLAlchemy ORM модели
├── schemas.py       # Pydantic схемы валидации
├── database.py      # Настройка асинхронного подключения к БД
├── security.py      # JWT аутентификация и bcrypt
│
├── requirements.txt # Зависимости Python
├── .env            # Переменные окружения (не в git)
├── .gitignore      # Игнорируемые файлы
└── README.md       # Документация
```

## Обработка ошибок

API возвращает стандартные HTTP коды ответов:

- **200** - успешный запрос
- **201** - ресурс создан
- **400** - ошибка валидации данных
- **401** - не авторизован
- **403** - доступ запрещен (недостаточно прав)
- **404** - ресурс не найден
- **422** - ошибка обработки данных (Pydantic validation)

## Автор

Проект разработан для демонстрации навыков создания REST API с использованием FastAPI и современных практик разработки.

## Лицензия

MIT License
