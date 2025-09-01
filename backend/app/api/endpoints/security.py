# IROAS BOSS V2 - セキュリティAPIエンドポイント
# Phase 21対応・エンタープライズセキュリティ統合

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserSession, UserAccessLog
from app.api.deps import get_current_user
from app.services.security_service import security_service
from app.services.audit_service import mlm_audit_service, AuditEvent, AuditEventType
from app.services.notification_service import security_notification_service
from app.services.auth_service import auth_service
from pydantic import BaseModel

router = APIRouter()

# ===================
# レスポンスモデル
# ===================

class SecurityMetrics(BaseModel):
    password_strength: int
    mfa_enabled: bool
    active_sessions: int
    last_password_change: Optional[str]
    recent_failed_logins: int
    trusted_devices: int

class SecurityRecommendation(BaseModel):
    priority: str
    category: str
    title: str
    description: str
    action_url: str

class SessionInfo(BaseModel):
    id: str
    device_info: Dict[str, Any]
    ip_address: str
    is_current: bool
    last_used_at: str
    created_at: str
    location: Optional[Dict[str, str]] = None

class SecurityAlert(BaseModel):
    id: str
    type: str
    level: str
    title: str
    description: str
    timestamp: str
    acknowledged: bool
    details: Optional[Dict[str, Any]] = None

class AccessLogEntry(BaseModel):
    id: str
    action: str
    ip_address: str
    user_agent: str
    success: bool
    timestamp: str
    location: Optional[str] = None
    risk_level: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PasswordStrengthRequest(BaseModel):
    password: str

class PasswordStrengthResponse(BaseModel):
    is_valid: bool
    score: int
    errors: List[str]
    suggestions: List[str]

class SessionRevokeRequest(BaseModel):
    session_ids: List[str]
    reason: Optional[str] = "ユーザーによる手動削除"

class TrustDeviceRequest(BaseModel):
    trusted: bool

# ===================
# セキュリティ状況API
# ===================

