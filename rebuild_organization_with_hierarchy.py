#!/usr/bin/env python3
"""
階層パス対応の組織ポジション再構築スクリプト
CSVの「組織階層」フィールドを正しく解析して親子関係を構築
"""
import csv
import sqlite3
import sys
from datetime import datetime

def find_parent_by_hierarchy_path(current_hierarchy, current_level, positions_list, hierarchy_to_id):
    """CSVの順序を考慮して正確な親を特定する"""
    if current_level <= 0:
        return None
    
    # 現在のポジションのインデックスを見つける
    current_index = -1
    for i, pos in enumerate(positions_list):
        if pos['hierarchy_path'] == current_hierarchy:
            current_index = i
            break
    
    if current_index == -1:
        return None
    
    # 現在のポジションより前で、1レベル上の最も近い親を見つける
    for i in range(current_index - 1, -1, -1):
        candidate = positions_list[i]
        if candidate['level'] == current_level - 1:
            return hierarchy_to_id.get(candidate['hierarchy_path'])
    
    return None

def rebuild_organization_with_hierarchy():
    """組織ポジションを階層パス対応で再構築"""
    
    # データベース接続
    db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
    csv_path = "/Users/lennon/projects/iroas-boss-v2/archive/csv/original_2025年8月組織図（バイナリ）.csv"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 階層パス対応組織ポジション再構築を開始...")
    
    # 1. 既存のorganization_positions, organization_sales を削除
    print("📋 既存の組織データを削除中...")
    cursor.execute("DELETE FROM organization_sales")
    cursor.execute("DELETE FROM organization_positions")
    print(f"✅ 削除完了")
    
    # 2. CSVファイルを読み込んで階層構造を解析
    print("📂 組織CSVファイルを読み込み中...")
    positions_to_insert = []
    hierarchy_mapping = {}  # hierarchy_path -> position_data のマッピング
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # 基本データ取得
                level = int(row.get('階層', '0')) if row.get('階層', '').isdigit() else 0
                hierarchy_path = row.get(' 組織階層', '').strip()
                member_number_raw = row.get(' 会員番号', '').strip()
                name = row.get(' 会員氏名', '').strip()
                
                if not member_number_raw:
                    continue
                
                # 会員番号を11桁に整形
                try:
                    member_number = str(int(member_number_raw)).zfill(11)
                except (ValueError, TypeError):
                    member_number = str(member_number_raw).zfill(11)
                
                # 退会フラグ確認
                withdrawn_flag = row.get(' 退', '').strip()
                is_withdrawn = "(退)" in str(withdrawn_flag)
                
                # 直接フラグ確認
                direct_flag = row.get(' 直', '').strip()
                is_direct = "(直)" in str(direct_flag)
                
                # 人数と売上データ
                def safe_int(value):
                    if not value or str(value).strip() == '':
                        return 0
                    try:
                        return int(str(value).replace(',', ''))
                    except (ValueError, AttributeError):
                        return 0
                
                def safe_float(value):
                    if not value or str(value).strip() == '':
                        return 0.0
                    try:
                        return float(str(value).replace(',', ''))
                    except (ValueError, AttributeError):
                        return 0.0
                
                left_count = safe_int(row.get(' 左人数（A）', ''))
                right_count = safe_int(row.get(' 右人数（A）', ''))
                left_sales = safe_float(row.get(' 左実績', ''))
                right_sales = safe_float(row.get(' 右実績', ''))
                new_purchase = safe_float(row.get(' 新規購入', ''))
                repeat_purchase = safe_float(row.get(' リピート購入', ''))
                additional_purchase = safe_float(row.get(' 追加購入', ''))
                
                # 会員IDまたは退会者IDを特定
                member_id = None
                withdrawn_id = None
                
                if is_withdrawn:
                    # 退会者の場合、withdrawalsテーブルで検索または作成
                    cursor.execute("SELECT id FROM withdrawals WHERE original_member_number = ?", (member_number,))
                    withdrawal_record = cursor.fetchone()
                    
                    if withdrawal_record:
                        withdrawn_id = withdrawal_record[0]
                    else:
                        # 新しい退会レコードを作成
                        cursor.execute("""
                        INSERT INTO withdrawals (withdrawal_number, original_member_number, original_name, withdrawal_date, created_at) 
                        VALUES (?, ?, ?, ?, ?)
                        """, (
                            f"WD{member_number}",
                            member_number,
                            name,
                            '2024-01-01',  # 仮の退会日
                            datetime.now()
                        ))
                        withdrawn_id = cursor.lastrowid
                else:
                    # アクティブ会員の場合、membersテーブルで検索
                    cursor.execute("SELECT id FROM members WHERE member_number = ?", (member_number,))
                    member_record = cursor.fetchone()
                    
                    if member_record:
                        member_id = member_record[0]
                    else:
                        print(f"⚠️  会員が見つかりません: {member_number} - {name}")
                        continue
                
                # ポジションタイプの決定
                # 直紹介を最優先で判定
                if is_direct:
                    position_type = "DIRECT"
                elif "LEFT" in hierarchy_path:
                    position_type = "LEFT"
                elif "RIGHT" in hierarchy_path:
                    position_type = "RIGHT"
                else:
                    position_type = "LEFT"  # デフォルト
                
                # 組織ポジションデータ準備
                position_data = {
                    'member_id': member_id,
                    'withdrawn_id': withdrawn_id,
                    'parent_id': None,  # 後で設定
                    'position_type': position_type,
                    'level': level,
                    'hierarchy_path': hierarchy_path,
                    'left_count': left_count,
                    'right_count': right_count,
                    'left_sales': left_sales,
                    'right_sales': right_sales,
                    'member_number': member_number,
                    'name': name,
                    'is_withdrawn': is_withdrawn
                }
                
                positions_to_insert.append(position_data)
                hierarchy_mapping[hierarchy_path] = position_data
                
                # 進捗表示
                if row_num % 100 == 0:
                    print(f"📊 処理進捗: {row_num}行目")
                    
            except Exception as e:
                print(f"❌ 行{row_num}でエラー: {e}")
                continue
    
    print(f"📋 {len(positions_to_insert)}件のポジションデータを準備完了")
    
    # 3. 階層パスから親子関係を解析
    print("🔗 親子関係を解析中...")
    hierarchy_to_id = {}  # hierarchy_path -> database_id のマッピング
    
    # まず全てのポジションを挿入してIDを取得
    for position in positions_to_insert:
        cursor.execute("""
            INSERT INTO organization_positions (
                member_id, withdrawn_id, parent_id, position_type, level, 
                hierarchy_path, left_count, right_count, left_sales, right_sales,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            position['member_id'],
            position['withdrawn_id'],
            None,  # parent_id は後で更新
            position['position_type'],
            position['level'],
            position['hierarchy_path'],
            position['left_count'],
            position['right_count'],
            position['left_sales'],
            position['right_sales'],
            datetime.now(),
            datetime.now()
        ))
        
        hierarchy_to_id[position['hierarchy_path']] = cursor.lastrowid
    
    # 4. 親子関係を設定
    print("👨‍👩‍👧‍👦 親子関係を設定中...")
    parent_updates = 0
    
    for position in positions_to_insert:
        current_hierarchy = position['hierarchy_path']
        current_level = position['level']
        current_id = hierarchy_to_id[current_hierarchy]
        
        if current_level > 0:  # ルート以外
            # 親を見つける：1レベル上で最も近い階層
            parent_id = None
            
            # 階層パスから正確な親を特定
            parent_id = find_parent_by_hierarchy_path(current_hierarchy, current_level, positions_to_insert, hierarchy_to_id)
            
            # 親子関係を更新
            if parent_id:
                cursor.execute("UPDATE organization_positions SET parent_id = ? WHERE id = ?", 
                             (parent_id, current_id))
                parent_updates += 1
    
    print(f"✅ {parent_updates}件の親子関係を設定完了")
    
    # 5. コミットして結果確認
    conn.commit()
    
    # 結果確認
    cursor.execute("SELECT COUNT(*) FROM organization_positions WHERE member_id IS NOT NULL")
    active_positions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM organization_positions WHERE withdrawn_id IS NOT NULL")
    withdrawn_positions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM organization_positions")
    total_positions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM organization_positions WHERE parent_id IS NOT NULL")
    with_parents = cursor.fetchone()[0]
    
    print(f"✅ 階層パス対応組織ポジション再構築完了!")
    print(f"   📊 総ポジション数: {total_positions}")
    print(f"   👥 アクティブ会員ポジション: {active_positions}")
    print(f"   💼 退会者ポジション: {withdrawn_positions}")
    print(f"   🔗 親子関係設定済み: {with_parents}")
    
    # 上村勇斗の配下確認
    cursor.execute("""
        SELECT COUNT(*) FROM organization_positions child
        JOIN organization_positions parent ON child.parent_id = parent.id
        LEFT JOIN withdrawals w ON parent.withdrawn_id = w.id
        WHERE w.original_member_number = '00000070000'
    """)
    uemura_children = cursor.fetchone()[0]
    print(f"   👨‍👩‍👧‍👦 上村勇斗の直接配下: {uemura_children}人")
    
    conn.close()
    return True

if __name__ == "__main__":
    try:
        success = rebuild_organization_with_hierarchy()
        if success:
            print("🎉 階層パス対応組織ポジション再構築が成功しました!")
            sys.exit(0)
        else:
            print("❌ 階層パス対応組織ポジション再構築が失敗しました!")
            sys.exit(1)
    except Exception as e:
        print(f"💥 予期しないエラー: {e}")
        sys.exit(1)