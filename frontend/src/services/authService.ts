import apiClient from './apiClient';
import { UserRole } from '@/contexts/AuthContext';

// API型定義（Phase 21 MLM認証要件準拠）
export interface LoginRequest {
  username: string;
  password: string;
  remember_me?: boolean;
  mfa_code?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    username: string;
    email: string;
    full_name?: string;
    display_name?: string;
    role: UserRole;
    is_active: boolean;
    is_verified: boolean;
    mfa_enabled: boolean;
    last_login_at?: string;
    created_at: string;
  };
  permissions: string[];
  mfa_required?: boolean;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  all_devices?: boolean;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  display_name?: string;
  phone?: string;
}

export interface MFASetupRequest {
  enable: boolean;
  verification_code?: string;
}

export interface MFASetupResponse {
  qr_code: string;
  secret_key: string;
  backup_codes: string[];
  enabled: boolean;
}

export interface SessionInfo {
  id: number;
  ip_address?: string;
  user_agent?: string;
  device_info?: Record<string, any>;
  created_at: string;
  last_used_at?: string;
  expires_at: string;
  is_current: boolean;
}

export interface SessionListResponse {
  sessions: SessionInfo[];
  total: number;
}

export interface SessionRevokeRequest {
  session_ids: number[];
  reason?: string;
}

export interface AccessLogSummary {
  id: number;
  action: string;
  ip_address?: string;
  success: boolean;
  created_at: string;
}

export interface AccessLogListResponse {
  logs: AccessLogSummary[];
  total: number;
  page: number;
  limit: number;
}

/**
 * 認証サービスクラス
 * Phase 21 MLMビジネス要件完全準拠
 */
class AuthService {
  private readonly baseUrl = '/api/v1/auth';

