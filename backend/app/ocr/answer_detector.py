import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ChoiceConfig:
    """选择题配置"""
    option_count: int = 4
    option_width: int = 30
    option_height: int = 30
    option_spacing: int = 10
    fill_threshold: float = 0.15
    multi_select: bool = False


@dataclass
class ChoiceResult:
    """选择题识别结果"""
    question_number: int
    selected_options: List[str]
    confidence: float
    is_filled: bool
    fill_ratios: Dict[str, float]


class ChoiceAnswerDetector:
    """选择题答案检测器"""
    
    def __init__(self, config: Optional[ChoiceConfig] = None):
        self.config = config or ChoiceConfig()
        self.options = ['A', 'B', 'C', 'D', 'E', 'F'][:self.config.option_count]
    
    def detect_all(self, image: np.ndarray, 
                   question_regions: List[Tuple[int, int, int, int]]) -> List[ChoiceResult]:
        """
        检测所有选择题答案
        
        Args:
            image: 校正后的答题卡图片 (灰度或二值化)
            question_regions: 每道题的区域坐标列表 [(x, y, w, h), ...]
        
        Returns:
            每道题的识别结果
        """
        results = []
        
        for i, region in enumerate(question_regions, 1):
            x, y, w, h = region
            question_image = image[y:y+h, x:x+w]
            result = self.detect_single(question_image, i)
            results.append(result)
        
        return results
    
    def detect_single(self, question_image: np.ndarray, 
                      question_number: int) -> ChoiceResult:
        """
        检测单道选择题答案
        
        Args:
            question_image: 单道题目的图片区域
            question_number: 题号
        
        Returns:
            识别结果
        """
        h, w = question_image.shape[:2]
        
        if len(question_image.shape) == 3:
            gray = cv2.cvtColor(question_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = question_image
        
        # 二值化（反色，涂写区域为白色）
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 计算每个选项的填充比例
        fill_ratios = {}
        option_width = w // self.config.option_count
        
        for idx, option in enumerate(self.options):
            x_start = idx * option_width
            x_end = (idx + 1) * option_width if idx < self.config.option_count - 1 else w
            option_region = binary[:, x_start:x_end]
            
            total_pixels = option_region.size
            filled_pixels = cv2.countNonZero(option_region)
            fill_ratio = filled_pixels / total_pixels
            
            fill_ratios[option] = fill_ratio
        
        # 判断选中的选项
        selected = []
        max_ratio = max(fill_ratios.values())
        
        if max_ratio >= self.config.fill_threshold:
            if self.config.multi_select:
                for option, ratio in fill_ratios.items():
                    if ratio >= self.config.fill_threshold:
                        selected.append(option)
            else:
                best_option = max(fill_ratios, key=fill_ratios.get)
                selected.append(best_option)
        
        confidence = max_ratio if selected else 0.0
        
        return ChoiceResult(
            question_number=question_number,
            selected_options=selected,
            confidence=confidence,
            is_filled=len(selected) > 0,
            fill_ratios=fill_ratios
        )
