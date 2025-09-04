"""
統合データモデル定義
Phase 1: 会員管理と組織図データの統合
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum

class MemberStatus(str, Enum):
    """会員ステータス"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    WITHDRAWN = "WITHDRAWN"

class DataSource(str, Enum):
    """データソース"""
    MEMBER_MASTER = "MEMBER_MASTER"
    ORGANIZATION_CSV = "ORGANIZATION_CSV"
    INTEGRATED = "INTEGRATED"

class UnifiedMemberData(BaseModel):
    """統合会員データ型"""
    # 基本情報（会員管理マスター）
    member_number: str = Field(..., description="会員番号（11桁）", min_length=11, max_length=11)
    name: str = Field(..., description="氏名")
    email: Optional[str] = Field(None, description="メールアドレス")
    phone: Optional[str] = Field(None, description="電話番号")
    status: MemberStatus = Field(..., description="会員ステータス")
    registration_date: Optional[str] = Field(None, description="登録日")
    
    # 組織情報（組織図データ）
    level: int = Field(0, description="組織レベル", ge=0)
    hierarchy_path: str = Field("", description="階層パス")
    is_direct: bool = Field(False, description="直接下位フラグ")
    is_withdrawn: bool = Field(False, description="退会フラグ")
    
    # 売上実績
    left_sales: float = Field(0.0, description="左側売上", ge=0)
    right_sales: float = Field(0.0, description="右側売上", ge=0)
    new_purchase: float = Field(0.0, description="新規購入額", ge=0)
    repeat_purchase: float = Field(0.0, description="リピート購入額", ge=0)
    additional_purchase: float = Field(0.0, description="追加購入額", ge=0)
    
    # 組織構成
    left_count: int = Field(0, description="左側人数", ge=0)
    right_count: int = Field(0, description="右側人数", ge=0)
    children: List["UnifiedMemberData"] = Field(default_factory=list, description="子会員リスト")
    
    # 統合情報
    current_title: str = Field("", description="会員管理の現在称号")
    historical_title: str = Field("", description="組織図の最高称号")
    display_title: str = Field("", description="表示用称号")
    
    # メタ情報
    last_updated: Optional[datetime] = Field(None, description="最終更新日時")
    data_source: DataSource = Field(DataSource.INTEGRATED, description="データソース")
    
    class Config:
        """Pydantic設定"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# 循環参照のためのモデル更新
UnifiedMemberData.model_rebuild()

class UnifiedOrganizationTree(BaseModel):
    """統合組織ツリー"""
    root_nodes: List[UnifiedMemberData] = Field(..., description="ルートノードリスト")
    total_members: int = Field(..., description="総会員数", ge=0)
    active_members: int = Field(..., description="アクティブ会員数", ge=0)
    withdrawn_members: int = Field(..., description="退会会員数", ge=0)
    max_level: int = Field(..., description="最大レベル", ge=0)
    total_sales: float = Field(..., description="総売上", ge=0)
    
    # 統計情報
    stats: Dict[str, Any] = Field(default_factory=dict, description="統計情報")
    
class MemberSearchParams(BaseModel):
    """会員検索パラメータ"""
    member_number: Optional[str] = Field(None, description="会員番号")
    name: Optional[str] = Field(None, description="氏名（部分一致）")
    status: Optional[MemberStatus] = Field(None, description="ステータス")
    level_min: Optional[int] = Field(None, description="最小レベル", ge=0)
    level_max: Optional[int] = Field(None, description="最大レベル", ge=0)
    active_only: Optional[bool] = Field(None, description="アクティブのみ")
    page: int = Field(1, description="ページ番号", ge=1)
    per_page: int = Field(50, description="1ページあたりの件数", ge=1, le=1000)
    sort_by: str = Field("member_number", description="ソート項目")
    sort_order: Literal["asc", "desc"] = Field("asc", description="ソート順")

class UnifiedMemberListResponse(BaseModel):
    """統合会員一覧レスポンス"""
    members: List[UnifiedMemberData] = Field(..., description="会員リスト")
    total_count: int = Field(..., description="総件数", ge=0)
    active_count: int = Field(..., description="アクティブ会員数", ge=0)
    inactive_count: int = Field(..., description="非アクティブ会員数", ge=0)
    withdrawn_count: int = Field(..., description="退会会員数", ge=0)
    page: int = Field(..., description="現在ページ", ge=1)
    per_page: int = Field(..., description="1ページあたりの件数", ge=1)
    total_pages: int = Field(..., description="総ページ数", ge=1)
    has_next: bool = Field(..., description="次ページ存在フラグ")
    has_prev: bool = Field(..., description="前ページ存在フラグ")

class DataIntegrityReport(BaseModel):
    """データ整合性レポート"""
    check_date: datetime = Field(..., description="チェック実行日時")
    total_issues: int = Field(..., description="総問題数", ge=0)
    
    # 問題の詳細
    duplicate_member_numbers: List[str] = Field(default_factory=list, description="重複会員番号")
    invalid_member_numbers: List[str] = Field(default_factory=list, description="無効会員番号")
    missing_names: List[str] = Field(default_factory=list, description="氏名欠損会員番号")
    orphaned_members: List[str] = Field(default_factory=list, description="親が存在しない会員")
    
    # 統計情報
    data_quality_score: float = Field(..., description="データ品質スコア（0-100）", ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list, description="改善推奨事項")
    
class MigrationStatus(BaseModel):
    """移行ステータス"""
    phase: str = Field(..., description="移行フェーズ")
    status: Literal["not_started", "in_progress", "completed", "failed"] = Field(..., description="ステータス")
    progress_percentage: float = Field(..., description="進捗率", ge=0, le=100)
    
    # 詳細情報
    started_at: Optional[datetime] = Field(None, description="開始日時")
    completed_at: Optional[datetime] = Field(None, description="完了日時")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    
    # 統計
    processed_records: int = Field(0, description="処理済みレコード数", ge=0)
    total_records: int = Field(0, description="総レコード数", ge=0)
    failed_records: int = Field(0, description="失敗レコード数", ge=0)