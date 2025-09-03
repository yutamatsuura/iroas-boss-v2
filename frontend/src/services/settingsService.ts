import { ApiService } from './apiClient';

/**
 * マスタ設定サービス
 * P-008: システム固定値の確認表示のみ（変更不可）
 * 要件定義: 参加費、タイトル条件、報酬率などの固定値表示
 */

// システム固定設定
export interface SystemSettings {
  // 基本設定
  systemName: string;
  version: string;
  environment: 'development' | 'staging' | 'production';
  maintenanceMode: boolean;
  
  // 会員設定
  memberNumberDigits: number; // 会員番号桁数（11桁）
  maxMembersPerPage: number;
  defaultMemberStatus: string;
  
  // 参加費設定
  participationFee: {
    heroPlan: number; // ヒーロープラン参加費
    testPlan: number; // テストプラン参加費
    currency: string; // 通貨単位
    taxIncluded: boolean; // 税込みフラグ
  };
  
  // タイトル設定
  titleSettings: {
    titles: Array<{
      name: string;
      order: number;
      requiredPersonalSales: number; // 個人売上要件
      requiredOrganizationSales: number; // 組織売上要件
      requiredDirectReferrals: number; // 直紹介要件
      requiredDownlineManagers: number; // 下位マネージャー要件
      titleBonus: number; // タイトルボーナス金額
      description: string;
    }>;
    autoPromotionEnabled: boolean;
    promotionCheckFrequency: 'daily' | 'weekly' | 'monthly';
  };
  
  // 報酬設定
  rewardSettings: {
    dailyBonusRate: number; // デイリーボーナス率
    referralBonusRate: number; // リファラルボーナス率（50%）
    
    // パワーボーナス率
    powerBonusRates: {
      level1: number;
      level2: number;
      level3: number;
      level4: number;
      level5Plus: number;
    };
    
    // メンテナンスボーナス
    maintenanceBonusPerKit: number; // キット1個あたりの報酬
    
    // セールスアクティビティボーナス
    salesActivityBonus: number; // 固定報酬額
    
    // ロイヤルファミリーボーナス
    royalFamilyBonus: number; // 固定報酬額
    
    // 計算設定
    calculationSchedule: 'monthly'; // 計算頻度
    calculationDate: number; // 月次計算日（25日）
  };
  
  // 支払設定
  payoutSettings: {
    minimumPayoutAmount: number; // 最低支払金額（5,000円）
    bankTransferFee: number; // 振込手数料（会社負担なので0）
    payoutSchedule: 'monthly'; // 支払い頻度
    payoutDate: number; // 月次支払日（15日頃）
    carryForwardEnabled: boolean; // 繰越機能有効
    
    // 源泉徴収設定
    withholdingTax: {
      enabled: boolean;
      businessRate: number; // 事業所得税率
      personalRate: number; // 個人所得税率
      exemptionAmount: number; // 控除額
    };
    
    // GMOネットバンク設定
    gmoSettings: {
      enabled: boolean;
      csvFormat: string;
      encoding: 'Shift-JIS' | 'UTF-8';
      maxRecordsPerFile: number;
    };
  };
  
  // 決済設定
  paymentSettings: {
    // Univapay設定
    univapaySettings: {
      enabled: boolean;
      cardPaymentEnabled: boolean;
      bankTransferEnabled: boolean;
      csvFormat: string;
      encoding: 'Shift-JIS' | 'UTF-8';
      cardPaymentDeadline: number; // 月の締め日（5日）
      bankTransferDeadline: number; // 月の締め日（12日）
      bankTransferExecutionDate: number; // 実行日（27日）
    };
    
    // 手動決済設定
    manualPaymentMethods: string[]; // 銀行振込、インフォカート
    
    // リトライ設定
    retrySettings: {
      enabled: boolean;
      maxRetries: number;
      retryIntervalDays: number;
    };
  };
  
