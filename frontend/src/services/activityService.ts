import { ApiService } from './apiClient';

/**
 * アクティビティログサービス
 * P-007: システムで実行された全操作の履歴を時系列で確認
 * セキュリティ・監査・操作追跡機能
 */

// アクティビティタイプ
export enum ActivityType {
  // 会員管理
  MEMBER_CREATE = '会員新規登録',
  MEMBER_UPDATE = '会員情報更新',
  MEMBER_DELETE = '会員削除',
  MEMBER_WITHDRAW = '会員退会処理',
  MEMBER_RESTORE = '会員復元',
  
  // 組織管理
  ORGANIZATION_CHANGE = '組織変更',
  SPONSOR_CHANGE = 'スポンサー変更',
  TITLE_PROMOTION = 'タイトル昇格',
  TITLE_DEMOTION = 'タイトル降格',
  
  // 決済管理
  PAYMENT_CSV_EXPORT = '決済CSV出力',
  PAYMENT_CSV_IMPORT = '決済CSV取込',
  PAYMENT_MANUAL_RECORD = '手動決済記録',
  PAYMENT_RETRY = '決済再処理',
  
  // 報酬計算
  REWARD_CALCULATION = '報酬計算実行',
  REWARD_APPROVAL = '報酬計算承認',
  REWARD_CORRECTION = '報酬修正',
  REWARD_CSV_EXPORT = '報酬CSV出力',
  
  // 支払管理
  PAYOUT_CSV_GENERATE = '支払CSV生成',
  PAYOUT_CONFIRM = '支払確定',
  PAYOUT_CANCEL = '支払取消',
  PAYOUT_RETRY = '支払再処理',
  
  // システム管理
  SYSTEM_LOGIN = 'ログイン',
  SYSTEM_LOGOUT = 'ログアウト',
  SYSTEM_BACKUP = 'バックアップ',
  SYSTEM_RESTORE = 'リストア',
  SYSTEM_CONFIG_CHANGE = '設定変更',
  
  // データ管理
  DATA_IMPORT = 'データインポート',
  DATA_EXPORT = 'データエクスポート',
  DATA_MIGRATION = 'データ移行',
  DATA_CLEANUP = 'データクリーンアップ',
  
  // エラー・例外
  SYSTEM_ERROR = 'システムエラー',
  VALIDATION_ERROR = 'バリデーションエラー',
  PERMISSION_ERROR = '権限エラー',
}

// アクティビティレベル
export enum ActivityLevel {
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
  CRITICAL = 'CRITICAL',
  DEBUG = 'DEBUG',
}

// アクティビティステータス
export enum ActivityStatus {
  SUCCESS = '成功',
  FAILED = '失敗',
  IN_PROGRESS = '実行中',
  CANCELLED = 'キャンセル',
}

// アクティビティログエントリ
export interface ActivityLog {
  id: number;
  timestamp: string;
  type: ActivityType;
  level: ActivityLevel;
  status: ActivityStatus;
  userId?: number;
  userName?: string;
  targetId?: number; // 操作対象のID（会員ID、組織IDなど）
  targetType?: string; // 操作対象の種別
  targetName?: string; // 操作対象の名前
  description: string;
  details?: Record<string, any>; // 詳細情報（JSON）
  ipAddress?: string;
  userAgent?: string;
  sessionId?: string;
  duration?: number; // 実行時間（ミリ秒）
  errorMessage?: string;
  stackTrace?: string;
  relatedActivityId?: number; // 関連するアクティビティID
}

// アクティビティ統計
export interface ActivityStatistics {
  totalActivities: number;
  successCount: number;
  failedCount: number;
  errorCount: number;
  topActivityTypes: Array<{
    type: ActivityType;
    count: number;
    percentage: number;
  }>;
  topUsers: Array<{
    userId: number;
    userName: string;
    activityCount: number;
  }>;
  hourlyDistribution: Array<{
    hour: number;
    count: number;
  }>;
  dailyDistribution: Array<{
    date: string;
    count: number;
  }>;
}

