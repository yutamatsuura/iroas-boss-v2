"""
データ管理API スキーマ

Phase E-1a: データ管理API群（8.1-8.4）
- インポート・エクスポート・バックアップ・リストア機能
- 完全独立、いつでも実装可能

モックアップP-009対応
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from enum import Enum
import base64


class ImportFormatEnum(str, Enum):
    """インポート形式"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class ExportFormatEnum(str, Enum):
    """エクスポート形式"""
    CSV = "csv" 
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"


class BackupTypeEnum(str, Enum):
    """バックアップ種別"""
    FULL = "full"       # 全データ
    MEMBERS = "members"  # 会員データのみ
    PAYMENTS = "payments" # 決済データのみ
    REWARDS = "rewards"   # 報酬データのみ
    SETTINGS = "settings" # 設定データのみ


class ImportStatusEnum(str, Enum):
    """インポート状況"""
    PENDING = "待機中"
    PROCESSING = "処理中"
    COMPLETED = "完了"
    FAILED = "失敗"
    CANCELLED = "キャンセル"


class DataImportRequest(BaseModel):
    """
    データインポートリクエストスキーマ
    API 8.1: POST /api/data/import/members
    """
    # ファイル情報
    file_name: str = Field(..., description="アップロードファイル名")
    file_content: str = Field(..., description="ファイル内容（Base64エンコード）")
    file_format: ImportFormatEnum = Field(..., description="ファイル形式")
    
    # インポート設定
    import_type: str = Field(..., description="インポート種別（members/payments/rewards等）")
    encoding: str = Field(default="utf-8", description="文字エンコーディング")
    
    # オプション設定
    skip_header: bool = Field(default=True, description="ヘッダー行をスキップするか")
    update_existing: bool = Field(default=False, description="既存データを更新するか（新規追加のみならFalse）")
    validate_only: bool = Field(default=False, description="バリデーションのみ実行（実際のインポートは行わない）")
    
    # 重複処理
    duplicate_handling: str = Field(default="skip", description="重複データの処理方法")
    
    # エラー処理
    stop_on_error: bool = Field(default=False, description="エラー発生時に処理を停止するか")
    max_errors: int = Field(default=100, description="許容する最大エラー数")
    
    @validator('file_name')
    def validate_file_name(cls, v):
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.json']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'サポートされているファイル形式: {", ".join(allowed_extensions)}')
        return v
    
    @validator('file_content')
    def validate_file_content(cls, v):
        try:
            # Base64デコードテスト
            base64.b64decode(v)
        except Exception:
            raise ValueError('ファイル内容はBase64エンコード形式で指定してください')
        return v
    
    @validator('duplicate_handling')
    def validate_duplicate_handling(cls, v):
        valid_options = ['skip', 'update', 'error']
        if v not in valid_options:
            raise ValueError(f'重複処理方法は{valid_options}のいずれかで指定してください')
        return v


class DataImportResponse(BaseModel):
    """
    データインポートレスポンススキーマ
    API 8.1: インポート結果
    """
    # インポート結果
    import_id: int = Field(description="インポートID")
    status: ImportStatusEnum = Field(description="インポート状況")
    
    # 処理結果サマリー
    total_rows: int = Field(description="総行数")
    processed_rows: int = Field(description="処理行数")
    success_count: int = Field(description="成功件数")
    error_count: int = Field(description="エラー件数")
    skipped_count: int = Field(description="スキップ件数")
    updated_count: int = Field(description="更新件数")
    
    # エラー詳細
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="エラー詳細リスト")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="警告リスト")
    
    # 処理時間
    started_at: datetime = Field(description="処理開始日時")
    completed_at: Optional[datetime] = Field(description="処理完了日時")
    processing_time_seconds: Optional[float] = Field(description="処理時間（秒）")
    
    # インポートされたデータサマリー
    imported_data_summary: Dict[str, Any] = Field(description="インポートデータサマリー")
    
    @property
    def success_rate(self) -> float:
        """成功率算出"""
        if self.total_rows == 0:
            return 0.0
        return round(self.success_count / self.total_rows * 100, 2)
    
    @property
    def is_completed(self) -> bool:
        """完了判定"""
        return self.status in [ImportStatusEnum.COMPLETED, ImportStatusEnum.FAILED]


class DataExportRequest(BaseModel):
    """
    データエクスポートリクエストスキーマ
    各種データのCSV/Excel出力用
    """
    # エクスポート対象
    export_type: str = Field(..., description="エクスポート種別")
    export_format: ExportFormatEnum = Field(default=ExportFormatEnum.CSV, description="出力形式")
    encoding: str = Field(default="utf-8", description="文字エンコーディング")
    
    # フィルター条件
    date_from: Optional[datetime] = Field(default=None, description="期間（開始）")
    date_to: Optional[datetime] = Field(default=None, description="期間（終了）")
    member_filter: Optional[List[str]] = Field(default=None, description="対象会員番号リスト")
    status_filter: Optional[List[str]] = Field(default=None, description="ステータスフィルター")
    
    # 出力オプション
    include_headers: bool = Field(default=True, description="ヘッダー行を含めるか")
    include_deleted: bool = Field(default=False, description="削除済みデータを含めるか")
    max_records: int = Field(default=10000, description="最大出力件数")
    
    # フォーマット設定
    date_format: str = Field(default="%Y-%m-%d", description="日付フォーマット")
    number_format: str = Field(default="comma", description="数値フォーマット")


