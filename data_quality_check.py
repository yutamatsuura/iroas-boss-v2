#!/usr/bin/env python3
"""
データ品質チェックスクリプト
会員管理データと組織図データの整合性を確認
"""
import csv
import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
import os
import re

def read_csv_file(filepath: str) -> List[Dict]:
    """CSVファイルを読み込む"""
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # カラム名のスペースを削除
                cleaned_row = {}
                for key, value in row.items():
                    clean_key = key.strip() if key else key
                    cleaned_row[clean_key] = value
                data.append(cleaned_row)
        print(f"✓ {os.path.basename(filepath)}: {len(data)}件のレコードを読み込み")
    except Exception as e:
        print(f"✗ {os.path.basename(filepath)}の読み込みエラー: {e}")
    return data

def analyze_member_numbers(data: List[Dict], data_name: str) -> Dict:
    """会員番号の分析"""
    member_numbers = []
    invalid_numbers = []
    
    for row in data:
        member_num = row.get('会員番号', '').strip()
        if member_num:
            member_numbers.append(member_num)
            # 11桁数字チェック
            if not (member_num.isdigit() and len(member_num) == 11):
                invalid_numbers.append(member_num)
    
    duplicates = [num for num, count in Counter(member_numbers).items() if count > 1]
    
    return {
        'total_count': len(member_numbers),
        'unique_count': len(set(member_numbers)),
        'duplicates': duplicates,
        'invalid_format': invalid_numbers,
        'data_name': data_name
    }

def analyze_names(data: List[Dict], data_name: str) -> Dict:
    """氏名データの分析"""
    names = []
    empty_names = 0
    empty_name_details = []
    
    for i, row in enumerate(data):
        name = row.get('会員氏名', '').strip()
        member_num = row.get('会員番号', '').strip()
        if name:
            names.append(name)
        else:
            empty_names += 1
            empty_name_details.append(f"行{i+2}: 会員番号={member_num}")
            # 空の氏名の出力を制限
            if empty_names <= 10:  
                print(f"  - 空の氏名: 行{i+2}, 会員番号={member_num}")
    
    if empty_names > 10:
        print(f"  - 空の氏名: ...他{empty_names - 10}件")
    
    return {
        'total_count': len(data),
        'with_names': len(names),
        'empty_names': empty_names,
        'empty_name_details': empty_name_details[:10],  # 最初の10件のみ保存
        'data_name': data_name
    }

def analyze_hierarchy(org_data: List[Dict]) -> Dict:
    """組織階層の分析"""
    levels = []
    hierarchy_paths = []
    parent_child = defaultdict(list)
    
    for row in org_data:
        level = row.get('階層', '').strip()
        hierarchy = row.get('組織階層', '').strip()
        member_num = row.get('会員番号', '').strip()
        
        if level.isdigit():
            levels.append(int(level))
        
        if hierarchy:
            hierarchy_paths.append(hierarchy)
            # 階層パスから親子関係を抽出
            if '/' in hierarchy:
                parts = hierarchy.split('/')
                if len(parts) >= 2:
                    parent = parts[-2]
                    parent_child[parent].append(member_num)
    
    return {
        'max_level': max(levels) if levels else 0,
        'min_level': min(levels) if levels else 0,
        'level_distribution': Counter(levels),
        'orphans': [],  # 親が存在しないメンバー（後で計算）
        'total_hierarchies': len(hierarchy_paths)
    }

def compare_datasets(org_binary_data: List[Dict], org_referral_data: List[Dict]) -> Dict:
    """組織図データセット間の比較"""
    member_numbers_binary = set(row.get('会員番号', '').strip() for row in org_binary_data if row.get('会員番号', '').strip())
    member_numbers_referral = set(row.get('会員番号', '').strip() for row in org_referral_data if row.get('会員番号', '').strip())
    
    only_in_binary = member_numbers_binary - member_numbers_referral
    only_in_referral = member_numbers_referral - member_numbers_binary
    common = member_numbers_binary & member_numbers_referral
    
    # 氏名の一致チェック
    name_mismatches = []
    binary_name_map = {row.get('会員番号', '').strip(): row.get('会員氏名', '').strip() for row in org_binary_data}
    referral_name_map = {row.get('会員番号', '').strip(): row.get('会員氏名', '').strip() for row in org_referral_data}
    
    for member_num in common:
        binary_name = binary_name_map.get(member_num, '')
        referral_name = referral_name_map.get(member_num, '')
        if binary_name and referral_name and binary_name != referral_name:
            name_mismatches.append({
                'member_number': member_num,
                'binary_name': binary_name,
                'referral_name': referral_name
            })
    
    return {
        'total_binary_data': len(member_numbers_binary),
        'total_referral_data': len(member_numbers_referral),
        'common_members': len(common),
        'only_in_binary_data': list(only_in_binary),
        'only_in_referral_data': list(only_in_referral),
        'name_mismatches': name_mismatches
    }

