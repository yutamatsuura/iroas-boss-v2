"""
設定管理API スキーマ

Phase A-1a: 基本設定API（7.1-7.2）
- システム設定・ビジネスルール表示専用
- 要件定義書：「システム固定値の確認表示のみ（変更不可）」

モックアップP-008対応
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SettingCategoryEnum(str, Enum):
    """設定カテゴリ"""
    BUSINESS_RULES = "ビジネスルール"
    PAYMENT_SETTINGS = "決済設定"
    REWARD_SETTINGS = "報酬設定"
    SYSTEM_SETTINGS = "システム設定"


class SettingTypeEnum(str, Enum):
    """設定値タイプ"""
    STRING = "文字列"
    INTEGER = "整数"
    DECIMAL = "小数"
    BOOLEAN = "真偽値"
    JSON = "JSON"


class SystemSettingResponse(BaseModel):
    """
    システム設定レスポンススキーマ
    API 7.1: GET /api/settings/system
    """
    key: str = Field(description="設定キー")
    category: SettingCategoryEnum = Field(description="カテゴリ")
    setting_type: SettingTypeEnum = Field(description="設定値タイプ")
    value: Union[str, int, float, bool, Dict[str, Any]] = Field(description="設定値")
    formatted_value: str = Field(description="フォーマット済み表示値")
    display_name: str = Field(description="表示名")
    description: Optional[str] = Field(description="説明")
    unit: Optional[str] = Field(description="単位")
    is_editable: bool = Field(default=False, description="編集可能フラグ（常にFalse）")
    sort_order: int = Field(description="表示順序")
    updated_at: datetime = Field(description="更新日時")
    
    class Config:
        from_attributes = True


class BusinessRuleResponse(BaseModel):
    """
    ビジネスルール詳細レスポンススキーマ
    API 7.2: GET /api/settings/business-rules
    要件定義書の固定値を構造化して返却
    """
    
    # プラン関連
    plan_settings: Dict[str, Any] = Field(description="プラン設定")
    
    # 決済関連
    payment_settings: Dict[str, Any] = Field(description="決済設定")
    
    # 報酬計算関連
    reward_settings: Dict[str, Any] = Field(description="報酬設定")
    
    # タイトル関連
    title_settings: Dict[str, Any] = Field(description="タイトル設定")
    
    # システム制限
    system_limits: Dict[str, Any] = Field(description="システム制限")
    
    @classmethod
    def create_default(cls) -> "BusinessRuleResponse":
        """
        デフォルトビジネスルール生成
        要件定義書の固定値に基づく
        """
        return cls(
            plan_settings={
                "hero_plan": {
                    "name": "ヒーロープラン",
                    "amount": 10670,
                    "daily_bonus_rate": 150,
                    "description": "メインプラン"
                },
                "test_plan": {
                    "name": "テストプラン", 
                    "amount": 9800,
                    "daily_bonus_rate": 130,
                    "description": "テスト用プラン"
                }
            },
            payment_settings={
                "methods": [
                    {"code": "card", "name": "カード決済", "provider": "Univapay"},
                    {"code": "transfer", "name": "口座振替", "provider": "Univapay"},
                    {"code": "bank", "name": "銀行振込", "provider": "手動"},
                    {"code": "infocart", "name": "インフォカート", "provider": "手動"}
                ],
                "periods": {
                    "card_export": "月初1-5日",
                    "transfer_export": "月初-12日",
                    "transfer_execution": "27日"
                }
            },
            reward_settings={
                "calculation_day": 25,
                "min_payout_amount": 5000,
                "bonus_types": [
                    {"code": "daily", "name": "デイリーボーナス", "description": "参加費に応じた日割り報酬"},
                    {"code": "title", "name": "タイトルボーナス", "description": "タイトルに応じた固定報酬"},
                    {"code": "referral", "name": "リファラルボーナス", "description": "直紹介者の参加費の50%"},
                    {"code": "power", "name": "パワーボーナス", "description": "組織売上に応じた報酬"},
                    {"code": "maintenance", "name": "メンテナンスボーナス", "description": "センターメンテナンスキット販売報酬"},
                    {"code": "sales_activity", "name": "セールスアクティビティボーナス", "description": "新規紹介活動報酬"},
                    {"code": "royal_family", "name": "ロイヤルファミリーボーナス", "description": "最高タイトル保持者への特別報酬"}
                ],
                "referral_bonus_rate": 50,
                "power_bonus_rate": 3
            },
            title_settings={
                "hierarchy": [
                    {"level": 0, "code": "none", "name": "称号なし", "bonus_amount": 0},
                    {"level": 1, "code": "start", "name": "スタート", "bonus_amount": 0},
                    {"level": 2, "code": "leader", "name": "リーダー", "bonus_amount": 0},
                    {"level": 3, "code": "sub_manager", "name": "サブマネージャー", "bonus_amount": 0},
                    {"level": 4, "code": "manager", "name": "マネージャー", "bonus_amount": 0},
                    {"level": 5, "code": "expert_manager", "name": "エキスパートマネージャー", "bonus_amount": 0},
                    {"level": 6, "code": "director", "name": "ディレクター", "bonus_amount": 0},
                    {"level": 7, "code": "area_director", "name": "エリアディレクター", "bonus_amount": 0}
                ],
                "special_titles": [
                    {"code": "knight_dame", "name": "ナイト/デイム", "bonus_amount": 2500},
                    {"code": "lord_lady", "name": "ロード/レディ", "bonus_amount": 5000},
                    {"code": "king_queen", "name": "キング/クイーン", "bonus_amount": 10000},
                    {"code": "emperor_empress", "name": "エンペラー/エンブレス", "bonus_amount": 20000}
                ]
            },
            system_limits={
                "max_member_count": 50,
                "new_registration_allowed": False,
                "csv_encoding": "shift_jis",
                "organization_compression": "manual",
                "version": "2.0.0"
            }
        )


class SystemSettingList(BaseModel):
    """
    システム設定一覧レスポンススキーマ  
    API 7.1: GET /api/settings/system（カテゴリ別グループ化）
    """
    business_rules: List[SystemSettingResponse] = Field(description="ビジネスルール設定")
    payment_settings: List[SystemSettingResponse] = Field(description="決済設定")
    reward_settings: List[SystemSettingResponse] = Field(description="報酬設定")
    system_settings: List[SystemSettingResponse] = Field(description="システム設定")
    
    total_count: int = Field(description="設定総数")
    editable_count: int = Field(default=0, description="編集可能設定数（常に0）")
    last_updated: Optional[datetime] = Field(description="最終更新日時")


class SettingValidationInfo(BaseModel):
    """
    設定値検証情報
    UI表示用の制約情報
    """
    required: bool = Field(description="必須フラグ")
    min_value: Optional[Union[int, float]] = Field(description="最小値")
    max_value: Optional[Union[int, float]] = Field(description="最大値")
    min_length: Optional[int] = Field(description="最小文字数")
    max_length: Optional[int] = Field(description="最大文字数")
    pattern: Optional[str] = Field(description="正規表現パターン")
    enum_values: Optional[List[str]] = Field(description="選択肢リスト")


class SystemHealthResponse(BaseModel):
    """
    システム稼働状況レスポンススキーマ
    ダッシュボード表示用
    """
    system_name: str = Field(description="システム名")
    version: str = Field(description="バージョン")
    status: str = Field(description="稼働状況")
    uptime_seconds: int = Field(description="稼働時間（秒）")
    database_status: str = Field(description="データベース接続状況")
    last_backup: Optional[datetime] = Field(description="最終バックアップ日時")
    
    # システム統計
    total_members: int = Field(description="総会員数")
    active_members: int = Field(description="アクティブ会員数")
    last_calculation: Optional[datetime] = Field(description="最終報酬計算日時")
    last_payment: Optional[datetime] = Field(description="最終支払処理日時")
    
    # 警告・注意事項
    warnings: List[str] = Field(default_factory=list, description="警告メッセージリスト")
    notices: List[str] = Field(default_factory=list, description="お知らせリスト")