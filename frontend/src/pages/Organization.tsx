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
import { 
  OrganizationService, 
  OrganizationNode, 
  OrganizationTree, 
  OrganizationStats 
} from '@/services/organizationService';

/**
 * P-003: 組織図ビューア
 * MLM組織構造の視覚的表示と階層確認
 * 要件定義書: 手動での組織調整（自動圧縮NG）
 */

// フロントエンド用組織ノード（レガシー互換性のため）
interface LegacyOrganizationNode {
  id: number;
  memberNumber: string;
  name: string;
  title: string;
  level: number;
  totalSales?: number;
  personalSales?: number;
  children: LegacyOrganizationNode[];
  isExpanded?: boolean;
  status: string;
}

const Organization: React.FC = () => {
  // State管理
  const [organizationData, setOrganizationData] = useState<OrganizationNode[]>([]);
  const [organizationStats, setOrganizationStats] = useState<OrganizationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedMember, setSelectedMember] = useState<OrganizationNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState<number | ''>('');
  const [showSponsorDialog, setShowSponsorDialog] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState<OrganizationNode[]>([]);
  const [viewMode, setViewMode] = useState<'tree' | 'table'>('tree');


  useEffect(() => {
    fetchOrganizationData();
  }, []);

  // データ取得
  const fetchOrganizationData = async () => {
    setLoading(true);
    try {
      // 組織ツリーデータを取得
      const treeData = await OrganizationService.getOrganizationTree();
      setOrganizationData(treeData.root_nodes);
      
      // 組織統計データを取得
      const stats = await OrganizationService.getOrganizationStats();
      setOrganizationStats(stats);
    } catch (error) {
      console.error('組織データ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  // ノード展開/折りたたみ
  const toggleNodeExpansion = (nodeId: string) => {
    const updatedData = OrganizationService.toggleNodeExpansion(organizationData, nodeId);
    setOrganizationData(updatedData);
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
    const getStatusColor = OrganizationService.getStatusColor;
    const getTitleColor = OrganizationService.getTitleColor;

    return (
      <Box key={node.id}>
        <Card
          sx={{
            mb: 1,
            ml: depth * 3,
            border: selectedMember?.id === node.id ? 2 : 1,
            borderColor: selectedMember?.id === node.id ? 'primary.main' : 'divider',
            cursor: 'pointer',
            opacity: node.is_withdrawn ? 0.6 : 1,
            backgroundColor: node.is_withdrawn ? '#f5f5f5' : 'inherit',
            borderStyle: node.is_withdrawn ? 'dashed' : 'solid',
            '&:hover': {
              boxShadow: node.is_withdrawn ? 1 : 2,
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
                  {node.is_expanded ? <ExpandLess /> : <ExpandMore />}
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
                    ({node.member_number})
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
                  {(node.left_sales + node.right_sales > 0) && (
                    <Typography variant="caption" color="text.secondary">
                      売上: ¥{(node.left_sales + node.right_sales).toLocaleString()}
                    </Typography>
                  )}
                  {node.is_direct && (
                    <Chip label="直" size="small" color="primary" variant="outlined" />
                  )}
                  {node.is_withdrawn && (
                    <Chip label="退" size="small" color="error" variant="outlined" />
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
                  disabled={node.is_withdrawn}
                >
                  <SwapHoriz fontSize="small" />
                </IconButton>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* 子ノード表示 */}
        {node.is_expanded && node.children.map(child => (
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
                {crumb.name} ({crumb.member_number})
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
                onClick={() => OrganizationService.downloadCsv('binary')}
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
                アクティブメンバー
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="success.main">
                {organizationStats?.active_members || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                退会者: {organizationStats?.withdrawn_members || 0}名
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
                {organizationStats?.max_level || 0}
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
                ¥{organizationStats ? (organizationStats.total_sales / 1000000).toFixed(1) : 0}M
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
                {organizationStats?.average_level?.toFixed(1) || 0}
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