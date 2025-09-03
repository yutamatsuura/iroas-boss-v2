"""
Direct padding test - test the padding function directly
"""

def empty_to_none(value):
    """空文字や空白のみをNoneに変換"""
    return None if value == '' else value

def pad_number(value, length):
    try:
        print(f"pad_number: value={repr(value)}, length={length}")
        
        if value and str(value).strip() and str(value).strip().isdigit():
            padded = str(value).strip().zfill(length)
            print(f"  -> padded: {padded}")
            return padded
        
        result = empty_to_none(value)
        print(f"  -> not padded: {repr(result)}")
        return result
    except Exception as e:
        print(f"  -> ERROR: {str(e)}")
        return empty_to_none(value)

# Test the function
print("=== Testing pad_number function ===")
test_values = [
    ('500', 11),
    ('700', 11),
    ('1', 4),
    ('5', 3),
    ('123456', 7),
    ('', 11),
    (None, 11),
]

for value, length in test_values:
    result = pad_number(value, length)
    print(f"Final result: {repr(result)}")
    print("---")