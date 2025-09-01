"""
データベーステーブル作成スクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.database import Base
from app.models import Member, PaymentHistory, RewardCalculation, ActivityLog

def create_all_tables():
    """全テーブルを作成"""
    # データベースURL（環境変数から取得、なければデフォルト値）
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://lennon@localhost:5432/iroas_boss_dev"
    )
    
    print(f"データベース接続: {database_url}")
    
    try:
        # エンジン作成
        engine = create_engine(database_url)
        
        # 全テーブル作成
        Base.metadata.create_all(bind=engine)
        
        print("✅ 全テーブルの作成が完了しました")
        
        # 作成されたテーブル一覧を表示
        print("\n作成されたテーブル:")
        for table in Base.metadata.tables.keys():
            print(f"  - {table}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_all_tables()