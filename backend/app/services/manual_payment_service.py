"""
手動決済サービス

Phase A-2b: 手動決済・履歴API（3.6-3.7）
- 完全独立、いつでも実装可能
- モックアップP-004対応

エンドポイント:
- 3.6 POST /api/payments/manual - 手動決済記録
- 3.7 GET /api/payments/history - 決済履歴
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.member import Member, MemberStatus, PaymentMethod
from app.models.payment import Payment, PaymentStatus, PaymentType
from app.schemas.payment import (
    ManualPaymentRequest,
    PaymentResponse,
    PaymentHistoryResponse,
    PaymentHistoryListResponse
)
from app.services.activity_service import ActivityService


class ManualPaymentService:
    """
    手動決済サービスクラス
    銀行振込・インフォカート決済の手動記録を担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)

    async def create_manual_payment(
        self,
        payment_data: ManualPaymentRequest
    ) -> PaymentResponse:
        """
        手動決済記録作成
        API 3.6: POST /api/payments/manual
        """
        # 会員存在確認
        member = self.db.query(Member).filter(Member.id == payment_data.member_id).first()
        if not member:
            raise ValueError(f"会員ID {payment_data.member_id} は存在しません")
        
        # 手動決済方法の確認
        if member.payment_method not in [PaymentMethod.BANK, PaymentMethod.INFOCART]:
            raise ValueError(f"会員 {member.member_number} は手動決済対象ではありません（決済方法: {member.payment_method.value}）")
        
        # 重複支払いチェック（同一月・同一会員）
        existing_payment = self.db.query(Payment).filter(
            and_(
                Payment.member_id == payment_data.member_id,
                Payment.target_month == payment_data.target_month,
                Payment.status.in_([PaymentStatus.COMPLETED, PaymentStatus.PENDING])
            )
        ).first()
        
        if existing_payment and not payment_data.allow_duplicate:
            raise ValueError(
                f"会員 {member.member_number} の {payment_data.target_month} 分の決済は既に記録されています"
            )
        
        # 手動決済レコード作成
        new_payment = Payment(
            member_id=payment_data.member_id,
            payment_method=member.payment_method,
            payment_type=PaymentType.MANUAL,
            target_month=payment_data.target_month,
            amount=payment_data.amount,
            status=payment_data.status,
            
            # 手動決済固有項目
            payment_date=payment_data.payment_date,
            confirmation_number=payment_data.confirmation_number,
            bank_transfer_info=payment_data.bank_transfer_info,
            infocart_order_id=payment_data.infocart_order_id,
            notes=payment_data.notes,
            
            # システム項目
            created_at=datetime.now(),
            updated_at=datetime.now(),
            recorded_by="manual_entry"
        )
        
        self.db.add(new_payment)
        self.db.commit()
        self.db.refresh(new_payment)
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="手動決済記録作成",
            details=f"会員: {member.member_number}, 対象月: {payment_data.target_month}, 金額: ¥{payment_data.amount:,}, 方法: {member.payment_method.value}",
            user_id="manual_entry",
            target_id=new_payment.id
        )
        
        return self._convert_to_response(new_payment, member)

    async def get_payment_history(
        self,
        member_id: Optional[int] = None,
        payment_method: Optional[List[str]] = None,
        status: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50
    ) -> PaymentHistoryListResponse:
        """
        決済履歴取得
        API 3.7: GET /api/payments/history
        """
        # ベースクエリ（新しい順）
        query = self.db.query(Payment, Member).join(Member, Payment.member_id == Member.id)
        query = query.order_by(desc(Payment.created_at))
        
        # 会員フィルター
        if member_id:
            query = query.filter(Payment.member_id == member_id)
        
        # 決済方法フィルター
        if payment_method:
            query = query.filter(Payment.payment_method.in_(payment_method))
        
        # ステータスフィルター
        if status:
            query = query.filter(Payment.status.in_(status))
        
        # 日付範囲フィルター
        if date_from:
            query = query.filter(Payment.payment_date >= date_from)
        if date_to:
            end_date = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Payment.payment_date <= end_date)
        
        # 総件数取得
        total_count = query.count()
        
        # ページネーション
        offset = (page - 1) * per_page
        results = query.offset(offset).limit(per_page).all()
        
        # レスポンス変換
        history_list = []
        total_amount = Decimal('0')
        
        for payment, member in results:
            history_item = PaymentHistoryResponse(
                payment=self._convert_to_response(payment, member),
                member_info={
                    "member_number": member.member_number,
                    "member_name": member.name,
                    "plan": member.plan,
                    "status": member.status
                },
                payment_summary={
                    "target_month": payment.target_month,
                    "amount": payment.amount,
                    "payment_method": payment.payment_method,
                    "status": payment.status,
                    "payment_date": payment.payment_date
                }
            )
            
            history_list.append(history_item)
            if payment.status == PaymentStatus.COMPLETED:
                total_amount += payment.amount
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="決済履歴取得",
            details=f"検索条件: 会員ID={member_id}, 方法={payment_method}, ステータス={status}, 結果: {len(history_list)}件",
            user_id="system"
        )
        
        return PaymentHistoryListResponse(
            history=history_list,
            filter_conditions={
                "member_id": member_id,
                "payment_method": payment_method,
                "status": status,
                "date_from": date_from,
                "date_to": date_to
            },
            total_count=total_count,
            total_amount=total_amount,
            page=page,
            per_page=per_page,
            total_pages=(total_count + per_page - 1) // per_page
        )

    async def update_payment_status(
        self,
        payment_id: int,
        new_status: PaymentStatus,
        notes: Optional[str] = None
    ) -> PaymentResponse:
        """
        決済ステータス更新
        内部使用：決済結果反映時に使用
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError(f"決済ID {payment_id} は存在しません")
        
        old_status = payment.status
        payment.status = new_status
        payment.updated_at = datetime.now()
        
        if notes:
            if payment.notes:
                payment.notes += f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
            else:
                payment.notes = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
        
        self.db.commit()
        self.db.refresh(payment)
        
        # 会員情報取得
        member = self.db.query(Member).filter(Member.id == payment.member_id).first()
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="決済ステータス更新",
            details=f"決済ID: {payment_id}, ステータス: {old_status.value} → {new_status.value}",
            user_id="system",
            target_id=payment_id
        )
        
        return self._convert_to_response(payment, member)

    async def get_payment_statistics(
        self,
        period_months: int = 3
    ) -> Dict[str, Any]:
        """
        決済統計情報取得
        内部使用：ダッシュボード表示用
        """
        # 集計期間設定
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_months * 30)
        
        # 期間内の決済データ取得
        payments = self.db.query(Payment).filter(
            Payment.created_at >= start_date
        ).all()
        
        # 決済方法別集計
        method_stats = {}
        for method in PaymentMethod:
            method_payments = [p for p in payments if p.payment_method == method]
            completed_payments = [p for p in method_payments if p.status == PaymentStatus.COMPLETED]
            
            method_stats[method.value] = {
                "total_count": len(method_payments),
                "completed_count": len(completed_payments),
                "total_amount": sum(p.amount for p in completed_payments),
                "success_rate": len(completed_payments) / len(method_payments) * 100 if method_payments else 0
            }
        
        # ステータス別集計
        status_stats = {}
        for status in PaymentStatus:
            status_payments = [p for p in payments if p.status == status]
            status_stats[status.value] = {
                "count": len(status_payments),
                "total_amount": sum(p.amount for p in status_payments)
            }
        
        # 月別売上推移
        monthly_revenue = {}
        for i in range(period_months):
            month_start = (end_date.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
            month_payments = [
                p for p in payments 
                if p.payment_date and p.payment_date.month == month_start.month 
                and p.payment_date.year == month_start.year
                and p.status == PaymentStatus.COMPLETED
            ]
            
            month_key = month_start.strftime("%Y-%m")
            monthly_revenue[month_key] = {
                "count": len(month_payments),
                "amount": sum(p.amount for p in month_payments)
            }
        
        return {
            "period_months": period_months,
            "total_payments": len(payments),
            "total_revenue": sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED),
            "method_statistics": method_stats,
            "status_statistics": status_stats,
            "monthly_revenue": monthly_revenue,
            "generated_at": datetime.now().isoformat()
        }

    def _convert_to_response(self, payment: Payment, member: Member) -> PaymentResponse:
        """
        Payment モデルを PaymentResponse スキーマに変換
        """
        return PaymentResponse(
            id=payment.id,
            member_id=payment.member_id,
            member_number=member.member_number,
            member_name=member.name,
            payment_method=payment.payment_method,
            payment_type=payment.payment_type,
            target_month=payment.target_month,
            amount=payment.amount,
            status=payment.status,
            
            # 決済詳細
            payment_date=payment.payment_date,
            confirmation_number=payment.confirmation_number,
            bank_transfer_info=payment.bank_transfer_info,
            infocart_order_id=payment.infocart_order_id,
            notes=payment.notes,
            
            # システム項目
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            recorded_by=payment.recorded_by,
            
            # 表示用フォーマット
            formatted_amount=f"¥{payment.amount:,}",
            formatted_payment_date=payment.payment_date.strftime("%Y年%m月%d日") if payment.payment_date else None,
            status_display=f"{payment.status.value}",
            payment_method_display=f"{payment.payment_method.value}",
            is_completed=payment.status == PaymentStatus.COMPLETED
        )

    async def validate_manual_payment_data(
        self,
        payment_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        手動決済データバリデーション
        内部使用：作成前のデータチェック
        """
        errors = {}
        
        # 必須項目チェック
        required_fields = ["member_id", "target_month", "amount"]
        for field in required_fields:
            if not payment_data.get(field):
                if field not in errors:
                    errors[field] = []
                errors[field].append(f"{field} は必須項目です")
        
        # 金額チェック
        if payment_data.get("amount"):
            amount = payment_data["amount"]
            if amount <= 0:
                if "amount" not in errors:
                    errors["amount"] = []
                errors["amount"].append("金額は0より大きい値を入力してください")
        
        # 対象月フォーマットチェック
        if payment_data.get("target_month"):
            target_month = payment_data["target_month"]
            if not target_month.match(r'^\d{4}-\d{2}$'):
                if "target_month" not in errors:
                    errors["target_month"] = []
                errors["target_month"].append("対象月はYYYY-MM形式で入力してください")
        
        return errors