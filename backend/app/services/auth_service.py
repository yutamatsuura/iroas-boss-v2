# IROAS BOSS V2 - 認証サービス
# Phase 21対応・MLMビジネス要件準拠

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.user import (
    User, UserSession, UserAccessLog, UserPermission, UserRolePermission,
    UserRole, UserStatus
)
from app.schemas.auth import (
    LoginRequest, LoginResponse, UserSummary, UserCreate, UserUpdate,
    UserPasswordChange, MFASetupRequest, MFASetupResponse, 
    SessionInfo, AccessLogSummary
)
from app.core.security import security, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.database import SessionLocal
from app.services.security_service import security_service
from app.services.audit_service import mlm_audit_service, AuditEvent, AuditEventType
from app.services.notification_service import security_notification_service

class AuthService:
    """認証サービス（MLMビジネス要件準拠）"""
    
    def __init__(self):
        self.security = security
    
    # ===================
    # 認証機能
    # ===================
    
    async def authenticate_user(
        self, 
        login_data: LoginRequest, 
        ip_address: str, 
        user_agent: str,
        db: Session
    ) -> LoginResponse:
        """ユーザー認証・ログイン処理（セキュリティ強化統合）"""
        
        # ユーザー取得
        user = db.query(User).filter(
            or_(
                User.username == login_data.username,
                User.email == login_data.username
            )
        ).first()
        
        if not user:
            # 監査ログ記録
            audit_event = AuditEvent(
                event_type=AuditEventType.LOGIN_FAILED,
                user_id=None,
                session_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
                resource="/auth/login",
                action="login",
                details={
                    "attempted_username": login_data.username,
                    "failure_reason": "user_not_found"
                },
                success=False,
                timestamp=datetime.utcnow(),
                risk_level="medium"
            )
            await mlm_audit_service.log_event(audit_event, db)
            
            await self._log_access(None, "login_failed", ip_address, user_agent, False, "ユーザーが存在しません", db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザー名またはパスワードが正しくありません"
            )
        
        # アカウント状態チェック
        if not user.is_active:
            await self._log_access(user.id, "login_failed", ip_address, user_agent, False, "アカウントが無効です", db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="アカウントが無効です"
            )
        
        if user.status != UserStatus.ACTIVE:
            await self._log_access(user.id, "login_failed", ip_address, user_agent, False, f"アカウント状態: {user.status.value}", db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"アカウント状態が無効です: {user.status.value}"
            )
        
        # アカウントロックチェック
        if self.security.is_account_locked(user):
            await self._log_access(user.id, "login_failed", ip_address, user_agent, False, "アカウントがロックされています", db)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="アカウントがロックされています。しばらく待ってから再試行してください。"
            )
        
        # セキュリティ行動分析
        security_analysis = await security_service.analyze_login_behavior(
            user.id, ip_address, user_agent, db
        )
        
        # 高リスクログインのブロック
        if security_analysis["block_login"]:
            audit_event = AuditEvent(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                user_id=user.id,
                session_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
                resource="/auth/login",
                action="login_blocked",
                details={
                    "risk_score": security_analysis["risk_score"],
                    "risk_factors": security_analysis["risk_factors"],
                    "security_analysis": security_analysis
                },
                success=False,
                timestamp=datetime.utcnow(),
                risk_level="critical"
            )
            await mlm_audit_service.log_event(audit_event, db)
            
            # 緊急セキュリティアラート送信
            await security_notification_service.send_critical_security_alert(
                event_type="high_risk_login_blocked",
                user=user,
                details={
                    "risk_score": security_analysis["risk_score"],
                    "risk_factors": security_analysis["risk_factors"]
                },
                ip_address=ip_address
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="セキュリティ上の理由によりログインがブロックされました。管理者にお問い合わせください。"
            )
        
        # パスワード検証
        if not self.security.verify_password(login_data.password, user.hashed_password):
            self.security.increment_login_attempts(user, db)
            await self._log_access(user.id, "login_failed", ip_address, user_agent, False, "パスワードが正しくありません", db)
            
            remaining_attempts = 5 - user.login_attempts
            if remaining_attempts > 0:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"パスワードが正しくありません。残り{remaining_attempts}回の試行が可能です。"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="ログイン試行回数が上限に達しました。アカウントがロックされました。"
                )
        
        # MFA確認（有効な場合）
        if user.mfa_enabled:
            if not login_data.mfa_code:
                raise HTTPException(
                    status_code=status.HTTP_202_ACCEPTED,
                    detail="MFAコードが必要です",
                    headers={"X-MFA-Required": "true"}
                )
            
            # MFAコード検証
            if not self._verify_mfa_code(user, login_data.mfa_code):
                self.security.increment_login_attempts(user, db)
                await self._log_access(user.id, "mfa_failed", ip_address, user_agent, False, "MFAコードが正しくありません", db)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="認証コードが正しくありません"
                )
        
        # 疑わしいアクティビティチェック
        if self.security.check_suspicious_activity(user, ip_address, db):
            await self._log_access(user.id, "suspicious_login", ip_address, user_agent, False, "疑わしいアクティビティを検出", db)
            # 管理者に通知（実装は省略）
        
        # ログイン成功
        self.security.reset_login_attempts(user, db)
        
        # セッション作成
        session = await self._create_session(user, ip_address, user_agent, login_data.remember_me, db)
        
        # トークン生成
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.security.create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = self.security.create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=refresh_token_expires
        )
        
        # セッションにトークン情報を保存
        session.session_token = access_token[:50]  # セキュリティのため一部のみ保存
        session.refresh_token = refresh_token[:50]
        db.commit()
        
        # ユーザー情報更新
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        db.commit()
        
        # 監査ログ記録（成功）
        audit_event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user.id,
            session_id=session.session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource="/auth/login",
            action="login",
            details={
                "username": user.username,
                "role": user.role.value,
                "mfa_used": user.mfa_enabled,
                "remember_me": login_data.remember_me,
                "security_analysis": security_analysis
            },
            success=True,
            timestamp=datetime.utcnow(),
            risk_level="low" if security_analysis["risk_score"] < 3 else "medium"
        )
        await mlm_audit_service.log_event(audit_event, db)
        
        # 追加認証が必要な場合のユーザー通知
        if security_analysis["require_additional_auth"]:
            await security_notification_service.send_user_security_notification(
                user=user,
                notification_type="suspicious_activity",
                details={
                    "ip_address": ip_address,
                    "risk_factors": security_analysis["risk_factors"],
                    "recommendation": "アカウントのセキュリティを確認してください"
                }
            )
        
        # 新しいデバイスからのログイン通知
        if "新しいデバイス・ブラウザからのアクセス" in security_analysis.get("risk_factors", []):
            await security_notification_service.send_user_security_notification(
                user=user,
                notification_type="new_device_login",
                details={
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "login_time": datetime.utcnow().isoformat()
                }
            )
        
        # アクセスログ記録
        await self._log_access(user.id, "login_success", ip_address, user_agent, True, "ログイン成功", db)
        
        # 権限取得
        permissions = await self.get_user_permissions(user.id, db)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user=UserSummary.from_orm(user),
            permissions=permissions,
            mfa_required=user.mfa_enabled
        )
    
    async def refresh_token(
        self, 
        refresh_token: str, 
        ip_address: str, 
        user_agent: str,
        db: Session
    ) -> LoginResponse:
        """リフレッシュトークンを使用してアクセストークンを更新"""
        
        # リフレッシュトークンを検証
        try:
            payload = self.security.verify_token(refresh_token, "refresh")
        except HTTPException:
            await self._log_access(None, "refresh_failed", ip_address, user_agent, False, "無効なリフレッシュトークン", db)
            raise
        
        user_id = int(payload.get("sub"))
        jti = payload.get("jti")
        
        # ユーザー取得
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザーが無効です"
            )
        
        # セッション確認
        session = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.jti == jti,
                UserSession.is_active == True,
                UserSession.refresh_expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session:
            await self._log_access(user_id, "refresh_failed", ip_address, user_agent, False, "セッションが無効または期限切れ", db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="セッションが無効です"
            )
        
        # 新しいアクセストークンを生成
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.security.create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        # セッション更新
        session.last_used_at = datetime.utcnow()
        session.session_token = access_token[:50]
        db.commit()
        
        # アクセスログ記録
        await self._log_access(user_id, "token_refresh", ip_address, user_agent, True, "トークンリフレッシュ成功", db)
        
        # 権限取得
        permissions = await self.get_user_permissions(user.id, db)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # リフレッシュトークンはそのまま返す
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user=UserSummary.from_orm(user),
            permissions=permissions
        )
    
    async def logout_user(
        self, 
        user_id: int, 
        session_token: str, 
        all_devices: bool,
        ip_address: str,
        user_agent: str,
        db: Session
    ):
        """ユーザーログアウト処理"""
        
        if all_devices:
            # 全デバイスからログアウト
            db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).update({
                "is_active": False,
                "revoked_at": datetime.utcnow(),
                "revoked_reason": "全デバイスログアウト"
            })
        else:
            # 現在のセッションのみログアウト
            db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.session_token == session_token[:50]
                )
            ).update({
                "is_active": False,
                "revoked_at": datetime.utcnow(),
                "revoked_reason": "ログアウト"
            })
        
        db.commit()
        
        # アクセスログ記録
        logout_type = "logout_all_devices" if all_devices else "logout"
        await self._log_access(user_id, logout_type, ip_address, user_agent, True, "ログアウト成功", db)
    
    # ===================
    # ユーザー管理
    # ===================
    
    async def create_user(
        self, 
        user_data: UserCreate,
        created_by: int,
        db: Session
    ) -> UserSummary:
        """ユーザー作成"""
        
        # 重複チェック
        existing_user = db.query(User).filter(
            or_(
                User.username == user_data.username,
                User.email == user_data.email
            )
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="ユーザー名またはメールアドレスが既に使用されています"
            )
        
        # パスワードハッシュ化
        hashed_password = self.security.hash_password(user_data.password)
        
        # ユーザー作成
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            display_name=user_data.display_name,
            phone=user_data.phone,
            role=user_data.role,
            status=UserStatus.PENDING,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # アクセスログ記録（作成者）
        await self._log_access(created_by, "user_created", None, None, True, f"ユーザー作成: {new_user.username}", db)
        
        return UserSummary.from_orm(new_user)
    
    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
        updated_by: int,
        db: Session
    ) -> UserSummary:
        """ユーザー更新"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # 更新可能フィールドの更新
        update_data = user_data.dict(exclude_unset=True)
        
        # メールアドレス重複チェック
        if "email" in update_data:
            existing_user = db.query(User).filter(
                and_(
                    User.email == update_data["email"],
                    User.id != user_id
                )
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="メールアドレスが既に使用されています"
                )
        
        # 更新実行
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # アクセスログ記録
        await self._log_access(updated_by, "user_updated", None, None, True, f"ユーザー更新: {user.username}", db)
        
        return UserSummary.from_orm(user)
    
    # ===================
    # 権限管理
    # ===================
    
    async def get_user_permissions(self, user_id: int, db: Session) -> List[str]:
        """ユーザーの権限一覧を取得"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # ロールベースの権限を取得
        role_permissions = db.query(UserRolePermission).filter(
            and_(
                UserRolePermission.role == user.role,
                UserRolePermission.is_granted == True
            )
        ).all()
        
        permission_ids = [rp.permission_id for rp in role_permissions]
        
        permissions = db.query(UserPermission).filter(
            and_(
                UserPermission.id.in_(permission_ids),
                UserPermission.is_active == True
            )
        ).all()
        
        return [p.permission_code for p in permissions]
    
    async def check_permission(
        self, 
        user_id: int, 
        permission_code: str, 
        db: Session
    ) -> bool:
        """ユーザーの権限をチェック"""
        
        user_permissions = await self.get_user_permissions(user_id, db)
        return permission_code in user_permissions or "admin.*" in user_permissions
    
    # ===================
    # セッション管理
    # ===================
    
    async def get_user_sessions(self, user_id: int, db: Session) -> List[SessionInfo]:
        """ユーザーのセッション一覧を取得"""
        
        sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).order_by(UserSession.last_used_at.desc()).all()
        
        return [SessionInfo.from_orm(session) for session in sessions]
    
    async def revoke_sessions(
        self, 
        user_id: int, 
        session_ids: List[int], 
        reason: str,
        db: Session
    ):
        """指定されたセッションを無効化"""
        
        db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.id.in_(session_ids)
            )
        ).update({
            "is_active": False,
            "revoked_at": datetime.utcnow(),
            "revoked_reason": reason
        }, synchronize_session=False)
        
        db.commit()
    
    # ===================
    # MFA管理
    # ===================
    
    async def setup_mfa(
        self, 
        user_id: int, 
        mfa_request: MFASetupRequest,
        db: Session
    ) -> MFASetupResponse:
        """MFA設定"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        if mfa_request.enable:
            # MFA有効化
            if not user.mfa_secret:
                user.mfa_secret = self.security.generate_mfa_secret()
            
            # QRコード生成
            qr_code = self.security.generate_mfa_qr_code(user.username, user.mfa_secret)
            
            # バックアップコード生成
            backup_codes = self.security.generate_backup_codes()
            user.mfa_backup_codes = json.dumps(self.security.hash_backup_codes(backup_codes))
            
            # 認証コード検証（初回設定時）
            if mfa_request.verification_code:
                if self.security.verify_mfa_code(user.mfa_secret, mfa_request.verification_code):
                    user.mfa_enabled = True
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="認証コードが正しくありません"
                    )
            
            db.commit()
            
            return MFASetupResponse(
                qr_code=qr_code,
                secret_key=user.mfa_secret,
                backup_codes=backup_codes if mfa_request.verification_code else [],
                enabled=user.mfa_enabled
            )
        else:
            # MFA無効化
            user.mfa_enabled = False
            user.mfa_secret = None
            user.mfa_backup_codes = None
            db.commit()
            
            return MFASetupResponse(
                qr_code="",
                secret_key="",
                backup_codes=[],
                enabled=False
            )
    
    # ===================
    # プライベートメソッド
    # ===================
    
    async def _create_session(
        self,
        user: User,
        ip_address: str,
        user_agent: str,
        remember_me: bool,
        db: Session
    ) -> UserSession:
        """セッションを作成"""
        
        device_info = self.security.extract_device_info(user_agent)
        
        # セッション期間設定
        if remember_me:
            expires_at = datetime.utcnow() + timedelta(days=30)
        else:
            expires_at = datetime.utcnow() + timedelta(hours=8)
        
        session = UserSession(
            user_id=user.id,
            session_token="",  # 後で更新
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=json.dumps(device_info),
            expires_at=expires_at,
            refresh_expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            is_active=True
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    async def _log_access(
        self,
        user_id: Optional[int],
        action: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        message: str,
        db: Session
    ):
        """アクセスログを記録"""
        
        log = UserAccessLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=message if not success else None
        )
        
        db.add(log)
        db.commit()
    
    def _verify_mfa_code(self, user: User, code: str) -> bool:
        """MFAコードまたはバックアップコードを検証"""
        
        # 通常のMFAコード検証
        if user.mfa_secret and self.security.verify_mfa_code(user.mfa_secret, code):
            return True
        
        # バックアップコード検証
        if user.mfa_backup_codes:
            try:
                backup_codes = json.loads(user.mfa_backup_codes)
                is_valid, updated_codes = self.security.verify_backup_code(backup_codes, code)
                
                if is_valid:
                    # 使用済みコードを更新
                    user.mfa_backup_codes = json.dumps(updated_codes)
                    return True
            except (json.JSONDecodeError, TypeError):
                pass
        
        return False

# サービスインスタンス
auth_service = AuthService()