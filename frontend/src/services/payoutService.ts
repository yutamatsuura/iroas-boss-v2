import { ApiService } from './apiClient';

/**
 * 報酬支払管理サービス
 * P-006: GMOネットバンク振込CSV生成と支払履歴管理
 * 要件定義: 最低支払金額5,000円、振込手数料会社負担
 */

// 支払いステータス
export enum PayoutStatus {
  PENDING = '支払待ち',
  PROCESSING = '処理中',
  COMPLETED = '支払完了',
  FAILED = '支払失敗',
  CANCELLED = 'キャンセル',
}

// 口座種別
export enum AccountType {
  SAVINGS = '普通',
  CURRENT = '当座',
}

// 個人別支払詳細
export interface MemberPayoutDetail {
  id: number;
  memberId: number;
  memberNumber: string;
  memberName: string;
  targetMonth: string;
  totalRewardAmount: number;
  carriedForwardAmount: number; // 前月繰越額
  currentMonthAmount: number; // 当月報酬額
  payoutAmount: number; // 支払予定額
  withholdingTax: number; // 源泉徴収税額
  netPayoutAmount: number; // 実支払額
  status: PayoutStatus;
  bankName?: string;
  bankCode?: string;
  branchName?: string;
  branchCode?: string;
  accountType?: AccountType;
  accountNumber?: string;
  accountHolderName?: string; // カタカナ
  notes?: string;
  paymentDate?: string;
  csvFileName?: string;
  csvExportedAt?: string;
  processedAt?: string;
  errorMessage?: string;
}

// GMOネットバンクCSVレコード
export interface GMOBankTransferRecord {
  bankCode: string; // 銀行コード（4桁）
  branchCode: string; // 支店コード（3桁）
  accountType: '1' | '2'; // 1:普通 2:当座
  accountNumber: string; // 口座番号（7桁以内）
  recipientName: string; // 受取人名（カタカナ30文字以内）
  transferAmount: number; // 振込金額
  feeBearer: '' | '1'; // 手数料負担（空欄:会社負担 1:受取人負担）
  ediInfo: string; // EDI情報（空欄）
}

// 月次支払サマリー
export interface MonthlyPayoutSummary {
  targetMonth: string;
  totalMembers: number; // 全会員数
  payoutEligibleMembers: number; // 支払対象会員数（5,000円以上）
  belowMinimumMembers: number; // 最低支払額未満会員数
  totalRewardAmount: number; // 総報酬額
  totalCarriedForward: number; // 総繰越額
  totalPayoutAmount: number; // 総支払予定額
  totalWithholdingTax: number; // 総源泉徴収額
  totalNetPayoutAmount: number; // 総実支払額
  averagePayoutAmount: number; // 平均支払額
  csvGenerated: boolean; // CSV生成済みフラグ
  csvGeneratedAt?: string;
  paymentCompleted: boolean; // 支払完了フラグ
  paymentCompletedAt?: string;
}

// CSV生成リクエスト
export interface CSVGenerateRequest {
  targetMonth: string; // YYYY-MM形式
  includeCarriedForward?: boolean; // 繰越額を含める
  minimumAmount?: number; // 最低支払額（デフォルト5000円）
  excludeMembers?: number[]; // 除外する会員ID
}

// 支払確定リクエスト
export interface PaymentConfirmRequest {
  targetMonth: string;
  csvFileName: string;
  paymentDate: string;
  confirmedBy: string;
  notes?: string;
}

// 支払履歴
export interface PaymentHistory {
  id: number;
  targetMonth: string;
  csvFileName: string;
  totalMembers: number;
  totalAmount: number;
  paymentDate: string;
  confirmedBy: string;
  status: PayoutStatus;
  createdAt: string;
  processedAt?: string;
  notes?: string;
}

// 繰越管理
export interface CarryForwardManagement {
  memberId: number;
  memberNumber: string;
  memberName: string;
  currentMonth: string;
  previousCarriedForward: number;
  currentMonthReward: number;
  totalAmount: number;
  payoutAmount: number;
  remainingCarryForward: number;
  isPayoutEligible: boolean; // 5,000円以上かどうか
}

export class PayoutService {
  private static readonly BASE_URL = '/payouts';

  /**
   * 月次支払サマリー取得
   */
  static async getMonthlyPayoutSummary(targetMonth: string): Promise<MonthlyPayoutSummary> {
    return ApiService.get<MonthlyPayoutSummary>(`${this.BASE_URL}/summary`, {
      params: { targetMonth },
    });
  }

  /**
   * 会員別支払詳細一覧取得
   */
  static async getMemberPayoutDetails(targetMonth: string): Promise<MemberPayoutDetail[]> {
    return ApiService.get<MemberPayoutDetail[]>(`${this.BASE_URL}/details`, {
      params: { targetMonth },
    });
  }

