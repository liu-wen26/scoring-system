from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.core.database import Base


class WrongQuestion(Base):
    __tablename__ = "wrong_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    question_num = Column(Integer, nullable=False)
    question_type = Column(String(20), nullable=False)
    correct_answer = Column(Text)
    student_answer = Column(Text)
    wrong_reason = Column(String(200))
    score = Column(Numeric(5, 2))
    created_at = Column(DateTime, server_default=func.now())
