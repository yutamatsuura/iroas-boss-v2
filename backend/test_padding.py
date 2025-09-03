"""
数値パディング機能のテスト
"""
import requests
import os

# テスト用CSVデータ（短い番号、正しいヘッダー名）
test_csv = """ステータス,IROAS会員番号,氏名,メールアドレス,称号,ユーザータイプ,加入プラン,決済方法,登録日,直上者ID,紹介者ID,銀行名,銀行コード,支店名,支店コード,口座番号,口座種別
アクティブ,1000,テスト太郎,test1@example.com,称号なし,通常,HERO,銀行振込,2025/01/01,500,700,みずほ銀行,1,新宿,5,123456,普通
アクティブ,2000,テスト花子,test2@example.com,ナイト/デイム,通常,HERO,カード決済,2025/01/01,600,800,三菱UFJ,5,東京,10,789012,普通"""

# CSVファイル作成
with open('test_padding.csv', 'w', encoding='utf-8') as f:
    f.write(test_csv)

print("テスト用CSVファイル作成完了")
print("短い番号でテスト:")
print("- 会員番号: 1000, 2000")
print("- 直上者ID: 500, 600") 
print("- 紹介者ID: 700, 800")
print("- 銀行コード: 1, 5")
print("- 支店コード: 5, 10")
print("- 口座番号: 123456, 789012")

# APIテスト
try:
    with open('test_padding.csv', 'rb') as f:
        files = {'file': ('test_padding.csv', f, 'text/csv')}
        response = requests.post('http://localhost:8000/api/v1/members/import', files=files)
    
    print(f"\nAPIレスポンス:")
    print(f"ステータス: {response.status_code}")
    print(f"結果: {response.text}")
    
except Exception as e:
    print(f"エラー: {str(e)}")

# クリーンアップ
if os.path.exists('test_padding.csv'):
    os.remove('test_padding.csv')