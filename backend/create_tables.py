#!/usr/bin/env python3
"""
テーブル作成スクリプト
新しい組織図テーブルを作成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models.member import Member
from app.models.organization import OrganizationPosition, Withdrawal, OrganizationSales, OrganizationStats

def main():
    print("Creating database tables...")
    try:
        # テーブル作成
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # 作成されたテーブルを確認
        import sqlite3
        conn = sqlite3.connect('iroas_boss_v2.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n📋 Current tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()