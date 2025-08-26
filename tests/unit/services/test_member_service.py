# -*- coding: utf-8 -*-
"""
会員管理サービステスト
Phase A-1b API 1.1-1.4, 1.6の動作保証

実データ主義テスト：
- 30項目会員データ完全検証
- 実データベース操作確認
- 業務エラーハンドリング検証
"""

import pytest
from decimal import Decimal
from datetime import datetime, date

from app.services.member_service import MemberService
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../backend"))
from app.core.exceptions import BusinessRuleError, DataNotFoundError, ValidationError


class TestMemberService:
    """会員管理サービステスト"""

    def test_get_members_success(self, test_session, sample_members):
        """1.1 会員一覧取得 - 成功ケース"""
        service = MemberService(test_session)
        
        # テスト実行
        result = service.get_members(page=1, limit=10)
        
        # 検証
        assert len(result["items"]) == 3
        assert result["pagination"]["total_count"] == 3
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["has_next"] is False
        
        # 会員データ確認
        tanaka = next(m for m in result["items"] if m["member_number"] == "0000001")
        assert tanaka["name"] == "田中太郎"
        assert tanaka["status"] == "アクティブ"
        assert tanaka["plan"] == "ヒーロープラン"

    def test_get_members_pagination(self, test_session, sample_members):
        """1.1 会員一覧取得 - ページネーション"""
        service = MemberService(test_session)
        
        # 1ページ目（2件）
        result = service.get_members(page=1, limit=2)
        assert len(result["items"]) == 2
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is False
        
        # 2ページ目（1件）
        result = service.get_members(page=2, limit=2)
        assert len(result["items"]) == 1
        assert result["pagination"]["has_next"] is False
        assert result["pagination"]["has_prev"] is True

    def test_get_members_filter_by_status(self, test_session, sample_members):
        """1.1 会員一覧取得 - ステータスフィルタ"""
        service = MemberService(test_session)
        
        # 退会者作成
        retired_member = sample_members[0]
        retired_member.status = "退会済"
        test_session.commit()
        
        # アクティブのみ取得
        result = service.get_members(status_filter="アクティブ")
        assert len(result["items"]) == 2
        
        # 退会済のみ取得  
        result = service.get_members(status_filter="退会済")
        assert len(result["items"]) == 1

    def test_create_member_success(self, test_session):
        """1.2 新規会員登録 - 成功ケース"""
        service = MemberService(test_session)
        
        member_data = {
            "member_number": "0000004",
            "name": "鈴木一郎",
            "name_kana": "スズキイチロウ", 
            "email": "suzuki@example.com",
            "plan": "ヒーロープラン",
            "payment_method": "カード決済",
            "phone": "090-4567-8901",
            "gender": "男性",
            "postal_code": "460-0001",
            "prefecture": "愛知県",
            "address2": "名古屋市中区錦",
            "address3": "4-4-4",
            "bank_name": "UFJ銀行",
            "bank_code": "0005", 
            "branch_name": "本店",
            "branch_code": "001",
            "account_number": "3456789",
            "account_type": "普通"
        }
        
        # テスト実行
        result = service.create_member(member_data)
        
        # 結果確認
        assert result["member_id"] is not None
        assert result["member_number"] == "0000004"
        assert result["name"] == "鈴木一郎"
        
        # データベース確認
        from app.models.member import Member
        created_member = test_session.query(Member).filter(
            Member.member_number == "0000004"
        ).first()
        
        assert created_member is not None
        assert created_member.name == "鈴木一郎"
        assert created_member.status == "アクティブ"  # デフォルト値
        assert created_member.title == "称号なし"    # デフォルト値
        assert created_member.user_type == "通常"    # デフォルト値

    def test_create_member_duplicate_number(self, test_session, sample_members):
        """1.2 新規会員登録 - 会員番号重複エラー"""
        service = MemberService(test_session)
        
        member_data = {
            "member_number": "0000001",  # 既存の会員番号
            "name": "重複太郎",
            "email": "duplicate@example.com"
        }
        
        with pytest.raises(BusinessRuleError, match="会員番号 0000001 は既に使用されています"):
            service.create_member(member_data)

    def test_create_member_duplicate_email(self, test_session, sample_members):
        """1.2 新規会員登録 - メールアドレス重複エラー"""
        service = MemberService(test_session)
        
        member_data = {
            "member_number": "0000099",
            "name": "重複花子", 
            "email": "tanaka@example.com"  # 既存のメールアドレス
        }
        
        with pytest.raises(BusinessRuleError, match="メールアドレス tanaka@example.com は既に使用されています"):
            service.create_member(member_data)

    def test_get_member_success(self, test_session, sample_members):
        """1.3 会員詳細取得 - 成功ケース"""
        service = MemberService(test_session)
        
        # テスト実行
        result = service.get_member(sample_members[0].id)
        
        # 結果確認
        assert result["member_id"] == sample_members[0].id
        assert result["member_number"] == "0000001"
        assert result["name"] == "田中太郎"
        assert result["name_kana"] == "タナカタロウ"
        assert result["email"] == "tanaka@example.com"
        assert result["status"] == "アクティブ"
        assert result["plan"] == "ヒーロープラン"
        assert result["payment_method"] == "カード決済"
        assert result["bank_name"] == "三井住友銀行"
        
        # 全30項目の存在確認
        expected_fields = [
            "member_id", "member_number", "name", "name_kana", "email",
            "status", "title", "user_type", "plan", "payment_method",
            "registration_date", "withdrawal_date", "phone", "gender",
            "postal_code", "prefecture", "address2", "address3",
            "direct_sponsor_id", "direct_sponsor_name", "referrer_id", "referrer_name",
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "postal_symbol", "postal_number", "account_type", "memo"
        ]
        
        for field in expected_fields:
            assert field in result

    def test_get_member_not_found(self, test_session):
        """1.3 会員詳細取得 - 会員不存在エラー"""
        service = MemberService(test_session)
        
        with pytest.raises(DataNotFoundError, match="会員ID: nonexistent が見つかりません"):
            service.get_member("nonexistent")

    def test_update_member_success(self, test_session, sample_members):
        """1.4 会員情報更新 - 成功ケース"""
        service = MemberService(test_session)
        
        update_data = {
            "name": "田中太郎（更新）",
            "phone": "090-9999-9999",
            "bank_name": "更新後銀行",
            "memo": "更新テスト"
        }
        
        # テスト実行
        result = service.update_member(sample_members[0].id, update_data)
        
        # 結果確認
        assert result["success"] is True
        assert "更新されました" in result["message"]
        
        # データベース確認
        updated_member = test_session.query(type(sample_members[0])).filter(
            type(sample_members[0]).id == sample_members[0].id
        ).first()
        
        assert updated_member.name == "田中太郎（更新）"
        assert updated_member.phone == "090-9999-9999" 
        assert updated_member.bank_name == "更新後銀行"
        assert updated_member.memo == "更新テスト"

    def test_update_member_not_found(self, test_session):
        """1.4 会員情報更新 - 会員不存在エラー"""
        service = MemberService(test_session)
        
        with pytest.raises(DataNotFoundError, match="会員ID: nonexistent が見つかりません"):
            service.update_member("nonexistent", {"name": "存在しない"})

    def test_update_member_duplicate_email(self, test_session, sample_members):
        """1.4 会員情報更新 - メールアドレス重複エラー"""
        service = MemberService(test_session)
        
        with pytest.raises(BusinessRuleError, match="メールアドレス .* は既に他の会員によって使用されています"):
            service.update_member(
                sample_members[0].id,
                {"email": "sato@example.com"}  # 佐藤花子のメール
            )

    def test_search_members_by_number(self, test_session, sample_members):
        """1.6 会員検索 - 会員番号検索"""
        service = MemberService(test_session)
        
        # 完全一致
        result = service.search_members("0000001")
        assert len(result) == 1
        assert result[0]["member_number"] == "0000001"
        
        # 部分一致
        result = service.search_members("000000")
        assert len(result) == 3  # 全て該当

    def test_search_members_by_name(self, test_session, sample_members):
        """1.6 会員検索 - 氏名検索"""
        service = MemberService(test_session)
        
        # 完全一致
        result = service.search_members("田中太郎")
        assert len(result) == 1
        assert result[0]["name"] == "田中太郎"
        
        # 部分一致
        result = service.search_members("田中")
        assert len(result) == 1
        
        # カナ検索
        result = service.search_members("タナカ")
        assert len(result) == 1

    def test_search_members_by_email(self, test_session, sample_members):
        """1.6 会員検索 - メールアドレス検索"""
        service = MemberService(test_session)
        
        # 完全一致
        result = service.search_members("tanaka@example.com")
        assert len(result) == 1
        assert result[0]["email"] == "tanaka@example.com"
        
        # ドメイン検索
        result = service.search_members("example.com")
        assert len(result) == 3  # 全て該当

    def test_search_members_empty_result(self, test_session, sample_members):
        """1.6 会員検索 - 該当なし"""
        service = MemberService(test_session)
        
        result = service.search_members("存在しない検索語")
        assert result == []

    def test_search_members_multiple_conditions(self, test_session, sample_members):
        """1.6 会員検索 - 複数条件"""
        service = MemberService(test_session)
        
        # 複数条件での検索（OR条件）
        result = service.search_members("田中", plan_filter="ヒーロープラン")
        assert len(result) == 1
        assert result[0]["name"] == "田中太郎"
        
        # プランフィルタのみ
        result = service.search_members(plan_filter="テストプラン")
        assert len(result) == 1
        assert result[0]["name"] == "山田次郎"

    def test_service_initialization(self, test_session):
        """サービス初期化テスト"""
        service = MemberService(test_session)
        assert service.db == test_session

    def test_member_data_validation(self, test_session):
        """会員データバリデーション"""
        service = MemberService(test_session)
        
        # 必須項目不足
        invalid_data = {}
        
        with pytest.raises((ValidationError, KeyError)):
            service.create_member(invalid_data)

    def test_member_status_transitions(self, test_session, sample_members):
        """会員ステータス遷移テスト"""
        service = MemberService(test_session)
        
        member_id = sample_members[0].id
        
        # アクティブ -> 休会中
        service.update_member(member_id, {"status": "休会中"})
        member = service.get_member(member_id)
        assert member["status"] == "休会中"
        
        # 休会中 -> アクティブ
        service.update_member(member_id, {"status": "アクティブ"})
        member = service.get_member(member_id)
        assert member["status"] == "アクティブ"

    def test_bank_account_info_handling(self, test_session, sample_members):
        """銀行口座情報処理テスト"""
        service = MemberService(test_session)
        
        # ゆうちょ銀行情報更新
        update_data = {
            "bank_name": "ゆうちょ銀行",
            "postal_symbol": "99999",
            "postal_number": "88888888"
        }
        
        service.update_member(sample_members[2].id, update_data)
        member = service.get_member(sample_members[2].id)
        
        assert member["bank_name"] == "ゆうちょ銀行"
        assert member["postal_symbol"] == "99999"
        assert member["postal_number"] == "88888888"

    def test_special_characters_handling(self, test_session):
        """特殊文字処理テスト"""
        service = MemberService(test_session)
        
        member_data = {
            "member_number": "0000999",
            "name": "髙橋・佐々木",  # 特殊文字
            "name_kana": "タカハシ・ササキ",
            "email": "test+special@example.com",  # +記号
            "address2": "東京都渋谷区神宮前１－２－３",  # 全角数字
            "memo": "特殊文字テスト：①②③"
        }
        
        result = service.create_member(member_data)
        assert result["name"] == "髙橋・佐々木"
        
        # 取得確認
        member = service.get_member(result["member_id"])
        assert member["name"] == "髙橋・佐々木"
        assert member["email"] == "test+special@example.com"