#!/usr/bin/env python3
# IROAS BOSS V2 - 認証システム専用初期化スクリプト
# Phase 21対応・MLMビジネス要件準拠

import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from enum import Enum

# 認証専用のベースクラスとエンジンを作成
Base = declarative_base()
DATABASE_URL = "sqlite:///./iroas_auth_test.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 認証専用モデル定義（シンプル版）
class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MLM_MANAGER = "mlm_manager"
    VIEWER = "viewer"

class UserStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"

class User(Base):
    """認証ユーザーモデル（認証テスト用シンプル版）"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    display_name = Column(String(50))
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(32))
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_at = Column(DateTime)
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class UserPermission(Base):
    """権限テーブル"""
    __tablename__ = "user_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    permission_name = Column(String(100), nullable=False)
    permission_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    resource = Column(String(50))
    action = Column(String(50))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class UserRolePermission(Base):
    """ロール権限関連テーブル"""
    __tablename__ = "user_role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("user_permissions.id"), nullable=False)
    is_granted = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # リレーション
    permission = relationship("UserPermission", backref="role_permissions")

# セキュリティマネージャー（簡易版）
class SimpleSecurityManager:
    def __init__(self):
        import hashlib
        self.hash_method = hashlib.sha256
    
    def hash_password(self, password: str) -> str:
        """シンプルなパスワードハッシュ化"""
        return self.hash_method(password.encode()).hexdigest()

security = SimpleSecurityManager()

async def initialize_auth_system():
    """認証システム初期化"""
    
    print("🔐 IROAS BOSS V2 - 認証システム初期化開始")
    
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    # データベースセッション
    db: Session = SessionLocal()
    
    try:
        # 既存データクリア
        db.query(UserRolePermission).delete()
        db.query(UserPermission).delete()
        db.query(User).delete()
        db.commit()
        
        print("⚙️  MLMビジネス権限システムを初期化中...")
        
        # MLMビジネス権限定義（抜粋版）
        permissions_data = [
            # システム管理権限
            ("システム管理", "system.admin", "システム全体の管理権限", "system"),
            ("ユーザー管理", "user.manage", "ユーザーアカウントの管理権限", "user"),
            ("ユーザー閲覧", "user.view", "ユーザー情報の閲覧権限", "user"),
            
            # 会員管理権限（MLM固有）
            ("会員管理", "member.manage", "会員情報の管理権限", "mlm"),
            ("会員閲覧", "member.view", "会員情報の閲覧権限", "mlm"),
            ("会員作成", "member.create", "新規会員の登録権限", "mlm"),
            
            # 組織管理権限（MLM固有）
            ("組織管理", "organization.manage", "組織構造の管理権限", "mlm"),
            ("組織閲覧", "organization.view", "組織構造の閲覧権限", "mlm"),
            
            # 決済管理権限（MLM固有）
            ("決済管理", "payment.manage", "決済データの管理権限", "mlm"),
            ("決済閲覧", "payment.view", "決済データの閲覧権限", "mlm"),
            ("決済CSV出力", "payment.csv_export", "決済CSV出力権限", "mlm"),
            
            # 報酬管理権限（MLM固有）
            ("報酬管理", "reward.manage", "報酬計算の管理権限", "mlm"),
            ("報酬閲覧", "reward.view", "報酬データの閲覧権限", "mlm"),
            ("報酬計算実行", "reward.calculate", "報酬計算実行権限", "mlm"),
            
            # 支払管理権限（MLM固有）
            ("支払管理", "payout.manage", "支払管理権限", "mlm"),
            ("支払閲覧", "payout.view", "支払データの閲覧権限", "mlm"),
            ("GMO CSV出力", "payout.gmo_export", "GMOネットバンク用CSV出力権限", "mlm"),
            
            # データ管理権限
            ("データ管理", "data.manage", "データ入出力管理権限", "mlm"),
            ("データ出力", "data.export", "データ出力権限", "mlm"),
            ("データ取込", "data.import", "データ取込権限", "mlm"),
        ]
        
        # 権限を作成
        permissions = []
        for perm_name, perm_code, description, category in permissions_data:
            permission = UserPermission(
                permission_name=perm_name,
                permission_code=perm_code,
                description=description,
                category=category,
                resource=perm_code.split('.')[0],
                action=perm_code.split('.')[1] if '.' in perm_code else 'all'
            )
            permissions.append(permission)
            db.add(permission)
        
        db.commit()
        
        # 権限IDマッピング作成
        permission_map = {perm.permission_code: perm.id for perm in permissions}
        
        # ロール別権限設定
        role_permission_mapping = {
            UserRole.SUPER_ADMIN: list(permission_map.keys()),  # 全権限
            UserRole.ADMIN: [k for k in permission_map.keys() if not k.startswith("system.")],  # システム管理以外
            UserRole.MLM_MANAGER: [
                "user.view", "member.manage", "member.view", "member.create",
                "organization.manage", "organization.view",
                "payment.manage", "payment.view", "payment.csv_export",
                "reward.manage", "reward.view", "reward.calculate",
                "payout.manage", "payout.view", "payout.gmo_export",
                "data.manage", "data.export", "data.import"
            ],
            UserRole.VIEWER: [
                "member.view", "organization.view", "payment.view", "reward.view", "payout.view"
            ]
        }
        
        # ロール権限を作成
        for role, permission_codes in role_permission_mapping.items():
            for permission_code in permission_codes:
                if permission_code in permission_map:
                    role_permission = UserRolePermission(
                        role=role,
                        permission_id=permission_map[permission_code],
                        is_granted=True
                    )
                    db.add(role_permission)
        
        db.commit()
        print("✅ MLMビジネス権限システムの初期化完了")
        
        # スーパーユーザー作成
        print("👤 スーパーユーザーを作成中...")
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
        
        # 統計表示
        print("\n📊 権限システム確認")
        total_permissions = len(permissions)
        print(f"✅ 登録済み権限数: {total_permissions}個")
        
        for role in UserRole:
            role_perms = db.query(UserRolePermission).filter(
                UserRolePermission.role == role
            ).count()
            print(f"   {role.value}: {role_perms}個の権限")
        
        print("\n🎉 認証システム初期化が正常に完了しました！")
        
    except Exception as e:
        print(f"❌ 初期化中にエラーが発生しました: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(initialize_auth_system())