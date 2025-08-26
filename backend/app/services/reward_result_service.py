"""
計算結果管理サービス

Phase C-1c: 計算結果管理API（4.3-4.6）
- C-1b（計算実行）完了後実装可能
- モックアップP-005対応

エンドポイント:
- 4.3 GET /api/rewards/results/{id} - 計算結果取得
- 4.4 GET /api/rewards/results/{id}/member/{mid} - 個人別内訳
- 4.5 DELETE /api/rewards/results/{id} - 計算結果削除
- 4.6 GET /api/rewards/history - 計算履歴
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.member import Member
from app.models.reward import (
    RewardCalculation, Reward, BonusType,
    CalculationStatus, PaymentStatus as RewardPaymentStatus
)
from app.schemas.reward import (
    RewardCalculationResponse, RewardHistoryResponse, MemberRewardSummary,
    RewardCalculationListResponse, RewardCalculationDeleteResponse
)
from app.services.activity_service import ActivityService


class RewardResultService:
    """
    計算結果管理サービスクラス
    報酬計算結果の取得・管理・削除を担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)

    async def get_calculation_result(
        self,
        calculation_id: int
    ) -> RewardCalculationResponse:
        """
        計算結果取得
        API 4.3: GET /api/rewards/results/{id}
        """
        # 計算レコード取得
        calculation = self.db.query(RewardCalculation).filter(
            RewardCalculation.id == calculation_id
        ).first()
        
        if not calculation:
            raise ValueError(f"計算ID {calculation_id} は存在しません")
        
        # 関連する報酬レコード取得
        rewards = self.db.query(Reward).filter(
            Reward.calculation_id == calculation_id
        ).all()
        
        # ボーナス別集計
        bonus_summary = {}
        for bonus_type in BonusType:
            type_rewards = [r for r in rewards if r.bonus_type == bonus_type]
            bonus_summary[bonus_type.value] = {
                "total_amount": sum(r.amount for r in type_rewards),
                "recipient_count": len(type_rewards),
                "details": {
                    reward.member.member_number: {
                        "amount": reward.amount,
                        "calculation_details": reward.calculation_details
                    }
                    for reward in type_rewards
                }
            }
        
        # 支払統計
        total_payable = sum(r.amount for r in rewards if r.amount >= 5000)
        total_carryover = sum(r.amount for r in rewards if r.amount < 5000)
        payable_count = len([r for r in rewards if r.amount >= 5000])
        carryover_count = len([r for r in rewards if r.amount < 5000])
        
        payment_stats = {
            "total_payable": total_payable,
            "total_carryover": total_carryover,
            "payable_member_count": payable_count,
            "carryover_member_count": carryover_count,
            "minimum_payout": Decimal('5000')
        }
        
        # 会員統計
        unique_members = len(set(r.member_id for r in rewards))
        member_stats = {
            "total_reward_recipients": unique_members,
            "average_reward_per_member": calculation.total_amount / max(unique_members, 1),
            "max_individual_reward": max((r.amount for r in rewards), default=Decimal('0')),
            "min_individual_reward": min((r.amount for r in rewards), default=Decimal('0'))
        }
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="計算結果取得",
            details=f"計算ID: {calculation_id}, 対象月: {calculation.calculation_month}",
            user_id="system",
            target_id=calculation_id
        )
        
        return RewardCalculationResponse(
            calculation_id=calculation.id,
            calculation_month=calculation.calculation_month,
            calculation_type=calculation.calculation_type,
            status=calculation.status,
            
            # 実行結果サマリー
            total_amount=calculation.total_amount or Decimal('0'),
            target_member_count=calculation.target_member_count or 0,
            carryover_member_count=carryover_count,
            execution_time_seconds=self._calculate_execution_time(calculation),
            
            # ボーナス別集計
            bonus_summary=bonus_summary,
            
            # 統計情報
            payment_stats=payment_stats,
            member_stats=member_stats,
            
            # 実行情報
            started_at=calculation.started_at,
            completed_at=calculation.completed_at,
            
            # エラー情報
            error_message=calculation.error_message,
            warnings=[]
        )

    async def get_member_reward_detail(
        self,
        calculation_id: int,
        member_id: int
    ) -> MemberRewardSummary:
        """
        個人別報酬内訳取得
        API 4.4: GET /api/rewards/results/{id}/member/{mid}
        """
        # 計算レコード確認
        calculation = self.db.query(RewardCalculation).filter(
            RewardCalculation.id == calculation_id
        ).first()
        
        if not calculation:
            raise ValueError(f"計算ID {calculation_id} は存在しません")
        
        # 会員確認
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"会員ID {member_id} は存在しません")
        
        # 該当会員の報酬レコード取得
        member_rewards = self.db.query(Reward).filter(
            and_(
                Reward.calculation_id == calculation_id,
                Reward.member_id == member_id
            )
        ).all()
        
        # ボーナス別内訳作成
        bonus_breakdown = []
        total_reward = Decimal('0')
        
        for reward in member_rewards:
            bonus_detail = RewardHistoryResponse(
                member_id=member.id,
                member_number=member.member_number,
                member_name=member.name,
                calculation_id=calculation_id,
                calculation_month=calculation.calculation_month,
                bonus_type=reward.bonus_type,
                bonus_amount=reward.amount,
                calculation_details=reward.calculation_details or {},
                payment_status=reward.payment_status,
                payment_date=reward.payment_date,
                is_payable=reward.amount >= 5000,
                formatted_amount=f"¥{reward.amount:,}",
                calculation_description=self._format_calculation_description(reward),
                created_at=reward.created_at,
                updated_at=reward.updated_at
            )
            
            bonus_breakdown.append(bonus_detail)
            total_reward += reward.amount
        
        # 支払可能額・繰越額計算
        payable_amount = total_reward if total_reward >= 5000 else Decimal('0')
        carryover_amount = total_reward if total_reward < 5000 else Decimal('0')
        
        # 0円ボーナス検出
        zero_bonuses = []
        all_bonus_types = set(BonusType)
        member_bonus_types = set(r.bonus_type for r in member_rewards)
        missing_bonus_types = all_bonus_types - member_bonus_types
        
        for bonus_type in missing_bonus_types:
            zero_bonuses.append(bonus_type.value)
        
        # 支払予定日算出（翌月末）
        try:
            year, month = map(int, calculation.calculation_month.split('-'))
            if month == 12:
                payment_scheduled_date = datetime(year + 1, 1, 31)
            else:
                payment_scheduled_date = datetime(year, month + 1, 28)  # 簡易計算
        except:
            payment_scheduled_date = None
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="個人別報酬内訳取得",
            details=f"計算ID: {calculation_id}, 会員: {member.member_number}({member.name}), 総額: ¥{total_reward:,}",
            user_id="system",
            target_id=member_id
        )
        
        return MemberRewardSummary(
            member_number=member.member_number,
            member_name=member.name,
            calculation_month=calculation.calculation_month,
            
            # 合計金額
            total_reward=total_reward,
            payable_amount=payable_amount,
            carryover_amount=carryover_amount,
            
            # ボーナス別内訳
            bonus_breakdown=bonus_breakdown,
            
            # 統計
            bonus_count=len(bonus_breakdown),
            zero_bonuses=zero_bonuses,
            
            # 支払情報
            will_be_paid=payable_amount > 0,
            payment_scheduled_date=payment_scheduled_date
        )

    async def delete_calculation_result(
        self,
        calculation_id: int,
        delete_reason: Optional[str] = None
    ) -> RewardCalculationDeleteResponse:
        """
        計算結果削除
        API 4.5: DELETE /api/rewards/results/{id}
        """
        # 計算レコード取得
        calculation = self.db.query(RewardCalculation).filter(
            RewardCalculation.id == calculation_id
        ).first()
        
        if not calculation:
            raise ValueError(f"計算ID {calculation_id} は存在しません")
        
        # 既に支払済みの報酬がある場合は削除不可
        paid_rewards = self.db.query(Reward).filter(
            and_(
                Reward.calculation_id == calculation_id,
                Reward.payment_status == RewardPaymentStatus.PAID
            )
        ).count()
        
        if paid_rewards > 0:
            raise ValueError(f"支払済み報酬が {paid_rewards} 件あるため削除できません")
        
        # 削除対象の報酬レコード取得
        rewards_to_delete = self.db.query(Reward).filter(
            Reward.calculation_id == calculation_id
        ).all()
        
        # 影響を受ける会員リスト
        affected_members = list(set(r.member.member_number for r in rewards_to_delete))
        
        # 削除実行前の情報保存
        deleted_calculation_data = RewardCalculationResponse(
            calculation_id=calculation.id,
            calculation_month=calculation.calculation_month,
            calculation_type=calculation.calculation_type,
            status=calculation.status,
            total_amount=calculation.total_amount or Decimal('0'),
            target_member_count=calculation.target_member_count or 0,
            carryover_member_count=0,  # 簡易計算
            execution_time_seconds=self._calculate_execution_time(calculation),
            bonus_summary={},
            payment_stats={},
            member_stats={},
            started_at=calculation.started_at,
            completed_at=calculation.completed_at,
            error_message=calculation.error_message,
            warnings=[]
        )
        
        # 報酬レコード削除
        deleted_reward_count = len(rewards_to_delete)
        for reward in rewards_to_delete:
            self.db.delete(reward)
        
        # 計算レコード削除
        self.db.delete(calculation)
        self.db.commit()
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="計算結果削除",
            details=f"計算ID: {calculation_id}, 対象月: {calculation.calculation_month}, 削除報酬数: {deleted_reward_count}, 理由: {delete_reason or '未記載'}",
            user_id="system"
        )
        
        return RewardCalculationDeleteResponse(
            success=True,
            calculation_id=calculation_id,
            deleted_calculation=deleted_calculation_data,
            deleted_reward_count=deleted_reward_count,
            affected_members=affected_members,
            deleted_at=datetime.now(),
            deleted_by="system",
            delete_reason=delete_reason,
            warnings=[]
        )

    async def get_calculation_history(
        self,
        page: int = 1,
        per_page: int = 20,
        calculation_month: Optional[str] = None,
        status_filter: Optional[List[str]] = None
    ) -> RewardCalculationListResponse:
        """
        計算履歴取得
        API 4.6: GET /api/rewards/history
        """
        # ベースクエリ
        query = self.db.query(RewardCalculation).order_by(desc(RewardCalculation.created_at))
        
        # フィルター適用
        if calculation_month:
            query = query.filter(RewardCalculation.calculation_month == calculation_month)
        
        if status_filter:
            query = query.filter(RewardCalculation.status.in_(status_filter))
        
        # 総件数取得
        total_count = query.count()
        
        # ページネーション
        offset = (page - 1) * per_page
        calculations = query.offset(offset).limit(per_page).all()
        
        # 計算履歴リスト作成
        calculation_list = []
        for calc in calculations:
            calc_response = await self._convert_to_calculation_response(calc)
            calculation_list.append(calc_response)
        
        # 統計情報
        successful_count = self.db.query(RewardCalculation).filter(
            RewardCalculation.status == CalculationStatus.COMPLETED
        ).count()
        
        failed_count = self.db.query(RewardCalculation).filter(
            RewardCalculation.status == CalculationStatus.FAILED
        ).count()
        
        # 今年の計算回数
        this_year = datetime.now().year
        this_year_count = self.db.query(RewardCalculation).filter(
            RewardCalculation.created_at >= datetime(this_year, 1, 1)
        ).count()
        
        # 最新計算結果
        last_calculation = None
        if calculation_list:
            last_calculation = calculation_list[0]
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="計算履歴取得",
            details=f"ページ: {page}, 件数: {len(calculation_list)}, フィルター: {status_filter}",
            user_id="system"
        )
        
        return RewardCalculationListResponse(
            calculations=calculation_list,
            total_calculations=total_count,
            successful_calculations=successful_count,
            failed_calculations=failed_count,
            this_year_calculations=this_year_count,
            last_calculation=last_calculation,
            page=page,
            per_page=per_page,
            total_pages=(total_count + per_page - 1) // per_page
        )

    async def _convert_to_calculation_response(
        self, 
        calculation: RewardCalculation
    ) -> RewardCalculationResponse:
        """
        RewardCalculation を RewardCalculationResponse に変換
        """
        # 簡易版（詳細は get_calculation_result で取得）
        return RewardCalculationResponse(
            calculation_id=calculation.id,
            calculation_month=calculation.calculation_month,
            calculation_type=calculation.calculation_type,
            status=calculation.status,
            total_amount=calculation.total_amount or Decimal('0'),
            target_member_count=calculation.target_member_count or 0,
            carryover_member_count=0,  # 詳細計算は省略
            execution_time_seconds=self._calculate_execution_time(calculation),
            bonus_summary={},  # 詳細は省略
            payment_stats={},  # 詳細は省略
            member_stats={},   # 詳細は省略
            started_at=calculation.started_at,
            completed_at=calculation.completed_at,
            error_message=calculation.error_message,
            warnings=[]
        )

    def _calculate_execution_time(self, calculation: RewardCalculation) -> float:
        """
        実行時間計算
        """
        if calculation.started_at and calculation.completed_at:
            return (calculation.completed_at - calculation.started_at).total_seconds()
        return 0.0

    def _format_calculation_description(self, reward: Reward) -> str:
        """
        計算詳細の文字列フォーマット
        """
        if not reward.calculation_details:
            return f"{reward.bonus_type.value}: ¥{reward.amount:,}"
        
        details = reward.calculation_details
        
        if reward.bonus_type == BonusType.DAILY:
            return f"デイリーボーナス: {details.get('formula', '')} = ¥{reward.amount:,}"
        elif reward.bonus_type == BonusType.TITLE:
            return f"タイトルボーナス: {details.get('title', '')} = ¥{reward.amount:,}"
        elif reward.bonus_type == BonusType.REFERRAL:
            referral_count = details.get('direct_referrals_count', 0)
            return f"リファラルボーナス: {referral_count}名紹介 = ¥{reward.amount:,}"
        elif reward.bonus_type == BonusType.POWER:
            sales = details.get('organization_sales', '0')
            rate = details.get('bonus_rate', '0%')
            return f"パワーボーナス: 売上¥{sales} × {rate} = ¥{reward.amount:,}"
        else:
            return f"{reward.bonus_type.value}: ¥{reward.amount:,}"

    async def get_reward_statistics(
        self,
        period_months: int = 12
    ) -> Dict[str, Any]:
        """
        報酬統計情報取得
        内部使用：ダッシュボード表示用
        """
        # 期間設定
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_months * 30)
        
        # 期間内の計算取得
        calculations = self.db.query(RewardCalculation).filter(
            RewardCalculation.created_at >= start_date
        ).all()
        
        # 月別統計
        monthly_stats = {}
        for calc in calculations:
            month_key = calc.calculation_month
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    "calculation_count": 0,
                    "total_amount": Decimal('0'),
                    "target_members": 0
                }
            
            monthly_stats[month_key]["calculation_count"] += 1
            monthly_stats[month_key]["total_amount"] += calc.total_amount or Decimal('0')
            monthly_stats[month_key]["target_members"] += calc.target_member_count or 0
        
        # ボーナス種別統計
        bonus_stats = {}
        for bonus_type in BonusType:
            rewards = self.db.query(Reward).filter(
                and_(
                    Reward.bonus_type == bonus_type,
                    Reward.created_at >= start_date
                )
            ).all()
            
            bonus_stats[bonus_type.value] = {
                "total_amount": sum(r.amount for r in rewards),
                "recipient_count": len(set(r.member_id for r in rewards)),
                "payment_count": len(rewards)
            }
        
        return {
            "period_months": period_months,
            "total_calculations": len(calculations),
            "successful_calculations": len([c for c in calculations if c.status == CalculationStatus.COMPLETED]),
            "failed_calculations": len([c for c in calculations if c.status == CalculationStatus.FAILED]),
            "total_rewards_paid": sum(c.total_amount or Decimal('0') for c in calculations),
            "monthly_statistics": monthly_stats,
            "bonus_type_statistics": bonus_stats,
            "generated_at": datetime.now()
        }