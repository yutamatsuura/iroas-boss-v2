"""
会員管理APIエンドポイント
"""
import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import Member, MemberStatus
from app.schemas.member import (
    MemberCreate, 
    MemberUpdate, 
    MemberResponse, 
    MemberList,
    MemberListItem
)

router = APIRouter(prefix="/members", tags=["members"])

@router.get("/", response_model=MemberList)
async def get_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    memberNumber: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    status: Optional[MemberStatus] = None,
    plan: Optional[str] = None,
    paymentMethod: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """会員一覧取得"""
    query = db.query(Member).filter(Member.is_deleted == False)
    
    # 検索条件（個別フィールド）
    if memberNumber:
        query = query.filter(Member.member_number.contains(memberNumber))
    if name:
        query = query.filter(Member.name.contains(name))
    if email:
        query = query.filter(Member.email.contains(email))
    
    # 汎用検索（後方互換性のため残す）
    if search:
        search_filter = or_(
            Member.member_number.contains(search),
            Member.name.contains(search),
            Member.email.contains(search)
        )
        query = query.filter(search_filter)
    
    if status:
        query = query.filter(Member.status == status)
    
    if plan:
        query = query.filter(Member.plan == plan)
    
    if paymentMethod:
        query = query.filter(Member.payment_method == paymentMethod)
    
    # 総件数取得
    total = query.count()
    
    # ステータス別カウント取得
    active_count = db.query(Member).filter(Member.status == MemberStatus.ACTIVE, Member.is_deleted == False).count()
    inactive_count = db.query(Member).filter(Member.status == MemberStatus.INACTIVE, Member.is_deleted == False).count()
    withdrawn_count = db.query(Member).filter(Member.status == MemberStatus.WITHDRAWN, Member.is_deleted == False).count()
    
    # ページネーション
    members = query.offset(skip).limit(limit).all()
    
    return {
        "members": members,
        "total_count": total,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "withdrawn_count": withdrawn_count
    }

