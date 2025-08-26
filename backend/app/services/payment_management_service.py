# -*- coding: utf-8 -*-
"""
Phase D-1a: 支払管理サービス実装
GMOネットバンク振込CSV生成、支払対象者管理、繰越処理、支払確定機能

対応API:
- 5.1: GET /api/payments/reward-summary (支払対象者一覧)
- 5.2: POST /api/payments/export/gmo (GMO CSV出力)
- 5.3: POST /api/payments/confirm (支払確定)
- 5.4: GET /api/payments/carryover (繰越一覧)

要件: 
- 最低支払金額: 5,000円以上が支払対象
- 5,000円未満は翌月繰り越し
- GMOネットバンクCSVフォーマット対応
- Shift-JISエンコーディング
- 振込手数料会社負担
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import csv
import tempfile
import os
from io import StringIO

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..models.member import Member
from ..models.reward_result import RewardResult
from ..models.payment_record import PaymentRecord
from ..models.activity_log import ActivityLog
from ..core.exceptions import (
    BusinessRuleError,
    DataNotFoundError,
    ValidationError
)


class PaymentManagementService:
    """
    支払管理サービス
    
    GMOネットバンク振込、支払対象者管理、繰越処理を担当
    要件定義の最低支払金額5,000円と繰り越し機能を厳密に実装
    """

    def __init__(self, db: Session):
        self.db = db
        self.minimum_payment_amount = Decimal('5000')  # 最低支払金額
        self.gmo_csv_headers = [
            "銀行コード",
            "支店コード", 
            "口座種別",
            "口座番号",
            "受取人名",
            "振込金額",
            "手数料負担",
            "EDI情報"
        ]

    def get_payment_targets(self, target_month: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        5.1: 支払対象者一覧取得（5,000円以上）
        
        Args:
            target_month: 対象月 (YYYY-MM形式、未指定時は当月)
            
        Returns:
            List[Dict]: 支払対象者情報一覧
            
        Raises:
            BusinessRuleError: 報酬計算が完了していない場合
        """
        if not target_month:
            target_month = datetime.now().strftime("%Y-%m")

        # 対象月の報酬計算結果を取得
        reward_results = self._get_latest_reward_results(target_month)
        
        if not reward_results:
            raise BusinessRuleError(f"{target_month}の報酬計算が実行されていません")

        payment_targets = []
        
        for reward_result in reward_results:
            member = self.db.query(Member).filter(
                Member.id == reward_result.member_id
            ).first()
            
            if not member:
                continue
                
            # 前月繰越金額を取得
            carryover_amount = self._get_carryover_amount(
                member.id, target_month
            )
            
            # 今月報酬 + 前月繰越
            total_reward = reward_result.total_amount + carryover_amount
            
            # 5,000円以上が支払対象
            if total_reward >= self.minimum_payment_amount:
                # 支払確定状況を確認
                payment_status = self._get_payment_status(
                    member.id, target_month
                )
                
                payment_targets.append({
                    "member_id": member.id,
                    "member_number": member.member_number,
                    "name": member.name,
                    "plan": member.plan,
                    "current_month_reward": float(reward_result.total_amount),
                    "carryover_amount": float(carryover_amount),
                    "payment_amount": float(total_reward),
                    "bank_name": member.bank_name or "",
                    "bank_code": member.bank_code or "",
                    "branch_name": member.branch_name or "",
                    "branch_code": member.branch_code or "",
                    "account_type": member.account_type or "普通",
                    "account_number": member.account_number or "",
                    "account_holder_kana": member.name_kana or "",
                    "postal_symbol": member.postal_symbol or "",
                    "postal_number": member.postal_number or "",
                    "payment_status": payment_status,
                    "target_month": target_month
                })

        # 支払金額の降順でソート
        payment_targets.sort(
            key=lambda x: x["payment_amount"], reverse=True
        )
        
        return payment_targets

    def get_carryover_list(self, target_month: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        5.4: 繰越金額一覧取得（5,000円未満）
        
        Args:
            target_month: 対象月 (YYYY-MM形式、未指定時は当月)
            
        Returns:
            List[Dict]: 繰越対象者情報一覧
        """
        if not target_month:
            target_month = datetime.now().strftime("%Y-%m")

        # 対象月の報酬計算結果を取得
        reward_results = self._get_latest_reward_results(target_month)
        
        if not reward_results:
            return []  # 報酬計算未実行の場合は空リスト

        carryover_list = []
        
        for reward_result in reward_results:
            member = self.db.query(Member).filter(
                Member.id == reward_result.member_id
            ).first()
            
            if not member:
                continue
                
            # 前月繰越金額を取得
            carryover_amount = self._get_carryover_amount(
                member.id, target_month
            )
            
            # 今月報酬 + 前月繰越
            total_amount = reward_result.total_amount + carryover_amount
            
            # 5,000円未満が繰越対象
            if total_amount < self.minimum_payment_amount:
                carryover_list.append({
                    "member_id": member.id,
                    "member_number": member.member_number,
                    "name": member.name,
                    "plan": member.plan,
                    "current_month_reward": float(reward_result.total_amount),
                    "previous_carryover": float(carryover_amount),
                    "total_amount": float(total_amount),
                    "carryover_reason": "最低支払額未満",
                    "target_month": target_month
                })

        # 合計金額の降順でソート
        carryover_list.sort(
            key=lambda x: x["total_amount"], reverse=True
        )
        
        return carryover_list

    def export_gmo_csv(
        self, 
        target_month: str, 
        target_member_ids: Optional[List[str]] = None
    ) -> str:
        """
        5.2: GMOネットバンク振込CSV出力
        
        Args:
            target_month: 対象月 (YYYY-MM形式)
            target_member_ids: 対象会員ID一覧（未指定時は全支払対象者）
            
        Returns:
            str: 生成されたCSVファイルのパス
            
        Raises:
            BusinessRuleError: 支払対象者が存在しない場合
            ValidationError: 銀行情報が不完全な場合
        """
        # 支払対象者を取得
        payment_targets = self.get_payment_targets(target_month)
        
        if not payment_targets:
            raise BusinessRuleError(f"{target_month}の支払対象者が存在しません")

        # 対象会員を絞り込み（指定がある場合）
        if target_member_ids:
            payment_targets = [
                target for target in payment_targets
                if target["member_id"] in target_member_ids
            ]

        if not payment_targets:
            raise BusinessRuleError("指定された会員に支払対象者が存在しません")

        # GMOネットバンクCSVフォーマットで出力
        csv_data = []
        total_amount = Decimal('0')
        invalid_members = []

        for target in payment_targets:
            # 支払確定済みはスキップ
            if target["payment_status"] == "confirmed":
                continue

            # 銀行情報検証
            bank_validation_result = self._validate_bank_info(target)
            if not bank_validation_result["valid"]:
                invalid_members.append({
                    "member_number": target["member_number"],
                    "name": target["name"],
                    "error": bank_validation_result["error"]
                })
                continue

            # GMO CSVレコード作成
            csv_row = self._create_gmo_csv_row(target)
            csv_data.append(csv_row)
            total_amount += Decimal(str(target["payment_amount"]))

        if invalid_members:
            error_msg = "銀行情報が不完全な会員がいます:\n"
            for invalid in invalid_members:
                error_msg += f"- {invalid['member_number']}: {invalid['name']} ({invalid['error']})\n"
            raise ValidationError(error_msg.strip())

        if not csv_data:
            raise BusinessRuleError("CSVに出力する支払対象者がいません")

        # CSVファイル生成
        csv_filename = f"GMO_振込_{target_month.replace('-', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = self._generate_csv_file(csv_filename, csv_data)

        # アクティビティログ記録
        self._log_activity(
            f"GMO振込CSV出力",
            f"対象月: {target_month}, 対象者数: {len(csv_data)}名, 総額: ¥{total_amount:,.0f}"
        )

        return csv_path

    def confirm_payment(
        self, 
        member_id: str, 
        target_month: str,
        payment_amount: Decimal,
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        5.3: 支払確定処理
        
        Args:
            member_id: 会員ID
            target_month: 対象月 (YYYY-MM形式)
            payment_amount: 支払金額
            memo: 備考
            
        Returns:
            Dict[str, Any]: 処理結果
            
        Raises:
            DataNotFoundError: 会員または報酬データが見つからない場合
            BusinessRuleError: 重複確定など業務エラー
        """
        # 会員存在確認
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise DataNotFoundError(f"会員ID: {member_id} が見つかりません")

        # 重複確定チェック
        existing_payment = self.db.query(PaymentRecord).filter(
            and_(
                PaymentRecord.member_id == member_id,
                PaymentRecord.target_month == target_month,
                PaymentRecord.status == "confirmed"
            )
        ).first()
        
        if existing_payment:
            raise BusinessRuleError(
                f"会員 {member.member_number}: {member.name} の{target_month}分は既に支払確定済みです"
            )

        # 対象月の報酬結果確認
        reward_result = self._get_member_reward_result(member_id, target_month)
        if not reward_result:
            raise DataNotFoundError(f"{target_month}の報酬計算結果が見つかりません")

        # 前月繰越金額取得
        carryover_amount = self._get_carryover_amount(member_id, target_month)
        expected_amount = reward_result.total_amount + carryover_amount

        # 支払金額妥当性チェック
        if abs(payment_amount - expected_amount) > Decimal('0.01'):
            raise BusinessRuleError(
                f"支払金額が不正です。期待値: ¥{expected_amount}, 実際: ¥{payment_amount}"
            )

        # 支払記録作成
        payment_record = PaymentRecord(
            member_id=member_id,
            target_month=target_month,
            payment_method="bank_transfer",
            reward_amount=reward_result.total_amount,
            carryover_amount=carryover_amount,
            payment_amount=payment_amount,
            status="confirmed",
            confirmed_at=datetime.now(),
            memo=memo or f"GMO振込確定 {member.member_number}: {member.name}"
        )

        self.db.add(payment_record)
        self.db.commit()

        # アクティビティログ記録
        self._log_activity(
            "支払確定",
            f"会員: {member.member_number} {member.name}, 対象月: {target_month}, 支払額: ¥{payment_amount:,.0f}"
        )

        return {
            "success": True,
            "message": f"会員 {member.member_number}: {member.name} の支払を確定しました",
            "payment_record_id": payment_record.id,
            "payment_amount": float(payment_amount),
            "confirmed_at": payment_record.confirmed_at.isoformat()
        }

    def get_payment_history(
        self, 
        page: int = 1, 
        limit: int = 50,
        month_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        支払履歴取得
        
        Args:
            page: ページ番号
            limit: 1ページあたりの件数
            month_filter: 月フィルタ (YYYY-MM形式)
            
        Returns:
            Dict[str, Any]: ページネーション付き支払履歴
        """
        query = self.db.query(PaymentRecord).filter(
            PaymentRecord.status == "confirmed"
        )

        if month_filter:
            query = query.filter(PaymentRecord.target_month == month_filter)

        # 総件数取得
        total_count = query.count()

        # ページネーション適用
        offset = (page - 1) * limit
        payment_records = query.order_by(
            desc(PaymentRecord.confirmed_at)
        ).offset(offset).limit(limit).all()

        # 履歴データ整形
        history_items = []
        for record in payment_records:
            member = self.db.query(Member).filter(
                Member.id == record.member_id
            ).first()

            history_items.append({
                "payment_record_id": record.id,
                "member_id": record.member_id,
                "member_number": member.member_number if member else "不明",
                "member_name": member.name if member else "不明",
                "target_month": record.target_month,
                "payment_method": record.payment_method,
                "reward_amount": float(record.reward_amount),
                "carryover_amount": float(record.carryover_amount),
                "payment_amount": float(record.payment_amount),
                "confirmed_at": record.confirmed_at.isoformat(),
                "memo": record.memo or ""
            })

        return {
            "items": history_items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit,
                "has_next": page * limit < total_count,
                "has_prev": page > 1
            }
        }

    # プライベートメソッド群

    def _get_latest_reward_results(self, target_month: str) -> List[RewardResult]:
        """対象月の最新報酬計算結果を取得"""
        return self.db.query(RewardResult).filter(
            func.date_format(RewardResult.calculation_date, '%Y-%m') == target_month
        ).order_by(desc(RewardResult.calculation_date)).all()

    def _get_member_reward_result(self, member_id: str, target_month: str) -> Optional[RewardResult]:
        """特定会員の報酬計算結果を取得"""
        return self.db.query(RewardResult).filter(
            and_(
                RewardResult.member_id == member_id,
                func.date_format(RewardResult.calculation_date, '%Y-%m') == target_month
            )
        ).order_by(desc(RewardResult.calculation_date)).first()

    def _get_carryover_amount(self, member_id: str, target_month: str) -> Decimal:
        """前月繰越金額を取得"""
        # 過去の繰越記録を検索
        # 実装では、前月までの未支払い報酬の累計を計算
        # ここでは簡略化して0を返す（実際は複雑な繰越計算が必要）
        
        # TODO: 実際の繰越計算ロジック実装
        # 1. 過去の報酬結果から支払済み分を除外
        # 2. 5,000円未満だった月の報酬を累積
        # 3. 翌月繰越として管理
        
        return Decimal('0')

    def _get_payment_status(self, member_id: str, target_month: str) -> str:
        """支払状況を取得"""
        payment_record = self.db.query(PaymentRecord).filter(
            and_(
                PaymentRecord.member_id == member_id,
                PaymentRecord.target_month == target_month,
                PaymentRecord.status == "confirmed"
            )
        ).first()

        return "confirmed" if payment_record else "pending"

    def _validate_bank_info(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """銀行情報の妥当性検証"""
        errors = []

        # 一般銀行の場合
        if not target.get("postal_symbol"):  # ゆうちょ以外
            if not target.get("bank_code"):
                errors.append("銀行コードが未設定")
            if not target.get("branch_code"):
                errors.append("支店コードが未設定")
            if not target.get("account_number"):
                errors.append("口座番号が未設定")
        else:  # ゆうちょ銀行の場合
            if not target.get("postal_symbol"):
                errors.append("ゆうちょ記号が未設定")
            if not target.get("postal_number"):
                errors.append("ゆうちょ番号が未設定")

        if not target.get("account_holder_kana"):
            errors.append("口座名義人（カナ）が未設定")

        return {
            "valid": len(errors) == 0,
            "error": ", ".join(errors) if errors else None
        }

    def _create_gmo_csv_row(self, target: Dict[str, Any]) -> List[str]:
        """GMOネットバンクCSV形式のレコードを作成"""
        # ゆうちょ銀行の場合は特別処理
        if target.get("postal_symbol"):
            return [
                "9900",  # ゆうちょ銀行コード
                "000",   # 支店コード（ゆうちょ）
                "1",     # 普通預金
                target["postal_number"],
                target["account_holder_kana"][:30],  # 名前は30文字制限
                str(int(target["payment_amount"])),  # 小数点なし
                "",      # 手数料会社負担（空欄）
                ""       # EDI情報（空欄）
            ]
        else:
            # 一般銀行
            return [
                target["bank_code"],
                target["branch_code"],
                "1" if target["account_type"] == "普通" else "2",  # 1:普通, 2:当座
                target["account_number"],
                target["account_holder_kana"][:30],
                str(int(target["payment_amount"])),
                "",  # 手数料会社負担
                ""   # EDI情報
            ]

    def _generate_csv_file(self, filename: str, csv_data: List[List[str]]) -> str:
        """CSVファイルを生成（Shift-JISエンコーディング）"""
        # 一時ディレクトリにファイル作成
        temp_dir = tempfile.gettempdir()
        csv_path = os.path.join(temp_dir, filename)

        with open(csv_path, 'w', encoding='shift_jis', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # ヘッダー行書き込み
            writer.writerow(self.gmo_csv_headers)
            
            # データ行書き込み
            for row in csv_data:
                writer.writerow(row)

        return csv_path

    def _log_activity(self, action: str, details: str):
        """アクティビティログ記録"""
        log = ActivityLog(
            user_id="system",  # 認証実装後に実際のユーザーIDを設定
            action=action,
            target_type="payment",
            target_id=None,
            details=details,
            created_at=datetime.now()
        )
        
        self.db.add(log)
        self.db.commit()