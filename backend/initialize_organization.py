#!/usr/bin/env python3
"""
初期組織データ投入スクリプト
45名のアクティブメンバーから組織構造を構築
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.member import Member
from app.models.organization import OrganizationPosition, PositionType

def main():
    print("🚀 初期組織データ投入を開始...")
    
    # セッション作成
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 既存の組織データをクリア
        session.query(OrganizationPosition).delete()
        session.commit()
        print("✅ 既存組織データをクリア")
        
        # 全アクティブメンバーを取得
        members = session.query(Member).filter(Member.status == 'ACTIVE').all()
        print(f"📋 アクティブメンバー: {len(members)}名")
        
        # 会員番号でメンバー辞書を作成
        member_dict = {m.member_number: m for m in members}
        
        # 1. ルートノード（白石達也）を作成
        root_member = member_dict.get('00000000000')
        if not root_member:
            print("❌ ルートメンバー（白石達也）が見つかりません")
            return
        
        root_position = OrganizationPosition(
            member_id=root_member.id,
            position_type=PositionType.ROOT,
            level=0,
            hierarchy_path='0'
        )
        session.add(root_position)
        session.commit()
        print(f"✅ ルートノード作成: {root_member.name}")
        
        # ポジション辞書を作成（会員番号 -> OrganizationPosition）
        position_dict = {'00000000000': root_position}
        
        # 2. 他のメンバーを階層構造で配置
        remaining_members = [m for m in members if m.member_number != '00000000000']
        processed_count = 0
        max_iterations = len(remaining_members) * 2  # 無限ループ防止
        iteration = 0
        
        while remaining_members and iteration < max_iterations:
            iteration += 1
            newly_processed = []
            
            for member in remaining_members:
                # 直上者のポジションが存在するかチェック
                upline_number = member.upline_id or '00000000000'  # upline_idがNoneの場合はroot
                
                if upline_number in position_dict:
                    parent_position = position_dict[upline_number]
                    
                    # LEFT/RIGHT の決定
                    # 既存の子ノードをチェック
                    existing_children = session.query(OrganizationPosition).filter(
                        OrganizationPosition.parent_id == parent_position.id
                    ).all()
                    
                    # LEFTが空いているか確認
                    has_left = any(child.position_type == PositionType.LEFT for child in existing_children)
                    has_right = any(child.position_type == PositionType.RIGHT for child in existing_children)
                    
                    if not has_left:
                        position_type = PositionType.LEFT
                    elif not has_right:
                        position_type = PositionType.RIGHT
                    else:
                        # 両方埋まっている場合、LEFTの下に配置（簡易版）
                        left_child = next(child for child in existing_children if child.position_type == PositionType.LEFT)
                        parent_position = left_child
                        position_type = PositionType.LEFT
                    
                    # 新しいポジション作成
                    new_position = OrganizationPosition(
                        member_id=member.id,
                        parent_id=parent_position.id,
                        position_type=position_type,
                        level=parent_position.level + 1,
                        hierarchy_path=f"{parent_position.hierarchy_path}.{len(position_dict)}"
                    )
                    
                    session.add(new_position)
                    position_dict[member.member_number] = new_position
                    newly_processed.append(member)
                    processed_count += 1
                    
                    print(f"📍 {member.name} ({member.member_number}) -> {position_type.value} of {parent_position.member.name}")
            
            # 処理されたメンバーを除去
            for member in newly_processed:
                remaining_members.remove(member)
            
            if not newly_processed:
                print(f"⚠️  残り {len(remaining_members)} 名の配置先が決まりません")
                # 残りのメンバーはルート直下のRIGHTに配置
                for member in remaining_members:
                    new_position = OrganizationPosition(
                        member_id=member.id,
                        parent_id=root_position.id,
                        position_type=PositionType.RIGHT,
                        level=1,
                        hierarchy_path=f"0.{len(position_dict)}"
                    )
                    session.add(new_position)
                    position_dict[member.member_number] = new_position
                    processed_count += 1
                    print(f"📍 {member.name} ({member.member_number}) -> ROOT.RIGHT (fallback)")
                break
        
        session.commit()
        print(f"✅ 組織構造作成完了: {processed_count + 1}名配置")
        
        # 3. 統計情報を更新
        update_organization_stats(session)
        
        # 4. 結果確認
        total_positions = session.query(OrganizationPosition).count()
        print(f"📊 総ポジション数: {total_positions}")
        
        # 階層別集計
        level_counts = {}
        for position in session.query(OrganizationPosition).all():
            level_counts[position.level] = level_counts.get(position.level, 0) + 1
        
        print("📈 階層別人数:")
        for level in sorted(level_counts.keys()):
            print(f"  レベル {level}: {level_counts[level]}名")
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

def update_organization_stats(session):
    """組織統計を更新"""
    print("📊 組織統計を更新中...")
    
    # 各ポジションの左右カウントを更新
    positions = session.query(OrganizationPosition).all()
    
    for position in positions:
        # 左の子ノード数
        left_count = session.query(OrganizationPosition).filter(
            OrganizationPosition.parent_id == position.id,
            OrganizationPosition.position_type == PositionType.LEFT
        ).count()
        
        # 右の子ノード数  
        right_count = session.query(OrganizationPosition).filter(
            OrganizationPosition.parent_id == position.id,
            OrganizationPosition.position_type == PositionType.RIGHT
        ).count()
        
        position.left_count = left_count
        position.right_count = right_count
    
    session.commit()
    print("✅ 組織統計更新完了")

if __name__ == "__main__":
    main()