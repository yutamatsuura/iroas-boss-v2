"""
組織構造サービス

Phase B-1a: 組織構造API（2.1-2.3）
- A-1b（会員管理）完了後実装可能
- モックアップP-003対応

エンドポイント:
- 2.1 GET /api/organization/tree - 組織ツリー取得
- 2.2 GET /api/organization/tree/{id} - 特定会員配下取得
- 2.3 GET /api/organization/member/{id}/downline - 直下メンバー一覧
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.models.member import Member, MemberStatus
from app.schemas.organization import (
    OrganizationTreeResponse,
    OrganizationNodeResponse,
    DownlineMemberResponse,
    OrganizationStatsResponse
)
from app.services.activity_service import ActivityService


class OrganizationService:
    """
    組織構造サービスクラス
    MLM組織ツリーの構築・管理を担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)

    async def get_organization_tree(
        self,
        root_member_id: Optional[int] = None,
        max_depth: int = 10,
        include_inactive: bool = False
    ) -> OrganizationTreeResponse:
        """
        組織ツリー取得
        API 2.1: GET /api/organization/tree
        """
        # ルート会員設定（未指定時は全てのトップレベル会員）
        if root_member_id:
            root_members = [self.db.query(Member).filter(Member.id == root_member_id).first()]
            if not root_members[0]:
                raise ValueError(f"会員ID {root_member_id} は存在しません")
        else:
            # 直上者がいない会員（トップレベル）を取得
            root_members = self.db.query(Member).filter(Member.parent_id.is_(None)).all()
        
        # ツリー構築
        tree_nodes = []
        total_members = 0
        
        for root in root_members:
            if not root:
                continue
                
            # 各ルートから組織ツリーを構築
            node = await self._build_tree_node(
                root, 
                max_depth, 
                include_inactive, 
                current_depth=0
            )
            
            if node:
                tree_nodes.append(node)
                total_members += node.total_downline_count + 1
        
        # 組織統計情報
        org_stats = await self._calculate_organization_stats(include_inactive)
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="組織ツリー取得",
            details=f"ルート: {root_member_id or 'ALL'}, 深度: {max_depth}, 総会員数: {total_members}",
            user_id="system"
        )
        
        return OrganizationTreeResponse(
            tree_nodes=tree_nodes,
            root_member_id=root_member_id,
            max_depth_displayed=max_depth,
            total_displayed_members=total_members,
            include_inactive_members=include_inactive,
            organization_stats=org_stats,
            generated_at=datetime.now()
        )

    async def get_member_downline_tree(
        self,
        member_id: int,
        max_depth: int = 5,
        include_inactive: bool = False
    ) -> OrganizationTreeResponse:
        """
        特定会員配下取得
        API 2.2: GET /api/organization/tree/{id}
        """
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"会員ID {member_id} は存在しません")
        
        # 指定会員をルートとした組織ツリー取得
        tree_response = await self.get_organization_tree(
            root_member_id=member_id,
            max_depth=max_depth,
            include_inactive=include_inactive
        )
        
        return tree_response

    async def get_direct_downline_members(
        self,
        member_id: int,
        include_inactive: bool = False,
        page: int = 1,
        per_page: int = 50
    ) -> List[DownlineMemberResponse]:
        """
        直下メンバー一覧取得
        API 2.3: GET /api/organization/member/{id}/downline
        """
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"会員ID {member_id} は存在しません")
        
        # 直下メンバー取得クエリ
        query = self.db.query(Member).filter(Member.parent_id == member_id)
        
        # ステータスフィルター
        if not include_inactive:
            query = query.filter(Member.status == MemberStatus.ACTIVE)
        
        # ページネーション
        offset = (page - 1) * per_page
        direct_members = query.offset(offset).limit(per_page).all()
        
        # レスポンス作成
        downline_list = []
        for direct_member in direct_members:
            # 各メンバーの配下数計算
            downline_count = await self._get_total_downline_count(direct_member.id, include_inactive)
            
            downline_response = DownlineMemberResponse(
                member_id=direct_member.id,
                member_number=direct_member.member_number,
                member_name=direct_member.name,
                status=direct_member.status,
                title=direct_member.title,
                plan=direct_member.plan,
                registration_date=direct_member.registration_date,
                
                # 組織情報
                parent_member_id=direct_member.parent_id,
                parent_member_name=direct_member.parent_name,
                referrer_member_id=direct_member.referrer_id,
                referrer_member_name=direct_member.referrer_name,
                
                # 配下統計
                direct_downline_count=await self._get_direct_downline_count(direct_member.id, include_inactive),
                total_downline_count=downline_count,
                
                # 表示用
                formatted_registration_date=direct_member.registration_date.strftime("%Y年%m月%d日") if direct_member.registration_date else None,
                depth_level=1,  # 直下なので深度1
                has_downline=downline_count > 0,
                is_active=direct_member.status == MemberStatus.ACTIVE
            )
            
            downline_list.append(downline_response)
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="直下メンバー取得",
            details=f"会員: {member.member_number}, 直下: {len(downline_list)}名",
            user_id="system",
            target_id=member_id
        )
        
        return downline_list

    async def _build_tree_node(
        self,
        member: Member,
        max_depth: int,
        include_inactive: bool,
        current_depth: int = 0
    ) -> Optional[OrganizationNodeResponse]:
        """
        組織ツリーノード構築（再帰処理）
        """
        # 非アクティブ会員の除外判定
        if not include_inactive and member.status != MemberStatus.ACTIVE:
            return None
        
        # 最大深度チェック
        if current_depth >= max_depth:
            return OrganizationNodeResponse(
                member_id=member.id,
                member_number=member.member_number,
                member_name=member.name,
                status=member.status,
                title=member.title,
                plan=member.plan,
                registration_date=member.registration_date,
                parent_member_id=member.parent_id,
                depth_level=current_depth,
                children=[],  # 最大深度のため子は空
                direct_children_count=0,
                total_downline_count=0,
                is_leaf=True,
                is_active=member.status == MemberStatus.ACTIVE
            )
        
        # 直下メンバー取得
        direct_children_query = self.db.query(Member).filter(Member.parent_id == member.id)
        if not include_inactive:
            direct_children_query = direct_children_query.filter(Member.status == MemberStatus.ACTIVE)
        
        direct_children = direct_children_query.all()
        
        # 子ノード構築（再帰）
        child_nodes = []
        total_downline = 0
        
        for child in direct_children:
            child_node = await self._build_tree_node(
                child,
                max_depth,
                include_inactive,
                current_depth + 1
            )
            
            if child_node:
                child_nodes.append(child_node)
                total_downline += child_node.total_downline_count + 1
        
        return OrganizationNodeResponse(
            member_id=member.id,
            member_number=member.member_number,
            member_name=member.name,
            status=member.status,
            title=member.title,
            plan=member.plan,
            registration_date=member.registration_date,
            
            # 組織情報
            parent_member_id=member.parent_id,
            depth_level=current_depth,
            
            # 子ノード
            children=child_nodes,
            direct_children_count=len(child_nodes),
            total_downline_count=total_downline,
            
            # 表示用
            is_leaf=len(child_nodes) == 0,
            is_active=member.status == MemberStatus.ACTIVE,
            formatted_registration_date=member.registration_date.strftime("%Y年%m月%d日") if member.registration_date else None
        )

    async def _get_direct_downline_count(self, member_id: int, include_inactive: bool = False) -> int:
        """
        直下メンバー数取得
        """
        query = self.db.query(Member).filter(Member.parent_id == member_id)
        if not include_inactive:
            query = query.filter(Member.status == MemberStatus.ACTIVE)
        
        return query.count()

    async def _get_total_downline_count(self, member_id: int, include_inactive: bool = False) -> int:
        """
        総配下メンバー数取得（再帰計算）
        """
        # 直下メンバー取得
        direct_query = self.db.query(Member).filter(Member.parent_id == member_id)
        if not include_inactive:
            direct_query = direct_query.filter(Member.status == MemberStatus.ACTIVE)
        
        direct_members = direct_query.all()
        total_count = len(direct_members)
        
        # 各直下メンバーの配下も再帰的に計算
        for direct_member in direct_members:
            total_count += await self._get_total_downline_count(direct_member.id, include_inactive)
        
        return total_count

    async def _calculate_organization_stats(self, include_inactive: bool = False) -> OrganizationStatsResponse:
        """
        組織統計情報計算
        """
        # 全会員数
        total_query = self.db.query(Member)
        if not include_inactive:
            total_query = total_query.filter(Member.status == MemberStatus.ACTIVE)
        total_members = total_query.count()
        
        # トップレベル会員数（直上者がいない）
        top_level_query = self.db.query(Member).filter(Member.parent_id.is_(None))
        if not include_inactive:
            top_level_query = top_level_query.filter(Member.status == MemberStatus.ACTIVE)
        top_level_count = top_level_query.count()
        
        # 最大深度計算
        max_depth = await self._calculate_max_organization_depth(include_inactive)
        
        # プラン別分布
        from app.models.member import Plan
        plan_distribution = {}
        for plan in Plan:
            plan_query = self.db.query(Member).filter(Member.plan == plan)
            if not include_inactive:
                plan_query = plan_query.filter(Member.status == MemberStatus.ACTIVE)
            plan_distribution[plan.value] = plan_query.count()
        
        # タイトル別分布
        from app.models.member import Title
        title_distribution = {}
        for title in Title:
            title_query = self.db.query(Member).filter(Member.title == title)
            if not include_inactive:
                title_query = title_query.filter(Member.status == MemberStatus.ACTIVE)
            title_distribution[title.value] = title_query.count()
        
        return OrganizationStatsResponse(
            total_members=total_members,
            top_level_members=top_level_count,
            max_organization_depth=max_depth,
            plan_distribution=plan_distribution,
            title_distribution=title_distribution,
            average_downline_per_member=total_members / max(top_level_count, 1),
            calculated_at=datetime.now()
        )

    async def _calculate_max_organization_depth(self, include_inactive: bool = False) -> int:
        """
        組織の最大深度計算
        """
        max_depth = 0
        
        # トップレベル会員から開始
        top_level_members = self.db.query(Member).filter(Member.parent_id.is_(None)).all()
        
        for top_member in top_level_members:
            if not include_inactive and top_member.status != MemberStatus.ACTIVE:
                continue
                
            depth = await self._calculate_member_depth(top_member.id, include_inactive)
            max_depth = max(max_depth, depth)
        
        return max_depth

    async def _calculate_member_depth(self, member_id: int, include_inactive: bool = False, current_depth: int = 0) -> int:
        """
        特定会員の組織深度計算（再帰）
        """
        # 直下メンバー取得
        direct_query = self.db.query(Member).filter(Member.parent_id == member_id)
        if not include_inactive:
            direct_query = direct_query.filter(Member.status == MemberStatus.ACTIVE)
        
        direct_members = direct_query.all()
        
        if not direct_members:
            return current_depth
        
        max_child_depth = current_depth
        
        # 各直下メンバーの深度を再帰計算
        for direct_member in direct_members:
            child_depth = await self._calculate_member_depth(
                direct_member.id, 
                include_inactive, 
                current_depth + 1
            )
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth

    async def validate_organization_integrity(self) -> Dict[str, Any]:
        """
        組織構造整合性チェック
        内部使用：循環参照・孤立ノードの検出
        """
        issues = []
        warnings = []
        
        # 全会員取得
        all_members = self.db.query(Member).all()
        
        for member in all_members:
            # 自分自身を親に指定していないかチェック
            if member.parent_id == member.id:
                issues.append(f"循環参照: 会員 {member.member_number} が自分自身を親に指定")
            
            # 親会員の存在チェック
            if member.parent_id:
                parent = self.db.query(Member).filter(Member.id == member.parent_id).first()
                if not parent:
                    issues.append(f"親会員不存在: 会員 {member.member_number} の親ID {member.parent_id} が見つかりません")
                
                # 循環参照チェック（深度制限付き）
                if await self._check_circular_reference(member.id, member.parent_id, max_check_depth=50):
                    issues.append(f"循環参照検出: 会員 {member.member_number} の組織経路で循環")
            
            # 紹介者の存在チェック
            if member.referrer_id:
                referrer = self.db.query(Member).filter(Member.id == member.referrer_id).first()
                if not referrer:
                    warnings.append(f"紹介者不存在: 会員 {member.member_number} の紹介者ID {member.referrer_id} が見つかりません")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_members_checked": len(all_members),
            "checked_at": datetime.now().isoformat()
        }

    async def _check_circular_reference(self, original_id: int, current_parent_id: int, max_check_depth: int = 50) -> bool:
        """
        循環参照チェック（再帰、深度制限付き）
        """
        if max_check_depth <= 0:
            return False  # 深度制限に達した場合は循環なしとみなす
        
        if current_parent_id == original_id:
            return True  # 循環参照発見
        
        # 親の親をチェック
        parent = self.db.query(Member).filter(Member.id == current_parent_id).first()
        if not parent or not parent.parent_id:
            return False  # 親がいない（ルート到達）
        
        return await self._check_circular_reference(original_id, parent.parent_id, max_check_depth - 1)