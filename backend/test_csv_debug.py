"""
CSV読み込みテスト
"""
import csv
import io

# テスト用CSVデータ
test_csv = """ステータス,IROAS会員番号,氏名,メールアドレス,称号,ユーザータイプ,加入プラン,決済方法,登録日,直上者ID,紹介者ID,銀行名,銀行コード,支店名,支店コード,口座番号,口座種別
アクティブ,1000,テスト太郎,test1@example.com,称号なし,通常,HERO,銀行振込,2025/01/01,500,700,みずほ銀行,1,新宿,5,123456,普通
アクティブ,2000,テスト花子,test2@example.com,ナイト/デイム,通常,HERO,カード決済,2025/01/01,600,800,三菱UFJ,5,東京,10,789012,普通"""

reader = csv.DictReader(io.StringIO(test_csv))

for row_num, row in enumerate(reader, start=2):
    print(f"行{row_num}: {dict(row)}")
    print(f"直上者ID: '{row.get('直上者ID')}' (type: {type(row.get('直上者ID'))})")
    print(f"紹介者ID: '{row.get('紹介者ID')}' (type: {type(row.get('紹介者ID'))})")  
    print(f"銀行コード: '{row.get('銀行コード')}' (type: {type(row.get('銀行コード'))})")
    print(f"支店コード: '{row.get('支店コード')}' (type: {type(row.get('支店コード'))})")
    print(f"口座番号: '{row.get('口座番号')}' (type: {type(row.get('口座番号'))})")
    print("---")