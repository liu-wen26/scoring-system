from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple

from app.models.exam import Exam, Subject, ExamSubject
from app.schemas.exam import ExamCreate, ExamUpdate, ExamResponse, SubjectProgress


class ExamService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_exams(
        self,
        status: Optional[str] = None,
        exam_type: Optional[str] = None,
        grade: Optional[str] = None,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        allowed_grades: Optional[List[str]] = None
    ) -> Tuple[int, List[ExamResponse]]:
        """获取考试列表"""
        query = self.db.query(Exam)

        if status:
            query = query.filter(Exam.status == status)
        if exam_type:
            query = query.filter(Exam.exam_type == exam_type)
        if grade:
            query = query.filter(Exam.grade == grade)
        elif allowed_grades:
            query = query.filter(Exam.grade.in_(allowed_grades))
        if keyword:
            query = query.filter(Exam.exam_name.contains(keyword))
        
        total = query.count()
        exams = query.order_by(Exam.created_at.desc()).offset(skip).limit(limit).all()
        
        return total, [self._to_response(exam) for exam in exams]
    
    def get_exam(self, exam_id: int) -> Optional[ExamResponse]:
        """获取考试详情"""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if exam:
            return self._to_response(exam)
        return None
    
    def create_exam(self, exam_data: ExamCreate, user_id: int) -> ExamResponse:
        """创建考试"""
        # 计算总分（各科目分数之和）
        total_score = exam_data.total_score
        subject_scores = exam_data.subject_scores or []
        if subject_scores:
            total_score = sum(s.total_score for s in subject_scores)

        exam = Exam(
            exam_name=exam_data.exam_name,
            exam_type=exam_data.exam_type,
            exam_level=exam_data.exam_level,
            grade=exam_data.grade,
            start_time=exam_data.start_time,
            end_time=exam_data.end_time,
            description=exam_data.description,
            total_score=total_score,
            total_students=exam_data.total_students,
            created_by=user_id
        )
        
        self.db.add(exam)
        self.db.flush()
        
        # 创建考试科目关联
        if subject_scores:
            for ss in subject_scores:
                exam_subject = ExamSubject(
                    exam_id=exam.id,
                    subject_id=ss.subject_id,
                    total_score=ss.total_score
                )
                self.db.add(exam_subject)
        elif exam_data.subject_ids:
            for subject_id in exam_data.subject_ids:
                exam_subject = ExamSubject(
                    exam_id=exam.id,
                    subject_id=subject_id,
                    total_score=exam_data.total_score
                )
                self.db.add(exam_subject)
        
        self.db.commit()
        self.db.refresh(exam)
        
        return self._to_response(exam)
    
    def update_exam(self, exam_id: int, exam_data: ExamUpdate) -> ExamResponse:
        """更新考试"""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise ValueError("考试不存在")
        
        update_data = exam_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(exam, field, value)
        
        self.db.commit()
        self.db.refresh(exam)
        
        return self._to_response(exam)
    
    def delete_exam(self, exam_id: int):
        """删除考试"""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise ValueError("考试不存在")
        
        self.db.delete(exam)
        self.db.commit()
    
    def update_status(self, exam_id: int, status: str) -> ExamResponse:
        """更新考试状态"""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise ValueError("考试不存在")
        
        exam.status = status
        self.db.commit()
        self.db.refresh(exam)
        
        return self._to_response(exam)
    
    def _to_response(self, exam: Exam) -> ExamResponse:
        """转换为响应模型"""
        subjects = []
        for es in exam.subjects:
            subject = es.subject
            if not subject:
                continue
            progress = 0
            if es.scanned_count > 0:
                progress = round((es.marked_count / es.scanned_count) * 100, 2)

            subjects.append(SubjectProgress(
                subject_id=subject.id,
                subject_name=subject.subject_name,
                status=es.status,
                total_score=es.total_score,
                scanned_count=es.scanned_count,
                marked_count=es.marked_count,
                progress=progress
            ))
        
        grade_id = getattr(exam, 'grade_id', None)
        if grade_id is None:
            from app.models.user import Grade
            g = self.db.query(Grade).filter(Grade.grade_name == exam.grade).first()
            grade_id = g.id if g else 0

        return ExamResponse(
            id=exam.id,
            exam_name=exam.exam_name,
            exam_type=exam.exam_type,
            exam_level=exam.exam_level,
            grade_id=grade_id,
            grade=exam.grade,
            start_time=exam.start_time,
            end_time=exam.end_time,
            description=exam.description,
            total_score=exam.total_score,
            total_students=exam.total_students,
            status=exam.status,
            subjects=subjects,
            created_at=exam.created_at,
            updated_at=exam.updated_at
        )
