#!/usr/bin/env python3
"""組織図・会員管理API最小限サーバー"""

import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from app.api.v1.organization_db_only import get_organization_tree_db_only
from app.schemas.organization import OrganizationTree
from app.api.v1 import unified

# FastAPIアプリケーション
app = FastAPI(title="組織図API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 統合APIルーター追加
app.include_router(unified.router, prefix="/api/v1", tags=["統合API"])

@app.get("/api/v1/organization/tree", response_model=OrganizationTree)
def get_organization_tree_endpoint(
    member_id: Optional[str] = Query(None, description="特定メンバーをルートとしたサブツリー取得（会員番号）"),
    max_level: Optional[int] = Query(3, description="最大表示レベル（デフォルト3階層）"),
    active_only: Optional[bool] = Query(False, description="アクティブメンバーのみ表示")
):
    """組織ツリー取得（段階的表示）"""
    try:
        return get_organization_tree_db_only(member_id, max_level, active_only)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/members")
def get_members(
    memberNumber: Optional[str] = Query("", description="会員番号で検索"),
    name: Optional[str] = Query("", description="氏名で検索"),
    email: Optional[str] = Query("", description="メールアドレスで検索"),
    page: int = Query(1, description="ページ番号"),
    perPage: int = Query(20, description="1ページあたりの件数"),
    sortBy: str = Query("memberNumber", description="ソート対象フィールド"),
    sortOrder: str = Query("asc", description="ソート順序")
):
    """会員一覧取得"""
    try:
        # データベース接続
        db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # ベースクエリ
        query = """
        SELECT 
            id, status, member_number, name, kana, email, title, user_type, plan, 
            payment_method, registration_date, withdrawal_date, phone, gender,
            postal_code, prefecture, address2, address3, upline_id, upline_name,
            referrer_id, referrer_name, bank_name, bank_code, branch_name, 
            branch_code, account_number, yucho_symbol, yucho_number, account_type, notes
        FROM members 
        WHERE 1=1
        """
        params = []
        
        # フィルター条件
        if memberNumber and memberNumber.strip():
            query += " AND member_number LIKE ?"
            params.append(f"%{memberNumber.strip()}%")
            
        if name and name.strip():
            query += " AND name LIKE ?"
            params.append(f"%{name.strip()}%")
            
        if email and email.strip():
            query += " AND email LIKE ?"
            params.append(f"%{email.strip()}%")
        
        # ソート
        valid_sort_fields = ["memberNumber", "name", "email", "status", "registration_date"]
        if sortBy in valid_sort_fields:
            # camelCaseをsnake_caseに変換
            db_sort_field = "member_number" if sortBy == "memberNumber" else sortBy
            sort_order = "ASC" if sortOrder.lower() == "asc" else "DESC"
            query += f" ORDER BY {db_sort_field} {sort_order}"
        
        # ページング
        offset = (page - 1) * perPage
        query += f" LIMIT {perPage} OFFSET {offset}"
        
        # 実行
        rows = conn.execute(query, params).fetchall()
        
        # 総件数取得
        count_query = "SELECT COUNT(*) as total FROM members WHERE 1=1"
        if memberNumber and memberNumber.strip():
            count_query += " AND member_number LIKE ?"
        if name and name.strip():
            count_query += " AND name LIKE ?"
        if email and email.strip():
            count_query += " AND email LIKE ?"
        
        total_count = conn.execute(count_query, params[:-2] if len(params) > 2 else params).fetchone()["total"]
        
        # データ変換
        members = []
        for row in rows:
            member = dict(row)
            # camelCase変換（フロントエンド互換）
            member["memberNumber"] = member["member_number"]
            member["userType"] = member["user_type"]
            member["paymentMethod"] = member["payment_method"]
            member["registrationDate"] = member["registration_date"]
            member["withdrawalDate"] = member["withdrawal_date"]
            member["postalCode"] = member["postal_code"]
            member["uplineId"] = member["upline_id"]
            member["uplineName"] = member["upline_name"]
            member["referrerId"] = member["referrer_id"]
            member["referrerName"] = member["referrer_name"]
            member["bankName"] = member["bank_name"]
            member["bankCode"] = member["bank_code"]
            member["branchName"] = member["branch_name"]
            member["branchCode"] = member["branch_code"]
            member["accountNumber"] = member["account_number"]
            member["yuchoSymbol"] = member["yucho_symbol"]
            member["yuchoNumber"] = member["yucho_number"]
            member["accountType"] = member["account_type"]
            members.append(member)
        
        # 統計情報取得
        stats_query = """
        SELECT 
            COUNT(*) as total_members,
            COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_members,
            COUNT(CASE WHEN status = 'INACTIVE' THEN 1 END) as inactive_members
        FROM members
        """
        stats = conn.execute(stats_query).fetchone()
        
        # 退会者数取得
        withdrawal_query = "SELECT COUNT(*) as withdrawn_count FROM withdrawals"
        withdrawal_stats = conn.execute(withdrawal_query).fetchone()
        
        conn.close()
        
        return {
            "members": members,
            "total": total_count,
            "page": page,
            "perPage": perPage,
            "totalPages": (total_count + perPage - 1) // perPage,
            "total_count": stats["total_members"] + withdrawal_stats["withdrawn_count"],
            "active_count": stats["active_members"],
            "inactive_count": stats["inactive_members"],
            "withdrawn_count": withdrawal_stats["withdrawn_count"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/organization/stats")
def get_organization_stats():
    """組織統計取得"""
    try:
        # データベース接続
        db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # 基本統計（現在のメンバーテーブルから）
        member_stats_query = """
        SELECT 
            COUNT(*) as current_members,
            COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_members,
            COUNT(CASE WHEN status = 'INACTIVE' THEN 1 END) as inactive_members
        FROM members
        """
        member_stats = conn.execute(member_stats_query).fetchone()
        
        # 退会者数取得
        withdrawal_query = "SELECT COUNT(*) as withdrawn_count FROM withdrawals"
        withdrawal_stats = conn.execute(withdrawal_query).fetchone()
        
        # 総メンバー数（現在 + 退会済み）
        total_members = member_stats["current_members"] + withdrawal_stats["withdrawn_count"]
        
        # 組織位置テーブルから最大レベル取得
        level_query = "SELECT MAX(level) as max_level, AVG(level) as average_level FROM organization_positions"
        level_stats = conn.execute(level_query).fetchone()
        
        conn.close()
        
        return {
            "total_members": total_members,
            "active_members": member_stats["active_members"],
            "withdrawn_members": withdrawal_stats["withdrawn_count"],
            "max_level": level_stats["max_level"] or 0,
            "average_level": round(level_stats["average_level"] or 0, 2),
            "total_left_sales": 0.0,  # 今回は簡略化
            "total_right_sales": 0.0, # 今回は簡略化
            "total_sales": 0.0        # 今回は簡略化
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "組織図API 最小限サーバー"}

@app.get("/api/v1/members/{member_number}")
def get_member_detail(member_number: str):
    """統合された会員詳細情報を取得"""
    try:
        # データベース接続
        db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # 会員基本情報取得
        member_query = """
        SELECT 
            id, status, member_number, name, kana, email, title, user_type, plan, 
            payment_method, registration_date, withdrawal_date, phone, gender,
            postal_code, prefecture, address2, address3, upline_id, upline_name,
            referrer_id, referrer_name, bank_name, bank_code, branch_name, 
            branch_code, account_number, yucho_symbol, yucho_number, account_type, notes
        FROM members 
        WHERE member_number = ?
        """
        member_row = conn.execute(member_query, (member_number,)).fetchone()
        
        if not member_row:
            raise HTTPException(status_code=404, detail="会員が見つかりません")
        
        # 組織情報取得
        org_query = """
        SELECT 
            op.level, op.hierarchy_path, op.left_count, op.right_count, 
            op.left_sales, op.right_sales, op.position_type
        FROM organization_positions op
        LEFT JOIN members m ON op.member_id = m.id
        WHERE m.member_number = ?
        """
        org_row = conn.execute(org_query, (member_number,)).fetchone()
        
        # データ変換
        member_data = dict(member_row)
        
        # 組織情報を追加
        if org_row:
            member_data.update({
                "organization_level": org_row["level"],
                "hierarchy_path": org_row["hierarchy_path"],
                "left_count": org_row["left_count"] or 0,
                "right_count": org_row["right_count"] or 0,
                "left_sales": float(org_row["left_sales"]) if org_row["left_sales"] else 0.0,
                "right_sales": float(org_row["right_sales"]) if org_row["right_sales"] else 0.0,
                "is_direct": org_row["position_type"] == "DIRECT"
            })
        
        # camelCase変換
        member_data["memberNumber"] = member_data["member_number"]
        member_data["userType"] = member_data["user_type"]
        member_data["paymentMethod"] = member_data["payment_method"]
        member_data["registrationDate"] = member_data["registration_date"]
        member_data["withdrawalDate"] = member_data["withdrawal_date"]
        member_data["postalCode"] = member_data["postal_code"]
        member_data["uplineId"] = member_data["upline_id"]
        member_data["uplineName"] = member_data["upline_name"]
        member_data["referrerId"] = member_data["referrer_id"]
        member_data["referrerName"] = member_data["referrer_name"]
        member_data["bankName"] = member_data["bank_name"]
        member_data["bankCode"] = member_data["bank_code"]
        member_data["branchName"] = member_data["branch_name"]
        member_data["branchCode"] = member_data["branch_code"]
        member_data["accountNumber"] = member_data["account_number"]
        member_data["yuchoSymbol"] = member_data["yucho_symbol"]
        member_data["yuchoNumber"] = member_data["yucho_number"]
        member_data["accountType"] = member_data["account_type"]
        
        conn.close()
        return member_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/organization/member/{member_number}")
def get_organization_member_detail(member_number: str):
    """組織図から見たメンバー詳細情報を取得（統合データ）"""
    try:
        # データベース接続
        db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # 会員基本情報と組織情報を統合取得
        query = """
        SELECT 
            m.id, m.status, m.member_number, m.name, m.kana, m.email, m.title, 
            m.user_type, m.plan, m.payment_method, m.registration_date, m.withdrawal_date, 
            m.phone, m.gender, m.postal_code, m.prefecture, m.address2, m.address3, 
            m.upline_id, m.upline_name, m.referrer_id, m.referrer_name, 
            m.bank_name, m.bank_code, m.branch_name, m.branch_code, m.account_number, 
            m.yucho_symbol, m.yucho_number, m.account_type, m.notes,
            op.level, op.hierarchy_path, op.left_count, op.right_count, 
            op.left_sales, op.right_sales, op.position_type
        FROM members m
        LEFT JOIN organization_positions op ON m.id = op.member_id
        WHERE m.member_number = ?
        """
        row = conn.execute(query, (member_number,)).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="会員が見つかりません")
        
        # 組織図ノード形式でデータを構築
        member_data = {
            "id": f"{row['level'] or 0}-{row['member_number']}",
            "member_number": row["member_number"],
            "name": row["name"],
            "title": row["title"] or "称号なし",
            "level": row["level"] or 0,
            "hierarchy_path": row["hierarchy_path"] or "",
            "registration_date": row["registration_date"],
            "is_direct": row["position_type"] == "DIRECT" if row["position_type"] else False,
            "is_withdrawn": row["status"] == "WITHDRAWN",
            "left_count": row["left_count"] or 0,
            "right_count": row["right_count"] or 0,
            "left_sales": float(row["left_sales"]) if row["left_sales"] else 0.0,
            "right_sales": float(row["right_sales"]) if row["right_sales"] else 0.0,
            "new_purchase": 0.0,
            "repeat_purchase": 0.0,
            "additional_purchase": 0.0,
            "children": [],
            "is_expanded": True,
            "status": row["status"],
            
            # 追加の会員情報
            "email": row["email"],
            "phone": row["phone"],
            "gender": row["gender"],
            "postal_code": row["postal_code"],
            "prefecture": row["prefecture"],
            "address2": row["address2"],
            "address3": row["address3"],
            "user_type": row["user_type"],
            "plan": row["plan"],
            "payment_method": row["payment_method"],
            "upline_id": row["upline_id"],
            "upline_name": row["upline_name"],
            "referrer_id": row["referrer_id"],
            "referrer_name": row["referrer_name"],
            "bank_name": row["bank_name"],
            "bank_code": row["bank_code"],
            "branch_name": row["branch_name"],
            "branch_code": row["branch_code"],
            "account_number": row["account_number"],
            "yucho_symbol": row["yucho_symbol"],
            "yucho_number": row["yucho_number"],
            "account_type": row["account_type"],
            "notes": row["notes"]
        }
        
        conn.close()
        return member_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)