"""
会員管理APIエンドポイント（完全データ対応版）
"""
import sqlite3
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/members", tags=["members"])

# 会員更新用のPydanticモデル
class MemberUpdate(BaseModel):
    # snake_case (DB形式)
    name: Optional[str] = None
    kana: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    user_type: Optional[str] = None
    plan: Optional[str] = None
    payment_method: Optional[str] = None
    postal_code: Optional[str] = None
    prefecture: Optional[str] = None
    address2: Optional[str] = None
    address3: Optional[str] = None
    upline_id: Optional[str] = None
    upline_name: Optional[str] = None
    referrer_id: Optional[str] = None
    referrer_name: Optional[str] = None
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    branch_name: Optional[str] = None
    branch_code: Optional[str] = None
    account_number: Optional[str] = None
    yucho_symbol: Optional[str] = None
    yucho_number: Optional[str] = None
    account_type: Optional[str] = None
    registration_date: Optional[str] = None
    withdrawal_date: Optional[str] = None
    notes: Optional[str] = None
    
    # camelCase (フロントエンド形式) - 互換性のため
    userType: Optional[str] = None
    paymentMethod: Optional[str] = None
    postalCode: Optional[str] = None
    uplineId: Optional[str] = None
    uplineName: Optional[str] = None
    referrerId: Optional[str] = None
    referrerName: Optional[str] = None
    bankName: Optional[str] = None
    bankCode: Optional[str] = None
    branchName: Optional[str] = None
    branchCode: Optional[str] = None
    accountNumber: Optional[str] = None
    yuchoSymbol: Optional[str] = None
    yuchoNumber: Optional[str] = None
    accountType: Optional[str] = None
    registrationDate: Optional[str] = None
    withdrawalDate: Optional[str] = None

