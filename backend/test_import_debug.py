"""
CSV インポート処理のデバッグ
"""
import requests
import os

# テスト用のシンプルなCSV（先頭0が削除されたケース）
test_csv = """ステータス,IROAS会員番号,氏名,メールアドレス,称号,ユーザータイプ,加入プラン,決済方法,登録日,電話番号,性別,郵便番号,都道府県,住所2,住所3,直上者ID,直上者名,紹介者ID,紹介者名,報酬振込先の銀行名,報酬振込先の銀行コード,報酬振込先の支店名,報酬振込先の支店コード,口座番号,ゆうちょの場合の記号,ゆうちょの場合の番号,口座種別,備考
アクティブ,0,白石 達也,lisence@mikoto.co.jp,エンペラー/エンプレス,通常,HERO,銀行振込,2016/7/27,090-3333-3333,男性,,,,,,,,,愛知,0005,一宮,001,2050632,,,普通,IROAS創業者。組織図のトップに配置
アクティブ,15700,澤原 洋,hilo586@mac.com,ナイト/デイム,通常,HERO,カード決済,2016/7/27,090-3424-2376,男性,491-0131,愛知県,一宮市,笹野字上久野22-2,,70000,上村 勇斗,愛知,0005,一宮,001,2050632,,,普通,"""

# CSVファイルを作成
with open('test_import.csv', 'w', encoding='utf-8') as f:
    f.write(test_csv)

print("テストCSVファイルを作成しました")

# APIにアップロード
try:
    with open('test_import.csv', 'rb') as f:
        files = {'file': ('test_import.csv', f, 'text/csv')}
        response = requests.post('http://localhost:8000/api/v1/members/import', files=files)
    
    print(f"ステータスコード: {response.status_code}")
    print(f"レスポンス: {response.text}")
    
    if response.status_code == 200:
        print("インポート成功")
    else:
        print("インポート失敗")
        
except Exception as e:
    print(f"エラー: {str(e)}")

# クリーンアップ
if os.path.exists('test_import.csv'):
    os.remove('test_import.csv')