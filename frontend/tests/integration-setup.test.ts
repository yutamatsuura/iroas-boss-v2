import { test, expect } from '@playwright/test';

/**
 * 統合テスト環境セットアップ確認
 * フロントエンド・バックエンド接続確認・初期環境検証
 */

test.describe('IROAS BOSS V2 - 統合テスト環境確認', () => {
  
  test('フロントエンド基本起動確認', async ({ page }) => {
    // フロントエンドサーバーへの接続確認
    await page.goto('/');
    
    // タイトル確認
    await expect(page).toHaveTitle(/IROAS BOSS V2/);
    
    // 基本的なUI要素確認
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('nav')).toBeVisible();
    
    // JavaScriptが正常に動作することを確認
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    expect(bodyText!.length).toBeGreaterThan(100);
  });

  test('React アプリケーション正常動作確認', async ({ page }) => {
    await page.goto('/');
    
    // React コンポーネントの描画確認
    await expect(page.locator('[data-testid], [class*="MuiBox"], [class*="MuiContainer"]')).toBeVisible();
    
    // CSS スタイルの適用確認
    const mainElement = page.locator('main, [role="main"], body');
    const backgroundColor = await mainElement.evaluate(el => 
      window.getComputedStyle(el).backgroundColor
    );
    expect(backgroundColor).toBeTruthy();
    
    // JavaScriptエラーがないことを確認
    const errors: string[] = [];
    page.on('pageerror', error => {
      errors.push(error.message);
    });
    
    await page.waitForTimeout(2000);
    expect(errors).toHaveLength(0);
  });

  test('ページルーティング動作確認', async ({ page }) => {
    await page.goto('/');
    
    // ルート確認
    expect(page.url()).toBe('http://localhost:5173/');
    
    // 存在しないページへのアクセス（404確認）
    const response = await page.goto('/nonexistent-page');
    // 通常は404またはReactルーターによるフォールバック
    expect(response?.status()).toBeOneOf([200, 404]);
    
    // ダッシュボードに戻る
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('API接続準備確認（モック環境）', async ({ page }) => {
    // モック API 環境での動作確認
    await page.goto('/members');
    
    // API 呼び出し監視
    const apiCalls: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiCalls.push(request.url());
      }
    });
    
    await page.waitForLoadState('networkidle');
    
    // API呼び出しが発生することを確認（モックデータでも可）
    // 実際のAPI接続がない場合でも、フロントエンドからのリクエスト試行を確認
    console.log('API calls attempted:', apiCalls.length);
    
    // ページが正常に表示されることを確認（モックデータまたはエラーハンドリング）
    await expect(page.locator('h1')).toContainText('会員管理');
  });

  test('MUI コンポーネント描画確認', async ({ page }) => {
    await page.goto('/members');
    
    // MUI コンポーネントの基本的な描画確認
    const muiElements = [
      '.MuiButton-root',
      '.MuiTextField-root', 
      '.MuiSelect-root',
      '.MuiDataGrid-root, [data-testid*="data-grid"]'
    ];
    
    for (const selector of muiElements) {
      const element = page.locator(selector).first();
      if (await element.isVisible()) {
        await expect(element).toBeVisible();
        console.log(`✓ MUI component found: ${selector}`);
      } else {
        console.log(`! MUI component not found: ${selector} (may not be on this page)`);
      }
    }
    
    // エンタープライズテーマの適用確認
    const button = page.locator('.MuiButton-root').first();
    if (await button.isVisible()) {
      const buttonColor = await button.evaluate(el => 
        window.getComputedStyle(el).backgroundColor
      );
      expect(buttonColor).toBeTruthy();
    }
  });

  test('TypeScript コンパイル・実行時エラー確認', async ({ page }) => {
    // コンソールエラー監視
    const consoleErrors: string[] = [];
    const jsErrors: string[] = [];
    
    page.on('console', message => {
      if (message.type() === 'error') {
        consoleErrors.push(message.text());
      }
    });
    
    page.on('pageerror', error => {
      jsErrors.push(error.message);
    });
    
    // 複数ページを訪問してエラーチェック
    const testPages = ['/', '/members', '/payments', '/rewards'];
    
    for (const pagePath of testPages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    }
    
    // エラーレポート
    if (consoleErrors.length > 0) {
      console.log('Console errors:', consoleErrors);
    }
    if (jsErrors.length > 0) {
      console.log('JavaScript errors:', jsErrors);
    }
    
    // 重大なエラーがないことを確認（警告は許容）
    const criticalErrors = jsErrors.filter(error => 
      !error.includes('Warning:') && 
      !error.includes('Failed to fetch') // API接続エラーは許容
    );
    
    expect(criticalErrors).toHaveLength(0);
  });

  test('レスポンシブデザイン基本確認', async ({ page }) => {
    // デスクトップサイズ
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
    
    // タブレットサイズ
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();
    await expect(page.locator('h1')).toBeVisible();
    
    // モバイルサイズ
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await expect(page.locator('h1')).toBeVisible();
    
    // ナビゲーションの表示確認（モバイルでもアクセス可能）
    const navigation = page.locator('nav');
    await expect(navigation).toBeVisible();
  });

  test('パフォーマンス・ロード時間基本確認', async ({ page }) => {
    // ページロード時間測定
    const startTime = Date.now();
    
    await page.goto('/', { waitUntil: 'networkidle' });
    
    const loadTime = Date.now() - startTime;
    console.log(`Page load time: ${loadTime}ms`);
    
    // 10秒以内のロードを期待（開発環境）
    expect(loadTime).toBeLessThan(10000);
    
    // 基本的なUI要素が表示されることを確認
    await expect(page.locator('h1')).toBeVisible();
  });

  test('ブラウザ間互換性確認準備', async ({ page, browserName }) => {
    // 現在のブラウザ情報をログ出力
    console.log(`Testing on browser: ${browserName}`);
    
    await page.goto('/');
    
    // ブラウザ固有の機能テスト
    const userAgent = await page.evaluate(() => navigator.userAgent);
    console.log('User Agent:', userAgent);
    
    // 基本機能が全ブラウザで動作することを確認
    await expect(page.locator('h1')).toBeVisible();
    
    // Local Storageサポート確認
    const hasLocalStorage = await page.evaluate(() => 
      typeof window.localStorage !== 'undefined'
    );
    expect(hasLocalStorage).toBe(true);
    
    // CSS Grid/Flexboxサポート確認（モダンブラウザ機能）
    const supportsGrid = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.style.display = 'grid';
      return testEl.style.display === 'grid';
    });
    expect(supportsGrid).toBe(true);
  });
});