from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.routers import users, items, websocket
from app.exceptions import CustomException
from app.database import database, init_db

# Lifespan context manager for database connections
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to the database
    await database.connect()
    await init_db()
    yield
    # Shutdown: Disconnect from the database
    await database.disconnect()

# Create FastAPI application
app = FastAPI(
    title="FastAPI Demo",
    description="A complete FastAPI demo application",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add processing time middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Add exception handler
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )

# Include routers
app.include_router(users.router)
app.include_router(items.router)
app.include_router(websocket.router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Demo"}