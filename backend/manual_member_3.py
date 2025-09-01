#!/usr/bin/env python3
"""
手動登録テスト3人目 - テストプラン・インフォカート決済・その他性別
"""

import urllib.request
import json

# 3人目: 多様性テストデータ（30項目完全版）
member_data_3 = {
    # 1-5: 基本情報
    "status": "ACTIVE",
    "member_number": "10000000023",
    "name": "橋本ゆいか", 
    "email": "hashimoto.yuika@example.com",
    
    # 6-9: MLM情報
    "title": "EMPEROR_EMPRESS",  # 最高称号
    "user_type": "NORMAL",
    "plan": "TEST",  # テストプラン
    "payment_method": "INFOCART",  # インフォカート決済
    
    # 10-11: 日付情報
    "registration_date": "2016年3月25日",  # 日本語形式
    "withdrawal_date": None,
    
    # 12-17: 連絡先情報
    "phone": "052-777-9999",
    "gender": "OTHER",  # その他性別
    "postal_code": "460-0008", 
    "prefecture": "愛知県",
    "address2": "名古屋市中区栄3-4-5",
    "address3": "サンシャイン栄12階",
    
    # 18-21: 組織情報
    "upline_id": "10000000001",
    "upline_name": "山田太郎",
    "referrer_id": "10000000021",
    "referrer_name": "新井美津子",
    
    # 22-29: 銀行情報（地方銀行）
    "bank_name": "愛知銀行",
    "bank_code": "0542",
    "branch_name": "栄町支店", 
    "branch_code": "007",
    "account_number": "5555777",
    "yucho_symbol": None,
    "yucho_number": None,
    "account_type": "ORDINARY",
    
    # 30: その他
    "notes": "テストプラン・インフォカート・その他性別・手動登録テスト3人目"
}

print("=== 手動登録テスト3人目（多様性テスト） ===")
print(f"会員番号: {member_data_3['member_number']}")
print(f"氏名: {member_data_3['name']}")
print(f"称号: {member_data_3['title']}")
print(f"プラン: {member_data_3['plan']}")
print(f"性別: {member_data_3['gender']}")
print(f"決済方法: {member_data_3['payment_method']}")
print(f"登録日: {member_data_3['registration_date']}")
print()

# API登録実行
url = "http://localhost:8000/api/v1/members/"
headers = {
    'Content-Type': 'application/json'
}

try:
    # JSON データを準備
    json_data = json.dumps(member_data_3).encode('utf-8')
    
    # リクエスト作成
    request = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
    
    # API呼び出し
    with urllib.request.urlopen(request) as response:
        response_data = json.loads(response.read())
    
    print("✅ 3人目の登録成功！")
    print(f"   内部ID: {response_data.get('id')}")
    print(f"   作成日時: {response_data.get('created_at')}")
    print()

except urllib.error.HTTPError as e:
    print(f"❌ HTTP エラー: {e.code}")
    error_data = e.read().decode('utf-8')
    print(f"エラー詳細: {error_data}")
except Exception as e:
    print(f"❌ 登録エラー: {e}")