import { ApiService } from './apiClient';

/**
 * 決済管理サービス
 * P-004: 決済管理機能のAPIサービス
 * Univapay CSV出力、決済結果取込、手動決済記録を統合
 */

// 決済方法
export enum PaymentMethod {
  CARD = 'カード決済',
  BANK_TRANSFER = '口座振替',
  BANK_DEPOSIT = '銀行振込',
  INFOCART = 'インフォカート',
}

// 決済ステータス
export enum PaymentStatus {
  PENDING = '処理中',
  SUCCESS = '成功',
  FAILED = '失敗',
  CANCELLED = 'キャンセル',
}

// 決済対象者データ
export interface PaymentTarget {
  id: number;
  memberNumber: string;
  memberName: string;
  paymentMethod: PaymentMethod;
  amount: number;
  plan: string;
  targetMonth: string;
  status: PaymentStatus;
  createdAt: string;
  processedAt?: string;
  errorMessage?: string;
}

// 決済結果データ
export interface PaymentResult {
  id: number;
  memberNumber: string;
  memberName: string;
  paymentMethod: PaymentMethod;
  amount: number;
  status: PaymentStatus;
  paymentDate: string;
  transactionId?: string;
  errorMessage?: string;
  csvFileName: string;
  importedAt: string;
}

// 手動決済記録
export interface ManualPaymentRecord {
  id: number;
  memberNumber: string;
  memberName: string;
  paymentMethod: PaymentMethod;
  amount: number;
  paymentDate: string;
  confirmedBy: string;
  notes?: string;
  receiptNumber?: string;
  createdAt: string;
}

// CSV出力リクエスト
export interface PaymentExportRequest {
  targetMonth: string; // YYYY-MM形式
  paymentMethod: PaymentMethod;
  includePendingOnly?: boolean;
}

// CSV取込リクエスト
export interface PaymentImportRequest {
  file: File;
  paymentMethod: PaymentMethod;
}

// 決済統計
export interface PaymentStatistics {
  totalTargets: number;
  successCount: number;
  failedCount: number;
  pendingCount: number;
  successRate: number;
  totalAmount: number;
  successAmount: number;
  failedAmount: number;
}

// 月次決済サマリー
export interface MonthlyPaymentSummary {
  month: string;
  cardPayment: PaymentStatistics;
  bankTransfer: PaymentStatistics;
  manualPayments: {
    bankDeposit: PaymentStatistics;
    infocart: PaymentStatistics;
  };
  overall: PaymentStatistics;
}

export class PaymentService {
  private static readonly BASE_URL = '/payments';

  /**
   * 決済対象者一覧取得
   */
  static async getPaymentTargets(targetMonth: string): Promise<PaymentTarget[]> {
    return ApiService.get<PaymentTarget[]>(`${this.BASE_URL}/targets`, {
      params: { targetMonth },
    });
  }

  /**
   * 決済対象者CSV出力
   */
  static async exportPaymentTargets(request: PaymentExportRequest): Promise<Blob> {
    const response = await ApiService.get(`${this.BASE_URL}/export`, {
      params: request,
      responseType: 'blob',
    });
    return response as Blob;
  }

  /**
   * 決済結果CSV取込
   */
  static async importPaymentResults(request: PaymentImportRequest): Promise<{
    successCount: number;
    failedCount: number;
    errors?: string[];
  }> {
    const formData = new FormData();
    formData.append('file', request.file);
    formData.append('paymentMethod', request.paymentMethod);
    
    return ApiService.post(`${this.BASE_URL}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  /**
   * 決済結果一覧取得
   */
  static async getPaymentResults(targetMonth: string): Promise<PaymentResult[]> {
    return ApiService.get<PaymentResult[]>(`${this.BASE_URL}/results`, {
      params: { targetMonth },
    });
  }

  /**
   * 手動決済記録登録
   */
  static async recordManualPayment(record: Omit<ManualPaymentRecord, 'id' | 'createdAt'>): Promise<ManualPaymentRecord> {
    return ApiService.post<ManualPaymentRecord>(`${this.BASE_URL}/manual`, record);
  }

  /**
   * 手動決済記録一覧取得
   */
  static async getManualPaymentRecords(targetMonth: string): Promise<ManualPaymentRecord[]> {
    return ApiService.get<ManualPaymentRecord[]>(`${this.BASE_URL}/manual`, {
      params: { targetMonth },
    });
  }

  /**
   * 手動決済記録更新
   */
  static async updateManualPaymentRecord(
    id: number,
    record: Partial<ManualPaymentRecord>
  ): Promise<ManualPaymentRecord> {
    return ApiService.put<ManualPaymentRecord>(`${this.BASE_URL}/manual/${id}`, record);
  }

  /**
   * 手動決済記録削除
   */
  static async deleteManualPaymentRecord(id: number): Promise<void> {
    return ApiService.delete(`${this.BASE_URL}/manual/${id}`);
  }

  /**
   * 月次決済サマリー取得
   */
  static async getMonthlyPaymentSummary(targetMonth: string): Promise<MonthlyPaymentSummary> {
    return ApiService.get<MonthlyPaymentSummary>(`${this.BASE_URL}/summary`, {
      params: { targetMonth },
    });
  }

  /**
   * 決済履歴取得（複数月対応）
   */
  static async getPaymentHistory(
    startMonth: string,
    endMonth: string,
    paymentMethod?: PaymentMethod
  ): Promise<PaymentResult[]> {
    return ApiService.get<PaymentResult[]>(`${this.BASE_URL}/history`, {
      params: { startMonth, endMonth, paymentMethod },
    });
  }

  /**
   * 決済エラー再処理
   */
  static async retryFailedPayments(targetMonth: string, memberNumbers?: string[]): Promise<{
    retryCount: number;
    successCount: number;
    failedCount: number;
  }> {
    return ApiService.post(`${this.BASE_URL}/retry`, {
      targetMonth,
      memberNumbers,
    });
  }

  /**
   * 決済処理状況確認
   */
  static async getPaymentProcessStatus(targetMonth: string): Promise<{
    cardPaymentDeadline: string;
    bankTransferDeadline: string;
    isCardPaymentPeriod: boolean;
    isBankTransferPeriod: boolean;
    nextProcessDate: string;
  }> {
    return ApiService.get(`${this.BASE_URL}/process-status`, {
      params: { targetMonth },
    });
  }
}