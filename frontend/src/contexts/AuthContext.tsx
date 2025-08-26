import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';
import { authService } from '@/services/authService';

// ユーザーロール定義（Phase 21 MLM要件準拠）
export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  MLM_MANAGER = 'mlm_manager',
  VIEWER = 'viewer',
}

// ユーザー情報型定義
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  display_name?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  mfa_enabled: boolean;
  permissions: string[];
  last_login_at?: string;
  created_at: string;
}

// JWTペイロード型定義
interface JWTPayload {
  sub: string;
  exp: number;
  iat: number;
  type: 'access' | 'refresh';
}

// 認証状態型定義
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  accessToken: string | null;
  refreshToken: string | null;
}

// 認証コンテキスト型定義
interface AuthContextType extends AuthState {
  login: (username: string, password: string, mfaCode?: string) => Promise<void>;
  logout: (allDevices?: boolean) => Promise<void>;
  refreshAuth: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
  updateUserInfo: () => Promise<void>;
}

// 認証コンテキスト作成
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ローカルストレージキー
const ACCESS_TOKEN_KEY = 'iroas_boss_access_token';
const REFRESH_TOKEN_KEY = 'iroas_boss_refresh_token';

/**
 * 認証プロバイダーコンポーネント
 * Phase 21 MLM認証要件完全準拠
 */
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  });

  // トークンの有効性チェック
  const isTokenValid = (token: string): boolean => {
    try {
      const decoded: JWTPayload = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      return decoded.exp > currentTime;
    } catch {
      return false;
    }
  };

  // ログイン処理
  const login = async (username: string, password: string, mfaCode?: string): Promise<void> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));

      const loginData = {
        username,
        password,
        remember_me: true,
        ...(mfaCode && { mfa_code: mfaCode }),
      };

      const response = await authService.login(loginData);

      // トークン保存
      localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);

      setAuthState({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      });
    } catch (error) {
      // ログイン失敗
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        accessToken: null,
        refreshToken: null,
      });
      
      throw error;
    }
  };

  // ログアウト処理
  const logout = async (allDevices: boolean = false): Promise<void> => {
    try {
      if (authState.accessToken) {
        await authService.logout({ all_devices: allDevices });
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // ローカル状態クリア
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        accessToken: null,
        refreshToken: null,
      });
    }
  };

  // トークンリフレッシュ処理
  const refreshAuth = async (): Promise<void> => {
    try {
      const refreshToken = authState.refreshToken || localStorage.getItem(REFRESH_TOKEN_KEY);
      
      if (!refreshToken || !isTokenValid(refreshToken)) {
        throw new Error('Invalid refresh token');
      }

      const response = await authService.refreshToken({ refresh_token: refreshToken });

      // 新しいトークン保存
      localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);

      setAuthState({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      });
    } catch (error) {
      console.error('Token refresh failed:', error);
      await logout();
      throw error;
    }
  };

  // ユーザー情報更新
  const updateUserInfo = async (): Promise<void> => {
    try {
      if (!authState.accessToken) return;
      
      const userInfo = await authService.getCurrentUser();
      setAuthState(prev => ({
        ...prev,
        user: userInfo,
      }));
    } catch (error) {
      console.error('Failed to update user info:', error);
    }
  };

  // 権限チェック（MLMビジネス権限対応）
  const hasPermission = (permission: string): boolean => {
    if (!authState.user) return false;
    if (authState.user.role === UserRole.SUPER_ADMIN) return true;
    return authState.user.permissions.includes(permission);
  };

  // ロールチェック
  const hasRole = (roles: UserRole | UserRole[]): boolean => {
    if (!authState.user) return false;
    const roleArray = Array.isArray(roles) ? roles : [roles];
    return roleArray.includes(authState.user.role);
  };

  // 初期認証状態チェック
  useEffect(() => {
    const initializeAuth = async () => {
      const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (!accessToken || !refreshToken) {
        setAuthState(prev => ({ ...prev, isLoading: false }));
        return;
      }

      try {
        if (isTokenValid(accessToken)) {
          // アクセストークンが有効な場合、ユーザー情報取得
          const userInfo = await authService.getCurrentUser();
          setAuthState({
            user: userInfo,
            isAuthenticated: true,
            isLoading: false,
            accessToken,
            refreshToken,
          });
        } else if (isTokenValid(refreshToken)) {
          // アクセストークンが無効でリフレッシュトークンが有効な場合
          await refreshAuth();
        } else {
          // 両方のトークンが無効
          throw new Error('All tokens invalid');
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          accessToken: null,
          refreshToken: null,
        });
      }
    };

    initializeAuth();
  }, []);

  // トークンの自動リフレッシュ設定
  useEffect(() => {
    if (!authState.accessToken || !authState.isAuthenticated) return;

    const setupTokenRefresh = () => {
      try {
        const decoded: JWTPayload = jwtDecode(authState.accessToken!);
        const currentTime = Date.now() / 1000;
        const timeUntilExpiry = (decoded.exp - currentTime) * 1000;
        
        // トークンの5分前にリフレッシュを実行
        const refreshTime = Math.max(timeUntilExpiry - 5 * 60 * 1000, 0);

        const timeoutId = setTimeout(() => {
          refreshAuth().catch(console.error);
        }, refreshTime);

        return () => clearTimeout(timeoutId);
      } catch (error) {
        console.error('Failed to setup token refresh:', error);
      }
    };

    return setupTokenRefresh();
  }, [authState.accessToken]);

  const contextValue: AuthContextType = {
    ...authState,
    login,
    logout,
    refreshAuth,
    hasPermission,
    hasRole,
    updateUserInfo,
  };

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

/**
 * 認証コンテキストフック
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;