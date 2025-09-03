"""
テスト会員データ削除スクリプト
00000000400以外の全てのテストデータを削除
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.member import Member

# データベース接続URL
DATABASE_URL = "postgresql://lennon:@localhost/iroas_boss_dev"

# データベースエンジンの作成
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def delete_test_members():
    """00000000400以外のテスト会員データを削除"""
    db = SessionLocal()
    
    try:
        # 削除対象のデータを確認
        members_to_delete = db.query(Member).filter(
            Member.member_number != '00000000400'
        ).all()
        
        print(f"削除対象: {len(members_to_delete)}件")
        
        # 各会員の情報を表示
        for member in members_to_delete:
            print(f"  - {member.member_number}: {member.name}")
        
        # 削除実行
        if members_to_delete:
            for member in members_to_delete:
                db.delete(member)
            
            db.commit()
            print(f"\n✅ {len(members_to_delete)}件のテストデータを削除しました")
        else:
            print("\n削除対象のデータはありません")
        
        # 残ったデータを確認
        remaining = db.query(Member).all()
        print(f"\n残存データ: {len(remaining)}件")
        for member in remaining:
            print(f"  - {member.member_number}: {member.name}")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("テスト会員データ削除処理を開始します...")
    print("00000000400以外のデータを削除します\n")
    delete_test_members()