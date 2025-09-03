"""
簡易テストサーバー - 動作確認用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# パスを追加してアプリモジュールをインポート可能にする
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="IROAS BOSS V2 Test Server")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターを登録
try:
    from app.api.v1.organization import router as organization_router
    from app.api.v1.members import router as members_router
    
    app.include_router(organization_router, prefix="/api/v1/organization")
    app.include_router(members_router, prefix="/api/v1")
    print("✅ APIルーター登録完了")
except Exception as e:
    print(f"❌ APIルーター登録エラー: {e}")

@app.get("/")
async def root():
    return {"message": "IROAS BOSS V2 API is running", "status": "ok"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "IROAS BOSS V2",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)