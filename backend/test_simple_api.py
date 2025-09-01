"""
簡単なAPIテスト
"""
import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Member

app = FastAPI()

@app.get("/test/members")
async def test_members(db: Session = Depends(get_db)):
    members = db.query(Member).limit(3).all()
    result = []
    for member in members:
        result.append({
            "member_number": member.member_number,
            "name": member.name,
            "status": str(member.status)
        })
    return {"count": len(result), "members": result}

@app.get("/test/health")
async def test_health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)