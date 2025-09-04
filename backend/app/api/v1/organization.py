"""
組織図API エンドポイント

P-003: 組織図ビューア
MLM組織構造の視覚的表示と階層確認
"""

import csv
import os
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database import get_db
from app.schemas.organization import OrganizationNode, OrganizationTree, OrganizationStats

router = APIRouter()

# CSVファイルのパス（絶対パス指定で安全性向上）
CSV_BINARY_PATH = "/Users/lennon/projects/iroas-boss-v2/csv/2025年8月組織図（バイナリ）.csv"
CSV_REFERRAL_PATH = "/Users/lennon/projects/iroas-boss-v2/csv/2025年8月組織図（紹介系列）.csv"

# CSVファイルパス設定完了


def parse_hierarchy_path(hierarchy_path: str) -> tuple:
    """階層パスを解析してレベルと位置を取得"""
    if not hierarchy_path or hierarchy_path.strip() == "0 なし":
        return 0, "ROOT"
    
    # "┣ 1 LEFT" -> (1, "LEFT")
    # "┃┣ 2 LEFT" -> (2, "LEFT") 
    # "┃┃┃┣ 4 LEFT" -> (4, "LEFT")
    parts = hierarchy_path.strip().split()
    if len(parts) >= 3:
        try:
            level = int(parts[1])
            position = parts[2]
            return level, position
        except (ValueError, IndexError):
            pass
    
    # 数値のみの場合（階層フィールドから）
    try:
        level = int(hierarchy_path.strip())
        return level, "UNKNOWN"
    except ValueError:
        pass
    
    return 0, "UNKNOWN"


def parse_status_flags(direct_flag: str, withdrawn_flag: str) -> tuple:
    """ステータスフラグを解析"""
    # 空文字列や None の場合は False として扱う
    direct_str = str(direct_flag).strip() if direct_flag else ""
    withdrawn_str = str(withdrawn_flag).strip() if withdrawn_flag else ""
    
    is_direct = "(直)" in direct_str
    is_withdrawn = "(退)" in withdrawn_str
    
    # 確実にブール値を返す
    return bool(is_direct), bool(is_withdrawn)


