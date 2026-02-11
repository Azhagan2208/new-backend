from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback

from app.database import Base, engine
from app.routers.auth import router as auth
from app.routers.rooms import router as room
from app.routers.questions import router as question
from app.routers.votes import router as vote

app = FastAPI(title="Questup Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "https://questup-frontend.vercel.app"  # future frontend domain
    ],
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
    return {"status": "Running Successfully!!!"}
