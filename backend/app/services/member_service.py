"""
会員管理サービス

Phase A-1b: 会員基本管理API（1.1-1.4, 1.6）
- 完全独立、いつでも実装可能
- モックアップP-002対応（30項目完全再現）

エンドポイント:
- 1.1 GET /api/members - 会員一覧取得
- 1.2 POST /api/members - 新規会員登録
- 1.3 GET /api/members/{id} - 会員詳細取得
- 1.4 PUT /api/members/{id} - 会員情報更新
- 1.6 GET /api/members/search - 会員検索
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime

from app.models.member import Member, MemberStatus, Title, UserType, Plan, PaymentMethod, Gender, AccountType
from app.schemas.member import (
    MemberResponse,
    MemberListResponse,
    MemberCreateRequest,
    MemberUpdateRequest,
    MemberSearchResponse
)
from app.services.activity_service import ActivityService


class MemberService:
    """
    会員管理サービスクラス
    要件定義書の30項目完全対応
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)

    async def get_members(
        self, 
        page: int = 1, 
        per_page: int = 20,
        status_filter: Optional[List[str]] = None
    ) -> MemberListResponse:
        """
        会員一覧取得
        API 1.1: GET /api/members
        """
        # ベースクエリ
        query = self.db.query(Member)
        
        # ステータスフィルター
        if status_filter:
            query = query.filter(Member.status.in_(status_filter))
        
        # 総件数取得
        total_count = query.count()
        
        # ページネーション
        offset = (page - 1) * per_page
        members = query.offset(offset).limit(per_page).all()
        
        # レスポンス変換
        member_list = [self._convert_to_response(member) for member in members]
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="会員一覧取得",
            details=f"ページ: {page}, 件数: {len(member_list)}, フィルター: {status_filter}",
            user_id="system"
        )
        
        return MemberListResponse(
            members=member_list,
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=(total_count + per_page - 1) // per_page,
            has_next=page * per_page < total_count,
            has_previous=page > 1
        )

    async def create_member(self, member_data: MemberCreateRequest) -> MemberResponse:
        """
        新規会員登録
        API 1.2: POST /api/members
        """
        # 会員番号重複チェック
        existing = self.db.query(Member).filter(Member.member_number == member_data.member_number).first()
        if existing:
            raise ValueError(f"会員番号 {member_data.member_number} は既に使用されています")
        
        # メールアドレス重複チェック（空でない場合のみ）
        if member_data.email:
            existing_email = self.db.query(Member).filter(Member.email == member_data.email).first()
            if existing_email:
                raise ValueError(f"メールアドレス {member_data.email} は既に登録されています")
        
        # 新規会員作成
        new_member = Member(
            # 基本情報（1-5）
            status=member_data.status,
            member_number=member_data.member_number,
            name=member_data.name,
            kana=member_data.kana,
            email=member_data.email,
            
            # 会員属性（6-10）
            title=member_data.title,
            user_type=member_data.user_type,
            plan=member_data.plan,
            payment_method=member_data.payment_method,
            registration_date=member_data.registration_date or datetime.now(),
            
            # 個人情報（11-17）
            withdrawal_date=member_data.withdrawal_date,
            phone_number=member_data.phone_number,
            gender=member_data.gender,
            postal_code=member_data.postal_code,
            prefecture=member_data.prefecture,
            address2=member_data.address2,
            address3=member_data.address3,
            
            # 組織情報（18-21）
            parent_id=member_data.parent_id,
            parent_name=member_data.parent_name,
            referrer_id=member_data.referrer_id,
            referrer_name=member_data.referrer_name,
            
            # 銀行情報（22-29）
            bank_name=member_data.bank_name,
            bank_code=member_data.bank_code,
            branch_name=member_data.branch_name,
            branch_code=member_data.branch_code,
            account_number=member_data.account_number,
            yucho_symbol=member_data.yucho_symbol,
            yucho_number=member_data.yucho_number,
            account_type=member_data.account_type,
            
            # その他（30）
            remarks=member_data.remarks,
            
            # システム項目
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(new_member)
        self.db.commit()
        self.db.refresh(new_member)
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="新規会員登録",
            details=f"会員番号: {new_member.member_number}, 氏名: {new_member.name}",
            user_id="system",
            target_id=new_member.id
        )
        
        return self._convert_to_response(new_member)

    async def get_member(self, member_id: int) -> MemberResponse:
        """
        会員詳細取得
        API 1.3: GET /api/members/{id}
        """
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"会員ID {member_id} は存在しません")
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="会員詳細取得",
            details=f"会員番号: {member.member_number}, 氏名: {member.name}",
            user_id="system",
            target_id=member.id
        )
        
        return self._convert_to_response(member)

    async def update_member(self, member_id: int, member_data: MemberUpdateRequest) -> MemberResponse:
        """
        会員情報更新
        API 1.4: PUT /api/members/{id}
        """
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"会員ID {member_id} は存在しません")
        
        # 会員番号重複チェック（変更時）
        if member_data.member_number and member_data.member_number != member.member_number:
            existing = self.db.query(Member).filter(
                and_(
                    Member.member_number == member_data.member_number,
                    Member.id != member_id
                )
            ).first()
            if existing:
                raise ValueError(f"会員番号 {member_data.member_number} は既に使用されています")
        
        # メールアドレス重複チェック（変更時）
        if member_data.email and member_data.email != member.email:
            existing_email = self.db.query(Member).filter(
                and_(
                    Member.email == member_data.email,
                    Member.id != member_id
                )
            ).first()
            if existing_email:
                raise ValueError(f"メールアドレス {member_data.email} は既に登録されています")
        
        # 更新対象項目のみ更新（None以外の値）
        update_data = member_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(member, field) and value is not None:
                setattr(member, field, value)
        
        # システム更新日時
        member.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(member)
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="会員情報更新",
            details=f"会員番号: {member.member_number}, 更新項目: {list(update_data.keys())}",
            user_id="system",
            target_id=member.id
        )
        
        return self._convert_to_response(member)

    async def search_members(
        self,
        query: Optional[str] = None,
        status: Optional[List[str]] = None,
        title: Optional[List[str]] = None,
        plan: Optional[List[str]] = None,
        payment_method: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 20
    ) -> MemberSearchResponse:
        """
        会員検索
        API 1.6: GET /api/members/search
        検索条件: 会員番号、氏名、メールアドレス
        """
        # ベースクエリ
        db_query = self.db.query(Member)
        
        # テキスト検索（会員番号、氏名、メールアドレス）
        if query:
            search_conditions = or_(
                Member.member_number.ilike(f"%{query}%"),
                Member.name.ilike(f"%{query}%"),
                Member.kana.ilike(f"%{query}%"),
                Member.email.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_conditions)
        
        # ステータスフィルター
        if status:
            db_query = db_query.filter(Member.status.in_(status))
        
        # 称号フィルター
        if title:
            db_query = db_query.filter(Member.title.in_(title))
        
        # プランフィルター
        if plan:
            db_query = db_query.filter(Member.plan.in_(plan))
        
        # 決済方法フィルター
        if payment_method:
            db_query = db_query.filter(Member.payment_method.in_(payment_method))
        
        # 総件数取得
        total_count = db_query.count()
        
        # ページネーション
        offset = (page - 1) * per_page
        members = db_query.offset(offset).limit(per_page).all()
        
        # レスポンス変換
        member_list = [self._convert_to_response(member) for member in members]
        
        # アクティビティログ記録
        await self.activity_service.log_activity(
            action="会員検索",
            details=f"検索語: '{query}', 結果: {len(member_list)}件",
            user_id="system"
        )
        
        return MemberSearchResponse(
            members=member_list,
            search_query=query,
            search_filters={
                "status": status,
                "title": title,
                "plan": plan,
                "payment_method": payment_method
            },
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=(total_count + per_page - 1) // per_page
        )

    async def get_member_statistics(self) -> Dict[str, Any]:
        """
        会員統計情報取得
        内部使用：ダッシュボード表示用
        """
        # ステータス別集計
        status_counts = {}
        for status in MemberStatus:
            count = self.db.query(Member).filter(Member.status == status).count()
            status_counts[status.value] = count
        
        # プラン別集計
        plan_counts = {}
        for plan in Plan:
            count = self.db.query(Member).filter(Member.plan == plan).count()
            plan_counts[plan.value] = count
        
        # 決済方法別集計
        payment_counts = {}
        for payment in PaymentMethod:
            count = self.db.query(Member).filter(Member.payment_method == payment).count()
            payment_counts[payment.value] = count
        
        # 称号別集計
        title_counts = {}
        for title in Title:
            count = self.db.query(Member).filter(Member.title == title).count()
            title_counts[title.value] = count
        
        # 総会員数
        total_members = self.db.query(Member).count()
        active_members = self.db.query(Member).filter(Member.status == MemberStatus.ACTIVE).count()
        
        return {
            "total_members": total_members,
            "active_members": active_members,
            "status_distribution": status_counts,
            "plan_distribution": plan_counts,
            "payment_distribution": payment_counts,
            "title_distribution": title_counts,
            "last_updated": datetime.now().isoformat()
        }

    def _convert_to_response(self, member: Member) -> MemberResponse:
        """
        Member モデルを MemberResponse スキーマに変換
        30項目完全対応
        """
        return MemberResponse(
            # システム項目
            id=member.id,
            
            # 基本情報（1-5）
            status=member.status,
            member_number=member.member_number,
            name=member.name,
            kana=member.kana,
            email=member.email,
            
            # 会員属性（6-10）
            title=member.title,
            user_type=member.user_type,
            plan=member.plan,
            payment_method=member.payment_method,
            registration_date=member.registration_date,
            
            # 個人情報（11-17）
            withdrawal_date=member.withdrawal_date,
            phone_number=member.phone_number,
            gender=member.gender,
            postal_code=member.postal_code,
            prefecture=member.prefecture,
            address2=member.address2,
            address3=member.address3,
            
            # 組織情報（18-21）
            parent_id=member.parent_id,
            parent_name=member.parent_name,
            referrer_id=member.referrer_id,
            referrer_name=member.referrer_name,
            
            # 銀行情報（22-29）
            bank_name=member.bank_name,
            bank_code=member.bank_code,
            branch_name=member.branch_name,
            branch_code=member.branch_code,
            account_number=member.account_number,
            yucho_symbol=member.yucho_symbol,
            yucho_number=member.yucho_number,
            account_type=member.account_type,
            
            # その他（30）
            remarks=member.remarks,
            
            # システム項目
            created_at=member.created_at,
            updated_at=member.updated_at,
            
            # 表示用フォーマット
            display_name=f"{member.name} ({member.member_number})",
            formatted_registration_date=member.registration_date.strftime("%Y年%m月%d日") if member.registration_date else None,
            is_active=member.status == MemberStatus.ACTIVE
        )

    async def validate_member_data(self, member_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        会員データバリデーション
        内部使用：作成・更新前のデータチェック
        """
        errors = {}
        
        # 必須項目チェック
        required_fields = ["member_number", "name", "kana"]
        for field in required_fields:
            if not member_data.get(field):
                if field not in errors:
                    errors[field] = []
                errors[field].append(f"{field} は必須項目です")
        
        # フォーマットチェック
        if member_data.get("member_number"):
            member_number = member_data["member_number"]
            if not member_number.isdigit() or len(member_number) != 7:
                if "member_number" not in errors:
                    errors["member_number"] = []
                errors["member_number"].append("会員番号は7桁の数字で入力してください")
        
        # メールアドレス形式チェック
        if member_data.get("email"):
            email = member_data["email"]
            if "@" not in email or "." not in email:
                if "email" not in errors:
                    errors["email"] = []
                errors["email"].append("メールアドレスの形式が正しくありません")
        
        return errors