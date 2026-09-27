from pydantic import BaseModel, Field, AliasGenerator, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional
from datetime import datetime


common_config = ConfigDict(
    alias_generator=AliasGenerator(
        validation_alias=to_camel,
        serialization_alias=to_camel,
    ),
    populate_by_name=True,
)


class UserBase(BaseModel):
    model_config = common_config

    username: str = Field(..., min_length=3, max_length=50)
    real_name: str = Field(..., min_length=1, max_length=50)
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    model_config = common_config

    real_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[int] = None
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    subject_id: Optional[int] = None


class UserResponse(UserBase):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    status: int
    created_at: datetime
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    subject_id: Optional[int] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    model_config = common_config

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class StudentBase(BaseModel):
    model_config = common_config

    student_no: str
    real_name: str
    class_id: Optional[int] = None
    grade_id: Optional[int] = None
    gender: Optional[str] = None
    status: Optional[int] = 1


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    model_config = common_config

    student_no: Optional[str] = None
    real_name: Optional[str] = None
    class_id: Optional[int] = None
    grade_id: Optional[int] = None
    gender: Optional[str] = None
    status: Optional[int] = None


class StudentResponse(StudentBase):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    class_name: Optional[str] = None
    grade_name: Optional[str] = None


class StudentBatchCreate(BaseModel):
    model_config = common_config

    student_no: str
    real_name: str
    class_id: Optional[int] = None
    grade_id: Optional[int] = None
    gender: Optional[str] = None
    status: Optional[int] = 1


class TeacherBase(BaseModel):
    model_config = common_config

    username: str = Field(..., min_length=3, max_length=50)
    real_name: str = Field(..., min_length=1, max_length=50)
    role: str = "teacher"
    phone: Optional[str] = None
    email: Optional[str] = None
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    subject_id: Optional[int] = None
    status: Optional[int] = 1


class TeacherCreate(TeacherBase):
    password: str = Field(..., min_length=6, max_length=100)


class TeacherUpdate(BaseModel):
    model_config = common_config

    username: Optional[str] = None
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    subject_id: Optional[int] = None
    status: Optional[int] = None


class TeacherBatchCreate(BaseModel):
    model_config = common_config

    username: str = Field(..., min_length=3, max_length=50)
    real_name: str = Field(..., min_length=1, max_length=50)
    password: Optional[str] = Field(default="123456", min_length=6, max_length=100)
    phone: Optional[str] = None
    email: Optional[str] = None
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    subject_id: Optional[int] = None
    status: Optional[int] = 1


class TeacherResponse(TeacherBase):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    created_at: datetime
    grade_name: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
