#!/usr/bin/env python3
"""
数据库初始化脚本
创建表结构并插入种子数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine, AsyncSessionLocal
from app.models.base import Base
from app.core.security import get_password_hash


async def create_tables():
    """创建所有表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


async def seed_data():
    """插入种子数据"""
    async with AsyncSessionLocal() as session:
        # 导入模型
        from app.models.user import User
        from app.models.exam import Exam, ExamSubject

        # 检查是否已有数据
        result = await session.execute("SELECT COUNT(*) FROM users")
        count = result.scalar()
        if count > 0:
            print("⚠️  数据库已有数据，跳过种子数据插入")
            return

        # 创建管理员用户
        admin = User(
            username="admin",
            email="admin@school.edu.cn",
            hashed_password=get_password_hash("admin123"),
            name="系统管理员",
            role="admin",
            is_active=True
        )
        session.add(admin)

        # 创建教师用户
        teachers = [
            User(
                username="teacher1",
                email="teacher1@school.edu.cn",
                hashed_password=get_password_hash("teacher123"),
                name="张老师",
                role="teacher",
                is_active=True
            ),
            User(
                username="teacher2",
                email="teacher2@school.edu.cn",
                hashed_password=get_password_hash("teacher123"),
                name="李老师",
                role="teacher",
                is_active=True
            ),
            User(
                username="marker1",
                email="marker1@school.edu.cn",
                hashed_password=get_password_hash("marker123"),
                name="阅卷老师A",
                role="marker",
                is_active=True
            )
        ]
        for t in teachers:
            session.add(t)

        await session.flush()

        # 创建科目字典（与前端科目 ID 保持一致）
        from app.models.exam import Subject
        from datetime import datetime

        subject_data = [
            {"id": 1, "subject_name": "语文", "subject_code": "yuwen", "sort_order": 1},
            {"id": 2, "subject_name": "数学", "subject_code": "shuxue", "sort_order": 2},
            {"id": 3, "subject_name": "英语", "subject_code": "yingyu", "sort_order": 3},
            {"id": 4, "subject_name": "物理", "subject_code": "wuli", "sort_order": 4},
            {"id": 5, "subject_name": "化学", "subject_code": "huaxue", "sort_order": 5},
            {"id": 6, "subject_name": "生物学", "subject_code": "shengwu", "sort_order": 6},
            {"id": 7, "subject_name": "道德与法治", "subject_code": "daofa", "sort_order": 7},
            {"id": 8, "subject_name": "历史", "subject_code": "lishi", "sort_order": 8},
            {"id": 9, "subject_name": "地理", "subject_code": "dili", "sort_order": 9},
            {"id": 10, "subject_name": "信息科技", "subject_code": "xinxikeji", "sort_order": 10},
            {"id": 11, "subject_name": "音乐", "subject_code": "yinyue", "sort_order": 11},
            {"id": 12, "subject_name": "美术", "subject_code": "meishu", "sort_order": 12},
            {"id": 13, "subject_name": "体育与健康", "subject_code": "tiyu", "sort_order": 13},
            {"id": 14, "subject_name": "综合实践活动", "subject_code": "zonghe", "sort_order": 14},
        ]
        for s in subject_data:
            session.add(Subject(**s))

        await session.flush()

        # 创建示例考试
        exam = Exam(
            exam_name="2024年春季期中考试",
            exam_type="midterm",
            exam_level="school",
            grade="初三",
            start_time=datetime(2024, 4, 15, 8, 0, 0),
            end_time=datetime(2024, 4, 15, 17, 0, 0),
            status="completed",
            total_score=750,
            total_students=472,
            created_by=admin.id
        )
        session.add(exam)
        await session.flush()

        # 创建考试科目关联
        exam_subjects = [
            ExamSubject(exam_id=exam.id, subject_id=1, total_score=150),
            ExamSubject(exam_id=exam.id, subject_id=2, total_score=150),
            ExamSubject(exam_id=exam.id, subject_id=3, total_score=150),
            ExamSubject(exam_id=exam.id, subject_id=4, total_score=100),
            ExamSubject(exam_id=exam.id, subject_id=5, total_score=100),
        ]
        for es in exam_subjects:
            session.add(es)

        await session.commit()
        print("✅ 种子数据插入完成")
        print("   - 管理员: admin / admin123")
        print("   - 教师: teacher1 / teacher123")
        print("   - 阅卷老师: marker1 / marker123")


async def main():
    print("🚀 开始初始化数据库...")
    await create_tables()
    await seed_data()
    print("✨ 数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
