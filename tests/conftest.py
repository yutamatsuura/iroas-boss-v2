# -*- coding: utf-8 -*-
"""
pytest設定ファイル

実データベースを使用したテスト環境構築
要件定義に従って全33APIの動作を保証
"""

import pytest
import tempfile
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.database import Base, get_db
from app.models import *  # 全モデルをインポート


@pytest.fixture(scope="session")
def test_engine():
    """テスト用SQLiteエンジン作成"""
    # メモリDBではなく一時ファイルDBを使用（実データ主義）
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    database_url = f"sqlite:///{temp_db.name}"
    
    engine = create_engine(
        database_url,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # クリーンアップ
    temp_db.close()
    os.unlink(temp_db.name)


@pytest.fixture(scope="function")
def test_session(test_engine) -> Generator:
    """テスト用セッション作成"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_db_dependency_override(test_session):
    """データベース依存性オーバーライド"""
    def override_get_db():
        try:
            yield test_session
        finally:
            pass
    
    return override_get_db


@pytest.fixture(scope="function")
def sample_members(test_session):
    """テスト用会員データ作成"""
    from app.models.member import Member
    
    members_data = [
        {
            "id": "member001",
            "member_number": "0000001", 
            "name": "田中太郎",
            "name_kana": "タナカタロウ",
            "email": "tanaka@example.com",
            "status": "アクティブ",
            "title": "称号なし",
            "user_type": "通常",
            "plan": "ヒーロープラン",
            "payment_method": "カード決済",
            "phone": "090-1234-5678",
            "gender": "男性",
            "postal_code": "100-0001",
            "prefecture": "東京都",
            "address2": "千代田区千代田",
            "address3": "1-1-1",
            "direct_sponsor_id": None,
            "referrer_id": None,
            "bank_name": "三井住友銀行",
            "bank_code": "0009",
            "branch_name": "本店",
            "branch_code": "001",
            "account_number": "1234567",
            "account_type": "普通"
        },
        {
            "id": "member002",
            "member_number": "0000002",
            "name": "佐藤花子", 
            "name_kana": "サトウハナコ",
            "email": "sato@example.com",
            "status": "アクティブ",
            "title": "称号なし",
            "user_type": "通常",
            "plan": "ヒーロープラン",
            "payment_method": "口座振替",
            "phone": "090-2345-6789",
            "gender": "女性",
            "postal_code": "150-0001",
            "prefecture": "東京都",
            "address2": "渋谷区神宮前",
            "address3": "2-2-2",
            "direct_sponsor_id": "member001",
            "referrer_id": "member001",
            "bank_name": "みずほ銀行",
            "bank_code": "0001", 
            "branch_name": "新宿支店",
            "branch_code": "123",
            "account_number": "2345678",
            "account_type": "普通"
        },
        {
            "id": "member003",
            "member_number": "0000003",
            "name": "山田次郎",
            "name_kana": "ヤマダジロウ", 
            "email": "yamada@example.com",
            "status": "アクティブ",
            "title": "称号なし",
            "user_type": "通常",
            "plan": "テストプラン",
            "payment_method": "銀行振込",
            "phone": "090-3456-7890",
            "gender": "男性",
            "postal_code": "530-0001",
            "prefecture": "大阪府",
            "address2": "大阪市北区梅田",
            "address3": "3-3-3",
            "direct_sponsor_id": "member002",
            "referrer_id": "member002",
            "postal_symbol": "12345",
            "postal_number": "67890123"
        }
    ]
    
    members = []
    for data in members_data:
        member = Member(**data)
        test_session.add(member)
        members.append(member)
    
    test_session.commit()
    return members


@pytest.fixture(scope="function") 
def sample_reward_results(test_session, sample_members):
    """テスト用報酬結果データ作成"""
    from app.models.reward_result import RewardResult
    from decimal import Decimal
    from datetime import datetime
    
    reward_results = []
    amounts = [Decimal('8500.00'), Decimal('15670.00'), Decimal('4800.00')]  # 5000円以上、以上、未満
    
    for member, amount in zip(sample_members, amounts):
        reward_result = RewardResult(
            id=f"reward_{member.id}",
            member_id=member.id,
            calculation_date=datetime.now(),
            target_month="2025-08",
            total_amount=amount,
            daily_bonus=amount * Decimal('0.4'),
            title_bonus=amount * Decimal('0.2'),
            referral_bonus=amount * Decimal('0.2'), 
            power_bonus=amount * Decimal('0.1'),
            maintenance_bonus=Decimal('0'),
            sales_activity_bonus=Decimal('0'),
            royal_family_bonus=amount * Decimal('0.1')
        )
        test_session.add(reward_result)
        reward_results.append(reward_result)
    
    test_session.commit()
    return reward_results


@pytest.fixture(scope="function")
def sample_payment_records(test_session, sample_members):
    """テスト用支払記録データ作成"""
    from app.models.payment_record import PaymentRecord
    from decimal import Decimal
    from datetime import datetime
    
    # 一部会員に既存の支払記録を作成
    payment_record = PaymentRecord(
        member_id=sample_members[1].id,  # 佐藤花子
        target_month="2025-07",
        payment_method="bank_transfer",
        reward_amount=Decimal('12000.00'),
        carryover_amount=Decimal('0'),
        payment_amount=Decimal('12000.00'),
        status="confirmed",
        confirmed_at=datetime.now()
    )
    
    test_session.add(payment_record)
    test_session.commit()
    return [payment_record]