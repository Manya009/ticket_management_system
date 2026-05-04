from fastapi import FastAPI
from .database import engine, Base
from contextlib import asynccontextmanager
from .auth_routes import auth_router
from .ticket_routes import ticket_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine, checkfirst=True) #create tables if they don't exist
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(auth_router)
app.include_router(ticket_router)