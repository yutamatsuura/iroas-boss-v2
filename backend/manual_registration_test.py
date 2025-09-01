#!/usr/bin/env python3
"""
手動会員登録APIテスト
30項目すべてを含む完全な新規会員データを登録
"""

import urllib.request
import json

# 新規会員データ（30項目完全版）
new_member_data = {
    # 1-5: 基本情報
    "status": "ACTIVE",
    "member_number": "10000000016",  # 新しい会員番号
    "name": "テスト太郎",
    "email": "test.taro@example.com",
    
    # 6-9: MLM情報
    "title": "KNIGHT_DAME",
    "user_type": "NORMAL", 
    "plan": "HERO",
    "payment_method": "CARD",
    
    # 10-11: 日付情報
    "registration_date": "2024-01-15",
    "withdrawal_date": None,
    
    # 12-17: 連絡先情報
    "phone": "090-1111-2222",
    "gender": "MALE",
    "postal_code": "105-0011",
    "prefecture": "東京都",
    "address2": "港区芝公園1-2-3",
    "address3": "東京タワービル901",
    
    # 18-21: 組織情報
    "upline_id": "10000000001",
    "upline_name": "山田太郎",
    "referrer_id": "10000000002", 
    "referrer_name": "佐藤花子",
    
    # 22-29: 銀行情報
    "bank_name": "住信SBIネット銀行",
    "bank_code": "0038",
    "branch_name": "法人第一支店",
    "branch_code": "106", 
    "account_number": "1122334",
    "yucho_symbol": None,
    "yucho_number": None,
    "account_type": "ORDINARY",
    
    # 30: その他
    "notes": "手動登録テスト用会員・全項目入力済み"
}

print("=== 手動会員登録APIテスト ===")
print(f"会員番号: {new_member_data['member_number']}")
print(f"氏名: {new_member_data['name']}")
print()

# API登録実行
url = "http://localhost:8000/api/v1/members/"
headers = {
    'Content-Type': 'application/json'
}

try:
    # JSON データを準備
    json_data = json.dumps(new_member_data).encode('utf-8')
    
    # リクエスト作成
    request = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
    
    # API呼び出し
    with urllib.request.urlopen(request) as response:
        response_data = json.loads(response.read())
    
    print("✅ 新規会員登録成功！")
    print(f"   内部ID: {response_data.get('id')}")
    print(f"   作成日時: {response_data.get('created_at')}")
    print()
    
    # 登録された会員の詳細確認
    member_url = f"http://localhost:8000/api/v1/members/{new_member_data['member_number']}"
    with urllib.request.urlopen(member_url) as response:
        member_detail = json.loads(response.read())
    
    print("📋 登録された会員詳細（30項目確認）:")
    fields = [
        'status', 'member_number', 'name', 'email',
        'title', 'user_type', 'plan', 'payment_method', 
        'registration_date', 'withdrawal_date',
        'phone', 'gender', 'postal_code', 'prefecture', 'address2', 'address3',
        'upline_id', 'upline_name', 'referrer_id', 'referrer_name',
        'bank_name', 'bank_code', 'branch_name', 'branch_code', 
        'account_number', 'yucho_symbol', 'yucho_number', 'account_type',
        'notes'
    ]
    
    populated = 0
    for i, field in enumerate(fields, 1):
        value = member_detail.get(field)
        status = "✓" if value else "✗"
        print(f"{i:2}. {status} {field:20} = {value if value else '(empty)'}")
        if value:
            populated += 1
    
    print()
    print(f"📊 結果: {populated}/{len(fields)} 項目が入力されています")
    
    # 統計更新確認
    stats_url = "http://localhost:8000/api/v1/members/"
    with urllib.request.urlopen(stats_url) as response:
        stats = json.loads(response.read())
    
    print()
    print("📈 登録後の統計:")
    print(f"   総会員数: {stats['total_count']}")
    print(f"   アクティブ: {stats['active_count']}")
    print(f"   休会中: {stats['inactive_count']}")  
    print(f"   退会済: {stats['withdrawn_count']}")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP エラー: {e.code}")
    error_data = e.read().decode('utf-8')
    print(f"エラー詳細: {error_data}")
except Exception as e:
    print(f"❌ 登録エラー: {e}")