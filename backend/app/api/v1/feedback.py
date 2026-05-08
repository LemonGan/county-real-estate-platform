"""
灵山公交留言反馈接口
"""
import json
import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["反馈"])

# 数据存储路径
DATA_DIR = Path(__file__).parent.parent.parent / "data"
FEEDBACK_FILE = DATA_DIR / "feedback.json"

class FeedbackCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="留言内容")
    contact: str = Field("", max_length=100, description="联系方式")
    source: str = Field("lingshan-bus", description="来源")

class FeedbackResponse(BaseModel):
    ok: bool
    message: str

def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK_FILE.exists():
        FEEDBACK_FILE.write_text("[]", encoding="utf-8")

def _load_feedback():
    _ensure_data_dir()
    try:
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except:
        return []

def _save_feedback(items):
    FEEDBACK_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(data: FeedbackCreate):
    """提交留言反馈"""
    feedbacks = _load_feedback()
    feedbacks.append({
        "id": len(feedbacks) + 1,
        "content": data.content,
        "contact": data.contact,
        "source": data.source,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    _save_feedback(feedbacks)
    return FeedbackResponse(ok=True, message="提交成功")