  // セキュリティ設定
  securitySettings: {
    sessionTimeout: number; // セッションタイムアウト（分）
    passwordPolicy: {
      minLength: number;
      requireUppercase: boolean;
      requireLowercase: boolean;
      requireNumbers: boolean;
      requireSymbols: boolean;
    };
    ipWhitelist: string[]; // 許可IPアドレス
    maxLoginAttempts: number; // 最大ログイン試行回数
    lockoutDuration: number; // ロックアウト時間（分）
  };
  
  // データ保持設定
  dataRetentionSettings: {
    activityLogRetentionDays: number; // アクティビティログ保持日数
    paymentHistoryRetentionMonths: number; // 決済履歴保持月数
    memberDataRetentionYears: number; // 会員データ保持年数
    autoCleanupEnabled: boolean; // 自動クリーンアップ有効
  };
  
  // システム制限
  systemLimits: {
    maxMembersTotal: number; // 最大会員数
    maxConcurrentUsers: number; // 最大同時接続ユーザー数
    maxFileUploadSize: number; // 最大ファイルアップロードサイズ（MB）
    maxOrganizationDepth: number; // 最大組織階層深度
  };
  
  // 通知設定
  notificationSettings: {
    emailEnabled: boolean;
    smsEnabled: boolean;
    pushEnabled: boolean;
    adminNotificationEmail: string;
    systemMaintenanceNotice: boolean;
  };
}

// 選択肢マスタデータ
export interface MasterData {
  // 会員ステータス
  memberStatuses: Array<{
    value: string;
    label: string;
    description: string;
    color: string;
  }>;
  
  // 称号
  titles: Array<{
    value: string;
    label: string;
    description: string;
    order: number;
  }>;
  
  // ユーザータイプ
  userTypes: Array<{
    value: string;
    label: string;
    description: string;
  }>;
  
  // 加入プラン
  plans: Array<{
    value: string;
    label: string;
    monthlyFee: number;
    description: string;
    features: string[];
  }>;
  
  // 決済方法
  paymentMethods: Array<{
    value: string;
    label: string;
    description: string;
    processingFee: number;
    enabled: boolean;
  }>;
  
  // 性別
  genders: Array<{
    value: string;
    label: string;
  }>;
  
  // 口座種別
  accountTypes: Array<{
    value: string;
    label: string;
    code: string; // GMOネットバンク用コード
  }>;
  
  // 都道府県
  prefectures: Array<{
    value: string;
    label: string;
    region: string;
  }>;
  
  // アクティビティタイプ
  activityTypes: Array<{
    value: string;
    label: string;
    category: string;
    description: string;
  }>;
}

// システム情報
export interface SystemInfo {
  // バージョン情報
  version: {
    application: string;
    database: string;
    api: string;
    frontend: string;
  };
  
  // 環境情報
  environment: {
    name: string;
    description: string;
    debugMode: boolean;
    logLevel: string;
  };
  
  // リソース情報
  resources: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    dbConnections: number;
    activeUsers: number;
  };
  
  // 統計情報
  statistics: {
    totalMembers: number;
    activeMembers: number;
    totalRewards: number;
    totalPayouts: number;
    lastCalculationDate: string;
    lastPayoutDate: string;
  };
  
  // メンテナンス情報
  maintenance: {
    scheduled: boolean;
    startTime?: string;
    endTime?: string;
    reason?: string;
    affectedServices?: string[];
  };
}

export class SettingsService {
  private static readonly BASE_URL = '/settings';

  /**
   * システム設定取得（読み取り専用）
   */
  static async getSystemSettings(): Promise<SystemSettings> {
    return ApiService.get<SystemSettings>(`${this.BASE_URL}/system`);
  }

  /**
   * マスタデータ取得
   */
  static async getMasterData(): Promise<MasterData> {
    return ApiService.get<MasterData>(`${this.BASE_URL}/master-data`);
  }

  /**
   * システム情報取得
   */
  static async getSystemInfo(): Promise<SystemInfo> {
    return ApiService.get<SystemInfo>(`${this.BASE_URL}/system-info`);
  }

  /**
   * 設定値の説明取得
   */
  static async getSettingDescription(settingKey: string): Promise<{
    key: string;
    name: string;
    description: string;
    type: string;
    defaultValue: any;
    constraints?: {
      min?: number;
      max?: number;
      options?: string[];
      pattern?: string;
    };
    lastModified: string;
    modifiedBy: string;
  }> {
    return ApiService.get(`${this.BASE_URL}/description/${settingKey}`);
  }

