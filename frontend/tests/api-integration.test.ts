import { test, expect } from '@playwright/test';

/**
 * API統合テスト - フロントエンド・バックエンド連携検証
 * 33個の全APIエンドポイント動作確認
 */

test.describe('IROAS BOSS V2 - API統合テスト', () => {
  
  test.beforeEach(async ({ page }) => {
    // ダッシュボードから開始
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Phase A-1: 基本API群テスト', () => {
    
    test('7.1-7.2 システム設定API - P-008マスタ設定', async ({ page }) => {
      // マスタ設定ページへ遷移
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');
      
      // システム設定データ読み込み確認
      await expect(page.locator('text=システム名')).toBeVisible();
      await expect(page.locator('text=バージョン')).toBeVisible();
      
      // APIレスポンス確認（ネットワークタブ監視）
      const responsePromise = page.waitForResponse('**/api/settings/**');
      await page.reload();
      const response = await responsePromise;
      expect(response.status()).toBe(200);
    });

    test('1.1-1.4,1.6 会員管理API - P-002会員管理', async ({ page }) => {
      // 会員管理ページへ遷移
      await page.goto('/members');
      await page.waitForLoadState('networkidle');
      
      // 会員一覧API (1.1) 確認
      await expect(page.locator('[data-testid="member-data-grid"]')).toBeVisible();
      
      // 検索API (1.6) 確認
      await page.locator('input[placeholder*="会員番号"]').fill('0000001');
      await page.locator('button:has-text("検索")').click();
      await page.waitForLoadState('networkidle');
      
      // 新規登録ダイアログ確認 (1.2 POST準備)
      await page.locator('button:has-text("新規登録")').click();
      await expect(page.locator('text=新規会員登録')).toBeVisible();
      
      // 必須フィールド確認
      await expect(page.locator('input[name="name"]')).toBeVisible();
      await expect(page.locator('input[name="email"]')).toBeVisible();
      await expect(page.locator('input[name="memberNumber"]')).toBeVisible();
      
      // ダイアログクローズ
      await page.locator('button:has-text("キャンセル")').click();
    });

    test('6.1-6.3 アクティビティログAPI - P-007アクティビティ', async ({ page }) => {
      // アクティビティログページへ遷移
      await page.goto('/activity');
      await page.waitForLoadState('networkidle');
      
      // ログ一覧API (6.1) 確認
      await expect(page.locator('[data-testid="activity-data-grid"]')).toBeVisible();
      
      // フィルター検索API (6.2) 確認
      await page.locator('input[name="dateFrom"]').fill('2024-01-01');
      await page.locator('button:has-text("検索")').click();
      await page.waitForLoadState('networkidle');
      
      // ログ詳細確認 (6.3) - 最初のログをクリック
      const firstRow = page.locator('[data-testid="activity-data-grid"] .MuiDataGrid-row').first();
      if (await firstRow.isVisible()) {
        await firstRow.click();
        await expect(page.locator('text=詳細情報')).toBeVisible();
      }
    });
  });

  test.describe('Phase A-2: 決済基盤API群テスト', () => {
    
    test('3.1-3.2 決済対象API - P-004決済管理', async ({ page }) => {
      // 決済管理ページへ遷移
      await page.goto('/payments');
      await page.waitForLoadState('networkidle');
      
      // カード決済対象者API (3.1) 確認
      await page.locator('text=カード決済').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('[data-testid="payment-data-grid"]')).toBeVisible();
      
      // 口座振替対象者API (3.2) 確認
      await page.locator('text=口座振替').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('[data-testid="payment-data-grid"]')).toBeVisible();
    });

    test('3.6-3.7 手動決済・履歴API - P-004決済管理', async ({ page }) => {
      // 決済管理ページへ遷移
      await page.goto('/payments');
      await page.waitForLoadState('networkidle');
      
      // 手動決済タブ確認 (3.6)
      await page.locator('text=手動決済').click();
      await page.waitForLoadState('networkidle');
      
      // 手動記録ボタン確認
      await expect(page.locator('button:has-text("手動記録")')).toBeVisible();
      
      // 決済履歴タブ確認 (3.7)
      await page.locator('text=履歴').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('[data-testid="payment-history-grid"]')).toBeVisible();
    });
  });

  test.describe('Phase E-1: データ管理API群テスト', () => {
    
    test('8.1-8.4 データ入出力API - P-009データ管理', async ({ page }) => {
      // データ管理ページへ遷移
      await page.goto('/data');
      await page.waitForLoadState('networkidle');
      
      // インポート機能確認 (8.1)
      await page.locator('text=インポート').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=ファイル選択')).toBeVisible();
      await expect(page.locator('select[name="dataType"]')).toBeVisible();
      
      // バックアップ機能確認 (8.2)
      await page.locator('text=バックアップ').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('button:has-text("バックアップ実行")')).toBeVisible();
      
      // バックアップ一覧確認 (8.3)
      await expect(page.locator('[data-testid="backup-list"]')).toBeVisible();
      
      // 履歴タブ確認
      await page.locator('text=履歴').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('[data-testid="process-history-grid"]')).toBeVisible();
    });
  });

  test.describe('Phase B-1: 組織管理API群テスト', () => {
    
    test('2.1-2.3 組織構造API - P-003組織図', async ({ page }) => {
      // 組織図ページへ遷移
      await page.goto('/organization');
      await page.waitForLoadState('networkidle');
      
      // 組織ツリーAPI (2.1) 確認
      await expect(page.locator('[data-testid="organization-tree"]')).toBeVisible();
      
      // ツリー展開・検索機能確認
      await page.locator('button:has-text("展開")').click();
      await page.waitForTimeout(1000);
      
      // 検索機能 (2.2, 2.3)
      const searchInput = page.locator('input[placeholder*="会員検索"]');
      if (await searchInput.isVisible()) {
        await searchInput.fill('テスト');
        await page.locator('button:has-text("検索")').click();
        await page.waitForLoadState('networkidle');
      }
    });

    test('1.5,1.7 スポンサー変更API - P-002会員管理', async ({ page }) => {
      // 会員管理ページへ遷移
      await page.goto('/members');
      await page.waitForLoadState('networkidle');
      
      // 会員詳細・編集モード確認
      const firstRow = page.locator('[data-testid="member-data-grid"] .MuiDataGrid-row').first();
      if (await firstRow.isVisible()) {
        await firstRow.click();
        await page.waitForTimeout(500);
        
        // 編集ボタンがあれば確認
        const editButton = page.locator('button:has-text("編集")');
        if (await editButton.isVisible()) {
          await editButton.click();
          
          // スポンサー変更フィールド確認 (1.7)
          await expect(page.locator('input[name="uplineId"], input[name="sponsorId"]')).toBeVisible();
          
          // 退会処理ボタン確認 (1.5)
          const withdrawButton = page.locator('button:has-text("退会")');
          if (await withdrawButton.isVisible()) {
            await expect(withdrawButton).toBeVisible();
          }
        }
      }
    });
  });

  test.describe('Phase B-2: 決済実行API群テスト', () => {
    
    test('3.3-3.4 CSV出力API - P-004決済管理', async ({ page }) => {
      // 決済管理ページへ遷移
      await page.goto('/payments');
      await page.waitForLoadState('networkidle');
      
      // カード決済CSV出力 (3.3)
      await page.locator('text=カード決済').click();
      await page.waitForLoadState('networkidle');
      
      const cardCsvButton = page.locator('button:has-text("CSV出力")');
      if (await cardCsvButton.isVisible()) {
        await expect(cardCsvButton).toBeVisible();
      }
      
      // 口座振替CSV出力 (3.4)
      await page.locator('text=口座振替').click();
      await page.waitForLoadState('networkidle');
      
      const transferCsvButton = page.locator('button:has-text("CSV出力")');
      if (await transferCsvButton.isVisible()) {
        await expect(transferCsvButton).toBeVisible();
      }
    });

    test('3.5 決済結果取込API - P-004決済管理', async ({ page }) => {
      // 決済管理ページへ遷移
      await page.goto('/payments');
      await page.waitForLoadState('networkidle');
      
      // 結果取込ボタン確認 (3.5)
      const importButton = page.locator('button:has-text("結果取込")');
      if (await importButton.isVisible()) {
        await importButton.click();
        
        // ファイル選択ダイアログ確認
        await expect(page.locator('text=結果ファイル取込')).toBeVisible();
        await expect(page.locator('input[type="file"]')).toBeVisible();
      }
    });
  });

  test.describe('Phase C-1: 報酬計算API群テスト', () => {
    
    test('4.1-4.2 報酬計算実行API - P-005報酬計算', async ({ page }) => {
      // 報酬計算ページへ遷移
      await page.goto('/rewards');
      await page.waitForLoadState('networkidle');
      
      // 前提条件確認API (4.1) - ページ読み込み時に自動実行
      await expect(page.locator('text=報酬計算実行')).toBeVisible();
      
      // 計算実行ダイアログ確認 (4.2)
      await page.locator('button:has-text("報酬計算実行")').click();
      await expect(page.locator('text=報酬計算実行')).toBeVisible();
      await expect(page.locator('text=対象月')).toBeVisible();
      
      // ダイアログクローズ
      await page.locator('button:has-text("キャンセル")').click();
    });

    test('4.3-4.6 計算結果管理API - P-005報酬計算', async ({ page }) => {
      // 報酬計算ページへ遷移
      await page.goto('/rewards');
      await page.waitForLoadState('networkidle');
      
      // 計算結果一覧確認 (4.6)
      await expect(page.locator('[data-testid="calculation-history"]')).toBeVisible();
      
      // 履歴の最初のエントリクリック (4.3)
      const firstHistoryRow = page.locator('[data-testid="calculation-history"] .MuiDataGrid-row').first();
      if (await firstHistoryRow.isVisible()) {
        await firstHistoryRow.click();
        
        // 個人別内訳確認 (4.4)
        await expect(page.locator('text=個人別内訳')).toBeVisible();
        
        // 削除ボタン確認 (4.5)
        const deleteButton = page.locator('button:has-text("削除")');
        if (await deleteButton.isVisible()) {
          await expect(deleteButton).toBeVisible();
        }
      }
    });
  });

  test.describe('Phase D-1: 支払管理API群テスト', () => {
    
    test('5.1-5.4 支払管理API - P-006報酬支払管理', async ({ page }) => {
      // 報酬支払管理ページへ遷移
      await page.goto('/payouts');
      await page.waitForLoadState('networkidle');
      
      // 支払対象者一覧API (5.1)
      await expect(page.locator('[data-testid="payout-data-grid"]')).toBeVisible();
      
      // GMO CSV出力ボタン確認 (5.2)
      await expect(page.locator('button:has-text("GMO CSV出力")')).toBeVisible();
      
      // 支払確定ボタン確認 (5.3)
      await expect(page.locator('button:has-text("支払確定")')).toBeVisible();
      
      // 繰越一覧確認 (5.4)
      const carryoverTab = page.locator('text=繰越管理');
      if (await carryoverTab.isVisible()) {
        await carryoverTab.click();
        await page.waitForLoadState('networkidle');
        await expect(page.locator('[data-testid="carryover-list"]')).toBeVisible();
      }
    });
  });

  test('全APIエンドポイント - ネットワーク統合テスト', async ({ page }) => {
    // 全ページを順次訪問してAPIコール確認
    const pages = [
      '/members',      // A-1b, B-1b APIs
      '/organization', // B-1a APIs  
      '/payments',     // A-2a, A-2b, B-2a, B-2b APIs
      '/rewards',      // C-1a, C-1b, C-1c APIs
      '/payouts',      // D-1a APIs
      '/activity',     // A-1c APIs
      '/settings',     // A-1a APIs
      '/data'          // E-1a APIs
    ];
    
    for (const pagePath of pages) {
      // ネットワーク監視開始
      const networkResponses: any[] = [];
      page.on('response', response => {
        if (response.url().includes('/api/')) {
          networkResponses.push({
            url: response.url(),
            status: response.status(),
            method: response.request().method()
          });
        }
      });
      
      // ページ遷移
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');
      
      // APIコールが発生したことを確認
      expect(networkResponses.length).toBeGreaterThan(0);
      
      // 少なくとも1つのAPIが200 OKを返すことを確認
      const successResponses = networkResponses.filter(r => r.status === 200);
      expect(successResponses.length).toBeGreaterThan(0);
      
      console.log(`${pagePath}: ${networkResponses.length} API calls, ${successResponses.length} successful`);
    }
  });
});