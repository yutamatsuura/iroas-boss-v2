"""
IROAS BOSS V2 Backend API Server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api.v1 import members, organization  # organization_new は一時無効化
# 基本モデルのみインポート
from app.models.member import Member

print("Starting with basic models only")

app = FastAPI(
    title="IROAS BOSS V2 API",
    version="2.0.0",
    description="MLM Member Management System Backend API"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発中は全許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ヘルスチェックエンドポイント
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "IROAS BOSS V2",
        "version": "2.0.0"
    }

# APIルーター登録
app.include_router(members.router, prefix="/api/v1")
app.include_router(organization.router, prefix="/api/v1/organization", tags=["organization"])
# app.include_router(organization_new.router, prefix="/api/v1/organization-db", tags=["organization-db"])  # 一時無効化

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)