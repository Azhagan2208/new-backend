from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers.auth import router as auth

from app.routers.rooms import router as room
from app.routers.questions import router as question
from app.routers.votes import router as vote

app = FastAPI(title="Questup Backend")


@app.on_event("startup")
def on_startup():
    # creating the database tables only when app starts
    try:
        if "dummy" not in str(engine.url):
            Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Table creation failed: {e}")


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
