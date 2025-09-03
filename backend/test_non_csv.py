"""
非CSVファイルのテスト
"""
import requests

# テキストファイル作成
with open('test.txt', 'w') as f:
    f.write('test')

try:
    with open('test.txt', 'rb') as f:
        files = {'file': ('test.txt', f, 'text/plain')}
        response = requests.post('http://localhost:8000/api/v1/members/import', files=files)
    
    print(f"ステータス: {response.status_code}")
    print(f"レスポンス: {response.text}")
    
except Exception as e:
    print(f"エラー: {str(e)}")

import os
if os.path.exists('test.txt'):
    os.remove('test.txt')