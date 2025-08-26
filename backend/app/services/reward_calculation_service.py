"""
報酬計算実行サービス

Phase C-1b: 報酬計算実行API（4.2）
- C-1a（前提確認）完了後実装可能
- モックアップP-005対応

エンドポイント:
- 4.2 POST /api/rewards/calculate - 報酬計算実行

要件定義書の7種類のボーナス完全実装:
1. デイリーボーナス - 参加費に応じた日割り報酬
2. タイトルボーナス - タイトルに応じた固定報酬
3. リファラルボーナス - 直紹介者の参加費の50%
4. パワーボーナス - 組織売上に応じた報酬
5. メンテナンスボーナス - センターメンテナンスキット販売報酬
6. セールスアクティビティボーナス - 新規紹介活動報酬
7. ロイヤルファミリーボーナス - 最高タイトル保持者への特別報酬
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import asyncio

from app.models.member import Member, MemberStatus, Title, Plan, PaymentMethod
from app.models.payment import Payment, PaymentStatus
from app.models.reward import (
    RewardCalculation, Reward, BonusType, 
    CalculationStatus, PaymentStatus as RewardPaymentStatus
)
from app.schemas.reward import (
    RewardCalculationRequest, RewardCalculationResponse,
    RewardCalculationProgress
)
from app.services.reward_prerequisite_service import RewardPrerequisiteService
from app.services.organization_service import OrganizationService
from app.services.activity_service import ActivityService


class RewardCalculationService:
    """
    報酬計算実行サービスクラス
    7種類のボーナス計算ロジックを担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)
        self.prerequisite_service = RewardPrerequisiteService(db)
        self.organization_service = OrganizationService(db)

    async def calculate_rewards(
        self,
        calculation_request: RewardCalculationRequest
    ) -> RewardCalculationResponse:
        """
        報酬計算実行
        API 4.2: POST /api/rewards/calculate
        """
        started_at = datetime.now()
        
        try:
            # 前提条件チェック
            if not calculation_request.dry_run:
                prerequisite_result = await self.prerequisite_service.check_calculation_prerequisites(
                    calculation_request.calculation_month
                )
                
                if not prerequisite_result.can_calculate:
                    raise ValueError(f"計算前提条件未充足: {prerequisite_result.blocking_issues}")
            
            # 既存計算の削除（再計算時）
            if calculation_request.recalculate_existing:
                await self._delete_existing_calculations(calculation_request.calculation_month)
            
            # 計算実行レコード作成
            calculation = RewardCalculation(
                calculation_month=calculation_request.calculation_month,
                calculation_type=calculation_request.calculation_type,
                status=CalculationStatus.RUNNING,
                started_at=started_at,
                target_bonuses=calculation_request.target_bonuses or [],
                is_dry_run=calculation_request.dry_run,
                created_at=started_at
            )
            
            if not calculation_request.dry_run:
                self.db.add(calculation)
                self.db.commit()
                self.db.refresh(calculation)
            else:
                calculation.id = 0  # ドライラン用
            
            # 対象会員取得
            target_members = await self._get_target_members(
                calculation_request.calculation_month,
                calculation_request.target_members
            )
            
            # 7種類のボーナス計算実行
            bonus_results = {}
            total_amount = Decimal('0')
            target_bonuses = calculation_request.target_bonuses or list(BonusType)
            
            for bonus_type in target_bonuses:
                bonus_result = await self._calculate_bonus_by_type(
                    bonus_type,
                    target_members,
                    calculation_request.calculation_month,
                    calculation.id if not calculation_request.dry_run else 0,
                    calculation_request.dry_run
                )
                
                bonus_results[bonus_type.value] = bonus_result
                total_amount += bonus_result["total_amount"]
            
            completed_at = datetime.now()
            
            # 計算完了処理
            if not calculation_request.dry_run:
                calculation.status = CalculationStatus.COMPLETED
                calculation.completed_at = completed_at
                calculation.total_amount = total_amount
                calculation.target_member_count = len(target_members)
                
                self.db.commit()
            
            # 統計情報生成
            payment_stats, member_stats = await self._generate_calculation_stats(
                bonus_results, target_members
            )
            
            # アクティビティログ記録
            await self.activity_service.log_activity(
                action="報酬計算実行",
                details=f"対象月: {calculation_request.calculation_month}, 対象者: {len(target_members)}名, 総額: ¥{total_amount:,}, ドライラン: {calculation_request.dry_run}",
                user_id="system",
                target_id=calculation.id if not calculation_request.dry_run else None
            )
            
            return RewardCalculationResponse(
                calculation_id=calculation.id,
                calculation_month=calculation_request.calculation_month,
                calculation_type=calculation_request.calculation_type,
                status=CalculationStatus.COMPLETED,
                
                # 実行結果サマリー
                total_amount=total_amount,
                target_member_count=len(target_members),
                carryover_member_count=sum(1 for _, stats in member_stats.items() if stats.get("total_reward", 0) < 5000),
                execution_time_seconds=(completed_at - started_at).total_seconds(),
                
                # ボーナス別集計
                bonus_summary=bonus_results,
                
                # 統計情報
                payment_stats=payment_stats,
                member_stats=member_stats,
                
                # 実行情報
                started_at=started_at,
                completed_at=completed_at,
                
                # エラー情報
                error_message=None,
                warnings=[]
            )
            
        except Exception as e:
            # 計算エラー処理
            if 'calculation' in locals() and not calculation_request.dry_run:
                calculation.status = CalculationStatus.FAILED
                calculation.error_message = str(e)
                calculation.completed_at = datetime.now()
                self.db.commit()
            
            await self.activity_service.log_activity(
                action="報酬計算実行失敗",
                details=f"対象月: {calculation_request.calculation_month}, エラー: {str(e)}",
                user_id="system"
            )
            
            return RewardCalculationResponse(
                calculation_id=calculation.id if 'calculation' in locals() else 0,
                calculation_month=calculation_request.calculation_month,
                calculation_type=calculation_request.calculation_type,
                status=CalculationStatus.FAILED,
                total_amount=Decimal('0'),
                target_member_count=0,
                carryover_member_count=0,
                execution_time_seconds=0,
                bonus_summary={},
                payment_stats={},
                member_stats={},
                started_at=started_at,
                completed_at=datetime.now(),
                error_message=str(e),
                warnings=[]
            )

    async def _get_target_members(
        self,
        calculation_month: str,
        target_member_ids: Optional[List[str]] = None
    ) -> List[Member]:
        """
        計算対象会員取得
        """
        # ベースクエリ（決済完了会員）
        completed_payment_member_ids = self.db.query(Payment.member_id).filter(
            and_(
                Payment.target_month == calculation_month,
                Payment.status == PaymentStatus.COMPLETED
            )
        ).subquery()
        
        query = self.db.query(Member).filter(
            and_(
                Member.status == MemberStatus.ACTIVE,
                Member.id.in_(completed_payment_member_ids)
            )
        )
        
        # 特定会員指定時
        if target_member_ids:
            query = query.filter(Member.member_number.in_(target_member_ids))
        
        return query.all()

    async def _calculate_bonus_by_type(
        self,
        bonus_type: BonusType,
        target_members: List[Member],
        calculation_month: str,
        calculation_id: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        ボーナス種別別計算実行
        """
        if bonus_type == BonusType.DAILY:
            return await self._calculate_daily_bonus(target_members, calculation_month, calculation_id, dry_run)
        elif bonus_type == BonusType.TITLE:
            return await self._calculate_title_bonus(target_members, calculation_month, calculation_id, dry_run)
        elif bonus_type == BonusType.REFERRAL:
            return await self._calculate_referral_bonus(target_members, calculation_month, calculation_id, dry_run)
        elif bonus_type == BonusType.POWER:
            return await self._calculate_power_bonus(target_members, calculation_month, calculation_id, dry_run)
        elif bonus_type == BonusType.MAINTENANCE:
            return await self._calculate_maintenance_bonus(target_members, calculation_month, calculation_id, dry_run)
        elif bonus_type == BonusType.SALES_ACTIVITY:
            return await self._calculate_sales_activity_bonus(target_members, calculation_month, calculation_id, dry_run)
        elif bonus_type == BonusType.ROYAL_FAMILY:
            return await self._calculate_royal_family_bonus(target_members, calculation_month, calculation_id, dry_run)
        else:
            return {"total_amount": Decimal('0'), "recipient_count": 0, "details": {}}

    async def _calculate_daily_bonus(
        self, target_members: List[Member], calculation_month: str, calculation_id: int, dry_run: bool
    ) -> Dict[str, Any]:
        """
        デイリーボーナス計算
        参加費に応じた日割り報酬
        """
        total_amount = Decimal('0')
        recipient_count = 0
        details = {}
        
        # 対象月の日数算出
        year, month = map(int, calculation_month.split('-'))
        if month == 12:
            next_month_start = datetime(year + 1, 1, 1)
        else:
            next_month_start = datetime(year, month + 1, 1)
        
        month_start = datetime(year, month, 1)
        days_in_month = (next_month_start - month_start).days
        
        for member in target_members:
            # 参加費取得
            payment = self.db.query(Payment).filter(
                and_(
                    Payment.member_id == member.id,
                    Payment.target_month == calculation_month,
                    Payment.status == PaymentStatus.COMPLETED
                )
            ).first()
            
            if not payment:
                continue
            
            # デイリーボーナス = 参加費 × 100% ÷ 月日数
            daily_amount = (payment.amount * Decimal('1.0') / Decimal(str(days_in_month))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            monthly_amount = daily_amount * Decimal(str(days_in_month))
            
            if not dry_run:
                reward = Reward(
                    member_id=member.id,
                    calculation_id=calculation_id,
                    bonus_type=BonusType.DAILY,
                    amount=monthly_amount,
                    calculation_details={
                        "base_amount": str(payment.amount),
                        "days_in_month": days_in_month,
                        "daily_amount": str(daily_amount),
                        "formula": "参加費 × 100%"
                    },
                    payment_status=RewardPaymentStatus.PENDING,
                    created_at=datetime.now()
                )
                self.db.add(reward)
            
            total_amount += monthly_amount
            recipient_count += 1
            details[member.member_number] = {
                "amount": monthly_amount,
                "base_payment": payment.amount,
                "daily_rate": daily_amount
            }
        
        return {
            "total_amount": total_amount,
            "recipient_count": recipient_count,
            "details": details,
            "formula": "参加費 × 100% ÷ 月日数"
        }

    async def _calculate_title_bonus(
        self, target_members: List[Member], calculation_month: str, calculation_id: int, dry_run: bool
    ) -> Dict[str, Any]:
        """
        タイトルボーナス計算
        タイトルに応じた固定報酬
        """
        # タイトル別固定額設定（要件定義書参照）
        title_bonus_amounts = {
            Title.START: Decimal('1000'),
            Title.LEADER: Decimal('3000'),
            Title.SUB_MANAGER: Decimal('5000'),
            Title.MANAGER: Decimal('10000'),
            Title.EXPERT_MANAGER: Decimal('20000'),
            Title.DIRECTOR: Decimal('50000'),
            Title.AREA_DIRECTOR: Decimal('100000')
        }
        
        total_amount = Decimal('0')
        recipient_count = 0
        details = {}
        
        for member in target_members:
            if not member.title or member.title == Title.NONE:
                continue
            
            bonus_amount = title_bonus_amounts.get(member.title, Decimal('0'))
            if bonus_amount <= 0:
                continue
            
            if not dry_run:
                reward = Reward(
                    member_id=member.id,
                    calculation_id=calculation_id,
                    bonus_type=BonusType.TITLE,
                    amount=bonus_amount,
                    calculation_details={
                        "title": member.title.value,
                        "bonus_amount": str(bonus_amount),
                        "formula": f"タイトル別固定額: {member.title.value}"
                    },
                    payment_status=RewardPaymentStatus.PENDING,
                    created_at=datetime.now()
                )
                self.db.add(reward)
            
            total_amount += bonus_amount
            recipient_count += 1
            details[member.member_number] = {
                "amount": bonus_amount,
                "title": member.title.value
            }
        
        return {
            "total_amount": total_amount,
            "recipient_count": recipient_count,
            "details": details,
            "formula": "タイトル別固定額"
        }

    async def _calculate_referral_bonus(
        self, target_members: List[Member], calculation_month: str, calculation_id: int, dry_run: bool
    ) -> Dict[str, Any]:
        """
        リファラルボーナス計算
        直紹介者の参加費の50%
        """
        total_amount = Decimal('0')
        recipient_count = 0
        details = {}
        
        for member in target_members:
            # 直紹介者取得（referrer_idが自分のID）
            direct_referrals = self.db.query(Member).filter(
                and_(
                    Member.referrer_id == member.id,
                    Member.status == MemberStatus.ACTIVE
                )
            ).all()
            
            member_total = Decimal('0')
            referral_details = []
            
            for referral in direct_referrals:
                # 直紹介者の当月決済取得
                referral_payment = self.db.query(Payment).filter(
                    and_(
                        Payment.member_id == referral.id,
                        Payment.target_month == calculation_month,
                        Payment.status == PaymentStatus.COMPLETED
                    )
                ).first()
                
                if referral_payment:
                    # リファラルボーナス = 直紹介者参加費 × 50%
                    referral_bonus = (referral_payment.amount * Decimal('0.5')).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )
                    
                    member_total += referral_bonus
                    referral_details.append({
                        "referral_member": referral.member_number,
                        "referral_name": referral.name,
                        "base_amount": referral_payment.amount,
                        "bonus_amount": referral_bonus
                    })
            
            if member_total > 0:
                if not dry_run:
                    reward = Reward(
                        member_id=member.id,
                        calculation_id=calculation_id,
                        bonus_type=BonusType.REFERRAL,
                        amount=member_total,
                        calculation_details={
                            "direct_referrals_count": len(referral_details),
                            "referral_details": referral_details,
                            "formula": "直紹介者参加費 × 50%"
                        },
                        payment_status=RewardPaymentStatus.PENDING,
                        created_at=datetime.now()
                    )
                    self.db.add(reward)
                
                total_amount += member_total
                recipient_count += 1
                details[member.member_number] = {
                    "amount": member_total,
                    "referral_count": len(referral_details),
                    "referrals": referral_details
                }
        
        return {
            "total_amount": total_amount,
            "recipient_count": recipient_count,
            "details": details,
            "formula": "直紹介者参加費 × 50%"
        }

    async def _calculate_power_bonus(
        self, target_members: List[Member], calculation_month: str, calculation_id: int, dry_run: bool
    ) -> Dict[str, Any]:
        """
        パワーボーナス計算
        組織売上に応じた報酬
        """
        total_amount = Decimal('0')
        recipient_count = 0
        details = {}
        
        # パワーボーナス料率テーブル（組織売上に応じた段階的料率）
        power_bonus_rates = [
            (Decimal('100000'), Decimal('0.01')),   # 10万円以上: 1%
            (Decimal('500000'), Decimal('0.02')),   # 50万円以上: 2%
            (Decimal('1000000'), Decimal('0.03')),  # 100万円以上: 3%
            (Decimal('3000000'), Decimal('0.04')),  # 300万円以上: 4%
            (Decimal('5000000'), Decimal('0.05'))   # 500万円以上: 5%
        ]
        
        for member in target_members:
            # 組織売上計算（配下全員の決済合計）
            downline_members = await self.organization_service._get_all_downline_members(member.id)
            downline_ids = [dm.id for dm in downline_members] + [member.id]  # 自分含む
            
            # 組織売上合計
            organization_sales = self.db.query(func.sum(Payment.amount)).filter(
                and_(
                    Payment.member_id.in_(downline_ids),
                    Payment.target_month == calculation_month,
                    Payment.status == PaymentStatus.COMPLETED
                )
            ).scalar() or Decimal('0')
            
            # 料率決定
            bonus_rate = Decimal('0')
            for threshold, rate in reversed(power_bonus_rates):
                if organization_sales >= threshold:
                    bonus_rate = rate
                    break
            
            if bonus_rate > 0:
                power_bonus = (organization_sales * bonus_rate).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                
                if not dry_run:
                    reward = Reward(
                        member_id=member.id,
                        calculation_id=calculation_id,
                        bonus_type=BonusType.POWER,
                        amount=power_bonus,
                        calculation_details={
                            "organization_sales": str(organization_sales),
                            "bonus_rate": str(bonus_rate * 100) + "%",
                            "downline_count": len(downline_members),
                            "formula": f"組織売上 {organization_sales:,}円 × {bonus_rate * 100}%"
                        },
                        payment_status=RewardPaymentStatus.PENDING,
                        created_at=datetime.now()
                    )
                    self.db.add(reward)
                
                total_amount += power_bonus
                recipient_count += 1
                details[member.member_number] = {
                    "amount": power_bonus,
                    "organization_sales": organization_sales,
                    "bonus_rate": bonus_rate,
                    "downline_count": len(downline_members)
                }
        
        return {
            "total_amount": total_amount,
            "recipient_count": recipient_count,
            "details": details,
            "formula": "組織売上 × 段階的料率"
        }

    async def _calculate_maintenance_bonus(
        self, target_members: List[Member], calculation_month: str, calculation_id: int, dry_run: bool
    ) -> Dict[str, Any]:
        """
        メンテナンスボーナス計算
        センターメンテナンスキット販売報酬
        """
        # 現在は販売実績データがないため0円で実装
        # 将来的には販売実績テーブルから集計
        return {
            "total_amount": Decimal('0'),
            "recipient_count": 0,
            "details": {},
            "formula": "メンテナンスキット販売実績 × 報酬率（未実装）"
        }

    async def _calculate_sales_activity_bonus(
        self, target_members: List[Member], calculation_month: str, calculation_id: int, dry_run: bool
    ) -> Dict[str, Any]:
        """
        セールスアクティビティボーナス計算
        新規紹介活動報酬
        """
        # 現在は紹介活動実績データがないため0円で実装
        # 将来的には活動実績テーブルから集計
        return {
            "total_amount": Decimal('0'),
            "recipient_count": 0,
            "details": {},
            "formula": "新規紹介活動実績 × 報酬率（未実装）"
        }

    async def _calculate_royal_family_bonus(
        self, target_members: List[Member], calculation_month: str, calculation_id: int, dry_run: bool
    ) -> Dict[str, Any]:
        """
        ロイヤルファミリーボーナス計算
        最高タイトル保持者への特別報酬
        """
        # エリアディレクター（最高タイトル）保持者に特別報酬
        royal_bonus_amount = Decimal('50000')  # 固定額
        
        total_amount = Decimal('0')
        recipient_count = 0
        details = {}
        
        # エリアディレクターのみ対象
        royal_members = [m for m in target_members if m.title == Title.AREA_DIRECTOR]
        
        for member in royal_members:
            if not dry_run:
                reward = Reward(
                    member_id=member.id,
                    calculation_id=calculation_id,
                    bonus_type=BonusType.ROYAL_FAMILY,
                    amount=royal_bonus_amount,
                    calculation_details={
                        "title": member.title.value,
                        "bonus_amount": str(royal_bonus_amount),
                        "formula": "最高タイトル保持者特別報酬"
                    },
                    payment_status=RewardPaymentStatus.PENDING,
                    created_at=datetime.now()
                )
                self.db.add(reward)
            
            total_amount += royal_bonus_amount
            recipient_count += 1
            details[member.member_number] = {
                "amount": royal_bonus_amount,
                "title": member.title.value
            }
        
        return {
            "total_amount": total_amount,
            "recipient_count": recipient_count,
            "details": details,
            "formula": "最高タイトル保持者特別報酬"
        }

    async def _delete_existing_calculations(self, calculation_month: str):
        """
        既存計算削除（再計算時）
        """
        # 既存の計算レコード削除
        existing_calculations = self.db.query(RewardCalculation).filter(
            RewardCalculation.calculation_month == calculation_month
        ).all()
        
        for calc in existing_calculations:
            # 関連する報酬レコード削除
            self.db.query(Reward).filter(Reward.calculation_id == calc.id).delete()
            self.db.delete(calc)
        
        self.db.commit()

    async def _generate_calculation_stats(
        self, bonus_results: Dict[str, Any], target_members: List[Member]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        計算統計情報生成
        """
        payment_stats = {
            "total_bonuses": len(bonus_results),
            "total_recipients": sum(result["recipient_count"] for result in bonus_results.values()),
            "bonus_breakdown": {
                bonus_type: {
                    "amount": result["total_amount"],
                    "recipients": result["recipient_count"]
                }
                for bonus_type, result in bonus_results.items()
            }
        }
        
        member_stats = {}
        for member in target_members:
            member_total = Decimal('0')
            member_bonuses = []
            
            for bonus_type, result in bonus_results.items():
                if member.member_number in result["details"]:
                    bonus_detail = result["details"][member.member_number]
                    member_total += bonus_detail["amount"]
                    member_bonuses.append({
                        "type": bonus_type,
                        "amount": bonus_detail["amount"]
                    })
            
            member_stats[member.member_number] = {
                "total_reward": member_total,
                "bonus_count": len(member_bonuses),
                "bonuses": member_bonuses,
                "is_payable": member_total >= 5000,  # 最低支払金額
                "will_carryover": member_total < 5000
            }
        
        return payment_stats, member_stats