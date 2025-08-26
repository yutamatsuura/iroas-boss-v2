import { ApiService } from './apiClient';
import { Member } from './memberService';

/**
 * 報酬計算サービス
 * P-005: 7種類のボーナス計算実行と計算結果確認
 * 要件定義: デイリー・タイトル・リファラル・パワー・メンテナンス・セールスアクティビティ・ロイヤルファミリー
 */

// ボーナス種別
export enum BonusType {
  DAILY = 'デイリーボーナス',
  TITLE = 'タイトルボーナス',
  REFERRAL = 'リファラルボーナス',
  POWER = 'パワーボーナス',
  MAINTENANCE = 'メンテナンスボーナス',
  SALES_ACTIVITY = 'セールスアクティビティボーナス',
  ROYAL_FAMILY = 'ロイヤルファミリーボーナス',
}

// タイトル階層
export enum Title {
  START = 'スタート',
  LEADER = 'リーダー',
  SUB_MANAGER = 'サブマネージャー',
  MANAGER = 'マネージャー',
  EXPERT_MANAGER = 'エキスパートマネージャー',
  DIRECTOR = 'ディレクター',
  AREA_DIRECTOR = 'エリアディレクター',
}

// 計算ステータス
export enum CalculationStatus {
  NOT_STARTED = '未実行',
  IN_PROGRESS = '実行中',
  COMPLETED = '完了',
  ERROR = 'エラー',
}

// 個人別ボーナス詳細
export interface MemberBonusDetail {
  memberId: number;
  memberNumber: string;
  memberName: string;
  title: Title;
  bonusType: BonusType;
  amount: number;
  calculationBase?: number;
  rate?: number;
  notes?: string;
}

// ボーナス計算結果
export interface BonusCalculationResult {
  id: number;
  targetMonth: string;
  bonusType: BonusType;
  totalAmount: number;
  memberCount: number;
  status: CalculationStatus;
  calculatedAt: string;
  calculatedBy: string;
  details: MemberBonusDetail[];
  errorMessage?: string;
}

// 月次報酬サマリー
export interface MonthlyRewardSummary {
  targetMonth: string;
  totalRewards: number;
  memberCount: number;
  bonusBreakdown: {
    [BonusType.DAILY]: number;
    [BonusType.TITLE]: number;
    [BonusType.REFERRAL]: number;
    [BonusType.POWER]: number;
    [BonusType.MAINTENANCE]: number;
    [BonusType.SALES_ACTIVITY]: number;
    [BonusType.ROYAL_FAMILY]: number;
  };
  calculationStatus: {
    [key in BonusType]: CalculationStatus;
  };
  lastCalculated: string;
}

// 計算実行リクエスト
export interface CalculationExecuteRequest {
  targetMonth: string; // YYYY-MM形式
  bonusTypes: BonusType[];
  recalculate?: boolean; // 再計算フラグ
}

// 計算履歴
export interface CalculationHistory {
  id: number;
  targetMonth: string;
  executedAt: string;
  executedBy: string;
  bonusTypes: BonusType[];
  totalAmount: number;
  memberCount: number;
  status: CalculationStatus;
  executionTime: number; // 実行時間（秒）
  notes?: string;
}

// タイトル条件
export interface TitleRequirement {
  title: Title;
  personalSalesMin: number; // 個人売上最低金額
  organizationSalesMin: number; // 組織売上最低金額
  directReferralsMin: number; // 直紹介者最低人数
  titleBonus: number; // タイトルボーナス金額
}

// 報酬設定
export interface RewardSettings {
  participationFee: number; // 参加費
  dailyBonusRate: number; // デイリーボーナス率
  referralBonusRate: number; // リファラルボーナス率（50%）
  powerBonusRates: { // パワーボーナス率
    level1: number;
    level2: number;
    level3: number;
    level4: number;
    level5Plus: number;
  };
  maintenanceBonusPerKit: number; // メンテナンスキット1個あたり報酬
  salesActivityBonus: number; // セールスアクティビティボーナス固定額
  royalFamilyBonus: number; // ロイヤルファミリーボーナス固定額
  titleRequirements: TitleRequirement[];
}

export class RewardsService {
  private static readonly BASE_URL = '/rewards';

  /**
   * 月次報酬サマリー取得
   */
  static async getMonthlyRewardSummary(targetMonth: string): Promise<MonthlyRewardSummary> {
    return ApiService.get<MonthlyRewardSummary>(`${this.BASE_URL}/summary`, {
      params: { targetMonth },
    });
  }

