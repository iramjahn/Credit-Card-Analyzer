# backend/api/main.py

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.auth import router as auth_router
from backend.api.routes.cards import router as cards_router
from backend.api.routes.transactions import router as transactions_router
from backend.api.routes.ml import router as ml_router
from backend.api.routes.plaid import router as plaid_router
from backend.api.routes.ingest import router as ingest_router
from backend.database.connection import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="CardOptimizer API",
    description="Credit card rewards optimization platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cards_router)
app.include_router(transactions_router)
app.include_router(ml_router)
app.include_router(plaid_router)
app.include_router(ingest_router)

@app.get("/")
def read_root():
    return {"message": "CardOptimizer API", "version": "1.0.0", "status": "running", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