// アクティビティ検索パラメータ
export interface ActivitySearchParams {
  startDate?: string;
  endDate?: string;
  type?: ActivityType;
  level?: ActivityLevel;
  status?: ActivityStatus;
  userId?: number;
  targetId?: number;
  targetType?: string;
  keyword?: string; // 説明文での検索
  ipAddress?: string;
  page?: number;
  perPage?: number;
  sortBy?: 'timestamp' | 'type' | 'level' | 'status' | 'userId';
  sortOrder?: 'asc' | 'desc';
}

// アクティビティ検索結果
export interface ActivitySearchResult {
  activities: ActivityLog[];
  totalCount: number;
  page: number;
  perPage: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// アクティビティ作成リクエスト
export interface ActivityCreateRequest {
  type: ActivityType;
  level: ActivityLevel;
  status: ActivityStatus;
  targetId?: number;
  targetType?: string;
  targetName?: string;
  description: string;
  details?: Record<string, any>;
  duration?: number;
  errorMessage?: string;
  relatedActivityId?: number;
}

// セキュリティイベント
export interface SecurityEvent {
  id: number;
  timestamp: string;
  eventType: 'LOGIN_ATTEMPT' | 'LOGIN_SUCCESS' | 'LOGIN_FAILURE' | 'LOGOUT' | 'PERMISSION_VIOLATION' | 'SUSPICIOUS_ACTIVITY';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  userId?: number;
  userName?: string;
  ipAddress: string;
  userAgent: string;
  description: string;
  details?: Record<string, any>;
  resolved: boolean;
  resolvedAt?: string;
  resolvedBy?: string;
}

export class ActivityService {
  private static readonly BASE_URL = '/activities';

  /**
   * アクティビティログ検索
   */
  static async searchActivities(params: ActivitySearchParams): Promise<ActivitySearchResult> {
    return ApiService.get<ActivitySearchResult>(`${this.BASE_URL}/search`, {
      params: {
        ...params,
        page: params.page || 1,
        perPage: params.perPage || 50,
        sortBy: params.sortBy || 'timestamp',
        sortOrder: params.sortOrder || 'desc',
      },
    });
  }

  /**
   * アクティビティログ詳細取得
   */
  static async getActivityDetail(id: number): Promise<ActivityLog> {
    return ApiService.get<ActivityLog>(`${this.BASE_URL}/${id}`);
  }

  /**
   * アクティビティログ作成
   */
  static async createActivity(activity: ActivityCreateRequest): Promise<ActivityLog> {
    return ApiService.post<ActivityLog>(`${this.BASE_URL}`, activity);
  }

  /**
   * アクティビティ統計取得
   */
  static async getActivityStatistics(
    startDate: string,
    endDate: string,
    groupBy?: 'hour' | 'day' | 'week' | 'month'
  ): Promise<ActivityStatistics> {
    return ApiService.get<ActivityStatistics>(`${this.BASE_URL}/statistics`, {
      params: { startDate, endDate, groupBy: groupBy || 'day' },
    });
  }

  /**
   * 最新アクティビティ取得
   */
  static async getRecentActivities(limit: number = 20): Promise<ActivityLog[]> {
    return ApiService.get<ActivityLog[]>(`${this.BASE_URL}/recent`, {
      params: { limit },
    });
  }

  /**
   * ユーザー別アクティビティ履歴
   */
  static async getUserActivities(
    userId: number,
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ): Promise<ActivityLog[]> {
    return ApiService.get<ActivityLog[]>(`${this.BASE_URL}/user/${userId}`, {
      params: { startDate, endDate, limit },
    });
  }

  /**
   * 対象別アクティビティ履歴
   */
  static async getTargetActivities(
    targetType: string,
    targetId: number,
    limit: number = 50
  ): Promise<ActivityLog[]> {
    return ApiService.get<ActivityLog[]>(`${this.BASE_URL}/target`, {
      params: { targetType, targetId, limit },
    });
  }

