#!/usr/bin/env python3
# IROAS BOSS V2 - 認証API テストスクリプト
# Phase 21対応・MLMビジネス要件準拠

import asyncio
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# FastAPIのテスト環境をセットアップ
os.environ["DATABASE_URL"] = "sqlite:///./iroas_auth_test.db"

from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.api.endpoints.auth import router
from app.database import get_db

# FastAPIアプリケーション作成
app = FastAPI(title="IROAS BOSS V2 Auth Test")
app.include_router(router)

# テストクライアント作成
client = TestClient(app)

class AuthAPITester:
    """認証API統合テスト"""
    
    def __init__(self):
        self.client = client
        self.tokens = {}
        self.test_users = {}
        self.base_url = ""
    
    def test_user_registration(self):
        """ユーザー登録テスト"""
        print("👤 ユーザー登録テスト")
        
        # 管理者でログイン（事前作成済み）
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@123!",
            "remember_me": False
        })
        
        if login_response.status_code != 200:
            print(f"❌ 管理者ログインに失敗: {login_response.status_code}")
            print(f"   レスポンス: {login_response.text}")
            return False
        
        admin_token = login_response.json()["access_token"]
        self.tokens["admin"] = admin_token
        
        # テストユーザー作成
        test_users_data = [
            {
                "username": "test_mlm_manager",
                "email": "mlm@test.com",
                "password": "Test@123!",
                "confirm_password": "Test@123!",
                "full_name": "MLM管理者テスト",
                "role": "mlm_manager"
            },
            {
                "username": "test_viewer", 
                "email": "viewer@test.com",
                "password": "Test@123!",
                "confirm_password": "Test@123!",
                "full_name": "閲覧者テスト",
                "role": "viewer"
            }
        ]
        
        for user_data in test_users_data:
            response = self.client.post(
                "/api/v1/auth/users",
                json=user_data,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code == 200:
                print(f"   ✅ {user_data['username']} 作成成功")
                self.test_users[user_data["role"]] = user_data["username"]
            else:
                print(f"   ❌ {user_data['username']} 作成失敗: {response.status_code}")
                print(f"      レスポンス: {response.text}")
        
        return True
    
    def test_authentication_flow(self):
        """認証フローテスト"""
        print("\n🔐 認証フローテスト")
        
        # 正常ログイン
        login_data = {
            "username": "admin",
            "password": "Admin@123!",
            "remember_me": True
        }
        
        response = self.client.post("/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ ログイン成功")
            print(f"      トークンタイプ: {data['token_type']}")
            print(f"      有効期限: {data['expires_in']}秒")
            print(f"      ユーザー: {data['user']['username']}")
            print(f"      権限数: {len(data['permissions'])}個")
            
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]
            
            # トークンリフレッシュテスト
            refresh_response = self.client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            if refresh_response.status_code == 200:
                print("   ✅ トークンリフレッシュ成功")
            else:
                print(f"   ❌ トークンリフレッシュ失敗: {refresh_response.status_code}")
            
            # ログアウトテスト
            logout_response = self.client.post(
                "/api/v1/auth/logout",
                json={"all_devices": False},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if logout_response.status_code == 200:
                print("   ✅ ログアウト成功")
            else:
                print(f"   ❌ ログアウト失敗: {logout_response.status_code}")
        
        else:
            print(f"   ❌ ログイン失敗: {response.status_code}")
            print(f"      レスポンス: {response.text}")
            return False
        
        # 不正ログインテスト
        invalid_login = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "WrongPassword",
            "remember_me": False
        })
        
        if invalid_login.status_code == 401:
            print("   ✅ 不正ログイン拒否確認")
        else:
            print(f"   ❌ 不正ログイン処理異常: {invalid_login.status_code}")
        
        return True
    
    def test_permission_based_access(self):
        """権限ベースアクセステスト"""
        print("\n🔒 権限ベースアクセステスト")
        
        # 各ロールでログインしてアクセステスト
        test_accounts = [
            {"username": "admin", "password": "Admin@123!", "role": "super_admin"},
            {"username": "test_mlm_manager", "password": "Test@123!", "role": "mlm_manager"},
            {"username": "test_viewer", "password": "Test@123!", "role": "viewer"}
        ]
        
        for account in test_accounts:
            print(f"\n   📋 {account['role']} 権限テスト")
            
            # ログイン
            login_response = self.client.post("/api/v1/auth/login", json={
                "username": account["username"],
                "password": account["password"],
                "remember_me": False
            })
            
            if login_response.status_code != 200:
                print(f"      ❌ ログイン失敗: {login_response.status_code}")
                continue
            
            token = login_response.json()["access_token"]
            permissions = login_response.json()["permissions"]
            
            print(f"      ✅ ログイン成功 (権限数: {len(permissions)}個)")
            
            # 現在のユーザー情報取得
            me_response = self.client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"      ✅ ユーザー情報取得成功: {user_info['username']}")
            else:
                print(f"      ❌ ユーザー情報取得失敗: {me_response.status_code}")
            
            # セッション一覧取得
            sessions_response = self.client.get(
                "/api/v1/auth/sessions", 
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if sessions_response.status_code == 200:
                sessions = sessions_response.json()
                print(f"      ✅ セッション一覧取得成功 (セッション数: {sessions['total']}個)")
            else:
                print(f"      ❌ セッション一覧取得失敗: {sessions_response.status_code}")
            
            # 管理者専用機能テスト（ユーザー一覧）
            if account["role"] in ["super_admin", "admin"]:
                # 権限初期化（管理者のみ）
                if account["role"] == "super_admin":
                    init_response = self.client.post(
                        "/api/v1/auth/permissions/initialize",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    if init_response.status_code == 200:
                        print("      ✅ 権限初期化成功")
                    else:
                        print(f"      ❌ 権限初期化失敗: {init_response.status_code}")
            
            else:
                # 非管理者による管理機能アクセステスト（拒否されるべき）
                unauthorized_response = self.client.post(
                    "/api/v1/auth/permissions/initialize",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if unauthorized_response.status_code == 403:
                    print("      ✅ 権限制限確認 (権限初期化拒否)")
                else:
                    print(f"      ❌ 権限制限異常: {unauthorized_response.status_code}")
    
    def test_password_management(self):
        """パスワード管理テスト"""
        print("\n🔑 パスワード管理テスト")
        
        # 管理者でログイン
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@123!",
            "remember_me": False
        })
        
        if login_response.status_code != 200:
            print("   ❌ ログインに失敗")
            return False
        
        token = login_response.json()["access_token"]
        
        # パスワード変更テスト
        change_password_data = {
            "current_password": "Admin@123!",
            "new_password": "NewAdmin@456!",
            "confirm_password": "NewAdmin@456!"
        }
        
        change_response = self.client.post(
            "/api/v1/auth/change-password",
            json=change_password_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if change_response.status_code == 200:
            print("   ✅ パスワード変更成功")
            
            # 新しいパスワードでログインテスト
            new_login_response = self.client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "NewAdmin@456!",
                "remember_me": False
            })
            
            if new_login_response.status_code == 200:
                print("   ✅ 新パスワードでログイン成功")
                
                # パスワードを元に戻す
                token = new_login_response.json()["access_token"]
                self.client.post(
                    "/api/v1/auth/change-password",
                    json={
                        "current_password": "NewAdmin@456!",
                        "new_password": "Admin@123!",
                        "confirm_password": "Admin@123!"
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
                print("   ✅ パスワードを元に戻しました")
            else:
                print("   ❌ 新パスワードでのログインに失敗")
        else:
            print(f"   ❌ パスワード変更失敗: {change_response.status_code}")
            print(f"      レスポンス: {change_response.text}")
    
    def test_access_logs(self):
        """アクセスログテスト"""
        print("\n📊 アクセスログテスト")
        
        # 管理者でログイン
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@123!",
            "remember_me": False
        })
        
        if login_response.status_code != 200:
            print("   ❌ ログインに失敗")
            return False
        
        token = login_response.json()["access_token"]
        
        # アクセスログ取得テスト
        logs_response = self.client.get(
            "/api/v1/auth/logs/access?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            print(f"   ✅ アクセスログ取得成功 (ログ数: {logs_data['total']}個)")
        else:
            print(f"   ❌ アクセスログ取得失敗: {logs_response.status_code}")
    
    def run_all_tests(self):
        """全テスト実行"""
        print("🧪 IROAS BOSS V2 - 認証API統合テスト開始")
        print("=" * 60)
        
        try:
            # テスト実行
            self.test_user_registration()
            self.test_authentication_flow()
            self.test_permission_based_access() 
            self.test_password_management()
            self.test_access_logs()
            
            print("\n" + "=" * 60)
            print("🎉 認証API統合テスト完了！")
            
        except Exception as e:
            print(f"❌ テスト実行中にエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # 既存のデータベースを使用
    if not os.path.exists("iroas_auth_test.db"):
        print("❌ テストデータベースが存在しません。先に init_auth_only.py を実行してください。")
        sys.exit(1)
    
    tester = AuthAPITester()
    tester.run_all_tests()