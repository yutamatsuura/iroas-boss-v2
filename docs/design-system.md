# デザインシステム定義書

## 基本情報
- プロジェクト名: iroas-boss-v2
- テーマ名: エンタープライズテーマ
- 作成日: 2025-08-26
- バージョン: 1.0.0

## デザインコンセプト

エンタープライズテーマは、MLM組織管理システムという業務システムの特性に最適化された信頼性重視のデザイン思想です。ネイビーブルーを基調とした落ち着いた配色により、長時間の作業でも疲れにくく、操作ミスを防ぐ堅実なユーザーインターフェースを実現します。

企業システムとしての安心感と機能性を重視し、直感的な操作性と視認性を両立させることで、50名規模のMLM組織管理業務を効率的にサポートします。装飾性よりも実用性を優先し、情報の階層化と適切なコントラストにより、重要な決済管理や報酬計算といった業務に集中できる環境を提供します。

## カラーパレット

### プライマリカラー
```css
/* メインカラー - システムの主要な操作要素 */
--primary: #1e3a8a;          /* ネイビーブルー */
--primary-hover: #1e40af;    /* ホバー状態 */
--primary-light: #3b82f6;    /* アクセント用 */
```

### セカンダリカラー
```css
/* サポートカラー - 補完的な要素 */
--secondary: #3b82f6;        /* ブルー */
--secondary-hover: #2563eb;  /* ホバー状態 */
--secondary-light: #60a5fa;  /* 軽いアクセント */
```

### ニュートラルカラー
```css
/* ベース色 - 背景、テキスト、境界線 */
--background: #f1f5f9;       /* メイン背景 */
--surface: #ffffff;          /* カード・モーダル背景 */
--text-primary: #1e293b;     /* メインテキスト */
--text-secondary: #475569;   /* サブテキスト */
--text-muted: #64748b;       /* ヘルプテキスト */
--border: #cbd5e1;           /* 境界線 */
--border-light: #e2e8f0;     /* 軽い境界線 */
```

### セマンティックカラー
```css
/* 状態表示色 - 成功、警告、エラー、情報 */
--success: #10b981;          /* 成功状態 */
--success-bg: #f0fdf4;       /* 成功背景 */
--warning: #f59e0b;          /* 警告状態 */
--warning-bg: #fffbeb;       /* 警告背景 */
--error: #ef4444;            /* エラー状態 */
--error-bg: #fef2f2;         /* エラー背景 */
--info: #3b82f6;             /* 情報状態 */
--info-bg: #eff6ff;          /* 情報背景 */
```

## タイポグラフィ

### フォントファミリー
```css
/* メインフォント - システム全体 */
--font-primary: 'Inter', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;

/* コードフォント - データ表示用 */
--font-mono: 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
```

### フォントサイズ
```css
/* 見出し用 */
--text-3xl: 1.875rem;        /* 30px - ページタイトル */
--text-2xl: 1.5rem;          /* 24px - セクションタイトル */
--text-xl: 1.25rem;          /* 20px - カードタイトル */
--text-lg: 1.125rem;         /* 18px - サブタイトル */

/* 本文用 */
--text-base: 1rem;           /* 16px - 標準テキスト */
--text-sm: 0.875rem;         /* 14px - 補助テキスト */
--text-xs: 0.75rem;          /* 12px - キャプション */
```

## スペーシング
```css
/* 統一的な余白設定 */
--spacing-xs: 0.25rem;       /* 4px */
--spacing-sm: 0.5rem;        /* 8px */
--spacing-md: 1rem;          /* 16px */
--spacing-lg: 1.5rem;        /* 24px */
--spacing-xl: 2rem;          /* 32px */
--spacing-2xl: 3rem;         /* 48px */
--spacing-3xl: 4rem;         /* 64px */
```

## UI要素スタイル

### ボタン
```css
/* プライマリボタン */
.btn-primary {
    background: var(--primary);
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    font-size: var(--text-base);
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary:hover {
    background: var(--primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(30, 58, 138, 0.25);
}

/* セカンダリボタン */
.btn-secondary {
    background: transparent;
    color: var(--primary);
    padding: 12px 24px;
    border: 1px solid var(--primary);
    border-radius: 8px;
    font-weight: 500;
    font-size: var(--text-base);
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-secondary:hover {
    background: var(--primary);
    color: white;
}
```

### カード
```css
.card {
    background: var(--surface);
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    padding: var(--spacing-lg);
    transition: all 0.2s ease;
}

.card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--border-light);
}

.card-title {
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}
```