  // トークン管理
  setAuthToken(token: string | null) {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
    }
  }

  /**
   * ログイン
   */
  async login(loginData: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>(`${this.baseUrl}/login`, loginData);
      
      // トークンをAPIクライアントにセット
      this.setAuthToken(response.data.access_token);
      
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  /**
   * ログアウト
   */
  async logout(logoutData: LogoutRequest = {}): Promise<void> {
    try {
      await apiClient.post(`${this.baseUrl}/logout`, logoutData);
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    } finally {
      // トークンをクリア
      this.setAuthToken(null);
    }
  }

  /**
   * トークンリフレッシュ
   */
  async refreshToken(refreshData: RefreshTokenRequest): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>(`${this.baseUrl}/refresh`, refreshData);
      
      // 新しいトークンをAPIクライアントにセット
      this.setAuthToken(response.data.access_token);
      
      return response.data;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // リフレッシュ失敗時はトークンクリア
      this.setAuthToken(null);
      throw error;
    }
  }

  /**
   * 現在のユーザー情報取得
   */
  async getCurrentUser(): Promise<LoginResponse['user'] & { permissions: string[] }> {
    try {
      const response = await apiClient.get<LoginResponse['user'] & { permissions: string[] }>(`${this.baseUrl}/me`);
      return response.data;
    } catch (error) {
      console.error('Get current user failed:', error);
      throw error;
    }
  }

  /**
   * ユーザー情報更新
   */
  async updateCurrentUser(userData: UserUpdateRequest): Promise<LoginResponse['user']> {
    try {
      const response = await apiClient.put<LoginResponse['user']>(`${this.baseUrl}/me`, userData);
      return response.data;
    } catch (error) {
      console.error('Update user failed:', error);
      throw error;
    }
  }

  /**
   * パスワード変更
   */
  async changePassword(passwordData: PasswordChangeRequest): Promise<void> {
    try {
      await apiClient.post(`${this.baseUrl}/change-password`, passwordData);
    } catch (error) {
      console.error('Password change failed:', error);
      throw error;
    }
  }

  /**
   * MFA設定
   */
  async setupMFA(mfaData: MFASetupRequest): Promise<MFASetupResponse> {
    try {
      const response = await apiClient.post<MFASetupResponse>(`${this.baseUrl}/mfa/setup`, mfaData);
      return response.data;
    } catch (error) {
      console.error('MFA setup failed:', error);
      throw error;
    }
  }

  /**
   * MFA認証
   */
  async verifyMFA(code: string, backupCode?: string): Promise<void> {
    try {
      await apiClient.post(`${this.baseUrl}/mfa/verify`, {
        code,
        backup_code: backupCode,
      });
    } catch (error) {
      console.error('MFA verification failed:', error);
      throw error;
    }
  }

  /**
   * セッション一覧取得
   */
  async getSessions(): Promise<SessionListResponse> {
    try {
      const response = await apiClient.get<SessionListResponse>(`${this.baseUrl}/sessions`);
      return response.data;
    } catch (error) {
      console.error('Get sessions failed:', error);
      throw error;
    }
  }

  /**
   * セッション無効化
   */
  async revokeSessions(revokeData: SessionRevokeRequest): Promise<void> {
    try {
      await apiClient.post(`${this.baseUrl}/sessions/revoke`, revokeData);
    } catch (error) {
      console.error('Revoke sessions failed:', error);
      throw error;
    }
  }

  /**
   * アクセスログ取得（管理者専用）
   */
  async getAccessLogs(params: {
    page?: number;
    limit?: number;
    user_id?: number;
    action?: string;
    success?: boolean;
  } = {}): Promise<AccessLogListResponse> {
    try {
      const response = await apiClient.get<AccessLogListResponse>(`${this.baseUrl}/logs/access`, {
        params,
      });
      return response.data;
    } catch (error) {
      console.error('Get access logs failed:', error);
      throw error;
    }
  }

  /**
   * ユーザー作成（管理者専用）
   */
  async createUser(userData: {
    username: string;
    email: string;
    password: string;
    confirm_password: string;
    full_name?: string;
    role?: UserRole;
  }): Promise<LoginResponse['user']> {
    try {
      const response = await apiClient.post<LoginResponse['user']>(`${this.baseUrl}/users`, userData);
      return response.data;
    } catch (error) {
      console.error('Create user failed:', error);
      throw error;
    }
  }

  /**
   * ユーザー更新（管理者専用）
   */
  async updateUser(userId: number, userData: UserUpdateRequest & { role?: UserRole; is_active?: boolean }): Promise<LoginResponse['user']> {
    try {
      const response = await apiClient.put<LoginResponse['user']>(`${this.baseUrl}/users/${userId}`, userData);
      return response.data;
    } catch (error) {
      console.error('Update user failed:', error);
      throw error;
    }
  }

  /**
   * ユーザー詳細取得（管理者専用）
   */
  async getUser(userId: number): Promise<LoginResponse['user'] & { permissions: string[] }> {
    try {
      const response = await apiClient.get<LoginResponse['user'] & { permissions: string[] }>(`${this.baseUrl}/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Get user failed:', error);
      throw error;
    }
  }

  /**
   * ロール権限一覧取得（管理者専用）
   */
  async getRolePermissions(role: UserRole): Promise<{
    role: UserRole;
    permissions: Array<{
      id: number;
      permission_name: string;
      permission_code: string;
      description?: string;
      category: string;
      created_at: string;
    }>;
    total: number;
  }> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/permissions/roles/${role}`);
      return response.data;
    } catch (error) {
      console.error('Get role permissions failed:', error);
      throw error;
    }
  }

  /**
   * 権限初期化（スーパー管理者専用）
   */
  async initializePermissions(): Promise<void> {
    try {
      await apiClient.post(`${this.baseUrl}/permissions/initialize`);
    } catch (error) {
      console.error('Initialize permissions failed:', error);
      throw error;
    }
  }
}

// シングルトンインスタンス
export const authService = new AuthService();
export default authService;