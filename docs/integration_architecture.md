# MLM統合データアーキテクチャ設計書

## 概要
報酬計算・売上管理に最適化された統合データモデルの設計

## フェーズ別実装計画

### Phase 1: データ統合基盤（2週間）
1. **統合データモデル定義**
   - UnifiedMember インターフェース
   - RewardCalculation インターフェース
   - OrganizationHierarchy インターフェース

2. **統合サービス層構築**
   - MemberIntegrationService
   - RewardCalculationService
   - HierarchyManagementService

3. **統合API設計**
   - `/api/v1/unified/members` - 統合会員データ
   - `/api/v1/unified/organization` - 統合組織データ
   - `/api/v1/unified/rewards/calculate` - 報酬計算API

### Phase 2: 報酬計算エンジン（3週間）
1. **計算ロジック実装**
   - バイナリーボーナス計算
   - ランクボーナス計算
   - チームボーナス計算

2. **履歴管理システム**
   - 報酬計算履歴
   - 組織変更履歴
   - 称号変更履歴

3. **整合性チェック機能**
   - データ同期検証
   - 計算結果検証
   - 異常値検出

### Phase 3: 運用機能（2週間）
1. **管理画面統合**
   - 統合ダッシュボード
   - 報酬明細表示
   - 組織変更インパクト分析

2. **自動化機能**
   - 定期的な報酬計算
   - アラート機能
   - バックアップ・復旧

## 技術仕様

### データベース設計
```sql
-- 統合会員マスター
CREATE TABLE unified_members (
    member_number VARCHAR(11) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    status ENUM('ACTIVE', 'INACTIVE', 'WITHDRAWN'),
    current_title VARCHAR(50),
    level INTEGER,
    parent_member VARCHAR(11),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_member) REFERENCES unified_members(member_number)
);

-- 売上実績テーブル
CREATE TABLE member_sales (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    member_number VARCHAR(11) NOT NULL,
    sales_date DATE NOT NULL,
    sales_type ENUM('PERSONAL', 'LEFT', 'RIGHT'),
    amount DECIMAL(15,2) NOT NULL,
    product_category VARCHAR(50),
    
    FOREIGN KEY (member_number) REFERENCES unified_members(member_number)
);

-- 報酬計算結果テーブル
CREATE TABLE reward_calculations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    member_number VARCHAR(11) NOT NULL,
    calculation_date DATE NOT NULL,
    reward_type VARCHAR(50) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    calculation_data JSON,
    
    FOREIGN KEY (member_number) REFERENCES unified_members(member_number)
);
```

### API仕様
```typescript
// 統合会員データ取得
GET /api/v1/unified/members/{member_number}
Response: {
  member_number: string;
  name: string;
  organization: {
    level: number;
    hierarchy: string;
    children: string[];
  };
  sales: {
    personal: number;
    left_total: number;
    right_total: number;
    monthly_breakdown: MonthlyData[];
  };
  rewards: {
    current_month: number;
    total_earned: number;
    next_rank_requirement: RankRequirement;
  };
}

// 報酬計算実行
POST /api/v1/unified/rewards/calculate
Request: {
  calculation_date: string;
  member_numbers?: string[];  // 特定メンバーのみ計算
  force_recalculate?: boolean;
}
Response: {
  calculation_id: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  progress: number;
  results: CalculationResult[];
}
```

## メリット

### 1. データ整合性の保証
- Single Source of Truth
- トランザクション制御
- 整合性制約

### 2. パフォーマンス最適化
- インデックス最適化
- キャッシュ戦略
- バッチ処理

### 3. 拡張性
- モジュラー設計
- API First
- マイクロサービス対応

### 4. 監査・コンプライアンス
- 変更履歴追跡
- 計算根拠保持
- レポート機能

## 実装優先度

### High Priority（必須）
- [ ] 統合データモデル定義
- [ ] 基本的な報酬計算ロジック
- [ ] データ同期機能

### Medium Priority（重要）
- [ ] 履歴管理システム
- [ ] 管理画面統合
- [ ] パフォーマンス最適化

### Low Priority（将来）
- [ ] 高度な分析機能
- [ ] 外部システム連携
- [ ] AI予測機能