import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Badge,
  Avatar,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  People,
  AccountTree,
  Payment,
  Calculate,
  AccountBalance,
  History,
  Settings,
  Storage,
  Notifications,
} from '@mui/icons-material';
import UserMenu from '@/components/auth/UserMenu';
import { navigationMenuItems } from '@/router/routes';

// アイコンマッピング
const iconMap: { [key: string]: React.ElementType } = {
  Dashboard,
  People,
  AccountTree,
  Payment,
  Calculate,
  AccountBalance,
  History,
  Settings,
  Storage,
};

const drawerWidth = 260;

/**
 * メインレイアウトコンポーネント
 * エンタープライズテーマのサイドバー + ヘッダーレイアウト
 */
const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    setMobileOpen(false);
  };

  // ドロワーコンテンツ
  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* ロゴ部分 */}
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            bgcolor: 'primary.main',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography variant="h6" color="white" fontWeight="bold">
            IB
          </Typography>
        </Box>
        <Box>
          <Typography variant="h6" fontWeight="bold" color="text.primary">
            IROAS BOSS
          </Typography>
          <Typography variant="caption" color="text.secondary">
            V2 Management System
          </Typography>
        </Box>
      </Box>
      
      <Divider />
      
      {/* ナビゲーションメニュー */}
      <List sx={{ flex: 1, px: 1, py: 1 }}>
        {navigationMenuItems.map((item) => {
          const Icon = iconMap[item.icon] || Dashboard;
          const isActive = location.pathname === item.path || 
                          (item.path !== '/' && location.pathname.startsWith(item.path));
          
          return (
            <Tooltip key={item.id} title={item.description || ''} placement="right" arrow>
              <ListItemButton
                onClick={() => handleNavigate(item.path)}
                selected={isActive}
                sx={{
                  borderRadius: 1.5,
                  mb: 0.5,
                  ...(isActive && {
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': {
                      bgcolor: 'primary.dark',
                    },
                    '& .MuiListItemIcon-root': {
                      color: 'white',
                    },
                  }),
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {item.badge ? (
                    <Badge badgeContent={item.badge} color="error">
                      <Icon fontSize="small" />
                    </Badge>
                  ) : (
                    <Icon fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText 
                  primary={item.title}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: isActive ? 600 : 400,
                  }}
                />
              </ListItemButton>
            </Tooltip>
          );
        })}
      </List>
      
      <Divider />
      
      {/* バージョン情報 */}
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Version 1.0.0
        </Typography>
        <br />
        <Typography variant="caption" color="text.secondary">
          © 2025 IROAS
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* ヘッダー */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          bgcolor: 'background.paper',
          color: 'text.primary',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navigationMenuItems.find((item) => 
              location.pathname === item.path || 
              (item.path !== '/' && location.pathname.startsWith(item.path))
            )?.title || 'ダッシュボード'}
          </Typography>
          
          {/* 右側のツールバー項目 */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* 通知アイコン */}
            <IconButton color="inherit">
              <Badge badgeContent={3} color="error">
                <Notifications />
              </Badge>
            </IconButton>
            
            {/* ユーザーメニュー（認証機能統合） */}
            <UserMenu />
          </Box>
        </Toolbar>
      </AppBar>
      
      {/* サイドバー */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        {/* モバイル用ドロワー */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // モバイルでのパフォーマンス向上
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              bgcolor: 'background.paper',
            },
          }}
        >
          {drawerContent}
        </Drawer>
        
        {/* デスクトップ用ドロワー */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              bgcolor: 'background.paper',
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>
      
      {/* メインコンテンツ */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          bgcolor: 'background.default',
          mt: 8, // AppBarの高さ分
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;