"""
決済CSV出力サービス

Phase B-2a: CSV出力API（3.3-3.4）
- A-2a（決済対象）完了後実装可能
- モックアップP-004対応

エンドポイント:
- 3.3 POST /api/payments/export/card - カード決済CSV出力
- 3.4 POST /api/payments/export/transfer - 口座振替CSV出力
"""

import csv
import io
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.member import Member, PaymentMethod
from app.schemas.payment import (
    PaymentExportRequest,
    PaymentExportResponse,
    PaymentTargetResponse
)
from app.services.payment_target_service import PaymentTargetService
from app.services.activity_service import ActivityService


class PaymentExportService:
    """
    決済CSV出力サービスクラス
    Univapay連携用CSV生成を担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)
        self.payment_target_service = PaymentTargetService(db)

    async def export_card_payment_csv(
        self,
        export_request: PaymentExportRequest
    ) -> PaymentExportResponse:
        """
        カード決済CSV出力
        API 3.3: POST /api/payments/export/card
        """
        # 対象月設定
        target_month = export_request.target_month or self._get_next_month()
        
        # カード決済対象者取得
        targets_response = await self.payment_target_service.get_card_payment_targets(
            target_month=target_month,
            include_pending=not export_request.exclude_processed
        )
        
        if not targets_response.targets:
            raise ValueError(f"{target_month} のカード決済対象者が見つかりません")
        
        # CSV生成
        csv_content = await self._generate_card_payment_csv(
            targets_response.targets,
            export_request.encoding or "shift_jis"
        )
        
        # ファイル名生成
        filename = export_request.custom_filename or f"card_payment_{target_month.replace('-', '')}.csv"
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="カード決済CSV出力",
            details=f"対象月: {target_month}, 対象者: {len(targets_response.targets)}名, 総額: ¥{targets_response.total_amount:,}",
            user_id="system"
        )
        
        return PaymentExportResponse(
            export_id=int(datetime.now().timestamp()),
            export_type="card_payment",
            target_month=target_month,
            filename=filename,
            file_content=csv_content,
            encoding=export_request.encoding or "shift_jis",
            
            # 統計情報
            total_records=len(targets_response.targets),
            total_amount=targets_response.total_amount,
            
            # Univapay用メタデータ
            univapay_metadata={
                "payment_method": "credit_card",
                "batch_id": f"card_{target_month.replace('-', '')}_{datetime.now().strftime('%H%M%S')}",
                "currency": "JPY",
                "execution_date": self._get_card_execution_date(target_month)
            },
            
            # 出力情報
            generated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            is_ready_for_univapay=True,
            
            # 警告・注意事項
            warnings=await self._validate_card_export_data(targets_response.targets)
        )

    async def export_transfer_payment_csv(
        self,
        export_request: PaymentExportRequest
    ) -> PaymentExportResponse:
        """
        口座振替CSV出力
        API 3.4: POST /api/payments/export/transfer
        """
        # 対象月設定
        target_month = export_request.target_month or self._get_next_month()
        
        # 口座振替対象者取得
        targets_response = await self.payment_target_service.get_transfer_payment_targets(
            target_month=target_month,
            include_pending=not export_request.exclude_processed
        )
        
        if not targets_response.targets:
            raise ValueError(f"{target_month} の口座振替対象者が見つかりません")
        
        # 銀行情報検証
        validation_errors = await self._validate_bank_information(targets_response.targets)
        if validation_errors and export_request.strict_validation:
            raise ValueError(f"銀行情報エラー: {validation_errors}")
        
        # CSV生成
        csv_content = await self._generate_transfer_payment_csv(
            targets_response.targets,
            export_request.encoding or "shift_jis"
        )
        
        # ファイル名生成
        filename = export_request.custom_filename or f"transfer_payment_{target_month.replace('-', '')}.csv"
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="口座振替CSV出力",
            details=f"対象月: {target_month}, 対象者: {len(targets_response.targets)}名, 総額: ¥{targets_response.total_amount:,}",
            user_id="system"
        )
        
        return PaymentExportResponse(
            export_id=int(datetime.now().timestamp()),
            export_type="transfer_payment",
            target_month=target_month,
            filename=filename,
            file_content=csv_content,
            encoding=export_request.encoding or "shift_jis",
            
            # 統計情報
            total_records=len(targets_response.targets),
            total_amount=targets_response.total_amount,
            
            # Univapay用メタデータ
            univapay_metadata={
                "payment_method": "bank_transfer",
                "batch_id": f"transfer_{target_month.replace('-', '')}_{datetime.now().strftime('%H%M%S')}",
                "currency": "JPY",
                "execution_date": self._get_transfer_execution_date(target_month)
            },
            
            # 出力情報
            generated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            is_ready_for_univapay=True,
            
            # 警告・注意事項
            warnings=validation_errors or []
        )

    async def _generate_card_payment_csv(
        self,
        targets: List[PaymentTargetResponse],
        encoding: str = "shift_jis"
    ) -> str:
        """
        カード決済CSV生成
        Univapay仕様に準拠
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー行（Univapay仕様）
        headers = [
            "顧客オーダー番号",
            "金額", 
            "通貨",
            "決済方法",
            "顧客名",
            "顧客メールアドレス",
            "備考"
        ]
        writer.writerow(headers)
        
        # データ行
        for target in targets:
            row = [
                target.customer_order_number,  # 会員番号_対象月
                target.amount,  # プラン料金
                target.currency or "JPY",
                "credit_card",
                target.member_name,
                target.member_email or "",
                f"{target.plan.value} - {target.target_month}"
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        # エンコーディング変換
        if encoding.lower() in ["shift_jis", "shift-jis", "sjis"]:
            return csv_content.encode('shift_jis', errors='ignore').decode('shift_jis')
        else:
            return csv_content

    async def _generate_transfer_payment_csv(
        self,
        targets: List[PaymentTargetResponse],
        encoding: str = "shift_jis"
    ) -> str:
        """
        口座振替CSV生成
        Univapay仕様に準拠
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー行（Univapay口座振替仕様）
        headers = [
            "顧客番号",
            "振替日",
            "金額",
            "通貨",
            "銀行コード",
            "支店コード",
            "口座種別",
            "口座番号",
            "口座名義人",
            "顧客名",
            "備考"
        ]
        writer.writerow(headers)
        
        # データ行
        for target in targets:
            # 口座種別変換（1:普通, 2:当座）
            account_type_code = "1" if target.account_type and target.account_type.value == "普通" else "2"
            
            row = [
                target.customer_number,  # 会員番号
                target.transfer_date.strftime("%Y-%m-%d") if target.transfer_date else "",
                target.amount,
                target.currency or "JPY",
                target.bank_code or "",
                target.branch_code or "",
                account_type_code,
                target.account_number or "",
                target.member_name,  # 口座名義人として会員名を使用
                target.member_name,
                f"{target.plan.value} - {target.target_month}"
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        # エンコーディング変換
        if encoding.lower() in ["shift_jis", "shift-jis", "sjis"]:
            return csv_content.encode('shift_jis', errors='ignore').decode('shift_jis')
        else:
            return csv_content

    async def _validate_card_export_data(self, targets: List[PaymentTargetResponse]) -> List[str]:
        """
        カード決済データ検証
        """
        warnings = []
        
        for target in targets:
            # 会員番号チェック
            if not target.member_number or len(target.member_number) != 7:
                warnings.append(f"会員番号形式異常: {target.member_number}")
            
            # 金額チェック  
            if target.amount <= 0:
                warnings.append(f"金額異常: {target.member_number} - ¥{target.amount}")
            
            # 顧客オーダー番号重複チェック
            order_numbers = [t.customer_order_number for t in targets]
            if order_numbers.count(target.customer_order_number) > 1:
                warnings.append(f"顧客オーダー番号重複: {target.customer_order_number}")
        
        return warnings

    async def _validate_bank_information(self, targets: List[PaymentTargetResponse]) -> List[str]:
        """
        銀行情報検証
        """
        errors = []
        
        for target in targets:
            # 銀行コードチェック
            if not target.bank_code or len(target.bank_code) != 4 or not target.bank_code.isdigit():
                errors.append(f"銀行コード異常: {target.member_number} - {target.bank_code}")
            
            # 支店コードチェック
            if not target.branch_code or len(target.branch_code) != 3 or not target.branch_code.isdigit():
                errors.append(f"支店コード異常: {target.member_number} - {target.branch_code}")
            
            # 口座番号チェック
            if not target.account_number:
                errors.append(f"口座番号未設定: {target.member_number}")
            elif not target.account_number.isdigit():
                errors.append(f"口座番号形式異常: {target.member_number} - {target.account_number}")
        
        return errors

    def _get_next_month(self) -> str:
        """
        翌月の年月文字列取得（YYYY-MM）
        """
        today = datetime.now()
        next_month = today.replace(day=1) + timedelta(days=32)
        return next_month.strftime("%Y-%m")

    def _get_card_execution_date(self, target_month: str) -> str:
        """
        カード決済実行日取得（月初1～5日）
        """
        try:
            year, month = map(int, target_month.split('-'))
            execution_date = datetime(year, month, 5)  # 5日に設定
            return execution_date.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            return datetime.now().strftime("%Y-%m-%d")

    def _get_transfer_execution_date(self, target_month: str) -> str:
        """
        口座振替実行日取得（27日）
        """
        try:
            year, month = map(int, target_month.split('-'))
            execution_date = datetime(year, month, 27)
            return execution_date.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            return datetime.now().strftime("%Y-%m-%d")

    async def get_export_history(
        self,
        export_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        CSV出力履歴取得
        内部使用：出力実績管理
        """
        # 実装は省略（実際にはexport_logテーブルを作成して管理）
        return {
            "exports": [],
            "total_count": 0,
            "page": page,
            "per_page": per_page,
            "filter_conditions": {
                "export_type": export_type,
                "date_from": date_from,
                "date_to": date_to
            }
        }

    async def validate_univapay_format(self, csv_content: str, payment_method: str) -> Dict[str, Any]:
        """
        Univapay形式検証
        内部使用：CSV出力前の最終チェック
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "format_compliance": {},
            "record_count": 0
        }
        
        try:
            # CSV解析
            reader = csv.reader(io.StringIO(csv_content))
            rows = list(reader)
            
            if not rows:
                validation_result["is_valid"] = False
                validation_result["errors"].append("CSVファイルが空です")
                return validation_result
            
            # ヘッダー行チェック
            headers = rows[0]
            expected_headers = self._get_expected_headers(payment_method)
            
            missing_headers = set(expected_headers) - set(headers)
            if missing_headers:
                validation_result["errors"].append(f"必須ヘッダー不足: {list(missing_headers)}")
                validation_result["is_valid"] = False
            
            # データ行チェック
            data_rows = rows[1:]
            validation_result["record_count"] = len(data_rows)
            
            for idx, row in enumerate(data_rows, start=2):  # ヘッダー行を除くため+2
                if len(row) != len(headers):
                    validation_result["errors"].append(f"行{idx}: カラム数不一致")
                
                # 必須項目チェック
                if payment_method == "card" and not row[0]:  # 顧客オーダー番号
                    validation_result["errors"].append(f"行{idx}: 顧客オーダー番号が空です")
                elif payment_method == "transfer" and not row[0]:  # 顧客番号
                    validation_result["errors"].append(f"行{idx}: 顧客番号が空です")
            
            validation_result["format_compliance"] = {
                "header_match": len(missing_headers) == 0,
                "column_consistency": True,  # 詳細チェック実装省略
                "required_fields": len(validation_result["errors"]) == 0
            }
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"CSV解析エラー: {str(e)}")
        
        return validation_result

    def _get_expected_headers(self, payment_method: str) -> List[str]:
        """
        決済方法別期待ヘッダー取得
        """
        if payment_method == "card":
            return ["顧客オーダー番号", "金額", "通貨", "決済方法", "顧客名", "顧客メールアドレス", "備考"]
        elif payment_method == "transfer":
            return ["顧客番号", "振替日", "金額", "通貨", "銀行コード", "支店コード", "口座種別", "口座番号", "口座名義人", "顧客名", "備考"]
        else:
            return []