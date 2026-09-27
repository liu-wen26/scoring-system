from pydantic import BaseModel, Field, AliasGenerator, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List
from datetime import datetime


common_config = ConfigDict(
    alias_generator=AliasGenerator(
        validation_alias=to_camel,
        serialization_alias=to_camel,
    ),
    populate_by_name=True,
)


class SubjectScore(BaseModel):
    model_config = common_config

    subject_id: int
    subject_name: Optional[str] = None
    total_score: int = 100


class ExamBase(BaseModel):
    model_config = common_config

    exam_name: str = Field(..., min_length=1, max_length=100)
    exam_type: str
    exam_level: str
    grade_id: int = 0
    grade: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    total_score: int = 100
    total_students: int = 0


class ExamCreate(ExamBase):
    subject_ids: List[int] = []
    subject_scores: Optional[List[SubjectScore]] = None


class ExamUpdate(BaseModel):
    model_config = common_config

    exam_name: Optional[str] = None
    exam_type: Optional[str] = None
    exam_level: Optional[str] = None
    grade: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[str] = None


class SubjectProgress(BaseModel):
    model_config = common_config

    subject_id: int
    subject_name: str
    status: str
    total_score: int
    scanned_count: int
    marked_count: int
    progress: float


class ExamResponse(ExamBase):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    status: str
    subjects: List[SubjectProgress] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class ExamListResponse(BaseModel):
    total: int
    items: List[ExamResponse]
