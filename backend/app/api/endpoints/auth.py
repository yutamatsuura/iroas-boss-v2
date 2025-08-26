# IROAS BOSS V2 - 認証API エンドポイント
# Phase 21対応・MLMビジネス要件準拠

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import security
from app.services.auth_service import auth_service
from app.services.permission_service import permission_service
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest, LoginResponse, RefreshTokenRequest, LogoutRequest,
    UserCreate, UserUpdate, UserSummary, UserDetail, UserPasswordChange,
    MFASetupRequest, MFASetupResponse, MFAVerifyRequest,
    SessionListResponse, SessionRevokeRequest,
    AccessLogListResponse, RolePermissionsResponse,
    AuthErrorResponse
)

# Router設定
router = APIRouter(prefix="/api/v1/auth", tags=["認証"])
security_scheme = HTTPBearer()

# ===================
# 依存関数
# ===================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """現在のログインユーザーを取得"""
    
    token = credentials.credentials
    
    try:
        payload = security.verify_token(token, "access")
        user_id = int(payload.get("sub"))
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンです"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザーが見つかりません"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="アカウントが無効です"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました"
        )

async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """管理者権限を持つ現在のユーザーを取得"""
    
    if not await permission_service.check_user_permission(current_user.id, "user.manage", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    
    return current_user

def get_client_ip(request: Request) -> str:
    """クライアントIPアドレスを取得"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"

# ===================
# 認証エンドポイント
# ===================

@router.post("/login", response_model=LoginResponse, summary="ログイン")
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ユーザーログイン
    
    MLMビジネス要件に準拠した認証処理:
    - アカウント状態チェック
    - ログイン試行回数制限
    - MFA対応
    - セッション管理
    - アクセスログ記録
    """
    
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    try:
        return await auth_service.authenticate_user(
            login_data=login_data,
            ip_address=ip_address,
            user_agent=user_agent,
            db=db
        )
    except HTTPException as e:
        if e.status_code == status.HTTP_202_ACCEPTED:
            # MFA必須の場合
            raise e
        
        # その他のエラー
        raise e

@router.post("/refresh", response_model=LoginResponse, summary="トークンリフレッシュ")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    リフレッシュトークンを使用してアクセストークンを更新
    """
    
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    return await auth_service.refresh_token(
        refresh_token=refresh_data.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        db=db
    )

@router.post("/logout", summary="ログアウト")
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """
    ユーザーログアウト
    """
    
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    await auth_service.logout_user(
        user_id=current_user.id,
        session_token=credentials.credentials,
        all_devices=logout_data.all_devices,
        ip_address=ip_address,
        user_agent=user_agent,
        db=db
    )
    
    return {"message": "ログアウトしました"}

@router.get("/me", response_model=UserDetail, summary="現在のユーザー情報取得")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    現在ログイン中のユーザー情報を取得
    """
    
    # 権限一覧を取得
    permissions = await auth_service.get_user_permissions(current_user.id, db)
    
    user_detail = UserDetail.from_orm(current_user)
    user_detail.permissions = permissions
    
    return user_detail

@router.put("/me", response_model=UserSummary, summary="現在のユーザー情報更新")
async def update_current_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    現在ログイン中のユーザー情報を更新
    """
    
    # ロール・ステータス・管理者権限の変更を制限
    restricted_update = user_update.copy()
    restricted_update.role = None
    restricted_update.status = None
    restricted_update.is_active = None
    
    return await auth_service.update_user(
        user_id=current_user.id,
        user_data=restricted_update,
        updated_by=current_user.id,
        db=db
    )

@router.post("/change-password", summary="パスワード変更")
async def change_password(
    password_data: UserPasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    現在のユーザーのパスワードを変更
    """
    
    # 現在のパスワードを確認
    if not security.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスワードが正しくありません"
        )
    
    # パスワード更新
    current_user.hashed_password = security.hash_password(password_data.new_password)
    db.commit()
    
    # アクセスログ記録
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    await auth_service._log_access(
        current_user.id, "password_changed", ip_address, user_agent, True, "パスワード変更", db
    )
    
    return {"message": "パスワードを変更しました"}

# ===================
# MFAエンドポイント
# ===================

