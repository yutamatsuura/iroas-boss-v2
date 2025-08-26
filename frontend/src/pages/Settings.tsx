import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore,
  Info,
  Settings as SettingsIcon,
  Payment,
  Security,
  Storage,
  Assessment,
  Description,
  Refresh,
  HealthAndSafety,
} from '@mui/icons-material';
import {
  SettingsService,
  SystemSettings,
  MasterData,
  SystemInfo,
} from '@/services/settingsService';

/**
 * P-008: マスタ設定
 * システム固定値の確認表示のみ（変更不可）
 * 要件定義: 参加費、タイトル条件、報酬率の固定値表示
 */
const Settings: React.FC = () => {
  // State管理
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [masterData, setMasterData] = useState<MasterData | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  // モックデータ
  const mockSystemSettings: SystemSettings = {
    systemName: 'IROAS BOSS V2',
    version: '2.0.0',
    environment: 'production',
    maintenanceMode: false,
    memberNumberDigits: 7,
    maxMembersPerPage: 50,
    defaultMemberStatus: 'アクティブ',
    
    participationFee: {
      heroPlan: 21780,
      testPlan: 0,
      currency: 'JPY',
      taxIncluded: true,
    },
    
    titleSettings: {
      titles: [
        {
          name: 'スタート',
          order: 1,
          requiredPersonalSales: 0,
          requiredOrganizationSales: 0,
          requiredDirectReferrals: 0,
          requiredDownlineManagers: 0,
          titleBonus: 0,
          description: '初期タイトル',
        },
        {
          name: 'リーダー',
          order: 2,
          requiredPersonalSales: 65340,
          requiredOrganizationSales: 0,
          requiredDirectReferrals: 3,
          requiredDownlineManagers: 0,
          titleBonus: 10000,
          description: '3名直紹介 + 個人売上65,340円',
        },
        {
          name: 'マネージャー',
          order: 3,
          requiredPersonalSales: 65340,
          requiredOrganizationSales: 500000,
          requiredDirectReferrals: 3,
          requiredDownlineManagers: 2,
          titleBonus: 30000,
          description: 'リーダー条件 + 組織売上50万円 + 下位マネージャー2名',
        },
        {
          name: 'ディレクター',
          order: 4,
          requiredPersonalSales: 65340,
          requiredOrganizationSales: 2000000,
          requiredDirectReferrals: 3,
          requiredDownlineManagers: 3,
          titleBonus: 100000,
          description: 'マネージャー条件 + 組織売上200万円 + 下位マネージャー3名',
        },
        {
          name: 'エリアディレクター',
          order: 5,
          requiredPersonalSales: 65340,
          requiredOrganizationSales: 5000000,
          requiredDirectReferrals: 5,
          requiredDownlineManagers: 5,
          titleBonus: 300000,
          description: 'ディレクター条件 + 組織売上500万円 + 下位マネージャー5名',
        },
      ],
      autoPromotionEnabled: true,
      promotionCheckFrequency: 'monthly',
    },
    
    rewardSettings: {
      dailyBonusRate: 0.033,
      referralBonusRate: 0.5,
      powerBonusRates: {
        level1: 0.08,
        level2: 0.05,
        level3: 0.03,
        level4: 0.02,
        level5Plus: 0.01,
      },
      maintenanceBonusPerKit: 3000,
      salesActivityBonus: 50000,
      royalFamilyBonus: 100000,
      calculationSchedule: 'monthly',
      calculationDate: 25,
    },
    
    payoutSettings: {
      minimumPayoutAmount: 5000,
      bankTransferFee: 0,
      payoutSchedule: 'monthly',
      payoutDate: 15,
      carryForwardEnabled: true,
      withholdingTax: {
        enabled: true,
        businessRate: 0.1021,
        personalRate: 0.1021,
        exemptionAmount: 0,
      },
      gmoSettings: {
        enabled: true,
        csvFormat: 'GMO NetBank Format',
        encoding: 'Shift-JIS',
        maxRecordsPerFile: 1000,
      },
    },
    
    paymentSettings: {
      univapaySettings: {
        enabled: true,
        cardPaymentEnabled: true,
        bankTransferEnabled: true,
        csvFormat: 'Univapay Standard',
        encoding: 'Shift-JIS',
        cardPaymentDeadline: 5,
        bankTransferDeadline: 12,
        bankTransferExecutionDate: 27,
      },
      manualPaymentMethods: ['銀行振込', 'インフォカート'],
      retrySettings: {
        enabled: true,
        maxRetries: 3,
        retryIntervalDays: 7,
      },
    },
    
    securitySettings: {
      sessionTimeout: 60,
      passwordPolicy: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true,
        requireSymbols: false,
      },
      ipWhitelist: ['192.168.1.0/24'],
      maxLoginAttempts: 5,
      lockoutDuration: 30,
    },
    
    dataRetentionSettings: {
      activityLogRetentionDays: 365,
      paymentHistoryRetentionMonths: 84,
      memberDataRetentionYears: 7,
      autoCleanupEnabled: true,
    },
    
    systemLimits: {
      maxMembersTotal: 1000,
      maxConcurrentUsers: 10,
      maxFileUploadSize: 10,
      maxOrganizationDepth: 10,
    },
    
    notificationSettings: {
      emailEnabled: true,
      smsEnabled: false,
      pushEnabled: false,
      adminNotificationEmail: 'admin@iroas-boss.com',
      systemMaintenanceNotice: true,
    },
  };

  const mockSystemInfo: SystemInfo = {
    version: {
      application: '2.0.0',
      database: '1.2.1',
      api: '2.0.0',
      frontend: '2.0.0',
    },
    environment: {
      name: 'Production',
      description: '本番環境',
      debugMode: false,
      logLevel: 'INFO',
    },
    resources: {
      cpuUsage: 45.2,
      memoryUsage: 68.9,
      diskUsage: 32.1,
      dbConnections: 8,
      activeUsers: 3,
    },
    statistics: {
      totalMembers: 50,
      activeMembers: 48,
      totalRewards: 12500000,
      totalPayouts: 11800000,
      lastCalculationDate: '2024-03-25',
      lastPayoutDate: '2024-03-15',
    },
    maintenance: {
      scheduled: false,
    },
  };

  useEffect(() => {
    fetchSettingsData();
  }, []);

  // データ取得
  const fetchSettingsData = async () => {
    setLoading(true);
    try {
      // 実際のAPI呼び出し（現在はモック）
      await new Promise(resolve => setTimeout(resolve, 500));
      setSystemSettings(mockSystemSettings);
      setSystemInfo(mockSystemInfo);
    } catch (error) {
      console.error('設定データ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          マスタ設定
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          システム固定値の確認表示（変更不可）
        </Typography>
      </Box>

      {/* 読み取り専用アラート */}
      <Alert severity="info" sx={{ mb: 3 }}>
        💡 このページの設定値は読み取り専用です。システムの動作を理解するための参考情報として表示されています。
      </Alert>

      {/* システム情報カード */}
      {systemInfo && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  システム名
                </Typography>
                <Typography variant="h6" fontWeight="bold">
                  {systemSettings?.systemName}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  バージョン
                </Typography>
                <Typography variant="h6" fontWeight="bold">
                  {systemInfo.version.application}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  総会員数
                </Typography>
                <Typography variant="h6" fontWeight="bold" color="primary.main">
                  {systemInfo.statistics.totalMembers}名
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    システム状態
                  </Typography>
                  <Chip 
                    label="正常稼働中" 
                    color="success" 
                    size="small" 
                    icon={<HealthAndSafety />}
                  />
                </Box>
                <IconButton onClick={fetchSettingsData} size="small">
                  <Refresh />
                </IconButton>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* タブ */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab icon={<Payment />} label="報酬・決済設定" />
          <Tab icon={<SettingsIcon />} label="システム設定" />
          <Tab icon={<Security />} label="セキュリティ設定" />
          <Tab icon={<Assessment />} label="システム情報" />
        </Tabs>
      </Paper>

      {systemSettings && (
        <>
          {/* タブ1: 報酬・決済設定 */}
          {tabValue === 0 && (
            <Box>
              {/* 参加費設定 */}
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    参加費設定
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>ヒーロープラン</strong></TableCell>
                          <TableCell>¥{systemSettings.participationFee.heroPlan.toLocaleString()}</TableCell>
                          <TableCell>
                            <Chip label="税込" size="small" color="info" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>テストプラン</strong></TableCell>
                          <TableCell>¥{systemSettings.participationFee.testPlan.toLocaleString()}</TableCell>
                          <TableCell>
                            <Chip label="無料" size="small" color="success" />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              {/* タイトル条件 */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    タイトル昇格条件
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>タイトル</strong></TableCell>
                          <TableCell><strong>個人売上</strong></TableCell>
                          <TableCell><strong>組織売上</strong></TableCell>
                          <TableCell><strong>直紹介</strong></TableCell>
                          <TableCell><strong>タイトルボーナス</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {systemSettings.titleSettings.titles.map((title) => (
                          <TableRow key={title.name}>
                            <TableCell>
                              <Chip 
                                label={title.name} 
                                size="small" 
                                variant="outlined"
                                color={title.order === 1 ? 'default' : 'primary'}
                              />
                            </TableCell>
                            <TableCell>
                              {title.requiredPersonalSales > 0 
                                ? `¥${title.requiredPersonalSales.toLocaleString()}`
                                : '-'
                              }
                            </TableCell>
                            <TableCell>
                              {title.requiredOrganizationSales > 0
                                ? `¥${title.requiredOrganizationSales.toLocaleString()}`
                                : '-'
                              }
                            </TableCell>
                            <TableCell>
                              {title.requiredDirectReferrals > 0
                                ? `${title.requiredDirectReferrals}名`
                                : '-'
                              }
                            </TableCell>
                            <TableCell>
                              {title.titleBonus > 0
                                ? `¥${title.titleBonus.toLocaleString()}`
                                : '-'
                              }
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              {/* 報酬率設定 */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    報酬率設定
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>基本報酬率</Typography>
                      <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>デイリーボーナス率</TableCell>
                              <TableCell>{(systemSettings.rewardSettings.dailyBonusRate * 100).toFixed(1)}%</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>リファラルボーナス率</TableCell>
                              <TableCell>{(systemSettings.rewardSettings.referralBonusRate * 100)}%</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>パワーボーナス率</Typography>
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableBody>
                            {Object.entries(systemSettings.rewardSettings.powerBonusRates).map(([level, rate]) => (
                              <TableRow key={level}>
                                <TableCell>{level}</TableCell>
                                <TableCell>{(rate * 100)}%</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>固定ボーナス</Typography>
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>メンテナンスボーナス（1キットあたり）</TableCell>
                              <TableCell>¥{systemSettings.rewardSettings.maintenanceBonusPerKit.toLocaleString()}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>セールスアクティビティボーナス</TableCell>
                              <TableCell>¥{systemSettings.rewardSettings.salesActivityBonus.toLocaleString()}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>ロイヤルファミリーボーナス</TableCell>
                              <TableCell>¥{systemSettings.rewardSettings.royalFamilyBonus.toLocaleString()}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* 支払設定 */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    支払設定
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>最低支払金額</strong></TableCell>
                          <TableCell>¥{systemSettings.payoutSettings.minimumPayoutAmount.toLocaleString()}</TableCell>
                          <TableCell>
                            <Chip label="未満は繰越" size="small" color="info" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>振込手数料</strong></TableCell>
                          <TableCell>¥{systemSettings.payoutSettings.bankTransferFee}</TableCell>
                          <TableCell>
                            <Chip label="会社負担" size="small" color="success" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>支払サイクル</strong></TableCell>
                          <TableCell>毎月{systemSettings.payoutSettings.payoutDate}日頃</TableCell>
                          <TableCell>
                            <Chip label="月次" size="small" color="primary" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>源泉徴収税率</strong></TableCell>
                          <TableCell>{(systemSettings.payoutSettings.withholdingTax.businessRate * 100).toFixed(2)}%</TableCell>
                          <TableCell>
                            <Chip 
                              label={systemSettings.payoutSettings.withholdingTax.enabled ? '適用' : '無効'} 
                              size="small" 
                              color={systemSettings.payoutSettings.withholdingTax.enabled ? 'warning' : 'default'} 
                            />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}

          {/* タブ2: システム設定 */}
          {tabValue === 1 && (
            <Box>
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    基本設定
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>会員番号桁数</strong></TableCell>
                          <TableCell>{systemSettings.memberNumberDigits}桁</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>1ページあたり最大表示件数</strong></TableCell>
                          <TableCell>{systemSettings.maxMembersPerPage}件</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>報酬計算日</strong></TableCell>
                          <TableCell>毎月{systemSettings.rewardSettings.calculationDate}日</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    システム制限
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>最大会員数</strong></TableCell>
                          <TableCell>{systemSettings.systemLimits.maxMembersTotal}名</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>最大同時接続ユーザー数</strong></TableCell>
                          <TableCell>{systemSettings.systemLimits.maxConcurrentUsers}名</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>最大ファイルアップロードサイズ</strong></TableCell>
                          <TableCell>{systemSettings.systemLimits.maxFileUploadSize}MB</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>最大組織階層深度</strong></TableCell>
                          <TableCell>{systemSettings.systemLimits.maxOrganizationDepth}階層</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}

          {/* タブ3: セキュリティ設定 */}
          {tabValue === 2 && (
            <Box>
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    認証・セッション
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>セッションタイムアウト</strong></TableCell>
                          <TableCell>{systemSettings.securitySettings.sessionTimeout}分</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>最大ログイン試行回数</strong></TableCell>
                          <TableCell>{systemSettings.securitySettings.maxLoginAttempts}回</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>ロックアウト時間</strong></TableCell>
                          <TableCell>{systemSettings.securitySettings.lockoutDuration}分</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    データ保持設定
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>アクティビティログ保持期間</strong></TableCell>
                          <TableCell>{systemSettings.dataRetentionSettings.activityLogRetentionDays}日</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>決済履歴保持期間</strong></TableCell>
                          <TableCell>{systemSettings.dataRetentionSettings.paymentHistoryRetentionMonths}ヶ月</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>会員データ保持期間</strong></TableCell>
                          <TableCell>{systemSettings.dataRetentionSettings.memberDataRetentionYears}年</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>自動クリーンアップ</strong></TableCell>
                          <TableCell>
                            <Chip 
                              label={systemSettings.dataRetentionSettings.autoCleanupEnabled ? '有効' : '無効'} 
                              size="small"
                              color={systemSettings.dataRetentionSettings.autoCleanupEnabled ? 'success' : 'default'}
                            />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}

          {/* タブ4: システム情報 */}
          {tabValue === 3 && systemInfo && (
            <Box>
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    バージョン情報
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        {Object.entries(systemInfo.version).map(([key, version]) => (
                          <TableRow key={key}>
                            <TableCell><strong>{key}</strong></TableCell>
                            <TableCell>{version}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    リソース使用状況
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="body2" color="text.secondary">
                            CPU使用率
                          </Typography>
                          <Typography variant="h4" color="primary.main">
                            {systemInfo.resources.cpuUsage}%
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="body2" color="text.secondary">
                            メモリ使用率
                          </Typography>
                          <Typography variant="h4" color="warning.main">
                            {systemInfo.resources.memoryUsage}%
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="body2" color="text.secondary">
                            ディスク使用率
                          </Typography>
                          <Typography variant="h4" color="success.main">
                            {systemInfo.resources.diskUsage}%
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="body2" color="text.secondary">
                            アクティブユーザー数
                          </Typography>
                          <Typography variant="h4" color="info.main">
                            {systemInfo.resources.activeUsers}名
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6" fontWeight="600">
                    統計情報
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>総会員数</strong></TableCell>
                          <TableCell>{systemInfo.statistics.totalMembers}名</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>アクティブ会員数</strong></TableCell>
                          <TableCell>{systemInfo.statistics.activeMembers}名</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>累計報酬総額</strong></TableCell>
                          <TableCell>¥{systemInfo.statistics.totalRewards.toLocaleString()}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>累計支払総額</strong></TableCell>
                          <TableCell>¥{systemInfo.statistics.totalPayouts.toLocaleString()}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>最終報酬計算日</strong></TableCell>
                          <TableCell>{systemInfo.statistics.lastCalculationDate}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>最終支払実行日</strong></TableCell>
                          <TableCell>{systemInfo.statistics.lastPayoutDate}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default Settings;