### フォーム要素
```css
.form-group {
    margin-bottom: var(--spacing-lg);
}

.form-label {
    display: block;
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
}

.form-input {
    width: 100%;
    padding: 12px 16px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: var(--text-base);
    background: var(--surface);
    transition: all 0.2s ease;
}

.form-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
}

.form-select {
    width: 100%;
    padding: 12px 16px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: var(--text-base);
    background: var(--surface);
    cursor: pointer;
}
```

### アラート
```css
.alert {
    padding: var(--spacing-md);
    border-radius: 8px;
    margin-bottom: var(--spacing-md);
    font-size: var(--text-sm);
}

.alert-success {
    background: var(--success-bg);
    color: var(--success);
    border: 1px solid var(--success);
}

.alert-warning {
    background: var(--warning-bg);
    color: var(--warning);
    border: 1px solid var(--warning);
}

.alert-error {
    background: var(--error-bg);
    color: var(--error);
    border: 1px solid var(--error);
}

.alert-info {
    background: var(--info-bg);
    color: var(--info);
    border: 1px solid var(--info);
}
```

### ナビゲーション要素
```css
.primary-nav {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: var(--spacing-md) 0;
}

.nav-menu {
    display: flex;
    gap: var(--spacing-lg);
    list-style: none;
    margin: 0;
    padding: 0;
}

.nav-item {
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: 6px;
    color: var(--text-secondary);
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.nav-item:hover {
    background: var(--border-light);
    color: var(--text-primary);
}

.nav-item.active {
    background: var(--primary);
    color: white;
}
```

### サイドバー要素
```css
.sidebar {
    background: var(--surface);
    border-right: 1px solid var(--border);
    width: 280px;
    height: 100vh;
    padding: var(--spacing-lg);
    overflow-y: auto;
}

.sidebar-menu {
    list-style: none;
    margin: 0;
    padding: 0;
}

.menu-section {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: var(--spacing-xl) 0 var(--spacing-sm) 0;
}

.menu-item {
    margin-bottom: var(--spacing-xs);
}

.menu-item a {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: 6px;
    color: var(--text-secondary);
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s ease;
}

.menu-item a:hover {
    background: var(--border-light);
    color: var(--text-primary);
}

.menu-item a.active {
    background: var(--primary);
    color: white;
}
```

## レイアウト

### コンテナ
```css
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--spacing-lg);
}

.container-fluid {
    width: 100%;
    padding: 0 var(--spacing-lg);
}
```

### グリッドシステム
```css
.grid {
    display: grid;
    gap: var(--spacing-lg);
}

.grid-cols-1 { grid-template-columns: 1fr; }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }

/* レスポンシブグリッド */
.grid-responsive {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--spacing-lg);
}
```

## ナビゲーション構造

### グローバルナビゲーション
レイアウトパターン: サイドバー型（管理画面に最適）

構成要素:
- プライマリメニュー: 主要機能（ダッシュボード、会員管理、組織図、決済管理、報酬計算）
- セカンダリメニュー: 補助機能（支払管理、ログ、設定、データ入出力）
- ユーザーメニュー: システム操作（設定、ログアウト）

### サイドバー仕様

展開/折りたたみ:
- デフォルト状態: デスクトップでは展開、モバイルでは折りたたみ
- モバイル時の挙動: オーバーレイ表示
- アイコン+ラベル表示で視認性を確保

階層構造:
- 最大階層数: 2階層まで（分類 > 機能）
- グルーピング戦略: 機能別セクション分け
- アクティブ状態: 現在のページを明確に表示

### レスポンシブ戦略

ブレークポイント:
- モバイル（768px未満）: オーバーレイサイドバー + ハンバーガーメニュー
- タブレット（768px-1024px）: 折りたたみサイドバー
- デスクトップ（1024px以上）: 展開サイドバー

## アニメーション
```css
/* トランジション設定 */
--transition-fast: all 0.15s ease;
--transition-base: all 0.2s ease;
--transition-slow: all 0.3s ease;

/* ページ遷移 */
.page-transition {
    animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ホバー効果 */
.hover-lift:hover {
    transform: translateY(-2px);
    transition: var(--transition-base);
}
```

