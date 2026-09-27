from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    status = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    
    grade_id = Column(Integer, ForeignKey("grades.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    
    grade = relationship("Grade", foreign_keys=[grade_id])
    class_ = relationship("Class", foreign_keys=[class_id])
    subject = relationship("Subject", foreign_keys=[subject_id])

    @property
    def class_name(self):
        return self.class_.class_name if self.class_ else None

    @property
    def grade_name(self):
        return self.grade.grade_name if self.grade else None

    @property
    def subject_name(self):
        return self.subject.subject_name if self.subject else None


class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    grade_name = Column(String(20), nullable=False)
    grade_level = Column(Integer)


class Class(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(50), nullable=False)
    grade_id = Column(Integer, ForeignKey("grades.id"))
    student_count = Column(Integer, default=0)


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_no = Column(String(50), unique=True, nullable=False)
    real_name = Column(String(50), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), index=True)
    grade_id = Column(Integer, ForeignKey("grades.id"))
    gender = Column(String(10))
    birthday = Column(DateTime)
    status = Column(Integer, default=1)
    
    grade = relationship("Grade")
    class_ = relationship("Class")

    @property
    def class_name(self):
        return self.class_.class_name if self.class_ else None

    @property
    def grade_name(self):
        return self.grade.grade_name if self.grade else None
