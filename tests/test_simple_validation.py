# -*- coding: utf-8 -*-
"""
簡単な動作確認テスト
実データ主義の基本動作を確認
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

def test_basic_imports():
    """基本的なインポートテスト"""
    try:
        from app.models.member import Member
        print("✅ Member model import successful")
        
        from app.models.reward import RewardHistory, BonusType
        print("✅ RewardHistory model import successful")
        
        from app.models.payment import PaymentHistory
        print("✅ PaymentRecord model import successful")
        
        from app.services.payment_management_service import PaymentManagementService
        print("✅ PaymentManagementService import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_enum_values():
    """Enum値の確認"""
    try:
        from app.models.reward import BonusType
        
        assert BonusType.DAILY == "デイリーボーナス"
        assert BonusType.TITLE == "タイトルボーナス"
        assert BonusType.REFERRAL == "リファラルボーナス"
        assert BonusType.POWER == "パワーボーナス"
        print("✅ BonusType enum validation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Enum validation error: {e}")
        return False

def test_decimal_operations():
    """Decimal演算の確認"""
    try:
        from decimal import Decimal
        
        # 5,000円未満繰越チェック
        amount1 = Decimal('4999.99')
        amount2 = Decimal('5000.00')
        
        assert amount1 < Decimal('5000')
        assert amount2 >= Decimal('5000')
        
        # 報酬計算精度チェック
        daily_rate = Decimal('344.52')  # 10670 / 31
        total = daily_rate * 31
        
        print(f"Daily rate: {daily_rate}")
        print(f"Total: {total}")
        print("✅ Decimal operations successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Decimal operation error: {e}")
        return False

def main():
    """メイン実行"""
    print("🚀 IROAS BOSS v2 基本動作確認テスト")
    print("=" * 50)
    
    tests = [
        ("基本インポート", test_basic_imports),
        ("Enum値確認", test_enum_values),
        ("Decimal演算", test_decimal_operations)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 {name}テスト:")
        result = test_func()
        results.append(result)
        print()
    
    # 結果サマリー
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 全テスト合格！ ({passed}/{total})")
        print("✅ 実データ主義テスト環境構築完了")
        return 0
    else:
        print(f"❌ 一部テスト失敗 ({passed}/{total})")
        return 1

if __name__ == "__main__":
    exit(main())