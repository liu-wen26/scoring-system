from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import time

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.camel_case import convert_keys
from app.models.user import User
from app.models.scan import ScanBatch, ScanPage
from app.services.storage import MinIOStorage
from app.services.pdf_parser import PDFParser, PDFUploadService

try:
    from app.tasks.ocr_tasks import process_scan_image
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    process_scan_image = None

router = APIRouter()


@router.post("/upload/pdf")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    exam_id: int = Form(...),
    subject_id: int = Form(...),
    binding_mode: str = Form("auto"),
    student_list: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传 PDF 答题卡文件"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
    
    content = await file.read()
    
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过 100MB")
    
    parser = PDFParser(target_dpi=300)
    storage = MinIOStorage()
    upload_service = PDFUploadService(parser, storage)
    
    metadata = {
        'upload_id': f"{exam_id}_{subject_id}_{current_user.id}_{int(time.time())}",
        'exam_id': exam_id,
        'subject_id': subject_id,
        'binding_mode': binding_mode,
        'student_list': json.loads(student_list) if student_list else [],
        'uploaded_by': current_user.id
    }
    
    result = await upload_service.process_upload(content, metadata)
    
    for page in result['pages']:
        background_tasks.add_task(
            process_scan_image,
            exam_id=exam_id,
            subject_id=subject_id,
            file_url=page['file_url'],
            page_number=page['page_number'],
            student_id=result['student_bindings'][page['page_number'] - 1].get('student_id')
        )
    
    return convert_keys({
        "success": True,
        "message": "PDF 上传成功",
        "total_pages": result['total_pages'],
        "pages": result['pages'],
        "student_bindings": result['student_bindings']
    })


@router.post("/upload/image")
async def upload_scan_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    exam_id: int = Form(...),
    subject_id: int = Form(...),
    student_id: Optional[int] = Form(None),
    page_number: int = Form(1),
    scan_mode: str = Form("direct"),
    binding_mode: str = Form("auto"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传扫描图片（直连模式）"""
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPG/PNG 图片")

    storage = MinIOStorage()
    content = await file.read()

    file_url = await storage.save_image(
        image_data=content,
        exam_id=exam_id,
        subject_id=subject_id,
        filename=file.filename
    )

    # 创建扫描批次（如果不存在）
    batch = db.query(ScanBatch).filter(
        ScanBatch.exam_id == exam_id,
        ScanBatch.subject_id == subject_id
    ).first()
    if not batch:
        import uuid
        batch_no = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        batch = ScanBatch(
            batch_no=batch_no, exam_id=exam_id, subject_id=subject_id,
            scan_mode="direct", total_pages=0, processed_pages=0,
            status="uploading", uploaded_by=current_user.id
        )
        db.add(batch)
        db.flush()

    # 学生绑定：
    # - auto（默认）：交由 OCR 识别考号/姓名后按名册匹配（无学生信息页继承同批次上一页）
    # - sequential：按上传顺序依次绑定学生
    if not student_id and binding_mode == "sequential":
        from app.models.user import Student
        # 统计该考试科目已上传的扫描页数，用于确定当前序号
        existing_count = db.query(ScanPage).filter(
            ScanPage.exam_id == exam_id,
            ScanPage.subject_id == subject_id
        ).count()
        # 按顺序取下一个学生
        students = db.query(Student).order_by(Student.id).offset(existing_count).first()
        if students:
            student_id = students.id

    binding_status = "bound" if student_id else "pending"
    # 创建扫描页记录
    scan_page = ScanPage(
        batch_id=batch.id, exam_id=exam_id, subject_id=subject_id,
        page_number=page_number, file_url=file_url,
        student_id=student_id,
        binding_status=binding_status,
        status="pending"
    )
    db.add(scan_page)
    batch.total_pages += 1
    db.commit()
    db.refresh(scan_page)

    background_tasks.add_task(
        process_scan_image,
        exam_id=exam_id,
        subject_id=subject_id,
        file_url=file_url,
        page_number=page_number,
        student_id=student_id
    )

    return convert_keys({
        "success": True,
        "message": "图片上传成功",
        "file_url": file_url,
        "scan_page_id": scan_page.id,
        "student_id": student_id,
        "scan_mode": "direct"
    })


@router.post("/upload/batch")
async def batch_upload(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    exam_id: int = Form(...),
    subject_id: int = Form(...),
    binding_mode: str = Form("sequential"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量上传扫描文件"""
    results = []
    
    for i, file in enumerate(files):
        try:
            if file.filename.endswith('.pdf'):
                result = await upload_pdf(
                    background_tasks=background_tasks,
                    file=file,
                    exam_id=exam_id,
                    subject_id=subject_id,
                    binding_mode=binding_mode,
                    db=db,
                    current_user=current_user
                )
            else:
                result = await upload_scan_image(
                    background_tasks=background_tasks,
                    file=file,
                    exam_id=exam_id,
                    subject_id=subject_id,
                    page_number=i + 1,
                    db=db,
                    current_user=current_user
                )
            
            results.append({"success": True, "filename": file.filename, "data": result})
        except Exception as e:
            results.append({"success": False, "filename": file.filename, "error": str(e)})
    
    return convert_keys({
        "success": True,
        "total": len(files),
        "success_count": sum(1 for r in results if r["success"]),
        "results": results
    })


@router.post("/reprocess/{scan_page_id}")
async def reprocess_scan_page(
    scan_page_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重新处理单页扫描图片（更新答题卡配置后使用）"""
    scan_page = db.query(ScanPage).filter(ScanPage.id == scan_page_id).first()
    if not scan_page:
        raise HTTPException(status_code=404, detail="扫描页不存在")

    scan_page.status = "pending"
    scan_page.error_message = None
    scan_page.ocr_result = None
    db.commit()

    background_tasks.add_task(
        process_scan_image,
        exam_id=scan_page.exam_id,
        subject_id=scan_page.subject_id,
        file_url=scan_page.file_url,
        page_number=scan_page.page_number,
        student_id=scan_page.student_id
    )

    return convert_keys({
        "success": True,
        "message": "已重新提交处理",
        "scan_page_id": scan_page.id
    })


@router.post("/reprocess/exam/{exam_id}/{subject_id}")
async def reprocess_exam_subject(
    exam_id: int,
    subject_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量重新处理某考试科目的所有扫描页"""
    scan_pages = db.query(ScanPage).filter(
        ScanPage.exam_id == exam_id,
        ScanPage.subject_id == subject_id
    ).all()

    for page in scan_pages:
        page.status = "pending"
        page.error_message = None
        page.ocr_result = None
        background_tasks.add_task(
            process_scan_image,
            exam_id=page.exam_id,
            subject_id=page.subject_id,
            file_url=page.file_url,
            page_number=page.page_number,
            student_id=page.student_id
        )

    db.commit()

    return convert_keys({
        "success": True,
        "message": f"已重新提交 {len(scan_pages)} 页处理",
        "total": len(scan_pages)
    })
