"""
統合された組織図スキーマ（将来の拡張用）
組織図データと会員管理データの統合に対応
"""

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class EnhancedOrganizationNode(BaseModel):
    # 既存の組織図データ
    id: str
    member_number: str
    name: str
    title: str
    level: int
    hierarchy_path: str
    registration_date: Optional[str] = None
    is_direct: bool = False
    is_withdrawn: bool = False
    
    # 組織実績
    left_count: int = 0
    right_count: int = 0
    left_sales: int = 0
    right_sales: int = 0
    new_purchase: int = 0
    repeat_purchase: int = 0
    additional_purchase: int = 0
    
    # 会員管理データとの統合情報（オプション）
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    plan: Optional[str] = None
    payment_method: Optional[str] = None
    withdrawal_date: Optional[str] = None
    supervisor_id: Optional[str] = None
    supervisor_name: Optional[str] = None
    
    # 銀行情報（オプション）
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    account_number: Optional[str] = None
    
    # フロントエンド用
    children: List['EnhancedOrganizationNode'] = []
    is_expanded: bool = True
    status: str = "ACTIVE"
    
    # 統合ステータス
    has_member_details: bool = False  # 会員管理データが利用可能かどうか

class Config:
    # 前方参照の解決
    model_rebuild = True

# 前方参照の解決
EnhancedOrganizationNode.model_rebuild()

class EnhancedOrganizationTree(BaseModel):
    root_nodes: List[EnhancedOrganizationNode]
    total_members: int
    max_level: int
    total_sales: int = 0
    active_members: int = 0
    withdrawn_members: int = 0
    
    # 統合統計
    members_with_details: int = 0  # 詳細情報が利用可能なメンバー数
    integration_rate: float = 0.0  # 統合率（%）

class MemberIntegrationService:
    """
    会員データ統合サービス
    組織図データと会員管理データを統合する
    """
    
    @staticmethod
    def load_member_details_cache():
        """会員詳細データをキャッシュに読み込み（本番用）"""
        # 実装例:
        # - 会員管理データベースから詳細情報を取得
        # - 会員番号をキーとした辞書を作成
        # - Redis等にキャッシュ
        pass
    
    @staticmethod
    def enhance_organization_node(org_node: dict, member_cache: dict) -> dict:
        """組織ノードに会員詳細情報を追加"""
        member_num = org_node.get('member_number')
        if member_num in member_cache:
            member_details = member_cache[member_num]
            
            # 会員管理データを組織データに統合
            org_node.update({
                'email': member_details.get('email'),
                'phone': member_details.get('phone'),
                'address': member_details.get('address'),
                'gender': member_details.get('gender'),
                'plan': member_details.get('plan'),
                'payment_method': member_details.get('payment_method'),
                'withdrawal_date': member_details.get('withdrawal_date'),
                'supervisor_id': member_details.get('supervisor_id'),
                'supervisor_name': member_details.get('supervisor_name'),
                'bank_name': member_details.get('bank_name'),
                'branch_name': member_details.get('branch_name'),
                'account_number': member_details.get('account_number'),
                'has_member_details': True
            })
        
        return org_node
    
    @staticmethod
    def calculate_integration_stats(nodes: List[dict]) -> dict:
        """統合統計を計算"""
        total_members = len(nodes)
        members_with_details = sum(1 for node in nodes if node.get('has_member_details', False))
        integration_rate = (members_with_details / total_members * 100) if total_members > 0 else 0
        
        return {
            'members_with_details': members_with_details,
            'integration_rate': integration_rate
        }