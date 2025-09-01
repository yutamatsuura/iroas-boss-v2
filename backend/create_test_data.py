#!/usr/bin/env python3
"""
テスト会員データ作成スクリプト
要件定義書の30項目を完全に含むテストデータを作成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.member import Member, MemberStatus, Title, UserType, Plan, PaymentMethod, Gender, AccountType
from datetime import datetime

# テーブル作成
Base.metadata.create_all(bind=engine)

# セッション作成
db = SessionLocal()

# テスト会員データ（30項目完全版）
test_members = [
    {
        # 1-5: 基本情報
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000001",
        "name": "山田太郎",
        "kana": None,  # カナは廃止
        "email": "yamada@example.com",
        
        # 6-9: MLM情報
        "title": Title.EMPEROR_EMPRESS,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.CARD,
        
        # 10-11: 日付情報
        "registration_date": "2016-04-15",
        "withdrawal_date": None,
        
        # 12-17: 連絡先情報
        "phone": "090-1234-5678",
        "gender": Gender.MALE,
        "postal_code": "100-0001",
        "prefecture": "東京都",
        "address2": "千代田区千代田",
        "address3": "1-1-1 皇居ビル101",
        
        # 18-21: 組織情報
        "upline_id": None,
        "upline_name": None,
        "referrer_id": None,
        "referrer_name": None,
        
        # 22-29: 銀行情報
        "bank_name": "三菱UFJ銀行",
        "bank_code": "0005",
        "branch_name": "東京営業部",
        "branch_code": "001",
        "account_number": "1234567",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        
        # 30: その他
        "notes": "創業メンバー・最高称号保持者"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000002",
        "name": "佐藤花子",
        "kana": None,
        "email": "sato@example.com",
        "title": Title.KING_QUEEN,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.BANK,
        "registration_date": "2017-08-20",
        "withdrawal_date": None,
        "phone": "080-2222-3333",
        "gender": Gender.FEMALE,
        "postal_code": "530-0001",
        "prefecture": "大阪府",
        "address2": "大阪市北区梅田",
        "address3": "2-2-2 梅田タワー2001",
        "upline_id": "10000000001",
        "upline_name": "山田太郎",
        "referrer_id": "10000000001",
        "referrer_name": "山田太郎",
        "bank_name": "みずほ銀行",
        "bank_code": "0001",
        "branch_name": "大阪支店",
        "branch_code": "101",
        "account_number": "2345678",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        "notes": "関西エリアのトップリーダー"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000003",
        "name": "田中一郎",
        "kana": None,
        "email": "tanaka@example.com",
        "title": Title.LORD_LADY,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.TRANSFER,
        "registration_date": "2018-03-10",
        "withdrawal_date": None,
        "phone": "070-3333-4444",
        "gender": Gender.MALE,
        "postal_code": "460-0001",
        "prefecture": "愛知県",
        "address2": "名古屋市中区",
        "address3": "栄3-3-3",
        "upline_id": "10000000001",
        "upline_name": "山田太郎",
        "referrer_id": "10000000002",
        "referrer_name": "佐藤花子",
        "bank_name": "ゆうちょ銀行",
        "bank_code": None,
        "branch_name": None,
        "branch_code": None,
        "account_number": None,
        "yucho_symbol": "12345",
        "yucho_number": "12345678",
        "account_type": None,
        "notes": "口座振替利用者"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000004",
        "name": "鈴木美咲",
        "kana": None,
        "email": "suzuki@example.com",
        "title": Title.KNIGHT_DAME,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.INFOCART,
        "registration_date": "2019-06-15",
        "withdrawal_date": None,
        "phone": "090-4444-5555",
        "gender": Gender.FEMALE,
        "postal_code": "810-0001",
        "prefecture": "福岡県",
        "address2": "福岡市中央区天神",
        "address3": "4-4-4",
        "upline_id": "10000000002",
        "upline_name": "佐藤花子",
        "referrer_id": "10000000002",
        "referrer_name": "佐藤花子",
        "bank_name": "西日本シティ銀行",
        "bank_code": "0190",
        "branch_name": "天神支店",
        "branch_code": "001",
        "account_number": "3456789",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        "notes": "インフォカート決済利用"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000005",
        "name": "高橋健太",
        "kana": None,
        "email": "takahashi@example.com",
        "title": Title.NONE,
        "user_type": UserType.NORMAL,
        "plan": Plan.TEST,
        "payment_method": PaymentMethod.CARD,
        "registration_date": "2020-01-10",
        "withdrawal_date": None,
        "phone": "080-5555-6666",
        "gender": Gender.MALE,
        "postal_code": "060-0001",
        "prefecture": "北海道",
        "address2": "札幌市中央区",
        "address3": "北1条西5-5-5",
        "upline_id": "10000000003",
        "upline_name": "田中一郎",
        "referrer_id": "10000000003",
        "referrer_name": "田中一郎",
        "bank_name": "北洋銀行",
        "bank_code": "0501",
        "branch_name": "札幌支店",
        "branch_code": "001",
        "account_number": "4567890",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        "notes": "テストプラン利用者"
    },
    {
        "status": MemberStatus.INACTIVE,
        "member_number": "10000000006",
        "name": "渡辺さくら",
        "kana": None,
        "email": "watanabe@example.com",
        "title": Title.KNIGHT_DAME,
        "user_type": UserType.ATTENTION,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.BANK,
        "registration_date": "2019-09-01",
        "withdrawal_date": None,
        "phone": "070-6666-7777",
        "gender": Gender.FEMALE,
        "postal_code": "980-0001",
        "prefecture": "宮城県",
        "address2": "仙台市青葉区",
        "address3": "中央6-6-6",
        "upline_id": "10000000004",
        "upline_name": "鈴木美咲",
        "referrer_id": "10000000004",
        "referrer_name": "鈴木美咲",
        "bank_name": "七十七銀行",
        "bank_code": "0125",
        "branch_name": "仙台支店",
        "branch_code": "001",
        "account_number": "5678901",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.CHECKING,
        "notes": "休会中・要注意ユーザー"
    },
    {
        "status": MemberStatus.WITHDRAWN,
        "member_number": "10000000007",
        "name": "伊藤次郎",
        "kana": None,
        "email": "ito@example.com",
        "title": Title.NONE,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.CARD,
        "registration_date": "2018-12-01",
        "withdrawal_date": "2021-03-31",
        "phone": "090-7777-8888",
        "gender": Gender.MALE,
        "postal_code": "730-0001",
        "prefecture": "広島県",
        "address2": "広島市中区",
        "address3": "紙屋町7-7-7",
        "upline_id": "10000000005",
        "upline_name": "高橋健太",
        "referrer_id": "10000000005",
        "referrer_name": "高橋健太",
        "bank_name": None,
        "bank_code": None,
        "branch_name": None,
        "branch_code": None,
        "account_number": None,
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": None,
        "notes": "2021年3月退会済み"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000008",
        "name": "山本真理子",
        "kana": None,
        "email": "yamamoto@example.com",
        "title": Title.LORD_LADY,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.TRANSFER,
        "registration_date": "2020-07-15",
        "withdrawal_date": None,
        "phone": "080-8888-9999",
        "gender": Gender.FEMALE,
        "postal_code": "600-8001",
        "prefecture": "京都府",
        "address2": "京都市下京区",
        "address3": "四条通8-8-8",
        "upline_id": "10000000002",
        "upline_name": "佐藤花子",
        "referrer_id": "10000000001",
        "referrer_name": "山田太郎",
        "bank_name": "京都銀行",
        "bank_code": "0158",
        "branch_name": "四条支店",
        "branch_code": "011",
        "account_number": "6789012",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        "notes": None
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000009",
        "name": "小林大輔",
        "kana": None,
        "email": "kobayashi@example.com",
        "title": Title.NONE,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.CARD,
        "registration_date": "2021-01-20",
        "withdrawal_date": None,
        "phone": "070-9999-0000",
        "gender": Gender.MALE,
        "postal_code": "330-0001",
        "prefecture": "埼玉県",
        "address2": "さいたま市大宮区",
        "address3": "大宮9-9-9",
        "upline_id": "10000000008",
        "upline_name": "山本真理子",
        "referrer_id": "10000000008",
        "referrer_name": "山本真理子",
        "bank_name": "埼玉りそな銀行",
        "bank_code": "0017",
        "branch_name": "大宮支店",
        "branch_code": "201",
        "account_number": "7890123",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        "notes": "新規会員"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000010",
        "name": "加藤愛美",
        "kana": None,
        "email": "kato@example.com",
        "title": Title.KNIGHT_DAME,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.BANK,
        "registration_date": "2021-05-01",
        "withdrawal_date": None,
        "phone": "090-0000-1111",
        "gender": Gender.FEMALE,
        "postal_code": "220-0001",
        "prefecture": "神奈川県",
        "address2": "横浜市西区",
        "address3": "みなとみらい10-10-10",
        "upline_id": "10000000009",
        "upline_name": "小林大輔",
        "referrer_id": "10000000008",
        "referrer_name": "山本真理子",
        "bank_name": "横浜銀行",
        "bank_code": "0138",
        "branch_name": "みなとみらい支店",
        "branch_code": "301",
        "account_number": "8901234",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        "notes": "急成長中のメンバー"
    }
]

# データ挿入
try:
    for data in test_members:
        member = Member(**data)
        db.add(member)
    
    db.commit()
    print(f"✅ {len(test_members)}件のテスト会員データを作成しました")
    
    # 統計情報表示
    active_count = db.query(Member).filter(Member.status == MemberStatus.ACTIVE).count()
    inactive_count = db.query(Member).filter(Member.status == MemberStatus.INACTIVE).count()
    withdrawn_count = db.query(Member).filter(Member.status == MemberStatus.WITHDRAWN).count()
    
    print(f"\n📊 統計情報:")
    print(f"  - アクティブ: {active_count}名")
    print(f"  - 休会中: {inactive_count}名")
    print(f"  - 退会済: {withdrawn_count}名")
    print(f"  - 合計: {active_count + inactive_count + withdrawn_count}名")
    
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    db.rollback()
finally:
    db.close()