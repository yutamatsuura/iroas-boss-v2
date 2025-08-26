import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import path from 'path';

/**
 * 静的検証テスト - サーバー起動無しでの実行可能テスト
 * ファイル存在確認・設定検証・依存関係確認
 */

test.describe('IROAS BOSS V2 - 静的検証テスト', () => {
  
  const frontendRoot = path.resolve(__dirname, '..');
  
  test('プロジェクト構造・基本ファイル存在確認', async () => {
    // 重要ファイルの存在確認
    const requiredFiles = [
      'package.json',
      'tsconfig.json', 
      'vite.config.ts',
      'index.html',
      'src/main.tsx',
      'src/App.tsx',
      'src/theme/theme.ts',
      'playwright.config.ts'
    ];
    
    for (const file of requiredFiles) {
      const filePath = path.join(frontendRoot, file);
      expect(existsSync(filePath), `Missing required file: ${file}`).toBe(true);
    }
    
    // ディレクトリ構造確認
    const requiredDirs = [
      'src',
      'src/pages', 
      'src/services',
      'src/components',
      'src/theme',
      'tests'
    ];
    
    for (const dir of requiredDirs) {
      const dirPath = path.join(frontendRoot, dir);
      expect(existsSync(dirPath), `Missing required directory: ${dir}`).toBe(true);
    }
  });

  test('package.json 設定・依存関係確認', async () => {
    const packageJsonPath = path.join(frontendRoot, 'package.json');
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));
    
    // 基本情報確認
    expect(packageJson.name).toBe('iroas-boss-v2-frontend');
    expect(packageJson.type).toBe('module');
    expect(packageJson.private).toBe(true);
    
    // 必須スクリプト確認
    expect(packageJson.scripts.dev).toBeTruthy();
    expect(packageJson.scripts.build).toBeTruthy();
    expect(packageJson.scripts.test).toBe('playwright test');
    
    // 主要依存関係確認
    const requiredDeps = [
      'react',
      'react-dom', 
      'react-router-dom',
      '@mui/material',
      '@mui/icons-material',
      '@mui/x-data-grid',
      'axios',
      'recharts'
    ];
    
    for (const dep of requiredDeps) {
      expect(packageJson.dependencies[dep], `Missing dependency: ${dep}`).toBeTruthy();
    }
    
    // 開発依存関係確認
    const requiredDevDeps = [
      'typescript',
      '@vitejs/plugin-react',
      '@playwright/test',
      'vite'
    ];
    
    for (const dep of requiredDevDeps) {
      expect(packageJson.devDependencies[dep], `Missing dev dependency: ${dep}`).toBeTruthy();
    }
  });

  test('TypeScript設定確認', async () => {
    const tsconfigPath = path.join(frontendRoot, 'tsconfig.json');
    const tsconfig = JSON.parse(readFileSync(tsconfigPath, 'utf-8'));
    
    // 重要なコンパイラオプション確認
    expect(tsconfig.compilerOptions.target).toBeTruthy();
    expect(tsconfig.compilerOptions.lib).toBeTruthy();
    expect(tsconfig.compilerOptions.module).toBeTruthy();
    expect(tsconfig.compilerOptions.moduleResolution).toBeTruthy();
    expect(tsconfig.compilerOptions.jsx).toBeTruthy();
    
    // 型安全性設定確認
    expect(tsconfig.compilerOptions.strict).toBe(true);
    expect(tsconfig.compilerOptions.noUnusedLocals).toBeTruthy();
    expect(tsconfig.compilerOptions.noUnusedParameters).toBeTruthy();
    
    // インクルード対象確認
    expect(tsconfig.include).toContain('src');
  });

  test('Vite設定確認', async () => {
    const viteConfigPath = path.join(frontendRoot, 'vite.config.ts');
    const viteConfig = readFileSync(viteConfigPath, 'utf-8');
    
    // React plugin設定確認
    expect(viteConfig).toContain('@vitejs/plugin-react');
    expect(viteConfig).toContain('plugins: [react()]');
    
    // TypeScript設定確認
    expect(viteConfig).toContain('typescript');
  });

  test('Playwright設定確認', async () => {
    const playwrightConfigPath = path.join(frontendRoot, 'playwright.config.ts');
    const playwrightConfig = readFileSync(playwrightConfigPath, 'utf-8');
    
    // 基本設定確認
    expect(playwrightConfig).toContain('testDir: \'./tests\'');
    expect(playwrightConfig).toContain('baseURL: \'http://localhost:5173\'');
    
    // ブラウザ設定確認
    expect(playwrightConfig).toContain('chromium');
    expect(playwrightConfig).toContain('firefox');
    expect(playwrightConfig).toContain('webkit');
    
    // レポート設定確認
    expect(playwrightConfig).toContain('reporter');
  });

  test('React コンポーネント基本構造確認', async () => {
    // App.tsx確認
    const appPath = path.join(frontendRoot, 'src/App.tsx');
    const appContent = readFileSync(appPath, 'utf-8');
    
    expect(appContent).toContain('import React');
    expect(appContent).toContain('function App()');
    expect(appContent).toContain('export default App');
    expect(appContent).toContain('BrowserRouter');
    
    // main.tsx確認
    const mainPath = path.join(frontendRoot, 'src/main.tsx');
    const mainContent = readFileSync(mainPath, 'utf-8');
    
    expect(mainContent).toContain('import React');
    expect(mainContent).toContain('import ReactDOM');
    expect(mainContent).toContain('createRoot');
  });

  test('ページコンポーネント実装確認', async () => {
    const pageFiles = [
      'Dashboard.tsx',
      'Members.tsx',
      'Organization.tsx', 
      'Payments.tsx',
      'Rewards.tsx',
      'Payouts.tsx',
      'Activity.tsx',
      'Settings.tsx',
      'DataManagement.tsx'
    ];
    
    for (const pageFile of pageFiles) {
      const pagePath = path.join(frontendRoot, 'src/pages', pageFile);
      expect(existsSync(pagePath), `Missing page component: ${pageFile}`).toBe(true);
      
      const pageContent = readFileSync(pagePath, 'utf-8');
      expect(pageContent).toContain('import React');
      expect(pageContent).toContain('export default');
      expect(pageContent).toContain('function ');
    }
  });

  test('サービス層実装確認', async () => {
    const serviceFiles = [
      'apiClient.ts',
      'memberService.ts',
      'organizationService.ts',
      'paymentService.ts', 
      'rewardsService.ts',
      'payoutService.ts',
      'activityService.ts',
      'settingsService.ts',
      'dataManagementService.ts'
    ];
    
    for (const serviceFile of serviceFiles) {
      const servicePath = path.join(frontendRoot, 'src/services', serviceFile);
      expect(existsSync(servicePath), `Missing service file: ${serviceFile}`).toBe(true);
      
      const serviceContent = readFileSync(servicePath, 'utf-8');
      expect(serviceContent).toContain('export');
      
      // APIサービスクラス確認
      if (serviceFile !== 'apiClient.ts') {
        expect(serviceContent).toContain('class');
        expect(serviceContent).toContain('static async');
      }
    }
  });

  test('テーマ・スタイル設定確認', async () => {
    const themePath = path.join(frontendRoot, 'src/theme/theme.ts');
    const themeContent = readFileSync(themePath, 'utf-8');
    
    // MUIテーマ設定確認
    expect(themeContent).toContain('createTheme');
    expect(themeContent).toContain('palette');
    
    // エンタープライズテーマ色確認
    expect(themeContent).toContain('#1e3a8a'); // Navy Blue
  });

  test('テストファイル構造確認', async () => {
    const testFiles = [
      'page-navigation.test.ts',
      'api-integration.test.ts',
      'ui-functionality.test.ts',
      'integration-setup.test.ts',
      'static-validation.test.ts'
    ];
    
    for (const testFile of testFiles) {
      const testPath = path.join(frontendRoot, 'tests', testFile);
      expect(existsSync(testPath), `Missing test file: ${testFile}`).toBe(true);
      
      const testContent = readFileSync(testPath, 'utf-8');
      expect(testContent).toContain('import { test, expect } from \'@playwright/test\'');
      expect(testContent).toContain('test.describe(');
    }
  });

  test('HTMLテンプレート確認', async () => {
    const indexPath = path.join(frontendRoot, 'index.html');
    const indexContent = readFileSync(indexPath, 'utf-8');
    
    // 基本HTML構造確認
    expect(indexContent).toContain('<!DOCTYPE html>');
    expect(indexContent).toContain('<html lang="ja">');
    expect(indexContent).toContain('<title>IROAS BOSS V2</title>');
    expect(indexContent).toContain('<div id="root">');
    expect(indexContent).toContain('src="/src/main.tsx"');
  });

  test('TypeScript型定義・インターフェース確認', async () => {
    const serviceFiles = [
      'memberService.ts',
      'paymentService.ts',
      'rewardsService.ts',
      'payoutService.ts',
      'activityService.ts',
      'settingsService.ts',
      'dataManagementService.ts'
    ];
    
    let totalInterfaces = 0;
    let totalEnums = 0;
    
    for (const serviceFile of serviceFiles) {
      const servicePath = path.join(frontendRoot, 'src/services', serviceFile);
      const serviceContent = readFileSync(servicePath, 'utf-8');
      
      // インターフェース定義確認
      const interfaceMatches = serviceContent.match(/export interface \w+/g);
      if (interfaceMatches) {
        totalInterfaces += interfaceMatches.length;
      }
      
      // Enum定義確認
      const enumMatches = serviceContent.match(/export enum \w+/g);
      if (enumMatches) {
        totalEnums += enumMatches.length;
      }
      
      // クラス定義確認
      expect(serviceContent).toMatch(/export class \w+Service/);
    }
    
    // 最低限の型定義数を確認
    expect(totalInterfaces).toBeGreaterThan(20); // 各サービスに複数のインターフェース
    expect(totalEnums).toBeGreaterThan(10); // 各サービスに複数のEnum
    
    console.log(`Total interfaces: ${totalInterfaces}, Total enums: ${totalEnums}`);
  });

  test('API エンドポイント定義確認', async () => {
    const serviceFiles = [
      'memberService.ts',
      'organizationService.ts',
      'paymentService.ts',
      'rewardsService.ts', 
      'payoutService.ts',
      'activityService.ts',
      'settingsService.ts',
      'dataManagementService.ts'
    ];
    
    let totalApiMethods = 0;
    
    for (const serviceFile of serviceFiles) {
      const servicePath = path.join(frontendRoot, 'src/services', serviceFile);
      const serviceContent = readFileSync(servicePath, 'utf-8');
      
      // APIメソッド定義確認
      const apiMethodMatches = serviceContent.match(/static async \w+/g);
      if (apiMethodMatches) {
        totalApiMethods += apiMethodMatches.length;
      }
      
      // BASE_URL定義確認
      expect(serviceContent).toContain('BASE_URL');
      
      // ApiService使用確認
      expect(serviceContent).toContain('ApiService.');
    }
    
    // 33個のAPIエンドポイントに対応したメソッドを確認
    expect(totalApiMethods).toBeGreaterThan(30);
    console.log(`Total API methods: ${totalApiMethods}`);
  });

  test('依存関係バージョン互換性確認', async () => {
    const packageJsonPath = path.join(frontendRoot, 'package.json');
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));
    
    // React 18確認
    expect(packageJson.dependencies.react).toMatch(/\^18\./);
    expect(packageJson.dependencies['react-dom']).toMatch(/\^18\./);
    
    // MUI v5確認
    expect(packageJson.dependencies['@mui/material']).toMatch(/\^5\./);
    expect(packageJson.dependencies['@mui/icons-material']).toMatch(/\^5\./);
    
    // TypeScript 5確認
    expect(packageJson.devDependencies.typescript).toMatch(/\^5\./);
    
    // Vite 5確認
    expect(packageJson.devDependencies.vite).toMatch(/\^5\./);
  });
});