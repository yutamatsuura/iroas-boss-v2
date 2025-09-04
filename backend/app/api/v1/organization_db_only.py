"""
組織図API - 完全データベース専用実装
CSV依存を排除し、データベースのみを使用した安全な実装
"""

import sqlite3
from typing import Dict, List, Optional
from fastapi import HTTPException

from app.schemas.organization import OrganizationNode, OrganizationTree, OrganizationStats

def get_organization_tree_db_only(
    member_id: Optional[str] = None,
    max_level: Optional[int] = 3,
    active_only: Optional[bool] = False
) -> OrganizationTree:
    """データベースのみを使用した組織ツリー取得"""
    try:
        # レベル制限の適用
        if max_level is None:
            max_level = 5
        elif max_level > 100:
            max_level = 100
        
        # データベース接続
        db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        
        # メンバーフォーカス時の処理
        focus_member_level = None
        if member_id:
            normalized_member_id = member_id.zfill(11)
            focus_query = """
            SELECT op.level 
            FROM organization_positions op
            LEFT JOIN members m ON op.member_id = m.id
            LEFT JOIN withdrawals w ON op.withdrawn_id = w.id
            WHERE (m.member_number = ? OR w.original_member_number = ?)
            LIMIT 1
            """
            focus_row = conn.execute(focus_query, (normalized_member_id, normalized_member_id)).fetchone()
            if focus_row:
                focus_member_level = focus_row['level']
        
        # 組織データクエリ
        query = """
        SELECT 
            op.id as position_id, 
            op.parent_id, 
            op.level, 
            op.hierarchy_path, 
            op.left_count, 
            op.right_count, 
            op.left_sales, 
            op.right_sales, 
            op.position_type,
            CASE 
                WHEN op.member_id IS NOT NULL THEN m.member_number
                WHEN op.withdrawn_id IS NOT NULL THEN w.original_member_number
            END as member_number,
            CASE 
                WHEN op.member_id IS NOT NULL THEN m.name
                WHEN op.withdrawn_id IS NOT NULL THEN CONCAT('（退会者）', w.original_name)
            END as name,
            CASE 
                WHEN op.member_id IS NOT NULL THEN m.title
                ELSE 'WITHDRAWN'
            END as title,
            CASE 
                WHEN op.member_id IS NOT NULL THEN m.status
                ELSE 'WITHDRAWN'
            END as status,
            CASE 
                WHEN op.member_id IS NOT NULL THEN m.registration_date
                ELSE NULL
            END as registration_date,
            CASE 
                WHEN op.withdrawn_id IS NOT NULL THEN 1
                ELSE 0
            END as is_withdrawn,
            CASE 
                WHEN op.position_type = 'DIRECT' THEN 1
                ELSE 0
            END as is_direct
        FROM organization_positions op
        LEFT JOIN members m ON op.member_id = m.id
        LEFT JOIN withdrawals w ON op.withdrawn_id = w.id
        WHERE 1=1
        """
        
        params = []
        
        # レベル制限を適用
        if focus_member_level is not None:
            # フォーカス時: 指定メンバーから相対的なレベル制限
            query += " AND op.level BETWEEN ? AND ?"
            params.extend([focus_member_level, focus_member_level + max_level])
        else:
            # 通常時: 絶対的なレベル制限
            query += " AND op.level <= ?"
            params.append(max_level)
        
        query += " ORDER BY op.level, op.hierarchy_path"
        
        rows = conn.execute(query, params).fetchall()
        print(f"[DEBUG] 取得した行数: {len(rows)}")
        
        # データ変換
        org_data = []
        for row in rows:
            # アクティブのみフィルター
            if active_only and row['is_withdrawn']:
                print(f"[DEBUG] 退会者のためスキップ: {row['name']} (Level {row['level']})")
                continue
                
            if active_only:
                print(f"[DEBUG] アクティブフィルター通過: {row['name']} (Level {row['level']}) Status: {row['status']}")
                
            org_data.append({
                'id': f"{row['level']}-{row['member_number']}",
                'member_number': row['member_number'],
                'name': row['name'],
                'title': _translate_title(row['title']),
                'level': row['level'],
                'hierarchy_path': row['hierarchy_path'],
                'registration_date': row['registration_date'],
                'is_direct': bool(row['is_direct']),
                'is_withdrawn': bool(row['is_withdrawn']),
                'left_count': row['left_count'] or 0,
                'right_count': row['right_count'] or 0,
                'left_sales': float(row['left_sales']) if row['left_sales'] else 0.0,
                'right_sales': float(row['right_sales']) if row['right_sales'] else 0.0,
                'new_purchase': 0.0,  # デフォルト値
                'repeat_purchase': 0.0,  # デフォルト値
                'additional_purchase': 0.0,  # デフォルト値
                'status': row['status'] if not row['is_withdrawn'] else 'WITHDRAWN'
            })
        
        # 親子関係構築
        node_map = {}
        root_nodes = []
        
        # ノード作成
        for item in org_data:
            node = OrganizationNode(
                id=item['id'],
                member_number=item['member_number'],
                name=item['name'],
                title=item['title'],
                level=item['level'],
                hierarchy_path=item['hierarchy_path'],
                registration_date=item['registration_date'],
                is_direct=item['is_direct'],
                is_withdrawn=item['is_withdrawn'],
                left_count=item['left_count'],
                right_count=item['right_count'],
                left_sales=item['left_sales'],
                right_sales=item['right_sales'],
                new_purchase=item['new_purchase'],
                repeat_purchase=item['repeat_purchase'],
                additional_purchase=item['additional_purchase'],
                children=[],
                is_expanded=True,
                status=item['status']
            )
            node_map[item['id']] = node
            
            # ルートノード判定（レベル0またはフォーカス時の基準レベル）
            base_level = focus_member_level if focus_member_level is not None else 0
            if item['level'] == base_level:
                root_nodes.append(node)
        
        # 親子関係構築（データベースのparent_idを使用）
        _build_hierarchy_relationships_db(conn, org_data, node_map)
        
        # 階層スキップ表示ノードを挿入（一時的に無効化）
        # _insert_level_skip_nodes(node_map)
        
        # アクティブフィルター時: 親を持たないノード（親が退会者でフィルターされた場合）をルートに追加
        if active_only:
            all_children = set()
            for node in node_map.values():
                for child in node.children:
                    all_children.add(child.id)
            
            # 子として含まれていない（親を持たない）ノードを見つけてルートに追加
            for node in node_map.values():
                if node.id not in all_children and node not in root_nodes:
                    root_nodes.append(node)
                    print(f"[DEBUG] 孤立ノードをルートに追加: {node.name} (Level {node.level})")
        
        # フォーカスメンバーが指定されている場合、そのメンバーのみをルートとして設定
        if member_id:
            normalized_member_id = member_id.zfill(11)
            focus_root_nodes = []
            
            # 指定されたメンバーをルートノードとして検索
            for item in org_data:
                if item['member_number'] == normalized_member_id:
                    focus_node = node_map.get(item['id'])
                    if focus_node:
                        focus_root_nodes.append(focus_node)
                        print(f"[DEBUG] フォーカスルート設定: {focus_node.name} ({focus_node.member_number}) Level {focus_node.level}")
                    break
            
            if focus_root_nodes:
                root_nodes = focus_root_nodes
            else:
                print(f"[WARNING] フォーカス対象が見つかりません: {normalized_member_id}")
        
        # 統計情報計算
        active_members = sum(1 for item in org_data if not item['is_withdrawn'])
        withdrawn_members = sum(1 for item in org_data if item['is_withdrawn'])
        max_level_actual = max([item['level'] for item in org_data]) if org_data else 0
        total_sales = sum(item['left_sales'] + item['right_sales'] for item in org_data)
        
        conn.close()
        
        return OrganizationTree(
            root_nodes=root_nodes,
            total_members=len(org_data),
            max_level=max_level_actual,
            total_sales=total_sales,
            active_members=active_members,
            withdrawn_members=withdrawn_members
        )
        
    except Exception as e:
        import traceback
        print(f"組織ツリーエラー詳細: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"組織ツリー取得エラー: {str(e)}")

def _translate_title(title: str) -> str:
    """称号の日本語翻訳"""
    title_map = {
        'COMPANY': '会社',
        'EMPEROR': 'エンペラー',
        'EMPRESS': 'エンブレス', 
        'KING': 'キング',
        'QUEEN': 'クイーン',
        'LORD': 'ロード',
        'LADY': 'レディ',
        'KNIGHT': 'ナイト',
        'DAME': 'デイム',
        'KNIGHT_DAME': 'ナイト/デイム',
        'NONE': '称号なし',
        'WITHDRAWN': '退会済み'
    }
    return title_map.get(title, title)

def _insert_level_skip_nodes(node_map: Dict):
    """階層スキップ表示ノードを挿入"""
    
    # 各ノードの子ノードをチェックして、レベルの飛びがある場合にスキップノードを挿入
    for parent_node in list(node_map.values()):
        if not parent_node.children:
            continue
            
        # 子ノードをレベル順にソート
        children_by_level = sorted(parent_node.children, key=lambda x: x.level)
        new_children = []
        
        for child in children_by_level:
            level_gap = child.level - parent_node.level
            
            # レベルが2以上飛んでいる場合、スキップノードを挿入
            if level_gap > 1:
                skipped_levels = level_gap - 1
                skip_node_id = f"skip-{parent_node.level + 1}-to-{child.level - 1}"
                
                skip_node = OrganizationNode(
                    id=skip_node_id,
                    member_number="",
                    name=f"...{skipped_levels}階層スキップ...",
                    title="",
                    level=parent_node.level + 1,
                    hierarchy_path="",
                    registration_date=None,
                    is_direct=False,
                    is_withdrawn=False,
                    left_count=0,
                    right_count=0,
                    left_sales=0,
                    right_sales=0,
                    new_purchase=0,
                    repeat_purchase=0,
                    additional_purchase=0,
                    children=[child],
                    is_expanded=True,
                    status="SKIP"
                )
                
                new_children.append(skip_node)
                node_map[skip_node_id] = skip_node
                print(f"[DEBUG] 階層スキップノード挿入: {skip_node.name} (Level {parent_node.level} → {child.level})")
            else:
                new_children.append(child)
        
        parent_node.children = new_children

def _build_hierarchy_relationships_db(conn, org_data: List[Dict], node_map: Dict):
    """データベースのparent_idを使用した正確な親子関係構築"""
    # position_idからorg_dataのidへのマッピングを作成
    position_to_org_id = {}
    
    # position_idを取得するクエリを実行
    for item in org_data:
        query = """
        SELECT op.id as position_id, op.parent_id
        FROM organization_positions op
        LEFT JOIN members m ON op.member_id = m.id
        LEFT JOIN withdrawals w ON op.withdrawn_id = w.id
        WHERE (m.member_number = ? OR w.original_member_number = ?)
        """
        row = conn.execute(query, (item['member_number'], item['member_number'])).fetchone()
        if row:
            position_to_org_id[row['position_id']] = {
                'org_id': item['id'],
                'parent_id': row['parent_id']
            }
    
    # 親子関係を構築
    for position_id, data in position_to_org_id.items():
        if data['parent_id'] is not None:
            # 親のposition_idから親のorg_idを検索（現在のorg_dataにある親の中で）
            parent_found = False
            for parent_pos_id, parent_data in position_to_org_id.items():
                if parent_pos_id == data['parent_id']:
                    parent_node = node_map.get(parent_data['org_id'])
                    child_node = node_map.get(data['org_id'])
                    if parent_node and child_node:
                        parent_node.children.append(child_node)
                        print(f"[DEBUG] 親子関係構築: {parent_node.name} → {child_node.name}")
                        parent_found = True
                    break
            

def _build_hierarchy_relationships(org_data: List[Dict], node_map: Dict):
    """階層パスベースで親子関係を構築（バックアップ用）"""
    # レベルごとにデータをグループ化
    by_level = {}
    for item in org_data:
        level = item['level']
        if level not in by_level:
            by_level[level] = []
        by_level[level].append(item)
    
    # 各レベルで親子関係を構築
    for level in sorted(by_level.keys()):
        if level == 0:
            continue  # ルートレベルはスキップ
            
        for item in by_level[level]:
            parent_level = level - 1
            if parent_level in by_level:
                # 階層パスから親を特定（簡単なマッチング）
                for potential_parent in by_level[parent_level]:
                    # 階層パスのプレフィックスマッチングまたは位置関係で判定
                    if _is_parent_child_relationship(potential_parent, item):
                        parent_node = node_map[potential_parent['id']]
                        child_node = node_map[item['id']]
                        parent_node.children.append(child_node)
                        break

def _is_parent_child_relationship(parent_item: Dict, child_item: Dict) -> bool:
    """階層パスから親子関係を判定"""
    parent_path = parent_item['hierarchy_path']
    child_path = child_item['hierarchy_path']
    
    # 簡単な判定：子の階層パスが親の階層パスを含むかチェック
    # より正確な実装が必要な場合は、データベースのparent_id関係を使用
    return True  # 暫定的に最初の親候補を選択