from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.camel_case import convert_keys
from app.schemas.exam import ExamCreate, ExamUpdate, ExamResponse, ExamListResponse
from app.models.user import User, Grade, Class, Student
from app.models.exam import Subject, ExamQuestion
from app.services.exam_service import ExamService
from app.services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=ExamListResponse)
async def list_exams(
    status: Optional[str] = Query(None, description="考试状态"),
    exam_type: Optional[str] = Query(None, description="考试类型"),
    grade: Optional[str] = Query(None, description="年级"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取考试列表"""
    service = ExamService(db)
    total, items = service.get_exams(
        status=status,
        exam_type=exam_type,
        grade=grade,
        keyword=keyword,
        skip=skip,
        limit=limit,
        allowed_grades=["七年级", "八年级", "九年级"]
    )
    return ExamListResponse(total=total, items=items)


@router.post("/", response_model=ExamResponse)
async def create_exam(
    exam_data: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建考试"""
    service = ExamService(db)
    return service.create_exam(exam_data, current_user.id)


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取考试详情"""
    service = ExamService(db)
    exam = service.get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    return exam


@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新考试信息"""
    service = ExamService(db)
    return service.update_exam(exam_id, exam_data)


@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除考试"""
    service = ExamService(db)
    service.delete_exam(exam_id)
    return {"message": "删除成功"}


@router.put("/{exam_id}/status")
async def update_exam_status(
    exam_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新考试状态"""
    service = ExamService(db)
    return service.update_status(exam_id, status)


@router.get("/meta/subjects")
async def list_subjects(
    grade_id: Optional[int] = Query(None, alias="gradeId"),
    grade_level: Optional[int] = Query(None, alias="gradeLevel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取科目列表（支持按年级筛选）"""
    query = db.query(Subject)
    if grade_id:
        # 通过 grade_id 找到对应的 grade_level
        g = db.query(Grade).filter(Grade.id == grade_id).first()
        if g:
            grade_level = g.grade_level
    if grade_level is not None:
        query = query.filter((Subject.grade_level == grade_level) | (Subject.grade_level == 0))
    else:
        query = query.filter(Subject.grade_level == 0)
    items = query.order_by(Subject.sort_order).all()
    return convert_keys([{"id": s.id, "subject_name": s.subject_name, "subject_code": s.subject_code, "grade_level": s.grade_level} for s in items])


@router.get("/meta/grades")
async def list_grades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取年级列表（仅保留七、八、九年级）"""
    items = db.query(Grade).filter(Grade.grade_level.in_([7, 8, 9])).order_by(Grade.grade_level).all()
    return convert_keys([{"id": g.id, "grade_name": g.grade_name, "grade_level": g.grade_level} for g in items])


@router.get("/meta/classes")
async def list_classes(
    grade_id: Optional[int] = Query(None, alias="gradeId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取班级列表（仅保留七、八、九年级）"""
    query = db.query(Class).filter(Class.grade_id.in_(
        db.query(Grade.id).filter(Grade.grade_level.in_([7, 8, 9]))
    ))
    if grade_id:
        query = query.filter(Class.grade_id == grade_id)
    items = query.order_by(Class.class_name).all()
    return convert_keys([{"id": c.id, "class_name": c.class_name, "grade_id": c.grade_id} for c in items])


@router.get("/meta/student-count")
async def get_student_count_by_grade(
    grade_id: Optional[int] = Query(None, alias="gradeId"),
    grade: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定年级的学生人数（关联学生档案）"""
    service = UserService(db)
    count = service.count_students(grade_id=grade_id)
    # 如果传了 grade 字符串，尝试通过 grade_name 查找
    if not count and grade:
        g = db.query(Grade).filter(Grade.grade_name == grade).first()
        if g:
            count = service.count_students(grade_id=g.id)
    return convert_keys({"count": count})


@router.get("/{exam_id}/questions")
async def list_exam_questions(
    exam_id: int,
    subject_id: Optional[int] = Query(None, alias="subjectId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取考试题目列表（用于 AI 阅卷时自动填充题目内容）"""
    query = db.query(ExamQuestion).filter(
        ExamQuestion.exam_id == exam_id,
        ExamQuestion.status == 1
    )
    if subject_id:
        query = query.filter(ExamQuestion.subject_id == subject_id)
    questions = query.order_by(ExamQuestion.sort_order, ExamQuestion.id).all()
    return convert_keys({
        "total": len(questions),
        "items": [{
            "id": q.id,
            "exam_id": q.exam_id,
            "subject_id": q.subject_id,
            "question_no": q.question_no,
            "question_title": q.question_title,
            "question_content": q.question_content,
            "knowledge_point": q.knowledge_point,
            "ability": q.ability,
            "score": float(q.score) if q.score else 0,
            "question_type": q.question_type,
            "sort_order": q.sort_order,
        } for q in questions]
    })
