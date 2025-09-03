"""
パディング関数のテスト
"""

def empty_to_none(value):
    """空文字や空白のみをNoneに変換"""
    if not value or str(value).strip() == "":
        return None
    return str(value).strip()

def pad_number(value, length, field_name=""):
    print(f"pad_number called: {field_name}={value} (type: {type(value)})")
    
    if value and str(value).strip() and str(value).strip().isdigit():
        padded = str(value).strip().zfill(length)
        print(f"DEBUG: {field_name}: {value} -> {padded}")
        return padded
    
    print(f"DEBUG: {field_name}: {value} -> None (not padded)")
    return empty_to_none(value)

# テスト
test_values = [
    ('500', 11, '直上者ID'),
    ('700', 11, '紹介者ID'),
    ('1', 4, '銀行コード'),
    ('5', 3, '支店コード'),
    ('123456', 7, '口座番号'),
]

for value, length, field_name in test_values:
    result = pad_number(value, length, field_name)
    print(f"結果: {result}")
    print("---")