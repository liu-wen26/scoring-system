"""
Pytest 配置文件
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """提供测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """提供认证请求头 (模拟)"""
    return {
        "Authorization": "Bearer test-token"
    }
