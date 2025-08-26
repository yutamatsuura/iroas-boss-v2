"""
報酬計算API スキーマ

Phase C-1a: 報酬計算前提確認API（4.1）
Phase C-1b: 報酬計算実行API（4.2）
Phase C-1c: 計算結果管理API（4.3-4.6）

要件定義書：7種類のボーナス計算
1. デイリーボーナス 2. タイトルボーナス 3. リファラルボーナス 4. パワーボーナス
5. メンテナンスボーナス 6. セールスアクティビティボーナス 7. ロイヤルファミリーボーナス

モックアップP-005対応
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.models.reward import BonusType, CalculationStatus, PaymentStatus


class BonusTypeEnum(str, Enum):
    """ボーナス種別（7種類）"""
    DAILY = "デイリーボーナス"
    TITLE = "タイトルボーナス"
    REFERRAL = "リファラルボーナス"
    POWER = "パワーボーナス"
    MAINTENANCE = "メンテナンスボーナス"
    SALES_ACTIVITY = "セールスアクティビティボーナス"
    ROYAL_FAMILY = "ロイヤルファミリーボーナス"


class CalculationStatusEnum(str, Enum):
    """計算ステータス"""
    RUNNING = "実行中"
    COMPLETED = "完了"
    FAILED = "失敗"
    CANCELLED = "キャンセル"


class PaymentStatusEnum(str, Enum):
    """支払ステータス"""
    PENDING = "支払待ち"
    PAID = "支払済み"
    CARRYOVER = "繰越"
    CANCELLED = "キャンセル"


class RewardPrerequisiteResponse(BaseModel):
    """
    報酬計算前提条件レスポンススキーマ
    API 4.1: GET /api/rewards/check-prerequisites
    """
    # 全体判定
    can_calculate: bool = Field(description="計算実行可能フラグ")
    prerequisite_met: bool = Field(description="前提条件充足フラグ")
    
    # 個別チェック結果
    payment_data_ready: bool = Field(description="決済データ完了フラグ")
    organization_consistent: bool = Field(description="組織図整合性フラグ")
    member_status_updated: bool = Field(description="会員ステータス最新フラグ")
    no_duplicate_calculation: bool = Field(description="重複計算なしフラグ")
    
    # チェック詳細
    payment_completion_rate: float = Field(description="決済完了率（%）")
    pending_payments: int = Field(description="未完了決済数")
    organization_issues: List[str] = Field(description="組織図の問題リスト")
    member_data_issues: List[str] = Field(description="会員データの問題リスト")
    
    # 計算対象統計
    target_members: int = Field(description="計算対象会員数")
    active_members: int = Field(description="アクティブ会員数")
    eligible_for_bonus: Dict[str, int] = Field(description="ボーナス別対象者数")
    
    # 過去計算履歴
    last_calculation_date: Optional[datetime] = Field(description="最終計算日")
    last_calculation_month: Optional[str] = Field(description="最終計算対象月")
    
    # 警告・注意事項
    warnings: List[str] = Field(default_factory=list, description="警告メッセージ")
    blocking_issues: List[str] = Field(default_factory=list, description="計算阻害要因")
    
    # チェック実行情報
    checked_at: datetime = Field(description="チェック実行日時")
    check_duration_seconds: float = Field(description="チェック実行時間（秒）")


class RewardCalculationRequest(BaseModel):
    """
    報酬計算実行リクエストスキーマ
    API 4.2: POST /api/rewards/calculate
    """
    calculation_month: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="計算対象月（YYYY-MM）")
    calculation_type: str = Field(default="all", description="計算タイプ")
    
    # ボーナス選択（部分計算用）
    target_bonuses: Optional[List[BonusTypeEnum]] = Field(default=None, description="対象ボーナス（部分計算時）")
    
    # 計算オプション
    recalculate_existing: bool = Field(default=False, description="既存計算を削除して再計算するか")
    dry_run: bool = Field(default=False, description="テスト計算（実際の保存なし）")
    
    # 対象絞り込み
    target_members: Optional[List[str]] = Field(default=None, description="対象会員番号リスト（全体計算時は未指定）")
    
    @validator('calculation_month')
    def validate_calculation_month(cls, v):
        try:
            year, month = map(int, v.split('-'))
            if not (1 <= month <= 12):
                raise ValueError('無効な月です')
            if year < 2000 or year > 2100:
                raise ValueError('年は2000-2100の範囲で指定してください')
        except ValueError:
            raise ValueError('YYYY-MM形式で入力してください')
        return v
    
    @validator('calculation_type')
    def validate_calculation_type(cls, v):
        valid_types = ['all', 'partial', 'recalculation']
        if v not in valid_types:
            raise ValueError(f'計算タイプは{valid_types}のいずれかで指定してください')
        return v


class RewardCalculationResponse(BaseModel):
    """
    報酬計算実行レスポンススキーマ
    API 4.2: 計算結果サマリー
    """
    # 計算実行情報
    calculation_id: int = Field(description="計算ID")
    calculation_month: str = Field(description="計算対象月")
    calculation_type: str = Field(description="計算タイプ")
    status: CalculationStatusEnum = Field(description="計算ステータス")
    
    # 実行結果サマリー
    total_amount: Decimal = Field(description="総支払額")
    target_member_count: int = Field(description="支払対象者数")
    carryover_member_count: int = Field(description="繰越対象者数（5,000円未満）")
    execution_time_seconds: float = Field(description="実行時間（秒）")
    
    # ボーナス別集計
    bonus_summary: Dict[str, Any] = Field(description="ボーナス別集計結果")
    
    # 統計情報
    payment_stats: Dict[str, Any] = Field(description="支払統計")
    member_stats: Dict[str, Any] = Field(description="会員統計")
    
    # 実行情報
    started_at: datetime = Field(description="計算開始日時")
    completed_at: Optional[datetime] = Field(description="計算完了日時")
    
    # エラー情報
    error_message: Optional[str] = Field(description="エラーメッセージ")
    warnings: List[str] = Field(default_factory=list, description="警告リスト")
    
    class Config:
        from_attributes = True
    
    @property
    def formatted_total_amount(self) -> str:
        """フォーマット済み総額"""
        return f"¥{self.total_amount:,}"
    
    @property
    def is_completed(self) -> bool:
        """計算完了フラグ"""
        return self.status == CalculationStatusEnum.COMPLETED


class RewardHistoryResponse(BaseModel):
    """
    個人別報酬履歴レスポンススキーマ
    API 4.4: GET /api/rewards/results/{id}/member/{mid}
    """
    # 会員情報
    member_id: int = Field(description="会員ID")
    member_number: str = Field(description="会員番号")
    member_name: str = Field(description="会員氏名")
    
    # 計算情報
    calculation_id: int = Field(description="計算ID")
    calculation_month: str = Field(description="計算対象月")
    
    # ボーナス詳細
    bonus_type: BonusTypeEnum = Field(description="ボーナス種別")
    bonus_amount: Decimal = Field(description="ボーナス金額")
    calculation_details: Dict[str, Any] = Field(description="計算詳細データ")
    
    # 支払情報
    payment_status: PaymentStatusEnum = Field(description="支払ステータス")
    payment_date: Optional[datetime] = Field(description="支払日")
    is_payable: bool = Field(description="支払対象フラグ（5,000円以上）")
    
    # 表示用プロパティ
    formatted_amount: str = Field(description="フォーマット済み金額")
    calculation_description: str = Field(description="計算詳細の文字列表現")
    
    # タイムスタンプ
    created_at: datetime = Field(description="作成日時")
    updated_at: datetime = Field(description="更新日時")
    
    class Config:
        from_attributes = True


class MemberRewardSummary(BaseModel):
    """
    個人別報酬サマリーレスポンススキーマ
    API 4.4: 個人の全ボーナス内訳
    """
    # 会員情報
    member_number: str = Field(description="会員番号")
    member_name: str = Field(description="会員氏名")
    calculation_month: str = Field(description="計算対象月")
    
    # 合計金額
    total_reward: Decimal = Field(description="総報酬額")
    payable_amount: Decimal = Field(description="支払対象額（5,000円以上）")
    carryover_amount: Decimal = Field(description="繰越額（5,000円未満）")
    
    # ボーナス別内訳
    bonus_breakdown: List[RewardHistoryResponse] = Field(description="ボーナス別詳細リスト")
    
    # 統計
    bonus_count: int = Field(description="適用ボーナス数")
    zero_bonuses: List[str] = Field(description="0円ボーナス種別リスト")
    
    # 支払情報
    will_be_paid: bool = Field(description="支払予定フラグ")
    payment_scheduled_date: Optional[datetime] = Field(description="支払予定日")
    
    @property
    def formatted_total_reward(self) -> str:
        return f"¥{self.total_reward:,}"
    
    @property
    def formatted_payable_amount(self) -> str:
        return f"¥{self.payable_amount:,}"


class RewardCalculationListResponse(BaseModel):
    """
    報酬計算履歴一覧レスポンススキーマ
    API 4.6: GET /api/rewards/history
    """
    # 計算履歴リスト
    calculations: List[RewardCalculationResponse] = Field(description="計算履歴リスト")
    
    # 統計情報
    total_calculations: int = Field(description="総計算回数")
    successful_calculations: int = Field(description="成功計算回数")
    failed_calculations: int = Field(description="失敗計算回数")
    
    # 期間統計
    this_year_calculations: int = Field(description="今年の計算回数")
    last_calculation: Optional[RewardCalculationResponse] = Field(description="最新計算結果")
    
    # ページネーション
    page: int = Field(description="現在ページ")
    per_page: int = Field(description="ページサイズ")
    total_pages: int = Field(description="総ページ数")


class RewardCalculationDeleteResponse(BaseModel):
    """
    報酬計算削除レスポンススキーマ
    API 4.5: DELETE /api/rewards/results/{id}
    """
    # 削除結果
    success: bool = Field(description="削除成功フラグ")
    calculation_id: int = Field(description="削除された計算ID")
    
    # 削除詳細
    deleted_calculation: RewardCalculationResponse = Field(description="削除された計算詳細")
    deleted_reward_count: int = Field(description="削除された報酬レコード数")
    
    # 影響範囲
    affected_members: List[str] = Field(description="影響を受けた会員リスト")
    
    # 実行情報
    deleted_at: datetime = Field(description="削除日時")
    deleted_by: str = Field(description="削除実行者")
    delete_reason: Optional[str] = Field(description="削除理由")
    
    # 注意事項
    warnings: List[str] = Field(default_factory=list, description="削除に関する警告")


class RewardCalculationProgress(BaseModel):
    """
    報酬計算進行状況レスポンススキーマ
    WebSocket通信用（リアルタイム進捗）
    """
    calculation_id: int = Field(description="計算ID")
    status: CalculationStatusEnum = Field(description="現在ステータス")
    
    # 進行状況
    progress_percentage: float = Field(ge=0, le=100, description="進行率（%）")
    current_step: str = Field(description="現在の処理ステップ")
    current_bonus_type: Optional[BonusTypeEnum] = Field(description="処理中ボーナス種別")
    
    # 処理統計
    processed_members: int = Field(description="処理済み会員数")
    total_members: int = Field(description="総対象会員数")
    current_bonus_amount: Decimal = Field(description="現在までの計算総額")
    
    # 時間情報
    elapsed_seconds: float = Field(description="経過時間（秒）")
    estimated_remaining_seconds: Optional[float] = Field(description="残り推定時間（秒）")
    
    # ログメッセージ
    log_messages: List[str] = Field(description="処理ログメッセージ")
    
    # エラー・警告
    errors: List[str] = Field(default_factory=list, description="エラーリスト")
    warnings: List[str] = Field(default_factory=list, description="警告リスト")
    
    # タイムスタンプ
    updated_at: datetime = Field(description="進捗更新日時")