def read_organization_csv() -> List[Dict]:
    """組織CSV読み込み"""
    organization_data = []
    
    try:
        with open(CSV_BINARY_PATH, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # 必要なデータを抽出・変換
                # 階層フィールドから直接レベルを取得
                hierarchy_level = int(row.get('階層', '0')) if row.get('階層', '').isdigit() else 0
                # 組織階層から位置を取得
                hierarchy_path = row.get('組織階層', '') or ''
                _, position = parse_hierarchy_path(hierarchy_path)
                
                direct_val = row.get('直', '') or ''
                withdrawn_val = row.get('退', '') or ''
                is_direct, is_withdrawn = parse_status_flags(direct_val, withdrawn_val)
                
                
                # 数値データの変換（空文字・無効値をゼロに）
                def safe_int(value: str) -> int:
                    if not value or value.strip() == '':
                        return 0
                    try:
                        return int(value.replace(',', ''))
                    except (ValueError, AttributeError):
                        return 0
                
                # 退会者の場合は表示名を調整（実際の会員番号を保持）
                member_number_raw = row.get(' 会員番号', '') or row.get('会員番号', '')
                member_number_raw = member_number_raw.strip() if member_number_raw else ''
                original_name = row.get(' 会員氏名', '') or row.get('会員氏名', '')
                
                # 会員番号を11桁に整形
                if member_number_raw:
                    try:
                        member_number = str(int(member_number_raw)).zfill(11)
                    except (ValueError, TypeError):
                        member_number = str(member_number_raw).zfill(11)
                else:
                    member_number = '00000000000'
                
                if is_withdrawn:
                    # 退会者の場合：実際の会員番号は保持し、名前のみ表示調整
                    display_name = f"（退会者）{original_name}" if original_name else "（退会者）"
                    member_status = "WITHDRAWN"
                else:
                    display_name = original_name
                    member_status = "ACTIVE"
                
                org_node = {
                    'id': f"{hierarchy_level}-{member_number}",
                    'member_number': member_number,
                    'name': display_name,
                    'original_name': original_name,  # 元の名前を保持（管理用）
                    'title': row.get('資格名', '') or '',
                    'level': hierarchy_level,
                    'hierarchy_path': hierarchy_path,
                    'registration_date': row.get('登録日', '') or '',
                    'is_direct': is_direct,  # 既にbool型に変換済み
                    'is_withdrawn': is_withdrawn,  # 既にbool型に変換済み
                    'left_count': safe_int(row.get('左人数（A）', '')),
                    'right_count': safe_int(row.get('右人数（A）', '')),
                    'left_sales': safe_int(row.get('左実績', '')),
                    'right_sales': safe_int(row.get('右実績', '')),
                    'new_purchase': safe_int(row.get('新規購入', '')),
                    'repeat_purchase': safe_int(row.get('リピート購入', '')),
                    'additional_purchase': safe_int(row.get('追加購入', '')),
                    'position': position,
                    'raw_hierarchy': hierarchy_level,
                    'member_status': member_status  # 表示用ステータス
                }
                organization_data.append(org_node)
                
    except FileNotFoundError:
        pass  # ファイルが見つからない場合は空のリストを返す
    except Exception as e:
        pass  # エラー時は空のリストを返す
    
    return organization_data


def build_organization_tree(org_data: List[Dict]) -> List[OrganizationNode]:
    """組織データからツリー構造を構築"""
    if not org_data:
        return []
    
    # レベル0（ルート）から開始
    root_nodes = []
    node_map = {}
    
    # 全ノードをマップに格納
    for item in org_data:
        try:
            # デバッグ: Pydantic変換前の値チェック
            if item['member_number'] == '00000000000':
                print(f"[DEBUG] Pydantic変換前データ:")
                print(f"  current_title: {item.get('current_title')} (type: {type(item.get('current_title'))})")
                print(f"  historical_title: {item.get('historical_title')} (type: {type(item.get('historical_title'))})")
                print(f"  display_title: {item.get('display_title')} (type: {type(item.get('display_title'))})")
            
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
                status="WITHDRAWN" if item['is_withdrawn'] else "ACTIVE",
                # 称号統合フィールド
                current_title=item.get('current_title', ''),
                historical_title=item.get('historical_title', ''),
                display_title=item.get('display_title', '')
            )
            node_map[item['id']] = node
            
            # レベル0をルートとして設定
            if item['level'] == 0:
                root_nodes.append(node)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ノード作成エラー: {str(e)}")
    
    # 階層関係を構築（簡易版：レベル順に子として追加）
    for item in org_data:
        current_level = item['level']
        current_node = node_map[item['id']]
        
        # 自分より1レベル深い子ノードを検索
        for child_item in org_data:
            if (child_item['level'] == current_level + 1 and 
                child_item['hierarchy_path'].startswith(item['hierarchy_path']) and
                child_item['id'] != item['id']):
                child_node = node_map[child_item['id']]
                current_node.children.append(child_node)
    
    return root_nodes


@router.get("/tree", response_model=OrganizationTree)
def get_organization_tree_endpoint(
    member_id: Optional[str] = Query(None, description="特定メンバーをルートとしたサブツリー取得（会員番号）"),
    max_level: Optional[int] = Query(3, description="最大表示レベル（デフォルト3階層）"),
    active_only: Optional[bool] = Query(False, description="アクティブメンバーのみ表示")
):
    """組織ツリー取得（段階的表示）"""
    return get_organization_tree(member_id, max_level, active_only)

