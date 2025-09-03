"""
組織図API スキーマ

P-003: 組織図ビューア
MLM組織構造の視覚的表示と階層確認
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class OrganizationNode(BaseModel):
    """組織ノードスキーマ"""
    id: str = Field(..., description="ユニークID（階層-会員番号）")
    member_number: str = Field(..., description="会員番号") 
    name: str = Field(..., description="会員氏名")
    title: str = Field(..., description="資格名/称号")
    level: int = Field(..., description="階層レベル")
    hierarchy_path: str = Field(..., description="階層パス表示")
    registration_date: Optional[str] = Field(None, description="登録日")
    is_direct: bool = Field(False, description="直紹介フラグ")
    is_withdrawn: bool = Field(False, description="退会フラグ")
    
    # 組織実績
    left_count: int = Field(0, description="左人数")
    right_count: int = Field(0, description="右人数") 
    left_sales: int = Field(0, description="左実績")
    right_sales: int = Field(0, description="右実績")
    new_purchase: int = Field(0, description="新規購入")
    repeat_purchase: int = Field(0, description="リピート購入")
    additional_purchase: int = Field(0, description="追加購入")
    
    # フロントエンド用
    children: List['OrganizationNode'] = Field(default_factory=list, description="子ノード")
    is_expanded: bool = Field(True, description="展開状態")
    status: str = Field("ACTIVE", description="ステータス")


class OrganizationTree(BaseModel):
    """組織ツリーレスポンス"""
    root_nodes: List[OrganizationNode] = Field(description="ルートノード")
    total_members: int = Field(description="総メンバー数")
    max_level: int = Field(description="最大階層")
    total_sales: int = Field(description="総売上")
    active_members: int = Field(description="アクティブメンバー数")
    withdrawn_members: int = Field(description="退会メンバー数")


class OrganizationStats(BaseModel):
    """組織統計"""
    total_members: int = Field(description="総メンバー数")
    active_members: int = Field(description="アクティブメンバー数")
    withdrawn_members: int = Field(description="退会メンバー数")
    max_level: int = Field(description="最大階層")
    average_level: float = Field(description="平均階層深度")
    total_left_sales: int = Field(description="総左売上")
    total_right_sales: int = Field(description="総右売上")
    total_sales: int = Field(description="総売上")


# 前方参照を解決
OrganizationNode.model_rebuild()