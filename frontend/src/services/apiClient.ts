import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * APIクライアント設定
 * FastAPIバックエンドとの通信を管理
 */

// APIベースURL設定（開発環境）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Axiosインスタンス作成
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// リクエストインターセプター
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 認証トークンがある場合はヘッダーに追加（Step 21で実装予定）
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // デバッグ用ログ（開発環境のみ）
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }
    
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // デバッグ用ログ（開発環境のみ）
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.status} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    // エラーハンドリング
    if (error.response) {
      // サーバーからエラーレスポンスが返された場合
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          console.error('[API Error] Bad Request:', data.detail || data.message);
          break;
        case 401:
          console.error('[API Error] Unauthorized');
          // 認証エラーの場合はログイン画面へリダイレクト（Step 21で実装予定）
          // window.location.href = '/login';
          break;
        case 403:
          console.error('[API Error] Forbidden:', data.detail || data.message);
          break;
        case 404:
          console.error('[API Error] Not Found:', data.detail || data.message);
          break;
        case 422:
          console.error('[API Error] Validation Error:', data.detail || data.message);
          break;
        case 500:
          console.error('[API Error] Internal Server Error:', data.detail || data.message);
          break;
        default:
          console.error(`[API Error] Status ${status}:`, data.detail || data.message);
      }
    } else if (error.request) {
      // リクエストは送信されたが、レスポンスがない場合
      console.error('[API Error] No response received:', error.request);
    } else {
      // リクエストの設定中にエラーが発生した場合
      console.error('[API Error] Request setup error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// APIサービスクラス
export class ApiService {
  // GET リクエスト
  static async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.get<T>(url, config);
    return response.data;
  }
  
  // POST リクエスト
  static async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.post<T>(url, data, config);
    return response.data;
  }
  
  // PUT リクエスト
  static async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.put<T>(url, data, config);
    return response.data;
  }
  
  // PATCH リクエスト
  static async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.patch<T>(url, data, config);
    return response.data;
  }
  
  // DELETE リクエスト
  static async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.delete<T>(url, config);
    return response.data;
  }
}

export default apiClient;