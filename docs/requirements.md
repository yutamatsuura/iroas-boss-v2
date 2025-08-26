# iroas-boss-v2 - 要件定義書

## 1. プロジェクト概要

### 1.1 成果目標
月額10万円のBOSSシステムを完全に自社開発で置き換え、MLM組織管理、Univapay決済データ入出力、複雑な報酬計算、GMO一括振込データ生成を統合管理し、ランニングコストをゼロにする

### 1.2 成功指標

#### 定量的指標
- 月額システム利用料10万円→0円（100%削減）
- Univapay用CSV（カード・口座振替）出力の成功率100%
- 報酬計算（7種類のボーナス）の正確性100%
- GMOネットバンク用振込CSVの正確な生成
- 組織図の圧縮処理の正確性100%

#### 定性的指標
- 現行BOSSと同等の操作で決済データ出力が可能
- 銀行振込/インフォカート入金の簡単な記録登録
- 決済状況が一目で分かる管理画面
- Univapay用CSVフォーマットの完全互換性
- 決済エラー時の明確な対処法表示

## 2. 技術スタック（固定）

### 2.1 フロントエンド
- **フレームワーク**: React 18
- **ビルドツール**: Vite 5
- **言語**: TypeScript 5
- **UIライブラリ**: MUI v7 (Material-UI)
- **状態管理**: Zustand / TanStack Query
- **ルーティング**: React Router v6
- **APIクライアント**: Axios / OpenAPI Generator

### 2.2 バックエンド
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI 0.100+
- **ORM**: SQLAlchemy 2.0 + Alembic
- **バリデーション**: Pydantic v2
- **認証**: FastAPI-Users / Auth0（Phase 21で追加）
- **非同期タスク**: Celery + Redis
- **API文書**: OpenAPI 3.0（自動生成）

### 2.3 データベース
- **メインDB**: PostgreSQL 15+
- **環境統一**: 開発・ステージング・本番すべてPostgreSQL
- **キャッシュ**: Redis
- **マイグレーション**: SQLAlchemy + Alembic
- **バックアップ**: 日次自動バックアップ

### 2.4 インフラ＆デプロイ
- **フロントエンド**: Vercel (React/Vite最適化)
- **バックエンド**: GCP Cloud Run (FastAPI最適化)
- **データベース**: Railway PostgreSQL / Neon
- **CI/CD**: GitHub Actions統合

### 2.5 開発環境＆ツール
- **Python**: 3.11+
- **Node.js**: 20.x LTS
- **パッケージマネージャー**: Poetry（Python）, pnpm（JavaScript）
- **コード品質**: Black, Ruff, ESLint, Prettier

## 3. ページ詳細仕様

### 3.1 P-001: ダッシュボード（ホーム）

#### 目的
各機能への導線提供とシステムナビゲーション

#### 主要機能
- 各機能へのメニューリンク
- システム全体のナビゲーション

#### エンドポイント（FastAPI形式）
```python
# 静的ページのため、APIエンドポイントなし
```

### 3.2 P-002: 会員管理

#### 目的
50名の会員データの完全管理と組織変更処理を統合実施

#### 主要機能
- 会員一覧表示（検索機能付き）
- 会員詳細編集（30項目）
- 退会処理
- 手動での組織調整
- タイトル管理

#### エンドポイント（FastAPI形式）
```python
@router.get("/api/members")
async def get_members(search: Optional[str] = None) -> List[MemberModel]:
    """会員一覧取得（検索条件付き）"""

@router.get("/api/members/{member_id}")
async def get_member(member_id: str) -> MemberDetailModel:
    """会員詳細取得"""

@router.post("/api/members")
async def create_member(member: MemberCreateModel) -> MemberModel:
    """新規会員登録"""

@router.put("/api/members/{member_id}")
async def update_member(member_id: str, member: MemberUpdateModel) -> MemberModel:
    """会員情報更新"""

@router.delete("/api/members/{member_id}")
async def delete_member(member_id: str) -> SuccessResponse:
    """会員退会処理"""

@router.get("/api/members/search")
async def search_members(q: str) -> List[MemberModel]:
    """会員検索（番号/氏名/メール）"""

@router.put("/api/members/{member_id}/sponsor")
async def update_sponsor(member_id: str, sponsor_id: str) -> SuccessResponse:
    """スポンサー変更"""
```

