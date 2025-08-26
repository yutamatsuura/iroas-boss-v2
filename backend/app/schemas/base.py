"""
基本的なPydanticスキーマ

全APIで共通利用するベーススキーマを定義
- レスポンス基底クラス
- ページネーション
- エラーハンドリング
"""

from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

# 汎用型変数
DataT = TypeVar('DataT')


class BaseResponse(BaseModel):
    """
    基本レスポンススキーマ
    全APIレスポンスの基底クラス
    """
    success: bool = Field(default=True, description="処理成功フラグ")
    message: Optional[str] = Field(default=None, description="メッセージ")
    timestamp: datetime = Field(default_factory=datetime.now, description="レスポンス生成時刻")
    
    class Config:
        # JSONレスポンス時の日時フォーマット
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DataResponse(BaseResponse, Generic[DataT]):
    """
    データ付きレスポンススキーマ
    単一データ返却用
    """
    data: DataT = Field(description="レスポンスデータ")


class ListResponse(BaseResponse, Generic[DataT]):
    """
    リスト付きレスポンススキーマ
    複数データ返却用（ページネーション対応）
    """
    data: List[DataT] = Field(description="データリスト")
    pagination: Optional["PaginationMeta"] = Field(default=None, description="ページネーション情報")


class PaginationMeta(BaseModel):
    """
    ページネーション情報
    リスト取得APIで使用
    """
    page: int = Field(ge=1, description="現在のページ番号（1から開始）")
    per_page: int = Field(ge=1, le=1000, description="1ページあたりの件数")
    total: int = Field(ge=0, description="総件数")
    total_pages: int = Field(ge=0, description="総ページ数")
    has_next: bool = Field(description="次のページが存在するか")
    has_prev: bool = Field(description="前のページが存在するか")
    
    @classmethod
    def create(cls, page: int, per_page: int, total: int) -> "PaginationMeta":
        """ページネーション情報を生成"""
        total_pages = (total + per_page - 1) // per_page
        return cls(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class ErrorResponse(BaseResponse):
    """
    エラーレスポンススキーマ
    API例外時のレスポンス
    """
    success: bool = Field(default=False, description="処理成功フラグ（常にFalse）")
    error_code: Optional[str] = Field(default=None, description="エラーコード")
    error_type: Optional[str] = Field(default=None, description="エラー種別")
    details: Optional[Dict[str, Any]] = Field(default=None, description="詳細エラー情報")
    
    @classmethod
    def create_validation_error(cls, errors: List[Dict[str, Any]]) -> "ErrorResponse":
        """バリデーションエラーレスポンス生成"""
        return cls(
            message="入力データにエラーがあります",
            error_code="VALIDATION_ERROR",
            error_type="validation",
            details={"errors": errors}
        )
    
    @classmethod
    def create_not_found_error(cls, resource_type: str, identifier: str) -> "ErrorResponse":
        """リソース未発見エラーレスポンス生成"""
        return cls(
            message=f"{resource_type}が見つかりません",
            error_code="NOT_FOUND",
            error_type="not_found",
            details={"resource_type": resource_type, "identifier": identifier}
        )
    
    @classmethod
    def create_business_error(cls, message: str, error_code: str = "BUSINESS_ERROR") -> "ErrorResponse":
        """ビジネスロジックエラーレスポンス生成"""
        return cls(
            message=message,
            error_code=error_code,
            error_type="business",
        )


class FileResponse(BaseResponse):
    """
    ファイルダウンロードレスポンススキーマ
    CSV出力等で使用
    """
    filename: str = Field(description="ファイル名")
    content_type: str = Field(description="Content-Type")
    size: Optional[int] = Field(default=None, description="ファイルサイズ（バイト）")


class BulkOperationResponse(BaseResponse):
    """
    一括操作レスポンススキーマ
    CSV取込、バックアップ等で使用
    """
    total_count: int = Field(ge=0, description="処理対象総数")
    success_count: int = Field(ge=0, description="成功件数") 
    error_count: int = Field(ge=0, description="エラー件数")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="エラー詳細リスト")
    
    def add_error(self, row: int, field: str, message: str) -> None:
        """エラー情報追加"""
        self.errors.append({
            "row": row,
            "field": field,
            "message": message
        })
    
    @property
    def success_rate(self) -> float:
        """成功率算出"""
        if self.total_count == 0:
            return 0.0
        return round(self.success_count / self.total_count * 100, 2)


# Pydantic v2 対応
ListResponse.model_rebuild()
DataResponse.model_rebuild()