from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import base64
import io

from PIL import Image

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.camel_case import convert_keys
from app.core.config import settings
from app.models.user import User, Grade
from app.models.exam import Exam, ExamSubject, Subject
from app.models.answer_card import AnswerCardConfig, AnswerCardTemplate
from app.schemas.answer_card import (
    AnswerCardConfigCreate,
    AnswerCardConfigResponse,
    AnswerCardTemplateCreate,
    AnswerCardTemplateUpdate,
)

router = APIRouter()


def _parse_image_size(data_url: str) -> tuple:
    """从单个 base64 data URL 解析图片宽高"""
    if not data_url:
        return 0, 0
    try:
        if data_url.startswith("data:"):
            data_url = data_url.split(",", 1)[1]
        img_bytes = base64.b64decode(data_url)
        img = Image.open(io.BytesIO(img_bytes))
        return img.width, img.height
    except Exception:
        return 0, 0


def _parse_preview_size(page_previews: List[str], template_image: str = None) -> tuple:
    """从 page_previews 或 template_image 解析模板宽高"""
    if page_previews:
        return _parse_image_size(page_previews[0])
    if template_image:
        return _parse_image_size(template_image)
    return 0, 0


@router.get("/templates")
async def list_templates(
    template_type: Optional[str] = Query(None, alias="templateType"),
    grade_id: Optional[int] = Query(None, alias="gradeId"),
    subject_id: Optional[int] = Query(None, alias="subjectId"),
    mark_mode: Optional[str] = Query(None, alias="markMode"),
    my_created: Optional[bool] = Query(False, alias="myCreated"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取答题卡模板列表"""
    query = db.query(AnswerCardTemplate).filter(
        AnswerCardTemplate.status == 1
    )
    if template_type:
        query = query.filter(AnswerCardTemplate.template_type == template_type)
    if grade_id:
        query = query.filter(AnswerCardTemplate.grade_id == grade_id)
    if subject_id:
        query = query.filter(AnswerCardTemplate.subject_id == subject_id)
    if my_created:
        query = query.filter(AnswerCardTemplate.created_by == current_user.id)

    templates = query.order_by(AnswerCardTemplate.created_at.desc()).all()

    items = []
    for t in templates:
        grade_name = ""
        subject_name = ""
        if t.grade_id:
            grade = db.query(Grade).filter(Grade.id == t.grade_id).first()
            grade_name = grade.grade_name if grade else ""
        if t.subject_id:
            subject = db.query(Subject).filter(Subject.id == t.subject_id).first()
            subject_name = subject.subject_name if subject else ""
        cfg = t.config or {}
        item = {
            "id": t.id,
            "template_name": t.template_name,
            "template_code": t.template_code,
            "template_type": t.template_type,
            "grade_id": t.grade_id,
            "subject_id": t.subject_id,
            "grade_name": grade_name,
            "subject_name": subject_name,
            "mark_mode": cfg.get("markMode", "online"),
            "preview_url": t.preview_url,
            "width": t.width,
            "height": t.height,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "created_by": t.created_by,
        }
        if mark_mode and item["mark_mode"] != mark_mode:
            continue
        items.append(item)

    return convert_keys({"items": items})


def _default_template_config() -> dict:
    return {
        "title": "",
        "scenario": "exam",
        "markMode": "online",
        "studentNumberType": "handwrite",
        "showNotes": True,
        "showAbsentMark": True,
        "layout": "two",
        "color": "black",
        "sealLine": False,
        "partition": False,
        "digits": 8,
        "sections": []
    }


@router.post("/templates")
async def create_template(
    data: AnswerCardTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建答题卡模板"""
    grade_name = ""
    subject_name = ""
    if data.grade_id:
        grade = db.query(Grade).filter(Grade.id == data.grade_id).first()
        grade_name = grade.grade_name if grade else ""
    if data.subject_id:
        subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
        subject_name = subject.subject_name if subject else ""

    template_name = data.template_name or f"{grade_name}{subject_name}答题卡" or "新建答题卡"
    template_code = data.template_code or f"AC{uuid.uuid4().hex[:8].upper()}"

    existing = db.query(AnswerCardTemplate).filter(
        AnswerCardTemplate.template_code == template_code
    ).first()
    if existing:
        template_code = f"AC{uuid.uuid4().hex[:8].upper()}"

    config = data.config or _default_template_config()
    if not config.get("title"):
        config["title"] = template_name

    template = AnswerCardTemplate(
        template_name=template_name,
        template_code=template_code,
        template_type=data.template_type or 'custom',
        grade_id=data.grade_id,
        subject_id=data.subject_id,
        width=data.width or 210,
        height=data.height or 297,
        config=config,
        preview_url=data.preview_url,
        status=1,
        created_by=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return convert_keys({
        "id": template.id,
        "template_name": template.template_name,
        "template_code": template.template_code,
        "template_type": template.template_type,
        "grade_id": template.grade_id,
        "subject_id": template.subject_id,
        "grade_name": grade_name,
        "subject_name": subject_name,
        "width": template.width,
        "height": template.height,
        "config": template.config,
        "preview_url": template.preview_url,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    })


@router.get("/templates/{template_id}")
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """答题卡模板详情"""
    template = db.query(AnswerCardTemplate).filter(
        AnswerCardTemplate.id == template_id,
        AnswerCardTemplate.status == 1
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    grade_name = ""
    subject_name = ""
    if template.grade_id:
        grade = db.query(Grade).filter(Grade.id == template.grade_id).first()
        grade_name = grade.grade_name if grade else ""
    if template.subject_id:
        subject = db.query(Subject).filter(Subject.id == template.subject_id).first()
        subject_name = subject.subject_name if subject else ""

    return convert_keys({
        "id": template.id,
        "template_name": template.template_name,
        "template_code": template.template_code,
        "template_type": template.template_type,
        "grade_id": template.grade_id,
        "subject_id": template.subject_id,
        "grade_name": grade_name,
        "subject_name": subject_name,
        "width": template.width,
        "height": template.height,
        "config": template.config or _default_template_config(),
        "preview_url": template.preview_url,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    })


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    data: AnswerCardTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新答题卡模板"""
    template = db.query(AnswerCardTemplate).filter(
        AnswerCardTemplate.id == template_id,
        AnswerCardTemplate.status == 1
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if data.template_name is not None:
        template.template_name = data.template_name
    if data.template_code is not None:
        template.template_code = data.template_code
    if data.template_type is not None:
        template.template_type = data.template_type
    if data.grade_id is not None:
        template.grade_id = data.grade_id
    if data.subject_id is not None:
        template.subject_id = data.subject_id
    if data.width is not None:
        template.width = data.width
    if data.height is not None:
        template.height = data.height
    if data.config is not None:
        template.config = data.config
    if data.preview_url is not None:
        template.preview_url = data.preview_url

    db.commit()
    db.refresh(template)

    grade_name = ""
    subject_name = ""
    if template.grade_id:
        grade = db.query(Grade).filter(Grade.id == template.grade_id).first()
        grade_name = grade.grade_name if grade else ""
    if template.subject_id:
        subject = db.query(Subject).filter(Subject.id == template.subject_id).first()
        subject_name = subject.subject_name if subject else ""

    return convert_keys({
        "id": template.id,
        "template_name": template.template_name,
        "template_code": template.template_code,
        "template_type": template.template_type,
        "grade_id": template.grade_id,
        "subject_id": template.subject_id,
        "grade_name": grade_name,
        "subject_name": subject_name,
        "width": template.width,
        "height": template.height,
        "config": template.config,
        "preview_url": template.preview_url,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    })


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除答题卡模板（软删除）"""
    template = db.query(AnswerCardTemplate).filter(
        AnswerCardTemplate.id == template_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    template.status = 0
    db.commit()
    return convert_keys({"message": "删除成功"})


@router.post("/third-party")
async def upload_third_party_template(
    file: UploadFile = File(...),
    grade_id: int = Form(..., alias="gradeId"),
    subject_id: int = Form(..., alias="subjectId"),
    mark_mode: Optional[str] = Form('online', alias="markMode"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传第三方答题卡模板"""
    content_type = file.content_type or ""
    if not content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图片文件")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过10MB")

    upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "uploads", "answer_cards"
    )
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or '')[1] or '.png'
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(content)

    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    template_name = f"{grade.grade_name if grade else ''}{subject.subject_name if subject else ''}第三方答题卡"

    template = AnswerCardTemplate(
        template_name=template_name,
        template_code=f"TP{uuid.uuid4().hex[:8].upper()}",
        template_type='third_party',
        grade_id=grade_id,
        subject_id=subject_id,
        width=210,
        height=297,
        config={"markMode": mark_mode or 'online'},
        preview_url=f"/uploads/answer_cards/{filename}",
        status=1,
        created_by=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return convert_keys({
        "id": template.id,
        "template_name": template.template_name,
        "preview_url": template.preview_url,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    })


@router.get("/config")
async def get_config(
    exam_id: int = Query(..., alias="examId"),
    subject_id: int = Query(..., alias="subjectId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取考试科目的答题卡配置（不存在则返回默认空配置）"""
    config = db.query(AnswerCardConfig).filter(
        AnswerCardConfig.exam_id == exam_id,
        AnswerCardConfig.subject_id == subject_id
    ).first()
    if not config:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        return convert_keys({
            "exam_id": exam_id,
            "subject_id": subject_id,
            "template_id": None,
            "template_image": None,
            "questions_config": {
                "student_number": {
                    "config_type": "handwrite",
                    "digits": 10,
                    "position": {"x": 20, "y": 20, "w": 160, "h": 30}
                },
                "question_groups": []
            },
            "standard_answers": {},
            "mark_points": [],
            "regions": [],
            "page_count": 1,
            "page_previews": [],
            "status": "pending"
        })
    # 兼容旧数据：如果未记录模板尺寸，尝试从预览图解析
    template_width = config.template_width or 0
    template_height = config.template_height or 0
    if (template_width == 0 or template_height == 0) and (config.page_previews or config.template_image):
        template_width, template_height = _parse_preview_size(
            config.page_previews or [], config.template_image
        )

    return convert_keys({
        "id": config.id,
        "exam_id": config.exam_id,
        "subject_id": config.subject_id,
        "template_id": config.template_id,
        "template_image": config.template_image,
        "questions_config": config.questions_config or {},
        "standard_answers": config.standard_answers or {},
        "mark_points": config.mark_points or [],
        "regions": config.regions or [],
        "page_count": config.page_count or 2,
        "page_previews": config.page_previews or [],
        "template_width": template_width,
        "template_height": template_height,
        "status": config.status,
        "created_at": config.created_at.isoformat() if config.created_at else None
    })


@router.post("/config")
async def save_config(
    data: AnswerCardConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存或更新考试科目的答题卡配置"""
    exam = db.query(Exam).filter(Exam.id == data.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="科目不存在")

    exam_subject = db.query(ExamSubject).filter(
        ExamSubject.exam_id == data.exam_id,
        ExamSubject.subject_id == data.subject_id
    ).first()
    if not exam_subject:
        raise HTTPException(status_code=400, detail="该考试未包含此科目")

    config = db.query(AnswerCardConfig).filter(
        AnswerCardConfig.exam_id == data.exam_id,
        AnswerCardConfig.subject_id == data.subject_id
    ).first()

    q_config = data.questions_config.model_dump() if data.questions_config else {}
    mark_points = [r.model_dump() for r in data.mark_points] if data.mark_points else []
    regions = [r.model_dump() for r in data.regions] if data.regions else []

    # 解析模板预览图尺寸，用于后续扫描图坐标缩放
    previews = data.page_previews or []
    template_width, template_height = _parse_preview_size(previews, data.template_image)

    if config:
        config.template_id = data.template_id
        config.template_image = data.template_image
        config.questions_config = q_config
        config.standard_answers = data.standard_answers
        config.mark_points = mark_points
        config.regions = regions
        config.page_count = data.page_count or 1
        config.page_previews = previews
        config.template_width = template_width
        config.template_height = template_height
        config.status = data.status or "configured"
    else:
        config = AnswerCardConfig(
            exam_id=data.exam_id,
            subject_id=data.subject_id,
            template_id=data.template_id,
            template_image=data.template_image,
            questions_config=q_config,
            standard_answers=data.standard_answers,
            mark_points=mark_points,
            regions=regions,
            page_count=data.page_count or 1,
            page_previews=previews,
            template_width=template_width,
            template_height=template_height,
            status=data.status or "configured",
        )
        db.add(config)

    # 同步更新考试科目的题目数量和分值统计
    choice_count = 0
    choice_score = 0
    subjective_count = 0
    subjective_score = 0
    if data.questions_config and data.questions_config.question_groups:
        for group in data.questions_config.question_groups:
            if group.type == "choice":
                choice_count += group.count
                choice_score += group.count * group.score_per_question
            elif group.type == "subjective":
                subjective_count += group.count
                individual = group.individual_scores or {}
                for i in range(group.count):
                    no = str(group.start_no + i)
                    subjective_score += individual.get(no, group.score_per_question)

    exam_subject.choice_count = choice_count
    exam_subject.choice_score = choice_score
    exam_subject.subjective_count = subjective_count
    exam_subject.subjective_score = subjective_score
    exam_subject.status = "configured"

    db.commit()
    db.refresh(config)
    return convert_keys({
        "success": True,
        "message": "保存成功",
        "id": config.id
    })


@router.post("/upload-template")
async def upload_template(
    file: UploadFile = File(...),
    exam_id: int = Form(..., alias="examId"),
    subject_id: int = Form(..., alias="subjectId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传答题卡模板（支持图片和 PDF）"""
    content_type = file.content_type or ""
    is_image = content_type.startswith('image/')
    is_pdf = content_type == 'application/pdf'

    if not is_image and not is_pdf:
        raise HTTPException(status_code=400, detail="只支持图片或 PDF 文件")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过10MB")

    import base64
    file_url = f"data:{file.content_type};base64,{base64.b64encode(content).decode()}"

    width, height = 600, 840
    page_count = 1

    if is_pdf:
        try:
            import fitz
            import io as _io
            doc = fitz.open(stream=content, filetype="pdf")
            page_count = len(doc)
            page_previews = []
            for page_idx in range(page_count):
                page = doc[page_idx]
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                preview_bytes = pix.tobytes("png")
                preview_b64 = base64.b64encode(preview_bytes).decode()
                page_previews.append(f"data:image/png;base64,{preview_b64}")
                if page_idx == 0:
                    width, height = int(pix.width), int(pix.height)
            preview_url = page_previews[0] if page_previews else file_url
            doc.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF 解析失败: {str(e)}")
    else:
        preview_url = file_url
        page_previews = [file_url]
        try:
            from PIL import Image
            import io as _io
            img = Image.open(_io.BytesIO(content))
            width, height = img.size
        except Exception:
            pass

    config = db.query(AnswerCardConfig).filter(
        AnswerCardConfig.exam_id == exam_id,
        AnswerCardConfig.subject_id == subject_id
    ).first()

    if config:
        config.template_image = file_url
        config.page_count = page_count
        config.page_previews = page_previews
        config.template_width = width
        config.template_height = height
        db.commit()
    else:
        config = AnswerCardConfig(
            exam_id=exam_id,
            subject_id=subject_id,
            template_image=file_url,
            page_count=page_count,
            page_previews=page_previews,
            template_width=width,
            template_height=height,
            status="pending",
        )
        db.add(config)
        db.commit()

    return convert_keys({
        "success": True,
        "file_url": file_url,
        "preview_url": preview_url,
        "page_previews": page_previews,
        "width": width,
        "height": height,
        "page_count": page_count
    })


@router.get("/config/list")
async def list_exam_configs(
    exam_id: int = Query(..., alias="examId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取考试下所有科目的答题卡配置状态"""
    exam_subjects = db.query(ExamSubject).filter(
        ExamSubject.exam_id == exam_id
    ).all()

    configs = db.query(AnswerCardConfig).filter(
        AnswerCardConfig.exam_id == exam_id
    ).all()
    config_map = {(c.subject_id): c for c in configs}

    items = []
    for es in exam_subjects:
        subject = db.query(Subject).filter(Subject.id == es.subject_id).first()
        config = config_map.get(es.subject_id)
        items.append({
            "subject_id": es.subject_id,
            "subject_name": subject.subject_name if subject else "",
            "status": config.status if config else es.status,
            "configured": config is not None,
            "config_id": config.id if config else None,
        })

    return convert_keys({
        "exam_id": exam_id,
        "items": items
    })
