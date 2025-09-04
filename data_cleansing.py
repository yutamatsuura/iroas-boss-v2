#!/usr/bin/env python3
"""
データクレンジングスクリプト
会員番号の11桁正規化と氏名データの修正
"""
import csv
import os
import shutil
from typing import Dict, List

def normalize_member_number(member_num: str) -> str:
    """会員番号を11桁形式に正規化"""
    if not member_num or not member_num.strip():
        return member_num
    
    # 数字のみ抽出
    num_str = member_num.strip()
    if num_str.isdigit():
        # 11桁に0パディング
        return num_str.zfill(11)
    return member_num

def fix_member_names(member_num: str, current_name: str) -> str:
    """特定の会員の氏名を修正"""
    name_fixes = {
        '00000154400': '株式会社アクシスネットワーク',
        '00000066600': '株式会社Rise'
    }
    
    normalized_num = normalize_member_number(member_num)
    
    # 空の氏名の場合、修正データがあれば使用
    if not current_name.strip() and normalized_num in name_fixes:
        return name_fixes[normalized_num]
    
    return current_name

def clean_csv_file(input_file: str, output_file: str) -> Dict:
    """CSVファイルをクレンジング"""
    processed_count = 0
    normalized_count = 0
    name_fixed_count = 0
    
    try:
        # バックアップ作成
        backup_file = input_file + '.backup'
        shutil.copy2(input_file, backup_file)
        print(f"バックアップ作成: {backup_file}")
        
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = [name.strip() for name in reader.fieldnames]
            
            cleaned_rows = []
            for row in reader:
                processed_count += 1
                cleaned_row = {}
                
                for key, value in row.items():
                    clean_key = key.strip()
                    cleaned_row[clean_key] = value
                
                # 会員番号の正規化
                original_num = cleaned_row.get('会員番号', '')
                normalized_num = normalize_member_number(original_num)
                
                if original_num != normalized_num:
                    normalized_count += 1
                    cleaned_row['会員番号'] = normalized_num
                
                # 氏名の修正
                original_name = cleaned_row.get('会員氏名', '')
                fixed_name = fix_member_names(normalized_num, original_name)
                
                if original_name != fixed_name:
                    name_fixed_count += 1
                    print(f"氏名修正: {normalized_num} '{original_name}' → '{fixed_name}'")
                
                cleaned_row['会員氏名'] = fixed_name
                cleaned_rows.append(cleaned_row)
        
        # クリーンなデータを書き込み
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)
        
        print(f"✓ {os.path.basename(output_file)}: {processed_count}件処理完了")
        
        return {
            'processed_count': processed_count,
            'normalized_count': normalized_count,
            'name_fixed_count': name_fixed_count,
            'output_file': output_file
        }
        
    except Exception as e:
        print(f"✗ {os.path.basename(input_file)}のクレンジングエラー: {e}")
        return {
            'processed_count': 0,
            'normalized_count': 0,
            'name_fixed_count': 0,
            'output_file': None,
            'error': str(e)
        }

def main():
    print("=== データクレンジング開始 ===\n")
    
    csv_dir = "/Users/lennon/projects/iroas-boss-v2/csv"
    
    # 処理対象ファイル
    files_to_clean = [
        "2025年8月組織図（バイナリ）.csv",
        "2025年8月組織図（紹介系列）.csv"
    ]
    
    total_stats = {
        'files_processed': 0,
        'total_records': 0,
        'total_normalized': 0,
        'total_name_fixed': 0
    }
    
    for filename in files_to_clean:
        input_path = os.path.join(csv_dir, filename)
        output_path = os.path.join(csv_dir, f"cleaned_{filename}")
        
        if not os.path.exists(input_path):
            print(f"⚠️ ファイルが見つかりません: {filename}")
            continue
        
        print(f"🔧 クレンジング中: {filename}")
        result = clean_csv_file(input_path, output_path)
        
        if result.get('output_file'):
            total_stats['files_processed'] += 1
            total_stats['total_records'] += result['processed_count']
            total_stats['total_normalized'] += result['normalized_count']
            total_stats['total_name_fixed'] += result['name_fixed_count']
            
            print(f"   - 処理レコード数: {result['processed_count']}")
            print(f"   - 正規化した会員番号: {result['normalized_count']}")
            print(f"   - 修正した氏名: {result['name_fixed_count']}")
            print(f"   - 出力ファイル: {os.path.basename(result['output_file'])}")
        else:
            print(f"   - エラー: {result.get('error', '不明')}")
        print()
    
    # サマリー
    print("📊 クレンジングサマリー:")
    print(f"   - 処理ファイル数: {total_stats['files_processed']}")
    print(f"   - 総レコード数: {total_stats['total_records']}")
    print(f"   - 正規化した会員番号: {total_stats['total_normalized']}")
    print(f"   - 修正した氏名: {total_stats['total_name_fixed']}")
    
    if total_stats['files_processed'] > 0:
        print("\n✅ データクレンジングが正常に完了しました")
        print("\n次のステップ:")
        print("1. cleaned_*.csv ファイルを確認")
        print("2. 問題がなければ元のファイルを置換")
        print("3. 統合システムの実装を開始")
    else:
        print("\n❌ データクレンジングが完了しませんでした")
    
    print("\n=== データクレンジング完了 ===")

if __name__ == "__main__":
    main()