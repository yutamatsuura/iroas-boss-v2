#!/usr/bin/env python3
"""
API機能チェックスクリプト
開発時に実行して機能が正常か確認する
"""

import requests
import sys
import json
from datetime import datetime

def check_server_running():
    """サーバーが起動しているかチェック"""
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_member_list_api():
    """会員一覧APIの基本機能チェック"""
    try:
        response = requests.get("http://localhost:8001/api/v1/members/")
        if response.status_code != 200:
            return False, f"Status code: {response.status_code}"
        
        data = response.json()
        
        # 基本構造チェック
        if "data" not in data or "total" not in data:
            return False, "Missing data or total field"
        
        if len(data["data"]) == 0:
            return False, "No members returned"
        
        # 必須フィールドチェック
        first_member = data["data"][0]
        required_fields = [
            "id", "member_number", "name", "email", "phone", "gender",
            "status", "title", "plan", "payment_method"
        ]
        
        for field in required_fields:
            if field not in first_member:
                return False, f"Missing field: {field}"
        
        return True, f"OK - {len(data['data'])} members, {data['total']} total"
        
    except Exception as e:
        return False, f"Exception: {str(e)}"

def check_member_search():
    """検索機能チェック"""
    tests = [
        ("会員番号検索", "http://localhost:8001/api/v1/members/?memberNumber=0000"),
        ("名前検索", "http://localhost:8001/api/v1/members/?name=白石"),
        ("メール検索", "http://localhost:8001/api/v1/members/?email=gmail"),
    ]
    
    results = []
    for test_name, url in tests:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                count = len(data["data"])
                results.append((test_name, True, f"{count} results"))
            else:
                results.append((test_name, False, f"Status: {response.status_code}"))
        except Exception as e:
            results.append((test_name, False, f"Error: {str(e)}"))
    
    return results

def check_member_detail():
    """会員詳細取得チェック"""
    tests = [
        ("ID取得", "http://localhost:8001/api/v1/members/2"),
        ("会員番号取得", "http://localhost:8001/api/v1/members/00000000000"),
    ]
    
    results = []
    for test_name, url in tests:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    results.append((test_name, False, data["error"]))
                else:
                    results.append((test_name, True, f"Member: {data.get('name', 'N/A')}"))
            else:
                results.append((test_name, False, f"Status: {response.status_code}"))
        except Exception as e:
            results.append((test_name, False, f"Error: {str(e)}"))
    
    return results

def main():
    """メイン処理"""
    print("🏥 IROAS BOSS API ヘルスチェック")
    print("=" * 50)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # サーバー起動チェック
    print("1. サーバー起動チェック")
    if check_server_running():
        print("   ✅ サーバーは正常に起動しています")
    else:
        print("   ❌ サーバーが起動していません")
        print("   → python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 で起動してください")
        sys.exit(1)
    
    print()
    
    # 会員一覧APIチェック
    print("2. 会員一覧API")
    success, message = check_member_list_api()
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
    
    print()
    
    # 検索機能チェック
    print("3. 検索機能")
    search_results = check_member_search()
    for test_name, success, message in search_results:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {message}")
    
    print()
    
    # 詳細取得チェック
    print("4. 会員詳細取得")
    detail_results = check_member_detail()
    for test_name, success, message in detail_results:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {message}")
    
    print()
    
    # 総合判定
    all_tests = [success for _, success, _ in search_results + detail_results]
    list_success, _ = check_member_list_api()
    all_tests.append(list_success)
    
    if all(all_tests):
        print("🎉 すべてのAPI機能が正常に動作しています！")
        return True
    else:
        print("⚠️  一部のAPI機能に問題があります。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)