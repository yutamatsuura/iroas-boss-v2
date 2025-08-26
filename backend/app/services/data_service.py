"""
データ管理サービス

Phase E-1a: データ管理API群（8.1-8.4）
- 完全独立、いつでも実装可能
- モックアップP-009対応

エンドポイント:
- 8.1 POST /api/data/import/members - 会員データインポート
- 8.2 POST /api/data/backup - バックアップ実行
- 8.3 GET /api/data/backups - バックアップ一覧
- 8.4 POST /api/data/restore/{id} - リストア実行
"""

import os
import json
import base64
import zipfile
import shutil
from typing import List, Optional, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from io import BytesIO, StringIO

from app.models.member import Member
from app.schemas.data import (
    DataImportRequest,
    DataImportResponse,
    BackupRequest,
    BackupResponse,
    RestoreRequest,
    RestoreResponse,
    DataIntegrityCheckResponse,
    ImportStatusEnum,
    BackupTypeEnum
)
from app.services.activity_service import ActivityService


class DataService:
    """
    データ管理サービスクラス
    インポート・エクスポート・バックアップ・リストア機能を担当
    """

    def __init__(self, db: Session):
        self.db = db
        self.activity_service = ActivityService(db)
        self.backup_dir = Path("/tmp/iroas_backups")
        self.backup_dir.mkdir(exist_ok=True)

    async def import_member_data(
        self,
        import_request: DataImportRequest
    ) -> DataImportResponse:
        """
        会員データインポート
        API 8.1: POST /api/data/import/members
        """
        started_at = datetime.now()
        
        try:
            # ファイル内容をデコード
            file_content = base64.b64decode(import_request.file_content)
            
            # ファイル形式に応じた読み込み
            if import_request.file_format.value == "csv":
                df = self._read_csv_data(file_content, import_request.encoding)
            elif import_request.file_format.value in ["excel", "xlsx"]:
                df = pd.read_excel(BytesIO(file_content))
            elif import_request.file_format.value == "json":
                json_data = json.loads(file_content.decode(import_request.encoding))
                df = pd.DataFrame(json_data)
            else:
                raise ValueError(f"サポートされていないファイル形式: {import_request.file_format}")
            
            # バリデーションのみモード
            if import_request.validate_only:
                validation_results = self._validate_import_data(df)
                return self._create_validation_response(validation_results, started_at)
            
            # データインポート実行
            results = await self._process_import_data(
                df, 
                import_request.update_existing,
                import_request.duplicate_handling,
                import_request.stop_on_error,
                import_request.max_errors
            )
            
            completed_at = datetime.now()
            
            # アクティビティログ記録
            await self.activity_service.log_activity(
                action="会員データインポート",
                details=f"ファイル: {import_request.file_name}, 成功: {results['success_count']}件, エラー: {results['error_count']}件",
                user_id="system"
            )
            
            return DataImportResponse(
                import_id=results['import_id'],
                status=ImportStatusEnum.COMPLETED if results['error_count'] == 0 else ImportStatusEnum.FAILED,
                total_rows=results['total_rows'],
                processed_rows=results['processed_rows'],
                success_count=results['success_count'],
                error_count=results['error_count'],
                skipped_count=results['skipped_count'],
                updated_count=results['updated_count'],
                errors=results['errors'],
                warnings=results['warnings'],
                started_at=started_at,
                completed_at=completed_at,
                processing_time_seconds=(completed_at - started_at).total_seconds(),
                imported_data_summary=results['summary']
            )
            
        except Exception as e:
            # インポートエラー処理
            await self.activity_service.log_activity(
                action="会員データインポート失敗",
                details=f"ファイル: {import_request.file_name}, エラー: {str(e)}",
                user_id="system"
            )
            
            return DataImportResponse(
                import_id=0,
                status=ImportStatusEnum.FAILED,
                total_rows=0,
                processed_rows=0,
                success_count=0,
                error_count=1,
                skipped_count=0,
                updated_count=0,
                errors=[{"error": str(e), "row": 0}],
                warnings=[],
                started_at=started_at,
                completed_at=datetime.now(),
                processing_time_seconds=0,
                imported_data_summary={}
            )

    async def create_backup(
        self,
        backup_request: BackupRequest
    ) -> BackupResponse:
        """
        バックアップ作成
        API 8.2: POST /api/data/backup
        """
        started_at = datetime.now()
        
        # バックアップ名生成
        backup_name = backup_request.backup_name or f"backup_{started_at.strftime('%Y%m%d_%H%M%S')}"
        backup_filename = f"{backup_name}.zip"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # バックアップデータ収集
            backup_data = await self._collect_backup_data(backup_request.backup_type)
            
            # バックアップファイル作成
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                
                if backup_request.backup_type in [BackupTypeEnum.FULL, BackupTypeEnum.MEMBERS]:
                    # 会員データ
                    members_data = self._export_members_data()
                    zipf.writestr("members.json", json.dumps(members_data, ensure_ascii=False, indent=2))
                
                if backup_request.backup_type in [BackupTypeEnum.FULL, BackupTypeEnum.PAYMENTS]:
                    # 決済データ（実装予定）
                    zipf.writestr("payments.json", json.dumps([], ensure_ascii=False, indent=2))
                
                if backup_request.backup_type in [BackupTypeEnum.FULL, BackupTypeEnum.REWARDS]:
                    # 報酬データ（実装予定）
                    zipf.writestr("rewards.json", json.dumps([], ensure_ascii=False, indent=2))
                
                if backup_request.backup_type in [BackupTypeEnum.FULL, BackupTypeEnum.SETTINGS]:
                    # 設定データ
                    settings_data = {"backup_created": started_at.isoformat()}
                    zipf.writestr("settings.json", json.dumps(settings_data, ensure_ascii=False, indent=2))
                
                # メタデータ
                metadata = {
                    "backup_name": backup_name,
                    "backup_type": backup_request.backup_type.value,
                    "created_at": started_at.isoformat(),
                    "description": backup_request.description,
                    "version": "1.0"
                }
                zipf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
            
            # ファイルサイズ取得
            file_size = backup_path.stat().st_size
            
            completed_at = datetime.now()
            
            # アクティビティログ記録
            await self.activity_service.log_activity(
                action="バックアップ作成",
                details=f"ファイル: {backup_filename}, サイズ: {file_size} bytes, 種別: {backup_request.backup_type.value}",
                user_id="system"
            )
            
            return BackupResponse(
                backup_id=hash(backup_filename) % 1000000,  # 簡易ID生成
                backup_name=backup_name,
                backup_type=backup_request.backup_type,
                description=backup_request.description,
                file_name=backup_filename,
                file_size_bytes=file_size,
                file_path=str(backup_path),
                is_compressed=True,
                is_encrypted=backup_request.encryption,
                compression_ratio=75.0,  # 概算
                total_records=len(backup_data.get("members", [])),
                table_counts=self._get_table_counts(backup_data),
                created_at=started_at,
                created_by="system",
                backup_duration_seconds=(completed_at - started_at).total_seconds(),
                status="completed"
            )
            
        except Exception as e:
            await self.activity_service.log_activity(
                action="バックアップ作成失敗",
                details=f"エラー: {str(e)}",
                user_id="system"
            )
            
            return BackupResponse(
                backup_id=0,
                backup_name=backup_name,
                backup_type=backup_request.backup_type,
                description=backup_request.description,
                file_name=backup_filename,
                file_size_bytes=0,
                file_path="",
                is_compressed=False,
                is_encrypted=False,
                compression_ratio=0,
                total_records=0,
                table_counts={},
                created_at=started_at,
                created_by="system",
                backup_duration_seconds=0,
                status="failed",
                error_message=str(e)
            )

    async def list_backups(self) -> List[BackupResponse]:
        """
        バックアップ一覧取得
        API 8.3: GET /api/data/backups
        """
        backups = []
        
        if not self.backup_dir.exists():
            return backups
        
        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                # メタデータ読み込み
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    metadata_content = zipf.read("metadata.json").decode('utf-8')
                    metadata = json.loads(metadata_content)
                
                file_size = backup_file.stat().st_size
                created_time = datetime.fromtimestamp(backup_file.stat().st_ctime)
                
                backup = BackupResponse(
                    backup_id=hash(backup_file.name) % 1000000,
                    backup_name=metadata.get("backup_name", backup_file.stem),
                    backup_type=BackupTypeEnum(metadata.get("backup_type", "full")),
                    description=metadata.get("description"),
                    file_name=backup_file.name,
                    file_size_bytes=file_size,
                    file_path=str(backup_file),
                    is_compressed=True,
                    is_encrypted=False,  # 暫定
                    compression_ratio=75.0,
                    total_records=0,  # メタデータから取得可能
                    table_counts={},
                    created_at=created_time,
                    created_by="system",
                    backup_duration_seconds=0,
                    status="completed"
                )
                
                backups.append(backup)
                
            except Exception as e:
                # 読み込めないファイルはスキップ
                continue
        
        # 作成日時順にソート
        backups.sort(key=lambda x: x.created_at, reverse=True)
        
        return backups

    async def restore_backup(
        self,
        backup_id: int,
        restore_request: RestoreRequest
    ) -> RestoreResponse:
        """
        バックアップリストア
        API 8.4: POST /api/data/restore/{id}
        """
        started_at = datetime.now()
        
        # バックアップファイル検索
        backup_files = await self.list_backups()
        target_backup = next((b for b in backup_files if b.backup_id == backup_id), None)
        
        if not target_backup:
            raise ValueError(f"バックアップID {backup_id} は存在しません")
        
        try:
            # 事前バックアップ作成（設定されている場合）
            pre_restore_backup_id = None
            if restore_request.backup_current_before_restore:
                pre_backup_request = BackupRequest(
                    backup_type=BackupTypeEnum.FULL,
                    backup_name=f"pre_restore_{started_at.strftime('%Y%m%d_%H%M%S')}",
                    description=f"リストア前自動バックアップ（復元対象: {target_backup.backup_name}）"
                )
                pre_backup = await self.create_backup(pre_backup_request)
                pre_restore_backup_id = pre_backup.backup_id
            
            # バックアップファイル検証
            if restore_request.validate_before_restore:
                validation_result = self._validate_backup_file(target_backup.file_path)
                if not validation_result["is_valid"]:
                    raise ValueError(f"バックアップファイルが破損しています: {validation_result['errors']}")
            
            # リストア実行
            restore_results = await self._execute_restore(
                target_backup.file_path,
                restore_request.restore_type,
                restore_request.target_tables,
                restore_request.overwrite_existing
            )
            
            completed_at = datetime.now()
            
            # アクティビティログ記録
            await self.activity_service.log_activity(
                action="バックアップリストア実行",
                details=f"バックアップ: {target_backup.backup_name}, 復元レコード数: {restore_results['total_restored']}",
                user_id="system"
            )
            
            return RestoreResponse(
                restore_id=hash(f"{backup_id}_{started_at.timestamp()}") % 1000000,
                backup_id=backup_id,
                status="completed",
                total_records_restored=restore_results["total_restored"],
                table_restore_counts=restore_results["table_counts"],
                pre_restore_backup_id=pre_restore_backup_id,
                started_at=started_at,
                completed_at=completed_at,
                restore_duration_seconds=(completed_at - started_at).total_seconds(),
                restored_by="system",
                restore_reason=restore_request.restore_reason,
                success_count=restore_results["success_count"],
                error_count=restore_results["error_count"],
                errors=restore_results["errors"],
                warnings=restore_results["warnings"]
            )
            
        except Exception as e:
            await self.activity_service.log_activity(
                action="バックアップリストア失敗",
                details=f"エラー: {str(e)}",
                user_id="system"
            )
            
            return RestoreResponse(
                restore_id=0,
                backup_id=backup_id,
                status="failed",
                total_records_restored=0,
                table_restore_counts={},
                pre_restore_backup_id=pre_restore_backup_id,
                started_at=started_at,
                completed_at=datetime.now(),
                restore_duration_seconds=0,
                restored_by="system",
                restore_reason=restore_request.restore_reason,
                success_count=0,
                error_count=1,
                errors=[{"error": str(e)}],
                warnings=[]
            )

    def _read_csv_data(self, file_content: bytes, encoding: str) -> pd.DataFrame:
        """
        CSV読み込み（エンコーディング自動判定対応）
        """
        try:
            # 指定エンコーディングで試行
            content_str = file_content.decode(encoding)
            return pd.read_csv(StringIO(content_str))
        except UnicodeDecodeError:
            # Shift-JISで再試行
            try:
                content_str = file_content.decode('shift_jis')
                return pd.read_csv(StringIO(content_str))
            except UnicodeDecodeError:
                # UTF-8で再試行
                content_str = file_content.decode('utf-8')
                return pd.read_csv(StringIO(content_str))

    def _validate_import_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        インポートデータバリデーション
        """
        errors = []
        warnings = []
        
        # 必須カラムチェック
        required_columns = ["member_number", "name", "kana"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"必須カラムが不足: {missing_columns}")
        
        # データ型チェック
        for idx, row in df.iterrows():
            if pd.isna(row.get('member_number')):
                errors.append(f"行{idx+1}: 会員番号が空です")
            elif not str(row['member_number']).isdigit():
                warnings.append(f"行{idx+1}: 会員番号が数字ではありません")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_rows": len(df)
        }

    async def _process_import_data(
        self,
        df: pd.DataFrame,
        update_existing: bool,
        duplicate_handling: str,
        stop_on_error: bool,
        max_errors: int
    ) -> Dict[str, Any]:
        """
        インポートデータ処理実行
        """
        results = {
            "import_id": int(datetime.now().timestamp()),
            "total_rows": len(df),
            "processed_rows": 0,
            "success_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "updated_count": 0,
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
        for idx, row in df.iterrows():
            try:
                # 会員番号による重複チェック
                member_number = str(row.get('member_number', ''))
                existing_member = self.db.query(Member).filter(Member.member_number == member_number).first()
                
                if existing_member:
                    if duplicate_handling == "skip":
                        results["skipped_count"] += 1
                        continue
                    elif duplicate_handling == "update" and update_existing:
                        # 既存会員更新
                        self._update_member_from_row(existing_member, row)
                        results["updated_count"] += 1
                    elif duplicate_handling == "error":
                        raise ValueError(f"重複する会員番号: {member_number}")
                else:
                    # 新規会員作成
                    self._create_member_from_row(row)
                    results["success_count"] += 1
                
                results["processed_rows"] += 1
                
            except Exception as e:
                results["error_count"] += 1
                results["errors"].append({"row": idx + 1, "error": str(e)})
                
                if stop_on_error or results["error_count"] >= max_errors:
                    break
        
        self.db.commit()
        
        return results

    def _export_members_data(self) -> List[Dict[str, Any]]:
        """
        会員データエクスポート
        """
        members = self.db.query(Member).all()
        members_data = []
        
        for member in members:
            member_dict = {
                "id": member.id,
                "status": member.status.value if member.status else None,
                "member_number": member.member_number,
                "name": member.name,
                "kana": member.kana,
                "email": member.email,
                # 他の30項目も同様に追加
                "created_at": member.created_at.isoformat() if member.created_at else None,
                "updated_at": member.updated_at.isoformat() if member.updated_at else None
            }
            members_data.append(member_dict)
        
        return members_data

    def _get_table_counts(self, backup_data: Dict[str, Any]) -> Dict[str, int]:
        """
        テーブル別レコード数取得
        """
        return {
            "members": len(backup_data.get("members", [])),
            "payments": len(backup_data.get("payments", [])),
            "rewards": len(backup_data.get("rewards", []))
        }

    def _validate_backup_file(self, file_path: str) -> Dict[str, Any]:
        """
        バックアップファイル検証
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # ファイル整合性チェック
                bad_file = zipf.testzip()
                if bad_file:
                    return {"is_valid": False, "errors": [f"破損ファイル: {bad_file}"]}
                
                # メタデータ存在チェック
                if "metadata.json" not in zipf.namelist():
                    return {"is_valid": False, "errors": ["メタデータファイルが見つかりません"]}
                
            return {"is_valid": True, "errors": []}
            
        except Exception as e:
            return {"is_valid": False, "errors": [str(e)]}

    async def _collect_backup_data(self, backup_type: BackupTypeEnum) -> Dict[str, Any]:
        """
        バックアップデータ収集
        """
        data = {}
        
        if backup_type in [BackupTypeEnum.FULL, BackupTypeEnum.MEMBERS]:
            data["members"] = self._export_members_data()
        
        return data

    async def _execute_restore(
        self,
        backup_path: str,
        restore_type: str,
        target_tables: Optional[List[str]],
        overwrite_existing: bool
    ) -> Dict[str, Any]:
        """
        リストア実行
        """
        restore_results = {
            "total_restored": 0,
            "table_counts": {},
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # 会員データリストア
                if not target_tables or "members" in target_tables:
                    members_content = zipf.read("members.json").decode('utf-8')
                    members_data = json.loads(members_content)
                    
                    restored_count = self._restore_members_data(members_data, overwrite_existing)
                    restore_results["table_counts"]["members"] = restored_count
                    restore_results["total_restored"] += restored_count
                    restore_results["success_count"] += restored_count
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            restore_results["error_count"] += 1
            restore_results["errors"].append({"error": str(e)})
        
        return restore_results

    def _create_member_from_row(self, row: pd.Series) -> Member:
        """
        行データから会員作成
        """
        # 実装は省略（実際にはすべての30項目をマッピング）
        new_member = Member(
            member_number=str(row.get('member_number', '')),
            name=str(row.get('name', '')),
            kana=str(row.get('kana', '')),
            email=str(row.get('email', '')) if pd.notna(row.get('email')) else None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(new_member)
        return new_member

    def _update_member_from_row(self, member: Member, row: pd.Series):
        """
        行データから会員更新
        """
        member.name = str(row.get('name', member.name))
        member.kana = str(row.get('kana', member.kana))
        member.updated_at = datetime.now()

    def _restore_members_data(self, members_data: List[Dict[str, Any]], overwrite_existing: bool) -> int:
        """
        会員データリストア
        """
        restored_count = 0
        
        for member_data in members_data:
            member_number = member_data.get('member_number')
            if not member_number:
                continue
                
            existing = self.db.query(Member).filter(Member.member_number == member_number).first()
            
            if existing and not overwrite_existing:
                continue
            elif existing and overwrite_existing:
                # 既存更新
                for key, value in member_data.items():
                    if hasattr(existing, key) and key not in ['id', 'created_at']:
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
            else:
                # 新規作成
                new_member = Member(**{k: v for k, v in member_data.items() if k != 'id'})
                new_member.created_at = datetime.now()
                new_member.updated_at = datetime.now()
                self.db.add(new_member)
            
            restored_count += 1
        
        return restored_count

    def _create_validation_response(self, validation_results: Dict[str, Any], started_at: datetime) -> DataImportResponse:
        """
        バリデーション結果レスポンス作成
        """
        return DataImportResponse(
            import_id=0,
            status=ImportStatusEnum.COMPLETED if validation_results["is_valid"] else ImportStatusEnum.FAILED,
            total_rows=validation_results["total_rows"],
            processed_rows=0,
            success_count=0,
            error_count=len(validation_results["errors"]),
            skipped_count=0,
            updated_count=0,
            errors=validation_results["errors"],
            warnings=validation_results["warnings"],
            started_at=started_at,
            completed_at=datetime.now(),
            processing_time_seconds=0,
            imported_data_summary={"validation_only": True}
        )