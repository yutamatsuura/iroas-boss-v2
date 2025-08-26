# IROAS BOSS V2 - 監査・コンプライアンスサービス
# Phase 21対応・MLM監査要件準拠

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from dataclasses import dataclass

from app.models.user import UserAccessLog, User
from app.database import SessionLocal

class AuditEventType(Enum):
    """監査イベント分類"""
    # 認証関連
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    
    # アカウント管理
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_UPDATED = "account_updated"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # MLMビジネス操作
    MEMBER_CREATED = "member_created"
    MEMBER_UPDATED = "member_updated"
    MEMBER_DELETED = "member_deleted"
    ORGANIZATION_CHANGED = "organization_changed"
    SPONSOR_CHANGED = "sponsor_changed"
    
    # 決済関連
    PAYMENT_EXPORTED = "payment_exported"
    PAYMENT_IMPORTED = "payment_imported"
    REWARD_CALCULATED = "reward_calculated"
    PAYOUT_PROCESSED = "payout_processed"
    
    # システム管理
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    DATA_BACKUP = "data_backup"
    DATA_RESTORE = "data_restore"
    
    # セキュリティ
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

@dataclass
class AuditEvent:
    """監査イベント"""
    event_type: AuditEventType
    user_id: Optional[int]
    session_id: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    resource: Optional[str]
    action: str
    details: Dict[str, Any]
    success: bool
    timestamp: datetime
    risk_level: str = "low"  # low, medium, high, critical

