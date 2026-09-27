"""
考试管理模块测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base

# 内存数据库用于测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestExamAPI:
    """考试管理 API 测试"""

    def test_create_exam(self):
        """测试创建考试"""
        response = client.post("/api/v1/exam/", json={
            "name": "单元测试考试",
            "exam_type": "unit_test",
            "grade": "初二",
            "semester": "2024春季",
            "start_time": "2024-05-01T08:00:00",
            "end_time": "2024-05-01T10:00:00"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "单元测试考试"
        assert data["grade"] == "初二"

    def test_list_exams(self):
        """测试获取考试列表"""
        # 先创建一个考试
        client.post("/api/v1/exam/", json={
            "name": "列表测试考试",
            "exam_type": "midterm",
            "grade": "初三",
            "semester": "2024春季"
        })

        response = client.get("/api/v1/exam/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_exam_detail(self):
        """测试获取考试详情"""
        # 创建考试
        create_resp = client.post("/api/v1/exam/", json={
            "name": "详情测试考试",
            "exam_type": "final",
            "grade": "初一"
        })
        exam_id = create_resp.json()["id"]

        # 获取详情
        response = client.get(f"/api/v1/exam/{exam_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "详情测试考试"

    def test_update_exam(self):
        """测试更新考试"""
        create_resp = client.post("/api/v1/exam/", json={
            "name": "更新前",
            "exam_type": "quiz"
        })
        exam_id = create_resp.json()["id"]

        response = client.put(f"/api/v1/exam/{exam_id}", json={
            "name": "更新后"
        })
        assert response.status_code == 200
        assert response.json()["name"] == "更新后"

    def test_delete_exam(self):
        """测试删除考试"""
        create_resp = client.post("/api/v1/exam/", json={
            "name": "待删除考试"
        })
        exam_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/exam/{exam_id}")
        assert response.status_code == 200

        # 确认已删除
        get_resp = client.get(f"/api/v1/exam/{exam_id}")
        assert get_resp.status_code == 404


class TestHealthCheck:
    """健康检查测试"""

    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "初中智能阅卷系统" in response.json()["message"]
