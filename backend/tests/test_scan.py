"""
扫描上传模块测试

覆盖图片直连上传、PDF 上传、参数校验与「按顺序关联」学生绑定。
文件落盘与后台 OCR 处理通过 mock 隔离，避免测试依赖磁盘与识别模型。
"""

from unittest.mock import patch, AsyncMock

import pytest


@pytest.fixture
def mock_scan_deps():
    """隔离对象存储与后台 OCR 任务"""
    with patch("app.api.v1.scan.MinIOStorage") as storage_cls, \
            patch("app.api.v1.scan.process_scan_image") as task:
        storage_cls.return_value.save_image = AsyncMock(
            return_value="/uploads/1/2/2043/01/01/test.png"
        )
        yield storage_cls.return_value, task


PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


class TestImageUpload:
    """图片上传 API 测试"""

    def test_upload_image_success(self, client, mock_scan_deps):
        """图片上传成功并返回扫描页信息"""
        files = {"file": ("test.png", PNG_BYTES, "image/png")}
        data = {
            "exam_id": 1, "subject_id": 2, "page_number": 1,
            "scan_mode": "direct", "binding_mode": "auto",
        }

        response = client.post("/api/v1/scan/upload/image", data=data, files=files)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["success"] is True
        assert body["fileUrl"] == "/uploads/1/2/2043/01/01/test.png"
        assert body["scanPageId"]
        assert body["scanMode"] == "direct"

    def test_upload_image_rejects_non_image(self, client, mock_scan_deps):
        """非图片类型应返回 400"""
        files = {"file": ("test.pdf", b"%PDF-1.4", "application/pdf")}
        response = client.post(
            "/api/v1/scan/upload/image",
            data={"exam_id": 1, "subject_id": 2},
            files=files,
        )
        assert response.status_code == 400

    def test_upload_image_missing_file(self, client, mock_scan_deps):
        """缺少文件应返回 422"""
        response = client.post(
            "/api/v1/scan/upload/image",
            data={"exam_id": 1, "subject_id": 2},
        )
        assert response.status_code == 422

    def test_upload_image_sequential_binding(self, client, mock_scan_deps, students):
        """按顺序关联：第一页绑定第一名学生"""
        files = {"file": ("a.png", PNG_BYTES, "image/png")}
        response = client.post(
            "/api/v1/scan/upload/image",
            data={"exam_id": 5, "subject_id": 6, "binding_mode": "sequential"},
            files=files,
        )
        assert response.status_code == 200, response.text
        assert response.json()["studentId"] == students[0]


class TestPDFUpload:
    """PDF 上传 API 测试"""

    def test_upload_pdf_rejects_non_pdf(self, client, mock_scan_deps):
        """非 PDF 文件应返回 400"""
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}
        response = client.post(
            "/api/v1/scan/upload/pdf",
            data={"exam_id": 1, "subject_id": 2},
            files=files,
        )
        assert response.status_code == 400

    def test_upload_pdf_success(self, client, mock_scan_deps):
        """PDF 解析成功返回页数与绑定信息"""
        fake_result = {
            "total_pages": 2,
            "pages": [
                {"file_url": "/uploads/1/2/x/p1.png", "page_number": 1},
                {"file_url": "/uploads/1/2/x/p2.png", "page_number": 2},
            ],
            "student_bindings": [{"student_id": None}, {"student_id": None}],
        }
        with patch("app.api.v1.scan.PDFUploadService") as service_cls:
            service_cls.return_value.process_upload = AsyncMock(return_value=fake_result)

            files = {"file": ("test.pdf", b"%PDF-1.4\n", "application/pdf")}
            response = client.post(
                "/api/v1/scan/upload/pdf",
                data={"exam_id": 1, "subject_id": 2, "binding_mode": "auto"},
                files=files,
            )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["success"] is True
        assert body["totalPages"] == 2
        assert len(body["pages"]) == 2
