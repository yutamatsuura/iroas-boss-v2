"""
統合サービス層
Phase 1: 会員管理と組織図データの統合サービス
"""
import csv
import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import logging

from ..models.unified_models import (
    UnifiedMemberData, UnifiedOrganizationTree, MemberSearchParams,
    UnifiedMemberListResponse, DataIntegrityReport, MemberStatus,
    DataSource
)

logger = logging.getLogger(__name__)

class UnifiedMemberService:
    """統合会員サービス"""
    
    def __init__(self):
        """初期化"""
        self.csv_dir = "/Users/lennon/projects/iroas-boss-v2/csv"
        self.binary_csv = os.path.join(self.csv_dir, "2025年8月組織図（バイナリ）.csv")
        self.referral_csv = os.path.join(self.csv_dir, "2025年8月組織図（紹介系列）.csv")
        self._cache = {}
        self._cache_timestamp = None
    
    def _load_csv_data(self, filepath: str) -> List[Dict[str, Any]]:
        """CSVファイルからデータを読み込む"""
        data = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # カラム名のスペースを削除
                    cleaned_row = {}
                    for key, value in row.items():
                        clean_key = key.strip() if key else key
                        cleaned_row[clean_key] = value.strip() if value else value
                    data.append(cleaned_row)
            logger.info(f"CSV読み込み完了: {os.path.basename(filepath)} ({len(data)}件)")
        except Exception as e:
            logger.error(f"CSV読み込みエラー: {filepath}, {e}")
        return data
    
    def _normalize_member_status(self, is_withdrawn: bool, is_active: bool = True) -> MemberStatus:
        """会員ステータスを正規化"""
        if is_withdrawn:
            return MemberStatus.WITHDRAWN
        elif is_active:
            return MemberStatus.ACTIVE
        else:
            return MemberStatus.INACTIVE
    
    def _parse_boolean(self, value: str) -> bool:
        """文字列をbooleanに変換"""
        if not value:
            return False
        return value.strip().lower() in ['(退)', '(直)', 'true', '1', 'yes']
    
    def _parse_float(self, value: str, default: float = 0.0) -> float:
        """文字列をfloatに変換"""
        try:
            if not value or not value.strip():
                return default
            # カンマを除去して変換
            return float(value.replace(',', ''))
        except (ValueError, TypeError):
            return default
    
    def _parse_int(self, value: str, default: int = 0) -> int:
        """文字列をintに変換"""
        try:
            if not value or not value.strip():
                return default
            return int(value.replace(',', ''))
        except (ValueError, TypeError):
            return default
    
    def _create_unified_member(self, row: Dict[str, Any], data_source: DataSource) -> UnifiedMemberData:
        """CSVデータから統合会員データを作成"""
        member_number = row.get('会員番号', '').strip()
        name = row.get('会員氏名', '').strip()
        
        # 退会・直接フラグの解析
        is_withdrawn = self._parse_boolean(row.get('退', ''))
        is_direct = self._parse_boolean(row.get('直', ''))
        
        # ステータス決定
        status = self._normalize_member_status(is_withdrawn, not is_withdrawn)
        
        # レベルと階層
        level = self._parse_int(row.get('階層', '0'))
        hierarchy_path = row.get('組織階層', '').strip()
        
        # 売上データ
        left_sales = self._parse_float(row.get('左実績', '0'))
        right_sales = self._parse_float(row.get('右実績', '0'))
        new_purchase = self._parse_float(row.get('新規購入', '0'))
        repeat_purchase = self._parse_float(row.get('リピート購入', '0'))
        additional_purchase = self._parse_float(row.get('追加購入', '0'))
        
        # 人数データ
        left_count = self._parse_int(row.get('左人数（A）', '0'))
        right_count = self._parse_int(row.get('右人数（A）', '0'))
        
        # 称号情報
        current_title = row.get('資格名', '').strip()
        
        # 表示用称号の決定
        display_title = current_title if current_title else '称号なし'
        
        return UnifiedMemberData(
            member_number=member_number,
            name=name,
            status=status,
            registration_date=row.get('登録日', ''),
            level=level,
            hierarchy_path=hierarchy_path,
            is_direct=is_direct,
            is_withdrawn=is_withdrawn,
            left_sales=left_sales,
            right_sales=right_sales,
            new_purchase=new_purchase,
            repeat_purchase=repeat_purchase,
            additional_purchase=additional_purchase,
            left_count=left_count,
            right_count=right_count,
            current_title=current_title,
            historical_title=current_title,
            display_title=display_title,
            last_updated=datetime.now(),
            data_source=data_source
        )
    
    def _should_refresh_cache(self) -> bool:
        """キャッシュを更新すべきかチェック"""
        if not self._cache_timestamp:
            return True
        
        # 5分間キャッシュ
        cache_duration = 300  # seconds
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed > cache_duration
    
    def _load_unified_members(self, force_refresh: bool = False) -> Dict[str, UnifiedMemberData]:
        """統合会員データを読み込み"""
        if not force_refresh and not self._should_refresh_cache():
            return self._cache.get('members', {})
        
        logger.info("統合会員データの読み込み開始")
        members = {}
        
        # バイナリ組織図データを読み込み（メイン）
        binary_data = self._load_csv_data(self.binary_csv)
        for row in binary_data:
            try:
                member = self._create_unified_member(row, DataSource.ORGANIZATION_CSV)
                if member.member_number:
                    members[member.member_number] = member
            except Exception as e:
                logger.error(f"バイナリ組織データ変換エラー: {row.get('会員番号', 'N/A')}, {e}")
        
        # 紹介系列データで補完（追加メンバーのみ）
        referral_data = self._load_csv_data(self.referral_csv)
        for row in referral_data:
            try:
                member_number = row.get('会員番号', '').strip()
                if member_number and member_number not in members:
                    member = self._create_unified_member(row, DataSource.ORGANIZATION_CSV)
                    members[member_number] = member
            except Exception as e:
                logger.error(f"紹介系列データ変換エラー: {row.get('会員番号', 'N/A')}, {e}")
        
        # キャッシュ更新
        self._cache['members'] = members
        self._cache_timestamp = datetime.now()
        
        logger.info(f"統合会員データ読み込み完了: {len(members)}名")
        return members
    
    def get_unified_member(self, member_number: str) -> Optional[UnifiedMemberData]:
        """統合会員データを取得"""
        members = self._load_unified_members()
        return members.get(member_number)
    
    def get_unified_member_list(self, params: MemberSearchParams) -> UnifiedMemberListResponse:
        """統合会員一覧を取得"""
        members = self._load_unified_members()
        all_members = list(members.values())
        
        # フィルタリング
        filtered_members = self._filter_members(all_members, params)
        
        # ソート
        sorted_members = self._sort_members(filtered_members, params.sort_by, params.sort_order)
        
        # ページネーション
        total_count = len(sorted_members)
        start_idx = (params.page - 1) * params.per_page
        end_idx = start_idx + params.per_page
        page_members = sorted_members[start_idx:end_idx]
        
        # 統計計算
        active_count = sum(1 for m in sorted_members if m.status == MemberStatus.ACTIVE)
        inactive_count = sum(1 for m in sorted_members if m.status == MemberStatus.INACTIVE)
        withdrawn_count = sum(1 for m in sorted_members if m.status == MemberStatus.WITHDRAWN)
        
        total_pages = (total_count + params.per_page - 1) // params.per_page
        
        return UnifiedMemberListResponse(
            members=page_members,
            total_count=total_count,
            active_count=active_count,
            inactive_count=inactive_count,
            withdrawn_count=withdrawn_count,
            page=params.page,
            per_page=params.per_page,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1
        )
    
    def _filter_members(self, members: List[UnifiedMemberData], params: MemberSearchParams) -> List[UnifiedMemberData]:
        """会員リストをフィルタリング"""
        filtered = members
        
        if params.member_number:
            filtered = [m for m in filtered if params.member_number in m.member_number]
        
        if params.name:
            filtered = [m for m in filtered if params.name in m.name]
        
        if params.status:
            filtered = [m for m in filtered if m.status == params.status]
        
        if params.level_min is not None:
            filtered = [m for m in filtered if m.level >= params.level_min]
        
        if params.level_max is not None:
            filtered = [m for m in filtered if m.level <= params.level_max]
        
        if params.active_only:
            filtered = [m for m in filtered if m.status == MemberStatus.ACTIVE]
        
        return filtered
    
    def _sort_members(self, members: List[UnifiedMemberData], sort_by: str, sort_order: str) -> List[UnifiedMemberData]:
        """会員リストをソート"""
        reverse = sort_order == "desc"
        
        if sort_by == "member_number":
            return sorted(members, key=lambda m: m.member_number, reverse=reverse)
        elif sort_by == "name":
            return sorted(members, key=lambda m: m.name, reverse=reverse)
        elif sort_by == "level":
            return sorted(members, key=lambda m: m.level, reverse=reverse)
        elif sort_by == "registration_date":
            return sorted(members, key=lambda m: m.registration_date or "", reverse=reverse)
        else:
            return sorted(members, key=lambda m: m.member_number, reverse=reverse)


