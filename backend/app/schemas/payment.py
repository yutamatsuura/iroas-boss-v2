"""
決済管理API スキーマ

Phase A-2a: 決済対象API（3.1-3.2）
Phase A-2b: 手動決済・履歴API（3.6-3.7）
Phase B-2a: CSV出力API（3.3-3.4）  
Phase B-2b: 決済結果取込API（3.5）

モックアップP-004の4種類決済方法対応
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from enum import Enum
import io

from app.models.payment import PaymentStatus, PaymentType


class PaymentStatusEnum(str, Enum):
    """決済ステータス（APIスキーマ用）"""
    SUCCESS = "成功"
    FAILED = "失敗"
    PENDING = "保留"
    CANCELLED = "キャンセル"


class PaymentTypeEnum(str, Enum):
    """決済種別"""
    CARD = "カード決済"
    TRANSFER = "口座振替"
    BANK = "銀行振込"
    INFOCART = "インフォカート"


class PaymentTargetResponse(BaseModel):
    """
    決済対象者レスポンススキーマ
    API 3.1-3.2: GET /api/payments/targets/{card|transfer}
    """
    member_id: int = Field(description="会員ID")
    member_number: str = Field(description="会員番号")
    member_name: str = Field(description="会員氏名")
    plan: str = Field(description="加入プラン")
    amount: int = Field(description="決済金額")
    last_payment_date: Optional[datetime] = Field(description="最終決済日")
    payment_method: str = Field(description="決済方法")
    
    # 表示用
    display_name: str = Field(description="表示用氏名（会員番号 - 氏名）")
    formatted_amount: str = Field(description="フォーマット済み金額")
    
    class Config:
        from_attributes = True


class PaymentTargetList(BaseModel):
    """
    決済対象者一覧レスポンススキーマ
    API 3.1-3.2: Univapay CSV出力対象者リスト
    """
    targets: List[PaymentTargetResponse] = Field(description="対象者リスト")
    total_count: int = Field(description="総件数")
    total_amount: int = Field(description="総決済金額")
    target_month: str = Field(description="対象月（YYYY-MM）")
    payment_type: PaymentTypeEnum = Field(description="決済種別")
    export_period: str = Field(description="出力可能期間")


class PaymentExportRequest(BaseModel):
    """
    決済CSV出力リクエストスキーマ
    API 3.3-3.4: POST /api/payments/export/{card|transfer}
    """
    target_month: str = Field(..., regex=r'^\d{4}-\d{2}$', description="対象月（YYYY-MM）")
    export_type: PaymentTypeEnum = Field(..., description="出力種別")
    
    @validator('target_month')
    def validate_target_month(cls, v):
        try:
            year, month = map(int, v.split('-'))
            if not (1 <= month <= 12):
                raise ValueError('無効な月です')
            if year < 2000 or year > 2100:
                raise ValueError('年は2000-2100の範囲で指定してください')
        except ValueError:
            raise ValueError('YYYY-MM形式で入力してください')
        return v


class PaymentImportRequest(BaseModel):
    """
    決済結果取込リクエストスキーマ  
    API 3.5: POST /api/payments/import/result
    """
    file_name: str = Field(..., description="アップロードファイル名")
    file_content: str = Field(..., description="ファイル内容（Base64エンコード）")
    payment_type: PaymentTypeEnum = Field(..., description="決済種別（自動判定も可能）")
    
    @validator('file_name')
    def validate_file_name(cls, v):
        if not v.lower().endswith('.csv'):
            raise ValueError('CSVファイルのみアップロード可能です')
        return v


class PaymentImportResponse(BaseModel):
    """
    決済結果取込レスポンススキーマ
    API 3.5: CSV取込結果
    """
    total_rows: int = Field(description="処理対象行数")
    success_count: int = Field(description="成功件数")
    error_count: int = Field(description="エラー件数")
    skipped_count: int = Field(description="スキップ件数")
    
    # エラー詳細
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="エラー詳細リスト")
    
    # 処理結果サマリー
    imported_payments: List[Dict[str, Any]] = Field(description="取込済み決済リスト")
    
    @property
    def success_rate(self) -> float:
        """成功率算出"""
        if self.total_rows == 0:
            return 0.0
        return round(self.success_count / self.total_rows * 100, 2)


class ManualPaymentRequest(BaseModel):
    """
    手動決済記録リクエストスキーマ
    API 3.6: POST /api/payments/manual
    """
    member_number: str = Field(..., regex=r'^\d{7}$', description="会員番号（7桁）")
    payment_type: PaymentTypeEnum = Field(..., description="決済種別（銀行振込/インフォカート）")
    amount: Decimal = Field(..., gt=0, le=999999, description="決済金額")
    payment_date: datetime = Field(..., description="決済日")
    transaction_id: Optional[str] = Field(default=None, max_length=100, description="取引ID")
    memo: Optional[str] = Field(default=None, max_length=500, description="メモ")
    
    @validator('payment_type')
    def validate_manual_payment_type(cls, v):
        if v not in [PaymentTypeEnum.BANK, PaymentTypeEnum.INFOCART]:
            raise ValueError('手動記録は銀行振込またはインフォカートのみ対応です')
        return v
    
    @validator('payment_date')
    def validate_payment_date(cls, v):
        if v > datetime.now():
            raise ValueError('決済日は過去または現在日時で入力してください')
        return v


class PaymentHistoryResponse(BaseModel):
    """
    決済履歴レスポンススキーマ
    API 3.7: GET /api/payments/history
    """
    id: int = Field(description="履歴ID")
    
    # 会員情報
    member_number: str = Field(description="会員番号")
    member_name: str = Field(description="会員氏名")
    
    # 決済情報
    payment_date: datetime = Field(description="決済日")
    payment_type: PaymentTypeEnum = Field(description="決済種別")
    payment_method: str = Field(description="決済方法")
    amount: Decimal = Field(description="決済金額")
    
    # ステータス
    status: PaymentStatusEnum = Field(description="決済ステータス")
    
    # 外部システム連携
    transaction_id: Optional[str] = Field(description="取引ID")
    external_order_id: Optional[str] = Field(description="外部オーダー番号")
    
    # エラー情報
    error_message: Optional[str] = Field(description="エラーメッセージ")
    
    # その他
    notes: Optional[str] = Field(description="備考・メモ")
    
    # 手動記録情報
    recorded_by: Optional[str] = Field(description="記録者")
    recorded_at: Optional[datetime] = Field(description="記録日時")
    
    # 表示用プロパティ
    formatted_amount: str = Field(description="フォーマット済み金額")
    payment_icon: str = Field(description="決済方法アイコン")
    is_manual_payment: bool = Field(description="手動記録かどうか")
    
    class Config:
        from_attributes = True


class PaymentHistorySearch(BaseModel):
    """
    決済履歴検索リクエストスキーマ
    API 3.7: GET /api/payments/history（検索パラメータ）
    """
    # 検索条件
    member_number: Optional[str] = Field(default=None, regex=r'^\d{7}$', description="会員番号")
    member_name: Optional[str] = Field(default=None, description="会員氏名（部分一致）")
    
    # フィルター条件
    payment_type: Optional[PaymentTypeEnum] = Field(default=None, description="決済種別")
    status: Optional[PaymentStatusEnum] = Field(default=None, description="決済ステータス")
    
    # 期間条件
    payment_date_from: Optional[datetime] = Field(default=None, description="決済日（開始）")
    payment_date_to: Optional[datetime] = Field(default=None, description="決済日（終了）")
    
    # 金額条件
    amount_from: Optional[Decimal] = Field(default=None, ge=0, description="金額（最小）")
    amount_to: Optional[Decimal] = Field(default=None, ge=0, description="金額（最大）")
    
    # ページング
    page: int = Field(default=1, ge=1, description="ページ番号")
    per_page: int = Field(default=20, ge=1, le=100, description="1ページあたりの件数")
    
    # ソート
    sort_by: Optional[str] = Field(default="payment_date", description="ソート項目")
    sort_order: Optional[str] = Field(default="desc", regex=r'^(asc|desc)$', description="ソート順序")


class PaymentSummary(BaseModel):
    """
    決済サマリーレスポンススキーマ
    ダッシュボード表示用
    """
    # 期間統計
    this_month_total: Decimal = Field(description="今月総決済額")
    this_month_count: int = Field(description="今月決済件数")
    last_month_total: Decimal = Field(description="先月総決済額")
    last_month_count: int = Field(description="先月決済件数")
    
    # 方法別統計
    card_total: Decimal = Field(description="カード決済総額")
    transfer_total: Decimal = Field(description="口座振替総額")
    bank_total: Decimal = Field(description="銀行振込総額")
    infocart_total: Decimal = Field(description="インフォカート総額")
    
    # ステータス別統計
    success_count: int = Field(description="成功件数")
    failed_count: int = Field(description="失敗件数")
    pending_count: int = Field(description="保留件数")
    
    # 成功率
    success_rate: float = Field(description="決済成功率（%）")
    
    # 直近の決済失敗
    recent_failures: List[PaymentHistoryResponse] = Field(description="直近の決済失敗（最大5件）")
    
    # 次回決済予定
    next_card_export: Optional[datetime] = Field(description="次回カード決済CSV出力予定日")
    next_transfer_export: Optional[datetime] = Field(description="次回口座振替CSV出力予定日")


class CSVExportResponse(BaseModel):
    """
    CSV出力レスポンススキーマ
    """
    filename: str = Field(description="出力ファイル名")
    record_count: int = Field(description="出力レコード数")
    total_amount: Decimal = Field(description="総金額")
    export_date: datetime = Field(description="出力日時")
    csv_format: str = Field(description="CSVフォーマット種別")
    
    # ファイル情報
    file_size: int = Field(description="ファイルサイズ（バイト）")
    content_type: str = Field(default="text/csv; charset=shift_jis", description="Content-Type")
    
    # Univapay連携情報
    univapay_format: bool = Field(description="Univapay形式かどうか")
    import_instructions: List[str] = Field(description="Univapayへの取込手順")