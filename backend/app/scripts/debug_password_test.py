#!/usr/bin/env python3
# パスワード強度デバッグテスト

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.security_service import security_service

print("🔍 パスワード強度デバッグテスト")
print("=" * 40)

# 強いパスワードの詳細チェック
strong_password = "ComplexPassword123!"
result = security_service.validate_password_strength(strong_password)

print(f"パスワード: {strong_password}")
print(f"有効: {result['is_valid']}")
print(f"スコア: {result['score']}")
print(f"エラー: {result['errors']}")
print(f"推奨: {result['suggestions']}")
print()

# 各チェック項目を個別に確認
import re

print("個別チェック:")
print(f"長さ >= 12: {len(strong_password) >= 12}")
print(f"大文字含む: {bool(re.search(r'[A-Z]', strong_password))}")
print(f"小文字含む: {bool(re.search(r'[a-z]', strong_password))}")
print(f"数字含む: {bool(re.search(r'\d', strong_password))}")
print(f"記号含む: {bool(re.search(r'[!@#$%^&*(),.?\":{}|<>]', strong_password))}")

common_passwords = [
    "password", "123456", "admin", "qwerty", "letmein", 
    "welcome", "monkey", "dragon", "master", "secret"
]
print(f"一般的パスワードではない: {strong_password.lower() not in common_passwords}")

print(f"連続文字なし: {not bool(re.search(r'(.)\\1{2,}', strong_password))}")
print(f"連続文字列なし: {not bool(re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', strong_password.lower()))}")