# IROAS BOSS V2 - セキュリティ・認証コア機能
# Phase 21対応・MLMビジネス要件準拠

import os
import secrets
import hashlib
import pyotp
import qrcode
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from io import BytesIO
from base64 import b64encode, b64decode

import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserSession, UserAccessLog, UserRole, UserStatus
from app.schemas.auth import LoginRequest, LoginResponse, UserSummary

# ===================
# セキュリティ設定
# ===================

# パスワードハッシュ化設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# セキュリティ設定
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
SESSION_CLEANUP_DAYS = 30

class SecurityManager:
    """セキュリティ管理クラス"""
    
    def __init__(self):
        self.pwd_context = pwd_context
    
    # ===================
    # パスワード管理
    # ===================
    
    def hash_password(self, password: str) -> str:
        """パスワードをハッシュ化"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """パスワードを検証"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_secure_password(self, length: int = 16) -> str:
        """安全なパスワードを生成"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # ===================
    # JWT トークン管理
    # ===================
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """アクセストークンを作成"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """リフレッシュトークンを作成"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # JWT ID
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """トークンを検証"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="無効なトークンタイプ"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="トークンが期限切れです"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンです"
            )
    
    # ===================
    # MFA（多要素認証）管理
    # ===================
    
    def generate_mfa_secret(self) -> str:
        """MFA秘密鍵を生成"""
        return pyotp.random_base32()
    
    def generate_mfa_qr_code(self, username: str, secret: str) -> str:
        """MFA用QRコードを生成"""
        totp_auth = pyotp.totp.TOTP(secret)
        provisioning_uri = totp_auth.provisioning_uri(
            name=username,
            issuer_name="IROAS BOSS V2"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Base64エンコード
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_mfa_code(self, secret: str, code: str) -> bool:
        """MFAコードを検証"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """バックアップコードを生成"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes
    
    def hash_backup_codes(self, codes: List[str]) -> List[str]:
        """バックアップコードをハッシュ化"""
        return [hashlib.sha256(code.encode()).hexdigest() for code in codes]
    
    def verify_backup_code(self, hashed_codes: List[str], code: str) -> Tuple[bool, List[str]]:
        """バックアップコードを検証"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        if code_hash in hashed_codes:
            # 使用済みコードを削除
            updated_codes = [c for c in hashed_codes if c != code_hash]
            return True, updated_codes
        
        return False, hashed_codes
    
    # ===================
    # セッション管理
    # ===================
    
    def generate_session_token(self) -> str:
        """セッショントークンを生成"""
        return secrets.token_urlsafe(32)
    
    def extract_device_info(self, user_agent: str) -> Dict[str, Any]:
        """ユーザーエージェントからデバイス情報を抽出"""
        # 簡易的なデバイス情報抽出（実際はより詳細な解析が必要）
        device_info = {
            "user_agent": user_agent,
            "browser": "unknown",
            "os": "unknown",
            "device": "unknown"
        }
        
        if user_agent:
            user_agent_lower = user_agent.lower()
            
            # ブラウザ判定
            if "chrome" in user_agent_lower:
                device_info["browser"] = "Chrome"
            elif "firefox" in user_agent_lower:
                device_info["browser"] = "Firefox"
            elif "safari" in user_agent_lower:
                device_info["browser"] = "Safari"
            elif "edge" in user_agent_lower:
                device_info["browser"] = "Edge"
            
            # OS判定
            if "windows" in user_agent_lower:
                device_info["os"] = "Windows"
            elif "mac" in user_agent_lower:
                device_info["os"] = "macOS"
            elif "linux" in user_agent_lower:
                device_info["os"] = "Linux"
            elif "android" in user_agent_lower:
                device_info["os"] = "Android"
            elif "ios" in user_agent_lower:
                device_info["os"] = "iOS"
            
            # デバイス判定
            if any(mobile in user_agent_lower for mobile in ["mobile", "android", "iphone"]):
                device_info["device"] = "Mobile"
            elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
                device_info["device"] = "Tablet"
            else:
                device_info["device"] = "Desktop"
        
        return device_info
    
    # ===================
    # セキュリティ検証
    # ===================
    
    def is_account_locked(self, user: User) -> bool:
        """アカウントがロックされているかチェック"""
        if not user.locked_at:
            return False
        
        lockout_duration = timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        unlock_time = user.locked_at + lockout_duration
        
        return datetime.utcnow() < unlock_time
    
    def should_lock_account(self, user: User) -> bool:
        """アカウントをロックすべきかチェック"""
        return user.login_attempts >= MAX_LOGIN_ATTEMPTS
    
    def reset_login_attempts(self, user: User, db: Session):
        """ログイン試行回数をリセット"""
        user.login_attempts = 0
        user.locked_at = None
        db.commit()
    
    def increment_login_attempts(self, user: User, db: Session):
        """ログイン試行回数を増加"""
        user.login_attempts += 1
        
        if self.should_lock_account(user):
            user.locked_at = datetime.utcnow()
            user.status = UserStatus.LOCKED
        
        db.commit()
    
    def validate_ip_address(self, ip: str) -> bool:
        """IPアドレスを検証（基本的なフォーマットチェック）"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def check_suspicious_activity(self, user: User, ip: str, db: Session) -> bool:
        """疑わしいアクティビティをチェック"""
        # 過去24時間のアクセスログを確認
        recent_logs = db.query(UserAccessLog).filter(
            UserAccessLog.user_id == user.id,
            UserAccessLog.created_at >= datetime.utcnow() - timedelta(days=1)
        ).all()
        
        # 異なるIPからの大量アクセスをチェック
        unique_ips = set(log.ip_address for log in recent_logs if log.ip_address)
        if len(unique_ips) > 5:  # 閾値は調整可能
            return True
        
        # 失敗ログが多いかチェック
        failed_attempts = sum(1 for log in recent_logs if not log.success)
        if failed_attempts > 20:  # 閾値は調整可能
            return True
        
        return False

# グローバルインスタンス
security = SecurityManager()