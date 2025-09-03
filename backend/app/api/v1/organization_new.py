"""
新しい組織図API エンドポイント
データベースから退会者を含む組織構造を取得
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, text

from app.database import get_db
from app.models.organization import OrganizationPosition, Withdrawal, PositionType
from app.models.member import Member

router = APIRouter()

@router.get("/tree")
def get_organization_tree(
    member_id: Optional[int] = Query(None, description="特定メンバーからのツリー取得"),
    max_level: Optional[int] = Query(None, description="最大表示レベル")
):
    """組織ツリー取得（データベース版）- 一時的にCSVフォールバック"""
    try:
        # 一時的にCSV版の組織図API（organization.py）を使用
        from app.api.v1.organization import read_organization_csv, build_organization_tree
        
        # CSVデータを読み込み
        org_data = read_organization_csv()
        
        if max_level is not None:
            org_data = [item for item in org_data if item['level'] <= max_level]
        
        # ツリー構造構築
        root_nodes = build_organization_tree(org_data)
        
        # 統計計算
        total_members = len(org_data)
        max_level_found = max([item['level'] for item in org_data]) if org_data else 0
        active_members = len([item for item in org_data if not item['is_withdrawn']])
        withdrawn_members = total_members - active_members
        total_sales = sum([item['left_sales'] + item['right_sales'] for item in org_data])
        
        return {
            'root_nodes': [node.dict() for node in root_nodes],  # Pydantic model to dict
            'total_members': total_members,
            'active_members': active_members,
            'withdrawn_members': withdrawn_members,
            'max_level': max_level_found,
            'total_sales': total_sales,
            'data_source': 'CSV (temporary fallback)'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"組織ツリー取得エラー: {str(e)}")

@router.get("/stats")
def get_organization_stats(db: Session = Depends(get_db)):
    """組織統計取得（データベース版）"""
    try:
        # 基本統計
        total_positions = db.query(OrganizationPosition).count()
        active_positions = db.query(OrganizationPosition).filter(
            OrganizationPosition.member_id.isnot(None)
        ).count()
        withdrawn_positions = db.query(OrganizationPosition).filter(
            OrganizationPosition.withdrawn_id.isnot(None)
        ).count()
        
        # 階層統計
        max_level_result = db.query(func.max(OrganizationPosition.level)).scalar()
        max_level = max_level_result if max_level_result is not None else 0
        
        avg_level_result = db.query(func.avg(OrganizationPosition.level)).scalar()
        average_level = float(avg_level_result) if avg_level_result is not None else 0.0
        
        # 売上統計
        total_left_sales = db.query(func.sum(OrganizationPosition.left_sales)).scalar() or 0
        total_right_sales = db.query(func.sum(OrganizationPosition.right_sales)).scalar() or 0
        
        return {
            'total_members': total_positions,
            'active_members': active_positions,
            'withdrawn_members': withdrawn_positions,
            'max_level': max_level,
            'average_level': round(average_level, 2),
            'total_left_sales': float(total_left_sales),
            'total_right_sales': float(total_right_sales),
            'total_sales': float(total_left_sales + total_right_sales)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"組織統計取得エラー: {str(e)}")

@router.get("/member/{identifier}/downline")
def get_member_downline(
    identifier: str,
    max_depth: Optional[int] = Query(10, description="最大深度"),
    db: Session = Depends(get_db)
):
    """特定メンバーのダウンライン取得"""
    try:
        # メンバー番号でアクティブメンバーを検索
        target_position = None
        
        # まずアクティブメンバーから検索
        active_member = db.query(Member).filter(Member.member_number == identifier).first()
        if active_member:
            target_position = db.query(OrganizationPosition).filter(
                OrganizationPosition.member_id == active_member.id
            ).first()
        
        # 見つからない場合は退会者から検索
        if not target_position:
            withdrawal = db.query(Withdrawal).filter(
                or_(
                    Withdrawal.withdrawal_number == identifier,
                    Withdrawal.original_member_number == identifier
                )
            ).first()
            if withdrawal:
                target_position = db.query(OrganizationPosition).filter(
                    OrganizationPosition.withdrawn_id == withdrawal.id
                ).first()
        
        if not target_position:
            raise HTTPException(status_code=404, detail=f"メンバー {identifier} が見つかりません")
        
        # ダウンライン検索（指定した深度まで）
        target_level = target_position.level
        downline_positions = db.query(OrganizationPosition).filter(
            OrganizationPosition.level > target_level,
            OrganizationPosition.level <= target_level + max_depth,
            OrganizationPosition.hierarchy_path.like(f"{target_position.hierarchy_path}%")
        ).options(
            joinedload(OrganizationPosition.member),
            joinedload(OrganizationPosition.withdrawal)
        ).all()
        
        # ダウンラインデータを構築
        downline_tree = []
        for position in downline_positions:
            if position.member_id:
                member = position.member
                node_data = {
                    'id': str(position.id),
                    'member_number': member.member_number,
                    'name': member.name,
                    'title': member.title,
                    'status': 'ACTIVE',
                    'is_withdrawn': False
                }
            else:
                withdrawal = position.withdrawal
                node_data = {
                    'id': str(position.id),
                    'member_number': withdrawal.withdrawal_number,
                    'name': '退会者',
                    'title': '',
                    'status': 'WITHDRAWN',
                    'is_withdrawn': True,
                    'original_name': withdrawal.original_name
                }
            
            node_data.update({
                'level': position.level,
                'position_type': position.position_type.value,
                'left_count': position.left_count,
                'right_count': position.right_count
            })
            
            downline_tree.append(node_data)
        
        # ターゲットメンバー情報
        if target_position.member_id:
            member = target_position.member
            target_member = {
                'id': str(target_position.id),
                'member_number': member.member_number,
                'name': member.name,
                'title': member.title,
                'status': 'ACTIVE'
            }
        else:
            withdrawal = target_position.withdrawal
            target_member = {
                'id': str(target_position.id),
                'member_number': withdrawal.withdrawal_number,
                'name': '退会者',
                'title': '',
                'status': 'WITHDRAWN',
                'original_name': withdrawal.original_name
            }
        
        return {
            'target_member': target_member,
            'downline_tree': downline_tree,
            'downline_count': len(downline_tree)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ダウンライン取得エラー: {str(e)}")

@router.get("/test/positions")
def test_organization_positions():
    """組織ポジションのテスト用エンドポイント（依存性注入なしでテスト）"""
    try:
        # 全く新しいエンジンとセッションを作成
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import os
        
        # 絶対パスでデータベースURLを作成
        database_url = f"sqlite:///{os.path.abspath('./iroas_boss_v2.db')}"
        fresh_engine = create_engine(database_url, echo=False)
        
        Session = sessionmaker(bind=fresh_engine)
        session = Session()
        
        try:
            # 明示的にコミットされたデータを読み取る
            session.commit()  # 現在のトランザクションをコミット（空でも）
            
            # ORM クエリでテスト
            orm_count = session.query(OrganizationPosition).count()
            withdrawal_count = session.query(Withdrawal).count()
            member_count = session.query(Member).count()
            
            # 最初の3件を取得
            positions = session.query(OrganizationPosition).limit(3).all()
            position_data = []
            for pos in positions:
                position_data.append({
                    'id': pos.id,
                    'level': pos.level,
                    'member_id': pos.member_id,
                    'withdrawn_id': pos.withdrawn_id,
                    'position_type': pos.position_type.value if pos.position_type else None
                })
            
            return {
                'database_connection': 'OK - Fresh Engine',
                'database_url': database_url,
                'working_directory': os.getcwd(),
                'organization_positions': orm_count,
                'withdrawals': withdrawal_count,
                'members': member_count,
                'sample_positions': position_data
            }
            
        finally:
            session.close()
        
    except Exception as e:
        import traceback
        return {
            'error': str(e),
            'traceback': traceback.format_exc()
        }