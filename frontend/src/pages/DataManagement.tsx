import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Button,
  Typography,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  IconButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  FormControlLabel,
  Checkbox,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import {
  Upload,
  Download,
  Backup,
  Restore,
  Refresh,
  Delete,
  Visibility,
  GetApp,
  CloudUpload,
  CloudDownload,
  Storage,
  Schedule,
  CheckCircle,
  Error,
  Warning,
  ExpandMore,
  DataUsage,
  FileCopy,
  Transform,
  History,
  Settings,
} from '@mui/icons-material';
import {
  DataManagementService,
  DataType,
  DataFormat,
  ProcessStatus,
  ImportSettings,
  ExportSettings,
  BackupInfo,
  BackupSettings,
  ProcessResult,
  DataStatistics,
  DataTemplate,
} from '@/services/dataManagementService';

/**
 * P-009: データ入出力
 * 各種CSV入出力、バックアップ、データ移行機能
 * 要件定義: インポート、エクスポート、バックアップ、リストア
 */
const DataManagement: React.FC = () => {
  // State管理
  const [dataStatistics, setDataStatistics] = useState<DataStatistics[]>([]);
  const [processHistory, setProcessHistory] = useState<ProcessResult[]>([]);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [templates, setTemplates] = useState<DataTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  // ダイアログ管理
  const [importDialog, setImportDialog] = useState(false);
  const [exportDialog, setExportDialog] = useState(false);
  const [backupDialog, setBackupDialog] = useState(false);
  const [restoreDialog, setRestoreDialog] = useState(false);
  const [progressDialog, setProgressDialog] = useState(false);

  // ファイルアップロード
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentJob, setCurrentJob] = useState<ProcessResult | null>(null);

  // 設定
  const [importSettings, setImportSettings] = useState<ImportSettings>({
    dataType: DataType.MEMBERS,
    format: DataFormat.CSV,
    encoding: 'UTF-8',
    skipHeader: true,
    delimiter: ',',
    conflictResolution: 'update',
    validateOnly: false,
    chunkSize: 1000,
  });

  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    dataType: DataType.MEMBERS,
    format: DataFormat.CSV,
    encoding: 'UTF-8',
    includeHeader: true,
    delimiter: ',',
    dateFormat: 'yyyy-MM-dd',
  });

  const [backupSettings, setBackupSettings] = useState<BackupSettings>({
    name: '',
    dataTypes: [DataType.ALL],
    format: 'full',
    compression: true,
    encryption: false,
    retentionDays: 30,
    scheduledBackup: false,
  });

  // モックデータ
  const mockStatistics: DataStatistics[] = [
    {
      dataType: DataType.MEMBERS,
      totalRecords: 50,
      lastUpdated: '2024-03-25T10:30:00Z',
      recordsAddedToday: 2,
      recordsUpdatedToday: 5,
      averageRecordSize: 1024,
      indexSize: 512000,
      tableSize: 2048000,
    },
    {
      dataType: DataType.PAYMENTS,
      totalRecords: 156,
      lastUpdated: '2024-03-25T09:15:00Z',
      recordsAddedToday: 12,
      recordsUpdatedToday: 8,
      averageRecordSize: 512,
      indexSize: 256000,
      tableSize: 1024000,
    },
  ];

  const mockProcessHistory: ProcessResult[] = [
    {
      id: 'job-001',
      dataType: DataType.MEMBERS,
      format: DataFormat.CSV,
      status: ProcessStatus.COMPLETED,
      startedAt: '2024-03-25T14:00:00Z',
      completedAt: '2024-03-25T14:02:30Z',
      totalRecords: 50,
      processedRecords: 50,
      successRecords: 48,
      errorRecords: 2,
      skippedRecords: 0,
      errors: ['行15: メールアドレスの形式が不正です', '行32: 必須項目が未入力です'],
      warnings: [],
      executionTime: 150,
      fileSize: 25600,
    },
  ];

  const mockBackups: BackupInfo[] = [
    {
      id: 'backup-001',
      name: '月次バックアップ_2024年3月',
      description: '月次定期バックアップ',
      createdAt: '2024-03-25T02:00:00Z',
      createdBy: '管理者',
      size: 52428800,
      dataTypes: [DataType.ALL],
      format: 'full',
      compressed: true,
      encrypted: false,
      retentionDate: '2024-04-25T02:00:00Z',
      restoreAvailable: true,
    },
  ];

  useEffect(() => {
    fetchDataManagementData();
  }, []);

  const fetchDataManagementData = async () => {
    setLoading(true);
    try {
      // 実際のAPI呼び出し（現在はモック）
      await new Promise(resolve => setTimeout(resolve, 500));
      setDataStatistics(mockStatistics);
      setProcessHistory(mockProcessHistory);
      setBackups(mockBackups);
    } catch (error) {
      console.error('データ管理情報取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  // ファイルアップロード処理
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  // インポート実行
  const handleImport = async () => {
    if (!selectedFile) return;

    try {
      setProgressDialog(true);
      setUploadProgress(0);

      // ファイルアップロード（検証）
      const uploadResult = await DataManagementService.uploadFile(selectedFile, importSettings);
      
      // プログレスバー更新（模擬）
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            return 100;
          }
          return prev + 10;
        });
      }, 200);

      console.log('インポート完了:', uploadResult);
      
      setImportDialog(false);
      setProgressDialog(false);
      fetchDataManagementData();
      
    } catch (error) {
      console.error('インポートエラー:', error);
      setProgressDialog(false);
    }
  };

  // エクスポート実行
  const handleExport = async () => {
    try {
      setProgressDialog(true);
      
      const result = await DataManagementService.executeExport(exportSettings);
      console.log('エクスポート開始:', result);
      
      setExportDialog(false);
      setProgressDialog(false);
      
    } catch (error) {
      console.error('エクスポートエラー:', error);
      setProgressDialog(false);
    }
  };

  // バックアップ実行
  const handleBackup = async () => {
    try {
      setProgressDialog(true);
      
      const result = await DataManagementService.createBackup(backupSettings);
      console.log('バックアップ開始:', result);
      
      setBackupDialog(false);
      setProgressDialog(false);
      fetchDataManagementData();
      
    } catch (error) {
      console.error('バックアップエラー:', error);
      setProgressDialog(false);
    }
  };

  // ステータス色取得
  const getStatusColor = (status: ProcessStatus) => {
    switch (status) {
      case ProcessStatus.COMPLETED:
        return 'success';
      case ProcessStatus.IN_PROGRESS:
        return 'info';
      case ProcessStatus.FAILED:
        return 'error';
      case ProcessStatus.CANCELLED:
        return 'warning';
      default:
        return 'default';
    }
  };

  // 処理履歴の列定義
  const historyColumns: GridColDef[] = [
    {
      field: 'startedAt',
      headerName: '実行日時',
      width: 180,
      renderCell: (params: GridRenderCellParams) =>
        new Date(params.value).toLocaleString('ja-JP'),
    },
    {
      field: 'dataType',
      headerName: 'データ種別',
      width: 150,
    },
    {
      field: 'format',
      headerName: '形式',
      width: 100,
    },
    {
      field: 'status',
      headerName: 'ステータス',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value}
          size="small"
          color={getStatusColor(params.value)}
        />
      ),
    },
    {
      field: 'totalRecords',
      headerName: '総件数',
      width: 100,
      align: 'right',
    },
    {
      field: 'successRecords',
      headerName: '成功件数',
      width: 100,
      align: 'right',
    },
    {
      field: 'errorRecords',
      headerName: 'エラー件数',
      width: 100,
      align: 'right',
    },
    {
      field: 'executionTime',
      headerName: '実行時間',
      width: 100,
      renderCell: (params: GridRenderCellParams) => `${params.value}秒`,
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 100,
      sortable: false,
      renderCell: (params: GridRenderCellParams) => (
        <IconButton size="small" title="詳細表示">
          <Visibility fontSize="small" />
        </IconButton>
      ),
    },
  ];

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          データ入出力
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          各種CSV入出力、バックアップ、データ移行機能
        </Typography>
      </Box>

      {/* データ統計カード */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {dataStatistics.map((stat) => (
          <Grid item xs={12} sm={6} md={3} key={stat.dataType}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  {stat.dataType}
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  {stat.totalRecords.toLocaleString()}件
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  今日: +{stat.recordsAddedToday}件
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* アクションボタン */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<Upload />}
              onClick={() => setImportDialog(true)}
            >
              データインポート
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Download />}
              onClick={() => setExportDialog(true)}
            >
              データエクスポート
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Backup />}
              onClick={() => setBackupDialog(true)}
            >
              バックアップ作成
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Restore />}
              onClick={() => setRestoreDialog(true)}
            >
              リストア
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* タブ */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab icon={<History />} label="処理履歴" />
          <Tab icon={<Storage />} label="バックアップ管理" />
          <Tab icon={<FileCopy />} label="テンプレート" />
          <Tab icon={<Settings />} label="設定" />
        </Tabs>
      </Paper>

      {/* タブ1: 処理履歴 */}
      {tabValue === 0 && (
        <Paper sx={{ height: 400 }}>
          <DataGrid
            rows={processHistory}
            columns={historyColumns}
            loading={loading}
            pageSizeOptions={[25, 50, 100]}
            sx={{
              '& .MuiDataGrid-cell': {
                borderBottom: '1px solid #e0e0e0',
              },
            }}
          />
        </Paper>
      )}

      {/* タブ2: バックアップ管理 */}
      {tabValue === 1 && (
        <Box>
          <Grid container spacing={2}>
            {backups.map((backup) => (
              <Grid item xs={12} md={6} lg={4} key={backup.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6" fontWeight="600">
                        {backup.name}
                      </Typography>
                      <Chip
                        label={backup.format}
                        size="small"
                        color="primary"
                      />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {backup.description}
                    </Typography>
                    
                    <Typography variant="caption" display="block">
                      作成日時: {new Date(backup.createdAt).toLocaleString('ja-JP')}
                    </Typography>
                    <Typography variant="caption" display="block">
                      サイズ: {(backup.size / (1024 * 1024)).toFixed(1)}MB
                    </Typography>
                    <Typography variant="caption" display="block">
                      作成者: {backup.createdBy}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                      <Button
                        size="small"
                        startIcon={<CloudDownload />}
                        disabled={!backup.restoreAvailable}
                      >
                        ダウンロード
                      </Button>
                      <Button
                        size="small"
                        startIcon={<Restore />}
                        disabled={!backup.restoreAvailable}
                        onClick={() => setRestoreDialog(true)}
                      >
                        リストア
                      </Button>
                      <IconButton size="small" color="error">
                        <Delete fontSize="small" />
                      </IconButton>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* タブ3: テンプレート */}
      {tabValue === 2 && (
        <Box>
          <Alert severity="info" sx={{ mb: 2 }}>
            📄 データインポート用のテンプレートファイルをダウンロードできます。
          </Alert>
          
          <Grid container spacing={2}>
            {Object.values(DataType).filter(type => type !== DataType.ALL).map((dataType) => (
              <Grid item xs={12} sm={6} md={4} key={dataType}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" fontWeight="600" sx={{ mb: 1 }}>
                      {dataType}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {dataType}のインポート用テンプレート
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<GetApp />}
                      fullWidth
                      onClick={() => console.log(`${dataType}テンプレートダウンロード`)}
                    >
                      テンプレートダウンロード
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* タブ4: 設定 */}
      {tabValue === 3 && (
        <Box>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6" fontWeight="600">
                デフォルト設定
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>デフォルト文字コード</InputLabel>
                    <Select
                      value="UTF-8"
                      label="デフォルト文字コード"
                    >
                      <MenuItem value="UTF-8">UTF-8</MenuItem>
                      <MenuItem value="Shift-JIS">Shift-JIS</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>デフォルト区切り文字</InputLabel>
                    <Select
                      value=","
                      label="デフォルト区切り文字"
                    >
                      <MenuItem value=",">カンマ (,)</MenuItem>
                      <MenuItem value=";">セミコロン (;)</MenuItem>
                      <MenuItem value="\t">タブ</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={<Checkbox defaultChecked />}
                    label="インポート前の検証を必須とする"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={<Checkbox defaultChecked />}
                    label="エクスポート時にヘッダー行を含める"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6" fontWeight="600">
                自動バックアップ設定
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Alert severity="info" sx={{ mb: 2 }}>
                自動バックアップは毎日午前2時に実行され、30日間保持されます。
              </Alert>
              <FormControlLabel
                control={<Checkbox defaultChecked />}
                label="自動バックアップを有効にする"
              />
            </AccordionDetails>
          </Accordion>
        </Box>
      )}

      {/* インポートダイアログ */}
      <Dialog
        open={importDialog}
        onClose={() => setImportDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>データインポート</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <input
                type="file"
                accept=".csv,.xlsx,.json"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                id="file-upload"
              />
              <label htmlFor="file-upload">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<CloudUpload />}
                  fullWidth
                >
                  ファイルを選択
                </Button>
              </label>
              {selectedFile && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  選択ファイル: {selectedFile.name}
                </Typography>
              )}
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>データ種別</InputLabel>
                <Select
                  value={importSettings.dataType}
                  label="データ種別"
                  onChange={(e) => setImportSettings({ 
                    ...importSettings, 
                    dataType: e.target.value as DataType 
                  })}
                >
                  {Object.values(DataType).filter(type => type !== DataType.ALL).map((type) => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>文字コード</InputLabel>
                <Select
                  value={importSettings.encoding}
                  label="文字コード"
                  onChange={(e) => setImportSettings({ 
                    ...importSettings, 
                    encoding: e.target.value as 'UTF-8' | 'Shift-JIS' 
                  })}
                >
                  <MenuItem value="UTF-8">UTF-8</MenuItem>
                  <MenuItem value="Shift-JIS">Shift-JIS</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={importSettings.skipHeader}
                    onChange={(e) => setImportSettings({ 
                      ...importSettings, 
                      skipHeader: e.target.checked 
                    })}
                  />
                }
                label="1行目をヘッダーとしてスキップ"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={importSettings.validateOnly}
                    onChange={(e) => setImportSettings({ 
                      ...importSettings, 
                      validateOnly: e.target.checked 
                    })}
                  />
                }
                label="検証のみ実行（プレビューモード）"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialog(false)}>キャンセル</Button>
          <Button
            variant="contained"
            onClick={handleImport}
            disabled={!selectedFile}
            startIcon={<Upload />}
          >
            インポート実行
          </Button>
        </DialogActions>
      </Dialog>

      {/* エクスポートダイアログ */}
      <Dialog
        open={exportDialog}
        onClose={() => setExportDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>データエクスポート</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>データ種別</InputLabel>
                <Select
                  value={exportSettings.dataType}
                  label="データ種別"
                  onChange={(e) => setExportSettings({ 
                    ...exportSettings, 
                    dataType: e.target.value as DataType 
                  })}
                >
                  {Object.values(DataType).map((type) => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>形式</InputLabel>
                <Select
                  value={exportSettings.format}
                  label="形式"
                  onChange={(e) => setExportSettings({ 
                    ...exportSettings, 
                    format: e.target.value as DataFormat 
                  })}
                >
                  <MenuItem value={DataFormat.CSV}>CSV</MenuItem>
                  <MenuItem value={DataFormat.EXCEL}>Excel</MenuItem>
                  <MenuItem value={DataFormat.JSON}>JSON</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>文字コード</InputLabel>
                <Select
                  value={exportSettings.encoding}
                  label="文字コード"
                  onChange={(e) => setExportSettings({ 
                    ...exportSettings, 
                    encoding: e.target.value as 'UTF-8' | 'Shift-JIS' 
                  })}
                >
                  <MenuItem value="UTF-8">UTF-8</MenuItem>
                  <MenuItem value="Shift-JIS">Shift-JIS</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={exportSettings.includeHeader}
                    onChange={(e) => setExportSettings({ 
                      ...exportSettings, 
                      includeHeader: e.target.checked 
                    })}
                  />
                }
                label="ヘッダー行を含める"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>キャンセル</Button>
          <Button
            variant="contained"
            onClick={handleExport}
            startIcon={<Download />}
          >
            エクスポート実行
          </Button>
        </DialogActions>
      </Dialog>

      {/* バックアップダイアログ */}
      <Dialog
        open={backupDialog}
        onClose={() => setBackupDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>バックアップ作成</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="バックアップ名"
                value={backupSettings.name}
                onChange={(e) => setBackupSettings({ 
                  ...backupSettings, 
                  name: e.target.value 
                })}
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="説明（任意）"
                multiline
                rows={2}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>バックアップ形式</InputLabel>
                <Select
                  value={backupSettings.format}
                  label="バックアップ形式"
                  onChange={(e) => setBackupSettings({ 
                    ...backupSettings, 
                    format: e.target.value as 'full' | 'incremental' | 'differential' 
                  })}
                >
                  <MenuItem value="full">フル</MenuItem>
                  <MenuItem value="incremental">増分</MenuItem>
                  <MenuItem value="differential">差分</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="保持期間（日）"
                type="number"
                value={backupSettings.retentionDays}
                onChange={(e) => setBackupSettings({ 
                  ...backupSettings, 
                  retentionDays: Number(e.target.value) 
                })}
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={backupSettings.compression}
                    onChange={(e) => setBackupSettings({ 
                      ...backupSettings, 
                      compression: e.target.checked 
                    })}
                  />
                }
                label="圧縮する"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={backupSettings.encryption}
                    onChange={(e) => setBackupSettings({ 
                      ...backupSettings, 
                      encryption: e.target.checked 
                    })}
                  />
                }
                label="暗号化する"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBackupDialog(false)}>キャンセル</Button>
          <Button
            variant="contained"
            onClick={handleBackup}
            disabled={!backupSettings.name}
            startIcon={<Backup />}
          >
            バックアップ作成
          </Button>
        </DialogActions>
      </Dialog>

      {/* 進捗ダイアログ */}
      <Dialog
        open={progressDialog}
        onClose={() => {}}
        maxWidth="sm"
        fullWidth
        disableEscapeKeyDown
      >
        <DialogTitle>処理実行中</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              進捗: {uploadProgress}%
            </Typography>
            <LinearProgress variant="determinate" value={uploadProgress} />
          </Box>
          <Alert severity="info">
            処理を実行しています。しばらくお待ちください。
          </Alert>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default DataManagement;