#### データモデル（Pydantic）
```python
class MemberModel(BaseModel):
    member_number: str  # 7桁の数字
    status: Literal["アクティブ", "休会中", "退会済"]
    name: str
    kana: str
    email: str
    title: Literal["称号なし", "ナイト/デイム", "ロード/レディ", "キング/クイーン", "エンペラー/エンブレス"]
    user_type: Literal["通常", "注意"]
    plan: Literal["ヒーロープラン", "テストプラン"]
    payment_method: Literal["カード決済", "口座振替", "銀行振込", "インフォカート"]
    registration_date: str
    withdrawal_date: Optional[str]
    phone: str
    gender: Literal["男性", "女性", "その他"]
    postal_code: str
    prefecture: str
    address2: str
    address3: str
    upline_id: str
    upline_name: str
    referrer_id: str
    referrer_name: str
    bank_name: str
    bank_code: str
    branch_name: str
    branch_code: str
    account_number: str
    yucho_symbol: Optional[str]
    yucho_number: Optional[str]
    account_type: Literal["普通", "当座"]
    notes: Optional[str]
```

### 3.3 P-003: 組織図ビューア

#### 目的
MLM組織をツリー形式で視覚的に表示し、階層構造を把握

#### 主要機能
- ツリー形式での組織表示
- ノードの展開/折りたたみ
- 各会員の基本情報表示（番号、氏名、称号、プラン）
- 会員詳細へのリンク

#### エンドポイント（FastAPI形式）
```python
@router.get("/api/organization/tree")
async def get_organization_tree() -> OrganizationTreeModel:
    """組織ツリー全体取得"""

@router.get("/api/organization/tree/{member_id}")
async def get_member_tree(member_id: str) -> OrganizationTreeModel:
    """特定会員配下のツリー取得"""

@router.get("/api/organization/member/{member_id}/downline")
async def get_downline(member_id: str) -> List[MemberModel]:
    """直下メンバー一覧"""
```

### 3.4 P-004: 決済管理

#### 目的
Univapay向けCSV出力、決済結果取込、手動決済記録を一元管理

#### 主要機能
- カード決済用CSV出力（月初1-5日）
- 口座振替用CSV出力（月初-12日）
- 決済結果CSV取込
- 手動決済記録（銀行振込・インフォカート）
- 決済履歴管理

#### エンドポイント（FastAPI形式）
```python
@router.get("/api/payments/targets/card")
async def get_card_targets() -> List[PaymentTargetModel]:
    """カード決済対象者一覧"""

@router.get("/api/payments/targets/transfer")
async def get_transfer_targets() -> List[PaymentTargetModel]:
    """口座振替対象者一覧"""

@router.post("/api/payments/export/card")
async def export_card_csv() -> FileResponse:
    """カード決済用CSV出力"""

@router.post("/api/payments/export/transfer")
async def export_transfer_csv() -> FileResponse:
    """口座振替用CSV出力"""

@router.post("/api/payments/import/result")
async def import_payment_result(file: UploadFile) -> ImportResultModel:
    """決済結果CSV取込"""

@router.post("/api/payments/manual")
async def record_manual_payment(payment: ManualPaymentModel) -> SuccessResponse:
    """手動決済記録（銀行振込/インフォカート）"""

@router.get("/api/payments/history")
async def get_payment_history() -> List[PaymentHistoryModel]:
    """決済履歴一覧"""
```

### 3.5 P-005: 報酬計算

#### 目的
7種類のボーナス計算を正確に実行し、個人別内訳を確認可能

#### 主要機能
- 計算前提条件チェック（決済状況・組織図）
- 7種類のボーナス一括計算
- 個人別内訳表示
- 計算やり直し機能