  /**
   * エラーログ取得
   */
  static async getErrorLogs(
    startDate?: string,
    endDate?: string,
    severity?: ActivityLevel,
    limit: number = 100
  ): Promise<ActivityLog[]> {
    return ApiService.get<ActivityLog[]>(`${this.BASE_URL}/errors`, {
      params: { startDate, endDate, severity, limit },
    });
  }

  /**
   * セキュリティイベント取得
   */
  static async getSecurityEvents(
    startDate?: string,
    endDate?: string,
    resolved?: boolean,
    severity?: string,
    limit: number = 100
  ): Promise<SecurityEvent[]> {
    return ApiService.get<SecurityEvent[]>(`${this.BASE_URL}/security-events`, {
      params: { startDate, endDate, resolved, severity, limit },
    });
  }

  /**
   * アクティビティログ削除（管理者のみ）
   */
  static async deleteActivity(id: number, reason: string): Promise<void> {
    return ApiService.delete(`${this.BASE_URL}/${id}`, {
      data: { reason },
    });
  }

  /**
   * アクティビティログ一括削除（管理者のみ）
   */
  static async bulkDeleteActivities(
    ids: number[],
    reason: string
  ): Promise<{ deletedCount: number }> {
    return ApiService.post(`${this.BASE_URL}/bulk-delete`, {
      ids,
      reason,
    });
  }

  /**
   * アクティビティログエクスポート
   */
  static async exportActivities(
    params: ActivitySearchParams,
    format: 'csv' | 'json' = 'csv'
  ): Promise<Blob> {
    const response = await ApiService.get(`${this.BASE_URL}/export`, {
      params: { ...params, format },
      responseType: 'blob',
    });
    return response as Blob;
  }

  /**
   * ログ保持設定取得
   */
  static async getLogRetentionSettings(): Promise<{
    retentionDays: number;
    autoCleanupEnabled: boolean;
    maxLogSize: number;
    compressionEnabled: boolean;
    archiveEnabled: boolean;
  }> {
    return ApiService.get(`${this.BASE_URL}/retention-settings`);
  }

  /**
   * ログクリーンアップ実行（管理者のみ）
   */
  static async executeLogCleanup(
    olderThanDays: number,
    dryRun: boolean = true
  ): Promise<{
    totalLogs: number;
    eligibleForDeletion: number;
    deletedLogs?: number;
    spaceFreed?: number;
  }> {
    return ApiService.post(`${this.BASE_URL}/cleanup`, {
      olderThanDays,
      dryRun,
    });
  }

  /**
   * アクティビティタイプ一覧取得
   */
  static async getActivityTypes(): Promise<Array<{
    type: ActivityType;
    description: string;
    category: string;
  }>> {
    return ApiService.get(`${this.BASE_URL}/types`);
  }

  /**
   * システムヘルス監視
   */
  static async getSystemHealth(): Promise<{
    status: 'healthy' | 'warning' | 'critical';
    lastActivity: string;
    errorRate: number;
    averageResponseTime: number;
    activeUsers: number;
    systemLoad: number;
    issues: Array<{
      type: string;
      message: string;
      severity: string;
      timestamp: string;
    }>;
  }> {
    return ApiService.get(`${this.BASE_URL}/system-health`);
  }

  /**
   * 監査レポート生成
   */
  static async generateAuditReport(
    startDate: string,
    endDate: string,
    includeDetails: boolean = false
  ): Promise<{
    reportId: string;
    generatedAt: string;
    period: { startDate: string; endDate: string };
    summary: {
      totalActivities: number;
      uniqueUsers: number;
      errorCount: number;
      securityEvents: number;
    };
    downloadUrl: string;
  }> {
    return ApiService.post(`${this.BASE_URL}/audit-report`, {
      startDate,
      endDate,
      includeDetails,
    });
  }
}