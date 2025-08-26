# -*- coding: utf-8 -*-
"""
支払管理サービステスト
Phase D-1a API 5.1-5.4の動作保証

実データ主義：
- モック使用禁止
- 実際のデータベース操作
- 要件定義完全準拠テスト
"""

import pytest
import tempfile
import os
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../backend'))

from app.services.payment_management_service import PaymentManagementService
from app.core.exceptions import BusinessRuleError, DataNotFoundError, ValidationError


class TestPaymentManagementService:
    """支払管理サービステスト"""

    def test_get_payment_targets_success(self, test_session, sample_members, sample_reward_results):
        """5.1 支払対象者一覧取得 - 成功ケース"""
        service = PaymentManagementService(test_session)
        
        # テスト実行
        result = service.get_payment_targets("2025-08")
        
        # 検証
        assert len(result) == 2  # 5000円以上は2名
        
        # 田中太郎（8500円）
        tanaka = next(r for r in result if r["member_number"] == "0000001")
        assert tanaka["name"] == "田中太郎"
        assert tanaka["payment_amount"] == 8500.0
        assert tanaka["payment_status"] == "pending"
        assert tanaka["bank_name"] == "三井住友銀行"
        
        # 佐藤花子（15670円）
        sato = next(r for r in result if r["member_number"] == "0000002")
        assert sato["name"] == "佐藤花子"
        assert sato["payment_amount"] == 15670.0
        assert sato["bank_name"] == "みずほ銀行"
        
        # 山田次郎（4800円）は含まれない（5000円未満）
        yamada_exists = any(r["member_number"] == "0000003" for r in result)
        assert not yamada_exists

    def test_get_payment_targets_no_reward_results(self, test_session):
        """5.1 支払対象者一覧取得 - 報酬計算未実行エラー"""
        service = PaymentManagementService(test_session)
        
        with pytest.raises(BusinessRuleError, match="2025-09の報酬計算が実行されていません"):
            service.get_payment_targets("2025-09")

    def test_get_carryover_list_success(self, test_session, sample_members, sample_reward_results):
        """5.4 繰越金額一覧取得 - 成功ケース"""
        service = PaymentManagementService(test_session)
        
        # テスト実行
        result = service.get_carryover_list("2025-08")
        
        # 検証
        assert len(result) == 1  # 5000円未満は1名
        
        # 山田次郎（4800円）のみ
        yamada = result[0]
        assert yamada["member_number"] == "0000003"
        assert yamada["name"] == "山田次郎"
        assert yamada["total_amount"] == 4800.0
        assert yamada["carryover_reason"] == "最低支払額未満"

    def test_get_carryover_list_empty(self, test_session):
        """5.4 繰越金額一覧取得 - 空リスト"""
        service = PaymentManagementService(test_session)
        
        result = service.get_carryover_list("2025-09")
        assert result == []

    def test_export_gmo_csv_success(self, test_session, sample_members, sample_reward_results):
        """5.2 GMO CSV出力 - 成功ケース"""
        service = PaymentManagementService(test_session)
        
        # テスト実行
        csv_path = service.export_gmo_csv("2025-08")
        
        # ファイル存在確認
        assert os.path.exists(csv_path)
        assert csv_path.endswith('.csv')
        
        # CSV内容確認
        with open(csv_path, 'r', encoding='shift_jis') as f:
            content = f.read()
            
        lines = content.strip().split('\n')
        
        # ヘッダー確認
        header = lines[0]
        expected_headers = "銀行コード,支店コード,口座種別,口座番号,受取人名,振込金額,手数料負担,EDI情報"
        assert header == expected_headers
        
        # データ行確認（2名分）
        assert len(lines) == 3  # ヘッダー + 2データ行
        
        # 田中太郎のレコード確認
        tanaka_line = next(line for line in lines[1:] if "タナカタロウ" in line)
        tanaka_fields = tanaka_line.split(',')
        assert tanaka_fields[0] == "0009"  # 三井住友銀行コード
        assert tanaka_fields[1] == "001"   # 支店コード
        assert tanaka_fields[2] == "1"     # 普通預金
        assert tanaka_fields[3] == "1234567"  # 口座番号
        assert tanaka_fields[4] == "タナカタロウ"
        assert tanaka_fields[5] == "8500"  # 振込金額
        assert tanaka_fields[6] == ""      # 手数料会社負担
        
        # 一時ファイル削除
        os.unlink(csv_path)

    def test_export_gmo_csv_postal_account(self, test_session, sample_members, sample_reward_results):
        """5.2 GMO CSV出力 - ゆうちょ銀行ケース"""
        service = PaymentManagementService(test_session)
        
        # 山田次郎の報酬を5000円以上に変更
        yamada_reward = next(r for r in sample_reward_results if r.member_id == "member003")
        yamada_reward.total_amount = Decimal('6000.00')
        test_session.commit()
        
        # テスト実行
        csv_path = service.export_gmo_csv("2025-08", ["member003"])
        
        # CSV内容確認
        with open(csv_path, 'r', encoding='shift_jis') as f:
            content = f.read()
            
        lines = content.strip().split('\n')
        
        # ゆうちょのレコード確認
        yamada_line = lines[1]  # データ行
        yamada_fields = yamada_line.split(',')
        assert yamada_fields[0] == "9900"  # ゆうちょ銀行コード
        assert yamada_fields[1] == "000"   # ゆうちょ支店コード
        assert yamada_fields[3] == "67890123"  # ゆうちょ番号
        
        os.unlink(csv_path)

    def test_export_gmo_csv_no_targets(self, test_session):
        """5.2 GMO CSV出力 - 支払対象者なしエラー"""
        service = PaymentManagementService(test_session)
        
        with pytest.raises(BusinessRuleError, match="2025-09の支払対象者が存在しません"):
            service.export_gmo_csv("2025-09")

    def test_export_gmo_csv_invalid_bank_info(self, test_session, sample_members, sample_reward_results):
        """5.2 GMO CSV出力 - 銀行情報不完全エラー"""
        service = PaymentManagementService(test_session)
        
        # 田中太郎の銀行コードを削除
        tanaka = next(m for m in sample_members if m.member_number == "0000001")
        tanaka.bank_code = None
        test_session.commit()
        
        with pytest.raises(ValidationError, match="銀行情報が不完全な会員がいます"):
            service.export_gmo_csv("2025-08")

    def test_confirm_payment_success(self, test_session, sample_members, sample_reward_results):
        """5.3 支払確定 - 成功ケース"""
        service = PaymentManagementService(test_session)
        
        # テスト実行
        result = service.confirm_payment(
            member_id="member001",
            target_month="2025-08", 
            payment_amount=Decimal('8500.00'),
            memo="テスト支払確定"
        )
        
        # 結果確認
        assert result["success"] is True
        assert "田中太郎" in result["message"]
        assert result["payment_amount"] == 8500.0
        assert "payment_record_id" in result
        
        # データベース確認
        from app.models.payment_record import PaymentRecord
        payment_record = test_session.query(PaymentRecord).filter(
            PaymentRecord.id == result["payment_record_id"]
        ).first()
        
        assert payment_record is not None
        assert payment_record.member_id == "member001"
        assert payment_record.target_month == "2025-08"
        assert payment_record.payment_amount == Decimal('8500.00')
        assert payment_record.status == "confirmed"
        assert payment_record.memo == "テスト支払確定"

    def test_confirm_payment_member_not_found(self, test_session):
        """5.3 支払確定 - 会員不存在エラー"""
        service = PaymentManagementService(test_session)
        
        with pytest.raises(DataNotFoundError, match="会員ID: nonexistent が見つかりません"):
            service.confirm_payment(
                member_id="nonexistent",
                target_month="2025-08",
                payment_amount=Decimal('5000.00')
            )

    def test_confirm_payment_duplicate(self, test_session, sample_members, sample_reward_results):
        """5.3 支払確定 - 重複確定エラー"""
        service = PaymentManagementService(test_session)
        
        # 1回目の確定
        service.confirm_payment(
            member_id="member001",
            target_month="2025-08",
            payment_amount=Decimal('8500.00')
        )
        
        # 2回目の確定（エラー）
        with pytest.raises(BusinessRuleError, match="既に支払確定済みです"):
            service.confirm_payment(
                member_id="member001",
                target_month="2025-08", 
                payment_amount=Decimal('8500.00')
            )

    def test_confirm_payment_amount_mismatch(self, test_session, sample_members, sample_reward_results):
        """5.3 支払確定 - 支払金額不正エラー"""
        service = PaymentManagementService(test_session)
        
        with pytest.raises(BusinessRuleError, match="支払金額が不正です"):
            service.confirm_payment(
                member_id="member001",
                target_month="2025-08",
                payment_amount=Decimal('9999.99')  # 実際は8500円
            )

    def test_get_payment_history_success(self, test_session, sample_payment_records):
        """支払履歴取得 - 成功ケース"""
        service = PaymentManagementService(test_session)
        
        # テスト実行
        result = service.get_payment_history(page=1, limit=10)
        
        # 結果確認
        assert len(result["items"]) == 1
        assert result["pagination"]["total_count"] == 1
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["has_next"] is False
        
        # 履歴アイテム確認
        item = result["items"][0]
        assert item["member_number"] == "0000002"
        assert item["member_name"] == "佐藤花子"
        assert item["target_month"] == "2025-07"
        assert item["payment_amount"] == 12000.0

    def test_get_payment_history_with_filter(self, test_session, sample_payment_records):
        """支払履歴取得 - 月フィルタ"""
        service = PaymentManagementService(test_session)
        
        # 存在する月
        result = service.get_payment_history(month_filter="2025-07")
        assert len(result["items"]) == 1
        
        # 存在しない月  
        result = service.get_payment_history(month_filter="2025-06")
        assert len(result["items"]) == 0

    def test_private_methods(self, test_session, sample_members, sample_reward_results):
        """プライベートメソッドのテスト"""
        service = PaymentManagementService(test_session)
        
        # _get_latest_reward_results
        results = service._get_latest_reward_results("2025-08")
        assert len(results) == 3
        
        # _get_member_reward_result
        tanaka_result = service._get_member_reward_result("member001", "2025-08")
        assert tanaka_result is not None
        assert tanaka_result.total_amount == Decimal('8500.00')
        
        # _get_carryover_amount (現在は0を返す)
        carryover = service._get_carryover_amount("member001", "2025-08")
        assert carryover == Decimal('0')
        
        # _get_payment_status
        status = service._get_payment_status("member001", "2025-08")
        assert status == "pending"
        
        # _validate_bank_info
        target_valid = {
            "bank_code": "0001",
            "branch_code": "123", 
            "account_number": "1234567",
            "account_holder_kana": "テスト"
        }
        validation = service._validate_bank_info(target_valid)
        assert validation["valid"] is True
        
        target_invalid = {
            "account_holder_kana": "テスト"
        }
        validation = service._validate_bank_info(target_invalid)
        assert validation["valid"] is False
        assert "銀行コードが未設定" in validation["error"]

    def test_gmo_csv_creation(self, test_session):
        """GMO CSVレコード作成テスト"""
        service = PaymentManagementService(test_session)
        
        # 一般銀行
        target_bank = {
            "bank_code": "0001",
            "branch_code": "123",
            "account_type": "普通",
            "account_number": "1234567",
            "account_holder_kana": "テストタロウ",
            "payment_amount": 10000
        }
        
        row = service._create_gmo_csv_row(target_bank)
        assert row == ["0001", "123", "1", "1234567", "テストタロウ", "10000", "", ""]
        
        # ゆうちょ銀行
        target_postal = {
            "postal_symbol": "12345",
            "postal_number": "67890123", 
            "account_holder_kana": "テストハナコ",
            "payment_amount": 8500
        }
        
        row = service._create_gmo_csv_row(target_postal)
        assert row == ["9900", "000", "1", "67890123", "テストハナコ", "8500", "", ""]