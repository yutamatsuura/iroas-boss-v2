"""
会員データモデル

要件定義書の会員マスタ項目（30項目）を完全実装：
1. ステータス 2. IROAS会員番号 3. 氏名 4. カナ 5. メールアドレス
6. 称号 7. ユーザータイプ 8. 加入プラン 9. 決済方法 10. 登録日
11. 退会日 12. 電話番号 13. 性別 14. 郵便番号 15. 都道府県
16. 住所2 17. 住所3 18. 直上者ID 19. 直上者名 20. 紹介者ID
21. 紹介者名 22. 銀行名 23. 銀行コード 24. 支店名 25. 支店コード
26. 口座番号 27. ゆうちょ記号 28. ゆうちょ番号 29. 口座種別 30. 備考
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class MemberStatus(str, Enum):
    """会員ステータス"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    WITHDRAWN = "WITHDRAWN"


class Title(str, Enum):
    """称号（MLMタイトル体系）"""
    NONE = "NONE"
    KNIGHT_DAME = "KNIGHT_DAME"
    LORD_LADY = "LORD_LADY"
    KING_QUEEN = "KING_QUEEN"
    EMPEROR_EMPRESS = "EMPEROR_EMPRESS"


class UserType(str, Enum):
    """ユーザータイプ"""
    NORMAL = "NORMAL"
    ATTENTION = "ATTENTION"


class Plan(str, Enum):
    """加入プラン"""
    HERO = "HERO"
    TEST = "TEST"


class PaymentMethod(str, Enum):
    """決済方法（4種類）"""
    CARD = "CARD"
    TRANSFER = "TRANSFER"
    BANK = "BANK"
    INFOCART = "INFOCART"


class Gender(str, Enum):
    """性別"""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class AccountType(str, Enum):
    """口座種別"""
    ORDINARY = "ORDINARY"
    CHECKING = "CHECKING"


class Member(Base):
    """
    会員マスタテーブル
    要件定義書の30項目を完全再現
    """
    __tablename__ = "members"
    
    # 基本情報（1-5）
    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLEnum(MemberStatus), nullable=False, default=MemberStatus.ACTIVE, comment="1.ステータス")
    member_number = Column(String(11), unique=True, nullable=False, index=True, comment="2.IROAS会員番号（11桁）")
    name = Column(String(100), nullable=False, comment="3.氏名")
    kana = Column(String(100), nullable=True, comment="4.カナ（廃止予定）")
    email = Column(String(255), nullable=False, unique=True, index=True, comment="5.メールアドレス")
    
    # MLM情報（6-9）
    title = Column(SQLEnum(Title), nullable=False, default=Title.NONE, comment="6.称号")
    user_type = Column(SQLEnum(UserType), nullable=False, default=UserType.NORMAL, comment="7.ユーザータイプ")
    plan = Column(SQLEnum(Plan), nullable=False, comment="8.加入プラン")
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False, comment="9.決済方法")
    
    # 日付情報（10-11）
    registration_date = Column(String(50), nullable=True, comment="10.登録日（任意形式）")
    withdrawal_date = Column(String(50), nullable=True, comment="11.退会日（任意形式）")
    
    # 連絡先情報（12-17）
    phone = Column(String(20), nullable=True, comment="12.電話番号")
    gender = Column(SQLEnum(Gender), nullable=True, comment="13.性別")
    postal_code = Column(String(8), nullable=True, comment="14.郵便番号")
    prefecture = Column(String(10), nullable=True, comment="15.都道府県")
    address2 = Column(String(200), nullable=True, comment="16.住所2")
    address3 = Column(String(200), nullable=True, comment="17.住所3")
    
    # 組織情報（18-21）
    upline_id = Column(String(11), nullable=True, comment="18.直上者ID")
    upline_name = Column(String(100), nullable=True, comment="19.直上者名")
    referrer_id = Column(String(11), nullable=True, comment="20.紹介者ID") 
    referrer_name = Column(String(100), nullable=True, comment="21.紹介者名")
    
    # 銀行情報（22-29）
    bank_name = Column(String(100), nullable=True, comment="22.報酬振込先の銀行名")
    bank_code = Column(String(4), nullable=True, comment="23.報酬振込先の銀行コード")
    branch_name = Column(String(100), nullable=True, comment="24.報酬振込先の支店名") 
    branch_code = Column(String(3), nullable=True, comment="25.報酬振込先の支店コード")
    account_number = Column(String(10), nullable=True, comment="26.口座番号")
    yucho_symbol = Column(String(5), nullable=True, comment="27.ゆうちょの場合の記号")
    yucho_number = Column(String(8), nullable=True, comment="28.ゆうちょの場合の番号")
    account_type = Column(SQLEnum(AccountType), nullable=True, comment="29.口座種別")
    
    # その他（30）
    notes = Column(Text, nullable=True, comment="30.備考")
    
    # システム情報
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, comment="論理削除フラグ")
    
    # リレーション（外部キー制約を削除し、アプリケーションレベルで管理）
    # upline = relationship("Member", remote_side=[member_number], foreign_keys=[upline_id], backref="downlines")
    # referrer = relationship("Member", remote_side=[member_number], foreign_keys=[referrer_id], backref="referrals")
    
    # 決済履歴
    payment_histories = relationship("PaymentHistory", back_populates="member", cascade="all, delete-orphan")
    
    # 報酬履歴
    reward_histories = relationship("RewardHistory", back_populates="member", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Member(member_number={self.member_number}, name={self.name}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """アクティブ会員かどうか"""
        return self.status == MemberStatus.ACTIVE
    
    @property 
    def plan_amount(self) -> int:
        """プラン料金"""
        return 10670 if self.plan == Plan.HERO else 9800
    
    @property
    def display_name(self) -> str:
        """表示用氏名（会員番号付き）"""
        return f"{self.member_number} - {self.name}"
    
    def get_display_name(self) -> str:
        """表示用氏名（会員番号付き）- 後方互換性のため"""
        return self.display_name
    
    def can_withdraw(self) -> bool:
        """退会可能かどうか"""
        return self.status != MemberStatus.WITHDRAWN
    
    def set_withdrawn(self) -> None:
        """退会処理"""
        self.status = MemberStatus.WITHDRAWN
        from datetime import datetime
        self.withdrawal_date = datetime.now().strftime("%Y-%m-%d")
    
    def get_bank_info_dict(self) -> dict:
        """GMOネットバンク用の銀行情報を辞書で返す"""
        return {
            "bank_code": self.bank_code,
            "branch_code": self.branch_code,
            "account_type": "1" if self.account_type == AccountType.ORDINARY else "2",
            "account_number": self.account_number,
            "account_holder_kana": self.kana,
            "yucho_symbol": self.yucho_symbol,
            "yucho_number": self.yucho_number,
        }