def get_organization_tree(
    member_id: Optional[str] = None,
    max_level: Optional[int] = 3,
    active_only: Optional[bool] = False
):
    """組織ツリー取得（段階的表示）"""
    try:
        # 初期表示は軽量化：最大表示制限を緩和
        if max_level is None:
            max_level = 5  # デフォルト5階層で表示
        elif max_level > 100:  # 非常に高い値の場合のみ制限
            max_level = 100
        
        # 制限付きでCSVデータを読み込み
        limited_org_data = []
        focus_member_level = None
        
        # まず特定メンバーのレベルを取得（フォーカス時）
        if member_id:
            normalized_member_id = member_id.zfill(11)
            with open(CSV_BINARY_PATH, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    member_number_raw = row.get(' 会員番号', '') or row.get('会員番号', '')
                    if member_number_raw:
                        try:
                            csv_member_number = str(int(member_number_raw)).zfill(11)
                            if csv_member_number == normalized_member_id:
                                level_str = row.get('階層', '0') or '0'
                                focus_member_level = int(level_str) if level_str.isdigit() else 0
                                break
                        except (ValueError, TypeError):
                            continue
        
        # 称号統合のためのキャッシュ読み込み
        from app.services.member_integration import member_integration_service
        member_integration_service.load_member_details()
        
        # デバッグ: active_onlyフラグ確認
        print(f"[DEBUG] active_only = {active_only}")
        
        # デバッグ: キャッシュ内容確認
        print(f"[DEBUG] キャッシュ内会員番号: {list(member_integration_service.member_details_cache.keys())[:5]}")
        if '00000000000' in member_integration_service.member_details_cache:
            print(f"[DEBUG] 白石達也データ: {member_integration_service.member_details_cache['00000000000']}")
        if '00000000400' in member_integration_service.member_details_cache:
            print(f"[DEBUG] 澤原洋①データ: {member_integration_service.member_details_cache['00000000400']}")
        
        with open(CSV_BINARY_PATH, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            count = 0
            
            for row in csv_reader:
                # 階層制限の計算
                level_str = row.get('階層', '0') or '0'
                level = int(level_str) if level_str.isdigit() else 0
                
                # フォーカス時は相対レベルで制限
                if focus_member_level is not None:
                    relative_level = level - focus_member_level
                    if relative_level > max_level:
                        continue
                else:
                    # 通常表示時は絶対レベルで制限
                    if level > max_level:
                        continue
                
                # 軽量データ構築（フィールド名スペース除去）
                # CSVヘッダーに空白があるため、トリム処理が必要
                member_number_raw = row.get(' 会員番号', '') or row.get('会員番号', '')
                member_number_raw = member_number_raw.strip() if member_number_raw else ''
                
                # 会員番号を11桁に整形（先頭ゼロ埋め）
                if member_number_raw:
                    try:
                        member_number = str(int(member_number_raw)).zfill(11)
                    except (ValueError, TypeError):
                        member_number = str(member_number_raw).zfill(11)
                else:
                    member_number = '00000000000'  # デフォルト11桁ゼロ
                
                original_name = row.get(' 会員氏名', '') or row.get('会員氏名', '')
                original_name = original_name.strip() if original_name else ''
                
                withdrawn_flag = row.get(' 退', '') or row.get('退', '')
                withdrawn_flag = withdrawn_flag.strip() if withdrawn_flag else ''
                is_withdrawn = "(退)" in str(withdrawn_flag)
                
                # アクティブメンバーのみ表示フィルター
                if active_only and is_withdrawn:
                    print(f"[DEBUG] FILTERED OUT (退会者): {member_number} - {original_name}")
                    # 退会者はスキップしますが、後で階層再構築時にその子メンバーは親を繋ぎ直します
                    continue
                
                display_name = f"（退会者）{original_name}" if is_withdrawn and original_name else original_name
                
                # 📋 称号の統合処理（シンプル統合）
                historical_title = (row.get(' 資格名', '') or row.get('資格名', '')).strip()  # 組織図CSV由来
                current_title = historical_title  # デフォルトは組織図の称号
                
                # デバッグ: 処理中の会員番号
                if count < 5:  # 最初の5件のみデバッグ
                    print(f"[DEBUG] 処理中会員: {member_number}, 元のタイトル: '{historical_title}'")
                
                # 会員管理データから現在称号を取得
                if member_number in member_integration_service.member_details_cache:
                    member_details = member_integration_service.member_details_cache[member_number]
                    # デバッグ出力
                    if member_number in ['00000000000', '00000000400', '00000069700']:
                        print(f"[DEBUG] {member_number} 詳細: {member_details}")
                    
                    # 会員管理CSVの「称号」フィールドから取得
                    current_title_from_csv = None
                    for field in ['title', '称号', '資格名']:
                        if field in member_details and member_details[field]:
                            current_title_from_csv = member_details[field].strip()
                            if member_number in ['00000000000', '00000000400', '00000069700']:
                                print(f"[DEBUG] フィールド {field}: {current_title_from_csv}")
                            break
                    
                    if current_title_from_csv:
                        current_title = current_title_from_csv
                    else:
                        current_title = '称号なし'
                else:
                    # キャッシュにない場合のデバッグ
                    if member_number == '00000069700':
                        print(f"[DEBUG] {member_number} はキャッシュに見つかりません")
                
                # シンプル統合ロジック: アクティブは現在称号、退会者は過去最高称号
                display_title = current_title if not is_withdrawn else historical_title
                
                # デバッグ: 称号統合結果
                print(f"[DEBUG] {member_number} 称号統合結果:")
                print(f"  historical_title: '{historical_title}'")
                print(f"  current_title: '{current_title}'")
                print(f"  display_title: '{display_title}'")
                print(f"  is_withdrawn: {is_withdrawn}")
                
                org_node = {
                    'id': f"{level}-{member_number}",
                    'member_number': member_number,
                    'name': display_name,
                    'title': display_title,
                    'historical_title': historical_title,  # 報酬計算用
                    'current_title': current_title,        # 統合情報
                    'display_title': display_title,        # 表示用統合称号
                    'level': level,
                    'hierarchy_path': (row.get(' 組織階層', '') or row.get('組織階層', '')).strip(),
                    'registration_date': (row.get(' 登録日', '') or row.get('登録日', '')).strip(),
                    'is_direct': "(直)" in str(row.get(' 直', '') or row.get('直', '') or ''),
                    'is_withdrawn': is_withdrawn,
                    'left_count': 0,  # 軽量化のため省略
                    'right_count': 0,  # 軽量化のため省略
                    'left_sales': 0,   # 軽量化のため省略
                    'right_sales': 0,  # 軽量化のため省略
                    'new_purchase': 0,
                    'repeat_purchase': 0,
                    'additional_purchase': 0,
                    'position': "UNKNOWN",
                    'raw_hierarchy': level,
                    'member_status': "WITHDRAWN" if is_withdrawn else "ACTIVE"
                }
                
                # デバッグ: org_node作成直後の確認
                if member_number == '00000000000':
                    print(f"[DEBUG] org_node作成直後:")
                    print(f"  current_title: '{org_node['current_title']}'")
                    print(f"  historical_title: '{org_node['historical_title']}'")
                    print(f"  display_title: '{org_node['display_title']}'")
                
                limited_org_data.append(org_node)
                
                count += 1
                if count > 2000:  # 最大2000行まで（拡張表示）
                    break
        
        # 軽量ツリー構造構築（簡易版：レベル順階層）
        root_nodes = []
        node_map = {}
        
        # 全ノードをマップに格納
        for item in limited_org_data:
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
                status=item['member_status']
            )
            node_map[item['id']] = node
            
            # レベル0をルートとして設定
            if item['level'] == 0:
                root_nodes.append(node)
        
        # バイナリツリー階層パターンに基づく親子関係構築（アクティブフィルター対応版）
        def find_parent_by_position(current_index, current_level, all_data, filtered_data_map):
            """CSVの位置と階層レベルに基づいて親を特定する（アクティブフィルター時は退会者をスキップ）"""
            import re
            
            if current_level <= 1:
                # レベル0またはレベル1はルートまたは直下
                if current_level == 1:
                    # レベル1の親は必ずレベル0（ルート）
                    for i in range(current_index - 1, -1, -1):
                        if all_data[i]['level'] == 0:
                            # フィルター済みデータに存在するかチェック
                            if all_data[i]['hierarchy_path'] in filtered_data_map:
                                return all_data[i]['hierarchy_path']
                return None
            
            # レベル2以上の場合、アクティブな親を探す（退会者をスキップ）
            # 現在位置から上に向かって、フィルター済みデータに存在する最も近い上位レベルを検索
            for target_level in range(current_level - 1, -1, -1):
                for i in range(current_index - 1, -1, -1):
                    item = all_data[i]
                    if (item['level'] == target_level and 
                        item['hierarchy_path'] in filtered_data_map):
                        return item['hierarchy_path']
            
            return None
        
        # 階層パターンマッピングを作成
        hierarchy_to_member = {}
        for item in limited_org_data:
            hierarchy_to_member[item['hierarchy_path']] = item
        
        # アクティブフィルター時は簡易的な親子関係構築
        if active_only:
            # レベルごとにメンバーをグループ化
            members_by_level = {}
            for item in limited_org_data:
                level = item['level']
                if level not in members_by_level:
                    members_by_level[level] = []
                members_by_level[level].append(item)
            
            # 各メンバーについて、より上位のレベルから最も近い親を見つける
            for item in limited_org_data:
                current_node = node_map[item['id']]
                current_level = item['level']
                
                if current_level > 0:
                    # 上位レベルから最も近い親を探す
                    parent_found = False
                    for parent_level in range(current_level - 1, -1, -1):
                        if parent_level in members_by_level:
                            # アクティブフィルター時はシンプルに：最も近い上位レベルのメンバーを親とする
                            # （退会者がスキップされているため、厳密な階層パスマッチングは不要）
                            if members_by_level[parent_level]:
                                # デバッグ: 親子関係の確認
                                potential_parent = members_by_level[parent_level][0]  # 簡易的に最初のメンバーを親とする
                                parent_node = node_map[potential_parent['id']]
                                parent_node.children.append(current_node)
                                print(f"[DEBUG] 親子関係構築: {potential_parent['name']} (Level {parent_level}) <- {item['name']} (Level {current_level})")
                                parent_found = True
                                break
                    
                    # 親が見つからない場合、レベル0のルートに直接接続
                    if not parent_found and 0 in members_by_level:
                        root_node = node_map[members_by_level[0][0]['id']]
                        root_node.children.append(current_node)
                        print(f"[DEBUG] ルート直接接続: {members_by_level[0][0]['name']} (Level 0) <- {item['name']} (Level {current_level})")
        else:
            # 通常表示時の親子関係構築（元のロジック）
            for i, item in enumerate(limited_org_data):
                current_node = node_map[item['id']]
                current_level = item['level']
                
                if current_level > 0:
                    # CSVの位置に基づいて親を特定
                    parent_hierarchy = find_parent_by_position(i, current_level, limited_org_data, set(hierarchy_to_member.keys()))
                    
                    if parent_hierarchy and parent_hierarchy in hierarchy_to_member:
                        parent_item = hierarchy_to_member[parent_hierarchy]
                        if parent_item['id'] in node_map:
                            parent_node = node_map[parent_item['id']]
                            parent_node.children.append(current_node)
        
        # 特定メンバーにフォーカスする場合
        if member_id:
            # 11桁形式に正規化
            normalized_member_id = member_id.zfill(11)
            
            # 指定されたメンバーをルートとしたサブツリーを抽出
            focus_root = None
            for item in limited_org_data:
                if item['member_number'] == normalized_member_id:
                    focus_root = node_map[item['id']]
                    break
            
            if focus_root:
                root_nodes = [focus_root]
        
        # 軽量統計計算
        total_members = len(limited_org_data)
        max_level_found = max([item['level'] for item in limited_org_data]) if limited_org_data else 0
        active_members = len([item for item in limited_org_data if not item['is_withdrawn']])
        withdrawn_members = total_members - active_members
        
        return OrganizationTree(
            root_nodes=root_nodes,
            total_members=total_members,
            max_level=max_level_found,
            total_sales=0,  # 軽量化のため省略
            active_members=active_members,
            withdrawn_members=withdrawn_members
        )
        
    except Exception as e:
        # エラー詳細をログ出力（デバッグ用）
        import traceback
        print(f"組織ツリーエラー詳細: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"組織ツリー取得エラー: {str(e)}")


def read_organization_stats_only() -> dict:
    """統計情報のみを軽量に読み込み"""
    stats = {
        'total_members': 0,
        'active_members': 0,  
        'withdrawn_members': 0,
        'max_level': 0,
        'total_levels': 0,
        'total_left_sales': 0,
        'total_right_sales': 0
    }
    
    try:
        with open(CSV_BINARY_PATH, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # 統計情報のみ計算（重いデータ構造は作らない）
                stats['total_members'] += 1
                
                # 退会フラグ確認
                withdrawn_flag = row.get('退', '') or ''
                is_withdrawn = "(退)" in str(withdrawn_flag)
                if not is_withdrawn:
                    stats['active_members'] += 1
                else:
                    stats['withdrawn_members'] += 1
                
                # レベル情報
                level = int(row.get('階層', '0')) if row.get('階層', '').isdigit() else 0
                stats['max_level'] = max(stats['max_level'], level)
                stats['total_levels'] += level
                
                # 売上情報
                def safe_int(value: str) -> int:
                    if not value or str(value).strip() == '':
                        return 0
                    try:
                        return int(str(value).replace(',', ''))
                    except (ValueError, AttributeError):
                        return 0
                
                stats['total_left_sales'] += safe_int(row.get('左実績', ''))
                stats['total_right_sales'] += safe_int(row.get('右実績', ''))
                
    except Exception:
        pass
    
    return stats

@router.get("/test")
def test_organization_csv():
    """CSVファイル読み込みテスト（完全デバッグ）"""
    try:
        with open(CSV_BINARY_PATH, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            # ヘッダー情報確認
            headers = csv_reader.fieldnames
            
            # 最初の2行の完全データ確認
            sample_data = []
            for i, row in enumerate(csv_reader):
                if i < 2:
                    # 全フィールドをチェック
                    field_analysis = {}
                    for key in headers:
                        field_analysis[f"'{key}'"] = f"'{row.get(key, '[MISSING]')}'"
                    
                    sample_data.append({
                        "row_number": i + 1,
                        "field_analysis": field_analysis
                    })
                else:
                    break
        
        return {
            "status": "success", 
            "csv_path": CSV_BINARY_PATH,
            "headers": [f"'{h}'" for h in headers] if headers else None,
            "header_count": len(headers) if headers else 0,
            "sample_data": sample_data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "csv_path": CSV_BINARY_PATH
        }

@router.get("/stats", response_model=OrganizationStats)
def get_organization_stats(db: Session = Depends(get_db)):
    """組織統計取得（軽量版・高速処理）"""
    try:
        # 高速で統計のみ計算
        stats = {
            'total_members': 0,
            'active_members': 0,  
            'withdrawn_members': 0,
            'max_level': 0,
            'total_levels': 0,
            'total_left_sales': 0,
            'total_right_sales': 0
        }
        
        # バッチ処理で高速読み込み
        with open(CSV_BINARY_PATH, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            batch_count = 0
            
            for row in csv_reader:
                # 統計情報のみ高速計算
                stats['total_members'] += 1
                
                # 退会フラグ確認（高速）
                withdrawn_flag = row.get(' 退', '') or row.get('退', '') or ''
                is_withdrawn = "(退)" in str(withdrawn_flag)
                if not is_withdrawn:
                    stats['active_members'] += 1
                else:
                    stats['withdrawn_members'] += 1
                
                # レベル情報（高速）
                level = int(row.get('階層', '0')) if row.get('階層', '').isdigit() else 0
                stats['max_level'] = max(stats['max_level'], level)
                stats['total_levels'] += level
                
                # 1000行ごとにプロセスを一時停止（タイムアウト防止）
                batch_count += 1
                if batch_count % 1000 == 0:
                    pass  # バッチ処理完了
        
        total_members = stats['total_members']
        average_level = stats['total_levels'] / total_members if total_members > 0 else 0
        total_sales = 0  # 高速化のため売上計算は省略
        
        return OrganizationStats(
            total_members=total_members,
            active_members=stats['active_members'],
            withdrawn_members=stats['withdrawn_members'],
            max_level=stats['max_level'],
            average_level=round(average_level, 2),
            total_left_sales=0,  # 高速化のため省略
            total_right_sales=0,  # 高速化のため省略
            total_sales=total_sales
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"組織統計取得エラー: {str(e)}")


@router.get("/member/{member_number}/downline")
def get_member_downline(
    member_number: str,
    max_depth: Optional[int] = Query(10, description="最大深度"),
    db: Session = Depends(get_db)
):
    """特定メンバーのダウンライン取得"""
    try:
        org_data = read_organization_csv()
        
        # 指定メンバーを検索
        target_member = None
        for item in org_data:
            if item['member_number'] == member_number:
                target_member = item
                break
        
        if not target_member:
            raise HTTPException(status_code=404, detail=f"会員番号 {member_number} が見つかりません")
        
        # ダウンラインを検索
        target_level = target_member['level']
        downline_data = []
        
        for item in org_data:
            if (item['level'] > target_level and 
                item['level'] <= target_level + max_depth and
                item['hierarchy_path'].startswith(target_member['hierarchy_path'])):
                downline_data.append(item)
        
        # ツリー構造構築
        downline_tree = build_organization_tree([target_member] + downline_data)
        
        return {
            "target_member": target_member,
            "downline_tree": downline_tree,
            "downline_count": len(downline_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ダウンライン取得エラー: {str(e)}")


@router.get("/export/csv")
def export_organization_csv(
    format_type: str = Query("binary", description="出力形式: binary または referral"),
    db: Session = Depends(get_db)
):
    """組織図CSV出力"""
    try:
        if format_type == "binary":
            file_path = CSV_BINARY_PATH
        elif format_type == "referral":
            file_path = CSV_REFERRAL_PATH
        else:
            raise HTTPException(status_code=400, detail="無効な形式です。binary または referral を指定してください。")
        
        # CSVファイル内容を返す
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return {
            "filename": os.path.basename(file_path),
            "content": content,
            "format": format_type
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSVファイルが見つかりません")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV出力エラー: {str(e)}")


@router.get("/member/{member_number}", summary="組織メンバー詳細取得")
def get_organization_member_detail(
    member_number: str,
    db: Session = Depends(get_db)
):
    """組織データから特定メンバーの詳細を取得"""
    try:
        # 11桁形式に正規化
        normalized_member_number = member_number.zfill(11)
        
        with open(CSV_BINARY_PATH, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # 会員番号の取得と正規化
                member_number_raw = row.get(' 会員番号', '') or row.get('会員番号', '')
                member_number_raw = member_number_raw.strip() if member_number_raw else ''
                
                if member_number_raw:
                    try:
                        csv_member_number = str(int(member_number_raw)).zfill(11)
                    except (ValueError, TypeError):
                        csv_member_number = str(member_number_raw).zfill(11)
                else:
                    csv_member_number = '00000000000'  # デフォルト11桁ゼロ
                
                # 会員番号が一致する場合、詳細データを構築
                if csv_member_number == normalized_member_number:
                    original_name = row.get(' 会員氏名', '') or row.get('会員氏名', '')
                    original_name = original_name.strip() if original_name else ''
                    
                    withdrawn_flag = row.get(' 退', '') or row.get('退', '')
                    withdrawn_flag = withdrawn_flag.strip() if withdrawn_flag else ''
                    is_withdrawn = "(退)" in str(withdrawn_flag)
                    
                    display_name = f"（退会者）{original_name}" if is_withdrawn and original_name else original_name
                    
                    level_str = row.get('階層', '0') or '0'
                    level = int(level_str) if level_str.isdigit() else 0
                    
                    member_detail = {
                        "member_number": csv_member_number,
                        "name": display_name,
                        "title": (row.get(' 資格名', '') or row.get('資格名', '')).strip(),
                        "status": "WITHDRAWN" if is_withdrawn else "ACTIVE",
                        "level": level,
                        "hierarchy_path": (row.get(' 組織階層', '') or row.get('組織階層', '')).strip(),
                        "registration_date": (row.get(' 登録日', '') or row.get('登録日', '')).strip(),
                        "is_direct": "(直)" in str(row.get(' 直', '') or row.get('直', '') or ''),
                        "is_withdrawn": is_withdrawn,
                        "left_count": _safe_int(row.get(' 左人数（A）', '') or row.get('左人数（A）', '')),
                        "right_count": _safe_int(row.get(' 右人数（A）', '') or row.get('右人数（A）', '')),
                        "left_sales": _safe_int(row.get(' 左実績', '') or row.get('左実績', '')),
                        "right_sales": _safe_int(row.get(' 右実績', '') or row.get('右実績', '')),
                        "new_purchase": _safe_int(row.get(' 新規購入', '') or row.get('新規購入', '')),
                        "repeat_purchase": _safe_int(row.get(' リピート購入', '') or row.get('リピート購入', '')),
                        "additional_purchase": _safe_int(row.get(' 追加購入', '') or row.get('追加購入', '')),
                        "total_sales": _safe_int(row.get(' 左実績', '') or row.get('左実績', '')) + _safe_int(row.get(' 右実績', '') or row.get('右実績', ''))
                    }
                    
                    return member_detail
        
        # メンバーが見つからない場合
        raise HTTPException(status_code=404, detail=f"会員番号 {normalized_member_number} が見つかりません")
        
    except FileNotFoundError:
        logger.error(f"組織データCSVファイルが見つかりません: {CSV_BINARY_PATH}")
        raise HTTPException(status_code=404, detail="組織データファイルが見つかりません")
    except Exception as e:
        logger.error(f"会員詳細取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"会員詳細取得エラー: {str(e)}")


def _safe_int(value: str) -> int:
    """安全な整数変換"""
    try:
        if not value or value.strip() == '':
            return 0
        # カンマを除去してから変換
        clean_value = str(value).replace(',', '').strip()
        return int(clean_value) if clean_value.isdigit() else 0
    except (ValueError, TypeError):
        return 0