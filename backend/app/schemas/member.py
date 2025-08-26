"""
会員管理API スキーマ

Phase A-1b: 会員基本管理API（1.1-1.4, 1.6）
Phase B-1b: スポンサー変更API（1.5, 1.7）

モックアップP-002の30項目会員データに完全対応
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
from enum import Enum

from app.models.member import MemberStatus, Title, UserType, Plan, PaymentMethod, Gender, AccountType


class MemberStatusEnum(str, Enum):
    """会員ステータス（APIスキーマ用）"""
    ACTIVE = "アクティブ"
    INACTIVE = "休会中"
    WITHDRAWN = "退会済"


class TitleEnum(str, Enum):
    """称号（APIスキーマ用）"""
    NONE = "称号なし"
    KNIGHT_DAME = "ナイト/デイム"
    LORD_LADY = "ロード/レディ"
    KING_QUEEN = "キング/クイーン"
    EMPEROR_EMPRESS = "エンペラー/エンブレス"
    START = "スタート"
    LEADER = "リーダー"
    SUB_MANAGER = "サブマネージャー"
    MANAGER = "マネージャー"
    EXPERT_MANAGER = "エキスパートマネージャー"
    DIRECTOR = "ディレクター"
    AREA_DIRECTOR = "エリアディレクター"


class UserTypeEnum(str, Enum):
    """ユーザータイプ"""
    NORMAL = "通常"
    ATTENTION = "注意"


class PlanEnum(str, Enum):
    """加入プラン"""
    HERO = "ヒーロープラン"
    TEST = "テストプラン"


class PaymentMethodEnum(str, Enum):
    """決済方法"""
    CARD = "カード決済"
    TRANSFER = "口座振替"
    BANK = "銀行振込"
    INFOCART = "インフォカート"


class GenderEnum(str, Enum):
    """性別"""
    MALE = "男性"
    FEMALE = "女性"
    OTHER = "その他"


class AccountTypeEnum(str, Enum):
    """口座種別"""
    ORDINARY = "普通"
    CHECKING = "当座"


class MemberBase(BaseModel):
    """
    会員基本情報スキーマ
    作成・更新で共通利用
    """
    # 基本情報（1-5）
    status: MemberStatusEnum = Field(default=MemberStatusEnum.ACTIVE, description="1.ステータス")
    member_number: str = Field(..., min_length=7, max_length=7, pattern=r'^\d{7}$', description="2.IROAS会員番号（7桁数字）")
    name: str = Field(..., min_length=1, max_length=100, description="3.氏名")
    kana: str = Field(..., min_length=1, max_length=100, description="4.カナ")
    email: EmailStr = Field(..., description="5.メールアドレス")
    
    # MLM情報（6-9）
    title: TitleEnum = Field(default=TitleEnum.NONE, description="6.称号")
    user_type: UserTypeEnum = Field(default=UserTypeEnum.NORMAL, description="7.ユーザータイプ")
    plan: PlanEnum = Field(..., description="8.加入プラン")
    payment_method: PaymentMethodEnum = Field(..., description="9.決済方法")
    
    # 日付情報（10-11）
    registration_date: Optional[datetime] = Field(default=None, description="10.登録日")
    withdrawal_date: Optional[datetime] = Field(default=None, description="11.退会日")
    
    # 連絡先情報（12-17）
    phone: Optional[str] = Field(default=None, max_length=20, description="12.電話番号")
    gender: Optional[GenderEnum] = Field(default=None, description="13.性別")
    postal_code: Optional[str] = Field(default=None, max_length=8, pattern=r'^\d{3}-?\d{4}$', description="14.郵便番号")
    prefecture: Optional[str] = Field(default=None, max_length=10, description="15.都道府県")
    address2: Optional[str] = Field(default=None, max_length=200, description="16.住所2")
    address3: Optional[str] = Field(default=None, max_length=200, description="17.住所3")
    
    # 組織情報（18-21）
    upline_id: Optional[str] = Field(default=None, max_length=7, pattern=r'^\d{7}$', description="18.直上者ID")
    upline_name: Optional[str] = Field(default=None, max_length=100, description="19.直上者名")
    referrer_id: Optional[str] = Field(default=None, max_length=7, pattern=r'^\d{7}$', description="20.紹介者ID")
    referrer_name: Optional[str] = Field(default=None, max_length=100, description="21.紹介者名")
    
    # 銀行情報（22-29）
    bank_name: Optional[str] = Field(default=None, max_length=100, description="22.報酬振込先の銀行名")
    bank_code: Optional[str] = Field(default=None, max_length=4, pattern=r'^\d{4}$', description="23.報酬振込先の銀行コード")
    branch_name: Optional[str] = Field(default=None, max_length=100, description="24.報酬振込先の支店名")
    branch_code: Optional[str] = Field(default=None, max_length=3, pattern=r'^\d{3}$', description="25.報酬振込先の支店コード")
    account_number: Optional[str] = Field(default=None, max_length=10, pattern=r'^\d+$', description="26.口座番号")
    yucho_symbol: Optional[str] = Field(default=None, max_length=5, pattern=r'^\d{5}$', description="27.ゆうちょの場合の記号")
    yucho_number: Optional[str] = Field(default=None, max_length=8, pattern=r'^\d{1,8}$', description="28.ゆうちょの場合の番号")
    account_type: Optional[AccountTypeEnum] = Field(default=None, description="29.口座種別")
    
    # その他（30）
    notes: Optional[str] = Field(default=None, description="30.備考")


class MemberCreate(MemberBase):
    """
    会員新規登録リクエストスキーマ
    API 1.2: POST /api/members
    """
    pass


class MemberUpdate(BaseModel):
    """
    会員更新リクエストスキーマ
    API 1.4: PUT /api/members/{id}
    部分更新対応（Optional化）
    """
    # 基本情報（ステータスと会員番号は更新不可）
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="3.氏名")
    kana: Optional[str] = Field(default=None, min_length=1, max_length=100, description="4.カナ")
    email: Optional[EmailStr] = Field(default=None, description="5.メールアドレス")
    
    # MLM情報
    title: Optional[TitleEnum] = Field(default=None, description="6.称号")
    user_type: Optional[UserTypeEnum] = Field(default=None, description="7.ユーザータイプ")
    plan: Optional[PlanEnum] = Field(default=None, description="8.加入プラン")
    payment_method: Optional[PaymentMethodEnum] = Field(default=None, description="9.決済方法")
    
    # 日付情報（registration_dateは更新不可、withdrawal_dateは退会処理で自動設定）
    
    # 連絡先情報
    phone: Optional[str] = Field(default=None, max_length=20, description="12.電話番号")
    gender: Optional[GenderEnum] = Field(default=None, description="13.性別")
    postal_code: Optional[str] = Field(default=None, max_length=8, pattern=r'^\d{3}-?\d{4}$', description="14.郵便番号")
    prefecture: Optional[str] = Field(default=None, max_length=10, description="15.都道府県")
    address2: Optional[str] = Field(default=None, max_length=200, description="16.住所2")
    address3: Optional[str] = Field(default=None, max_length=200, description="17.住所3")
    
    # 組織情報（upline系は別APIで更新）
    referrer_id: Optional[str] = Field(default=None, max_length=7, pattern=r'^\d{7}$', description="20.紹介者ID")
    referrer_name: Optional[str] = Field(default=None, max_length=100, description="21.紹介者名")
    
    # 銀行情報
    bank_name: Optional[str] = Field(default=None, max_length=100, description="22.報酬振込先の銀行名")
    bank_code: Optional[str] = Field(default=None, max_length=4, pattern=r'^\d{4}$', description="23.報酬振込先の銀行コード")
    branch_name: Optional[str] = Field(default=None, max_length=100, description="24.報酬振込先の支店名")
    branch_code: Optional[str] = Field(default=None, max_length=3, pattern=r'^\d{3}$', description="25.報酬振込先の支店コード")
    account_number: Optional[str] = Field(default=None, max_length=10, pattern=r'^\d+$', description="26.口座番号")
    yucho_symbol: Optional[str] = Field(default=None, max_length=5, pattern=r'^\d{5}$', description="27.ゆうちょの場合の記号")
    yucho_number: Optional[str] = Field(default=None, max_length=8, pattern=r'^\d{1,8}$', description="28.ゆうちょの場合の番号")
    account_type: Optional[AccountTypeEnum] = Field(default=None, description="29.口座種別")
    
    # その他
    notes: Optional[str] = Field(default=None, description="30.備考")


class MemberResponse(MemberBase):
    """
    会員レスポンススキーマ
    API 1.1, 1.3: 会員情報返却用
    """
    id: int = Field(description="内部ID")
    created_at: datetime = Field(description="作成日時")
    updated_at: datetime = Field(description="更新日時")
    
    # 計算プロパティ
    is_active: bool = Field(description="アクティブ状態フラグ")
    plan_amount: int = Field(description="プラン金額")
    display_name: str = Field(description="表示用氏名（会員番号 - 氏名）")
    
    class Config:
        from_attributes = True


class MemberListItem(BaseModel):
    """
    会員一覧項目スキーマ
    API 1.1: GET /api/members（一覧表示用）
    """
    id: int = Field(description="内部ID")
    member_number: str = Field(description="会員番号")
    name: str = Field(description="氏名")
    email: str = Field(description="メールアドレス")
    status: MemberStatusEnum = Field(description="ステータス")
    title: TitleEnum = Field(description="称号")
    plan: PlanEnum = Field(description="加入プラン")
    payment_method: PaymentMethodEnum = Field(description="決済方法")
    registration_date: datetime = Field(description="登録日")
    upline_name: Optional[str] = Field(description="直上者名")
    
    # 計算プロパティ
    is_active: bool = Field(description="アクティブ状態フラグ")
    display_name: str = Field(description="表示用氏名")
    
    class Config:
        from_attributes = True


class MemberList(BaseModel):
    """
    会員一覧レスポンススキーマ
    API 1.1: GET /api/members
    """
    members: List[MemberListItem] = Field(description="会員リスト")
    total_count: int = Field(description="総件数")
    active_count: int = Field(description="アクティブ会員数")
    inactive_count: int = Field(description="休会中会員数")
    withdrawn_count: int = Field(description="退会済み会員数")


class MemberSearch(BaseModel):
    """
    会員検索リクエストスキーマ
    API 1.6: GET /api/members/search
    """
    # 検索条件
    keyword: Optional[str] = Field(default=None, description="キーワード（会員番号、氏名、メールアドレス）")
    member_number: Optional[str] = Field(default=None, max_length=7, description="会員番号")
    name: Optional[str] = Field(default=None, max_length=100, description="氏名（部分一致）")
    email: Optional[str] = Field(default=None, description="メールアドレス（部分一致）")
    
    # フィルター条件
    status: Optional[MemberStatusEnum] = Field(default=None, description="ステータス")
    title: Optional[TitleEnum] = Field(default=None, description="称号")
    plan: Optional[PlanEnum] = Field(default=None, description="加入プラン")
    payment_method: Optional[PaymentMethodEnum] = Field(default=None, description="決済方法")
    
    # 期間条件
    registration_date_from: Optional[datetime] = Field(default=None, description="登録日（開始）")
    registration_date_to: Optional[datetime] = Field(default=None, description="登録日（終了）")
    
    # ページング
    page: int = Field(default=1, ge=1, description="ページ番号")
    per_page: int = Field(default=20, ge=1, le=100, description="1ページあたりの件数")
    
    # ソート
    sort_by: Optional[str] = Field(default="member_number", description="ソート項目")
    sort_order: Optional[str] = Field(default="asc", pattern=r'^(asc|desc)$', description="ソート順序")


class SponsorChangeRequest(BaseModel):
    """
    スポンサー変更リクエストスキーマ
    API 1.7: PUT /api/members/{id}/sponsor
    """
    new_sponsor_id: str = Field(..., max_length=7, pattern=r'^\d{7}$', description="新しいスポンサーの会員番号")
    reason: Optional[str] = Field(default=None, max_length=500, description="変更理由")
    
    @validator('new_sponsor_id')
    def validate_sponsor_id(cls, v):
        if len(v) != 7 or not v.isdigit():
            raise ValueError('スポンサーIDは7桁の数字である必要があります')
        return v


class MemberWithdrawRequest(BaseModel):
    """
    会員退会リクエストスキーマ  
    API 1.5: DELETE /api/members/{id}
    """
    reason: Optional[str] = Field(default=None, max_length=500, description="退会理由")
    withdrawal_date: Optional[datetime] = Field(default=None, description="退会日（未指定時は現在日時）")