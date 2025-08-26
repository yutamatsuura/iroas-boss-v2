"""
決済対象サービス

Phase A-2a: 決済対象API（3.1-3.2）
- 完全独立、いつでも実装可能
- モックアップP-004対応

エンドポイント:
- 3.1 GET /api/payments/targets/card - カード決済対象者
- 3.2 GET /api/payments/targets/transfer - 口座振替対象者
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta

from app.models.member import Member, MemberStatus, PaymentMethod, Plan
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentTargetResponse, PaymentTargetListResponse
from app.services.activity_service import ActivityService


class PaymentTargetService:
    """
    決済対象サービスクラス
    Univapay CSV出力用の決済対象者抽出を担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)

    async def get_card_payment_targets(
        self,
        target_month: Optional[str] = None,
        include_pending: bool = True
    ) -> PaymentTargetListResponse:
        """
        カード決済対象者取得
        API 3.1: GET /api/payments/targets/card
        """
        # 対象月設定（未指定時は翌月）
        if not target_month:
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            target_month = next_month.strftime("%Y-%m")
        
        # カード決済会員を抽出
        query = self.db.query(Member).filter(
            and_(
                Member.status == MemberStatus.ACTIVE,
                Member.payment_method == PaymentMethod.CARD
            )
        )
        
        members = query.all()
        
        # 決済対象者リスト作成
        targets = []
        total_amount = 0
        
        for member in members:
            # 当月の決済履歴チェック
            existing_payment = None
            if include_pending:
                existing_payment = self.db.query(Payment).filter(
                    and_(
                        Payment.member_id == member.id,
                        Payment.payment_method == PaymentMethod.CARD,
                        Payment.target_month == target_month,
                        Payment.status != PaymentStatus.FAILED
                    )
                ).first()
            
            # 既に決済済みでない場合のみ対象とする
            if not existing_payment:
                # プラン料金取得
                plan_amount = self._get_plan_amount(member.plan)
                
                target = PaymentTargetResponse(
                    member_id=member.id,
                    member_number=member.member_number,
                    member_name=member.name,
                    plan=member.plan,
                    payment_method=member.payment_method,
                    target_month=target_month,
                    amount=plan_amount,
                    status="対象",
                    
                    # Univapay CSV用項目
                    customer_order_number=f"{member.member_number}_{target_month.replace('-', '')}",
                    payment_amount=plan_amount,
                    currency="JPY",
                    
                    # 表示用項目
                    formatted_amount=f"¥{plan_amount:,}",
                    is_eligible=True,
                    notes=f"{member.plan.value} - カード決済"
                )
                
                targets.append(target)
                total_amount += plan_amount
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="カード決済対象者取得",
            details=f"対象月: {target_month}, 対象者: {len(targets)}名, 総額: ¥{total_amount:,}",
            user_id="system"
        )
        
        return PaymentTargetListResponse(
            targets=targets,
            target_month=target_month,
            payment_method=PaymentMethod.CARD,
            total_members=len(targets),
            total_amount=total_amount,
            csv_ready=True,
            generated_at=datetime.now(),
            univapay_format={
                "file_name": f"card_payment_{target_month.replace('-', '')}.csv",
                "encoding": "Shift-JIS",
                "required_columns": ["顧客オーダー番号", "金額", "決済方法"]
            }
        )

    async def get_transfer_payment_targets(
        self,
        target_month: Optional[str] = None,
        include_pending: bool = True
    ) -> PaymentTargetListResponse:
        """
        口座振替対象者取得
        API 3.2: GET /api/payments/targets/transfer
        """
        # 対象月設定（未指定時は翌月）
        if not target_month:
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            target_month = next_month.strftime("%Y-%m")
        
        # 口座振替会員を抽出
        query = self.db.query(Member).filter(
            and_(
                Member.status == MemberStatus.ACTIVE,
                Member.payment_method == PaymentMethod.TRANSFER
            )
        )
        
        members = query.all()
        
        # 決済対象者リスト作成
        targets = []
        total_amount = 0
        
        for member in members:
            # 当月の決済履歴チェック
            existing_payment = None
            if include_pending:
                existing_payment = self.db.query(Payment).filter(
                    and_(
                        Payment.member_id == member.id,
                        Payment.payment_method == PaymentMethod.TRANSFER,
                        Payment.target_month == target_month,
                        Payment.status != PaymentStatus.FAILED
                    )
                ).first()
            
            # 既に決済済みでない場合のみ対象とする
            if not existing_payment:
                # プラン料金取得
                plan_amount = self._get_plan_amount(member.plan)
                
                # 振替日設定（27日）
                transfer_date = self._get_transfer_date(target_month)
                
                target = PaymentTargetResponse(
                    member_id=member.id,
                    member_number=member.member_number,
                    member_name=member.name,
                    plan=member.plan,
                    payment_method=member.payment_method,
                    target_month=target_month,
                    amount=plan_amount,
                    status="対象",
                    
                    # Univapay CSV用項目
                    customer_number=member.member_number,
                    transfer_date=transfer_date,
                    transfer_amount=plan_amount,
                    currency="JPY",
                    
                    # 銀行情報
                    bank_name=member.bank_name,
                    bank_code=member.bank_code,
                    branch_name=member.branch_name,
                    branch_code=member.branch_code,
                    account_number=member.account_number,
                    account_type=member.account_type,
                    
                    # 表示用項目
                    formatted_amount=f"¥{plan_amount:,}",
                    formatted_transfer_date=transfer_date.strftime("%Y年%m月%d日") if transfer_date else None,
                    is_eligible=True,
                    notes=f"{member.plan.value} - 口座振替"
                )
                
                targets.append(target)
                total_amount += plan_amount
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="口座振替対象者取得",
            details=f"対象月: {target_month}, 対象者: {len(targets)}名, 総額: ¥{total_amount:,}",
            user_id="system"
        )
        
        return PaymentTargetListResponse(
            targets=targets,
            target_month=target_month,
            payment_method=PaymentMethod.TRANSFER,
            total_members=len(targets),
            total_amount=total_amount,
            csv_ready=True,
            generated_at=datetime.now(),
            univapay_format={
                "file_name": f"transfer_payment_{target_month.replace('-', '')}.csv",
                "encoding": "Shift-JIS",
                "required_columns": ["顧客番号", "振替日", "金額"]
            }
        )

    async def validate_payment_targets(
        self,
        targets: List[PaymentTargetResponse]
    ) -> Dict[str, Any]:
        """
        決済対象者データの整合性チェック
        内部使用：CSV出力前の検証
        """
        validation_errors = []
        warnings = []
        
        for target in targets:
            # 会員番号の有効性チェック
            if not target.member_number or len(target.member_number) != 7:
                validation_errors.append(f"会員番号が無効: {target.member_number}")
            
            # 金額の妥当性チェック
            if target.amount <= 0:
                validation_errors.append(f"金額が無効: {target.member_number} - ¥{target.amount}")
            
            # 口座振替の場合：銀行情報チェック
            if target.payment_method == PaymentMethod.TRANSFER:
                if not target.bank_code:
                    validation_errors.append(f"銀行コード未設定: {target.member_number}")
                if not target.branch_code:
                    validation_errors.append(f"支店コード未設定: {target.member_number}")
                if not target.account_number:
                    validation_errors.append(f"口座番号未設定: {target.member_number}")
                
                # 銀行コード形式チェック
                if target.bank_code and (len(target.bank_code) != 4 or not target.bank_code.isdigit()):
                    warnings.append(f"銀行コード形式要確認: {target.member_number} - {target.bank_code}")
        
        return {
            "is_valid": len(validation_errors) == 0,
            "validation_errors": validation_errors,
            "warnings": warnings,
            "total_checked": len(targets),
            "error_count": len(validation_errors),
            "warning_count": len(warnings)
        }

    def _get_plan_amount(self, plan: Plan) -> int:
        """
        プラン料金取得
        要件定義書の固定料金
        """
        plan_rates = {
            Plan.HERO: 10670,  # ヒーロープラン
            Plan.TEST: 9800    # テストプラン
        }
        return plan_rates.get(plan, 0)

    def _get_transfer_date(self, target_month: str) -> Optional[datetime]:
        """
        振替日取得（27日）
        """
        try:
            year, month = map(int, target_month.split('-'))
            return datetime(year, month, 27)
        except (ValueError, IndexError):
            return None

    async def get_payment_statistics(
        self,
        target_month: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        決済統計情報取得
        内部使用：ダッシュボード表示用
        """
        if not target_month:
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            target_month = next_month.strftime("%Y-%m")
        
        # カード決済統計
        card_targets = await self.get_card_payment_targets(target_month)
        
        # 口座振替統計
        transfer_targets = await self.get_transfer_payment_targets(target_month)
        
        # 手動決済会員数（銀行振込・インフォカート）
        manual_members = self.db.query(Member).filter(
            and_(
                Member.status == MemberStatus.ACTIVE,
                Member.payment_method.in_([PaymentMethod.BANK, PaymentMethod.INFOCART])
            )
        ).count()
        
        # 全アクティブ会員数
        total_active = self.db.query(Member).filter(Member.status == MemberStatus.ACTIVE).count()
        
        return {
            "target_month": target_month,
            "card_payment": {
                "target_count": card_targets.total_members,
                "total_amount": card_targets.total_amount
            },
            "transfer_payment": {
                "target_count": transfer_targets.total_members,
                "total_amount": transfer_targets.total_amount
            },
            "manual_payment_members": manual_members,
            "total_active_members": total_active,
            "payment_method_distribution": {
                "card": card_targets.total_members,
                "transfer": transfer_targets.total_members,
                "manual": manual_members
            },
            "total_expected_revenue": card_targets.total_amount + transfer_targets.total_amount,
            "generated_at": datetime.now().isoformat()
        }