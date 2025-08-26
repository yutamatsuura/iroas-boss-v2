"""
システム設定サービス

Phase A-1a: システム設定API（7.1-7.2）
- 完全独立、いつでも実装可能
- モックアップP-008対応

エンドポイント:
- 7.1 GET /api/settings/system - システム設定
- 7.2 GET /api/settings/business-rules - ビジネスルール
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.setting import Setting, BusinessRule
from app.schemas.setting import (
    SystemSettingsResponse,
    BusinessRulesResponse,
    PlanRate,
    TitleRequirement,
    BonusRate
)


class SettingService:
    """
    システム設定サービスクラス
    ビジネスルールと固定値の管理を担当
    """

    def __init__(self, db: Session):
        self.db = db

    async def get_system_settings(self) -> SystemSettingsResponse:
        """
        システム設定取得
        API 7.1: GET /api/settings/system
        """
        # プラン料金設定
        plan_rates = [
            PlanRate(
                plan_name="ヒーロープラン",
                monthly_fee=10670,
                annual_fee=128040,
                description="メインプラン"
            ),
            PlanRate(
                plan_name="テストプラン",
                monthly_fee=9800,
                annual_fee=117600,
                description="テスト用プラン"
            )
        ]

        # 決済タイミング設定
        payment_timing = {
            "card_payment": {
                "execution_period": "月初1～5日",
                "csv_output_timing": "対象月前月末",
                "description": "Univapayカード決済"
            },
            "bank_transfer": {
                "execution_period": "月初～12日CSV出力、27日自動実行",
                "csv_output_timing": "対象月前月末～12日",
                "description": "Univapay口座振替"
            },
            "manual_bank": {
                "execution_period": "随時",
                "csv_output_timing": "手動確認後記録",
                "description": "銀行振込（手動）"
            },
            "infocart": {
                "execution_period": "随時",
                "csv_output_timing": "手動確認後記録",
                "description": "インフォカート（手動）"
            }
        }

        # 最低支払金額設定
        minimum_payout = {
            "amount": 5000,
            "currency": "JPY",
            "carryover_rule": "5,000円未満は翌月繰越",
            "bank_fee": "会社負担"
        }

        return SystemSettingsResponse(
            version="2.0.0",
            system_name="IROAS BOSS v2",
            max_members=50,
            recruitment_status="停止中",
            plan_rates=plan_rates,
            payment_timing=payment_timing,
            minimum_payout=minimum_payout,
            encoding_settings={
                "csv_export": "Shift-JIS",
                "csv_import": "UTF-8/Shift-JIS自動判定",
                "database": "UTF-8"
            },
            calculation_timing={
                "reward_calculation": "毎月25日頃",
                "payment_execution": "計算完了後1週間以内",
                "csv_generation": "支払確定時"
            }
        )

    async def get_business_rules(self) -> BusinessRulesResponse:
        """
        ビジネスルール取得
        API 7.2: GET /api/settings/business-rules
        """
        # タイトル要件定義
        title_requirements = [
            TitleRequirement(
                title="スタート",
                conditions=["新規登録時"],
                benefits=["基本タイトルボーナス"]
            ),
            TitleRequirement(
                title="リーダー",
                conditions=["直下2名以上", "月間売上10万円以上"],
                benefits=["リーダーボーナス", "組織ボーナス"]
            ),
            TitleRequirement(
                title="サブマネージャー",
                conditions=["直下リーダー2名以上", "組織売上50万円以上"],
                benefits=["サブマネージャーボーナス", "パワーボーナス"]
            ),
            TitleRequirement(
                title="マネージャー",
                conditions=["直下サブマネージャー2名以上", "組織売上100万円以上"],
                benefits=["マネージャーボーナス", "マネジメントボーナス"]
            ),
            TitleRequirement(
                title="エキスパートマネージャー",
                conditions=["直下マネージャー2名以上", "組織売上300万円以上"],
                benefits=["エキスパートボーナス", "リーダーシップボーナス"]
            ),
            TitleRequirement(
                title="ディレクター",
                conditions=["直下エキスパート2名以上", "組織売上500万円以上"],
                benefits=["ディレクターボーナス", "エリアボーナス"]
            ),
            TitleRequirement(
                title="エリアディレクター",
                conditions=["直下ディレクター2名以上", "組織売上1000万円以上"],
                benefits=["エリアディレクターボーナス", "ロイヤルファミリーボーナス"]
            )
        ]

        # ボーナス料率設定
        bonus_rates = [
            BonusRate(
                bonus_type="デイリーボーナス",
                rate=100.0,
                calculation_method="参加費×日割り計算",
                payment_timing="月次"
            ),
            BonusRate(
                bonus_type="タイトルボーナス",
                rate=0.0,
                calculation_method="タイトル別固定額",
                payment_timing="月次"
            ),
            BonusRate(
                bonus_type="リファラルボーナス",
                rate=50.0,
                calculation_method="直紹介者参加費の50%",
                payment_timing="月次"
            ),
            BonusRate(
                bonus_type="パワーボーナス",
                rate=0.0,
                calculation_method="組織売上に応じた変動率",
                payment_timing="月次"
            ),
            BonusRate(
                bonus_type="メンテナンスボーナス",
                rate=0.0,
                calculation_method="センターメンテナンスキット販売実績",
                payment_timing="月次"
            ),
            BonusRate(
                bonus_type="セールスアクティビティボーナス",
                rate=0.0,
                calculation_method="新規紹介活動実績",
                payment_timing="月次"
            ),
            BonusRate(
                bonus_type="ロイヤルファミリーボーナス",
                rate=0.0,
                calculation_method="最高タイトル保持者特別報酬",
                payment_timing="月次"
            )
        ]

        # 組織管理ルール
        organization_rules = {
            "withdrawal_processing": {
                "method": "手動調整",
                "auto_compression": False,
                "manual_sponsor_change": True,
                "approval_required": True,
                "description": "退会時は自動圧縮ではなく手動でスポンサー調整"
            },
            "sponsor_change": {
                "restrictions": ["月1回まで", "組織構造維持", "承認必要"],
                "approval_process": "管理者承認",
                "effective_timing": "翌月1日"
            },
            "max_depth": {
                "unlimited": True,
                "recommended_depth": 10,
                "warning_depth": 15
            }
        }

        # CSV形式設定
        csv_formats = {
            "univapay_card": {
                "encoding": "Shift-JIS",
                "delimiter": ",",
                "required_columns": ["顧客オーダー番号", "金額", "決済方法"],
                "file_name_format": "card_payment_YYYYMMDD.csv"
            },
            "univapay_transfer": {
                "encoding": "Shift-JIS", 
                "delimiter": ",",
                "required_columns": ["顧客番号", "金額", "振替日"],
                "file_name_format": "transfer_payment_YYYYMMDD.csv"
            },
            "gmo_netbank": {
                "encoding": "Shift-JIS",
                "delimiter": ",",
                "required_columns": ["銀行コード", "支店コード", "口座種別", "口座番号", "受取人名", "振込金額"],
                "file_name_format": "gmo_transfer_YYYYMMDD.csv"
            }
        }

        return BusinessRulesResponse(
            title_requirements=title_requirements,
            bonus_rates=bonus_rates,
            organization_rules=organization_rules,
            csv_formats=csv_formats,
            calculation_rules={
                "calculation_order": [
                    "デイリーボーナス",
                    "タイトルボーナス", 
                    "リファラルボーナス",
                    "パワーボーナス",
                    "メンテナンスボーナス",
                    "セールスアクティビティボーナス",
                    "ロイヤルファミリーボーナス"
                ],
                "minimum_payout": 5000,
                "carryover_handling": "automatic",
                "calculation_precision": 2
            },
            member_limits={
                "max_total_members": 50,
                "new_registration": False,
                "status_change_restrictions": ["管理者承認必要"]
            }
        )

    async def validate_system_integrity(self) -> Dict[str, Any]:
        """
        システム整合性チェック
        内部使用：設定値の整合性を確認
        """
        issues = []
        
        # 基本設定チェック
        system_settings = await self.get_system_settings()
        business_rules = await self.get_business_rules()
        
        # プラン料金の整合性チェック
        for plan in system_settings.plan_rates:
            if plan.monthly_fee <= 0:
                issues.append(f"プラン {plan.plan_name} の月額料金が無効です")
        
        # ボーナス料率の整合性チェック
        total_rate = sum(bonus.rate for bonus in business_rules.bonus_rates if bonus.rate > 0)
        if total_rate > 100:
            issues.append("ボーナス料率の合計が100%を超えています")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "checked_at": "2024-01-01T00:00:00",
            "total_checks": len(system_settings.plan_rates) + len(business_rules.bonus_rates)
        }