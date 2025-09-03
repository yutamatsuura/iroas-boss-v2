#!/usr/bin/env python3
"""
Debug script to test direct ORM queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.organization import OrganizationPosition, Withdrawal
from app.models.member import Member

def main():
    print("🔍 Debug: Testing direct ORM queries...")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Test basic counts
        print("Testing counts:")
        org_count = session.query(OrganizationPosition).count()
        print(f"  OrganizationPosition count: {org_count}")
        
        withdrawal_count = session.query(Withdrawal).count()
        print(f"  Withdrawal count: {withdrawal_count}")
        
        member_count = session.query(Member).count()
        print(f"  Member count: {member_count}")
        
        # Test first few records
        print("\nTesting first 3 organization positions:")
        positions = session.query(OrganizationPosition).limit(3).all()
        for i, pos in enumerate(positions, 1):
            print(f"  {i}. ID: {pos.id}, Level: {pos.level}, Member ID: {pos.member_id}, Withdrawn ID: {pos.withdrawn_id}")
        
        # Test raw SQL
        print("\nTesting raw SQL:")
        result = session.execute("SELECT COUNT(*) FROM organization_positions").fetchone()
        print(f"  Raw SQL count: {result[0] if result else 'None'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    main()