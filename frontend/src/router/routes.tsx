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
import NotFound from '@/pages/NotFound';

/**
 * ルート定義
 * 要件定義書の9ページ（P-001～P-009）に対応
 */

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Dashboard />, // P-001: ダッシュボード
      },
      {
        path: 'dashboard',
        element: <Dashboard />, // P-001: ダッシュボード
      },
      {
        path: 'members',
        children: [
          {
            index: true,
            element: <Members />, // P-002: 会員管理
          },
          {
            path: ':id',
            element: <Members />, // 会員詳細（P-002内）
          },
        ],
      },
      {
        path: 'organization',
        element: <Organization />, // P-003: 組織図ビューア
      },
      {
        path: 'payments',
        element: <Payments />, // P-004: 決済管理
      },
      {
        path: 'rewards',
        element: <Rewards />, // P-005: 報酬計算
      },
      {
        path: 'payouts',
        element: <Payouts />, // P-006: 報酬支払管理
      },
      {
        path: 'activity',
        element: <Activity />, // P-007: アクティビティログ
      },
      {
        path: 'settings',
        element: <Settings />, // P-008: マスタ設定
      },
      {
        path: 'data',
        element: <DataManagement />, // P-009: データ入出力
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