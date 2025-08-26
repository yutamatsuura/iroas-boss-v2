"""
初期データ作成スクリプト

要件定義書の固定値を SystemSetting として登録
開発・テスト用のサンプル会員データも作成
"""

from sqlalchemy.orm import Session
from app.models.setting import SystemSetting, DEFAULT_SYSTEM_SETTINGS
from app.models.member import Member, MemberStatus, Title, Plan, PaymentMethod, Gender, AccountType
from app.models.organization import OrganizationNode
from datetime import datetime


def create_system_settings(db: Session) -> None:
    """システム設定の初期データ作成"""
    
    # 既存設定をチェック
    existing_count = db.query(SystemSetting).count()
    if existing_count > 0:
        print(f"システム設定は既に {existing_count} 件存在します。スキップします。")
        return
    
    print("システム設定の初期データを作成中...")
    
    # デフォルト設定を作成
    for key, display_name, value, description, unit, sort_order in DEFAULT_SYSTEM_SETTINGS:
        # カテゴリを判定
        if "PLAN_AMOUNT" in key or "PAYOUT" in key or "CALCULATION_DAY" in key:
            category = "ビジネスルール"
        elif "PAYMENT" in key or "TRANSFER" in key:
            category = "決済設定"
        elif "BONUS" in key or "TITLE_BONUS" in key:
            category = "報酬設定"
        else:
            category = "システム設定"
        
        # 設定タイプを判定
        if isinstance(value, bool):
            setting_type = "真偽値"
        elif isinstance(value, int):
            setting_type = "整数"
        elif isinstance(value, float):
            setting_type = "小数"
        else:
            setting_type = "文字列"
        
        setting = SystemSetting(
            key=key,
            category=category,
            setting_type=setting_type,
            display_name=display_name,
            description=description,
            unit=unit,
            is_editable=False,
            is_system=True,
            sort_order=sort_order
        )
        
        # 値を設定
        setting.set_value(value)
        db.add(setting)
    
    db.commit()
    print(f"システム設定 {len(DEFAULT_SYSTEM_SETTINGS)} 件を作成しました。")