class MLMAuditService:
    """
    MLM監査サービス
    コンプライアンス・規制要件準拠
    """
    
    def __init__(self):
        self.retention_days = 2555  # 7年間保存（法的要件）
        self.high_risk_events = [
            AuditEventType.PERMISSION_GRANTED,
            AuditEventType.SPONSOR_CHANGED,
            AuditEventType.ORGANIZATION_CHANGED,
            AuditEventType.REWARD_CALCULATED,
            AuditEventType.PAYOUT_PROCESSED,
            AuditEventType.SYSTEM_CONFIG_CHANGED,
        ]
    
    # ===================
    # 監査ログ記録
    # ===================
    
    async def log_event(
        self, 
        event: AuditEvent,
        db: Session,
        additional_context: Dict[str, Any] = None
    ):
        """
        監査イベント記録
        """
        # リスクレベル自動判定
        risk_level = self._determine_risk_level(event)
        
        # 追加コンテキスト情報
        context = {
            "timestamp_utc": event.timestamp.isoformat(),
            "server_info": self._get_server_info(),
            **(additional_context or {})
        }
        
        # 機密データのマスキング
        masked_details = self._mask_sensitive_data(event.details)
        
        # データベース記録
        access_log = UserAccessLog(
            user_id=event.user_id,
            action=event.event_type.value,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            path=event.resource,
            method=event.action,
            success=event.success,
            error_message=masked_details.get("error_message"),
            created_at=event.timestamp,
        )
        
        db.add(access_log)
        db.commit()
        
        # 高リスクイベントの場合は即座に通知
        if risk_level in ["high", "critical"]:
            await self._send_compliance_alert(event, risk_level)
        
        # 統計情報更新
        await self._update_audit_statistics(event, db)
    
    def _determine_risk_level(self, event: AuditEvent) -> str:
        """リスクレベル判定"""
        
        # 失敗イベントは中リスク以上
        if not event.success:
            if event.event_type in [
                AuditEventType.UNAUTHORIZED_ACCESS,
                AuditEventType.SUSPICIOUS_ACTIVITY
            ]:
                return "critical"
            return "medium"
        
        # 高リスクイベント
        if event.event_type in self.high_risk_events:
            return "high"
        
        # MLMビジネス操作は中リスク
        if event.event_type.value.startswith(("member_", "organization_", "reward_", "payout_")):
            return "medium"
        
        return "low"
    
    def _mask_sensitive_data(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """機密データマスキング"""
        masked = details.copy()
        
        sensitive_fields = [
            "password", "secret", "token", "key", "ssn", "credit_card",
            "bank_account", "personal_id", "mfa_secret"
        ]
        
        def mask_value(value):
            if isinstance(value, str) and len(value) > 4:
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
            return "***MASKED***"
        
        def mask_recursive(obj):
            if isinstance(obj, dict):
                return {
                    k: mask_value(v) if any(field in k.lower() for field in sensitive_fields) 
                    else mask_recursive(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [mask_recursive(item) for item in obj]
            return obj
        
        return mask_recursive(masked)
    
    def _get_server_info(self) -> Dict[str, str]:
        """サーバー情報取得"""
        import platform
        import socket
        
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }
    
    async def _send_compliance_alert(self, event: AuditEvent, risk_level: str):
        """コンプライアンス通知"""
        # 実装では実際の通知システム連携
        import logging
        
        logger = logging.getLogger("compliance")
        logger.warning(
            f"High-risk audit event: {event.event_type.value} "
            f"by user {event.user_id} from {event.ip_address}"
        )
    
    # ===================
    # 監査分析・レポート
    # ===================
    
    async def generate_compliance_report(
        self, 
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None,
        event_types: Optional[List[AuditEventType]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        コンプライアンス報告書生成
        """
        if not db:
            db = SessionLocal()
        
        try:
            # 基本統計
            base_query = db.query(UserAccessLog).filter(
                and_(
                    UserAccessLog.created_at >= start_date,
                    UserAccessLog.created_at <= end_date
                )
            )
            
            if user_id:
                base_query = base_query.filter(UserAccessLog.user_id == user_id)
            
            if event_types:
                event_values = [e.value for e in event_types]
                base_query = base_query.filter(UserAccessLog.action.in_(event_values))
            
            total_events = base_query.count()
            success_events = base_query.filter(UserAccessLog.success == True).count()
            failed_events = total_events - success_events
            
            # ユーザー別統計
            user_stats = base_query.join(User).with_entities(
                User.username,
                User.role,
                func.count(UserAccessLog.id).label('event_count'),
                func.sum(func.cast(UserAccessLog.success, db.Integer)).label('success_count')
            ).group_by(User.id, User.username, User.role).all()
            
            # 時間別分析
            hourly_stats = base_query.with_entities(
                func.extract('hour', UserAccessLog.created_at).label('hour'),
                func.count(UserAccessLog.id).label('count')
            ).group_by(func.extract('hour', UserAccessLog.created_at)).all()
            
            # IP別分析
            ip_stats = base_query.with_entities(
                UserAccessLog.ip_address,
                func.count(UserAccessLog.id).label('count'),
                func.count(func.distinct(UserAccessLog.user_id)).label('unique_users')
            ).group_by(UserAccessLog.ip_address).order_by(
                func.count(UserAccessLog.id).desc()
            ).limit(20).all()
            
            # 失敗イベント分析
            failed_events_detail = base_query.filter(
                UserAccessLog.success == False
            ).with_entities(
                UserAccessLog.action,
                UserAccessLog.ip_address,
                func.count(UserAccessLog.id).label('count')
            ).group_by(
                UserAccessLog.action, UserAccessLog.ip_address
            ).order_by(
                func.count(UserAccessLog.id).desc()
            ).limit(10).all()
            
            report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "summary": {
                    "total_events": total_events,
                    "success_events": success_events,
                    "failed_events": failed_events,
                    "success_rate": (success_events / total_events * 100) if total_events > 0 else 0,
                },
                "user_activity": [
                    {
                        "username": stat.username,
                        "role": stat.role.value if stat.role else "unknown",
                        "total_events": stat.event_count,
                        "success_events": stat.success_count or 0,
                        "failure_rate": ((stat.event_count - (stat.success_count or 0)) / stat.event_count * 100) if stat.event_count > 0 else 0
                    }
                    for stat in user_stats
                ],
                "time_distribution": [
                    {"hour": int(stat.hour), "count": stat.count}
                    for stat in hourly_stats
                ],
                "ip_analysis": [
                    {
                        "ip_address": stat.ip_address,
                        "total_requests": stat.count,
                        "unique_users": stat.unique_users,
                        "requests_per_user": stat.count / stat.unique_users if stat.unique_users > 0 else 0
                    }
                    for stat in ip_stats
                ],
                "security_incidents": [
                    {
                        "event_type": detail.action,
                        "ip_address": detail.ip_address,
                        "failure_count": detail.count
                    }
                    for detail in failed_events_detail
                ],
                "generated_at": datetime.utcnow().isoformat(),
                "report_hash": self._generate_report_hash({
                    "total_events": total_events,
                    "success_rate": (success_events / total_events) if total_events > 0 else 0,
                    "period": f"{start_date.date()}-{end_date.date()}"
                })
            }
            
            return report
        
        finally:
            db.close()
    
    def _generate_report_hash(self, report_summary: Dict[str, Any]) -> str:
        """報告書ハッシュ生成（改ざん検知）"""
        report_str = json.dumps(report_summary, sort_keys=True)
        return hashlib.sha256(report_str.encode()).hexdigest()
    
    # ===================
    # MLM固有監査機能
    # ===================
    
    async def audit_mlm_commission_calculation(
        self,
        calculation_id: str,
        user_id: int,
        member_data: Dict[str, Any],
        calculation_result: Dict[str, Any],
        db: Session
    ):
        """MLM報酬計算監査"""
        
        event = AuditEvent(
            event_type=AuditEventType.REWARD_CALCULATED,
            user_id=user_id,
            session_id=None,
            ip_address="system",
            user_agent="reward_calculation_engine",
            resource="mlm_rewards",
            action="calculate",
            details={
                "calculation_id": calculation_id,
                "member_count": len(member_data.get("members", [])),
                "total_commission": calculation_result.get("total_commission", 0),
                "calculation_method": calculation_result.get("method"),
                "bonus_types": calculation_result.get("bonus_types", []),
                "affected_members": len(calculation_result.get("member_commissions", []))
            },
            success=True,
            timestamp=datetime.utcnow(),
            risk_level="high"
        )
        
        await self.log_event(event, db)
    
    async def audit_organization_change(
        self,
        changed_member_id: int,
        old_sponsor_id: Optional[int],
        new_sponsor_id: int,
        changed_by_user_id: int,
        reason: str,
        ip_address: str,
        db: Session
    ):
        """組織変更監査"""
        
        event = AuditEvent(
            event_type=AuditEventType.ORGANIZATION_CHANGED,
            user_id=changed_by_user_id,
            session_id=None,
            ip_address=ip_address,
            user_agent=None,
            resource="mlm_organization",
            action="sponsor_change",
            details={
                "member_id": changed_member_id,
                "old_sponsor_id": old_sponsor_id,
                "new_sponsor_id": new_sponsor_id,
                "change_reason": reason,
                "impact_analysis": "pending"  # 実装では影響分析を実行
            },
            success=True,
            timestamp=datetime.utcnow(),
            risk_level="high"
        )
        
        await self.log_event(event, db)
    
    # ===================
    # データ保護・プライバシー
    # ===================
    
    async def anonymize_user_audit_data(self, user_id: int, db: Session):
        """
        ユーザー監査データ匿名化（GDPR対応）
        """
        anonymized_user_id = f"anonymized_user_{hashlib.md5(str(user_id).encode()).hexdigest()[:8]}"
        
        # 監査ログの個人情報を匿名化
        logs = db.query(UserAccessLog).filter(UserAccessLog.user_id == user_id).all()
        
        for log in logs:
            # user_idを匿名化IDに置換
            log.user_id = None  # 匿名化
            # IPアドレスを部分マスキング
            if log.ip_address:
                ip_parts = log.ip_address.split('.')
                if len(ip_parts) == 4:
                    log.ip_address = f"{ip_parts[0]}.{ip_parts[1]}.xxx.xxx"
        
        db.commit()
    
    async def cleanup_expired_audit_data(self, db: Session):
        """期限切れ監査データクリーンアップ"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        expired_logs = db.query(UserAccessLog).filter(
            UserAccessLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        return expired_logs
    
    async def _update_audit_statistics(self, event: AuditEvent, db: Session):
        """監査統計更新"""
        # 実装では統計テーブル更新
        # - 日別/時間別統計
        # - ユーザー別統計
        # - イベント種別統計
        pass

# グローバルインスタンス
mlm_audit_service = MLMAuditService()