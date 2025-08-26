"""
スポンサー変更・退会処理サービス

Phase B-1b: スポンサー変更API（1.5, 1.7）
- B-1a（組織構造）完了後実装可能
- モックアップP-002対応

エンドポイント:
- 1.5 DELETE /api/members/{id} - 会員退会処理
- 1.7 PUT /api/members/{id}/sponsor - スポンサー変更
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.models.member import Member, MemberStatus
from app.schemas.member import (
    MemberWithdrawalRequest,
    MemberWithdrawalResponse,
    SponsorChangeRequest,
    SponsorChangeResponse
)
from app.services.organization_service import OrganizationService
from app.services.activity_service import ActivityService


class SponsorChangeService:
    """
    スポンサー変更・退会処理サービスクラス
    組織構造の変更と退会時の組織調整を担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)
        self.organization_service = OrganizationService(db)

    async def withdraw_member(
        self,
        member_id: int,
        withdrawal_request: MemberWithdrawalRequest
    ) -> MemberWithdrawalResponse:
        """
        会員退会処理
        API 1.5: DELETE /api/members/{id}
        要件: 退会後、手動で組織調整を行う（自動圧縮NG）
        """
        # 会員存在確認
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"会員ID {member_id} は存在しません")
        
        if member.status == MemberStatus.WITHDRAWN:
            raise ValueError(f"会員 {member.member_number} は既に退会済みです")
        
        # 配下メンバー確認
        downline_members = await self._get_all_downline_members(member_id)
        
        if downline_members and not withdrawal_request.force_withdrawal:
            # 配下メンバーがいる場合の確認
            return MemberWithdrawalResponse(
                member_id=member_id,
                member_number=member.member_number,
                member_name=member.name,
                withdrawal_status="confirmation_required",
                affected_downline_count=len(downline_members),
                affected_downline_members=downline_members[:10],  # 最初の10名のみ表示
                
                # 組織調整オプション
                organization_adjustment_required=True,
                suggested_adjustments=await self._suggest_organization_adjustments(member_id),
                
                # 確認用情報
                confirmation_required=True,
                warnings=[
                    f"{len(downline_members)}名の配下メンバーが存在します",
                    "退会実行前に組織調整が必要です",
                    "配下メンバーの新しいスポンサーを指定してください"
                ],
                
                withdrawal_completed=False,
                processed_at=datetime.now()
            )
        
        # 退会処理実行
        old_status = member.status
        member.status = MemberStatus.WITHDRAWN
        member.withdrawal_date = withdrawal_request.withdrawal_date or datetime.now()
        member.updated_at = datetime.now()
        
        # 退会理由記録
        if withdrawal_request.withdrawal_reason:
            withdrawal_note = f"[{datetime.now().strftime('%Y-%m-%d')}] 退会理由: {withdrawal_request.withdrawal_reason}"
            if member.remarks:
                member.remarks += f"\n{withdrawal_note}"
            else:
                member.remarks = withdrawal_note
        
        self.db.commit()
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="会員退会処理",
            details=f"会員: {member.member_number}({member.name}), 配下: {len(downline_members)}名, 理由: {withdrawal_request.withdrawal_reason or '未記載'}",
            user_id="system",
            target_id=member_id
        )
        
        return MemberWithdrawalResponse(
            member_id=member_id,
            member_number=member.member_number,
            member_name=member.name,
            withdrawal_status="completed",
            withdrawal_date=member.withdrawal_date,
            affected_downline_count=len(downline_members),
            affected_downline_members=downline_members,
            
            # 組織調整情報
            organization_adjustment_required=len(downline_members) > 0,
            pending_adjustments=len(downline_members),
            
            # 処理結果
            confirmation_required=False,
            warnings=[] if len(downline_members) == 0 else [
                f"配下メンバー {len(downline_members)}名の組織調整が必要です"
            ],
            
            withdrawal_completed=True,
            processed_at=datetime.now(),
            previous_status=old_status
        )

    async def change_sponsor(
        self,
        member_id: int,
        sponsor_change_request: SponsorChangeRequest
    ) -> SponsorChangeResponse:
        """
        スポンサー変更
        API 1.7: PUT /api/members/{id}/sponsor
        """
        # 対象会員確認
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"会員ID {member_id} は存在しません")
        
        # 新スポンサー確認
        new_sponsor = None
        if sponsor_change_request.new_sponsor_id:
            new_sponsor = self.db.query(Member).filter(
                Member.id == sponsor_change_request.new_sponsor_id
            ).first()
            if not new_sponsor:
                raise ValueError(f"新スポンサーID {sponsor_change_request.new_sponsor_id} は存在しません")
            
            if new_sponsor.status != MemberStatus.ACTIVE:
                raise ValueError(f"新スポンサー {new_sponsor.member_number} は非アクティブです")
        
        # 循環参照チェック
        if sponsor_change_request.new_sponsor_id:
            if await self._check_circular_reference(member_id, sponsor_change_request.new_sponsor_id):
                raise ValueError("循環参照が発生するため、この変更はできません")
        
        # 組織影響度分析
        impact_analysis = await self._analyze_sponsor_change_impact(
            member_id, 
            sponsor_change_request.new_sponsor_id
        )
        
        # 変更実行前の確認
        if not sponsor_change_request.confirmed and impact_analysis["high_impact"]:
            return SponsorChangeResponse(
                member_id=member_id,
                member_number=member.member_number,
                member_name=member.name,
                change_status="confirmation_required",
                
                # 変更前情報
                old_sponsor_id=member.parent_id,
                old_sponsor_name=member.parent_name,
                new_sponsor_id=sponsor_change_request.new_sponsor_id,
                new_sponsor_name=new_sponsor.name if new_sponsor else None,
                
                # 影響分析
                impact_analysis=impact_analysis,
                confirmation_required=True,
                warnings=impact_analysis.get("warnings", []),
                
                # 処理状況
                change_completed=False,
                processed_at=datetime.now()
            )
        
        # スポンサー変更実行
        old_sponsor_id = member.parent_id
        old_sponsor_name = member.parent_name
        
        member.parent_id = sponsor_change_request.new_sponsor_id
        member.parent_name = new_sponsor.name if new_sponsor else None
        member.updated_at = datetime.now()
        
        # 変更履歴記録
        change_note = f"[{datetime.now().strftime('%Y-%m-%d')}] スポンサー変更: {old_sponsor_name or 'なし'} → {new_sponsor.name if new_sponsor else 'なし'}"
        if sponsor_change_request.change_reason:
            change_note += f" (理由: {sponsor_change_request.change_reason})"
        
        if member.remarks:
            member.remarks += f"\n{change_note}"
        else:
            member.remarks = change_note
        
        self.db.commit()
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="スポンサー変更",
            details=f"会員: {member.member_number}({member.name}), 変更: {old_sponsor_name or 'なし'} → {new_sponsor.name if new_sponsor else 'なし'}",
            user_id="system",
            target_id=member_id
        )
        
        return SponsorChangeResponse(
            member_id=member_id,
            member_number=member.member_number,
            member_name=member.name,
            change_status="completed",
            
            # 変更情報
            old_sponsor_id=old_sponsor_id,
            old_sponsor_name=old_sponsor_name,
            new_sponsor_id=sponsor_change_request.new_sponsor_id,
            new_sponsor_name=new_sponsor.name if new_sponsor else None,
            change_reason=sponsor_change_request.change_reason,
            
            # 影響分析
            impact_analysis=impact_analysis,
            affected_members_count=impact_analysis.get("affected_count", 0),
            
            # 処理結果
            confirmation_required=False,
            warnings=[],
            change_completed=True,
            processed_at=datetime.now(),
            effective_date=sponsor_change_request.effective_date or datetime.now()
        )

    async def get_organization_adjustment_options(
        self,
        withdrawing_member_id: int
    ) -> Dict[str, Any]:
        """
        組織調整オプション取得
        退会時の配下メンバー再配置案を提示
        """
        member = self.db.query(Member).filter(Member.id == withdrawing_member_id).first()
        if not member:
            raise ValueError(f"会員ID {withdrawing_member_id} は存在しません")
        
        # 配下メンバー取得
        downline_members = await self._get_all_downline_members(withdrawing_member_id)
        
        # 調整オプション生成
        adjustment_options = []
        
        # オプション1: 上位スポンサーに統合
        if member.parent_id:
            parent = self.db.query(Member).filter(Member.id == member.parent_id).first()
            if parent and parent.status == MemberStatus.ACTIVE:
                adjustment_options.append({
                    "option_type": "merge_to_parent",
                    "description": f"配下メンバーを上位スポンサー {parent.name} に統合",
                    "target_sponsor_id": parent.id,
                    "target_sponsor_name": parent.name,
                    "affected_members": len(downline_members),
                    "advantages": ["組織構造の維持", "上位スポンサーによる継続支援"],
                    "disadvantages": ["上位スポンサーの負担増加"]
                })
        
        # オプション2: 同レベル会員への分散
        sibling_members = await self._get_sibling_members(withdrawing_member_id)
        active_siblings = [s for s in sibling_members if s.status == MemberStatus.ACTIVE]
        
        if active_siblings:
            for sibling in active_siblings[:3]:  # 最大3名まで提案
                adjustment_options.append({
                    "option_type": "transfer_to_sibling",
                    "description": f"配下メンバーを同レベル会員 {sibling.name} に移管",
                    "target_sponsor_id": sibling.id,
                    "target_sponsor_name": sibling.name,
                    "affected_members": len(downline_members),
                    "advantages": ["同レベルでの継続支援"],
                    "disadvantages": ["既存関係性の変化"]
                })
        
        # オプション3: 個別指定
        adjustment_options.append({
            "option_type": "manual_assignment",
            "description": "配下メンバーごとに個別にスポンサーを指定",
            "target_sponsor_id": None,
            "target_sponsor_name": "個別指定",
            "affected_members": len(downline_members),
            "advantages": ["最適なマッチング可能"],
            "disadvantages": ["作業負荷が高い"]
        })
        
        return {
            "withdrawing_member": {
                "id": member.id,
                "number": member.member_number,
                "name": member.name
            },
            "downline_members_count": len(downline_members),
            "downline_members": [
                {
                    "id": dm.id,
                    "number": dm.member_number,
                    "name": dm.name,
                    "status": dm.status,
                    "title": dm.title
                }
                for dm in downline_members[:20]  # 最大20名表示
            ],
            "adjustment_options": adjustment_options,
            "recommended_option": adjustment_options[0] if adjustment_options else None,
            "generated_at": datetime.now()
        }

    async def execute_organization_adjustment(
        self,
        adjustments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        組織調整実行
        退会後の配下メンバー再配置を実行
        """
        results = {
            "total_adjustments": len(adjustments),
            "successful_adjustments": 0,
            "failed_adjustments": 0,
            "adjustment_details": [],
            "errors": []
        }
        
        for adjustment in adjustments:
            try:
                member_id = adjustment["member_id"]
                new_sponsor_id = adjustment.get("new_sponsor_id")
                
                # スポンサー変更実行
                change_request = SponsorChangeRequest(
                    new_sponsor_id=new_sponsor_id,
                    change_reason=f"組織調整（退会者配下再配置）",
                    confirmed=True
                )
                
                change_result = await self.change_sponsor(member_id, change_request)
                
                if change_result.change_completed:
                    results["successful_adjustments"] += 1
                    results["adjustment_details"].append({
                        "member_id": member_id,
                        "status": "success",
                        "details": change_result
                    })
                else:
                    results["failed_adjustments"] += 1
                    results["errors"].append(f"会員ID {member_id} の調整に失敗")
                    
            except Exception as e:
                results["failed_adjustments"] += 1
                results["errors"].append(f"会員ID {adjustment.get('member_id', 'unknown')}: {str(e)}")
        
        # 調整結果ログ
        await self.activity_service.log_activity(
            action="組織調整実行",
            details=f"総数: {results['total_adjustments']}, 成功: {results['successful_adjustments']}, 失敗: {results['failed_adjustments']}",
            user_id="system"
        )
        
        return results

    async def _get_all_downline_members(self, member_id: int) -> List[Member]:
        """
        全配下メンバー取得（再帰）
        """
        downline = []
        
        # 直下メンバー取得
        direct_members = self.db.query(Member).filter(Member.parent_id == member_id).all()
        
        for direct_member in direct_members:
            downline.append(direct_member)
            # 再帰的に配下の配下も取得
            sub_downline = await self._get_all_downline_members(direct_member.id)
            downline.extend(sub_downline)
        
        return downline

    async def _get_sibling_members(self, member_id: int) -> List[Member]:
        """
        同レベル会員（兄弟会員）取得
        """
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member or not member.parent_id:
            return []
        
        # 同じ親を持つ会員を取得（自分以外）
        siblings = self.db.query(Member).filter(
            and_(
                Member.parent_id == member.parent_id,
                Member.id != member_id
            )
        ).all()
        
        return siblings

    async def _suggest_organization_adjustments(self, member_id: int) -> List[Dict[str, Any]]:
        """
        組織調整案提案
        """
        member = self.db.query(Member).filter(Member.id == member_id).first()
        suggestions = []
        
        # 上位スポンサーへの統合案
        if member.parent_id:
            suggestions.append({
                "type": "merge_to_parent",
                "description": "配下メンバーを上位スポンサーに統合",
                "priority": "high"
            })
        
        # 同レベル分散案
        siblings = await self._get_sibling_members(member_id)
        if siblings:
            suggestions.append({
                "type": "distribute_to_siblings",
                "description": "配下メンバーを同レベル会員に分散",
                "priority": "medium"
            })
        
        return suggestions

    async def _analyze_sponsor_change_impact(
        self,
        member_id: int,
        new_sponsor_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        スポンサー変更影響分析
        """
        member = self.db.query(Member).filter(Member.id == member_id).first()
        downline_count = await self.organization_service._get_total_downline_count(member_id)
        
        analysis = {
            "high_impact": downline_count > 5,
            "affected_count": downline_count,
            "depth_change": 0,  # 詳細実装省略
            "warnings": [],
            "recommendations": []
        }
        
        if downline_count > 10:
            analysis["warnings"].append(f"大規模組織変更: {downline_count}名に影響")
        
        if downline_count > 0:
            analysis["recommendations"].append("変更前に配下メンバーへの通知を推奨")
        
        return analysis

    async def _check_circular_reference(self, member_id: int, new_parent_id: int) -> bool:
        """
        循環参照チェック
        """
        # 新しい親が自分の配下にいるかチェック
        downline_members = await self._get_all_downline_members(member_id)
        downline_ids = [dm.id for dm in downline_members]
        
        return new_parent_id in downline_ids