# 組織図システム設計書

## 📊 要件定義

### 基本方針
- 現在の45名アクティブメンバーから将来の退会者のみ管理
- 既存の6,678名退会者データは取り込まない
- 会員管理機能への影響はゼロ
- 組織ポジションの永続的保持

### 退会者管理
- **表示名**: 「退会者」で統一
- **会員番号**: WITHDRAWN_001、WITHDRAWN_002...
- **視覚的区別**: 専用アイコン・色分け
- **ポジション**: LEFT/RIGHTポジション永続保持

### 報酬計算
- アクティブメンバーのみ対象
- 退会者の過去実績は考慮しない
- 上位者への実績継承なし

## 🏗️ テーブル設計

### 1. members テーブル（既存）
```sql
-- 既存テーブルはそのまま利用
-- status: 'ACTIVE', 'INACTIVE', 'WITHDRAWN'
-- 退会時にstatusを'WITHDRAWN'に変更するだけ
```

### 2. organization_positions テーブル（新規）
```sql
CREATE TABLE organization_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,                    -- NULL の場合は退会者
    withdrawn_id INTEGER,                 -- 退会者の場合のみ使用
    parent_id INTEGER,                    -- 直上者のposition_id
    position_type VARCHAR(10) NOT NULL,   -- 'ROOT', 'LEFT', 'RIGHT'
    level INTEGER DEFAULT 0,              -- 階層レベル
    hierarchy_path TEXT,                  -- '1.2.1' 形式のパス
    left_count INTEGER DEFAULT 0,         -- 左組織人数（アクティブのみ）
    right_count INTEGER DEFAULT 0,        -- 右組織人数（アクティブのみ）
    left_sales DECIMAL(12,2) DEFAULT 0,   -- 左組織売上
    right_sales DECIMAL(12,2) DEFAULT 0,  -- 右組織売上
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (withdrawn_id) REFERENCES withdrawals(id),
    FOREIGN KEY (parent_id) REFERENCES organization_positions(id)
);
```

### 3. withdrawals テーブル（新規）
```sql
CREATE TABLE withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    withdrawal_number VARCHAR(20) UNIQUE NOT NULL, -- 'WITHDRAWN_001'
    original_member_id INTEGER,                     -- 元の会員ID
    original_member_number VARCHAR(11),             -- 元の会員番号
    original_name TEXT,                             -- 元の氏名（記録用）
    withdrawal_date DATE NOT NULL,                  -- 退会日
    withdrawal_reason TEXT,                         -- 退会理由
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (original_member_id) REFERENCES members(id)
);
```

### 4. organization_sales テーブル（新規）
```sql
CREATE TABLE organization_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,
    year_month VARCHAR(7) NOT NULL,       -- '2025-08' 形式
    new_purchase DECIMAL(12,2) DEFAULT 0,
    repeat_purchase DECIMAL(12,2) DEFAULT 0,
    additional_purchase DECIMAL(12,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (position_id) REFERENCES organization_positions(id),
    UNIQUE(position_id, year_month)
);
```

## 🔄 データ管理フロー

### 初期データ投入
```sql
-- 1. 現在の45名アクティブメンバーの組織ポジション作成
-- 2. ROOT（白石達也）から始まる組織ツリー構築
-- 3. 現在の直上者・紹介者関係をポジションに反映
```

### 退会処理フロー
```sql
-- 1. members.status を 'WITHDRAWN' に変更
-- 2. withdrawals テーブルに退会情報登録
-- 3. organization_positions.member_id を NULL に
-- 4. organization_positions.withdrawn_id を設定
-- 5. ポジション構造はそのまま保持
```

### 組織図表示ロジック
```sql
-- アクティブメンバー: members テーブルから情報取得
-- 退会者: withdrawals テーブルから 'WITHDRAWN_XXX' 情報取得
-- ポジション構造: organization_positions で管理
```

## 📊 報酬計算仕様

### バイナリー報酬
- 左右の売上実績バランスで計算
- アクティブメンバーの実績のみ集計
- 退会者ポジションは実績ゼロとして扱う

### アクティブ条件
- members.status = 'ACTIVE' のメンバーのみ
- 月次売上実績がある場合のみ

## 🎨 フロントエンド表示

### 組織ツリー表示
```typescript
interface OrganizationNode {
  id: string;
  member_id?: number;        // アクティブメンバーの場合
  withdrawal_id?: number;    // 退会者の場合
  display_name: string;      // 氏名 or '退会者'
  member_number: string;     // 会員番号 or 'WITHDRAWN_001'
  status: 'ACTIVE' | 'WITHDRAWN';
  position_type: 'ROOT' | 'LEFT' | 'RIGHT';
  level: number;
  left_count: number;
  right_count: number;
  left_sales: number;
  right_sales: number;
  children: OrganizationNode[];
  is_expanded: boolean;
}
```

### 視覚的区別
- **アクティブメンバー**: 緑のアイコン、通常の色
- **退会者**: グレーのアイコン、薄いグレー文字
- **直接紹介**: 青い線で接続
- **バイナリー配置**: 赤い線で LEFT/RIGHT 表示

## 📈 パフォーマンス考慮

### インデックス設計
```sql
CREATE INDEX idx_org_pos_member ON organization_positions(member_id);
CREATE INDEX idx_org_pos_parent ON organization_positions(parent_id);
CREATE INDEX idx_org_pos_path ON organization_positions(hierarchy_path);
CREATE INDEX idx_withdrawals_number ON withdrawals(withdrawal_number);
```

### クエリ最適化
- 階層クエリの効率化（CTEまたは再帰クエリ）
- 売上実績の月次集計キャッシュ
- 大きな組織ツリーの分割表示

## 🔒 データ整合性

### 制約
- 各ポジションは member_id または withdrawn_id のどちらか一つのみ
- ROOT ポジションは1つのみ
- 親子関係の循環参照チェック

### バリデーション
- 退会処理時のポジション整合性確認
- 組織変更時の階層レベル再計算
- 売上実績の正確性チェック

---

**作成日**: 2025/09/02  
**次ステップ**: テーブル作成 → 初期データ投入 → API実装