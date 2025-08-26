import { ApiService } from './apiClient';

/**
 * セキュリティ管理サービス
 * Phase 21対応・エンタープライズセキュリティ統合
 */

// セキュリティメトリクス型定義
export interface SecurityMetrics {
  passwordStrength: number;
  mfaEnabled: boolean;
  activeSessions: number;
  lastPasswordChange: string | null;
  recentFailedLogins: number;
  trustedDevices: number;
  securityScore: number;
}

// セキュリティ推奨事項
export interface SecurityRecommendation {
  priority: 'high' | 'medium' | 'low';
  category: string;
  title: string;
  description: string;
  actionUrl: string;
}

// セッション情報
export interface SessionInfo {
  id: string;
  deviceInfo: {
    browser?: string;
    os?: string;
    device?: string;
    trusted?: boolean;
  };
  ipAddress: string;
  isCurrent: boolean;
  lastUsedAt: string;
  createdAt: string;
  location?: {
    country?: string;
    city?: string;
  };
}

// セキュリティアラート
export interface SecurityAlert {
  id: string;
  type: string;
  level: 'info' | 'warning' | 'critical';
  title: string;
  description: string;
  timestamp: string;
  acknowledged: boolean;
  details?: Record<string, any>;
}

// アクセスログ
export interface AccessLog {
  id: string;
  action: string;
  ipAddress: string;
  userAgent: string;
  success: boolean;
  timestamp: string;
  location?: string;
  riskLevel?: string;
  details?: Record<string, any>;
}

// パスワード強度チェック結果
export interface PasswordStrengthResult {
  isValid: boolean;
  score: number;
  errors: string[];
  suggestions: string[];
}

export class SecurityService {
  private static baseUrl = '/api/v1/security';

  // ===================
  // セキュリティ状況取得
  // ===================

  /**
   * セキュリティメトリクス取得
   */
  static async getSecurityMetrics(): Promise<SecurityMetrics> {
    try {
      const response = await ApiService.get<SecurityMetrics>(`${this.baseUrl}/metrics`);
      
      return {
        ...response,
        // フロントエンドで計算する総合セキュリティスコア
        securityScore: this.calculateSecurityScore(response)
      };
    } catch (error) {
      console.error('Failed to fetch security metrics:', error);
      throw error;
    }
  }

  /**
   * セキュリティ推奨事項取得
   */
  static async getSecurityRecommendations(): Promise<SecurityRecommendation[]> {
    try {
      return await ApiService.get<SecurityRecommendation[]>(`${this.baseUrl}/recommendations`);
    } catch (error) {
      console.error('Failed to fetch security recommendations:', error);
      throw error;
    }
  }

  /**
   * アクティブセッション一覧取得
   */
  static async getActiveSessions(): Promise<SessionInfo[]> {
    try {
      const response = await ApiService.get<{ sessions: SessionInfo[] }>(`${this.baseUrl}/sessions`);
      return response.sessions;
    } catch (error) {
      console.error('Failed to fetch active sessions:', error);
      throw error;
    }
  }

  /**
   * セキュリティアラート取得
   */
  static async getSecurityAlerts(): Promise<SecurityAlert[]> {
    try {
      return await ApiService.get<SecurityAlert[]>(`${this.baseUrl}/alerts`);
    } catch (error) {
      console.error('Failed to fetch security alerts:', error);
      throw error;
    }
  }

  /**
   * アクセス履歴取得
   */
  static async getAccessHistory(limit: number = 50): Promise<AccessLog[]> {
    try {
      return await ApiService.get<AccessLog[]>(`${this.baseUrl}/access-history?limit=${limit}`);
    } catch (error) {
      console.error('Failed to fetch access history:', error);
      throw error;
    }
  }

  // ===================
  // セキュリティ操作
  // ===================

  /**
   * セッション削除
   */
  static async revokeSessions(sessionIds: string[], reason?: string): Promise<void> {
    try {
      await ApiService.post(`${this.baseUrl}/sessions/revoke`, {
        session_ids: sessionIds,
        reason: reason || 'ユーザーによる手動削除'
      });
    } catch (error) {
      console.error('Failed to revoke sessions:', error);
      throw error;
    }
  }

  /**
   * 全セッション削除（現在のセッション除く）
   */
  static async revokeAllOtherSessions(): Promise<void> {
    try {
      await ApiService.post(`${this.baseUrl}/sessions/revoke-all-others`);
    } catch (error) {
      console.error('Failed to revoke all other sessions:', error);
      throw error;
    }
  }

  /**
   * パスワード強度チェック
   */
  static async checkPasswordStrength(password: string): Promise<PasswordStrengthResult> {
    try {
      return await ApiService.post<PasswordStrengthResult>(`${this.baseUrl}/password/check-strength`, {
        password
      });
    } catch (error) {
      console.error('Failed to check password strength:', error);
      throw error;
    }
  }

  /**
   * セキュアパスワード生成
   */
  static async generateSecurePassword(length: number = 16): Promise<string> {
    try {
      const response = await ApiService.post<{ password: string }>(`${this.baseUrl}/password/generate`, {
        length
      });
      return response.password;
    } catch (error) {
      console.error('Failed to generate secure password:', error);
      throw error;
    }
  }