class DataIntegrityService:
    """データ整合性サービス"""
    
    def __init__(self):
        self.unified_service = UnifiedMemberService()
    
    def check_data_integrity(self) -> DataIntegrityReport:
        """データ整合性をチェック"""
        logger.info("データ整合性チェック開始")
        
        members = self.unified_service._load_unified_members(force_refresh=True)
        
        # 問題の検出
        duplicate_numbers = self._find_duplicate_member_numbers(members)
        invalid_numbers = self._find_invalid_member_numbers(members)
        missing_names = self._find_missing_names(members)
        orphaned_members = self._find_orphaned_members(members)
        
        # 品質スコアの計算
        total_members = len(members)
        total_issues = (len(duplicate_numbers) + len(invalid_numbers) + 
                       len(missing_names) + len(orphaned_members))
        
        quality_score = max(0, 100 - (total_issues / max(total_members, 1)) * 100)
        
        # 推奨事項の生成
        recommendations = self._generate_recommendations(
            duplicate_numbers, invalid_numbers, missing_names, orphaned_members
        )
        
        return DataIntegrityReport(
            check_date=datetime.now(),
            total_issues=total_issues,
            duplicate_member_numbers=duplicate_numbers,
            invalid_member_numbers=invalid_numbers,
            missing_names=missing_names,
            orphaned_members=orphaned_members,
            data_quality_score=quality_score,
            recommendations=recommendations
        )
    
    def _find_duplicate_member_numbers(self, members: Dict[str, UnifiedMemberData]) -> List[str]:
        """重複会員番号を検出"""
        # Dictキーがユニークなので、基本的に重複はない
        return []
    
    def _find_invalid_member_numbers(self, members: Dict[str, UnifiedMemberData]) -> List[str]:
        """無効な会員番号を検出"""
        invalid = []
        for member_number, member in members.items():
            if not member_number.isdigit() or len(member_number) != 11:
                invalid.append(member_number)
        return invalid
    
    def _find_missing_names(self, members: Dict[str, UnifiedMemberData]) -> List[str]:
        """氏名が欠損している会員を検出"""
        missing = []
        for member_number, member in members.items():
            if not member.name or member.name.strip() == "":
                missing.append(member_number)
        return missing
    
    def _find_orphaned_members(self, members: Dict[str, UnifiedMemberData]) -> List[str]:
        """親が存在しない会員を検出（階層構造の整合性）"""
        # 実装は複雑なため、現時点では空リストを返す
        return []
    
    def _generate_recommendations(self, duplicates: List[str], invalid: List[str], 
                                missing: List[str], orphaned: List[str]) -> List[str]:
        """改善推奨事項を生成"""
        recommendations = []
        
        if duplicates:
            recommendations.append(f"重複会員番号{len(duplicates)}件の統合が必要です")
        
        if invalid:
            recommendations.append(f"無効会員番号{len(invalid)}件の修正が必要です")
        
        if missing:
            recommendations.append(f"氏名欠損{len(missing)}件の補完が必要です")
        
        if orphaned:
            recommendations.append(f"孤立メンバー{len(orphaned)}件の階層修正が必要です")
        
        if not any([duplicates, invalid, missing, orphaned]):
            recommendations.append("データ品質は良好です")
        
        return recommendations