  /**
   * ボーナス計算実行
   */
  static async executeCalculation(request: CalculationExecuteRequest): Promise<{
    jobId: string;
    estimatedTime: number;
  }> {
    return ApiService.post(`${this.BASE_URL}/calculate`, request);
  }

  /**
   * 計算実行状況確認
   */
  static async getCalculationStatus(jobId: string): Promise<{
    status: CalculationStatus;
    progress: number; // 0-100
    currentBonusType?: BonusType;
    estimatedRemaining: number; // 残り時間（秒）
  }> {
    return ApiService.get(`${this.BASE_URL}/calculation-status/${jobId}`);
  }

  /**
   * ボーナス計算結果取得
   */
  static async getBonusCalculationResults(
    targetMonth: string,
    bonusType?: BonusType
  ): Promise<BonusCalculationResult[]> {
    return ApiService.get<BonusCalculationResult[]>(`${this.BASE_URL}/results`, {
      params: { targetMonth, bonusType },
    });
  }

  /**
   * 個人別ボーナス詳細取得
   */
  static async getMemberBonusDetail(
    targetMonth: string,
    memberId: number
  ): Promise<MemberBonusDetail[]> {
    return ApiService.get<MemberBonusDetail[]>(`${this.BASE_URL}/member-detail`, {
      params: { targetMonth, memberId },
    });
  }

  /**
   * 計算履歴取得
   */
  static async getCalculationHistory(
    startMonth?: string,
    endMonth?: string,
    limit: number = 50
  ): Promise<CalculationHistory[]> {
    return ApiService.get<CalculationHistory[]>(`${this.BASE_URL}/history`, {
      params: { startMonth, endMonth, limit },
    });
  }

  /**
   * 計算結果CSV出力
   */
  static async exportCalculationResults(
    targetMonth: string,
    bonusType?: BonusType
  ): Promise<Blob> {
    const response = await ApiService.get(`${this.BASE_URL}/export`, {
      params: { targetMonth, bonusType },
      responseType: 'blob',
    });
    return response as Blob;
  }

  /**
   * 計算エラー詳細取得
   */
  static async getCalculationErrors(
    targetMonth: string,
    bonusType?: BonusType
  ): Promise<{
    errors: Array<{
      memberId: number;
      memberNumber: string;
      memberName: string;
      bonusType: BonusType;
      errorMessage: string;
      errorCode: string;
    }>;
  }> {
    return ApiService.get(`${this.BASE_URL}/errors`, {
      params: { targetMonth, bonusType },
    });
  }

  /**
   * 報酬設定取得
   */
  static async getRewardSettings(): Promise<RewardSettings> {
    return ApiService.get<RewardSettings>(`${this.BASE_URL}/settings`);
  }

  /**
   * タイトル自動昇格実行
   */
  static async executeAutoTitlePromotion(targetMonth: string): Promise<{
    promotedMembers: Array<{
      memberId: number;
      memberNumber: string;
      memberName: string;
      oldTitle: Title;
      newTitle: Title;
      reason: string;
    }>;
  }> {
    return ApiService.post(`${this.BASE_URL}/auto-promotion`, { targetMonth });
  }

  /**
   * 計算結果承認
   */
  static async approveCalculationResults(
    targetMonth: string,
    bonusTypes: BonusType[],
    approvedBy: string
  ): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/approve`, {
      targetMonth,
      bonusTypes,
      approvedBy,
    });
  }

  /**
   * デイリーボーナス計算詳細
   */
  static async getDailyBonusCalculation(targetMonth: string): Promise<{
    participationFee: number;
    activeMemberCount: number;
    totalDaysInMonth: number;
    dailyAmount: number; // 1日あたりの金額
    memberDetails: Array<{
      memberId: number;
      memberNumber: string;
      memberName: string;
      activeDays: number;
      bonusAmount: number;
    }>;
  }> {
    return ApiService.get(`${this.BASE_URL}/daily-bonus-detail`, {
      params: { targetMonth },
    });
  }

  /**
   * パワーボーナス組織売上取得
   */
  static async getPowerBonusOrganizationSales(
    targetMonth: string,
    memberId: number
  ): Promise<{
    memberId: number;
    memberNumber: string;
    memberName: string;
    personalSales: number;
    organizationSales: number;
    levelSales: {
      level1: number;
      level2: number;
      level3: number;
      level4: number;
      level5Plus: number;
    };
    bonusCalculation: {
      level1Bonus: number;
      level2Bonus: number;
      level3Bonus: number;
      level4Bonus: number;
      level5PlusBonus: number;
      totalBonus: number;
    };
  }> {
    return ApiService.get(`${this.BASE_URL}/power-bonus-detail`, {
      params: { targetMonth, memberId },
    });
  }
}