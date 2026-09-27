#!/usr/bin/env python3
"""
学生个人报告功能模拟数据脚本
插入年级、班级、学生、考试、科目、题目、成绩、小题分等数据
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, init_db
from app.models.user import Grade, Class, Student
from app.models.exam import Exam, Subject, ExamSubject, ExamQuestion
from app.models.mark import MarkResult, MarkDetail
from app.models.scan import ScanPage


def get_or_create_subjects(db):
    subjects = db.query(Subject).all()
    if not subjects:
        subject_data = [
            ("语文", "chinese"),
            ("数学", "math"),
            ("英语", "english"),
            ("物理", "physics"),
            ("化学", "chemistry"),
        ]
        for i, (name, code) in enumerate(subject_data):
            db.add(Subject(subject_name=name, subject_code=code, sort_order=i, status=1))
        db.commit()
        subjects = db.query(Subject).all()
    return subjects


def get_or_create_grades(db):
    grades = db.query(Grade).filter(Grade.grade_level.in_([7, 8, 9])).all()
    if not grades:
        for i, name in enumerate(["七年级", "八年级", "九年级"], start=7):
            db.add(Grade(grade_name=name, grade_level=i))
        db.commit()
        grades = db.query(Grade).filter(Grade.grade_level.in_([7, 8, 9])).all()
    return grades


def get_or_create_classes(db, grade, count=3):
    classes = db.query(Class).filter(Class.grade_id == grade.id).all()
    if not classes:
        for i in range(1, count + 1):
            db.add(Class(class_name=f"{grade.grade_name}{i}班", grade_id=grade.id))
        db.commit()
        classes = db.query(Class).filter(Class.grade_id == grade.id).all()
    return classes


def create_students(db, classes, count_per_class=15):
    students = []
    for cls in classes:
        existing = db.query(Student).filter(Student.class_id == cls.id).count()
        if existing >= count_per_class:
            students.extend(db.query(Student).filter(Student.class_id == cls.id).all())
            continue
        for i in range(existing + 1, count_per_class + 1):
            s = Student(
                student_no=f"2024{cls.grade_id:02d}{cls.id:03d}{i:02d}",
                real_name=f"学生{cls.grade_id}{cls.id}{i:02d}",
                class_id=cls.id,
                grade_id=cls.grade_id,
                gender=random.choice(["男", "女"]),
                status=1
            )
            db.add(s)
            students.append(s)
    db.commit()
    return students


def create_exam(db, name, grade, subjects, start_time, status="finished"):
    exam = db.query(Exam).filter(Exam.exam_name == name).first()
    if exam:
        return exam
    exam = Exam(
        exam_name=name,
        exam_type="midterm",
        exam_level="school",
        grade_id=grade.id,
        grade=grade.grade_name,
        start_time=start_time,
        end_time=start_time + timedelta(hours=8),
        status=status,
        total_score=sum(150 if s.subject_name in ["语文", "数学", "英语"] else 100 for s in subjects[:3]),
        total_students=45
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def create_exam_subjects(db, exam, subjects):
    existing = db.query(ExamSubject).filter(ExamSubject.exam_id == exam.id).all()
    if existing:
        return existing
    exam_subjects = []
    for s in subjects:
        full = 150 if s.subject_name in ["语文", "数学", "英语"] else 100
        es = ExamSubject(exam_id=exam.id, subject_id=s.id, total_score=full)
        db.add(es)
        exam_subjects.append(es)
    db.commit()
    return exam_subjects


def make_question_meta(subject_name, idx):
    """按科目和题号生成模拟题目元数据（题号使用数字字符串，与前端题号选择保持一致）"""
    if subject_name == "语文":
        meta = [
            ("1", "古诗文默写", "识记", "补写出下列句子中的空缺部分。\n（1）长风破浪会有时，____________。\n（2）____________，化作春泥更护花。"),
            ("2", "词语运用", "理解", "下列句子中加点词语使用不正确的一项是（  ）\nA. 他学习刻苦，成绩优异。\nB. 这篇文章写得栩栩如生。\nC. 他做事总是马马虎虎。\nD. 这道题轻而易举地解决了。"),
            ("3", "病句辨析", "应用", "下列句子没有语病的一项是（  ）\nA. 通过这次活动，使我深受教育。\nB. 我们要认真改正并找出作业中的错误。\nC. 能否取得好成绩，关键在于平时的努力。\nD. 他的写作水平明显提高了。"),
            ("4", "现代文阅读", "综合分析", "阅读下面的文章，完成题目。\n文章节选：……作者在文中表达了对故乡的思念之情。\n1. 文章开头描写环境的作用是？\n2. 赏析文中画线句子的表达效果。\n3. 结合全文，分析作者情感变化。"),
            ("5", "作文", "表达", "请以《那一刻，我长大了》为题，写一篇不少于 600 字的记叙文。要求：内容具体，感情真挚，条理清楚。"),
        ]
    elif subject_name == "数学":
        meta = [
            ("1", "实数运算", "运算", "计算：(-2)^2 + √9 - |1 - √2|"),
            ("2", "方程与不等式", "理解", "解不等式组，并把解集在数轴上表示出来：\n{ 2x - 1 > 3 \n{ x + 4 ≤ 7"),
            ("3", "函数图像", "应用", "已知二次函数 y = x^2 - 4x + 3。\n（1）求该函数图像的顶点坐标；\n（2）求函数图像与 x 轴的交点坐标。"),
            ("4", "几何证明", "推理", "如图，在△ABC 中，D、E 分别是 AB、AC 的中点。求证：DE ∥ BC 且 DE = 1/2 BC。"),
            ("5", "综合应用", "综合分析", "某商店销售一种商品，每件进价 40 元，售价为 60 元时每天可售出 200 件。经调查发现，售价每降低 1 元，每天可多售出 20 件。设降价 x 元，每天利润为 y 元。\n（1）求 y 与 x 的函数关系式；\n（2）当售价为多少时，每天利润最大？"),
        ]
    elif subject_name == "英语":
        meta = [
            ("1", "词汇辨析", "识记", "Choose the best answer to complete the sentence.\nThe weather is _______ worse than yesterday.\nA. very  B. much  C. too  D. so"),
            ("2", "时态语态", "理解", "Complete the sentence with the correct form of the verb.\nBy the time I got to the station, the train _______.\nA. left  B. had left  C. has left  D. leaves"),
            ("3", "阅读理解", "应用", "Read the passage and answer the questions.\nPassage: ...\n1. What is the main idea of the passage?"),
            ("4", "完形填空", "综合分析", "Complete the passage with the proper words.\nOnce upon a time, there was a little girl ..."),
            ("5", "书面表达", "表达", "Write a short passage of about 80 words on the topic 'My Favorite Season'."),
        ]
    else:
        meta = [
            (str(i), f"{subject_name}知识点{i}", "理解", f"{subject_name}第{i}题题目内容...")
            for i in range(1, 6)
        ]
    return meta[idx] if idx < len(meta) else (str(idx + 1), "综合", "理解", "题目内容")


def create_exam_questions(db, exam, subject, full_score):
    existing = db.query(ExamQuestion).filter(
        ExamQuestion.exam_id == exam.id,
        ExamQuestion.subject_id == subject.id
    ).all()
    if existing:
        return existing
    questions = []
    count = 5 if subject.subject_name in ["语文", "数学", "英语"] else 4
    score_per = full_score / count
    for i in range(count):
        question_no, knowledge, ability, content = make_question_meta(subject.subject_name, i)
        q = ExamQuestion(
            exam_id=exam.id,
            subject_id=subject.id,
            question_no=question_no,
            question_title=f"{subject.subject_name}{question_no}",
            question_content=content,
            knowledge_point=knowledge,
            ability=ability,
            score=round(score_per, 2),
            question_type="subjective",
            sort_order=i + 1,
            status=1
        )
        db.add(q)
        questions.append(q)
    db.commit()
    return questions


def get_or_create_scan_page(db, exam, subject, student):
    sp = db.query(ScanPage).filter(
        ScanPage.exam_id == exam.id,
        ScanPage.subject_id == subject.id,
        ScanPage.student_id == student.id
    ).first()
    if sp:
        return sp
    sp = ScanPage(
        exam_id=exam.id,
        subject_id=subject.id,
        student_id=student.id,
        page_number=1,
        status="processed",
        binding_status="bound",
        ocr_result={"choice": [], "subjective_cuts": []}
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return sp


def create_mark_results(db, exam, subject, students, questions):
    results = []
    full_score = sum(float(q.score) for q in questions)

    # 为每道题预设难度系数，确保生成简单、中等、很难、非常难四个分组
    # 题目越靠后难度越高
    base_difficulty = []
    n = len(questions)
    for idx, q in enumerate(questions):
        # 将题目均匀分布到四个难度区间
        if idx < n * 0.25:
            base = random.uniform(0.95, 1.0)
        elif idx < n * 0.5:
            base = random.uniform(0.60, 0.80)
        elif idx < n * 0.75:
            base = random.uniform(0.40, 0.60)
        else:
            base = random.uniform(0.20, 0.40)
        base_difficulty.append(base)

    for s in students:
        existing = db.query(MarkResult).filter(
            MarkResult.exam_id == exam.id,
            MarkResult.student_id == s.id,
            MarkResult.subject_id == subject.id
        ).first()
        if existing:
            results.append(existing)
            continue

        # 为该学生创建扫描页
        scan_page = get_or_create_scan_page(db, exam, subject, s)

        # 学生能力系数：0.7 ~ 1.0，使简单题班级得分率能超过 80%
        ability = random.uniform(0.7, 1.0)
        detail_scores = []
        for q, base in zip(questions, base_difficulty):
            q_full = float(q.score)
            # 最终得分率 = 难度系数 * 能力系数 + 随机扰动
            rate = base * ability + random.uniform(-0.10, 0.10)
            rate = max(0.0, min(1.0, rate))
            score = round(q_full * rate, 2)
            score = max(0.0, min(q_full, score))
            detail_scores.append(score)

        total = round(sum(detail_scores), 2)

        mr = MarkResult(
            exam_id=exam.id,
            subject_id=subject.id,
            student_id=s.id,
            scan_page_id=scan_page.id,
            choice_score=0,
            subjective_score=0,
            total_score=0,
            status="pending"
        )
        db.add(mr)
        db.commit()
        db.refresh(mr)
        results.append(mr)

        subjective_cuts = []
        subjective_scores = {}
        for q, score in zip(questions, detail_scores):
            q_full = float(q.score)
            if score >= q_full - 0.01:
                answer_text = "该生作答完整、规范，步骤清晰，答案正确。"
            elif score >= q_full * 0.6:
                answer_text = "该生作答基本正确，但部分步骤不够完整或存在小瑕疵。"
            else:
                answer_text = "该生作答存在明显错误，概念理解不够到位，需要加强相关知识点的练习。"
            md = MarkDetail(
                mark_result_id=mr.id,
                exam_id=exam.id,
                subject_id=subject.id,
                student_id=s.id,
                question_id=q.id,
                score=score,
                student_answer=answer_text,
                status="completed",
                marked_at=datetime.now()
            )
            db.add(md)
            subjective_cuts.append({
                "question_no": q.question_no,
                "full_score": q_full,
                "got_score": score,
                "file_url": None,
                "student_answer": answer_text
            })
            subjective_scores[str(q.question_no)] = float(score)
        # 写入 subjective_result 并标记为已批阅，便于按题阅卷与 AI 阅卷测试
        mr.subjective_result = {"cuts": subjective_cuts, "scores": subjective_scores}
        mr.subjective_score = total
        mr.total_score = total
        mr.status = "marked"
        mr.marked_at = datetime.now()
        scan_page.ocr_result = {"choice": [], "subjective_cuts": subjective_cuts}
        db.commit()
    return results


def clear_exam_marks(db, exam_ids, subject_id):
    """清空指定考试和科目的成绩、小题分与扫描页，便于重新生成"""
    db.query(MarkDetail).filter(
        MarkDetail.exam_id.in_(exam_ids),
        MarkDetail.subject_id == subject_id
    ).delete(synchronize_session=False)
    db.query(MarkResult).filter(
        MarkResult.exam_id.in_(exam_ids),
        MarkResult.subject_id == subject_id
    ).delete(synchronize_session=False)
    db.query(ScanPage).filter(
        ScanPage.exam_id.in_(exam_ids),
        ScanPage.subject_id == subject_id
    ).delete(synchronize_session=False)
    db.commit()
    print("   已清空旧的成绩、小题分与扫描页数据")


def main():
    print("🚀 开始生成模拟数据...")
    init_db()
    db = SessionLocal()
    try:
        subjects = get_or_create_subjects(db)
        grades = get_or_create_grades(db)
        target_grade = next((g for g in grades if g.grade_name == "九年级"), grades[-1])
        classes = get_or_create_classes(db, target_grade, count=3)
        students = create_students(db, classes, count_per_class=15)
        print(f"   学生数量: {len(students)}")

        target_subject = next((s for s in subjects if s.subject_name == "语文"), subjects[0])

        prev_exam = create_exam(
            db, "2024年春季期中考试", target_grade, subjects,
            datetime(2024, 4, 15, 8, 0, 0), status="finished"
        )
        curr_exam = create_exam(
            db, "初三四模考试", target_grade, subjects,
            datetime(2024, 6, 20, 8, 0, 0), status="finished"
        )
        print(f"   当前考试: {curr_exam.exam_name}")

        # 重新生成成绩数据，确保难度分组合理
        clear_exam_marks(db, [prev_exam.id, curr_exam.id], target_subject.id)

        for exam in [prev_exam, curr_exam]:
            create_exam_subjects(db, exam, subjects)
            questions = create_exam_questions(db, exam, target_subject, 150)
            create_mark_results(db, exam, target_subject, students, questions)

        db.commit()
        print("✅ 模拟数据生成完成")
        print(f"   考试ID: {curr_exam.id}, 科目ID: {target_subject.id}, 年级ID: {target_grade.id}")
        print(f"   班级IDs: {[c.id for c in classes]}")
        print("   示例学生ID:", students[0].id)
    except Exception as e:
        db.rollback()
        print(f"❌ 生成失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
