from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import (
    get_current_user, verify_password, get_password_hash,
    create_access_token
)
from app.core.camel_case import convert_keys
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin, TokenResponse,
    StudentCreate, StudentUpdate, StudentBatchCreate,
    TeacherCreate, TeacherUpdate, TeacherBatchCreate
)
from app.models.user import User
from app.services.user_service import UserService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """用户登录"""
    service = UserService(db)
    user = service.get_user_by_username(login_data.username)
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if user.status != 1:
        raise HTTPException(status_code=403, detail="用户已被禁用")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表"""
    service = UserService(db)
    return service.get_users(skip=skip, limit=limit)


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户"""
    service = UserService(db)
    return service.create_user(user_data)


# 学生档案接口（放在泛型 /{user_id} 之前，避免路由冲突）
@router.get("/students")
async def list_students(
    grade_id: Optional[int] = Query(None, alias="gradeId"),
    class_id: Optional[int] = Query(None, alias="classId"),
    keyword: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """学生档案列表"""
    service = UserService(db)
    items = service.list_students(grade_id, class_id, keyword, skip, limit)
    total = service.count_students(grade_id, class_id, keyword)
    return convert_keys({
        "items": [
            {
                "id": s.id,
                "student_no": s.student_no,
                "real_name": s.real_name,
                "gender": s.gender,
                "grade_id": s.grade_id,
                "class_id": s.class_id,
                "grade_name": s.grade_name,
                "class_name": s.class_name,
                "status": s.status,
            }
            for s in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    })


@router.get("/students/{student_id}")
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """学生详情"""
    service = UserService(db)
    s = service.get_student(student_id)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    return convert_keys({
        "id": s.id,
        "student_no": s.student_no,
        "real_name": s.real_name,
        "gender": s.gender,
        "grade_id": s.grade_id,
        "class_id": s.class_id,
        "grade_name": s.grade_name,
        "class_name": s.class_name,
        "status": s.status,
    })


@router.post("/students")
async def create_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """新增学生"""
    service = UserService(db)
    try:
        s = service.create_student(data)
        return convert_keys({
            "id": s.id,
            "student_no": s.student_no,
            "real_name": s.real_name,
            "gender": s.gender,
            "grade_id": s.grade_id,
            "class_id": s.class_id,
            "status": s.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/students/batch")
async def batch_create_students(
    data: List[StudentBatchCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量新增学生"""
    service = UserService(db)
    try:
        result = service.batch_create_students(data)
        return convert_keys({
            "success_count": len(result["success"]),
            "failed_count": len(result["failed"]),
            "failed": result["failed"],
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/students/{student_id}")
async def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """编辑学生"""
    service = UserService(db)
    try:
        s = service.update_student(student_id, data)
        return convert_keys({
            "id": s.id,
            "student_no": s.student_no,
            "real_name": s.real_name,
            "gender": s.gender,
            "grade_id": s.grade_id,
            "class_id": s.class_id,
            "status": s.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除学生"""
    service = UserService(db)
    service.delete_student(student_id)
    return convert_keys({"message": "删除成功"})


# 教师档案接口
@router.get("/teachers")
async def list_teachers(
    subject_id: Optional[int] = Query(None, alias="subjectId"),
    keyword: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """教师档案列表"""
    service = UserService(db)
    items = service.list_teachers(subject_id, keyword, skip, limit)
    total = service.count_teachers(subject_id, keyword)
    return convert_keys({
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "real_name": u.real_name,
                "phone": u.phone,
                "email": u.email,
                "grade_id": u.grade_id,
                "class_id": u.class_id,
                "subject_id": u.subject_id,
                "grade_name": u.grade_name,
                "class_name": u.class_name,
                "subject_name": u.subject_name,
                "status": u.status,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    })


@router.get("/teachers/{teacher_id}")
async def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """教师详情"""
    service = UserService(db)
    u = service.get_teacher(teacher_id)
    if not u:
        raise HTTPException(status_code=404, detail="教师不存在")
    return convert_keys({
        "id": u.id,
        "username": u.username,
        "real_name": u.real_name,
        "phone": u.phone,
        "email": u.email,
        "grade_id": u.grade_id,
        "class_id": u.class_id,
        "subject_id": u.subject_id,
        "grade_name": u.grade_name,
        "class_name": u.class_name,
        "subject_name": u.subject_name,
        "status": u.status,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    })


@router.post("/teachers")
async def create_teacher(
    data: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """新增教师"""
    service = UserService(db)
    try:
        u = service.create_teacher(data)
        return convert_keys({
            "id": u.id,
            "username": u.username,
            "real_name": u.real_name,
            "phone": u.phone,
            "email": u.email,
            "grade_id": u.grade_id,
            "class_id": u.class_id,
            "subject_id": u.subject_id,
            "status": u.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/teachers/batch")
async def batch_create_teachers(
    data: List[TeacherBatchCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量新增教师"""
    service = UserService(db)
    try:
        result = service.batch_create_teachers(data)
        return convert_keys({
            "success_count": len(result["success"]),
            "failed_count": len(result["failed"]),
            "failed": result["failed"],
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/teachers/{teacher_id}")
async def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """编辑教师"""
    service = UserService(db)
    try:
        u = service.update_teacher(teacher_id, data)
        return convert_keys({
            "id": u.id,
            "username": u.username,
            "real_name": u.real_name,
            "phone": u.phone,
            "email": u.email,
            "grade_id": u.grade_id,
            "class_id": u.class_id,
            "subject_id": u.subject_id,
            "status": u.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/teachers/{teacher_id}")
async def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除教师"""
    service = UserService(db)
    service.delete_teacher(teacher_id)
    return convert_keys({"message": "删除成功"})


# 泛型用户路由必须放在最后，避免与 /students、/teachers 等具体路由冲突
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情"""
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息"""
    service = UserService(db)
    return service.update_user(user_id, user_data)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户"""
    service = UserService(db)
    service.delete_user(user_id)
    return {"message": "删除成功"}
