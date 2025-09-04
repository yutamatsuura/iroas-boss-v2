"""
統合APIエンドポイント
Phase 1: 統合表示システム
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
import logging

from ...models.unified_models import (
    UnifiedMemberData, UnifiedOrganizationTree, MemberSearchParams,
    UnifiedMemberListResponse, DataIntegrityReport, MemberStatus
)
from ...services.unified_service import UnifiedMemberService, DataIntegrityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified", tags=["unified"])

# サービスインスタンス
unified_member_service = UnifiedMemberService()
data_integrity_service = DataIntegrityService()


@router.get("/members", response_model=UnifiedMemberListResponse)
async def get_unified_members(
    member_number: Optional[str] = Query(None, description="会員番号での検索"),
    name: Optional[str] = Query(None, description="氏名での部分一致検索"),
    status: Optional[MemberStatus] = Query(None, description="ステータスフィルター"),
    level_min: Optional[int] = Query(None, description="最小レベル", ge=0),
    level_max: Optional[int] = Query(None, description="最大レベル", ge=0),
    active_only: Optional[bool] = Query(None, description="アクティブメンバーのみ"),
    page: int = Query(1, description="ページ番号", ge=1),
    per_page: int = Query(50, description="1ページあたりの件数", ge=1, le=1000),
    sort_by: str = Query("member_number", description="ソート項目"),
    sort_order: str = Query("asc", description="ソート順（asc/desc）")
):
    """
    統合会員一覧取得
    会員管理と組織図データを統合した会員一覧を取得
    """
    try:
        params = MemberSearchParams(
            member_number=member_number,
            name=name,
            status=status,
            level_min=level_min,
            level_max=level_max,
            active_only=active_only,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = unified_member_service.get_unified_member_list(params)
        logger.info(f"統合会員一覧取得: {result.total_count}件中{len(result.members)}件返却")
        
        return result
        
    except Exception as e:
        logger.error(f"統合会員一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail="統合会員一覧の取得に失敗しました")


@router.get("/members/{member_number}", response_model=UnifiedMemberData)
async def get_unified_member(member_number: str):
    """
    統合会員詳細取得
    指定された会員番号の統合データを取得
    """
    try:
        # 会員番号の正規化（11桁）
        normalized_number = member_number.strip().zfill(11) if member_number.strip().isdigit() else member_number
        
        member = unified_member_service.get_unified_member(normalized_number)
        if not member:
            raise HTTPException(status_code=404, detail=f"会員番号 {member_number} は見つかりませんでした")
        
        logger.info(f"統合会員詳細取得: {member_number} -> {member.name}")
        return member
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"統合会員詳細取得エラー: {member_number}, {e}")
        raise HTTPException(status_code=500, detail="統合会員詳細の取得に失敗しました")


@router.get("/organization/tree", response_model=UnifiedOrganizationTree)
async def get_unified_organization_tree(
    member_id: Optional[str] = Query(None, description="ルートメンバー番号"),
    max_level: Optional[int] = Query(None, description="最大階層レベル", ge=1, le=100),
    active_only: Optional[bool] = Query(False, description="アクティブメンバーのみ"),
    include_sales: Optional[bool] = Query(True, description="売上データを含める"),
    include_stats: Optional[bool] = Query(True, description="統計情報を含める")
):
    """
    統合組織ツリー取得
    統合された組織階層データを階層構造で取得
    """
    try:
        # 統合メンバーデータを取得
        members = unified_member_service._load_unified_members()
        
        # 簡易的なツリー構造を作成
        root_nodes = []
        if member_id:
            root_member = members.get(member_id.zfill(11))
            if root_member:
                root_nodes = [root_member]
        else:
            # ルートメンバーを取得（レベル0）
            root_nodes = [m for m in members.values() if m.level == 0]
        
        # 統計情報を計算
        total_members = len(members)
        active_members = sum(1 for m in members.values() if m.status == MemberStatus.ACTIVE)
        withdrawn_members = sum(1 for m in members.values() if m.status == MemberStatus.WITHDRAWN)
        max_level_val = max((m.level for m in members.values()), default=0)
        total_sales = sum(m.left_sales + m.right_sales for m in members.values())
        
        # 統合統計情報を追加
        stats = {}
        if include_stats:
            stats = {
                "data_source": "INTEGRATED",
                "last_updated": unified_member_service._cache_timestamp.isoformat() if unified_member_service._cache_timestamp else None,
                "cache_status": "ACTIVE"
            }
        
        result = UnifiedOrganizationTree(
            root_nodes=root_nodes,
            total_members=total_members,
            active_members=active_members,
            withdrawn_members=withdrawn_members,
            max_level=max_level_val,
            total_sales=total_sales,
            stats=stats
        )
        
        logger.info(f"統合組織ツリー取得: ルート={member_id}, ノード数={len(root_nodes)}")
        return result
        
    except Exception as e:
        logger.error(f"統合組織ツリー取得エラー: {e}")
        raise HTTPException(status_code=500, detail="統合組織ツリーの取得に失敗しました")


@router.get("/data-integrity", response_model=DataIntegrityReport)
async def check_data_integrity():
    """
    データ整合性チェック
    統合データの品質と整合性をチェック
    """
    try:
        report = data_integrity_service.check_data_integrity()
        logger.info(f"データ整合性チェック完了: スコア={report.data_quality_score:.1f}, 問題={report.total_issues}件")
        return report
        
    except Exception as e:
        logger.error(f"データ整合性チェックエラー: {e}")
        raise HTTPException(status_code=500, detail="データ整合性チェックに失敗しました")


@router.post("/cache/refresh")
async def refresh_cache():
    """
    キャッシュリフレッシュ
    統合データのキャッシュを強制更新
    """
    try:
        # キャッシュをクリア
        unified_member_service._cache.clear()
        unified_member_service._cache_timestamp = None
        
        # 新しいデータを読み込み
        members = unified_member_service._load_unified_members(force_refresh=True)
        
        result = {
            "status": "success",
            "message": f"キャッシュを更新しました",
            "member_count": len(members),
            "updated_at": unified_member_service._cache_timestamp.isoformat()
        }
        
        logger.info(f"キャッシュリフレッシュ完了: {len(members)}名のデータを更新")
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"キャッシュリフレッシュエラー: {e}")
        raise HTTPException(status_code=500, detail="キャッシュのリフレッシュに失敗しました")


@router.get("/stats/summary")
async def get_unified_stats():
    """
    統合統計サマリー
    統合システムの統計情報を取得
    """
    try:
        # 統合会員データの統計
        members = unified_member_service._load_unified_members()
        
        # ステータス別集計
        status_counts = {
            "active": sum(1 for m in members.values() if m.status == MemberStatus.ACTIVE),
            "inactive": sum(1 for m in members.values() if m.status == MemberStatus.INACTIVE),
            "withdrawn": sum(1 for m in members.values() if m.status == MemberStatus.WITHDRAWN)
        }
        
        # レベル別集計
        level_distribution = {}
        for member in members.values():
            level = member.level
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        # 売上統計
        total_sales = sum(m.left_sales + m.right_sales for m in members.values())
        total_new_purchase = sum(m.new_purchase for m in members.values())
        total_repeat_purchase = sum(m.repeat_purchase for m in members.values())
        
        result = {
            "total_members": len(members),
            "status_counts": status_counts,
            "level_distribution": dict(sorted(level_distribution.items())),
            "sales_summary": {
                "total_sales": total_sales,
                "new_purchase": total_new_purchase,
                "repeat_purchase": total_repeat_purchase
            },
            "cache_info": {
                "last_updated": unified_member_service._cache_timestamp.isoformat() if unified_member_service._cache_timestamp else None,
                "cache_size": len(members)
            }
        }
        
        logger.info(f"統合統計サマリー取得: 総会員数={len(members)}")
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"統合統計サマリー取得エラー: {e}")
        raise HTTPException(status_code=500, detail="統合統計サマリーの取得に失敗しました")


