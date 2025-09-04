#!/usr/bin/env python3
"""組織図API機能のみテスト用サーバー"""

from fastapi import FastAPI, HTTPException
from app.api.v1.organization_db_only import get_organization_tree_db_only
from app.schemas.organization import OrganizationTree
from typing import Optional

app = FastAPI(title="組織図テスト")

@app.get("/api/v1/organization/tree", response_model=OrganizationTree)
def get_organization_tree(
    member_id: Optional[str] = None,
    max_level: Optional[int] = 3,
    active_only: Optional[bool] = False
):
    """組織ツリー取得（テスト用）"""
    try:
        return get_organization_tree_db_only(member_id, max_level, active_only)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "組織図API テストサーバー"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)