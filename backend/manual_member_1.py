#!/usr/bin/env python3
"""
手動登録テスト1人目 - 通常銀行利用者
"""

import urllib.request
import json

# 1人目: 通常銀行利用者データ（30項目完全版）
member_data_1 = {
    # 1-5: 基本情報
    "status": "ACTIVE",
    "member_number": "10000000021",
    "name": "新井美津子", 
    "email": "arai.mitsuko@example.com",
    
    # 6-9: MLM情報
    "title": "KING_QUEEN",
    "user_type": "NORMAL",
    "plan": "HERO", 
    "payment_method": "BANK",
    
    # 10-11: 日付情報
    "registration_date": "2018-07-12",
    "withdrawal_date": None,
    
    # 12-17: 連絡先情報
    "phone": "03-5555-1234",
    "gender": "FEMALE",
    "postal_code": "150-0001", 
    "prefecture": "東京都",
    "address2": "渋谷区神宮前1-2-3",
    "address3": "表参道ヒルズ801",
    
    # 18-21: 組織情報
    "upline_id": "10000000001",
    "upline_name": "山田太郎",
    "referrer_id": "10000000002",
    "referrer_name": "佐藤花子",
    
    # 22-29: 銀行情報（通常銀行）
    "bank_name": "三菱UFJ銀行",
    "bank_code": "0005",
    "branch_name": "新宿支店", 
    "branch_code": "661",
    "account_number": "1234567",
    "yucho_symbol": None,
    "yucho_number": None,
    "account_type": "ORDINARY",
    
    # 30: その他
    "notes": "通常銀行利用・手動登録テスト1人目"
}

print("=== 手動登録テスト1人目（通常銀行） ===")
print(f"会員番号: {member_data_1['member_number']}")
print(f"氏名: {member_data_1['name']}")
print(f"銀行: {member_data_1['bank_name']}")
print(f"支店: {member_data_1['branch_name']}")
print(f"口座番号: {member_data_1['account_number']}")
print()

# API登録実行
url = "http://localhost:8000/api/v1/members/"
headers = {
    'Content-Type': 'application/json'
}

try:
    # JSON データを準備
    json_data = json.dumps(member_data_1).encode('utf-8')
    
    # リクエスト作成
    request = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
    
    # API呼び出し
    with urllib.request.urlopen(request) as response:
        response_data = json.loads(response.read())
    
    print("✅ 1人目の登録成功！")
    print(f"   内部ID: {response_data.get('id')}")
    print(f"   作成日時: {response_data.get('created_at')}")
    print()

except urllib.error.HTTPError as e:
    print(f"❌ HTTP エラー: {e.code}")
    error_data = e.read().decode('utf-8')
    print(f"エラー詳細: {error_data}")
except Exception as e:
    print(f"❌ 登録エラー: {e}")