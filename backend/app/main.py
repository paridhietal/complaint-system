from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.routers import complaints, chat

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AIVOA Customer Complaint Management System",
    description="AI-powered complaint intake for pharmaceutical QMS",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relaxed for local dev/demo purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints.router)
app.include_router(chat.router)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    # Surfaces setup errors (e.g. missing GROQ_API_KEY) as a readable JSON
    # message instead of a generic 500, since this is the #1 thing that will
    # go wrong the first time you run this.
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/")
def root():
    return {"status": "ok", "service": "AIVOA Complaint Management API"}
