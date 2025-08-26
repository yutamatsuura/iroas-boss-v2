#!/usr/bin/env python3
# IROAS BOSS V2 - 権限初期化スクリプト
# Phase 21対応・MLMビジネス要件準拠

import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import Base, User, UserRole, UserStatus
from app.services.permission_service import permission_service
from app.core.security import security

async def init_permissions():
    """権限とスーパーユーザーの初期化"""
    
    # データベーステーブル作成
    Base.metadata.create_all(bind=engine)
    
    # データベースセッション取得
    db: Session = SessionLocal()
    
    try:
        print("🔐 IROAS BOSS V2 - 権限初期化開始")
        
        # 権限システム初期化
        print("⚙️  MLMビジネス権限システムを初期化中...")
        await permission_service.initialize_permissions(db)
        print("✅ MLMビジネス権限システムの初期化完了")
        
        # スーパーユーザー作成確認
        super_user = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        
        if not super_user:
            print("👤 スーパーユーザーを作成中...")
            
            # スーパーユーザー作成
            super_user = User(
                username="admin",
                email="admin@iroas-boss.com",
                hashed_password=security.hash_password("Admin@123!"),
                full_name="システム管理者",
                display_name="管理者",
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_verified=True,
                is_superuser=True
            )
            
            db.add(super_user)
            db.commit()
            
            print("✅ スーパーユーザー作成完了")
            print("   ユーザー名: admin")
            print("   パスワード: Admin@123!")
            print("   ⚠️  初回ログイン後にパスワードを変更してください")
        else:
            print("✅ スーパーユーザーは既に存在します")
        
        # 権限確認
        print("\n📊 権限システム確認中...")
        all_permissions = await permission_service.get_all_permissions(db)
        print(f"✅ 登録済み権限数: {len(all_permissions)}個")
        
        # ロール別権限確認
        for role in UserRole:
            role_perms = await permission_service.get_role_permissions(role, db)
            print(f"   {role.value}: {role_perms.total}個の権限")
        
        print("\n🎉 権限初期化が正常に完了しました！")
        
    except Exception as e:
        print(f"❌ 権限初期化中にエラーが発生しました: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(init_permissions())