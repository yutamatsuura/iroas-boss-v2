import { ApiService } from './apiClient';

/**
 * 会員管理サービス
 * P-002: 会員管理機能のAPIサービス
 */

// 会員ステータス
export enum MemberStatus {
  ACTIVE = 'アクティブ',
  INACTIVE = '休会中',
  WITHDRAWN = '退会済',
}

// 称号
export enum Title {
  NONE = '称号なし',
  KNIGHT_DAME = 'ナイト/デイム',
  LORD_LADY = 'ロード/レディ',
  KING_QUEEN = 'キング/クイーン',
  EMPEROR_EMPRESS = 'エンペラー/エンブレス',
}

// ユーザータイプ
export enum UserType {
  NORMAL = '通常',
  CAUTION = '注意',
}

// 加入プラン
export enum Plan {
  HERO = 'ヒーロープラン',
  TEST = 'テストプラン',
}

// 決済方法
export enum PaymentMethod {
  CARD = 'カード決済',
  BANK_TRANSFER = '口座振替',
  BANK_DEPOSIT = '銀行振込',
  INFOCART = 'インフォカート',
}

// 性別
export enum Gender {
  MALE = '男性',
  FEMALE = '女性',
  OTHER = 'その他',
}

// 口座種別
export enum AccountType {
  NORMAL = '普通',
  CURRENT = '当座',
}

// 会員データインターフェース（29項目 + ID）
export interface Member {
  id: number;
  status: MemberStatus;
  memberNumber: string; // 7桁数字
  name: string;
  nameKana: string;
  email: string;
  title: Title;
  userType: UserType;
  plan: Plan;
  paymentMethod: PaymentMethod;
  registrationDate: string;
  withdrawalDate?: string;
  phone?: string;
  gender?: Gender;
  postalCode?: string;
  prefecture?: string;
  address2?: string;
  address3?: string;
  uplineId?: string;
  uplineName?: string;
  referrerId?: string;
  referrerName?: string;
  bankName?: string;
  bankCode?: string;
  branchName?: string;
  branchCode?: string;
  accountNumber?: string;
  yuchoSymbol?: string;
  yuchoNumber?: string;
  accountType?: AccountType;
  notes?: string;
}

// 会員作成/更新用インターフェース
export interface MemberInput {
  status?: MemberStatus;
  memberNumber: string;
  name: string;
  nameKana: string;
  email: string;
  title?: Title;
  userType?: UserType;
  plan: Plan;
  paymentMethod: PaymentMethod;
  registrationDate?: string;
  phone?: string;
  gender?: Gender;
  postalCode?: string;
  prefecture?: string;
  address2?: string;
  address3?: string;
  uplineId?: string;
  uplineName?: string;
  referrerId?: string;
  referrerName?: string;
  bankName?: string;
  bankCode?: string;
  branchName?: string;
  branchCode?: string;
  accountNumber?: string;
  yuchoSymbol?: string;
  yuchoNumber?: string;
  accountType?: AccountType;
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
  totalCount: number;
  activeCount: number;
  inactiveCount: number;
  withdrawnCount: number;
  page: number;
  perPage: number;
  totalPages: number;
}

// スポンサー変更リクエスト
export interface SponsorChangeRequest {
  newSponsorId: string;
  reason?: string;
}

export class MemberService {
  private static readonly BASE_URL = '/members';

  /**
   * 会員一覧取得
   */
  static async getMembers(params?: MemberSearchParams): Promise<MemberListResponse> {
    return ApiService.get<MemberListResponse>(this.BASE_URL, { params });
  }

  /**
   * 会員詳細取得
   */
  static async getMemberById(id: number): Promise<Member> {
    return ApiService.get<Member>(`${this.BASE_URL}/${id}`);
  }

  /**
   * 会員登録
   */
  static async createMember(member: MemberInput): Promise<Member> {
    return ApiService.post<Member>(this.BASE_URL, member);
  }

  /**
   * 会員情報更新
   */
  static async updateMember(id: number, member: Partial<MemberInput>): Promise<Member> {
    return ApiService.put<Member>(`${this.BASE_URL}/${id}`, member);
  }

  /**
   * 退会処理
   */
  static async withdrawMember(id: number, reason?: string): Promise<Member> {
    return ApiService.post<Member>(`${this.BASE_URL}/${id}/withdraw`, { reason });
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