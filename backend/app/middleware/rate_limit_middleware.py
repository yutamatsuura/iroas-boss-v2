# IROAS BOSS V2 - レート制限ミドルウェア
# Phase 21対応・認証セキュリティ強化

import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    レート制限ミドルウェア
    ブルートフォース攻撃・DDoS攻撃対策
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 期間内の最大リクエスト数
        self.period = period  # 期間（秒）
        self.requests: Dict[str, List[float]] = defaultdict(list)
        
        # エンドポイント別制限設定
        self.endpoint_limits = {
            '/api/v1/auth/login': {'calls': 5, 'period': 300},  # ログイン: 5回/5分
            '/api/v1/auth/refresh': {'calls': 20, 'period': 60},  # リフレッシュ: 20回/分
            '/api/v1/auth/change-password': {'calls': 3, 'period': 900},  # パスワード変更: 3回/15分
            '/api/v1/auth/mfa/setup': {'calls': 3, 'period': 300},  # MFA設定: 3回/5分
            '/api/v1/auth/mfa/verify': {'calls': 10, 'period': 300},  # MFA認証: 10回/5分
        }
        
        # グローバル制限除外パス
        self.whitelist_paths = [
            '/api/v1/auth/me',  # ユーザー情報取得
            '/api/settings',  # システム設定
            '/docs',  # API文書
            '/openapi.json',
        ]

    async def dispatch(self, request: Request, call_next):
        # IPアドレス取得
        client_ip = self._get_client_ip(request)
        
        # パス取得
        path = request.url.path
        
        # ホワイトリストチェック
        if any(path.startswith(wp) for wp in self.whitelist_paths):
            return await call_next(request)
        
        # 制限確認
        if not self._is_allowed(client_ip, path):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "リクエスト制限に達しました。しばらく待ってから再試行してください。",
                    "retry_after": self._get_retry_after(client_ip, path)
                }
            )
        
        # リクエスト記録
        self._record_request(client_ip, path)
        
        response = await call_next(request)
        
        # レスポンスヘッダーに制限情報追加
        remaining = self._get_remaining_requests(client_ip, path)
        response.headers["X-RateLimit-Limit"] = str(self._get_limit(path))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self._get_period(path))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """クライアントIP取得"""
        # X-Forwarded-For ヘッダーをチェック（プロキシ対応）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # X-Real-IP ヘッダーをチェック
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 直接接続の場合
        return request.client.host if request.client else "unknown"
    
    def _get_limit(self, path: str) -> int:
        """パス別制限数取得"""
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]["calls"]
        return self.calls
    
    def _get_period(self, path: str) -> int:
        """パス別制限期間取得"""
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]["period"]
        return self.period
    
    def _is_allowed(self, client_ip: str, path: str) -> bool:
        """リクエスト許可判定"""
        key = f"{client_ip}:{path}"
        now = time.time()
        
        # 古いリクエスト記録を削除
        period = self._get_period(path)
        self.requests[key] = [
            req_time for req_time in self.requests[key] 
            if now - req_time < period
        ]
        
        # 制限チェック
        limit = self._get_limit(path)
        return len(self.requests[key]) < limit
    
    def _record_request(self, client_ip: str, path: str):
        """リクエスト記録"""
        key = f"{client_ip}:{path}"
        self.requests[key].append(time.time())
    
    def _get_remaining_requests(self, client_ip: str, path: str) -> int:
        """残りリクエスト数取得"""
        key = f"{client_ip}:{path}"
        limit = self._get_limit(path)
        used = len(self.requests[key])
        return max(0, limit - used)
    
    def _get_retry_after(self, client_ip: str, path: str) -> int:
        """再試行可能時間取得（秒）"""
        key = f"{client_ip}:{path}"
        if not self.requests[key]:
            return 0
        
        period = self._get_period(path)
        oldest_request = min(self.requests[key])
        return max(0, int(period - (time.time() - oldest_request)))

class SecurityHeaders:
    """
    セキュリティヘッダーミドルウェア
    XSS・CSRF・クリックジャッキング対策
    """
    
    @staticmethod
    def add_security_headers(response, request: Request = None):
        """セキュリティヘッダー追加"""
        
        # XSS Protection
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy (厳格な設定)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HTTPS強制（本番環境用）
        if request and request.headers.get("X-Forwarded-Proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # キャッシュ制御（認証関連）
        if request and "/api/v1/auth" in request.url.path:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

# セキュリティログ記録
class SecurityLogger:
    """セキュリティイベントログ"""
    
    @staticmethod
    def log_rate_limit_exceeded(client_ip: str, path: str, user_agent: str = None):
        """レート制限超過ログ"""
        import logging
        
        logger = logging.getLogger("security")
        logger.warning(
            f"Rate limit exceeded - IP: {client_ip}, Path: {path}, User-Agent: {user_agent}"
        )
    
    @staticmethod
    def log_suspicious_activity(client_ip: str, activity: str, details: str = None):
        """疑わしいアクティビティログ"""
        import logging
        
        logger = logging.getLogger("security")
        logger.warning(
            f"Suspicious activity - IP: {client_ip}, Activity: {activity}, Details: {details}"
        )
    
    @staticmethod
    def log_authentication_failure(client_ip: str, username: str, reason: str):
        """認証失敗ログ"""
        import logging
        
        logger = logging.getLogger("security")
        logger.warning(
            f"Authentication failed - IP: {client_ip}, Username: {username}, Reason: {reason}"
        )