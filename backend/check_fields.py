#!/usr/bin/env python3
"""30フィールド確認スクリプト"""
import urllib.request
import json

# API エンドポイント
url = "http://localhost:8000/api/v1/members/10000000001"
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read())

print("=== 30 Fields Check ===")
print()

# 30フィールドリスト（カナ除外）
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

missing = []
populated = 0

for i, field in enumerate(fields, 1):
    value = data.get(field)
    status = "✓" if value else "✗"
    display_value = value if value else "(empty)"
    print(f"{i:2}. {status} {field:20} = {display_value}")
    
    if value:
        populated += 1
    else:
        missing.append(field)

print()
print(f"Total fields: {len(fields)}")
print(f"Populated: {populated}/{len(fields)}")
print(f"Empty: {len(missing)}")
if missing:
    print(f"Empty fields: {', '.join(missing)}")