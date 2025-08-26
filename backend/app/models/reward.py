"""
報酬計算データモデル

要件定義書の7種類のボーナス計算に対応：
1. デイリーボーナス - 参加費に応じた日割り報酬  
2. タイトルボーナス - タイトルに応じた固定報酬
3. リファラルボーナス - 直紹介者の参加費の50%
4. パワーボーナス - 組織売上に応じた報酬
5. メンテナンスボーナス - センターメンテナンスキット販売報酬
6. セールスアクティビティボーナス - 新規紹介活動報酬  
7. ロイヤルファミリーボーナス - 最高タイトル保持者への特別報酬

支払いルール：
- 最低支払金額: 5,000円（未満は翌月繰越）
- 振込手数料: 会社負担
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class BonusType(str, Enum):
    """ボーナス種別（7種類）"""
    DAILY = "デイリーボーナス"
    TITLE = "タイトルボーナス"
    REFERRAL = "リファラルボーナス"
    POWER = "パワーボーナス"
    MAINTENANCE = "メンテナンスボーナス"
    SALES_ACTIVITY = "セールスアクティビティボーナス"
    ROYAL_FAMILY = "ロイヤルファミリーボーナス"


class CalculationStatus(str, Enum):
    """計算ステータス"""
    RUNNING = "実行中"
    COMPLETED = "完了"
    FAILED = "失敗"
    CANCELLED = "キャンセル"


class PaymentStatus(str, Enum):
    """支払ステータス"""
    PENDING = "支払待ち"
    PAID = "支払済み"
    CARRYOVER = "繰越"
    CANCELLED = "キャンセル"


class RewardCalculation(Base):
    """
    報酬計算実行履歴テーブル
    月次計算の管理と結果サマリーを保存
    """
    __tablename__ = "reward_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 計算情報
    calculation_month = Column(String(7), nullable=False, index=True, comment="計算対象月（YYYY-MM）")
    calculation_type = Column(String(20), nullable=False, default="all", comment="計算タイプ（all/partial/recalculation）")
    status = Column(SQLEnum(CalculationStatus), nullable=False, default=CalculationStatus.RUNNING, comment="計算ステータス")
    
    # 実行結果サマリー
    total_amount = Column(Numeric(10, 0), nullable=True, comment="総支払額")
    target_member_count = Column(Integer, nullable=True, comment="支払対象者数")
    carryover_member_count = Column(Integer, nullable=True, comment="繰越対象者数（5,000円未満）")
    execution_time_seconds = Column(Numeric(5, 2), nullable=True, comment="実行時間（秒）")
    
    # ボーナス別サマリー（JSON）
    bonus_summary = Column(JSON, nullable=True, comment="ボーナス別集計結果")
    
    # エラー情報
    error_message = Column(Text, nullable=True, comment="エラーメッセージ")
    
    # システム情報
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="計算開始日時")
    completed_at = Column(DateTime, nullable=True, comment="計算完了日時")
    is_deleted = Column(Boolean, default=False, comment="論理削除フラグ")
    
    # リレーション
    reward_histories = relationship("RewardHistory", back_populates="calculation", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<RewardCalculation(id={self.id}, month={self.calculation_month}, status={self.status})>"
    
    @property
    def is_completed(self) -> bool:
        """計算完了かどうか"""
        return self.status == CalculationStatus.COMPLETED
    
    @property
    def formatted_total_amount(self) -> str:
        """フォーマット済み総額"""
        return f"¥{self.total_amount:,}" if self.total_amount else "¥0"
    
    def get_bonus_amount(self, bonus_type: BonusType) -> Decimal:
        """指定ボーナス種別の合計額を取得"""
        if not self.bonus_summary:
            return Decimal('0')
        return Decimal(str(self.bonus_summary.get(bonus_type.value, 0)))
    
    def set_completed(self, total_amount: Decimal, target_count: int, carryover_count: int, 
                     execution_time: float, bonus_summary: Dict[str, Any]) -> None:
        """計算完了状態に設定"""
        self.status = CalculationStatus.COMPLETED
        self.total_amount = total_amount
        self.target_member_count = target_count
        self.carryover_member_count = carryover_count
        self.execution_time_seconds = Decimal(str(execution_time))
        self.bonus_summary = bonus_summary
        self.completed_at = datetime.utcnow()
    
    def set_failed(self, error_message: str) -> None:
        """計算失敗状態に設定"""
        self.status = CalculationStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()


class RewardHistory(Base):
    """
    報酬履歴テーブル
    個人別・ボーナス種別の詳細記録
    """
    __tablename__ = "reward_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 計算・会員情報
    calculation_id = Column(Integer, ForeignKey("reward_calculations.id"), nullable=False, comment="計算ID")
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, comment="会員ID")
    member_number = Column(String(7), nullable=False, index=True, comment="会員番号")
    
    # ボーナス情報
    bonus_type = Column(SQLEnum(BonusType), nullable=False, comment="ボーナス種別")
    bonus_amount = Column(Numeric(10, 0), nullable=False, default=0, comment="ボーナス金額")
    
    # 計算詳細（JSON）
    calculation_details = Column(JSON, nullable=True, comment="計算詳細データ")
    
    # 支払情報
    payment_status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, comment="支払ステータス")
    payment_date = Column(DateTime, nullable=True, comment="支払日")
    
    # システム情報
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, comment="論理削除フラグ")
    
    # リレーション
    calculation = relationship("RewardCalculation", back_populates="reward_histories")
    member = relationship("Member", back_populates="reward_histories")
    
    def __repr__(self) -> str:
        return f"<RewardHistory(member_number={self.member_number}, bonus_type={self.bonus_type}, amount={self.bonus_amount})>"
    
    @property
    def formatted_amount(self) -> str:
        """フォーマット済み金額"""
        return f"¥{self.bonus_amount:,}"
    
    @property
    def is_payable(self) -> bool:
        """支払対象かどうか（5,000円以上）"""
        return self.bonus_amount >= 5000
    
    def get_calculation_description(self) -> str:
        """計算詳細の文字列表現"""
        if not self.calculation_details:
            return "計算詳細なし"
            
        details = self.calculation_details
        
        if self.bonus_type == BonusType.DAILY:
            days = details.get('days', 0)
            daily_rate = details.get('daily_rate', 0)
            return f"{days}日 × {daily_rate}円"
            
        elif self.bonus_type == BonusType.TITLE:
            title = details.get('title', '')
            return f"{title}称号"
            
        elif self.bonus_type == BonusType.REFERRAL:
            referral_count = details.get('referral_count', 0)
            referral_amount = details.get('referral_amount', 0)
            return f"直紹介{referral_count}名 × {referral_amount}円"
            
        elif self.bonus_type == BonusType.POWER:
            organization_sales = details.get('organization_sales', 0)
            rate = details.get('rate', 0)
            return f"組織売上: {organization_sales:,}円 × {rate}%"
            
        elif self.bonus_type == BonusType.MAINTENANCE:
            months = details.get('continuous_months', 0)
            return f"継続{months}ヶ月"
            
        else:
            return str(details)
    
    @classmethod
    def create_daily_bonus(cls, calculation_id: int, member_id: int, member_number: str,
                          days: int, daily_rate: Decimal) -> 'RewardHistory':
        """デイリーボーナス作成"""
        amount = days * daily_rate
        return cls(
            calculation_id=calculation_id,
            member_id=member_id,
            member_number=member_number,
            bonus_type=BonusType.DAILY,
            bonus_amount=amount,
            calculation_details={
                'days': days,
                'daily_rate': float(daily_rate),
                'calculation': f"{days}日 × {daily_rate}円"
            }
        )
    
    @classmethod
    def create_title_bonus(cls, calculation_id: int, member_id: int, member_number: str,
                          title: str, title_amount: Decimal) -> 'RewardHistory':
        """タイトルボーナス作成"""
        return cls(
            calculation_id=calculation_id,
            member_id=member_id,
            member_number=member_number,
            bonus_type=BonusType.TITLE,
            bonus_amount=title_amount,
            calculation_details={
                'title': title,
                'title_amount': float(title_amount)
            }
        )
    
    @classmethod
    def create_referral_bonus(cls, calculation_id: int, member_id: int, member_number: str,
                             referral_count: int, referral_amount: Decimal) -> 'RewardHistory':
        """リファラルボーナス作成"""
        return cls(
            calculation_id=calculation_id,
            member_id=member_id,
            member_number=member_number,
            bonus_type=BonusType.REFERRAL,
            bonus_amount=referral_count * referral_amount,
            calculation_details={
                'referral_count': referral_count,
                'referral_amount': float(referral_amount),
                'total_amount': float(referral_count * referral_amount)
            }
        )