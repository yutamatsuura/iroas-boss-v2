import requests

# APIから会員一覧を取得
response = requests.get("http://localhost:8000/api/v1/members/")
data = response.json()

print(f"総会員数: {data['total_count']}")
print(f"アクティブ: {data['active_count']}")
print(f"休会中: {data['inactive_count']}") 
print(f"退会済: {data['withdrawn_count']}")
print(f"\n会員リスト件数: {len(data['members'])}")

if data['members']:
    print("\n会員データ:")
    for member in data['members']:
        print(f"  - {member['member_number']}: {member['name']}")