#!/usr/bin/env python3
"""
バランスの取れた組織構造作成スクリプト
45名のアクティブメンバーでバイナリツリーを構築
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.member import Member
from app.models.organization import OrganizationPosition, PositionType
import math

def main():
    print("🚀 バランス組織構造作成を開始...")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 既存の組織データをクリア
        session.query(OrganizationPosition).delete()
        session.commit()
        
        # アクティブメンバーを会員番号順で取得
        members = session.query(Member).filter(Member.status == 'ACTIVE').order_by(Member.member_number).all()
        print(f"📋 アクティブメンバー: {len(members)}名")
        
        if not members:
            print("❌ アクティブメンバーが見つかりません")
            return
        
        # 1. ルートノード作成（白石達也）
        root_member = next((m for m in members if m.member_number == '00000000000'), members[0])
        root_position = OrganizationPosition(
            member_id=root_member.id,
            position_type=PositionType.ROOT,
            level=0,
            hierarchy_path='0'
        )
        session.add(root_position)
        session.flush()  # IDを取得するためflush
        
        print(f"✅ ルートノード: {root_member.name}")
        
        # 2. ルート以外のメンバーでバイナリツリーを構築
        remaining_members = [m for m in members if m.id != root_member.id]
        positions = [root_position]  # 既に作成されたポジション
        member_positions = {root_member.id: root_position}
        
        # バイナリツリー構築（幅優先）
        for i, member in enumerate(remaining_members):
            # 親ポジションを決定（バイナリツリーの性質を利用）
            parent_index = i // 2
            if parent_index >= len(positions):
                parent_index = 0  # フォールバック：ルートの子に
            
            parent_position = positions[parent_index]
            
            # LEFT/RIGHT を決定
            # 奇数番目（i%2==0）をLEFT、偶数番目（i%2==1）をRIGHTに配置
            position_type = PositionType.LEFT if (i % 2 == 0) else PositionType.RIGHT
            
            # 既に同じ親の同じ側にポジションがある場合はRIGHTに
            existing_children = [p for p in positions if getattr(p, 'parent_id', None) == parent_position.id]
            existing_types = [p.position_type for p in existing_children]
            
            if position_type in existing_types:
                position_type = PositionType.RIGHT if PositionType.RIGHT not in existing_types else PositionType.LEFT
            
            # 両方埋まっている場合は、次の親を探す
            if PositionType.LEFT in existing_types and PositionType.RIGHT in existing_types:
                # より深い階層で親を探す
                parent_index = (parent_index + 1) % len(positions)
                parent_position = positions[parent_index]
                position_type = PositionType.LEFT
            
            # 新しいポジション作成
            new_position = OrganizationPosition(
                member_id=member.id,
                parent_id=parent_position.id,
                position_type=position_type,
                level=parent_position.level + 1,
                hierarchy_path=f"{parent_position.hierarchy_path}.{len(positions)}"
            )
            
            session.add(new_position)
            positions.append(new_position)
            member_positions[member.id] = new_position
            
            # 親メンバー名を取得
            parent_member = session.query(Member).filter(Member.id == parent_position.member_id).first()
            parent_name = parent_member.name if parent_member else "Unknown"
            
            print(f"📍 {member.name} -> {position_type.value} of {parent_name} (Level {new_position.level})")
        
        session.commit()
        print(f"✅ 組織構造作成完了: {len(positions)}名配置")
        
        # 3. 組織統計を更新
        update_organization_counts(session)
        
        # 4. 結果確認
        show_organization_summary(session)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

def update_organization_counts(session):
    """組織の左右カウントを更新"""
    print("📊 組織統計を更新中...")
    
    def count_subtree(position):
        """再帰的に部下をカウント"""
        children = session.query(OrganizationPosition).filter(
            OrganizationPosition.parent_id == position.id
        ).all()
        
        left_count = 0
        right_count = 0
        
        for child in children:
            if child.position_type == PositionType.LEFT:
                left_count = 1 + count_subtree(child)
            elif child.position_type == PositionType.RIGHT:
                right_count = 1 + count_subtree(child)
        
        position.left_count = left_count
        position.right_count = right_count
        
        return left_count + right_count
    
    # ルートから再帰的にカウント
    root = session.query(OrganizationPosition).filter(
        OrganizationPosition.position_type == PositionType.ROOT
    ).first()
    
    if root:
        count_subtree(root)
    
    session.commit()
    print("✅ 組織統計更新完了")

def show_organization_summary(session):
    """組織概要を表示"""
    total_positions = session.query(OrganizationPosition).count()
    print(f"📊 総ポジション数: {total_positions}")
    
    # 階層別集計
    level_counts = {}
    positions = session.query(OrganizationPosition).all()
    
    for position in positions:
        level_counts[position.level] = level_counts.get(position.level, 0) + 1
    
    print("📈 階層別人数:")
    for level in sorted(level_counts.keys()):
        print(f"  レベル {level}: {level_counts[level]}名")
    
    # ルートの左右バランス
    root = session.query(OrganizationPosition).filter(
        OrganizationPosition.position_type == PositionType.ROOT
    ).first()
    
    if root:
        print(f"⚖️  ルートバランス: LEFT {root.left_count}名 | RIGHT {root.right_count}名")

if __name__ == "__main__":
    main()