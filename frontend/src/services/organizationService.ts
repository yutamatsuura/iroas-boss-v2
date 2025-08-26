import { ApiService } from './apiClient';

/**
 * 組織管理サービス
 * P-003: 組織図ビューア機能
 * 要件定義: ツリー表示、階層確認、組織調整（手動）
 */

// 組織ノード情報
export interface OrganizationNode {
  id: number;
  memberNumber: string;
  name: string;
  title: string;
  status: string;
  level: number;
  parentId?: number;
  uplineId?: number;
  children: OrganizationNode[];
  directReferrals: number;
  totalDownline: number;
  monthlyPersonalSales: number;
  monthlyOrganizationSales: number;
  joinDate: string;
  lastActivityDate: string;
}

// 組織統計情報
export interface OrganizationStats {
  totalMembers: number;
  activeMembers: number;
  maxDepth: number;
  averageDepth: number;
  totalDirectReferrals: number;
  totalOrganizationSales: number;
  topPerformers: Array<{
    memberNumber: string;
    name: string;
    personalSales: number;
    organizationSales: number;
  }>;
}

// 組織検索条件
export interface OrganizationSearchCriteria {
  memberNumber?: string;
  name?: string;
  title?: string;
  minLevel?: number;
  maxLevel?: number;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
}

// 組織調整履歴
export interface OrganizationAdjustment {
  id: number;
  memberNumber: string;
  memberName: string;
  adjustmentType: 'SPONSOR_CHANGE' | 'LEVEL_ADJUSTMENT' | 'WITHDRAWAL';
  oldParentId?: number;
  newParentId?: number;
  oldUplineId?: number;
  newUplineId?: number;
  reason: string;
  adjustedAt: string;
  adjustedBy: string;
  approved: boolean;
  approvedBy?: string;
  approvedAt?: string;
}

export class OrganizationService {
  private static readonly BASE_URL = '/organization';

  /**
   * 組織ツリー全体取得
   */
  static async getOrganizationTree(): Promise<OrganizationNode[]> {
    return ApiService.get<OrganizationNode[]>(`${this.BASE_URL}/tree`);
  }

  /**
   * 特定会員配下の組織取得
   */
  static async getMemberDownline(memberId: number, maxDepth?: number): Promise<OrganizationNode> {
    return ApiService.get<OrganizationNode>(`${this.BASE_URL}/tree/${memberId}`, {
      params: { maxDepth },
    });
  }

  /**
   * 直下メンバー一覧取得
   */
  static async getDirectDownline(memberId: number): Promise<OrganizationNode[]> {
    return ApiService.get<OrganizationNode[]>(`${this.BASE_URL}/member/${memberId}/downline`);
  }

  /**
   * 組織統計情報取得
   */
  static async getOrganizationStats(memberId?: number): Promise<OrganizationStats> {
    return ApiService.get<OrganizationStats>(`${this.BASE_URL}/stats`, {
      params: { memberId },
    });
  }

  /**
   * 組織内検索
   */
  static async searchOrganization(criteria: OrganizationSearchCriteria): Promise<OrganizationNode[]> {
    return ApiService.get<OrganizationNode[]>(`${this.BASE_URL}/search`, {
      params: criteria,
    });
  }

  /**
   * 会員の上位ライン取得
   */
  static async getUpline(memberId: number, levels?: number): Promise<OrganizationNode[]> {
    return ApiService.get<OrganizationNode[]>(`${this.BASE_URL}/member/${memberId}/upline`, {
      params: { levels },
    });
  }

  /**
   * スポンサー変更（組織調整）
   */
  static async changeSponsor(memberId: number, newSponsorId: number, reason: string): Promise<{
    adjustmentId: number;
    success: boolean;
    message: string;
  }> {
    return ApiService.put(`${this.BASE_URL}/member/${memberId}/sponsor`, {
      newSponsorId,
      reason,
    });
  }

