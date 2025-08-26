import { test, expect } from '@playwright/test';

/**
 * UI機能テスト - ユーザーインタラクション・エラーハンドリング検証
 * フォーム操作、ダイアログ、検索、フィルタリング機能確認
 */

test.describe('IROAS BOSS V2 - UI機能テスト', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.describe('P-002 会員管理 - UI機能テスト', () => {
    
    test('会員検索・フィルタリング機能', async ({ page }) => {
      await page.goto('/members');
      await page.waitForLoadState('networkidle');
      
      // 会員番号検索
      await page.locator('input[placeholder*="会員番号"]').fill('0000001');
      await page.locator('button:has-text("検索")').click();
      await page.waitForLoadState('networkidle');
      
      // 会員名検索
      await page.locator('input[placeholder*="会員番号"]').clear();
      await page.locator('input[placeholder*="会員名"]').fill('山田');
      await page.locator('button:has-text("検索")').click();
      await page.waitForLoadState('networkidle');
      
      // ステータスフィルター
      const statusFilter = page.locator('select[name="status"]');
      if (await statusFilter.isVisible()) {
        await statusFilter.selectOption('アクティブ');
        await page.waitForLoadState('networkidle');
      }
      
      // 検索クリア
      await page.locator('button:has-text("クリア")').click();
      await page.waitForLoadState('networkidle');
    });

    test('新規会員登録フォーム - 入力検証', async ({ page }) => {
      await page.goto('/members');
      await page.waitForLoadState('networkidle');
      
      // 新規登録ダイアログを開く
      await page.locator('button:has-text("新規登録")').click();
      await expect(page.locator('text=新規会員登録')).toBeVisible();
      
      // 必須フィールドバリデーション
      await page.locator('button:has-text("登録")').click();
      await expect(page.locator('text=必須項目です')).toBeVisible();
      
      // 正常入力
      await page.locator('input[name="name"]').fill('テスト 太郎');
      await page.locator('input[name="nameKana"]').fill('テスト タロウ');
      await page.locator('input[name="email"]').fill('test@example.com');
      await page.locator('input[name="memberNumber"]').fill('0000999');
      
      // プラン選択
      await page.locator('select[name="plan"]').selectOption('ヒーロープラン');
      
      // 決済方法選択
      await page.locator('select[name="paymentMethod"]').selectOption('カード決済');
      
      // キャンセルして閉じる
      await page.locator('button:has-text("キャンセル")').click();
      await expect(page.locator('text=新規会員登録')).not.toBeVisible();
    });

    test('会員詳細・編集機能', async ({ page }) => {
      await page.goto('/members');
      await page.waitForLoadState('networkidle');
      
      // 最初の会員をクリック
      const firstRow = page.locator('[data-testid="member-data-grid"] .MuiDataGrid-row').first();
      if (await firstRow.isVisible()) {
        await firstRow.click();
        await page.waitForTimeout(500);
        
        // 詳細ダイアログが開くことを確認
        await expect(page.locator('text=会員詳細')).toBeVisible();
        
        // 編集モードに切り替え
        const editButton = page.locator('button:has-text("編集")');
        if (await editButton.isVisible()) {
          await editButton.click();
          
          // フィールドが編集可能になることを確認
          await expect(page.locator('input[name="name"]')).not.toBeDisabled();
          
          // 変更をキャンセル
          await page.locator('button:has-text("キャンセル")').click();
        }
        
        // ダイアログを閉じる
        await page.keyboard.press('Escape');
      }
    });
  });

  test.describe('P-004 決済管理 - UI機能テスト', () => {
    
    test('タブ切り替え・CSV機能', async ({ page }) => {
      await page.goto('/payments');
      await page.waitForLoadState('networkidle');
      
      // カード決済タブ
      await page.locator('text=カード決済').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('[data-testid="payment-data-grid"]')).toBeVisible();
      
      // CSV出力ボタンクリック
      const csvButton = page.locator('button:has-text("CSV出力")');
      if (await csvButton.isVisible()) {
        await csvButton.click();
        // 出力確認ダイアログ
        await expect(page.locator('text=CSV出力')).toBeVisible();
        await page.locator('button:has-text("キャンセル")').click();
      }
      
      // 口座振替タブ
      await page.locator('text=口座振替').click();
      await page.waitForLoadState('networkidle');
      
      // 手動決済タブ
      await page.locator('text=手動決済').click();
      await page.waitForLoadState('networkidle');
      
      // 手動記録ダイアログ
      const manualButton = page.locator('button:has-text("手動記録")');
      if (await manualButton.isVisible()) {
        await manualButton.click();
        await expect(page.locator('text=手動決済記録')).toBeVisible();
        await page.locator('button:has-text("キャンセル")').click();
      }
      
      // 履歴タブ
      await page.locator('text=履歴').click();
      await page.waitForLoadState('networkidle');
    });

    test('決済結果取込機能', async ({ page }) => {
      await page.goto('/payments');
      await page.waitForLoadState('networkidle');
      
      // 結果取込ボタン
      const importButton = page.locator('button:has-text("結果取込")');
      if (await importButton.isVisible()) {
        await importButton.click();
        
        // ファイル選択ダイアログ
        await expect(page.locator('text=結果ファイル取込')).toBeVisible();
        await expect(page.locator('input[type="file"]')).toBeVisible();
        await expect(page.locator('select[name="paymentMethod"]')).toBeVisible();
        
        // キャンセル
        await page.locator('button:has-text("キャンセル")').click();
      }
    });
  });

  test.describe('P-005 報酬計算 - UI機能テスト', () => {
    
    test('報酬計算実行ダイアログ', async ({ page }) => {
      await page.goto('/rewards');
      await page.waitForLoadState('networkidle');
      
      // 計算実行ダイアログを開く
      await page.locator('button:has-text("報酬計算実行")').click();
      await expect(page.locator('text=報酬計算実行')).toBeVisible();
      
      // 対象月選択
      const monthSelect = page.locator('input[name="targetMonth"]');
      if (await monthSelect.isVisible()) {
        await monthSelect.fill('2024-01');
      }
      
      // 計算タイプ確認
      await expect(page.locator('text=デイリーボーナス')).toBeVisible();
      await expect(page.locator('text=タイトルボーナス')).toBeVisible();
      await expect(page.locator('text=リファラルボーナス')).toBeVisible();
      
      // キャンセル
      await page.locator('button:has-text("キャンセル")').click();
    });

    test('計算履歴・詳細表示', async ({ page }) => {
      await page.goto('/rewards');
      await page.waitForLoadState('networkidle');
      
      // 計算履歴確認
      const historyGrid = page.locator('[data-testid="calculation-history"]');
      if (await historyGrid.isVisible()) {
        // 最初の履歴エントリクリック
        const firstRow = historyGrid.locator('.MuiDataGrid-row').first();
        if (await firstRow.isVisible()) {
          await firstRow.click();
          
          // 詳細表示確認
          await expect(page.locator('text=計算詳細')).toBeVisible();
          await expect(page.locator('text=個人別内訳')).toBeVisible();
        }
      }
    });
  });

  test.describe('P-006 報酬支払管理 - UI機能テスト', () => {
    
    test('GMO CSV出力・支払確定', async ({ page }) => {
      await page.goto('/payouts');
      await page.waitForLoadState('networkidle');
      
      // GMO CSV出力
      const gmoCsvButton = page.locator('button:has-text("GMO CSV出力")');
      if (await gmoCsvButton.isVisible()) {
        await gmoCsvButton.click();
        await expect(page.locator('text=GMO振込用CSV出力')).toBeVisible();
        await page.locator('button:has-text("キャンセル")').click();
      }
      
      // 支払確定
      const confirmButton = page.locator('button:has-text("支払確定")');
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
        await expect(page.locator('text=支払確定')).toBeVisible();
        await page.locator('button:has-text("キャンセル")').click();
      }
      
      // 繰越管理タブ
      const carryoverTab = page.locator('text=繰越管理');
      if (await carryoverTab.isVisible()) {
        await carryoverTab.click();
        await page.waitForLoadState('networkidle');
      }
    });
  });

  test.describe('P-007 アクティビティログ - UI機能テスト', () => {
    
    test('ログ検索・フィルタリング', async ({ page }) => {
      await page.goto('/activity');
      await page.waitForLoadState('networkidle');
      
      // 日付範囲フィルター
      await page.locator('input[name="dateFrom"]').fill('2024-01-01');
      await page.locator('input[name="dateTo"]').fill('2024-12-31');
      
      // アクティビティタイプフィルター
      const typeSelect = page.locator('select[name="activityType"]');
      if (await typeSelect.isVisible()) {
        await typeSelect.selectOption('会員新規登録');
      }
      
      // ユーザーフィルター
      const userInput = page.locator('input[name="userId"]');
      if (await userInput.isVisible()) {
        await userInput.fill('admin');
      }
      
      // 検索実行
      await page.locator('button:has-text("検索")').click();
      await page.waitForLoadState('networkidle');
      
      // 検索クリア
      await page.locator('button:has-text("クリア")').click();
      await page.waitForLoadState('networkidle');
    });

    test('ログ詳細表示・エクスポート', async ({ page }) => {
      await page.goto('/activity');
      await page.waitForLoadState('networkidle');
      
      // 最初のログエントリクリック
      const firstRow = page.locator('[data-testid="activity-data-grid"] .MuiDataGrid-row').first();
      if (await firstRow.isVisible()) {
        await firstRow.click();
        await expect(page.locator('text=ログ詳細')).toBeVisible();
        await page.keyboard.press('Escape');
      }
      
      // エクスポート機能
      const exportButton = page.locator('button:has-text("CSV出力")');
      if (await exportButton.isVisible()) {
        await exportButton.click();
        await expect(page.locator('text=ログエクスポート')).toBeVisible();
        await page.locator('button:has-text("キャンセル")').click();
      }
    });
  });

  test.describe('P-009 データ管理 - UI機能テスト', () => {
    
    test('インポート機能UI', async ({ page }) => {
      await page.goto('/data');
      await page.waitForLoadState('networkidle');
      
      // インポートタブ
      await page.locator('text=インポート').click();
      await page.waitForLoadState('networkidle');
      
      // データタイプ選択
      await page.locator('select[name="dataType"]').selectOption('会員データ');
      
      // ファイル形式選択
      const formatSelect = page.locator('select[name="format"]');
      if (await formatSelect.isVisible()) {
        await formatSelect.selectOption('CSV');
      }
      
      // エンコーディング選択
      const encodingSelect = page.locator('select[name="encoding"]');
      if (await encodingSelect.isVisible()) {
        await encodingSelect.selectOption('UTF-8');
      }
      
      // ファイル選択エリア確認
      await expect(page.locator('text=ファイル選択')).toBeVisible();
    });

    test('バックアップ機能UI', async ({ page }) => {
      await page.goto('/data');
      await page.waitForLoadState('networkidle');
      
      // バックアップタブ
      await page.locator('text=バックアップ').click();
      await page.waitForLoadState('networkidle');
      
      // バックアップ実行ダイアログ
      const backupButton = page.locator('button:has-text("バックアップ実行")');
      if (await backupButton.isVisible()) {
        await backupButton.click();
        
        // 設定項目確認
        await expect(page.locator('input[name="backupName"]')).toBeVisible();
        await expect(page.locator('select[name="dataTypes"]')).toBeVisible();
        await expect(page.locator('select[name="format"]')).toBeVisible();
        
        // キャンセル
        await page.locator('button:has-text("キャンセル")').click();
      }
      
      // バックアップ一覧確認
      await expect(page.locator('[data-testid="backup-list"]')).toBeVisible();
    });
  });

  test.describe('エラーハンドリング・レスポンシブ対応', () => {
    
    test('ネットワークエラーハンドリング', async ({ page }) => {
      // ネットワークを無効化
      await page.setOfflineMode(true);
      
      await page.goto('/members');
      
      // エラーメッセージ表示確認
      await expect(page.locator('text=接続エラー')).toBeVisible({ timeout: 10000 });
      
      // ネットワークを復活
      await page.setOfflineMode(false);
      
      // リロードボタンがあれば実行
      const reloadButton = page.locator('button:has-text("再読み込み")');
      if (await reloadButton.isVisible()) {
        await reloadButton.click();
        await page.waitForLoadState('networkidle');
      }
    });

    test('モバイル表示確認', async ({ page }) => {
      // モバイルサイズに変更
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // ハンバーガーメニュー確認
      const menuButton = page.locator('[data-testid="mobile-menu-button"]');
      if (await menuButton.isVisible()) {
        await menuButton.click();
        await expect(page.locator('nav')).toBeVisible();
      }
      
      // レスポンシブ対応確認
      await page.goto('/members');
      await page.waitForLoadState('networkidle');
      
      // データグリッドのモバイル対応確認
      await expect(page.locator('[data-testid="member-data-grid"]')).toBeVisible();
    });

    test('パフォーマンス確認', async ({ page }) => {
      // パフォーマンス測定開始
      await page.goto('/members', { waitUntil: 'networkidle' });
      
      // 大量データ処理確認（検索なし状態）
      const dataGrid = page.locator('[data-testid="member-data-grid"]');
      await expect(dataGrid).toBeVisible();
      
      // 検索パフォーマンス確認
      const searchInput = page.locator('input[placeholder*="会員番号"]');
      await searchInput.fill('0000');
      
      const searchTime = Date.now();
      await page.locator('button:has-text("検索")').click();
      await page.waitForLoadState('networkidle');
      const searchDuration = Date.now() - searchTime;
      
      // 3秒以内の応答を期待
      expect(searchDuration).toBeLessThan(3000);
    });
  });
});