# IROAS BOSS V2 - 高度セキュリティサービス
# Phase 21対応・認証セキュリティ強化

import hashlib
import hmac
import secrets
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from ipaddress import ip_address, ip_network
# import geoip2.database
# import geoip2.errors

from app.models.user import User, UserAccessLog, UserSession
from app.core.security import security

class SecurityService:
    """
    高度認証セキュリティサービス
    MLMビジネス要件準拠・エンタープライズグレードセキュリティ
    """
    
    def __init__(self):
        self.password_history_limit = 12  # パスワード履歴保持数
        self.suspicious_activity_threshold = 5  # 疑わしいアクティビティ閾値
        
        # 信頼できるIPレンジ（社内ネットワーク等）
        self.trusted_ip_ranges = [
            "192.168.0.0/16",
            "10.0.0.0/8",
            "172.16.0.0/12",
        ]
        
        # 危険な国コード（必要に応じて設定）
        self.high_risk_countries = [
            "CN", "RU", "KP", "IR"  # 例：中国、ロシア、北朝鮮、イラン
        ]

    # ===================
    # パスワードセキュリティ強化
    # ===================
    
    def validate_password_strength(self, password: str, user: User = None) -> Dict[str, any]:
        """
        高度パスワード強度チェック
        MLMビジネス要件準拠
        """
        result = {
            "is_valid": True,
            "score": 0,
            "errors": [],
            "suggestions": []
        }
        
        # 基本長さチェック
        if len(password) < 12:
            result["errors"].append("パスワードは12文字以上にしてください")
            result["is_valid"] = False
        else:
            result["score"] += 2
        
        # 文字種チェック
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_symbol = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if not has_upper:
            result["errors"].append("大文字を含めてください")
            result["is_valid"] = False
        else:
            result["score"] += 1
            
        if not has_lower:
            result["errors"].append("小文字を含めてください")
            result["is_valid"] = False
        else:
            result["score"] += 1
            
        if not has_digit:
            result["errors"].append("数字を含めてください")
            result["is_valid"] = False
        else:
            result["score"] += 1
            
        if not has_symbol:
            result["errors"].append("記号を含めてください")
            result["is_valid"] = False
        else:
            result["score"] += 1
        
        # 辞書攻撃対策：一般的なパスワードチェック
        common_passwords = [
            "password", "123456", "admin", "qwerty", "letmein", 
            "welcome", "monkey", "dragon", "master", "secret"
        ]
        
        if password.lower() in common_passwords:
            result["errors"].append("一般的なパスワードは使用できません")
            result["is_valid"] = False
        else:
            result["score"] += 1
        
        # ユーザー情報を含むパスワードチェック
        if user:
            user_info = [
                user.username.lower(),
                user.email.split('@')[0].lower() if user.email else "",
                user.full_name.lower() if user.full_name else ""
            ]
            
            for info in user_info:
                if info and info in password.lower():
                    result["errors"].append("個人情報をパスワードに含めないでください")
                    result["is_valid"] = False
                    break
            else:
                result["score"] += 1
        else:
            # ユーザー情報がない場合もスコア加算
            result["score"] += 1
        
        # 連続文字・重複文字チェック
        if re.search(r'(.)\1{2,}', password):  # 同じ文字が3回以上連続
            result["errors"].append("同じ文字の連続は3文字まででお願いします")
            result["is_valid"] = False
        
        # 4文字以上の連続文字列をチェック（3文字までは許可）
        if re.search(r'(0123|1234|2345|3456|4567|5678|6789|7890|abcd|bcde|cdef)', password.lower()):
            result["errors"].append("4文字以上の連続した文字列は避けてください")
            result["is_valid"] = False
        
        # スコアベース推奨事項
        if result["score"] < 5:
            result["suggestions"].append("より複雑なパスワードにしてください")
        if len(password) < 16:
            result["suggestions"].append("16文字以上にすることを推奨します")
        
        return result

    def check_password_history(self, user_id: int, new_password: str, db: Session) -> bool:
        """
        パスワード履歴チェック（過去のパスワード再利用防止）
        """
        # 実装では、パスワードハッシュの履歴テーブルを参照
        # 現在は基本実装のみ
        return True  # 履歴チェック通過

    def generate_secure_password(self, length: int = 16) -> str:
        """
        安全なパスワード生成（MLM管理者用）
        """
        # 文字セット定義
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        digits = "0123456789"
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # 最低1文字ずつ保証
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(symbols)
        ]
        
        # 残りの文字をランダム選択
        all_chars = uppercase + lowercase + digits + symbols
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # シャッフル
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)

    # ===================
    # 行動分析・異常検知
    # ===================
    
    async def analyze_login_behavior(self, user_id: int, ip_address: str, user_agent: str, db: Session) -> Dict[str, any]:
        """
        ログイン行動分析・異常検知
        """
        analysis = {
            "risk_score": 0,
            "risk_factors": [],
            "require_additional_auth": False,
            "block_login": False
        }
        
        # 過去30日のログイン履歴取得
        recent_logs = db.query(UserAccessLog).filter(
            and_(
                UserAccessLog.user_id == user_id,
                UserAccessLog.action == "login_success",
                UserAccessLog.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).order_by(desc(UserAccessLog.created_at)).limit(100).all()
        
        # IP地理的分析
        geo_risk = self._analyze_geographic_risk(ip_address, recent_logs)
        analysis["risk_score"] += geo_risk["score"]
        analysis["risk_factors"].extend(geo_risk["factors"])
        
        # 時間帯分析
        time_risk = self._analyze_time_pattern_risk(recent_logs)
        analysis["risk_score"] += time_risk["score"]
        analysis["risk_factors"].extend(time_risk["factors"])
        
        # デバイス・ブラウザ分析
        device_risk = self._analyze_device_risk(user_agent, recent_logs)
        analysis["risk_score"] += device_risk["score"]
        analysis["risk_factors"].extend(device_risk["factors"])
        
        # 頻度分析
        frequency_risk = self._analyze_login_frequency_risk(recent_logs)
        analysis["risk_score"] += frequency_risk["score"]
        analysis["risk_factors"].extend(frequency_risk["factors"])
        
        # リスクレベル判定
        if analysis["risk_score"] >= 8:
            analysis["block_login"] = True
            analysis["risk_factors"].append("高リスクログイン試行")
        elif analysis["risk_score"] >= 5:
            analysis["require_additional_auth"] = True
            analysis["risk_factors"].append("追加認証が必要")
        
        return analysis

    def _analyze_geographic_risk(self, ip_address: str, recent_logs: List[UserAccessLog]) -> Dict[str, any]:
        """IP地理的リスク分析"""
        result = {"score": 0, "factors": []}
        
        # 信頼できるIPレンジチェック
        try:
            ip = ip_address(ip_address)
            for trusted_range in self.trusted_ip_ranges:
                if ip in ip_network(trusted_range):
                    result["score"] = -2  # 信頼できるIPはリスク軽減
                    result["factors"].append("信頼できるネットワークからのアクセス")
                    return result
        except:
            pass
        
        # 過去のIP履歴と比較
        recent_ips = [log.ip_address for log in recent_logs if log.ip_address]
        unique_ips = set(recent_ips)
        
        if ip_address not in unique_ips:
            result["score"] += 3
            result["factors"].append("新しいIPアドレスからのアクセス")
            
            # 同一日に複数の新しいIPからのアクセス
            today_new_ips = []
            today = datetime.utcnow().date()
            for log in recent_logs:
                if (log.created_at.date() == today and 
                    log.ip_address not in unique_ips and 
                    log.ip_address != ip_address):
                    today_new_ips.append(log.ip_address)
            
            if len(set(today_new_ips)) > 0:
                result["score"] += 2
                result["factors"].append("同日内の複数新規IPアクセス")
        
        return result

    def _analyze_time_pattern_risk(self, recent_logs: List[UserAccessLog]) -> Dict[str, any]:
        """時間パターンリスク分析"""
        result = {"score": 0, "factors": []}
        
        if not recent_logs:
            return result
        
        # 通常のログイン時間帯分析
        login_hours = [log.created_at.hour for log in recent_logs]
        current_hour = datetime.utcnow().hour
        
        # 深夜早朝（0-5時、22-23時）のアクセス
        if current_hour in [0, 1, 2, 3, 4, 5, 22, 23]:
            usual_night_logins = sum(1 for hour in login_hours if hour in [0, 1, 2, 3, 4, 5, 22, 23])
            if usual_night_logins < len(login_hours) * 0.1:  # 通常の10%未満の場合
                result["score"] += 2
                result["factors"].append("通常とは異なる時間帯のアクセス")
        
        return result

    def _analyze_device_risk(self, user_agent: str, recent_logs: List[UserAccessLog]) -> Dict[str, any]:
        """デバイス・ブラウザリスク分析"""
        result = {"score": 0, "factors": []}
        
        # 過去のUser-Agent履歴
        recent_agents = [log.user_agent for log in recent_logs if log.user_agent]
        
        if user_agent not in recent_agents:
            result["score"] += 2
            result["factors"].append("新しいデバイス・ブラウザからのアクセス")
        
        # 自動化ツール検知
        bot_indicators = ["bot", "crawler", "spider", "scraper", "automated"]
        if any(indicator in user_agent.lower() for indicator in bot_indicators):
            result["score"] += 5
            result["factors"].append("自動化ツールの可能性")
        
        return result

    def _analyze_login_frequency_risk(self, recent_logs: List[UserAccessLog]) -> Dict[str, any]:
        """ログイン頻度リスク分析"""
        result = {"score": 0, "factors": []}
        
        # 過去1時間のログイン試行数
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_attempts = [
            log for log in recent_logs 
            if log.created_at >= one_hour_ago
        ]
        
        if len(recent_attempts) > 10:
            result["score"] += 3
            result["factors"].append("短時間内の大量ログイン試行")
        
        return result

    # ===================
    # セキュリティ通知・アラート
    # ===================
    
    async def send_security_alert(self, user: User, alert_type: str, details: Dict[str, any]):
        """
        セキュリティアラート送信
        （実装では実際のメール送信・Slack通知等）
        """
        alert_messages = {
            "suspicious_login": f"不審なログイン試行が検出されました。IP: {details.get('ip_address')}",
            "password_changed": "パスワードが変更されました。",
            "mfa_enabled": "多要素認証が有効化されました。",
            "account_locked": f"アカウントがロックされました。理由: {details.get('reason')}",
            "new_device_login": f"新しいデバイスからのログインが検出されました。デバイス: {details.get('device_info')}"
        }
        
        message = alert_messages.get(alert_type, "セキュリティイベントが発生しました。")
        
        # ログ記録
        import logging
        logger = logging.getLogger("security")
        logger.info(f"Security alert sent to user {user.id}: {message}")
        
        # 実際の通知実装は環境に応じて
        # - メール送信
        # - Slack通知
        # - SMS送信
        # など

    # ===================
    # セキュリティ設定管理
    # ===================
    
    def get_security_recommendations(self, user: User, db: Session) -> List[Dict[str, any]]:
        """
        ユーザー向けセキュリティ推奨事項
        """
        recommendations = []
        
        # MFA未設定の場合
        if not user.mfa_enabled:
            recommendations.append({
                "priority": "high",
                "category": "authentication",
                "title": "多要素認証(MFA)を有効にする",
                "description": "アカウントセキュリティを大幅に向上させます",
                "action_url": "/security/mfa"
            })
        
        # パスワード更新期間チェック
        if user.updated_at and (datetime.utcnow() - user.updated_at).days > 90:
            recommendations.append({
                "priority": "medium",
                "category": "password",
                "title": "パスワードを更新する",
                "description": "90日以上パスワードが変更されていません",
                "action_url": "/security/password"
            })
        
        # セッション数チェック
        active_sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user.id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).count()
        
        if active_sessions > 5:
            recommendations.append({
                "priority": "medium",
                "category": "sessions",
                "title": "不要なセッションを削除する",
                "description": f"現在{active_sessions}個のセッションがアクティブです",
                "action_url": "/security/sessions"
            })
        
        return recommendations

# グローバルインスタンス
security_service = SecurityService()