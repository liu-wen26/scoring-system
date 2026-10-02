"""
考试管理模块测试

接口响应统一使用 camelCase（examName/grade/status 等）。
"""

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user


EXAM_PAYLOAD = {
    "examName": "单元测试考试",
    "examType": "unit_test",
    "examLevel": "校级",
    "grade": "八年级",
    "startTime": "2024-05-01T08:00:00",
    "endTime": "2024-05-01T10:00:00",
}


class TestExamAPI:
    """考试管理 API 测试"""

    def test_create_exam(self, client):
        """测试创建考试"""
        response = client.post("/api/v1/exam/", json=EXAM_PAYLOAD)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["examName"] == "单元测试考试"
        assert data["grade"] == "八年级"
        assert data["status"] == "draft"

    def test_list_exams(self, client):
        """测试获取考试列表"""
        client.post("/api/v1/exam/", json={**EXAM_PAYLOAD, "examName": "列表测试考试"})

        response = client.get("/api/v1/exam/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert "列表测试考试" in [e["examName"] for e in data["items"]]

    def test_get_exam_detail(self, client):
        """测试获取考试详情"""
        exam_id = client.post("/api/v1/exam/", json=EXAM_PAYLOAD).json()["id"]

        response = client.get(f"/api/v1/exam/{exam_id}")
        assert response.status_code == 200
        assert response.json()["examName"] == "单元测试考试"

    def test_update_exam(self, client):
        """测试更新考试"""
        exam_id = client.post("/api/v1/exam/", json=EXAM_PAYLOAD).json()["id"]

        response = client.put(f"/api/v1/exam/{exam_id}", json={"examName": "更新后考试"})
        assert response.status_code == 200
        assert response.json()["examName"] == "更新后考试"

    def test_delete_exam(self, client):
        """测试删除考试"""
        exam_id = client.post("/api/v1/exam/", json=EXAM_PAYLOAD).json()["id"]

        assert client.delete(f"/api/v1/exam/{exam_id}").status_code == 200

        # 确认已删除
        assert client.get(f"/api/v1/exam/{exam_id}").status_code == 404

    def test_exam_requires_auth(self):
        """未携带凭据访问应被拒绝"""
        saved = app.dependency_overrides.pop(get_current_user)
        try:
            response = TestClient(app).get("/api/v1/exam/")
            assert response.status_code in (401, 403)
        finally:
            app.dependency_overrides[get_current_user] = saved


class TestHealthCheck:
    """健康检查测试"""

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "初中智能阅卷系统" in response.json()["message"]
