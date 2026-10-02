"""
OCR / 答案识别模块测试

针对实际存在的 app.ocr.answer_detector.ChoiceAnswerDetector 做功能验证。
"""

import numpy as np

from app.ocr.answer_detector import ChoiceAnswerDetector, ChoiceConfig


def _make_question_row(width=400, height=100, option_count=4, filled_index=None):
    """构造单行选择题图片：白色底，选定选项涂黑"""
    image = np.full((height, width), 255, dtype=np.uint8)
    if filled_index is not None:
        option_width = width // option_count
        x_start = filled_index * option_width
        x_end = width if filled_index == option_count - 1 else (filled_index + 1) * option_width
        image[:, x_start:x_end] = 0
    return image


class TestChoiceAnswerDetector:
    """选择题答案检测测试"""

    def test_detect_single_selected_option(self):
        """涂黑第 3 个选项应识别为 C"""
        detector = ChoiceAnswerDetector()
        image = _make_question_row(filled_index=2)

        result = detector.detect_single(image, 1)

        assert result.selected_options == ["C"]
        assert result.is_filled is True
        assert result.confidence > 0.9

    def test_detect_single_blank(self):
        """全空白区域应判定为未填涂"""
        detector = ChoiceAnswerDetector()
        image = _make_question_row(filled_index=None)

        result = detector.detect_single(image, 1)

        assert result.selected_options == []
        assert result.is_filled is False
        assert result.confidence == 0.0

    def test_detect_all_regions(self):
        """多题区域批量识别，题号与答案一一对应"""
        detector = ChoiceAnswerDetector()
        regions = [
            (0, 0, 400, 100),
            (0, 100, 400, 100),
            (0, 200, 400, 100),
        ]
        image = np.full((300, 400), 255, dtype=np.uint8)
        image[0:100, 200:300] = 0      # 第 1 题 -> C
        image[100:200, 0:100] = 0      # 第 2 题 -> A
        image[200:300, 300:400] = 0    # 第 3 题 -> D

        results = detector.detect_all(image, regions)

        assert [r.question_number for r in results] == [1, 2, 3]
        assert results[0].selected_options == ["C"]
        assert results[1].selected_options == ["A"]
        assert results[2].selected_options == ["D"]

    def test_multi_select(self):
        """多选题模式下应返回全部涂黑选项"""
        detector = ChoiceAnswerDetector(ChoiceConfig(multi_select=True))
        image = _make_question_row(filled_index=None)
        image[:, 0:100] = 0      # A
        image[:, 200:300] = 0    # C

        result = detector.detect_single(image, 1)

        assert set(result.selected_options) == {"A", "C"}

    def test_custom_option_count(self):
        """自定义选项数量（如 3 选项）"""
        detector = ChoiceAnswerDetector(ChoiceConfig(option_count=3))
        image = _make_question_row(width=300, option_count=3, filled_index=2)

        result = detector.detect_single(image, 1)

        assert detector.options == ["A", "B", "C"]
        assert result.selected_options == ["C"]