@router.get("/")
def get_members(
    page: int = Query(1, ge=1),
    perPage: int = Query(20, ge=1, le=100),
    memberNumber: str = Query("", description="会員番号で検索"),
    name: str = Query("", description="名前で検索"),
    email: str = Query("", description="メールアドレスで検索"),
    sortBy: str = Query("memberNumber", description="ソート項目"),
    sortOrder: str = Query("asc", description="ソート順")
):
    """会員一覧取得（検索対応版）"""
    try:
        db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        
        # 検索条件を構築
        where_conditions = []
        params = []
        
        if memberNumber.strip():
            where_conditions.append("member_number LIKE ?")
            params.append(f"%{memberNumber.strip()}%")
        
        if name.strip():
            where_conditions.append("name LIKE ?")
            params.append(f"%{name.strip()}%")
        
        if email.strip():
            where_conditions.append("email LIKE ?")
            params.append(f"%{email.strip()}%")
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # ソート項目のマッピング
        sort_mapping = {
            "memberNumber": "member_number",
            "name": "name", 
            "email": "email",
            "status": "status",
            "plan": "plan"
        }
        sort_column = sort_mapping.get(sortBy, "member_number")
        sort_direction = "DESC" if sortOrder.lower() == "desc" else "ASC"
        
        # 総件数取得
        count_query = f"SELECT COUNT(*) FROM members{where_clause}"
        total = conn.execute(count_query, params).fetchone()[0]
        
        # ステータス別集計取得
        status_query = f"SELECT status, COUNT(*) as count FROM members{where_clause} GROUP BY status"
        status_counts = conn.execute(status_query, params).fetchall()
        
        # ステータス別カウントを計算
        active_count = 0
        inactive_count = 0 
        withdrawn_count = 0
        
        for status_row in status_counts:
            status = status_row["status"] or "ACTIVE"
            count = status_row["count"]
            if status == "ACTIVE":
                active_count += count
            elif status == "INACTIVE":
                inactive_count += count
            elif status == "WITHDRAWN":
                withdrawn_count += count
            else:
                active_count += count  # デフォルトはACTIVE扱い
        
        # データ取得
        offset = (page - 1) * perPage
        query = f"SELECT * FROM members{where_clause} ORDER BY {sort_column} {sort_direction} LIMIT ? OFFSET ?"
        rows = conn.execute(query, params + [perPage, offset]).fetchall()
        
        members = []
        for row in rows:
            member_data = {
                # 基本情報
                "id": row["id"],
                "member_number": row["member_number"] or "",
                "memberNumber": row["member_number"] or "",  # フロントエンド互換
                "name": row["name"] or "",
                "kana": row["kana"] or "",
                "email": row["email"] or "",
                "phone": row["phone"] or "",
                "gender": row["gender"] or "",
                
                # ステータス関連
                "status": row["status"] or "ACTIVE",
                "title": row["title"] or "NONE",
                "user_type": row["user_type"] or "NORMAL",
                "userType": row["user_type"] or "NORMAL",  # フロントエンド互換
                "plan": row["plan"] or "BASIC",
                "payment_method": row["payment_method"] or "CARD",
                "paymentMethod": row["payment_method"] or "CARD",  # フロントエンド互換
                
                # 住所情報
                "postal_code": row["postal_code"] or "",
                "postalCode": row["postal_code"] or "",  # フロントエンド互換
                "prefecture": row["prefecture"] or "",
                "address2": row["address2"] or "",
                "address3": row["address3"] or "",
                
                # 組織関連
                "upline_id": row["upline_id"] or "",
                "uplineId": row["upline_id"] or "",  # フロントエンド互換
                "upline_name": row["upline_name"] or "",
                "uplineName": row["upline_name"] or "",  # フロントエンド互換
                "referrer_id": row["referrer_id"] or "",
                "referrerId": row["referrer_id"] or "",  # フロントエンド互換
                "referrer_name": row["referrer_name"] or "",
                "referrerName": row["referrer_name"] or "",  # フロントエンド互換
                
                # 口座情報
                "bank_name": row["bank_name"] or "",
                "bankName": row["bank_name"] or "",  # フロントエンド互換
                "bank_code": row["bank_code"] or "",
                "bankCode": row["bank_code"] or "",  # フロントエンド互換
                "branch_name": row["branch_name"] or "",
                "branchName": row["branch_name"] or "",  # フロントエンド互換
                "branch_code": row["branch_code"] or "",
                "branchCode": row["branch_code"] or "",  # フロントエンド互換
                "account_number": row["account_number"] or "",
                "accountNumber": row["account_number"] or "",  # フロントエンド互換
                "yucho_symbol": row["yucho_symbol"] or "",
                "yuchoSymbol": row["yucho_symbol"] or "",  # フロントエンド互換
                "yucho_number": row["yucho_number"] or "",
                "yuchoNumber": row["yucho_number"] or "",  # フロントエンド互換
                "account_type": row["account_type"] or "",
                "accountType": row["account_type"] or "",  # フロントエンド互換
                
                # 日付
                "registration_date": row["registration_date"] or "",
                "registrationDate": row["registration_date"] or "",  # フロントエンド互換
                "withdrawal_date": row["withdrawal_date"] or "",
                "withdrawalDate": row["withdrawal_date"] or "",  # フロントエンド互換
                "created_at": row["created_at"] or "",
                "createdAt": row["created_at"] or "",  # フロントエンド互換
                "updated_at": row["updated_at"] or "",
                "updatedAt": row["updated_at"] or "",  # フロントエンド互換
                
                # その他
                "notes": row["notes"] or "",
                "is_deleted": row["is_deleted"] or False,
                "isDeleted": row["is_deleted"] or False,  # フロントエンド互換
            }
            members.append(member_data)
        
        conn.close()
        
        return {
            "data": members,
            "members": members,
            "total": total,
            "total_count": total,
            "totalCount": total,
            "active_count": active_count,
            "activeCount": active_count,
            "inactive_count": inactive_count,
            "inactiveCount": inactive_count,
            "withdrawn_count": withdrawn_count,
            "withdrawnCount": withdrawn_count,
            "page": page,
            "perPage": perPage,
            "totalPages": (total + perPage - 1) // perPage,
            "source": "complete_database"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "data": [],
            "members": [],
            "total": 0,
            "page": page,
            "perPage": perPage
        }