  /**
   * セキュリティアラート確認
   */
  static async acknowledgeAlert(alertId: string): Promise<void> {
    try {
      await ApiService.patch(`${this.baseUrl}/alerts/${alertId}/acknowledge`);
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
      throw error;
    }
  }

  /**
   * IP信頼設定
   */
  static async setTrustedDevice(sessionId: string, trusted: boolean): Promise<void> {
    try {
      await ApiService.patch(`${this.baseUrl}/sessions/${sessionId}/trust`, {
        trusted
      });
    } catch (error) {
      console.error('Failed to set device trust:', error);
      throw error;
    }
  }

  // ===================
  // MFA管理
  // ===================

  /**
   * MFA設定開始
   */
  static async initiateMFASetup(): Promise<{ qr_code: string; secret: string; backup_codes: string[] }> {
    try {
      return await ApiService.post(`${this.baseUrl}/mfa/setup`);
    } catch (error) {
      console.error('Failed to initiate MFA setup:', error);
      throw error;
    }
  }

  /**
   * MFA有効化
   */
  static async enableMFA(code: string): Promise<void> {
    try {
      await ApiService.post(`${this.baseUrl}/mfa/enable`, { code });
    } catch (error) {
      console.error('Failed to enable MFA:', error);
      throw error;
    }
  }

  /**
   * MFA無効化
   */
  static async disableMFA(password: string, code: string): Promise<void> {
    try {
      await ApiService.post(`${this.baseUrl}/mfa/disable`, { password, code });
    } catch (error) {
      console.error('Failed to disable MFA:', error);
      throw error;
    }
  }

  /**
   * MFAバックアップコード生成
   */
  static async generateBackupCodes(): Promise<string[]> {
    try {
      const response = await ApiService.post<{ backup_codes: string[] }>(`${this.baseUrl}/mfa/backup-codes`);
      return response.backup_codes;
    } catch (error) {
      console.error('Failed to generate backup codes:', error);
      throw error;
    }
  }

  // ===================
  // ユーティリティ
  // ===================

  /**
   * セキュリティスコア計算
   */
  private static calculateSecurityScore(metrics: Partial<SecurityMetrics>): number {
    let score = 0;
    
    // パスワード強度 (40%)
    if (metrics.passwordStrength) {
      score += (metrics.passwordStrength / 100) * 40;
    }
    
    // MFA有効化 (30%)
    if (metrics.mfaEnabled) {
      score += 30;
    }
    
    // セッション管理 (20%)
    if (metrics.activeSessions !== undefined) {
      // 3セッション以下が理想
      const sessionScore = Math.max(0, 20 - ((metrics.activeSessions - 1) * 5));
      score += Math.min(sessionScore, 20);
    }
    
    // 信頼デバイス (10%)
    if (metrics.trustedDevices && metrics.trustedDevices > 0) {
      score += 10;
    }
    
    return Math.round(Math.min(score, 100));
  }

  /**
   * リスクレベル表示用色取得
   */
  static getRiskLevelColor(level: string): string {
    switch (level.toLowerCase()) {
      case 'critical':
        return '#d32f2f';
      case 'high':
        return '#f57c00';
      case 'medium':
        return '#ffa000';
      case 'low':
      default:
        return '#388e3c';
    }
  }

  /**
   * セキュリティスコア色取得
   */
  static getSecurityScoreColor(score: number): string {
    if (score >= 80) return '#4caf50'; // Green
    if (score >= 60) return '#ff9800'; // Orange
    if (score >= 40) return '#ff5722'; // Deep Orange
    return '#f44336'; // Red
  }

  /**
   * デバイス情報パース
   */
  static parseUserAgent(userAgent: string): { browser: string; os: string; device: string } {
    // 簡易UserAgentパース（本格実装ではライブラリ使用）
    let browser = 'Unknown';
    let os = 'Unknown';
    let device = 'Desktop';
    
    if (userAgent.includes('Chrome')) browser = 'Chrome';
    else if (userAgent.includes('Firefox')) browser = 'Firefox';
    else if (userAgent.includes('Safari')) browser = 'Safari';
    else if (userAgent.includes('Edge')) browser = 'Edge';
    
    if (userAgent.includes('Windows')) os = 'Windows';
    else if (userAgent.includes('MacOS') || userAgent.includes('Mac OS X')) os = 'macOS';
    else if (userAgent.includes('Linux')) os = 'Linux';
    else if (userAgent.includes('Android')) os = 'Android';
    else if (userAgent.includes('iOS')) os = 'iOS';
    
    if (userAgent.includes('Mobile') || userAgent.includes('Android') || userAgent.includes('iOS')) {
      device = 'Mobile';
    } else if (userAgent.includes('Tablet') || userAgent.includes('iPad')) {
      device = 'Tablet';
    }
    
    return { browser, os, device };
  }

  /**
   * 時間差表示（相対時間）
   */
  static getTimeAgo(timestamp: string): string {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMinutes < 1) return 'たった今';
    if (diffMinutes < 60) return `${diffMinutes}分前`;
    if (diffHours < 24) return `${diffHours}時間前`;
    if (diffDays < 30) return `${diffDays}日前`;
    
    return time.toLocaleDateString('ja-JP');
  }
}

export default SecurityService;