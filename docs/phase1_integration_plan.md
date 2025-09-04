# Phase 1: 統合表示システム実装計画

## 🎯 目標
会員管理と組織図データの統合表示（無停止移行対応）

## 📋 実装ステップ

### Step 1: 統合データサービス層構築（1-2日）

#### 1.1 統合インターフェース定義
```typescript
// 統合会員データ型
export interface UnifiedMemberData {
  // 基本情報（会員管理マスター）
  member_number: string;
  name: string;
  email: string;
  phone: string;
  status: MemberStatus;
  registration_date: string;
  
  // 組織情報（組織図データ）  
  level: number;
  hierarchy_path: string;
  is_direct: boolean;
  left_sales: number;
  right_sales: number;
  children: UnifiedMemberData[];
  
  // 統合情報
  current_title: string;        // 会員管理の現在称号
  historical_title: string;     // 組織図の最高称号
  display_title: string;        // 表示用称号
  
  // メタ情報
  last_updated: string;
  data_source: 'MEMBER_MASTER' | 'ORGANIZATION_CSV' | 'INTEGRATED';
}
```

#### 1.2 統合サービス作成
- `UnifiedMemberService`: 両データソースを結合
- `DataIntegrityService`: データ整合性チェック
- `MigrationService`: 段階的移行サポート

### Step 2: 統合API実装（2-3日）

#### 2.1 新しいAPIエンドポイント
```
GET /api/v1/unified/members          # 統合会員一覧
GET /api/v1/unified/members/{id}     # 統合会員詳細
GET /api/v1/unified/organization     # 統合組織図
GET /api/v1/unified/organization/tree # 統合組織ツリー
```

#### 2.2 後方互換性の維持
既存のAPIは残し、新しいAPIと並行稼働

### Step 3: フロントエンド統合表示（2-3日）

#### 3.1 統合会員管理画面
- 組織階層情報を会員詳細に追加
- 売上データを会員情報に統合
- 称号の現在/過去最高を並記

#### 3.2 統合組織図
- 会員詳細情報を組織図に統合
- 連絡先・プラン情報を組織ノードに追加
- ワンクリックで詳細画面遷移

### Step 4: データ整合性機能（1日）

#### 4.1 整合性チェック
- 会員番号の重複検証
- 組織階層の整合性確認
- データソース間の同期状況確認

#### 4.2 レポート機能
- データ品質レポート
- 統合状況ダッシュボード
- エラーログ表示

## 🔧 技術実装詳細

### バックエンド実装

#### 統合サービス
```python
class UnifiedMemberService:
    def __init__(self):
        self.member_service = MemberService()
        self.org_service = OrganizationService()
        
    def get_unified_member(self, member_number: str) -> UnifiedMemberData:
        # 会員マスターから基本情報取得
        member_data = self.member_service.get_member(member_number)
        
        # 組織図から階層・売上情報取得
        org_data = self.org_service.get_member_org_data(member_number)
        
        # データ統合
        return self._merge_member_data(member_data, org_data)
    
    def _merge_member_data(self, member_data, org_data) -> UnifiedMemberData:
        return UnifiedMemberData(
            member_number=member_data.member_number,
            name=member_data.name,
            email=member_data.email,
            status=member_data.status,
            level=org_data.level if org_data else 0,
            left_sales=org_data.left_sales if org_data else 0,
            right_sales=org_data.right_sales if org_data else 0,
            current_title=member_data.title,
            historical_title=org_data.title if org_data else '',
            display_title=member_data.title or org_data.title if org_data else '称号なし'
        )
```

### フロントエンド実装

#### 統合サービス
```typescript
export class UnifiedMemberService {
  static async getUnifiedMember(memberNumber: string): Promise<UnifiedMemberData> {
    return ApiService.get<UnifiedMemberData>(`/api/v1/unified/members/${memberNumber}`);
  }
  
  static async getUnifiedMemberList(params?: SearchParams): Promise<UnifiedMemberData[]> {
    return ApiService.get<UnifiedMemberData[]>('/api/v1/unified/members', { params });
  }
  
  static async getUnifiedOrganizationTree(
    memberId?: string, 
    maxLevel?: number, 
    activeOnly?: boolean
  ): Promise<UnifiedOrganizationTree> {
    const params = { member_id: memberId, max_level: maxLevel, active_only: activeOnly };
    return ApiService.get<UnifiedOrganizationTree>('/api/v1/unified/organization/tree', { params });
  }
}
```

## 📊 移行戦略（無停止対応）

### 段階的切り替え
1. **Week 1**: 統合APIを並行稼働（既存API継続）
2. **Week 2**: フロントエンドで統合表示テスト
3. **Week 3**: 段階的にユーザーを新システムに誘導
4. **Week 4**: 完全移行・旧システム停止

### ロールバック対応
- 統合API障害時は既存APIに自動フォールバック
- データ不整合検出時はアラート表示
- 手動で旧画面に戻せる緊急スイッチ

## ✅ 成功指標

### 機能指標
- [ ] 全会員データが統合表示される
- [ ] 組織図に会員詳細が表示される
- [ ] データ不整合が0件になる
- [ ] 既存機能が100%動作する

### パフォーマンス指標
- [ ] 統合API応答時間 < 1秒
- [ ] 画面表示時間 < 3秒
- [ ] データ同期遅延 < 5分

## 🚀 次フェーズへの準備

Phase 1完了後、以下の準備が整います：
- 統合データモデルの確立
- データ品質の向上
- 報酬計算システムの基盤構築（Phase 2）