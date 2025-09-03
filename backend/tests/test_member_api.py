"""
会員API統合テスト - 機能の後退を防ぐためのテストスイート
このテストが失敗する = API機能が壊れている
"""
import pytest
import requests
import json
from typing import Dict, List

# APIベースURL
BASE_URL = "http://localhost:8001/api/v1"

class TestMemberAPI:
    """会員API機能テスト"""
    
    def test_member_list_basic(self):
        """基本的な会員一覧取得テスト"""
        response = requests.get(f"{BASE_URL}/members/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        
        # 必須フィールドの存在確認
        first_member = data["data"][0]
        required_fields = [
            "id", "member_number", "memberNumber", "name", "email", 
            "status", "plan", "phone", "gender", "title", "user_type", "userType",
            "payment_method", "paymentMethod", "postal_code", "postalCode",
            "prefecture", "bank_name", "bankName", "notes"
        ]
        for field in required_fields:
            assert field in first_member, f"Required field '{field}' missing"
    
    def test_member_search_by_number(self):
        """会員番号検索テスト - この機能が壊れやすい"""
        # 部分一致検索
        response = requests.get(f"{BASE_URL}/members/?memberNumber=0000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0
        
        # 検索結果が条件に一致することを確認
        for member in data["data"]:
            assert "0000" in member["member_number"]
    
    def test_member_search_by_name(self):
        """名前検索テスト"""
        response = requests.get(f"{BASE_URL}/members/?name=白石")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        
        # 検索結果が条件に一致することを確認
        for member in data["data"]:
            assert "白石" in member["name"]
    
    def test_member_search_by_email(self):
        """メール検索テスト"""
        response = requests.get(f"{BASE_URL}/members/?email=gmail")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0
        
        # 検索結果が条件に一致することを確認
        for member in data["data"]:
            assert "gmail" in member["email"]
    
    def test_member_detail_by_id(self):
        """ID指定での会員詳細取得テスト"""
        response = requests.get(f"{BASE_URL}/members/2")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 2
        assert "name" in data
        assert "email" in data
    
    def test_member_detail_by_member_number(self):
        """会員番号指定での詳細取得テスト - 重要！この機能が編集画面に必要"""
        response = requests.get(f"{BASE_URL}/members/00000000000")
        assert response.status_code == 200
        data = response.json()
        assert data["member_number"] == "00000000000"
        assert data["name"] == "白石 達也"
        
        # 編集画面で必要な全フィールドの存在確認
        edit_required_fields = [
            "phone", "gender", "postal_code", "prefecture", "address2", "address3",
            "bank_name", "bank_code", "branch_name", "branch_code", "account_number",
            "yucho_symbol", "yucho_number", "account_type", "notes", "title",
            "user_type", "plan", "payment_method", "registration_date"
        ]
        for field in edit_required_fields:
            assert field in data, f"Edit screen field '{field}' missing"
    
    def test_search_parameters_acceptance(self):
        """検索パラメータが正しく受け取られることをテスト"""
        # 複数パラメータでの検索
        response = requests.get(f"{BASE_URL}/members/?memberNumber=000&name=白石&sortBy=name&sortOrder=desc")
        assert response.status_code == 200
        data = response.json()
        
        # パラメータが処理されていることを確認（結果が絞り込まれている）
        total_response = requests.get(f"{BASE_URL}/members/")
        total_data = total_response.json()
        assert len(data["data"]) <= len(total_data["data"])
    
    def test_api_response_structure(self):
        """APIレスポンス構造の一貫性テスト"""
        response = requests.get(f"{BASE_URL}/members/")
        assert response.status_code == 200
        data = response.json()
        
        # 必須レスポンスフィールド
        required_response_fields = [
            "data", "members", "total", "total_count", "totalCount",
            "active_count", "activeCount", "page", "perPage", "totalPages"
        ]
        for field in required_response_fields:
            assert field in data, f"Response field '{field}' missing"
        
        # フロントエンド互換性確認
        assert data["data"] == data["members"]
        assert data["total"] == data["total_count"] == data["totalCount"]

def run_api_tests():
    """APIテストを実行"""
    print("🧪 会員API統合テストを実行中...")
    
    try:
        # サーバーが起動しているか確認
        response = requests.get(f"{BASE_URL}/members/", timeout=5)
        if response.status_code != 200:
            print("❌ サーバーが起動していません")
            return False
    except requests.exceptions.RequestException:
        print("❌ サーバーに接続できません")
        return False
    
    # テストインスタンス作成
    test_instance = TestMemberAPI()
    
    # 各テストを実行
    tests = [
        ("基本的な会員一覧", test_instance.test_member_list_basic),
        ("会員番号検索", test_instance.test_member_search_by_number),
        ("名前検索", test_instance.test_member_search_by_name),
        ("メール検索", test_instance.test_member_search_by_email),
        ("ID詳細取得", test_instance.test_member_detail_by_id),
        ("会員番号詳細取得", test_instance.test_member_detail_by_member_number),
        ("検索パラメータ", test_instance.test_search_parameters_acceptance),
        ("レスポンス構造", test_instance.test_api_response_structure),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}: PASS")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAIL - {str(e)}")
            failed += 1
    
    print(f"\n📊 テスト結果: {passed} PASS, {failed} FAIL")
    
    if failed == 0:
        print("🎉 全てのテストが成功しました！")
        return True
    else:
        print("⚠️  失敗したテストがあります。API機能を確認してください。")
        return False

if __name__ == "__main__":
    import sys
    success = run_api_tests()
    sys.exit(0 if success else 1)