"""
決済データモデル

要件定義書の決済方法（4種類）と決済結果CSV形式に対応：
- カード決済（Univapay）
- 口座振替（Univapay）
- 銀行振込（手動）
- インフォカート（手動）

決済結果CSV形式：
- カード決済：IPScardresult_YYYYMMDD.csv
- 口座振替：XXXXXX_TrnsCSV_YYYYMMDDHHMMSS.csv
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentStatus(str, Enum):
    """決済ステータス"""
    SUCCESS = "成功"
    FAILED = "失敗"
    PENDING = "保留"
    CANCELLED = "キャンセル"


class PaymentType(str, Enum):
    """決済種別"""
    CARD = "カード決済"
    TRANSFER = "口座振替"
    BANK = "銀行振込"
    INFOCART = "インフォカート"


class PaymentHistory(Base):
    """
    決済履歴テーブル
    Univapay連携 + 手動記録の両方に対応
    """
    __tablename__ = "payment_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 会員情報
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, comment="会員ID")
    member_number = Column(String(7), nullable=False, index=True, comment="会員番号")
    
    # 決済情報
    payment_date = Column(DateTime, nullable=False, comment="決済日")
    payment_type = Column(SQLEnum(PaymentType), nullable=False, comment="決済種別")
    payment_method = Column(String(50), nullable=False, comment="決済方法")
    amount = Column(Numeric(10, 0), nullable=False, comment="決済金額")
    
    # ステータス
    status = Column(SQLEnum(PaymentStatus), nullable=False, comment="決済ステータス")
    
    # 外部システム連携
    transaction_id = Column(String(100), nullable=True, unique=True, index=True, comment="取引ID")
    external_order_id = Column(String(100), nullable=True, comment="外部オーダー番号（Univapay等）")
    
    # エラー情報
    error_code = Column(String(20), nullable=True, comment="エラーコード")
    error_message = Column(String(500), nullable=True, comment="エラーメッセージ")
    
    # CSV処理情報
    csv_filename = Column(String(200), nullable=True, comment="処理元CSVファイル名")
    csv_row_number = Column(Integer, nullable=True, comment="CSV行番号")
    
    # その他
    notes = Column(Text, nullable=True, comment="備考・メモ")
    
    # 手動記録情報
    recorded_by = Column(String(100), nullable=True, comment="記録者（手動記録の場合）")
    recorded_at = Column(DateTime, nullable=True, comment="記録日時（手動記録の場合）")
    
    # システム情報
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, comment="論理削除フラグ")
    
    # リレーション
    member = relationship("Member", back_populates="payment_histories")
    
    def __repr__(self) -> str:
        return f"<PaymentHistory(member_number={self.member_number}, amount={self.amount}, status={self.status})>"
    
    @property
    def is_successful(self) -> bool:
        """決済成功かどうか"""
        return self.status == PaymentStatus.SUCCESS
    
    @property
    def is_univapay_payment(self) -> bool:
        """Univapay決済かどうか"""
        return self.payment_type in [PaymentType.CARD, PaymentType.TRANSFER]
    
    @property
    def is_manual_payment(self) -> bool:
        """手動記録かどうか"""
        return self.payment_type in [PaymentType.BANK, PaymentType.INFOCART]
    
    @property
    def formatted_amount(self) -> str:
        """フォーマット済み金額"""
        return f"¥{self.amount:,}"
    
    def get_payment_icon(self) -> str:
        """決済方法アイコン（UI用）"""
        icon_map = {
            PaymentType.CARD: "credit_card",
            PaymentType.TRANSFER: "account_balance",
            PaymentType.BANK: "account_balance",
            PaymentType.INFOCART: "shopping_cart",
        }
        return icon_map.get(self.payment_type, "payment")
    
    def to_univapay_card_csv_row(self) -> dict:
        """Univapayカード決済CSV用データ"""
        return {
            "顧客オーダー番号": self.member_number,
            "金額": int(self.amount),
            "決済結果": "OK" if self.is_successful else "NG"
        }
    
    def to_univapay_transfer_csv_row(self) -> dict:
        """Univapay口座振替CSV用データ"""
        return {
            "顧客番号": self.member_number,
            "振替日": self.payment_date.strftime("%Y%m%d"),
            "金額": int(self.amount),
            "エラー情報": self.error_message or ""
        }
    
    @classmethod
    def create_from_card_csv(cls, csv_row: dict, member_id: int, csv_filename: str, row_number: int):
        """カード決済CSV結果からインスタンス作成"""
        return cls(
            member_id=member_id,
            member_number=csv_row.get("顧客オーダー番号"),
            payment_date=datetime.utcnow(),  # CSV処理日
            payment_type=PaymentType.CARD,
            payment_method="カード決済",
            amount=Decimal(str(csv_row.get("金額", 0))),
            status=PaymentStatus.SUCCESS if csv_row.get("決済結果") == "OK" else PaymentStatus.FAILED,
            external_order_id=csv_row.get("顧客オーダー番号"),
            csv_filename=csv_filename,
            csv_row_number=row_number
        )
    
    @classmethod
    def create_from_transfer_csv(cls, csv_row: dict, member_id: int, csv_filename: str, row_number: int):
        """口座振替CSV結果からインスタンス作成"""
        payment_date = datetime.strptime(csv_row.get("振替日"), "%Y%m%d") if csv_row.get("振替日") else datetime.utcnow()
        has_error = bool(csv_row.get("エラー情報", "").strip())
        
        return cls(
            member_id=member_id,
            member_number=csv_row.get("顧客番号"),
            payment_date=payment_date,
            payment_type=PaymentType.TRANSFER,
            payment_method="口座振替",
            amount=Decimal(str(csv_row.get("金額", 0))),
            status=PaymentStatus.FAILED if has_error else PaymentStatus.SUCCESS,
            error_message=csv_row.get("エラー情報") if has_error else None,
            csv_filename=csv_filename,
            csv_row_number=row_number
        )
    
    @classmethod
    def create_manual_record(cls, member_id: int, member_number: str, payment_type: PaymentType, 
                           amount: Decimal, payment_date: datetime, notes: str = None, 
                           transaction_id: str = None, recorded_by: str = "system"):
        """手動記録からインスタンス作成"""
        return cls(
            member_id=member_id,
            member_number=member_number,
            payment_date=payment_date,
            payment_type=payment_type,
            payment_method=payment_type.value,
            amount=amount,
            status=PaymentStatus.SUCCESS,
            transaction_id=transaction_id,
            notes=notes,
            recorded_by=recorded_by,
            recorded_at=datetime.utcnow()
        )