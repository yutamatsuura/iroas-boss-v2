import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Typography,
  Chip,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Alert,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  AccountTree,
  Person,
  ExpandMore,
  ExpandLess,
  Search,
  FilterList,
  Refresh,
  SwapHoriz,
  Visibility,
  Download,
} from '@mui/icons-material';
import { MemberService, Member, MemberStatus } from '@/services/memberService';

/**
 * P-003: 組織図ビューア
 * MLM組織構造の視覚的表示と階層確認
 * 要件定義書: 手動での組織調整（自動圧縮NG）
 */

// 組織ツリーノードインターフェース
interface OrganizationNode {
  id: number;
  memberNumber: string;
  name: string;
  title: string;
  level: number;
  totalSales?: number;
  personalSales?: number;
  children: OrganizationNode[];
  isExpanded?: boolean;
  status: MemberStatus;
}

const Organization: React.FC = () => {
  // State管理
  const [organizationData, setOrganizationData] = useState<OrganizationNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMember, setSelectedMember] = useState<OrganizationNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState<number | ''>('');
  const [showSponsorDialog, setShowSponsorDialog] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState<OrganizationNode[]>([]);
  const [viewMode, setViewMode] = useState<'tree' | 'table'>('tree');

  // 模擬組織データ
  const mockOrganizationData: OrganizationNode[] = [
    {
      id: 1,
      memberNumber: '0000001',
      name: '山田太郎',
      title: 'エリアディレクター',
      level: 1,
      totalSales: 5000000,
      personalSales: 500000,
      status: MemberStatus.ACTIVE,
      isExpanded: true,
      children: [
        {
          id: 2,
          memberNumber: '0000002',
          name: '佐藤花子',
          title: 'ディレクター',
          level: 2,
          totalSales: 2500000,
          personalSales: 300000,
          status: MemberStatus.ACTIVE,
          isExpanded: false,
          children: [
            {
              id: 3,
              memberNumber: '0000003',
              name: '田中次郎',
              title: 'マネージャー',
              level: 3,
              totalSales: 800000,
              personalSales: 200000,
              status: MemberStatus.ACTIVE,
              isExpanded: false,
              children: [],
            },
          ],
        },
        {
          id: 4,
          memberNumber: '0000004',
          name: '鈴木三郎',
          title: 'マネージャー',
          level: 2,
          totalSales: 1200000,
          personalSales: 250000,
          status: MemberStatus.INACTIVE,
          isExpanded: false,
          children: [],
        },
      ],
    },
  ];

  useEffect(() => {
    fetchOrganizationData();
  }, []);

  // データ取得
  const fetchOrganizationData = async () => {
    setLoading(true);
    try {
      // 実際のAPI呼び出し（現在はモック）
      await new Promise(resolve => setTimeout(resolve, 500)); // 模擬ローディング
      setOrganizationData(mockOrganizationData);
    } catch (error) {
      console.error('組織データ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  // ノード展開/折りたたみ
  const toggleNodeExpansion = (nodeId: number) => {
    const toggleNode = (nodes: OrganizationNode[]): OrganizationNode[] => {
      return nodes.map(node => {
        if (node.id === nodeId) {
          return { ...node, isExpanded: !node.isExpanded };
        }
        if (node.children.length > 0) {
          return { ...node, children: toggleNode(node.children) };
        }
        return node;
      });
    };
    setOrganizationData(toggleNode(organizationData));
  };

  // メンバー詳細表示
  const handleMemberDetail = (member: OrganizationNode) => {
    setSelectedMember(member);
    // パンくずリスト更新（実際は階層を遡って構築）
    setBreadcrumbs([member]);
  };

  // スポンサー変更ダイアログ表示
  const handleSponsorChange = (member: OrganizationNode) => {
    setSelectedMember(member);
    setShowSponsorDialog(true);
  };

  // 組織ツリーコンポーネント
  const OrganizationTreeNode: React.FC<{ 
    node: OrganizationNode; 
    depth: number;
  }> = ({ node, depth }) => {
    const getStatusColor = (status: MemberStatus) => {
      switch (status) {
        case MemberStatus.ACTIVE:
          return 'success';
        case MemberStatus.INACTIVE:
          return 'warning';
        case MemberStatus.WITHDRAWN:
          return 'error';
        default:
          return 'default';
      }
    };

    const getTitleColor = (title: string) => {
      if (title.includes('エリアディレクター')) return '#8b5cf6';
      if (title.includes('ディレクター')) return '#3b82f6';
      if (title.includes('マネージャー')) return '#10b981';
      if (title.includes('リーダー')) return '#f59e0b';
      return '#6b7280';
    };

    return (
      <Box key={node.id}>
        <Card
          sx={{
            mb: 1,
            ml: depth * 3,
            border: selectedMember?.id === node.id ? 2 : 1,
            borderColor: selectedMember?.id === node.id ? 'primary.main' : 'divider',
            cursor: 'pointer',
            '&:hover': {
              boxShadow: 2,
            },
          }}
          onClick={() => handleMemberDetail(node)}
        >
          <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {/* 展開/折りたたみボタン */}
              {node.children.length > 0 && (
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleNodeExpansion(node.id);
                  }}
                >
                  {node.isExpanded ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              )}

              {/* メンバー情報 */}
              <Person sx={{ color: 'primary.main' }} />
              
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {node.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ({node.memberNumber})
                  </Typography>
                  <Chip
                    label={node.status}
                    size="small"
                    color={getStatusColor(node.status)}
                  />
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 0.5 }}>
                  <Chip
                    label={node.title}
                    size="small"
                    sx={{
                      bgcolor: getTitleColor(node.title),
                      color: 'white',
                      fontSize: '0.7rem',
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    レベル {node.level}
                  </Typography>
                  {node.totalSales && (
                    <Typography variant="caption" color="text.secondary">
                      売上: ¥{node.totalSales.toLocaleString()}
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* アクションボタン */}
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                <IconButton
                  size="small"
                  color="primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleMemberDetail(node);
                  }}
                  title="詳細表示"
                >
                  <Visibility fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  color="warning"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSponsorChange(node);
                  }}
                  title="スポンサー変更"
                  disabled={node.status === MemberStatus.WITHDRAWN}
                >
                  <SwapHoriz fontSize="small" />
                </IconButton>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* 子ノード表示 */}
        {node.isExpanded && node.children.map(child => (
          <OrganizationTreeNode
            key={child.id}
            node={child}
            depth={depth + 1}
          />
        ))}
      </Box>
    );
  };

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          組織図ビューア
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          MLM組織構造の視覚的表示と階層確認
        </Typography>
      </Box>

      {/* パンくずナビ */}
      {breadcrumbs.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Breadcrumbs>
            <Link color="inherit" href="#" onClick={() => setBreadcrumbs([])}>
              組織全体
            </Link>
            {breadcrumbs.map((crumb, index) => (
              <Typography key={crumb.id} color="text.primary">
                {crumb.name} ({crumb.memberNumber})
              </Typography>
            ))}
          </Breadcrumbs>
        </Paper>
      )}

      {/* 検索・フィルター */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              label="会員検索"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="会員番号または氏名"
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>レベルフィルター</InputLabel>
              <Select
                value={filterLevel}
                label="レベルフィルター"
                onChange={(e) => setFilterLevel(e.target.value)}
              >
                <MenuItem value="">すべて</MenuItem>
                <MenuItem value={1}>レベル1</MenuItem>
                <MenuItem value={2}>レベル2</MenuItem>
                <MenuItem value={3}>レベル3</MenuItem>
                <MenuItem value={4}>レベル4</MenuItem>
                <MenuItem value={5}>レベル5以上</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<FilterList />}
            >
              フィルター
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<Download />}
                onClick={() => console.log('組織図CSV出力')}
              >
                CSV出力
              </Button>
              <IconButton onClick={fetchOrganizationData} color="primary">
                <Refresh />
              </IconButton>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* 組織統計 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                総メンバー数
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                50
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                最大階層
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                5
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                総売上
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                ¥12.5M
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                平均階層深度
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                3.2
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 組織ツリー表示 */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h6" fontWeight="600">
            組織階層構造
          </Typography>
          <Box>
            <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
              💡 要件: 退会時は手動で組織調整を行います（自動圧縮なし）
            </Alert>
          </Box>
        </Box>

        {loading ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography>組織データを読み込み中...</Typography>
          </Box>
        ) : (
          <Box>
            {organizationData.map(rootNode => (
              <OrganizationTreeNode
                key={rootNode.id}
                node={rootNode}
                depth={0}
              />
            ))}
          </Box>
        )}
      </Paper>

      {/* スポンサー変更ダイアログ */}
      <Dialog
        open={showSponsorDialog}
        onClose={() => setShowSponsorDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          スポンサー変更 - {selectedMember?.name}
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            スポンサー変更は組織構造に重大な影響を与えます。慎重に実行してください。
          </Alert>
          
          <TextField
            fullWidth
            label="新しいスポンサーの会員番号"
            margin="normal"
            placeholder="7桁の会員番号を入力"
          />
          
          <TextField
            fullWidth
            label="変更理由"
            margin="normal"
            multiline
            rows={3}
            placeholder="スポンサー変更の理由を詳しく記入してください"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSponsorDialog(false)}>
            キャンセル
          </Button>
          <Button 
            variant="contained"
            color="warning"
            onClick={() => {
              console.log('スポンサー変更実行');
              setShowSponsorDialog(false);
            }}
          >
            変更実行
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Organization;