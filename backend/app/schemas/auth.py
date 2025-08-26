# IROAS BOSS V2 - 認証スキーマ
# Phase 21対応・MLMビジネス要件準拠

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, validator, Field
from enum import Enum

from app.models.user import UserRole, UserStatus

# ===================
# 基本認証スキーマ
# ===================

class LoginRequest(BaseModel):
    """ログインリクエスト"""
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")
    password: str = Field(..., min_length=8, max_length=100, description="パスワード")
    remember_me: bool = Field(default=False, description="ログイン状態保持")
    mfa_code: Optional[str] = Field(None, pattern=r"^\d{6}$", description="MFAコード（6桁）")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('ユーザー名は英数字、ハイフン、アンダースコアのみ使用可能です')
        return v.lower()

class LoginResponse(BaseModel):
    """ログインレスポンス"""
    access_token: str = Field(..., description="アクセストークン")
    refresh_token: str = Field(..., description="リフレッシュトークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
    expires_in: int = Field(..., description="有効期限（秒）")
    user: "UserSummary" = Field(..., description="ユーザー情報")
    permissions: List[str] = Field(default=[], description="ユーザー権限一覧")
    mfa_required: bool = Field(default=False, description="MFA必須フラグ")

class RefreshTokenRequest(BaseModel):
    """リフレッシュトークンリクエスト"""
    refresh_token: str = Field(..., description="リフレッシュトークン")

class LogoutRequest(BaseModel):
    """ログアウトリクエスト"""
    all_devices: bool = Field(default=False, description="全デバイスからログアウト")

# ===================
# ユーザー管理スキーマ
# ===================

class UserBase(BaseModel):
    """ユーザー基本情報"""
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")
    email: EmailStr = Field(..., description="メールアドレス")
    full_name: Optional[str] = Field(None, max_length=100, description="フルネーム")
    display_name: Optional[str] = Field(None, max_length=50, description="表示名")
    phone: Optional[str] = Field(None, pattern=r"^[0-9\-+().\s]+$", description="電話番号")
    role: UserRole = Field(default=UserRole.VIEWER, description="ユーザー役割")

class UserCreate(UserBase):
    """ユーザー作成"""
    password: str = Field(..., min_length=8, max_length=100, description="パスワード")
    confirm_password: str = Field(..., description="パスワード確認")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('パスワードが一致しません')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        # パスワード強度チェック
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        if not any(c.isupper() for c in v):
            raise ValueError('パスワードには大文字を含める必要があります')
        if not any(c.islower() for c in v):
            raise ValueError('パスワードには小文字を含める必要があります')
        if not any(c.isdigit() for c in v):
            raise ValueError('パスワードには数字を含める必要があります')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('パスワードには記号を含める必要があります')
        return v

class UserUpdate(BaseModel):
    """ユーザー更新"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, pattern=r"^[0-9\-+().\s]+$")
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None

class UserPasswordChange(BaseModel):
    """パスワード変更"""
    current_password: str = Field(..., description="現在のパスワード")
    new_password: str = Field(..., min_length=8, max_length=100, description="新しいパスワード")
    confirm_password: str = Field(..., description="パスワード確認")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('パスワードが一致しません')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        # UserCreateと同じバリデーション
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        if not any(c.isupper() for c in v):
            raise ValueError('パスワードには大文字を含める必要があります')
        if not any(c.islower() for c in v):
            raise ValueError('パスワードには小文字を含める必要があります')
        if not any(c.isdigit() for c in v):
            raise ValueError('パスワードには数字を含める必要があります')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('パスワードには記号を含める必要があります')
        return v

class UserSummary(BaseModel):
    """ユーザー要約情報"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    display_name: Optional[str]
    role: UserRole
    status: UserStatus
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserDetail(UserSummary):
    """ユーザー詳細情報"""
    phone: Optional[str]
    is_superuser: bool
    login_attempts: int
    locked_at: Optional[datetime]
    last_login_ip: Optional[str]
    updated_at: datetime
    permissions: List[str] = []

# ===================
# MFA関連スキーマ
# ===================

class MFASetupRequest(BaseModel):
    """MFA設定リクエスト"""
    enable: bool = Field(..., description="MFA有効化フラグ")
    verification_code: Optional[str] = Field(None, pattern=r"^\d{6}$", description="認証コード")

class MFASetupResponse(BaseModel):
    """MFA設定レスポンス"""
    qr_code: str = Field(..., description="QRコードURL")
    secret_key: str = Field(..., description="秘密鍵")
    backup_codes: List[str] = Field(..., description="バックアップコード")
    enabled: bool = Field(..., description="MFA有効状態")

class MFAVerifyRequest(BaseModel):
    """MFA認証リクエスト"""
    code: str = Field(..., pattern=r"^\d{6}$", description="認証コード")
    backup_code: Optional[str] = Field(None, description="バックアップコード")

# ===================
# セッション管理スキーマ
# ===================

class SessionInfo(BaseModel):
    """セッション情報"""
    id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[Dict[str, Any]]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: datetime
    is_current: bool = Field(default=False, description="現在のセッション")
    
    class Config:
        from_attributes = True

class SessionListResponse(BaseModel):
    """セッション一覧レスポンス"""
    sessions: List[SessionInfo]
    total: int

class SessionRevokeRequest(BaseModel):
    """セッション無効化リクエスト"""
    session_ids: List[int] = Field(..., description="無効化するセッションID一覧")
    reason: Optional[str] = Field(None, max_length=100, description="無効化理由")

# ===================
# アクセスログスキーマ
# ===================

class AccessLogSummary(BaseModel):
    """アクセスログ要約"""
    id: int
    action: str
    ip_address: Optional[str]
    success: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AccessLogDetail(AccessLogSummary):
    """アクセスログ詳細"""
    user_agent: Optional[str]
    path: Optional[str]
    method: Optional[str]
    status_code: Optional[int]
    error_message: Optional[str]

class AccessLogListResponse(BaseModel):
    """アクセスログ一覧レスポンス"""
    logs: List[AccessLogSummary]
    total: int
    page: int
    limit: int

# ===================
# 権限管理スキーマ
# ===================

class PermissionBase(BaseModel):
    """権限基本情報"""
    permission_name: str = Field(..., max_length=100)
    permission_code: str = Field(..., max_length=50)
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    resource: Optional[str] = Field(None, max_length=50)
    action: Optional[str] = Field(None, max_length=50)

class PermissionSummary(PermissionBase):
    """権限要約情報"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class RolePermissionsResponse(BaseModel):
    """役割権限レスポンス"""
    role: UserRole
    permissions: List[PermissionSummary]
    total: int

# ===================
# エラーレスポンススキーマ
# ===================

class AuthErrorDetail(BaseModel):
    """認証エラー詳細"""
    error_code: str = Field(..., description="エラーコード")
    error_message: str = Field(..., description="エラーメッセージ")
    retry_after: Optional[int] = Field(None, description="再試行可能まで秒数")
    locked_until: Optional[datetime] = Field(None, description="ロック期限")

class AuthErrorResponse(BaseModel):
    """認証エラーレスポンス"""
    success: bool = Field(default=False)
    error: AuthErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Forward reference resolution
UserSummary.update_forward_refs()