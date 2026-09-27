from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.models.user import User, Student, Grade, Class
from app.models.exam import Subject
from app.schemas.user import (
    UserCreate, UserUpdate,
    StudentCreate, StudentUpdate, StudentBatchCreate,
    TeacherCreate, TeacherUpdate, TeacherBatchCreate
)
from app.core.security import get_password_hash


class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_users(self, skip: int = 0, limit: int = 20) -> List[User]:
        """获取用户列表"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户详情"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        existing = self.get_user_by_username(user_data.username)
        if existing:
            raise ValueError("用户名已存在")
        
        user = User(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            real_name=user_data.real_name,
            role=user_data.role,
            phone=user_data.phone,
            email=user_data.email
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """更新用户"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id: int):
        """删除用户"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        self.db.delete(user)
        self.db.commit()

    # 学生档案
    def list_students(
        self,
        grade_id: Optional[int] = None,
        class_id: Optional[int] = None,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Student]:
        query = self.db.query(Student).options(joinedload(Student.grade), joinedload(Student.class_))
        if grade_id:
            query = query.filter(Student.grade_id == grade_id)
        if class_id:
            query = query.filter(Student.class_id == class_id)
        if keyword:
            query = query.filter(
                (Student.real_name.contains(keyword)) | (Student.student_no.contains(keyword))
            )
        return query.order_by(Student.student_no).offset(skip).limit(limit).all()

    def count_students(
        self,
        grade_id: Optional[int] = None,
        class_id: Optional[int] = None,
        keyword: Optional[str] = None
    ) -> int:
        query = self.db.query(Student)
        if grade_id:
            query = query.filter(Student.grade_id == grade_id)
        if class_id:
            query = query.filter(Student.class_id == class_id)
        if keyword:
            query = query.filter(
                (Student.real_name.contains(keyword)) | (Student.student_no.contains(keyword))
            )
        return query.count()

    def get_student(self, student_id: int) -> Optional[Student]:
        return self.db.query(Student).options(joinedload(Student.grade), joinedload(Student.class_)).filter(Student.id == student_id).first()

    def get_student_by_no(self, student_no: str) -> Optional[Student]:
        return self.db.query(Student).filter(Student.student_no == student_no).first()

    def create_student(self, data: StudentCreate) -> Student:
        existing = self.get_student_by_no(data.student_no)
        if existing:
            raise ValueError("学号已存在")
        student = Student(**data.model_dump())
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def batch_create_students(self, items: List[StudentBatchCreate]) -> dict:
        """批量创建学生，逐条使用 SAVEPOINT，单条失败不影响其他记录"""
        success = []
        failed = []
        for idx, data in enumerate(items):
            sp = self.db.begin_nested()
            try:
                existing = self.get_student_by_no(data.student_no)
                if existing:
                    raise ValueError(f"学号 {data.student_no} 已存在")
                student = Student(**data.model_dump())
                self.db.add(student)
                self.db.flush()
                success.append(student)
                sp.commit()
            except Exception as e:
                sp.rollback()
                failed.append({
                    "index": idx,
                    "student_no": data.student_no,
                    "real_name": data.real_name,
                    "error": str(e),
                })
        self.db.commit()
        return {"success": success, "failed": failed}

    def update_student(self, student_id: int, data: StudentUpdate) -> Student:
        student = self.get_student(student_id)
        if not student:
            raise ValueError("学生不存在")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(student, field, value)
        self.db.commit()
        self.db.refresh(student)
        return student

    def delete_student(self, student_id: int):
        student = self.get_student(student_id)
        if not student:
            raise ValueError("学生不存在")
        self.db.delete(student)
        self.db.commit()

    # 教师档案
    def list_teachers(
        self,
        subject_id: Optional[int] = None,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        query = self.db.query(User).options(joinedload(User.grade), joinedload(User.class_), joinedload(User.subject)).filter(User.role == "teacher")
        if subject_id:
            query = query.filter(User.subject_id == subject_id)
        if keyword:
            query = query.filter(
                (User.real_name.contains(keyword)) | (User.username.contains(keyword))
            )
        return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    def count_teachers(
        self,
        subject_id: Optional[int] = None,
        keyword: Optional[str] = None
    ) -> int:
        query = self.db.query(User).filter(User.role == "teacher")
        if subject_id:
            query = query.filter(User.subject_id == subject_id)
        if keyword:
            query = query.filter(
                (User.real_name.contains(keyword)) | (User.username.contains(keyword))
            )
        return query.count()

    def get_teacher(self, teacher_id: int) -> Optional[User]:
        return self.db.query(User).options(joinedload(User.grade), joinedload(User.class_), joinedload(User.subject)).filter(User.id == teacher_id, User.role == "teacher").first()

    def create_teacher(self, data: TeacherCreate) -> User:
        existing = self.get_user_by_username(data.username)
        if existing:
            raise ValueError("用户名已存在")
        teacher = User(
            username=data.username,
            password_hash=get_password_hash(data.password),
            real_name=data.real_name,
            role="teacher",
            phone=data.phone,
            email=data.email,
            grade_id=data.grade_id,
            class_id=data.class_id,
            subject_id=data.subject_id,
            status=data.status or 1
        )
        self.db.add(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def batch_create_teachers(self, items: List[TeacherBatchCreate]) -> dict:
        """批量创建教师，逐条使用 SAVEPOINT，单条失败不影响其他记录"""
        success = []
        failed = []
        for idx, data in enumerate(items):
            sp = self.db.begin_nested()
            try:
                existing = self.get_user_by_username(data.username)
                if existing:
                    raise ValueError(f"用户名 {data.username} 已存在")
                teacher = User(
                    username=data.username,
                    password_hash=get_password_hash(data.password or "123456"),
                    real_name=data.real_name,
                    role="teacher",
                    phone=data.phone,
                    email=data.email,
                    grade_id=data.grade_id,
                    class_id=data.class_id,
                    subject_id=data.subject_id,
                    status=data.status or 1
                )
                self.db.add(teacher)
                self.db.flush()
                success.append(teacher)
                sp.commit()
            except Exception as e:
                sp.rollback()
                failed.append({
                    "index": idx,
                    "username": data.username,
                    "real_name": data.real_name,
                    "error": str(e),
                })
        self.db.commit()
        return {"success": success, "failed": failed}

    def update_teacher(self, teacher_id: int, data: TeacherUpdate) -> User:
        teacher = self.get_teacher(teacher_id)
        if not teacher:
            raise ValueError("教师不存在")
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data.pop("password")
        for field, value in update_data.items():
            setattr(teacher, field, value)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def delete_teacher(self, teacher_id: int):
        teacher = self.get_teacher(teacher_id)
        if not teacher:
            raise ValueError("教师不存在")
        self.db.delete(teacher)
        self.db.commit()