#### エンドポイント（FastAPI形式）
```python
@router.get("/api/rewards/check-prerequisites")
async def check_prerequisites() -> PrerequisiteCheckResult:
    """計算前提条件チェック（決済状況・組織図）"""

@router.post("/api/rewards/calculate")
async def calculate_rewards(month: str) -> CalculationResultModel:
    """報酬計算実行"""

@router.get("/api/rewards/results/{calculation_id}")
async def get_calculation_result(calculation_id: int) -> CalculationResultModel:
    """計算結果取得"""

@router.get("/api/rewards/results/{calculation_id}/member/{member_id}")
async def get_member_reward_detail(calculation_id: int, member_id: str) -> MemberRewardDetail:
    """個人別内訳取得"""

@router.delete("/api/rewards/results/{calculation_id}")
async def delete_calculation(calculation_id: int) -> SuccessResponse:
    """計算結果削除（再計算用）"""

@router.get("/api/rewards/history")
async def get_calculation_history() -> List[CalculationHistoryModel]:
    """過去の計算履歴"""
```

#### 7種類のボーナス
1. デイリーボーナス
2. タイトルボーナス
3. リファラルボーナス（直紹介者の参加費の50%）
4. パワーボーナス
5. メンテナンスボーナス
6. セールスアクティビティボーナス
7. ロイヤルファミリーボーナス

### 3.6 P-006: 報酬支払管理

#### 目的
GMOネットバンク振込CSV生成と支払履歴管理、繰越管理

#### 主要機能
- 支払対象者確認（5,000円以上）
- GMOネットバンク用CSV出力
- 支払確定処理
- 繰越金額管理（5,000円未満）

#### エンドポイント（FastAPI形式）
```python
@router.get("/api/payments/reward-summary")
async def get_reward_summary() -> RewardSummaryModel:
    """支払対象者一覧（5000円以上）"""

@router.post("/api/payments/export/gmo")
async def export_gmo_csv() -> FileResponse:
    """GMOネットバンク用CSV出力"""

@router.post("/api/payments/confirm")
async def confirm_payment(payment_id: int) -> SuccessResponse:
    """支払確定処理"""

@router.get("/api/payments/carryover")
async def get_carryover_list() -> List[CarryoverModel]:
    """繰越金額一覧（5000円未満）"""

@router.get("/api/payments/history")
async def get_payment_history() -> List[PaymentHistoryModel]:
    """支払履歴"""
```

### 3.7 P-007: アクティビティログ

#### 目的
システムで実行された全操作の履歴を時系列で確認

#### 主要機能
- 操作履歴の時系列表示
- 日付・操作種別でのフィルタリング
- 詳細情報の確認

#### エンドポイント（FastAPI形式）
```python
@router.get("/api/activity/logs")
async def get_activity_logs(page: int = 1, size: int = 50) -> ActivityLogList:
    """アクティビティログ一覧（ページング付き）"""

@router.get("/api/activity/logs/filter")
async def filter_logs(date_from: str, date_to: str, type: str) -> ActivityLogList:
    """条件指定でログ検索"""

@router.get("/api/activity/logs/{log_id}")
async def get_log_detail(log_id: int) -> ActivityLogDetail:
    """ログ詳細取得"""
```

### 3.8 P-008: マスタ設定

#### 目的
システム固定値の確認と最小限の設定管理

#### 主要機能
- 固定設定値の確認表示
- 参加費: ヒーロープラン10,670円、テストプラン9,800円
- タイトル条件・報酬率の確認（変更不可）

#### エンドポイント（FastAPI形式）
```python
@router.get("/api/settings/system")
async def get_system_settings() -> SystemSettingsModel:
    """システム設定取得（読み取り専用）"""

@router.get("/api/settings/business-rules")
async def get_business_rules() -> BusinessRulesModel:
    """ビジネスルール確認（固定値）"""
```

### 3.9 P-009: データ入出力

#### 目的
初期データ移行とシステムバックアップ・リストア管理

#### 主要機能
- Googleスプレッドシートからの会員データインポート
- データベースバックアップ（日次自動 + 手動）
- バックアップからのリストア