@router.get("/{identifier}")
def get_member(identifier: str):
    """会員詳細取得（ID又は会員番号）"""
    try:
        db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        
        # 数字のみで短い場合(3桁以下)はIDとして検索、それ以外は会員番号として検索
        if identifier.isdigit() and len(identifier) <= 3:
            row = conn.execute("SELECT * FROM members WHERE id = ?", (int(identifier),)).fetchone()
        else:
            row = conn.execute("SELECT * FROM members WHERE member_number = ?", (identifier,)).fetchone()
        
        conn.close()
        
        if not row:
            return {"error": "Member not found"}
        
        # 完全なデータを返す
        return {
            "id": row["id"],
            "member_number": row["member_number"] or "",
            "memberNumber": row["member_number"] or "",
            "name": row["name"] or "",
            "kana": row["kana"] or "",
            "email": row["email"] or "",
            "phone": row["phone"] or "",
            "gender": row["gender"] or "",
            "status": row["status"] or "ACTIVE",
            "title": row["title"] or "NONE",
            "user_type": row["user_type"] or "NORMAL",
            "userType": row["user_type"] or "NORMAL",
            "plan": row["plan"] or "BASIC",
            "payment_method": row["payment_method"] or "CARD",
            "paymentMethod": row["payment_method"] or "CARD",
            "postal_code": row["postal_code"] or "",
            "postalCode": row["postal_code"] or "",
            "prefecture": row["prefecture"] or "",
            "address2": row["address2"] or "",
            "address3": row["address3"] or "",
            "upline_id": row["upline_id"] or "",
            "uplineId": row["upline_id"] or "",
            "upline_name": row["upline_name"] or "",
            "uplineName": row["upline_name"] or "",
            "referrer_id": row["referrer_id"] or "",
            "referrerId": row["referrer_id"] or "",
            "referrer_name": row["referrer_name"] or "",
            "referrerName": row["referrer_name"] or "",
            "bank_name": row["bank_name"] or "",
            "bankName": row["bank_name"] or "",
            "bank_code": row["bank_code"] or "",
            "bankCode": row["bank_code"] or "",
            "branch_name": row["branch_name"] or "",
            "branchName": row["branch_name"] or "",
            "branch_code": row["branch_code"] or "",
            "branchCode": row["branch_code"] or "",
            "account_number": row["account_number"] or "",
            "accountNumber": row["account_number"] or "",
            "yucho_symbol": row["yucho_symbol"] or "",
            "yuchoSymbol": row["yucho_symbol"] or "",
            "yucho_number": row["yucho_number"] or "",
            "yuchoNumber": row["yucho_number"] or "",
            "account_type": row["account_type"] or "",
            "accountType": row["account_type"] or "",
            "registration_date": row["registration_date"] or "",
            "registrationDate": row["registration_date"] or "",
            "withdrawal_date": row["withdrawal_date"] or "",
            "withdrawalDate": row["withdrawal_date"] or "",
            "created_at": row["created_at"] or "",
            "createdAt": row["created_at"] or "",
            "updated_at": row["updated_at"] or "",
            "updatedAt": row["updated_at"] or "",
            "notes": row["notes"] or "",
            "is_deleted": row["is_deleted"] or False,
            "isDeleted": row["is_deleted"] or False
        }
    except Exception as e:
        return {"error": str(e)}

