"""
組織管理API スキーマ

Phase B-1a: 組織構造API（2.1-2.3）
Phase B-1b: スポンサー変更API（1.5, 1.7）

要件定義書：「退会処理と組織圧縮 - 退会者が出た場合、その下の会員を上位スポンサーに自動接続」
重要仕様：「退会処理は自動圧縮ではなく手動調整方式」

モックアップP-003対応
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from app.models.member import MemberStatus, Title, Plan


class MemberStatusEnum(str, Enum):
    """会員ステータス（組織図用）"""
    ACTIVE = "アクティブ"
    INACTIVE = "休会中"
    WITHDRAWN = "退会済"


class TitleEnum(str, Enum):
    """称号（組織図用）"""
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


class PlanEnum(str, Enum):
    """加入プラン（組織図用）"""
    HERO = "ヒーロープラン"
    TEST = "テストプラン"


class OrganizationNodeResponse(BaseModel):
    """
    組織ノードレスポンススキーマ
    API 2.1-2.3: 組織ツリー構造の各ノード
    """
    # ノード基本情報
    id: int = Field(description="ノードID")
    member_id: int = Field(description="会員ID")
    member_number: str = Field(description="会員番号")
    
    # 会員基本情報
    name: str = Field(description="会員氏名")
    title: TitleEnum = Field(description="称号")
    plan: PlanEnum = Field(description="加入プラン")
    status: MemberStatusEnum = Field(description="会員ステータス")
    registration_date: datetime = Field(description="登録日")
    
    # 組織構造情報
    parent_id: Optional[int] = Field(description="親ノードID")
    sponsor_id: Optional[int] = Field(description="スポンサーノードID")
    level: int = Field(description="階層レベル（0=ルート）")
    path: str = Field(description="階層パス")
    
    # 組織統計
    direct_downline_count: int = Field(description="直下会員数")
    total_downline_count: int = Field(description="配下総会員数")
    active_downline_count: int = Field(description="配下アクティブ会員数")
    
    # 実績情報（月別）
    current_month_sales: int = Field(description="当月売上")
    current_month_recruits: int = Field(description="当月新規紹介数")
    total_sales: int = Field(description="累計売上")
    total_recruits: int = Field(description="累計新規紹介数")
    
    # 表示用プロパティ
    display_name: str = Field(description="表示用氏名（会員番号 - 氏名）")
    depth_indicator: str = Field(description="階層表示用インデント")
    has_downlines: bool = Field(description="配下会員存在フラグ")
    is_active: bool = Field(description="アクティブ状態")
    
    # タイムスタンプ
    created_at: datetime = Field(description="作成日時")
    updated_at: datetime = Field(description="更新日時")
    
    class Config:
        from_attributes = True


class OrganizationTreeResponse(BaseModel):
    """
    組織ツリーレスポンススキーマ
    API 2.1: GET /api/organization/tree
    """
    # ルート情報
    root_node: OrganizationNodeResponse = Field(description="ルートノード")
    
    # ツリー構造（階層化）
    tree_data: List[Dict[str, Any]] = Field(description="ツリー構造データ")
    
    # 統計情報
    total_nodes: int = Field(description="総ノード数")
    active_nodes: int = Field(description="アクティブノード数")
    max_depth: int = Field(description="最大階層数")
    
    # 階層別統計
    level_stats: Dict[int, int] = Field(description="階層別会員数")
    
    # 実績統計
    total_organization_sales: int = Field(description="組織全体売上")
    total_organization_recruits: int = Field(description="組織全体新規紹介数")
    
    # フィルター情報
    filter_applied: Dict[str, Any] = Field(default_factory=dict, description="適用中フィルター")
    
    @classmethod
    def create_tree_structure(cls, nodes: List[OrganizationNodeResponse]) -> List[Dict[str, Any]]:
        """ノードリストからツリー構造を生成"""
        tree = []
        node_map = {node.id: node.dict() for node in nodes}
        
        # 子要素をparentに追加
        for node_data in node_map.values():
            parent_id = node_data.get('parent_id')
            if parent_id and parent_id in node_map:
                if 'children' not in node_map[parent_id]:
                    node_map[parent_id]['children'] = []
                node_map[parent_id]['children'].append(node_data)
            elif not parent_id:  # ルートノード
                tree.append(node_data)
        
        return tree


class OrganizationMemberDownlineResponse(BaseModel):
    """
    会員配下一覧レスポンススキーマ
    API 2.2: GET /api/organization/tree/{id}
    API 2.3: GET /api/organization/member/{id}/downline
    """
    # 基準会員情報
    base_member: OrganizationNodeResponse = Field(description="基準会員情報")
    
    # 配下会員リスト
    downline_members: List[OrganizationNodeResponse] = Field(description="配下会員リスト")
    
    # 統計情報
    direct_count: int = Field(description="直下会員数")
    total_count: int = Field(description="総配下会員数")
    active_count: int = Field(description="アクティブ配下会員数")
    
    # 階層別内訳
    level_breakdown: Dict[int, int] = Field(description="階層別配下会員数")
    
    # 実績サマリー
    downline_total_sales: int = Field(description="配下総売上")
    downline_total_recruits: int = Field(description="配下総新規紹介数")
    
    # 表示設定
    max_display_level: Optional[int] = Field(default=None, description="最大表示階層")
    show_inactive: bool = Field(default=True, description="非アクティブ表示フラグ")


class SponsorChangeRequest(BaseModel):
    """
    スポンサー変更リクエストスキーマ
    API 1.7: PUT /api/members/{id}/sponsor
    組織手動調整機能
    """
    new_sponsor_member_number: str = Field(..., pattern=r'^\d{7}$', description="新しいスポンサーの会員番号")
    change_reason: str = Field(..., min_length=1, max_length=500, description="変更理由（必須）")
    
    # 変更オプション
    move_downlines: bool = Field(default=True, description="配下会員も一緒に移動するか")
    effective_date: Optional[datetime] = Field(default=None, description="有効日（未指定時は即時）")
    
    # 承認フロー（将来拡張用）
    require_approval: bool = Field(default=False, description="承認が必要か")
    approver_note: Optional[str] = Field(default=None, max_length=1000, description="承認者コメント")
    
    @validator('new_sponsor_member_number')
    def validate_sponsor_member_number(cls, v):
        if len(v) != 7 or not v.isdigit():
            raise ValueError('スポンサー会員番号は7桁の数字である必要があります')
        return v
    
    @validator('effective_date')
    def validate_effective_date(cls, v):
        if v and v < datetime.now():
            raise ValueError('有効日は現在日時以降で指定してください')
        return v


class SponsorChangeResponse(BaseModel):
    """
    スポンサー変更レスポンススキーマ
    変更結果と影響範囲の報告
    """
    # 変更結果
    success: bool = Field(description="変更成功フラグ")
    change_id: int = Field(description="変更記録ID")
    
    # 変更詳細
    target_member: str = Field(description="変更対象会員（会員番号 - 氏名）")
    old_sponsor: Optional[str] = Field(description="旧スポンサー（会員番号 - 氏名）")
    new_sponsor: str = Field(description="新スポンサー（会員番号 - 氏名）")
    
    # 影響範囲
    affected_members: List[str] = Field(description="影響を受ける会員リスト")
    moved_downlines: int = Field(description="一緒に移動した配下会員数")
    
    # 組織統計変更
    old_structure_stats: Dict[str, int] = Field(description="変更前組織統計")
    new_structure_stats: Dict[str, int] = Field(description="変更後組織統計")
    
    # 実行情報
    executed_at: datetime = Field(description="実行日時")
    executed_by: str = Field(description="実行者")
    
    # 警告・注意事項
    warnings: List[str] = Field(default_factory=list, description="警告メッセージ")
    notices: List[str] = Field(default_factory=list, description="注意事項")


class OrganizationSearchRequest(BaseModel):
    """
    組織検索リクエストスキーマ
    組織図フィルタリング機能
    """
    # 検索条件
    keyword: Optional[str] = Field(default=None, description="キーワード（会員番号、氏名）")
    member_number: Optional[str] = Field(default=None, pattern=r'^\d{7}$', description="会員番号")
    name: Optional[str] = Field(default=None, description="氏名（部分一致）")
    
    # フィルター条件
    status: Optional[MemberStatusEnum] = Field(default=None, description="会員ステータス")
    title: Optional[TitleEnum] = Field(default=None, description="称号")
    plan: Optional[PlanEnum] = Field(default=None, description="加入プラン")
    
    # 階層条件
    min_level: Optional[int] = Field(default=None, ge=0, description="最小階層レベル")
    max_level: Optional[int] = Field(default=None, ge=0, description="最大階層レベル")
    
    # 実績条件
    min_downlines: Optional[int] = Field(default=None, ge=0, description="最小配下会員数")
    min_sales: Optional[int] = Field(default=None, ge=0, description="最小売上")
    
    # 表示オプション
    include_inactive: bool = Field(default=True, description="非アクティブ会員を含めるか")
    max_results: int = Field(default=100, ge=1, le=1000, description="最大結果数")


class OrganizationAdjustmentLog(BaseModel):
    """
    組織調整ログレスポンススキーマ
    手動調整履歴の管理
    """
    id: int = Field(description="ログID")
    
    # 調整情報
    adjustment_type: str = Field(description="調整種別（スポンサー変更、退会処理等）")
    target_member_number: str = Field(description="対象会員番号")
    target_member_name: str = Field(description="対象会員氏名")
    
    # 変更詳細
    before_data: Dict[str, Any] = Field(description="変更前データ")
    after_data: Dict[str, Any] = Field(description="変更後データ")
    change_reason: str = Field(description="変更理由")
    
    # 影響範囲
    affected_member_count: int = Field(description="影響会員数")
    organization_impact: Dict[str, Any] = Field(description="組織への影響")
    
    # 実行情報
    executed_at: datetime = Field(description="実行日時")
    executed_by: str = Field(description="実行者")
    
    # 承認フロー
    approval_status: Optional[str] = Field(description="承認ステータス")
    approved_by: Optional[str] = Field(description="承認者")
    approved_at: Optional[datetime] = Field(description="承認日時")
    
    class Config:
        from_attributes = True