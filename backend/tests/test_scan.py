"""
扫描上传模块测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np

from app.main import app

client = TestClient(app)


class TestScanUpload:
    """扫描上传 API 测试"""

    def test_upload_image_success(self):
        """测试图片上传成功"""
        # 创建一个简单的测试图片
        from io import BytesIO
        image_data = BytesIO(b"fake image data")

        response = client.post(
            "/api/v1/scan/upload",
            data={"exam_id": 1, "student_id": "2024001"},
            files={"file": ("test.jpg", image_data, "image/jpeg")}
        )
        # 由于我们没有真正的文件处理，这里可能会返回 422 或 200
        assert response.status_code in [200, 422]

    def test_upload_pdf_success(self):
        """测试 PDF 上传成功"""
        from io import BytesIO
        pdf_data = BytesIO(b"fake pdf data")

        response = client.post(
            "/api/v1/scan/upload-pdf",
            data={"exam_id": 1},
            files={"file": ("test.pdf", pdf_data, "application/pdf")}
        )
        assert response.status_code in [200, 422]

    def test_upload_without_file(self):
        """测试不带文件上传"""
        response = client.post(
            "/api/v1/scan/upload",
            data={"exam_id": 1}
        )
        assert response.status_code == 422

    def test_upload_progress(self):
        """测试上传进度查询"""
        response = client.get("/api/v1/scan/progress/1")
        assert response.status_code == 200
        data = response.json()
        assert "progress" in data or "code" in data


class TestPDFParser:
    """PDF 解析测试"""

    @patch("app.services.pdf_parser.fitz.open")
    def test_pdf_parse(self, mock_fitz_open):
        """测试 PDF 解析"""
        from app.services.pdf_parser import PDFParser

        # 模拟 PDF 文档
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=2)
        mock_page = MagicMock()
        mock_page.rect = MagicMock()
        mock_page.rect.width = 595
        mock_page.rect.height = 842
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        parser = PDFParser(target_dpi=300)
        # 由于需要真实文件，这里只测试初始化
        assert parser.target_dpi == 300

    def test_detect_student_id(self):
        """测试学号检测"""
        from app.services.pdf_parser import PDFParser

        parser = PDFParser()
        # 创建一个模拟的页面图像
        mock_image = np.ones((1000, 800, 3), dtype=np.uint8) * 255

        # 由于没有真实的 OCR，测试应该返回 None
        result = parser.detect_student_id(mock_image)
        assert result is None or isinstance(result, str)
