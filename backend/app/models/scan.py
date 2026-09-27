from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ScanBatch(Base):
    __tablename__ = "scan_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_no = Column(String(50), unique=True, nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    
    scan_mode = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    
    total_pages = Column(Integer, default=0)
    processed_pages = Column(Integer, default=0)
    failed_pages = Column(Integer, default=0)
    
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    
    original_filename = Column(String(255))
    file_size = Column(Integer)
    pdf_metadata = Column(JSON)
    
    exam = relationship("Exam", back_populates="scan_batches")
    pages = relationship("ScanPage", back_populates="batch", cascade="all, delete-orphan")


class ScanPage(Base):
    __tablename__ = "scan_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("scan_batches.id"), index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    page_number = Column(Integer, nullable=False)
    
    file_url = Column(String(500))
    thumbnail_url = Column(String(500))
    
    student_id = Column(Integer, ForeignKey("students.id"))
    binding_status = Column(String(20), default="pending")
    binding_confidence = Column(String(20))
    
    status = Column(String(20), default="pending")
    ocr_result = Column(JSON)
    error_message = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    
    batch = relationship("ScanBatch", back_populates="pages")
    exam = relationship("Exam", back_populates="scan_pages")
    subject = relationship("Subject", back_populates="scan_pages")
