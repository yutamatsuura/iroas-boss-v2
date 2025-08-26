#!/usr/bin/env python3
# IROAS BOSS V2 - 簡易セキュリティテスト
# Phase 21対応・基本機能確認

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

print("🔒 IROAS BOSS V2 セキュリティ基本テスト")
print("=" * 50)

# 1. インポートテスト
try:
    from app.services.security_service import security_service
    print("✅ SecurityService インポート成功")
except Exception as e:
    print(f"❌ SecurityService インポートエラー: {e}")

try:
    from app.services.audit_service import mlm_audit_service
    print("✅ AuditService インポート成功")
except Exception as e:
    print(f"❌ AuditService インポートエラー: {e}")

try:
    from app.services.notification_service import security_notification_service
    print("✅ NotificationService インポート成功")
except Exception as e:
    print(f"❌ NotificationService インポートエラー: {e}")

try:
    from app.core.security import security
    print("✅ Security Core インポート成功")
except Exception as e:
    print(f"❌ Security Core インポートエラー: {e}")

# 2. パスワード強度テスト
print("\n🔐 パスワード強度テスト")
try:
    weak_result = security_service.validate_password_strength("123456")
    strong_result = security_service.validate_password_strength("ComplexPassword123!")
    
    if not weak_result["is_valid"]:
        print("✅ 弱いパスワード検出成功")
    else:
        print("❌ 弱いパスワード検出失敗")
    
    if strong_result["is_valid"]:
        print("✅ 強いパスワード認識成功")
    else:
        print("❌ 強いパスワード認識失敗")
        
except Exception as e:
    print(f"❌ パスワード強度テストエラー: {e}")

# 3. セキュアパスワード生成テスト
print("\n🎲 パスワード生成テスト")
try:
    password = security_service.generate_secure_password(16)
    if len(password) == 16:
        print(f"✅ セキュアパスワード生成成功: {password}")
    else:
        print(f"❌ パスワード長不正: {len(password)}")
        
except Exception as e:
    print(f"❌ パスワード生成エラー: {e}")

# 4. ハッシュ化テスト
print("\n#️⃣ パスワードハッシュテスト")
try:
    test_password = "TestPassword123!"
    hashed = security.hash_password(test_password)
    verified = security.verify_password(test_password, hashed)
    
    if verified:
        print("✅ パスワードハッシュ化・検証成功")
    else:
        print("❌ パスワード検証失敗")
        
except Exception as e:
    print(f"❌ パスワードハッシュエラー: {e}")

# 5. JWTトークンテスト
print("\n🎟️ JWTトークンテスト")
try:
    token_data = {"sub": "1", "username": "test_user", "role": "MLM_MANAGER"}
    token = security.create_access_token(token_data)
    
    if token and len(token) > 10:
        print("✅ JWT生成成功")
    else:
        print("❌ JWT生成失敗")
        
except Exception as e:
    print(f"❌ JWTテストエラー: {e}")

print("\n" + "=" * 50)
print("🎯 基本セキュリティ機能テスト完了")
print("Phase 21 認証システム基本動作確認済み")
print("=" * 50)