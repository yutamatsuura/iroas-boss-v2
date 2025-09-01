#!/usr/bin/env python3
import urllib.request
import json

# ゆうちょ銀行利用者のデータを確認
members_to_check = ["10000000003", "10000000013"]

for member_id in members_to_check:
    url = f"http://localhost:8000/api/v1/members/{member_id}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        
        print(f"=== Member {member_id} ({data['name']}) ===")
        print(f"銀行名: {data.get('bank_name', '(なし)')}")
        print(f"ゆうちょ記号: {data.get('yucho_symbol', '(なし)')}")
        print(f"ゆうちょ番号: {data.get('yucho_number', '(なし)')}")
        print()
    except Exception as e:
        print(f"Error getting member {member_id}: {e}")