## アクセシビリティ
```css
/* フォーカス表示 */
.focus-ring:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
}

/* 高コントラスト対応 */
@media (prefers-contrast: high) {
    :root {
        --border: #000000;
        --text-secondary: #000000;
    }
}

/* アニメーション無効化対応 */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

## 実装ガイド

### 1. CSS変数の読み込み
```css
/* グローバルスタイルファイル（例: globals.css）に追加 */
:root {
    /* カラーパレット */
    --primary: #1e3a8a;
    --secondary: #3b82f6;
    --background: #f1f5f9;
    --surface: #ffffff;
    --text-primary: #1e293b;
    --border: #cbd5e1;
    
    /* スペーシング */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    
    /* フォント */
    --font-primary: 'Inter', 'Noto Sans JP', sans-serif;
    --text-base: 1rem;
    --text-sm: 0.875rem;
    --text-lg: 1.125rem;
    
    /* トランジション */
    --transition-base: all 0.2s ease;
}
```

### 2. クラスの使用例

```html
<!-- ボタン例 -->
<button class="btn-primary">メインアクション</button>
<button class="btn-secondary">サブアクション</button>

<!-- フォーム例 -->
<div class="form-group">
    <label class="form-label" for="member-name">会員名</label>
    <input type="text" id="member-name" class="form-input" placeholder="田中 太郎">
</div>

<!-- カード例 -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title">会員情報</h3>
    </div>
    <div class="card-content">
        <p>会員番号: 0000001</p>
        <p>ステータス: アクティブ</p>
    </div>
</div>

<!-- アラート例 -->
<div class="alert alert-success">
    会員情報が正常に更新されました。
</div>

<!-- グリッド例 -->
<div class="grid grid-cols-3">
    <div class="card">カード1</div>
    <div class="card">カード2</div>
    <div class="card">カード3</div>
</div>
```

### 3. ナビゲーション実装例

```html
<!-- グローバルナビゲーション -->
<nav class="primary-nav">
    <div class="container">
        <div class="nav-brand">
            <h1>IROAS BOSS v2</h1>
        </div>
        <ul class="nav-menu">
            <li><a href="/" class="nav-item active">ダッシュボード</a></li>
            <li><a href="/members" class="nav-item">会員管理</a></li>
            <li><a href="/organization" class="nav-item">組織図</a></li>
            <li><a href="/payments" class="nav-item">決済管理</a></li>
        </ul>
        <div class="nav-user">
            <button class="btn-secondary">設定</button>
        </div>
    </div>
</nav>

<!-- サイドバー -->
<aside class="sidebar">
    <ul class="sidebar-menu">
        <li class="menu-section">メイン機能</li>
        <li class="menu-item">
            <a href="/" class="active">
                <i class="icon-dashboard"></i>
                ダッシュボード
            </a>
        </li>
        <li class="menu-item">
            <a href="/members">
                <i class="icon-users"></i>
                会員管理
            </a>
        </li>
        <li class="menu-item">
            <a href="/organization">
                <i class="icon-tree"></i>
                組織図
            </a>
        </li>
        
        <li class="menu-section">決済・報酬</li>
        <li class="menu-item">
            <a href="/payments">
                <i class="icon-credit-card"></i>
                決済管理
            </a>
        </li>
        <li class="menu-item">
            <a href="/rewards">
                <i class="icon-calculator"></i>
                報酬計算
            </a>
        </li>
        <li class="menu-item">
            <a href="/payouts">
                <i class="icon-bank"></i>
                支払管理
            </a>
        </li>
        
        <li class="menu-section">システム</li>
        <li class="menu-item">
            <a href="/activity">
                <i class="icon-activity"></i>
                アクティビティログ
            </a>
        </li>
        <li class="menu-item">
            <a href="/settings">
                <i class="icon-settings"></i>
                設定
            </a>
        </li>
        <li class="menu-item">
            <a href="/data">
                <i class="icon-database"></i>
                データ入出力
            </a>
        </li>
    </ul>
</aside>
```

## 更新履歴

| バージョン | 日付 | 更新内容 |
|-----------|------|----------|
| 1.0.0 | 2025-08-26 | 初版作成 - エンタープライズテーマ基本定義 |

## 注意事項

1. **一貫性の維持**: 全てのページで統一したCSS変数とクラス名を使用してください
2. **レスポンシブ対応**: モバイル、タブレット、デスクトップの3つのブレークポイントに対応してください  
3. **アクセシビリティ**: キーボードナビゲーションとスクリーンリーダー対応を忘れずに実装してください
4. **カラーコントラスト**: WCAG 2.1 AA基準を満たすコントラスト比を維持してください
5. **パフォーマンス**: CSS変数の活用により、テーマ変更時の再描画コストを最小化してください