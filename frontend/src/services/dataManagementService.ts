import { ApiService } from './apiClient';

/**
 * データ入出力管理サービス
 * P-009: 各種CSV入出力、バックアップ、データ移行機能
 * 要件定義: インポート、エクスポート、バックアップ、リストア
 */

// インポート/エクスポートタイプ
export enum DataType {
  MEMBERS = '会員データ',
  PAYMENTS = '決済データ',
  REWARDS = '報酬データ',
  PAYOUTS = '支払データ',
  ACTIVITIES = 'アクティビティログ',
  ORGANIZATION = '組織データ',
  ALL = '全データ',
}

// インポート/エクスポート形式
export enum DataFormat {
  CSV = 'CSV',
  JSON = 'JSON',
  EXCEL = 'Excel',
  BACKUP = 'Backup',
}

// 処理ステータス
export enum ProcessStatus {
  PENDING = '待機中',
  IN_PROGRESS = '処理中',
  COMPLETED = '完了',
  FAILED = '失敗',
  CANCELLED = 'キャンセル',
}

// データ検証結果
export interface ValidationResult {
  isValid: boolean;
  totalRecords: number;
  validRecords: number;
  invalidRecords: number;
  errors: Array<{
    row: number;
    field: string;
    value: any;
    message: string;
    severity: 'error' | 'warning';
  }>;
  warnings: Array<{
    row: number;
    field: string;
    value: any;
    message: string;
  }>;
}

// インポート設定
export interface ImportSettings {
  dataType: DataType;
  format: DataFormat;
  encoding: 'UTF-8' | 'Shift-JIS';
  skipHeader: boolean;
  delimiter: ',' | ';' | '\t';
  conflictResolution: 'skip' | 'update' | 'error';
  validateOnly: boolean; // プレビューモード
  chunkSize: number; // バッチ処理サイズ
  customMappings?: Record<string, string>; // カラムマッピング
}

// エクスポート設定
export interface ExportSettings {
  dataType: DataType;
  format: DataFormat;
  encoding: 'UTF-8' | 'Shift-JIS';
  includeHeader: boolean;
  delimiter: ',' | ';' | '\t';
  dateFormat: string;
  filters?: Record<string, any>; // フィルター条件
  columns?: string[]; // 出力対象カラム
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// インポート/エクスポート結果
export interface ProcessResult {
  id: string;
  dataType: DataType;
  format: DataFormat;
  status: ProcessStatus;
  startedAt: string;
  completedAt?: string;
  totalRecords: number;
  processedRecords: number;
  successRecords: number;
  errorRecords: number;
  skippedRecords: number;
  errors: string[];
  warnings: string[];
  downloadUrl?: string; // エクスポートの場合
  executionTime: number; // 実行時間（秒）
  fileSize?: number; // ファイルサイズ（バイト）
}

// データ統計
export interface DataStatistics {
  dataType: DataType;
  totalRecords: number;
  lastUpdated: string;
  recordsAddedToday: number;
  recordsUpdatedToday: number;
  averageRecordSize: number;
  indexSize: number;
  tableSize: number;
}

// バックアップ情報
export interface BackupInfo {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  createdBy: string;
  size: number;
  dataTypes: DataType[];
  format: 'full' | 'incremental' | 'differential';
  compressed: boolean;
  encrypted: boolean;
  retentionDate: string;
  downloadUrl?: string;
  restoreAvailable: boolean;
}

// バックアップ設定
export interface BackupSettings {
  name: string;
  description?: string;
  dataTypes: DataType[];
  format: 'full' | 'incremental' | 'differential';
  compression: boolean;
  encryption: boolean;
  password?: string;
  retentionDays: number;
  scheduledBackup: boolean;
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly';
    dayOfWeek?: number; // 0-6 (Sunday-Saturday)
    dayOfMonth?: number; // 1-31
    time: string; // HH:MM format
  };
}

