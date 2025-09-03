import { ApiService } from './apiClient';

/**
 * 会員管理サービス
 * P-002: 会員管理機能のAPIサービス
 */

// 会員ステータス
export enum MemberStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  WITHDRAWN = 'WITHDRAWN',
}

// 称号
export enum Title {
  NONE = 'NONE',
  KNIGHT_DAME = 'KNIGHT_DAME',
  LORD_LADY = 'LORD_LADY',
  KING_QUEEN = 'KING_QUEEN',
  EMPEROR_EMPRESS = 'EMPEROR_EMPRESS',
}

// ユーザータイプ
export enum UserType {
  NORMAL = 'NORMAL',
  ATTENTION = 'ATTENTION',
}

// 加入プラン
export enum Plan {
  HERO = 'HERO',
  TEST = 'TEST',
}

// 決済方法
export enum PaymentMethod {
  CARD = 'CARD',
  TRANSFER = 'TRANSFER',
  BANK = 'BANK',
  INFOCART = 'INFOCART',
}

// 性別
export enum Gender {
  MALE = 'MALE',
  FEMALE = 'FEMALE',
  OTHER = 'OTHER',
}

// 口座種別
export enum AccountType {
  ORDINARY = 'ORDINARY',
  CHECKING = 'CHECKING',
}

// 会員データインターフェース（30項目 + ID）
export interface Member {
  id: number;
  status: MemberStatus | string;
  member_number?: string; // APIからのレスポンス用（11桁）
  memberNumber?: string; // フロントエンド互換性（11桁）
  name: string;
  email: string;
  title: Title | string;
  userType?: UserType;
  plan: Plan | string;
  payment_method?: string; // APIからのレスポンス用
  paymentMethod?: PaymentMethod; // フロントエンド互換性
  registration_date?: string; // APIからのレスポンス用
  registrationDate?: string; // フロントエンド互換性
  withdrawalDate?: string;
  phone?: string;
  gender?: Gender;
  postalCode?: string;
  prefecture?: string;
  address2?: string;
  address3?: string;
  uplineId?: string;
  upline_id?: string; // APIからのレスポンス用
  uplineName?: string;
  upline_name?: string; // APIからのレスポンス用
  referrerId?: string;
  referrer_id?: string; // APIからのレスポンス用
  referrerName?: string;
  referrer_name?: string; // APIからのレスポンス用
  bankName?: string;
  bank_name?: string; // APIからのレスポンス用
  bankCode?: string;
  bank_code?: string; // APIからのレスポンス用
  branchName?: string;
  branch_name?: string; // APIからのレスポンス用
  branchCode?: string;
  branch_code?: string; // APIからのレスポンス用
  accountNumber?: string;
  account_number?: string; // APIからのレスポンス用
  yuchoSymbol?: string;
  yucho_symbol?: string; // APIからのレスポンス用
  yuchoNumber?: string;
  yucho_number?: string; // APIからのレスポンス用
  accountType?: AccountType;
  account_type?: AccountType; // APIからのレスポンス用
  notes?: string;
}

// 会員作成/更新用インターフェース
export interface MemberInput {
  status?: MemberStatus;
  member_number: string;
  name: string;
  email: string;
  title?: Title;
  user_type?: UserType;
  plan: Plan;
  payment_method: PaymentMethod;
  registration_date?: string;
  phone?: string;
  gender?: Gender;
  postal_code?: string;
  prefecture?: string;
  address2?: string;
  address3?: string;
  upline_id?: string;
  upline_name?: string;
  referrer_id?: string;
  referrer_name?: string;
  bank_name?: string;
  bank_code?: string;
  branch_name?: string;
  branch_code?: string;
  account_number?: string;
  yucho_symbol?: string;
  yucho_number?: string;
  account_type?: AccountType;
  notes?: string;
}

// 検索条件インターフェース
export interface MemberSearchParams {
  memberNumber?: string;
  name?: string;
  email?: string;
  status?: MemberStatus;
  plan?: Plan;
  paymentMethod?: PaymentMethod;
  page?: number;
  perPage?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// 会員一覧レスポンス
export interface MemberListResponse {
  members: Member[];
  total_count: number;
  active_count: number;
  inactive_count: number;
  withdrawn_count: number;
  totalCount?: number;  // 後方互換性
  activeCount?: number;
  inactiveCount?: number;
  withdrawnCount?: number;
  page?: number;
  perPage?: number;
  totalPages?: number;
}

// スポンサー変更リクエスト
export interface SponsorChangeRequest {
  newSponsorId: string;
  reason?: string;
}

export class MemberService {
  private static readonly BASE_URL = '/v1/members';

  /**
   * 会員一覧取得
   */
  static async getMembers(params?: MemberSearchParams): Promise<MemberListResponse> {
    return ApiService.get<MemberListResponse>(this.BASE_URL, { params });
  }

  /**
   * 会員詳細取得（ID）
   */
  static async getMemberById(id: number): Promise<Member> {
    return ApiService.get<Member>(`${this.BASE_URL}/${id}`);
  }

  /**
   * 会員詳細取得（会員番号）
   */
  static async getMemberByNumber(memberNumber: string): Promise<Member> {
    return ApiService.get<Member>(`${this.BASE_URL}/${memberNumber}`);
  }

  /**
   * 会員登録
   */
  static async createMember(member: MemberInput): Promise<Member> {
    return ApiService.post<Member>(this.BASE_URL, member);
  }

  /**
   * 会員情報更新（ID）
   */
  static async updateMember(id: number, member: Partial<MemberInput>): Promise<Member> {
    return ApiService.put<Member>(`${this.BASE_URL}/${id}`, member);
  }

  /**
   * 会員情報更新（会員番号）
   */
  static async updateMemberByNumber(memberNumber: string, member: Partial<MemberInput>): Promise<Member> {
    return ApiService.put<Member>(`${this.BASE_URL}/${memberNumber}`, member);
  }

  /**
   * 退会処理（ID）
   */
  static async withdrawMember(id: number, reason?: string): Promise<Member> {
    return ApiService.post<Member>(`${this.BASE_URL}/${id}/withdraw`, { reason });
  }

  /**
   * 退会処理（会員番号）
   */
  static async withdrawMemberByNumber(memberNumber: string, reason?: string): Promise<any> {
    return ApiService.post<any>(`${this.BASE_URL}/${memberNumber}/withdraw`, { reason });
  }

  /**
   * スポンサー変更
   */
  static async changeSponsor(id: number, request: SponsorChangeRequest): Promise<Member> {
    return ApiService.put<Member>(`${this.BASE_URL}/${id}/sponsor`, request);
  }

  /**
   * 組織ツリー取得
   */
  static async getOrganizationTree(memberId: number): Promise<any> {
    return ApiService.get(`${this.BASE_URL}/${memberId}/organization`);
  }

  /**
   * CSV出力
   */
  static async exportMembers(params?: MemberSearchParams): Promise<Blob> {
    const response = await ApiService.get(`${this.BASE_URL}/export`, {
      params,
      responseType: 'blob',
    });
    return response as Blob;
  }

  /**
   * CSV取込
   */
  static async importMembers(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    return ApiService.post(`${this.BASE_URL}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
}