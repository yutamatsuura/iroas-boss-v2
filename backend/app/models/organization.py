"""
組織図関連のデータモデル

MLM組織構造の管理：
- バイナリツリー構造（LEFT/RIGHT）
- 退会者ポジション永続保持
- 売上実績・報酬計算
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Text, 
    ForeignKey, Enum as SQLEnum, DECIMAL, Boolean
)
from sqlalchemy.orm import relationship, backref
from app.database import Base


class PositionType(str, Enum):
    """組織ポジションタイプ"""
    ROOT = "ROOT"
    LEFT = "LEFT" 
    RIGHT = "RIGHT"


class OrganizationPosition(Base):
    """
    組織ポジションテーブル
    すべての組織ポジション（アクティブメンバー・退会者）を管理
    """
    __tablename__ = "organization_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # メンバー参照（アクティブメンバーの場合）
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    
    # 退会者参照（退会者の場合）
    withdrawn_id = Column(Integer, ForeignKey("withdrawals.id"), nullable=True)
    
    # 組織構造
    parent_id = Column(Integer, ForeignKey("organization_positions.id"), nullable=True)
    position_type = Column(SQLEnum(PositionType), nullable=False)
    level = Column(Integer, default=0)
    hierarchy_path = Column(String(500), nullable=True)  # "1.2.1" 形式
    
    # 組織実績（アクティブメンバーのみカウント）
    left_count = Column(Integer, default=0)      # 左組織のアクティブ人数
    right_count = Column(Integer, default=0)     # 右組織のアクティブ人数
    left_sales = Column(DECIMAL(12, 2), default=0)   # 左組織売上
    right_sales = Column(DECIMAL(12, 2), default=0)  # 右組織売上
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    member = relationship("Member", backref="organization_position")
    withdrawal = relationship("Withdrawal", backref="organization_position")
    
    # 自己参照リレーション
    parent = relationship(
        "OrganizationPosition",
        remote_side=[id],
        backref=backref("children", cascade="all, delete-orphan")
    )
    
    # 売上実績
    sales_records = relationship(
        "OrganizationSales", 
        backref="position",
        cascade="all, delete-orphan"
    )


class Withdrawal(Base):
    """
    退会者テーブル
    退会した会員の情報（組織図表示用）
    """
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 退会者識別
    withdrawal_number = Column(String(20), unique=True, nullable=False)  # WITHDRAWN_001
    
    # 元会員情報（記録用）
    original_member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    original_member_number = Column(String(11), nullable=True)
    original_name = Column(Text, nullable=True)
    
    # 退会情報
    withdrawal_date = Column(Date, nullable=False)
    withdrawal_reason = Column(Text, nullable=True)
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    original_member = relationship("Member", backref="withdrawal_record")


class OrganizationSales(Base):
    """
    組織売上実績テーブル
    月次の売上実績を管理
    """
    __tablename__ = "organization_sales"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ポジション参照
    position_id = Column(Integer, ForeignKey("organization_positions.id"), nullable=False)
    
    # 期間
    year_month = Column(String(7), nullable=False)  # "2025-08" 形式
    
    # 売上実績
    new_purchase = Column(DECIMAL(12, 2), default=0)      # 新規購入
    repeat_purchase = Column(DECIMAL(12, 2), default=0)   # リピート購入  
    additional_purchase = Column(DECIMAL(12, 2), default=0)  # 追加購入
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        # 同じポジション・月の重複を防ぐ
        {'sqlite_autoincrement': True},
    )


class OrganizationStats(Base):
    """
    組織統計テーブル
    組織全体の統計情報をキャッシュ
    """
    __tablename__ = "organization_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 統計期間
    stats_date = Column(Date, nullable=False)
    
    # メンバー統計
    total_positions = Column(Integer, default=0)       # 全ポジション数
    active_members = Column(Integer, default=0)        # アクティブメンバー数
    withdrawn_members = Column(Integer, default=0)     # 退会者数
    max_level = Column(Integer, default=0)             # 最大階層レベル
    
    # 売上統計
    total_sales = Column(DECIMAL(12, 2), default=0)    # 総売上
    monthly_sales = Column(DECIMAL(12, 2), default=0)  # 月次売上
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)