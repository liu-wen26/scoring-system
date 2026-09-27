from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String(100), nullable=False, index=True)
    exam_type = Column(String(20), nullable=False)
    exam_level = Column(String(20), nullable=False)
    grade_id = Column(Integer, default=0)
    grade = Column(String(20), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="draft")
    description = Column(Text)
    total_score = Column(Integer, default=100)
    total_students = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    subjects = relationship("ExamSubject", back_populates="exam", cascade="all, delete-orphan")
    scan_batches = relationship("ScanBatch", back_populates="exam")
    scan_pages = relationship("ScanPage", back_populates="exam")


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(50), nullable=False)
    subject_code = Column(String(20))
    sort_order = Column(Integer, default=0)
    status = Column(Integer, default=1)
    grade_level = Column(Integer, default=0)  # 7/8/9 年级，0 表示通用
    
    scan_pages = relationship("ScanPage", back_populates="subject")


class ExamSubject(Base):
    __tablename__ = "exam_subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    total_score = Column(Integer, default=100)
    choice_count = Column(Integer, default=0)
    choice_score = Column(Integer, default=0)
    subjective_count = Column(Integer, default=0)
    subjective_score = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    scanned_count = Column(Integer, default=0)
    marked_count = Column(Integer, default=0)
    
    exam = relationship("Exam", back_populates="subjects")
    subject = relationship("Subject")


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    question_no = Column(String(50), nullable=False)
    question_title = Column(String(200))
    question_content = Column(Text)
    knowledge_point = Column(String(200))
    ability = Column(String(200))
    score = Column(Numeric(5, 2), default=0)
    question_type = Column(String(20), default="subjective")
    sort_order = Column(Integer, default=0)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
