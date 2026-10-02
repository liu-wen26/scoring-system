"""
Pytest 共享配置

- 使用内存 SQLite 替换应用数据库
- 覆盖认证依赖，注入测试管理员（接口均已要求登录）
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db, Base
from app.core.security import get_current_user
from app import models  # noqa: F401  确保所有模型注册到 Base.metadata
from app.models.user import User, Student

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """测试用数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """每个用例前后建表 / 拆表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def admin_user(setup_database):
    """创建测试管理员账号"""
    db = TestingSessionLocal()
    user = User(
        username="admin",
        password_hash="test-hash",
        real_name="系统管理员",
        role="admin",
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture(scope="function", autouse=True)
def override_dependencies(admin_user):
    """覆盖数据库与当前用户依赖"""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="function")
def client():
    """提供测试客户端"""
    return TestClient(app)


@pytest.fixture(scope="function")
def students(setup_database):
    """创建两名测试学生，用于验证按顺序关联"""
    db = TestingSessionLocal()
    items = [
        Student(student_no="2024001", real_name="张伟"),
        Student(student_no="2024002", real_name="李娜"),
    ]
    db.add_all(items)
    db.commit()
    ids = [s.id for s in items]
    db.close()
    return ids


@pytest.fixture
def auth_headers():
    """提供认证请求头（依赖已覆盖，仅占位）"""
    return {"Authorization": "Bearer test-token"}
