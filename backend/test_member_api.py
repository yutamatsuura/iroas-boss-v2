#!/usr/bin/env python3
"""
会員管理API完全性テスト
これを実行して全てPASSしない限り、本番環境にデプロイしない
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"
TEST_MEMBER_NUMBER = "00000000000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_result(test_name, passed, details=""):
    """テスト結果を表示"""
    if passed:
        print(f"{Colors.GREEN}✓{Colors.END} {test_name}")
    else:
        print(f"{Colors.RED}✗{Colors.END} {test_name}")
        if details:
            print(f"  {Colors.YELLOW}→ {details}{Colors.END}")
    return passed

def test_member_list():
    """会員一覧取得テスト"""
    print(f"\n{Colors.BLUE}【会員一覧取得テスト】{Colors.END}")
    
    tests_passed = []
    
    # 基本的な取得
    try:
        response = requests.get(f"{BASE_URL}/members/")
        tests_passed.append(test_result(
            "GET /members/ - 基本取得",
            response.status_code == 200,
            f"Status: {response.status_code}"
        ))
        
        data = response.json()
        tests_passed.append(test_result(
            "必須フィールド存在確認",
            all(field in data for field in ['data', 'total', 'totalCount', 'page', 'perPage']),
            f"Fields: {list(data.keys())}"
        ))
        
        if 'data' in data and len(data['data']) > 0:
            member = data['data'][0]
            required_fields = [
                'id', 'member_number', 'memberNumber', 'name', 'email',
                'phone', 'gender', 'status', 'title', 'plan',
                'uplineId', 'uplineName', 'referrerId', 'referrerName'
            ]
            tests_passed.append(test_result(
                "会員データフィールド完全性",
                all(field in member for field in required_fields),
                f"Missing: {[f for f in required_fields if f not in member]}"
            ))
    except Exception as e:
        tests_passed.append(test_result("会員一覧API", False, str(e)))
    
    # ページネーション
    try:
        response = requests.get(f"{BASE_URL}/members/?page=2&perPage=10")
        tests_passed.append(test_result(
            "ページネーション機能",
            response.status_code == 200 and response.json().get('page') == 2,
            f"Page: {response.json().get('page', 'N/A')}"
        ))
    except Exception as e:
        tests_passed.append(test_result("ページネーション", False, str(e)))
    
    # 検索機能
    search_tests = [
        ("memberNumber", "0000", "会員番号検索"),
        ("name", "白石", "名前検索"),
        ("email", "gmail", "メール検索")
    ]
    
    for param, value, test_name in search_tests:
        try:
            response = requests.get(f"{BASE_URL}/members/?{param}={value}")
            data = response.json()
            tests_passed.append(test_result(
                test_name,
                response.status_code == 200 and len(data.get('data', [])) >= 0,
                f"Results: {len(data.get('data', []))}"
            ))
        except Exception as e:
            tests_passed.append(test_result(test_name, False, str(e)))
    
    return all(tests_passed)

def test_member_detail():
    """会員詳細取得テスト"""
    print(f"\n{Colors.BLUE}【会員詳細取得テスト】{Colors.END}")
    
    tests_passed = []
    
    # ID指定
    try:
        response = requests.get(f"{BASE_URL}/members/2")
        tests_passed.append(test_result(
            "GET /members/{{id}} - ID指定取得",
            response.status_code == 200 and 'error' not in response.json(),
            f"Status: {response.status_code}"
        ))
    except Exception as e:
        tests_passed.append(test_result("ID指定取得", False, str(e)))
    
    # 会員番号指定（重要！編集画面で使用）
    try:
        response = requests.get(f"{BASE_URL}/members/{TEST_MEMBER_NUMBER}")
        data = response.json()
        tests_passed.append(test_result(
            "GET /members/{{member_number}} - 会員番号指定取得",
            response.status_code == 200 and 'error' not in data,
            f"Status: {response.status_code}"
        ))
        
        # 編集画面必須フィールド
        edit_fields = [
            'phone', 'gender', 'postal_code', 'prefecture',
            'bank_name', 'bank_code', 'branch_name', 'branch_code',
            'upline_id', 'upline_name', 'uplineId', 'uplineName'
        ]
        tests_passed.append(test_result(
            "編集画面必須フィールド存在確認",
            all(field in data for field in edit_fields),
            f"Missing: {[f for f in edit_fields if f not in data]}"
        ))
    except Exception as e:
        tests_passed.append(test_result("会員番号指定取得", False, str(e)))
    
    return all(tests_passed)

def test_member_update():
    """会員更新テスト"""
    print(f"\n{Colors.BLUE}【会員更新テスト】{Colors.END}")
    
    tests_passed = []
    
    # 直上者フィールド更新（最も問題が多かった）
    test_data = {
        "uplineId": "TEST_UPDATE_" + datetime.now().strftime("%H%M%S"),
        "uplineName": "テスト直上者_" + datetime.now().strftime("%H%M%S")
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/members/{TEST_MEMBER_NUMBER}",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        tests_passed.append(test_result(
            "PUT /members/{{member_number}} - 更新エンドポイント",
            response.status_code == 200,
            f"Status: {response.status_code}"
        ))
        
        # 更新確認
        response = requests.get(f"{BASE_URL}/members/{TEST_MEMBER_NUMBER}")
        data = response.json()
        tests_passed.append(test_result(
            "直上者フィールド更新確認",
            data.get('uplineId') == test_data['uplineId'] and 
            data.get('uplineName') == test_data['uplineName'],
            f"uplineId: {data.get('uplineId')}, uplineName: {data.get('uplineName')}"
        ))
    except Exception as e:
        tests_passed.append(test_result("会員更新", False, str(e)))
    
    return all(tests_passed)

def test_status_counts():
    """ステータス別集計テスト"""
    print(f"\n{Colors.BLUE}【ステータス別集計テスト】{Colors.END}")
    
    tests_passed = []
    
    try:
        response = requests.get(f"{BASE_URL}/members/")
        data = response.json()
        
        # 集計フィールド存在確認
        count_fields = [
            'total', 'totalCount',
            'active_count', 'activeCount',
            'inactive_count', 'inactiveCount',
            'withdrawn_count', 'withdrawnCount'
        ]
        tests_passed.append(test_result(
            "ステータス集計フィールド存在確認",
            all(field in data for field in count_fields),
            f"Missing: {[f for f in count_fields if f not in data]}"
        ))
        
        # 集計の一貫性
        tests_passed.append(test_result(
            "集計値の一貫性",
            data.get('total') == data.get('totalCount') and
            data.get('active_count') == data.get('activeCount'),
            f"total: {data.get('total')}, active: {data.get('active_count')}"
        ))
    except Exception as e:
        tests_passed.append(test_result("ステータス集計", False, str(e)))
    
    return all(tests_passed)

def main():
    """メインテスト実行"""
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}   会員管理API完全性テスト - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # サーバー起動確認
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=3)
        if response.status_code != 200:
            print(f"{Colors.RED}❌ サーバーが起動していません{Colors.END}")
            return False
    except:
        print(f"{Colors.RED}❌ サーバーに接続できません（port 8001）{Colors.END}")
        return False
    
    print(f"{Colors.GREEN}✓ サーバー接続確認OK{Colors.END}")
    
    # 各テスト実行
    all_passed = True
    all_passed &= test_member_list()
    all_passed &= test_member_detail()
    all_passed &= test_member_update()
    all_passed &= test_status_counts()
    
    # 結果サマリー
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    if all_passed:
        print(f"{Colors.GREEN}🎉 全テスト合格！本番環境へのデプロイ可能です{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}⚠️  テスト失敗 - 修正が必要です{Colors.END}")
        print(f"{Colors.YELLOW}上記の失敗項目を修正してから再度テストを実行してください{Colors.END}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)