"""
AI 辅助阅卷服务
- 调用阿里云百炼大模型对主观题自动评分
- 提供连续批阅、数量限制、停止等控制能力
"""

import json
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.models.mark import AIMarkConfig, AIMarkTask, AIMarkLog, MarkResult, MarkDetail
from app.models.exam import ExamQuestion
from app.models.user import Student


BAILIAN_DEFAULT_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
BAILIAN_DEFAULT_MODEL = "qwen-turbo"


async def call_bailian_score(
    api_key: str,
    model: str,
    endpoint: str,
    question_content: str,
    standard_answer: str,
    scoring_criteria: str,
    student_answer: str,
    full_score: float,
) -> Tuple[float, str]:
    """
    调用百炼大模型评分，返回 (score, reason)
    """
    system_prompt = """你是一位严谨的中小学主观题阅卷专家。请根据题目、标准答案、评分标准和学生答案，给出公正、合理的分数与简短评价。
你必须按以下 JSON 格式输出，不要包含任何其他内容：
{"score": 分数, "reason": "评分理由"}
分数必须是 0 到满分之间的数字（可保留一位小数），评分理由控制在 100 字以内。"""

    user_prompt = f"""题目：
{question_content}

标准答案：
{standard_answer}

评分标准：
{scoring_criteria}

学生答案：
{student_answer}

满分：{full_score} 分

请输出 JSON 评分结果。"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
    if not content:
        raise ValueError("模型返回内容为空")

    # 提取 JSON
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content)
        content = re.sub(r"```$", "", content).strip()

    result = json.loads(content)
    score = float(result.get("score", 0))
    reason = result.get("reason", "")
    score = max(0.0, min(float(full_score), score))
    return round(score, 1), reason


def get_or_create_ai_config(db: Session, user_id: int, api_key: str) -> AIMarkConfig:
    """获取或创建 AI 阅卷配置"""
    config = db.query(AIMarkConfig).filter(AIMarkConfig.user_id == user_id).first()
    if not config:
        config = AIMarkConfig(
            user_id=user_id,
            provider="bailian",
            api_key=api_key,
            model=BAILIAN_DEFAULT_MODEL,
            endpoint=BAILIAN_DEFAULT_ENDPOINT,
        )
        db.add(config)
    else:
        config.api_key = api_key
    db.commit()
    db.refresh(config)
    return config


def get_ai_config(db: Session, user_id: int) -> Optional[AIMarkConfig]:
    return db.query(AIMarkConfig).filter(AIMarkConfig.user_id == user_id).first()


def create_ai_mark_task(
    db: Session,
    user_id: int,
    exam_id: int,
    subject_id: int,
    question_no: str,
    question_content: str,
    standard_answer: str,
    scoring_criteria: str,
    total_limit: int = 0,
) -> AIMarkTask:
    task = AIMarkTask(
        exam_id=exam_id,
        subject_id=subject_id,
        question_no=question_no,
        question_content=question_content,
        standard_answer=standard_answer,
        scoring_criteria=scoring_criteria,
        total_limit=total_limit,
        created_by=user_id,
        status="running",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def find_next_pending_paper(db: Session, task: AIMarkTask) -> Optional[dict]:
    """
    查找该题下一道未批阅试卷。
    优先从 MarkDetail 中读取学生答案；若无 MarkDetail，则尝试 MarkResult.subjective_result。
    """
    # 已处理过的 result_id 集合
    processed_result_ids = {
        log.result_id for log in db.query(AIMarkLog).filter(
            AIMarkLog.task_id == task.id,
            AIMarkLog.status.in_(["success", "skipped"])
        ).all() if log.result_id
    }

    # 所有该考试科目的 MarkResult
    results = db.query(MarkResult).filter(
        MarkResult.exam_id == task.exam_id,
        MarkResult.subject_id == task.subject_id,
    ).all()

    for result in results:
        if result.id in processed_result_ids:
            continue

        # 读取该题 MarkDetail
        detail = db.query(MarkDetail).filter(
            MarkDetail.mark_result_id == result.id,
            MarkDetail.exam_id == task.exam_id,
            MarkDetail.subject_id == task.subject_id,
        ).join(ExamQuestion, MarkDetail.question_id == ExamQuestion.id).filter(
            ExamQuestion.question_no == task.question_no
        ).first()

        full_score = None
        student_answer = None

        if detail:
            full_score = float(detail.score) if detail.score else None
            student_answer = detail.student_answer
            question_id = detail.question_id
        else:
            # 从 MarkResult.subjective_result 兜底
            subjective = result.subjective_result or {}
            cuts = subjective.get("cuts", [])
            for cut in cuts:
                if str(cut.get("question_no")) == str(task.question_no):
                    full_score = float(cut.get("full_score", 0))
                    student_answer = cut.get("student_answer") or result.student_answer
                    question_id = None
                    break

        if full_score is None:
            # 尝试从 exam_questions 获取分数
            question = db.query(ExamQuestion).filter(
                ExamQuestion.exam_id == task.exam_id,
                ExamQuestion.subject_id == task.subject_id,
                ExamQuestion.question_no == task.question_no,
            ).first()
            if question:
                full_score = float(question.score)
                question_id = question.id
            else:
                continue

        # 未写答案也允许 AI 评 0 分
        student = db.query(Student).filter(Student.id == result.student_id).first()

        return {
            "result_id": result.id,
            "scan_page_id": result.scan_page_id,
            "student_id": result.student_id,
            "student_name": student.real_name if student else "",
            "question_no": task.question_no,
            "full_score": full_score,
            "student_answer": student_answer or "（学生未作答）",
            "question_id": question_id,
        }

    return None


def submit_question_score(db: Session, result_id: int, question_no: str, score: float) -> MarkResult:
    """保存单题分数到 MarkResult.subjective_result（兼容现有阅卷逻辑）"""
    result = db.query(MarkResult).filter(MarkResult.id == result_id).first()
    if not result:
        raise ValueError("阅卷结果不存在")

    subjective_result = result.subjective_result or {"cuts": []}
    if "scores" not in subjective_result:
        subjective_result["scores"] = {}
    subjective_result["scores"][str(question_no)] = float(score)

    subjective_score = sum(float(v) for v in subjective_result["scores"].values())
    result.subjective_result = subjective_result
    result.subjective_score = subjective_score
    result.total_score = float(result.choice_score or 0) + subjective_score
    result.status = "marked"
    result.marked_at = datetime.now()
    db.commit()
    db.refresh(result)
    return result


def mark_detail_as_ai_scored(db: Session, detail: MarkDetail, score: float):
    """同步更新 MarkDetail 的分数与状态"""
    if not detail:
        return
    detail.score = Decimal(str(score))
    detail.status = "completed"
    detail.marked_at = datetime.now()
    db.commit()
