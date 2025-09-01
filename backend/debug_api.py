"""
デバッグ用APIエンドポイント
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import json

app = FastAPI(title="Debug API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

class MemberCreate(BaseModel):
    member_number: str
    name: str
    kana: str
    email: str
    plan: str
    payment_method: str
    phone: str = None
    gender: str = None
    postal_code: str = None
    prefecture: str = None
    address2: str = None
    address3: str = None
    notes: str = None

@app.post("/api/v1/members/")
async def debug_create_member(request_data: dict):
    print(f"Raw request data: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    try:
        member = MemberCreate(**request_data)
        print(f"Validated data: {member.dict()}")
        return {"status": "success", "data": member.dict()}
    except ValidationError as e:
        print(f"Validation error: {e.errors()}")
        return {"status": "error", "errors": e.errors()}
    except Exception as e:
        print(f"Other error: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)