  /**
   * タイトル昇格条件詳細取得
   */
  static async getTitleRequirements(): Promise<Array<{
    title: string;
    requirements: {
      personalSales: {
        amount: number;
        period: string; // '3ヶ月連続' など
        description: string;
      };
      organizationSales: {
        amount: number;
        period: string;
        description: string;
      };
      directReferrals: {
        count: number;
        period: string;
        description: string;
      };
      downlineManagers?: {
        count: number;
        minTitle: string;
        description: string;
      };
    };
    benefits: {
      titleBonus: number;
      additionalBenefits: string[];
    };
    examples: string[];
  }>> {
    return ApiService.get(`${this.BASE_URL}/title-requirements`);
  }

  /**
   * 報酬計算ロジック詳細取得
   */
  static async getRewardCalculationLogic(): Promise<{
    dailyBonus: {
      description: string;
      formula: string;
      example: string;
    };
    titleBonus: {
      description: string;
      formula: string;
      example: string;
    };
    referralBonus: {
      description: string;
      formula: string;
      rate: number;
      example: string;
    };
    powerBonus: {
      description: string;
      formula: string;
      rates: { [level: string]: number };
      example: string;
    };
    maintenanceBonus: {
      description: string;
      formula: string;
      perKitAmount: number;
      example: string;
    };
    salesActivityBonus: {
      description: string;
      amount: number;
      conditions: string[];
      example: string;
    };
    royalFamilyBonus: {
      description: string;
      amount: number;
      conditions: string[];
      example: string;
    };
  }> {
    return ApiService.get(`${this.BASE_URL}/reward-logic`);
  }

  /**
   * CSV形式仕様取得
   */
  static async getCSVFormats(): Promise<{
    univapayCardPayment: {
      description: string;
      fileName: string;
      encoding: string;
      columns: Array<{
        name: string;
        description: string;
        type: string;
        maxLength?: number;
        required: boolean;
        example: string;
      }>;
    };
    univapayBankTransfer: {
      description: string;
      fileName: string;
      encoding: string;
      columns: Array<{
        name: string;
        description: string;
        type: string;
        maxLength?: number;
        required: boolean;
        example: string;
      }>;
    };
    gmoBankTransfer: {
      description: string;
      fileName: string;
      encoding: string;
      columns: Array<{
        name: string;
        description: string;
        type: string;
        maxLength?: number;
        required: boolean;
        example: string;
      }>;
    };
  }> {
    return ApiService.get(`${this.BASE_URL}/csv-formats`);
  }

  /**
   * システムヘルスチェック
   */
  static async getSystemHealth(): Promise<{
    overall: 'healthy' | 'warning' | 'critical';
    checks: Array<{
      name: string;
      status: 'healthy' | 'warning' | 'critical';
      message: string;
      lastCheck: string;
      responseTime?: number;
    }>;
    recommendations: string[];
  }> {
    return ApiService.get(`${this.BASE_URL}/health`);
  }

  /**
   * 設定変更履歴取得（読み取り専用）
   */
  static async getSettingHistory(settingKey?: string): Promise<Array<{
    id: number;
    settingKey: string;
    settingName: string;
    oldValue: any;
    newValue: any;
    changedAt: string;
    changedBy: string;
    reason: string;
    approved: boolean;
    approvedBy?: string;
    approvedAt?: string;
  }>> {
    return ApiService.get(`${this.BASE_URL}/history`, {
      params: { settingKey },
    });
  }

  /**
   * API制限情報取得
   */
  static async getApiLimits(): Promise<{
    rateLimit: {
      requestsPerMinute: number;
      requestsPerHour: number;
      requestsPerDay: number;
    };
    quotas: {
      maxFileUploadSize: number;
      maxConcurrentRequests: number;
      maxResponseTime: number;
    };
    restrictions: string[];
  }> {
    return ApiService.get(`${this.BASE_URL}/api-limits`);
  }
}