@router.post("/mfa/setup", response_model=MFASetupResponse, summary="MFA設定")
async def setup_mfa(
    mfa_request: MFASetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    多要素認証（MFA）の設定・解除
    """
    
    return await auth_service.setup_mfa(
        user_id=current_user.id,
        mfa_request=mfa_request,
        db=db
    )

@router.post("/mfa/verify", summary="MFA認証")
async def verify_mfa(
    verify_request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    MFAコードの検証
    """
    
    # MFAが有効でない場合はエラー
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAが有効になっていません"
        )
    
    # コード検証
    is_valid = False
    
    if verify_request.code:
        is_valid = security.verify_mfa_code(current_user.mfa_secret, verify_request.code)
    elif verify_request.backup_code:
        # バックアップコード検証の実装（auth_serviceに移譲）
        pass
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="認証コードが正しくありません"
        )
    
    return {"message": "MFA認証に成功しました"}

# ===================
# セッション管理エンドポイント
# ===================

@router.get("/sessions", response_model=SessionListResponse, summary="セッション一覧")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    現在のユーザーのセッション一覧を取得
    """
    
    sessions = await auth_service.get_user_sessions(current_user.id, db)
    
    return SessionListResponse(
        sessions=sessions,
        total=len(sessions)
    )

@router.post("/sessions/revoke", summary="セッション無効化")
async def revoke_sessions(
    revoke_request: SessionRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    指定されたセッションを無効化
    """
    
    await auth_service.revoke_sessions(
        user_id=current_user.id,
        session_ids=revoke_request.session_ids,
        reason=revoke_request.reason or "ユーザーによる無効化",
        db=db
    )
    
    return {"message": "セッションを無効化しました"}

# ===================
# 管理者向けエンドポイント
# ===================

@router.post("/users", response_model=UserSummary, summary="ユーザー作成")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    新規ユーザー作成（管理者権限必要）
    """
    
    return await auth_service.create_user(
        user_data=user_data,
        created_by=current_user.id,
        db=db
    )

@router.put("/users/{user_id}", response_model=UserSummary, summary="ユーザー更新")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    ユーザー情報更新（管理者権限必要）
    """
    
    return await auth_service.update_user(
        user_id=user_id,
        user_data=user_update,
        updated_by=current_user.id,
        db=db
    )

@router.get("/users/{user_id}", response_model=UserDetail, summary="ユーザー詳細取得")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    指定ユーザーの詳細情報取得（管理者権限必要）
    """
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    permissions = await auth_service.get_user_permissions(user.id, db)
    
    user_detail = UserDetail.from_orm(user)
    user_detail.permissions = permissions
    
    return user_detail

# ===================
# 権限管理エンドポイント
# ===================

@router.get("/permissions/roles/{role}", response_model=RolePermissionsResponse, summary="ロール権限一覧")
async def get_role_permissions(
    role: UserRole,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    指定されたロールの権限一覧を取得
    """
    
    return await permission_service.get_role_permissions(role, db)

@router.post("/permissions/initialize", summary="権限初期化")
async def initialize_permissions(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    MLMビジネス要件に基づく権限の初期化
    """
    
    # スーパーユーザーのみ実行可能
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="スーパーユーザー権限が必要です"
        )
    
    await permission_service.initialize_permissions(db)
    
    return {"message": "権限の初期化が完了しました"}

# ===================
# アクセスログエンドポイント
# ===================

@router.get("/logs/access", response_model=AccessLogListResponse, summary="アクセスログ一覧")
async def get_access_logs(
    page: int = 1,
    limit: int = 50,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    success: Optional[bool] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    アクセスログ一覧を取得（管理者権限必要）
    """
    
    from app.models.user import UserAccessLog
    from sqlalchemy import and_, desc
    
    # クエリ構築
    query = db.query(UserAccessLog)
    
    conditions = []
    if user_id:
        conditions.append(UserAccessLog.user_id == user_id)
    if action:
        conditions.append(UserAccessLog.action.ilike(f"%{action}%"))
    if success is not None:
        conditions.append(UserAccessLog.success == success)
    
    if conditions:
        query = query.filter(and_(*conditions))
    
    # ページネーション
    total = query.count()
    logs = query.order_by(desc(UserAccessLog.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    from app.schemas.auth import AccessLogSummary
    return AccessLogListResponse(
        logs=[AccessLogSummary.from_orm(log) for log in logs],
        total=total,
        page=page,
        limit=limit
    )