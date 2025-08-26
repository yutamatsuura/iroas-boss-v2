# IROAS BOSS V2 - セキュリティ通知・アラートサービス
# Phase 21対応・コンプライアンス通知統合

import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.user import User, UserAccessLog
from app.services.audit_service import AuditEvent, AuditEventType

# 通知レベル
class NotificationLevel:
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"
    SECURITY = "security"

class SecurityNotificationService:
    """
    セキュリティアラート・通知サービス
    MLMコンプライアンス通知統合
    """
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"  # 環境設定で変更
        self.smtp_port = 587
        self.from_email = "security@iroas-boss.com"  # 環境設定で変更
        self.admin_emails = [
            "admin@iroas-boss.com",
            "security@iroas-boss.com"
        ]
        
        # セキュリティログ設定
        self.security_logger = logging.getLogger("security.notifications")
        handler = logging.FileHandler("security_notifications.log")
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.security_logger.addHandler(handler)
        self.security_logger.setLevel(logging.INFO)
        
        # 通知閾値設定
        self.notification_thresholds = {
            "failed_login_attempts": 5,  # 5回の失敗ログイン試行
            "rate_limit_violations": 3,  # 3回のレート制限違反
            "suspicious_ip_activity": 10,  # 同一IPからの10回以上のアクセス
            "mfa_bypass_attempts": 1,  # MFAバイパス試行（即座に通知）
            "admin_permission_changes": 1,  # 管理者権限変更（即座に通知）
        }
    
    # ===================
    # 即座通知（Critical）
    # ===================
    
    async def send_critical_security_alert(
        self,
        event_type: str,
        user: Optional[User],
        details: Dict[str, Any],
        ip_address: str
    ):
        """
        緊急セキュリティアラート送信
        """
        alert_data = {
            "level": NotificationLevel.CRITICAL,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_info": {
                "user_id": user.id if user else None,
                "username": user.username if user else "Unknown",
                "role": user.role.value if user and user.role else None
            },
            "ip_address": ip_address,
            "details": details
        }
        
        # ログ記録
        self.security_logger.critical(f"CRITICAL SECURITY ALERT: {json.dumps(alert_data, indent=2)}")
        
        # メール通知
        await self._send_email_alert(
            subject=f"🚨 緊急セキュリティアラート: {event_type}",
            alert_data=alert_data,
            recipients=self.admin_emails
        )
        
        # Slack通知（実装環境に応じて）
        await self._send_slack_alert(alert_data)
        
        # SMS通知（重要なイベント用）
        if event_type in ["unauthorized_admin_access", "data_breach_attempt", "system_compromise"]:
            await self._send_sms_alert(alert_data)
    
    async def send_mfa_bypass_alert(self, user: User, ip_address: str, attempt_details: Dict[str, Any]):
        """MFAバイパス試行アラート"""
        await self.send_critical_security_alert(
            event_type="mfa_bypass_attempt",
            user=user,
            details={
                **attempt_details,
                "severity": "CRITICAL",
                "recommendation": "アカウントを即座に無効化し、調査を開始してください"
            },
            ip_address=ip_address
        )
    
    async def send_admin_privilege_change_alert(
        self,
        changed_user: User,
        admin_user: User,
        changes: Dict[str, Any],
        ip_address: str
    ):
        """管理者権限変更アラート"""
        await self.send_critical_security_alert(
            event_type="admin_privilege_change",
            user=admin_user,
            details={
                "target_user": {
                    "id": changed_user.id,
                    "username": changed_user.username,
                    "role": changed_user.role.value
                },
                "changes": changes,
                "severity": "HIGH",
                "compliance_note": "MLMコンプライアンス要件により記録"
            },
            ip_address=ip_address
        )
    
    # ===================
    # 累積アラート（Warning）
    # ===================
    
    async def check_and_send_accumulated_alerts(self, db: Session):
        """
        累積セキュリティアラート確認・送信
        """
        # 過去1時間の失敗ログイン試行
        await self._check_failed_login_threshold(db)
        
        # レート制限違反
        await self._check_rate_limit_violations(db)
        
        # 疑わしいIP活動
        await self._check_suspicious_ip_activity(db)
        
        # MLM特有のアラート
        await self._check_mlm_compliance_alerts(db)
    
    async def _check_failed_login_threshold(self, db: Session):
        """失敗ログイン試行閾値チェック"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        failed_attempts = db.query(UserAccessLog).filter(
            UserAccessLog.action == "login_failed",
            UserAccessLog.created_at >= one_hour_ago,
            UserAccessLog.success == False
        ).all()
        
        # IPアドレス別集計
        ip_attempts = {}
        for attempt in failed_attempts:
            ip = attempt.ip_address
            if ip not in ip_attempts:
                ip_attempts[ip] = []
            ip_attempts[ip].append(attempt)
        
        # 閾値超過IPに対してアラート送信
        for ip, attempts in ip_attempts.items():
            if len(attempts) >= self.notification_thresholds["failed_login_attempts"]:
                await self._send_warning_alert(
                    event_type="excessive_failed_logins",
                    details={
                        "ip_address": ip,
                        "attempt_count": len(attempts),
                        "timeframe": "past_hour",
                        "usernames_attempted": [a.user_id for a in attempts if a.user_id]
                    }
                )
    
    async def _check_rate_limit_violations(self, db: Session):
        """レート制限違反チェック"""
        # 実装では専用テーブルまたはログから集計
        # ここでは基本実装のみ
        pass
    
    async def _check_suspicious_ip_activity(self, db: Session):
        """疑わしいIP活動チェック"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        # 同一IPからの大量アクセス検出
        ip_activity = db.query(
            UserAccessLog.ip_address,
            db.func.count(UserAccessLog.id).label('request_count')
        ).filter(
            UserAccessLog.created_at >= one_hour_ago
        ).group_by(UserAccessLog.ip_address).having(
            db.func.count(UserAccessLog.id) >= self.notification_thresholds["suspicious_ip_activity"]
        ).all()
        
        for ip, count in ip_activity:
            await self._send_warning_alert(
                event_type="suspicious_ip_activity",
                details={
                    "ip_address": ip,
                    "request_count": count,
                    "timeframe": "past_hour",
                    "recommendation": "IPブロックを検討してください"
                }
            )
    
    async def _check_mlm_compliance_alerts(self, db: Session):
        """MLMコンプライアンスアラート"""
        # 重要なMLM操作の監視
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        critical_actions = [
            "reward_calculated",
            "organization_changed", 
            "sponsor_changed",
            "payout_processed"
        ]
        
        for action in critical_actions:
            recent_events = db.query(UserAccessLog).filter(
                UserAccessLog.action == action,
                UserAccessLog.created_at >= one_hour_ago
            ).all()
            
            if len(recent_events) > 5:  # 1時間に5回以上の重要操作
                await self._send_warning_alert(
                    event_type="excessive_mlm_operations",
                    details={
                        "operation_type": action,
                        "count": len(recent_events),
                        "timeframe": "past_hour",
                        "compliance_note": "MLM規制要件により監視中"
                    }
                )
    
    # ===================
    # 通知送信メソッド
    # ===================
    
    async def _send_warning_alert(self, event_type: str, details: Dict[str, Any]):
        """警告レベルアラート送信"""
        alert_data = {
            "level": NotificationLevel.WARNING,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        
        self.security_logger.warning(f"WARNING SECURITY ALERT: {json.dumps(alert_data, indent=2)}")
        
        # 管理者へメール通知
        await self._send_email_alert(
            subject=f"⚠️ セキュリティ警告: {event_type}",
            alert_data=alert_data,
            recipients=self.admin_emails
        )
    
    async def _send_email_alert(
        self,
        subject: str,
        alert_data: Dict[str, Any],
        recipients: List[str]
    ):
        """メールアラート送信"""
        try:
            # HTML形式のアラートメール作成
            html_content = self._generate_alert_email_html(alert_data)
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(recipients)
            
            # HTMLパート追加
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)
            
            # 実装では実際のSMTP送信
            # 開発環境ではログ記録のみ
            self.security_logger.info(f"Email alert sent: {subject} to {recipients}")
            
        except Exception as e:
            self.security_logger.error(f"Failed to send email alert: {e}")
    
    async def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Slack通知送信"""
        try:
            # 実装では実際のSlack Webhook使用
            slack_payload = {
                "text": f"🚨 IROAS BOSS V2 Security Alert",
                "attachments": [
                    {
                        "color": "danger" if alert_data["level"] == NotificationLevel.CRITICAL else "warning",
                        "fields": [
                            {"title": "Event Type", "value": alert_data["event_type"], "short": True},
                            {"title": "Level", "value": alert_data["level"], "short": True},
                            {"title": "Timestamp", "value": alert_data["timestamp"], "short": True}
                        ]
                    }
                ]
            }
            
            self.security_logger.info(f"Slack alert prepared: {alert_data['event_type']}")
            
        except Exception as e:
            self.security_logger.error(f"Failed to send Slack alert: {e}")
    
    async def _send_sms_alert(self, alert_data: Dict[str, Any]):
        """SMS緊急通知送信"""
        try:
            # 実装では実際のSMS API使用（Twilio等）
            message = f"IROAS BOSS V2 緊急アラート: {alert_data['event_type']} - {alert_data['timestamp']}"
            
            self.security_logger.info(f"SMS alert prepared: {message}")
            
        except Exception as e:
            self.security_logger.error(f"Failed to send SMS alert: {e}")
    
    def _generate_alert_email_html(self, alert_data: Dict[str, Any]) -> str:
        """アラートメールHTML生成"""
        level_colors = {
            NotificationLevel.INFO: "#2196F3",
            NotificationLevel.WARNING: "#FF9800", 
            NotificationLevel.CRITICAL: "#F44336",
            NotificationLevel.SECURITY: "#9C27B0"
        }
        
        color = level_colors.get(alert_data["level"], "#666666")
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h2 style="margin: 0;">IROAS BOSS V2 セキュリティアラート</h2>
                    <p style="margin: 5px 0 0 0;">レベル: {alert_data["level"].upper()}</p>
                </div>
                <div style="background: #f5f5f5; padding: 20px; border-radius: 0 0 8px 8px; border: 1px solid #ddd;">
                    <h3>イベント詳細</h3>
                    <p><strong>種類:</strong> {alert_data["event_type"]}</p>
                    <p><strong>時刻:</strong> {alert_data["timestamp"]}</p>
                    
                    {self._format_alert_details_html(alert_data.get("details", {}))}
                    
                    <hr>
                    <p style="font-size: 12px; color: #666;">
                        このアラートはIROAS BOSS V2セキュリティシステムにより自動生成されました。
                        Phase 21 - 認証セキュリティ統合
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _format_alert_details_html(self, details: Dict[str, Any]) -> str:
        """アラート詳細HTML整形"""
        html = "<h4>詳細情報</h4><ul>"
        
        for key, value in details.items():
            if isinstance(value, dict):
                html += f"<li><strong>{key}:</strong><ul>"
                for subkey, subvalue in value.items():
                    html += f"<li>{subkey}: {subvalue}</li>"
                html += "</ul></li>"
            else:
                html += f"<li><strong>{key}:</strong> {value}</li>"
        
        html += "</ul>"
        return html
    
    # ===================
    # ユーザー通知
    # ===================
    
    async def send_user_security_notification(
        self,
        user: User,
        notification_type: str,
        details: Dict[str, Any]
    ):
        """ユーザー向けセキュリティ通知"""
        notification_templates = {
            "password_changed": "パスワードが変更されました。",
            "mfa_enabled": "多要素認証が有効化されました。",
            "new_device_login": "新しいデバイスからのログインが検出されました。",
            "suspicious_activity": "アカウントで疑わしい活動が検出されました。",
            "account_locked": "セキュリティ上の理由によりアカウントがロックされました。"
        }
        
        message = notification_templates.get(notification_type, "セキュリティイベントが発生しました。")
        
        # ユーザー通知ログ記録
        self.security_logger.info(
            f"User notification sent - User: {user.username}, Type: {notification_type}, Message: {message}"
        )
        
        # 実装では実際のユーザーメール送信
        if user.email:
            await self._send_user_email(user, notification_type, message, details)

    async def _send_user_email(self, user: User, notification_type: str, message: str, details: Dict[str, Any]):
        """ユーザーメール送信"""
        try:
            subject = f"IROAS BOSS V2 セキュリティ通知: {notification_type}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2196F3;">セキュリティ通知</h2>
                    <p>こんにちは {user.username}さん、</p>
                    <p>{message}</p>
                    
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>時刻:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                        <p><strong>IP アドレス:</strong> {details.get('ip_address', 'Unknown')}</p>
                    </div>
                    
                    <p>このアクションがお客様によるものでない場合は、直ちに管理者にお知らせください。</p>
                    
                    <hr>
                    <p style="font-size: 12px; color: #666;">
                        IROAS BOSS V2 セキュリティシステム
                    </p>
                </div>
            </body>
            </html>
            """
            
            self.security_logger.info(f"User email notification prepared for {user.username}: {notification_type}")
            
        except Exception as e:
            self.security_logger.error(f"Failed to send user email: {e}")

# グローバルインスタンス
security_notification_service = SecurityNotificationService()