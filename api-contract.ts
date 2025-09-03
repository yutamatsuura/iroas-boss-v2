/**
 * 会員管理API 型定義契約書
 * フロントエンド・バックエンドで共有する型定義
 * 
 * ⚠️ この型定義を変更する場合は、フロントエンド・バックエンド両方を更新すること
 */

// ===== 基本型定義 =====

export enum MemberStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  WITHDRAWN = 'WITHDRAWN'
}

export enum Title {
  NONE = 'NONE',
  KNIGHT_DAME = 'KNIGHT_DAME',
  LORD_LADY = 'LORD_LADY',
  KING_QUEEN = 'KING_QUEEN',
  EMPEROR_EMPRESS = 'EMPEROR_EMPRESS'
}

export enum UserType {
  NORMAL = 'NORMAL',
  ATTENTION = 'ATTENTION'
}

export enum Plan {
  HERO = 'HERO',
  BASIC = 'BASIC',
  TEST = 'TEST'
}

export enum PaymentMethod {
  CARD = 'CARD',
  TRANSFER = 'TRANSFER',
  BANK = 'BANK',
  INFOCART = 'INFOCART'
}

export enum Gender {
  MALE = 'MALE',
  FEMALE = 'FEMALE',
  OTHER = 'OTHER'
}

export enum AccountType {
  ORDINARY = 'ORDINARY',
  CHECKING = 'CHECKING'
}

// ===== 会員データ型定義 =====

/**
 * 会員データの完全な型定義
 * APIレスポンス・DB保存・フロントエンド表示すべてに対応
 */
export interface Member {
  // 基本情報
  id: number;
  member_number: string;      // DB形式（snake_case）
  memberNumber: string;       // フロントエンド形式（camelCase）
  name: string;
  kana?: string;
  email: string;
  phone?: string;
  gender?: Gender;

  // ステータス・権限
  status: MemberStatus;
  title: Title;
  user_type: UserType;        // DB形式
  userType: UserType;         // フロントエンド形式
  plan: Plan;
  payment_method: PaymentMethod;  // DB形式
  paymentMethod: PaymentMethod;   // フロントエンド形式

  // 住所情報
  postal_code?: string;       // DB形式
  postalCode?: string;        // フロントエンド形式
  prefecture?: string;
  address2?: string;
  address3?: string;

  // 組織情報（重要：過去に不具合が多発）
  upline_id?: string;         // DB形式
  uplineId?: string;          // フロントエンド形式
  upline_name?: string;       // DB形式
  uplineName?: string;        // フロントエンド形式
  referrer_id?: string;       // DB形式
  referrerId?: string;        // フロントエンド形式
  referrer_name?: string;     // DB形式
  referrerName?: string;      // フロントエンド形式

  // 銀行情報
  bank_name?: string;         // DB形式
  bankName?: string;          // フロントエンド形式
  bank_code?: string;         // DB形式
  bankCode?: string;          // フロントエンド形式
  branch_name?: string;       // DB形式
  branchName?: string;        // フロントエンド形式
  branch_code?: string;       // DB形式
  branchCode?: string;        // フロントエンド形式
  account_number?: string;    // DB形式
  accountNumber?: string;     // フロントエンド形式
  yucho_symbol?: string;      // DB形式
  yuchoSymbol?: string;       // フロントエンド形式
  yucho_number?: string;      // DB形式
  yuchoNumber?: string;       // フロントエンド形式
  account_type?: AccountType; // DB形式
  accountType?: AccountType;  // フロントエンド形式

  // 日付情報
  registration_date?: string; // DB形式
  registrationDate?: string;  // フロントエンド形式
  withdrawal_date?: string;   // DB形式
  withdrawalDate?: string;    // フロントエンド形式
  created_at: string;         // DB形式
  createdAt: string;          // フロントエンド形式
  updated_at: string;         // DB形式
  updatedAt: string;          // フロントエンド形式

  // その他
  notes?: string;
  is_deleted: boolean;        // DB形式
  isDeleted: boolean;         // フロントエンド形式
}

// ===== API リクエスト・レスポンス型定義 =====

/**
 * 会員更新リクエスト
 * ⚠️ 重要: 編集画面からの送信で使用される
 */
export interface MemberUpdateRequest {
  // 基本情報
  name?: string;
  kana?: string;
  email?: string;
  phone?: string;
  gender?: Gender;

  // ステータス・権限
  status?: MemberStatus;
  title?: Title;
  user_type?: UserType;       // DB形式で送信
  plan?: Plan;
  payment_method?: PaymentMethod;  // DB形式で送信

  // 住所情報
  postal_code?: string;       // DB形式で送信
  prefecture?: string;
  address2?: string;
  address3?: string;

  // 組織情報（過去に送信漏れが多発したフィールド）
  upline_id?: string;         // DB形式で送信 ⚠️必須チェック
  upline_name?: string;       // DB形式で送信 ⚠️必須チェック
  referrer_id?: string;       // DB形式で送信
  referrer_name?: string;     // DB形式で送信

  // 銀行情報
  bank_name?: string;         // DB形式で送信
  bank_code?: string;         // DB形式で送信
  branch_name?: string;       // DB形式で送信
  branch_code?: string;       // DB形式で送信
  account_number?: string;    // DB形式で送信
  yucho_symbol?: string;      // DB形式で送信
  yucho_number?: string;      // DB形式で送信
  account_type?: AccountType; // DB形式で送信