// リストア設定
export interface RestoreSettings {
  backupId: string;
  password?: string;
  dataTypes: DataType[];
  conflictResolution: 'skip' | 'overwrite' | 'merge';
  validateBeforeRestore: boolean;
  createBackupBeforeRestore: boolean;
}

// データ移行ジョブ
export interface MigrationJob {
  id: string;
  name: string;
  description: string;
  sourceSystem: string;
  targetSystem: string;
  dataTypes: DataType[];
  status: ProcessStatus;
  progress: number; // 0-100
  startedAt: string;
  estimatedCompletion?: string;
  completedAt?: string;
  totalRecords: number;
  migratedRecords: number;
  errors: string[];
  logs: Array<{
    timestamp: string;
    level: 'info' | 'warn' | 'error';
    message: string;
  }>;
}

// テンプレート定義
export interface DataTemplate {
  id: string;
  name: string;
  description: string;
  dataType: DataType;
  format: DataFormat;
  columns: Array<{
    name: string;
    type: 'string' | 'number' | 'date' | 'boolean';
    required: boolean;
    maxLength?: number;
    pattern?: string;
    defaultValue?: any;
    description: string;
  }>;
  sampleData: Record<string, any>[];
  downloadUrl: string;
  lastUpdated: string;
}

export class DataManagementService {
  private static readonly BASE_URL = '/data-management';

  /**
   * データ統計取得
   */
  static async getDataStatistics(): Promise<DataStatistics[]> {
    return ApiService.get<DataStatistics[]>(`${this.BASE_URL}/statistics`);
  }

  /**
   * ファイルアップロード（インポート前検証）
   */
  static async uploadFile(file: File, settings: ImportSettings): Promise<{
    fileId: string;
    fileName: string;
    fileSize: number;
    uploadedAt: string;
    validationResult: ValidationResult;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('settings', JSON.stringify(settings));
    
    return ApiService.post(`${this.BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  /**
   * データインポート実行
   */
  static async executeImport(
    fileId: string,
    settings: ImportSettings
  ): Promise<{ jobId: string }> {
    return ApiService.post(`${this.BASE_URL}/import`, {
      fileId,
      settings,
    });
  }

  /**
   * データエクスポート実行
   */
  static async executeExport(settings: ExportSettings): Promise<{ jobId: string }> {
    return ApiService.post(`${this.BASE_URL}/export`, { settings });
  }

  /**
   * 処理状況確認
   */
  static async getProcessStatus(jobId: string): Promise<ProcessResult> {
    return ApiService.get<ProcessResult>(`${this.BASE_URL}/process/${jobId}`);
  }

  /**
   * 処理履歴取得
   */
  static async getProcessHistory(
    dataType?: DataType,
    limit: number = 50
  ): Promise<ProcessResult[]> {
    return ApiService.get<ProcessResult[]>(`${this.BASE_URL}/history`, {
      params: { dataType, limit },
    });
  }

  /**
   * バックアップ実行
   */
  static async createBackup(settings: BackupSettings): Promise<{ jobId: string }> {
    return ApiService.post(`${this.BASE_URL}/backup`, { settings });
  }

  /**
   * バックアップ一覧取得
   */
  static async getBackups(): Promise<BackupInfo[]> {
    return ApiService.get<BackupInfo[]>(`${this.BASE_URL}/backups`);
  }

  /**
   * バックアップダウンロード
   */
  static async downloadBackup(backupId: string): Promise<Blob> {
    const response = await ApiService.get(`${this.BASE_URL}/backups/${backupId}/download`, {
      responseType: 'blob',
    });
    return response as Blob;
  }

  /**
   * リストア実行
   */
  static async executeRestore(settings: RestoreSettings): Promise<{ jobId: string }> {
    return ApiService.post(`${this.BASE_URL}/restore`, { settings });
  }

  /**
   * バックアップ削除
   */
  static async deleteBackup(backupId: string): Promise<void> {
    return ApiService.delete(`${this.BASE_URL}/backups/${backupId}`);
  }

  /**
   * データテンプレート取得
   */
  static async getDataTemplates(dataType?: DataType): Promise<DataTemplate[]> {
    return ApiService.get<DataTemplate[]>(`${this.BASE_URL}/templates`, {
      params: { dataType },
    });
  }

  /**
   * テンプレートダウンロード
   */
  static async downloadTemplate(templateId: string): Promise<Blob> {
    const response = await ApiService.get(`${this.BASE_URL}/templates/${templateId}/download`, {
      responseType: 'blob',
    });
    return response as Blob;
  }

  /**
   * データ移行ジョブ作成
   */
  static async createMigrationJob(job: Omit<MigrationJob, 'id' | 'status' | 'progress' | 'startedAt' | 'migratedRecords' | 'errors' | 'logs'>): Promise<{ jobId: string }> {
    return ApiService.post(`${this.BASE_URL}/migration`, { job });
  }

  /**
   * データ移行ジョブ一覧
   */
  static async getMigrationJobs(): Promise<MigrationJob[]> {
    return ApiService.get<MigrationJob[]>(`${this.BASE_URL}/migration`);
  }

  /**
   * データ移行ジョブ詳細
   */
  static async getMigrationJob(jobId: string): Promise<MigrationJob> {
    return ApiService.get<MigrationJob>(`${this.BASE_URL}/migration/${jobId}`);
  }

  /**
   * データ移行ジョブキャンセル
   */
  static async cancelMigrationJob(jobId: string): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/migration/${jobId}/cancel`);
  }

