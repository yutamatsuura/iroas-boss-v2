# -*- coding: utf-8 -*-
"""
カスタム例外クラス定義

要件定義書に基づく業務エラーハンドリング
- データ不正エラー
- ビジネスルール違反エラー  
- バリデーションエラー
"""


class BaseAPIException(Exception):
    """APIの基本例外クラス"""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 400):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class BusinessRuleError(BaseAPIException):
    """ビジネスルール違反エラー"""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_RULE_ERROR"):
        super().__init__(message, error_code, 400)


class DataNotFoundError(BaseAPIException):
    """データ未発見エラー"""
    
    def __init__(self, message: str, error_code: str = "DATA_NOT_FOUND"):
        super().__init__(message, error_code, 404)


class ValidationError(BaseAPIException):
    """バリデーションエラー"""
    
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, error_code, 400)


class DuplicateError(BaseAPIException):
    """重複データエラー"""
    
    def __init__(self, message: str, error_code: str = "DUPLICATE_ERROR"):
        super().__init__(message, error_code, 409)


class CalculationError(BaseAPIException):
    """報酬計算エラー"""
    
    def __init__(self, message: str, error_code: str = "CALCULATION_ERROR"):
        super().__init__(message, error_code, 400)


class CSVProcessingError(BaseAPIException):
    """CSV処理エラー"""
    
    def __init__(self, message: str, error_code: str = "CSV_PROCESSING_ERROR"):
        super().__init__(message, error_code, 400)


class PaymentError(BaseAPIException):
    """決済処理エラー"""
    
    def __init__(self, message: str, error_code: str = "PAYMENT_ERROR"):
        super().__init__(message, error_code, 400)