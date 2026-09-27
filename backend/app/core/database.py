from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# 创建引擎（SQLite 需要关闭连接池并允许同线程复用）
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.DEBUG,
}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = __import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool
else:
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20})

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()


def get_db() -> Session:
    """获取数据库会话（依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    from app.models import exam, user, mark, scan, answer_card, wrong_question
    from app.models.exam import ExamQuestion
    from app.models.mark import MarkDetail, AIMarkConfig, AIMarkTask, AIMarkLog
    Base.metadata.create_all(bind=engine)


def migrate_db():
    """执行数据库迁移（自动添加新列）"""
    from app.models.exam import ExamQuestion
    from app.models.mark import MarkDetail, AIMarkConfig, AIMarkTask, AIMarkLog
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    try:
        columns = [c['name'] for c in inspector.get_columns('answer_card_configs')]
        template_columns = [c['name'] for c in inspector.get_columns('answer_card_templates')]
        exam_columns = [c['name'] for c in inspector.get_columns('exams')]
        question_columns = [c['name'] for c in inspector.get_columns('exam_questions')]
        detail_columns = [c['name'] for c in inspector.get_columns('mark_details')]
        subject_columns = [c['name'] for c in inspector.get_columns('subjects')]
    except SQLAlchemyError:
        return

    with engine.begin() as conn:
        if 'template_width' not in columns:
            conn.execute(text("ALTER TABLE answer_card_configs ADD COLUMN template_width INTEGER DEFAULT 0"))
            print("[migrate_db] 已添加列 answer_card_configs.template_width")
        if 'template_height' not in columns:
            conn.execute(text("ALTER TABLE answer_card_configs ADD COLUMN template_height INTEGER DEFAULT 0"))
            print("[migrate_db] 已添加列 answer_card_configs.template_height")
        if 'grade_id' not in template_columns:
            conn.execute(text("ALTER TABLE answer_card_templates ADD COLUMN grade_id INTEGER"))
            print("[migrate_db] 已添加列 answer_card_templates.grade_id")
        if 'subject_id' not in template_columns:
            conn.execute(text("ALTER TABLE answer_card_templates ADD COLUMN subject_id INTEGER"))
            print("[migrate_db] 已添加列 answer_card_templates.subject_id")
        if 'template_type' not in template_columns:
            conn.execute(text("ALTER TABLE answer_card_templates ADD COLUMN template_type VARCHAR(20) DEFAULT 'custom'"))
            print("[migrate_db] 已添加列 answer_card_templates.template_type")
        if 'grade_id' not in exam_columns:
            conn.execute(text("ALTER TABLE exams ADD COLUMN grade_id INTEGER DEFAULT 0"))
            print("[migrate_db] 已添加列 exams.grade_id")
        if 'question_content' not in question_columns:
            conn.execute(text("ALTER TABLE exam_questions ADD COLUMN question_content TEXT"))
            print("[migrate_db] 已添加列 exam_questions.question_content")
        if 'knowledge_point' not in question_columns:
            conn.execute(text("ALTER TABLE exam_questions ADD COLUMN knowledge_point VARCHAR(200)"))
            print("[migrate_db] 已添加列 exam_questions.knowledge_point")
        if 'ability' not in question_columns:
            conn.execute(text("ALTER TABLE exam_questions ADD COLUMN ability VARCHAR(200)"))
            print("[migrate_db] 已添加列 exam_questions.ability")
        if 'student_answer' not in detail_columns:
            conn.execute(text("ALTER TABLE mark_details ADD COLUMN student_answer TEXT"))
            print("[migrate_db] 已添加列 mark_details.student_answer")
        if 'grade_level' not in subject_columns:
            conn.execute(text("ALTER TABLE subjects ADD COLUMN grade_level INTEGER DEFAULT 0"))
            print("[migrate_db] 已添加列 subjects.grade_level")


def seed_data():
    """初始化默认基础数据（仅在表为空时插入）"""
    from app.models.user import Grade, Class
    from app.models.exam import Subject

    db = SessionLocal()
    try:
        if not db.query(Grade).first():
            grade_names = ['七年级', '八年级', '九年级']
            db.add_all([
                Grade(grade_name=name, grade_level=i + 7)
                for i, name in enumerate(grade_names)
            ])
            print("[seed_data] 已初始化默认年级")

        if not db.query(Subject).first():
            # 先初始化所有通用科目（年级字段为 0）
            general_subjects = [
                ('语文', 'chinese'), ('数学', 'math'), ('英语', 'english'),
                ('体育', 'pe'), ('音乐', 'music'), ('美术', 'art'),
                ('信息技术', 'it'), ('综合实践活动', 'practice')
            ]
            sort_order = 0
            for name, code in general_subjects:
                db.add(Subject(subject_name=name, subject_code=code, status=1, sort_order=sort_order, grade_level=0))
                sort_order += 1

            # 再按年级初始化科目（七八年级：史地生政；九年级：物化史政）
            grade_subjects = {
                7: [
                    ('历史', 'history'), ('地理', 'geography'),
                    ('生物学', 'biology'), ('道德与法治', 'morality_law')
                ],
                8: [
                    ('历史', 'history'), ('地理', 'geography'),
                    ('生物学', 'biology'), ('道德与法治', 'morality_law')
                ],
                9: [
                    ('物理', 'physics'), ('化学', 'chemistry'),
                    ('历史', 'history'), ('道德与法治', 'morality_law')
                ]
            }
            for grade_level, subjects in grade_subjects.items():
                for name, code in subjects:
                    db.add(Subject(subject_name=name, subject_code=code, status=1, sort_order=sort_order, grade_level=grade_level))
                    sort_order += 1
            print("[seed_data] 已初始化默认科目")

        # 为每个年级初始化默认班级（如 七年级1班、七年级2班、七年级3班）
        if not db.query(Class).first():
            grades = db.query(Grade).all()
            classes = []
            for grade in grades:
                for i in range(1, 4):
                    classes.append(Class(class_name=f"{grade.grade_name}{i}班", grade_id=grade.id))
            if classes:
                db.add_all(classes)
                print("[seed_data] 已初始化默认班级")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[seed_data] 初始化数据失败: {e}")
    finally:
        db.close()
