#!/usr/bin/env python3
"""
IROAS BOSS V2 テストサーバー
シンプルなテスト用バックエンドサーバー
"""

import json
import csv
import os
from typing import List, Dict, Any, Optional

# ベーシックなHTTPサーバー（外部依存なし）
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class IroasTestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """CORSプリフライトリクエスト対応"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """GET リクエスト処理"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # CORS ヘッダー設定
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # ルーティング
        if path == '/api/health':
            response = {
                "status": "healthy", 
                "service": "IROAS BOSS V2 Test Server",
                "version": "2.0.0-test"
            }
        elif path == '/api/v1/members':
            response = self.get_members()
        elif path == '/api/v1/organization/tree':
            response = self.get_organization_tree()
        elif path == '/api/v1/organization/stats':
            response = self.get_organization_stats()
        # 統合システムAPI
        elif path == '/api/v1/unified/members':
            response = self.get_unified_members(query_params)
        elif path == '/api/v1/unified/stats/summary':
            response = self.get_unified_stats_summary()
        elif path == '/api/v1/unified/data-integrity':
            response = self.get_data_integrity_report()
        else:
            response = {"error": "Not Found", "path": path}
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def get_members(self) -> Dict[str, Any]:
        """会員データ取得（実際のCSVからアクティブメンバーのみ）"""
        csv_path = "/Users/lennon/projects/iroas-boss-v2/csv/2025年8月組織図（バイナリ）.csv"
        
        if os.path.exists(csv_path):
            members = []
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 退会メンバーを除外（アクティブのみ）
                        is_withdrawn = row.get('退', '').strip() == '(退)'
                        if not is_withdrawn:  # アクティブメンバーのみ
                            members.append({
                                "id": len(members) + 1,
                                "member_number": row.get('会員番号', '').zfill(11),
                                "name": row.get('会員氏名', '').strip(),
                                "email": "",  # 組織図CSVにはメールアドレスなし
                                "phone": "",  # 組織図CSVには電話番号なし
                                "title": row.get('資格名', '').strip(),
                                "plan": "",
                                "payment_method": "",
                                "registration_date": row.get('登録日', ''),
                                "upline_id": "",
                                "upline_name": "",
                                "referrer_id": "",
                                "referrer_name": "",
                                "status": "ACTIVE"
                            })
            except Exception as e:
                print(f"CSV読み込みエラー: {e}")
                # エラー時はダミーデータにフォールバック
                members = [
                    {
                        "id": 1,
                        "member_number": "1000001", 
                        "name": "佐藤太郎",
                        "email": "sato@example.com",
                        "phone": "090-1234-5678",
                        "status": "ACTIVE"
                    },
                    {
                        "id": 2,
                        "member_number": "1000002",
                        "name": "田中花子", 
                        "email": "tanaka@example.com",
                        "phone": "090-8765-4321",
                        "status": "ACTIVE"
                    }
                ]
        else:
            # ファイルが見つからない場合はダミーデータ
            members = [
                {
                    "id": 1,
                    "member_number": "1000001", 
                    "name": "佐藤太郎",
                    "email": "sato@example.com",
                    "phone": "090-1234-5678",
                    "status": "ACTIVE"
                },
                {
                    "id": 2,
                    "member_number": "1000002",
                    "name": "田中花子", 
                    "email": "tanaka@example.com",
                    "phone": "090-8765-4321",
                    "status": "ACTIVE"
                }
            ]
        
        return {
            "members": members,
            "total_count": len(members),
            "active_count": len([m for m in members if m["status"] == "ACTIVE"]),
            "inactive_count": len([m for m in members if m["status"] == "INACTIVE"]),
            "withdrawn_count": len([m for m in members if m["status"] == "WITHDRAWN"]),
            "page": 1,
            "perPage": 50,
            "totalPages": 1
        }

    def get_organization_tree(self) -> Dict[str, Any]:
        """組織ツリーデータ取得（テスト用）"""
        csv_path = "/Users/lennon/projects/iroas-boss-v2/csv/2025年8月組織図（バイナリ）.csv"
        
        if os.path.exists(csv_path):
            # 実際の組織CSVデータを読み込み
            try:
                org_nodes = []
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for idx, row in enumerate(reader):
                        if idx > 10:  # テスト用に最初の10行のみ
                            break
                        
                        level = int(row.get('階層', '0')) if row.get('階層', '').isdigit() else 0
                        member_number = row.get('会員番号', f'TEST{idx:03d}')
                        name = row.get('会員氏名', f'テスト会員{idx:03d}')
                        
                        org_nodes.append({
                            "id": f"{level}-{member_number}",
                            "member_number": member_number,
                            "name": name,
                            "title": row.get('資格名', ''),
                            "level": level,
                            "hierarchy_path": row.get('組織階層', ''),
                            "registration_date": row.get('登録日', ''),
                            "is_direct": "(直)" in str(row.get('直', '')),
                            "is_withdrawn": "(退)" in str(row.get('退', '')),
                            "left_count": int(row.get('左人数（A）', '0')) if row.get('左人数（A）', '').isdigit() else 0,
                            "right_count": int(row.get('右人数（A）', '0')) if row.get('右人数（A）', '').isdigit() else 0,
                            "left_sales": int(row.get('左実績', '0')) if row.get('左実績', '').replace(',', '').isdigit() else 0,
                            "right_sales": int(row.get('右実績', '0')) if row.get('右実績', '').replace(',', '').isdigit() else 0,
                            "new_purchase": int(row.get('新規購入', '0')) if row.get('新規購入', '').replace(',', '').isdigit() else 0,
                            "repeat_purchase": int(row.get('リピート購入', '0')) if row.get('リピート購入', '').replace(',', '').isdigit() else 0,
                            "additional_purchase": int(row.get('追加購入', '0')) if row.get('追加購入', '').replace(',', '').isdigit() else 0,
                            "children": [],
                            "is_expanded": True,
                            "status": "WITHDRAWN" if "(退)" in str(row.get('退', '')) else "ACTIVE"
                        })
                        
                return {
                    "root_nodes": org_nodes,
                    "total_members": len(org_nodes),
                    "max_level": max([node["level"] for node in org_nodes]) if org_nodes else 0,
                    "total_sales": sum([node["left_sales"] + node["right_sales"] for node in org_nodes]),
                    "active_members": len([n for n in org_nodes if n["status"] == "ACTIVE"]),
                    "withdrawn_members": len([n for n in org_nodes if n["status"] == "WITHDRAWN"])
                }
                        
            except Exception as e:
                print(f"組織CSV読み込みエラー: {e}")
                
        # ダミー組織データ
        return {
            "root_nodes": [
                {
                    "id": "0-1000001",
                    "member_number": "1000001",
                    "name": "佐藤太郎",
                    "title": "エリアディレクター",
                    "level": 0,
                    "hierarchy_path": "0 なし",
                    "registration_date": "2023-01-01",
                    "is_direct": True,
                    "is_withdrawn": False,
                    "left_count": 5,
                    "right_count": 3,
                    "left_sales": 150000,
                    "right_sales": 80000,
                    "new_purchase": 10000,
                    "repeat_purchase": 20000,
                    "additional_purchase": 5000,
                    "children": [],
                    "is_expanded": True,
                    "status": "ACTIVE"
                }
            ],
            "total_members": 1,
            "max_level": 0,
            "total_sales": 230000,
            "active_members": 1,
            "withdrawn_members": 0
        }

    def get_organization_stats(self) -> Dict[str, Any]:
        """組織統計データ取得（テスト用）"""
        return {
            "total_members": 50,
            "active_members": 45,
            "withdrawn_members": 5,
            "max_level": 8,
            "average_level": 3.2,
            "total_left_sales": 2500000,
            "total_right_sales": 1800000,
            "total_sales": 4300000
        }

    def get_unified_members(self, query_params: Dict[str, List[str]]) -> Dict[str, Any]:
        """統合会員一覧取得（テスト用）"""
        # 基本の会員データを取得
        members_data = self.get_members()
        
        # 統合データ形式に変換
        unified_members = []
        for member in members_data["members"]:
            unified_member = {
                "member_number": member["member_number"].zfill(11),
                "name": member["name"],
                "email": member.get("email", ""),
                "phone": member.get("phone", ""),
                "status": member["status"],
                "registration_date": member.get("registration_date", ""),
                "level": 0,
                "hierarchy_path": "0 なし",
                "is_direct": True,
                "is_withdrawn": member["status"] == "WITHDRAWN",
                "left_sales": 50000.0,
                "right_sales": 30000.0,
                "new_purchase": 10000.0,
                "repeat_purchase": 5000.0,
                "additional_purchase": 2000.0,
                "left_count": 2,
                "right_count": 1,
                "current_title": member.get("title", "称号なし"),
                "historical_title": member.get("title", "称号なし"),
                "display_title": member.get("title", "称号なし"),
                "last_updated": "2024-09-04T12:00:00",
                "data_source": "INTEGRATED",
                "children": []
            }
            unified_members.append(unified_member)
        
        return {
            "members": unified_members,
            "total_count": len(unified_members),
            "active_count": len([m for m in unified_members if m["status"] == "ACTIVE"]),
            "inactive_count": len([m for m in unified_members if m["status"] == "INACTIVE"]),
            "withdrawn_count": len([m for m in unified_members if m["status"] == "WITHDRAWN"]),
            "page": 1,
            "per_page": 50,
            "total_pages": 1,
            "has_next": False,
            "has_prev": False
        }

    def get_unified_stats_summary(self) -> Dict[str, Any]:
        """統合統計サマリー取得（テスト用）"""
        csv_path = "/Users/lennon/projects/iroas-boss-v2/csv/2025年8月組織図（バイナリ）.csv"
        
        # 実際のCSVから統計を計算
        try:
            total_members = 0
            active_count = 0
            withdrawn_count = 0
            level_distribution = {}
            total_sales = 0.0
            
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        total_members += 1
                        
                        # レベル統計
                        level = int(row.get('階層', '0')) if row.get('階層', '').isdigit() else 0
                        level_distribution[str(level)] = level_distribution.get(str(level), 0) + 1
                        
                        # ステータス統計
                        if "(退)" in str(row.get('退', '')):
                            withdrawn_count += 1
                        else:
                            active_count += 1
                        
                        # 売上統計
                        left_sales = float(row.get('左実績', '0').replace(',', '')) if row.get('左実績', '').replace(',', '').isdigit() else 0
                        right_sales = float(row.get('右実績', '0').replace(',', '')) if row.get('右実績', '').replace(',', '').isdigit() else 0
                        total_sales += left_sales + right_sales
            
            return {
                "total_members": total_members,
                "status_counts": {
                    "active": active_count,
                    "inactive": 0,
                    "withdrawn": withdrawn_count
                },
                "level_distribution": level_distribution,
                "sales_summary": {
                    "total_sales": total_sales,
                    "new_purchase": total_sales * 0.1,
                    "repeat_purchase": total_sales * 0.2
                },
                "cache_info": {
                    "last_updated": "2024-09-04T12:00:00",
                    "cache_size": total_members
                }
            }
        except Exception as e:
            print(f"統合統計計算エラー: {e}")
            return {
                "total_members": 0,
                "status_counts": {"active": 0, "inactive": 0, "withdrawn": 0},
                "level_distribution": {},
                "sales_summary": {"total_sales": 0, "new_purchase": 0, "repeat_purchase": 0},
                "cache_info": {"last_updated": None, "cache_size": 0}
            }

    def get_data_integrity_report(self) -> Dict[str, Any]:
        """データ整合性レポート取得（テスト用）"""
        return {
            "check_date": "2024-09-04T12:00:00",
            "total_issues": 3,
            "duplicate_member_numbers": [],
            "invalid_member_numbers": ["0", "400"],
            "missing_names": ["00000154400"],
            "orphaned_members": [],
            "data_quality_score": 97.5,
            "recommendations": [
                "無効会員番号2件の修正が必要です",
                "氏名欠損1件の補完が必要です"
            ]
        }

def start_test_server(port=8000):
    """テストサーバー起動"""
    server = HTTPServer(('0.0.0.0', port), IroasTestHandler)
    print(f"🚀 IROAS BOSS V2 テストサーバー起動: http://localhost:{port}")
    print(f"📡 ヘルスチェック: http://localhost:{port}/api/health")
    print(f"👥 会員API: http://localhost:{port}/api/v1/members")
    print(f"🌳 組織API: http://localhost:{port}/api/v1/organization/tree")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹  サーバーを停止しています...")
        server.shutdown()

if __name__ == "__main__":
    start_test_server()