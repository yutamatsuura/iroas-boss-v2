"""
テストデータ投入スクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Member, MemberStatus, Title, UserType, Plan, PaymentMethod, Gender, AccountType
from app.database import Base

# データベースURL
database_url = os.getenv(
    "DATABASE_URL", 
    "postgresql://lennon@localhost:5432/iroas_boss_dev"
)

# エンジンとセッション作成
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def generate_test_members():
    """テスト用会員データ生成"""
    members = []
    
    # 姓と名のサンプル
    last_names = ["山田", "鈴木", "田中", "佐藤", "高橋", "伊藤", "渡辺", "中村", "小林", "加藤"]
    first_names = ["太郎", "花子", "一郎", "美咲", "健太", "陽子", "翔太", "明美", "大輔", "由美"]
    
    # 都道府県サンプル
    prefectures = ["東京都", "神奈川県", "大阪府", "愛知県", "福岡県", "北海道", "京都府", "兵庫県", "埼玉県", "千葉県"]
    
    # 銀行サンプル
    banks = [
        ("三菱UFJ銀行", "0005"),
        ("三井住友銀行", "0009"),
        ("みずほ銀行", "0001"),
        ("りそな銀行", "0010"),
        ("楽天銀行", "0036")
    ]
    
    for i in range(1, 51):  # 50件のテストデータ
        member_number = f"{i:07d}"  # 7桁の会員番号
        last_name = random.choice(last_names)
        first_name = random.choice(first_names)
        
        # ステータスをランダムに設定（8割アクティブ）
        if i <= 40:
            status = "アクティブ"
        elif i <= 45:
            status = "休会中"
        else:
            status = "退会済"
        
        # タイトルをランダムに設定
        titles = [Title.NONE, Title.START, Title.LEADER, Title.SUB_MANAGER, Title.MANAGER]
        title = random.choice(titles)
        
        # プランをランダムに設定（8割ヒーロープラン）
        plan = Plan.HERO if i <= 40 else Plan.TEST
        
        # 決済方法をランダムに設定
        payment_methods = [PaymentMethod.CARD, PaymentMethod.TRANSFER, PaymentMethod.BANK]
        payment_method = random.choice(payment_methods)
        
        # 銀行情報
        bank_name, bank_code = random.choice(banks)
        
        member = Member(
            member_number=member_number,
            name=f"{last_name} {first_name}",
            kana=f"{last_name} {first_name}",
            email=f"member{i:03d}@example.com",
            status=status,
            title=title,
            user_type=UserType.NORMAL,
            plan=plan,
            payment_method=payment_method,
            registration_date=datetime.now() - timedelta(days=random.randint(30, 365)),
            withdrawal_date=datetime.now() if status == "退会済" else None,
            phone=f"090-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            gender=random.choice([Gender.MALE, Gender.FEMALE]),
            postal_code=f"{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            prefecture=random.choice(prefectures),
            address2=f"{random.choice(['中央区', '港区', '新宿区', '渋谷区'])} {random.randint(1, 5)}-{random.randint(1, 20)}-{random.randint(1, 10)}",
            address3=f"マンション{random.randint(101, 999)}号室",
            upline_id=f"{max(1, i-1):07d}" if i > 1 else None,
            upline_name=f"{last_names[max(0, i-2) % 10]} {first_names[max(0, i-2) % 10]}" if i > 1 else None,
            referrer_id=f"{max(1, i-random.randint(1, 5)):07d}" if i > 5 else None,
            referrer_name=f"{last_names[max(0, i-6) % 10]} {first_names[max(0, i-6) % 10]}" if i > 5 else None,
            bank_name=bank_name,
            bank_code=bank_code,
            branch_name=f"{random.choice(['本店', '東京', '大阪', '名古屋'])}支店",
            branch_code=f"{random.randint(100, 999)}",
            account_number=f"{random.randint(1000000, 9999999)}",
            account_type=AccountType.ORDINARY,
            notes=f"テストデータ {i}"
        )
        members.append(member)
    
    return members

def seed_database():
    """データベースにテストデータを投入"""
    db = SessionLocal()
    
    try:
        # 既存データをクリア
        print("既存データをクリアしています...")
        db.query(Member).delete()
        db.commit()
        
        # テストデータ生成
        print("テストデータを生成しています...")
        members = generate_test_members()
        
        # データベースに投入
        print("データベースに投入しています...")
        db.add_all(members)
        db.commit()
        
        print(f"✅ {len(members)}件のテストデータを投入しました")
        
        # 統計情報表示
        active_count = db.query(Member).filter(Member.status == "アクティブ").count()
        inactive_count = db.query(Member).filter(Member.status == "休会中").count()
        withdrawn_count = db.query(Member).filter(Member.status == "退会済").count()
        
        print(f"\n📊 会員統計:")
        print(f"  - アクティブ: {active_count}件")
        print(f"  - 休会中: {inactive_count}件")
        print(f"  - 退会済み: {withdrawn_count}件")
        print(f"  - 合計: {active_count + inactive_count + withdrawn_count}件")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()