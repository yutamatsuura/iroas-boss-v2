# IROAS BOSS V2 開発進捗まとめ

## プロジェクト概要
IROAS BOSS V2 - MLM会員管理システム  
環境移行: Windows → Mac（2025/09/01）

## 技術スタック
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: React 18 + TypeScript + Material-UI + Vite
- **Database**: PostgreSQL with Alembic migrations

## 完了した機能

### 1. 基本システム設定
- ✅ Mac環境への移行完了
- ✅ ローカル開発用認証スキップ実装
- ✅ CORS設定調整（開発環境用）

### 2. 会員管理機能（完全実装済み）
#### 基本機能
- ✅ 会員一覧表示（検索・フィルタリング・ソート）
- ✅ 会員詳細表示（ポップアップダイアログ）
- ✅ 会員新規登録
- ✅ 会員情報編集・更新
- ✅ 会員退会処理

#### データ構造（30項目完全対応）
```
1. ステータス（アクティブ/休会中/退会済）
2. IROAS会員番号（11桁数字）
3. 氏名
4. カナ（廃止）
5. メールアドレス
6. 称号（称号なし/ナイト・デイム/ロード・レディ/キング・クイーン/エンペラー・エンプレス）
7. ユーザータイプ（通常/要注意）
8. 加入プラン（HERO/TEST）
9. 決済方法（カード/振込/銀行/インフォカート）
10. 登録日（自由形式文字列）
11. 退会日
12. 電話番号
13. 性別（男性/女性/その他）
14. 郵便番号
15. 都道府県
16. 住所2
17. 住所3
18. 直上者ID
19. 直上者名
20. 紹介者ID
21. 紹介者名
22. 報酬振込先の銀行名
23. 報酬振込先の銀行コード
24. 報酬振込先の支店名
25. 報酬振込先の支店コード
26. 口座番号
27. ゆうちょの場合の記号
28. ゆうちょの場合の番号
29. 口座種別（普通/当座）
30. 備考
```

#### CSV機能
- ✅ CSV出力（日本語表示対応）
- ✅ CSVテンプレートダウンロード（サンプル・空白）
- ✅ CSV取り込み機能
- ✅ 日本語⇔英語値マッピング完全対応

### 3. UI/UX改善
- ✅ サイドバーメニュー視認性改善（アクティブ項目の色調整）
- ✅ レスポンシブデザイン対応
- ✅ Material-UI エンタープライズテーマ適用

## 重要な技術的変更・修正

### 1. 会員番号仕様変更
- **変更前**: 7桁数字
- **変更後**: 11桁数字（先頭0埋め対応）
- **影響**: バリデーション、API、UI全体

### 2. データベース・API修正
```python
# 主要修正ファイル
- backend/app/schemas/member.py（バリデーション緩和）
- backend/app/api/v1/members.py（日本語マッピング追加）
- backend/app/models/member.py（Enum定義統一）
```

### 3. フロントエンド修正
```typescript
- frontend/src/services/memberService.ts（API統合）
- frontend/src/pages/Members.tsx（30項目UI対応）
- frontend/src/layouts/MainLayout.tsx（メニュー視認性改善）
```

### 4. 解決済み重要バグ
1. **422バリデーションエラー**: bank_code/branch_code桁数制限緩和
2. **CSV日本語表示**: 英語値→日本語表示マッピング追加
3. **フィールド表示欠損**: 全30項目表示確認済み
4. **メニュー視認性**: アクティブ項目色調整済み

## テストデータ
- 22件の会員データ作成済み
- 各ステータス、プラン、称号のテストケース網羅
- CSV取り込みテスト完了（00000000400番で確認）

## API仕様

### 会員管理API
```
GET    /api/v1/members              会員一覧
POST   /api/v1/members              会員新規登録
GET    /api/v1/members/{id}         会員詳細
PUT    /api/v1/members/{id}         会員更新
DELETE /api/v1/members/{id}         会員退会
GET    /api/v1/members/export       CSV出力
POST   /api/v1/members/import       CSV取り込み
GET    /api/v1/members/template/download  テンプレートDL
```

## 設定・環境

### データベース設定
```python
DATABASE_URL = "postgresql://lennon:@localhost/iroas_boss_v2"
```

### 開発サーバー
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- 認証: スキップ設定済み

## 今後の開発予定

### Phase 次期: 組織図機能
- 会員組織ツリー表示
- 直上者・部下関係の可視化
- 組織変更機能
- 報酬体系連動

## 注意事項

### 1. データ整合性
- 会員番号は必ず11桁（先頭0埋め）
- ゆうちょ銀行と通常銀行の項目使い分け
- Enum値は内部値（英語）で保存、表示時に日本語変換

### 2. 互換性維持
- フロントエンド（camelCase）⇔ バックエンド（snake_case）変換
- 旧データとの互換性確保
- API レスポンス形式統一

### 3. セキュリティ
- 本番環境では認証機能有効化必須
- CORS設定は本番用に変更要
- データベースアクセス制限設定

### 4. 🚨 データベース設定の重要事項
**問題**: 複数のデータベースが混在していた
- PostgreSQL: `iroas_boss_dev`（初期データ用）
- SQLite: `iroas_boss_v2.db`（APIサーバー実際使用）

**原因**: 
- 環境変数DATABASE_URLが未設定
- デフォルトでSQLiteを使用する設定になっていた
- データ削除時にPostgreSQLを操作していたが、APIはSQLiteを参照

**解決策**:
```bash
# SQLiteのデータ削除
sqlite3 iroas_boss_v2.db "DELETE FROM members WHERE member_number <> '00000000400';"

# PostgreSQLのデータ削除
psql -U lennon -d iroas_boss_dev -c "DELETE FROM members WHERE member_number <> '00000000400';"
```

**今後の防止策**:
1. **統一データベース使用**: 開発時は必ずどちらか1つに統一
2. **環境変数設定**: `export DATABASE_URL="postgresql://lennon:@localhost/iroas_boss_dev"`
3. **設定確認**: APIサーバー起動時にデータベース接続先を必ず確認
4. **データ操作前確認**: データ変更前に必ず現在のデータベースを確認

## ファイル構成
```
backend/
├── app/
│   ├── api/v1/members.py          # 会員API
│   ├── schemas/member.py          # Pydanticスキーマ
│   ├── models/member.py           # SQLAlchemyモデル
│   └── services/member_service.py # ビジネスロジック

frontend/
├── src/
│   ├── pages/Members.tsx          # 会員管理画面
│   ├── services/memberService.ts  # API通信
│   ├── layouts/MainLayout.tsx     # メインレイアウト
│   └── components/auth/           # 認証コンポーネント
```

## 動作確認済み機能
- ✅ 会員一覧表示・検索・ソート
- ✅ 会員詳細ポップアップ
- ✅ 会員新規登録（全30項目）
- ✅ 会員編集・更新
- ✅ CSV出力・取り込み
- ✅ テンプレートダウンロード
- ✅ サイドバーメニュー表示

**開発者**: システム完全実装済み、組織図開発準備完了
**更新日**: 2025/09/01