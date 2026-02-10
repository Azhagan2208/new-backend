from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers.auth import router as auth

from .routers.rooms import router as room
from .routers.questions import router as question
from .routers.votes import router as vote

# creating the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Questup Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth)
app.include_router(room)
app.include_router(question)
app.include_router(vote)


@app.get("/")
def home():
    return {"Questup": "Api is running successfully!!!"}


@app.get("/health")
def health():
    return {"status": "Running Sucesfully!!!"}
