from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.camel_case import convert_keys, convert_keys_to_snake
from app.models.user import User
from app.models.mark import MarkAllocation, MarkResult, MarkDetail, AIMarkTask, AIMarkLog
from app.models.exam import Exam, ExamSubject, ExamQuestion
from app.models.scan import ScanPage
from app.services import ai_mark_service

router = APIRouter()


@router.get("/allocations")
async def list_allocations(
    exam_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取阅卷分配列表"""
    query = db.query(MarkAllocation)
    if exam_id:
        query = query.filter(MarkAllocation.exam_id == exam_id)
    if subject_id:
        query = query.filter(MarkAllocation.subject_id == subject_id)
    if status:
        query = query.filter(MarkAllocation.status == status)
    # 过滤掉无效数据：必须有题号范围
    query = query.filter(
        (MarkAllocation.question_nos != None) &
        (MarkAllocation.question_nos != []) &
        (MarkAllocation.question_nos != '[]') &
        (MarkAllocation.question_nos != 'null')
    )
    allocations = query.order_by(MarkAllocation.created_at.desc()).all()

    # marker 角色在 Python 端过滤（SQLite 不支持 JSON contains）
    if current_user.role == "marker":
        allocations = [
            a for a in allocations
            if a.user_id == current_user.id or current_user.id in (a.user_ids or [])
        ]

    return convert_keys({
        "total": len(allocations),
        "items": [{
            "id": a.id, "exam_id": a.exam_id, "subject_id": a.subject_id,
            "user_id": a.user_id, "question_type": a.question_type,
            "start_num": a.start_num, "end_num": a.end_num,
            "total_papers": a.total_papers, "marked_papers": a.marked_papers,
            "status": a.status,
            "progress": round(a.marked_papers / a.total_papers * 100, 2) if a.total_papers > 0 else 0,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "question_nos": a.question_nos or [],
            "user_ids": a.user_ids or [],
            "mark_mode": a.mark_mode or "single",
            "allocation_mode": a.allocation_mode or "efficiency"
        } for a in allocations]
    })


@router.post("/allocations")
async def create_allocation(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建阅卷分配"""
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="无权操作")
    data = convert_keys_to_snake(data)

    user_ids = data.get("user_ids") or data.get("user_id") and [data.get("user_id")] or []
    question_nos = data.get("question_nos") or []
    exam_id = data.get("exam_id")
    subject_id = data.get("subject_id")

    # 未指定份数时，按实际扫描的学生数统计（去重，多页答题卡只算一份）；无绑定学生则退回页数
    total_papers = data.get("total_papers", 0) or 0
    if total_papers <= 0:
        scan_students = db.query(func.count(func.distinct(ScanPage.student_id))).filter(
            ScanPage.exam_id == exam_id,
            ScanPage.subject_id == subject_id,
            ScanPage.student_id.isnot(None)
        ).scalar() or 0
        if scan_students > 0:
            total_papers = scan_students
        else:
            scan_count = db.query(func.count(ScanPage.id)).filter(
                ScanPage.exam_id == exam_id,
                ScanPage.subject_id == subject_id
            ).scalar() or 0
            if scan_count > 0:
                total_papers = scan_count
            else:
                exam = db.query(Exam).filter(Exam.id == exam_id).first()
                total_papers = exam.total_students if exam and exam.total_students else 0

    allocation = MarkAllocation(
        exam_id=exam_id, subject_id=subject_id,
        user_id=user_ids[0] if user_ids else None,
        user_ids=user_ids,
        question_type=data.get("question_type", "subjective"),
        start_num=data.get("start_num"), end_num=data.get("end_num"),
        question_nos=question_nos,
        mark_mode=data.get("mark_mode", "single"),
        allocation_mode=data.get("allocation_mode", "efficiency"),
        total_papers=total_papers, status="pending"
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return convert_keys({"success": True, "id": allocation.id, "message": "阅卷分配创建成功"})


@router.delete("/allocations/{allocation_id}")
async def delete_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除阅卷分配"""
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="无权操作")
    allocation = db.query(MarkAllocation).filter(MarkAllocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(allocation)
    db.commit()
    return {"success": True, "message": "删除成功"}


@router.delete("/allocations")
async def batch_delete_allocations(
    allocation_ids: List[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量删除阅卷分配"""
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="无权操作")
    if allocation_ids:
        db.query(MarkAllocation).filter(MarkAllocation.id.in_(allocation_ids)).delete(synchronize_session=False)
        db.commit()
    return {"success": True, "message": "删除成功"}