  /**
   * データ検証（ファイルアップロード無し）
   */
  static async validateData(
    dataType: DataType,
    data: Record<string, any>[],
    settings?: Partial<ImportSettings>
  ): Promise<ValidationResult> {
    return ApiService.post(`${this.BASE_URL}/validate`, {
      dataType,
      data,
      settings,
    });
  }

  /**
   * データクリーンアップ
   */
  static async cleanupData(options: {
    dataTypes: DataType[];
    olderThanDays?: number;
    dryRun?: boolean;
  }): Promise<{
    affectedRecords: number;
    spaceFreed: number;
    deletedRecords?: number;
    errors: string[];
  }> {
    return ApiService.post(`${this.BASE_URL}/cleanup`, options);
  }

  /**
   * データ整合性チェック
   */
  static async checkDataIntegrity(): Promise<{
    overall: 'healthy' | 'warning' | 'critical';
    checks: Array<{
      dataType: DataType;
      status: 'healthy' | 'warning' | 'critical';
      issues: string[];
      recommendations: string[];
    }>;
    lastCheck: string;
  }> {
    return ApiService.get(`${this.BASE_URL}/integrity-check`);
  }

  /**
   * スケジュールバックアップ設定
   */
  static async setBackupSchedule(settings: BackupSettings): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/backup-schedule`, { settings });
  }

  /**
   * スケジュールバックアップ取得
   */
  static async getBackupSchedule(): Promise<BackupSettings[]> {
    return ApiService.get<BackupSettings[]>(`${this.BASE_URL}/backup-schedule`);
  }

  /**
   * ファイル削除
   */
  static async deleteUploadedFile(fileId: string): Promise<void> {
    return ApiService.delete(`${this.BASE_URL}/files/${fileId}`);
  }

  /**
   * 処理キャンセル
   */
  static async cancelProcess(jobId: string): Promise<void> {
    return ApiService.post(`${this.BASE_URL}/process/${jobId}/cancel`);
  }

  /**
   * データ変換ユーティリティ
   */
  static async convertData(options: {
    fromFormat: DataFormat;
    toFormat: DataFormat;
    data: any;
    settings?: Record<string, any>;
  }): Promise<{
    convertedData: any;
    warnings: string[];
  }> {
    return ApiService.post(`${this.BASE_URL}/convert`, options);
  }
}