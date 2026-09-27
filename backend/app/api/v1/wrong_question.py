from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.camel_case import convert_keys
from app.models.user import User

router = APIRouter()


@router.get("/list")
async def list_wrong_questions(
    exam_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    skip: int = 0, limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取错题列表"""
    return convert_keys({"total": 0, "items": []})


@router.get("/analysis/{exam_id}")
async def get_analysis(
    exam_id: int,
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取错因分析"""
    return convert_keys({
        "exam_id": exam_id, "subject_id": subject_id,
        "analysis": {"total_wrong": 0, "wrong_rate": 0, "common_reasons": []}
    })


@router.get("/book/{student_id}")
async def get_wrong_book(
    student_id: int,
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学生错题本"""
    return convert_keys({"student_id": student_id, "subject_id": subject_id, "total": 0, "items": []})


@router.post("/collect")
async def collect_wrong_question(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """收集错题"""
    return convert_keys({"success": True, "message": "错题收集成功"})