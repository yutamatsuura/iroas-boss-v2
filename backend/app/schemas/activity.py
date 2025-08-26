"""
アクティビティログAPI スキーマ

Phase A-1c: アクティビティログAPI（6.1-6.3）
- システムで実行された全操作の履歴を時系列で記録
- フィルタリング機能（操作者、対象、期間等）
- 詳細表示機能

モックアップP-007対応
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from app.models.activity import ActivityType, ActivityLevel


class ActivityTypeEnum(str, Enum):
    """アクティビティ種別（APIスキーマ用）"""
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


class ActivityLevelEnum(str, Enum):
    """重要度レベル"""
    INFO = "情報"
    WARNING = "警告"
    ERROR = "エラー"
    CRITICAL = "重要"


class ActivityLogResponse(BaseModel):
    """
    アクティビティログレスポンススキーマ
    API 6.1, 6.3: ログ一覧・詳細用
    """
    id: int = Field(description="ログID")
    
    # 基本情報
    activity_type: ActivityTypeEnum = Field(description="アクティビティ種別")
    activity_level: ActivityLevelEnum = Field(description="重要度レベル")
    
    # 操作者情報
    user_id: Optional[str] = Field(description="操作者ID")
    user_name: Optional[str] = Field(description="操作者名")
    ip_address: Optional[str] = Field(description="IPアドレス")
    user_agent: Optional[str] = Field(description="ユーザーエージェント")
    
    # 操作対象
    target_type: Optional[str] = Field(description="対象種別")
    target_id: Optional[str] = Field(description="対象ID")
    target_name: Optional[str] = Field(description="対象名")
    
    # 操作内容
    description: str = Field(description="操作内容の説明")
    details: Optional[Dict[str, Any]] = Field(description="詳細データ")
    
    # 結果情報
    is_success: bool = Field(description="操作成功/失敗")
    error_message: Optional[str] = Field(description="エラーメッセージ")
    
    # システム情報
    created_at: datetime = Field(description="実行日時")
    session_id: Optional[str] = Field(description="セッションID")
    
    # 表示用プロパティ
    formatted_created_at: str = Field(description="フォーマット済み実行日時")
    level_badge_class: str = Field(description="レベル別バッジクラス")
    activity_icon: str = Field(description="アクティビティ種別アイコン")
    
    class Config:
        from_attributes = True


class ActivityLogSearch(BaseModel):
    """
    アクティビティログ検索リクエストスキーマ
    API 6.2: GET /api/activity/logs/filter
    """
    # 検索条件
    keyword: Optional[str] = Field(default=None, description="キーワード（説明、対象名等）")
    
    # フィルター条件
    activity_type: Optional[ActivityTypeEnum] = Field(default=None, description="アクティビティ種別")
    activity_level: Optional[ActivityLevelEnum] = Field(default=None, description="重要度レベル")
    user_name: Optional[str] = Field(default=None, description="操作者名")
    target_type: Optional[str] = Field(default=None, description="対象種別")
    target_id: Optional[str] = Field(default=None, description="対象ID")
    is_success: Optional[bool] = Field(default=None, description="成功/失敗")
    
    # 期間条件
    date_from: Optional[datetime] = Field(default=None, description="実行日時（開始）")
    date_to: Optional[datetime] = Field(default=None, description="実行日時（終了）")
    
    # ページング
    page: int = Field(default=1, ge=1, description="ページ番号")
    per_page: int = Field(default=50, ge=1, le=1000, description="1ページあたりの件数")
    
    # ソート
    sort_by: Optional[str] = Field(default="created_at", description="ソート項目")
    sort_order: Optional[str] = Field(default="desc", pattern=r'^(asc|desc)$', description="ソート順序")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('終了日時は開始日時より後である必要があります')
        return v


class ActivityLogSummary(BaseModel):
    """
    アクティビティログサマリーレスポンススキーマ
    ダッシュボード表示用
    """
    # 期間統計
    total_activities: int = Field(description="総アクティビティ数")
    today_activities: int = Field(description="今日のアクティビティ数")
    this_week_activities: int = Field(description="今週のアクティビティ数")
    this_month_activities: int = Field(description="今月のアクティビティ数")
    
    # レベル別統計
    info_count: int = Field(description="情報レベル数")
    warning_count: int = Field(description="警告レベル数")
    error_count: int = Field(description="エラーレベル数")
    critical_count: int = Field(description="重要レベル数")
    
    # 種別別統計
    member_activities: int = Field(description="会員管理系")
    payment_activities: int = Field(description="決済管理系")
    reward_activities: int = Field(description="報酬計算系")
    system_activities: int = Field(description="システム系")
    
    # 直近のアクティビティ
    recent_activities: List[ActivityLogResponse] = Field(description="直近のアクティビティ（最大10件）")
    
    # エラー・警告サマリー
    recent_errors: List[ActivityLogResponse] = Field(description="直近のエラー（最大5件）")
    recent_warnings: List[ActivityLogResponse] = Field(description="直近の警告（最大5件）")


class ActivityLogStats(BaseModel):
    """
    アクティビティログ統計レスポンススキーマ
    分析・監査用
    """
    # 期間別統計
    daily_stats: Dict[str, int] = Field(description="日別統計（過去30日）")
    hourly_stats: Dict[str, int] = Field(description="時間別統計（過去24時間）")
    
    # 種別別統計
    type_stats: Dict[str, int] = Field(description="種別別統計")
    level_stats: Dict[str, int] = Field(description="レベル別統計")
    
    # ユーザー別統計
    user_stats: Dict[str, int] = Field(description="ユーザー別統計")
    
    # 成功率統計
    success_rate: float = Field(description="全体成功率（%）")
    type_success_rates: Dict[str, float] = Field(description="種別別成功率（%）")
    
    # パフォーマンス指標
    peak_activity_hour: int = Field(description="最も活動が多い時間帯")
    avg_daily_activities: float = Field(description="1日平均アクティビティ数")
    
    # 期間情報
    stats_period_from: datetime = Field(description="統計期間開始")
    stats_period_to: datetime = Field(description="統計期間終了")


class ActivityLogExportRequest(BaseModel):
    """
    アクティビティログエクスポートリクエストスキーマ
    監査・分析用CSV出力
    """
    # エクスポート条件（ActivityLogSearchと同様）
    activity_type: Optional[ActivityTypeEnum] = Field(default=None, description="アクティビティ種別")
    activity_level: Optional[ActivityLevelEnum] = Field(default=None, description="重要度レベル")
    date_from: Optional[datetime] = Field(default=None, description="実行日時（開始）")
    date_to: Optional[datetime] = Field(default=None, description="実行日時（終了）")
    
    # エクスポート形式
    format: str = Field(default="csv", pattern=r'^(csv|excel)$', description="出力形式")
    include_details: bool = Field(default=False, description="詳細データを含めるか")
    encoding: str = Field(default="utf-8", pattern=r'^(utf-8|shift_jis)$', description="文字エンコーディング")
    
    # 制限
    max_records: int = Field(default=10000, ge=1, le=100000, description="最大出力件数")