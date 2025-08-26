"""
アクティビティログデータモデル

要件定義書のアクティビティログ要件に対応：
- システムで実行された全操作の履歴を時系列で記録
- フィルタリング機能（操作者、対象、期間等）
- 詳細表示機能
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, JSON, Boolean
from app.database import Base


class ActivityType(str, Enum):
    """アクティビティ種別"""
    # 会員管理
    MEMBER_CREATE = "会員新規登録"
    MEMBER_UPDATE = "会員情報更新"
    MEMBER_DELETE = "会員退会処理"
    MEMBER_SPONSOR_CHANGE = "スポンサー変更"
    
    # 決済管理
    PAYMENT_CSV_EXPORT = "決済CSV出力"
    PAYMENT_RESULT_IMPORT = "決済結果取込"
    PAYMENT_MANUAL_RECORD = "手動決済記録"
    
    # 報酬計算
    REWARD_CALCULATION_START = "報酬計算開始"
    REWARD_CALCULATION_COMPLETE = "報酬計算完了"
    REWARD_CALCULATION_FAILED = "報酬計算失敗"
    REWARD_CALCULATION_DELETE = "報酬計算削除"
    
    # 支払管理
    PAYOUT_GMO_CSV_EXPORT = "GMO CSV出力"
    PAYOUT_CONFIRM = "支払確定"
    PAYOUT_CARRYOVER = "繰越処理"
    
    # データ管理
    DATA_IMPORT = "データインポート"
    DATA_EXPORT = "データエクスポート"
    DATA_BACKUP = "バックアップ実行"
    DATA_RESTORE = "リストア実行"
    
    # システム
    SYSTEM_LOGIN = "ログイン"
    SYSTEM_LOGOUT = "ログアウト"
    SYSTEM_SETTING_UPDATE = "システム設定更新"


class ActivityLevel(str, Enum):
    """重要度レベル"""
    INFO = "情報"
    WARNING = "警告"
    ERROR = "エラー"
    CRITICAL = "重要"


class ActivityLog(Base):
    """
    アクティビティログテーブル
    システムの全操作履歴を記録
    """
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本情報
    activity_type = Column(SQLEnum(ActivityType), nullable=False, index=True, comment="アクティビティ種別")
    activity_level = Column(SQLEnum(ActivityLevel), nullable=False, default=ActivityLevel.INFO, comment="重要度レベル")
    
    # 操作者情報
    user_id = Column(String(100), nullable=True, comment="操作者ID（将来の認証対応）")
    user_name = Column(String(100), nullable=True, comment="操作者名")
    ip_address = Column(String(45), nullable=True, comment="IPアドレス")
    user_agent = Column(String(500), nullable=True, comment="ユーザーエージェント")
    
    # 操作対象
    target_type = Column(String(50), nullable=True, comment="対象種別（member, payment, reward等）")
    target_id = Column(String(100), nullable=True, index=True, comment="対象ID")
    target_name = Column(String(200), nullable=True, comment="対象名")
    
    # 操作内容
    description = Column(String(500), nullable=False, comment="操作内容の説明")
    details = Column(JSON, nullable=True, comment="詳細データ（JSON）")
    
    # 結果情報
    is_success = Column(Boolean, nullable=False, default=True, comment="操作成功/失敗")
    error_message = Column(Text, nullable=True, comment="エラーメッセージ")
    
    # システム情報
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True, comment="実行日時")
    session_id = Column(String(100), nullable=True, comment="セッションID")
    
    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, type={self.activity_type}, user={self.user_name})>"
    
    @property
    def formatted_created_at(self) -> str:
        """フォーマット済み実行日時"""
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def level_badge_class(self) -> str:
        """レベル別バッジクラス（UI用）"""
        class_map = {
            ActivityLevel.INFO: "status-info",
            ActivityLevel.WARNING: "status-warning", 
            ActivityLevel.ERROR: "status-error",
            ActivityLevel.CRITICAL: "status-critical"
        }
        return class_map.get(self.activity_level, "status-info")
    
    @property
    def activity_icon(self) -> str:
        """アクティビティ種別アイコン（UI用）"""
        icon_map = {
            # 会員管理
            ActivityType.MEMBER_CREATE: "person_add",
            ActivityType.MEMBER_UPDATE: "edit",
            ActivityType.MEMBER_DELETE: "person_remove", 
            ActivityType.MEMBER_SPONSOR_CHANGE: "swap_horiz",
            
            # 決済管理
            ActivityType.PAYMENT_CSV_EXPORT: "download",
            ActivityType.PAYMENT_RESULT_IMPORT: "upload",
            ActivityType.PAYMENT_MANUAL_RECORD: "edit",
            
            # 報酬計算
            ActivityType.REWARD_CALCULATION_START: "play_arrow",
            ActivityType.REWARD_CALCULATION_COMPLETE: "check_circle",
            ActivityType.REWARD_CALCULATION_FAILED: "error",
            ActivityType.REWARD_CALCULATION_DELETE: "delete",
            
            # 支払管理
            ActivityType.PAYOUT_GMO_CSV_EXPORT: "file_download",
            ActivityType.PAYOUT_CONFIRM: "verified",
            ActivityType.PAYOUT_CARRYOVER: "forward",
            
            # データ管理
            ActivityType.DATA_IMPORT: "cloud_upload",
            ActivityType.DATA_EXPORT: "cloud_download",
            ActivityType.DATA_BACKUP: "backup",
            ActivityType.DATA_RESTORE: "restore",
            
            # システム
            ActivityType.SYSTEM_LOGIN: "login",
            ActivityType.SYSTEM_LOGOUT: "logout",
            ActivityType.SYSTEM_SETTING_UPDATE: "settings",
        }
        return icon_map.get(self.activity_type, "info")
    
    def get_detail_value(self, key: str, default: Any = None) -> Any:
        """詳細データから値を取得"""
        if not self.details:
            return default
        return self.details.get(key, default)
    
    @classmethod
    def create_member_activity(cls, activity_type: ActivityType, member_number: str, member_name: str,
                              description: str, details: Dict[str, Any] = None, 
                              user_name: str = "system") -> 'ActivityLog':
        """会員関連アクティビティ作成"""
        return cls(
            activity_type=activity_type,
            user_name=user_name,
            target_type="member",
            target_id=member_number,
            target_name=member_name,
            description=description,
            details=details or {}
        )
    
    @classmethod
    def create_payment_activity(cls, activity_type: ActivityType, description: str,
                               target_count: int = None, details: Dict[str, Any] = None,
                               user_name: str = "system") -> 'ActivityLog':
        """決済関連アクティビティ作成"""
        return cls(
            activity_type=activity_type,
            user_name=user_name,
            target_type="payment",
            description=description,
            details=details or {"target_count": target_count} if target_count else details or {}
        )
    
    @classmethod
    def create_reward_activity(cls, activity_type: ActivityType, calculation_id: int, 
                              calculation_month: str, description: str,
                              details: Dict[str, Any] = None, user_name: str = "system",
                              level: ActivityLevel = ActivityLevel.INFO) -> 'ActivityLog':
        """報酬関連アクティビティ作成"""
        return cls(
            activity_type=activity_type,
            activity_level=level,
            user_name=user_name,
            target_type="reward_calculation",
            target_id=str(calculation_id),
            target_name=f"{calculation_month}月分報酬計算",
            description=description,
            details=details or {}
        )
    
    @classmethod
    def create_system_activity(cls, activity_type: ActivityType, description: str,
                              details: Dict[str, Any] = None, user_name: str = "system",
                              level: ActivityLevel = ActivityLevel.INFO) -> 'ActivityLog':
        """システム関連アクティビティ作成"""
        return cls(
            activity_type=activity_type,
            activity_level=level,
            user_name=user_name,
            target_type="system",
            description=description,
            details=details or {}
        )
    
    @classmethod
    def create_error_activity(cls, activity_type: ActivityType, error_message: str,
                             details: Dict[str, Any] = None, user_name: str = "system") -> 'ActivityLog':
        """エラーアクティビティ作成"""
        return cls(
            activity_type=activity_type,
            activity_level=ActivityLevel.ERROR,
            user_name=user_name,
            description=f"エラー発生: {error_message[:100]}",
            error_message=error_message,
            is_success=False,
            details=details or {}
        )