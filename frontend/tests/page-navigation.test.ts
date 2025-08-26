import { test, expect } from '@playwright/test';

/**
 * P-001〜P-009 ページナビゲーション基本テスト
 * 全9ページの基本的な画面遷移と表示確認
 */

test.describe('IROAS BOSS V2 - ページナビゲーションテスト', () => {
  
  test.beforeEach(async ({ page }) => {
    // ダッシュボードページから開始
    await page.goto('/');
    
    // ページロード完了を待機
    await page.waitForLoadState('networkidle');
  });

  test('P-001 ダッシュボード - 基本表示確認', async ({ page }) => {
    // ページタイトル確認
    await expect(page).toHaveTitle(/IROAS BOSS V2/);
    
    // ヘッダー要素確認
    await expect(page.locator('h1')).toContainText('ダッシュボード');
    
    // ナビゲーションメニュー確認
    const nav = page.locator('nav');
    await expect(nav.locator('text=会員管理')).toBeVisible();
    await expect(nav.locator('text=組織図')).toBeVisible();
    await expect(nav.locator('text=決済管理')).toBeVisible();
    await expect(nav.locator('text=報酬計算')).toBeVisible();
    await expect(nav.locator('text=報酬支払')).toBeVisible();
    await expect(nav.locator('text=アクティビティ')).toBeVisible();
    await expect(nav.locator('text=設定')).toBeVisible();
    await expect(nav.locator('text=データ管理')).toBeVisible();
    
    // 統計カードの表示確認
    await expect(page.locator('text=総会員数')).toBeVisible();
    await expect(page.locator('text=アクティブ会員数')).toBeVisible();
    await expect(page.locator('text=今月の売上')).toBeVisible();
    await expect(page.locator('text=未処理決済')).toBeVisible();
  });

  test('P-002 会員管理ページ - 遷移・表示確認', async ({ page }) => {
    // 会員管理ページへ遷移
    await page.locator('nav').locator('text=会員管理').click();
    await page.waitForLoadState('networkidle');
    
    // URL確認
    expect(page.url()).toBe('http://localhost:5173/members');
    
    // ページタイトル確認
    await expect(page.locator('h1')).toContainText('会員管理');
    
    // 主要機能ボタン確認
    await expect(page.locator('text=新規登録')).toBeVisible();
    await expect(page.locator('text=CSV出力')).toBeVisible();
    await expect(page.locator('text=CSV取込')).toBeVisible();
    
    // DataGrid表示確認
    await expect(page.locator('[data-testid="member-data-grid"]')).toBeVisible();
    
    // 検索フォーム確認
    await expect(page.locator('input[placeholder*="会員番号"]')).toBeVisible();
    await expect(page.locator('input[placeholder*="会員名"]')).toBeVisible();
  });

  test('P-003 組織図ビューアページ - 遷移・表示確認', async ({ page }) => {
    // 組織図ページへ遷移
    await page.locator('nav').locator('text=組織図').click();
    await page.waitForLoadState('networkidle');
    
    // URL確認
    expect(page.url()).toBe('http://localhost:5173/organization');
    
    // ページタイトル確認
    await expect(page.locator('h1')).toContainText('組織図ビューア');
    
    // 組織図操作ボタン確認
    await expect(page.locator('text=展開')).toBeVisible();
    await expect(page.locator('text=折りたたみ')).toBeVisible();
    await expect(page.locator('text=検索')).toBeVisible();
    
    // 組織ツリー表示エリア確認
    await expect(page.locator('[data-testid="organization-tree"]')).toBeVisible();
  });

  test('P-004 決済管理ページ - 遷移・表示確認', async ({ page }) => {
    // 決済管理ページへ遷移
    await page.locator('nav').locator('text=決済管理').click();
    await page.waitForLoadState('networkidle');
    
    // URL確認
    expect(page.url()).toBe('http://localhost:5173/payments');
    
    // ページタイトル確認
    await expect(page.locator('h1')).toContainText('決済管理');
    
    // タブ表示確認
    await expect(page.locator('text=カード決済')).toBeVisible();
    await expect(page.locator('text=口座振替')).toBeVisible();
    await expect(page.locator('text=手動決済')).toBeVisible();
    await expect(page.locator('text=履歴')).toBeVisible();
    
    // 主要機能ボタン確認
    await expect(page.locator('text=CSV出力')).toBeVisible();
    await expect(page.locator('text=結果取込')).toBeVisible();
  });

  test('P-005 報酬計算ページ - 遷移・表示確認', async ({ page }) => {
    // 報酬計算ページへ遷移
    await page.locator('nav').locator('text=報酬計算').click();
    await page.waitForLoadState('networkidle');
    
    // URL確認
    expect(page.url()).toBe('http://localhost:5173/rewards');
    
    // ページタイトル確認
    await expect(page.locator('h1')).toContainText('報酬計算');
    
    // 計算実行ボタン確認
    await expect(page.locator('text=報酬計算実行')).toBeVisible();
    
    // 7種類ボーナス表示確認
    await expect(page.locator('text=デイリーボーナス')).toBeVisible();
    await expect(page.locator('text=タイトルボーナス')).toBeVisible();
    await expect(page.locator('text=リファラルボーナス')).toBeVisible();
    await expect(page.locator('text=パワーボーナス')).toBeVisible();
    await expect(page.locator('text=メンテナンスボーナス')).toBeVisible();
    await expect(page.locator('text=セールスアクティビティボーナス')).toBeVisible();
    await expect(page.locator('text=ロイヤルファミリーボーナス')).toBeVisible();
  });

  test('P-006 報酬支払管理ページ - 遷移・表示確認', async ({ page }) => {
    // 報酬支払管理ページへ遷移
    await page.locator('nav').locator('text=報酬支払').click();
    await page.waitForLoadState('networkidle');
    
    // URL確認
    expect(page.url()).toBe('http://localhost:5173/payouts');
    
    // ページタイトル確認
    await expect(page.locator('h1')).toContainText('報酬支払管理');
    
    // 主要機能ボタン確認
    await expect(page.locator('text=GMO CSV出力')).toBeVisible();
    await expect(page.locator('text=支払確定')).toBeVisible();
    
    // 支払対象者リスト確認
    await expect(page.locator('[data-testid="payout-data-grid"]')).toBeVisible();
  });

  test('P-007 アクティビティログページ - 遷移・表示確認', async ({ page }) => {
    // アクティビティログページへ遷移
    await page.locator('nav').locator('text=アクティビティ').click();
    await page.waitForLoadState('networkidle');
    
    // URL確認
    expect(page.url()).toBe('http://localhost:5173/activity');
    
    // ページタイトル確認
    await expect(page.locator('h1')).toContainText('アクティビティログ');
    
    // フィルター機能確認
    await expect(page.locator('text=日付範囲')).toBeVisible();
    await expect(page.locator('text=アクティビティタイプ')).toBeVisible();
    await expect(page.locator('text=ユーザー')).toBeVisible();
    
    // ログ一覧表示確認
    await expect(page.locator('[data-testid="activity-data-grid"]')).toBeVisible();
  });

  test('P-008 マスタ設定ページ - 遷移・表示確認', async ({ page }) => {
    // マスタ設定ページへ遷移
    await page.locator('nav').locator('text=設定').click();
    await page.waitForLoadState('networkidle');
    
    // URL確認
    expect(page.url()).toBe('http://localhost:5173/settings');
    
    // ページタイトル確認
    await expect(page.locator('h1')).toContainText('マスタ設定');
    
    // 設定カテゴリ確認
    await expect(page.locator('text=システム設定')).toBeVisible();
    await expect(page.locator('text=参加費設定')).toBeVisible();
    await expect(page.locator('text=タイトル設定')).toBeVisible();
    await expect(page.locator('text=報酬設定')).toBeVisible();
    await expect(page.locator('text=支払設定')).toBeVisible();
  });

  test('P-009 データ入出力管理ページ - 遷移・表示確認', async ({ page }) => {
    // データ入出力管理ページへ遷移
    await page.locator('nav').locator('text=データ管理').click();
    await page.waitForLoadState('networkidle');
    
    // URL確認
    expect(page.url()).toBe('http://localhost:5173/data');
    
    // ページタイトル確認
    await expect(page.locator('h1')).toContainText('データ入出力管理');
    
    // タブ表示確認
    await expect(page.locator('text=インポート')).toBeVisible();
    await expect(page.locator('text=エクスポート')).toBeVisible();
    await expect(page.locator('text=バックアップ')).toBeVisible();
    await expect(page.locator('text=履歴')).toBeVisible();
    
    // 主要機能確認
    await expect(page.locator('text=ファイル選択')).toBeVisible();
  });

  test('全ページナビゲーション - 順次遷移テスト', async ({ page }) => {
    const pages = [
      { name: '会員管理', url: '/members' },
      { name: '組織図', url: '/organization' },
      { name: '決済管理', url: '/payments' },
      { name: '報酬計算', url: '/rewards' },
      { name: '報酬支払', url: '/payouts' },
      { name: 'アクティビティ', url: '/activity' },
      { name: '設定', url: '/settings' },
      { name: 'データ管理', url: '/data' }
    ];
    
    for (const pageInfo of pages) {
      // ページ遷移
      await page.locator('nav').locator(`text=${pageInfo.name}`).click();
      await page.waitForLoadState('networkidle');
      
      // URL確認
      expect(page.url()).toBe(`http://localhost:5173${pageInfo.url}`);
      
      // ページが正常に読み込まれることを確認
      await expect(page.locator('h1')).toBeVisible();
      
      // 最低0.5秒待機（UX確認）
      await page.waitForTimeout(500);
    }
    
    // ダッシュボードに戻る
    await page.locator('nav').locator('text=ダッシュボード').click();
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBe('http://localhost:5173/');
  });
});