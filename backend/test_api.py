"""
APIテストスクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Member, MemberStatus

# データベースURL
database_url = os.getenv(
    "DATABASE_URL", 
    "postgresql://lennon@localhost:5432/iroas_boss_dev"
)

# エンジンとセッション作成
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_query():
    """クエリテスト"""
    db = SessionLocal()
    
    try:
        # 総数取得
        total = db.query(Member).count()
        print(f"Total members: {total}")
        
        # is_deleted フィルタテスト
        query = db.query(Member).filter(Member.is_deleted == False)
        filtered_count = query.count()
        print(f"Non-deleted members: {filtered_count}")
        
        # 最初の5件を表示
        members = query.limit(5).all()
        for member in members:
            print(f"  - {member.member_number}: {member.name} ({member.status})")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_query()