class BackupRequest(BaseModel):
    """
    バックアップ実行リクエストスキーマ
    API 8.2: POST /api/data/backup
    """
    # バックアップ設定
    backup_type: BackupTypeEnum = Field(..., description="バックアップ種別")
    backup_name: Optional[str] = Field(default=None, description="バックアップ名（未指定時は自動生成）")
    description: Optional[str] = Field(default=None, max_length=500, description="バックアップ説明")
    
    # 圧縮設定
    compression: bool = Field(default=True, description="圧縮するか")
    encryption: bool = Field(default=False, description="暗号化するか")
    
    # 対象期間（部分バックアップ用）
    date_from: Optional[datetime] = Field(default=None, description="バックアップ対象期間（開始）")
    date_to: Optional[datetime] = Field(default=None, description="バックアップ対象期間（終了）")
    
    @validator('backup_name')
    def validate_backup_name(cls, v):
        if v and len(v.strip()) == 0:
            raise ValueError('バックアップ名は空文字にできません')
        return v


class BackupResponse(BaseModel):
    """
    バックアップレスポンススキーマ
    API 8.2-8.3: バックアップ結果・一覧
    """
    # バックアップ基本情報
    backup_id: int = Field(description="バックアップID")
    backup_name: str = Field(description="バックアップ名")
    backup_type: BackupTypeEnum = Field(description="バックアップ種別")
    description: Optional[str] = Field(description="バックアップ説明")
    
    # ファイル情報
    file_name: str = Field(description="バックアップファイル名")
    file_size_bytes: int = Field(description="ファイルサイズ（バイト）")
    file_path: str = Field(description="ファイルパス")
    
    # 圧縮・暗号化情報
    is_compressed: bool = Field(description="圧縮フラグ")
    is_encrypted: bool = Field(description="暗号化フラグ")
    compression_ratio: Optional[float] = Field(description="圧縮率（%）")
    
    # バックアップ内容統計
    total_records: int = Field(description="総レコード数")
    table_counts: Dict[str, int] = Field(description="テーブル別レコード数")
    
    # 実行情報
    created_at: datetime = Field(description="作成日時")
    created_by: str = Field(description="作成者")
    backup_duration_seconds: float = Field(description="バックアップ実行時間（秒）")
    
    # ステータス
    status: str = Field(description="バックアップ状況")
    error_message: Optional[str] = Field(description="エラーメッセージ")
    
    @property
    def formatted_file_size(self) -> str:
        """フォーマット済みファイルサイズ"""
        if self.file_size_bytes < 1024:
            return f"{self.file_size_bytes} B"
        elif self.file_size_bytes < 1024 * 1024:
            return f"{self.file_size_bytes / 1024:.1f} KB"
        elif self.file_size_bytes < 1024 * 1024 * 1024:
            return f"{self.file_size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    class Config:
        from_attributes = True


class RestoreRequest(BaseModel):
    """
    リストア実行リクエストスキーマ
    API 8.4: POST /api/data/restore/{id}
    """
    # リストア設定
    restore_type: str = Field(default="full", description="リストア種別")
    overwrite_existing: bool = Field(default=False, description="既存データを上書きするか")
    
    # 対象テーブル選択（部分リストア用）
    target_tables: Optional[List[str]] = Field(default=None, description="対象テーブルリスト")
    
    # 確認設定
    confirmation_token: str = Field(..., description="確認トークン（危険操作のため必須）")
    restore_reason: str = Field(..., min_length=1, max_length=500, description="リストア理由")
    
    # オプション
    backup_current_before_restore: bool = Field(default=True, description="リストア前に現在データをバックアップするか")
    validate_before_restore: bool = Field(default=True, description="リストア前にバックアップファイルを検証するか")


class RestoreResponse(BaseModel):
    """
    リストアレスポンススキーマ
    API 8.4: リストア結果
    """
    # リストア結果
    restore_id: int = Field(description="リストアID")
    backup_id: int = Field(description="使用したバックアップID")
    status: str = Field(description="リストア状況")
    
    # 処理結果
    total_records_restored: int = Field(description="復元総レコード数")
    table_restore_counts: Dict[str, int] = Field(description="テーブル別復元レコード数")
    
    # 事前バックアップ情報
    pre_restore_backup_id: Optional[int] = Field(description="事前バックアップID")
    
    # 実行情報
    started_at: datetime = Field(description="リストア開始日時")
    completed_at: Optional[datetime] = Field(description="リストア完了日時")
    restore_duration_seconds: Optional[float] = Field(description="リストア実行時間（秒）")
    restored_by: str = Field(description="リストア実行者")
    restore_reason: str = Field(description="リストア理由")
    
    # 結果詳細
    success_count: int = Field(description="成功件数")
    error_count: int = Field(description="エラー件数")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="エラー詳細")
    
    # 警告・注意事項
    warnings: List[str] = Field(default_factory=list, description="警告リスト")
    
    @property
    def success_rate(self) -> float:
        """成功率算出"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return round(self.success_count / total * 100, 2)


class DataIntegrityCheckResponse(BaseModel):
    """
    データ整合性チェックレスポンススキーマ
    システム健全性確認用
    """
    # チェック結果
    overall_status: str = Field(description="全体ステータス")
    check_passed: bool = Field(description="チェック合格フラグ")
    
    # テーブル別チェック結果
    table_checks: Dict[str, Dict[str, Any]] = Field(description="テーブル別チェック結果")
    
    # 整合性問題
    integrity_issues: List[Dict[str, Any]] = Field(description="整合性問題リスト")
    missing_relations: List[Dict[str, Any]] = Field(description="欠損リレーション")
    orphaned_records: List[Dict[str, Any]] = Field(description="孤立レコード")
    
    # 統計情報
    total_records: int = Field(description="総レコード数")
    total_tables: int = Field(description="総テーブル数")
    issues_found: int = Field(description="発見された問題数")
    
    # 実行情報
    checked_at: datetime = Field(description="チェック実行日時")
    check_duration_seconds: float = Field(description="チェック実行時間（秒）")