  /**
   * 組織レベル調整
   */
  static async adjustLevel(memberId: number, newLevel: number, reason: string): Promise<{
    adjustmentId: number;
    success: boolean;
    message: string;
  }> {
    return ApiService.put(`${this.BASE_URL}/member/${memberId}/level`, {
      newLevel,
      reason,
    });
  }

  /**
   * 組織調整履歴取得
   */
  static async getAdjustmentHistory(
    memberId?: number,
    limit: number = 50
  ): Promise<OrganizationAdjustment[]> {
    return ApiService.get<OrganizationAdjustment[]>(`${this.BASE_URL}/adjustments`, {
      params: { memberId, limit },
    });
  }

  /**
   * 組織調整承認
   */
  static async approveAdjustment(adjustmentId: number): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/adjustments/${adjustmentId}/approve`);
  }

  /**
   * 組織調整拒否
   */
  static async rejectAdjustment(adjustmentId: number, reason: string): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/adjustments/${adjustmentId}/reject`, {
      reason,
    });
  }

  /**
   * 会員退会時の組織調整
   */
  static async handleWithdrawalAdjustment(
    withdrawingMemberId: number,
    adjustmentType: 'MOVE_TO_SPONSOR' | 'MOVE_TO_UPLINE' | 'MANUAL',
    targetParentId?: number
  ): Promise<{
    affectedMembers: number[];
    adjustmentRecords: OrganizationAdjustment[];
    success: boolean;
  }> {
    return ApiService.post(`${this.BASE_URL}/withdrawal-adjustment`, {
      withdrawingMemberId,
      adjustmentType,
      targetParentId,
    });
  }

  /**
   * 組織整合性チェック
   */
  static async checkOrganizationIntegrity(): Promise<{
    overall: 'healthy' | 'warning' | 'critical';
    issues: Array<{
      type: 'ORPHANED_MEMBER' | 'CIRCULAR_REFERENCE' | 'INVALID_LEVEL' | 'MISSING_PARENT';
      memberId: number;
      memberNumber: string;
      memberName: string;
      description: string;
      severity: 'low' | 'medium' | 'high';
    }>;
    recommendations: string[];
    lastCheck: string;
  }> {
    return ApiService.get(`${this.BASE_URL}/integrity-check`);
  }

  /**
   * 組織ツリー再構築
   */
  static async rebuildOrganizationTree(): Promise<{
    success: boolean;
    processedMembers: number;
    fixedIssues: number;
    remainingIssues: number;
    executionTime: number;
  }> {
    return ApiService.post(`${this.BASE_URL}/rebuild`);
  }

  /**
   * 組織パフォーマンス分析
   */
  static async getPerformanceAnalysis(
    memberId: number,
    period: 'monthly' | 'quarterly' | 'yearly' = 'monthly'
  ): Promise<{
    member: {
      memberNumber: string;
      name: string;
      title: string;
    };
    period: string;
    personalPerformance: {
      sales: number;
      growth: number;
      rank: number;
    };
    organizationPerformance: {
      totalSales: number;
      activeMembers: number;
      newRecruits: number;
      promotions: number;
    };
    downlineAnalysis: Array<{
      level: number;
      memberCount: number;
      totalSales: number;
      averageSales: number;
      topPerformer: {
        memberNumber: string;
        name: string;
        sales: number;
      };
    }>;
  }> {
    return ApiService.get(`${this.BASE_URL}/performance/${memberId}`, {
      params: { period },
    });
  }

  /**
   * 組織成長予測
   */
  static async getGrowthProjection(
    memberId: number,
    months: number = 12
  ): Promise<{
    currentStats: OrganizationStats;
    projections: Array<{
      month: number;
      projectedMembers: number;
      projectedSales: number;
      confidence: number;
    }>;
    assumptions: string[];
  }> {
    return ApiService.get(`${this.BASE_URL}/growth-projection/${memberId}`, {
      params: { months },
    });
  }
}