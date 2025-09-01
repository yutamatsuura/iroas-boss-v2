#!/usr/bin/env python3
"""
手動登録テスト2人目 - 注意ユーザー・カード決済
"""

import urllib.request
import json

# 2人目: 注意ユーザーデータ（30項目完全版）
member_data_2 = {
    # 1-5: 基本情報
    "status": "ACTIVE",
    "member_number": "10000000022",
    "name": "中島直人", 
    "email": "nakajima.naoto@example.com",
    
    # 6-9: MLM情報
    "title": "KNIGHT_DAME",
    "user_type": "ATTENTION",  # 注意ユーザー
    "plan": "HERO", 
    "payment_method": "CARD",
    
    # 10-11: 日付情報
    "registration_date": "2020/11/08",
    "withdrawal_date": None,
    
    # 12-17: 連絡先情報
    "phone": "090-8888-2222",
    "gender": "MALE",
    "postal_code": "532-0011", 
    "prefecture": "大阪府",
    "address2": "淀川区西中島5-14-10",
    "address3": "新大阪第一生命ビル21F",
    
    # 18-21: 組織情報
    "upline_id": "10000000003",
    "upline_name": "田中一郎",
    "referrer_id": "10000000008",
    "referrer_name": "山本真理子",
    
    # 22-29: 銀行情報（りそな銀行）
    "bank_name": "りそな銀行",
    "bank_code": "0010",
    "branch_name": "梅田支店", 
    "branch_code": "004",
    "account_number": "9876543",
    "yucho_symbol": None,
    "yucho_number": None,
    "account_type": "CHECKING",  # 当座預金
    
    # 30: その他
    "notes": "注意ユーザー・カード決済・手動登録テスト2人目"
}

print("=== 手動登録テスト2人目（注意ユーザー） ===")
print(f"会員番号: {member_data_2['member_number']}")
print(f"氏名: {member_data_2['name']}")
print(f"ユーザータイプ: {member_data_2['user_type']}")
print(f"銀行: {member_data_2['bank_name']}")
print(f"決済方法: {member_data_2['payment_method']}")
print()

# API登録実行
url = "http://localhost:8000/api/v1/members/"
headers = {
    'Content-Type': 'application/json'
}

try:
    # JSON データを準備
    json_data = json.dumps(member_data_2).encode('utf-8')
    
    # リクエスト作成
    request = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
    
    # API呼び出し
    with urllib.request.urlopen(request) as response:
        response_data = json.loads(response.read())
    
    print("✅ 2人目の登録成功！")
    print(f"   内部ID: {response_data.get('id')}")
    print(f"   作成日時: {response_data.get('created_at')}")
    print()

except urllib.error.HTTPError as e:
    print(f"❌ HTTP エラー: {e.code}")
    error_data = e.read().decode('utf-8')
    print(f"エラー詳細: {error_data}")
except Exception as e:
    print(f"❌ 登録エラー: {e}")