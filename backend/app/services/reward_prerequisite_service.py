"""
報酬計算前提確認サービス

Phase C-1a: 報酬計算前提確認API（4.1）
- B-1a（組織構造）+ B-2b（決済結果取込）完了後実装可能
- モックアップP-005対応

エンドポイント:
- 4.1 GET /api/rewards/check-prerequisites - 計算前提条件確認
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, distinct
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.member import Member, MemberStatus
from app.models.payment import Payment, PaymentStatus
from app.models.reward import RewardCalculation, CalculationStatus
from app.schemas.reward import RewardPrerequisiteResponse
from app.services.organization_service import OrganizationService
from app.services.activity_service import ActivityService


class RewardPrerequisiteService:
    """
    報酬計算前提確認サービスクラス
    計算実行前の必要条件チェックを担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)
        self.organization_service = OrganizationService(db)

    async def check_calculation_prerequisites(
        self,
        target_month: Optional[str] = None
    ) -> RewardPrerequisiteResponse:
        """
        報酬計算前提条件確認
        API 4.1: GET /api/rewards/check-prerequisites
        """
        # 対象月設定（未指定時は前月）
        if not target_month:
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            target_month = last_month.strftime("%Y-%m")
        
        # 各種前提条件チェック実行
        payment_check = await self._check_payment_data_status(target_month)
        organization_check = await self._check_organization_consistency()
        member_status_check = await self._check_member_status_updated()
        duplicate_check = await self._check_duplicate_calculation(target_month)
        
        # 統計情報取得
        target_stats = await self._get_target_member_statistics(target_month)
        history_info = await self._get_last_calculation_info()
        
        # 総合判定
        can_calculate = (
            payment_check["is_ready"] and
            organization_check["is_consistent"] and
            member_status_check["is_updated"] and
            duplicate_check["no_duplicates"]
        )
        
        prerequisite_met = can_calculate and len(self._get_blocking_issues(
            payment_check, organization_check, member_status_check, duplicate_check
        )) == 0
        
        # 警告・阻害要因収集
        warnings = []
        blocking_issues = []
        
        if not payment_check["is_ready"]:
            blocking_issues.extend(payment_check.get("issues", []))
        
        if not organization_check["is_consistent"]:
            blocking_issues.extend(organization_check.get("issues", []))
        
        if not member_status_check["is_updated"]:
            warnings.extend(member_status_check.get("warnings", []))
        
        if not duplicate_check["no_duplicates"]:
            blocking_issues.extend(duplicate_check.get("issues", []))
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="報酬計算前提確認",
            details=f"対象月: {target_month}, 実行可能: {can_calculate}, 対象者: {target_stats['target_members']}名",
            user_id="system"
        )
        
        return RewardPrerequisiteResponse(
            can_calculate=can_calculate,
            prerequisite_met=prerequisite_met,
            
            # 個別チェック結果
            payment_data_ready=payment_check["is_ready"],
            organization_consistent=organization_check["is_consistent"],
            member_status_updated=member_status_check["is_updated"],
            no_duplicate_calculation=duplicate_check["no_duplicates"],
            
            # チェック詳細
            payment_completion_rate=payment_check["completion_rate"],
            pending_payments=payment_check["pending_count"],
            organization_issues=organization_check.get("issues", []),
            member_data_issues=member_status_check.get("issues", []),
            
            # 計算対象統計
            target_members=target_stats["target_members"],
            active_members=target_stats["active_members"],
            eligible_for_bonus=target_stats["bonus_eligible"],
            
            # 過去計算履歴
            last_calculation_date=history_info.get("last_date"),
            last_calculation_month=history_info.get("last_month"),
            
            # 警告・注意事項
            warnings=warnings,
            blocking_issues=blocking_issues,
            
            # チェック実行情報
            checked_at=datetime.now(),
            check_duration_seconds=0.0  # 実際は処理時間を計測
        )

    async def _check_payment_data_status(self, target_month: str) -> Dict[str, Any]:
        """
        決済データ完了状況チェック
        """
        # 対象月のアクティブ会員取得
        active_members = self.db.query(Member).filter(
            Member.status == MemberStatus.ACTIVE
        ).all()
        
        # 決済完了状況確認
        completed_payments = self.db.query(Payment).filter(
            and_(
                Payment.target_month == target_month,
                Payment.status == PaymentStatus.COMPLETED
            )
        ).count()
        
        # 未完了決済取得
        pending_payments = self.db.query(Payment).filter(
            and_(
                Payment.target_month == target_month,
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.FAILED])
            )
        ).count()
        
        # 決済データ不足会員確認
        member_ids_with_payments = self.db.query(distinct(Payment.member_id)).filter(
            Payment.target_month == target_month
        ).subquery()
        
        members_without_payments = self.db.query(Member).filter(
            and_(
                Member.status == MemberStatus.ACTIVE,
                ~Member.id.in_(member_ids_with_payments)
            )
        ).all()
        
        total_expected = len(active_members)
        completion_rate = (completed_payments / total_expected * 100) if total_expected > 0 else 0
        
        issues = []
        if len(members_without_payments) > 0:
            issues.append(f"決済データ未登録: {len(members_without_payments)}名")
        
        if pending_payments > 0:
            issues.append(f"未完了決済: {pending_payments}件")
        
        return {
            "is_ready": completion_rate >= 95.0 and len(members_without_payments) == 0,
            "completion_rate": round(completion_rate, 2),
            "completed_count": completed_payments,
            "pending_count": pending_payments,
            "missing_payment_members": len(members_without_payments),
            "issues": issues
        }

    async def _check_organization_consistency(self) -> Dict[str, Any]:
        """
        組織図整合性チェック
        """
        integrity_result = await self.organization_service.validate_organization_integrity()
        
        return {
            "is_consistent": integrity_result["is_valid"],
            "issues": integrity_result["issues"],
            "warnings": integrity_result["warnings"],
            "total_members_checked": integrity_result["total_members_checked"]
        }

    async def _check_member_status_updated(self) -> Dict[str, Any]:
        """
        会員ステータス最新性チェック
        """
        # 最近更新されていない会員を検出
        stale_threshold = datetime.now() - timedelta(days=30)
        
        stale_members = self.db.query(Member).filter(
            and_(
                Member.status == MemberStatus.ACTIVE,
                Member.updated_at < stale_threshold
            )
        ).count()
        
        # 退会処理未完了の検出
        incomplete_withdrawals = self.db.query(Member).filter(
            and_(
                Member.status == MemberStatus.WITHDRAWN,
                Member.withdrawal_date.is_(None)
            )
        ).count()
        
        issues = []
        warnings = []
        
        if stale_members > 0:
            warnings.append(f"30日以上未更新の会員: {stale_members}名")
        
        if incomplete_withdrawals > 0:
            issues.append(f"退会日未設定の退会会員: {incomplete_withdrawals}名")
        
        return {
            "is_updated": incomplete_withdrawals == 0,
            "stale_members_count": stale_members,
            "incomplete_withdrawals": incomplete_withdrawals,
            "issues": issues,
            "warnings": warnings
        }

    async def _check_duplicate_calculation(self, target_month: str) -> Dict[str, Any]:
        """
        重複計算チェック
        """
        existing_calculations = self.db.query(RewardCalculation).filter(
            and_(
                RewardCalculation.calculation_month == target_month,
                RewardCalculation.status.in_([
                    CalculationStatus.RUNNING,
                    CalculationStatus.COMPLETED
                ])
            )
        ).all()
        
        issues = []
        if existing_calculations:
            for calc in existing_calculations:
                issues.append(f"既存計算あり: ID={calc.id}, ステータス={calc.status.value}")
        
        return {
            "no_duplicates": len(existing_calculations) == 0,
            "existing_calculations": len(existing_calculations),
            "issues": issues
        }

    async def _get_target_member_statistics(self, target_month: str) -> Dict[str, Any]:
        """
        計算対象者統計取得
        """
        # アクティブ会員数
        active_members = self.db.query(Member).filter(
            Member.status == MemberStatus.ACTIVE
        ).count()
        
        # 決済完了会員数（計算対象）
        target_members = self.db.query(distinct(Payment.member_id)).filter(
            and_(
                Payment.target_month == target_month,
                Payment.status == PaymentStatus.COMPLETED
            )
        ).count()
        
        # ボーナス別対象者数算出
        bonus_eligible = await self._calculate_bonus_eligible_counts(target_month)
        
        return {
            "target_members": target_members,
            "active_members": active_members,
            "bonus_eligible": bonus_eligible
        }

    async def _calculate_bonus_eligible_counts(self, target_month: str) -> Dict[str, int]:
        """
        ボーナス別対象者数算出
        """
        # 決済完了会員取得
        completed_payment_member_ids = self.db.query(Payment.member_id).filter(
            and_(
                Payment.target_month == target_month,
                Payment.status == PaymentStatus.COMPLETED
            )
        ).subquery()
        
        eligible_members = self.db.query(Member).filter(
            Member.id.in_(completed_payment_member_ids)
        ).all()
        
        bonus_counts = {
            "デイリーボーナス": len(eligible_members),  # 全決済完了者が対象
            "タイトルボーナス": len([m for m in eligible_members if m.title]),  # タイトル保持者
            "リファラルボーナス": 0,  # 直紹介者がいる会員（計算省略）
            "パワーボーナス": 0,  # 組織売上条件満たす会員（計算省略）
            "メンテナンスボーナス": 0,  # メンテナンスキット販売者（計算省略）
            "セールスアクティビティボーナス": 0,  # 新規紹介活動者（計算省略）
            "ロイヤルファミリーボーナス": 0  # 最高タイトル保持者（計算省略）
        }
        
        return bonus_counts

    async def _get_last_calculation_info(self) -> Dict[str, Any]:
        """
        最終計算情報取得
        """
        last_calculation = self.db.query(RewardCalculation).filter(
            RewardCalculation.status == CalculationStatus.COMPLETED
        ).order_by(RewardCalculation.created_at.desc()).first()
        
        if not last_calculation:
            return {}
        
        return {
            "last_date": last_calculation.created_at,
            "last_month": last_calculation.calculation_month,
            "last_id": last_calculation.id
        }

    def _get_blocking_issues(self, *check_results) -> List[str]:
        """
        計算阻害要因収集
        """
        blocking_issues = []
        
        for result in check_results:
            if isinstance(result, dict) and "issues" in result:
                blocking_issues.extend(result["issues"])
        
        return blocking_issues

    async def get_detailed_prerequisite_report(self, target_month: str) -> Dict[str, Any]:
        """
        詳細前提条件レポート取得
        内部使用：管理者向け詳細情報
        """
        prerequisite_result = await self.check_calculation_prerequisites(target_month)
        
        # 追加詳細情報
        payment_details = await self._get_payment_breakdown(target_month)
        member_breakdown = await self._get_member_status_breakdown()
        organization_metrics = await self._get_organization_metrics()
        
        return {
            "prerequisite_check": prerequisite_result,
            "payment_breakdown": payment_details,
            "member_breakdown": member_breakdown,
            "organization_metrics": organization_metrics,
            "recommendations": await self._generate_prerequisite_recommendations(prerequisite_result),
            "generated_at": datetime.now()
        }

    async def _get_payment_breakdown(self, target_month: str) -> Dict[str, Any]:
        """
        決済状況詳細分析
        """
        # 決済方法別集計
        from app.models.member import PaymentMethod
        
        payment_breakdown = {}
        
        for method in PaymentMethod:
            completed = self.db.query(Payment).filter(
                and_(
                    Payment.target_month == target_month,
                    Payment.payment_method == method,
                    Payment.status == PaymentStatus.COMPLETED
                )
            ).count()
            
            pending = self.db.query(Payment).filter(
                and_(
                    Payment.target_month == target_month,
                    Payment.payment_method == method,
                    Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.FAILED])
                )
            ).count()
            
            payment_breakdown[method.value] = {
                "completed": completed,
                "pending": pending,
                "total": completed + pending
            }
        
        return payment_breakdown

    async def _get_member_status_breakdown(self) -> Dict[str, Any]:
        """
        会員ステータス詳細分析
        """
        status_counts = {}
        
        for status in MemberStatus:
            count = self.db.query(Member).filter(Member.status == status).count()
            status_counts[status.value] = count
        
        return {
            "status_distribution": status_counts,
            "total_members": sum(status_counts.values()),
            "active_ratio": status_counts.get("アクティブ", 0) / max(sum(status_counts.values()), 1) * 100
        }

    async def _get_organization_metrics(self) -> Dict[str, Any]:
        """
        組織構造メトリクス
        """
        org_stats = await self.organization_service._calculate_organization_stats(include_inactive=False)
        
        return {
            "total_active_members": org_stats.total_members,
            "top_level_members": org_stats.top_level_members,
            "max_depth": org_stats.max_organization_depth,
            "average_downline": org_stats.average_downline_per_member
        }

    async def _generate_prerequisite_recommendations(
        self, 
        prerequisite_result: RewardPrerequisiteResponse
    ) -> List[str]:
        """
        前提条件に基づく推奨事項生成
        """
        recommendations = []
        
        if not prerequisite_result.payment_data_ready:
            recommendations.append("決済データの完了を待ってから計算を実行してください")
        
        if not prerequisite_result.organization_consistent:
            recommendations.append("組織図の整合性問題を解決してから計算してください")
        
        if prerequisite_result.pending_payments > 0:
            recommendations.append(f"未完了決済 {prerequisite_result.pending_payments}件の処理完了を推奨")
        
        if prerequisite_result.payment_completion_rate < 100:
            recommendations.append(f"決済完了率 {prerequisite_result.payment_completion_rate}% - 100%達成を推奨")
        
        return recommendations