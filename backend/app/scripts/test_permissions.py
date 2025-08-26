#!/usr/bin/env python3
# IROAS BOSS V2 - 権限テストスクリプト
# Phase 21対応・MLMビジネス要件準拠

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.services.permission_service import permission_service
from app.core.security import security

class PermissionTester:
    """権限システムテスト"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.test_users = {}
    
    async def setup_test_users(self):
        """テスト用ユーザー作成"""
        
        print("👥 テスト用ユーザーを作成中...")
        
        # テストユーザー定義
        test_user_data = [
            {
                "username": "test_admin",
                "email": "admin@test.com",
                "role": UserRole.ADMIN,
                "name": "管理者テスト"
            },
            {
                "username": "test_mlm_manager",
                "email": "mlm@test.com", 
                "role": UserRole.MLM_MANAGER,
                "name": "MLM管理者テスト"
            },
            {
                "username": "test_viewer",
                "email": "viewer@test.com",
                "role": UserRole.VIEWER, 
                "name": "閲覧者テスト"
            }
        ]
        
        for user_data in test_user_data:
            # 既存ユーザーチェック
            existing_user = self.db.query(User).filter(
                User.username == user_data["username"]
            ).first()
            
            if not existing_user:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=security.hash_password("Test@123!"),
                    full_name=user_data["name"],
                    display_name=user_data["name"],
                    role=user_data["role"],
                    status=UserStatus.ACTIVE,
                    is_active=True,
                    is_verified=True
                )
                
                self.db.add(user)
                self.db.commit()
                self.test_users[user_data["role"]] = user.id
                print(f"   ✅ {user_data['name']} 作成完了")
            else:
                self.test_users[user_data["role"]] = existing_user.id
                print(f"   ⏭️  {user_data['name']} 既存")
    
    async def test_role_permissions(self):
        """ロール別権限テスト"""
        
        print("\n🔒 ロール別権限テスト開始")
        
        # テスト権限項目
        test_permissions = [
            # システム権限
            ("system.admin", "システム管理"),
            ("user.manage", "ユーザー管理"),
            ("user.view", "ユーザー閲覧"),
            
            # MLM会員管理
            ("member.manage", "会員管理"),
            ("member.view", "会員閲覧"),
            ("member.create", "会員作成"),
            
            # MLM組織管理
            ("organization.manage", "組織管理"),
            ("organization.view", "組織閲覧"),
            
            # MLM決済管理
            ("payment.manage", "決済管理"),
            ("payment.view", "決済閲覧"),
            ("payment.csv_export", "決済CSV出力"),
            
            # MLM報酬管理
            ("reward.manage", "報酬管理"),
            ("reward.calculate", "報酬計算"),
            
            # MLM支払管理
            ("payout.manage", "支払管理"),
            ("payout.gmo_export", "GMO CSV出力")
        ]
        
        for role, user_id in self.test_users.items():
            print(f"\n📋 {role.value} 権限テスト")
            
            permissions_granted = []
            permissions_denied = []
            
            for permission_code, permission_name in test_permissions:
                has_permission = await permission_service.check_user_permission(
                    user_id, permission_code, self.db
                )
                
                if has_permission:
                    permissions_granted.append(permission_name)
                else:
                    permissions_denied.append(permission_name)
            
            print(f"   ✅ 許可された権限 ({len(permissions_granted)}個):")
            for perm in permissions_granted:
                print(f"      - {perm}")
            
            print(f"   ❌ 拒否された権限 ({len(permissions_denied)}個):")
            for perm in permissions_denied[:5]:  # 最初の5個のみ表示
                print(f"      - {perm}")
            if len(permissions_denied) > 5:
                print(f"      ... 他{len(permissions_denied)-5}個")
    
    async def test_resource_access(self):
        """リソースアクセステスト"""
        
        print("\n🗂️  リソースアクセステスト開始")
        
        # テストリソース・アクション
        test_resources = [
            ("member", "manage", "会員管理"),
            ("member", "view", "会員閲覧"),
            ("organization", "manage", "組織管理"),
            ("payment", "manage", "決済管理"),
            ("reward", "calculate", "報酬計算"),
            ("payout", "gmo_export", "GMO CSV出力")
        ]
        
        for role, user_id in self.test_users.items():
            print(f"\n📁 {role.value} リソースアクセステスト")
            
            for resource, action, description in test_resources:
                has_access = await permission_service.check_user_resource_access(
                    user_id, resource, action, self.db
                )
                
                status = "✅ 許可" if has_access else "❌ 拒否"
                print(f"   {status} {description} ({resource}.{action})")
    
    async def test_accessible_resources(self):
        """アクセス可能リソース一覧テスト"""
        
        print("\n📊 アクセス可能リソース一覧テスト")
        
        for role, user_id in self.test_users.items():
            print(f"\n🔑 {role.value} アクセス可能リソース:")
            
            resources = await permission_service.get_user_accessible_resources(
                user_id, self.db
            )
            
            for resource, actions in resources.items():
                print(f"   📂 {resource}:")
                for action in actions:
                    print(f"      - {action}")
    
    async def test_mlm_specific_permissions(self):
        """MLM固有権限テスト"""
        
        print("\n🏢 MLMビジネス固有権限テスト")
        
        mlm_tests = [
            ("can_manage_members", "会員管理"),
            ("can_view_members", "会員閲覧"),
            ("can_manage_organization", "組織管理"),
            ("can_calculate_rewards", "報酬計算"),
            ("can_export_payments", "決済CSV出力"),
            ("can_export_gmo", "GMO CSV出力")
        ]
        
        for role, user_id in self.test_users.items():
            print(f"\n💼 {role.value} MLM権限テスト:")
            
            for method_name, description in mlm_tests:
                method = getattr(permission_service, method_name)
                has_permission = await method(user_id, self.db)
                
                status = "✅ 許可" if has_permission else "❌ 拒否"
                print(f"   {status} {description}")
    
    async def run_all_tests(self):
        """全テスト実行"""
        
        try:
            print("🧪 IROAS BOSS V2 - 権限システムテスト開始")
            print("=" * 60)
            
            await self.setup_test_users()
            await self.test_role_permissions()
            await self.test_resource_access()
            await self.test_accessible_resources()
            await self.test_mlm_specific_permissions()
            
            print("\n" + "=" * 60)
            print("🎉 権限システムテスト完了！")
            
        except Exception as e:
            print(f"❌ テスト実行中にエラーが発生しました: {str(e)}")
            raise
        
        finally:
            self.db.close()

async def main():
    """メイン関数"""
    tester = PermissionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())