from pydantic import BaseModel, Field, AliasGenerator, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List, Dict, Any
from datetime import datetime


common_config = ConfigDict(
    alias_generator=AliasGenerator(
        validation_alias=to_camel,
        serialization_alias=to_camel,
    ),
    populate_by_name=True,
)


class StudentNumberConfig(BaseModel):
    model_config = common_config

    config_type: str = Field(default="handwrite", description="barcode/qrcode/handwrite")
    digits: int = Field(default=10, ge=4, le=20)
    position: Optional[Dict[str, int]] = Field(default=None, description="x,y,w,h")


class QuestionGroup(BaseModel):
    model_config = common_config

    type: str = Field(..., description="choice/fill/subjective")
    start_no: int = Field(..., ge=1)
    count: int = Field(..., ge=1)
    score_per_question: float = Field(..., ge=0)
    options: Optional[List[str]] = Field(default=None, description="客观题选项")
    group_label: Optional[str] = Field(default="", description="大题号名称")
    question_type: Optional[str] = Field(default="", description="题型类型")
    individual_scores: Optional[Dict[str, float]] = Field(default=None, description="小题单独分值")


class SubjectiveRegion(BaseModel):
    model_config = common_config

    question_no: str
    page: int = Field(default=1, ge=1)
    x: int
    y: int
    w: int
    h: int
    score: Optional[float] = Field(default=None, description="区域分值")


class RegionItem(BaseModel):
    model_config = common_config

    key: str
    type: str
    page: int = Field(default=1, ge=1)
    question_no: Optional[str] = None
    field: Optional[str] = None
    x: int
    y: int
    w: int
    h: int
    score: Optional[float] = Field(default=None, description="区域分值")


class AnswerCardQuestionsConfig(BaseModel):
    model_config = common_config

    student_number: Optional[StudentNumberConfig] = Field(default_factory=StudentNumberConfig)
    question_groups: List[QuestionGroup] = Field(default_factory=list)


class AnswerCardTemplateCreate(BaseModel):
    model_config = common_config

    template_name: Optional[str] = Field(default=None)
    template_code: Optional[str] = Field(default=None)
    template_type: Optional[str] = Field(default='custom')
    grade_id: Optional[int] = None
    subject_id: Optional[int] = None
    width: Optional[int] = 210
    height: Optional[int] = 297
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    preview_url: Optional[str] = None


class AnswerCardTemplateUpdate(BaseModel):
    model_config = common_config

    template_name: Optional[str] = None
    template_code: Optional[str] = None
    template_type: Optional[str] = None
    grade_id: Optional[int] = None
    subject_id: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    preview_url: Optional[str] = None


class AnswerCardConfigCreate(BaseModel):
    model_config = common_config

    exam_id: int
    subject_id: int
    template_id: Optional[int] = None
    template_image: Optional[str] = None
    questions_config: AnswerCardQuestionsConfig
    standard_answers: Optional[Dict[str, str]] = Field(default_factory=dict)
    mark_points: Optional[List[SubjectiveRegion]] = Field(default_factory=list)
    regions: Optional[List[RegionItem]] = Field(default_factory=list)
    page_count: Optional[int] = 2
    page_previews: Optional[List[str]] = Field(default_factory=list)
    template_width: Optional[int] = 0
    template_height: Optional[int] = 0
    status: Optional[str] = "configured"


class AnswerCardConfigResponse(AnswerCardConfigCreate):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    created_at: Optional[datetime] = None
