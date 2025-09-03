"""
シンプルなインポートテスト - padding関数が呼ばれているか確認
"""
import requests
import os

# 非常にシンプルなCSV（1行のみ）
test_csv = """ステータス,IROAS会員番号,氏名,メールアドレス,直上者ID,紹介者ID,銀行コード,支店コード,口座番号
アクティブ,9999,テスト,test@example.com,500,700,1,5,123456"""

# CSVファイル作成
with open('test_simple.csv', 'w', encoding='utf-8') as f:
    f.write(test_csv)

print("シンプルCSVファイル作成完了")
print("テストデータ: 会員番号=9999, 直上者ID=500, 紹介者ID=700, 銀行コード=1, 支店コード=5, 口座番号=123456")

# APIテスト
try:
    with open('test_simple.csv', 'rb') as f:
        files = {'file': ('test_simple.csv', f, 'text/csv')}
        response = requests.post('http://localhost:8000/api/v1/members/import', files=files)
    
    print(f"APIレスポンス:")
    print(f"ステータス: {response.status_code}")
    print(f"結果: {response.text}")
    
except Exception as e:
    print(f"エラー: {str(e)}")

# クリーンアップ
if os.path.exists('test_simple.csv'):
    os.remove('test_simple.csv')