@router.get("/export")
async def export_members(
    memberNumber: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    status: Optional[MemberStatus] = None,
    db: Session = Depends(get_db)
):
    """会員データCSV出力"""
    query = db.query(Member).filter(Member.is_deleted == False)
    
    # 検索条件適用
    if memberNumber:
        query = query.filter(Member.member_number.contains(memberNumber))
    if name:
        query = query.filter(Member.name.contains(name))
    if email:
        query = query.filter(Member.email.contains(email))
    if status:
        query = query.filter(Member.status == status)
    
    members = query.all()
    
    # CSV作成
    output = io.StringIO()
    writer = csv.writer(output)
    
    # ヘッダー行（カナを除く29項目）
    writer.writerow([
        'ステータス', '会員番号', '氏名', 'メールアドレス',
        '称号', 'ユーザータイプ', '加入プラン', '決済方法',
        '登録日', '退会日', '電話番号', '性別',
        '郵便番号', '都道府県', '住所2', '住所3',
        '直上者ID', '直上者名', '紹介者ID', '紹介者名',
        '銀行名', '銀行コード', '支店名', '支店コード',
        '口座番号', 'ゆうちょ記号', 'ゆうちょ番号', '口座種別', '備考'
    ])
    
    # 表示用マッピング辞書
    status_map = {'ACTIVE': 'アクティブ', 'INACTIVE': '休会中', 'WITHDRAWN': '退会済'}
    title_map = {'NONE': '称号なし', 'KNIGHT_DAME': 'ナイト/デイム', 'LORD_LADY': 'ロード/レディ', 
                 'KING_QUEEN': 'キング/クイーン', 'EMPEROR_EMPRESS': 'エンペラー/エンプレス'}
    user_type_map = {'NORMAL': '通常', 'ATTENTION': '注意'}
    plan_map = {'HERO': 'ヒーロープラン', 'TEST': 'テストプラン'}
    payment_method_map = {'CARD': 'カード決済', 'TRANSFER': '口座振替', 'BANK': '銀行振込', 'INFOCART': 'インフォカート'}
    gender_map = {'MALE': '男性', 'FEMALE': '女性', 'OTHER': 'その他'}
    account_type_map = {'ORDINARY': '普通', 'CHECKING': '当座'}
    
    # データ行
    for member in members:
        writer.writerow([
            status_map.get(member.status.value, '') if member.status else '',
            member.member_number,
            member.name,
            member.email,
            title_map.get(member.title.value, '') if member.title else '',
            user_type_map.get(member.user_type.value, '') if member.user_type else '',
            plan_map.get(member.plan.value, '') if member.plan else '',
            payment_method_map.get(member.payment_method.value, '') if member.payment_method else '',
            member.registration_date or '',
            member.withdrawal_date or '',
            member.phone or '',
            gender_map.get(member.gender.value, '') if member.gender else '',
            member.postal_code or '',
            member.prefecture or '',
            member.address2 or '',
            member.address3 or '',
            member.upline_id or '',
            member.upline_name or '',
            member.referrer_id or '',
            member.referrer_name or '',
            member.bank_name or '',
            member.bank_code or '',
            member.branch_name or '',
            member.branch_code or '',
            member.account_number or '',
            member.yucho_symbol or '',
            member.yucho_number or '',
            account_type_map.get(member.account_type.value, '') if member.account_type else '',
            member.notes or ''
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members.csv"}
    )

@router.get("/{member_number}", response_model=MemberResponse)
async def get_member(member_number: str, db: Session = Depends(get_db)):
    """会員詳細取得"""
    member = db.query(Member).filter(
        Member.member_number == member_number,
        Member.is_deleted == False
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return member

@router.post("/", response_model=MemberResponse)
async def create_member(member_data: MemberCreate, db: Session = Depends(get_db)):
    """会員登録"""
    print(f"Received data: {member_data.dict()}")  # デバッグログ
    
    # 重複チェック
    existing = db.query(Member).filter(
        or_(
            Member.member_number == member_data.member_number,
            Member.email == member_data.email
        )
    ).first()
    
    if existing:
        print(f"Duplicate found: {existing.member_number} - {existing.email}")
        raise HTTPException(
            status_code=400, 
            detail="Member number or email already exists"
        )
    
    # 会員作成
    member = Member(**member_data.dict())
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return member

@router.put("/{member_number}", response_model=MemberResponse)
async def update_member(
    member_number: str,
    member_data: MemberUpdate,
    db: Session = Depends(get_db)
):
    """会員情報更新"""
    member = db.query(Member).filter(
        Member.member_number == member_number,
        Member.is_deleted == False
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # 更新
    update_data = member_data.dict(exclude_unset=True)
    print(f"受信した更新データ: {update_data}")  # デバッグログ
    for key, value in update_data.items():
        setattr(member, key, value)
        print(f"更新: {key} = {value}")  # デバッグログ
    
    db.commit()
    db.refresh(member)
    
    return member

@router.delete("/{member_number}")
async def delete_member(member_number: str, db: Session = Depends(get_db)):
    """会員削除（論理削除）"""
    member = db.query(Member).filter(
        Member.member_number == member_number,
        Member.is_deleted == False
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # 論理削除
    member.is_deleted = True
    db.commit()
    
    return {"message": "Member deleted successfully"}

@router.post("/{member_number}/withdraw")
async def withdraw_member(member_number: str, db: Session = Depends(get_db)):
    """会員退会処理"""
    member = db.query(Member).filter(
        Member.member_number == member_number,
        Member.is_deleted == False
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if not member.can_withdraw():
        raise HTTPException(status_code=400, detail="Member cannot withdraw")
    
    # 退会処理
    member.set_withdrawn()
    db.commit()
    
    return {"message": "Member withdrawn successfully"}

@router.get("/template/download")
async def download_member_template():
    """会員データCSVテンプレートダウンロード"""
    # CSVテンプレート作成
    output = io.StringIO()
    writer = csv.writer(output)
    
    # ヘッダー行（29項目）
    writer.writerow([
        'ステータス', '会員番号', '氏名', 'メールアドレス',
        '称号', 'ユーザータイプ', '加入プラン', '決済方法',
        '登録日', '退会日', '電話番号', '性別',
        '郵便番号', '都道府県', '住所2', '住所3',
        '直上者ID', '直上者名', '紹介者ID', '紹介者名',
        '銀行名', '銀行コード', '支店名', '支店コード',
        '口座番号', 'ゆうちょ記号', 'ゆうちょ番号', '口座種別', '備考'
    ])
    
    # サンプルデータ行（記入例として3行）
    writer.writerow([
        'アクティブ', '10000000999', 'サンプル太郎', 'sample.taro@example.com',
        'ナイト/デイム', '通常', 'ヒーロープラン', 'カード決済',
        '2024-01-01', '', '090-0000-0000', '男性',
        '100-0001', '東京都', '千代田区1-1-1', 'サンプルビル101',
        '10000000001', '山田太郎', '10000000002', '佐藤花子',
        '三菱UFJ銀行', '0005', '東京支店', '001',
        '1234567', '', '', '普通', 'サンプルデータ'
    ])
    
    writer.writerow([
        'アクティブ', '10000000998', 'サンプル花子', 'sample.hanako@example.com',
        'ロード/レディ', '注意', 'ヒーロープラン', '口座振替',
        '2024-02-01', '', '080-0000-0000', '女性',
        '164-0001', '東京都', '中野区5-6-7', 'サンプルマンション201',
        '10000000002', '佐藤花子', '10000000003', '田中一郎',
        'ゆうちょ銀行', '', '', '',
        '', '18220', '87654321', '', 'ゆうちょ銀行利用例'
    ])
    
    writer.writerow([
        '休会中', '10000000997', 'サンプル次郎', 'sample.jiro@example.com',
        'エンペラー/エンプレス', '通常', 'テストプラン', 'インフォカート',
        '2023年12月1日', '', '070-0000-0000', 'その他',
        '530-0001', '大阪府', '大阪市北区梅田2-2-2', 'サンプルタワー501',
        '10000000003', '田中一郎', '10000000001', '山田太郎',
        'みずほ銀行', '0001', '大阪支店', '101',
        '9876543', '', '', '当座', '多様性サンプル'
    ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=member_import_template.csv"}
    )

@router.post("/import")
async def import_members(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """会員データCSV取込"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSV file required")
    
    contents = await file.read()
    decoded = contents.decode('utf-8-sig')
    
    reader = csv.DictReader(io.StringIO(decoded))
    
    imported_count = 0
    errors = []
    
    for row_num, row in enumerate(reader, start=2):
        try:
            # 既存チェック
            existing = db.query(Member).filter(
                Member.member_number == row['会員番号']
            ).first()
            
            if existing:
                errors.append(f"行{row_num}: 会員番号 {row['会員番号']} は既に存在します")
                continue
            
            # 空文字列をNoneに変換するヘルパー関数
            def empty_to_none(value):
                return None if value == '' else value
            
            # 日本語値を内部Enum値に変換
            status_map = {'アクティブ': 'ACTIVE', '休会中': 'INACTIVE', '退会済': 'WITHDRAWN'}
            title_map = {'称号なし': 'NONE', 'ナイト/デイム': 'KNIGHT_DAME', 'ロード/レディ': 'LORD_LADY', 
                        'キング/クイーン': 'KING_QUEEN', 'エンペラー/エンプレス': 'EMPEROR_EMPRESS'}
            user_type_map = {'通常': 'NORMAL', '注意': 'ATTENTION'}
            plan_map = {'ヒーロープラン': 'HERO', 'テストプラン': 'TEST'}
            payment_map = {'カード決済': 'CARD', '口座振替': 'TRANSFER', '銀行振込': 'BANK', 'インフォカート': 'INFOCART'}
            gender_map = {'男性': 'MALE', '女性': 'FEMALE', 'その他': 'OTHER'}
            account_map = {'普通': 'ORDINARY', '当座': 'CHECKING'}
            
            # 新規作成
            member = Member(
                status=status_map.get(row.get('ステータス', 'アクティブ'), 'ACTIVE'),
                member_number=row['会員番号'],
                name=row['氏名'],
                email=row['メールアドレス'],
                title=title_map.get(row.get('称号', '称号なし'), 'NONE'),
                user_type=user_type_map.get(row.get('ユーザータイプ', '通常'), 'NORMAL'),
                plan=plan_map.get(row.get('加入プラン', 'ヒーロープラン'), 'HERO'),
                payment_method=payment_map.get(row.get('決済方法', 'カード決済'), 'CARD'),
                registration_date=empty_to_none(row.get('登録日')),
                withdrawal_date=empty_to_none(row.get('退会日')),
                phone=empty_to_none(row.get('電話番号')),
                gender=gender_map.get(row.get('性別')) if row.get('性別') else None,
                postal_code=empty_to_none(row.get('郵便番号')),
                prefecture=empty_to_none(row.get('都道府県')),
                address2=empty_to_none(row.get('住所2')),
                address3=empty_to_none(row.get('住所3')),
                upline_id=empty_to_none(row.get('直上者ID')),
                upline_name=empty_to_none(row.get('直上者名')),
                referrer_id=empty_to_none(row.get('紹介者ID')),
                referrer_name=empty_to_none(row.get('紹介者名')),
                bank_name=empty_to_none(row.get('銀行名')),
                bank_code=empty_to_none(row.get('銀行コード')),
                branch_name=empty_to_none(row.get('支店名')),
                branch_code=empty_to_none(row.get('支店コード')),
                account_number=empty_to_none(row.get('口座番号')),
                yucho_symbol=empty_to_none(row.get('ゆうちょ記号')),
                yucho_number=empty_to_none(row.get('ゆうちょ番号')),
                account_type=account_map.get(row.get('口座種別')) if row.get('口座種別') else None,
                notes=empty_to_none(row.get('備考'))
            )
            
            db.add(member)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"行{row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "imported": imported_count,
        "errors": errors
    }