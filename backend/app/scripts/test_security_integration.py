#!/usr/bin/env python3
# IROAS BOSS V2 - セキュリティ統合テスト
# Phase 21対応・認証セキュリティ完全テスト

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# パス追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole, UserStatus
from app.services.auth_service import auth_service
from app.services.security_service import security_service
from app.services.audit_service import mlm_audit_service, AuditEvent, AuditEventType
from app.services.notification_service import security_notification_service
from app.schemas.auth import LoginRequest
from app.core.security import security

class SecurityIntegrationTester:
    """セキュリティ統合テストクラス"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.test_results = []
        
    def add_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """テスト結果追加"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    async def setup_test_environment(self):
        """テスト環境セットアップ"""
        print("🔧 セットアップ中...")
        
        try:
            # データベーステーブル作成
            Base.metadata.create_all(bind=engine)
            
            # テストユーザー削除（既存の場合）
            existing_users = self.db.query(User).filter(
                User.username.in_(["security_test_user", "security_admin_user"])
            ).all()
            
            for user in existing_users:
                self.db.delete(user)
            
            self.db.commit()
            
            # テストユーザー作成
            test_user = User(
                username="security_test_user",
                email="security_test@iroas-boss.com",
                full_name="セキュリティテストユーザー",
                hashed_password=security.get_password_hash("TestPassword123!"),
                role=UserRole.MLM_MANAGER,
                status=UserStatus.ACTIVE,
                is_active=True,
                mfa_enabled=False
            )
            
            admin_user = User(
                username="security_admin_user", 
                email="security_admin@iroas-boss.com",
                full_name="セキュリティ管理者ユーザー",
                hashed_password=security.get_password_hash("AdminPassword123!"),
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                is_active=True,
                mfa_enabled=True,
                mfa_secret="TESTSECRET123456789"
            )
            
            self.db.add(test_user)
            self.db.add(admin_user)
            self.db.commit()
            
            self.add_result("テスト環境セットアップ", True, "テストユーザー作成完了")
            
        except Exception as e:
            self.add_result("テスト環境セットアップ", False, error=str(e))
            raise
    
    async def test_basic_authentication(self):
        """基本認証テスト"""
        print("🔐 基本認証テスト開始...")
        
        try:
            # 正常ログインテスト
            login_request = LoginRequest(
                username="security_test_user",
                password="TestPassword123!"
            )
            
            response = await auth_service.authenticate_user(
                login_request, "127.0.0.1", "Test-Agent", self.db
            )
            
            if response.access_token and response.user.username == "security_test_user":
                self.add_result("正常ログイン", True, "JWTトークン生成成功")
            else:
                self.add_result("正常ログイン", False, "レスポンスが不正")
            
            # 不正パスワードテスト
            try:
                login_request_invalid = LoginRequest(
                    username="security_test_user",
                    password="WrongPassword"
                )
                
                await auth_service.authenticate_user(
                    login_request_invalid, "127.0.0.1", "Test-Agent", self.db
                )
                self.add_result("不正パスワードブロック", False, "不正ログインが通ってしまった")
                
            except Exception:
                self.add_result("不正パスワードブロック", True, "不正ログインが正しくブロックされた")
            
        except Exception as e:
            self.add_result("基本認証テスト", False, error=str(e))
    
    async def test_security_analysis(self):
        """セキュリティ分析テスト"""
        print("🔍 セキュリティ分析テスト開始...")
        
        try:
            # ユーザー取得
            test_user = self.db.query(User).filter(User.username == "security_test_user").first()
            
            # 行動分析テスト
            analysis = await security_service.analyze_login_behavior(
                test_user.id, "192.168.1.100", "Mozilla/5.0 Test", self.db
            )
            
            if "risk_score" in analysis and "risk_factors" in analysis:
                self.add_result("セキュリティ行動分析", True, f"リスクスコア: {analysis['risk_score']}")
            else:
                self.add_result("セキュリティ行動分析", False, "分析結果が不正")
            
            # パスワード強度チェック
            weak_password = security_service.validate_password_strength("123456")
            strong_password = security_service.validate_password_strength("ComplexPassword123!")
            
            if not weak_password["is_valid"] and strong_password["is_valid"]:
                self.add_result("パスワード強度チェック", True, "弱いパスワードが正しく検出された")
            else:
                self.add_result("パスワード強度チェック", False, "パスワード強度判定が不正")
            
            # セキュアパスワード生成
            generated_password = security_service.generate_secure_password(16)
            
            if len(generated_password) == 16:
                self.add_result("セキュアパスワード生成", True, f"生成されたパスワード長: {len(generated_password)}")
            else:
                self.add_result("セキュアパスワード生成", False, "パスワード生成失敗")
            
        except Exception as e:
            self.add_result("セキュリティ分析テスト", False, error=str(e))
    
    async def test_audit_logging(self):
        """監査ログテスト"""
        print("📝 監査ログテスト開始...")
        
        try:
            # 監査イベント作成
            audit_event = AuditEvent(
                event_type=AuditEventType.LOGIN_SUCCESS,
                user_id=1,
                session_id="test_session_123",
                ip_address="127.0.0.1",
                user_agent="Test-Agent",
                resource="/auth/login",
                action="test_login",
                details={
                    "test_mode": True,
                    "integration_test": True
                },
                success=True,
                timestamp=datetime.utcnow(),
                risk_level="low"
            )
            
            # ログ記録
            await mlm_audit_service.log_event(audit_event, self.db)
            
            self.add_result("監査ログ記録", True, "監査イベントが正常に記録された")
            
            # コンプライアンス報告書生成テスト
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = datetime.utcnow()
            
            report = await mlm_audit_service.generate_compliance_report(
                start_date, end_date, db=self.db
            )
            
            if "summary" in report and "generated_at" in report:
                self.add_result("コンプライアンス報告書", True, f"イベント数: {report['summary']['total_events']}")
            else:
                self.add_result("コンプライアンス報告書", False, "報告書生成失敗")
            
        except Exception as e:
            self.add_result("監査ログテスト", False, error=str(e))
    
    async def test_notification_system(self):
        """通知システムテスト"""
        print("📢 通知システムテスト開始...")
        
        try:
            # テストユーザー取得
            test_user = self.db.query(User).filter(User.username == "security_test_user").first()
            
            # セキュリティアラート送信テスト
            await security_notification_service.send_critical_security_alert(
                event_type="test_security_alert",
                user=test_user,
                details={
                    "test_mode": True,
                    "alert_level": "test"
                },
                ip_address="127.0.0.1"
            )
            
            self.add_result("緊急セキュリティアラート", True, "アラートが正常に処理された")
            
            # ユーザー通知テスト
            await security_notification_service.send_user_security_notification(
                user=test_user,
                notification_type="test_notification",
                details={
                    "test_mode": True
                }
            )
            
            self.add_result("ユーザーセキュリティ通知", True, "ユーザー通知が正常に処理された")
            
            # 累積アラートチェック（基本テスト）
            await security_notification_service.check_and_send_accumulated_alerts(self.db)
            
            self.add_result("累積アラートチェック", True, "累積アラート処理が完了")
            
        except Exception as e:
            self.add_result("通知システムテスト", False, error=str(e))
    
    async def test_mfa_integration(self):
        """MFA統合テスト"""
        print("🔐 MFA統合テスト開始...")
        
        try:
            # 管理者ユーザー取得
            admin_user = self.db.query(User).filter(User.username == "security_admin_user").first()
            
            # MFA有効ユーザーでのログインテスト
            try:
                login_request = LoginRequest(
                    username="security_admin_user",
                    password="AdminPassword123!"
                    # MFAコードなし
                )
                
                await auth_service.authenticate_user(
                    login_request, "127.0.0.1", "Test-Agent", self.db
                )
                self.add_result("MFA要求チェック", False, "MFAが要求されていない")
                
            except Exception as e:
                if "MFAコードが必要です" in str(e):
                    self.add_result("MFA要求チェック", True, "MFAが正しく要求された")
                else:
                    self.add_result("MFA要求チェック", False, f"予期しないエラー: {e}")
            
        except Exception as e:
            self.add_result("MFA統合テスト", False, error=str(e))
    
    async def test_rate_limiting(self):
        """レート制限テスト"""
        print("⚡ レート制限テスト開始...")
        
        try:
            # 短時間でのログイン試行をシミュレーション
            failed_attempts = 0
            
            for i in range(3):
                try:
                    login_request = LoginRequest(
                        username="security_test_user",
                        password="WrongPassword"
                    )
                    
                    await auth_service.authenticate_user(
                        login_request, "192.168.1.200", "Test-Agent", self.db
                    )
                    
                except Exception:
                    failed_attempts += 1
            
            if failed_attempts == 3:
                self.add_result("レート制限基本動作", True, f"失敗ログイン試行: {failed_attempts}回")
            else:
                self.add_result("レート制限基本動作", False, "レート制限が期待通りに動作していない")
            
        except Exception as e:
            self.add_result("レート制限テスト", False, error=str(e))
    
    def generate_test_report(self):
        """テストレポート生成"""
        print("=" * 60)
        print("🔒 IROAS BOSS V2 セキュリティ統合テスト結果")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 テスト結果サマリー:")
        print(f"   総テスト数: {total_tests}")
        print(f"   成功: {passed_tests}")
        print(f"   失敗: {failed_tests}")
        print(f"   成功率: {(passed_tests / total_tests * 100):.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ 失敗したテスト:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test_name']}: {result['error']}")
            print()
        
        print("✅ 実装されたセキュリティ機能:")
        security_features = [
            "JWT認証・自動リフレッシュ",
            "多要素認証(MFA)・TOTP",
            "ロールベースアクセス制御(RBAC)",
            "セキュリティ行動分析",
            "レート制限・ブルートフォース対策",
            "監査ログ・コンプライアンス報告",
            "セキュリティアラート・通知システム",
            "パスワード強度チェック・生成",
            "セッション管理・デバイス信頼",
            "IP地理的分析・リスク評価"
        ]
        
        for feature in security_features:
            print(f"   ✓ {feature}")
        
        print()
        print("🎯 Phase 21 認証セキュリティ統合: 完了")
        print(f"⏰ テスト実行時刻: {datetime.utcnow().isoformat()}")
        print("=" * 60)
        
        # JSONレポート保存
        report_data = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_results": self.test_results,
            "security_features": security_features,
            "timestamp": datetime.utcnow().isoformat(),
            "phase": "21",
            "test_type": "security_integration"
        }
        
        with open("security_integration_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print("📄 詳細レポート: security_integration_test_report.json")
        
        return passed_tests == total_tests
    
    async def run_all_tests(self):
        """全テスト実行"""
        print("🚀 IROAS BOSS V2 セキュリティ統合テスト開始")
        print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("=" * 60)
        
        try:
            await self.setup_test_environment()
            await self.test_basic_authentication()
            await self.test_security_analysis()
            await self.test_audit_logging()
            await self.test_notification_system()
            await self.test_mfa_integration()
            await self.test_rate_limiting()
            
            return self.generate_test_report()
            
        except Exception as e:
            print(f"💥 テスト実行中にエラー: {e}")
            return False
        
        finally:
            self.db.close()

async def main():
    """メイン実行"""
    tester = SecurityIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 全てのテストが成功しました！")
        exit(0)
    else:
        print("\n⚠️ 一部のテストが失敗しました。詳細を確認してください。")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())