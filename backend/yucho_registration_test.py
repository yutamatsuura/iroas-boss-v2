#!/usr/bin/env python3
"""
ゆうちょ銀行会員登録テスト
ゆうちょ銀行の記号・番号を使用した30項目完全版
"""

import urllib.request
import json

# ゆうちょ銀行利用者データ（30項目完全版）
yucho_member_data = {
    # 1-5: 基本情報
    "status": "ACTIVE",
    "member_number": "10000000020",
    "name": "手動登録テスト", 
    "email": "manual.test@example.com",
    
    # 6-9: MLM情報
    "title": "LORD_LADY",
    "user_type": "NORMAL",
    "plan": "HERO", 
    "payment_method": "TRANSFER",
    
    # 10-11: 日付情報
    "registration_date": "2024-02-20",
    "withdrawal_date": None,
    
    # 12-17: 連絡先情報
    "phone": "080-3333-4444",
    "gender": "FEMALE",
    "postal_code": "164-0001", 
    "prefecture": "東京都",
    "address2": "中野区中野5-6-7",
    "address3": "中野サンプラザ1205",
    
    # 18-21: 組織情報
    "upline_id": "10000000002",
    "upline_name": "佐藤花子",
    "referrer_id": "10000000016",
    "referrer_name": "テスト太郎",
    
    # 22-29: 銀行情報（ゆうちょ銀行）
    "bank_name": "ゆうちょ銀行",
    "bank_code": None,
    "branch_name": None, 
    "branch_code": None,
    "account_number": None,
    "yucho_symbol": "18220",
    "yucho_number": "87654321",
    "account_type": None,
    
    # 30: その他
    "notes": "ゆうちょ銀行利用・手動登録テスト"
}

print("=== ゆうちょ銀行会員登録APIテスト ===")
print(f"会員番号: {yucho_member_data['member_number']}")
print(f"氏名: {yucho_member_data['name']}")
print(f"銀行: {yucho_member_data['bank_name']}")
print(f"ゆうちょ記号: {yucho_member_data['yucho_symbol']}")
print(f"ゆうちょ番号: {yucho_member_data['yucho_number']}")
print()

# API登録実行
url = "http://localhost:8000/api/v1/members/"
headers = {
    'Content-Type': 'application/json'
}

try:
    # JSON データを準備
    json_data = json.dumps(yucho_member_data).encode('utf-8')
    
    # リクエスト作成
    request = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
    
    # API呼び出し
    with urllib.request.urlopen(request) as response:
        response_data = json.loads(response.read())
    
    print("✅ ゆうちょ銀行会員登録成功！")
    print(f"   内部ID: {response_data.get('id')}")
    print(f"   作成日時: {response_data.get('created_at')}")
    print()
    
    # 登録された会員の詳細確認
    member_url = f"http://localhost:8000/api/v1/members/{yucho_member_data['member_number']}"
    with urllib.request.urlopen(member_url) as response:
        member_detail = json.loads(response.read())
    
    print("📋 ゆうちょ銀行利用者の詳細（30項目確認）:")
    
    # 重要フィールドを先にチェック
    print("\n🏦 銀行情報:")
    print(f"   銀行名: {member_detail.get('bank_name', '(なし)')}")
    print(f"   ゆうちょ記号: {member_detail.get('yucho_symbol', '(なし)')}")
    print(f"   ゆうちょ番号: {member_detail.get('yucho_number', '(なし)')}")
    print(f"   銀行コード: {member_detail.get('bank_code', '(なし)')}")
    print(f"   支店名: {member_detail.get('branch_name', '(なし)')}")
    
    # 全項目チェック
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
    
    print("\n📋 全項目詳細:")
    populated = 0
    for i, field in enumerate(fields, 1):
        value = member_detail.get(field)
        status = "✓" if value else "✗"
        print(f"{i:2}. {status} {field:20} = {value if value else '(empty)'}")
        if value:
            populated += 1
    
    print()
    print(f"📊 結果: {populated}/{len(fields)} 項目が入力されています")
    
    # ゆうちょ専用項目が正しく設定されているか確認
    yucho_fields_ok = (
        member_detail.get('bank_name') == 'ゆうちょ銀行' and
        member_detail.get('yucho_symbol') == '18220' and
        member_detail.get('yucho_number') == '87654321' and
        member_detail.get('bank_code') is None and
        member_detail.get('branch_name') is None
    )
    
    print()
    print(f"🏦 ゆうちょ銀行専用項目: {'✅ 正常' if yucho_fields_ok else '❌ 異常'}")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP エラー: {e.code}")
    error_data = e.read().decode('utf-8')
    print(f"エラー詳細: {error_data}")
except Exception as e:
    print(f"❌ 登録エラー: {e}")