@router.put("/{identifier}")
def update_member(identifier: str, member_data: MemberUpdate):
    """会員情報更新（ID又は会員番号）"""
    try:
        # フロントエンドから送信されたデータを全てログ出力
        received_data = member_data.model_dump(exclude_unset=True)
        print(f"=== PUT UPDATE DEBUG - Member {identifier} ===")
        print(f"Received {len(received_data)} fields:")
        for field, value in received_data.items():
            print(f"  {field}: {repr(value)}")
        print("=" * 50)
        
        db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        
        # 現在のデータを取得
        if identifier.isdigit() and len(identifier) <= 3:
            current_row = conn.execute("SELECT * FROM members WHERE id = ?", (int(identifier),)).fetchone()
        else:
            current_row = conn.execute("SELECT * FROM members WHERE member_number = ?", (identifier,)).fetchone()
        
        if not current_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Member not found")
        
        # 更新データの準備
        update_fields = []
        update_params = []
        
        # camelCase → snake_case マッピング
        field_mapping = {
            'userType': 'user_type',
            'paymentMethod': 'payment_method', 
            'postalCode': 'postal_code',
            'uplineId': 'upline_id',
            'uplineName': 'upline_name',
            'referrerId': 'referrer_id',
            'referrerName': 'referrer_name',
            'bankName': 'bank_name',
            'bankCode': 'bank_code',
            'branchName': 'branch_name',
            'branchCode': 'branch_code',
            'accountNumber': 'account_number',
            'yuchoSymbol': 'yucho_symbol',
            'yuchoNumber': 'yucho_number',
            'accountType': 'account_type',
            'registrationDate': 'registration_date',
            'withdrawalDate': 'withdrawal_date'
        }
        
        # 送信されたフィールドのみ更新
        for field, value in member_data.model_dump(exclude_unset=True).items():
            if value is not None:
                # camelCaseの場合はsnake_caseに変換
                db_field = field_mapping.get(field, field)
                update_fields.append(f"{db_field} = ?")
                update_params.append(value)
        
        # updated_atを追加
        update_fields.append("updated_at = ?")
        update_params.append(datetime.now().isoformat())
        
        # WHERE条件の準備
        if identifier.isdigit() and len(identifier) <= 3:
            where_clause = "id = ?"
            update_params.append(int(identifier))
        else:
            where_clause = "member_number = ?"
            update_params.append(identifier)
        
        # 更新実行
        if update_fields:
            update_query = f"UPDATE members SET {', '.join(update_fields)} WHERE {where_clause}"
            conn.execute(update_query, update_params)
            conn.commit()
        
        # 更新後のデータを取得
        if identifier.isdigit() and len(identifier) <= 3:
            updated_row = conn.execute("SELECT * FROM members WHERE id = ?", (int(identifier),)).fetchone()
        else:
            updated_row = conn.execute("SELECT * FROM members WHERE member_number = ?", (identifier,)).fetchone()
        
        conn.close()
        
        # 更新されたデータを完全な形式で返す
        return {
            "id": updated_row["id"],
            "member_number": updated_row["member_number"] or "",
            "memberNumber": updated_row["member_number"] or "",
            "name": updated_row["name"] or "",
            "kana": updated_row["kana"] or "",
            "email": updated_row["email"] or "",
            "phone": updated_row["phone"] or "",
            "gender": updated_row["gender"] or "",
            "status": updated_row["status"] or "ACTIVE",
            "title": updated_row["title"] or "NONE",
            "user_type": updated_row["user_type"] or "NORMAL",
            "userType": updated_row["user_type"] or "NORMAL",
            "plan": updated_row["plan"] or "BASIC",
            "payment_method": updated_row["payment_method"] or "CARD",
            "paymentMethod": updated_row["payment_method"] or "CARD",
            "postal_code": updated_row["postal_code"] or "",
            "postalCode": updated_row["postal_code"] or "",
            "prefecture": updated_row["prefecture"] or "",
            "address2": updated_row["address2"] or "",
            "address3": updated_row["address3"] or "",
            "upline_id": updated_row["upline_id"] or "",
            "uplineId": updated_row["upline_id"] or "",
            "upline_name": updated_row["upline_name"] or "",
            "uplineName": updated_row["upline_name"] or "",
            "referrer_id": updated_row["referrer_id"] or "",
            "referrerId": updated_row["referrer_id"] or "",
            "referrer_name": updated_row["referrer_name"] or "",
            "referrerName": updated_row["referrer_name"] or "",
            "bank_name": updated_row["bank_name"] or "",
            "bankName": updated_row["bank_name"] or "",
            "bank_code": updated_row["bank_code"] or "",
            "bankCode": updated_row["bank_code"] or "",
            "branch_name": updated_row["branch_name"] or "",
            "branchName": updated_row["branch_name"] or "",
            "branch_code": updated_row["branch_code"] or "",
            "branchCode": updated_row["branch_code"] or "",
            "account_number": updated_row["account_number"] or "",
            "accountNumber": updated_row["account_number"] or "",
            "yucho_symbol": updated_row["yucho_symbol"] or "",
            "yuchoSymbol": updated_row["yucho_symbol"] or "",
            "yucho_number": updated_row["yucho_number"] or "",
            "yuchoNumber": updated_row["yucho_number"] or "",
            "account_type": updated_row["account_type"] or "",
            "accountType": updated_row["account_type"] or "",
            "registration_date": updated_row["registration_date"] or "",
            "registrationDate": updated_row["registration_date"] or "",
            "withdrawal_date": updated_row["withdrawal_date"] or "",
            "withdrawalDate": updated_row["withdrawal_date"] or "",
            "created_at": updated_row["created_at"] or "",
            "createdAt": updated_row["created_at"] or "",
            "updated_at": updated_row["updated_at"] or "",
            "updatedAt": updated_row["updated_at"] or "",
            "notes": updated_row["notes"] or "",
            "is_deleted": updated_row["is_deleted"] or False,
            "isDeleted": updated_row["is_deleted"] or False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))