"""
決済結果取込サービス

Phase B-2b: 決済結果取込API（3.5）
- B-2a（CSV出力）完了後実装可能
- モックアップP-004対応

エンドポイント:
- 3.5 POST /api/payments/import/result - 決済結果取込
"""

import csv
import io
import base64
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.models.member import Member, PaymentMethod
from app.models.payment import Payment, PaymentStatus, PaymentType
from app.schemas.payment import (
    PaymentResultImportRequest,
    PaymentResultImportResponse,
    PaymentResultRecord
)
from app.services.activity_service import ActivityService


class PaymentResultService:
    """
    決済結果取込サービスクラス
    Univapayからの決済結果CSV処理を担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)

    async def import_payment_results(
        self,
        import_request: PaymentResultImportRequest
    ) -> PaymentResultImportResponse:
        """
        決済結果取込
        API 3.5: POST /api/payments/import/result
        """
        started_at = datetime.now()
        
        try:
            # ファイル内容をデコード
            file_content = base64.b64decode(import_request.file_content)
            
            # CSV解析
            payment_results = await self._parse_payment_result_csv(
                file_content,
                import_request.result_type,
                import_request.encoding
            )
            
            # 決済結果処理
            processing_results = await self._process_payment_results(
                payment_results,
                import_request.result_type,
                import_request.target_month,
                import_request.auto_update_status
            )
            
            completed_at = datetime.now()
            
            # アクティビティログ記録
            await self.activity_service.log_activity(
                action="決済結果取込",
                details=f"ファイル: {import_request.file_name}, 種別: {import_request.result_type}, 成功: {processing_results['success_count']}件, エラー: {processing_results['error_count']}件",
                user_id="system"
            )
            
            return PaymentResultImportResponse(
                import_id=processing_results['import_id'],
                file_name=import_request.file_name,
                result_type=import_request.result_type,
                target_month=import_request.target_month,
                
                # 処理結果
                total_records=processing_results['total_records'],
                processed_records=processing_results['processed_records'],
                success_count=processing_results['success_count'],
                error_count=processing_results['error_count'],
                skipped_count=processing_results['skipped_count'],
                
                # 詳細結果
                successful_payments=processing_results['successful_payments'],
                failed_payments=processing_results['failed_payments'],
                processing_errors=processing_results['errors'],
                
                # 統計
                total_amount_processed=processing_results['total_amount'],
                success_rate=processing_results['success_rate'],
                
                # 実行情報
                started_at=started_at,
                completed_at=completed_at,
                processing_duration_seconds=(completed_at - started_at).total_seconds(),
                
                # ステータス
                import_status="completed" if processing_results['error_count'] == 0 else "completed_with_errors"
            )
            
        except Exception as e:
            # インポートエラー処理
            await self.activity_service.log_activity(
                action="決済結果取込失敗",
                details=f"ファイル: {import_request.file_name}, エラー: {str(e)}",
                user_id="system"
            )
            
            return PaymentResultImportResponse(
                import_id=0,
                file_name=import_request.file_name,
                result_type=import_request.result_type,
                target_month=import_request.target_month,
                total_records=0,
                processed_records=0,
                success_count=0,
                error_count=1,
                skipped_count=0,
                successful_payments=[],
                failed_payments=[],
                processing_errors=[{"error": str(e), "record": 0}],
                total_amount_processed=Decimal('0'),
                success_rate=0.0,
                started_at=started_at,
                completed_at=datetime.now(),
                processing_duration_seconds=0,
                import_status="failed"
            )

    async def _parse_payment_result_csv(
        self,
        file_content: bytes,
        result_type: str,
        encoding: str = "shift_jis"
    ) -> List[PaymentResultRecord]:
        """
        決済結果CSV解析
        """
        # エンコーディング処理
        try:
            csv_text = file_content.decode(encoding)
        except UnicodeDecodeError:
            # フォールバック: UTF-8で試行
            csv_text = file_content.decode('utf-8')
        
        # CSV読み込み
        reader = csv.DictReader(io.StringIO(csv_text))
        records = []
        
        for row_num, row in enumerate(reader, start=1):
            try:
                if result_type == "card":
                    record = self._parse_card_result_row(row, row_num)
                elif result_type == "transfer":
                    record = self._parse_transfer_result_row(row, row_num)
                else:
                    raise ValueError(f"サポートされていない結果種別: {result_type}")
                
                records.append(record)
                
            except Exception as e:
                # パース エラーも記録して続行
                error_record = PaymentResultRecord(
                    row_number=row_num,
                    customer_identifier="",
                    amount=Decimal('0'),
                    result_status="parse_error",
                    error_message=str(e),
                    raw_data=row
                )
                records.append(error_record)
        
        return records

    def _parse_card_result_row(self, row: Dict[str, str], row_num: int) -> PaymentResultRecord:
        """
        カード決済結果行解析
        IPScardresult_YYYYMMDD.csv フォーマット
        """
        # 必須カラム確認
        required_columns = ["顧客オーダー番号", "金額", "決済結果"]
        missing_columns = [col for col in required_columns if col not in row or not row[col].strip()]
        
        if missing_columns:
            raise ValueError(f"必須カラム不足: {missing_columns}")
        
        # 顧客オーダー番号から会員番号抽出（形式: 会員番号_YYYYMM）
        order_number = row["顧客オーダー番号"].strip()
        member_number = order_number.split('_')[0] if '_' in order_number else order_number
        
        # 金額処理
        try:
            amount = Decimal(str(row["金額"]).replace(',', '').replace('￥', '').replace('¥', '').strip())
        except (ValueError, TypeError):
            raise ValueError(f"金額が無効: {row['金額']}")
        
        # 決済結果判定
        result_text = row["決済結果"].strip().upper()
        if result_text in ["OK", "SUCCESS", "成功", "1"]:
            result_status = "success"
        elif result_text in ["NG", "FAILED", "失敗", "ERROR", "0"]:
            result_status = "failed"
        else:
            result_status = "unknown"
        
        return PaymentResultRecord(
            row_number=row_num,
            customer_identifier=member_number,
            customer_order_number=order_number,
            amount=amount,
            result_status=result_status,
            payment_date=datetime.now().date(),  # カード決済は処理日
            error_message=row.get("エラー情報", "").strip() or None,
            transaction_id=row.get("取引ID", "").strip() or None,
            raw_data=row
        )

    def _parse_transfer_result_row(self, row: Dict[str, str], row_num: int) -> PaymentResultRecord:
        """
        口座振替結果行解析
        XXXXXX_TrnsCSV_YYYYMMDDHHMMSS.csv フォーマット
        """
        # 必須カラム確認
        required_columns = ["顧客番号", "振替日", "金額"]
        missing_columns = [col for col in required_columns if col not in row or not row[col].strip()]
        
        if missing_columns:
            raise ValueError(f"必須カラム不足: {missing_columns}")
        
        member_number = row["顧客番号"].strip()
        
        # 振替日処理
        try:
            transfer_date_str = row["振替日"].strip()
            if transfer_date_str:
                payment_date = datetime.strptime(transfer_date_str, "%Y-%m-%d").date()
            else:
                payment_date = datetime.now().date()
        except ValueError:
            # フォーマット違いの場合の処理
            try:
                payment_date = datetime.strptime(transfer_date_str, "%Y/%m/%d").date()
            except ValueError:
                payment_date = datetime.now().date()
        
        # 金額処理
        try:
            amount = Decimal(str(row["金額"]).replace(',', '').replace('￥', '').replace('¥', '').strip())
        except (ValueError, TypeError):
            raise ValueError(f"金額が無効: {row['金額']}")
        
        # エラー情報による結果判定
        error_info = row.get("エラー情報", "").strip()
        if not error_info or error_info.upper() in ["なし", "NONE", "", "正常"]:
            result_status = "success"
        else:
            result_status = "failed"
        
        return PaymentResultRecord(
            row_number=row_num,
            customer_identifier=member_number,
            amount=amount,
            result_status=result_status,
            payment_date=payment_date,
            error_message=error_info or None,
            transfer_date=payment_date,
            raw_data=row
        )

    async def _process_payment_results(
        self,
        payment_results: List[PaymentResultRecord],
        result_type: str,
        target_month: str,
        auto_update_status: bool = True
    ) -> Dict[str, Any]:
        """
        決済結果処理実行
        """
        results = {
            "import_id": int(datetime.now().timestamp()),
            "total_records": len(payment_results),
            "processed_records": 0,
            "success_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "successful_payments": [],
            "failed_payments": [],
            "errors": [],
            "total_amount": Decimal('0'),
            "success_rate": 0.0
        }
        
        # 決済方法マッピング
        payment_method = PaymentMethod.CARD if result_type == "card" else PaymentMethod.TRANSFER
        
        for record in payment_results:
            try:
                # パースエラーレコードのスキップ
                if record.result_status == "parse_error":
                    results["error_count"] += 1
                    results["errors"].append({
                        "row": record.row_number,
                        "error": record.error_message,
                        "member_number": record.customer_identifier
                    })
                    continue
                
                # 会員検索
                member = self.db.query(Member).filter(
                    Member.member_number == record.customer_identifier
                ).first()
                
                if not member:
                    results["error_count"] += 1
                    results["errors"].append({
                        "row": record.row_number,
                        "error": f"会員番号 {record.customer_identifier} が見つかりません",
                        "member_number": record.customer_identifier
                    })
                    continue
                
                # 決済レコード検索・作成
                payment = await self._find_or_create_payment_record(
                    member,
                    payment_method,
                    target_month,
                    record
                )
                
                # ステータス更新
                if auto_update_status:
                    await self._update_payment_status(payment, record)
                
                # 結果集計
                results["processed_records"] += 1
                
                if record.result_status == "success":
                    results["success_count"] += 1
                    results["total_amount"] += record.amount
                    results["successful_payments"].append({
                        "member_number": member.member_number,
                        "member_name": member.name,
                        "amount": record.amount,
                        "payment_date": record.payment_date
                    })
                else:
                    results["failed_payments"].append({
                        "member_number": member.member_number,
                        "member_name": member.name,
                        "amount": record.amount,
                        "error_message": record.error_message,
                        "row_number": record.row_number
                    })
                
            except Exception as e:
                results["error_count"] += 1
                results["errors"].append({
                    "row": record.row_number,
                    "error": str(e),
                    "member_number": record.customer_identifier
                })
        
        # 成功率計算
        if results["processed_records"] > 0:
            results["success_rate"] = (results["success_count"] / results["processed_records"]) * 100
        
        self.db.commit()
        
        return results

    async def _find_or_create_payment_record(
        self,
        member: Member,
        payment_method: PaymentMethod,
        target_month: str,
        result_record: PaymentResultRecord
    ) -> Payment:
        """
        決済レコード検索・作成
        """
        # 既存レコード検索
        existing_payment = self.db.query(Payment).filter(
            Payment.member_id == member.id,
            Payment.payment_method == payment_method,
            Payment.target_month == target_month
        ).first()
        
        if existing_payment:
            return existing_payment
        
        # 新規作成
        new_payment = Payment(
            member_id=member.id,
            payment_method=payment_method,
            payment_type=PaymentType.UNIVAPAY,
            target_month=target_month,
            amount=result_record.amount,
            status=PaymentStatus.PENDING,
            payment_date=result_record.payment_date,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            recorded_by="univapay_import"
        )
        
        self.db.add(new_payment)
        return new_payment

    async def _update_payment_status(
        self,
        payment: Payment,
        result_record: PaymentResultRecord
    ):
        """
        決済ステータス更新
        """
        # ステータス更新
        if result_record.result_status == "success":
            payment.status = PaymentStatus.COMPLETED
        elif result_record.result_status == "failed":
            payment.status = PaymentStatus.FAILED
        else:
            payment.status = PaymentStatus.PENDING
        
        # エラー情報記録
        if result_record.error_message:
            error_note = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Univapayエラー: {result_record.error_message}"
            if payment.notes:
                payment.notes += f"\n{error_note}"
            else:
                payment.notes = error_note
        
        # 取引ID記録
        if result_record.transaction_id:
            payment.confirmation_number = result_record.transaction_id
        
        payment.updated_at = datetime.now()

    async def get_import_history(
        self,
        result_type: Optional[str] = None,
        target_month: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        取込履歴取得
        内部使用：取込実績管理
        """
        # 実装は省略（実際にはimport_logテーブルを作成して管理）
        return {
            "imports": [],
            "total_count": 0,
            "page": page,
            "per_page": per_page,
            "filter_conditions": {
                "result_type": result_type,
                "target_month": target_month,
                "date_from": date_from,
                "date_to": date_to
            }
        }

    async def validate_result_file_format(
        self,
        file_content: bytes,
        result_type: str,
        encoding: str = "shift_jis"
    ) -> Dict[str, Any]:
        """
        決済結果ファイル形式検証
        内部使用：取込前の事前チェック
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "file_info": {},
            "preview_data": []
        }
        
        try:
            # エンコーディングテスト
            try:
                csv_text = file_content.decode(encoding)
            except UnicodeDecodeError:
                csv_text = file_content.decode('utf-8')
                validation_result["warnings"].append(f"指定エンコーディング({encoding})で読み込めません。UTF-8で処理します。")
            
            # CSV構造チェック
            reader = csv.DictReader(io.StringIO(csv_text))
            headers = reader.fieldnames
            
            # 期待ヘッダーとの照合
            expected_headers = self._get_expected_result_headers(result_type)
            missing_headers = set(expected_headers) - set(headers or [])
            
            if missing_headers:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"必須ヘッダー不足: {list(missing_headers)}")
            
            # データ行サンプル
            sample_rows = []
            for i, row in enumerate(reader):
                if i >= 5:  # 最初の5行のみ
                    break
                sample_rows.append(row)
            
            validation_result["file_info"] = {
                "headers": headers or [],
                "sample_row_count": len(sample_rows),
                "encoding_detected": encoding
            }
            validation_result["preview_data"] = sample_rows
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"ファイル解析エラー: {str(e)}")
        
        return validation_result

    def _get_expected_result_headers(self, result_type: str) -> List[str]:
        """
        決済結果種別別期待ヘッダー取得
        """
        if result_type == "card":
            return ["顧客オーダー番号", "金額", "決済結果"]
        elif result_type == "transfer":
            return ["顧客番号", "振替日", "金額"]
        else:
            return []