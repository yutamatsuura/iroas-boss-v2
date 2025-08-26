"""
システム設定データモデル

要件定義書のマスタ設定要件に対応：
- システム固定値の確認表示（変更不可）
- 参加費、タイトル条件、報酬率などの固定値管理
- 最小限の設定項目のみ
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Union
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Numeric
from app.database import Base


class SettingCategory(str, Enum):
    """設定カテゴリ"""
    BUSINESS_RULES = "ビジネスルール"
    PAYMENT_SETTINGS = "決済設定"
    REWARD_SETTINGS = "報酬設定"
    SYSTEM_SETTINGS = "システム設定"


class SettingType(str, Enum):
    """設定値タイプ"""
    STRING = "文字列"
    INTEGER = "整数"
    DECIMAL = "小数"
    BOOLEAN = "真偽値"
    JSON = "JSON"


class SystemSetting(Base):
    """
    システム設定テーブル
    固定値の管理と表示用
    """
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 設定情報
    key = Column(String(100), nullable=False, unique=True, index=True, comment="設定キー")
    category = Column(String(50), nullable=False, index=True, comment="カテゴリ")
    setting_type = Column(String(20), nullable=False, comment="設定値タイプ")
    
    # 設定値
    string_value = Column(String(500), nullable=True, comment="文字列値")
    integer_value = Column(Integer, nullable=True, comment="整数値")
    decimal_value = Column(Numeric(10, 2), nullable=True, comment="小数値")
    boolean_value = Column(Boolean, nullable=True, comment="真偽値")
    json_value = Column(JSON, nullable=True, comment="JSON値")
    
    # 表示情報
    display_name = Column(String(200), nullable=False, comment="表示名")
    description = Column(Text, nullable=True, comment="説明")
    unit = Column(String(20), nullable=True, comment="単位")
    
    # 管理情報
    is_editable = Column(Boolean, nullable=False, default=False, comment="編集可能フラグ")
    is_system = Column(Boolean, nullable=False, default=True, comment="システム設定フラグ")
    sort_order = Column(Integer, nullable=False, default=0, comment="表示順序")
    
    # システム情報
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<SystemSetting(key={self.key}, value={self.get_value()})>"
    
    def get_value(self) -> Union[str, int, float, bool, Dict, None]:
        """設定値を取得"""
        if self.setting_type == SettingType.STRING:
            return self.string_value
        elif self.setting_type == SettingType.INTEGER:
            return self.integer_value
        elif self.setting_type == SettingType.DECIMAL:
            return float(self.decimal_value) if self.decimal_value is not None else None
        elif self.setting_type == SettingType.BOOLEAN:
            return self.boolean_value
        elif self.setting_type == SettingType.JSON:
            return self.json_value
        return None
    
    def set_value(self, value: Union[str, int, float, bool, Dict]) -> None:
        """設定値を設定"""
        # 全ての値をリセット
        self.string_value = None
        self.integer_value = None
        self.decimal_value = None
        self.boolean_value = None
        self.json_value = None
        
        # 型に応じて値を設定
        if self.setting_type == SettingType.STRING:
            self.string_value = str(value)
        elif self.setting_type == SettingType.INTEGER:
            self.integer_value = int(value)
        elif self.setting_type == SettingType.DECIMAL:
            self.decimal_value = float(value)
        elif self.setting_type == SettingType.BOOLEAN:
            self.boolean_value = bool(value)
        elif self.setting_type == SettingType.JSON:
            self.json_value = value
        
        self.updated_at = datetime.utcnow()
    
    @property
    def formatted_value(self) -> str:
        """フォーマット済み表示値"""
        value = self.get_value()
        if value is None:
            return "未設定"
        
        if self.unit:
            return f"{value}{self.unit}"
        
        if self.setting_type == SettingType.DECIMAL:
            return f"{value:,.2f}"
        elif self.setting_type == SettingType.INTEGER:
            return f"{value:,}"
        elif self.setting_type == SettingType.BOOLEAN:
            return "有効" if value else "無効"
        elif self.setting_type == SettingType.JSON:
            return str(value)
        
        return str(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返す"""
        return {
            "key": self.key,
            "category": self.category,
            "setting_type": self.setting_type,
            "value": self.get_value(),
            "formatted_value": self.formatted_value,
            "display_name": self.display_name,
            "description": self.description,
            "unit": self.unit,
            "is_editable": self.is_editable,
            "sort_order": self.sort_order,
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def create_business_rule(cls, key: str, display_name: str, value: Union[str, int, float, bool, Dict],
                            description: str = None, unit: str = None, 
                            sort_order: int = 0) -> 'SystemSetting':
        """ビジネスルール設定作成"""
        setting_type = cls._get_setting_type(value)
        setting = cls(
            key=key,
            category=SettingCategory.BUSINESS_RULES.value,
            setting_type=setting_type,
            display_name=display_name,
            description=description,
            unit=unit,
            is_editable=False,
            is_system=True,
            sort_order=sort_order
        )
        setting.set_value(value)
        return setting
    
    @classmethod
    def create_payment_setting(cls, key: str, display_name: str, value: Union[str, int, float, bool, Dict],
                              description: str = None, unit: str = None,
                              sort_order: int = 0) -> 'SystemSetting':
        """決済設定作成"""
        setting_type = cls._get_setting_type(value)
        setting = cls(
            key=key,
            category=SettingCategory.PAYMENT_SETTINGS.value,
            setting_type=setting_type,
            display_name=display_name,
            description=description,
            unit=unit,
            is_editable=False,
            is_system=True,
            sort_order=sort_order
        )
        setting.set_value(value)
        return setting
    
    @classmethod
    def create_reward_setting(cls, key: str, display_name: str, value: Union[str, int, float, bool, Dict],
                             description: str = None, unit: str = None,
                             sort_order: int = 0) -> 'SystemSetting':
        """報酬設定作成"""
        setting_type = cls._get_setting_type(value)
        setting = cls(
            key=key,
            category=SettingCategory.REWARD_SETTINGS.value,
            setting_type=setting_type,
            display_name=display_name,
            description=description,
            unit=unit,
            is_editable=False,
            is_system=True,
            sort_order=sort_order
        )
        setting.set_value(value)
        return setting
    
    @classmethod
    def _get_setting_type(cls, value: Any) -> str:
        """値の型から設定タイプを判定"""
        if isinstance(value, bool):
            return SettingType.BOOLEAN
        elif isinstance(value, int):
            return SettingType.INTEGER
        elif isinstance(value, (float, Decimal)):
            return SettingType.DECIMAL
        elif isinstance(value, (dict, list)):
            return SettingType.JSON
        else:
            return SettingType.STRING


# 固定値の初期データ定義（データベース初期化時に使用）
DEFAULT_SYSTEM_SETTINGS = [
    # ビジネスルール
    ("HERO_PLAN_AMOUNT", "ヒーロープラン参加費", 10670, "ヒーロープランの月額参加費", "円", 1),
    ("TEST_PLAN_AMOUNT", "テストプラン参加費", 9800, "テストプランの月額参加費", "円", 2),
    ("MIN_PAYOUT_AMOUNT", "最低支払金額", 5000, "報酬支払いの最低金額（未満は繰越）", "円", 3),
    ("CALCULATION_DAY", "報酬計算実行日", 25, "毎月の報酬計算実行日", "日", 4),
    
    # 決済設定
    ("CARD_PAYMENT_PERIOD", "カード決済CSV出力期間", "1-5日", "月初のカード決済CSV出力期間", None, 1),
    ("TRANSFER_PAYMENT_PERIOD", "口座振替CSV出力期間", "1-12日", "月初の口座振替CSV出力期間", None, 2),
    ("TRANSFER_EXECUTION_DAY", "口座振替実行日", 27, "Univapay口座振替の自動実行日", "日", 3),
    
    # 報酬設定
    ("DAILY_BONUS_RATE_HERO", "デイリーボーナス率（ヒーロー）", 150, "ヒーロープランのデイリーボーナス日額", "円/日", 1),
    ("DAILY_BONUS_RATE_TEST", "デイリーボーナス率（テスト）", 130, "テストプランのデイリーボーナス日額", "円/日", 2),
    ("REFERRAL_BONUS_RATE", "リファラルボーナス率", 50, "直紹介者参加費に対する報酬率", "%", 3),
    ("POWER_BONUS_RATE", "パワーボーナス率", 3, "組織売上に対する報酬率", "%", 4),
    
    # タイトル別固定報酬
    ("TITLE_BONUS_KNIGHT", "称号報酬（ナイト/デイム）", 2500, "ナイト/デイム称号の月額固定報酬", "円", 5),
    ("TITLE_BONUS_LORD", "称号報酬（ロード/レディ）", 5000, "ロード/レディ称号の月額固定報酬", "円", 6),
    ("TITLE_BONUS_KING", "称号報酬（キング/クイーン）", 10000, "キング/クイーン称号の月額固定報酬", "円", 7),
    ("TITLE_BONUS_EMPEROR", "称号報酬（エンペラー/エンブレス）", 20000, "エンペラー/エンブレス称号の月額固定報酬", "円", 8),
    
    # システム設定
    ("MAX_MEMBER_COUNT", "最大会員数", 50, "システムで管理可能な最大会員数", "名", 1),
    ("SYSTEM_NAME", "システム名", "IROAS BOSS v2", "システムの表示名", None, 2),
    ("VERSION", "バージョン", "2.0.0", "システムのバージョン", None, 3),
]