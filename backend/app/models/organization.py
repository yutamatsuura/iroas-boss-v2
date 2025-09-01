"""
組織データモデル

要件定義書の組織図要件に対応：
- MLM組織をツリー形式で表示
- 退会処理と組織圧縮（手動調整）
- タイトル昇格の自動判定
- 各種実績の追跡

重要な仕様：
- 退会処理は自動圧縮ではなく手動調整方式
- 組織変更は手動でのスポンサー変更機能
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


class OrganizationNode(Base):
    """
    組織ノードテーブル
    MLM組織構造の効率的な管理用
    """
    __tablename__ = "organization_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 会員情報
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, unique=True, comment="会員ID")
    member_number = Column(String(7), nullable=False, unique=True, index=True, comment="会員番号")
    
    # 組織構造
    parent_id = Column(Integer, ForeignKey("organization_nodes.id"), nullable=True, index=True, comment="親ノードID")
    sponsor_id = Column(Integer, ForeignKey("organization_nodes.id"), nullable=True, index=True, comment="スポンサーノードID")
    
    # 階層情報
    level = Column(Integer, nullable=False, default=0, comment="階層レベル（0=ルート）")
    path = Column(String(1000), nullable=True, comment="階層パス（/1/2/3/形式）")
    
    # 組織統計
    direct_downline_count = Column(Integer, nullable=False, default=0, comment="直下会員数")
    total_downline_count = Column(Integer, nullable=False, default=0, comment="配下総会員数")
    active_downline_count = Column(Integer, nullable=False, default=0, comment="配下アクティブ会員数")
    
    # 実績情報
    monthly_sales = Column(JSON, nullable=True, comment="月別売上実績（JSON）")
    monthly_recruits = Column(JSON, nullable=True, comment="月別新規紹介実績（JSON）")
    
    # ステータス
    is_active = Column(Boolean, nullable=False, default=True, comment="アクティブフラグ")
    is_root = Column(Boolean, nullable=False, default=False, comment="ルートノードフラグ")
    
    # システム情報
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    member = relationship("Member")
    parent = relationship("OrganizationNode", remote_side=[id], foreign_keys=[parent_id], backref="children")
    sponsor = relationship("OrganizationNode", remote_side=[id], foreign_keys=[sponsor_id])
    
    def __repr__(self) -> str:
        return f"<OrganizationNode(member_number={self.member_number}, level={self.level})>"
    
    @property
    def depth(self) -> int:
        """組織の深さ"""
        return len(self.path.split('/')) - 1 if self.path else 0
    
    @property
    def has_downlines(self) -> bool:
        """配下会員がいるかどうか"""
        return self.direct_downline_count > 0
    
    def get_path_list(self) -> List[int]:
        """パスをリスト形式で取得"""
        if not self.path:
            return []
        return [int(x) for x in self.path.split('/') if x]
    
    def get_monthly_sales(self, year_month: str) -> int:
        """指定月の売上を取得"""
        if not self.monthly_sales:
            return 0
        return self.monthly_sales.get(year_month, 0)
    
    def get_monthly_recruits(self, year_month: str) -> int:
        """指定月の新規紹介数を取得"""
        if not self.monthly_recruits:
            return 0
        return self.monthly_recruits.get(year_month, 0)
    
    def update_path(self, parent_path: str = None) -> None:
        """階層パスを更新"""
        if self.is_root:
            self.path = f"/{self.id}/"
            self.level = 0
        elif parent_path:
            self.path = f"{parent_path}{self.id}/"
            self.level = len(self.path.split('/')) - 2
        else:
            # 親から計算
            if self.parent:
                self.path = f"{self.parent.path}{self.id}/"
                self.level = self.parent.level + 1
    
    def update_downline_counts(self, direct_count: int, total_count: int, active_count: int) -> None:
        """配下数統計を更新"""
        self.direct_downline_count = direct_count
        self.total_downline_count = total_count  
        self.active_downline_count = active_count
        self.updated_at = datetime.utcnow()
    
    def add_monthly_sales(self, year_month: str, amount: int) -> None:
        """月別売上を追加"""
        if not self.monthly_sales:
            self.monthly_sales = {}
        
        # 辞書を更新
        monthly_sales = dict(self.monthly_sales)
        monthly_sales[year_month] = monthly_sales.get(year_month, 0) + amount
        self.monthly_sales = monthly_sales
    
    def add_monthly_recruit(self, year_month: str, count: int = 1) -> None:
        """月別新規紹介を追加"""
        if not self.monthly_recruits:
            self.monthly_recruits = {}
        
        # 辞書を更新
        monthly_recruits = dict(self.monthly_recruits)
        monthly_recruits[year_month] = monthly_recruits.get(year_month, 0) + count
        self.monthly_recruits = monthly_recruits
    
    def change_sponsor(self, new_sponsor_id: int, new_parent_id: int = None) -> None:
        """スポンサー変更（手動組織調整）"""
        self.sponsor_id = new_sponsor_id
        if new_parent_id:
            self.parent_id = new_parent_id
        self.updated_at = datetime.utcnow()
    
    def set_withdrawn(self) -> None:
        """退会処理（ノードを非アクティブに）"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_tree_dict(self, include_children: bool = False) -> Dict[str, Any]:
        """ツリー表示用辞書に変換"""
        result = {
            "id": self.id,
            "member_id": self.member_id,
            "member_number": self.member_number,
            "level": self.level,
            "direct_downline_count": self.direct_downline_count,
            "total_downline_count": self.total_downline_count,
            "active_downline_count": self.active_downline_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }
        
        # 会員情報を含める（member relationshipから）
        if hasattr(self, 'member') and self.member:
            result.update({
                "name": self.member.name,
                "title": self.member.title,
                "plan": self.member.plan,
                "status": self.member.status,
            })
        
        if include_children and hasattr(self, 'children'):
            result["children"] = [child.to_tree_dict() for child in self.children]
        
        return result
    
    @classmethod
    def create_root_node(cls, member_id: int, member_number: str) -> 'OrganizationNode':
        """ルートノード作成"""
        node = cls(
            member_id=member_id,
            member_number=member_number,
            parent_id=None,
            sponsor_id=None,
            level=0,
            is_root=True,
            is_active=True
        )
        # パスは保存後に更新される
        return node
    
    @classmethod
    def create_child_node(cls, member_id: int, member_number: str, 
                         parent_id: int, sponsor_id: int = None) -> 'OrganizationNode':
        """子ノード作成"""
        return cls(
            member_id=member_id,
            member_number=member_number,
            parent_id=parent_id,
            sponsor_id=sponsor_id or parent_id,  # sponsor未指定なら親と同じ
            is_active=True
        )