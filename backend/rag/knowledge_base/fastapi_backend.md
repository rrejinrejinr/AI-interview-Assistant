# FastAPI & Modern Backend Architecture

## Asynchronous Request Handling & ASGI
FastAPI is built on Starlette and Pydantic, running on ASGI (Asynchronous Server Gateway Interface) web servers like Uvicorn.
Async route handlers (`async def`) execute cooperatively on the Python event loop, allowing thousands of concurrent idle I/O connections.

## Dependency Injection & Security
FastAPI provides a powerful `Depends()` dependency injection mechanism used for:
- Database session lifecycle (yielding a SQLAlchemy session and closing it in `finally`).
- Authentication verification (extracting and decoding JWT bearer tokens via `OAuth2PasswordBearer`).
- Request validation and reusable service clients.

## Connection Pooling & Database Reliability
When communicating with relational databases (PostgreSQL, MySQL), always configure connection pooling (e.g., SQLAlchemy `pool_size`, `max_overflow`, `pool_pre_ping=True`) to prevent connection exhaustion under heavy load.
