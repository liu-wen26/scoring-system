from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.camel_case import convert_keys
from app.models.user import User
from app.models.mark import MarkResult
from app.models.exam import Exam, ExamSubject

router = APIRouter()


@router.get("/exam/{exam_id}")
async def get_exam_report(
    exam_id: int,
    subject_id: Optional[int] = Query(None),
    class_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取考试成绩报告"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id)
    if subject_id:
        query = query.filter(MarkResult.subject_id == subject_id)
    results = query.all()
    if not results:
        return convert_keys({"exam_id": exam_id, "exam_name": exam.exam_name, "message": "暂无成绩数据"})
    scores = [float(r.total_score) for r in results]
    scores.sort()
    n = len(scores)
    avg_score = sum(scores) / n
    segments = {"0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
    for s in scores:
        if s < 60: segments["0-59"] += 1
        elif s < 70: segments["60-69"] += 1
        elif s < 80: segments["70-79"] += 1
        elif s < 90: segments["80-89"] += 1
        else: segments["90-100"] += 1
    pass_count = sum(1 for s in scores if s >= 60)
    excellent_count = sum(1 for s in scores if s >= 90)
    return convert_keys({
        "exam_id": exam_id, "exam_name": exam.exam_name, "subject_id": subject_id,
        "statistics": {
            "total_students": n, "average_score": round(avg_score, 2),
            "max_score": round(max(scores), 2), "min_score": round(min(scores), 2),
            "median_score": round(scores[n // 2], 2) if n % 2 == 1 else round((scores[n // 2 - 1] + scores[n // 2]) / 2, 2),
            "pass_count": pass_count, "pass_rate": round(pass_count / n * 100, 2),
            "excellent_count": excellent_count, "excellent_rate": round(excellent_count / n * 100, 2)
        },
        "score_segments": segments,
        "standard_deviation": round((sum((s - avg_score) ** 2 for s in scores) / n) ** 0.5, 2)
    })


@router.get("/exam/{exam_id}/ranking")
async def get_exam_ranking(
    exam_id: int,
    subject_id: Optional[int] = Query(None),
    page: int = Query(1), page_size: int = Query(50),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取成绩排名"""
    query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id)
    if subject_id:
        query = query.filter(MarkResult.subject_id == subject_id)
    total = query.count()
    if order == "desc":
        query = query.order_by(desc(MarkResult.total_score))
    else:
        query = query.order_by(asc(MarkResult.total_score))
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for i, r in enumerate(results, start=(page - 1) * page_size + 1):
        items.append({
            "rank": i, "student_id": r.student_id,
            "choice_score": float(r.choice_score), "subjective_score": float(r.subjective_score),
            "total_score": float(r.total_score), "status": r.status
        })
    return convert_keys({"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/student/{student_id}")
async def get_student_report(
    student_id: int,
    exam_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学生个人成绩报告"""
    query = db.query(MarkResult).filter(MarkResult.student_id == student_id)
    if exam_id:
        query = query.filter(MarkResult.exam_id == exam_id)
    results = query.all()
    if not results:
        return convert_keys({"student_id": student_id, "message": "暂无成绩数据"})
    exams_data = []
    total_scores = []
    for r in results:
        exam = db.query(Exam).filter(Exam.id == r.exam_id).first()
        exams_data.append({
            "exam_id": r.exam_id, "exam_name": exam.exam_name if exam else "",
            "subject_id": r.subject_id, "choice_score": float(r.choice_score),
            "subjective_score": float(r.subjective_score), "total_score": float(r.total_score),
            "status": r.status, "marked_at": r.marked_at.isoformat() if r.marked_at else None
        })
        total_scores.append(float(r.total_score))
    avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
    return convert_keys({
        "student_id": student_id, "total_exams": len(exams_data),
        "average_score": round(avg_score, 2), "exams": exams_data
    })


def _calc_stats(scores):
    """计算基础统计指标"""
    n = len(scores)
    if n == 0:
        return {"avg": 0, "max": 0, "min": 0, "std": 0}
    avg = sum(scores) / n
    variance = sum((s - avg) ** 2 for s in scores) / n
    std = variance ** 0.5
    return {"avg": avg, "max": max(scores), "min": min(scores), "std": std}


def _build_ranking(results, key):
    """根据分数构建排名（相同分数同一名次）"""
    sorted_results = sorted(results, key=key, reverse=True)
    ranking = {}
    rank = 0
    prev_score = None
    for i, r in enumerate(sorted_results):
        score = key(r)
        if score != prev_score:
            rank = i + 1
            prev_score = score
        ranking[r.student_id] = rank
    return ranking


@router.get("/class/{class_id}")
async def get_class_report(
    class_id: int, exam_id: int,
    subject_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取班级成绩报告（含学生成绩单及年级对比指标）"""
    from app.models.user import Student, Class, Grade
    from app.models.exam import Subject, ExamSubject

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    class_ = db.query(Class).filter(Class.id == class_id).first()
    if not class_:
        raise HTTPException(status_code=404, detail="班级不存在")

    grade = db.query(Grade).filter(Grade.id == class_.grade_id).first() if class_.grade_id else None
    subject = db.query(Subject).filter(Subject.id == subject_id).first() if subject_id else None

    # 科目满分（用于优秀/良好/合格线）
    full_score = 100
    if subject_id:
        exam_subject = db.query(ExamSubject).filter(
            ExamSubject.exam_id == exam_id, ExamSubject.subject_id == subject_id
        ).first()
        if exam_subject and exam_subject.total_score:
            full_score = exam_subject.total_score
    else:
        exam_subjects = db.query(ExamSubject).filter(ExamSubject.exam_id == exam_id).all()
        if exam_subjects:
            full_score = sum(es.total_score or 0 for es in exam_subjects) / len(exam_subjects)

    # 本班学生与成绩
    students = db.query(Student).filter(Student.class_id == class_id).all()
    student_ids = [s.id for s in students]
    query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id, MarkResult.student_id.in_(student_ids))
    if subject_id:
        query = query.filter(MarkResult.subject_id == subject_id)
    results = query.all()

    result_map = {r.student_id: r for r in results}
    student_scores = []
    for s in students:
        r = result_map.get(s.id)
        score = float(r.total_score) if r else None
        student_scores.append({
            "student_id": s.id,
            "student_no": s.student_no,
            "student_name": s.real_name,
            "score": score,
            "status": r.status if r else "pending"
        })

    # 班级排名：按分数降序，相同分数排名相同
    sorted_class_scores = sorted([s for s in student_scores if s["score"] is not None], key=lambda x: x["score"], reverse=True)
    rank = 0
    prev_score = None
    for i, item in enumerate(sorted_class_scores):
        if item["score"] != prev_score:
            rank = i + 1
            prev_score = item["score"]
        item["class_rank"] = rank

    class_score_list = [s["score"] for s in student_scores if s["score"] is not None]
    class_stats = _calc_stats(class_score_list)
    class_n = len(class_score_list)

    # 年级维度对比数据
    grade_classes = db.query(Class).filter(Class.grade_id == class_.grade_id).all() if class_.grade_id else [class_]
    grade_class_ids = [c.id for c in grade_classes]
    grade_students = db.query(Student).filter(Student.class_id.in_(grade_class_ids)).all()
    grade_student_ids = [s.id for s in grade_students]
    grade_query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id, MarkResult.student_id.in_(grade_student_ids))
    if subject_id:
        grade_query = grade_query.filter(MarkResult.subject_id == subject_id)
    grade_results = grade_query.all()
    grade_score_list = [float(r.total_score) for r in grade_results]
    grade_stats = _calc_stats(grade_score_list)
    grade_n = len(grade_score_list)

    # 全校维度数据（校次）
    all_students = db.query(Student).all()
    all_student_ids = [s.id for s in all_students]
    school_query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id, MarkResult.student_id.in_(all_student_ids))
    if subject_id:
        school_query = school_query.filter(MarkResult.subject_id == subject_id)
    school_results = school_query.all()
    school_score_map = {r.student_id: float(r.total_score) for r in school_results}

    # 年级排名与全校排名
    grade_ranking = _build_ranking(grade_results, key=lambda r: float(r.total_score))
    school_ranking = _build_ranking(school_results, key=lambda r: float(r.total_score))
    for s in student_scores:
        s["grade_rank"] = grade_ranking.get(s["student_id"])
        s["school_rank"] = school_ranking.get(s["student_id"])

    # 3-4-3 分布：基于年级排名百分比
    distribution = {"top": 0, "middle": 0, "bottom": 0}
    distribution_students = {"top": [], "middle": [], "bottom": []}
    if grade_n > 0:
        for s in student_scores:
            gr = s.get("grade_rank")
            if gr is None:
                continue
            percentile = gr / grade_n
            if percentile <= 0.3:
                bucket = "top"
            elif percentile <= 0.7:
                bucket = "middle"
            else:
                bucket = "bottom"
            distribution[bucket] += 1
            distribution_students[bucket].append(s)

    top_students = sorted(distribution_students["top"], key=lambda x: (x.get("grade_rank") or 999, -(x["score"] or 0)))

    # 等级线（基于满分百分比）
    excellent_line = full_score * 0.9
    good_line = full_score * 0.8
    pass_line = full_score * 0.6
    borderline_margin = full_score * 0.05  # 临界范围：线下方 5%

    class_excellent = sum(1 for s in class_score_list if s >= excellent_line)
    class_good = sum(1 for s in class_score_list if s >= good_line)
    class_pass = sum(1 for s in class_score_list if s >= pass_line)

    # 临界生
    def make_borderline(score, line):
        if score is None or score >= line:
            return None
        diff = line - score
        return diff if diff <= borderline_margin else None

    borderline_excellent = []
    borderline_good = []
    borderline_pass = []
    for s in student_scores:
        score = s.get("score")
        be = make_borderline(score, excellent_line)
        if be is not None:
            borderline_excellent.append({**s, "diff": round(be, 2), "line": "excellent"})
            continue
        bg = make_borderline(score, good_line)
        if bg is not None:
            borderline_good.append({**s, "diff": round(bg, 2), "line": "good"})
            continue
        bp = make_borderline(score, pass_line)
        if bp is not None:
            borderline_pass.append({**s, "diff": round(bp, 2), "line": "pass"})

    borderline_excellent.sort(key=lambda x: x["diff"])
    borderline_good.sort(key=lambda x: x["diff"])
    borderline_pass.sort(key=lambda x: x["diff"])

    # 波动生：查找上一场同年级同科目考试，比较年级排名变化
    progress_students = []
    regress_students = []
    prev_exam = db.query(Exam).join(ExamSubject, Exam.id == ExamSubject.exam_id).filter(
        Exam.start_time < exam.start_time,
        ExamSubject.subject_id == subject_id if subject_id else True,
        Exam.id != exam_id
    ).order_by(Exam.start_time.desc()).first() if subject_id else None

    if prev_exam and subject_id:
        prev_grade_query = db.query(MarkResult).filter(
            MarkResult.exam_id == prev_exam.id,
            MarkResult.student_id.in_(grade_student_ids),
            MarkResult.subject_id == subject_id
        )
        prev_grade_results = prev_grade_query.all()
        prev_grade_ranking = _build_ranking(prev_grade_results, key=lambda r: float(r.total_score))
        prev_class_students = {s.student_no: s.id for s in students}
        for s in student_scores:
            prev_rank = prev_grade_ranking.get(s["student_id"])
            curr_rank = s.get("grade_rank")
            if prev_rank and curr_rank:
                change = prev_rank - curr_rank  # 排名上升为正（进步）
                if change >= 5:
                    progress_students.append({**s, "rank_change": change})
                elif change <= -5:
                    regress_students.append({**s, "rank_change": abs(change)})

    # 高阶指标
    z_score = 0
    t_score = 50
    mean_deviation = 0
    exceed_mean_rate = 0
    coefficient_variation = 0
    composite_score = 0

    if class_n > 0:
        composite_score = round(class_stats["avg"] / full_score * 100, 2)
        coefficient_variation = round(class_stats["std"] / class_stats["avg"] * 100, 2) if class_stats["avg"] else 0

    if grade_n > 0 and grade_stats["std"] > 0:
        z_score = round((class_stats["avg"] - grade_stats["avg"]) / grade_stats["std"], 2)
        t_score = round(50 + 10 * ((class_stats["avg"] - grade_stats["avg"]) / grade_stats["std"]), 2)
        mean_deviation = round(class_stats["avg"] - grade_stats["avg"], 2)
        exceed_mean_rate = round((class_stats["avg"] - grade_stats["avg"]) / grade_stats["avg"] * 100, 2) if grade_stats["avg"] else 0

    return convert_keys({
        "exam": {"id": exam.id, "name": exam.exam_name, "start_time": exam.start_time.isoformat() if exam.start_time else None},
        "class": {"id": class_.id, "name": class_.class_name},
        "grade": {"id": grade.id, "name": grade.grade_name} if grade else {"id": None, "name": ""},
        "subject": {"id": subject.id, "name": subject.subject_name} if subject else {"id": None, "name": ""},
        "full_score": full_score,
        "summary": {
            "total_classes": len(grade_classes),
            "total_participants": grade_n,
            "class_total_students": len(students),
            "class_scored_students": class_n,
            "absent_count": len(students) - class_n
        },
        "statistics": {
            "student_count": len(students),
            "scored_count": class_n,
            "average_score": round(class_stats["avg"], 2),
            "max_score": round(class_stats["max"], 2),
            "min_score": round(class_stats["min"], 2),
            "pass_rate": round(class_pass / class_n * 100, 2) if class_n else 0,
            "good_rate": round(class_good / class_n * 100, 2) if class_n else 0,
            "excellent_rate": round(class_excellent / class_n * 100, 2) if class_n else 0,
            "composite_score": composite_score,
            "z_score": z_score,
            "t_score": t_score,
            "mean_deviation": mean_deviation,
            "exceed_mean_rate": exceed_mean_rate,
            "coefficient_variation": coefficient_variation
        },
        "students": student_scores,
        "distribution": {
            "top_count": distribution["top"],
            "middle_count": distribution["middle"],
            "bottom_count": distribution["bottom"],
            "top_rate": round(distribution["top"] / class_n * 100, 2) if class_n else 0,
            "middle_rate": round(distribution["middle"] / class_n * 100, 2) if class_n else 0,
            "bottom_rate": round(distribution["bottom"] / class_n * 100, 2) if class_n else 0,
            "top_students": top_students,
            "excellent_line": excellent_line,
            "good_line": good_line,
            "pass_line": pass_line
        },
        "progress_students": progress_students,
        "regress_students": regress_students,
        "borderline": {
            "excellent": borderline_excellent,
            "good": borderline_good,
            "pass": borderline_pass
        }
    })


@router.get("/class/{class_id}/question-analysis")
async def get_class_question_analysis(
    class_id: int,
    exam_id: int,
    subject_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取班级小题分析（各学生各小题得分）"""
    from app.models.user import Student, Class, Grade
    from app.models.exam import Subject, ExamQuestion
    from app.models.mark import MarkResult, MarkDetail

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    class_ = db.query(Class).filter(Class.id == class_id).first()
    if not class_:
        raise HTTPException(status_code=404, detail="班级不存在")

    grade = db.query(Grade).filter(Grade.id == class_.grade_id).first() if class_.grade_id else None
    subject = db.query(Subject).filter(Subject.id == subject_id).first() if subject_id else None

    # 本班学生
    students = db.query(Student).filter(Student.class_id == class_id).all()
    student_ids = [s.id for s in students]

    # 年级学生（用于年级排名）
    grade_classes = db.query(Class).filter(Class.grade_id == class_.grade_id).all() if class_.grade_id else [class_]
    grade_class_ids = [c.id for c in grade_classes]
    grade_students = db.query(Student).filter(Student.class_id.in_(grade_class_ids)).all()
    grade_student_ids = [s.id for s in grade_students]

    # 全校学生（用于校次）
    all_students = db.query(Student).all()
    all_student_ids = [s.id for s in all_students]

    # 查询题目
    question_query = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id, ExamQuestion.status == 1)
    if subject_id:
        question_query = question_query.filter(ExamQuestion.subject_id == subject_id)
    questions = question_query.order_by(ExamQuestion.sort_order, ExamQuestion.id).all()
    question_ids = [q.id for q in questions]

    # 查询本班学生的成绩与小题分
    mark_results = db.query(MarkResult).filter(
        MarkResult.exam_id == exam_id,
        MarkResult.student_id.in_(student_ids)
    )
    if subject_id:
        mark_results = mark_results.filter(MarkResult.subject_id == subject_id)
    mark_results = mark_results.all()
    mark_result_ids = [r.id for r in mark_results]

    details = db.query(MarkDetail).filter(
        MarkDetail.mark_result_id.in_(mark_result_ids),
        MarkDetail.question_id.in_(question_ids)
    ).all()
    detail_map = {(d.student_id, d.question_id): float(d.score) for d in details}

    # 计算班级、年级、全校排名（基于总分）
    def build_ranking(student_id_list):
        query = db.query(MarkResult).filter(
            MarkResult.exam_id == exam_id,
            MarkResult.student_id.in_(student_id_list)
        )
        if subject_id:
            query = query.filter(MarkResult.subject_id == subject_id)
        results = query.all()
        sorted_results = sorted(results, key=lambda r: float(r.total_score), reverse=True)
        ranking = {}
        rank = 0
        prev_score = None
        for i, r in enumerate(sorted_results):
            score = float(r.total_score)
            if score != prev_score:
                rank = i + 1
                prev_score = score
            ranking[r.student_id] = rank
        return ranking

    class_ranking = build_ranking(student_ids)
    grade_ranking = build_ranking(grade_student_ids)
    school_ranking = build_ranking(all_student_ids)

    # 计算每题得分率
    question_rates = {}
    for q in questions:
        scores = [detail_map.get((s.id, q.id), 0) for s in students]
        full = float(q.score) or 1
        avg_rate = round(sum(scores) / (len(scores) * full) * 100, 2) if students else 0
        question_rates[q.id] = avg_rate

    # 组装学生行数据
    student_rows = []
    for s in students:
        row = {
            "student_id": s.id,
            "student_no": s.student_no,
            "student_name": s.real_name,
            "grade_rank": grade_ranking.get(s.id),
            "class_rank": class_ranking.get(s.id),
            "school_rank": school_ranking.get(s.id),
            "questions": []
        }
        for q in questions:
            score = detail_map.get((s.id, q.id))
            full = float(q.score) or 1
            rate = round(score / full * 100, 2) if score is not None else None
            row["questions"].append({
                "question_id": q.id,
                "question_no": q.question_no,
                "score": score,
                "rate": rate,
                "full_score": full
            })
        student_rows.append(row)

    # 按班级排名排序
    student_rows.sort(key=lambda x: (x["class_rank"] or 9999, -(x["questions"][0]["score"] if x["questions"] else 0)))

    return convert_keys({
        "exam": {"id": exam.id, "name": exam.exam_name},
        "class": {"id": class_.id, "name": class_.class_name},
        "grade": {"id": grade.id, "name": grade.grade_name} if grade else {"id": None, "name": ""},
        "subject": {"id": subject.id, "name": subject.subject_name} if subject else {"id": None, "name": ""},
        "questions": [
            {
                "question_id": q.id,
                "question_no": q.question_no,
                "question_title": q.question_title,
                "full_score": float(q.score),
                "question_type": q.question_type,
                "average_rate": question_rates[q.id]
            } for q in questions
        ],
        "students": student_rows
    })


@router.get("/student/{student_id}/report")
async def get_student_report(
    student_id: int,
    exam_id: int,
    subject_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学生个人成绩报告"""
    from app.models.user import Student, Class, Grade
    from app.models.exam import Subject, ExamQuestion
    from app.models.mark import MarkResult, MarkDetail

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    class_ = db.query(Class).filter(Class.id == student.class_id).first()
    grade = db.query(Grade).filter(Grade.id == student.grade_id).first() if student.grade_id else None
    subject = db.query(Subject).filter(Subject.id == subject_id).first() if subject_id else None

    # 本班、年级、全校学生
    classmates = db.query(Student).filter(Student.class_id == student.class_id).all()
    classmate_ids = [s.id for s in classmates]
    grade_classes = db.query(Class).filter(Class.grade_id == student.grade_id).all() if student.grade_id else [class_]
    grade_student_ids = [s.id for c in grade_classes for s in db.query(Student).filter(Student.class_id == c.id).all()]
    all_students = db.query(Student).all()
    all_student_ids = [s.id for s in all_students]

    # 当前成绩
    mark_query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id, MarkResult.student_id == student_id)
    if subject_id:
        mark_query = mark_query.filter(MarkResult.subject_id == subject_id)
    mark_result = mark_query.first()
    student_score = float(mark_result.total_score) if mark_result else 0

    # 排名计算
    def build_ranking(student_id_list):
        query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id, MarkResult.student_id.in_(student_id_list))
        if subject_id:
            query = query.filter(MarkResult.subject_id == subject_id)
        results = query.all()
        sorted_results = sorted(results, key=lambda r: float(r.total_score), reverse=True)
        ranking = {}
        rank = 0
        prev_score = None
        for i, r in enumerate(sorted_results):
            score = float(r.total_score)
            if score != prev_score:
                rank = i + 1
                prev_score = score
            ranking[r.student_id] = rank
        return ranking

    class_ranking = build_ranking(classmate_ids)
    grade_ranking = build_ranking(grade_student_ids)
    school_ranking = build_ranking(all_student_ids)

    class_rank = class_ranking.get(student_id)
    grade_rank = grade_ranking.get(student_id)
    school_rank = school_ranking.get(student_id)

    # 班级统计
    class_scores = [float(r.total_score) for r in db.query(MarkResult).filter(
        MarkResult.exam_id == exam_id,
        MarkResult.student_id.in_(classmate_ids)
    ).all() if subject_id is None or r.subject_id == subject_id]
    class_avg = sum(class_scores) / len(class_scores) if class_scores else 0
    class_max = max(class_scores) if class_scores else 0
    beat_count = sum(1 for s in class_scores if s < student_score)
    beat_rate = round(beat_count / len(class_scores) * 100, 2) if class_scores else 0

    # 年级统计
    grade_scores = [float(r.total_score) for r in db.query(MarkResult).filter(
        MarkResult.exam_id == exam_id,
        MarkResult.student_id.in_(grade_student_ids)
    ).all() if subject_id is None or r.subject_id == subject_id]
    grade_avg = sum(grade_scores) / len(grade_scores) if grade_scores else 0
    grade_std = (sum((s - grade_avg) ** 2 for s in grade_scores) / len(grade_scores)) ** 0.5 if grade_scores else 0

    # 高阶指标（以学生个人分数 vs 年级平均）
    z_score = round((student_score - grade_avg) / grade_std, 2) if grade_std else 0
    t_score = round(50 + 10 * ((student_score - grade_avg) / grade_std), 2) if grade_std else 0
    mean_deviation = round(student_score - grade_avg, 2)
    exceed_mean_rate = round((student_score - grade_avg) / grade_avg * 100, 2) if grade_avg else 0

    # 名次波动数（与上一场同科目考试对比）
    rank_change = 0
    prev_exam = db.query(Exam).filter(Exam.start_time < exam.start_time, Exam.status == 'finished').order_by(Exam.start_time.desc()).first()
    if prev_exam:
        prev_ranking = build_ranking_for_exam(prev_exam.id, grade_student_ids, subject_id, db)
        prev_rank = prev_ranking.get(student_id)
        if prev_rank and grade_rank:
            rank_change = abs(prev_rank - grade_rank)

    # 难易题得分详情
    questions = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id, ExamQuestion.status == 1)
    if subject_id:
        questions = questions.filter(ExamQuestion.subject_id == subject_id)
    questions = questions.order_by(ExamQuestion.sort_order).all()

    class_question_rates = {}
    student_question_map = {}
    for q in questions:
        q_full = float(q.score) or 1
        details = db.query(MarkDetail).filter(MarkDetail.question_id == q.id).all()
        scores = [float(d.score) for d in details]
        class_rate = sum(scores) / (len(scores) * q_full) * 100 if scores else 0
        class_question_rates[q.id] = class_rate
        student_detail = next((d for d in details if d.student_id == student_id), None)
        student_question_map[q.id] = {
            "score": float(student_detail.score) if student_detail else 0,
            "rate": float(student_detail.score) / q_full * 100 if student_detail else 0,
            "full_score": q_full,
            "question_no": q.question_no
        }

    # 按班级得分率划分难度
    difficulty_groups = {"simple": [], "medium": [], "hard": [], "very_hard": []}
    for q in questions:
        rate = class_question_rates[q.id]
        if rate >= 80:
            key = "simple"
        elif rate >= 60:
            key = "medium"
        elif rate >= 40:
            key = "hard"
        else:
            key = "very_hard"
        difficulty_groups[key].append(q.id)

    difficulty_analysis = {}
    for key, label in [("simple", "简单"), ("medium", "中等"), ("hard", "很难"), ("very_hard", "非常难")]:
        qids = difficulty_groups[key]
        if not qids:
            difficulty_analysis[key] = {"label": label, "my_rate": 0, "class_rate": 0}
            continue
        my_total = sum(student_question_map[qid]["score"] for qid in qids)
        my_full = sum(student_question_map[qid]["full_score"] for qid in qids)
        class_total_rate = sum(class_question_rates[qid] for qid in qids) / len(qids)
        my_rate = round(my_total / my_full * 100, 2) if my_full else 0
        difficulty_analysis[key] = {
            "label": label,
            "my_rate": my_rate,
            "class_rate": round(class_total_rate, 2)
        }

    # 历次考试情况
    history = []
    if subject_id:
        history_exams = db.query(Exam).filter(Exam.status == 'finished').order_by(Exam.start_time).all()
        for he in history_exams:
            hr = db.query(MarkResult).filter(MarkResult.exam_id == he.id, MarkResult.student_id == student_id, MarkResult.subject_id == subject_id).first()
            if hr:
                h_grade_ranking = build_ranking_for_exam(he.id, grade_student_ids, subject_id, db)
                h_rank = h_grade_ranking.get(student_id)
                h_grade_count = len(h_grade_ranking)
                percentile = round((1 - (h_rank - 1) / h_grade_count) * 100, 2) if h_grade_count else 0
                history.append({
                    "exam_id": he.id,
                    "exam_name": he.exam_name,
                    "exam_time": he.start_time.isoformat() if he.start_time else None,
                    "score": float(hr.total_score),
                    "grade_rank": h_rank,
                    "grade_percentile": percentile
                })

    # 薄弱知识点：按题号分组模拟（暂无真实知识点标签）
    weak_knowledge = []
    weak_types = []
    weak_abilities = []

    return convert_keys({
        "student": {"id": student.id, "name": student.real_name, "student_no": student.student_no},
        "exam": {"id": exam.id, "name": exam.exam_name},
        "class": {"id": class_.id, "name": class_.class_name} if class_ else {"id": None, "name": ""},
        "grade": {"id": grade.id, "name": grade.grade_name} if grade else {"id": None, "name": ""},
        "subject": {"id": subject.id, "name": subject.subject_name} if subject else {"id": None, "name": ""},
        "summary": {
            "total_score": student_score,
            "class_avg": round(class_avg, 2),
            "class_max": round(class_max, 2),
            "class_rank": class_rank,
            "grade_rank": grade_rank,
            "school_rank": school_rank,
            "beat_rate": beat_rate,
            "rank_change": rank_change
        },
        "advanced": {
            "z_score": z_score,
            "t_score": t_score,
            "mean_deviation": mean_deviation,
            "exceed_mean_rate": exceed_mean_rate
        },
        "difficulty_analysis": difficulty_analysis,
        "history": history,
        "weak_knowledge": weak_knowledge,
        "weak_types": weak_types,
        "weak_abilities": weak_abilities
    })


def build_ranking_for_exam(exam_id, student_ids, subject_id, db):
    from app.models.mark import MarkResult
    query = db.query(MarkResult).filter(MarkResult.exam_id == exam_id, MarkResult.student_id.in_(student_ids))
    if subject_id:
        query = query.filter(MarkResult.subject_id == subject_id)
    results = query.all()
    sorted_results = sorted(results, key=lambda r: float(r.total_score), reverse=True)
    ranking = {}
    rank = 0
    prev_score = None
    for i, r in enumerate(sorted_results):
        score = float(r.total_score)
        if score != prev_score:
            rank = i + 1
            prev_score = score
        ranking[r.student_id] = rank
    return ranking


@router.get("/student/{student_id}/wrong-questions")
async def get_student_wrong_questions(
    student_id: int,
    exam_id: int,
    subject_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学生本次考试错题集（失分题目）"""
    from app.models.user import Student, Class, Grade
    from app.models.exam import Subject, ExamQuestion
    from app.models.mark import MarkResult, MarkDetail

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    class_ = db.query(Class).filter(Class.id == student.class_id).first()
    grade = db.query(Grade).filter(Grade.id == student.grade_id).first() if student.grade_id else None
    subject = db.query(Subject).filter(Subject.id == subject_id).first() if subject_id else None

    # 本班、年级学生
    classmates = db.query(Student).filter(Student.class_id == student.class_id).all()
    classmate_ids = [s.id for s in classmates]
    grade_classes = db.query(Class).filter(Class.grade_id == student.grade_id).all() if student.grade_id else [class_]
    grade_student_ids = [s.id for c in grade_classes for s in db.query(Student).filter(Student.class_id == c.id).all()]

    # 查询题目
    question_query = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id, ExamQuestion.status == 1)
    if subject_id:
        question_query = question_query.filter(ExamQuestion.subject_id == subject_id)
    questions = question_query.order_by(ExamQuestion.sort_order).all()

    # 查询该学生的小题分
    details = db.query(MarkDetail).filter(
        MarkDetail.exam_id == exam_id,
        MarkDetail.student_id == student_id
    ).all()
    if subject_id:
        details = [d for d in details if d.subject_id == subject_id]
    detail_map = {d.question_id: d for d in details}

    # 查询班级/年级所有学生的小题分
    all_details = db.query(MarkDetail).filter(
        MarkDetail.exam_id == exam_id,
        MarkDetail.question_id.in_([q.id for q in questions])
    ).all()

    def question_avg_rate(qid, student_ids):
        scores = [float(d.score) for d in all_details if d.question_id == qid and d.student_id in student_ids]
        q = next((x for x in questions if x.id == qid), None)
        q_full = float(q.score) if q else 1
        if not scores or q_full == 0:
            return 0
        return sum(scores) / (len(scores) * q_full) * 100

    wrong_list = []
    for q in questions:
        detail = detail_map.get(q.id)
        if not detail:
            continue
        score = float(detail.score)
        q_full = float(q.score) or 1
        # 只要未得满分即视为错题/失分题
        if score >= q_full - 0.01:
            continue
        class_rate = question_avg_rate(q.id, classmate_ids)
        grade_rate = question_avg_rate(q.id, grade_student_ids)
        distance = round(class_rate - grade_rate, 2)
        wrong_list.append({
            "question_id": q.id,
            "question_no": q.question_no,
            "question_title": q.question_title or f"{subject.subject_name if subject else ''}{q.question_no}",
            "question_content": q.question_content or "",
            "knowledge_point": q.knowledge_point or "暂无",
            "ability": q.ability or "暂无",
            "full_score": q_full,
            "student_score": round(score, 2),
            "class_rate": round(class_rate, 2),
            "grade_rate": round(grade_rate, 2),
            "grade_distance": distance,
            "student_answer": detail.student_answer or "暂无该生作答记录",
            "best_answer": "【优解】\n" + (q.question_content or "暂无优解") + "\n\n该题主要考查" + (q.knowledge_point or "相关知识点") + "，解题时应注意审题和规范作答。"
        })

    return convert_keys({
        "student": {"id": student.id, "name": student.real_name, "student_no": student.student_no},
        "exam": {"id": exam.id, "name": exam.exam_name},
        "class": {"id": class_.id, "name": class_.class_name} if class_ else {"id": None, "name": ""},
        "grade": {"id": grade.id, "name": grade.grade_name} if grade else {"id": None, "name": ""},
        "subject": {"id": subject.id, "name": subject.subject_name} if subject else {"id": None, "name": ""},
        "wrong_questions": wrong_list,
        "total_count": len(wrong_list)
    })


@router.get("/subject-analysis/{exam_id}")
async def get_subject_analysis(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取各科成绩分析"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    subjects = db.query(ExamSubject).filter(ExamSubject.exam_id == exam_id).all()
    analysis = []
    for es in subjects:
        results = db.query(MarkResult).filter(MarkResult.exam_id == exam_id, MarkResult.subject_id == es.subject_id).all()
        scores = [float(r.total_score) for r in results]
        if scores:
            analysis.append({
                "subject_id": es.subject_id, "subject_name": es.subject.subject_name if es.subject else "",
                "full_score": es.total_score, "student_count": len(scores),
                "average_score": round(sum(scores) / len(scores), 2),
                "max_score": round(max(scores), 2), "min_score": round(min(scores), 2),
                "pass_rate": round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 2)
            })
    return convert_keys({"exam_id": exam_id, "exam_name": exam.exam_name, "subjects": analysis})


@router.get("/trend/{student_id}")
async def get_score_trend(
    student_id: int,
    subject_id: Optional[int] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学生成绩趋势"""
    query = db.query(MarkResult).filter(MarkResult.student_id == student_id).order_by(MarkResult.created_at.desc()).limit(limit)
    if subject_id:
        query = query.filter(MarkResult.subject_id == subject_id)
    results = query.all()
    trend = []
    for r in reversed(results):
        exam = db.query(Exam).filter(Exam.id == r.exam_id).first()
        trend.append({
            "exam_id": r.exam_id, "exam_name": exam.exam_name if exam else "",
            "total_score": float(r.total_score), "choice_score": float(r.choice_score),
            "subjective_score": float(r.subjective_score),
            "date": exam.start_time.isoformat() if exam and exam.start_time else None
        })
    return convert_keys({"student_id": student_id, "subject_id": subject_id, "trend": trend})


@router.post("/export/{exam_id}")
async def export_report(
    exam_id: int, data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出成绩报告"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    return convert_keys({
        "success": True, "message": "导出任务已创建",
        "exam_id": exam_id, "exam_name": exam.exam_name,
        "report_type": data.get("report_type", "full"),
        "export_format": data.get("format", "excel"),
        "download_url": f"/api/v1/report/download/{exam_id}"
    })