import { RouteObject } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import Dashboard from '@/pages/Dashboard';
import Members from '@/pages/Members';
import Organization from '@/pages/Organization';
import Payments from '@/pages/Payments';
import Rewards from '@/pages/Rewards';
import Payouts from '@/pages/Payouts';
import Activity from '@/pages/Activity';
import Settings from '@/pages/Settings';
import DataManagement from '@/pages/DataManagement';
import Login from '@/pages/Login';
import Profile from '@/pages/Profile';
import NotFound from '@/pages/NotFound';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { UserRole } from '@/contexts/AuthContext';

/**
 * ルート定義
 * 要件定義書の9ページ（P-001～P-009）に対応
 */

export const routes: RouteObject[] = [
  // 認証不要ルート
  {
    path: '/login',
    element: <Login />, // ログインページ
  },
  
  // 認証必須メインアプリケーション
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Dashboard />, // P-001: ダッシュボード
      },
      {
        path: 'dashboard',
        element: <Dashboard />, // P-001: ダッシュボード
      },
      
      // プロフィール設定
      {
        path: 'profile',
        element: <Profile />,
      },
      
      // 会員管理（MLM_MANAGER以上）
      {
        path: 'members',
        element: (
          <ProtectedRoute requiredPermissions={['member.view']}>
            <Members />
          </ProtectedRoute>
        ),
      },
      {
        path: 'members/:id',
        element: (
          <ProtectedRoute requiredPermissions={['member.view']}>
            <Members />
          </ProtectedRoute>
        ),
      },
      
      // 組織図（MLM_MANAGER以上）
      {
        path: 'organization',
        element: (
          <ProtectedRoute requiredPermissions={['organization.view']}>
            <Organization />
          </ProtectedRoute>
        ),
      },
      
      // 決済管理（MLM_MANAGER以上）
      {
        path: 'payments',
        element: (
          <ProtectedRoute requiredPermissions={['payment.view']}>
            <Payments />
          </ProtectedRoute>
        ),
      },
      
      // 報酬計算（MLM_MANAGER以上）
      {
        path: 'rewards',
        element: (
          <ProtectedRoute requiredPermissions={['reward.view']}>
            <Rewards />
          </ProtectedRoute>
        ),
      },
      
      // 支払管理（MLM_MANAGER以上）
      {
        path: 'payouts',
        element: (
          <ProtectedRoute requiredPermissions={['payout.view']}>
            <Payouts />
          </ProtectedRoute>
        ),
      },
      
      // アクティビティログ（管理者以上）
      {
        path: 'activity',
        element: (
          <ProtectedRoute requiredRoles={[UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MLM_MANAGER]}>
            <Activity />
          </ProtectedRoute>
        ),
      },
      
      // システム設定（全ユーザー閲覧可能）
      {
        path: 'settings',
        element: <Settings />, // P-008: マスタ設定
      },
      
      // データ管理（管理者以上）
      {
        path: 'data',
        element: (
          <ProtectedRoute requiredRoles={[UserRole.SUPER_ADMIN, UserRole.ADMIN]}>
            <DataManagement />
          </ProtectedRoute>
        ),
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />, // 404ページ
  },
];

// ナビゲーションメニュー項目定義
export interface NavMenuItem {
  id: string;
  title: string;
  path: string;
  icon: string;
  description?: string;
  badge?: number | string;
}

export const navigationMenuItems: NavMenuItem[] = [
  {
    id: 'dashboard',
    title: 'ダッシュボード',
    path: '/',
    icon: 'Dashboard',
    description: 'システム全体の状況を一目で把握',
  },
  {
    id: 'members',
    title: '会員管理',
    path: '/members',
    icon: 'People',
    description: '会員の登録・編集・退会処理・組織管理',
  },
  {
    id: 'organization',
    title: '組織図ビューア',
    path: '/organization',
    icon: 'AccountTree',
    description: 'MLM組織構造の視覚的表示と階層確認',
  },
  {
    id: 'payments',
    title: '決済管理',
    path: '/payments',
    icon: 'Payment',
    description: 'Univapay CSV出力、決済結果取込、手動決済記録',
  },
  {
    id: 'rewards',
    title: '報酬計算',
    path: '/rewards',
    icon: 'Calculate',
    description: '7種類のボーナス計算実行と計算結果確認',
  },
  {
    id: 'payouts',
    title: '報酬支払管理',
    path: '/payouts',
    icon: 'AccountBalance',
    description: 'GMOネットバンク振込CSV生成と支払履歴管理',
  },
  {
    id: 'activity',
    title: 'アクティビティログ',
    path: '/activity',
    icon: 'History',
    description: 'システムで実行された全操作の履歴を時系列で確認',
  },
  {
    id: 'settings',
    title: 'マスタ設定',
    path: '/settings',
    icon: 'Settings',
    description: 'システム固定値の確認表示のみ（変更不可）',
  },
  {
    id: 'data',
    title: 'データ入出力',
    path: '/data',
    icon: 'Storage',
    description: '各種CSV入出力、バックアップ、データ移行機能',
  },
];

export default routes;