  /**
   * 繰越管理データ取得
   */
  static async getCarryForwardManagement(targetMonth: string): Promise<CarryForwardManagement[]> {
    return ApiService.get<CarryForwardManagement[]>(`${this.BASE_URL}/carry-forward`, {
      params: { targetMonth },
    });
  }

  /**
   * GMOネットバンクCSV生成
   */
  static async generateGMOBankCSV(request: CSVGenerateRequest): Promise<Blob> {
    const response = await ApiService.post(`${this.BASE_URL}/generate-csv`, request, {
      responseType: 'blob',
    });
    return response as Blob;
  }

  /**
   * GMOネットバンクCSVプレビュー
   */
  static async previewGMOBankCSV(request: CSVGenerateRequest): Promise<{
    records: GMOBankTransferRecord[];
    totalAmount: number;
    recordCount: number;
    estimatedFees: number;
  }> {
    return ApiService.post(`${this.BASE_URL}/preview-csv`, request);
  }

  /**
   * 支払確定処理
   */
  static async confirmPayment(request: PaymentConfirmRequest): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/confirm-payment`, request);
  }

  /**
   * 支払履歴取得
   */
  static async getPaymentHistory(
    startMonth?: string,
    endMonth?: string,
    status?: PayoutStatus
  ): Promise<PaymentHistory[]> {
    return ApiService.get<PaymentHistory[]>(`${this.BASE_URL}/history`, {
      params: { startMonth, endMonth, status },
    });
  }

  /**
   * 個別支払詳細更新
   */
  static async updateMemberPayoutDetail(
    id: number,
    updates: Partial<MemberPayoutDetail>
  ): Promise<MemberPayoutDetail> {
    return ApiService.put<MemberPayoutDetail>(`${this.BASE_URL}/details/${id}`, updates);
  }

  /**
   * 支払除外設定
   */
  static async excludeFromPayout(
    memberId: number,
    targetMonth: string,
    reason: string
  ): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/exclude`, {
      memberId,
      targetMonth,
      reason,
    });
  }

  /**
   * 支払除外解除
   */
  static async includeInPayout(
    memberId: number,
    targetMonth: string,
    reason: string
  ): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/include`, {
      memberId,
      targetMonth,
      reason,
    });
  }

  /**
   * 源泉徴収税計算
   */
  static async calculateWithholdingTax(
    memberId: number,
    targetMonth: string,
    rewardAmount: number
  ): Promise<{
    rewardAmount: number;
    withholdingTaxRate: number;
    withholdingTaxAmount: number;
    netAmount: number;
    taxCalculationDetails: {
      isBusinessType: boolean;
      taxRate: number;
      exemptionAmount: number;
      taxableAmount: number;
    };
  }> {
    return ApiService.post(`${this.BASE_URL}/calculate-tax`, {
      memberId,
      targetMonth,
      rewardAmount,
    });
  }

  /**
   * 口座情報バリデーション
   */
  static async validateBankAccount(
    bankCode: string,
    branchCode: string,
    accountType: AccountType,
    accountNumber: string
  ): Promise<{
    isValid: boolean;
    bankName?: string;
    branchName?: string;
    errorMessage?: string;
  }> {
    return ApiService.post(`${this.BASE_URL}/validate-account`, {
      bankCode,
      branchCode,
      accountType,
      accountNumber,
    });
  }

  /**
   * 支払統計取得
   */
  static async getPayoutStatistics(
    startMonth: string,
    endMonth: string
  ): Promise<{
    monthlyStatistics: Array<{
      month: string;
      totalAmount: number;
      memberCount: number;
      averageAmount: number;
      carryForwardAmount: number;
    }>;
    totalPayout: number;
    totalMembers: number;
    averageMonthlyPayout: number;
    payoutTrend: 'increasing' | 'decreasing' | 'stable';
  }> {
    return ApiService.get(`${this.BASE_URL}/statistics`, {
      params: { startMonth, endMonth },
    });
  }

  /**
   * 支払エラー再処理
   */
  static async retryFailedPayouts(
    targetMonth: string,
    memberIds?: number[]
  ): Promise<{
    retryCount: number;
    successCount: number;
    failedCount: number;
    errors: Array<{
      memberId: number;
      errorMessage: string;
    }>;
  }> {
    return ApiService.post(`${this.BASE_URL}/retry-failed`, {
      targetMonth,
      memberIds,
    });
  }

  /**
   * 支払スケジュール取得
   */
  static async getPaymentSchedule(): Promise<{
    currentMonth: string;
    paymentDeadline: string;
    csvGenerationDeadline: string;
    isPaymentPeriod: boolean;
    nextPaymentDate: string;
    scheduleNotes: string[];
  }> {
    return ApiService.get(`${this.BASE_URL}/schedule`);
  }
}