@router.get("/tasks")
async def get_mark_tasks(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的阅卷任务"""
    # SQLite 不支持 JSON contains 查询，改为查询全部分配后 Python 端过滤
    query = db.query(MarkAllocation)
    if status:
        query = query.filter(MarkAllocation.status == status)
    all_allocations = query.all()

    # 过滤出当前用户相关的分配
    allocations = []
    for alloc in all_allocations:
        user_ids = alloc.user_ids or []
        if alloc.user_id == current_user.id or current_user.id in user_ids:
            allocations.append(alloc)

    tasks = []
    for alloc in allocations:
        exam = db.query(Exam).filter(Exam.id == alloc.exam_id).first()
        subject = db.query(ExamSubject).filter(
            ExamSubject.exam_id == alloc.exam_id,
            ExamSubject.subject_id == alloc.subject_id
        ).first()

        # 统计实际待阅卷数
        pending_count = db.query(func.count(MarkResult.id)).filter(
            MarkResult.exam_id == alloc.exam_id,
            MarkResult.subject_id == alloc.subject_id,
            MarkResult.status == "pending"
        ).scalar() or 0

        tasks.append({
            "allocation_id": alloc.id, "exam_id": alloc.exam_id,
            "exam_name": exam.exam_name if exam else "",
            "subject_id": alloc.subject_id,
            "subject_name": subject.subject.subject_name if subject and subject.subject else "",
            "question_type": alloc.question_type,
            "start_num": alloc.start_num, "end_num": alloc.end_num,
            "question_nos": alloc.question_nos or [],
            "total_papers": alloc.total_papers, "marked_papers": alloc.marked_papers,
            "pending_count": pending_count,
            "status": alloc.status,
            "mark_mode": alloc.mark_mode or "single",
            "allocation_mode": alloc.allocation_mode or "efficiency",
            "progress": round(alloc.marked_papers / alloc.total_papers * 100, 2) if alloc.total_papers > 0 else 0
        })
    return convert_keys({"total": len(tasks), "items": tasks})


@router.get("/paper/{scan_page_id}")
async def get_paper_detail(
    scan_page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待阅卷的试卷详情"""
    scan_page = db.query(ScanPage).filter(ScanPage.id == scan_page_id).first()
    if not scan_page:
        # 如果没有 scan_page 记录，尝试直接根据 MarkResult 返回数据
        mark_result = db.query(MarkResult).filter(MarkResult.scan_page_id == scan_page_id).first()
        if not mark_result:
            raise HTTPException(status_code=404, detail="试卷不存在")
        return convert_keys({
            "scan_page_id": scan_page_id, "exam_id": mark_result.exam_id,
            "subject_id": mark_result.subject_id, "student_id": mark_result.student_id,
            "page_number": 1, "file_url": None,
            "ocr_result": {"choice": [], "subjective_cuts": []},
            "choice_score": float(mark_result.choice_score),
            "subjective_score": float(mark_result.subjective_score),
            "total_score": float(mark_result.total_score),
            "status": mark_result.status,
            "marked_by": mark_result.marked_by,
            "marked_at": mark_result.marked_at.isoformat() if mark_result.marked_at else None
        })

    mark_result = db.query(MarkResult).filter(MarkResult.scan_page_id == scan_page_id).first()

    # 阅卷结果按学生聚合后，同一学生的非首页需要按 student_id 回查
    if not mark_result and scan_page.student_id:
        mark_result = db.query(MarkResult).filter(
            MarkResult.exam_id == scan_page.exam_id,
            MarkResult.subject_id == scan_page.subject_id,
            MarkResult.student_id == scan_page.student_id
        ).first()

    # 兼容没有 scan_page 关联的数据（直接按 student_id 补全）
    if mark_result and scan_page.student_id is None:
        scan_page.student_id = mark_result.student_id
        scan_page.exam_id = scan_page.exam_id or mark_result.exam_id
        scan_page.subject_id = scan_page.subject_id or mark_result.subject_id

    return convert_keys({
        "scan_page_id": scan_page_id, "exam_id": scan_page.exam_id,
        "subject_id": scan_page.subject_id, "student_id": scan_page.student_id,
        "page_number": scan_page.page_number, "file_url": scan_page.file_url,
        "ocr_result": scan_page.ocr_result or {"choice": [], "subjective_cuts": []},
        "choice_score": float(mark_result.choice_score) if mark_result else 0,
        "subjective_score": float(mark_result.subjective_score) if mark_result else 0,
        "total_score": float(mark_result.total_score) if mark_result else 0,
        "status": mark_result.status if mark_result else "pending",
        "marked_by": mark_result.marked_by if mark_result else None,
        "marked_at": mark_result.marked_at.isoformat() if mark_result and mark_result.marked_at else None
    })


@router.post("/score/{scan_page_id}")
async def submit_score(
    scan_page_id: int, data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交阅卷分数"""
    scan_page = db.query(ScanPage).filter(ScanPage.id == scan_page_id).first()
    if not scan_page:
        raise HTTPException(status_code=404, detail="试卷不存在")
    data = convert_keys_to_snake(data)
    mark_result = db.query(MarkResult).filter(MarkResult.scan_page_id == scan_page_id).first()
    if not mark_result:
        mark_result = MarkResult(
            exam_id=scan_page.exam_id, subject_id=scan_page.subject_id,
            student_id=scan_page.student_id, scan_page_id=scan_page_id,
            choice_score=data.get("choice_score", 0),
            subjective_score=data.get("subjective_score", 0),
            total_score=data.get("total_score", 0),
            choice_result=data.get("choice_result", {}),
            subjective_result=data.get("subjective_result", {}),
            status="marked", marked_by=current_user.id, marked_at=datetime.now()
        )
        db.add(mark_result)
    else:
        mark_result.subjective_score = data.get("subjective_score", mark_result.subjective_score)
        mark_result.total_score = data.get("total_score", mark_result.total_score)
        mark_result.subjective_result = data.get("subjective_result", mark_result.subjective_result)
        mark_result.status = "marked"
        mark_result.marked_by = current_user.id
        mark_result.marked_at = datetime.now()
    db.commit()
    db.refresh(mark_result)
    allocation = db.query(MarkAllocation).filter(
        MarkAllocation.exam_id == scan_page.exam_id,
        MarkAllocation.subject_id == scan_page.subject_id,
        MarkAllocation.user_id == current_user.id
    ).first()
    if allocation:
        allocation.marked_papers = db.query(MarkResult).filter(
            MarkResult.exam_id == scan_page.exam_id,
            MarkResult.subject_id == scan_page.subject_id,
            MarkResult.marked_by == current_user.id,
            MarkResult.status == "marked"
        ).count()
        if allocation.marked_papers >= allocation.total_papers:
            allocation.status = "completed"
        elif allocation.marked_papers > 0:
            allocation.status = "marking"
        db.commit()
    return convert_keys({
        "success": True, "message": "分数提交成功",
        "scan_page_id": scan_page_id, "total_score": float(mark_result.total_score)
    })


@router.get("/progress/{exam_id}")
async def get_mark_progress(
    exam_id: int,
    subject_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取阅卷进度"""
    query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id)
    if subject_id:
        query = query.filter(MarkResult.subject_id == subject_id)
    total = query.count()
    marked = query.filter(MarkResult.status.in_(["marked", "reviewed"])).count()
    avg_score = db.query(func.avg(MarkResult.total_score)).filter(MarkResult.exam_id == exam_id).scalar()
    max_score = db.query(func.max(MarkResult.total_score)).filter(MarkResult.exam_id == exam_id).scalar()
    min_score = db.query(func.min(MarkResult.total_score)).filter(MarkResult.exam_id == exam_id).scalar()
    return convert_keys({
        "exam_id": exam_id, "subject_id": subject_id,
        "total_papers": total, "marked_papers": marked,
        "pending_papers": total - marked,
        "progress": round(marked / total * 100, 2) if total > 0 else 0,
        "statistics": {
            "average_score": round(float(avg_score), 2) if avg_score else 0,
            "max_score": round(float(max_score), 2) if max_score else 0,
            "min_score": round(float(min_score), 2) if min_score else 0
        }
    })


@router.get("/results/{exam_id}")
async def get_mark_results(
    exam_id: int,
    subject_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    skip: int = Query(0), limit: int = Query(20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取阅卷结果列表"""
    query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id)
    if subject_id:
        query = query.filter(MarkResult.subject_id == subject_id)
    if student_id:
        query = query.filter(MarkResult.student_id == student_id)
    total = query.count()
    results = query.order_by(MarkResult.created_at.desc()).offset(skip).limit(limit).all()
    return convert_keys({
        "total": total,
        "items": [{
            "id": r.id, "exam_id": r.exam_id, "subject_id": r.subject_id,
            "student_id": r.student_id, "scan_page_id": r.scan_page_id,
            "choice_score": float(r.choice_score), "subjective_score": float(r.subjective_score),
            "total_score": float(r.total_score), "status": r.status,
            "marked_by": r.marked_by,
            "marked_at": r.marked_at.isoformat() if r.marked_at else None
        } for r in results]
    })


@router.get("/tasks/question/{exam_id}/{subject_id}")
async def get_question_mark_tasks(
    exam_id: int,
    subject_id: int,
    question_no: Optional[int] = Query(None),
    status: Optional[str] = Query("pending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取按题阅卷任务列表"""
    results = db.query(MarkResult).filter(
        MarkResult.exam_id == exam_id,
        MarkResult.subject_id == subject_id
    ).all()

    tasks = []
    for result in results:
        scan_page = db.query(ScanPage).filter(ScanPage.id == result.scan_page_id).first()
        subjective_result = result.subjective_result or {}
        cuts = subjective_result.get("cuts", [])

        for cut in cuts:
            cut_question_no = cut.get("question_no")
            if question_no is not None and cut_question_no != question_no:
                continue

            # 获取该题是否已打分
            scores = subjective_result.get("scores", {})
            q_status = "marked" if str(cut_question_no) in scores else "pending"
            if status and q_status != status:
                continue

            tasks.append({
                "result_id": result.id,
                "scan_page_id": result.scan_page_id,
                "student_id": result.student_id,
                "question_no": cut_question_no,
                "file_url": cut.get("file_url"),
                "full_score": cut.get("full_score", 0),
                "got_score": scores.get(str(cut_question_no), None),
                "status": q_status
            })

    return convert_keys({
        "total": len(tasks),
        "items": tasks
    })


@router.post("/score/question/{result_id}")
async def submit_question_score(
    result_id: int, data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交单题阅卷分数"""
    result = db.query(MarkResult).filter(MarkResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="阅卷结果不存在")

    data = convert_keys_to_snake(data)
    question_no = str(data.get("question_no"))
    score = float(data.get("score", 0))

    subjective_result = dict(result.subjective_result or {"cuts": []})
    scores = dict(subjective_result.get("scores") or {})
    scores[question_no] = score
    subjective_result["scores"] = scores

    # 计算主观题总分
    subjective_score = round(sum(float(v) for v in scores.values()), 2)
    result.subjective_result = subjective_result
    # 显式标记 JSON 字段已变更（原地修改不会被 SQLAlchemy 追踪）
    flag_modified(result, "subjective_result")
    result.subjective_score = subjective_score
    result.total_score = float(result.choice_score or 0) + subjective_score

    # 只有所有主观题都批阅完，才标记为 marked
    cuts = subjective_result.get("cuts", [])
    all_marked = all(str(c.get("question_no")) in scores for c in cuts) if cuts else True
    result.status = "marked" if all_marked else "marking"
    result.marked_by = current_user.id
    result.marked_at = datetime.now()

    db.commit()
    db.refresh(result)

    # 同步更新阅卷任务进度
    allocation = db.query(MarkAllocation).filter(
        MarkAllocation.exam_id == result.exam_id,
        MarkAllocation.subject_id == result.subject_id
    ).order_by(MarkAllocation.created_at.desc()).first()
    if allocation:
        allocation.marked_papers = db.query(func.count(MarkResult.id)).filter(
            MarkResult.exam_id == result.exam_id,
            MarkResult.subject_id == result.subject_id,
            MarkResult.status.in_(["marked", "reviewed"])
        ).scalar() or 0
        if allocation.total_papers and allocation.marked_papers >= allocation.total_papers:
            allocation.status = "completed"
        elif allocation.marked_papers > 0:
            allocation.status = "marking"
        db.commit()

    return convert_keys({
        "success": True, "message": "分数提交成功",
        "result_id": result_id, "question_no": question_no,
        "subjective_score": subjective_score,
        "total_score": float(result.total_score)
    })


@router.post("/review/{result_id}")
async def review_score(
    result_id: int, data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """复核分数（仲裁）"""
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="无权操作")
    data = convert_keys_to_snake(data)
    result = db.query(MarkResult).filter(MarkResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="阅卷结果不存在")
    result.subjective_score = data.get("subjective_score", result.subjective_score)
    result.total_score = data.get("total_score", result.total_score)
    result.status = "reviewed"
    result.marked_by = current_user.id
    result.marked_at = datetime.now()
    db.commit()
    db.refresh(result)
    return convert_keys({
        "success": True, "message": "复核完成",
        "result_id": result_id, "total_score": float(result.total_score)
    })


# -------------------- AI 辅助阅卷 --------------------

@router.get("/ai/config")
async def get_ai_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的 AI 阅卷配置（不返回完整 API-Key）"""
    config = ai_mark_service.get_ai_config(db, current_user.id)
    if not config:
        return convert_keys({"has_config": False, "model": "qwen-turbo"})
    masked_key = "*" * (len(config.api_key) - 8) + config.api_key[-8:] if len(config.api_key) > 8 else "*" * len(config.api_key)
    return convert_keys({
        "has_config": True,
        "provider": config.provider,
        "model": config.model,
        "endpoint": config.endpoint,
        "api_key": masked_key,
    })


@router.post("/ai/config")
async def save_ai_config(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存/更新当前用户的阿里云百炼 API-Key"""
    data = convert_keys_to_snake(data)
    api_key = data.get("api_key", "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="API-Key 不能为空")
    config = ai_mark_service.get_or_create_ai_config(db, current_user.id, api_key)
    if data.get("model"):
        config.model = data["model"]
    if data.get("endpoint"):
        config.endpoint = data["endpoint"]
    db.commit()
    return convert_keys({"success": True, "message": "API-Key 保存成功", "model": config.model})


@router.post("/ai/tasks")
async def create_ai_mark_task(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建 AI 阅卷任务（启动连续批阅）"""
    data = convert_keys_to_snake(data)
    exam_id = data.get("exam_id")
    subject_id = data.get("subject_id")
    question_no = str(data.get("question_no", ""))
    total_limit = int(data.get("total_limit") or 0)

    if not exam_id or not subject_id or not question_no:
        raise HTTPException(status_code=400, detail="考试、科目、题号不能为空")

    # 检查是否已有运行中的任务，避免重复
    running = db.query(AIMarkTask).filter(
        AIMarkTask.exam_id == exam_id,
        AIMarkTask.subject_id == subject_id,
        AIMarkTask.question_no == question_no,
        AIMarkTask.status == "running"
    ).first()
    if running:
        return convert_keys({"success": True, "task_id": running.id, "message": "已存在运行中的任务"})

    task = ai_mark_service.create_ai_mark_task(
        db=db,
        user_id=current_user.id,
        exam_id=exam_id,
        subject_id=subject_id,
        question_no=question_no,
        question_content=data.get("question_content", ""),
        standard_answer=data.get("standard_answer", ""),
        scoring_criteria=data.get("scoring_criteria", ""),
        total_limit=total_limit,
    )
    return convert_keys({"success": True, "task_id": task.id, "message": "AI 阅卷任务创建成功"})


@router.get("/ai/tasks/{task_id}")
async def get_ai_mark_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 AI 阅卷任务状态与进度"""
    task = db.query(AIMarkTask).filter(AIMarkTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return convert_keys({
        "task_id": task.id,
        "exam_id": task.exam_id,
        "subject_id": task.subject_id,
        "question_no": task.question_no,
        "total_limit": task.total_limit,
        "processed_count": task.processed_count,
        "success_count": task.success_count,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    })


@router.post("/ai/tasks/{task_id}/stop")
async def stop_ai_mark_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """暂停/停止 AI 阅卷任务"""
    task = db.query(AIMarkTask).filter(AIMarkTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.status = "paused"
    db.commit()
    return convert_keys({"success": True, "message": "已停止 AI 阅卷", "task_id": task_id})


@router.post("/ai/tasks/{task_id}/next")
async def get_next_ai_paper(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 AI 任务下一道待批阅试卷（不调用模型）"""
    task = db.query(AIMarkTask).filter(AIMarkTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "running":
        raise HTTPException(status_code=400, detail="任务未在运行中")

    paper = ai_mark_service.find_next_pending_paper(db, task)
    if not paper:
        task.status = "completed"
        db.commit()
        return convert_keys({"finished": True, "message": "该题已全部批阅完成"})

    return convert_keys({"finished": False, "paper": paper})


@router.post("/ai/tasks/{task_id}/score")
async def ai_score_paper(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 评分当前试卷并自动进入下一题（单步）"""
    config = ai_mark_service.get_ai_config(db, current_user.id)
    if not config:
        raise HTTPException(status_code=400, detail="请先配置阿里云百炼 API-Key")

    task = db.query(AIMarkTask).filter(AIMarkTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "running":
        raise HTTPException(status_code=400, detail="任务未在运行中")

    # 已达数量限制
    if task.total_limit > 0 and task.processed_count >= task.total_limit:
        task.status = "completed"
        db.commit()
        return convert_keys({"finished": True, "message": "已达到设定的批改数量上限"})

    paper = ai_mark_service.find_next_pending_paper(db, task)
    if not paper:
        task.status = "completed"
        db.commit()
        return convert_keys({"finished": True, "message": "该题已全部批阅完成"})

    log = AIMarkLog(
        task_id=task.id,
        result_id=paper["result_id"],
        scan_page_id=paper["scan_page_id"],
        student_id=paper["student_id"],
        question_no=paper["question_no"],
        full_score=paper["full_score"],
        status="pending",
    )
    db.add(log)
    db.commit()

    try:
        ai_score, reason = await ai_mark_service.call_bailian_score(
            api_key=config.api_key,
            model=config.model,
            endpoint=config.endpoint,
            question_content=task.question_content or "",
            standard_answer=task.standard_answer or "",
            scoring_criteria=task.scoring_criteria or "",
            student_answer=paper["student_answer"],
            full_score=paper["full_score"],
        )
    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"AI 评分失败: {e}")

    # 保存分数
    ai_mark_service.submit_question_score(db, paper["result_id"], paper["question_no"], ai_score)
    detail = db.query(MarkDetail).filter(
        MarkDetail.mark_result_id == paper["result_id"],
        MarkDetail.exam_id == task.exam_id,
        MarkDetail.subject_id == task.subject_id,
    ).join(ExamQuestion, MarkDetail.question_id == ExamQuestion.id).filter(
        ExamQuestion.question_no == task.question_no
    ).first()
    if detail:
        ai_mark_service.mark_detail_as_ai_scored(db, detail, ai_score)

    log.ai_score = ai_score
    log.ai_reason = reason
    log.status = "success"
    db.commit()

    task.processed_count += 1
    task.success_count += 1
    db.commit()

    # 检查是否达到数量限制
    finished = False
    message = None
    if task.total_limit > 0 and task.processed_count >= task.total_limit:
        task.status = "completed"
        db.commit()
        finished = True
        message = "已达到设定的批改数量上限"

    next_paper = ai_mark_service.find_next_pending_paper(db, task) if task.status == "running" else None
    if not next_paper and task.status == "running":
        task.status = "completed"
        db.commit()
        finished = True
        message = message or "该题已全部批阅完成"

    return convert_keys({
        "finished": finished,
        "message": message,
        "current": {
            "result_id": paper["result_id"],
            "scan_page_id": paper["scan_page_id"],
            "student_id": paper["student_id"],
            "student_name": paper["student_name"],
            "question_no": paper["question_no"],
            "full_score": paper["full_score"],
            "ai_score": ai_score,
            "ai_reason": reason,
            "student_answer": paper["student_answer"],
        },
        "next_paper": next_paper,
        "progress": {
            "processed_count": task.processed_count,
            "success_count": task.success_count,
            "total_limit": task.total_limit,
        },
    })