  // 日付情報
  registration_date?: string; // DB形式で送信
  withdrawal_date?: string;   // DB形式で送信

  // その他
  notes?: string;
}

/**
 * 会員一覧レスポンス
 */
export interface MemberListResponse {
  data: Member[];             // 会員データ配列
  members: Member[];          // 後方互換性用
  
  // 件数情報（過去にステータス別集計で不具合）
  total: number;
  total_count: number;        // DB形式
  totalCount: number;         // フロントエンド形式
  active_count: number;       // DB形式
  activeCount: number;        // フロントエンド形式  
  inactive_count: number;     // DB形式
  inactiveCount: number;      // フロントエンド形式
  withdrawn_count: number;    // DB形式
  withdrawnCount: number;     // フロントエンド形式

  // ページネーション情報（過去にrowCount不足で不具合）
  page: number;
  perPage: number;
  totalPages: number;
}

/**
 * 検索パラメータ
 */
export interface MemberSearchParams {
  memberNumber?: string;      // 会員番号検索
  name?: string;              // 名前検索
  email?: string;             // メール検索
  status?: MemberStatus;      // ステータス検索
  page?: number;              // ページ番号（1から開始）
  perPage?: number;           // 1ページあたりの件数
  sortBy?: string;            // ソート項目
  sortOrder?: 'asc' | 'desc'; // ソート順
}

// ===== API エンドポイント定義 =====

/**
 * 会員管理API エンドポイント仕様
 */
export interface MemberAPI {
  /**
   * 会員一覧取得
   * GET /api/v1/members/
   */
  getMembers(params?: MemberSearchParams): Promise<MemberListResponse>;

  /**
   * 会員詳細取得（ID指定）
   * GET /api/v1/members/{id}
   */
  getMemberById(id: number): Promise<Member>;

  /**
   * 会員詳細取得（会員番号指定）
   * GET /api/v1/members/{memberNumber}
   * ⚠️ 編集画面で使用される重要なエンドポイント
   */
  getMemberByNumber(memberNumber: string): Promise<Member>;

  /**
   * 会員情報更新（ID指定）
   * PUT /api/v1/members/{id}
   */
  updateMember(id: number, data: MemberUpdateRequest): Promise<Member>;

  /**
   * 会員情報更新（会員番号指定）
   * PUT /api/v1/members/{memberNumber}
   * ⚠️ 編集画面で使用される重要なエンドポイント
   */
  updateMemberByNumber(memberNumber: string, data: MemberUpdateRequest): Promise<Member>;
}

// ===== バリデーション関数 =====

/**
 * 会員データのバリデーション
 */
export function validateMember(member: Partial<Member>): string[] {
  const errors: string[] = [];

  // 必須フィールドチェック
  if (!member.name?.trim()) {
    errors.push('名前は必須です');
  }
  if (!member.email?.trim()) {
    errors.push('メールアドレスは必須です');
  }
  if (!member.member_number?.trim() && !member.memberNumber?.trim()) {
    errors.push('会員番号は必須です');
  }

  // フォーマットチェック
  if (member.email && !/\S+@\S+\.\S+/.test(member.email)) {
    errors.push('メールアドレスの形式が正しくありません');
  }

  return errors;
}

/**
 * 更新データの完全性チェック
 * ⚠️ 過去に送信漏れが多発したフィールドを重点チェック
 */
export function validateUpdateData(data: MemberUpdateRequest): string[] {
  const errors: string[] = [];
  const warnings: string[] = [];

  // 組織情報の整合性チェック
  if (data.upline_id && !data.upline_name) {
    warnings.push('直上者IDが設定されていますが、直上者名が未設定です');
  }
  if (data.upline_name && !data.upline_id) {
    warnings.push('直上者名が設定されていますが、直上者IDが未設定です');
  }

  // 銀行情報の整合性チェック
  if (data.bank_code && !data.bank_name) {
    warnings.push('銀行コードが設定されていますが、銀行名が未設定です');
  }

  // 警告をエラーとして表示（開発時）
  if (process.env.NODE_ENV === 'development') {
    errors.push(...warnings.map(w => `[警告] ${w}`));
  }

  return errors;
}

// ===== ユーティリティ関数 =====

/**
 * フロントエンド形式をDB形式に変換
 */
export function convertToDbFormat(data: any): any {
  return {
    ...data,
    member_number: data.memberNumber || data.member_number,
    user_type: data.userType || data.user_type,
    payment_method: data.paymentMethod || data.payment_method,
    postal_code: data.postalCode || data.postal_code,
    upline_id: data.uplineId || data.upline_id,
    upline_name: data.uplineName || data.upline_name,
    referrer_id: data.referrerId || data.referrer_id,
    referrer_name: data.referrerName || data.referrer_name,
    // ... 他のフィールドも同様に変換
  };
}

/**
 * DB形式をフロントエンド形式に変換
 */
export function convertToFrontendFormat(data: any): any {
  return {
    ...data,
    memberNumber: data.member_number || data.memberNumber,
    userType: data.user_type || data.userType,
    paymentMethod: data.payment_method || data.paymentMethod,
    postalCode: data.postal_code || data.postalCode,
    uplineId: data.upline_id || data.uplineId,
    uplineName: data.upline_name || data.uplineName,
    referrerId: data.referrer_id || data.referrerId,
    referrerName: data.referrer_name || data.referrerName,
    // ... 他のフィールドも同様に変換
  };
}