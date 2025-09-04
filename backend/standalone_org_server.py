#!/usr/bin/env python3
"""組織図API単独サーバー"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sys
import os

# パスを追加してアプリケーションのインポートを可能にする
sys.path.append('/Users/lennon/projects/iroas-boss-v2/backend')

from app.api.v1.organization import router as org_router

# FastAPIアプリケーション
app = FastAPI(title="組織図API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 組織図ルーター追加
app.include_router(org_router, prefix="/api/v1/organization", tags=["組織図"])

@app.get("/")
def root():
    return {"message": "組織図API単独サーバー"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)