def create_sample_members(db: Session) -> None:
    """サンプル会員データの作成（開発・テスト用）"""
    
    # 既存会員をチェック
    existing_count = db.query(Member).count()
    if existing_count > 0:
        print(f"会員データは既に {existing_count} 件存在します。サンプル作成をスキップします。")
        return
    
    print("サンプル会員データを作成中...")
    
    # サンプル会員データ定義
    sample_members = [
        {
            "member_number": "0000001",
            "name": "田中 太郎",
            "kana": "タナカ タロウ",
            "email": "tanaka@example.com",
            "title": Title.AREA_DIRECTOR,
            "plan": Plan.HERO,
            "payment_method": PaymentMethod.CARD,
            "phone": "090-1234-5678",
            "gender": Gender.MALE,
            "postal_code": "100-0001",
            "prefecture": "東京都",
            "address2": "千代田区千代田1-1",
            "address3": "千代田マンション101",
            "bank_name": "三菱UFJ銀行",
            "bank_code": "0005",
            "branch_name": "東京支店",
            "branch_code": "001",
            "account_number": "1234567",
            "account_type": AccountType.ORDINARY,
            "notes": "最上位会員（ルート）"
        },
        {
            "member_number": "0000002",
            "name": "佐藤 花子",
            "kana": "サトウ ハナコ",
            "email": "sato@example.com",
            "title": Title.DIRECTOR,
            "plan": Plan.HERO,
            "payment_method": PaymentMethod.TRANSFER,
            "phone": "090-2345-6789",
            "gender": Gender.FEMALE,
            "postal_code": "150-0001",
            "prefecture": "東京都",
            "address2": "渋谷区渋谷2-2",
            "upline_id": "0000001",
            "upline_name": "田中 太郎",
            "referrer_id": "0000001",
            "referrer_name": "田中 太郎",
            "bank_name": "みずほ銀行",
            "bank_code": "0001",
            "branch_name": "渋谷支店",
            "branch_code": "100",
            "account_number": "2345678",
            "account_type": AccountType.ORDINARY,
        },
        {
            "member_number": "0000003",
            "name": "山田 次郎",
            "kana": "ヤマダ ジロウ",
            "email": "yamada@example.com",
            "title": Title.EXPERT_MANAGER,
            "plan": Plan.HERO,
            "payment_method": PaymentMethod.BANK,
            "phone": "090-3456-7890",
            "gender": Gender.MALE,
            "status": MemberStatus.INACTIVE,
            "postal_code": "200-0001",
            "prefecture": "東京都",
            "address2": "立川市曙町3-3",
            "upline_id": "0000002",
            "upline_name": "佐藤 花子",
            "referrer_id": "0000002",
            "referrer_name": "佐藤 花子",
            "bank_name": "三井住友銀行",
            "bank_code": "0009",
            "branch_name": "立川支店",
            "branch_code": "200",
            "account_number": "3456789",
            "account_type": AccountType.ORDINARY,
        },
        {
            "member_number": "0000004",
            "name": "鈴木 美咲",
            "kana": "スズキ ミサキ",
            "email": "suzuki@example.com",
            "title": Title.MANAGER,
            "plan": Plan.TEST,
            "payment_method": PaymentMethod.INFOCART,
            "phone": "090-4567-8901",
            "gender": Gender.FEMALE,
            "postal_code": "300-0001",
            "prefecture": "茨城県",
            "address2": "土浦市中央1-1",
            "upline_id": "0000003",
            "upline_name": "山田 次郎",
            "referrer_id": "0000001",
            "referrer_name": "田中 太郎",
            "bank_name": "常陽銀行",
            "bank_code": "0130",
            "branch_name": "土浦支店",
            "branch_code": "001",
            "account_number": "4567890",
            "account_type": AccountType.ORDINARY,
        },
        {
            "member_number": "0000005",
            "name": "高橋 一郎",
            "kana": "タカハシ イチロウ",
            "email": "takahashi@example.com",
            "title": Title.NONE,
            "plan": Plan.TEST,
            "payment_method": PaymentMethod.CARD,
            "phone": "090-5678-9012",
            "gender": Gender.MALE,
            "status": MemberStatus.WITHDRAWN,
            "withdrawal_date": datetime(2024, 12, 15),
            "postal_code": "400-0001",
            "prefecture": "山梨県",
            "address2": "甲府市中央4-4",
            "upline_id": "0000001",
            "upline_name": "田中 太郎",
            "referrer_id": "0000004",
            "referrer_name": "鈴木 美咲",
            "notes": "2024年12月退会"
        }
    ]
    
    # 会員データ作成
    created_members = []
    for member_data in sample_members:
        member = Member(**member_data)
        db.add(member)
        created_members.append(member)
    
    # 一度コミットして ID を取得
    db.commit()
    
    # 組織ノード作成
    print("組織構造を作成中...")
    for member in created_members:
        if member.member_number == "0000001":
            # ルートノード
            org_node = OrganizationNode.create_root_node(member.id, member.member_number)
        else:
            # 親会員のIDを取得
            parent_member = db.query(Member).filter(Member.member_number == member.upline_id).first()
            if parent_member:
                parent_node = db.query(OrganizationNode).filter(
                    OrganizationNode.member_id == parent_member.id
                ).first()
                if parent_node:
                    org_node = OrganizationNode.create_child_node(
                        member.id, member.member_number, parent_node.id
                    )
                else:
                    continue
            else:
                continue
        
        db.add(org_node)
    
    db.commit()
    
    # 組織ノードのパス更新
    print("組織パスを更新中...")
    for node in db.query(OrganizationNode).all():
        if node.is_root:
            node.path = f"/{node.id}/"
            node.level = 0
        else:
            if node.parent:
                node.path = f"{node.parent.path}{node.id}/"
                node.level = node.parent.level + 1
    
    db.commit()
    
    print(f"サンプル会員 {len(sample_members)} 名と組織構造を作成しました。")


def initialize_database(db: Session) -> None:
    """データベースの初期化"""
    print("=== IROAS BOSS v2 データベース初期化 ===")
    
    # システム設定作成
    create_system_settings(db)
    
    # サンプル会員作成
    create_sample_members(db)
    
    print("=== 初期化完了 ===")


if __name__ == "__main__":
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        initialize_database(db)
    finally:
        db.close()