#### エンドポイント（FastAPI形式）
```python
@router.post("/api/data/import/members")
async def import_members(file: UploadFile) -> ImportResultModel:
    """会員データ一括インポート（Googleスプレッドシート形式）"""

@router.post("/api/data/backup")
async def create_backup() -> BackupModel:
    """手動バックアップ実行"""

@router.get("/api/data/backups")
async def get_backup_list() -> List[BackupModel]:
    """バックアップ一覧"""

@router.post("/api/data/restore/{backup_id}")
async def restore_from_backup(backup_id: int) -> SuccessResponse:
    """バックアップからリストア"""
```

## 4. データベース設計概要

### 主要テーブル（SQLAlchemy）
```python
class Member(Base):
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True)
    member_number = Column(String(7), unique=True, index=True)  # 7桁の会員番号
    status = Column(String(20))
    name = Column(String(100))
    kana = Column(String(100))
    email = Column(String(200))
    title = Column(String(50))
    user_type = Column(String(20))
    plan = Column(String(50))
    payment_method = Column(String(50))
    registration_date = Column(String(20))
    withdrawal_date = Column(String(20), nullable=True)
    # ... その他25項目
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class PaymentHistory(Base):
    __tablename__ = "payment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    payment_date = Column(Date)
    amount = Column(Decimal(10, 2))
    payment_type = Column(String(50))
    status = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

class RewardCalculation(Base):
    __tablename__ = "reward_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    calculation_month = Column(String(7))  # YYYY-MM
    member_id = Column(Integer, ForeignKey("members.id"))
    daily_bonus = Column(Decimal(10, 2))
    title_bonus = Column(Decimal(10, 2))
    referral_bonus = Column(Decimal(10, 2))
    power_bonus = Column(Decimal(10, 2))
    maintenance_bonus = Column(Decimal(10, 2))
    sales_activity_bonus = Column(Decimal(10, 2))
    royal_family_bonus = Column(Decimal(10, 2))
    total_amount = Column(Decimal(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(100))
    action_detail = Column(Text)
    user_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 5. 制約事項

### 外部API制限
- **Univapay**: CSVファイルの手動アップロードが必要
- **GMOネットバンク**: CSVファイルの手動アップロードが必要

### 技術的制約
- **会員数**: 最大50名（新規募集なし）
- **CSVエンコーディング**: Shift-JIS対応必須
- **バックアップ**: 日次自動実行

## 6. 主要処理連鎖

### VSA-001: 月次決済処理
**処理フロー**:
1. `GET /api/payments/targets/card` - カード決済対象者確認
2. `POST /api/payments/export/card` - CSV出力
3. **外部処理**: Univapayへアップロード
4. `POST /api/payments/import/result` - 決済結果取込

**外部依存**: Univapay

### VSA-002: 月次報酬計算・支払処理
**処理フロー**:
1. `GET /api/rewards/check-prerequisites` - 前提条件確認
2. `POST /api/rewards/calculate` - 報酬計算実行
3. `GET /api/payments/reward-summary` - 支払対象確認
4. `POST /api/payments/export/gmo` - GMO用CSV出力
5. **外部処理**: GMOネットバンクで振込
6. `POST /api/payments/confirm` - 支払確定

**外部依存**: GMOネットバンク

## 7. Docker環境構成

### docker-compose.yml 基本構成
```yaml
services:
  backend:    # FastAPI + Python
  frontend:   # React + Vite
  db:         # PostgreSQL
  redis:      # キャッシュ・セッション管理
```

## 8. 必要な外部サービス・アカウント

### 必須サービス
| サービス名 | 用途 | 取得先 | 備考 |
|-----------|------|--------|------|
| Univapay | カード決済・口座振替 | 既存アカウント利用 | CSV手動アップロード |
| GMOネットバンク | 報酬振込 | 既存アカウント利用 | CSV手動アップロード |

### オプションサービス
| サービス名 | 用途 | 取得先 | 備考 |
|-----------|------|--------|------|
| Auth0 | 認証機能 | https://auth0.com | Phase 21で追加 |

## 9. 今後の拡張予定

### フェーズ2
- 認証機能の追加（Phase 21）
- 多要素認証の実装

### フェーズ3
- レポート機能の拡充（必要に応じて）

---
*作成日: 2024-08-26*
*バージョン: 1.0*