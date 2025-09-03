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
const collapsedDrawerWidth = 60;

/**
 * メインレイアウトコンポーネント
 * エンタープライズテーマのサイドバー + ヘッダーレイアウト（開閉式対応）
 */
const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [desktopOpen, setDesktopOpen] = useState(true);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleDesktopDrawerToggle = () => {
    setDesktopOpen(!desktopOpen);
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    setMobileOpen(false);
  };

  // ドロワーコンテンツ（開閉対応）
  const drawerContent = (isCollapsed: boolean = false) => (
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
        {!isCollapsed && (
          <Box>
            <Typography variant="h6" fontWeight="bold" color="text.primary">
              IROAS BOSS
            </Typography>
            <Typography variant="caption" color="text.secondary">
              V2 Management System
            </Typography>
          </Box>
        )}
      </Box>
      
      <Divider />
      
      {/* ナビゲーションメニュー */}
      <List sx={{ flex: 1, px: 1, py: 1 }}>
        {navigationMenuItems.map((item) => {
          const Icon = iconMap[item.icon] || Dashboard;
          const isActive = location.pathname === item.path || 
                          (item.path !== '/' && location.pathname.startsWith(item.path));
          
          return (
            <Tooltip key={item.id} title={isCollapsed ? item.title : (item.description || '')} placement="right" arrow>
              <ListItemButton
                onClick={() => handleNavigate(item.path)}
                selected={isActive}
                sx={{
                  borderRadius: 1.5,
                  mb: 0.5,
                  justifyContent: isCollapsed ? 'center' : 'flex-start',
                  ...(isActive && {
                    bgcolor: '#e3f2fd',
                    color: '#1565c0',
                    border: '1px solid #1976d2',
                    '&:hover': {
                      bgcolor: '#bbdefb',
                    },
                    '& .MuiListItemIcon-root': {
                      color: '#1565c0',
                    },
                    '& .MuiListItemText-primary': {
                      color: '#1565c0 !important',
                      fontWeight: '600 !important',
                    },
                  }),
                }}
              >
                <ListItemIcon sx={{ minWidth: isCollapsed ? 'unset' : 40, justifyContent: 'center' }}>
                  {item.badge ? (
                    <Badge badgeContent={item.badge} color="error">
                      <Icon fontSize="small" />
                    </Badge>
                  ) : (
                    <Icon fontSize="small" />
                  )}
                </ListItemIcon>
                {!isCollapsed && (
                  <ListItemText 
                    primary={item.title}
                    primaryTypographyProps={{
                      fontSize: '0.875rem',
                      fontWeight: isActive ? 600 : 400,
                      color: isActive ? 'primary.dark' : 'inherit',
                    }}
                  />
                )}
              </ListItemButton>
            </Tooltip>
          );
        })}
      </List>
      
      <Divider />
      
      {/* バージョン情報 */}
      {!isCollapsed && (
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Version 1.0.0
          </Typography>
          <br />
          <Typography variant="caption" color="text.secondary">
            © 2025 IROAS
          </Typography>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* ヘッダー */}
      <AppBar
        position="fixed"
        sx={{
          width: { 
            sm: `calc(100% - ${desktopOpen ? drawerWidth : collapsedDrawerWidth}px)` 
          },
          ml: { 
            sm: `${desktopOpen ? drawerWidth : collapsedDrawerWidth}px` 
          },
          bgcolor: 'background.paper',
          color: 'text.primary',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
          transition: 'margin-left 0.3s, width 0.3s',
        }}
      >
        <Toolbar>
          {/* モバイル用メニューボタン */}
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          {/* デスクトップ用メニューボタン */}
          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            edge="start"
            onClick={handleDesktopDrawerToggle}
            sx={{ mr: 2, display: { xs: 'none', sm: 'block' } }}
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
        sx={{ 
          width: { sm: desktopOpen ? drawerWidth : collapsedDrawerWidth }, 
          flexShrink: { sm: 0 },
          transition: 'width 0.3s',
        }}
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
          {drawerContent(false)}
        </Drawer>
        
        {/* デスクトップ用ドロワー */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: desktopOpen ? drawerWidth : collapsedDrawerWidth,
              bgcolor: 'background.paper',
              borderRight: '1px solid',
              borderColor: 'divider',
              transition: 'width 0.3s',
              overflowX: 'hidden',
            },
          }}
          open
        >
          {drawerContent(!desktopOpen)}
        </Drawer>
      </Box>
      
      {/* メインコンテンツ */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { 
            sm: `calc(100% - ${desktopOpen ? drawerWidth : collapsedDrawerWidth}px)` 
          },
          minHeight: '100vh',
          bgcolor: 'background.default',
          mt: 8, // AppBarの高さ分
          transition: 'width 0.3s',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;