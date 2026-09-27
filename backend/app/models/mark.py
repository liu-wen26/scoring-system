from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MarkAllocation(Base):
    __tablename__ = "mark_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))  # 兼容旧数据/主负责人
    question_type = Column(String(20))
    start_num = Column(Integer)
    end_num = Column(Integer)
    total_papers = Column(Integer, default=0)
    marked_papers = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    
    # 扩展字段：支持多题号、多教师、批阅方式、分配方式
    question_nos = Column(JSON, default=list)  # ["31(1)", "31(2)"]
    user_ids = Column(JSON, default=list)      # [1, 2, 3]
    mark_mode = Column(String(20), default="single")   # single/batch/double
    allocation_mode = Column(String(20), default="efficiency")  # efficiency/balance/random


class MarkResult(Base):
    __tablename__ = "mark_results"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    scan_page_id = Column(Integer, ForeignKey("scan_pages.id"))
    
    choice_score = Column(Numeric(5, 2), default=0)
    subjective_score = Column(Numeric(5, 2), default=0)
    total_score = Column(Numeric(5, 2), default=0)
    
    choice_result = Column(JSON)
    subjective_result = Column(JSON)
    
    status = Column(String(20), default="pending")
    marked_by = Column(Integer, ForeignKey("users.id"))
    marked_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class MarkDetail(Base):
    __tablename__ = "mark_details"

    id = Column(Integer, primary_key=True, index=True)
    mark_result_id = Column(Integer, ForeignKey("mark_results.id"), index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    question_id = Column(Integer, ForeignKey("exam_questions.id"))
    score = Column(Numeric(5, 2), default=0)
    student_answer = Column(Text)
    status = Column(String(20), default="pending")
    marked_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())


class AIMarkConfig(Base):
    """AI 阅卷配置（按用户存储阿里云百炼 API-Key 等）"""
    __tablename__ = "ai_mark_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    provider = Column(String(20), default="bailian")
    api_key = Column(Text, nullable=False)
    model = Column(String(100), default="qwen-turbo")
    endpoint = Column(String(500), default="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AIMarkTask(Base):
    """AI 阅卷任务：针对某一题连续自动批改"""
    __tablename__ = "ai_mark_tasks"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    question_no = Column(String(50), nullable=False)

    question_content = Column(Text)
    standard_answer = Column(Text)
    scoring_criteria = Column(Text)

    total_limit = Column(Integer, default=0)  # 0 表示不限制，批改完该题全部试卷
    processed_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    status = Column(String(20), default="running")  # running / paused / completed / failed

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AIMarkLog(Base):
    """AI 阅卷单条评分记录"""
    __tablename__ = "ai_mark_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("ai_mark_tasks.id"), index=True, nullable=False)
    result_id = Column(Integer, ForeignKey("mark_results.id"), index=True)
    scan_page_id = Column(Integer, ForeignKey("scan_pages.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    question_no = Column(String(50), nullable=False)
    full_score = Column(Numeric(5, 2), default=0)
    ai_score = Column(Numeric(5, 2), default=0)
    ai_reason = Column(Text)
    status = Column(String(20), default="pending")  # pending / success / failed / skipped
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
