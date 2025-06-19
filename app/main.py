from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, entries, stats
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Reflective Journal API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(entries.router, prefix="/api/entries", tags=["entries"])
app.include_router(stats.router, prefix="/api", tags=["stats"])

@app.get("/")
def read_root():
    return {"message": "Reflective Journal API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"} 