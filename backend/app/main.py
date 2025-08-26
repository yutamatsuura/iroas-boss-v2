# IROAS BOSS V2 - FastAPIメインアプリケーション
# Phase 21対応・認証セキュリティ統合

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.endpoints import auth, security
from app.database import Base, engine, SessionLocal
from app.middleware.rate_limit_middleware import RateLimitMiddleware, SecurityHeaders
from app.services.permission_service import permission_service

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# セキュリティログ専用設定
security_logger = logging.getLogger("security")
security_handler = logging.FileHandler("security.log")
security_handler.setFormatter(
    logging.Formatter('%(asctime)s - SECURITY - %(levelname)s - %(message)s')
)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)

# アプリケーション初期化
@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時処理
    logger.info("IROAS BOSS V2 アプリケーションを開始しています...")
    
    # データベーステーブル作成
    Base.metadata.create_all(bind=engine)
    logger.info("データベーステーブルを初期化しました")
    
    # 権限システム初期化
    db = SessionLocal()
    try:
        await permission_service.initialize_permissions(db)
        logger.info("権限システムを初期化しました")
    except Exception as e:
        logger.error(f"権限システム初期化エラー: {e}")
    finally:
        db.close()
    
    logger.info("IROAS BOSS V2 アプリケーションが正常に開始されました")
    
    yield
    
    # 終了時処理
    logger.info("IROAS BOSS V2 アプリケーションを終了します...")

# FastAPIアプリケーション作成
app = FastAPI(
    title="IROAS BOSS V2 API",
    description="Phase 21対応・MLMビジネス統合管理システム",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS設定（開発環境用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# レート制限ミドルウェア追加
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# セキュリティヘッダーミドルウェア
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response = SecurityHeaders.add_security_headers(response, request)
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 監査ログミドルウェア
class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        
        # リクエスト情報記録
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        response = await call_next(request)
        
        # レスポンス時間計算
        process_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 監査ログ記録
        if request.url.path.startswith("/api/v1/auth") or response.status_code >= 400:
            logger.info(
                f"API Access - IP: {client_ip}, Path: {request.url.path}, "
                f"Method: {request.method}, Status: {response.status_code}, "
                f"Process Time: {process_time:.3f}s, User-Agent: {user_agent}"
            )
        
        # セキュリティ関連ログ
        if response.status_code in [401, 403, 429]:
            security_logger.warning(
                f"Security Event - IP: {client_ip}, Path: {request.url.path}, "
                f"Status: {response.status_code}, User-Agent: {user_agent}"
            )
        
        # レスポンスヘッダーにプロセス時間追加
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

app.add_middleware(AuditLoggingMiddleware)

# ルーター登録
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
app.include_router(security.router, prefix="/api/v1/security", tags=["セキュリティ"])

# ルートエンドポイント
@app.get("/")
async def root():
    """APIルートエンドポイント"""
    return {
        "message": "IROAS BOSS V2 API",
        "version": "2.0.0",
        "phase": "21 - 認証セキュリティ統合",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "21"
    }

# セキュリティ情報エンドポイント
@app.get("/security/status")
async def security_status():
    """セキュリティステータス"""
    return {
        "security_features": [
            "JWT Authentication",
            "Multi-Factor Authentication",
            "Role-Based Access Control", 
            "Rate Limiting",
            "Request Auditing",
            "Security Headers",
            "IP-based Analysis",
            "Session Management"
        ],
        "compliance": "MLM Business Requirements",
        "phase": "21",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("IROAS BOSS V2 開発サーバーを開始します...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )