"""
会員データ統合サービス
組織図データと会員管理データの統合機能
"""

import csv
import os
from typing import Dict, List, Optional
from collections import defaultdict

class MemberIntegrationService:
    """会員データ統合サービス"""
    
    def __init__(self):
        self.member_details_cache = {}
        self.integration_enabled = False
        
    def load_member_details(self, csv_path: str = None) -> bool:
        """
        会員管理CSVから詳細データを読み込み
        
        Args:
            csv_path: 会員管理CSVファイルのパス
            
        Returns:
            bool: 読み込み成功かどうか
        """
        if not csv_path:
            # デフォルトパスを試行
            csv_path = "/Users/lennon/projects/iroas-boss-v2/backend/members_export.csv"
            
        if not os.path.exists(csv_path):
            print(f"[INFO] 会員管理データが見つかりません: {csv_path}")
            return False
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    member_num = row.get('会員番号', '').strip()
                    if member_num:
                        # 会員番号を11桁に正規化
                        try:
                            normalized_num = str(int(member_num)).zfill(11)
                        except ValueError:
                            normalized_num = member_num
                            
                        self.member_details_cache[normalized_num] = {
                            'email': row.get('メールアドレス', '').strip(),
                            'phone': row.get('電話番号', '').strip(),
                            'status': row.get('﻿ステータス', '').strip(),
                            'plan': row.get('加入プラン', '').strip(),
                            'payment_method': row.get('決済方法', '').strip(),
                            'gender': row.get('性別', '').strip(),
                            'postal_code': row.get('郵便番号', '').strip(),
                            'prefecture': row.get('都道府県', '').strip(),
                            'address2': row.get('住所2', '').strip(),
                            'address3': row.get('住所3', '').strip(),
                            'withdrawal_date': row.get('退会日', '').strip(),
                            'supervisor_id': row.get('直上者ID', '').strip(),
                            'supervisor_name': row.get('直上者名', '').strip(),
                            'referrer_id': row.get('紹介者ID', '').strip(),
                            'referrer_name': row.get('紹介者名', '').strip(),
                            'bank_name': row.get('銀行名', '').strip(),
                            'bank_code': row.get('銀行コード', '').strip(),
                            'branch_name': row.get('支店名', '').strip(),
                            'branch_code': row.get('支店コード', '').strip(),
                            'account_number': row.get('口座番号', '').strip(),
                            'account_type': row.get('口座種別', '').strip(),
                            'remarks': row.get('備考', '').strip()
                        }
                        
            self.integration_enabled = True
            print(f"[INFO] 会員詳細データ読み込み完了: {len(self.member_details_cache)}件")
            return True
            
        except Exception as e:
            print(f"[ERROR] 会員詳細データ読み込みエラー: {str(e)}")
            return False
    
    def enhance_organization_data(self, org_data: List[Dict]) -> List[Dict]:
        """
        組織データに会員詳細情報を統合
        
        Args:
            org_data: 組織図データのリスト
            
        Returns:
            List[Dict]: 統合された組織データ
        """
        if not self.integration_enabled:
            # 統合無効の場合は元データを返す
            for item in org_data:
                item['has_member_details'] = False
            return org_data
            
        enhanced_data = []
        integration_count = 0
        
        for item in org_data:
            enhanced_item = item.copy()
            member_num = item.get('member_number', '')
            
            if member_num in self.member_details_cache:
                details = self.member_details_cache[member_num]
                
                # 会員詳細情報を追加
                enhanced_item.update({
                    'email': details['email'],
                    'phone': details['phone'],
                    'member_status_detail': details['status'],
                    'plan': details['plan'],
                    'payment_method': details['payment_method'],
                    'gender': details['gender'],
                    'address': f"{details['prefecture']} {details['address2']} {details['address3']}".strip(),
                    'postal_code': details['postal_code'],
                    'withdrawal_date': details['withdrawal_date'],
                    'supervisor_id': details['supervisor_id'],
                    'supervisor_name': details['supervisor_name'],
                    'referrer_id': details['referrer_id'],
                    'referrer_name': details['referrer_name'],
                    'bank_info': {
                        'bank_name': details['bank_name'],
                        'bank_code': details['bank_code'],
                        'branch_name': details['branch_name'],
                        'branch_code': details['branch_code'],
                        'account_number': details['account_number'],
                        'account_type': details['account_type']
                    } if details['bank_name'] else None,
                    'remarks': details['remarks'],
                    'has_member_details': True
                })
                integration_count += 1
            else:
                enhanced_item['has_member_details'] = False
                
            enhanced_data.append(enhanced_item)
        
        integration_rate = (integration_count / len(org_data) * 100) if org_data else 0
        print(f"[INFO] データ統合完了: {integration_count}/{len(org_data)}件 ({integration_rate:.1f}%)")
        
        return enhanced_data
    
    def get_integration_stats(self) -> Dict:
        """統合統計情報を取得"""
        return {
            'integration_enabled': self.integration_enabled,
            'cached_members': len(self.member_details_cache),
            'cache_size_kb': len(str(self.member_details_cache)) / 1024
        }
    
    def find_member_by_name(self, name: str) -> Optional[Dict]:
        """名前で会員詳細を検索"""
        if not self.integration_enabled:
            return None
            
        for member_num, details in self.member_details_cache.items():
            # 組織図データから氏名を取得する必要があるため、
            # ここでは会員番号のみ返す
            if name in str(details.values()):
                return {'member_number': member_num, **details}
        return None

# グローバルサービスインスタンス
member_integration_service = MemberIntegrationService()