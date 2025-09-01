#!/usr/bin/env python3
"""
5人の完全なテスト会員データ追加スクリプト
30項目すべてのフィールドを含む
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.member import Member, MemberStatus, Title, UserType, Plan, PaymentMethod, Gender, AccountType
from datetime import datetime

# セッション作成
db = SessionLocal()

# 5人の完全なテスト会員データ（30項目完全版）
new_members = [
    {
        # 1-5: 基本情報
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000011",
        "name": "中村健一",
        "kana": None,  # カナは廃止
        "email": "nakamura@example.com",
        
        # 6-9: MLM情報
        "title": Title.LORD_LADY,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.CARD,
        
        # 10-11: 日付情報
        "registration_date": "2017-12-01",
        "withdrawal_date": None,
        
        # 12-17: 連絡先情報
        "phone": "090-1111-2222",
        "gender": Gender.MALE,
        "postal_code": "150-0001",
        "prefecture": "東京都",
        "address2": "渋谷区渋谷1-2-3",
        "address3": "渋谷タワー801号室",
        
        # 18-21: 組織情報
        "upline_id": "10000000001",
        "upline_name": "山田太郎",
        "referrer_id": "10000000001",
        "referrer_name": "山田太郎",
        
        # 22-29: 銀行情報
        "bank_name": "三井住友銀行",
        "bank_code": "0009",
        "branch_name": "渋谷支店",
        "branch_code": "654",
        "account_number": "9876543",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        
        # 30: その他
        "notes": "2017年度優秀賞受賞・関東エリアリーダー"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000012",
        "name": "藤田美穂",
        "kana": None,
        "email": "fujita@example.com",
        "title": Title.KING_QUEEN,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.BANK,
        "registration_date": "2018-06-15",
        "withdrawal_date": None,
        "phone": "080-3333-4444",
        "gender": Gender.FEMALE,
        "postal_code": "530-0005",
        "prefecture": "大阪府",
        "address2": "大阪市北区中之島3-3-3",
        "address3": "中之島ビル1501",
        "upline_id": "10000000002",
        "upline_name": "佐藤花子",
        "referrer_id": "10000000011",
        "referrer_name": "中村健一",
        "bank_name": "りそな銀行",
        "bank_code": "0010",
        "branch_name": "大阪本店",
        "branch_code": "100",
        "account_number": "1357924",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        "notes": "関西エリア統括マネージャー・月間売上TOP10常連"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000013",
        "name": "松田直樹",
        "kana": None,
        "email": "matsuda@example.com",
        "title": Title.KNIGHT_DAME,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.TRANSFER,
        "registration_date": "2019-03-20",
        "withdrawal_date": None,
        "phone": "070-5555-6666",
        "gender": Gender.MALE,
        "postal_code": "460-0008",
        "prefecture": "愛知県",
        "address2": "名古屋市中区栄4-5-6",
        "address3": "栄ビルディング702",
        "upline_id": "10000000003",
        "upline_name": "田中一郎",
        "referrer_id": "10000000012",
        "referrer_name": "藤田美穂",
        "bank_name": "ゆうちょ銀行",
        "bank_code": None,
        "branch_name": None,
        "branch_code": None,
        "account_number": None,
        "yucho_symbol": "14100",
        "yucho_number": "98765432",
        "account_type": None,
        "notes": "東海エリア新規開拓担当・若手育成プログラム参加"
    },
    {
        "status": MemberStatus.ACTIVE,
        "member_number": "10000000014",
        "name": "清水由美",
        "kana": None,
        "email": "shimizu@example.com",
        "title": Title.LORD_LADY,
        "user_type": UserType.NORMAL,
        "plan": Plan.HERO,
        "payment_method": PaymentMethod.INFOCART,
        "registration_date": "2020-09-10",
        "withdrawal_date": None,
        "phone": "090-7777-8888",
        "gender": Gender.FEMALE,
        "postal_code": "650-0021",
        "prefecture": "兵庫県",
        "address2": "神戸市中央区三宮町1-1-1",
        "address3": "三宮センタービル2001",
        "upline_id": "10000000012",
        "upline_name": "藤田美穂",
        "referrer_id": "10000000002",
        "referrer_name": "佐藤花子",
        "bank_name": "三菱UFJ銀行",
        "bank_code": "0005",
        "branch_name": "神戸支店",
        "branch_code": "456",
        "account_number": "2468135",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.CHECKING,
        "notes": "インフォカート決済専門・オンラインマーケティング担当"
    },
    {
        "status": MemberStatus.INACTIVE,
        "member_number": "10000000015",
        "name": "吉田大介",
        "kana": None,
        "email": "yoshida@example.com",
        "title": Title.NONE,
        "user_type": UserType.ATTENTION,
        "plan": Plan.TEST,
        "payment_method": PaymentMethod.CARD,
        "registration_date": "2021-11-25",
        "withdrawal_date": None,
        "phone": "080-9999-0000",
        "gender": Gender.MALE,
        "postal_code": "920-0856",
        "prefecture": "石川県",
        "address2": "金沢市昭和町16-1",
        "address3": "金沢スカイビル505",
        "upline_id": "10000000013",
        "upline_name": "松田直樹",
        "referrer_id": "10000000013",
        "referrer_name": "松田直樹",
        "bank_name": "北國銀行",
        "bank_code": "0146",
        "branch_name": "金沢中央支店",
        "branch_code": "101",
        "account_number": "3692581",
        "yucho_symbol": None,
        "yucho_number": None,
        "account_type": AccountType.ORDINARY,
        "notes": "休会中・2024年12月復帰予定・要注意フラグ設定済み"
    }
]

# データ挿入
try:
    inserted_count = 0
    for data in new_members:
        # 既存チェック
        existing = db.query(Member).filter(
            Member.member_number == data["member_number"]
        ).first()
        
        if existing:
            print(f"⚠️  会員番号 {data['member_number']} は既に存在します")
            continue
            
        member = Member(**data)
        db.add(member)
        inserted_count += 1
        print(f"✅ {data['name']} ({data['member_number']}) を追加しました")
    
    db.commit()
    print(f"\n✅ {inserted_count}件の新規会員データを追加しました")
    
    # 統計情報表示
    total_count = db.query(Member).count()
    active_count = db.query(Member).filter(Member.status == MemberStatus.ACTIVE).count()
    inactive_count = db.query(Member).filter(Member.status == MemberStatus.INACTIVE).count()
    withdrawn_count = db.query(Member).filter(Member.status == MemberStatus.WITHDRAWN).count()
    
    print(f"\n📊 更新後の統計情報:")
    print(f"  - 総会員数: {total_count}名")
    print(f"  - アクティブ: {active_count}名")
    print(f"  - 休会中: {inactive_count}名")
    print(f"  - 退会済: {withdrawn_count}名")
    
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    db.rollback()
finally:
    db.close()