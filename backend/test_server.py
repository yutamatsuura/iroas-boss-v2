"""
簡易テストサーバー - 動作確認用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="IROAS BOSS V2 Test Server")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    uvicorn.run(app, host="0.0.0.0", port=8000)