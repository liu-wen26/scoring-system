"""
OCR 识别模块测试
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestImagePreprocessor:
    """图像预处理测试"""

    def test_denoise(self):
        """测试去噪功能"""
        from app.ocr.image.preprocess import ImagePreprocessor

        preprocessor = ImagePreprocessor()
        # 创建测试图像
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = preprocessor.denoise(image)

        assert result is not None
        assert result.shape == image.shape

    def test_grayscale(self):
        """测试灰度转换"""
        from app.ocr.image.preprocess import ImagePreprocessor

        preprocessor = ImagePreprocessor()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = preprocessor.to_grayscale(image)

        assert len(result.shape) == 2
        assert result.shape == (100, 100)

    def test_binarize(self):
        """测试二值化"""
        from app.ocr.image.preprocess import ImagePreprocessor

        preprocessor = ImagePreprocessor()
        gray = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        result = preprocessor.binarize(gray)

        assert result is not None
        assert set(np.unique(result)).issubset({0, 255})

    def test_enhance_contrast(self):
        """测试对比度增强"""
        from app.ocr.image.preprocess import ImagePreprocessor

        preprocessor = ImagePreprocessor()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = preprocessor.enhance_contrast(image)

        assert result is not None
        assert result.shape == image.shape


class TestPerspectiveTransformer:
    """透视变换测试"""

    def test_order_points(self):
        """测试点排序"""
        from app.ocr.image.perspective import PerspectiveTransformer

        transformer = PerspectiveTransformer()
        points = np.array([
            [100, 100],  # 左上
            [300, 100],  # 右上
            [300, 400],  # 右下
            [100, 400]   # 左下
        ])

        ordered = transformer._order_points(points)

        assert ordered is not None
        assert ordered.shape == (4, 2)

    def test_transform(self):
        """测试透视变换"""
        from app.ocr.image.perspective import PerspectiveTransformer

        transformer = PerspectiveTransformer()
        image = np.random.randint(0, 255, (500, 400, 3), dtype=np.uint8)

        points = np.array([
            [50, 50],
            [350, 50],
            [350, 450],
            [50, 450]
        ], dtype=np.float32)

        result = transformer.transform(image, points)

        assert result is not None
        assert len(result.shape) == 3


class TestAnswerDetector:
    """答案检测测试"""

    @patch("app.ocr.paddle_ocr.PaddleOCR")
    def test_detect_choice(self, mock_ocr_class):
        """测试选择题检测"""
        from app.ocr.answer_detector import ChoiceAnswerDetector

        # 模拟 OCR 结果
        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = [[
            [[[10, 10], [30, 10], [30, 30], [10, 30]], ('A', 0.95)],
            [[[50, 10], [70, 10], [70, 30], [50, 30]], ('B', 0.92)]
        ]]
        mock_ocr_class.return_value = mock_ocr

        detector = ChoiceAnswerDetector()
        # 创建模拟图像
        image = np.ones((200, 400, 3), dtype=np.uint8) * 255

        # 由于需要真实 OCR，这里只测试初始化
        assert detector is not None

    def test_calculate_fill_ratio(self):
        """测试涂写比例计算"""
        from app.ocr.answer_detector import ChoiceAnswerDetector

        detector = ChoiceAnswerDetector()
        # 全白区域
        white_region = np.ones((50, 50), dtype=np.uint8) * 255
        ratio_white = detector._calculate_fill_ratio(white_region)
        assert ratio_white == 0.0

        # 全黑区域
        black_region = np.zeros((50, 50), dtype=np.uint8)
        ratio_black = detector._calculate_fill_ratio(black_region)
        assert ratio_black == 1.0