def main():
    print("=== データ品質チェック開始 ===\n")
    
    # CSVファイルパス（会員マスタファイルは存在しないため除外）
    csv_dir = "/Users/lennon/projects/iroas-boss-v2/csv"
    org_binary_csv = os.path.join(csv_dir, "2025年8月組織図（バイナリ）.csv")
    org_referral_csv = os.path.join(csv_dir, "2025年8月組織図（紹介系列）.csv")
    
    # データ読み込み
    print("📁 データ読み込み中...")
    org_binary_data = read_csv_file(org_binary_csv)
    org_referral_data = read_csv_file(org_referral_csv)
    print()
    
    # 会員番号分析
    print("🔢 会員番号分析:")
    org_binary_analysis = analyze_member_numbers(org_binary_data, "組織図（バイナリ）")
    org_referral_analysis = analyze_member_numbers(org_referral_data, "組織図（紹介系列）")
    
    for analysis in [org_binary_analysis, org_referral_analysis]:
        print(f"  {analysis['data_name']}:")
        print(f"    - 総レコード数: {analysis['total_count']}")
        print(f"    - ユニーク会員番号数: {analysis['unique_count']}")
        if analysis['duplicates']:
            print(f"    - 重複: {len(analysis['duplicates'])}件 {analysis['duplicates'][:5]}...")
        if analysis['invalid_format']:
            print(f"    - 無効フォーマット: {len(analysis['invalid_format'])}件 {analysis['invalid_format'][:5]}...")
        print()
    
    # 氏名分析
    print("👤 氏名分析:")
    org_binary_name_analysis = analyze_names(org_binary_data, "組織図（バイナリ）")
    org_referral_name_analysis = analyze_names(org_referral_data, "組織図（紹介系列）")
    
    for analysis in [org_binary_name_analysis, org_referral_name_analysis]:
        print(f"  {analysis['data_name']}:")
        print(f"    - 氏名あり: {analysis['with_names']}/{analysis['total_count']}")
        if analysis['empty_names'] > 0:
            print(f"    - 空の氏名: {analysis['empty_names']}件")
        print()
    
    # 階層分析
    print("🏗️ 組織階層分析:")
    hierarchy_binary_analysis = analyze_hierarchy(org_binary_data)
    hierarchy_referral_analysis = analyze_hierarchy(org_referral_data)
    
    print(f"  バイナリ組織:")
    print(f"    - レベル範囲: {hierarchy_binary_analysis['min_level']} - {hierarchy_binary_analysis['max_level']}")
    print(f"    - レベル分布: {dict(hierarchy_binary_analysis['level_distribution'])}")
    print()
    
    print(f"  紹介系列組織:")
    print(f"    - レベル範囲: {hierarchy_referral_analysis['min_level']} - {hierarchy_referral_analysis['max_level']}")
    print(f"    - レベル分布: {dict(hierarchy_referral_analysis['level_distribution'])}")
    print()
    
    # データセット比較（バイナリ vs 紹介系列）
    print("🔄 データセット比較:")
    comparison = compare_datasets(org_binary_data, org_referral_data)
    print(f"  組織図（バイナリ） vs 組織図（紹介系列）:")
    print(f"    - バイナリ: {comparison['total_binary_data']}名")
    print(f"    - 紹介系列: {comparison['total_referral_data']}名")
    print(f"    - 共通: {comparison['common_members']}名")
    if comparison['only_in_binary_data']:
        print(f"    - バイナリのみ: {len(comparison['only_in_binary_data'])}名 {comparison['only_in_binary_data'][:5]}...")
    if comparison['only_in_referral_data']:
        print(f"    - 紹介系列のみ: {len(comparison['only_in_referral_data'])}名 {comparison['only_in_referral_data'][:5]}...")
    if comparison['name_mismatches']:
        print(f"    - 氏名不一致: {len(comparison['name_mismatches'])}件")
        for mismatch in comparison['name_mismatches'][:3]:
            print(f"      {mismatch['member_number']}: '{mismatch['binary_name']}' vs '{mismatch['referral_name']}'")
        if len(comparison['name_mismatches']) > 3:
            print(f"      ...他{len(comparison['name_mismatches']) - 3}件")
    print()
    
    # サマリー
    print("📊 サマリー:")
    total_issues = 0
    
    # 重複チェック
    if org_binary_analysis['duplicates'] or org_referral_analysis['duplicates']:
        print("  ⚠️  重複会員番号が検出されました")
        total_issues += len(org_binary_analysis['duplicates']) + len(org_referral_analysis['duplicates'])
    
    # フォーマットチェック
    if org_binary_analysis['invalid_format'] or org_referral_analysis['invalid_format']:
        print("  ⚠️  無効な会員番号フォーマットが検出されました")
        total_issues += len(org_binary_analysis['invalid_format']) + len(org_referral_analysis['invalid_format'])
    
    # 氏名チェック
    if org_binary_name_analysis['empty_names'] or org_referral_name_analysis['empty_names']:
        print("  ⚠️  空の氏名が検出されました")
        total_issues += org_binary_name_analysis['empty_names'] + org_referral_name_analysis['empty_names']
    
    # データ不一致チェック
    if comparison['name_mismatches']:
        print("  ⚠️  氏名の不一致が検出されました")
        total_issues += len(comparison['name_mismatches'])
    
    if comparison['only_in_binary_data'] or comparison['only_in_referral_data']:
        print("  ⚠️  データセット間で会員の差分が検出されました")
        total_issues += len(comparison['only_in_binary_data']) + len(comparison['only_in_referral_data'])
    
    if total_issues == 0:
        print("  ✅ データ品質に問題は検出されませんでした")
    else:
        print(f"  📋 合計 {total_issues} 件の問題が検出されました")
    
    print("\n=== データ品質チェック完了 ===")

if __name__ == "__main__":
    main()