@router.get("/metrics", response_model=SecurityMetrics, summary="セキュリティメトリクス取得")
async def get_security_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザーのセキュリティメトリクス取得"""
    
    # アクティブセッション数
    active_sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).count()
    
    # 信頼デバイス数
    trusted_devices = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.device_info.contains('"trusted": true')
    ).count()
    
    # 最近の失敗ログイン数（過去24時間）
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    recent_failed_logins = db.query(UserAccessLog).filter(
        UserAccessLog.user_id == current_user.id,
        UserAccessLog.action.in_(["login_failed", "mfa_failed"]),
        UserAccessLog.created_at >= one_day_ago,
        UserAccessLog.success == False
    ).count()
    
    # パスワード強度（実装では実際の計算）
    password_strength = 85 if current_user.role.value == "SUPER_ADMIN" else 75
    
    return SecurityMetrics(
        password_strength=password_strength,
        mfa_enabled=current_user.mfa_enabled,
        active_sessions=active_sessions,
        last_password_change=current_user.updated_at.isoformat() if current_user.updated_at else None,
        recent_failed_logins=recent_failed_logins,
        trusted_devices=trusted_devices
    )

@router.get("/recommendations", response_model=List[SecurityRecommendation], summary="セキュリティ推奨事項")
async def get_security_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """セキュリティ推奨事項取得"""
    recommendations = security_service.get_security_recommendations(current_user, db)
    
    return [
        SecurityRecommendation(
            priority=rec["priority"],
            category=rec["category"],
            title=rec["title"],
            description=rec["description"],
            action_url=rec["action_url"]
        )
        for rec in recommendations
    ]

@router.get("/sessions", summary="アクティブセッション一覧")
async def get_active_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """アクティブセッション一覧取得"""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).order_by(UserSession.last_used_at.desc()).all()
    
    current_ip = request.headers.get("X-Forwarded-For", request.client.host)
    
    session_list = []
    for session in sessions:
        device_info = session.device_info or {}
        is_current = session.ip_address == current_ip
        
        session_list.append(SessionInfo(
            id=session.session_id,
            device_info=device_info,
            ip_address=session.ip_address,
            is_current=is_current,
            last_used_at=session.last_used_at.isoformat(),
            created_at=session.created_at.isoformat(),
            location={"country": "Japan", "city": "Tokyo"}  # 実装では実際のGeoIP
        ))
    
    return {"sessions": session_list}

@router.get("/access-history", response_model=List[AccessLogEntry], summary="アクセス履歴")
async def get_access_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """アクセス履歴取得"""
    logs = db.query(UserAccessLog).filter(
        UserAccessLog.user_id == current_user.id
    ).order_by(UserAccessLog.created_at.desc()).limit(limit).all()
    
    return [
        AccessLogEntry(
            id=str(log.id),
            action=log.action,
            ip_address=log.ip_address,
            user_agent=log.user_agent or "",
            success=log.success,
            timestamp=log.created_at.isoformat(),
            location="Japan",  # 実装では実際のGeoIP
            risk_level="low",  # 実装では実際のリスク計算
            details={"method": log.method, "path": log.path}
        )
        for log in logs
    ]

@router.get("/alerts", response_model=List[SecurityAlert], summary="セキュリティアラート")
async def get_security_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """セキュリティアラート取得"""
    # 実装では実際のアラートテーブルから取得
    # 現在はサンプルデータ
    alerts = []
    
    # 最近の失敗ログインをアラートとして表示
    recent_failures = db.query(UserAccessLog).filter(
        UserAccessLog.user_id == current_user.id,
        UserAccessLog.success == False,
        UserAccessLog.created_at >= datetime.utcnow() - timedelta(days=7)
    ).order_by(UserAccessLog.created_at.desc()).limit(10).all()
    
    for failure in recent_failures:
        alerts.append(SecurityAlert(
            id=str(failure.id),
            type="login_failure",
            level="warning",
            title="ログイン失敗",
            description=f"IP {failure.ip_address} からのログイン試行が失敗しました",
            timestamp=failure.created_at.isoformat(),
            acknowledged=False,
            details={
                "ip_address": failure.ip_address,
                "user_agent": failure.user_agent,
                "action": failure.action
            }
        ))
    
    return alerts

# ===================
# セキュリティ操作API
# ===================

@router.post("/sessions/revoke", summary="セッション削除")
async def revoke_sessions(
    request: Request,
    request_data: SessionRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """指定セッション削除"""
    
    # セッション削除
    revoked_sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.session_id.in_(request_data.session_ids)
    ).all()
    
    for session in revoked_sessions:
        session.is_active = False
        session.revoked_at = datetime.utcnow()
        session.revoke_reason = request_data.reason
    
    db.commit()
    
    # 監査ログ記録
    audit_event = AuditEvent(
        event_type=AuditEventType.LOGOUT,
        user_id=current_user.id,
        session_id=None,
        ip_address=request.headers.get("X-Forwarded-For", request.client.host),
        user_agent=request.headers.get("User-Agent"),
        resource="/security/sessions",
        action="revoke_sessions",
        details={
            "revoked_session_count": len(revoked_sessions),
            "session_ids": request_data.session_ids,
            "reason": request_data.reason
        },
        success=True,
        timestamp=datetime.utcnow(),
        risk_level="low"
    )
    await mlm_audit_service.log_event(audit_event, db)
    
    return {"message": f"{len(revoked_sessions)}個のセッションを削除しました"}

@router.post("/sessions/revoke-all-others", summary="他全セッション削除")
async def revoke_all_other_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """現在のセッション以外を全削除"""
    
    current_ip = request.headers.get("X-Forwarded-For", request.client.host)
    
    # 現在のセッション以外を削除
    other_sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
        UserSession.ip_address != current_ip
    ).all()
    
    for session in other_sessions:
        session.is_active = False
        session.revoked_at = datetime.utcnow()
        session.revoke_reason = "ユーザーによる他全セッション削除"
    
    db.commit()
    
    # 監査ログ記録
    audit_event = AuditEvent(
        event_type=AuditEventType.LOGOUT,
        user_id=current_user.id,
        session_id=None,
        ip_address=current_ip,
        user_agent=request.headers.get("User-Agent"),
        resource="/security/sessions",
        action="revoke_all_others",
        details={
            "revoked_session_count": len(other_sessions)
        },
        success=True,
        timestamp=datetime.utcnow(),
        risk_level="low"
    )
    await mlm_audit_service.log_event(audit_event, db)
    
    return {"message": f"{len(other_sessions)}個のセッションを削除しました"}

@router.post("/password/check-strength", response_model=PasswordStrengthResponse, summary="パスワード強度チェック")
async def check_password_strength(
    request_data: PasswordStrengthRequest,
    current_user: User = Depends(get_current_user)
):
    """パスワード強度チェック"""
    result = security_service.validate_password_strength(request_data.password, current_user)
    
    return PasswordStrengthResponse(
        is_valid=result["is_valid"],
        score=result["score"],
        errors=result["errors"],
        suggestions=result["suggestions"]
    )

@router.post("/password/generate", summary="セキュアパスワード生成")
async def generate_secure_password(
    length: int = 16,
    current_user: User = Depends(get_current_user)
):
    """セキュアパスワード生成"""
    if length < 8 or length > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="パスワード長は8-64文字の間で指定してください"
        )
    
    password = security_service.generate_secure_password(length)
    
    return {"password": password}

@router.patch("/sessions/{session_id}/trust", summary="デバイス信頼設定")
async def set_device_trust(
    session_id: str,
    request_data: TrustDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """デバイス信頼設定"""
    
    session = db.query(UserSession).filter(
        UserSession.session_id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="セッションが見つかりません"
        )
    
    # デバイス情報更新
    device_info = session.device_info or {}
    device_info["trusted"] = request_data.trusted
    session.device_info = device_info
    
    db.commit()
    
    return {"message": "デバイス信頼設定を更新しました"}

@router.patch("/alerts/{alert_id}/acknowledge", summary="アラート確認")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """セキュリティアラート確認"""
    
    # 実装では実際のアラートテーブルを更新
    # 現在は基本レスポンスのみ
    
    return {"message": "アラートを確認しました"}

# ===================
# MFA管理API
# ===================

@router.post("/mfa/setup", summary="MFA設定開始")
async def initiate_mfa_setup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MFA設定開始"""
    
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAは既に有効化されています"
        )
    
    # MFAセットアップ開始
    setup_data = auth_service.initiate_mfa_setup(current_user.id, db)
    
    return {
        "qr_code": setup_data["qr_code"],
        "secret": setup_data["secret"],
        "backup_codes": setup_data["backup_codes"]
    }

@router.post("/mfa/enable", summary="MFA有効化")
async def enable_mfa(
    request: Request,
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MFA有効化"""
    
    success = await auth_service.enable_mfa(current_user.id, code, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="認証コードが正しくありません"
        )
    
    # セキュリティ通知送信
    await security_notification_service.send_user_security_notification(
        user=current_user,
        notification_type="mfa_enabled",
        details={
            "ip_address": request.headers.get("X-Forwarded-For", request.client.host),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {"message": "MFAが有効化されました"}

@router.post("/mfa/disable", summary="MFA無効化")
async def disable_mfa(
    request: Request,
    password: str,
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MFA無効化"""
    
    success = await auth_service.disable_mfa(current_user.id, password, code, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="パスワードまたは認証コードが正しくありません"
        )
    
    # セキュリティ通知送信
    await security_notification_service.send_user_security_notification(
        user=current_user,
        notification_type="mfa_disabled",
        details={
            "ip_address": request.headers.get("X-Forwarded-For", request.client.host),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {"message": "MFAが無効化されました"}