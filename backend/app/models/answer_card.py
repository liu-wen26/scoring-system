from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class AnswerCardTemplate(Base):
    __tablename__ = "answer_card_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False)
    template_code = Column(String(50), unique=True)
    template_type = Column(String(20), default='custom', index=True)
    grade_id = Column(Integer, index=True)
    subject_id = Column(Integer, index=True)
    width = Column(Integer, default=210)
    height = Column(Integer, default=297)
    config = Column(JSON)
    preview_url = Column(String(500))
    status = Column(Integer, default=1)
    created_by = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class AnswerCardConfig(Base):
    __tablename__ = "answer_card_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, index=True)
    subject_id = Column(Integer, index=True)
    template_id = Column(Integer)
    template_image = Column(Text)
    questions_config = Column(JSON)
    mark_points = Column(JSON)
    standard_answers = Column(JSON)
    regions = Column(JSON)
    page_count = Column(Integer, default=1)
    page_previews = Column(JSON)
    template_width = Column(Integer, default=0)
    template_height = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())
