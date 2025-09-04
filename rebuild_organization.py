#!/usr/bin/env python3
"""
組織ポジション再構築スクリプト
CSVから組織データベースを再構築します
"""
import csv
import sqlite3
import sys
from datetime import datetime

def rebuild_organization_positions():
    """組織ポジションを再構築"""
    
    # データベース接続
    db_path = "/Users/lennon/projects/iroas-boss-v2/backend/iroas_boss_v2.db"
    csv_path = "/Users/lennon/projects/iroas-boss-v2/csv/2025年8月組織図（バイナリ）.csv"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 組織ポジション再構築を開始...")
    
    # 1. 既存のorganization_positions, organization_sales を削除
    print("📋 既存の組織データを削除中...")
    cursor.execute("DELETE FROM organization_sales")
    cursor.execute("DELETE FROM organization_positions")
    print(f"✅ 削除完了")
    
    # 2. CSVファイルを読み込み
    print("📂 組織CSVファイルを読み込み中...")
    positions_to_insert = []
    sales_to_insert = []
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # 会員番号の取得と正規化
                member_number_raw = row.get(' 会員番号', '') or row.get('会員番号', '')
                member_number_raw = member_number_raw.strip() if member_number_raw else ''
                
                if not member_number_raw:
                    continue
                
                # 会員番号を11桁に整形
                try:
                    member_number = str(int(member_number_raw)).zfill(11)
                except (ValueError, TypeError):
                    member_number = str(member_number_raw).zfill(11)
                
                # 基本情報取得
                name = (row.get(' 会員氏名', '') or row.get('会員氏名', '')).strip()
                level = int(row.get('階層', '0')) if row.get('階層', '').isdigit() else 0
                hierarchy_path = (row.get(' 組織階層', '') or row.get('組織階層', '')).strip()
                
                # 退会フラグ確認
                withdrawn_flag = (row.get(' 退', '') or row.get('退', '')).strip()
                is_withdrawn = "(退)" in str(withdrawn_flag)
                
                # 直接フラグ確認
                direct_flag = (row.get(' 直', '') or row.get('直', '')).strip()
                is_direct = "(直)" in str(direct_flag)
                
                # 人数と売上データ
                left_count = int(row.get(' 左人数（A）', '') or row.get('左人数（A）', '') or '0') if str(row.get(' 左人数（A）', '') or row.get('左人数（A）', '') or '0').replace(',', '').isdigit() else 0
                right_count = int(row.get(' 右人数（A）', '') or row.get('右人数（A）', '') or '0') if str(row.get(' 右人数（A）', '') or row.get('右人数（A）', '') or '0').replace(',', '').isdigit() else 0
                left_sales = float(str(row.get(' 左実績', '') or row.get('左実績', '') or '0').replace(',', '')) if str(row.get(' 左実績', '') or row.get('左実績', '') or '0').replace(',', '').replace('.', '', 1).isdigit() else 0.0
                right_sales = float(str(row.get(' 右実績', '') or row.get('右実績', '') or '0').replace(',', '')) if str(row.get(' 右実績', '') or row.get('右実績', '') or '0').replace(',', '').replace('.', '', 1).isdigit() else 0.0
                
                # 購入データ
                new_purchase = float(str(row.get(' 新規購入', '') or row.get('新規購入', '') or '0').replace(',', '')) if str(row.get(' 新規購入', '') or row.get('新規購入', '') or '0').replace(',', '').replace('.', '', 1).isdigit() else 0.0
                repeat_purchase = float(str(row.get(' リピート購入', '') or row.get('リピート購入', '') or '0').replace(',', '')) if str(row.get(' リピート購入', '') or row.get('リピート購入', '') or '0').replace(',', '').replace('.', '', 1).isdigit() else 0.0
                additional_purchase = float(str(row.get(' 追加購入', '') or row.get('追加購入', '') or '0').replace(',', '')) if str(row.get(' 追加購入', '') or row.get('追加購入', '') or '0').replace(',', '').replace('.', '', 1).isdigit() else 0.0
                
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
                        print(f"📝 退会者レコード作成: {member_number} - {name}")
                else:
                    # アクティブ会員の場合、membersテーブルで検索
                    cursor.execute("SELECT id FROM members WHERE member_number = ?", (member_number,))
                    member_record = cursor.fetchone()
                    
                    if member_record:
                        member_id = member_record[0]
                    else:
                        print(f"⚠️  会員が見つかりません: {member_number} - {name}")
                        continue
                
                # 組織ポジションデータ準備
                position_data = (
                    member_id,
                    withdrawn_id,
                    None,  # parent_id は後で階層関係構築時に設定
                    'DIRECT' if is_direct else 'LEFT',  # 簡易的なposition_type
                    level,
                    hierarchy_path,
                    left_count,
                    right_count,
                    left_sales,
                    right_sales,
                    datetime.now(),
                    datetime.now()
                )
                
                positions_to_insert.append(position_data)
                
                # 進捗表示
                if row_num % 100 == 0:
                    print(f"📊 処理進捗: {row_num}行目")
                    
            except Exception as e:
                print(f"❌ 行{row_num}でエラー: {e}")
                print(f"   データ: {dict(row)}")
                continue
    
    # 3. 組織ポジションを一括挿入
    print(f"💾 組織ポジション {len(positions_to_insert)}件を挿入中...")
    cursor.executemany("""
        INSERT INTO organization_positions (
            member_id, withdrawn_id, parent_id, position_type, level, 
            hierarchy_path, left_count, right_count, left_sales, right_sales,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, positions_to_insert)
    
    # 4. コミットして結果確認
    conn.commit()
    
    # 結果確認
    cursor.execute("SELECT COUNT(*) FROM organization_positions WHERE member_id IS NOT NULL")
    active_positions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM organization_positions WHERE withdrawn_id IS NOT NULL")
    withdrawn_positions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM organization_positions")
    total_positions = cursor.fetchone()[0]
    
    print(f"✅ 組織ポジション再構築完了!")
    print(f"   📊 総ポジション数: {total_positions}")
    print(f"   👥 アクティブ会員ポジション: {active_positions}")
    print(f"   💼 退会者ポジション: {withdrawn_positions}")
    
    conn.close()
    return True

if __name__ == "__main__":
    try:
        success = rebuild_organization_positions()
        if success:
            print("🎉 組織ポジション再構築が成功しました!")
            sys.exit(0)
        else:
            print("❌ 組織ポジション再構築が失敗しました!")
            sys.exit(1)
    except Exception as e:
        print(f"💥 予期しないエラー: {e}")
        sys.exit(1)